"""Targeted research around the chosen topic's key questions.

Contract: knowledge/research-contract.md (compiled from the core IP).
V1 research runs over the collected evidence pool only — every cited URL
comes from that pool, unsupported questions are marked insufficient, and
resume never re-runs collection.
"""

from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import shutil
import subprocess
import unicodedata
from zoneinfo import ZoneInfo

from . import aihot, fetch, state, topics

AIHOT_EVIDENCE = "aihot-items.json"
RSS_EVIDENCE = "rss-items.json"
RESEARCH_MD = "research.md"
RESEARCH_JSON = "research.json"
STORY_MATRIX_JSON = "story-matrix.json"
INITIAL_EVIDENCE_JSON = "initial-evidence.json"
INITIAL_OSINT_JSON = "initial-osint.json"
INITIAL_OSINT_MD = "initial-osint.md"
MAX_EVIDENCE_PER_QUESTION = 3

_STOP_TOKENS = {"ai", "the", "a", "an", "of", "for", "and", "to", "how", "with"}
_ASCII_RE = re.compile(r"[a-z0-9][a-z0-9.+#-]*")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


class ResearchError(RuntimeError):
    """Raised when research cannot proceed honestly."""


_NO_EVIDENCE_MESSAGE = (
    "no evidence pool; run the collect stage first "
    "(research never fabricates evidence)"
)


# ---------------------------------------------------------------------------
# Evidence pool
# ---------------------------------------------------------------------------


def load_evidence(run_paths) -> list:
    """Load normalized aihot + rss items saved by the collect stage."""
    items = []
    for name in (AIHOT_EVIDENCE, RSS_EVIDENCE):
        path = run_paths.work_dir / name
        if path.exists():
            items.extend(json.loads(path.read_text(encoding="utf-8")))
    return items


def _item_url(item: dict) -> str:
    if item.get("origin") == "aihot":
        links = item.get("links") or {}
        return links.get("original") or links.get("aihot") or ""
    return item.get("url") or ""


def _item_text(item: dict) -> str:
    return f"{item.get('title','')} {item.get('summary','')}"


# ---------------------------------------------------------------------------
# Question → evidence matching (deterministic, lexical)
# ---------------------------------------------------------------------------


def _ascii_tokens(text: str) -> set:
    return {
        t
        for t in _ASCII_RE.findall((text or "").lower())
        if t not in _STOP_TOKENS and len(t) >= 2
    }


def _cjk_bigrams(text: str) -> set:
    chars = _CJK_RE.findall(unicodedata.normalize("NFKC", text or ""))
    s = "".join(chars)
    return {s[i : i + 2] for i in range(len(s) - 1)}


def _match_score(query: str, item: dict) -> int:
    text = _item_text(item)
    ascii_shared = len(_ascii_tokens(query) & _ascii_tokens(text))
    bigram_shared = len(_cjk_bigrams(query) & _cjk_bigrams(text))
    return 2 * ascii_shared + bigram_shared


_BLOCK_TAG_RE = re.compile(
    r"</?(?:p|div|br|hr|li|ul|ol|dl|dt|dd|blockquote|pre|figure|figcaption|"
    r"h[1-6]|table|thead|tbody|tfoot|tr|td|th|section|article|header|"
    r"footer|nav|aside|main)(?:\s[^<>]*)?\s*/?>",
    re.IGNORECASE,
)
_ANY_TAG_RE = re.compile(r"</?[a-zA-Z][^<>]*>")
_UNCLOSED_TAIL_TAG_RE = re.compile(r"<[^<>\n]*$")
_ELLIPSIS_RE = re.compile(r"\u2026|\.{3,}")
_SENTENCE_END_RE = re.compile(r"[。！？!?]|\.(?=\s|$)")
_CURLY_APOSTROPHES = {0x2018: "'", 0x2019: "'"}


def normalize_evidence_text(raw: str) -> str:
    """Turn messy feed evidence into clean prose.

    Feed summaries arrive with raw HTML, escaped entities and truncated
    tails (collect caps summaries mid-sentence, sometimes mid-tag).
    Unescape entities, drop a trailing unclosed tag, convert block tags
    to line breaks, strip all remaining markup and collapse whitespace.
    """
    text = html.unescape(raw or "")
    text = text.translate(_CURLY_APOSTROPHES)
    text = _UNCLOSED_TAIL_TAG_RE.sub("", text)
    text = _BLOCK_TAG_RE.sub("\n", text)
    text = _ANY_TAG_RE.sub("", text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _first_complete_sentence(line: str) -> str:
    match = _SENTENCE_END_RE.search(line)
    if match:
        candidate = line[: match.end()].strip()
        if any(ch.isalnum() for ch in candidate):
            return candidate
    return ""


def evidence_excerpt(summary: str, title: str) -> str:
    """First complete, residue-free sentence of a summary.

    Ellipsis-truncated fragments and unterminated tails are dropped
    instead of repeated; when no complete sentence survives, the
    normalized title stands in.  Never returns raw HTML.
    """
    text = normalize_evidence_text(summary)
    for chunk in _ELLIPSIS_RE.split(text):
        for line in chunk.split("\n"):
            sentence = _first_complete_sentence(line.strip())
            if sentence:
                return sentence
    return normalize_evidence_text(title)


def match_evidence(query: str, items: list, topic_title: str = "") -> list:
    """Rank pool items against one query, deterministically.

    Items qualify at score >= 2 (one shared ascii token, or two shared
    CJK bigrams).  The topic's own event always ranks first — it is the
    hardest fact of the run — then higher lexical scores, then
    title-ascending.  The ordering is applied before the per-question
    cap, so the topic's own announcement can never be squeezed out of a
    question by lexically-tied sibling stories that merely mention the
    same platform or company.
    """
    scored = []
    for item in items:
        score = _match_score(query, item)
        if score >= 2:  # one shared ascii token, or two shared CJK bigrams
            not_own_event = (
                0 if topics.same_event(item.get("title", ""), topic_title) else 1
            )
            scored.append((not_own_event, -score, item.get("title", ""), item))
    scored.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    return [entry[-1] for entry in scored[:MAX_EVIDENCE_PER_QUESTION]]


# ---------------------------------------------------------------------------
# Cross-validation notes
# ---------------------------------------------------------------------------


def cross_validation_notes(items: list) -> list:
    """Group same-event items (across origins) for the conflicts section."""
    notes = []
    used = set()
    for i, a in enumerate(items):
        if i in used:
            continue
        cluster = [a]
        for j in range(i + 1, len(items)):
            if j in used:
                continue
            if topics.same_event(a.get("title", ""), items[j].get("title", "")):
                cluster.append(items[j])
                used.add(j)
        used.add(i)
        if len(cluster) > 1:
            notes.append(cluster)
    return notes


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _render_md(run_paths, topic, questions, notes, pool_sizes) -> str:
    lines = [f"# Research：{topic['title']}", ""]
    lines.append(f"- run: {run_paths.run_id}")
    choice = state.read_state(run_paths).get("topic_choice", "")
    lines.append(f"- 选题来源: {choice}")
    if topic.get("direction"):
        lines.append(f"- 编辑方向（原样保留）: {topic['direction']}")
    lines.append("")

    lines.append("## 关键问题")
    lines.append("")
    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q['query']}")
    lines.append("")

    lines.append("## 证据与来源")
    lines.append("")
    supported = [q for q in questions if q["status"] == "supported"]
    if not supported:
        lines.append("- （无：所有关键问题都缺少可引用证据）")
    for q in supported:
        lines.append(f"### {q['query']}")
        lines.append("")
        for ev in q["evidence"]:
            lines.append(f"- {ev['excerpt']}（[{ev['title']}]({ev['url']})，{ev['origin']}）")
        lines.append("")

    lines.append("## 证据不足（不确定）")
    lines.append("")
    insufficient = [q for q in questions if q["status"] == "insufficient"]
    if not insufficient:
        lines.append("- （无）")
    for q in insufficient:
        lines.append(
            f"- “{q['query']}”：证据池中没有可引用的来源。"
            "不作为文章事实；如必须提及，只能以不确定口径表述。"
        )
    lines.append("")

    lines.append("## 冲突与交叉验证")
    lines.append("")
    if not notes:
        lines.append("- （无多来源事件）")
    for cluster in notes:
        origins = sorted({c.get("origin", "unknown") for c in cluster})
        lines.append(
            f"- 同一事件获得 {len(cluster)} 个来源报道（{ '、'.join(origins) }）："
        )
        for c in cluster:
            lines.append(f"  - [{c.get('title','')}]({_item_url(c)})（{c.get('origin','')}）")
    lines.append("")

    lines.append("## 事实边界")
    lines.append("")
    lines.append(
        f"- 本次研究仅使用 collect 阶段证据池（aihot {pool_sizes[0]} 条，"
        f"rss {pool_sizes[1]} 条），未联网补充。"
    )
    lines.append("- 数字与表述以上述来源为准；没有来源的数字一律不写。")
    lines.append("- 证据不足的问题已单独列出，draft 阶段不得为其补充臆测事实。")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run(run_paths, ensure_evidence=None, force: bool = False) -> dict:
    """Generate or resume research for the chosen topic.

    ``ensure_evidence`` (optional callable) is invoked only when the
    evidence pool is missing entirely; resume and regeneration from an
    existing pool never call it and never bump ``collect_runs``.
    """
    topic = topics.require_choice(run_paths)
    md_path = run_paths.work_dir / RESEARCH_MD
    json_path = run_paths.work_dir / RESEARCH_JSON

    if md_path.exists() and json_path.exists() and not force:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return {
            "status": "resumed",
            "research_md": md_path,
            "research_json": json_path,
            "questions": data["questions"],
        }

    items = load_evidence(run_paths)
    if not items:
        if ensure_evidence is None:
            # Record the refusal durably before raising so the run shows
            # WHY research stopped (stage_log + last_error), not just that
            # it stopped.
            state.fail(run_paths, "research", _NO_EVIDENCE_MESSAGE)
            raise ResearchError(_NO_EVIDENCE_MESSAGE)
        try:
            ensure_evidence()
        except Exception as exc:
            # A failed collection is recorded in state and never counted;
            # the next run may retry honestly.
            state.fail(run_paths, "research", f"evidence collection failed: {exc}")
            raise ResearchError(f"evidence collection failed: {exc}") from exc
        state.bump_counter(run_paths, "collect_runs")
        items = load_evidence(run_paths)
        if not items:
            state.fail(run_paths, "research", "collection produced no evidence items")
            raise ResearchError("collection produced no evidence items")

    topic_title = topic.get("title", "")
    questions = []
    for query in topic.get("research_queries") or [topic["title"]]:
        evidence_items = match_evidence(query, items, topic_title)
        evidence = [
            {
                "title": it.get("title", ""),
                "url": _item_url(it),
                "origin": it.get("origin", ""),
                "excerpt": evidence_excerpt(it.get("summary", ""), it.get("title", "")),
            }
            for it in evidence_items
            if _item_url(it)
        ]
        questions.append(
            {
                "query": query,
                "status": "supported" if evidence else "insufficient",
                "evidence": evidence,
            }
        )

    notes = cross_validation_notes(items)
    aihot_count = sum(1 for it in items if it.get("origin") == "aihot")
    rss_count = len(items) - aihot_count

    data = {
        "run_id": run_paths.run_id,
        "date": run_paths.date,
        "topic_title": topic["title"],
        "slug": topic.get("slug", ""),
        "questions": questions,
        "cross_validation": [
            [{"title": c.get("title", ""), "url": _item_url(c),
              "origin": c.get("origin", "")} for c in cluster]
            for cluster in notes
        ],
        "evidence_urls": sorted({_item_url(it) for it in items if _item_url(it)}),
    }
    md_path.write_text(
        _render_md(run_paths, topic, questions, notes, (aihot_count, rss_count)),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    state.record_artifact(run_paths, "research", str(md_path.relative_to(run_paths.root)))
    # Recovering from an earlier failed run clears the recorded error.
    if state.read_state(run_paths).get("last_error"):
        state.clear_error(run_paths)
    return {
        "status": "generated",
        "research_md": md_path,
        "research_json": json_path,
        "questions": questions,
    }


# ---------------------------------------------------------------------------
# V2 Initial Research (active search -> seven-module OSINT profile)
#
# The V2 path is opt-in (``run_initial`` / ``pipeline.run_initial_research``
# / ``cli research --mode live``); the V1 ``run()`` above stays untouched
# for the closed-pool fixture tests.  Everything network-shaped is
# injectable (``aihot_fetch``, ``http_fetcher``, ``cdp_runner``,
# ``discover_runner``, ``codex_runner``) so tests never touch the real
# network, browser, or Codex CLI.  Missing data is recorded honestly as
# ``unavailable`` / ``无`` — nothing is fabricated or force-attached.
# ---------------------------------------------------------------------------

INITIAL_MODULES = [
    {
        "key": "core_timeline",
        "title": "核心事实与时间线",
        "keywords": (
            "发布", "上线", "推出", "宣布", "公告", "版本", "日期", "时间",
            "milestone", "launch", "release", "announce", "timeline", "roadmap",
        ),
    },
    {
        "key": "finance_capital",
        "title": "财务与资本账本",
        "keywords": (
            "融资", "估值", "收入", "营收", "利润", "亏损", "成本", "价格",
            "定价", "计费", "预算", "资本", "财报", "采购",
            "funding", "valuation", "revenue", "pricing", "budget", "capex",
        ),
    },
    {
        "key": "tech_engineering",
        "title": "技术架构与工程实锤",
        "keywords": (
            "架构", "工程", "代码", "开源", "权重", "模型", "训练", "推理",
            "基准", "评测", "排行榜", "部署", "论文", "智能体", "拉取请求", "门控",
            "architecture", "engineering", "benchmark", "training", "inference",
            "deploy", "weights", "api", "paper",
        ),
    },
    {
        "key": "ecosystem_moat",
        "title": "生态博弈与护城河",
        "keywords": (
            "生态", "竞争", "对手", "护城河", "平台", "绑定", "替代", "市场",
            "份额", "兼容", "标准", "独占",
            "ecosystem", "competitor", "moat", "platform", "lock", "share",
        ),
    },
    {
        "key": "community_voices",
        "title": "社区原声与野生实操",
        "keywords": (
            "社区", "用户", "开发者", "反馈", "实测", "体验", "吐槽", "教程",
            "测评", "知乎", "网友", "评论",
            "reddit", "zhihu", "feedback", "workflow",
        ),
    },
    {
        "key": "org_people",
        "title": "组织动荡与人事",
        "keywords": (
            "人事", "离职", "加入", "高管", "团队", "组织", "裁员", "招聘",
            "创始人",
            "ceo", "hire", "resign", "layoff", "executive", "founder",
        ),
    },
    {
        "key": "editor_direction_check",
        "title": "主编定向指令核查",
        "keywords": (),  # derived from the chosen topic's direction at runtime
    },
]

_MODULE_KEYWORDS = {spec["key"]: tuple(spec["keywords"]) for spec in INITIAL_MODULES}
_ASCII_KW_CACHE: dict = {}


def _module_score(text: str, keywords) -> int:
    """Keyword-hit score of one text against one module's keyword list."""
    score = 0
    low = (text or "").lower()
    for kw in keywords or ():
        if kw.isascii():
            if kw not in _ASCII_KW_CACHE:
                _ASCII_KW_CACHE[kw] = re.compile(
                    r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"
                )
            if _ASCII_KW_CACHE[kw].search(low):
                score += 1
        elif kw in (text or ""):
            score += 1
    return score


def _module_specs(topic: dict) -> list:
    """(key, title, keywords) triples; direction keywords are derived."""
    direction = topic.get("direction", "") or ""
    specs = []
    for spec in INITIAL_MODULES:
        keywords = list(_MODULE_KEYWORDS[spec["key"]])
        if spec["key"] == "editor_direction_check":
            keywords = sorted(_ascii_tokens(direction)) + sorted(_cjk_bigrams(direction))
        specs.append((spec["key"], spec["title"], keywords))
    return specs


def _module_keys_for(evidence: dict, specs: list) -> list:
    """Deterministic bucketing: every module with keyword hits keeps the item.

    One evidence item may support several modules (release pages are
    simultaneously timeline, financial and engineering facts), so it is
    assigned to every matching module — data is never compressed into a
    single bucket.  Items matching nothing go to ``unclassified``.
    """
    text = f"{evidence.get('title', '')} {evidence.get('excerpt', '')}"
    keys = []
    for key, _, keywords in specs:
        score = _module_score(text, keywords)
        if score > 0:
            keys.append(key)
    return keys or ["unclassified"]


def _evidence_view(ev: dict) -> dict:
    """Compact module-scoped view of one fetched evidence item."""
    return {
        "title": ev.get("title", ""),
        "url": ev.get("url", ""),
        "status": ev.get("status", ""),
        "source_lane": ev.get("source_lane", ""),
        "sha256": ev.get("sha256", ""),
        "excerpt": ev.get("excerpt", ""),
    }


def _excerpt_with_flag(markdown: str, title: str, limit: int = 300) -> tuple:
    """First ~limit chars cut at a complete sentence boundary.

    Returns ``(excerpt, truncated)``.  ``truncated`` is True when the
    source continues past the excerpt, so downstream writers know the
    material is incomplete and must never quote it as a full sentence.
    """
    text = normalize_evidence_text(markdown)
    if not text:
        return normalize_evidence_text(title), False
    if len(text) <= limit:
        return text, False
    window = text[:limit]
    last_end = 0
    for m in _SENTENCE_END_RE.finditer(window):
        last_end = m.end()
    if last_end:
        return window[:last_end].strip(), True
    # No sentence end inside the window: extend to the next one so the
    # excerpt still closes a sentence instead of cutting mid-phrase.
    m = _SENTENCE_END_RE.search(text, limit, limit + 500)
    if m:
        return text[: m.end()].strip(), True
    return window.strip(), True


def _evidence_excerpt(markdown: str, title: str, limit: int = 300) -> str:
    """First ~limit chars of normalized markdown, cut at a complete
    sentence boundary; title stands in when empty."""
    excerpt, _ = _excerpt_with_flag(markdown, title, limit=limit)
    return excerpt


def _evidence_entry(result) -> dict:
    excerpt, truncated = _excerpt_with_flag(result.markdown, result.title)
    return {
        "url": result.url,
        "title": result.title,
        "status": result.status,
        "source_lane": result.source_lane,
        "sha256": result.sha256,
        "error": result.error,
        "fetched_at": result.fetched_at,
        "excerpt": excerpt,
        "excerpt_truncated": truncated,
    }


def _initial_url_list(topic: dict, matrix: dict, discover_runner=None) -> list:
    """Initial search-evidence URL list for one run.

    Story reports' ``original_url`` values are the mandatory seed;
    ``discover_runner`` (the zhida discovery lane) optionally adds
    query-driven URLs and is only exercised when injected, so tests
    never touch the browser.
    """
    urls, seen = [], set()

    def add(url):
        url = (url or "").strip()
        if url.startswith("http") and url not in seen:
            seen.add(url)
            urls.append(url)

    for report in matrix.get("reports") or []:
        add(report.get("original_url") or "")
    if not urls:
        # Board rotation can leave the matrix without reports; the editor's
        # chosen sources still carry fetchable original URLs.
        for source in topic.get("sources") or []:
            if isinstance(source, dict):
                add(source.get("url") or "")
    if discover_runner is not None:
        for query in topic.get("research_queries") or []:
            for link in fetch.discover(query, runner=discover_runner) or []:
                if isinstance(link, dict):
                    add(link.get("url") or "")
    return urls


def _build_osint_base(topic: dict, matrix: dict, evidence: list) -> tuple:
    """Seven-module base archive + evidence gaps (honest, never fabricated)."""
    specs = _module_specs(topic)
    bucket = {}
    for ev in evidence:
        for key in _module_keys_for(ev, specs):
            bucket.setdefault(key, []).append(_evidence_view(ev))

    modules = []
    for key, title, _ in specs:
        evs = bucket.get(key, [])
        modules.append(
            {
                "key": key,
                "title": title,
                "summary": "无" if not evs else "（已采集证据，待分析）",
                "evidence": evs,
                "gaps": [],
            }
        )
    unclassified = bucket.get("unclassified", [])
    modules.append(
        {
            "key": "unclassified",
            "title": "未归类线索",
            "summary": "无" if not unclassified else "（已采集证据，待分析）",
            "evidence": unclassified,
            "gaps": [],
        }
    )

    gaps = [str(g) for g in (topic.get("evidence_gaps") or []) if str(g)]
    if matrix.get("status") != "ok":
        gaps.append(
            f"AIHOT story matrix unavailable: "
            f"{matrix.get('reason') or matrix.get('status')}"
        )
    for mod in modules:
        if mod["key"] == "unclassified":
            continue
        if not mod["evidence"]:
            gaps.append(f"模块「{mod['title']}」暂无证据")
    for ev in evidence:
        if ev.get("status") != "fetched":
            gaps.append(
                f"{ev.get('url')} 抓取{ev.get('status')}: "
                f"{ev.get('error') or '无错误信息'}"
            )
    return modules, gaps


def _codex_prompt(topic: dict, matrix: dict, evidence: list) -> str:
    """Self-contained analysis prompt built from the saved input files."""
    compact = [
        {
            "url": ev.get("url", ""),
            "title": ev.get("title", ""),
            "status": ev.get("status", ""),
            "excerpt": ev.get("excerpt", ""),
        }
        for ev in evidence
    ]
    keys = "、".join(m["key"] for m in INITIAL_MODULES)
    now = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y年%m月%d日")
    return (
        "你是 OSINT 情报分析师。基于给定的 AIHOT story matrix 与抓取证据，"
        "生成七模块情报档案：核心事实与时间线、财务与资本账本、技术架构与工程实锤、"
        "生态博弈与护城河、社区原声与野生实操、组织动荡与人事、主编定向指令核查。\n\n"
        "【研究契约】（编译自 knowledge/research-contract.md 核心 IP）\n"
        + _RESEARCH_CONTRACT + "\n"
        "【时间红线】\n"
        f"当前系统时间是：{now}。\n"
        "1. 提取任何产品发布、算力售罄、财报数据、高管离职时，必须严格核对原文中的具体时间。\n"
        "2. 严禁将不同时间线的事件强行因果缝合。\n"
        "3. 如果原文没有明确说明“X月发生了Y”，必须标注为“[时间未披露]”，绝对禁止脑补月份和日期！\n\n"
        "【提取纪律】\n"
        "1. 数据零压缩：不要把“1.2亿美元”总结为“巨额资金”，保留原始数字、API 定价、Token 限制。\n"
        "2. 微观场景：去知乎/X/Reddit 找开发者实际怎么用、怎么骂，提取具体场景与原话。\n"
        "3. 剥离公关话术：跳过“致力于、赋能、革命性”，只看发布了什么接口、砍了什么功能、收了多少钱。\n"
        "4. 禁止 AI 味：严禁出现“不可否认、总而言之、标志着、具有深远意义”。\n\n"
        "约束：只引用证据中出现的 URL；证据不足的模块 summary 写\"无\"，不脑补；"
        "输出必须是单个 JSON 对象："
        "{\"modules\":[{\"key\":\"...\",\"summary\":\"...\",\"gaps\":[...]}],"
        "\"evidence_gaps\":[...]}。"
        "禁止输出任何前言、解释、Markdown 代码块或尾注，只输出这一个 JSON 对象。"
        f"modules[].key 只能取：{keys}。\n"
        f"选题方向（原样保留）：{topic.get('direction') or ''}\n"
        f"选题的研究问题（逐条回答，答不上来记入 gaps）："
        f"{'；'.join(topic.get('research_queries') or [])}\n"
        f"story matrix：{json.dumps(matrix, ensure_ascii=False)}\n"
        f"抓取证据：{json.dumps(compact, ensure_ascii=False)}\n"
    )


# 编译自 knowledge/research-contract.md（源头：RES core_directives、
# UDW anti_hallucination_and_firewall、LCW 增量搜证目标）。
_RESEARCH_CONTRACT = (
    "1. 围绕关键问题：必须逐条回答选题的 research queries，不做泛泛摘要。\n"
    "2. 证据层级：一手来源（官方公告、论文、发布说明）优先于二手转述；"
    "AIHOT/RSS 摘要属于二手信号，引用时必须保留原始出处链接。\n"
    "3. 引用协议：每条重要事实必须带 [标题](URL) 形式的来源链接；"
    "没有链接的事实不得进入证据区。\n"
    "4. 冲突显式标注：来源互相矛盾时，明确写出冲突双方与各自链接，"
    "不得抹平分歧；冲突本身记为证据缺口。\n"
    "5. 不确定处理：无法充分支持的内容必须三选一——降低断言强度、"
    "标记为不确定、或直接删除。\n"
    "6. 零捏造：不得为了让档案完整而编造数字、引语、来源、实验结果；"
    "不得虚构数字、金额与硬件型号。\n"
    "7. 恢复语义：不得丢弃已采集的证据，缺什么就如实写进 evidence_gaps。\n"
    "8. 维度控制：输出维度数量服从选题要求，不注水、不超发。\n"
)


def _parse_jsonl_events(stdout: str) -> list:
    """Split ``codex exec --json`` stdout into its JSON object events.

    Non-JSON lines (logs, prompts, warnings) are ignored; each JSON
    object line becomes one event.
    """
    events = []
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def _codex_event_message_text(obj: dict) -> str:
    """Final assistant message text carried by a ``codex exec`` event."""
    for envelope_key in ("payload", "item"):
        payload = obj.get(envelope_key)
        if not isinstance(payload, dict):
            continue
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            return text
        content = payload.get("content")
        if isinstance(content, list):
            blocks = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") in ("output_text", "text", "message"):
                    value = block.get("text")
                    if isinstance(value, str):
                        blocks.append(value)
            if blocks:
                return "".join(blocks)
    for key in ("text", "message"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _decode_json_text(text: str):
    """Decode ``text`` as a JSON value, unwrapping one level of double encoding.

    Models sometimes prefix or suffix the required JSON with prose; when
    the whole message does not parse, the last balanced ``{...}`` object
    is retried so a valid payload inside prose still counts.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if parsed is None and isinstance(text, str):
        start = text.rfind("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                parsed = None
    if parsed is None:
        return None
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _parse_codex_exec_stdout(stdout: str) -> dict:
    """Parse ``codex exec --json`` output (JSONL event stream) into a dict.

    Non-JSON lines are ignored.  The last event carrying final assistant
    message text wins and its text is decoded when it is a JSON string;
    otherwise the last plain JSON object on stdout (legacy single-object
    output) is accepted.  Any other outcome returns
    ``{"status": "unavailable", "reason": ...}`` so a failed or unusable
    run is never reported as a completed analysis.
    """
    events = _parse_jsonl_events(stdout)

    for obj in events:
        if obj.get("type") == "run_error":
            payload = obj.get("payload")
            message = payload.get("message") if isinstance(payload, dict) else ""
            return {
                "status": "unavailable",
                "reason": f"codex exec run error: {message or obj}",
            }

    last_message = ""
    for obj in reversed(events):
        text = _codex_event_message_text(obj)
        if not text:
            continue
        last_message = text
        decoded = _decode_json_text(text)
        if decoded is not None:
            return decoded
        break

    # Legacy single-object output: the last JSON object without an event
    # type envelope is accepted as the result.
    for obj in reversed(events):
        if "type" not in obj:
            return obj

    if last_message:
        snippet = last_message if len(last_message) <= 360 else (
            last_message[:200] + " … " + last_message[-160:]
        )
        return {
            "status": "unavailable",
            "reason": f"codex exec final message is not JSON: {snippet}",
        }
    return {
        "status": "unavailable",
        "reason": "codex exec produced no usable JSON output",
    }


_CODEX_FALLBACK_PATHS = (
    "/Applications/ChatGPT.app/Contents/Resources/codex",
)


def _codex_binary() -> str:
    """Resolve the codex CLI on PATH, then known macOS install locations."""
    found = shutil.which("codex")
    if found:
        return found
    for candidate in _CODEX_FALLBACK_PATHS:
        if pathlib.Path(candidate).is_file():
            return candidate
    return "codex"


def _default_codex_runner(prompt: str) -> dict:
    """Run the local ``codex exec --json`` CLI; never raises.

    Any unavailability (missing binary, non-zero exit, non-JSON output)
    returns ``{"status": "unavailable", "reason": ...}`` so the run
    records the truth instead of pretending the analysis happened.
    """
    try:
        proc = subprocess.run(
            [_codex_binary(), "exec", "--json", prompt],
            capture_output=True,
            text=True,
            timeout=900,
        )
    except Exception as exc:
        return {
            "status": "unavailable",
            "reason": f"codex exec unavailable: {type(exc).__name__}: {exc}",
        }
    if proc.returncode != 0:
        return {
            "status": "unavailable",
            "reason": (
                f"codex exec exited {proc.returncode}: "
                f"{proc.stderr.strip()[:200]}"
            ),
        }
    result = _parse_codex_exec_stdout(proc.stdout)
    if result.get("status") == "unavailable":
        return result
    result.setdefault("status", "completed")
    return result


def _run_codex_analysis(run_paths, codex_runner, topic, matrix, evidence) -> dict:
    """Call the (injectable) analysis executor and normalize the result."""
    prompt = _codex_prompt(topic, matrix, evidence)
    runner = codex_runner or _default_codex_runner
    try:
        analysis = runner(prompt)
    except Exception as exc:
        return {
            "status": "unavailable",
            "reason": f"codex analysis failed: {type(exc).__name__}: {exc}",
        }
    if not isinstance(analysis, dict):
        return {
            "status": "unavailable",
            "reason": "codex analysis returned a non-object result",
        }
    return analysis


def _merge_analysis(modules: list, gaps: list, analysis: dict) -> None:
    """Merge a completed analysis into the base archive (best effort)."""
    analysis_modules = analysis.get("modules")
    if isinstance(analysis_modules, list):
        by_key = {
            m.get("key"): m for m in analysis_modules if isinstance(m, dict)
        }
        for mod in modules:
            merged = by_key.get(mod["key"])
            if not isinstance(merged, dict):
                continue
            # A module with no collected evidence stays "无" — analysis
            # may add gaps, but never fabricate a summary over nothing.
            if mod["evidence"]:
                summary = str(merged.get("summary") or "")
                if summary:
                    mod["summary"] = summary
            extra = merged.get("gaps")
            if isinstance(extra, list):
                for g in extra:
                    g = str(g)
                    if g and g not in mod["gaps"]:
                        mod["gaps"].append(g)
    extra = analysis.get("evidence_gaps")
    if isinstance(extra, list):
        for g in extra:
            g = str(g)
            if g and g not in gaps:
                gaps.append(g)


def _render_initial_md(
    run_paths, topic, matrix, modules, gaps, evidence,
    analysis_status, analysis_reason,
) -> str:
    lines = [f"# Initial OSINT：{topic['title']}", ""]
    lines.append(f"- run: {run_paths.run_id}")
    lines.append(f"- date: {run_paths.date}")
    lines.append(f"- slug: {topic.get('slug', '')}")
    lines.append(f"- analysis_status: {analysis_status}")
    if analysis_reason:
        lines.append(f"- analysis_reason: {analysis_reason}")
    lines.append(f"- story_matrix: {matrix.get('status', 'unavailable')}")
    if matrix.get("status") != "ok":
        lines.append(f"- story_matrix_reason: {matrix.get('reason', '')}")
    if topic.get("direction"):
        lines.append(f"- 编辑方向（原样保留）: {topic['direction']}")
    lines.append("")

    lines.append("## AIHOT 报道矩阵")
    lines.append("")
    if matrix.get("status") == "ok":
        lines.append(f"- story_id: {matrix.get('story_id', '')}")
        lines.append(f"- story_title: {matrix.get('story_title', '')}")
        lines.append(f"- story_status: {matrix.get('story_status', '')}")
        lines.append(
            f"- source_count: {matrix.get('source_count', 0)} / "
            f"report_count: {matrix.get('report_count', 0)}"
        )
        if matrix.get("story_digest"):
            lines.append(f"- digest: {matrix['story_digest'][:200]}")
        if matrix.get("story_latest"):
            lines.append(f"- latest: {matrix['story_latest'][:200]}")
        lines.append("- 报告：")
        for report in matrix.get("reports") or []:
            url = report.get("original_url") or report.get("aihot_url") or ""
            party = "一手" if report.get("first_party") else "二手"
            lines.append(
                f"  - [{report.get('title', '')}]({url})"
                f"（{report.get('source_name', '')}，{party}）"
            )
    else:
        lines.append(f"- status: {matrix.get('status', 'unavailable')}")
        lines.append(f"- reason: {matrix.get('reason', '')}")
    lines.append("")

    lines.append("## 七模块情报档案")
    lines.append("")
    for index, mod in enumerate(modules, 1):
        lines.append(f"### {index}. {mod['title']}")
        lines.append("")
        lines.append(f"- 摘要：{mod['summary']}")
        if mod["evidence"]:
            lines.append("- 证据：")
            for ev in mod["evidence"]:
                lines.append(
                    f"  - [{ev['title']}]({ev['url']})"
                    f"（status={ev['status']}，lane={ev['source_lane']}，"
                    f"sha256={ev['sha256'][:12]}）"
                )
        else:
            lines.append("- 证据：无")
        if mod["gaps"]:
            lines.append("- 模块缺口：")
            for gap in mod["gaps"]:
                lines.append(f"  - {gap}")
        lines.append("")

    lines.append("## 证据缺口")
    lines.append("")
    if not gaps:
        lines.append("- （无）")
    for gap in gaps:
        lines.append(f"- {gap}")
    lines.append("")

    lines.append("## 来源与抓取状态")
    lines.append("")
    if not evidence:
        lines.append("- （无：本次没有可抓取的初始搜证 URL）")
    for ev in evidence:
        error = f"，error={ev.get('error')}" if ev.get("error") else ""
        lines.append(
            f"- [{ev['title']}]({ev['url']})"
            f"（status={ev['status']}，lane={ev['source_lane']}，"
            f"sha256={ev.get('sha256', '')[:12]}{error}）"
        )
    lines.append("")
    lines.append("## 事实边界")
    lines.append("")
    lines.append("- 本档案仅收录真实抓取的来源与 AIHOT story reports；引用 URL 均来自上述来源。")
    lines.append("- 证据不足的模块写“无”，不脑补；抓取失败显式记录 failed/partial/login_required/unavailable。")
    lines.append("- 七模块分析摘要只有在 Codex 分析完成后才替换占位文案，analysis_status 如实记录。")
    lines.append("")
    return "\n".join(lines)


def run_initial(
    run_paths,
    aihot_fetch=None,
    http_fetcher=None,
    cdp_runner=None,
    discover_runner=None,
    codex_runner=None,
    progress=None,
    force: bool = False,
    timeout: float = 30.0,
) -> dict:
    """V2 initial research: story matrix + active search + OSINT archive.

    Every network-shaped dependency is injectable (``aihot_fetch``,
    ``http_fetcher``, ``cdp_runner``, ``discover_runner``,
    ``codex_runner``); the default codex runner shells out to
    ``codex exec --json`` only when no runner is injected.  When the
    matrix or the analysis is unavailable the run still writes the
    artifacts and records ``unavailable`` with a reason — it never
    pretends the search or the analysis succeeded.
    """
    topic = topics.require_choice(run_paths)
    run_paths.ensure_work_dir()
    json_path = run_paths.work_dir / INITIAL_OSINT_JSON
    md_path = run_paths.work_dir / INITIAL_OSINT_MD

    if json_path.exists() and md_path.exists() and not force:
        # A same-day archive belongs to this run only when it records this
        # topic.  A leftover archive for another topic is stale and must be
        # regenerated, never silently resumed into the wrong topic.
        try:
            stored = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stored = {}
        if stored.get("topic_title") == topic.get("title"):
            return {
                "status": "resumed",
                "research_md": md_path,
                "research_json": json_path,
                "analysis_status": "resumed",
            }
        # fall through and regenerate for the current topic

    matrix = aihot.story_matrix_for_topic(
        topic["title"],
        fetch=aihot_fetch,
        timeout=timeout,
        source_urls=[
            s.get("url")
            for s in (topic.get("sources") or [])
            if isinstance(s, dict) and s.get("url")
        ],
    )
    matrix_path = run_paths.work_dir / STORY_MATRIX_JSON
    matrix_path.write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if progress:
        progress("matrix", matrix)

    evidence = []
    for url in _initial_url_list(topic, matrix, discover_runner):
        result = fetch.fetch(
            url,
            run_paths,
            http_fetcher=http_fetcher,
            cdp_runner=cdp_runner,
        )
        evidence.append(_evidence_entry(result))
    if progress:
        progress("evidence", evidence)

    evidence_path = run_paths.work_dir / INITIAL_EVIDENCE_JSON
    evidence_path.write_text(
        json.dumps(
            {
                "topic": {
                    "title": topic["title"],
                    "slug": topic.get("slug", ""),
                    "direction": topic.get("direction", ""),
                },
                "research_queries": topic.get("research_queries") or [],
                "story_matrix": matrix,
                "sources": evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    modules, gaps = _build_osint_base(topic, matrix, evidence)
    if progress:
        progress("analysis_start", {})
    analysis = _run_codex_analysis(run_paths, codex_runner, topic, matrix, evidence)
    analysis_status = analysis.get("status", "unavailable")
    analysis_reason = analysis.get("reason", "")
    if progress:
        progress("analysis_done", {"status": analysis_status, "reason": analysis_reason})
    if analysis_status == "completed":
        _merge_analysis(modules, gaps, analysis)

    data = {
        "run_id": run_paths.run_id,
        "date": run_paths.date,
        "topic_title": topic["title"],
        "slug": topic.get("slug", ""),
        "analysis_status": analysis_status,
        "analysis_reason": analysis_reason,
        "story_matrix": matrix,
        "modules": modules,
        "evidence_gaps": gaps,
        "research_queries": topic.get("research_queries") or [],
        "sources": evidence,
    }
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        _render_initial_md(
            run_paths, topic, matrix, modules, gaps, evidence,
            analysis_status, analysis_reason,
        ),
        encoding="utf-8",
    )

    state.record_artifact(
        run_paths, "initial-research", str(md_path.relative_to(run_paths.root))
    )
    if state.read_state(run_paths).get("last_error"):
        state.clear_error(run_paths)
    return {
        "status": "generated",
        "research_md": md_path,
        "research_json": json_path,
        "story_matrix": matrix_path,
        "evidence": evidence_path,
        "analysis_status": analysis_status,
        "matrix_status": matrix.get("status", "unavailable"),
        "fetched": len(evidence),
        "modules": [m["key"] for m in modules],
        "evidence_gaps": gaps,
    }

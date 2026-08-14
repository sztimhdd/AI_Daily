"""Topic candidate generation and the human topic gate.

Candidates are generated from the merged AIHOT + RSS item pool.  Same
event coverage is clustered first (a story reported by AIHOT and one or
more RSS feeds counts once).  Ranking is editorial, not popularity-based:
strategic relevance for enterprise/architecture/engineering readers
outranks raw hotness.  Exactly three rich candidates are produced, or
``TopicError`` is raised when fewer than three distinct events exist.
"""

from __future__ import annotations

import json
import pathlib
import re
import unicodedata

from . import state

CANDIDATE_COUNT = 3

REQUIRED_FIELDS = (
    "title",
    "thesis",
    "hook",
    "evidence_gaps",
    "research_queries",
    "strategic_relevance",
    "sources",
)


class TopicError(RuntimeError):
    """Raised when candidate generation or a human choice is invalid."""


class TopicGateBlocked(RuntimeError):
    """Raised when a later stage is attempted without a topic choice."""


# ---------------------------------------------------------------------------
# Title normalization and event clustering
# ---------------------------------------------------------------------------

_ASCII_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9.+#-]*")
_STOP_TOKENS = {"ai", "the", "a", "an", "of", "for", "and", "to", "vs", "how", "why"}

# Vocabulary that appears across unrelated stories; it must never count
# toward the two-shared-token merge rule (false-merge guard).
GENERIC_TOKENS = {
    "api", "app", "sdk", "cli", "ui", "saas", "llm", "gpu", "cpu",
    "new", "pro", "max", "plus", "ultra", "mini", "beta", "update",
    "release", "launch", "web", "com", "www", "http", "https",
}

CJK_BIGRAM_THRESHOLD = 0.8
MIXED_BIGRAM_THRESHOLD = 0.85


def normalize_title(title: str) -> str:
    """Lowercase, NFKC-fold and strip whitespace/punctuation for comparison."""
    t = unicodedata.normalize("NFKC", title or "").lower()
    t = re.sub(r"[\s\u3000]+", "", t)
    t = re.sub(r"[^\w\u4e00-\u9fff.+#-]", "", t)
    return t


def _ascii_tokens(text: str) -> set:
    return {
        tok
        for tok in _ASCII_TOKEN_RE.findall((text or "").lower())
        if tok not in _STOP_TOKENS and tok not in GENERIC_TOKENS and len(tok) >= 2
    }


_DIGIT_RUN_RE = re.compile(r"\d+")


def _digit_runs(text: str) -> tuple:
    return tuple(_DIGIT_RUN_RE.findall(text or ""))


def _char_bigrams(title: str) -> set:
    t = normalize_title(title)
    return {t[i : i + 2] for i in range(len(t) - 1)} if len(t) >= 2 else set()


_HAS_ASCII_RE = re.compile(r"[a-zA-Z0-9]")


def same_event(title_a: str, title_b: str) -> bool:
    """Heuristic: same story when titles match, share 2+ non-generic
    ascii tokens, or share enough character bigrams.

    Bigram fallback rules:

    - Pure-CJK titles merge at >= 80% bigram overlap.
    - Mixed ascii+CJK titles may also merge (a reworded headline with
      one shared token is still one story), but only when their ascii
      identity is identical — same non-generic token set AND same digit
      runs — at a stricter >= 85% overlap.  This keeps numbered series
      ("...硬件 0" vs "...硬件 1", "Grok 4.5" vs "Grok 4.6") distinct
      instead of being merged by textual similarity.
    - Generic tokens (api, app, sdk, ...) never count toward the
      two-token merge rule, so unrelated product stories do not merge.
    """
    if not title_a or not title_b:
        return False
    if normalize_title(title_a) == normalize_title(title_b):
        return True
    shared = _ascii_tokens(title_a) & _ascii_tokens(title_b)
    if len(shared) >= 2:
        return True
    ga, gb = _char_bigrams(title_a), _char_bigrams(title_b)
    if not ga or not gb:
        return False
    overlap = len(ga & gb) / min(len(ga), len(gb))
    mixed = bool(_HAS_ASCII_RE.search(title_a) or _HAS_ASCII_RE.search(title_b))
    if not mixed:
        return overlap >= CJK_BIGRAM_THRESHOLD
    if _ascii_tokens(title_a) != _ascii_tokens(title_b):
        return False
    if _digit_runs(title_a) != _digit_runs(title_b):
        return False
    return overlap >= MIXED_BIGRAM_THRESHOLD


# ---------------------------------------------------------------------------
# Strategic relevance scoring (editorial, deterministic)
# ---------------------------------------------------------------------------

COST_KEYWORDS = ("价格", "定价", "计费", "成本", "预算", "费用", "企业", "采购")
DEPLOY_KEYWORDS = ("部署", "上线", "生产环境", "落地")
OPEN_KEYWORDS = ("开源", "权重", "许可证", "开放")
ENGINEERING_KEYWORDS = (
    "智能体",
    "agent",
    "工作流",
    "拉取请求",
    "pr",
    "ci",
    "测试",
    "门控",
    "基准",
    "评测",
    "排行榜",
    "覆盖率",
)
INFRA_KEYWORDS = ("模型", "api", "token", "推理", "上下文", "发布", "搜索", "引擎")
ENTERTAINMENT_KEYWORDS = ("明星", "走红", "换脸", "娱乐", "短视频", "八卦", "网红")

_KEYWORD_WEIGHTS: dict = {}
_KEYWORD_WEIGHTS.update({kw: 3 for kw in COST_KEYWORDS})
_KEYWORD_WEIGHTS.update({kw: 2 for kw in DEPLOY_KEYWORDS})
_KEYWORD_WEIGHTS.update({kw: 2 for kw in OPEN_KEYWORDS})
_KEYWORD_WEIGHTS.update({kw: 2 for kw in ENGINEERING_KEYWORDS})
# Engineering-governance signals are the strongest practice-level evidence.
_KEYWORD_WEIGHTS.update({kw: 3 for kw in ("门控", "拉取请求", "ci", "覆盖率")})
_KEYWORD_WEIGHTS.update(
    {kw: 1 for kw in INFRA_KEYWORDS if kw not in _KEYWORD_WEIGHTS}
)

_ASCII_KW_RE = {
    kw: re.compile(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])")
    for kw in _KEYWORD_WEIGHTS
    if kw.isascii()
}


def _matched_keywords(text: str) -> list:
    t = (text or "").lower()
    hits = []
    for kw, weight in _KEYWORD_WEIGHTS.items():
        if kw.isascii():
            if _ASCII_KW_RE[kw].search(t):
                hits.append(kw)
        elif kw in t:
            hits.append(kw)
    return hits


def strategic_score(title: str, summary: str, popularity: int) -> int:
    """Weighted strategic relevance plus capped popularity.

    Entertainment-only items are pushed to the bottom regardless of heat:
    popularity alone must never outrank decision-relevant events.
    """
    text = f"{title} {summary}"
    hits = _matched_keywords(text)
    score = sum(_KEYWORD_WEIGHTS[kw] for kw in hits) * 100
    score += max(0, min(int(popularity or 0), 100))
    entertainment_hits = [kw for kw in ENTERTAINMENT_KEYWORDS if kw in text]
    strong_hits = [kw for kw in hits if _KEYWORD_WEIGHTS[kw] >= 3]
    # Entertainment stories sink regardless of incidental strategic words
    # (e.g. "与企业决策无关" must not rescue a celebrity story) unless the
    # item also carries multiple strong decision-relevant signals.
    if len(entertainment_hits) >= 2 and len(strong_hits) < 2:
        score -= 10000
    return score


def _category(hit_keywords: list) -> str:
    hit = set(hit_keywords)
    if hit & set(COST_KEYWORDS):
        return "cost"
    if hit & {"门控", "拉取请求", "ci", "覆盖率", "测试", "工作流"}:
        return "engineering"
    if hit & set(OPEN_KEYWORDS):
        return "open-weights"
    if hit & {"基准", "评测", "排行榜", "搜索"}:
        return "benchmark"
    if hit & {"发布", "模型", "推理"}:
        return "release"
    return "general"


_HOOKS = {
    "cost": "反共识点：大家都盯着模型单价，真正的账单却藏在没人统计的调用次数里。",
    "engineering": "反共识点：限制 AI 产出的往往不是模型能力，而是团队敢给它开多大的口子。",
    "open-weights": "反共识点：开放权重不等于能自部署，真正的门槛在权重文件之外。",
    "benchmark": "反共识点：榜单分数和落地成本之间，隔着一条没人画出来的线。",
    "release": "反共识点：发布说明里的能力和你真正能用上的能力之间，还差一步验证。",
    "general": "反共识点：热度最高的解读，往往不是对决策最有用的那个。",
}

_RELEVANCE = {
    "cost": "直接影响企业 AI 预算、采购节奏与供应商选择。",
    "engineering": "直接改变工程团队管理 AI 产出的流程、门槛与验收方式。",
    "open-weights": "影响自部署可行性、许可证合规与供应商谈判筹码。",
    "benchmark": "为模型与工具选型提供可对照的评测坐标。",
    "release": "影响模型选型、能力边界评估与迁移计划。",
    "general": "影响技术决策者判断趋势轻重缓急的框架。",
}

_CATEGORY_QUERIES = {
    "cost": "成本 预算 定价 口径",
    "engineering": "工程实践 流程 门控 验收",
    "open-weights": "开源 权重 许可证 自部署",
    "benchmark": "基准测试 评测 成本 对比",
    "release": "发布 能力 评测 迁移",
    "general": "背景 影响 决策",
}


# ---------------------------------------------------------------------------
# Item pool handling
# ---------------------------------------------------------------------------


def _item_view(item: dict) -> dict:
    """Normalize AIHOT and RSS items into one shape for clustering."""
    origin = item.get("origin", "")
    if origin == "aihot":
        links = item.get("links") or {}
        url = links.get("original") or links.get("aihot") or ""
        popularity = int(item.get("score") or 0)
        source_name = item.get("source_name") or "AIHOT"
    else:
        url = item.get("url") or ""
        popularity = int(item.get("score") or 0)
        source_name = item.get("feed") or "rss"
    return {
        "title": (item.get("title") or "").strip(),
        "summary": (item.get("summary") or "").strip(),
        "url": url,
        "origin": origin or "unknown",
        "popularity": popularity,
        "source_name": source_name,
    }


def cluster_events(items: list) -> list:
    """Greedy clustering; returns clusters (lists of item views), stable order."""
    clusters: list = []
    for view in map(_item_view, items):
        if not view["title"]:
            continue
        for cluster in clusters:
            if same_event(view["title"], cluster[0]["title"]):
                cluster.append(view)
                break
        else:
            clusters.append([view])
    return clusters


# ---------------------------------------------------------------------------
# Candidate enrichment
# ---------------------------------------------------------------------------


def _first_sentence(text: str) -> str:
    for part in re.split(r"[。！？!?]", text or ""):
        part = part.strip()
        if part:
            return part
    return (text or "").strip()


def _slugify_title(title: str, date: str) -> str:
    ascii_runs = re.findall(r"[a-z0-9]+", (title or "").lower())
    slug = "-".join(ascii_runs)[:48].strip("-")
    if not slug:
        slug = f"topic-{date.replace('-', '')}"
    return slug


def _build_candidate(cluster: list, date: str) -> dict:
    ranked = sorted(
        cluster,
        key=lambda v: (-strategic_score(v["title"], v["summary"], v["popularity"]),
                       -v["popularity"],
                       v["title"]),
    )
    lead = ranked[0]
    text = f"{lead['title']} {lead['summary']}"
    hits = _matched_keywords(text)
    cat = _category(hits)
    n = len(cluster)

    thesis = _first_sentence(lead["summary"]) or lead["title"]
    if n > 1:
        thesis = f"{thesis}（{n} 个来源报道了同一事件）"

    # Gap wording must match the actual evidence: only clusters with a
    # single independent source may claim a second source is missing.
    independent_sources = len({(v["origin"], v["source_name"]) for v in cluster})
    if independent_sources > 1:
        gaps = [
            f"已有 {independent_sources} 个独立来源报道同一事件，"
            "数字与口径仍需 research 阶段交叉核对。"
        ]
    else:
        gaps = [
            "目前只有 1 个来源报道，缺少独立的第二来源验证。",
            "关键数字缺少官方口径或可复现来源，需要 research 阶段补齐。",
        ]

    queries = []
    ascii_tokens = sorted(_ascii_tokens(lead["title"]))
    if ascii_tokens:
        queries.append(" ".join(ascii_tokens[:6]))
    queries.append(_CATEGORY_QUERIES[cat])
    queries.append(lead["title"])

    sources = []
    seen_urls = set()
    for view in ranked:
        if view["url"] and view["url"] not in seen_urls:
            seen_urls.add(view["url"])
            sources.append(
                {"url": view["url"], "title": view["title"], "origin": view["origin"]}
            )

    return {
        "title": lead["title"],
        "slug": _slugify_title(lead["title"], date),
        "thesis": thesis,
        "hook": _HOOKS[cat],
        "evidence_gaps": gaps,
        "research_queries": queries,
        "strategic_relevance": _RELEVANCE[cat],
        "category": cat,
        "sources": sources,
    }


def generate_candidates(aihot_items: list, rss_items: list = None, date: str = "") -> list:
    """Exactly three rich candidates from the merged pool.

    Raises ``TopicError`` when fewer than three distinct events exist;
    honest failure is required instead of padding with weak angles.
    """
    rss_items = rss_items or []
    pool = list(aihot_items) + list(rss_items)
    clusters = cluster_events(pool)
    if len(clusters) < CANDIDATE_COUNT:
        raise TopicError(
            f"only {len(clusters)} distinct event(s) available; "
            f"need {CANDIDATE_COUNT} for an honest topic choice"
        )

    def cluster_key(cluster):
        best = max(
            strategic_score(v["title"], v["summary"], v["popularity"]) for v in cluster
        )
        pop = max(v["popularity"] for v in cluster)
        return (-best, -pop, cluster[0]["title"])

    clusters.sort(key=cluster_key)
    import datetime as _dt

    date = date or _dt.date.today().isoformat()
    return [_build_candidate(c, date) for c in clusters[:CANDIDATE_COUNT]]


# ---------------------------------------------------------------------------
# Markdown presentation
# ---------------------------------------------------------------------------


def candidates_markdown(date: str, candidates: list) -> str:
    lines = [f"# 选题候选（{date}）", ""]
    lines.append(f"> 共 {len(candidates)} 个候选。回复候选编号即可选定；可附加写作方向，将原样保留。")
    lines.append("")
    for i, cand in enumerate(candidates, 1):
        lines.append(f"## 候选 {i}：{cand['title']}")
        lines.append("")
        lines.append(f"- thesis：{cand['thesis']}")
        lines.append(f"- hook：{cand['hook']}")
        lines.append(f"- 战略相关性：{cand['strategic_relevance']}")
        lines.append("- 证据缺口：")
        for gap in cand["evidence_gaps"]:
            lines.append(f"  - {gap}")
        lines.append("- research queries：")
        for q in cand["research_queries"]:
            lines.append(f"  - {q}")
        lines.append("- 来源：")
        for src in cand["sources"]:
            lines.append(f"  - [{src['title']}]({src['url']})（{src['origin']}）")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Human gate: fixture bypass and verbatim human choice
# ---------------------------------------------------------------------------

_SELECTED_FILENAME = "selected-topic.json"


def _write_selected(run_paths, topic: dict) -> None:
    run_paths.ensure_work_dir()
    path = run_paths.work_dir / _SELECTED_FILENAME
    path.write_text(
        json.dumps(topic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def choose_fixture(run_paths, fixture_path) -> dict:
    """Deterministic bypass for unattended CLI/E2E runs.

    Unreadable or malformed fixtures raise ``TopicError`` — raw
    OSError/JSONDecodeError never escapes to callers.
    """
    path = pathlib.Path(fixture_path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TopicError(f"topic fixture unreadable: {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TopicError(f"topic fixture is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TopicError(f"topic fixture must be a JSON object: {path}")
    for key in ("title", "slug"):
        if not data.get(key):
            raise TopicError(f"topic fixture missing required field: {key}")
    topic = dict(data)
    _write_selected(run_paths, topic)
    state.update_fields(
        run_paths,
        note=f"topic choice: fixture ({topic['slug']})",
        topic_choice="fixture",
        slug=topic["slug"],
        topic_title=topic["title"],
    )
    return topic


def record_human_choice(run_paths, candidates: list, choice: int, direction: str = "") -> dict:
    """Record the editor's 1-based choice with direction kept verbatim."""
    if not isinstance(choice, int) or choice < 1 or choice > len(candidates):
        raise TopicError(
            f"choice {choice!r} out of range; expected 1..{len(candidates)}"
        )
    cand = dict(candidates[choice - 1])
    cand["direction"] = direction
    cand.setdefault("slug", _slugify_title(cand["title"], run_paths.date))
    _write_selected(run_paths, cand)
    state.update_fields(
        run_paths,
        note=f"topic choice: human (candidate {choice})",
        topic_choice="human",
        slug=cand["slug"],
        topic_title=cand["title"],
    )
    return cand


def require_choice(run_paths) -> dict:
    """Gate for research and later stages."""
    st = state.read_state(run_paths)
    selected = run_paths.work_dir / _SELECTED_FILENAME
    if not st.get("topic_choice") or not selected.exists():
        raise TopicGateBlocked(
            "topic_choice is a mandatory human gate; choose a topic "
            "(or use the fixture bypass) before research"
        )
    return json.loads(selected.read_text(encoding="utf-8"))

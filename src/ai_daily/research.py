"""Targeted research around the chosen topic's key questions.

Contract: knowledge/research-contract.md (compiled from the core IP).
V1 research runs over the collected evidence pool only — every cited URL
comes from that pool, unsupported questions are marked insufficient, and
resume never re-runs collection.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata

from . import state, topics

AIHOT_EVIDENCE = "aihot-items.json"
RSS_EVIDENCE = "rss-items.json"
RESEARCH_MD = "research.md"
RESEARCH_JSON = "research.json"
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


def match_evidence(query: str, items: list) -> list:
    scored = []
    for item in items:
        score = _match_score(query, item)
        if score >= 2:  # one shared ascii token, or two shared CJK bigrams
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("title", "")))
    return [item for _, item in scored[:MAX_EVIDENCE_PER_QUESTION]]


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

    questions = []
    for query in topic.get("research_queries") or [topic["title"]]:
        evidence_items = match_evidence(query, items)
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

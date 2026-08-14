"""Fact-backed first draft driven by outline + research.

Rules compiled from knowledge/author-style.md: news peg, nut graf, short
mobile paragraphs, bolded lead-ins, source links preserved, uncertainty
stated, cold kicker instead of uplift.  The finished article must pass
the executable remove-ai-slop contract (deslop) or the stage fails.

Outline sensitivity: section bullets map 1:1 to draft headings, and the
thesis line is quoted verbatim — so human outline edits change the draft
without any re-collection.
"""

from __future__ import annotations

import json

from . import deslop, outline, state, topics

ARTICLE_MD = "article.md"


class DraftError(RuntimeError):
    """Raised when drafting cannot proceed or violates the style contract."""


def _load(run_paths):
    outline_path = run_paths.work_dir / outline.OUTLINE_MD
    if not outline_path.exists():
        raise DraftError("article-outline.md missing; run the outline stage first")
    research_path = run_paths.work_dir / "research.json"
    if not research_path.exists():
        raise DraftError("research.json missing; run the research stage first")
    outline_text = outline_path.read_text(encoding="utf-8")
    data = json.loads(research_path.read_text(encoding="utf-8"))
    return outline_text, data


def _first_supported(data):
    for q in data["questions"]:
        if q["status"] == "supported" and q["evidence"]:
            return q["evidence"][0]
    return None


def _citation(ev) -> str:
    return f"[{ev['title']}]({ev['url']})"


def _short(text: str, limit: int = 48) -> str:
    """First clause, capped; keeps paragraphs mobile-short."""
    clause = text
    for sep in ("。", "！", "？", "，", "；", ","):
        idx = clause.find(sep)
        if 0 < idx < len(clause):
            clause = clause[:idx]
    if len(clause) > limit:
        clause = clause[:limit] + "…"
    return clause


def _peg_paragraphs(data) -> list:
    ev = _first_supported(data)
    if ev is None:
        return [
            "这次选题在证据池里没有直接命中的报道。能确认的只有事件本身，"
            "其余都要按不确定处理。"
        ]
    return [
        f"{_short(ev['excerpt'], 60)}。",
        f"出处：{_citation(ev)}。这是本次选题最硬的一条事实。",
    ]


def _nut_graf(outline_text, topic) -> str:
    thesis = outline.thesis(outline_text) or topic.get("thesis", topic["title"])
    direction = topic.get("direction", "")
    if direction:
        return f"{thesis} 编辑给的方向很明确：{direction}"
    return thesis


def _evidence_paragraphs(query, data) -> list:
    question = next((q for q in data["questions"] if q["query"] == query), None)
    if question is None:
        return ["这一节没有可引用的证据，只保留结构，不作事实陈述。"]
    if question["status"] != "supported":
        return [
            "这个问题，证据池里暂时没有可引用的来源。缺少公开口径，"
            "本文不作事实断言；等后续研究补上来源，再下判断。"
        ]
    ev1 = question["evidence"][0]
    paras = [
        f"**{query}** {_short(ev1['excerpt'])}。",
        f"出处：{_citation(ev1)}。",
    ]
    if len(question["evidence"]) > 1:
        ev2 = question["evidence"][1]
        paras.append(f"另一条佐证：{_short(ev2['excerpt'], 32)}（{_citation(ev2)}）。")
    return paras


def _kicker_paragraph(topic) -> str:
    gaps = topic.get("evidence_gaps") or []
    if gaps:
        return f"风险很具体：{gaps[0]} 数字以来源公告为准，口径对不上的地方按不确定处理。"
    return "风险很具体：证据池只有单一来源，独立验证还没出现，先别把话说满。"


def _section_paragraphs(bullet: str, topic, data, outline_text) -> list:
    if "导语" in bullet or "新闻钩子" in bullet:
        return _peg_paragraphs(data)
    if "核心" in bullet or "为什么" in bullet:
        return [_nut_graf(outline_text, topic)]
    if "风险" in bullet or "冷评" in bullet:
        return [_kicker_paragraph(topic)]
    for q in data["questions"]:
        if q["query"] and q["query"] in bullet:
            return _evidence_paragraphs(q["query"], data)
    ev = _first_supported(data)
    if ev is None:
        return ["这一节没有可引用的证据，只保留结构，不作事实陈述。"]
    return [
        f"**补充事实。** {_short(ev['excerpt'])}。",
        f"出处：{_citation(ev)}。",
    ]


def render(run_paths, topic: dict, outline_text: str, data: dict) -> str:
    lines = [f"# {outline.working_title(outline_text)}", ""]
    for bullet in outline.section_bullets(outline_text):
        lines.append(f"## {bullet}")
        lines.append("")
        for para in _section_paragraphs(bullet, topic, data, outline_text):
            lines.append(para)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(run_paths, force: bool = False) -> dict:
    topic = topics.require_choice(run_paths)
    article_path = run_paths.work_dir / ARTICLE_MD
    if article_path.exists() and not force:
        return {"status": "resumed", "article": article_path}

    outline_text, data = _load(run_paths)
    article = render(run_paths, topic, outline_text, data)

    findings = deslop.check_text(article)
    if findings:
        raise DraftError(
            "draft violates the remove-ai-slop contract:\n" + deslop.report(findings)
        )

    article_path.write_text(article, encoding="utf-8")
    state.record_artifact(
        run_paths, "article", str(article_path.relative_to(run_paths.root))
    )
    return {"status": "generated", "article": article_path}

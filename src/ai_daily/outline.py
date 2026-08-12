"""Editable article outline with the 8 spec-required fields.

The outline is the contract between research and draft: humans may edit
any section (especially 核心论点 and 章节结构 bullets) and the draft
stage must follow the edited file.  Bullets under 章节结构 map 1:1 to
draft headings.
"""

from __future__ import annotations

import json
import re

from . import state, topics

OUTLINE_MD = "article-outline.md"


class OutlineError(RuntimeError):
    """Raised when the outline cannot be produced."""


def _load_research(run_paths) -> dict:
    path = run_paths.work_dir / "research.json"
    if not path.exists():
        raise OutlineError("research.json missing; run the research stage first")
    return json.loads(path.read_text(encoding="utf-8"))


def _audience(topic: dict) -> str:
    return topic.get("audience") or "CTO、架构师与技术决策者（默认读者画像）"


def _tension(topic: dict, data: dict) -> str:
    insufficient = [q for q in data["questions"] if q["status"] == "insufficient"]
    base = f"编辑 thesis 说“{topic.get('thesis', topic['title'])}”，"
    if insufficient:
        base += (
            f"但证据池回答不了 {len(insufficient)} 个关键问题；"
            "文章要在证据够的地方下判断，在不够的地方明说不够。"
        )
    else:
        base += "证据池全部答上了；文章要把每个论断都压到来源上。"
    return base


def build(run_paths, topic: dict, data: dict) -> str:
    supported = [q for q in data["questions"] if q["status"] == "supported"]
    insufficient = [q for q in data["questions"] if q["status"] == "insufficient"]

    lines = [f"# 文章大纲：{topic['title']}", ""]

    lines.append("## 工作标题")
    lines.append("")
    lines.append(topic["title"])
    lines.append("")

    lines.append("## 目标读者")
    lines.append("")
    lines.append(_audience(topic))
    lines.append("")

    lines.append("## 核心论点")
    lines.append("")
    lines.append(topic.get("thesis") or topic["title"])
    if topic.get("direction"):
        lines.append(f"编辑方向（原样保留）：{topic['direction']}")
    lines.append("")

    lines.append("## 矛盾")
    lines.append("")
    lines.append(_tension(topic, data))
    lines.append("")

    lines.append("## 章节结构")
    lines.append("")
    lines.append("- 导语·新闻钩子：最近发生的硬事实")
    lines.append("- 核心·为什么是现在：把事件抬到成本与决策层面")
    for i, q in enumerate(supported, 1):
        lines.append(f"- 拆解 {i}·{q['query']}：证据与口径")
    lines.append("- 风险冷评：给读者的具体警告")
    lines.append("")

    lines.append("## 关键事实")
    lines.append("")
    facts = 0
    for q in supported:
        for ev in q["evidence"]:
            if facts >= 6:
                break
            lines.append(f"- {ev['excerpt']}（[{ev['title']}]({ev['url']})）")
            facts += 1
    if facts == 0:
        lines.append("- （无：证据池没有可引用的支持性事实）")
    lines.append("")

    lines.append("## 事实边界")
    lines.append("")
    lines.append(
        f"- 证据池共 {len(data.get('evidence_urls', []))} 个来源 URL；"
        "文章只能引用其中出现过的链接与数字。"
    )
    lines.append("- 没有来源的数字、引语、实验结果一律不写。")
    if insufficient:
        lines.append(
            f"- {len(insufficient)} 个关键问题证据不足，只能以不确定口径提及。"
        )
    lines.append("")

    lines.append("## 不应声称")
    lines.append("")
    for q in insufficient:
        lines.append(f"- 不得把“{q['query']}”当作已证实的事实陈述。")
    lines.append("- 不得声称作者亲自测试、验证或采访了任何对象。")
    lines.append("- 不得对未来下确定性结论（必将、注定等）。")
    lines.append("")

    return "\n".join(lines)


def run(run_paths, force: bool = False) -> dict:
    topic = topics.require_choice(run_paths)
    path = run_paths.work_dir / OUTLINE_MD
    if path.exists() and not force:
        return {"status": "resumed", "outline": path}
    data = _load_research(run_paths)
    path.write_text(build(run_paths, topic, data), encoding="utf-8")
    state.record_artifact(
        run_paths, "outline", str(path.relative_to(run_paths.root))
    )
    return {"status": "generated", "outline": path}


# ---------------------------------------------------------------------------
# Parsing helpers shared with the draft stage
# ---------------------------------------------------------------------------


def parse(text: str) -> dict:
    """Split an outline into its sections (editable by humans)."""
    sections: dict = {}
    current = None
    for raw in text.splitlines():
        if raw.startswith("## "):
            current = raw[3:].strip()
            sections[current] = []
            continue
        if current is not None and raw.strip():
            sections[current].append(raw.strip())
    return sections


def working_title(text: str) -> str:
    sec = parse(text)
    for line in sec.get("工作标题", []):
        return line.strip()
    raise OutlineError("outline has no 工作标题")


def section_bullets(text: str) -> list:
    sec = parse(text)
    bullets = []
    for line in sec.get("章节结构", []):
        m = re.match(r"^[-*]\s+(.+)$", line)
        if m:
            bullets.append(m.group(1).strip())
    return bullets


def thesis(text: str) -> str:
    sec = parse(text)
    for line in sec.get("核心论点", []):
        return line.strip()
    return ""

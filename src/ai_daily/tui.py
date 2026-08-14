"""Pure-text TUI rendering and terminal input for the CLI.

No third-party dependencies: ANSI escapes, ``print`` and ``input`` only.
Every render function accepts ``color: bool``; when False the output is
plain text with no escape sequences, so tests assert stable output.
This module depends on nothing but the stage constants — not on the
pipeline or run state — so it stays easy to unit test.
"""

from __future__ import annotations

import sys

from . import STAGES

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
DIM = "\033[2m"

DONE_MARK = "\u2713"      # ✓
CURRENT_MARK = "\u2192"   # →


def supports_color(stream=None) -> bool:
    """True when ``stream`` is a real terminal (default: sys.stdout)."""
    if stream is None:
        stream = sys.stdout
    isatty = getattr(stream, "isatty", None)
    return bool(isatty and isatty())


def render_progress(stage: str, stages: list = None, color: bool = False) -> str:
    """Render the stage checklist around the current ``stage``.

    Completed stages (those before ``stage`` in the sequence) get a
    check mark, the current stage gets an arrow and is highlighted, and
    later stages are dimmed (color) or left with a blank mark slot
    (plain).  An unknown ``stage`` falls back to a plain listing of all
    stages without marks — it never raises.
    """
    if stages is None:
        stages = STAGES
    if stage not in stages:
        return "\n".join(stages)
    index = stages.index(stage)
    lines = []
    for i, name in enumerate(stages):
        if i < index:
            mark = f"{DONE_MARK} "
            if color:
                line = f"{GREEN}{mark}{RESET}{name}"
            else:
                line = f"{mark}{name}"
        elif i == index:
            mark = f"{CURRENT_MARK} "
            if color:
                line = f"{BOLD}{mark}{name}{RESET}"
            else:
                line = f"{mark}{name}"
        else:
            mark = "  "
            if color:
                line = f"{DIM}{mark}{name}{RESET}"
            else:
                line = f"{mark}{name}"
        lines.append(line)
    return "\n".join(lines)


def render_candidates(candidates: list, color: bool = False) -> str:
    """Render one numbered candidate block per entry.

    Each block leads with ``N. {title}``; thesis, hook and strategic
    relevance follow indented.  Evidence gaps are summarized for
    readability; research queries and source links are omitted (they
    stay in the markdown view).
    """
    blocks = []
    for i, cand in enumerate(candidates, 1):
        title = cand.get("title", "")
        if color:
            head = f"{BOLD}{i}. {title}{RESET}"
        else:
            head = f"{i}. {title}"
        lines = [head]
        for label, key in (
            ("thesis", "thesis"),
            ("hook", "hook"),
            ("战略相关性", "strategic_relevance"),
        ):
            lines.append(f"   {label}：{cand.get(key, '')}")
        gaps = cand.get("evidence_gaps") or []
        if gaps:
            lines.append("   证据缺口：" + "；".join(gaps))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_header(date: str, run_id: str = "", color: bool = False) -> str:
    """One-line banner: date plus optional run id."""
    line = f"AI Daily — {date}"
    if run_id:
        line += f"  ({run_id})"
    if color:
        line = f"{BOLD}{line}{RESET}"
    return line


def render_hot_topics(items: list, limit: int = None, color: bool = False) -> str:
    """Ranked AIHOT hot topics: title, source, score, story link, summary."""
    lines = ["AIHOT 热点榜"]
    if not items:
        lines.append("暂无数据")
        return "\n".join(lines)
    for i, item in enumerate(items[:limit] if limit else items, 1):
        title = item.get("title", "")
        head = f"{i:>2}. {title}"
        if color:
            head = f"{BOLD}{head}{RESET}"
        lines.append(head)
        meta = "    "
        source = item.get("source_name", "")
        if source:
            meta += f"来源：{source}"
        score = item.get("score")
        if score is not None:
            meta += f" · 热度 {score}"
        lines.append(meta)
        summary = (item.get("summary") or "").strip()
        if summary:
            lines.append(f"    {summary}")
    return "\n".join(lines)


def render_matrix(matrix: dict, color: bool = False) -> str:
    """AIHOT story matrix: matched story plus its reports (max 8 shown)."""
    lines = ["AIHOT 报道矩阵"]
    if matrix.get("status") != "ok":
        lines.append(f"不可用（{matrix.get('reason') or '无原因'}）")
        return "\n".join(lines)
    lines.append(f"命中：{matrix.get('story_title', '')}（{matrix.get('story_id', '')}）")
    reports = matrix.get("reports") or []
    lines.append(f"报道：{len(reports)} 条")
    for i, report in enumerate(reports[:8], 1):
        source = report.get("source_name") or report.get("source", "")
        lines.append(f"  {i}. {source} — {report.get('title', '')}")
        if report.get("original_url"):
            lines.append(f"     {report['original_url']}")
    if len(reports) > 8:
        lines.append(f"  … 其余 {len(reports) - 8} 条")
    return "\n".join(lines)


def render_evidence(evidence: list, color: bool = False) -> str:
    """Fetch status per evidence URL: check/cross marks and lane."""
    ok = sum(1 for e in evidence if e.get("status") == "fetched")
    lines = [f"抓取证据：{len(evidence)} 条（成功 {ok}）"]
    for e in evidence:
        mark = "✓" if e.get("status") == "fetched" else "✗"
        lines.append(f"  {mark} {e.get('url', '')} [{e.get('source_lane', '?')}]")
    return "\n".join(lines)


def render_osint(modules: list, gaps: list, analysis_status: str = "",
                 color: bool = False) -> str:
    """Seven-module OSINT archive summary plus evidence gaps."""
    lines = ["OSINT 情报档案"]
    for m in modules or []:
        summary = (m.get("summary") or "").strip()
        mark = "—" if summary in ("", "无") else "✓"
        lines.append(f"  {mark} {m.get('title', '')}（{m.get('key', '')}）")
        if summary and summary != "无":
            lines.append(f"      {summary[:160]}")
    if analysis_status:
        lines.append(f"Codex 分析：{analysis_status}")
    if gaps:
        lines.append("证据缺口：")
        for gap in gaps:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def prompt_choice(count: int, input_fn=input) -> int:
    """Loop until a valid 1..count integer is entered.

    Empty, non-numeric and out-of-range input retries instead of
    raising; only a valid choice returns.  The prompt states the range
    so an interactive user knows what is accepted.
    """
    while True:
        raw = input_fn(f"选择 1..{count}：")
        raw = raw.strip()
        try:
            value = int(raw)
        except ValueError:
            continue
        if 1 <= value <= count:
            return value


def prompt_optional_direction(input_fn=input) -> str:
    """Prompt for an optional editorial direction; Enter returns ""."""
    raw = input_fn("可选写作方向（直接回车跳过）：")
    return raw.strip()

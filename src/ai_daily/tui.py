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
DIM = "\033[2m"

# Truecolor palette (OTTY/iTerm2/kitty 原生支持；旧终端按最接近色降级)。
ACCENT = "\033[38;2;94;200;235m"     # 亮青：标题与当前阶段
GREEN = "\033[38;2;74;222;128m"      # 成功/完成
YELLOW = "\033[38;2;250;204;21m"     # 缺口/警告
RED = "\033[38;2;248;113;113m"       # 失败
MUTED = "\033[38;2;148;163;184m"     # 次要信息

DONE_MARK = "\u2713"      # ✓
CURRENT_MARK = "\u2192"   # →


def _paint(text: str, code: str, color: bool) -> str:
    return f"{code}{text}{RESET}" if color else text


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
                line = f"{GREEN}{mark}{RESET}{MUTED}{name}{RESET}"
            else:
                line = f"{mark}{name}"
        elif i == index:
            mark = f"{CURRENT_MARK} "
            if color:
                line = f"{ACCENT}{BOLD}{mark}{name}{RESET}"
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
            head = f"{ACCENT}{BOLD}{i}.{RESET} {BOLD}{title}{RESET}"
        else:
            head = f"{i}. {title}"
        lines = [head]
        for label, key in (
            ("thesis", "thesis"),
            ("hook", "hook"),
            ("战略相关性", "strategic_relevance"),
        ):
            if color:
                lines.append(f"   {MUTED}{label}：{RESET}{cand.get(key, '')}")
            else:
                lines.append(f"   {label}：{cand.get(key, '')}")
        gaps = cand.get("evidence_gaps") or []
        if gaps:
            gap_text = "   证据缺口：" + "；".join(gaps)
            lines.append(_paint(gap_text, YELLOW, color))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_header(date: str, run_id: str = "", color: bool = False) -> str:
    """One-line banner: date plus optional run id."""
    line = f"AI Daily — {date}"
    if run_id:
        line += f"  ({run_id})"
    if color:
        line = f"{ACCENT}{BOLD}{line}{RESET}"
        width = max(len(date) + len(run_id) + 16, 44)
        line += f"\n{MUTED}{'─' * width}{RESET}"
    return line


def render_hot_topics(items: list, limit: int = None, color: bool = False) -> str:
    """Ranked AIHOT hot topics: title, source, score, story link, summary."""
    lines = [_paint("AIHOT 热点榜", f"{ACCENT}{BOLD}", color)]
    if not items:
        lines.append("暂无数据")
        return "\n".join(lines)
    for i, item in enumerate(items[:limit] if limit else items, 1):
        title = item.get("title", "")
        if color:
            head = f"{ACCENT}{BOLD}{i:>2}.{RESET} {BOLD}{title}{RESET}"
        else:
            head = f"{i:>2}. {title}"
        lines.append(head)
        meta = "    "
        source = item.get("source_name", "")
        if source:
            meta += f"来源：{source}"
        score = item.get("score")
        if score is not None:
            meta += f" · 热度 {score}"
        lines.append(_paint(meta, MUTED, color))
        summary = (item.get("summary") or "").strip()
        if summary:
            lines.append(f"    {summary}")
    return "\n".join(lines)


def render_matrix(matrix: dict, color: bool = False) -> str:
    """AIHOT story matrix: matched story plus its reports (max 8 shown)."""
    lines = [_paint("AIHOT 报道矩阵", f"{ACCENT}{BOLD}", color)]
    if matrix.get("status") != "ok":
        lines.append(_paint(
            f"不可用（{matrix.get('reason') or '无原因'}）", YELLOW, color
        ))
        return "\n".join(lines)
    hit = f"命中：{matrix.get('story_title', '')}（{matrix.get('story_id', '')}）"
    lines.append(_paint(hit, BOLD, color))
    reports = matrix.get("reports") or []
    lines.append(_paint(f"报道：{len(reports)} 条", MUTED, color))
    for i, report in enumerate(reports[:8], 1):
        source = report.get("source_name") or report.get("source", "")
        lines.append(f"  {i}. {_paint(source, BOLD, color)} — {report.get('title', '')}")
        if report.get("original_url"):
            lines.append(_paint(f"     {report['original_url']}", MUTED, color))
    if len(reports) > 8:
        lines.append(_paint(f"  … 其余 {len(reports) - 8} 条", MUTED, color))
    return "\n".join(lines)


def render_evidence(evidence: list, color: bool = False) -> str:
    """Fetch status per evidence URL: check/cross marks and lane."""
    ok = sum(1 for e in evidence if e.get("status") == "fetched")
    lines = [_paint(f"抓取证据：{len(evidence)} 条（成功 {ok}）", BOLD, color)]
    for e in evidence:
        mark = "✓" if e.get("status") == "fetched" else "✗"
        code = GREEN if e.get("status") == "fetched" else RED
        lane = _paint(f"[{e.get('source_lane', '?')}]", MUTED, color)
        lines.append(
            f"  {_paint(mark, code, color)} {e.get('url', '')} "
            f"{lane}"
        )
    return "\n".join(lines)


def render_osint(modules: list, gaps: list, analysis_status: str = "",
                 color: bool = False) -> str:
    """Seven-module OSINT archive summary plus evidence gaps."""
    lines = [_paint("OSINT 情报档案", f"{ACCENT}{BOLD}", color)]
    for m in modules or []:
        summary = (m.get("summary") or "").strip()
        if summary in ("", "无"):
            mark, code, name_code = "—", MUTED, ""
        else:
            mark, code, name_code = "✓", GREEN, BOLD
        name = _paint(f"{m.get('title', '')}（{m.get('key', '')}）", name_code, color)
        lines.append(f"  {_paint(mark, code, color)} {name}")
        if summary and summary != "无":
            lines.append(f"      {summary[:160]}")
    if analysis_status:
        code = GREEN if analysis_status == "completed" else YELLOW
        lines.append(_paint(f"Codex 分析：{analysis_status}", code, color))
    if gaps:
        lines.append(_paint("证据缺口：", f"{YELLOW}{BOLD}", color))
        for gap in gaps:
            lines.append(_paint(f"  - {gap}", YELLOW, color))
    return "\n".join(lines)


_ARCHETYPE_TITLES = {
    "first_hand_test": "一手实测翻车",
    "contrarian_audit": "反共识拆台",
    "mechanism_teardown": "工程机制拆解",
    "cost_ledger": "成本与供应链账本",
    "workflow_playbook": "工作流配方",
    "power_map": "生态权力图",
    "compliance_risk": "政策合规风险",
    "decision_brief": "决策快讯",
}


def render_narrative_candidates(candidates: list, color: bool = False) -> str:
    """Two narrative candidates: archetype, hook, thesis, decision rule."""
    blocks = []
    for i, cand in enumerate(candidates, 1):
        title = cand.get("title", "")
        if color:
            head = f"{ACCENT}{BOLD}{i}.{RESET} {BOLD}{title}{RESET}"
        else:
            head = f"{i}. {title}"
        archetype = _ARCHETYPE_TITLES.get(
            cand.get("archetype", ""), cand.get("archetype", "")
        )
        lines = [head, f"   原型：{archetype}（{cand.get('archetype', '')}）"]
        for label, key in (("hook", "hook"), ("thesis", "thesis")):
            if cand.get(key):
                if color:
                    lines.append(f"   {MUTED}{label}：{RESET}{cand.get(key)}")
                else:
                    lines.append(f"   {label}：{cand.get(key)}")
        for arg in cand.get("key_arguments") or []:
            line = f"      · {arg.get('claim', '')}（{arg.get('observable', '')}）"
            lines.append(line)
        notes = cand.get("platform_notes") or {}
        if notes.get("linkedin"):
            lines.append(f"   LinkedIn：{notes['linkedin']}")
        if notes.get("wechat"):
            lines.append(f"   微信公众号：{notes['wechat']}")
        if cand.get("decision_rule"):
            line = f"   决策规则：{cand['decision_rule']}"
            lines.append(_paint(line, GREEN, color))
        if cand.get("author_stance"):
            line = f"   作者立场：{cand['author_stance']}"
            lines.append(_paint(line, ACCENT, color))
        if cand.get("personal_scene"):
            lines.append(f"   个人场景：{cand['personal_scene']}")
        if cand.get("kicker"):
            lines.append(f"   冷结尾：{cand['kicker']}")
        scores = cand.get("scores") or {}
        if scores:
            line = (
                f"   评分：LinkedIn {scores.get('linkedin_total', '?')} · "
                f"公众号 {scores.get('wechat_total', '?')}"
                f"（E {scores.get('evidence', '?')} C {scores.get('conflict', '?')}"
                f" D {scores.get('decision', '?')} F {scores.get('freshness', '?')}）"
            )
            lines.append(_paint(line, MUTED, color))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_audit(audit: dict, color: bool = False) -> str:
    """05 evidence-sufficiency audit: verdict, coverage, gaps, tasks."""
    lines = [_paint("证据充分性审计", f"{ACCENT}{BOLD}", color)]
    verdict = audit.get("verdict", "")
    verdict_code = {
        "sufficient": GREEN,
        "needs_research": YELLOW,
        "unsupported": RED,
    }.get(verdict, BOLD)
    lines.append(f"判定：{_paint(verdict, verdict_code, color)}")
    if audit.get("reason"):
        lines.append(_paint(f"原因：{audit['reason']}", YELLOW, color))
    for cov in audit.get("claim_coverage") or []:
        line = f"  - {cov.get('claim', '')}：{cov.get('coverage', '')}"
        if cov.get("evidence"):
            line += f"（{cov['evidence']}）"
        lines.append(line)
    if audit.get("evidence_gaps"):
        lines.append(_paint("证据缺口：" + "；".join(
            audit["evidence_gaps"]
        ), YELLOW, color))
    for task in audit.get("research_tasks") or []:
        lines.append(
            f"  · [{task.get('gap_type', '')}] {task.get('query', '')} → "
            f"{task.get('direction', '')}"
        )
    return "\n".join(lines)


def prompt_choice(count: int, input_fn=input) -> int:
    """Loop until a valid 1..count integer is entered.

    Empty, non-numeric and out-of-range input retries instead of
    raising; only a valid choice returns.  The prompt states the range
    so an interactive user knows what is accepted.
    """
    if count < 1:
        return -1
    while True:
        raw = input_fn(f"选择 1..{count}：")
        raw = raw.strip()
        try:
            value = int(raw)
        except ValueError:
            continue
        if 1 <= value <= count:
            return value

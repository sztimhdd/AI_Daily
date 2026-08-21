"""Command-line interface for the daily editorial pipeline.

Runnable from the repo root:

    PYTHONPATH=src python3 -m ai_daily.cli <command> [options]

Stages: collect -> topic_choice -> research -> outline -> draft ->
optional_cover -> assembly -> completed.  Exit code 0 on success, 1 on
a controlled pipeline/gate failure (message on stderr), 2 on usage
errors.  No credentials are ever requested or stored.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

from . import STAGES, assemble, assemble_en, claim_check, draft, draft_en, fetch
from . import narrative, outline, pipeline, publish, state, sufficiency
from . import targeted, topics, tui, visuals, linkedin
from . import telegram_adapter
from .paths import RunPaths


def _today() -> str:
    return datetime.date.today().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai_daily", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, need_root=True):
        p.add_argument("--root", default=".", help="repository root")
        p.add_argument("--date", default=_today(), help="run date YYYY-MM-DD")

    p = sub.add_parser("init", help="create state.md for a date")
    common(p)

    p = sub.add_parser("status", help="print the run state")
    common(p)

    p = sub.add_parser("collect", help="collect AIHOT (+ optional RSS)")
    common(p)
    p.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    p.add_argument("--aihot-fixture", default=None)
    p.add_argument("--rss-url", action="append", default=None,
                   help="explicit RSS URL (repeatable); default: none in fixture mode, catalog in live mode")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("candidates", help="print the 3 topic candidates")
    common(p)

    p = sub.add_parser("choose-topic", help="record the topic choice")
    common(p)
    p.add_argument("--fixture", default=None, help="fixture bypass JSON")
    p.add_argument("--choice", type=int, default=None, help="human choice 1..3")
    p.add_argument("--direction", default="", help="editorial direction, kept verbatim")
    p.add_argument("--simulate", action="store_true",
                   help="unattended simulated choice (no human wait); "
                        "records topic_choice: simulated with the candidate "
                        "kept verbatim; defaults to candidate 1 when --choice is omitted")

    for name, help_text in (
        ("outline", "build the outline"),
        ("draft", "write the draft"),
        ("assemble", "validate and package the article"),
    ):
        p = sub.add_parser(name, help=help_text)
        common(p)
        p.add_argument("--force", action="store_true")

    p = sub.add_parser("draft-en", help="write and quality-gate the English draft")
    common(p)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("assemble-en", help="package the English article")
    common(p)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("claim-check", help="fact-check the English draft against the evidence")
    common(p)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("illustrate", help="optional Gemini image generation and embedding (nonblocking)")
    common(p)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("linkedin-kit", help="generate the LinkedIn distribution kit (nonblocking)")
    common(p)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("research", help="run targeted research")
    common(p)
    p.add_argument("--force", action="store_true")
    p.add_argument(
        "--mode",
        choices=("fixture", "live"),
        default="fixture",
        help=(
            "fixture: closed-pool V1 research (default, compatible); "
            "live: active-search V2 initial research (story matrix + "
            "real URL fetching)"
        ),
    )

    p = sub.add_parser("regenerate-outline",
                       help="rebuild the draft after a human outline edit")
    common(p)

    p = sub.add_parser("cover", help="optional cover adoption (nonblocking)")
    common(p)
    p.add_argument("--source-dir", default=None,
                   help="dir holding ChatGPT Image exports")

    p = sub.add_parser("publish", help="publish with verified remote or local-only")
    common(p)
    p.add_argument("--repo-dir", required=True)
    p.add_argument("--remote-url", default=None)
    p.add_argument("--branch", default="main")

    p = sub.add_parser("run", help="unattended fixture end-to-end run")
    common(p)
    p.add_argument("--topic-fixture", required=True)
    p.add_argument("--aihot-fixture", required=True)
    p.add_argument("--cover-source", default=None)
    p.add_argument("--repo-dir", default=None)

    p = sub.add_parser("run-en", help="deliver the prepared English edition")
    common(p)
    p.add_argument("--repo-dir", default=None)
    p.add_argument("--remote-url", default=None)
    p.add_argument("--branch", default="main")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser(
        "telegram",
        help="Telegram decision channel: offer pending decision + apply reply",
    )
    common(p)
    p.add_argument("--offset", type=int, default=None,
                   help="getUpdates offset (track the last applied update id)")
    p.add_argument("--offer-only", action="store_true",
                   help="push the pending decision without applying replies")

    p = sub.add_parser("fetch", help="fetch one URL via the unified three-lane primitive")
    common(p)
    p.add_argument("--lane", choices=("auto", "http", "cdp"), default="auto",
                   help="force a lane (default: auto-route by host)")
    p.add_argument("url", help="URL to fetch")

    p = sub.add_parser(
        "session",
        help="visible-terminal session: collect -> topic choice -> research (TUI)",
    )
    common(p)
    p.add_argument("--mode", choices=("fixture", "live"), default="live")
    p.add_argument("--aihot-fixture", default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--choice", type=int, default=None,
                   help="skip the interactive topic prompt with this choice")
    p.add_argument("--direction", default="")
    p.add_argument("--narrative-choice", type=int, default=None,
                   help="skip the interactive narrative prompt with this choice")
    p.add_argument("--extra-research", default="",
                   help="editorial supplementary research direction for 06")

    p = sub.add_parser(
        "narrative",
        help="generate two narrative candidates and record the editor's choice",
    )
    common(p)
    p.add_argument("--force", action="store_true")
    p.add_argument("--choice", type=int, default=None)
    p.add_argument("--extra-research", default="")
    p.add_argument("--simulate", action="store_true",
                   help="unattended delegated choice (recorded as simulated)")

    p = sub.add_parser(
        "audit",
        help="run the evidence-sufficiency audit and the bounded targeted loop",
    )
    common(p)
    p.add_argument("--force", action="store_true")

    return parser


def _paths(args) -> RunPaths:
    return RunPaths.for_date(args.root, args.date)


def _ensure_state(run_paths) -> None:
    state.init_state(run_paths)


def cmd_init(args) -> int:
    _ensure_state(_paths(args))
    print(f"initialized run state for {args.date}")
    return 0


def cmd_status(args) -> int:
    run_paths = _paths(args)
    st = state.read_state(run_paths)
    print(f"run: {st['run_id']}")
    for key in ("stage", "status", "slug", "topic_choice", "topic_title", "last_error", "updated_at"):
        print(f"- {key}: {st.get(key, '')}")
    print("counters:")
    for k, v in sorted(st["counters"].items()):
        print(f"- {k}: {v}")
    print("artifacts:")
    for k, v in sorted(st["artifacts"].items()):
        print(f"- {k}: {v}")
    return 0


def cmd_collect(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_collect(
        run_paths,
        mode=args.mode,
        aihot_fixture=args.aihot_fixture,
        rss_urls=args.rss_url,
        force=args.force,
    )
    aihot_path = run_paths.work_dir / "aihot-items.json"
    items = (
        json.loads(aihot_path.read_text(encoding="utf-8"))
        if aihot_path.exists() else []
    )
    print(tui.render_hot_topics(items, color=tui.supports_color()))
    print(f"collect: {result['status']} "
          f"(aihot={result.get('aihot_items', '?')} rss={result.get('rss_items', '?')})")
    return 0


def cmd_candidates(args) -> int:
    run_paths = _paths(args)
    cands = pipeline.run_candidates(run_paths)
    print(topics.candidates_markdown(args.date, cands))
    return 0


def cmd_choose_topic(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    if args.simulate and args.fixture:
        print("error: choose-topic: --simulate cannot be combined with --fixture",
              file=sys.stderr)
        return 2
    if args.fixture:
        topic = pipeline.run_topic_fixture(run_paths, args.fixture)
    elif args.simulate:
        choice = args.choice if args.choice is not None else 1
        topic = pipeline.run_simulated_choice(run_paths, choice, args.direction)
    elif args.choice is not None:
        topic = pipeline.run_human_choice(run_paths, args.choice, args.direction)
    else:
        # Interactive TUI: show the stage progress and the candidates,
        # then let the editor pick by number.  Output rendering falls
        # back to plain text when stdout is not a terminal, so scripted
        # usage stays greppable.
        code = _require_interactive()
        if code is not None:
            return code
        cands = pipeline.run_candidates(run_paths)
        st = state.read_state(run_paths)
        use_color = tui.supports_color()
        print(tui.render_progress(st.get("stage", ""), STAGES, color=use_color))
        print()
        print(tui.render_candidates(cands, color=use_color))
        choice = tui.prompt_choice(len(cands))
        topic = pipeline.run_human_choice(run_paths, choice, "")
    print(f"topic chosen: {topic['title']} ({topic['slug']})")
    return 0


def cmd_research(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    if args.mode == "live":
        result = pipeline.run_initial_research(run_paths, force=args.force)
    else:
        result = pipeline.run_research(run_paths, force=args.force)
    print(f"research: {result['status']} ({result['research_md']})")
    return 0


def cmd_narrative(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    use_color = tui.supports_color()
    result = pipeline.run_narrative(run_paths, force=args.force)
    print(f"narrative: {result['status']}")
    candidates = result.get("candidates") or []
    if result["status"] == "unavailable":
        print(f"- reason: {result.get('reason', '')}")
        return 1
    if result["status"] in ("generated", "resumed"):
        print(tui.render_narrative_candidates(candidates, color=use_color))
        print()
        st = state.read_state(run_paths)
        if st.get("narrative_choice") and args.choice is None:
            print(f"叙事已定：{st.get('narrative_title', '')}")
        elif args.choice is not None:
            recorder = (
                narrative.record_simulated_choice if args.simulate
                else narrative.record_choice
            )
            chosen = recorder(
                run_paths, candidates, args.choice, args.extra_research
            )
            print(f"叙事已定：{chosen['title']}（{chosen['archetype']}）")
        else:
            code = _require_interactive()
            if code is not None:
                return code
            choice = tui.prompt_choice(len(candidates))
            chosen = narrative.record_choice(
                run_paths, candidates, choice, args.extra_research
            )
            print(f"叙事已定：{chosen['title']}（{chosen['archetype']}）")
    return 0


def cmd_audit(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    return _run_audit_flow(run_paths, args.force, tui.supports_color())


def cmd_outline(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_outline(run_paths, force=args.force)
    print(f"outline: {result['status']} ({result['outline']})")
    return 0


def cmd_draft(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_draft(run_paths, force=args.force)
    print(f"draft: {result['status']} ({result['article']})")
    return 0


def cmd_draft_en(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_draft_en(run_paths, force=args.force)
    print(f"draft-en: {result['status']}")
    if result.get("article") is not None:
        print(f"- article: {result['article']}")
    if result.get("verdict"):
        print(f"- quality: {result['verdict']} ({result.get('word_count')} words)")
    if result.get("downgraded"):
        print("- conservative downgrade: needs_research accepted, weak claims annotated")
    if result.get("status") == "unavailable":
        print(f"- reason: {result.get('reason', '')}")
        return 1
    return 0


def cmd_regenerate_outline(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.regenerate_outline_from_edit(run_paths)
    print(f"draft rebuilt from edited outline: {result['status']} ({result['article']})")
    return 0


def cmd_cover(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_cover(run_paths, source_dir=args.source_dir)
    if result.ok:
        print(f"cover: ok ({result.path} {result.width}x{result.height} {result.format})")
    else:
        print(f"cover: skipped (optional): {result.reason}")
    return 0  # cover is optional and never fails the run


def cmd_assemble(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_assemble(run_paths, force=args.force)
    print(f"assemble: {result['status']}")
    print(f"- package: {result['package_dir']}")
    print(f"- final: {result['final_article']}")
    return 0


def cmd_assemble_en(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_assemble_en(run_paths, force=args.force)
    print(f"assemble-en: {result['status']}")
    print(f"- package: {result['package_dir']}")
    print(f"- final: {result['final_article']}")
    return 0


def cmd_claim_check(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_claim_check(run_paths, force=args.force)
    print(f"claim-check: {result['status']} (verdict: {result.get('verdict')})")
    if result.get("reason"):
        print(f"- reason: {result['reason']}")
    if result.get("status") == "unavailable":
        return 1
    return 0


def cmd_illustrate(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_illustrate(run_paths, force=args.force)
    print(f"illustrate: {result['status']}")
    if result.get("generated"):
        print(f"- images: {result.get('generated')}")
    if result.get("reason"):
        print(f"- reason: {result['reason']}")
    return 0  # illustration is optional and never fails the run


def cmd_linkedin_kit(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_linkedin_kit(run_paths, force=args.force)
    print(f"linkedin-kit: {result['status']}")
    if result.get("seo_title"):
        print(f"- seo_title: {result['seo_title']}")
    if result.get("reason"):
        print(f"- reason: {result['reason']}")
    return 0  # the kit is optional and never fails the run


def cmd_publish(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_publish(
        run_paths, repo_dir=args.repo_dir,
        remote_url=args.remote_url, branch=args.branch,
    )
    print(f"publish: mode={result.mode}")
    print(f"- reason: {result.reason}")
    if result.remote_sha256:
        print(f"- remote sha256: {result.remote_sha256}")
    print(f"- local sha256: {result.local_sha256}")
    print(f"- article: {result.published_relpath}")
    return 0


def cmd_run(args) -> int:
    summary = pipeline.run_fixture_e2e(
        root=args.root,
        date=args.date,
        topic_fixture=args.topic_fixture,
        aihot_fixture=args.aihot_fixture,
        cover_source=args.cover_source,
        repo_dir=args.repo_dir,
    )
    print(f"run: {summary['run_id']} slug={summary['slug']}")
    print(f"- collect: {summary['collect']['status']}")
    print(f"- research/outline/draft: {summary['research']}/{summary['outline']}/{summary['draft']}")
    print(f"- cover_ok: {summary['cover_ok']}")
    print(f"- assembly: {summary['assembly']}")
    print(f"- publish: {summary['publish_mode']}")
    print(f"- final: {summary['final_article']}")
    print(f"- stage: {summary['stage']}")
    return 0


def cmd_run_en(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_delivery_en(
        run_paths, repo_dir=args.repo_dir, remote_url=args.remote_url,
        branch=args.branch, force=args.force,
    )
    print(f"run-en: {result['status']}")
    if result.get("summary") is not None:
        print(f"- summary: {result['summary']}")
    if result.get("reason"):
        print(f"- reason: {result['reason']}")
    return 0 if result["status"] == "delivered" else 1


def cmd_telegram(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    if args.offer_only:
        config = telegram_adapter.load_config()
        result = telegram_adapter.offer(
            run_paths, config["token"], config["chat"]
        )
        print(f"telegram: offered={result['offered']}")
        return 0
    result = telegram_adapter.run_once(run_paths, offset=args.offset)
    print(f"telegram: offered={result['offered']}")
    if result.get("reply"):
        print(f"- reply: {result['reply']}")
    applied = result.get("applied")
    if applied:
        if applied.get("ok"):
            print(f"- applied {applied.get('decision')}: {applied.get('chosen')}")
        else:
            print(f"- not applied: {applied.get('reason', '')}")
    return 0


def cmd_fetch(args) -> int:
    """Low-level fetch primitive: usable at any stage, no state.md needed."""
    run_paths = _paths(args)
    lane = None if args.lane == "auto" else args.lane
    result = fetch.fetch(args.url, run_paths, lane=lane)
    print(f"fetch: {result.status} lane={result.source_lane} "
          f"sha256={result.sha256} title={result.title}")
    print(result.markdown[:200])
    return 0


def _session_progress(use_color: bool):
    """Render live research milestones inside the visible session terminal."""
    def emit(kind, payload):
        if kind == "matrix":
            print(tui.render_matrix(payload, color=use_color))
            print()
        elif kind == "evidence":
            print(tui.render_evidence(payload, color=use_color))
            print()
        elif kind == "analysis_start":
            print("正在调用 Codex CLI 生成七模块 OSINT 分析…")
        elif kind == "analysis_done":
            reason = payload.get("reason")
            print(
                f"Codex 分析：{payload.get('status', '?')}"
                + (f"（{reason}）" if reason else "")
            )
    return emit


def _stale_run(run_paths) -> bool:
    """True when the saved AIHOT pool was written before today (a leftover run).

    A daily run must never resume yesterday's evidence or topic choice;
    same-day reruns still resume normally.  The file's own write time is
    the source of truth: it records when OUR pipeline collected the pool.
    """
    path = run_paths.work_dir / "aihot-items.json"
    if not path.exists():
        return False
    try:
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).date()
    except OSError:
        return False
    return mtime < datetime.date.today()


def _reset_run(run_paths) -> None:
    """Drop a previous day's regenerable artifacts and restart the state."""
    for name in (
        "aihot-items.json", "rss-items.json", "rss-pool.md", "rss-stats.json",
        "selected-topic.json", "story-matrix.json", "initial-evidence.json",
        "initial-osint.json", "initial-osint.md",
        "narrative-candidates.json", "narrative-candidates.md",
        "selected-narrative.json",
        "sufficiency-audit.json", "sufficiency-audit.md",
        "targeted-evidence.json", "evidence-package.json",
        "article-en.md", "quality-en-report.md",
    ):
        path = run_paths.work_dir / name
        if path.exists():
            path.unlink()
    state_path = run_paths.work_dir / "state.md"
    if state_path.exists():
        state_path.unlink()
    state.init_state(run_paths)
    print("检测到隔天的过期数据，已重置为全新一天（重新 collect + 重新选题）。")
    print()


def _require_interactive():
    """None when stdin is a terminal; else a usage error exit code."""
    if sys.stdin.isatty():
        return None
    print("error: stdin is not an interactive terminal; "
          "pass --choice N to run unattended", file=sys.stderr)
    return 2


def _next_stage_hint(stage: str, mode: str = "fixture") -> str:
    if stage == "narrative":
        if mode == "live":
            return "04 已跑完（下一步：05 证据充分性审计）"
        return "04 已跑完（下一步：outline）"
    if stage == "research" and mode == "fixture":
        return "03 已跑完（fixture 模式止步；live 模式继续叙事选择）"
    if stage in STAGES and stage != STAGES[-1]:
        return f"03 已跑完，下一步：{STAGES[STAGES.index(stage) + 1]}"
    return "03 已跑完，本会话结束"


def _audit_hint(verdict: str, reason: str = "") -> str:
    if verdict == "sufficient":
        return "05/06 已跑完：证据充分，下一步 07 英文全文与编辑质量门"
    if verdict == "unsupported":
        return f"阻塞：核心叙事无法被证据支持——{reason or '无原因'}"
    return f"两轮补证后仍不足，收口判定 needs_research——{reason or '无原因'}"


def _run_audit_flow(run_paths, force: bool, use_color: bool) -> int:
    """05 audit + (when needed) 06 bounded loop; shared by session/audit."""
    print("正在调用 Codex 审计证据充分性（约 2–5 分钟）…")
    audit = pipeline.run_sufficiency(run_paths, force=force)
    print(tui.render_audit(audit, color=use_color))
    print()
    if audit.get("status") == "unavailable":
        print("05 审计不可用，会话终止（不伪造判定）。")
        return 1
    if audit.get("verdict") == "needs_research":
        loop = pipeline.run_targeted_loop(
            run_paths, force=force, initial_audit=audit,
            progress=_audit_progress,
        )
        print(f"补证 {loop.get('rounds', 0)} 轮 → 最终判定："
              f"{loop.get('verdict')}")
        if loop.get("status") == "unavailable":
            print("06 补证循环不可用，会话终止。")
            return 1
        verdict = loop.get("verdict")
        reason = loop.get("reason", "")
        if verdict != "sufficient":
            state.fail(run_paths, "audit",
                       f"narrative {verdict}: {reason or '无原因'}")
    else:
        verdict = audit.get("verdict")
        reason = audit.get("reason", "")
        if verdict == "unsupported":
            state.fail(run_paths, "audit",
                       f"narrative unsupported: {reason or '无原因'}")
    print(_audit_hint(verdict, reason))
    return 0 if verdict == "sufficient" else 1


def _audit_progress(kind, payload):
    if kind == "round_start":
        print(f"第 {payload.get('round')} 轮定向补证：发现并抓取 "
              f"{payload.get('tasks', 0)} 条缺口的来源…")
    elif kind == "re_audit":
        print("补证完成，重新调用 Codex 审计…")


def cmd_session(args) -> int:
    """One visible-terminal session through stage 03 with full TUI output."""
    run_paths = _paths(args)
    _ensure_state(run_paths)
    if _stale_run(run_paths):
        _reset_run(run_paths)
    use_color = tui.supports_color()
    st = state.read_state(run_paths)
    print(tui.render_header(args.date, run_paths.run_id, color=use_color))
    print()
    print(tui.render_progress(st.get("stage", ""), STAGES, color=use_color))
    print()

    result = pipeline.run_collect(
        run_paths, mode=args.mode, aihot_fixture=args.aihot_fixture, force=args.force,
    )
    aihot_path = run_paths.work_dir / "aihot-items.json"
    items = (
        json.loads(aihot_path.read_text(encoding="utf-8"))
        if aihot_path.exists() else []
    )
    print(tui.render_hot_topics(items, color=use_color))
    print(f"collect: {result['status']}（AIHOT {len(items)} 条）")
    print()

    cands = pipeline.run_candidates(run_paths)
    print(tui.render_candidates(cands, color=use_color))
    print()

    st = state.read_state(run_paths)
    if st.get("topic_choice") and args.choice is None:
        print(f"选题已定：{st.get('topic_title', '')}（{st.get('slug', '')}）")
    elif args.choice is not None:
        topic = pipeline.run_human_choice(run_paths, args.choice, args.direction)
        print(f"选题已定：{topic['title']}（{topic['slug']}）")
    else:
        code = _require_interactive()
        if code is not None:
            return code
        choice = tui.prompt_choice(len(cands))
        topic = pipeline.run_human_choice(run_paths, choice, "")
        print(f"选题已定：{topic['title']}（{topic['slug']}）")
    print()

    if args.mode == "live":
        result = pipeline.run_initial_research(
            run_paths, force=args.force, progress=_session_progress(use_color),
        )
        print(f"research: {result['status']}")
        print("正在调用 Codex 生成两个叙事候选（约 2–5 分钟）…")
        narrative_result = pipeline.run_narrative(run_paths, force=args.force)
        print(f"narrative: {narrative_result['status']}")
        candidates = narrative_result.get("candidates") or []
        if narrative_result["status"] == "unavailable":
            print(f"- reason: {narrative_result.get('reason', '')}")
            return 1
        print(tui.render_narrative_candidates(candidates, color=use_color))
        print()
        st = state.read_state(run_paths)
        if st.get("narrative_choice") and args.narrative_choice is None:
            print(f"叙事已定：{st.get('narrative_title', '')}")
        elif args.narrative_choice is not None:
            chosen = narrative.record_choice(
                run_paths, candidates, args.narrative_choice, args.extra_research
            )
            print(f"叙事已定：{chosen['title']}（{chosen['archetype']}）")
        else:
            code = _require_interactive()
            if code is not None:
                return code
            choice = tui.prompt_choice(len(candidates))
            chosen = narrative.record_choice(
                run_paths, candidates, choice, args.extra_research
            )
            print(f"叙事已定：{chosen['title']}（{chosen['archetype']}）")
        print()
        print(_next_stage_hint("narrative", mode="live"))
        return _run_audit_flow(run_paths, args.force, use_color)
    else:
        result = pipeline.run_research(run_paths, force=args.force)
        print(f"research: {result['status']}")
    osint_path = run_paths.work_dir / "initial-osint.json"
    if osint_path.exists():
        data = json.loads(osint_path.read_text(encoding="utf-8"))
        print(tui.render_osint(
            data.get("modules", []),
            data.get("evidence_gaps", []),
            analysis_status=data.get("analysis_status", ""),
            color=use_color,
        ))
        print()
    print(_next_stage_hint(
        state.read_state(run_paths).get("stage", ""), mode=args.mode
    ))
    return 0


COMMANDS = {
    "init": cmd_init,
    "status": cmd_status,
    "collect": cmd_collect,
    "candidates": cmd_candidates,
    "choose-topic": cmd_choose_topic,
    "research": cmd_research,
    "outline": cmd_outline,
    "draft": cmd_draft,
    "draft-en": cmd_draft_en,
    "regenerate-outline": cmd_regenerate_outline,
    "cover": cmd_cover,
    "assemble": cmd_assemble,
    "assemble-en": cmd_assemble_en,
    "claim-check": cmd_claim_check,
    "illustrate": cmd_illustrate,
    "linkedin-kit": cmd_linkedin_kit,
    "publish": cmd_publish,
    "run": cmd_run,
    "run-en": cmd_run_en,
    "telegram": cmd_telegram,
    "fetch": cmd_fetch,
    "session": cmd_session,
    "narrative": cmd_narrative,
    "audit": cmd_audit,
}

# Controlled domain errors: reported cleanly, exit 1 (never a traceback).
_DOMAIN_ERRORS = (
    pipeline.PipelineError,
    topics.TopicError,
    topics.TopicGateBlocked,
    assemble.AssembleError,
    publish.PublishError,
    state.StateError,
    narrative.NarrativeError,
    narrative.NarrativeGateBlocked,
    sufficiency.AuditError,
    sufficiency.AuditGateBlocked,
    targeted.TargetedError,
    draft_en.DraftEnError,
    assemble_en.AssembleEnError,
    claim_check.ClaimCheckError,
    telegram_adapter.TelegramError,
    draft.__class__ and RuntimeError,  # draft/outline/research raise RuntimeError subclasses
)


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2
    handler = COMMANDS.get(args.command)
    if handler is None:
        print(f"error: unknown command {args.command!r}", file=sys.stderr)
        return 2
    try:
        return handler(args)
    except _DOMAIN_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

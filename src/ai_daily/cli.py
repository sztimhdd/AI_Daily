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
import sys

from . import assemble, draft, outline, pipeline, publish, state, topics
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
        ("research", "run targeted research"),
        ("outline", "build the outline"),
        ("draft", "write the draft"),
        ("assemble", "validate and package the article"),
    ):
        p = sub.add_parser(name, help=help_text)
        common(p)
        p.add_argument("--force", action="store_true")

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
    elif args.choice:
        topic = pipeline.run_human_choice(run_paths, args.choice, args.direction)
    else:
        print("error: choose-topic needs --fixture, --choice, or --simulate", file=sys.stderr)
        return 2
    print(f"topic chosen: {topic['title']} ({topic['slug']})")
    return 0


def cmd_research(args) -> int:
    run_paths = _paths(args)
    _ensure_state(run_paths)
    result = pipeline.run_research(run_paths, force=args.force)
    print(f"research: {result['status']} ({result['research_md']})")
    return 0


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


COMMANDS = {
    "init": cmd_init,
    "status": cmd_status,
    "collect": cmd_collect,
    "candidates": cmd_candidates,
    "choose-topic": cmd_choose_topic,
    "research": cmd_research,
    "outline": cmd_outline,
    "draft": cmd_draft,
    "regenerate-outline": cmd_regenerate_outline,
    "cover": cmd_cover,
    "assemble": cmd_assemble,
    "publish": cmd_publish,
    "run": cmd_run,
}

# Controlled domain errors: reported cleanly, exit 1 (never a traceback).
_DOMAIN_ERRORS = (
    pipeline.PipelineError,
    topics.TopicError,
    topics.TopicGateBlocked,
    assemble.AssembleError,
    publish.PublishError,
    state.StateError,
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

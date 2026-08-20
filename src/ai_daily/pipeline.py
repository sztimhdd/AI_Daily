"""Stage orchestration: gates, resume, and failure semantics.

Stage order (V1):
collect -> topic_choice -> research -> outline -> draft ->
optional_cover -> assembly -> completed

Rules enforced here:

- AIHOT failure stops candidate generation: collect fails honestly and
  the run is marked failed (no training-memory fallback).
- RSS failures never block: they are recorded in rss-stats.json.
- Resume never re-collects: existing evidence short-circuits collect.
- research is gated on the topic choice (human, simulated, or fixture bypass).
- Each stage transitions the durable state and clears stale errors on
  success.
"""

from __future__ import annotations

import json

from . import STAGES, aihot, assemble, assemble_en, claim_check, cover, draft, visuals, linkedin
from . import draft_en
from . import narrative, outline
from . import research, sufficiency, targeted
from . import rss_catalog, rss_collect, state, topics

AIHOT_EVIDENCE = "aihot-items.json"
RSS_EVIDENCE = "rss-items.json"
RSS_STATS = "rss-stats.json"
RSS_POOL = "rss-pool.md"


class PipelineError(RuntimeError):
    """Raised when a stage cannot honestly proceed."""


def _require_stage_ready(run_paths, artifact_name: str, stage_needed: str):
    if not (run_paths.work_dir / artifact_name).exists():
        raise PipelineError(
            f"{artifact_name} missing; run the {stage_needed} stage first"
        )


# ---------------------------------------------------------------------------
# collect
# ---------------------------------------------------------------------------


def _load_json_list(path) -> list:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def run_collect(
    run_paths,
    mode: str = "fixture",
    aihot_fixture=None,
    fetch=None,
    rss_urls=None,
    rss_fetch=None,
    force: bool = False,
) -> dict:
    """Collect AIHOT (required) + RSS (optional enrichment)."""
    evidence_path = run_paths.work_dir / AIHOT_EVIDENCE
    if evidence_path.exists() and not force:
        existing = _load_json_list(evidence_path)
        if existing:
            return {"status": "resumed", "aihot_items": len(existing)}

    state.transition(run_paths, "collect")

    result = aihot.collect_items(mode=mode, fixture_path=aihot_fixture, fetch=fetch)
    if not result.ok:
        state.fail(run_paths, "collect", f"AIHOT unavailable: {result.error}")
        raise PipelineError(f"AIHOT unavailable: {result.error}")
    if not result.items:
        state.fail(run_paths, "collect", "AIHOT returned zero items; cannot generate candidates honestly")
        raise PipelineError("AIHOT returned zero items; cannot generate candidates honestly")

    run_paths.ensure_work_dir()
    evidence_path.write_text(
        json.dumps(result.items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # RSS: optional, nonblocking.  Fixture mode without an injected fetcher
    # skips network RSS entirely instead of pretending to fetch.
    if rss_urls is None and mode == "live":
        catalog = rss_catalog.build_catalog(run_paths.root)
        rss_urls = [s["url"] for s in catalog["sources"] if s.get("extractable")]
    if rss_urls is None:
        rss_urls = []
    if mode == "fixture" and rss_fetch is None and rss_urls:
        rss_result = rss_collect.CollectResult(
            items=[], failures=[],
            stats={"feeds_requested": len(rss_urls), "feeds_ok": 0,
                   "feeds_failed": 0, "failures": [],
                   "items_seen": 0, "items_kept": 0,
                   "duplicates_removed": 0, "items_out_of_window": 0,
                   "undated_items": 0, "by_feed": {},
                   "window_hours": 96,
                   "note": "rss skipped in fixture mode (no injected fetcher)"},
        )
    else:
        rss_result = rss_collect.collect(rss_urls, fetch=rss_fetch)

    (run_paths.work_dir / RSS_EVIDENCE).write_text(
        json.dumps(rss_result.items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_paths.work_dir / RSS_STATS).write_text(
        json.dumps(rss_result.stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_paths.work_dir / RSS_POOL).write_text(
        rss_collect.pool_markdown(rss_collect.compress_pool(rss_result)),
        encoding="utf-8",
    )

    state.bump_counter(run_paths, "collect_runs")
    state.record_artifact(
        run_paths, "aihot-evidence", f".local/runs/{run_paths.date}/{AIHOT_EVIDENCE}"
    )
    state.clear_error(run_paths)
    state.update_fields(
        run_paths,
        note=(
            f"collect: aihot {len(result.items)} items ({mode}); "
            f"rss kept {rss_result.stats['items_kept']}, "
            f"failed feeds {rss_result.stats['feeds_failed']} (nonblocking)"
        ),
    )
    state.transition(run_paths, "topic_choice")
    return {
        "status": "collected",
        "aihot_items": len(result.items),
        "rss_items": len(rss_result.items),
        "rss_failures": len(rss_result.failures),
    }


# ---------------------------------------------------------------------------
# topic choice
# ---------------------------------------------------------------------------


def run_topic_fixture(run_paths, fixture_path) -> dict:
    """Fixture bypass of the human gate (unattended runs)."""
    state.transition(run_paths, "topic_choice")
    return topics.choose_fixture(run_paths, fixture_path)


def run_candidates(run_paths) -> list:
    """Exactly three rich candidates from the saved evidence pool."""
    aihot_items = _load_json_list(run_paths.work_dir / AIHOT_EVIDENCE)
    if not aihot_items:
        raise PipelineError("no collected evidence; run the collect stage first")
    rss_items = _load_json_list(run_paths.work_dir / RSS_EVIDENCE)
    return topics.generate_candidates(aihot_items, rss_items=rss_items, date=run_paths.date)


def run_human_choice(run_paths, choice: int, direction: str = "") -> dict:
    state.transition(run_paths, "topic_choice")
    return topics.record_human_choice(run_paths, run_candidates(run_paths), choice, direction)


def run_simulated_choice(run_paths, choice: int, direction: str = "") -> dict:
    """Simulated (unattended) choice from the ranked candidates.

    No human is waiting: the choice is recorded as
    ``topic_choice: simulated`` with the candidate kept verbatim.
    """
    state.transition(run_paths, "topic_choice")
    return topics.record_simulated_choice(run_paths, run_candidates(run_paths), choice, direction)


# ---------------------------------------------------------------------------
# research / outline / draft
# ---------------------------------------------------------------------------


def run_research(run_paths, ensure_evidence=None, force: bool = False) -> dict:
    topics.require_choice(run_paths)  # raises TopicGateBlocked when unchosen
    state.transition(run_paths, "research")
    return research.run(run_paths, ensure_evidence=ensure_evidence, force=force)


def run_initial_research(
    run_paths,
    aihot_fetch=None,
    http_fetcher=None,
    cdp_runner=None,
    discover_runner=None,
    codex_runner=None,
    progress=None,
    force: bool = False,
) -> dict:
    """V2 initial research (active search, opt-in live path).

    The V1 fixture path stays behind ``run_research``; this entry point
    drives the explicit live/V2 search and keeps every network-shaped
    dependency injectable so tests never touch the real network.
    """
    topics.require_choice(run_paths)  # raises TopicGateBlocked when unchosen
    state.transition(run_paths, "research")
    return research.run_initial(
        run_paths,
        aihot_fetch=aihot_fetch,
        http_fetcher=http_fetcher,
        cdp_runner=cdp_runner,
        discover_runner=discover_runner,
        codex_runner=codex_runner,
        progress=progress,
        force=force,
    )


def run_narrative(run_paths, codex_runner=None, force: bool = False) -> dict:
    """04 narrative candidates: evidence router + Codex generation."""
    return narrative.run(run_paths, codex_runner=codex_runner, force=force)


def run_sufficiency(run_paths, codex_runner=None, force: bool = False) -> dict:
    """05 evidence-sufficiency audit for the chosen narrative."""
    return sufficiency.run(run_paths, codex_runner=codex_runner, force=force)


def run_targeted_loop(run_paths, audit_runner=None, discover_runner=None,
                      http_fetcher=None, cdp_runner=None,
                      force: bool = False, initial_audit: dict = None,
                      progress=None) -> dict:
    """06 bounded supplementary research loop (max two rounds)."""
    return targeted.run_loop(
        run_paths,
        audit_runner=audit_runner,
        discover_runner=discover_runner,
        http_fetcher=http_fetcher,
        cdp_runner=cdp_runner,
        force=force,
        initial_audit=initial_audit,
        progress=progress,
    )


def run_outline(run_paths, force: bool = False) -> dict:
    topics.require_choice(run_paths)
    if (run_paths.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).exists():
        narrative.require_narrative(run_paths)
    if (run_paths.work_dir / sufficiency.AUDIT_JSON).exists():
        sufficiency.require_sufficient(run_paths)
    _require_stage_ready(run_paths, "research.json", "research")
    state.transition(run_paths, "outline")
    return outline.run(run_paths, force=force)


def run_draft(run_paths, force: bool = False) -> dict:
    topics.require_choice(run_paths)
    _require_stage_ready(run_paths, outline.OUTLINE_MD, "outline")
    state.transition(run_paths, "draft")
    return draft.run(run_paths, force=force)


def run_draft_en(run_paths, codex_runner=None, force: bool = False) -> dict:
    """07 English full draft: gated on a sufficient audit, then quality-gated."""
    sufficiency.require_writable(run_paths)
    _require_stage_ready(
        run_paths, targeted.EVIDENCE_PACKAGE_JSON, "targeted_research"
    )
    state.transition(run_paths, "draft")
    return draft_en.run(run_paths, codex_runner=codex_runner, force=force)


def regenerate_outline_from_edit(run_paths) -> dict:
    """Rebuild the draft after a human edited the outline file.

    The edited outline is authoritative; collection and research are not
    re-run.  ``collect_runs`` must stay unchanged.
    """
    _require_stage_ready(run_paths, outline.OUTLINE_MD, "outline")
    state.update_fields(run_paths, note="outline edited by human; rebuilding draft")
    state.transition(run_paths, "outline")
    return run_draft(run_paths, force=True)


# ---------------------------------------------------------------------------
# cover / assembly / publish
# ---------------------------------------------------------------------------


def run_cover(run_paths, source_dir=None) -> "cover.CoverResult":
    state.transition(run_paths, "optional_cover")
    result = cover.run(run_paths, source_dir=source_dir)
    state.update_fields(
        run_paths,
        note=f"cover: {'ok' if result.ok else 'skipped'} ({result.reason or result.path})",
    )
    if result.ok:
        state.record_artifact(run_paths, "cover", result.path)
    return result


def run_assemble(run_paths, force: bool = False) -> dict:
    topics.require_choice(run_paths)
    _require_stage_ready(run_paths, draft.ARTICLE_MD, "draft")
    state.transition(run_paths, "assembly")
    result = assemble.run(run_paths, force=force)
    if result["status"] in ("assembled", "resumed"):
        state.transition(run_paths, "completed", note="assembly accepted")
    return result


def run_assemble_en(run_paths, force: bool = False) -> dict:
    """08 English package: assemble the English draft into the durable package."""
    topics.require_choice(run_paths)
    _require_stage_ready(run_paths, draft_en.EN_ARTICLE_MD, "draft-en")
    state.transition(run_paths, "assembly")
    result = assemble_en.run(run_paths, force=force)
    if result["status"] in ("assembled", "resumed"):
        state.transition(run_paths, "completed", note="english assembly accepted")
    return result


def run_claim_check(run_paths, codex_runner=None, force: bool = False) -> dict:
    """Post-draft claim check: verify every assertion against the evidence."""
    _require_stage_ready(run_paths, draft_en.EN_ARTICLE_MD, "draft-en")
    return claim_check.run(run_paths, codex_runner=codex_runner, force=force)


def run_illustrate(run_paths, codex_runner=None, gemini_runner=None,
                   force: bool = False) -> dict:
    """Optional illustration: plan -> generate -> embed.  Never blocks."""
    _require_stage_ready(run_paths, draft_en.EN_ARTICLE_MD, "draft-en")
    return visuals.run_illustrate(
        run_paths,
        codex_runner=codex_runner,
        gemini_runner=gemini_runner,
        force=force,
    )


def run_linkedin_kit(run_paths, codex_runner=None, force: bool = False) -> dict:
    """Optional LinkedIn distribution kit.  Never blocks."""
    return linkedin.run(run_paths, codex_runner=codex_runner, force=force)


def run_publish(run_paths, repo_dir, transport=None, **transport_kwargs):
    from . import publish

    return publish.publish(run_paths, repo_dir, transport=transport, **transport_kwargs)


# ---------------------------------------------------------------------------
# Unattended fixture end-to-end
# ---------------------------------------------------------------------------


def run_fixture_e2e(
    root,
    date: str,
    topic_fixture,
    aihot_fixture,
    cover_source=None,
    repo_dir=None,
    transport=None,
) -> dict:
    """Full unattended fixture run: collect → … → completed (+ publish)."""
    from .paths import RunPaths

    run_paths = RunPaths.for_date(root, date)
    state.init_state(run_paths)

    collect = run_collect(run_paths, mode="fixture", aihot_fixture=aihot_fixture, rss_urls=[])
    topic = run_topic_fixture(run_paths, topic_fixture)
    res = run_research(run_paths)
    out = run_outline(run_paths)
    dra = run_draft(run_paths)
    cov = run_cover(run_paths, source_dir=cover_source)
    asm = run_assemble(run_paths)

    if repo_dir is None:
        repo_dir = run_paths.root / ".local" / "publish" / date
    pub = run_publish(run_paths, repo_dir=repo_dir, transport=transport)

    return {
        "run_id": run_paths.run_id,
        "slug": topic["slug"],
        "collect": collect,
        "research": res["status"],
        "outline": out["status"],
        "draft": dra["status"],
        "cover_ok": cov.ok,
        "assembly": asm["status"],
        "final_article": str(asm["final_article"]),
        "publish_mode": pub.mode,
        "stage": state.read_state(run_paths)["stage"],
    }

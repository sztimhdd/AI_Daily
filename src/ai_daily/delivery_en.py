"""Best-effort daily delivery for the English edition."""

from __future__ import annotations

import json

from . import assemble_en, claim_check, draft_en, linkedin, publish, state, visuals


SUMMARY_JSON = "delivery-en.json"


def _warning(result: dict) -> dict:
    status = result.get("status", "unavailable")
    if status in ("unavailable", "degraded"):
        return {"status": "warning" if status == "unavailable" else "degraded",
                "reason": result.get("reason", "")}
    return {"status": status, "reason": result.get("reason", "")}


def _persist(run_paths, summary: dict) -> dict:
    path = run_paths.work_dir / SUMMARY_JSON
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    state.record_artifact(run_paths, "delivery-en", str(path.relative_to(run_paths.root)))
    return {**summary, "summary": path}


def _failed(run_paths, summary: dict, reason: str) -> dict:
    summary["status"] = "failed"
    summary["reason"] = reason
    summary["assembly"] = {"status": "skipped", "reason": reason}
    return _persist(run_paths, summary)


def run(run_paths, *, codex_runner=None, gemini_runner=None, repo_dir=None,
        transport=None, force: bool = False, **transport_kwargs) -> dict:
    """Deliver an English package; soft review/enrichment failures are visible."""
    summary = {
        "run_id": run_paths.run_id,
        "status": "running",
        "draft": {"status": "pending"},
        "claim_check": {"status": "pending"},
        "images": {"status": "pending"},
        "linkedin_kit": {"status": "pending"},
        "assembly": {"status": "pending"},
        "publication": {"status": "pending", "reason": "not requested"},
    }
    try:
        draft = draft_en.run(run_paths, codex_runner=codex_runner, force=force)
    except Exception as exc:
        return _failed(run_paths, summary, f"draft failed: {type(exc).__name__}: {exc}")
    summary["draft"] = _warning(draft)
    if draft.get("status") == "unavailable":
        return _failed(run_paths, summary, draft.get("reason", "draft unavailable"))

    try:
        summary["claim_check"] = _warning(
            claim_check.run(run_paths, codex_runner=codex_runner, force=force)
        )
    except Exception as exc:
        summary["claim_check"] = {"status": "warning", "reason": str(exc)}
    try:
        images = visuals.run_illustrate(
            run_paths, codex_runner=codex_runner, gemini_runner=gemini_runner,
            force=force,
        )
        summary["images"] = _warning(images)
    except Exception as exc:
        summary["images"] = {"status": "degraded", "reason": str(exc)}
    if summary["images"]["status"] == "warning":
        summary["images"]["status"] = "degraded"
    try:
        kit = linkedin.run(run_paths, codex_runner=codex_runner, force=force)
        summary["linkedin_kit"] = _warning(kit)
    except Exception as exc:
        summary["linkedin_kit"] = {"status": "degraded", "reason": str(exc)}
    if summary["linkedin_kit"]["status"] == "warning":
        summary["linkedin_kit"]["status"] = "degraded"

    try:
        assembly = assemble_en.run(run_paths, force=force)
    except Exception as exc:
        return _failed(run_paths, summary, f"assembly failed: {type(exc).__name__}: {exc}")
    summary["assembly"] = _warning(assembly)
    summary["package_dir"] = str(assembly["package_dir"])
    summary["final_article"] = str(assembly["final_article"])
    if repo_dir is not None:
        try:
            publication = publish.publish_en(
                run_paths, repo_dir=repo_dir, transport=transport,
                **transport_kwargs,
            )
            summary["publication"] = {
                "status": publication.mode, "reason": publication.reason,
                "article": publication.published_relpath,
            }
        except Exception as exc:
            summary["publication"] = {"status": "failed", "reason": str(exc)}
    summary["status"] = "delivered"
    result = _persist(run_paths, summary)
    result["package_dir"] = assembly["package_dir"]
    result["final_article"] = assembly["final_article"]
    return result

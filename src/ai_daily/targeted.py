"""06 targeted research loop: bounded supplementary evidence rounds.

Consumes the 05 audit's atomic research_tasks, routes each through the
01 lane seam (explicit URL -> fetch; query -> zhida discovery -> fetch),
then re-audits.  The loop ceiling is two supplementary rounds; the final
verdict closes as one of the three audit states, never left hanging.
"""

from __future__ import annotations

import json

from . import fetch, narrative, research, state, sufficiency

TARGETED_JSON = "targeted-evidence.json"
EVIDENCE_PACKAGE_JSON = "evidence-package.json"
MAX_ROUNDS = 2
MAX_URLS_PER_TASK = 3


class TargetedError(RuntimeError):
    """Raised when the supplementary loop cannot honestly run."""


def _execute_tasks(run_paths, tasks: list, discover_runner=None,
                   http_fetcher=None, cdp_runner=None) -> list:
    """Execute atomic research tasks through the 01 lane seam."""
    entries, seen = [], set()
    for task in tasks or []:
        gap_type = task.get("gap_type", "")
        urls = []
        if task.get("url"):
            urls = [task["url"]]
        elif task.get("query"):
            for link in fetch.discover(
                task["query"], runner=discover_runner
            )[:MAX_URLS_PER_TASK]:
                if isinstance(link, dict) and link.get("url"):
                    urls.append(link["url"])
        for url in urls:
            if not str(url).startswith("http") or url in seen:
                continue
            seen.add(url)
            result = fetch.fetch(
                url, run_paths,
                http_fetcher=http_fetcher, cdp_runner=cdp_runner,
            )
            entries.append({
                "url": result.url,
                "title": result.title,
                "status": result.status,
                "source_lane": result.source_lane,
                "sha256": result.sha256,
                "excerpt": research._evidence_excerpt(result.markdown, result.title),
                "gap_type": gap_type,
            })
    return entries


def run_loop(run_paths, audit_runner=None, discover_runner=None,
             http_fetcher=None, cdp_runner=None, force: bool = False,
             initial_audit: dict = None, progress=None) -> dict:
    """Audit -> targeted rounds (max 2) -> final verdict + evidence package."""
    narrative.require_narrative(run_paths)
    package_path = run_paths.work_dir / EVIDENCE_PACKAGE_JSON
    if package_path.exists() and not force:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        targeted_data = json.loads(
            (run_paths.work_dir / TARGETED_JSON).read_text(encoding="utf-8")
        )
        return {
            "status": "resumed",
            "verdict": package.get("audit_verdict"),
            "reason": package.get("reason", ""),
            "rounds": len(targeted_data.get("rounds", [])),
            "evidence_package": package_path,
        }
    osint_path = run_paths.work_dir / research.INITIAL_OSINT_JSON
    if not osint_path.exists():
        raise TargetedError(
            "initial-osint.json missing; run the live research stage first"
        )
    osint = json.loads(osint_path.read_text(encoding="utf-8"))
    rounds = []
    if initial_audit is not None and initial_audit.get("status") == "completed":
        audit = initial_audit
    else:
        audit = sufficiency.run(run_paths, codex_runner=audit_runner,
                                force=force, round_number=1)
    if audit.get("status") == "unavailable":
        return {"status": "unavailable", "verdict": "unavailable",
                "reason": audit.get("reason", ""), "rounds": 0}
    extra = []
    if audit["verdict"] != "sufficient":
        while audit["verdict"] == "needs_research" and len(rounds) < MAX_ROUNDS:
            tasks = audit.get("research_tasks") or []
            if progress:
                progress("round_start", {"round": len(rounds) + 1,
                                         "tasks": len(tasks)})
            entries = _execute_tasks(
                run_paths, tasks,
                discover_runner=discover_runner,
                http_fetcher=http_fetcher,
                cdp_runner=cdp_runner,
            )
            rounds.append(entries)
            extra.extend(entries)
            state.transition(run_paths, "targeted_research")
            if progress:
                progress("re_audit", {"round": len(rounds) + 1})
            audit = sufficiency.run(
                run_paths, codex_runner=audit_runner, force=True,
                extra_evidence=extra, round_number=len(rounds) + 1,
            )
            if audit.get("status") == "unavailable":
                return {"status": "unavailable",
                        "verdict": audit.get("verdict", "unavailable"),
                        "reason": audit.get("reason", ""),
                        "rounds": len(rounds)}

    (run_paths.work_dir / TARGETED_JSON).write_text(
        json.dumps(
            {"rounds": [{"round": i + 1, "entries": entries}
                        for i, entries in enumerate(rounds)]},
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    state.record_artifact(
        run_paths, "targeted-evidence",
        str((run_paths.work_dir / TARGETED_JSON).relative_to(run_paths.root)),
    )
    package = {
        "run_id": run_paths.run_id,
        "topic_title": state.read_state(run_paths).get("topic_title", ""),
        "narrative_title": audit.get("narrative_title", ""),
        "audit_verdict": audit.get("verdict"),
        "reason": audit.get("reason", ""),
        "sources": (
            [{
                "url": s.get("url"), "title": s.get("title"),
                "status": s.get("status"), "source_lane": s.get("source_lane"),
                "excerpt": s.get("excerpt"), "origin": "initial",
                "sha256": s.get("sha256", ""), "error": s.get("error", ""),
                "fetched_at": s.get("fetched_at", ""),
            } for s in osint.get("sources") or []]
            + [{"origin": "targeted", **e} for e in extra]
        ),
    }
    (run_paths.work_dir / EVIDENCE_PACKAGE_JSON).write_text(
        json.dumps(package, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    state.record_artifact(
        run_paths, "evidence-package",
        str((run_paths.work_dir / EVIDENCE_PACKAGE_JSON).relative_to(
            run_paths.root
        )),
    )
    return {
        "status": "completed",
        "verdict": audit.get("verdict"),
        "reason": audit.get("reason", ""),
        "rounds": len(rounds),
        "evidence_package": run_paths.work_dir / EVIDENCE_PACKAGE_JSON,
    }

"""Durable run state: one state.md per daily run.

The state document is Markdown with machine-parseable ``- key: value``
fields plus ``## stage_log``, ``## artifacts`` and ``## counters``
sections.  It is the single source of truth for stage, decisions,
artifact references and the last error.
"""

from __future__ import annotations

import datetime

from . import STAGES
from .paths import RunPaths, list_state_files  # re-exported for callers

FIELD_KEYS = [
    "run_id",
    "date",
    "stage",
    "status",
    "slug",
    "topic_choice",
    "topic_title",
    "en_title",
    "en_slug",
    "narrative_choice",
    "narrative_title",
    "narrative_archetype",
    "narrative_extra_research",
    "narrative_directive",
    "last_error",
    "updated_at",
]


class StateError(RuntimeError):
    """Raised for invalid state transitions or unreadable state."""


def _now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _default_state(run_paths: RunPaths) -> dict:
    return {
        "run_id": run_paths.run_id,
        "date": run_paths.date,
        "stage": "collect",
        "status": "pending",
        "slug": "",
        "topic_choice": "",
        "topic_title": "",
        "last_error": "",
        "updated_at": _now(),
        "stage_log": [],
        "artifacts": {},
        "counters": {},
    }


def init_state(run_paths: RunPaths) -> dict:
    """Create state.md for the date if missing; never mix other dates."""
    run_paths.ensure_work_dir()
    if run_paths.state_file.exists():
        return read_state(run_paths)
    st = _default_state(run_paths)
    _write(run_paths, st)
    return st


def read_state(run_paths: RunPaths) -> dict:
    if not run_paths.state_file.exists():
        raise StateError(f"no state.md for run {run_paths.run_id}; run init first")
    text = run_paths.state_file.read_text(encoding="utf-8")
    st = _default_state(run_paths)
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.startswith("- "):
            continue
        body = line[2:]
        if section is None:
            if ": " in body or body.endswith(":"):
                key, _, value = body.partition(":")
                key = key.strip()
                value = value.strip()
                if key in FIELD_KEYS:
                    st[key] = value
        elif section == "stage_log":
            st["stage_log"].append(body)
        elif section == "artifacts" and ": " in body:
            key, _, value = body.partition(":")
            st["artifacts"][key.strip()] = value.strip()
        elif section == "counters" and ": " in body:
            key, _, value = body.partition(":")
            try:
                st["counters"][key.strip()] = int(value.strip())
            except ValueError:
                st["counters"][key.strip()] = 0
    return st


def _write(run_paths: RunPaths, st: dict) -> None:
    st["updated_at"] = _now()
    lines = [f"# Run {st['run_id']}", ""]
    for key in FIELD_KEYS:
        if key == "updated_at":
            lines.append(f"- updated_at: {st['updated_at']}")
        else:
            lines.append(f"- {key}: {st.get(key, '')}")
    lines += ["", "## stage_log", ""]
    lines += [f"- {entry}" for entry in st["stage_log"]]
    lines += ["", "## artifacts", ""]
    lines += [f"- {k}: {v}" for k, v in sorted(st["artifacts"].items())]
    lines += ["", "## counters", ""]
    lines += [f"- {k}: {v}" for k, v in sorted(st["counters"].items())]
    lines.append("")
    text = "\n".join(line.rstrip() for line in lines)
    run_paths.state_file.write_text(text, encoding="utf-8")


def transition(run_paths: RunPaths, stage: str, note: str = "") -> dict:
    if stage not in STAGES:
        raise StateError(f"unknown stage: {stage!r} (V1 stages: {', '.join(STAGES)})")
    st = read_state(run_paths)
    st["stage"] = stage
    if stage == "completed":
        st["status"] = "completed"
    elif st["status"] in ("pending", "failed", "completed"):
        st["status"] = "in_progress"
    entry = f"{_now()} -> {stage}"
    if note:
        entry += f" ({note})"
    st["stage_log"].append(entry)
    _write(run_paths, st)
    return st


def update_fields(run_paths: RunPaths, note: str = "", **fields) -> dict:
    st = read_state(run_paths)
    for key, value in fields.items():
        if key not in FIELD_KEYS and key not in ("stage",):
            raise StateError(f"unknown state field: {key!r}")
        st[key] = value
    if note:
        st["stage_log"].append(f"{_now()} note: {note}")
    _write(run_paths, st)
    return st


def fail(run_paths: RunPaths, where: str, message: str) -> dict:
    st = read_state(run_paths)
    st["status"] = "failed"
    st["last_error"] = f"{where}: {message}"
    st["stage_log"].append(f"{_now()} FAILED at {where}: {message}")
    _write(run_paths, st)
    return st


def clear_error(run_paths: RunPaths) -> dict:
    st = read_state(run_paths)
    st["last_error"] = ""
    if st["status"] == "failed":
        st["status"] = "in_progress"
    _write(run_paths, st)
    return st


def record_artifact(run_paths: RunPaths, name: str, ref: str) -> dict:
    st = read_state(run_paths)
    st["artifacts"][name] = ref
    _write(run_paths, st)
    return st


def bump_counter(run_paths: RunPaths, name: str) -> dict:
    st = read_state(run_paths)
    st["counters"][name] = int(st["counters"].get(name, 0)) + 1
    _write(run_paths, st)
    return st

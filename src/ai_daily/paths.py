"""Run path resolution for one daily editorial run.

A run is identified by a stable date-based id, ``AI-Daily/YYYY-MM-DD``.
Before a topic is chosen the run lives under ``.local/runs/<date>/``
(ignorable runtime state).  After the topic choice the durable article
package lives under ``outputs/YYYY/MM/DD/<slug>/`` and the publishable
article at ``articles/YYYY-MM-DD-<slug>-zh.md``.
"""

from __future__ import annotations

import datetime
import pathlib
import re

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class RunPathError(ValueError):
    """Raised for invalid dates, slugs, or path requests."""


def validate_date(date: str) -> str:
    try:
        datetime.date.fromisoformat(date)
    except ValueError as exc:
        raise RunPathError(f"invalid run date: {date!r}") from exc
    return date


def validate_slug(slug: str) -> str:
    if not SLUG_RE.match(slug or "") or slug in {".", ".."}:
        raise RunPathError(f"invalid article slug: {slug!r} (want lowercase kebab-case)")
    return slug


class RunPaths:
    """All filesystem locations for one dated run."""

    def __init__(self, root: pathlib.Path, date: str):
        self.root = pathlib.Path(root)
        self.date = validate_date(date)
        self.run_id = f"AI-Daily/{self.date}"

    @classmethod
    def for_date(cls, root, date: str) -> "RunPaths":
        return cls(pathlib.Path(root), date)

    # -- pre-selection working state (never mixed across dates) ---------
    @property
    def work_dir(self) -> pathlib.Path:
        return self.root / ".local" / "runs" / self.date

    @property
    def state_file(self) -> pathlib.Path:
        return self.work_dir / "state.md"

    def ensure_work_dir(self) -> pathlib.Path:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        return self.work_dir

    # -- durable package after topic choice ------------------------------
    def package_dir(self, slug: str) -> pathlib.Path:
        validate_slug(slug)
        y, m, d = self.date.split("-")
        return self.root / "outputs" / y / m / d / slug

    def final_article_path(self, slug: str) -> pathlib.Path:
        validate_slug(slug)
        return self.root / "articles" / f"{self.date}-{slug}-zh.md"


def list_state_files(root) -> list:
    """All state.md files under .local/runs (one per date)."""
    root = pathlib.Path(root)
    runs = root / ".local" / "runs"
    if not runs.is_dir():
        return []
    return sorted(p for p in runs.glob("*/state.md") if p.is_file())

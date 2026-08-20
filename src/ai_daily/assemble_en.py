"""English package assembly: article-en.md + sources-en.md + metadata-en.json.

Mirrors ``assemble.py`` for the English edition.  Outputs land alongside the
Chinese package in the same slug directory, using ``-en`` file names so the
two editions coexist without conflict:

- ``outputs/YYYY/MM/DD/<slug>/article-en.md``
- ``outputs/YYYY/MM/DD/<slug>/sources-en.md``
- ``outputs/YYYY/MM/DD/<slug>/metadata-en.json``
- ``articles/<date>-<slug>-en.md`` — the final publishable English article

Cover handling stays optional: a missing or invalid cover never blocks
assembly (the "images never block the body" rule).
"""

from __future__ import annotations

import json
import re

from . import assemble, draft_en, state, topics

ARTICLE_EN_FILE = "article-en.md"
SOURCES_EN_FILE = "sources-en.md"
METADATA_EN_FILE = "metadata-en.json"

_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")


class AssembleEnError(RuntimeError):
    """Raised when the English draft fails assembly validation."""


def _read_evidence(run_paths) -> dict:
    path = run_paths.work_dir / draft_en.EVIDENCE_PACKAGE_JSON
    if not path.exists():
        return {"sources": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sources": []}


def _collect_sources(evidence: dict) -> list:
    sources, seen = [], set()
    for src in evidence.get("sources") or []:
        if not isinstance(src, dict):
            continue
        url = src.get("url")
        if url and url not in seen:
            seen.add(url)
            sources.append(
                {
                    "title": src.get("title") or url,
                    "url": url,
                    "origin": src.get("origin", "evidence"),
                    "status": src.get("status", ""),
                }
            )
    return sources


def _render_sources_md(topic_title: str, sources: list) -> str:
    lines = [f"# Sources and evidence: {topic_title}", ""]
    lines.append(f"{len(sources)} deduplicated source(s) from the evidence package.")
    lines.append("")
    for src in sources:
        status = f" · {src['status']}" if src.get("status") else ""
        lines.append(f"- [{src['title']}]({src['url']})（{src['origin']}{status}）")
    lines.append("")
    return "\n".join(lines)


def run(run_paths, force: bool = False) -> dict:
    """Validate, package, and map the final English article."""
    topic = topics.require_choice(run_paths)
    slug = topic["slug"]
    package_dir = run_paths.package_dir(slug)
    final_path = run_paths.final_article_en_path(slug)

    if (
        (package_dir / ARTICLE_EN_FILE).is_file()
        and (package_dir / SOURCES_EN_FILE).is_file()
        and (package_dir / METADATA_EN_FILE).is_file()
        and final_path.is_file()
        and not force
    ):
        return {
            "status": "resumed",
            "package_dir": package_dir,
            "final_article": final_path,
        }

    draft_path = run_paths.work_dir / draft_en.EN_ARTICLE_MD
    if not draft_path.is_file():
        raise AssembleEnError(
            f"no english draft to assemble: {draft_path} (run draft-en first)"
        )
    text = draft_path.read_text(encoding="utf-8")
    problems = assemble.validate_article(text)
    if problems:
        raise AssembleEnError("assembly rejected: " + "; ".join(problems))

    evidence = _read_evidence(run_paths)
    sources = _collect_sources(evidence)

    # Every link cited in the article must be listed in sources-en.md so the
    # package never loses provenance.
    cited = set(_LINK_RE.findall(text))
    known = {s["url"] for s in sources}
    for url in sorted(cited):
        if url not in known:
            sources.append({"title": url, "url": url, "origin": "article"})

    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / ARTICLE_EN_FILE).write_text(text, encoding="utf-8")
    (package_dir / SOURCES_EN_FILE).write_text(
        _render_sources_md(topic["title"], sources), encoding="utf-8"
    )

    cover_info = assemble._adopt_cover(run_paths, package_dir)
    metadata = {
        "run_id": run_paths.run_id,
        "date": run_paths.date,
        "slug": slug,
        "title": topic["title"],
        "language": "en",
        "topic_choice": state.read_state(run_paths).get("topic_choice", ""),
        "has_cover": cover_info is not None,
        "cover": cover_info,
        "sources": sources,
        "final_article": str(final_path.relative_to(run_paths.root)),
        "package": str(package_dir.relative_to(run_paths.root)),
    }
    (package_dir / METADATA_EN_FILE).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(text, encoding="utf-8")

    state.record_artifact(
        run_paths, "package-en",
        str(package_dir.relative_to(run_paths.root)),
    )
    state.record_artifact(
        run_paths, "final-article-en",
        str(final_path.relative_to(run_paths.root)),
    )
    if cover_info:
        state.record_artifact(run_paths, "cover-en", cover_info["file"])
    return {
        "status": "assembled",
        "package_dir": package_dir,
        "final_article": final_path,
        "has_cover": cover_info is not None,
    }

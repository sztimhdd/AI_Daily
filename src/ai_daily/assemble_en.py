"""English package assembly (English-first edition).

The English edition is named by its own English title, never the Chinese
topic slug, and never the generic word "article".  Outputs land in an
English-slugged package directory:

- ``outputs/YYYY/MM/DD/<en-slug>/<en-slug>.md``
- ``outputs/YYYY/MM/DD/<en-slug>/sources.md``
- ``outputs/YYYY/MM/DD/<en-slug>/metadata.json``
- ``articles/<date>-<en-slug>-en.md`` — the final publishable English article

Cover handling stays optional: a missing or invalid cover never blocks
assembly (the "images never block the body" rule).
"""

from __future__ import annotations

import json
import re
import datetime
from urllib.parse import urlsplit

from . import assemble, draft_en, paths, state, topics

_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")


class AssembleEnError(RuntimeError):
    """Raised when the English draft fails assembly validation."""


def _en_title_slug(run_paths) -> tuple:
    """English title + slug, from the draft stage's state, else the H1."""
    st = state.read_state(run_paths)
    en_title = st.get("en_title", "")
    en_slug = st.get("en_slug", "")
    if en_title and en_slug:
        return en_title, en_slug
    draft_path = run_paths.work_dir / draft_en.EN_ARTICLE_MD
    if draft_path.is_file():
        lines = draft_path.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            if title:
                return title, paths.slugify_title(title, run_paths.date)
    raise AssembleEnError("no english title; run draft-en first")


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


def _read_quality(run_paths) -> dict:
    path = run_paths.work_dir / draft_en.QUALITY_JSON
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_audit(run_paths) -> dict:
    path = run_paths.work_dir / "sufficiency-audit.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _display_title(src: dict) -> str:
    """A presentable source title: fallback for failed fetches, language tag."""
    title = (src.get("title") or "").strip()
    status = str(src.get("status") or "").lower()
    if status != "fetched":
        if not title or title.startswith("http"):
            host = (urlsplit(src.get("url") or "").hostname or "").strip()
            return f"{host or 'unknown source'} (fetch failed)"
        return f"{title} (fetch failed)"
    if not title or title.startswith("http"):
        host = (urlsplit(src.get("url") or "").hostname or "").strip()
        return host or "unknown source"
    return title


def _render_sources_md(topic_title: str, sources: list) -> str:
    lines = [f"# Sources and evidence: {topic_title}", ""]
    lines.append(f"{len(sources)} deduplicated source(s) from the evidence package.")
    lines.append("")
    for src in sources:
        status = f" · {src['status']}" if src.get("status") else ""
        title = _display_title(src)
        lang = " · Chinese source" if _CJK_RE.search(title) else ""
        lines.append(
            f"- [{title}]({src['url']})（{src['origin']}{status}{lang}）"
        )
    lines.append("")
    return "\n".join(lines)


def run(run_paths, force: bool = False) -> dict:
    """Validate, package, and map the final English article."""
    topics.require_choice(run_paths)
    en_title, en_slug = _en_title_slug(run_paths)
    package_dir = run_paths.package_dir(en_slug)
    final_path = run_paths.final_article_en_path(en_slug)
    article_file = paths.article_file_name(en_slug)

    if (
        (package_dir / article_file).is_file()
        and (package_dir / "sources.md").is_file()
        and (package_dir / "metadata.json").is_file()
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
    (package_dir / article_file).write_text(text, encoding="utf-8")
    (package_dir / "sources.md").write_text(
        _render_sources_md(en_title, sources), encoding="utf-8"
    )

    cover_info = assemble._adopt_cover(run_paths, package_dir)
    quality_record = _read_quality(run_paths)
    audit = _read_audit(run_paths)
    evidence_verdict = audit.get("verdict") or evidence.get("audit_verdict", "")
    metadata = {
        "run_id": run_paths.run_id,
        "date": run_paths.date,
        "slug": en_slug,
        "title": en_title,
        "language": "en",
        "topic_choice": state.read_state(run_paths).get("topic_choice", ""),
        "quality": quality_record,
        "evidence_verdict": evidence_verdict,
        "downgraded": bool(quality_record.get("downgraded")
                           or evidence_verdict == "needs_research"),
        "evidence_caveats": audit.get("evidence_gaps") or [],
        "source_count": len(sources),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds"
        ),
        "seo_title": "",
        "seo_summary": "",
        "has_cover": cover_info is not None,
        "cover": cover_info,
        "sources": sources,
        "final_article": str(final_path.relative_to(run_paths.root)),
        "package": str(package_dir.relative_to(run_paths.root)),
    }
    (package_dir / "metadata.json").write_text(
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

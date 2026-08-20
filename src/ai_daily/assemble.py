"""Assembly: validate the draft, build the durable package, map final.

Assembly is the quality gate before publishing.  It refuses to package
an article that is empty, missing a title, or carries placeholders and
debug artifacts (``{[IMG_x]}``, ``{{ $json }}`` n8n expressions, bare
``[IMG_x]`` markers), published-article residue (raw HTML tags, ellipsis
sequences, truncated URL fragments), or nothing at all.  Source links
must survive into the package.

Outputs:

- ``outputs/YYYY/MM/DD/<slug>/`` with ``article.md``, ``metadata.json``,
  ``sources.md`` and ``images/cover.<ext>`` when a valid cover exists.
- ``articles/<date>-<slug>-zh.md`` — the final publishable article.

Cover handling is optional: a missing or invalid cover never blocks
assembly; it is simply excluded and ``has_cover`` stays false.
"""

from __future__ import annotations

import json
import pathlib
import re

from . import cover as cover_mod
from . import paths, state, topics

DRAFT_FILE = "article.md"
RESEARCH_JSON = "research.json"
SELECTED_TOPIC = "selected-topic.json"

_PLACEHOLDER_RES = (
    re.compile(r"\{\[\s*IMG_\d+\s*\]\}", re.I),   # {[IMG_1]}
    re.compile(r"\[\s*IMG_\d+\s*\]", re.I),        # [IMG_1]
    re.compile(r"\{\{.*?\}\}", re.S),              # n8n/template expressions
)

_LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")

# Published-article residue: raw HTML and ellipsis-truncated fragments
# leaked from capped feed summaries must never ship.
_RESIDUE_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^<>]*)?>")
_RESIDUE_HTML_UNCLOSED_RE = re.compile(r"<[a-zA-Z/][^<>\n]*$", re.M)
_RESIDUE_ELLIPSIS_RE = re.compile(r"\u2026|\.{3,}")
_RESIDUE_TRUNCATED_URL_RE = re.compile(
    r"https?://\S*?(?:\u2026|\.{3,})"
    r"|(?<![(\]\w])https?://[a-zA-Z0-9-]+(?=[\s，。；：、！？（）]|$)",
    re.M,
)


class AssembleError(RuntimeError):
    """Raised when the draft fails the assembly quality gate."""


def validate_article(text: str) -> list:
    """Return a list of problems (empty list means the draft is clean)."""
    problems = []
    stripped = (text or "").strip()
    if not stripped:
        problems.append("article is empty")
        return problems
    first_line = stripped.splitlines()[0]
    if not first_line.startswith("# "):
        problems.append("article must start with an H1 title line")
    for rx in _PLACEHOLDER_RES:
        m = rx.search(text)
        if m:
            problems.append(f"placeholder/debug artifact: {m.group(0)!r}")
    for rx in (_RESIDUE_HTML_TAG_RE, _RESIDUE_HTML_UNCLOSED_RE):
        m = rx.search(text)
        if m:
            problems.append(f"raw HTML tag: {m.group(0)!r}")
    m = _RESIDUE_ELLIPSIS_RE.search(text)
    if m:
        problems.append(f"ellipsis residue: {m.group(0)!r}")
    m = _RESIDUE_TRUNCATED_URL_RE.search(text)
    if m:
        problems.append(f"truncated URL fragment: {m.group(0)!r}")
    if not _LINK_RE.search(text):
        problems.append("article carries no source links")
    return problems


def _read_research(run_paths) -> dict:
    path = run_paths.work_dir / RESEARCH_JSON
    if not path.exists():
        return {"questions": [], "evidence_urls": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"questions": [], "evidence_urls": []}


def _collect_sources(topic: dict, research: dict) -> list:
    """Deduplicated sources: topic candidates first, then research evidence."""
    sources, seen = [], set()

    def add(title, url, origin):
        if url and url not in seen:
            seen.add(url)
            sources.append({"title": title, "url": url, "origin": origin})

    for src in topic.get("sources") or []:
        add(src.get("title", ""), src.get("url", ""), src.get("origin", "topic"))
    for q in research.get("questions") or []:
        for ev in q.get("evidence") or []:
            add(ev.get("title", ""), ev.get("url", ""), ev.get("origin", "research"))
    return sources


def _render_sources_md(topic: dict, sources: list) -> str:
    lines = [f"# 来源与证据：{topic['title']}", ""]
    lines.append(f"共 {len(sources)} 个去重后的来源（选题候选 + research 证据）。")
    lines.append("")
    for src in sources:
        lines.append(f"- [{src['title']}]({src['url']})（{src['origin']}）")
    lines.append("")
    return "\n".join(lines)


def _adopt_cover(run_paths, package_dir: pathlib.Path):
    """Copy a valid work-dir cover into images/; never block on it."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        candidate = run_paths.work_dir / f"cover.{ext}"
        if not candidate.is_file():
            continue
        result = cover_mod.validate_cover(candidate)
        if not result.ok:
            continue
        images = package_dir / "images"
        images.mkdir(parents=True, exist_ok=True)
        dest = images / f"cover.{ext}"
        dest.write_bytes(candidate.read_bytes())
        return {
            "file": f"images/cover.{ext}",
            "format": result.format,
            "width": result.width,
            "height": result.height,
        }
    return None


def run(run_paths, force: bool = False) -> dict:
    """Validate, package and map the final article.  Raises on bad draft."""
    topic = topics.require_choice(run_paths)
    slug = topic["slug"]
    package_dir = run_paths.package_dir(slug)
    final_path = run_paths.final_article_path(slug)
    article_file = paths.article_file_name(slug)

    if (
        (package_dir / article_file).is_file()
        and (package_dir / "metadata.json").is_file()
        and (package_dir / "sources.md").is_file()
        and final_path.is_file()
        and not force
    ):
        return {
            "status": "resumed",
            "package_dir": package_dir,
            "final_article": final_path,
        }

    draft_path = run_paths.work_dir / DRAFT_FILE
    if not draft_path.is_file():
        raise AssembleError(f"no draft to assemble: {draft_path} (run draft first)")
    text = draft_path.read_text(encoding="utf-8")
    problems = validate_article(text)
    if problems:
        raise AssembleError("assembly rejected: " + "; ".join(problems))

    research = _read_research(run_paths)
    sources = _collect_sources(topic, research)

    # Every link cited in the article must be listed in sources.md so the
    # package never loses provenance.
    cited = set(_LINK_RE.findall(text))
    known = {s["url"] for s in sources}
    for url in sorted(cited):
        if url not in known:
            sources.append({"title": url, "url": url, "origin": "article"})

    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / article_file).write_text(text, encoding="utf-8")
    (package_dir / "sources.md").write_text(
        _render_sources_md(topic, sources), encoding="utf-8"
    )

    cover_info = _adopt_cover(run_paths, package_dir)
    metadata = {
        "run_id": run_paths.run_id,
        "date": run_paths.date,
        "slug": slug,
        "title": topic["title"],
        "topic_choice": state.read_state(run_paths).get("topic_choice", ""),
        "has_cover": cover_info is not None,
        "cover": cover_info,
        "sources": sources,
        "final_article": str(final_path.relative_to(run_paths.root)),
        "package": str(package_dir.relative_to(run_paths.root)),
    }
    (package_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(text, encoding="utf-8")

    state.record_artifact(
        run_paths, "package", str(package_dir.relative_to(run_paths.root))
    )
    state.record_artifact(
        run_paths, "final-article", str(final_path.relative_to(run_paths.root))
    )
    if cover_info:
        state.record_artifact(run_paths, "cover", cover_info["file"])
    return {
        "status": "assembled",
        "package_dir": package_dir,
        "final_article": final_path,
        "has_cover": cover_info is not None,
    }

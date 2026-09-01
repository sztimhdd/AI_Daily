"""Unified fetch primitive for the three lanes (http / cdp / zhida).

Contract:

- ``FetchResult`` is the single return structure for every lane, so
  callers never branch on transport details.
- ``route_lane`` sends walled-platform hosts (zhihu.com,
  mp.weixin.qq.com and their subdomains) to the ``cdp`` lane; every
  other host uses plain ``http``.
- ``http_fetch`` never raises: network/HTTP errors become
  ``status="failed"`` with the exception text recorded in ``error``;
  an empty body becomes ``status="partial"``.
- ``cdp_fetch`` shells out to the locally installed walled-fetch-cdp
  skill and never raises; the skill's own status (``fetched``,
  ``partial``, ``failed``, ``login_required``) is passed through
  unchanged.
- ``fetch`` adds lane routing plus idempotent persistence under
  ``.local/runs/<date>/fetch/<sha1(lane:url)[:12]>.{md,json}``; a
  cached hit is served without re-fetching unless ``force=True``.
- ``discover`` is the zhida discovery lane: it fetches a zhihu search
  page through the cdp lane and returns candidate question links.

All network access is injectable (``fetch`` / ``runner`` callables);
the module itself never touches the browser or the network during
tests.  Standard library only.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import html as html_mod
import json
import pathlib
import re
import subprocess
import urllib.parse
import urllib.request

DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
DEFAULT_SKILL_ROOT = "/Users/hai/.agents/skills/walled-fetch-cdp"

_WALLED_HOSTS = ("zhihu.com", "mp.weixin.qq.com")
_BODY_RE = re.compile(r"<body\b[^>]*>(.*)</body>", re.IGNORECASE | re.DOTALL)
_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL
)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINE_RE = re.compile(r"\n[ \t]*\n+")
_META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_ACTIVITY_NAME_RE = re.compile(
    r"<[^>]+(?:id|class)\s*=\s*[\"']activity-name[\"'][^>]*>(.*?)</[^>]+>",
    re.IGNORECASE | re.DOTALL,
)
_TITLE_TAG_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
@dataclasses.dataclass
class FetchResult:
    """One normalized fetch outcome shared by all three lanes."""

    url: str
    title: str
    markdown: str
    sha256: str
    status: str  # fetched | partial | failed | login_required | unavailable
    source_lane: str  # http | cdp | zhida
    error: str = ""
    fetched_at: str = ""


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def route_lane(url: str) -> str:
    """Route walled-platform hosts to ``cdp``, everything else to ``http``."""
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    for suffix in _WALLED_HOSTS:
        if host == suffix or host.endswith("." + suffix):
            return "cdp"
    return "http"


def _default_http_fetch(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": DESKTOP_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _body_html(text: str) -> str:
    match = _BODY_RE.search(text)
    return match.group(1) if match else text


def html_to_markdown(text: str) -> str:
    """Textify HTML body: strip scripts/styles/tags, collapse whitespace."""
    body = _body_html(text)
    body = _SCRIPT_STYLE_RE.sub(" ", body)
    body = _TAG_RE.sub(" ", body)
    body = html_mod.unescape(body)
    body = _SPACE_RE.sub(" ", body)
    body = _BLANK_LINE_RE.sub("\n\n", body)
    return body.strip()


def _meta_content(text: str, key: str) -> str:
    """Value of the first ``<meta (property|name)=key content=...>`` tag."""
    for tag in _META_TAG_RE.findall(text):
        if re.search(
            r"\b(?:property|name)\s*=\s*[\"']" + re.escape(key) + r"[\"']",
            tag,
            re.IGNORECASE,
        ):
            match = re.search(
                r"\bcontent\s*=\s*[\"']([^\"']*)[\"']", tag, re.IGNORECASE
            )
            if match:
                return html_mod.unescape(match.group(1)).strip()
    return ""


def extract_title(text: str) -> str:
    """Title from og:title, then activity-name, then ``<title>``."""
    og = _meta_content(text, "og:title")
    if og:
        return og
    match = _ACTIVITY_NAME_RE.search(text)
    if match:
        title = _TAG_RE.sub(" ", match.group(1))
        title = " ".join(html_mod.unescape(title).split())
        if title:
            return title
    match = _TITLE_TAG_RE.search(text)
    if match:
        return " ".join(html_mod.unescape(match.group(1)).split())
    return ""


def extract_summary(text: str) -> str:
    """Summary from og:description, then a generic description meta."""
    return _meta_content(text, "og:description") or _meta_content(text, "description")


def http_fetch(url: str, timeout: float = 15.0, fetch=None) -> FetchResult:
    """Fetch one URL over plain HTTP with the desktop UA; never raises.

    ``fetch`` may be injected as ``fetch(url, timeout) -> bytes``.  The
    og:description summary, when present, leads the markdown body.
    """
    fetch = fetch or _default_http_fetch
    fetched_at = _now_iso()
    try:
        body = fetch(url, timeout)
    except Exception as exc:
        return FetchResult(
            url=url,
            title="",
            markdown="",
            sha256="",
            status="failed",
            source_lane="http",
            error=f"{type(exc).__name__}: {exc}",
            fetched_at=fetched_at,
        )
    text = body.decode("utf-8", errors="replace")
    body_md = html_to_markdown(text)
    summary = extract_summary(text)
    markdown = f"{summary}\n\n{body_md}" if summary and body_md else body_md
    return FetchResult(
        url=url,
        title=extract_title(text),
        markdown=markdown,
        sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        status="fetched" if body_md else "partial",
        source_lane="http",
        fetched_at=fetched_at,
    )


def _make_default_runner(skill_root: str):
    """Build the subprocess runner that calls the walled-fetch-cdp skill."""
    root = pathlib.Path(skill_root)
    python = root / ".venv" / "bin" / "python"
    script = root / "scripts" / "fetch_walled.py"

    def runner(url: str, out_dir: str, wait_ms: int) -> tuple[str, str]:
        proc = subprocess.run(
            [
                str(python),
                str(script),
                "--url",
                url,
                "--out",
                out_dir,
                "--wait-ms",
                str(wait_ms),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"fetch_cdp.py returned invalid JSON: {exc}; "
                f"stderr={proc.stderr.strip()[:200]}"
            ) from exc
        saved = ""
        saved_path = data.get("saved_text")
        if saved_path and pathlib.Path(saved_path).is_file():
            saved = pathlib.Path(saved_path).read_text(encoding="utf-8")
        return proc.stdout, saved

    return runner


def _strip_title_header(text: str) -> str:
    """Drop a leading ``# title`` line (and blank padding) from saved text."""
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def cdp_fetch(
    url,
    skill_root=None,
    out_dir=None,
    wait_ms: int = 4000,
    runner=None,
) -> FetchResult:
    """Fetch one URL through the walled-platform cdp lane; never raises.

    ``runner`` may be injected as ``runner(url, out_dir, wait_ms) ->
    (stdout_json, saved_text_content)``.  The skill's ``status`` is
    passed through unchanged; the saved text file, when present,
    becomes the markdown body.
    """
    runner = runner or _make_default_runner(skill_root or DEFAULT_SKILL_ROOT)
    fetched_at = _now_iso()
    try:
        stdout_json, saved_text = runner(url, out_dir, wait_ms)
        data = json.loads(stdout_json)
    except Exception as exc:
        return FetchResult(
            url=url,
            title="",
            markdown="",
            sha256="",
            status="failed",
            source_lane="cdp",
            error=f"{type(exc).__name__}: {exc}",
            fetched_at=fetched_at,
        )
    if saved_text:
        markdown = _strip_title_header(saved_text)
    else:
        markdown = str(data.get("text_preview", "") or "")
    markdown = markdown.strip()
    return FetchResult(
        url=url,
        title=str(data.get("title", "") or ""),
        markdown=markdown,
        sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        status=str(data.get("status", "") or "failed"),
        source_lane="cdp",
        fetched_at=fetched_at,
    )


def fetch(
    url,
    run_paths,
    lane=None,
    skill_root=None,
    wait_ms: int = 4000,
    http_fetcher=None,
    cdp_runner=None,
    force: bool = False,
) -> FetchResult:
    """Lane-routed, idempotently persisted fetch for one URL.

    ``lane`` defaults to ``route_lane(url)``; ``http_fetcher`` and
    ``cdp_runner`` are the injected transports.  The body is stored at
    ``.local/runs/<date>/fetch/<sha1(lane:url)[:12]>.md`` with sidecar
    JSON metadata; an existing pair is served without re-fetching.  The
    lane is part of the idempotency key so an HTTP fetch never shadows a
    later CDP fetch of the same URL.
    """
    lane = lane or route_lane(url)
    digest = hashlib.sha1(f"{lane}:{url}".encode("utf-8")).hexdigest()[:12]
    fetch_dir = run_paths.work_dir / "fetch"
    md_path = fetch_dir / f"{digest}.md"
    meta_path = fetch_dir / f"{digest}.json"

    if not force and md_path.is_file() and meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return FetchResult(
            url=meta.get("url", url),
            title=meta.get("title", ""),
            markdown=md_path.read_text(encoding="utf-8"),
            sha256=meta.get("sha256", ""),
            status=meta.get("status", ""),
            source_lane=meta.get("source_lane", ""),
            error=meta.get("error", ""),
            fetched_at=meta.get("fetched_at", ""),
        )

    fetch_dir.mkdir(parents=True, exist_ok=True)
    if lane == "cdp":
        result = cdp_fetch(
            url,
            skill_root=skill_root,
            out_dir=str(fetch_dir),
            wait_ms=wait_ms,
            runner=cdp_runner,
        )
    else:
        result = http_fetch(url, fetch=http_fetcher)

    md_path.write_text(result.markdown, encoding="utf-8")
    meta = {
        "url": result.url,
        "title": result.title,
        "status": result.status,
        "source_lane": result.source_lane,
        "sha256": result.sha256,
        "fetched_at": result.fetched_at,
        "error": result.error,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _make_search_runner(skill_root: str):
    """Build the subprocess runner that calls the zhihu-search skill script."""
    root = pathlib.Path(skill_root)
    python = root / ".venv" / "bin" / "python"
    script = root / "scripts" / "search_zhihu.py"

    def runner(topic: str, wait_ms: int) -> list:
        proc = subprocess.run(
            [str(python), str(script), "--q", topic, "--wait-ms", str(wait_ms)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        data = json.loads(proc.stdout)
        links = data.get("links")
        if not isinstance(links, list):
            return []
        return [
            {
                "title": str(it.get("title", "") or ""),
                "url": str(it.get("url", "") or ""),
            }
            for it in links
            if isinstance(it, dict) and it.get("url")
        ]

    return runner


def discover(topic, skill_root=None, wait_ms: int = 4000, runner=None) -> list:
    """Zhida discovery lane: search zhihu for the topic, return question links.

    Returns ``[{"title": str, "url": str}, ...]`` (possibly empty); the
    discovery lane is opportunistic, so any subprocess failure returns an
    empty list rather than raising.
    """
    runner = runner or _make_search_runner(skill_root or DEFAULT_SKILL_ROOT)
    try:
        return runner(topic, wait_ms)
    except Exception:
        return []

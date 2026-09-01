"""AIHOT discovery input (fixture or live API).

AIHOT (https://aihot.virxact.com) is the required discovery signal.
Live access is anonymous and read-only via the public v1 API, matching
the installed ``aihot`` skill.  When the live API fails this module
records the failure and returns no items: fabricating news from model
memory is explicitly forbidden.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://aihot.virxact.com/api/v1"
USER_AGENT = "aihot-skill/1.4.1 (+https://aihot.virxact.com/aihot-skill/)"

# Strict story link contract: only https://aihot.virxact.com/story/<uuid>
# is accepted.  Anything else (other hosts, http, non-uuid slugs, extra
# path segments, query strings) is invalid and yields no public id — the
# id is never guessed or assembled from partial matches.
_STORY_URL_RE = re.compile(
    r"^https://aihot\.virxact\.com/story/"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
)

_ASCII_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9.+#-]*")
_STOP_TOKENS = {"ai", "the", "a", "an", "of", "for", "and", "to", "vs", "how", "why"}
_IDENTITY_TOKEN_RE = re.compile(r"^[a-z]{2,}[0-9][a-z0-9.+#-]*$")


class AihotError(RuntimeError):
    """AIHOT input unavailable or malformed."""


class AihotHTTPError(AihotError):
    def __init__(self, status: int, reason: str):
        super().__init__(f"AIHOT API HTTP {status}: {reason}")
        self.status = status


def _default_fetch(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise AihotHTTPError(exc.code, exc.reason) from exc


def _normalize(raw_items) -> list:
    if not isinstance(raw_items, list):
        raise AihotError(f"malformed AIHOT payload: items is {type(raw_items).__name__}, not a list")
    items = []
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            raise AihotError(
                f"malformed AIHOT payload: item #{index} is {type(raw).__name__}, not an object"
            )
        links = raw.get("links")
        if not isinstance(links, dict):
            links = {}
        source = raw.get("source")
        if isinstance(source, dict):
            source_name = str(source.get("name") or "")
        elif isinstance(source, str):
            source_name = source
        else:
            source_name = ""
        title = raw.get("title")
        if not isinstance(title, str):
            raise AihotError(f"malformed AIHOT payload: item #{index} title is not a string")
        items.append(
            {
                "id": raw.get("id", ""),
                "title": title.strip(),
                "original_title": raw.get("originalTitle") or "",
                "summary": (raw.get("summary") or "").strip() if isinstance(raw.get("summary"), str) else "",
                "source_name": source_name.strip(),
                "links": {
                    "aihot": links.get("aihot") or "",
                    "original": links.get("original") or "",
                },
                "published_at": raw.get("publishedAt") or "",
                "discovered_at": raw.get("discoveredAt") or "",
                "category": raw.get("category") or "",
                "score": raw.get("score") or 0,
                "origin": "aihot",
            }
        )
    return [it for it in items if it["title"]]


def _parse_payload(body: bytes, origin: str) -> dict:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AihotError(f"{origin} returned non-JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise AihotError(f"{origin} payload is {type(payload).__name__}, not an object")
    if "items" not in payload:
        raise AihotError(f"{origin} payload has no 'items' field")
    return payload


def load_fixture(fixture_path) -> list:
    path = pathlib.Path(fixture_path)
    if not path.is_file():
        raise AihotError(f"AIHOT fixture not found: {path}")
    try:
        payload = _parse_payload(path.read_bytes(), "AIHOT fixture")
    except AihotError:
        raise
    except OSError as exc:
        raise AihotError(f"AIHOT fixture unreadable: {exc}") from exc
    return _normalize(payload["items"])


def fetch_live(fetch=None, window: str = "24h", limit: int = 20, timeout: float = 30.0) -> list:
    fetch = fetch or _default_fetch
    url = f"{API_BASE}/items?mode=selected&window={window}&limit={limit}"
    try:
        body = fetch(url, timeout)
    except AihotError:
        raise
    except Exception as exc:  # network errors, timeouts, DNS failures
        raise AihotError(f"AIHOT API request failed: {exc}") from exc
    payload = _parse_payload(body, "AIHOT API")
    return _normalize(payload["items"])


@dataclasses.dataclass
class CollectResult:
    ok: bool
    mode: str
    items: list
    error: str = ""


def collect_items(mode: str, fixture_path=None, fetch=None, **live_kwargs) -> CollectResult:
    """Fetch discovery items.

    mode="fixture": read tests/fixtures payload; failure is an error.
    mode="live": call the AIHOT API; on any failure return ok=False with
    an explicit error and ZERO items (no training-memory fallback).
    """
    try:
        if mode == "fixture":
            items = load_fixture(fixture_path)
        elif mode == "live":
            items = fetch_live(fetch=fetch, **live_kwargs)
        else:
            return CollectResult(
                ok=False, mode=mode, items=[], error=f"unknown AIHOT mode: {mode!r}"
            )
    except AihotError as exc:
        return CollectResult(ok=False, mode=mode, items=[], error=str(exc))
    except Exception as exc:  # defense in depth: malformed input never escapes
        return CollectResult(
            ok=False, mode=mode, items=[],
            error=f"unexpected AIHOT failure: {type(exc).__name__}: {exc}",
        )
    return CollectResult(ok=True, mode=mode, items=items)


# ---------------------------------------------------------------------------
# Story reporting layer (hot-topics -> story matrix)
#
# Contract (aihot skill v1.4.1):
# - Only ``https://aihot.virxact.com/api/v1/*`` is ever requested.
# - ``links.story`` is the only source of a story public id; it is an
#   HTML page and is never requested directly.
# - 404 / missing fields / malformed payloads mean the story layer is
#   currently unavailable; callers get a structured ``unavailable`` dict
#   instead of an exception or a guessed id.
# ---------------------------------------------------------------------------


def _ascii_tokens(text: str) -> set:
    return {
        tok
        for tok in _ASCII_TOKEN_RE.findall((text or "").lower())
        if tok not in _STOP_TOKENS and len(tok) >= 2
    }


def _is_unique_identity_token(token: str) -> bool:
    """True for a fused product-identity token such as ``qwen3.8-2.4t-a95b``.

    Bare version fragments (``v4``, ``3.8``, ``1m``) and generic words
    are not distinctive enough to decide a match on their own.
    """
    return bool(_IDENTITY_TOKEN_RE.match(token))


def _source_name(raw) -> str:
    if isinstance(raw, dict):
        return str(raw.get("name") or "").strip()
    if isinstance(raw, str):
        return raw.strip()
    return ""


def _link_urls(raw) -> dict:
    links = raw.get("links")
    if not isinstance(links, dict):
        links = {}
    return {
        "story": str(links.get("story") or ""),
        "original": str(links.get("original") or ""),
        "aihot": str(links.get("aihot") or ""),
    }


def _normalize_hot_topics(raw_items) -> list:
    """Normalize ``/hot-topics`` items into the matrix match shape."""
    if not isinstance(raw_items, list):
        raise AihotError(
            f"malformed AIHOT hot-topics payload: items is "
            f"{type(raw_items).__name__}, not a list"
        )
    out = []
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            raise AihotError(
                f"malformed AIHOT hot-topics payload: item #{index} is "
                f"{type(raw).__name__}, not an object"
            )
        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        source_names = raw.get("sourceNames")
        if not isinstance(source_names, list):
            source_names = []
        out.append(
            {
                "rank": raw.get("rank") or 0,
                "title": title.strip(),
                "summary": (
                    str(raw.get("summary") or "").strip()
                    if isinstance(raw.get("summary"), str)
                    else ""
                ),
                "source_count": raw.get("sourceCount") or 0,
                "signal_count": raw.get("signalCount") or 0,
                "source_names": [str(n) for n in source_names if str(n)],
                "latest_at": raw.get("latestAt") or "",
                "links": _link_urls(raw),
            }
        )
    return out


def fetch_hot_topics(fetch=None, timeout: float = 30.0) -> list:
    """Fetch the current AIHOT hot-topics board (Top 10, rank ascending)."""
    fetch = fetch or _default_fetch
    url = f"{API_BASE}/hot-topics"
    try:
        body = fetch(url, timeout)
    except AihotError:
        raise
    except Exception as exc:  # network errors, timeouts, DNS failures
        raise AihotError(f"AIHOT hot-topics request failed: {exc}") from exc
    payload = _parse_payload(body, "AIHOT hot-topics")
    return _normalize_hot_topics(payload["items"])


def extract_story_public_id(story_url) -> str:
    """Strictly parse a story public id from a story HTML link.

    Only ``https://aihot.virxact.com/story/<uuid>`` is accepted; anything
    else returns ``""``.  The id is never guessed from partial matches.
    """
    if not isinstance(story_url, str):
        return ""
    match = _STORY_URL_RE.match(story_url.strip())
    return match.group(1) if match else ""


def _is_first_party(source_name: str, original_url: str) -> bool:
    """Heuristic: the report comes directly from the event principal.

    First-party is assumed when the original URL's hostname and the
    source name share an ascii token (``GitHub Blog`` /
    ``github.blog``, ``Cursor Blog`` / ``cursor.com``).  Unverifiable
    reports stay ``False`` — first-party is never invented.
    """
    if not source_name or not original_url:
        return False
    host = (urllib.parse.urlsplit(original_url).hostname or "").lower()
    host = host.removeprefix("www.")
    tokens = {t for t in _ascii_tokens(source_name) if len(t) >= 3}
    return any(tok in host or host.startswith(tok) for tok in tokens)


def _normalize_story(story: dict, public_id: str) -> dict:
    """Normalize a ``/stories/{id}`` payload into the standard report shape."""
    story_title = str(story.get("title") or "").strip()
    story_digest = str(story.get("digest") or "").strip()
    story_latest = str(story.get("latest") or "").strip()
    story_status = str(story.get("status") or "").strip()
    raw_reports = story.get("reports")
    if not isinstance(raw_reports, list):
        raw_reports = []

    reports = []
    for raw in raw_reports:
        if not isinstance(raw, dict):
            continue
        links = _link_urls(raw)
        title = raw.get("title")
        if not isinstance(title, str):
            title = ""
        summary = raw.get("summary")
        if not isinstance(summary, str):
            summary = ""
        source_name = _source_name(raw.get("source"))
        first_party = raw.get("firstParty", raw.get("isFirstParty"))
        if not isinstance(first_party, bool):
            first_party = _is_first_party(source_name, links["original"])
        reports.append(
            {
                "title": title.strip(),
                "summary": summary.strip(),
                "source_name": source_name,
                "first_party": first_party,
                "published_at": raw.get("publishedAt") or raw.get("published") or "",
                "original_url": links["original"],
                "aihot_url": links["aihot"],
                "story_id": public_id,
                "story_title": story_title,
                "story_digest": story_digest,
                "story_latest": story_latest,
                "source_count": int(story.get("sourceCount") or 0),
                "report_count": len(raw_reports),
                "story_status": story_status,
            }
        )
    return {
        "status": "ok",
        "story_id": public_id,
        "story_title": story_title,
        "story_digest": story_digest,
        "story_latest": story_latest,
        "source_count": int(story.get("sourceCount") or 0),
        "report_count": len(raw_reports),
        "story_status": story_status,
        "reports": reports,
    }


def _unavailable(reason: str, **fields) -> dict:
    out = {"status": "unavailable", "reason": reason}
    out.update(fields)
    return out


def fetch_story(public_id, fetch=None, timeout: float = 30.0) -> dict:
    """Fetch and normalize one AIHOT story timeline.

    Never raises: HTTP/JSON/API failures become a structured
    ``{"status": "unavailable", "reason": ...}`` dict (404 included), so
    callers can record the failure honestly instead of crashing.
    """
    if not isinstance(public_id, str) or not extract_story_public_id(
        f"https://aihot.virxact.com/story/{public_id}"
    ):
        return _unavailable(f"invalid story public id: {public_id!r}")
    fetch = fetch or _default_fetch
    url = f"{API_BASE}/stories/{public_id}"
    try:
        body = fetch(url, timeout)
    except AihotError as exc:
        return _unavailable(f"story API unavailable: {exc}", story_id=public_id)
    except Exception as exc:  # network errors, timeouts, DNS failures
        return _unavailable(
            f"story API request failed: {exc}", story_id=public_id
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _unavailable(
            f"story API returned non-JSON payload: {exc}", story_id=public_id
        )
    if not isinstance(payload, dict) or not isinstance(payload.get("story"), dict):
        return _unavailable(
            "story API payload has no 'story' object", story_id=public_id
        )
    return _normalize_story(payload["story"], public_id)


def _best_topic_match(topic_title: str, hot_topics: list, source_urls=None) -> dict:
    """Best hot-topic match for the selected topic, or None.

    Priority: exact source URL -> exact normalized title -> best lexical
    overlap of identity tokens.  A match needs at least two shared
    non-generic ASCII identity tokens (``deepseek`` + ``v4``) or one
    fused entity token (``qwen3.8-2.4t-a95b``); shared CJK bigrams or a
    shared platform word (e.g. 硅基流动) never decide a match.  A topic
    that matches nothing returns None; an unrelated hot topic's story is
    never force-attached to the selected topic.
    """
    source_urls = {u for u in (source_urls or []) if u}
    if source_urls:
        for hot in hot_topics:
            hot_urls = {
                u
                for u in (
                    hot.get("links", {}).get("story"),
                    hot.get("links", {}).get("original"),
                    hot.get("links", {}).get("aihot"),
                )
                if u
            }
            if hot_urls & source_urls:
                return hot

    wanted = (topic_title or "").strip()
    if not wanted:
        return None
    target = _ascii_tokens(wanted)

    best = None
    best_score = 0
    for hot in hot_topics:
        title = hot.get("title", "")
        if title and title.strip() == wanted:
            return hot
        shared = target & _ascii_tokens(title)
        if len(shared) >= 2:
            score = len(shared)
        elif len(shared) == 1 and _is_unique_identity_token(next(iter(shared))):
            score = 2
        else:
            score = 0
        if score > best_score:
            best, best_score = hot, score
        elif score == best_score and score > 0:
            # stable tie-break: lower rank first, then title
            if best is not None and (
                hot.get("rank", 0) < best.get("rank", 0)
                or (
                    hot.get("rank", 0) == best.get("rank", 0)
                    and title < best.get("title", "")
                )
            ):
                best = hot
    if best_score >= 2:
        return best
    return None


def story_matrix_for_topic(
    topic_title, fetch=None, timeout: float = 30.0, source_urls=None
) -> dict:
    """Build the AIHOT story matrix for the selected topic.

    Returns ``{"status": "ok", ...reports}`` when the hot-topic board
    contains the topic AND the matched topic exposes a valid story
    public id AND the story API responds.  Every other outcome is
    ``{"status": "unavailable", "reason": ...}`` — no story id is ever
    guessed, and no unrelated hot topic's story is attached.
    """
    # A story URL explicitly supplied by an editor is a durable pin, unlike
    # the rolling hot-topic board.  Resolve it first so a valid story can be
    # researched after it has naturally fallen out of Top 10.
    explicit_ids = [
        extract_story_public_id(url)
        for url in (source_urls or [])
    ]
    explicit_id = next((item for item in explicit_ids if item), "")
    if explicit_id:
        story = fetch_story(explicit_id, fetch=fetch, timeout=timeout)
        if story.get("status") != "ok":
            return _unavailable(
                story.get("reason") or "story unavailable",
                story_id=explicit_id,
            )
        return {
            "status": "ok",
            "topic_title": topic_title,
            "story_id": explicit_id,
            "story_title": story.get("story_title", ""),
            "story_digest": story.get("story_digest", ""),
            "story_latest": story.get("story_latest", ""),
            "source_count": story.get("source_count", 0),
            "report_count": story.get("report_count", 0),
            "story_status": story.get("story_status", ""),
            "reports": story.get("reports", []),
        }

    try:
        hot_topics = fetch_hot_topics(fetch=fetch, timeout=timeout)
    except AihotError as exc:
        return _unavailable(f"hot-topics unavailable: {exc}")

    matched = _best_topic_match(topic_title, hot_topics, source_urls=source_urls)
    if matched is None:
        return _unavailable("no hot topic matches the selected topic title")

    story_url = (matched.get("links") or {}).get("story") or ""
    public_id = extract_story_public_id(story_url)
    if not public_id:
        return _unavailable(
            "matched hot topic has no valid story link", matched=matched
        )

    story = fetch_story(public_id, fetch=fetch, timeout=timeout)
    if story.get("status") != "ok":
        return _unavailable(
            story.get("reason") or "story unavailable",
            matched=matched,
            story_id=public_id,
        )
    return {
        "status": "ok",
        "topic_title": topic_title,
        "matched": matched,
        "story_id": public_id,
        "story_title": story.get("story_title", ""),
        "story_digest": story.get("story_digest", ""),
        "story_latest": story.get("story_latest", ""),
        "source_count": story.get("source_count", 0),
        "report_count": story.get("report_count", 0),
        "story_status": story.get("story_status", ""),
        "reports": story.get("reports", []),
    }

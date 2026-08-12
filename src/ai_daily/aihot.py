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
import urllib.error
import urllib.request

API_BASE = "https://aihot.virxact.com/api/v1"
USER_AGENT = "aihot-skill/1.4.1 (+https://aihot.virxact.com/aihot-skill/)"


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

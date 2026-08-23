"""Official Zhihu CLI lane: community evidence without CDP scraping.

Wraps the zhihu-cli binary from the official open-platform Skill
(search zhihu / search global / hot).  Every call goes through an
injectable runner; the default shells out to the installed CLI and
reports AUTH_REQUIRED / missing-binary / bad-JSON honestly as
``{"status": "unavailable", "reason": ...}`` — never fabricated results.

The live lane needs an Access Secret configured once by the user
(developer.zhihu.com/profile -> auth set --secret-stdin); until then
every business call returns ``unavailable`` with that reason.
"""

from __future__ import annotations

import json
import os
import subprocess
import time

DEFAULT_BIN = "/Users/hai/Library/Application Support/zhihu-cli/current/zhihu-cli"
_RATE_LIMIT_RETRY_DELAY = 20.0
_RATE_LIMIT_CODE = 30001


def _binary() -> str | None:
    """Resolve the zhihu-cli binary: env override, then the install path."""
    override = os.environ.get("ZHIHU_CLI_BIN", "").strip()
    if override:
        return override
    return DEFAULT_BIN if os.path.isfile(DEFAULT_BIN) else None


def _run(args: list, runner=None) -> dict:
    """Execute one CLI call; always returns a dict, never raises."""
    if runner is not None:
        def call():
            return runner(args)
    else:
        binary = _binary()
        if binary is None:
            return {"status": "unavailable",
                    "reason": "zhihu-cli 未安装；运行 zhihu-cli skill 的 setup 后重试"}

        def call():
            try:
                proc = subprocess.run(
                    [binary, *args], capture_output=True, text=True, timeout=60,
                )
                return json.loads(proc.stdout)
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                return {
                    "status": "unavailable",
                    "reason": f"zhihu-cli call failed: {type(exc).__name__}: {exc}",
                }

    try:
        payload = call()
    except Exception as exc:
        return {"status": "unavailable",
                "reason": f"zhihu-cli runner failed: {type(exc).__name__}: {exc}"}
    if (
        isinstance(payload, dict)
        and payload.get("Code") == _RATE_LIMIT_CODE
    ):
        # Free-tier burst limit: one bounded retry after a short backoff.
        time.sleep(_RATE_LIMIT_RETRY_DELAY)
        try:
            payload = call()
        except Exception as exc:
            payload = {
                "status": "unavailable",
                "reason": f"zhihu-cli runner failed: {type(exc).__name__}: {exc}",
            }
    if isinstance(payload, dict) and "status" in payload:
        return payload
    return payload if isinstance(payload, dict) else {
        "status": "unavailable", "reason": "zhihu-cli returned non-object output",
    }


def _normalize_items(items) -> list:
    out = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        out.append({
            "title": str(raw.get("Title") or raw.get("title") or ""),
            "author": str(raw.get("AuthorName") or raw.get("author") or ""),
            "content": str(raw.get("ContentText") or raw.get("content") or ""),
            "url": str(raw.get("Url") or raw.get("url") or ""),
            "content_type": str(raw.get("ContentType") or ""),
            "vote_up": int(raw.get("VoteUpCount") or 0),
            "comment_count": int(raw.get("CommentCount") or 0),
        })
    return out


def _ok(payload: dict) -> bool:
    """The open-platform envelope reports success with Code == 0."""
    return isinstance(payload, dict) and payload.get("Code") == 0


def search_zhihu(query: str, count: int = 10, runner=None) -> dict:
    """Search Zhihu community content; returns normalized items + links."""
    payload = _run(["search", "zhihu", "--query", query, "--count", str(count)],
                   runner=runner)
    if not _ok(payload):
        error = payload.get("error") or {}
        return {"status": "unavailable",
                "reason": str(error.get("message") or payload.get("reason")
                             or payload.get("Message") or "zhihu search unavailable")}
    data = payload.get("Data") or {}
    return {"status": "ok", "items": _normalize_items(data.get("Items"))}


def hot_topics(limit: int = 30, runner=None) -> dict:
    """Fetch the Zhihu hot list; discovery signal, not fact-checking."""
    payload = _run(["hot", "--limit", str(limit)], runner=runner)
    if not _ok(payload):
        error = payload.get("error") or {}
        return {"status": "unavailable",
                "reason": str(error.get("message") or payload.get("reason")
                             or payload.get("Message") or "zhihu hot unavailable")}
    data = payload.get("Data") or {}
    return {"status": "ok", "items": _normalize_items(data.get("Items"))}

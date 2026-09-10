"""Durable completion receipt for a finished daily English delivery.

``run-en`` is the scheduler's terminal stage, so a successful day used to end
silently: the article was delivered and nothing told the editor it was ready,
and the next tick returned early on the ``delivered`` state, skipping the
announcement for good.  This module turns the durable ``delivery-en.json``
summary into one Telegram message carrying the article and LinkedIn-kit
links, and keeps that announcement both retryable and non-duplicating:

- the marker ``.local/runs/<date>/completion-receipt.json`` is written only
  after ``sendMessage`` succeeds, so a failed send is retried on the next
  scheduler tick and a recorded send is not repeated;
- a changed delivery (``partial`` -> ``delivered``, or a kit that appeared
  later) changes the fingerprint and therefore earns a fresh receipt.

Delivery is therefore at-least-once, not exactly-once: a process death in the
window between a successful ``sendMessage`` and the marker write re-sends on
the next tick.  ``sendMessage`` has no idempotency key, so an occasional
duplicate is the honest price of never losing the announcement.

Sending reuses the Telegram decision-channel machinery
(``telegram_adapter``), and the network call stays injectable so every path
is testable offline.  Public links are emitted only for a publish the
publisher verified by remote re-read, and only for files that really exist,
so a local-only or degraded delivery never points the editor at a dead path.

The receipt is send-only: it calls ``sendMessage`` and never ``getUpdates``,
so re-issuing it on an already-delivered day cannot consume or advance the
reader's pending replies (``AI_DAILY_TELEGRAM_OFFSET`` is untouched).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib

from . import delivery_en, telegram_adapter

RECEIPT_JSON = "completion-receipt.json"
LINKEDIN_KIT_MD = "linkedin-kit.md"
METADATA_JSON = "metadata.json"

# Public publication repo, matching the raw base used for embedded images in
# ``visuals``.  The ``blob`` form is the clickable one for Telegram.
BLOB_BASE = "https://github.com/sztimhdd/AI_Daily/blob/main"

# Terminal delivery states worth announcing.  ``failed``/missing are either a
# non-delivery or already covered by the blocked-receipt path.
ANNOUNCED_STATUSES = ("delivered", "partial")

_STATUS_LINE = {
    "delivered": "英文版已完成",
    "partial": "英文版已交付（部分资产缺失，下一轮补齐）",
}


def _target_line(label: str, remote: bool, relpath: str, missing: str) -> str:
    """One link line: a public URL only when the publisher verified the remote."""
    if not relpath:
        return f"{label}：{missing}"
    if remote:
        return f"{label}：{BLOB_BASE}/{relpath}"
    return f"{label}（本地）：{relpath}"


def _now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _repo_rel(run_paths, candidate) -> str:
    """Repo-relative path of a durable file/dir, or ``""`` when it is absent."""
    text = str(candidate or "").strip()
    if not text:
        return ""
    root = pathlib.Path(run_paths.root).resolve()
    path = pathlib.Path(text)
    full = path if path.is_absolute() else root / path
    if not full.exists():
        return ""
    try:
        return str(full.resolve().relative_to(root))
    except ValueError:
        return ""


def _package_title(run_paths, package_rel: str) -> str:
    """English title from the assembled package metadata, when it is present."""
    if not package_rel:
        return ""
    meta = _read_json(run_paths.root / package_rel / METADATA_JSON)
    return str(meta.get("title") or "").strip()


def receipt_content(run_paths, summary: dict) -> dict:
    """The receipt text plus the article/LinkedIn-kit paths it references.

    Public URLs appear only for ``publication.status == "remote"`` (the mode
    the publisher proves by re-reading the remote); anything else is reported
    as local, so the message never implies a remote the editor cannot open.
    """
    status = str(summary.get("status") or "")
    publication = summary.get("publication") or {}
    mode = str(publication.get("status") or "")
    remote = mode == "remote"
    article_rel = _repo_rel(
        run_paths,
        publication.get("article") or summary.get("final_article"),
    )
    package_rel = _repo_rel(run_paths, summary.get("package_dir"))
    kit_rel = _repo_rel(
        run_paths, f"{package_rel}/{LINKEDIN_KIT_MD}" if package_rel else ""
    )
    lines = [f"AI Daily {run_paths.date} {_STATUS_LINE.get(status, status)}"]
    if not remote:
        lines.append(f"（远端未发布：{mode or '未记录'}）")
    title = _package_title(run_paths, package_rel)
    if title:
        lines += ["", title]
    lines += [
        "",
        _target_line("文章", remote, article_rel, "未找到已交付文件"),
        _target_line("LinkedIn 套件", remote, kit_rel, "未生成"),
    ]
    return {
        "text": "\n".join(lines),
        "article": article_rel,
        "linkedin_kit": kit_rel,
    }


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def send_completion_receipt(run_paths, token: str = None, chat_id: str = None,
                            http=None, env: dict = None,
                            env_path: str = None) -> dict:
    """Announce a finished delivery once, retrying after a failed send.

    Returns ``sent`` after a successful send, ``already-sent`` when the durable
    marker already covers this exact delivery, and ``noop`` when there is
    nothing to announce.  A transport failure raises ``TelegramError`` from the
    shared send machinery and writes no marker, so the caller retries later.
    """
    summary = _read_json(run_paths.work_dir / delivery_en.SUMMARY_JSON)
    status = str(summary.get("status") or "")
    if status not in ANNOUNCED_STATUSES:
        return {
            "status": "noop",
            "reason": f"delivery status {status or 'missing'!r} is not announceable",
        }

    content = receipt_content(run_paths, summary)
    fingerprint = _fingerprint("plain-v1\n" + content["text"])
    marker = _read_json(run_paths.work_dir / RECEIPT_JSON)
    if marker.get("status") == "sent" and marker.get("fingerprint") == fingerprint:
        # Resolved before any credential lookup or network call.
        return {
            "status": "already-sent",
            "fingerprint": fingerprint,
            "sent_at": marker.get("sent_at", ""),
            "article": marker.get("article", ""),
            "linkedin_kit": marker.get("linkedin_kit", ""),
        }

    if token is None or chat_id is None:
        config = telegram_adapter.load_config(env=env, env_path=env_path)
        token = token or config["token"]
        chat_id = chat_id or config["chat"]
    # Bare URLs contain underscores (AI_Daily); Markdown can consume them
    # across the two links while still returning a successful send.
    telegram_adapter.api_call(
        token, "sendMessage", {"chat_id": chat_id, "text": content["text"]},
        http=http,
    )

    record = {
        "status": "sent",
        "fingerprint": fingerprint,
        "delivery_status": status,
        "article": content["article"],
        "linkedin_kit": content["linkedin_kit"],
        "text": content["text"],
        "sent_at": _now(),
    }
    path = run_paths.work_dir / RECEIPT_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"status": "sent", **record}

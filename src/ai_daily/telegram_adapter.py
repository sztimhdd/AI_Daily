"""Telegram decision-channel adapter (ADR 0001).

Implements the durable decision contract: a pending run decision is
rendered as a Telegram message, a reply of ``1``..``3`` is recorded
through the same choice-recording path the CLI uses, and the run
resumes.  The adapter is a full-duplex channel: it can push the request
and accept the reply.

Credentials live only in ``.local/telegram.env`` (or environment
variables) and are never logged.  Network access is injectable
(``http``) so every path is testable offline.
"""

from __future__ import annotations

import json
import hashlib
import os
import pathlib
import re
import urllib.parse
import urllib.request

from . import narrative, pipeline, topics, tui

API_BASE = "https://api.telegram.org"
ENV_FILE = ".local/telegram.env"
_CUSTOM_TOPIC_RE = re.compile(r"^新选题\s*[:：]\s*(.+)$", re.DOTALL)


class TelegramError(RuntimeError):
    """Raised when the adapter cannot honestly proceed."""


def load_config(env: dict = None, env_path: str = None) -> dict:
    """Bot token + chat id from env, falling back to ``.local/telegram.env``."""
    environ = os.environ if env is None else env
    token = (environ.get("AI_DAILY_TELEGRAM_TOKEN") or "").strip()
    chat = (environ.get("AI_DAILY_TELEGRAM_CHAT") or "").strip()
    offset_raw = (environ.get("AI_DAILY_TELEGRAM_OFFSET") or "").strip()
    if token and chat:
        offset = int(offset_raw) if offset_raw.isdigit() else 0
        return {"token": token, "chat": chat, "offset": offset}
    path = pathlib.Path(env_path or ENV_FILE)
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key == "AI_DAILY_TELEGRAM_TOKEN" and not token:
                token = value
            elif key == "AI_DAILY_TELEGRAM_CHAT" and not chat:
                chat = value
            elif key == "AI_DAILY_TELEGRAM_OFFSET" and not offset_raw:
                offset_raw = value
    if not token:
        raise TelegramError("no Telegram bot token (AI_DAILY_TELEGRAM_TOKEN / .local/telegram.env)")
    if not chat:
        raise TelegramError("no Telegram chat id (AI_DAILY_TELEGRAM_CHAT / .local/telegram.env)")
    offset = int(offset_raw) if offset_raw.isdigit() else 0
    return {"token": token, "chat": chat, "offset": offset}


def save_config(config: dict, env_path: str = None) -> None:
    """Persist token/chat/offset back to ``.local/telegram.env`` (gitignored)."""
    path = pathlib.Path(env_path or ENV_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"AI_DAILY_TELEGRAM_TOKEN={config['token']}\n",
        f"AI_DAILY_TELEGRAM_CHAT={config['chat']}\n",
        f"AI_DAILY_TELEGRAM_OFFSET={config.get('offset', 0)}\n",
    ]
    path.write_text("".join(lines), encoding="utf-8")


def _default_http_post(url: str, payload: bytes) -> bytes:
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def api_call(token: str, method: str, params: dict, http=None) -> dict:
    """POST one Telegram Bot API method; never logs the token."""
    http = http or _default_http_post
    url = f"{API_BASE}/bot{token}/{method}"
    try:
        raw = http(url, json.dumps(params).encode("utf-8"))
    except Exception as exc:
        raise TelegramError(
            f"telegram {method} failed: {type(exc).__name__}: {exc}"
        ) from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TelegramError(f"telegram {method} returned non-JSON") from exc
    if not data.get("ok"):
        desc = (data.get("description") or "unknown error")[:200]
        raise TelegramError(f"telegram {method} rejected: {desc}")
    return data.get("result") or {}


def send_message(token: str, chat_id: str, text: str, http=None) -> dict:
    """Send one message to the configured chat."""
    try:
        return api_call(
            token, "sendMessage",
            {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            http=http,
        )
    except TelegramError as exc:
        # Markdown-incompatible text (e.g. a model name with underscores)
        # is rejected with 400; retry once as plain text rather than
        # dropping the message entirely.
        if "400" not in str(exc):
            raise
        return api_call(
            token, "sendMessage",
            {"chat_id": chat_id, "text": text},
            http=http,
        )


def get_updates(token: str, offset: int = 0, http=None) -> list:
    """Fetch updates; callers track ``offset`` for the next poll."""
    result = api_call(
        token, "getUpdates",
        {"offset": offset, "timeout": 0, "allowed_updates": ["message"]},
        http=http,
    )
    return result if isinstance(result, list) else []


def latest_reply(updates: list, chat_id: str) -> str:
    """The last text message from the configured chat, if any."""
    text = ""
    for update in updates:
        message = update.get("message") or {}
        if str(message.get("chat", {}).get("id", "")) != str(chat_id):
            continue
        value = (message.get("text") or "").strip()
        if value:
            text = value
    return text


def pending_decision(run_paths) -> str:
    """Which user-facing state is pending: topic | narrative | blocked | none."""
    from . import state

    st = state.read_state(run_paths)
    if st.get("status") == "failed":
        return "blocked"
    if not st.get("topic_choice"):
        return "topic"
    if not st.get("narrative_choice"):
        return "narrative"
    return "none"


def _offer_text(run_paths) -> tuple:
    """(decision, message) for the pending decision, or (None, \"\")."""
    decision = pending_decision(run_paths)
    if decision == "blocked":
        from . import state

        reason = state.read_state(run_paths).get("last_error") or "未知错误"
        if "audit: narrative needs_research" in reason:
            return decision, (
                "证据审计收口为 needs_research，但核心叙事未被证伪。\n"
                f"原因：{reason}\n"
                "可以继续走保守降级写作；弱论断必须标注、收窄或删除。"
            )
        return decision, (
            "本次流程已停止，未生成新的叙事候选。\n"
            f"原因：{reason}\n"
            "请先核实或补充来源；也可发送“新选题：<事件>”开始一个新选题。"
        )
    if decision == "topic":
        candidates = pipeline.run_candidates(run_paths)
        text = tui.render_candidates(candidates, color=False)
        return decision, text + (
            "\n\n回复编号 1/2/3 选择选题（可附写作方向，如：2 侧重成本）。"
            "若三条都不合适，发送：新选题：<你要研究的事件>。"
        )
    if decision == "narrative":
        candidates = _load_narrative_candidates(run_paths)
        if not candidates:
            return None, "叙事候选尚未生成；先跑 narrative 阶段再问。"
        text = tui.render_narrative_candidates(candidates, color=False)
        return decision, text + (
            "\n\n回复编号 1/2 选择叙事（可附补充方向）；"
            "若两条都不满意，直接发你的编辑意见，我会重写候选再给你。"
        )
    return None, ""


def _load_narrative_candidates(run_paths) -> list:
    path = run_paths.work_dir / narrative.NARRATIVE_CANDIDATES_JSON
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("candidates") if isinstance(data, dict) else data


def offer(run_paths, token: str, chat_id: str, http=None) -> dict:
    """Push the pending decision request; returns what was offered."""
    decision, text = _offer_text(run_paths)
    if decision is None:
        return {"ok": True, "offered": None, "reason": text or "no pending decision"}
    send_message(token, chat_id, text, http=http)
    return {"ok": True, "offered": decision}


def _ensure_narrative_candidates(run_paths, codex_runner=None) -> dict:
    """Regenerate narrative candidates when an editor directive is pending.

    A free-text directive invalidates the old candidates; the next poll must
    rebuild them (with the directive in the prompt) before offering again.
    Returns ``noop`` when nothing is pending, ``generated`` after a rebuild.
    """
    if pending_decision(run_paths) != "narrative":
        return {"status": "noop"}
    from . import state

    st = state.read_state(run_paths)
    if not (st.get("narrative_directive") or "").strip():
        return {"status": "noop"}
    if (run_paths.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).exists():
        return {"status": "noop"}
    try:
        return pipeline.run_narrative(
            run_paths, codex_runner=codex_runner, force=True
        )
    except narrative.NarrativeError as exc:
        return {"status": "unavailable", "reason": str(exc), "candidates": []}


def _receipt_text(applied: dict) -> str:
    """One-line status receipt the bot sends after applying a HITL reply."""
    if not applied:
        return ""
    if not applied.get("ok"):
        return (
            "无法处理这条回复："
            f"{applied.get('reason', '未知原因')}。"
            "请回复有效编号；选题阶段也可发送“新选题：<事件>”。"
        )
    if applied.get("directive"):
        return "已收到你的编辑意见。正在按它重写叙事候选，新候选稍后推送。"
    if applied.get("decision") == "topic":
        return (
            f"已记录选题：{applied.get('chosen', '')}。"
            "下一步：对该选题做多路研究，完成后推送叙事候选。"
        )
    if applied.get("decision") == "narrative":
        return (
            f"已记录叙事：{applied.get('chosen', '')}。"
            "下一步：证据充分性审计与定向补证，通过后进入英文写作。"
        )
    return "已记录。"


def _offer_fingerprint(run_paths) -> str:
    """Stable id of the current pending offer; empty when nothing pending."""
    decision, text = _offer_text(run_paths)
    if decision is None:
        return ""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{decision}:{digest}"


def apply_reply(run_paths, reply: str) -> dict:
    """Apply a reply: ``1``..``3`` picks a candidate; free text at the
    narrative stage records an editor directive that rebuilds candidates.
    At the topic stage, ``新选题：<event>`` records a custom human topic."""
    text = (reply or "").strip()
    decision = pending_decision(run_paths)
    custom_topic = _CUSTOM_TOPIC_RE.match(text)
    if custom_topic:
        if decision != "topic":
            return {"ok": False, "reason": "指定选题只能在选题阶段使用"}
        try:
            chosen = pipeline.run_custom_topic(run_paths, custom_topic.group(1))
        except (topics.TopicError, pipeline.PipelineError) as exc:
            return {"ok": False, "reason": str(exc)}
        return {"ok": True, "decision": "topic", "chosen": chosen["title"]}
    match = re.match(r"^(\d+)(?:\s+(.*))?$", text)
    if not match:
        if decision == "narrative":
            if not text:
                return {"ok": False, "reason": "空回复；请发编号或编辑意见"}
            try:
                result = narrative.apply_directive(run_paths, text)
            except narrative.NarrativeError as exc:
                return {"ok": False, "reason": str(exc)}
            return {
                "ok": True,
                "decision": "narrative",
                "directive": result["directive"],
                "chosen": "",
            }
        return {"ok": False, "reason": f"回复 {reply!r} 不是编号"}
    choice = int(match.group(1))
    extra = (match.group(2) or "").strip()
    decision = pending_decision(run_paths)
    try:
        if decision == "topic":
            chosen = pipeline.run_human_choice(run_paths, choice, extra)
            return {"ok": True, "decision": "topic", "chosen": chosen["title"]}
        if decision == "narrative":
            candidates = _load_narrative_candidates(run_paths)
            if not candidates:
                return {"ok": False, "reason": "叙事候选尚未生成"}
            chosen = narrative.record_choice(run_paths, candidates, choice, extra)
            return {"ok": True, "decision": "narrative", "chosen": chosen["title"]}
    except (narrative.NarrativeError, topics.TopicError,
            pipeline.PipelineError) as exc:
        return {"ok": False, "reason": str(exc)}
    return {"ok": False, "reason": "没有待处理的决策"}


def run_once(run_paths, token: str = None, chat_id: str = None,
             offset: int = None, http=None, env: dict = None,
             env_path: str = None, codex_runner=None) -> dict:
    """One adapter cycle: push pending + apply the latest reply."""
    if token is None or chat_id is None or offset is None:
        config = load_config(env=env)
        token = token or config["token"]
        chat_id = chat_id or config["chat"]
        offset = config["offset"] if offset is None else offset
    ensure_status = _ensure_narrative_candidates(
        run_paths, codex_runner=codex_runner
    )
    updates = get_updates(token, offset=offset, http=http)
    reply = latest_reply(updates, chat_id)
    applied = None
    after_directive = None
    apply_crashed = False
    if reply:
        try:
            applied = apply_reply(run_paths, reply)
        except Exception as exc:
            # Never lose a reply silently: keep the offset unchanged so the
            # update is re-delivered next poll, and tell the user what broke.
            apply_crashed = True
            applied = {
                "ok": False,
                "reason": f"apply failed: {type(exc).__name__}: {exc}",
            }
        receipt = _receipt_text(applied)
        if receipt:
            send_message(token, chat_id, receipt, http=http)
    if applied and applied.get("ok") and applied.get("directive"):
        rebuilt = _ensure_narrative_candidates(run_paths, codex_runner)
        if rebuilt.get("status") == "generated":
            offered = offer(run_paths, token, chat_id, http=http)
            after_directive = "generated"
        else:
            reason = (rebuilt.get("reason") or "unknown").strip()
            send_message(
                token, chat_id,
                "已收到退回意见；重写叙事暂不可用："
                f"{reason[:300] or 'unknown'}",
                http=http,
            )
            after_directive = rebuilt.get("status") or "failed"
    next_offset = offset
    for update in updates:
        next_offset = max(next_offset, int(update.get("update_id", 0)) + 1)
    if next_offset > offset and not apply_crashed:
        save_config(
            {"token": token, "chat": chat_id, "offset": next_offset},
            env_path=env_path,
        )
    offered = None
    if after_directive is None and pending_decision(run_paths) != "none":
        # Push the pending request only when it is new: never re-send the
        # same open question on every poll, and never duplicate a question
        # right after a reply resolved it.
        from . import state as _state

        fingerprint = _offer_fingerprint(run_paths)
        st = _state.read_state(run_paths)
        if st.get("last_offered") != fingerprint:
            offered = offer(run_paths, token, chat_id, http=http)
            _state.update_fields(run_paths, last_offered=fingerprint)
    return {
        "offered": offered.get("offered") if offered else None,
        "reply": reply or "",
        "applied": applied,
        "regenerated": ensure_status.get("status"),
        "after_directive": after_directive,
    }

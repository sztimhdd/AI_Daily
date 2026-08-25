"""Tests for the Telegram decision-channel adapter (ADR 0001)."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import narrative, paths, pipeline, state, telegram_adapter

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"
AIHOT_FIXTURE = FIXTURES / "aihot_items.json"


def _fake_http(captured):
    def fake(url, payload):
        captured["url"] = url
        captured["payload"] = json.loads(payload)
        return json.dumps({"ok": True, "result": {"message_id": 1}}).encode()

    return fake


def _narrative_candidates():
    return [
        {
            "archetype": "cost_ledger", "title": "A", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "evidence_audit": "e", "author_stance": "s",
            "personal_scene": "p", "kicker": "k",
        },
        {
            "archetype": "decision_brief", "title": "B", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "evidence_audit": "e", "author_stance": "s",
            "personal_scene": "p", "kicker": "k",
        },
    ]


def _write_narrative_candidates(rp):
    (rp.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).write_text(
        json.dumps({"candidates": _narrative_candidates()}), encoding="utf-8"
    )


def _write_osint(rp):
    (rp.work_dir / "initial-osint.json").write_text(
        json.dumps({
            "analysis_status": "completed",
            "modules": [
                {"key": "core_timeline", "title": "时间线", "summary": "8月发布。"},
                {"key": "finance_capital", "title": "财务", "summary": "定价 $0.75/1M"},
                {"key": "tech_engineering", "title": "工程", "summary": "743B 基座"},
                {"key": "ecosystem_moat", "title": "生态", "summary": "无"},
                {"key": "community_voices", "title": "社区", "summary": "V2EX 实测"},
                {"key": "org_people", "title": "人事", "summary": "无"},
                {"key": "editor_direction_check", "title": "主编核查", "summary": "无"},
            ],
            "evidence_gaps": [],
            "sources": [
                {"url": "https://example.com/a", "status": "fetched", "title": "发布"},
            ],
        }, ensure_ascii=False),
        encoding="utf-8",
    )


def _valid_candidates(first_title="新候选：AGI 前夜的闸门"):
    base = {
        "hook": "事实。冲突。决策。",
        "thesis": "论点",
        "key_arguments": [{
            "claim": "准入扩大", "observable": "官方公告",
            "source": "一手页", "limitation": "未双源",
            "decision": "可复核",
        }],
        "decision_rule": "条件成立才切",
        "platform_notes": {"linkedin": "LN", "wechat": "WX"},
        "author_stance": "我的判断",
        "personal_scene": "凌晨三点被报警吵醒",
        "kicker": "先别急着上车。",
        "evidence_audit": "EO 充足",
    }
    return [
        {**base, "archetype": "cost_ledger", "title": first_title},
        {
            **base,
            "archetype": "mechanism_teardown",
            "title": "新候选：可及性代价",
            "thesis": "准入机制会改变谁能使用前沿能力",
            "decision_rule": "先拆开准入机制，再决定是否调整部署",
        },
    ]


class TelegramAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-21")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pending_decision_states(self):
        self.assertEqual(telegram_adapter.pending_decision(self.rp), "topic")
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        self.assertEqual(telegram_adapter.pending_decision(self.rp), "narrative")
        cands = [{
            "archetype": "cost_ledger", "title": "A", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "evidence_audit": "e", "author_stance": "s",
            "personal_scene": "p", "kicker": "k",
        }]
        narrative.record_choice(self.rp, cands, 1)
        self.assertEqual(telegram_adapter.pending_decision(self.rp), "none")

    def test_send_message_never_puts_token_in_payload(self):
        captured = {}
        telegram_adapter.send_message(
            "TOKEN123", "42", "Hello", http=_fake_http(captured)
        )
        self.assertIn("/botTOKEN123/sendMessage", captured["url"])
        self.assertEqual(captured["payload"]["chat_id"], "42")
        self.assertEqual(captured["payload"]["text"], "Hello")
        self.assertNotIn("TOKEN123", json.dumps(captured["payload"]))

    def test_send_message_falls_back_to_plain_text_on_400(self):
        calls = []

        def fake(url, payload):
            calls.append(json.loads(payload))
            if len(calls) == 1:
                raise telegram_adapter.TelegramError(
                    "telegram sendMessage failed: HTTPError: HTTP Error 400: Bad Request"
                )
            return json.dumps({"ok": True, "result": {"message_id": 2}}).encode()

        result = telegram_adapter.send_message(
            "TOKEN123", "42", "Mythos_5 is at the door", http=fake
        )
        self.assertEqual(result["message_id"], 2)
        self.assertEqual(len(calls), 2)
        self.assertNotIn("parse_mode", calls[1])

    def test_latest_reply_picks_chat_message(self):
        updates = [
            {"message": {"chat": {"id": 1}, "text": "ignored"}},
            {"message": {"chat": {"id": 42}, "text": "2"}},
            {"message": {"chat": {"id": 42}, "text": "3"}},
        ]
        self.assertEqual(telegram_adapter.latest_reply(updates, "42"), "3")
        self.assertEqual(telegram_adapter.latest_reply(updates, "99"), "")

    def test_apply_topic_reply_records_choice(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        result = telegram_adapter.apply_reply(self.rp, "1 侧重成本")
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "topic")
        st = state.read_state(self.rp)
        self.assertEqual(st["topic_choice"], "human")
        selected = json.loads(
            (self.rp.work_dir / "selected-topic.json").read_text(encoding="utf-8")
        )
        self.assertIn("侧重成本", selected.get("direction", ""))

    def test_apply_narrative_reply_records_choice(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        _write_narrative_candidates(self.rp)
        result = telegram_adapter.apply_reply(self.rp, "2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "narrative")
        self.assertEqual(result["chosen"], "B")

    def test_apply_free_text_at_narrative_records_directive(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        _write_narrative_candidates(self.rp)
        result = telegram_adapter.apply_reply(
            self.rp, "两个叙事我都不喜欢，请深挖 AGI 前夜的准入问题"
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "narrative")
        self.assertIn("AGI 前夜的准入问题", result["directive"])
        st = state.read_state(self.rp)
        self.assertIn("AGI 前夜的准入问题", st["narrative_directive"])
        self.assertFalse(
            (self.rp.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).exists()
        )

    def test_apply_reply_rejects_non_number(self):
        result = telegram_adapter.apply_reply(self.rp, "second one")
        self.assertFalse(result["ok"])

    def test_apply_empty_reply_at_narrative_does_not_crash(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        result = telegram_adapter.apply_reply(self.rp, "   ")
        self.assertFalse(result["ok"])
        st = state.read_state(self.rp)
        self.assertEqual(st.get("narrative_directive", ""), "")

    def test_out_of_range_topic_reply_gets_failure_receipt(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        sent = []

        def fake_http(url, payload):
            data = json.loads(payload)
            if url.endswith("/sendMessage"):
                sent.append(data.get("text", ""))
                return json.dumps(
                    {"ok": True, "result": {"message_id": 1}}
                ).encode()
            return json.dumps(
                {"ok": True, "result": [
                    {"update_id": 700, "message": {
                        "chat": {"id": "42"}, "text": "9"
                    }}
                ]}
            ).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            result = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, env_path=env_path,
            )
        self.assertFalse(result["applied"]["ok"])
        self.assertIn("out of range", result["applied"]["reason"])
        self.assertTrue(
            any("无法处理" in text for text in sent),
            "an out-of-range reply must not be silently dropped",
        )

    def test_unexpected_apply_failure_keeps_offset(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )

        def fake_http(url, payload):
            if url.endswith("/getUpdates"):
                return json.dumps(
                    {"ok": True, "result": [
                        {"update_id": 800, "message": {
                            "chat": {"id": "42"}, "text": "2"
                        }}
                    ]}
                ).encode()
            return json.dumps(
                {"ok": True, "result": {"message_id": 1}}
            ).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            with mock.patch.object(
                telegram_adapter, "apply_reply",
                side_effect=RuntimeError("boom"),
            ):
                result = telegram_adapter.run_once(
                    self.rp, offset=config["offset"],
                    token=config["token"], chat_id=config["chat"],
                    http=fake_http, env_path=env_path,
                )
            saved = telegram_adapter.load_config(env={}, env_path=env_path)
        self.assertFalse(result["applied"]["ok"])
        self.assertIn("apply failed", result["applied"]["reason"])
        self.assertEqual(
            saved["offset"], 90,
            "a reply that fails to apply must stay in the queue",
        )

    def test_load_config_from_env_and_file(self):
        cfg = telegram_adapter.load_config(
            env={"AI_DAILY_TELEGRAM_TOKEN": "T", "AI_DAILY_TELEGRAM_CHAT": "C"}
        )
        self.assertEqual(cfg, {"token": "T", "chat": "C", "offset": 0})
        with tempfile.TemporaryDirectory() as tmp:
            env_file = pathlib.Path(tmp) / "telegram.env"
            env_file.write_text(
                "AI_DAILY_TELEGRAM_TOKEN=FILE_TOKEN\n"
                "AI_DAILY_TELEGRAM_CHAT=99\n"
                "AI_DAILY_TELEGRAM_OFFSET=7\n",
                encoding="utf-8",
            )
            cfg = telegram_adapter.load_config(env={}, env_path=str(env_file))
            self.assertEqual(cfg, {"token": "FILE_TOKEN", "chat": "99", "offset": 7})
        with self.assertRaises(telegram_adapter.TelegramError):
            telegram_adapter.load_config(env={}, env_path="/nonexistent/x.env")

    def test_run_once_advances_and_persists_offset(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        captured = {}

        def fake_http(url, payload):
            captured["url"] = url
            captured["payload"] = json.loads(payload)
            if url.endswith("/getUpdates"):
                return json.dumps(
                    {"ok": True, "result": [
                        {"update_id": 100, "message": {
                            "chat": {"id": "42"}, "text": "1"}}
                    ]}
                ).encode()
            return json.dumps({"ok": True, "result": {"message_id": 1}}).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            result = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"], http=fake_http,
                env_path=env_path,
            )
            self.assertEqual(result["applied"]["decision"], "topic")
            saved = telegram_adapter.load_config(env={}, env_path=env_path)
            self.assertEqual(saved["offset"], 101)

    def test_run_once_regenerates_and_pushes_after_directive_reply(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        _write_narrative_candidates(self.rp)
        _write_osint(self.rp)
        sent = []

        def fake_http(url, payload):
            data = json.loads(payload)
            if url.endswith("/sendMessage"):
                sent.append(data.get("text", ""))
                return json.dumps(
                    {"ok": True, "result": {"message_id": 1}}
                ).encode()
            return json.dumps(
                {"ok": True, "result": [
                    {"update_id": 300, "message": {
                        "chat": {"id": "42"},
                        "text": "两个叙事我都不喜欢，请深挖 AGI 前夜准入",
                    }}
                ]}
            ).encode()

        def runner(prompt):
            return {"candidates": _valid_candidates()}

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            result = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, codex_runner=runner, env_path=env_path,
            )
        self.assertTrue(result["applied"]["ok"])
        self.assertIn("directive", result["applied"])
        self.assertEqual(result["after_directive"], "generated")
        st = state.read_state(self.rp)
        self.assertIn("AGI 前夜准入", st["narrative_directive"])
        data = json.loads(
            (self.rp.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["candidates"][0]["title"], "新候选：AGI 前夜的闸门")
        self.assertTrue(
            any("新候选：AGI 前夜的闸门" in text for text in sent),
            "new candidates must be pushed to the bot",
        )

    def test_run_once_does_not_reoffer_when_reply_resolves_decision(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        _write_narrative_candidates(self.rp)
        sent = []

        def fake_http(url, payload):
            data = json.loads(payload)
            if url.endswith("/sendMessage"):
                sent.append(data.get("text", ""))
                return json.dumps(
                    {"ok": True, "result": {"message_id": 1}}
                ).encode()
            return json.dumps(
                {"ok": True, "result": [
                    {"update_id": 400, "message": {
                        "chat": {"id": "42"}, "text": "2"
                    }}
                ]}
            ).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            result = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, env_path=env_path,
            )
        self.assertTrue(result["applied"]["ok"])
        self.assertEqual(result["applied"]["chosen"], "B")
        self.assertFalse(
            any("回复编号" in text for text in sent),
            "no duplicate question when the reply resolves the decision",
        )
        self.assertTrue(
            any("已记录叙事" in text for text in sent),
            "a status receipt must follow a resolved reply",
        )

    def test_run_once_sends_receipt_after_topic_choice(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        sent = []

        def fake_http(url, payload):
            data = json.loads(payload)
            if url.endswith("/sendMessage"):
                sent.append(data.get("text", ""))
                return json.dumps(
                    {"ok": True, "result": {"message_id": 1}}
                ).encode()
            return json.dumps(
                {"ok": True, "result": [
                    {"update_id": 500, "message": {
                        "chat": {"id": "42"}, "text": "1"
                    }}
                ]}
            ).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            result = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, env_path=env_path,
            )
        self.assertTrue(result["applied"]["ok"])
        self.assertEqual(result["applied"]["decision"], "topic")
        self.assertTrue(
            any("已记录选题" in text for text in sent),
            "a status receipt must follow a topic choice",
        )

    def test_run_once_sends_failure_receipt_for_bad_reply(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        _write_narrative_candidates(self.rp)
        sent = []

        def fake_http(url, payload):
            data = json.loads(payload)
            if url.endswith("/sendMessage"):
                sent.append(data.get("text", ""))
                return json.dumps(
                    {"ok": True, "result": {"message_id": 1}}
                ).encode()
            return json.dumps(
                {"ok": True, "result": [
                    {"update_id": 600, "message": {
                        "chat": {"id": "42"}, "text": "99"
                    }}
                ]}
            ).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            result = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, env_path=env_path,
            )
        self.assertFalse(result["applied"]["ok"])
        self.assertTrue(
            any("无法处理" in text for text in sent),
            "a failure receipt must explain why the reply was rejected",
        )
        self.assertTrue(
            any("回复编号" in text for text in sent),
            "the pending question is re-pushed after a rejected reply",
        )

    def test_run_once_does_not_repush_same_pending_question(self):
        pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        pipeline.run_human_choice(self.rp, 1)
        _write_narrative_candidates(self.rp)
        sent = []

        def fake_http(url, payload):
            data = json.loads(payload)
            if url.endswith("/sendMessage"):
                sent.append(data.get("text", ""))
                return json.dumps(
                    {"ok": True, "result": {"message_id": 1}}
                ).encode()
            return json.dumps({"ok": True, "result": []}).encode()

        with tempfile.TemporaryDirectory() as tmp:
            env_path = str(pathlib.Path(tmp) / "telegram.env")
            telegram_adapter.save_config(
                {"token": "TOK", "chat": "42", "offset": 90}, env_path=env_path
            )
            config = telegram_adapter.load_config(env={}, env_path=env_path)
            first = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, env_path=env_path,
            )
            second = telegram_adapter.run_once(
                self.rp, offset=config["offset"],
                token=config["token"], chat_id=config["chat"],
                http=fake_http, env_path=env_path,
            )
        self.assertEqual(first["offered"], "narrative")
        self.assertEqual(second["offered"], None)
        self.assertEqual(
            len([t for t in sent if "回复编号" in t]), 1,
            "the same open question is only pushed once",
        )

if __name__ == "__main__":
    unittest.main()

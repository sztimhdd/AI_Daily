"""Tests for the Telegram decision-channel adapter (ADR 0001)."""

import json
import pathlib
import sys
import tempfile
import unittest

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
        cands = [
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
        (self.rp.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).write_text(
            json.dumps({"candidates": cands}), encoding="utf-8"
        )
        result = telegram_adapter.apply_reply(self.rp, "2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "narrative")
        self.assertEqual(result["chosen"], "B")

    def test_apply_reply_rejects_non_number(self):
        result = telegram_adapter.apply_reply(self.rp, "second one")
        self.assertFalse(result["ok"])

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


if __name__ == "__main__":
    unittest.main()

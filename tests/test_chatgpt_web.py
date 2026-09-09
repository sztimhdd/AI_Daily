"""Tests for the ChatGPT web image bridge (offline, no browser)."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import chatgpt_web


class FakeClient:
    """Scripted MCP client for orchestrating generate_one offline."""

    def __init__(self, results):
        self.results = results
        self.calls = []
        self.closed = False
        self.initialized = False
        self.notified = False

    def initialize(self):
        self.initialized = True
        return {}

    def notify_initialized(self):
        self.notified = True

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return self.results.get(name, {})

    def close(self):
        self.closed = True


def png_bytes():
    return b"\x89PNG\r\n\x1a\nfake"


class GenerateOneTests(unittest.TestCase):
    def test_success_calls_open_then_run_image_job_and_returns_bytes(self):
        client = FakeClient({"open_chatgpt_browser": {}, "run_image_job": {}})
        out = pathlib.Path("/tmp/ai-daily-chatgpt-test")
        out.mkdir(parents=True, exist_ok=True)
        data = chatgpt_web.generate_one(
            "draw a cup",
            output_dir=out,
            output_stem="01",
            client_factory=lambda: client,
            loader=lambda d, before: png_bytes(),
        )
        self.assertEqual(data, png_bytes())
        self.assertTrue(client.initialized)
        self.assertTrue(client.notified)
        self.assertEqual(
            [name for name, _ in client.calls],
            ["open_chatgpt_browser", "run_image_job"],
        )
        self.assertEqual(client.calls[1][1]["prompt"], "draw a cup")
        self.assertEqual(client.calls[1][1]["outputStem"], "01")
        self.assertTrue(client.closed)

    def test_open_needs_human_raises(self):
        client = FakeClient(
            {"open_chatgpt_browser": {"content": [{"text": "needs_human: login"}]}}
        )
        with self.assertRaises(chatgpt_web.ChatGPTWebError) as ctx:
            chatgpt_web.generate_one(
                "p", client_factory=lambda: client,
                loader=lambda d, before: png_bytes(),
            )
        self.assertIn("needs_human", str(ctx.exception))
        self.assertTrue(client.closed)

    def test_job_needs_human_raises(self):
        client = FakeClient(
            {
                "open_chatgpt_browser": {},
                "run_image_job": {"content": [{"text": "Just a moment"}]},
            }
        )
        with self.assertRaises(chatgpt_web.ChatGPTWebError) as ctx:
            chatgpt_web.generate_one(
                "p", client_factory=lambda: client,
                loader=lambda d, before: png_bytes(),
            )
        self.assertIn("needs_human", str(ctx.exception))

    def test_no_image_raises(self):
        client = FakeClient({"open_chatgpt_browser": {}, "run_image_job": {}})
        with self.assertRaises(chatgpt_web.ChatGPTWebError) as ctx:
            chatgpt_web.generate_one(
                "p", client_factory=lambda: client,
                loader=lambda d, before: None,
            )
        self.assertIn("no image produced", str(ctx.exception))

    def test_scan_new_image_picks_newest_raster(self):
        out = pathlib.Path("/tmp/ai-daily-chatgpt-scan")
        out.mkdir(parents=True, exist_ok=True)
        for name in ("old.png", "new.webp", "notes.txt"):
            (out / name).write_bytes(png_bytes())
        before = {"old.png", "notes.txt"}
        data = chatgpt_web._scan_new_image(out, before)
        self.assertEqual(data, png_bytes())

    def test_scan_new_image_returns_none_when_no_new_raster(self):
        out = pathlib.Path("/tmp/ai-daily-chatgpt-scan2")
        out.mkdir(parents=True, exist_ok=True)
        (out / "old.png").write_bytes(png_bytes())
        self.assertIsNone(chatgpt_web._scan_new_image(out, {"old.png"}))


class MCPProtocolTests(unittest.TestCase):
    def _client(self, lines, timeout=0.01):
        sent = []
        lines_iter = iter(lines)

        def send(line):
            sent.append(line)

        def recv(_timeout):
            return next(lines_iter, None)

        return chatgpt_web.MCPClient(send, recv), sent

    def test_request_returns_matched_result(self):
        client, sent = self._client(
            [b'{"jsonrpc":"2.0","id":1,"result":{"ok":true}}']
        )
        result = client.initialize()
        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(sent), 1)

    def test_request_skips_unrelated_ids(self):
        client, sent = self._client(
            [
                '{"jsonrpc":"2.0","id":999,"result":{"skip":true}}',
                '{"jsonrpc":"2.0","id":1,"result":{"ok":true}}',
            ]
        )
        self.assertEqual(client.initialize(), {"ok": True})

    def test_timeout_raises(self):
        client, _ = self._client([])
        with self.assertRaises(chatgpt_web.ChatGPTWebError) as ctx:
            client.initialize()
        self.assertIn("timeout", str(ctx.exception))

    def test_non_json_raises(self):
        client, _ = self._client(["this is not json"])
        with self.assertRaises(chatgpt_web.ChatGPTWebError) as ctx:
            client.initialize()
        self.assertIn("non-JSON", str(ctx.exception))

    def test_error_response_raises_with_message(self):
        client, _ = self._client(
            ['{"jsonrpc":"2.0","id":1,"error":{"message":"boom"}}']
        )
        with self.assertRaises(chatgpt_web.ChatGPTWebError) as ctx:
            client.initialize()
        self.assertIn("boom", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

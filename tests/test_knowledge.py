"""Tests for the omnigraph knowledge-graph background lane."""

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import knowledge


def _sse(data):
    return f"event: message\ndata: {json.dumps(data)}\n\n".encode()


class FakeHTTP:
    """Scripted MCP-over-HTTP transport: session header + SSE bodies."""

    def __init__(self, scripts):
        self.scripts = scripts
        self.calls = []

    def __call__(self, url, payload, headers=None, timeout=75):
        self.calls.append((url, payload, dict(headers or {})))
        idx = len(self.calls) - 1
        step = self.scripts[idx] if idx < len(self.scripts) else self.scripts[-1]
        if callable(step):
            return step(url, payload, headers, timeout)
        status, hdrs, body = step
        return status, hdrs, body


class KnowledgeClientTests(unittest.TestCase):
    def _client(self, scripts):
        return knowledge.MCPClient("http://x/mcp", http=FakeHTTP(scripts))

    def test_fts_search_returns_text(self):
        script = [
            (200, {"Mcp-Session-Id": "s1"},
             _sse({"jsonrpc": "2.0", "id": 1,
                   "result": {"protocolVersion": "2025-03-26"}})),
            (200, {},
             _sse({"jsonrpc": "2.0", "id": 100,
                   "result": {"content": [{"type": "text", "text": "draft model 机制"}]}})),
        ]
        client = self._client(script)
        self.assertEqual(client.fts_search("speculative decoding"), "draft model 机制")

    def test_kg_search_returns_job_id_when_running(self):
        script = [
            (200, {"Mcp-Session-Id": "s1"},
             _sse({"jsonrpc": "2.0", "id": 1,
                   "result": {"protocolVersion": "2025-03-26"}})),
            (200, {},
             _sse({"jsonrpc": "2.0", "id": 100,
                   "result": {"content": [{"type": "text", "text": "[kg-running] job_id=abc123"}]}})),
        ]
        client = self._client(script)
        self.assertEqual(client.kg_search("q")["job_id"], "abc123")

    def test_kg_poll_returns_report(self):
        script = [
            (200, {"Mcp-Session-Id": "s1"},
             _sse({"jsonrpc": "2.0", "id": 1,
                   "result": {"protocolVersion": "2025-03-26"}})),
            (200, {},
             _sse({"jsonrpc": "2.0", "id": 100,
                   "result": {"content": [{"type": "text", "text": "## Report\nFull synthesis."}]}})),
        ]
        client = self._client(script)
        self.assertEqual(client.kg_poll("abc123"), "## Report\nFull synthesis.")

    def test_fetch_background_degrades_on_network_error(self):
        def boom(url, payload, headers, timeout):
            raise OSError("connection refused")

        result = knowledge.fetch_background(
            {"title": "T", "direction": ""},
            client=knowledge.MCPClient("http://x/mcp", http=FakeHTTP([boom])),
        )
        self.assertEqual(result["status"], "degraded")
        self.assertTrue(result["secondary"])
        self.assertIn("refused", result["reason"])

    def test_fetch_background_uses_query_override(self):
        calls = {}

        class FakeClient:
            def fts_search(self, query, limit=5, lang="zh-CN"):
                calls["fts"] = query
                return "hit"

            def synthesize(self, query, max_polls=8):
                calls["kg"] = query
                return {"status": "completed", "report": "report"}

        result = knowledge.fetch_background(
            {"title": "T", "research_queries": ["q1", "q2"]},
            client=FakeClient(),
            query="speculative decoding mechanism",
        )
        self.assertEqual(calls["fts"], "speculative decoding mechanism")
        self.assertEqual(calls["kg"], "speculative decoding mechanism")
        self.assertEqual(result["status"], "completed")

    def test_fetch_background_defaults_to_first_research_query(self):
        calls = {}

        class FakeClient:
            def fts_search(self, query, limit=5, lang="zh-CN"):
                calls["fts"] = query
                return "hit"

            def synthesize(self, query, max_polls=8):
                calls["kg"] = query
                return {"status": "completed", "report": "r"}

        knowledge.fetch_background(
            {"title": "T", "research_queries": ["q1", "q2"]},
            client=FakeClient(),
        )
        self.assertEqual(calls["fts"], "q1")
        self.assertEqual(calls["kg"], "q1")

    def test_mechanism_concept_prefers_tech_summary(self):
        topic = {"title": "Claude 宕机", "research_queries": ["q1"]}
        concept = knowledge._mechanism_concept(
            topic, tech_summary="依赖拓扑、根因与回滚机制"
        )
        self.assertIn("依赖拓扑", concept)
        self.assertNotIn("q1", concept)

    def test_relevance_flags_no_data(self):
        self.assertFalse(knowledge._relevance("[no-results]", ""))
        self.assertFalse(
            knowledge._relevance("hit", "I do not have enough information to answer.")
        )
        self.assertFalse(knowledge._relevance("hit", "short"))
        self.assertTrue(
            knowledge._relevance("hit", "## Deep\n" + "mechanism " * 60)
        )

    def test_fetch_skips_synthesis_when_fts_misses(self):
        calls = {"synth": 0}

        class C:
            def fts_search(self, q, limit=5, lang="zh-CN"):
                return "[no-results]"

            def synthesize(self, q, max_polls=8):
                calls["synth"] += 1
                return {"status": "completed", "report": "x"}

        result = knowledge.fetch_background({"title": "T"}, client=C())
        self.assertEqual(result["status"], "degraded")
        self.assertFalse(result["relevant"])
        self.assertEqual(calls["synth"], 0)

    def test_fetch_relevant_when_report_substantive(self):
        class C:
            def fts_search(self, q, limit=5, lang="zh-CN"):
                return "draft model 机制"

            def synthesize(self, q, max_polls=8):
                return {"status": "completed", "report": "## Deep\n" + "mechanism " * 60}

        result = knowledge.fetch_background({"title": "T"}, client=C())
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["relevant"])

    def test_fetch_caches_by_query(self):
        calls = {"n": 0}

        class C:
            def fts_search(self, q, limit=5, lang="zh-CN"):
                calls["n"] += 1
                return "hit"

            def synthesize(self, q, max_polls=8):
                return {"status": "completed", "report": "r" * 400}

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = knowledge.fetch_background(
                {"title": "T"}, client=C(), cache_dir=tmp
            )
            result2 = knowledge.fetch_background(
                {"title": "T"}, client=C(), cache_dir=tmp
            )
        self.assertEqual(calls["n"], 1)
        self.assertTrue(result2.get("cached"))


if __name__ == "__main__":
    unittest.main()

"""Tests for the AIHOT discovery input: fixture, live, failure-stop."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import aihot

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "aihot_items.json"


class AihotFixtureTests(unittest.TestCase):
    def test_fixture_items_load_with_required_fields(self):
        items = aihot.load_fixture(FIXTURE)
        self.assertGreaterEqual(len(items), 3)
        for it in items:
            self.assertTrue(it["title"].strip())
            self.assertIn("aihot", it["links"])
            self.assertTrue(it["links"]["aihot"].startswith("https://"))

    def test_fixture_items_keep_source_and_summary(self):
        items = aihot.load_fixture(FIXTURE)
        self.assertTrue(all(it["source_name"] for it in items))
        self.assertTrue(any(it["summary"] for it in items))

    def test_missing_fixture_raises(self):
        with self.assertRaises(aihot.AihotError):
            aihot.load_fixture(pathlib.Path("/nonexistent/aihot.json"))


class AihotLiveTests(unittest.TestCase):
    def test_live_success_parses_items(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        def fake_fetch(url, timeout):
            return json.dumps(payload).encode("utf-8")

        items = aihot.fetch_live(fetch=fake_fetch)
        self.assertEqual(len(items), len(payload["items"]))

    def test_live_http_failure_raises_aihot_error(self):
        def broken_fetch(url, timeout):
            raise OSError("connection refused")

        with self.assertRaises(aihot.AihotError) as ctx:
            aihot.fetch_live(fetch=broken_fetch)
        self.assertIn("connection refused", str(ctx.exception))

    def test_live_bad_status_raises_aihot_error(self):
        def unauthorized(url, timeout):
            raise aihot.AihotHTTPError(401, "unauthorized")

        with self.assertRaises(aihot.AihotError):
            aihot.fetch_live(fetch=unauthorized)

    def test_live_invalid_json_raises_aihot_error(self):
        def garbage(url, timeout):
            return b"<html>not json</html>"

        with self.assertRaises(aihot.AihotError):
            aihot.fetch_live(fetch=garbage)

    def test_never_fabricates_items_on_failure(self):
        """Failure-stop: no training-memory fallback may invent news."""

        def broken_fetch(url, timeout):
            raise OSError("network unreachable")

        result = aihot.collect_items(mode="live", fetch=broken_fetch)
        self.assertEqual(result.items, [])
        self.assertFalse(result.ok)
        self.assertIn("network unreachable", result.error)




class AihotMalformedPayloadTests(unittest.TestCase):
    """Malformed payloads must become controlled failures, never escape."""

    def collect_live(self, body: bytes):
        def fetch(url, timeout):
            return body

        return aihot.collect_items(mode="live", fetch=fetch)

    def test_payload_not_a_dict_returns_failure_zero_items(self):
        result = self.collect_live(b"[1, 2, 3]")
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])
        self.assertTrue(result.error)

    def test_items_not_a_list_returns_failure_zero_items(self):
        result = self.collect_live(json.dumps({"items": "oops"}).encode("utf-8"))
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_missing_items_key_returns_failure_zero_items(self):
        result = self.collect_live(b"{}")
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_non_dict_item_entry_returns_failure_zero_items(self):
        body = json.dumps({"items": ["just a string"]}).encode("utf-8")
        result = self.collect_live(body)
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_wrong_typed_title_returns_failure_zero_items(self):
        body = json.dumps({"items": [{"title": 123}]}).encode("utf-8")
        result = self.collect_live(body)
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_source_string_is_normalized_not_crashed(self):
        body = json.dumps(
            {
                "items": [
                    {
                        "id": "x1",
                        "title": "Source string item",
                        "source": "Reuters Wire",
                        "links": {"aihot": "https://aihot.virxact.com/items/x1"},
                    }
                ]
            }
        ).encode("utf-8")
        result = self.collect_live(body)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.items[0]["source_name"], "Reuters Wire")

    def test_non_dict_links_field_does_not_escape(self):
        body = json.dumps(
            {
                "items": [
                    {
                        "id": "x2",
                        "title": "Bad links item",
                        "links": "https://aihot.virxact.com/items/x2",
                    }
                ]
            }
        ).encode("utf-8")
        result = self.collect_live(body)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.items[0]["links"]["aihot"], "")

    def test_malformed_fixture_returns_failure_zero_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            result = aihot.collect_items(mode="fixture", fixture_path=path)
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_fetch_live_malformed_shapes_raise_aihot_error(self):
        for body in (b"[1,2]", b"{}", json.dumps({"items": {"a": 1}}).encode()):

            def fetch(url, timeout, body=body):
                return body

            with self.assertRaises(aihot.AihotError):
                aihot.fetch_live(fetch=fetch)


if __name__ == "__main__":
    unittest.main()

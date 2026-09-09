"""build_catalog tolerates a missing core-IP source file without failing."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import rss_catalog


class MissingCoreIpFileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self._write_source("keep.json", {
            "name": "keep",
            "nodes": [
                {"name": "A feed", "parameters": {"url": "https://example.com/rss.xml"}},
            ],
        })

    def tearDown(self):
        self._tmp.cleanup()

    def _write_source(self, rel, payload):
        path = self.root / rel
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_missing_file_is_skipped_and_recorded(self):
        rss_catalog.CORE_IP_FILES = ["keep.json", "gone.json"]
        try:
            catalog = rss_catalog.build_catalog(self.root)
        finally:
            rss_catalog.CORE_IP_FILES = rss_catalog.CORE_IP_FILES_DEFAULT
        self.assertIn("gone.json", catalog["missing_files"])
        self.assertIn("keep.json", catalog["generated_from_read"])
        self.assertGreaterEqual(catalog["summary"]["legacy_entries"], 1)
        self.assertTrue(any(s["url"] == "https://example.com/rss.xml"
                            for s in catalog["sources"]))

    def test_all_missing_still_returns_catalog(self):
        rss_catalog.CORE_IP_FILES = ["a.json", "b.json"]
        try:
            catalog = rss_catalog.build_catalog(self.root)
        finally:
            rss_catalog.CORE_IP_FILES = rss_catalog.CORE_IP_FILES_DEFAULT
        self.assertEqual(catalog["missing_files"], ["a.json", "b.json"])
        self.assertEqual(catalog["summary"]["legacy_entries"], 0)


if __name__ == "__main__":
    unittest.main()

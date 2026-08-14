"""Tests for the provenance-aware legacy RSS catalog.

The catalog is extracted deterministically from the five immutable
core-IP JSONs.  It must preserve every legacy source entry (93) with
provenance and document the unique extractable feed URLs (73).  It must
never invent feeds: every URL must trace back to a source file + node.
"""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import rss_catalog

REPO = pathlib.Path(__file__).resolve().parents[1]


class CatalogExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = rss_catalog.build_catalog(REPO)

    def test_preserves_93_legacy_entries(self):
        self.assertEqual(self.catalog["summary"]["legacy_entries"], 93)

    def test_documents_73_unique_extractable_urls(self):
        self.assertEqual(self.catalog["summary"]["unique_extractable_urls"], 73)

    def test_every_source_has_provenance(self):
        for src in self.catalog["sources"]:
            self.assertTrue(src["provenance"], f"missing provenance: {src['url']}")
            for prov in src["provenance"]:
                self.assertTrue((REPO / prov["file"]).is_file(), prov["file"])
                self.assertTrue(prov["node"])

    def test_no_invented_feeds(self):
        """Every catalog URL must appear verbatim in its provenance file."""
        for src in self.catalog["sources"]:
            prov = src["provenance"][0]
            text = (REPO / prov["file"]).read_text(encoding="utf-8")
            self.assertIn(src["url"], text, f"URL not found in source: {src['url']}")

    def test_duplicate_legacy_entries_keep_both_provenances(self):
        by_url = {s["url"]: s for s in self.catalog["sources"]}
        dual = [s for s in by_url.values() if len(s["provenance"]) >= 2]
        self.assertTrue(dual, "expected URLs present in more than one legacy node")
        example = by_url["https://openai.com/news/rss.xml"]
        nodes = {p["node"] for p in example["provenance"]}
        self.assertIn("Top 20 AI RSS Feeds", nodes)
        self.assertIn("Super RSS Pool & Sampler", nodes)

    def test_feed_occurrence_counts_match_legacy_pools(self):
        occurrences = sum(len(s["provenance"]) for s in self.catalog["sources"])
        # 88 rss/atom occurrences (incl. zhihu feed API) + 3 xml blog feeds
        self.assertEqual(occurrences, 91)

    def test_auxiliary_services_recorded_not_feeds(self):
        names = {a["name"] for a in self.catalog["auxiliary_services"]}
        self.assertEqual(names, {"Tavily Search API", "Event Registry API"})
        for svc in self.catalog["auxiliary_services"]:
            self.assertFalse(svc.get("extractable_feed", False))

    def test_fetchable_total_includes_three_xml_blog_feeds(self):
        self.assertEqual(self.catalog["summary"]["unique_fetchable_urls"], 76)
        xml_blogs = [
            s for s in self.catalog["sources"]
            if s["extractable"] and not s["identifiable"]
        ]
        self.assertEqual(len(xml_blogs), 3)

    def test_extraction_is_deterministic(self):
        again = rss_catalog.build_catalog(REPO)
        self.assertEqual(
            json.dumps(self.catalog, sort_keys=True),
            json.dumps(again, sort_keys=True),
        )


class CatalogFileTests(unittest.TestCase):
    def test_write_and_load_roundtrip(self):
        catalog = rss_catalog.build_catalog(REPO)
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "rss-catalog.json"
            rss_catalog.write_catalog(catalog, path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["summary"]["legacy_entries"], 93)

    def test_repo_committed_catalog_matches_regeneration(self):
        committed = REPO / "knowledge" / "rss-catalog.json"
        if not committed.is_file():
            self.skipTest("catalog not generated yet")
        live = rss_catalog.build_catalog(REPO)
        stored = json.loads(committed.read_text(encoding="utf-8"))
        self.assertEqual(stored["summary"], live["summary"])
        self.assertEqual(
            [(s["url"], len(s["provenance"])) for s in stored["sources"]],
            [(s["url"], len(s["provenance"])) for s in live["sources"]],
        )




class DeterminismAndDocumentationTests(unittest.TestCase):
    def test_catalog_carries_no_timestamp(self):
        catalog = rss_catalog.build_catalog(REPO)
        self.assertNotIn("generated_at", catalog)
        self.assertNotIn("generated_at", catalog["summary"])

    def test_regeneration_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = pathlib.Path(tmp) / "one.json"
            p2 = pathlib.Path(tmp) / "two.json"
            rss_catalog.write_catalog(rss_catalog.build_catalog(REPO), p1)
            rss_catalog.write_catalog(rss_catalog.build_catalog(REPO), p2)
            self.assertEqual(p1.read_bytes(), p2.read_bytes())

    def test_entry_math_documented_in_summary(self):
        summary = rss_catalog.build_catalog(REPO)["summary"]
        self.assertEqual(
            summary["legacy_entries"],
            summary["feed_occurrences"] + summary["auxiliary_services"],
        )
        self.assertIn("91", summary["entry_math"])
        self.assertIn("2 auxiliary", summary["entry_math"])

    def test_extractability_documented_as_marker_heuristic(self):
        summary = rss_catalog.build_catalog(REPO)["summary"]
        note = summary["extractability_note"].lower()
        self.assertIn("heuristic", note)
        self.assertIn("not runtime", note)


if __name__ == "__main__":
    unittest.main()

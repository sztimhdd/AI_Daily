"""Observable delivery outcomes for the daily English edition."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import paths, state, topics


FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"


class DeliveryEnTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-21")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        topics.choose_fixture(self.rp, FIXTURES / "topic_fixture.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_delivery_keeps_assembled_article_when_enrichments_fail(self):
        from ai_daily import delivery_en

        article = self.rp.work_dir / "article-en.md"
        article.write_text(
            "# A usable English edition\n\nA sourced point ([source](https://example.com/1)).\n",
            encoding="utf-8",
        )
        (self.rp.work_dir / "evidence-package.json").write_text(
            json.dumps({"sources": [{"url": "https://example.com/1", "title": "source"}]}),
            encoding="utf-8",
        )
        state.update_fields(self.rp, en_title="A usable English edition", en_slug="a-usable-english-edition")

        with mock.patch.object(delivery_en.draft_en, "run", return_value={"status": "resumed", "article": article}), \
             mock.patch.object(delivery_en.claim_check, "run", return_value={"status": "unavailable", "reason": "review down"}), \
             mock.patch.object(delivery_en.visuals, "run_illustrate", return_value={"status": "unavailable", "reason": "image down"}), \
             mock.patch.object(delivery_en.linkedin, "run", return_value={"status": "unavailable", "reason": "kit down"}):
            result = delivery_en.run(self.rp)

        self.assertEqual(result["status"], "delivered")
        self.assertEqual(result["images"]["status"], "degraded")
        self.assertEqual(result["linkedin_kit"]["status"], "degraded")
        self.assertTrue(result["package_dir"].is_dir())
        summary = json.loads((self.rp.work_dir / "delivery-en.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "delivered")
        self.assertEqual(summary["claim_check"]["status"], "warning")

    def test_delivery_stops_before_assembly_when_draft_is_unavailable(self):
        from ai_daily import delivery_en

        with mock.patch.object(delivery_en.draft_en, "run", return_value={"status": "unavailable", "reason": "writer down"}), \
             mock.patch.object(delivery_en.assemble_en, "run") as assemble:
            result = delivery_en.run(self.rp)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["assembly"]["status"], "skipped")
        assemble.assert_not_called()


if __name__ == "__main__":
    unittest.main()

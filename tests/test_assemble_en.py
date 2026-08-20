"""Tests for English package assembly (08)."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import assemble_en, paths, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"

EN_ARTICLE = """# The search budget is the hidden line item

Three providers moved token billing by 15 to 40 percent this week, each change on the public blog ([announcement](https://source-a.example.com/1)).

**The search budget is the hidden line item.** One deep research task fires twenty-plus retrieval calls, and no vendor publishes a per-call count.

The risk is concrete: a team without a retrieval ceiling can double its inference spend next quarter.
"""


class AssembleEnBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        self.topic = topics.choose_fixture(self.rp, FIXTURES / "topic_fixture.json")

    def tearDown(self):
        self._tmp.cleanup()

    def write_article_en(self, text=EN_ARTICLE):
        (self.rp.work_dir / "article-en.md").write_text(text, encoding="utf-8")

    def write_evidence(self):
        data = {
            "run_id": self.rp.run_id,
            "topic_title": self.topic["title"],
            "narrative_title": "narrative",
            "audit_verdict": "sufficient",
            "reason": "",
            "sources": [
                {
                    "url": "https://source-a.example.com/1",
                    "title": "announcement",
                    "status": "fetched",
                    "source_lane": "http",
                    "excerpt": "Three providers moved token billing.",
                    "origin": "initial",
                }
            ],
        }
        (self.rp.work_dir / "evidence-package.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


class AssembleEnTests(AssembleEnBase):
    def _en_slug(self):
        return paths.slugify_title("The search budget is the hidden line item",
                                   self.rp.date)

    def test_package_created_with_article_sources_metadata(self):
        self.write_article_en()
        self.write_evidence()
        result = assemble_en.run(self.rp)
        pkg = self.rp.package_dir(self._en_slug())
        self.assertEqual(result["status"], "assembled")
        self.assertTrue((pkg / f"{self._en_slug()}.md").is_file())
        self.assertTrue((pkg / "sources.md").is_file())
        self.assertTrue((pkg / "metadata.json").is_file())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["slug"], self._en_slug())
        self.assertEqual(meta["title"], "The search budget is the hidden line item")
        self.assertEqual(meta["date"], "2026-08-12")
        self.assertEqual(meta["language"], "en")
        self.assertIn("topic_choice", meta)

    def test_final_article_written_to_en_path(self):
        self.write_article_en()
        self.write_evidence()
        result = assemble_en.run(self.rp)
        final = self.rp.final_article_en_path(self._en_slug())
        self.assertTrue(final.is_file())
        self.assertEqual(
            final.read_text(encoding="utf-8"), EN_ARTICLE
        )
        self.assertEqual(result["final_article"], final)
        self.assertTrue(final.name.endswith("-en.md"))

    def test_resumes_when_package_exists(self):
        self.write_article_en()
        self.write_evidence()
        assemble_en.run(self.rp)
        result = assemble_en.run(self.rp)
        self.assertEqual(result["status"], "resumed")

    def test_raises_without_draft(self):
        self.write_evidence()
        with self.assertRaises(assemble_en.AssembleEnError):
            assemble_en.run(self.rp)

    def test_raises_on_empty_draft(self):
        self.write_article_en("")
        self.write_evidence()
        with self.assertRaises(assemble_en.AssembleEnError):
            assemble_en.run(self.rp)

    def test_sources_carry_evidence_origin(self):
        self.write_article_en()
        self.write_evidence()
        assemble_en.run(self.rp)
        sources = (
            self.rp.package_dir(self._en_slug()) / "sources.md"
        ).read_text(encoding="utf-8")
        self.assertIn("https://source-a.example.com/1", sources)
        self.assertIn("initial", sources)


if __name__ == "__main__":
    unittest.main()

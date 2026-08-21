"""Tests for the post-draft claim check (ticket 13)."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import assemble_en, claim_check, paths, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"


class ClaimCheckBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        self.topic = topics.choose_fixture(self.rp, FIXTURES / "topic_fixture.json")
        (self.rp.work_dir / "article-en.md").write_text(
            "# The search budget is the hidden line item\n\nThree providers "
            "moved pricing ([post](https://example.com/1)).\n",
            encoding="utf-8",
        )
        (self.rp.work_dir / "evidence-package.json").write_text(
            json.dumps(
                {
                    "narrative_title": "narrative",
                    "audit_verdict": "sufficient",
                    "sources": [
                        {
                            "url": "https://example.com/1",
                            "title": "post",
                            "status": "fetched",
                            "excerpt": "Three providers moved pricing.",
                            "origin": "initial",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()


class ClaimCheckRunTests(ClaimCheckBase):
    def test_ok_verdict_persists(self):
        result = claim_check.run(
            self.rp,
            codex_runner=lambda p: {
                "status": "completed",
                "verdict": "ok",
                "items": [],
                "reason": "",
            },
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verdict"], "ok")
        data = json.loads(
            (self.rp.work_dir / "claim-check.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["verdict"], "ok")

    def test_mismatch_verdict_persists(self):
        result = claim_check.run(
            self.rp,
            codex_runner=lambda p: {
                "status": "completed",
                "verdict": "mismatch",
                "items": [{"claim": "x", "verdict": "mismatch"}],
                "reason": "quote miscounted",
            },
        )
        self.assertEqual(result["verdict"], "mismatch")

    def test_runner_unavailable_returns_unavailable(self):
        result = claim_check.run(
            self.rp,
            codex_runner=lambda p: {"status": "unavailable", "reason": "down"},
        )
        self.assertEqual(result["status"], "unavailable")

    def test_missing_article_raises(self):
        (self.rp.work_dir / "article-en.md").unlink()
        with self.assertRaises(claim_check.ClaimCheckError):
            claim_check.run(self.rp)


class AssembleEnClaimGateTests(ClaimCheckBase):
    def test_assembly_records_mismatch_without_blocking_delivery(self):
        claim_check.run(
            self.rp,
            codex_runner=lambda p: {
                "status": "completed",
                "verdict": "mismatch",
                "items": [],
                "reason": "x",
            },
        )
        result = assemble_en.run(self.rp)
        self.assertEqual(result["status"], "assembled")
        metadata = json.loads(
            (self.rp.package_dir(paths.slugify_title(
                "The search budget is the hidden line item", self.rp.date
            )) / "metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["claim_check"]["verdict"], "mismatch")

    def test_assembly_proceeds_on_ok(self):
        claim_check.run(
            self.rp,
            codex_runner=lambda p: {
                "status": "completed",
                "verdict": "ok",
                "items": [],
                "reason": "",
            },
        )
        result = assemble_en.run(self.rp)
        self.assertEqual(result["status"], "assembled")


if __name__ == "__main__":
    unittest.main()

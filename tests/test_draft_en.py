"""Tests for the English full-draft stage (07)."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import draft_en, narrative, paths, state, sufficiency


def sample_narrative_candidate():
    return {
        "archetype": "cost_ledger",
        "title": "The hidden search budget",
        "hook": "h",
        "thesis": "Retrieval depth is the uncontrolled cost line.",
        "key_arguments": [
            {
                "claim": "deep research fires many calls",
                "observable": "public pricing",
                "source": "https://example.com/1",
                "limitation": "no per-call count published",
            }
        ],
        "decision_rule": "d",
        "platform_notes": {"linkedin": "l", "wechat": "w"},
        "author_stance": "Cap the depth.",
        "personal_scene": "a scene",
        "kicker": "Cap the retrieval depth.",
        "evidence_audit": "e",
    }


def sample_evidence_package():
    return {
        "run_id": "AI-Daily/2026-08-20",
        "topic_title": "The hidden search budget",
        "narrative_title": "The hidden search budget",
        "audit_verdict": "sufficient",
        "reason": "",
        "sources": [
            {
                "url": "https://example.com/1",
                "title": "Vendor post",
                "status": "fetched",
                "source_lane": "http",
                "excerpt": "Three vendors moved token billing by 15 to 40 percent.",
                "origin": "initial",
            }
        ],
    }


def sample_topic():
    return {
        "title": "The hidden search budget",
        "slug": "hidden-search-budget",
        "direction": "",
        "thesis": "Retrieval depth is the uncontrolled cost line.",
    }


def clean_draft_body():
    return (
        "Three providers moved token billing by 15 to 40 percent this week, "
        "and each change is on the public blog "
        "([announcement](https://example.com/1)).\n\n"
        "**The search budget is the hidden line item.** One deep research "
        "task fires twenty-plus retrieval calls, and no vendor publishes a "
        "per-call count, so the number has to be reverse-engineered from "
        "public pricing.\n\n"
        "The risk is concrete: a team without a retrieval ceiling can double "
        "its inference spend next quarter."
    )


class DraftEnBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-20")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)
        state.update_fields(
            self.run_paths,
            topic_choice="human",
            topic_title="The hidden search budget",
            slug="hidden-search-budget",
        )
        (self.run_paths.work_dir / "selected-topic.json").write_text(
            json.dumps(sample_topic(), ensure_ascii=False), encoding="utf-8"
        )
        narrative.record_choice(self.run_paths, [sample_narrative_candidate()], 1)
        self._write_evidence_package()

    def tearDown(self):
        self._tmp.cleanup()

    def _write_evidence_package(self):
        (self.run_paths.work_dir / "evidence-package.json").write_text(
            json.dumps(sample_evidence_package(), ensure_ascii=False),
            encoding="utf-8",
        )

    def _write_audit(self, verdict="sufficient"):
        (self.run_paths.work_dir / "sufficiency-audit.json").write_text(
            json.dumps(
                {
                    "narrative_title": "The hidden search budget",
                    "verdict": verdict,
                    "reason": "",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _runner(self, payload):
        return lambda prompt: payload

    def _good_payload(self):
        return {
            "status": "completed",
            "title": "The hidden search budget",
            "body": clean_draft_body(),
        }


class DraftEnGateTests(DraftEnBase):
    def test_missing_audit_blocks_draft(self):
        with self.assertRaises(sufficiency.AuditGateBlocked):
            draft_en.run(self.run_paths)

    def test_unsupported_audit_blocks_draft(self):
        self._write_audit(verdict="unsupported")
        with self.assertRaises(sufficiency.AuditGateBlocked):
            draft_en.run(self.run_paths)

    def test_missing_evidence_package_raises(self):
        self._write_audit()
        (self.run_paths.work_dir / "evidence-package.json").unlink()
        with self.assertRaises(draft_en.DraftEnError):
            draft_en.run(self.run_paths)

    def test_corrupt_evidence_package_raises_draft_error(self):
        self._write_audit()
        (self.run_paths.work_dir / "evidence-package.json").write_text(
            "{not json", encoding="utf-8"
        )
        with self.assertRaises(draft_en.DraftEnError):
            draft_en.run(self.run_paths)


class DraftEnRunTests(DraftEnBase):
    def setUp(self):
        super().setUp()
        self._write_audit()

    def test_draft_writes_article_en(self):
        result = draft_en.run(
            self.run_paths,
            codex_runner=self._runner(self._good_payload()),
            min_words=10,
            max_words=500,
        )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["title"], "The hidden search budget")
        self.assertEqual(result["slug"], "the-hidden-search-budget")
        article = (self.run_paths.work_dir / "article-en.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue(article.startswith("# The hidden search budget"))
        self.assertIn("([announcement](https://example.com/1))", article)

    def test_draft_resumes_when_article_exists(self):
        (self.run_paths.work_dir / "article-en.md").write_text(
            "# existing\n", encoding="utf-8"
        )
        result = draft_en.run(self.run_paths)
        self.assertEqual(result["status"], "resumed")

    def test_runner_unavailable_returns_unavailable(self):
        result = draft_en.run(
            self.run_paths,
            codex_runner=self._runner({"status": "unavailable", "reason": "down"}),
        )
        self.assertEqual(result["status"], "unavailable")

    def test_malformed_output_returns_unavailable(self):
        result = draft_en.run(
            self.run_paths,
            codex_runner=self._runner({"status": "completed", "title": ""}),
        )
        self.assertEqual(result["status"], "unavailable")

    def test_quality_gate_rejects_de_ai_slop(self):
        payload = self._good_payload()
        payload["body"] = (
            "The platform leverages a robust stack "
            "([post](https://example.com/1))."
        )
        with self.assertRaises(draft_en.DraftEnError):
            draft_en.run(
                self.run_paths,
                codex_runner=self._runner(payload),
                min_words=1,
                max_words=500,
            )

    def test_quality_gate_writes_report(self):
        draft_en.run(
            self.run_paths,
            codex_runner=self._runner(self._good_payload()),
            min_words=10,
            max_words=500,
        )
        report = (self.run_paths.work_dir / "quality-en-report.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("PASS", report)


class DraftEnDowngradeTests(DraftEnBase):
    """Conservative downgrade path: needs_research annotates and passes."""

    def setUp(self):
        super().setUp()
        self._write_audit(verdict="needs_research")

    def _downgraded_payload(self):
        body = (
            "Three providers moved pricing this week, per a vendor post "
            "([announcement](https://example.com/1)). The reported deal "
            "price is second-hand and not independently verified. Token "
            "figures conflict across sources, so the exact volume is "
            "unconfirmed."
        )
        return {
            "status": "completed",
            "title": "The hidden search budget",
            "body": body,
        }

    def test_needs_research_writes_annotated_draft(self):
        result = draft_en.run(
            self.run_paths,
            codex_runner=self._runner(self._downgraded_payload()),
            min_words=1,
            max_words=500,
        )
        self.assertEqual(result["status"], "generated")
        self.assertTrue(result["downgraded"])

    def test_needs_research_rejects_unannotated_draft(self):
        payload = self._good_payload()  # no downgrade markers
        with self.assertRaises(draft_en.DraftEnError):
            draft_en.run(
                self.run_paths,
                codex_runner=self._runner(payload),
                min_words=1,
                max_words=500,
            )

if __name__ == "__main__":
    unittest.main()

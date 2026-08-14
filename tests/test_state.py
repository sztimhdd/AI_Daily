"""Tests for the daily run state.md document."""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import paths, state


class StateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.paths.ensure_work_dir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_creates_state_md_with_run_id_and_stage(self):
        st = state.init_state(self.paths)
        self.assertTrue(self.paths.state_file.exists())
        self.assertEqual(st["run_id"], "AI-Daily/2026-08-12")
        self.assertEqual(st["stage"], "collect")
        self.assertEqual(st["status"], "pending")

    def test_state_is_idempotent_for_same_date(self):
        s1 = state.init_state(self.paths)
        s2 = state.init_state(self.paths)
        self.assertEqual(s1["run_id"], s2["run_id"])
        self.assertEqual(len(state.list_state_files(self.root)), 1)

    def test_transition_records_stage_log(self):
        state.init_state(self.paths)
        state.transition(self.paths, "topic_choice", note="3 candidates ready")
        st = state.read_state(self.paths)
        self.assertEqual(st["stage"], "topic_choice")
        self.assertTrue(any("topic_choice" in line for line in st["stage_log"]))
        self.assertTrue(any("3 candidates ready" in line for line in st["stage_log"]))

    def test_transition_rejects_unknown_stage(self):
        state.init_state(self.paths)
        with self.assertRaises(state.StateError):
            state.transition(self.paths, "narrative_choice")

    def test_failure_recorded_with_last_error(self):
        state.init_state(self.paths)
        state.fail(self.paths, "aihot", "AIHOT API returned 503")
        st = state.read_state(self.paths)
        self.assertEqual(st["status"], "failed")
        self.assertEqual(st["last_error"], "aihot: AIHOT API returned 503")

    def test_artifact_references_recorded(self):
        state.init_state(self.paths)
        state.record_artifact(self.paths, "research", "research.md")
        st = state.read_state(self.paths)
        self.assertEqual(st["artifacts"]["research"], "research.md")

    def test_state_roundtrip_preserves_slug_and_choice(self):
        state.init_state(self.paths)
        state.update_fields(
            self.paths,
            slug="ai-search-budget-research-cost",
            topic_choice="fixture",
        )
        st = state.read_state(self.paths)
        self.assertEqual(st["slug"], "ai-search-budget-research-cost")
        self.assertEqual(st["topic_choice"], "fixture")

    def test_state_file_is_readable_markdown(self):
        state.init_state(self.paths)
        text = self.paths.state_file.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Run AI-Daily/2026-08-12"))
        self.assertIn("- stage: collect", text)

    def test_counters_increment(self):
        state.init_state(self.paths)
        state.bump_counter(self.paths, "collect_runs")
        state.bump_counter(self.paths, "collect_runs")
        st = state.read_state(self.paths)
        self.assertEqual(st["counters"]["collect_runs"], 2)


if __name__ == "__main__":
    unittest.main()

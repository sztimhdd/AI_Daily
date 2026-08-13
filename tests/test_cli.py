"""Tests for the CLI: subcommands, fixture E2E, error exits."""

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import cli

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"
AIHOT_FIXTURE = str(FIXTURES / "aihot_items.json")
TOPIC_FIXTURE = str(FIXTURES / "topic_fixture.json")


class CliBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = str(pathlib.Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class FixtureE2ETests(CliBase):
    def test_run_fixture_e2e_exit_zero_and_completed(self):
        code, out, err = self.run_cli(
            "run", "--root", self.root, "--date", "2026-08-12",
            "--topic-fixture", TOPIC_FIXTURE, "--aihot-fixture", AIHOT_FIXTURE,
        )
        self.assertEqual(code, 0, err)
        root = pathlib.Path(self.root)
        final = root / "articles" / "2026-08-12-ai-search-budget-research-cost-zh.md"
        self.assertTrue(final.is_file())
        state_text = (root / ".local" / "runs" / "2026-08-12" / "state.md").read_text(encoding="utf-8")
        self.assertIn("- stage: completed", state_text)
        self.assertIn("publish-mode: local-only", state_text)

    def test_run_fixture_e2e_is_idempotent_resume(self):
        first = self.run_cli(
            "run", "--root", self.root, "--date", "2026-08-12",
            "--topic-fixture", TOPIC_FIXTURE, "--aihot-fixture", AIHOT_FIXTURE,
        )
        second = self.run_cli(
            "run", "--root", self.root, "--date", "2026-08-12",
            "--topic-fixture", TOPIC_FIXTURE, "--aihot-fixture", AIHOT_FIXTURE,
        )
        self.assertEqual(first[0], 0)
        self.assertEqual(second[0], 0, second[2])
        state_text = (
            pathlib.Path(self.root) / ".local" / "runs" / "2026-08-12" / "state.md"
        ).read_text(encoding="utf-8")
        self.assertIn("collect_runs: 1", state_text)


class SteppedCliTests(CliBase):
    def test_step_by_step_flow(self):
        date_args = ("--root", self.root, "--date", "2026-08-12")
        code, _, err = self.run_cli("collect", *date_args, "--mode", "fixture",
                                    "--aihot-fixture", AIHOT_FIXTURE)
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("candidates", *date_args)
        self.assertEqual(code, 0, err)
        self.assertIn("选题候选", out)
        code, _, err = self.run_cli("choose-topic", *date_args, "--fixture", TOPIC_FIXTURE)
        self.assertEqual(code, 0, err)
        for cmd in ("research", "outline", "draft", "assemble"):
            code, _, err = self.run_cli(cmd, *date_args)
            self.assertEqual(code, 0, f"{cmd}: {err}")
        code, out, err = self.run_cli("status", *date_args)
        self.assertEqual(code, 0, err)
        self.assertIn("completed", out)

    def test_research_without_choice_exits_nonzero(self):
        code, _, err = self.run_cli("research", "--root", self.root, "--date", "2026-08-13")
        self.assertEqual(code, 1)
        self.assertIn("topic", err.lower())

    def test_choose_topic_simulate_chain_completes_without_recollect(self):
        date_args = ("--root", self.root, "--date", "2026-08-13")
        code, _, err = self.run_cli("collect", *date_args, "--mode", "fixture",
                                    "--aihot-fixture", AIHOT_FIXTURE)
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("choose-topic", *date_args,
                                      "--simulate", "--choice", "1")
        self.assertEqual(code, 0, err)
        self.assertIn("topic chosen:", out)
        state_path = pathlib.Path(self.root) / ".local" / "runs" / "2026-08-13" / "state.md"
        state_text = state_path.read_text(encoding="utf-8")
        self.assertIn("- topic_choice: simulated", state_text)
        self.assertIn("topic choice: simulated (unattended mode, candidate 1)", state_text)
        for cmd in ("research", "outline", "draft", "assemble"):
            code, _, err = self.run_cli(cmd, *date_args)
            self.assertEqual(code, 0, f"{cmd}: {err}")
        state_text = state_path.read_text(encoding="utf-8")
        self.assertIn("- stage: completed", state_text)
        self.assertIn("collect_runs: 1", state_text)

    def test_choose_topic_simulate_without_choice_autoselects_candidate_one(self):
        date_args = ("--root", self.root, "--date", "2026-08-13")
        code, _, err = self.run_cli("collect", *date_args, "--mode", "fixture",
                                    "--aihot-fixture", AIHOT_FIXTURE)
        self.assertEqual(code, 0, err)
        code, cands_out, err = self.run_cli("candidates", *date_args)
        self.assertEqual(code, 0, err)
        first_title = next(
            line[len("## 候选 1："):].strip()
            for line in cands_out.splitlines()
            if line.startswith("## 候选 1：")
        )
        code, _, err = self.run_cli("choose-topic", *date_args, "--simulate")
        self.assertEqual(code, 0, err)
        state_text = (
            pathlib.Path(self.root) / ".local" / "runs" / "2026-08-13" / "state.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- topic_choice: simulated", state_text)
        self.assertIn(f"- topic_title: {first_title}", state_text)
        self.assertIn("topic choice: simulated (unattended mode, candidate 1)", state_text)

    def test_choose_topic_simulate_with_fixture_is_usage_error(self):
        code, _, err = self.run_cli(
            "choose-topic", "--root", self.root, "--date", "2026-08-13",
            "--simulate", "--fixture", TOPIC_FIXTURE,
        )
        self.assertEqual(code, 2)
        self.assertIn("--simulate cannot be combined with --fixture", err)

    def test_unknown_command_exits_nonzero(self):
        code, _, err = self.run_cli("frobnicate")
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

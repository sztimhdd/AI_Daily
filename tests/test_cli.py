"""Tests for the CLI: subcommands, fixture E2E, error exits."""

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

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


class ResearchModeCliTests(CliBase):
    """CLI research routing: fixture (default) vs live (V2 initial)."""

    def test_research_default_mode_stays_on_fixture_path(self):
        with mock.patch.object(
            cli.pipeline, "run_research",
            return_value={"status": "generated", "research_md": pathlib.Path("/tmp/r.md")},
        ) as patched:
            code, out, err = self.run_cli(
                "research", "--root", self.root, "--date", "2026-08-12"
            )
        self.assertEqual(code, 0, err)
        self.assertIn("research: generated", out)
        patched.assert_called_once()

    def test_research_live_mode_routes_to_initial_research(self):
        with mock.patch.object(
            cli.pipeline, "run_initial_research",
            return_value={
                "status": "generated",
                "research_md": pathlib.Path("/tmp/initial-osint.md"),
                "analysis_status": "completed",
            },
        ) as patched:
            code, out, err = self.run_cli(
                "research", "--root", self.root, "--date", "2026-08-12", "--mode", "live"
            )
        self.assertEqual(code, 0, err)
        self.assertIn("research: generated", out)
        patched.assert_called_once()

    def test_research_invalid_mode_is_usage_error(self):
        code, _, err = self.run_cli(
            "research", "--root", self.root, "--date", "2026-08-12", "--mode", "bogus"
        )
        self.assertEqual(code, 2)
        self.assertIn("invalid choice", err)


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


class SessionCommandTests(CliBase):
    def _session_args(self, date="2026-08-13", *extra):
        return (
            "session", "--root", self.root, "--date", date,
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE, *extra,
        )

    def test_collect_prints_aihot_hot_topics(self):
        code, out, err = self.run_cli(
            "collect", "--root", self.root, "--date", "2026-08-13",
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE,
        )
        self.assertEqual(code, 0, err)
        self.assertIn("AIHOT 热点榜", out)
        self.assertIn(" 1. ", out)

    def test_session_completes_to_research_with_tui_output(self):
        code, out, err = self.run_cli(*self._session_args(), "--choice", "1")
        self.assertEqual(code, 0, err)
        self.assertIn("AIHOT 热点榜", out)
        self.assertIn("选题已定", out)
        self.assertIn("research:", out)
        state_text = (
            pathlib.Path(self.root) / ".local" / "runs" / "2026-08-13" / "state.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- stage: research", state_text)

    def test_session_rerun_skips_topic_prompt(self):
        first = self.run_cli(*self._session_args(), "--choice", "1")
        second = self.run_cli(*self._session_args())
        self.assertEqual(first[0], 0, first[2])
        self.assertEqual(second[0], 0, second[2])
        self.assertIn("选题已定", second[1])
        self.assertNotIn("选择 1..3", second[1])

    def test_session_without_choice_records_no_direction(self):
        class FakeTtyIn(io.StringIO):
            def isatty(self):
                return True

        with mock.patch.object(
            cli.tui, "prompt_choice", return_value=2
        ), mock.patch.object(
            sys, "stdin", FakeTtyIn("按企业采购视角写\n")
        ):
            code, out, err = self.run_cli(*self._session_args())
        self.assertEqual(code, 0, err)
        self.assertIn("选题已定", out)
        selected = json.loads(
            (
                pathlib.Path(self.root) / ".local" / "runs"
                / "2026-08-13" / "selected-topic.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(selected.get("direction"), "")
        state_text = (
            pathlib.Path(self.root) / ".local" / "runs" / "2026-08-13" / "state.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- topic_choice: human", state_text)

    def test_session_without_choice_on_piped_stdin_is_usage_error(self):
        with mock.patch.object(sys.stdin, "isatty", return_value=False):
            code, _, err = self.run_cli(*self._session_args())
        self.assertEqual(code, 2)
        self.assertIn("stdin", err.lower())

    def test_choose_topic_without_flags_on_piped_stdin_is_usage_error(self):
        code, _, err = self.run_cli(
            "collect", "--root", self.root, "--date", "2026-08-13",
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE,
        )
        self.assertEqual(code, 0, err)
        with mock.patch.object(sys.stdin, "isatty", return_value=False):
            code, _, err = self.run_cli(
                "choose-topic", "--root", self.root, "--date", "2026-08-13",
            )
        self.assertEqual(code, 2)
        self.assertIn("stdin", err.lower())

    def test_live_session_hint_stops_at_stage_03(self):
        aihot_item = {
            "title": "某热点", "summary": "", "source_name": "某源",
            "score": 80, "links": {"aihot": "https://aihot.virxact.com/items/x"},
        }
        cands = [{"title": "候选一", "thesis": "论点", "hook": "钩子"}]
        seen = {}

        def fake_collect(run_paths, **kwargs):
            run_paths.ensure_work_dir()
            (run_paths.work_dir / "aihot-items.json").write_text(
                json.dumps([aihot_item], ensure_ascii=False), encoding="utf-8"
            )
            return {"status": "collected"}

        def fake_initial(run_paths, **kwargs):
            seen["progress"] = kwargs.get("progress")
            return {"status": "generated", "research_md": "md"}

        with mock.patch.object(cli.pipeline, "run_collect", side_effect=fake_collect), \
             mock.patch.object(cli.pipeline, "run_candidates", return_value=cands), \
             mock.patch.object(cli.pipeline, "run_initial_research", side_effect=fake_initial):
            code, out, err = self.run_cli(
                "session", "--root", self.root, "--date", "2026-08-13",
                "--mode", "live", "--choice", "1",
            )
        self.assertEqual(code, 0, err)
        self.assertIn("本会话结束", out)
        self.assertNotIn("下一步：outline", out)
        self.assertTrue(callable(seen.get("progress")))


if __name__ == "__main__":
    unittest.main()

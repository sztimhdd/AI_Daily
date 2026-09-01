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
    def test_collect_and_research_default_to_live_mode(self):
        parser = cli.build_parser()
        collect = parser.parse_args(["collect", "--root", self.root])
        self.assertEqual(collect.mode, "live")
        research = parser.parse_args(["research", "--root", self.root])
        self.assertEqual(research.mode, "live")

    def test_kg_command_prints_background_status(self):
        with mock.patch.object(
            cli.pipeline, "run_knowledge_background",
            return_value={"status": "completed", "reason": ""},
        ) as patched:
            code, out, _ = self.run_cli(
                "kg", "--root", self.root, "--date", "2026-08-12"
            )
        self.assertEqual(code, 0, out)
        self.assertIn("kg background: completed", out)
        patched.assert_called_once()

    def test_zhihu_command_prints_community_status(self):
        with mock.patch.object(
            cli.pipeline, "run_zhihu_community",
            return_value={"status": "ok", "reason": ""},
        ) as patched:
            code, out, _ = self.run_cli(
                "zhihu", "--root", self.root, "--date", "2026-08-12"
            )
        self.assertEqual(code, 0, out)
        self.assertIn("zhihu community: ok", out)
        patched.assert_called_once()

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

    def test_research_default_mode_is_live(self):
        with mock.patch.object(
            cli.pipeline, "run_initial_research",
            return_value={
                "status": "generated",
                "research_md": pathlib.Path("/tmp/initial-osint.md"),
                "analysis_status": "completed",
            },
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
        code, _, err = self.run_cli("research", *date_args, "--mode", "fixture")
        self.assertEqual(code, 0, err)
        for cmd in ("outline", "draft", "assemble"):
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
        code, _, err = self.run_cli("research", *date_args, "--mode", "fixture")
        self.assertEqual(code, 0, err)
        for cmd in ("outline", "draft", "assemble"):
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

    def test_narrative_no_prompt_returns_after_generating_candidates(self):
        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        candidates = [{
            "archetype": "reported_story", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [],
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断", "personal_scene": "现场",
            "kicker": "结尾。", "evidence_audit": "e",
        }]
        with mock.patch.object(
            cli.pipeline, "run_narrative",
            return_value={"status": "generated", "candidates": candidates},
        ):
            code, _out, err = self.run_cli(
                "narrative", "--root", self.root, "--date", "2026-08-13",
                "--no-prompt",
            )
        self.assertEqual(code, 0, err)

    def test_session_rerun_skips_topic_prompt(self):
        first = self.run_cli(*self._session_args(), "--choice", "1")
        second = self.run_cli(*self._session_args())
        self.assertEqual(first[0], 0, first[2])
        self.assertEqual(second[0], 0, second[2])
        self.assertIn("选题已定", second[1])
        self.assertNotIn("选择 1..3", second[1])

    def test_session_force_keeps_existing_topic_choice(self):
        first = self.run_cli(*self._session_args(), "--choice", "1")
        second = self.run_cli(*self._session_args(), "--force")
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
        cands = [{
            "title": "候选一", "thesis": "论点", "hook": "钩子",
            "research_queries": ["查询"],
            "sources": [{"url": "https://example.com/x"}],
        }]
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

        def fake_narrative(run_paths, **kwargs):
            return {
                "status": "generated",
                "candidates": [{
                    "archetype": "decision_brief", "title": "叙事一",
                    "hook": "h", "thesis": "t", "key_arguments": [],
                    "decision_rule": "d",
                    "platform_notes": {"linkedin": "l", "wechat": "w"},
                    "author_stance": "我的判断",
                    "personal_scene": "凌晨三点被报警吵醒",
                    "kicker": "先别急着上车。",
                    "evidence_audit": "e",
                }],
            }

        def fake_sufficiency(run_paths, **kwargs):
            return {
                "status": "completed", "verdict": "sufficient",
                "claim_coverage": [], "evidence_gaps": [],
                "research_tasks": [], "reason": "",
            }

        with mock.patch.object(cli.pipeline, "run_collect", side_effect=fake_collect), \
             mock.patch.object(cli.pipeline, "run_candidates", return_value=cands), \
             mock.patch.object(cli.pipeline, "run_initial_research", side_effect=fake_initial), \
             mock.patch.object(cli.pipeline, "run_narrative", side_effect=fake_narrative), \
             mock.patch.object(cli.pipeline, "run_sufficiency", side_effect=fake_sufficiency), \
             mock.patch.object(
                 cli.pipeline, "run_targeted_loop",
                 return_value={"status": "completed", "verdict": "sufficient",
                               "rounds": 0, "reason": ""},
             ):
            code, out, err = self.run_cli(
                "session", "--root", self.root, "--date", "2026-08-13",
                "--mode", "live", "--choice", "1", "--narrative-choice", "1",
            )
        self.assertEqual(code, 0, err)
        self.assertIn("04 已跑完", out)
        self.assertNotIn("下一步：outline", out)
        self.assertTrue(callable(seen.get("progress")))

    def test_live_session_runs_narrative_and_stops_at_04(self):
        aihot_item = {
            "title": "某热点", "summary": "", "source_name": "某源",
            "score": 80, "links": {"aihot": "https://aihot.virxact.com/items/x"},
        }
        cands = [{
            "title": "候选一", "thesis": "论点", "hook": "钩子",
            "research_queries": ["查询"],
            "sources": [{"url": "https://example.com/x"}],
        }]
        narrative_cands = [{
            "archetype": "cost_ledger", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断",
            "personal_scene": "凌晨三点被报警吵醒",
            "kicker": "先别急着上车。",
            "evidence_audit": "e",
        }]
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

        def fake_narrative(run_paths, **kwargs):
            return {"status": "generated", "candidates": narrative_cands}

        def fake_sufficiency(run_paths, **kwargs):
            return {
                "status": "completed", "verdict": "sufficient",
                "claim_coverage": [], "evidence_gaps": [],
                "research_tasks": [], "reason": "",
            }

        with mock.patch.object(cli.pipeline, "run_collect", side_effect=fake_collect), \
             mock.patch.object(cli.pipeline, "run_candidates", return_value=cands), \
             mock.patch.object(cli.pipeline, "run_initial_research", side_effect=fake_initial), \
             mock.patch.object(cli.pipeline, "run_narrative", side_effect=fake_narrative), \
             mock.patch.object(cli.pipeline, "run_sufficiency", side_effect=fake_sufficiency), \
             mock.patch.object(
                 cli.pipeline, "run_targeted_loop",
                 return_value={"status": "completed", "verdict": "sufficient",
                               "rounds": 0, "reason": ""},
             ):
            code, out, err = self.run_cli(
                "session", "--root", self.root, "--date", "2026-08-13",
                "--mode", "live", "--choice", "1", "--narrative-choice", "1",
            )
        self.assertEqual(code, 0, err)
        self.assertIn("叙事一", out)
        self.assertIn("04 已跑完", out)
        self.assertIn("05", out)
        self.assertIn("正在调用 Codex 生成两个叙事候选", out)
        self.assertIn("正在调用 Codex 审计证据充分性", out)

    def test_fixture_session_stops_at_03_without_narrative(self):
        with mock.patch.object(
            cli.pipeline, "run_narrative"
        ) as run_narrative:
            code, out, err = self.run_cli(*self._session_args(), "--choice", "1")
        self.assertEqual(code, 0, err)
        run_narrative.assert_not_called()
        self.assertIn("03 已跑完", out)

    def test_narrative_command_records_choice(self):
        from ai_daily import paths, state

        narrative_cands = [{
            "archetype": "cost_ledger", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断",
            "personal_scene": "凌晨三点被报警吵醒",
            "kicker": "先别急着上车。",
            "evidence_audit": "e",
        }]
        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        with mock.patch.object(
            cli.pipeline, "run_narrative",
            return_value={"status": "generated", "candidates": narrative_cands},
        ):
            code, out, err = self.run_cli(
                "narrative", "--root", self.root, "--date", "2026-08-13",
                "--choice", "1", "--extra-research", "补证：供应商访谈",
            )
        self.assertEqual(code, 0, err)
        self.assertIn("叙事一", out)
        st = state.read_state(run_paths)
        self.assertEqual(st.get("narrative_choice"), "human")
        self.assertEqual(st.get("narrative_title"), "叙事一")

    def test_live_session_audit_sufficient_hints_stage_07(self):
        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        (run_paths.work_dir / "aihot-items.json").write_text(
            json.dumps([{
                "title": "某热点", "summary": "成本", "source_name": "某源",
                "score": 80, "links": {"aihot": "https://aihot.virxact.com/items/x"},
            }], ensure_ascii=False), encoding="utf-8"
        )
        cands = [{
            "title": "候选一", "thesis": "论点", "hook": "钩子",
            "research_queries": ["查询"],
            "sources": [{"url": "https://example.com/x"}],
        }]
        narrative_cands = [{
            "archetype": "cost_ledger", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断",
            "personal_scene": "凌晨三点被报警吵醒",
            "kicker": "先别急着上车。",
            "evidence_audit": "e",
        }]

        with mock.patch.object(cli.pipeline, "run_collect",
                               side_effect=lambda run_paths, **kw: {"status": "collected"}), \
             mock.patch.object(cli.pipeline, "run_candidates", return_value=cands), \
             mock.patch.object(cli.pipeline, "run_initial_research",
                               return_value={"status": "generated", "research_md": "md"}), \
             mock.patch.object(cli.pipeline, "run_narrative",
                               return_value={"status": "generated",
                                             "candidates": narrative_cands}), \
             mock.patch.object(cli.pipeline, "run_sufficiency",
                               return_value={"status": "completed",
                                             "verdict": "sufficient",
                                             "claim_coverage": [],
                                             "evidence_gaps": [],
                                             "research_tasks": [],
                                             "reason": ""}), \
             mock.patch.object(cli.pipeline, "run_targeted_loop",
                               return_value={"status": "completed",
                                             "verdict": "sufficient",
                                             "rounds": 0, "reason": ""}):
            code, out, err = self.run_cli(
                "session", "--root", self.root, "--date", "2026-08-13",
                "--mode", "live", "--choice", "1", "--narrative-choice", "1",
            )
        self.assertEqual(code, 0, err)
        self.assertIn("证据充分性审计", out)
        self.assertIn("sufficient", out)
        self.assertIn("07", out)

    def test_live_session_audit_unsupported_blocks(self):
        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        (run_paths.work_dir / "aihot-items.json").write_text(
            json.dumps([{
                "title": "某热点", "summary": "成本", "source_name": "某源",
                "score": 80, "links": {"aihot": "https://aihot.virxact.com/items/x"},
            }], ensure_ascii=False), encoding="utf-8"
        )
        cands = [{
            "title": "候选一", "thesis": "论点", "hook": "钩子",
            "research_queries": ["查询"],
            "sources": [{"url": "https://example.com/x"}],
        }]
        narrative_cands = [{
            "archetype": "cost_ledger", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断",
            "personal_scene": "凌晨三点被报警吵醒",
            "kicker": "先别急着上车。",
            "evidence_audit": "e",
        }]

        with mock.patch.object(cli.pipeline, "run_collect",
                               side_effect=lambda run_paths, **kw: {"status": "collected"}), \
             mock.patch.object(cli.pipeline, "run_candidates", return_value=cands), \
             mock.patch.object(cli.pipeline, "run_initial_research",
                               return_value={"status": "generated", "research_md": "md"}), \
             mock.patch.object(cli.pipeline, "run_narrative",
                               return_value={"status": "generated",
                                             "candidates": narrative_cands}), \
             mock.patch.object(cli.pipeline, "run_sufficiency",
                               return_value={"status": "completed",
                                             "verdict": "unsupported",
                                             "claim_coverage": [],
                                             "evidence_gaps": [],
                                             "research_tasks": [],
                                             "reason": "核心论点缺一手证据"}):
            code, out, err = self.run_cli(
                "session", "--root", self.root, "--date", "2026-08-13",
                "--mode", "live", "--choice", "1", "--narrative-choice", "1",
            )
        self.assertEqual(code, 1, err)
        self.assertIn("unsupported", out)
        self.assertIn("阻塞", out)
        self.assertIn("核心论点缺一手证据", out)

    def test_live_session_needs_research_runs_targeted_loop(self):
        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        (run_paths.work_dir / "aihot-items.json").write_text(
            json.dumps([{
                "title": "某热点", "summary": "成本", "source_name": "某源",
                "score": 80, "links": {"aihot": "https://aihot.virxact.com/items/x"},
            }], ensure_ascii=False), encoding="utf-8"
        )
        cands = [{
            "title": "候选一", "thesis": "论点", "hook": "钩子",
            "research_queries": ["查询"],
            "sources": [{"url": "https://example.com/x"}],
        }]
        narrative_cands = [{
            "archetype": "cost_ledger", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断",
            "personal_scene": "凌晨三点被报警吵醒",
            "kicker": "先别急着上车。",
            "evidence_audit": "e",
        }]

        with mock.patch.object(cli.pipeline, "run_collect",
                               side_effect=lambda run_paths, **kw: {"status": "collected"}), \
             mock.patch.object(cli.pipeline, "run_candidates", return_value=cands), \
             mock.patch.object(cli.pipeline, "run_initial_research",
                               return_value={"status": "generated", "research_md": "md"}), \
             mock.patch.object(cli.pipeline, "run_narrative",
                               return_value={"status": "generated",
                                             "candidates": narrative_cands}), \
             mock.patch.object(cli.pipeline, "run_sufficiency",
                               return_value={"status": "completed",
                                             "verdict": "needs_research",
                                             "claim_coverage": [],
                                             "evidence_gaps": [],
                                             "research_tasks": [{
                                                 "gap_type": "单一来源",
                                                 "query": "q",
                                                 "direction": "d"}],
                                             "reason": ""}), \
             mock.patch.object(cli.pipeline, "run_targeted_loop",
                               return_value={"status": "completed",
                                             "verdict": "sufficient",
                                             "rounds": 1, "reason": ""}):
            code, out, err = self.run_cli(
                "session", "--root", self.root, "--date", "2026-08-13",
                "--mode", "live", "--choice", "1", "--narrative-choice", "1",
            )
        self.assertEqual(code, 0, err)
        self.assertIn("补证 1 轮", out)
        self.assertIn("07", out)

    def test_narrative_simulate_flag_records_unattended(self):
        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        narrative_cands = [{
            "archetype": "cost_ledger", "title": "叙事一", "hook": "h",
            "thesis": "t", "key_arguments": [], "decision_rule": "d",
            "platform_notes": {"linkedin": "l", "wechat": "w"},
            "author_stance": "我的判断",
            "personal_scene": "凌晨三点被报警吵醒",
            "kicker": "先别急着上车。",
            "evidence_audit": "e",
        }]
        with mock.patch.object(
            cli.pipeline, "run_narrative",
            return_value={"status": "generated", "candidates": narrative_cands},
        ):
            code, out, err = self.run_cli(
                "narrative", "--root", self.root, "--date", "2026-08-13",
                "--choice", "1", "--simulate",
            )
        self.assertEqual(code, 0, err)
        st = state.read_state(run_paths)
        self.assertEqual(st.get("narrative_choice"), "simulated")

    def test_audit_command_sufficient_runs_zero_round_loop_for_evidence_package(self):
        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        with mock.patch.object(
            cli.pipeline, "run_sufficiency",
            return_value={"status": "completed", "verdict": "sufficient",
                          "claim_coverage": [], "evidence_gaps": [],
                          "research_tasks": [], "reason": ""},
        ), mock.patch.object(
            cli.pipeline, "run_targeted_loop",
            return_value={"status": "completed", "verdict": "sufficient",
                          "rounds": 0, "reason": ""},
        ) as loop_mock:
            code, out, err = self.run_cli(
                "audit", "--root", self.root, "--date", "2026-08-13",
            )
        self.assertEqual(code, 0, err)
        loop_mock.assert_called_once()
        self.assertEqual(loop_mock.call_args.kwargs["initial_audit"]["verdict"],
                         "sufficient")
        self.assertIn("07", out)

    def _seed_stale_run(self, date, stale=False):
        import datetime as _dt
        import os

        from ai_daily import paths, state

        run_paths = paths.RunPaths.for_date(self.root, date)
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        state.update_fields(
            run_paths,
            topic_choice="human",
            slug="old-slug",
            topic_title="昨天录的旧选题",
        )
        pool_path = run_paths.work_dir / "aihot-items.json"
        pool_path.write_text(
            json.dumps(
                [
                    {
                        "title": f"旧事件{i}", "summary": summary,
                        "source_name": "旧源", "score": 10,
                        "discovered_at": (
                            _dt.date.today() - _dt.timedelta(days=1)
                        ).isoformat() + "T12:00:00.000Z",
                        "links": {"aihot": "https://aihot.virxact.com/items/o"},
                        "origin": "aihot",
                    }
                    for i, summary in enumerate(
                        (
                            "多家推理服务商调整定价，企业成本结构将重算",
                            "开源模型权重发布，工程团队工作流将改变",
                            "平台抽成政策调整，生态格局将重排",
                        ),
                        1,
                    )
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        if stale:
            yesterday = _dt.datetime.now() - _dt.timedelta(days=1)
            os.utime(pool_path, (yesterday.timestamp(), yesterday.timestamp()))
        (run_paths.work_dir / "selected-topic.json").write_text(
            json.dumps({"title": "昨天录的旧选题"}, ensure_ascii=False),
            encoding="utf-8",
        )
        return run_paths

    def test_session_resets_stale_previous_day_run(self):
        from ai_daily import state

        date = "2026-08-15"
        run_paths = self._seed_stale_run(
            date, stale=True
        )
        (run_paths.work_dir / "narrative-candidates.json").write_text(
            json.dumps({"candidates": []}), encoding="utf-8"
        )
        (run_paths.work_dir / "selected-narrative.json").write_text(
            json.dumps({"title": "旧叙事"}), encoding="utf-8"
        )
        code, out, err = self.run_cli(
            "session", "--root", self.root, "--date", date,
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE,
            "--choice", "1",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("过期", out)
        st = state.read_state(run_paths)
        self.assertNotEqual(st.get("topic_title"), "昨天录的旧选题")
        self.assertEqual(st.get("stage"), "research")
        self.assertFalse((run_paths.work_dir / "narrative-candidates.json").exists())
        self.assertFalse((run_paths.work_dir / "selected-narrative.json").exists())

    def test_session_keeps_same_day_run(self):
        from ai_daily import state

        date = "2026-08-15"
        run_paths = self._seed_stale_run(date)
        code, out, err = self.run_cli(
            "session", "--root", self.root, "--date", date,
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE,
        )
        self.assertEqual(code, 0, err)
        self.assertNotIn("过期", out)
        self.assertIn("选题已定", out)
        self.assertEqual(
            state.read_state(run_paths).get("topic_title"), "昨天录的旧选题"
        )


class EnglishEditionCliTests(CliBase):
    def test_parser_registers_english_subcommands(self):
        self.assertIn("draft-en", cli.COMMANDS)
        self.assertIn("assemble-en", cli.COMMANDS)
        self.assertIn("run-en", cli.COMMANDS)

    def test_run_en_prints_summary(self):
        with mock.patch.object(
            cli.pipeline, "run_delivery_en",
            return_value={"status": "delivered", "summary": "delivery-en.json"},
        ) as patched:
            code, out, err = self.run_cli(
                "run-en", "--root", self.root, "--date", "2026-08-20"
            )
        self.assertEqual(code, 0, err)
        patched.assert_called_once()
        self.assertIn("summary: delivery-en.json", out)

    def test_run_en_returns_one_for_hard_failure(self):
        with mock.patch.object(
            cli.pipeline, "run_delivery_en",
            return_value={"status": "failed", "reason": "draft unavailable"},
        ):
            code, _out, _err = self.run_cli(
                "run-en", "--root", self.root, "--date", "2026-08-20"
            )
        self.assertEqual(code, 1)

    def test_draft_en_command_invokes_pipeline(self):
        result = {
            "status": "generated",
            "article": "article-en.md",
            "verdict": "pass",
            "word_count": 850,
        }
        with mock.patch.object(
            cli.pipeline, "run_draft_en", return_value=result
        ) as patched:
            code, out, err = self.run_cli(
                "draft-en", "--root", self.root, "--date", "2026-08-20"
            )
        self.assertEqual(code, 0, err)
        patched.assert_called_once()
        self.assertIn("pass", out)

    def test_draft_en_unavailable_exits_1(self):
        result = {"status": "unavailable", "reason": "down"}
        with mock.patch.object(cli.pipeline, "run_draft_en", return_value=result):
            code, out, err = self.run_cli(
                "draft-en", "--root", self.root, "--date", "2026-08-20"
            )
        self.assertEqual(code, 1)

    def test_assemble_en_command_invokes_pipeline(self):
        result = {
            "status": "assembled",
            "package_dir": "outputs/2026/08/20/slug",
            "final_article": "articles/2026-08-20-slug-en.md",
        }
        with mock.patch.object(
            cli.pipeline, "run_assemble_en", return_value=result
        ) as patched:
            code, out, err = self.run_cli(
                "assemble-en", "--root", self.root, "--date", "2026-08-20"
            )
        self.assertEqual(code, 0, err)
        patched.assert_called_once()
        self.assertIn("assemble-en: assembled", out)

    def test_telegram_command_invokes_adapter(self):
        from ai_daily import telegram_adapter

        result = {
            "offered": "topic",
            "reply": "1",
            "applied": {"ok": True, "decision": "topic", "chosen": "T"},
        }
        with mock.patch.object(
            cli.telegram_adapter, "run_once", return_value=result
        ) as patched:
            code, out, err = self.run_cli(
                "telegram", "--root", self.root, "--date", "2026-08-20"
            )
        self.assertEqual(code, 0, err)
        patched.assert_called_once()
        self.assertIn("telegram: offered=topic", out)

    def test_telegram_command_offer_only(self):
        from ai_daily import telegram_adapter

        with mock.patch.object(
            cli.telegram_adapter, "load_config",
            return_value={"token": "T", "chat": "C"},
        ), mock.patch.object(
            cli.telegram_adapter, "offer",
            return_value={"ok": True, "offered": "narrative"},
        ) as patched:
            code, _out, err = self.run_cli(
                "telegram", "--root", self.root, "--date", "2026-08-20",
                "--offer-only",
            )
        self.assertEqual(code, 0, err)
        patched.assert_called_once()


if __name__ == "__main__":
    unittest.main()

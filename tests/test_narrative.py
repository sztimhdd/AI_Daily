"""Tests for 04 narrative candidates: evidence routing, generation, HITL."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import STAGES, narrative, paths, state, topics


def sample_osint():
    return {
        "analysis_status": "completed",
        "modules": [
            {"key": "core_timeline", "title": "时间线", "summary": "8月发布。"},
            {"key": "finance_capital", "title": "财务", "summary": "定价 $0.75/1M"},
            {"key": "tech_engineering", "title": "工程", "summary": "743B 基座"},
            {"key": "ecosystem_moat", "title": "生态", "summary": "无"},
            {"key": "community_voices", "title": "社区", "summary": "V2EX 实测"},
            {"key": "org_people", "title": "人事", "summary": "无"},
            {"key": "editor_direction_check", "title": "主编核查", "summary": "无"},
        ],
        "evidence_gaps": [],
        "sources": [
            {"url": "https://example.com/a", "status": "fetched", "title": "发布"},
        ],
    }


class StagesOrderTests(unittest.TestCase):
    def test_narrative_stage_follows_research(self):
        self.assertEqual(
            STAGES[STAGES.index("research") + 1], "narrative"
        )


class EvidenceInventoryTests(unittest.TestCase):
    def test_module_signals_map_to_inventory_flags(self):
        inv = narrative.evidence_inventory(sample_osint())
        self.assertTrue(inv["cost_data"])
        self.assertTrue(inv["mechanism_signal"])
        self.assertTrue(inv["community_signal"])
        self.assertTrue(inv["primary_signal"])
        self.assertFalse(inv["org_source"])
        self.assertFalse(inv["policy_text"])

    def test_policy_url_and_org_summary_set_flags(self):
        osint = sample_osint()
        osint["modules"][5]["summary"] = "CEO 离职"
        osint["sources"].append({
            "url": "https://eur-lex.europa.eu/x", "status": "fetched",
            "title": "AI Act",
        })
        inv = narrative.evidence_inventory(osint)
        self.assertTrue(inv["org_source"])
        self.assertTrue(inv["policy_text"])

    def test_no_evidence_means_no_primary_signal(self):
        inv = narrative.evidence_inventory({"modules": [], "sources": [], "evidence_gaps": []})
        self.assertFalse(inv["primary_signal"])


class TensionDetectionTests(unittest.TestCase):
    def test_counter_consensus_hook_detected(self):
        topic = {"title": "X 发布", "hook": "反共识点：大家都盯单价，真账在调用次数"}
        tensions = narrative.tension_detection(topic, sample_osint())
        self.assertIn("consensus_vs_data", tensions)

    def test_price_tension_from_topic(self):
        topic = {"title": "API 涨价", "hook": ""}
        tensions = narrative.tension_detection(topic, sample_osint())
        self.assertIn("price_vs_tco", tensions)


class RouteArchetypeTests(unittest.TestCase):
    def test_cost_and_org_route_to_their_archetypes(self):
        osint = sample_osint()
        osint["modules"][5]["summary"] = "CEO 离职"
        allowed = narrative.route_archetypes(osint, {"consensus_vs_data"})
        self.assertIn("cost_ledger", allowed)
        self.assertIn("power_map", allowed)
        self.assertIn("decision_brief", allowed)
        self.assertNotIn("compliance_risk", allowed)

    def test_empty_evidence_kills_generation(self):
        with self.assertRaises(narrative.NarrativeError):
            narrative.route_archetypes(
                {"modules": [], "sources": [], "evidence_gaps": []}, set()
            )


class NarrativeRunTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-15")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)
        topics.choose_fixture(
            self.run_paths,
            pathlib.Path(__file__).resolve().parent / "fixtures" / "topic_fixture.json",
        )
        (self.run_paths.work_dir / "initial-osint.json").write_text(
            json.dumps(sample_osint(), ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def make_runner(archetype="cost_ledger"):
        def runner(prompt):
            return {
                "candidates": [
                    {
                        "archetype": archetype,
                        "title": "标题一",
                        "hook": "事实。冲突。决策。",
                        "thesis": "论点一",
                        "key_arguments": [{
                            "claim": "成本更低", "observable": "$5 vs $30",
                            "source": "账单", "limitation": "厂商自测",
                            "decision": "可复测",
                        }],
                        "decision_rule": "条件成立才切",
                        "platform_notes": {"linkedin": "LN", "wechat": "WX"},
                        "evidence_audit": "EO 充足",
                    },
                    {
                        "archetype": "decision_brief",
                        "title": "标题二",
                        "hook": "事实。冲突。决策。",
                        "thesis": "论点二",
                        "key_arguments": [{
                            "claim": "先观察", "observable": "单一来源",
                            "source": "官方帖", "limitation": "未双源",
                            "decision": "等待复测",
                        }],
                        "decision_rule": "先观察",
                        "platform_notes": {"linkedin": "LN2", "wechat": "WX2"},
                        "evidence_audit": "EO 充足",
                    },
                ]
            }
        return runner

    def test_run_writes_candidates_and_returns_two(self):
        result = narrative.run(
            self.run_paths, codex_runner=self.make_runner(), force=True
        )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(len(result["candidates"]), 2)
        data = json.loads(
            (self.run_paths.work_dir / "narrative-candidates.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(data["candidates"]), 2)
        md = (self.run_paths.work_dir / "narrative-candidates.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("标题一", md)

    def test_archetype_outside_whitelist_rejected(self):
        result = narrative.run(
            self.run_paths, codex_runner=self.make_runner("compliance_risk"),
            force=True,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("compliance_risk", result["reason"])

    def test_resume_skips_regeneration(self):
        calls = {"n": 0}

        def runner(prompt):
            calls["n"] += 1
            return self.make_runner()(prompt)

        first = narrative.run(self.run_paths, codex_runner=runner, force=True)
        second = narrative.run(self.run_paths, codex_runner=runner)
        self.assertEqual(first["status"], "generated")
        self.assertEqual(second["status"], "resumed")
        self.assertEqual(calls["n"], 1)

    def test_resume_records_narrative_stage(self):
        narrative.run(self.run_paths, codex_runner=self.make_runner(), force=True)
        self.assertEqual(
            state.read_state(self.run_paths)["stage"], "narrative"
        )
        narrative.run(self.run_paths, codex_runner=self.make_runner())
        self.assertEqual(
            state.read_state(self.run_paths)["stage"], "narrative"
        )

    def test_non_conforming_candidate_list_rejected(self):
        def runner(prompt):
            return {"candidates": [self.make_runner()(prompt)["candidates"][0]]}

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("non-conforming", result["reason"])

    def test_non_dict_candidate_rejected_cleanly(self):
        def runner(prompt):
            return {"candidates": ["不是对象", None]}

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")

    def test_missing_five_part_argument_fields_rejected(self):
        def runner(prompt):
            payload = self.make_runner()(prompt)
            payload["candidates"][0]["key_arguments"] = [
                {"claim": "只有 claim", "observable": "", "source": "",
                 "limitation": "", "decision": ""}
            ]
            return payload

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("observable", result["reason"])

    def test_missing_evidence_audit_rejected(self):
        def runner(prompt):
            payload = self.make_runner()(prompt)
            del payload["candidates"][0]["evidence_audit"]
            return payload

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("evidence_audit", result["reason"])

    def test_decision_brief_only_fallback(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/x", "status": "fetched", "title": "发布",
        }]
        allowed = narrative.route_archetypes(osint, set())
        self.assertEqual(allowed, ["decision_brief"])


class NarrativeGateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-15")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)

    def tearDown(self):
        self._tmp.cleanup()

    def test_require_narrative_blocks_before_choice(self):
        with self.assertRaises(narrative.NarrativeGateBlocked):
            narrative.require_narrative(self.run_paths)

    def test_record_choice_persists_durable_decision(self):
        candidates = [
            {
                "archetype": "cost_ledger", "title": "账本篇",
                "hook": "h", "thesis": "t", "key_arguments": [],
                "decision_rule": "d",
                "platform_notes": {"linkedin": "l", "wechat": "w"},
                "evidence_audit": "e",
            }
        ]
        chosen = narrative.record_choice(
            self.run_paths, candidates, 1, extra_research="补证：供应商访谈"
        )
        self.assertEqual(chosen["title"], "账本篇")
        selected = json.loads(
            (self.run_paths.work_dir / "selected-narrative.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(selected["archetype"], "cost_ledger")
        st = state.read_state(self.run_paths)
        self.assertEqual(st["narrative_choice"], "human")
        self.assertEqual(st["narrative_title"], "账本篇")
        self.assertEqual(st["narrative_archetype"], "cost_ledger")
        self.assertEqual(narrative.require_narrative(self.run_paths)["title"], "账本篇")

    def test_record_choice_rejects_out_of_range(self):
        with self.assertRaises(narrative.NarrativeError):
            narrative.record_choice(self.run_paths, [], 1)

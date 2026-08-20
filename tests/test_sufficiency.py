"""Tests for 05 evidence-sufficiency audit gate."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import narrative, paths, state, sufficiency


def sample_osint():
    return {
        "analysis_status": "completed",
        "modules": [
            {"key": "core_timeline", "title": "时间线", "summary": "8月发布。"},
        ],
        "evidence_gaps": [],
        "sources": [
            {"url": "https://example.com/a", "status": "fetched", "title": "发布"},
        ],
    }


def sample_narrative_candidate():
    return {
        "archetype": "cost_ledger", "title": "账本篇", "hook": "h",
        "thesis": "t", "key_arguments": [], "decision_rule": "d",
        "platform_notes": {"linkedin": "l", "wechat": "w"},
        "author_stance": "我的判断",
        "personal_scene": "凌晨三点被报警吵醒",
        "kicker": "先别急着上车。",
        "evidence_audit": "e",
    }


class SufficiencyBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-20")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)
        state.update_fields(
            self.run_paths,
            topic_choice="human",
            topic_title="选题",
            slug="slug",
        )
        narrative.record_choice(
            self.run_paths, [sample_narrative_candidate()], 1
        )
        (self.run_paths.work_dir / "initial-osint.json").write_text(
            json.dumps(sample_osint(), ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def audit_payload(verdict="sufficient", tasks=None, reason=""):
        return {
            "verdict": verdict,
            "claim_coverage": [{"claim": "c", "coverage": "supported"}],
            "evidence_gaps": ["gap"],
            "research_tasks": tasks or [],
            "reason": reason,
        }


class SufficiencyRunTests(SufficiencyBase):
    def test_sufficient_verdict_persists(self):
        result = sufficiency.run(
            self.run_paths,
            codex_runner=lambda p: self.audit_payload("sufficient"),
            force=True,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verdict"], "sufficient")
        data = json.loads(
            (self.run_paths.work_dir / "sufficiency-audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["verdict"], "sufficient")
        self.assertEqual(
            sufficiency.require_sufficient(self.run_paths)["verdict"],
            "sufficient",
        )

    def test_needs_research_requires_tasks(self):
        result = sufficiency.run(
            self.run_paths,
            codex_runner=lambda p: self.audit_payload("needs_research"),
            force=True,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("research_tasks", result["reason"])

    def test_needs_research_with_tasks_passes(self):
        payload = self.audit_payload("needs_research")
        payload["research_tasks"] = [
            {"gap_type": "缺真实使用反馈", "query": "实测 GLM", "direction": "zhida"}
        ]
        result = sufficiency.run(
            self.run_paths, codex_runner=lambda p: payload, force=True
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verdict"], "needs_research")

    def test_unsupported_requires_reason(self):
        result = sufficiency.run(
            self.run_paths,
            codex_runner=lambda p: self.audit_payload("unsupported", reason=""),
            force=True,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("reason", result["reason"])


class WritableGateTests(SufficiencyBase):
    """require_writable: sufficient + needs_research pass; unsupported blocks."""

    def _audit(self, verdict):
        (self.run_paths.work_dir / "sufficiency-audit.json").write_text(
            json.dumps(
                {
                    "narrative_title": "账本篇",
                    "verdict": verdict,
                    "reason": "r",
                    "evidence_gaps": ["gap"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def test_sufficient_is_writable_without_downgrade(self):
        self._audit("sufficient")
        audit = sufficiency.require_writable(self.run_paths)
        self.assertEqual(audit["verdict"], "sufficient")

    def test_needs_research_is_writable(self):
        self._audit("needs_research")
        audit = sufficiency.require_writable(self.run_paths)
        self.assertEqual(audit["verdict"], "needs_research")

    def test_unsupported_blocks(self):
        self._audit("unsupported")
        with self.assertRaises(sufficiency.AuditGateBlocked):
            sufficiency.require_writable(self.run_paths)

    def test_invalid_verdict_rejected(self):
        payload = self.audit_payload("maybe")
        payload["reason"] = "x"
        result = sufficiency.run(
            self.run_paths, codex_runner=lambda p: payload, force=True
        )
        self.assertEqual(result["status"], "unavailable")

    def test_runner_failure_records_unavailable(self):
        def broken(prompt):
            return {"status": "unavailable", "reason": "no output"}

        result = sufficiency.run(
            self.run_paths, codex_runner=broken, force=True
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["verdict"], "unavailable")

    def test_audit_blocked_without_narrative_choice(self):
        fresh = paths.RunPaths.for_date(self.root, "2026-08-21")
        fresh.ensure_work_dir()
        state.init_state(fresh)
        with self.assertRaises(narrative.NarrativeGateBlocked):
            sufficiency.run(fresh, codex_runner=lambda p: self.audit_payload())

    def test_require_sufficient_blocks_when_needs_research(self):
        payload = self.audit_payload("needs_research")
        payload["research_tasks"] = [
            {"gap_type": "x", "query": "q", "direction": "d"}
        ]
        sufficiency.run(
            self.run_paths, codex_runner=lambda p: payload, force=True
        )
        with self.assertRaises(sufficiency.AuditGateBlocked):
            sufficiency.require_sufficient(self.run_paths)

    def test_prompt_includes_narrative_thesis_and_evidence(self):
        prompt = sufficiency._compile_prompt(
            sample_narrative_candidate(), sample_osint(), [], 1
        )
        self.assertIn("账本篇", prompt)
        self.assertIn("t", prompt)
        self.assertIn("https://example.com/a", prompt)
        self.assertIn("sufficient", prompt)

    def test_resume_with_different_narrative_reruns(self):
        calls = {"n": 0}

        def runner(prompt):
            calls["n"] += 1
            return self.audit_payload("sufficient")

        sufficiency.run(self.run_paths, codex_runner=runner, force=True)
        other = sample_narrative_candidate()
        other["title"] = "另一篇叙事"
        narrative.record_choice(self.run_paths, [other], 1)
        result = sufficiency.run(self.run_paths, codex_runner=runner)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(calls["n"], 2)

    def test_require_sufficient_blocks_mismatched_narrative(self):
        sufficiency.run(
            self.run_paths,
            codex_runner=lambda p: self.audit_payload("sufficient"),
            force=True,
        )
        other = sample_narrative_candidate()
        other["title"] = "另一篇叙事"
        narrative.record_choice(self.run_paths, [other], 1)
        with self.assertRaises(sufficiency.AuditGateBlocked):
            sufficiency.require_sufficient(self.run_paths)

    def test_prompt_includes_round_number(self):
        prompt = sufficiency._compile_prompt(
            sample_narrative_candidate(), sample_osint(), [], 2
        )
        self.assertIn("第 2 轮", prompt)

    def test_runner_exception_wrapped(self):
        def exploding(prompt):
            raise RuntimeError("boom")

        result = sufficiency.run(
            self.run_paths, codex_runner=exploding, force=True
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("boom", result["reason"])

    def test_task_with_empty_query_rejected(self):
        payload = self.audit_payload("needs_research")
        payload["research_tasks"] = [
            {"gap_type": "单一来源", "query": "", "direction": "d"}
        ]
        result = sufficiency.run(
            self.run_paths, codex_runner=lambda p: payload, force=True
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("query", result["reason"])

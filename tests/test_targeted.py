"""Tests for 06 targeted research loop (bounded supplementary rounds)."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import narrative, paths, state, sufficiency, targeted, zhihu_lane


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


def needs_research_payload(tasks=None):
    return {
        "verdict": "needs_research",
        "claim_coverage": [],
        "evidence_gaps": ["缺真实使用反馈"],
        "research_tasks": tasks or [
            {"gap_type": "缺真实使用反馈", "query": "实测 GLM",
             "direction": "zhida"},
        ],
        "reason": "",
    }


class TargetedBase(unittest.TestCase):
    def setUp(self):
        self._zhihu_bin = mock.patch.object(
            zhihu_lane, "_binary", return_value=None
        )
        self._zhihu_bin.start()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-20")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)
        state.update_fields(
            self.run_paths, topic_choice="human", topic_title="选题", slug="s",
        )
        narrative.record_choice(
            self.run_paths, [sample_narrative_candidate()], 1
        )
        (self.run_paths.work_dir / "initial-osint.json").write_text(
            json.dumps(sample_osint(), ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self._zhihu_bin.stop()
        self._tmp.cleanup()


class TaskExecutionTests(TargetedBase):
    def test_tasks_fetch_discovered_urls_with_status(self):
        def fake_discover(topic, wait_ms):
            return [{"title": "t1", "url": "https://example.com/1"},
                    {"title": "t2", "url": "https://example.com/2"}]

        def fake_fetch(url, timeout):
            return f"<html>{url}</html>".encode("utf-8")

        entries = targeted._execute_tasks(
            self.run_paths,
            needs_research_payload()["research_tasks"],
            discover_runner=fake_discover,
            http_fetcher=fake_fetch,
            cdp_runner=None,
        )
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e["status"] == "fetched" for e in entries))
        self.assertTrue(all(e["gap_type"] == "缺真实使用反馈" for e in entries))

    def test_explicit_task_url_fetched_directly(self):
        tasks = [{"gap_type": "缺官方数据", "query": "",
                  "direction": "official", "url": "https://example.com/doc"}]

        def fake_fetch(url, timeout):
            return b"<html>doc</html>"

        entries = targeted._execute_tasks(
            self.run_paths, tasks,
            discover_runner=lambda t, w: [],
            http_fetcher=fake_fetch,
            cdp_runner=None,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["url"], "https://example.com/doc")

    def test_duplicate_urls_deduped(self):
        tasks = [
            {"gap_type": "单一来源", "query": "q1", "direction": "d"},
            {"gap_type": "单一来源", "query": "q2", "direction": "d"},
        ]

        def fake_discover(topic, wait_ms):
            return [{"title": "x", "url": "https://example.com/same"}]

        entries = targeted._execute_tasks(
            self.run_paths, tasks,
            discover_runner=fake_discover,
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
        )
        urls = [e["url"] for e in entries]
        self.assertEqual(len(urls), len(set(urls)))

    def test_community_gap_tasks_use_zhihu_lane(self):
        tasks = [{"gap_type": "缺真实使用反馈", "query": "实测 GLM",
                  "direction": "zhihu"}]

        def fake_zhihu(args):
            return {
                "Code": 0,
                "Message": "success",
                "Data": {
                    "Items": [{
                        "Title": "真实回答", "AuthorName": "某用户",
                        "ContentText": "实测翻车细节……",
                        "Url": "https://www.zhihu.com/question/1/answer/1",
                    }]
                },
            }

        entries = targeted._execute_tasks(
            self.run_paths, tasks,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            zhihu_runner=fake_zhihu,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_lane"], "zhihu-cli")
        self.assertEqual(entries[0]["url"],
                         "https://www.zhihu.com/question/1/answer/1")
        self.assertEqual(entries[0]["status"], "found")
        self.assertIn("实测翻车", entries[0]["excerpt"])

    def test_zhihu_lane_failure_does_not_block_other_tasks(self):
        tasks = [
            {"gap_type": "缺真实使用反馈", "query": "实测 GLM",
             "direction": "zhihu"},
            {"gap_type": "缺官方数据", "query": "", "direction": "official",
             "url": "https://example.com/doc"},
        ]

        def broken_zhihu(args):
            return {"Code": 401, "Message": "AUTH_REQUIRED"}

        entries = targeted._execute_tasks(
            self.run_paths, tasks,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            zhihu_runner=broken_zhihu,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["url"], "https://example.com/doc")


class LoopTests(TargetedBase):
    def _audit_sequence(self, verdicts):
        calls = {"n": 0}

        def audit_runner(prompt):
            verdict = verdicts[min(calls["n"], len(verdicts) - 1)]
            calls["n"] += 1
            if verdict == "sufficient":
                return {"verdict": "sufficient", "claim_coverage": [],
                        "evidence_gaps": [], "research_tasks": [], "reason": ""}
            return needs_research_payload()

        return audit_runner, calls

    def test_loop_stops_when_second_audit_is_sufficient(self):
        audit_runner, calls = self._audit_sequence(
            ["needs_research", "sufficient"]
        )
        result = targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [
                {"title": "x", "url": "https://example.com/1"}
            ],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            force=True,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verdict"], "sufficient")
        self.assertEqual(result["rounds"], 1)
        self.assertEqual(calls["n"], 2)

    def test_loop_caps_at_two_rounds_then_closes(self):
        audit_runner, calls = self._audit_sequence(["needs_research"])
        result = targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            force=True,
        )
        self.assertEqual(result["verdict"], "needs_research")
        self.assertEqual(result["rounds"], 2)
        self.assertEqual(calls["n"], 3)  # audit, round1 audit, round2 audit

    def test_evidence_package_merges_sources_with_fetch_status(self):
        audit_runner, _ = self._audit_sequence(["needs_research", "sufficient"])
        targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [
                {"title": "新证据", "url": "https://example.com/new"}
            ],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            force=True,
        )
        package = json.loads(
            (self.run_paths.work_dir / "evidence-package.json").read_text(
                encoding="utf-8"
            )
        )
        urls = [s["url"] for s in package["sources"]]
        self.assertIn("https://example.com/a", urls)
        self.assertIn("https://example.com/new", urls)
        self.assertTrue(all("status" in s for s in package["sources"]))

    def test_loop_blocked_without_narrative_choice(self):
        fresh = paths.RunPaths.for_date(self.root, "2026-08-21")
        fresh.ensure_work_dir()
        state.init_state(fresh)
        with self.assertRaises(narrative.NarrativeGateBlocked):
            targeted.run_loop(fresh, audit_runner=lambda p: {})

    def test_loop_resume_returns_stored_verdict_without_codex(self):
        audit_runner, calls = self._audit_sequence(
            ["needs_research", "sufficient"]
        )
        first = targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            force=True,
        )
        self.assertEqual(first["verdict"], "sufficient")
        calls_before = calls["n"]
        second = targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
        )
        self.assertEqual(second["status"], "resumed")
        self.assertEqual(second["verdict"], "sufficient")
        self.assertEqual(calls["n"], calls_before)

    def test_loop_regenerates_stale_package_from_other_narrative(self):
        # A stale package for a different narrative must never be reused.
        (self.run_paths.work_dir / "evidence-package.json").write_text(
            json.dumps({"narrative_title": "别的叙事", "audit_verdict": "sufficient"}),
            encoding="utf-8",
        )
        (self.run_paths.work_dir / "targeted-evidence.json").write_text(
            json.dumps({"rounds": []}), encoding="utf-8",
        )
        audit_runner, calls = self._audit_sequence(["sufficient"])
        result = targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
        )
        self.assertEqual(result["status"], "completed")
        package = json.loads(
            (self.run_paths.work_dir / "evidence-package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(package["narrative_title"], "账本篇")

    def test_loop_caps_urls_per_task(self):
        def fake_discover(topic, wait_ms):
            return [{"title": f"t{i}", "url": f"https://example.com/{i}"}
                    for i in range(6)]

        entries = targeted._execute_tasks(
            self.run_paths,
            needs_research_payload()["research_tasks"],
            discover_runner=fake_discover,
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
        )
        self.assertEqual(len(entries), 3)

    def test_mid_loop_unavailable_returns_unavailable(self):
        calls = {"n": 0}

        def audit_runner(prompt):
            calls["n"] += 1
            if calls["n"] == 1:
                return needs_research_payload()
            return {"status": "unavailable", "reason": "no output"}

        result = targeted.run_loop(
            self.run_paths,
            audit_runner=audit_runner,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x",
            cdp_runner=None,
            force=True,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["rounds"], 1)

    def test_unsupported_first_audit_closes_with_package(self):
        def audit_runner(prompt):
            return {
                "verdict": "unsupported", "claim_coverage": [],
                "evidence_gaps": [], "research_tasks": [],
                "reason": "核心论点缺一手证据",
            }

        result = targeted.run_loop(
            self.run_paths, audit_runner=audit_runner, force=True,
            discover_runner=lambda t, w: [],
            http_fetcher=lambda u, t: b"x", cdp_runner=None,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verdict"], "unsupported")
        self.assertEqual(result["rounds"], 0)
        self.assertTrue(
            (self.run_paths.work_dir / "evidence-package.json").exists()
        )

    def test_missing_osint_raises_targeted_error(self):
        fresh = paths.RunPaths.for_date(self.root, "2026-08-22")
        fresh.ensure_work_dir()
        state.init_state(fresh)
        state.update_fields(fresh, topic_choice="human", topic_title="t", slug="s")
        narrative.record_choice(
            fresh, [sample_narrative_candidate()], 1
        )
        with self.assertRaises(targeted.TargetedError):
            targeted.run_loop(fresh, audit_runner=lambda p: {})

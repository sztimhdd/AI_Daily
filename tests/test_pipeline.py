"""Tests for pipeline orchestration: gates, resume, failure semantics."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import aihot, pipeline, paths, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"
AIHOT_FIXTURE = FIXTURES / "aihot_items.json"
TOPIC_FIXTURE = FIXTURES / "topic_fixture.json"


class PipelineBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        state.init_state(self.rp)

    def tearDown(self):
        self._tmp.cleanup()


class CollectStageTests(PipelineBase):
    def test_fixture_collect_writes_evidence_and_transitions(self):
        result = pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[]
        )
        self.assertEqual(result["status"], "collected")
        items = json.loads(
            (self.rp.work_dir / "aihot-items.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(items), 3)
        self.assertTrue((self.rp.work_dir / "rss-items.json").is_file())
        st = state.read_state(self.rp)
        self.assertEqual(st["stage"], "topic_choice")
        self.assertEqual(st["counters"]["collect_runs"], 1)

    def test_aihot_live_failure_stops_candidates(self):
        def broken(url, timeout):
            raise OSError("aihot down")

        with self.assertRaises(pipeline.PipelineError):
            pipeline.run_collect(
                self.rp, mode="live", fetch=broken, rss_urls=[]
            )
        st = state.read_state(self.rp)
        self.assertEqual(st["status"], "failed")
        self.assertIn("aihot down", st["last_error"])
        self.assertFalse((self.rp.work_dir / "aihot-items.json").exists())

    def test_resume_does_not_recollect(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        before = (self.rp.work_dir / "aihot-items.json").stat().st_mtime_ns

        def must_not_be_called(url, timeout):
            raise AssertionError("collect must not fetch on resume")

        result = pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE,
            fetch=must_not_be_called, rss_urls=[],
        )
        self.assertEqual(result["status"], "resumed")
        self.assertEqual(
            (self.rp.work_dir / "aihot-items.json").stat().st_mtime_ns, before
        )
        st = state.read_state(self.rp)
        self.assertEqual(st["counters"]["collect_runs"], 1)

    def test_rss_failure_is_nonblocking(self):
        def rss_down(url, timeout):
            raise OSError("rss unreachable")

        result = pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE,
            rss_urls=["https://feeds.example.com/x", "https://feeds.example.com/y"],
            rss_fetch=rss_down,
        )
        self.assertEqual(result["status"], "collected")
        stats = json.loads(
            (self.rp.work_dir / "rss-stats.json").read_text(encoding="utf-8")
        )
        self.assertEqual(stats["feeds_failed"], 2)
        self.assertEqual(stats["items_kept"], 0)
        items = json.loads((self.rp.work_dir / "rss-items.json").read_text(encoding="utf-8"))
        self.assertEqual(items, [])
        st = state.read_state(self.rp)
        self.assertNotEqual(st["status"], "failed")

    def test_rss_stats_json_records_machine_readable_failure_details(self):
        good_feed = (FIXTURES / "feeds" / "source_a.xml").read_bytes()
        bad_xml = b"<rss><channel>"  # truncated: parse must fail, not raise

        def rss_flaky(url, timeout):
            if "good" in url:
                return good_feed
            if "badxml" in url:
                return bad_xml
            raise OSError("connection refused")

        result = pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE,
            rss_urls=[
                "https://feeds.example.com/good",
                "https://feeds.example.com/badxml",
                "https://feeds.example.com/down",
            ],
            rss_fetch=rss_flaky,
        )
        self.assertEqual(result["status"], "collected")
        stats = json.loads(
            (self.rp.work_dir / "rss-stats.json").read_text(encoding="utf-8")
        )
        self.assertIsInstance(stats.get("failures"), list)
        failed = {f["url"]: f["error"] for f in stats["failures"]}
        self.assertIn("https://feeds.example.com/badxml", failed)
        self.assertIn("https://feeds.example.com/down", failed)
        self.assertNotIn("https://feeds.example.com/good", failed)
        self.assertIn("parse failed", failed["https://feeds.example.com/badxml"])
        self.assertIn("fetch failed", failed["https://feeds.example.com/down"])
        # counts in the persisted stats must agree with the failure list
        self.assertEqual(len(stats["failures"]), stats["feeds_failed"])
        self.assertEqual(stats["feeds_requested"], stats["feeds_ok"] + stats["feeds_failed"])
        # rss-pool.md keeps the human-readable failure record alongside
        pool_md = (self.rp.work_dir / "rss-pool.md").read_text(encoding="utf-8")
        self.assertIn("https://feeds.example.com/down", pool_md)

    def test_empty_aihot_payload_is_honest_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = pathlib.Path(tmp) / "empty.json"
            empty.write_text(json.dumps({"items": []}), encoding="utf-8")
            with self.assertRaises(pipeline.PipelineError):
                pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=empty, rss_urls=[])


class StageGateTests(PipelineBase):
    def test_research_blocked_without_topic_choice(self):
        with self.assertRaises(topics.TopicGateBlocked):
            pipeline.run_research(self.rp)

    def test_outline_blocked_without_research(self):
        topics.choose_fixture(self.rp, TOPIC_FIXTURE)
        with self.assertRaises(pipeline.PipelineError):
            pipeline.run_outline(self.rp)

    def test_draft_blocked_without_outline(self):
        topics.choose_fixture(self.rp, TOPIC_FIXTURE)
        with self.assertRaises(pipeline.PipelineError):
            pipeline.run_draft(self.rp)

    def test_publish_blocked_without_assembly(self):
        from ai_daily import publish

        topics.choose_fixture(self.rp, TOPIC_FIXTURE)
        with self.assertRaises(publish.PublishError):
            pipeline.run_publish(self.rp, repo_dir=self.root / "repo")

    def test_candidates_generated_from_saved_evidence(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        cands = pipeline.run_candidates(self.rp)
        self.assertEqual(len(cands), 3)

    def test_human_choice_via_pipeline(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        topic = pipeline.run_human_choice(self.rp, choice=1, direction="测试方向")
        st = state.read_state(self.rp)
        self.assertEqual(st["topic_choice"], "human")
        self.assertEqual(st["slug"], topic["slug"])


class SimulatedChoiceStageTests(PipelineBase):
    def test_simulated_choice_passes_gate(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        topic = pipeline.run_simulated_choice(self.rp, choice=1)
        st = state.read_state(self.rp)
        self.assertEqual(st["topic_choice"], "simulated")
        self.assertEqual(st["stage"], "topic_choice")
        self.assertEqual(st["slug"], topic["slug"])
        self.assertEqual(st["topic_title"], topic["title"])
        # research gate accepts the simulated choice
        result = pipeline.run_research(self.rp)
        self.assertEqual(result["status"], "generated")

    def test_resume_after_simulated_choice_does_not_recollect(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        pipeline.run_simulated_choice(self.rp, choice=1)
        pipeline.run_research(self.rp)

        def must_not_be_called(url, timeout):
            raise AssertionError("collect must not fetch on resume")

        result = pipeline.run_collect(
            self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE,
            fetch=must_not_be_called, rss_urls=[],
        )
        self.assertEqual(result["status"], "resumed")
        st = state.read_state(self.rp)
        self.assertEqual(st["counters"]["collect_runs"], 1)
        self.assertEqual(st["topic_choice"], "simulated")

    def test_simulated_choice_out_of_range_fails_honestly(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        with self.assertRaises(topics.TopicError):
            pipeline.run_simulated_choice(self.rp, choice=4)


class RegenerateOutlineTests(PipelineBase):
    def collect_and_draft(self):
        pipeline.run_collect(self.rp, mode="fixture", aihot_fixture=AIHOT_FIXTURE, rss_urls=[])
        topics.choose_fixture(self.rp, TOPIC_FIXTURE)
        pipeline.run_research(self.rp)
        pipeline.run_outline(self.rp)
        pipeline.run_draft(self.rp)

    def test_outline_regenerate_rebuilds_draft_without_collect(self):
        self.collect_and_draft()
        article_before = (self.rp.work_dir / "article.md").read_text(encoding="utf-8")
        outline_path = self.rp.work_dir / "article-outline.md"
        outline_text = outline_path.read_text(encoding="utf-8")
        edited = outline_text.replace(
            "- 风险冷评：给读者的具体警告",
            "- 风险冷评：给读者的具体警告\n- 编辑追加章节：预算核对清单",
        )
        assert edited != outline_text
        outline_path.write_text(edited, encoding="utf-8")

        pipeline.regenerate_outline_from_edit(self.rp)

        article_after = (self.rp.work_dir / "article.md").read_text(encoding="utf-8")
        self.assertNotEqual(article_before, article_after)
        self.assertIn("编辑追加章节：预算核对清单", article_after)
        st = state.read_state(self.rp)
        self.assertEqual(st["counters"]["collect_runs"], 1, "edit must not re-collect")


if __name__ == "__main__":
    unittest.main()

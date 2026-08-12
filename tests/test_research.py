"""Tests for targeted research: questions, citations, uncertainty, resume."""

import json
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import aihot, paths, research, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
URL_RE = re.compile(r"\]\((https?://[^)]+)\)")


def fixture_aihot_items():
    payload = json.loads((FIXTURES / "aihot_items.json").read_text(encoding="utf-8"))
    return aihot._normalize(payload["items"])


class ResearchTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.paths.ensure_work_dir()
        state.init_state(self.paths)
        topics.choose_fixture(self.paths, FIXTURES / "topic_fixture.json")
        self.evidence_calls = 0

    def tearDown(self):
        self._tmp.cleanup()

    def write_evidence(self):
        (self.paths.work_dir / "aihot-items.json").write_text(
            json.dumps(fixture_aihot_items(), ensure_ascii=False, indent=1),
            encoding="utf-8",
        )

    def ensure_evidence(self):
        self.evidence_calls += 1
        self.write_evidence()


class GateTests(ResearchTestBase):
    def test_research_blocked_without_topic_choice(self):
        fresh = paths.RunPaths.for_date(self.root, "2026-08-13")
        fresh.ensure_work_dir()
        state.init_state(fresh)
        with self.assertRaises(topics.TopicGateBlocked):
            research.run(fresh)


class GenerationTests(ResearchTestBase):
    def test_research_without_evidence_or_collector_fails_honestly(self):
        with self.assertRaises(research.ResearchError):
            research.run(self.paths)

    def test_research_organizes_around_topic_key_questions(self):
        result = research.run(self.paths, ensure_evidence=self.ensure_evidence)
        md = (self.paths.work_dir / "research.md").read_text(encoding="utf-8")
        self.assertIn("## 关键问题", md)
        topic = json.loads((FIXTURES / "topic_fixture.json").read_text(encoding="utf-8"))
        for q in topic["research_queries"]:
            self.assertIn(q, md)
        self.assertEqual(result["status"], "generated")

    def test_supported_questions_carry_linked_evidence(self):
        research.run(self.paths, ensure_evidence=self.ensure_evidence)
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        supported = [q for q in data["questions"] if q["status"] == "supported"]
        self.assertTrue(supported, "expected at least one supported question")
        for q in supported:
            for ev in q["evidence"]:
                self.assertTrue(ev["url"].startswith("http"))
                self.assertTrue(ev["title"])

    def test_unsupported_questions_marked_insufficient_not_fabricated(self):
        research.run(self.paths, ensure_evidence=self.ensure_evidence)
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        insufficient = [q for q in data["questions"] if q["status"] == "insufficient"]
        self.assertTrue(insufficient, "expected at least one insufficient question")
        for q in insufficient:
            self.assertEqual(q["evidence"], [])
        md = (self.paths.work_dir / "research.md").read_text(encoding="utf-8")
        self.assertIn("## 证据不足", md)

    def test_no_url_outside_the_evidence_pool(self):
        research.run(self.paths, ensure_evidence=self.ensure_evidence)
        md = (self.paths.work_dir / "research.md").read_text(encoding="utf-8")
        cited = set(URL_RE.findall(md))
        evidence_urls = {it["links"]["original"] or it["links"]["aihot"]
                         for it in fixture_aihot_items()}
        self.assertTrue(cited, "research.md should cite sources")
        self.assertTrue(cited <= evidence_urls,
                        f"fabricated urls: {cited - evidence_urls}")

    def test_multi_source_events_noted_for_cross_validation(self):
        items = fixture_aihot_items()
        self.write_evidence()
        dup = {
            "title": items[0]["title"],
            "url": "https://elsewhere.example.com/same-story",
            "published": "",
            "summary": items[0]["summary"],
            "feed": "https://feeds.example.com/x",
            "origin": "rss",
        }
        (self.paths.work_dir / "rss-items.json").write_text(
            json.dumps([dup], ensure_ascii=False), encoding="utf-8"
        )
        research.run(self.paths, ensure_evidence=self.ensure_evidence)
        md = (self.paths.work_dir / "research.md").read_text(encoding="utf-8")
        self.assertIn("## 冲突与交叉验证", md)
        self.assertIn("https://elsewhere.example.com/same-story", md)


class ResumeTests(ResearchTestBase):
    def test_resume_skips_collect_and_preserves_artifacts(self):
        first = research.run(self.paths, ensure_evidence=self.ensure_evidence)
        md_before = (self.paths.work_dir / "research.md").read_bytes()
        self.assertEqual(state.read_state(self.paths)["counters"]["collect_runs"], 1)

        second = research.run(self.paths, ensure_evidence=self.ensure_evidence)
        self.assertEqual(second["status"], "resumed")
        self.assertEqual(self.evidence_calls, 1, "resume must not re-collect")
        self.assertEqual(state.read_state(self.paths)["counters"]["collect_runs"], 1)
        self.assertEqual(
            (self.paths.work_dir / "research.md").read_bytes(), md_before
        )

    def test_failed_research_continues_from_existing_evidence(self):
        # simulate: collect happened, research crashed, rerun without collector
        self.write_evidence()
        state.bump_counter(self.paths, "collect_runs")
        result = research.run(self.paths)  # no ensure_evidence available
        self.assertEqual(result["status"], "generated")
        self.assertEqual(state.read_state(self.paths)["counters"]["collect_runs"], 1)

    def test_force_regeneration_does_not_recollect(self):
        research.run(self.paths, ensure_evidence=self.ensure_evidence)
        result = research.run(
            self.paths, ensure_evidence=self.ensure_evidence, force=True
        )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(self.evidence_calls, 1)
        self.assertEqual(state.read_state(self.paths)["counters"]["collect_runs"], 1)

    def test_research_artifact_recorded_in_state(self):
        research.run(self.paths, ensure_evidence=self.ensure_evidence)
        st = state.read_state(self.paths)
        self.assertIn("research", st["artifacts"])




class EmptyEvidencePoolStateTests(ResearchTestBase):
    """An empty/unusable evidence pool must fail durably at research."""

    def test_refusal_without_pool_records_research_failure_in_state(self):
        with self.assertRaises(research.ResearchError):
            research.run(self.paths)  # no evidence, no collector injected
        st = state.read_state(self.paths)
        self.assertEqual(st["status"], "failed")
        self.assertTrue(st["last_error"].startswith("research: no evidence pool"))
        self.assertTrue(
            any("FAILED at research" in entry for entry in st["stage_log"]),
            st["stage_log"],
        )

    def test_pool_failure_recovers_once_evidence_exists(self):
        with self.assertRaises(research.ResearchError):
            research.run(self.paths)
        self.write_evidence()
        result = research.run(self.paths)
        self.assertEqual(result["status"], "generated")
        st = state.read_state(self.paths)
        self.assertEqual(st["last_error"], "")
        self.assertNotEqual(st["status"], "failed")


class ResumeAfterFailureTests(ResearchTestBase):
    def test_failed_collection_records_error_then_recovers(self):
        calls = {"n": 0}

        def broken():
            calls["n"] += 1
            raise OSError("feed server down")

        with self.assertRaises(research.ResearchError):
            research.run(self.paths, ensure_evidence=broken)
        st = state.read_state(self.paths)
        self.assertEqual(st["status"], "failed")
        self.assertIn("feed server down", st["last_error"])
        self.assertEqual(st["counters"].get("collect_runs", 0), 0)

        result = research.run(self.paths, ensure_evidence=self.ensure_evidence)
        self.assertEqual(result["status"], "generated")
        st = state.read_state(self.paths)
        self.assertEqual(st["last_error"], "")
        self.assertNotEqual(st["status"], "failed")
        self.assertEqual(st["counters"]["collect_runs"], 1)
        self.assertEqual(calls["n"], 1, "failed attempt must not count as collected")


if __name__ == "__main__":
    unittest.main()

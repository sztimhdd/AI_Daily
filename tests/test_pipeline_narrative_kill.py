"""run_narrative returns to topic selection when a weak topic is killed."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import paths, pipeline, state, topics


def _make_osint(sources, gaps=None):
    return {
        "analysis_status": "completed",
        "modules": [],
        "evidence_gaps": gaps or [],
        "sources": sources,
    }


class PipelineNarrativeKillTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        state.init_state(self.rp)
        # A chosen topic is required before narrative can run.
        selected = {
            "title": "某模型跑分", "slug": "benchmark-topic",
            "summary": "一个没有方法学 benchmark 的话题",
        }
        topics._write_selected(self.rp, selected)
        state.update_fields(
            self.rp,
            topic_choice="human",
            topic_title="某模型跑分",
            slug="benchmark-topic",
            status="in_progress",
            stage="research",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _write_osint(self, osint):
        (self.rp.work_dir / "initial-osint.json").write_text(
            json.dumps(osint, ensure_ascii=False), encoding="utf-8"
        )

    def test_killed_topic_returns_to_topic_stage_not_failed(self):
        # A benchmark-titled topic with no method keywords and no engineering
        # module triggers narrative._kill_reason -> "narrative killed".
        self._write_osint(
            _make_osint(
                [
                    {
                        "url": "https://example.com/benchmark",
                        "status": "fetched",
                        "title": "跑分对比",
                        "excerpt": "只有跑分图，没有方法学",
                    }
                ],
                gaps=["benchmark"],
            )
        )
        result = pipeline.run_narrative(self.rp)
        self.assertEqual(result.get("status"), "retry_topic")
        st = state.read_state(self.rp)
        self.assertNotEqual(st["status"], "failed")
        self.assertEqual(st["status"], "in_progress")
        # The previous weak topic is cleared so Telegram re-offers candidates.
        self.assertEqual(st["topic_choice"], "")
        self.assertEqual(st["topic_title"], "")
        self.assertEqual(st["slug"], "")
        self.assertIn("topic", st["last_error"] or "")

    def test_non_kill_error_still_fails(self):
        # A missing osint file is a genuine fatal error, not a weak topic.
        with self.assertRaises(Exception):
            pipeline.run_narrative(self.rp)
        st = state.read_state(self.rp)
        self.assertEqual(st["status"], "failed")


if __name__ == "__main__":
    unittest.main()

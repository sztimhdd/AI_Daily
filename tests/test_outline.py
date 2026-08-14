"""Tests for the editable article outline (8 required fields)."""

import json
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import outline, paths, research, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

REQUIRED_SECTIONS = [
    "## 工作标题",
    "## 目标读者",
    "## 核心论点",
    "## 矛盾",
    "## 章节结构",
    "## 关键事实",
    "## 事实边界",
    "## 不应声称",
]


def make_run(root):
    run_paths = paths.RunPaths.for_date(root, "2026-08-12")
    run_paths.ensure_work_dir()
    state.init_state(run_paths)
    topics.choose_fixture(run_paths, FIXTURES / "topic_fixture.json")
    payload = json.loads((FIXTURES / "aihot_items.json").read_text(encoding="utf-8"))
    from ai_daily import aihot

    (run_paths.work_dir / "aihot-items.json").write_text(
        json.dumps(aihot._normalize(payload["items"]), ensure_ascii=False),
        encoding="utf-8",
    )
    research.run(run_paths)
    return run_paths


class OutlineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_blocked_without_topic_choice(self):
        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        with self.assertRaises(topics.TopicGateBlocked):
            outline.run(run_paths)

    def test_blocked_without_research(self):
        run_paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        run_paths.ensure_work_dir()
        state.init_state(run_paths)
        topics.choose_fixture(run_paths, FIXTURES / "topic_fixture.json")
        with self.assertRaises(outline.OutlineError):
            outline.run(run_paths)

    def test_outline_contains_all_eight_required_fields_nonempty(self):
        run_paths = make_run(self.root)
        outline.run(run_paths)
        text = (run_paths.work_dir / "article-outline.md").read_text(encoding="utf-8")
        for header in REQUIRED_SECTIONS:
            self.assertIn(header, text)
            body = re.search(
                re.escape(header) + r"\n(.*?)(?=\n## |\Z)", text, re.S
            ).group(1)
            self.assertTrue(body.strip(), f"empty section: {header}")

    def test_section_structure_has_peg_sections_and_body(self):
        run_paths = make_run(self.root)
        outline.run(run_paths)
        text = (run_paths.work_dir / "article-outline.md").read_text(encoding="utf-8")
        bullets = re.findall(r"^[-*] (.+)$", text.split("## 章节结构")[1].split("\n## ")[0], re.M)
        self.assertGreaterEqual(len(bullets), 3)
        self.assertIn("导语", bullets[0])
        self.assertTrue(any("风险" in b for b in bullets[-1:]), bullets[-1])

    def test_key_facts_carry_research_links(self):
        run_paths = make_run(self.root)
        outline.run(run_paths)
        text = (run_paths.work_dir / "article-outline.md").read_text(encoding="utf-8")
        data = json.loads(
            (run_paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        supported_urls = {
            ev["url"]
            for q in data["questions"]
            if q["status"] == "supported"
            for ev in q["evidence"]
        }
        cited = set(re.findall(r"\]\((https?://[^)]+)\)", text))
        self.assertTrue(cited & supported_urls)

    def test_must_not_claim_covers_insufficient_questions(self):
        run_paths = make_run(self.root)
        outline.run(run_paths)
        text = (run_paths.work_dir / "article-outline.md").read_text(encoding="utf-8")
        data = json.loads(
            (run_paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        insufficient = [
            q["query"] for q in data["questions"] if q["status"] == "insufficient"
        ]
        self.assertTrue(insufficient)
        for query in insufficient:
            self.assertIn(query, text.split("## 不应声称")[1])

    def test_outline_regeneration_is_deterministic(self):
        run_paths = make_run(self.root)
        outline.run(run_paths)
        first = (run_paths.work_dir / "article-outline.md").read_bytes()
        outline.run(run_paths, force=True)
        self.assertEqual(
            (run_paths.work_dir / "article-outline.md").read_bytes(), first
        )

    def test_resume_returns_existing_outline_without_force(self):
        run_paths = make_run(self.root)
        outline.run(run_paths)
        result = outline.run(run_paths)
        self.assertEqual(result["status"], "resumed")


if __name__ == "__main__":
    unittest.main()

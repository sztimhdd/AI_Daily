"""Tests for fact-backed drafting, author style, and outline sensitivity."""

import json
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import aihot, deslop, draft, outline, paths, research, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
URL_RE = re.compile(r"\]\((https?://[^)]+)\)")


def fixture_items():
    payload = json.loads((FIXTURES / "aihot_items.json").read_text(encoding="utf-8"))
    return aihot._normalize(payload["items"])


def build_run(root, date="2026-08-12"):
    """Full chain through outline; collect happens once via the stub."""
    run_paths = paths.RunPaths.for_date(root, date)
    run_paths.ensure_work_dir()
    state.init_state(run_paths)
    topics.choose_fixture(run_paths, FIXTURES / "topic_fixture.json")

    calls = {"collect": 0}

    def ensure_evidence():
        calls["collect"] += 1
        (run_paths.work_dir / "aihot-items.json").write_text(
            json.dumps(fixture_items(), ensure_ascii=False), encoding="utf-8"
        )

    research.run(run_paths, ensure_evidence=ensure_evidence)
    outline.run(run_paths)
    return run_paths, calls


def paragraphs(text):
    return [p for p in text.split("\n\n") if p.strip()]


class DraftTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths, self.calls = build_run(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def article_text(self):
        return (self.paths.work_dir / "article.md").read_text(encoding="utf-8")

    def test_blocked_without_outline(self):
        fresh = paths.RunPaths.for_date(self.root, "2026-08-14")
        fresh.ensure_work_dir()
        state.init_state(fresh)
        topics.choose_fixture(fresh, FIXTURES / "topic_fixture.json")
        with self.assertRaises(draft.DraftError):
            draft.run(fresh)

    def test_h1_matches_outline_working_title(self):
        draft.run(self.paths)
        article = self.article_text()
        outline_text = (self.paths.work_dir / "article-outline.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue(article.startswith("# "))
        self.assertEqual(
            article.splitlines()[0][2:].strip(), outline.working_title(outline_text)
        )

    def test_every_outline_section_becomes_a_draft_heading_in_order(self):
        draft.run(self.paths)
        article = self.article_text()
        outline_text = (self.paths.work_dir / "article-outline.md").read_text(
            encoding="utf-8"
        )
        headings = re.findall(r"^## (.+)$", article, re.M)
        self.assertEqual(headings, outline.section_bullets(outline_text))

    def test_paragraphs_are_short_for_mobile_reading(self):
        draft.run(self.paths)
        for para in paragraphs(self.article_text()):
            if para.startswith("#"):
                continue
            self.assertLessEqual(len(para), 240, para)
            sentences = re.split(r"[。！？!?]", para)
            self.assertLessEqual(len([s for s in sentences if s.strip()]), 4, para)

    def test_source_links_preserved_from_research(self):
        draft.run(self.paths)
        article = self.article_text()
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        article_urls = set(URL_RE.findall(article))
        for q in data["questions"]:
            if q["status"] != "supported":
                continue
            ev_urls = {ev["url"] for ev in q["evidence"]}
            self.assertTrue(
                ev_urls & article_urls, f"no link kept for question {q['query']}"
            )
        evidence_pool = set(data["evidence_urls"])
        self.assertTrue(article_urls <= evidence_pool,
                        f"urls outside pool: {article_urls - evidence_pool}")

    def test_uncertainty_is_stated_not_hidden(self):
        draft.run(self.paths)
        article = self.article_text()
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        has_insufficient = any(
            q["status"] == "insufficient" for q in data["questions"]
        )
        if has_insufficient:
            self.assertIn("缺少公开口径", article)

    def test_article_passes_remove_ai_slop_contract(self):
        draft.run(self.paths)
        findings = deslop.check_text(self.article_text())
        self.assertEqual(findings, [], deslop.report(findings))

    def test_style_markers_present(self):
        draft.run(self.paths)
        article = self.article_text()
        self.assertRegex(article, r"\*\*.+?\*\*", "missing bolded lead-ins")
        self.assertNotIn("总结：", article)
        self.assertNotIn("[编辑注]", article)

    def test_draft_regeneration_is_deterministic(self):
        draft.run(self.paths)
        first = (self.paths.work_dir / "article.md").read_bytes()
        draft.run(self.paths, force=True)
        self.assertEqual((self.paths.work_dir / "article.md").read_bytes(), first)

    def test_resume_without_force(self):
        draft.run(self.paths)
        result = draft.run(self.paths)
        self.assertEqual(result["status"], "resumed")


class OutlineEditRegressionTests(unittest.TestCase):
    """Editing the outline changes the draft WITHOUT re-running collect."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths, self.calls = build_run(self.root)
        draft.run(self.paths)

    def tearDown(self):
        self._tmp.cleanup()

    def edit_outline(self):
        path = self.paths.work_dir / "article-outline.md"
        text = path.read_text(encoding="utf-8")
        old_thesis = outline.thesis(text)
        new_thesis = "搜索预算是智能体时代的第一张隐性账单，谁先记账谁先活。"
        text = text.replace(old_thesis, new_thesis, 1)
        bullets = outline.section_bullets(text)
        body_bullet = next(b for b in bullets if b.startswith("拆解"))
        text = text.replace(f"- {body_bullet}", "- 拆解 1·检索账单解剖：钱到底花在哪了", 1)
        path.write_text(text, encoding="utf-8")
        return new_thesis, body_bullet

    def test_outline_edit_changes_draft_without_collect(self):
        before = (self.paths.work_dir / "article.md").read_text(encoding="utf-8")
        collect_before = state.read_state(self.paths)["counters"].get("collect_runs", 0)
        new_thesis, old_bullet = self.edit_outline()

        result = draft.run(self.paths, force=True)
        self.assertEqual(result["status"], "generated")

        article = (self.paths.work_dir / "article.md").read_text(encoding="utf-8")
        self.assertNotEqual(article, before, "draft must change after outline edit")
        self.assertIn(new_thesis, article)
        self.assertIn("## 拆解 1·检索账单解剖：钱到底花在哪了", article)
        self.assertNotIn(f"## {old_bullet}", article)
        self.assertNotIn(old_bullet, article)

        # collection and research are untouched
        self.assertEqual(self.calls["collect"], 1)
        st = state.read_state(self.paths)
        self.assertEqual(st["counters"].get("collect_runs", 0), collect_before)

        # edited draft still satisfies the slop contract
        self.assertEqual(deslop.check_text(article), [])

    def test_edited_draft_keeps_source_links(self):
        self.edit_outline()
        draft.run(self.paths, force=True)
        article = (self.paths.work_dir / "article.md").read_text(encoding="utf-8")
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        supported_urls = {
            ev["url"]
            for q in data["questions"]
            if q["status"] == "supported"
            for ev in q["evidence"]
        }
        self.assertTrue(set(URL_RE.findall(article)) & supported_urls)


DIRTY_EXCERPT_HTML = (
    '<p><strong><a href="https://dirty.example.com/muse-glimmer">'
    "Deep research pricing report</a></strong></p>\n"
    "Deep research agents now price every search call separately! "
    "The pricing page lists 25 search calls per task and budgets keep gro"
)
DIRTY_EXCERPT_LONG = (
    "Meta 超级智能实验室的首个开放权重模型已在 OpenRouter 上线并开放按量计费与免费额度"
)
_RESIDUE_HTML_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*[\s>/]|<[a-zA-Z/][^<>\n]*$")


class ShortClauseResidueTests(unittest.TestCase):
    """_short must never emit raw HTML or ellipsis-truncated fragments."""

    def test_short_keeps_first_sentence_whole_beyond_limit(self):
        text = (
            "Deep research agents now price every search call separately. "
            "Budgets keep growing"
        )
        out = draft._short(text, 16)
        self.assertNotIn("…", out)
        self.assertEqual(
            out, "Deep research agents now price every search call separately"
        )

    def test_short_cuts_at_first_clause_separator(self):
        text = "搜索预算成了最贵的开销，个人创作者开始记账。"
        self.assertEqual(draft._short(text, 48), "搜索预算成了最贵的开销")

    def test_short_strips_html_and_drops_truncated_url_tag(self):
        self.assertEqual(draft._short('<p><strong><a href="https://rese', 48), "")

    def test_short_falls_back_to_title_when_excerpt_unusable(self):
        out = draft._short(
            '<p><strong><a href="https://rese', 48, fallback="Muse Glimmer 发布"
        )
        self.assertEqual(out, "Muse Glimmer 发布")

    def test_short_unescapes_entities_and_never_ellipsis(self):
        out = draft._short("Meta&#8217;s model ships today. Pricing pages follow", 16)
        self.assertEqual(out, "Meta's model ships today")
        self.assertNotIn("…", out)


class DirtyResearchDraftTests(unittest.TestCase):
    """Drafting over residue-laden research.json still emits clean prose."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths, self.calls = build_run(self.root)
        self._inject_dirty_research()

    def tearDown(self):
        self._tmp.cleanup()

    def _inject_dirty_research(self):
        path = self.paths.work_dir / "research.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        dirty = {
            "title": "Introducing Muse Glimmer",
            "url": "https://dirty.example.com/muse-glimmer",
            "origin": "rss",
            "excerpt": DIRTY_EXCERPT_HTML,
        }
        long_ev = {
            "title": "Muse Glimmer 上线 OpenRouter",
            "url": "https://dirty.example.com/openrouter",
            "origin": "rss",
            "excerpt": DIRTY_EXCERPT_LONG,
        }
        for q in data["questions"]:
            if q["status"] == "supported":
                q["evidence"] = [dirty, long_ev]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    def article_text(self):
        draft.run(self.paths, force=True)
        return (self.paths.work_dir / "article.md").read_text(encoding="utf-8")

    def test_draft_contains_no_raw_html(self):
        article = self.article_text()
        self.assertIsNone(_RESIDUE_HTML_RE.search(article), article)

    def test_draft_contains_no_ellipsis_truncation(self):
        article = self.article_text()
        self.assertNotIn("…", article)
        self.assertNotIn("...", article)

    def test_dirty_draft_still_passes_slop_contract(self):
        self.assertEqual(deslop.check_text(self.article_text()), [])

    def test_dirty_draft_keeps_source_links(self):
        urls = set(URL_RE.findall(self.article_text()))
        self.assertIn("https://dirty.example.com/muse-glimmer", urls)
        self.assertIn("https://dirty.example.com/openrouter", urls)


if __name__ == "__main__":
    unittest.main()

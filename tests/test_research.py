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



class EvidenceTextNormalizationTests(unittest.TestCase):
    """Evidence normalization: HTML and truncated fragments never survive."""

    def test_html_tags_stripped_and_entities_unescaped(self):
        raw = '<p>Meta&#8217;s model <a href="https://x.example.com/a">ships</a> today</p>'
        self.assertEqual(
            research.normalize_evidence_text(raw), "Meta's model ships today"
        )

    def test_block_tags_become_line_breaks(self):
        raw = "<p>First line</p><p>Second line</p>"
        self.assertEqual(
            research.normalize_evidence_text(raw), "First line\nSecond line"
        )

    def test_truncated_unclosed_tag_is_removed(self):
        raw = 'Agent pricing notes <a href="https://rese'
        self.assertEqual(research.normalize_evidence_text(raw), "Agent pricing notes")

    def test_first_complete_sentence_kept_with_terminator(self):
        raw = "Budgets shrank fast. Costs kept growing"
        self.assertEqual(
            research.evidence_excerpt(raw, "fallback"), "Budgets shrank fast."
        )

    def test_ellipsis_fragment_is_dropped_not_repeated(self):
        raw = "Search costs are exploding… full numbers coming soon."
        self.assertEqual(
            research.evidence_excerpt(raw, "fallback"), "full numbers coming soon."
        )

    def test_truncated_tail_without_terminator_is_dropped(self):
        raw = (
            "Deep research agents now price every search call separately! "
            "The pricing page lists 25 calls per task and budgets keep gro"
        )
        self.assertEqual(
            research.evidence_excerpt(raw, "fallback"),
            "Deep research agents now price every search call separately!",
        )

    def test_no_complete_sentence_falls_back_to_title(self):
        raw = "个人创作者的 AI 研究成本核算还没有公开口径，所有数字都来自零散的社区统"
        self.assertEqual(
            research.evidence_excerpt(raw, "Personal research cost notes"),
            "Personal research cost notes",
        )

    def test_decimal_dots_do_not_end_sentences(self):
        raw = "Costs rose 2.5x and budgets shrank."
        self.assertEqual(
            research.evidence_excerpt(raw, "fallback"),
            "Costs rose 2.5x and budgets shrank.",
        )


class EvidenceExcerptBoundaryTests(unittest.TestCase):
    """Fetched-page excerpts must end at a sentence boundary, never mid-phrase."""

    def _long_markdown(self):
        sentence = (
            "OpenRouter's blog promises that routing stays driven by what "
            "pricing customers actually choose. "
        )
        return sentence * 12  # far beyond the 300-char limit

    def test_excerpt_ends_at_sentence_boundary_not_mid_phrase(self):
        text = self._long_markdown()
        excerpt = research._evidence_excerpt(text, "fallback")
        self.assertTrue(
            excerpt.rstrip().endswith((".", "!", "?")),
            f"excerpt ends mid-sentence: {excerpt[-60:]!r}",
        )
        self.assertNotIn("what\n", excerpt[-40:])

    def test_excerpt_never_cuts_a_quote_phrase(self):
        # Regression: the published draft quoted "stays driven by what" —
        # a mid-phrase cut must be impossible now.
        text = self._long_markdown()
        excerpt = research._evidence_excerpt(text, "fallback")
        last_word = excerpt.rstrip().rstrip(".!?").split()[-1].lower()
        self.assertNotEqual(last_word, "what")

    def test_truncated_flag_true_when_source_continues(self):
        text, flag = research._excerpt_with_flag(self._long_markdown(), "fallback")
        self.assertTrue(flag)
        self.assertTrue(text)

    def test_truncated_flag_false_for_short_source(self):
        text, flag = research._excerpt_with_flag("One short sentence.", "fallback")
        self.assertFalse(flag)
        self.assertEqual(text, "One short sentence.")


DIRTY_RSS_ITEMS = [
    {
        "title": "Deep research agent search budget pricing",
        "url": "https://dirty.example.com/deep-research-pricing",
        "date_raw": "2026-08-12",
        "summary": (
            '<p><strong><a href="https://dirty.example.com/deep-research-pricing">'
            "Deep research agent search budget pricing</a></strong></p>\n"
            "Deep research agents now price every search call separately! "
            "The pricing page lists 25 search calls per task and budgets keep gro"
        ),
        "feed": "https://feeds.example.com/dirty",
        "origin": "rss",
    },
    {
        "title": "Search budget benchmarks for solo builders",
        "url": "https://dirty.example.com/search-budget-benchmarks",
        "date_raw": "2026-08-12",
        "summary": (
            "Search budget benchmarks are exploding… full numbers coming soon."
        ),
        "feed": "https://feeds.example.com/dirty",
        "origin": "rss",
    },
    {
        "title": "Personal research cost notes",
        "url": "https://dirty.example.com/personal-research-cost",
        "date_raw": "2026-08-12",
        "summary": "个人创作者的 AI 研究成本核算还没有公开口径，所有数字都来自零散的社区统",
        "feed": "https://feeds.example.com/dirty",
        "origin": "rss",
    },
]

_RESIDUE_HTML_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*[\s>/]")


class DirtyEvidenceRunTests(ResearchTestBase):
    """Research over HTML-littered, truncated summaries stays clean prose."""

    def write_dirty_rss(self):
        (self.paths.work_dir / "rss-items.json").write_text(
            json.dumps(DIRTY_RSS_ITEMS, ensure_ascii=False), encoding="utf-8"
        )

    def test_research_md_contains_no_raw_html_or_ellipsis(self):
        self.write_dirty_rss()
        research.run(self.paths)
        md = (self.paths.work_dir / "research.md").read_text(encoding="utf-8")
        self.assertIsNone(_RESIDUE_HTML_RE.search(md), md)
        self.assertNotIn("…", md)
        self.assertNotIn("...", md)

    def test_research_json_excerpts_are_clean_prose(self):
        self.write_dirty_rss()
        research.run(self.paths)
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        excerpts = [
            ev["excerpt"]
            for q in data["questions"]
            for ev in q["evidence"]
        ]
        self.assertTrue(excerpts)
        for excerpt in excerpts:
            self.assertIsNone(_RESIDUE_HTML_RE.search(excerpt), excerpt)
            self.assertNotIn("…", excerpt)
            self.assertNotIn("...", excerpt)

    def test_html_summary_excerpt_keeps_anchor_text_not_markup(self):
        self.write_dirty_rss()
        research.run(self.paths)
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        q2 = next(
            q for q in data["questions"]
            if q["query"] == "deep research agent search budget pricing"
        )
        lead = q2["evidence"][0]
        self.assertEqual(
            lead["excerpt"],
            "Deep research agents now price every search call separately!",
        )

    def test_truncated_summary_without_sentence_falls_back_to_title(self):
        self.write_dirty_rss()
        research.run(self.paths)
        data = json.loads(
            (self.paths.work_dir / "research.json").read_text(encoding="utf-8")
        )
        q3 = next(q for q in data["questions"] if q["query"] == "个人创作者 AI 研究成本")
        excerpts = {ev["excerpt"] for ev in q3["evidence"]}
        self.assertIn("Personal research cost notes", excerpts)

    def test_full_source_links_survive_normalization(self):
        self.write_dirty_rss()
        research.run(self.paths)
        md = (self.paths.work_dir / "research.md").read_text(encoding="utf-8")
        cited = set(URL_RE.findall(md))
        dirty_urls = {it["url"] for it in DIRTY_RSS_ITEMS}
        self.assertTrue(dirty_urls <= cited, f"missing links: {dirty_urls - cited}")

    def test_dirty_evidence_does_not_bump_collect(self):
        self.write_dirty_rss()
        research.run(self.paths)
        self.assertEqual(
            state.read_state(self.paths)["counters"].get("collect_runs", 0), 0
        )


class TopicEventPriorityTests(unittest.TestCase):
    """The topic's own event must outrank lexically-related siblings.

    A sibling story that merely mentions the topic's named entity (for
    example another product launching on the same platform) must never
    become the article's lead: the topic's own event is the hardest
    fact, even when lexical ties and the per-question evidence cap would
    otherwise push it out of the question entirely.
    """

    TOPIC_TITLE = "OpenRouter 推出实时网页搜索基准测试"
    TOPIC_URL = "https://openrouter.ai/blog/announcements/web-search-benchmark"
    SIBLING_URL = "https://offtopic.example.com/deepseek-v4-pro"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths = paths.RunPaths.for_date(self.root, "2026-08-13")
        self.paths.ensure_work_dir()
        state.init_state(self.paths)

    def tearDown(self):
        self._tmp.cleanup()

    def rss_item(self, title, summary, url):
        return {
            "title": title,
            "summary": summary,
            "url": url,
            "origin": "rss",
            "feed": "https://feeds.example.com/x",
            "published": "",
            "score": 5,
        }

    def write_pool(self):
        # Three sibling stories merely mention OpenRouter mid-sentence;
        # together with title-ascending tie-breaks they outrank the
        # topic's own announcement, which the evidence cap then drops.
        pool = [
            self.rss_item(
                "DeepSeek Ships V4 Pro as Its Flagship Model Leaves Preview",
                "DeepSeek has released the production version of its "
                "flagship model on OpenRouter, the company said.",
                self.SIBLING_URL,
            ),
            self.rss_item(
                "DeepSeek V4 Pro 0813 (on OpenRouter)",
                "Simon reviews the new DeepSeek release hosted on "
                "OpenRouter with benchmarks and pricing.",
                "https://simonwillison.example.com/deepseek-v4-pro",
            ),
            self.rss_item(
                "Meta 开源 Muse Glimmer 登陆 OpenRouter",
                "Meta 的开源模型 Muse Glimmer 现已上线 OpenRouter 平台。",
                "https://x.example.com/openrouter-muse-glimmer",
            ),
            self.rss_item(
                self.TOPIC_TITLE,
                "OpenRouter 发布实时网页搜索基准测试排行榜，系统评测搜索引擎。",
                self.TOPIC_URL,
            ),
        ]
        (self.paths.work_dir / "rss-items.json").write_text(
            json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    def choose(self):
        cand = {
            "title": self.TOPIC_TITLE,
            "slug": "openrouter-web-search-benchmark",
            "thesis": "OpenRouter 发布实时排行榜。",
            "hook": "hook",
            "evidence_gaps": ["目前只有 1 个来源报道，缺少独立的第二来源验证。"],
            "research_queries": ["openrouter", self.TOPIC_TITLE],
            "strategic_relevance": "影响模型选型。",
            "sources": [
                {"url": self.TOPIC_URL, "title": self.TOPIC_TITLE, "origin": "rss"}
            ],
        }
        topics.record_human_choice(self.paths, [cand], choice=1)

    def test_topics_own_event_ranks_first_in_matching_questions(self):
        self.write_pool()
        self.choose()
        result = research.run(self.paths)
        first = result["questions"][0]
        self.assertEqual(first["status"], "supported")
        self.assertEqual(first["evidence"][0]["url"], self.TOPIC_URL)

    def test_draft_lead_cites_topics_own_event_not_sibling_story(self):
        from ai_daily import draft, outline

        self.write_pool()
        self.choose()
        research.run(self.paths)
        outline.run(self.paths)
        draft.run(self.paths)
        marker = chr(10) + "## "
        article = (self.paths.work_dir / "article.md").read_text(encoding="utf-8")
        sections = article.split(marker)
        lead = next(s for s in sections if s.startswith("导语"))
        self.assertIn(self.TOPIC_URL, lead)
        self.assertNotIn(self.SIBLING_URL, lead)


if __name__ == "__main__":
    unittest.main()

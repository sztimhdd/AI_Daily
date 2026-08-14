"""Tests for the pure-text TUI layer (rendering + terminal input)."""

import io
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import STAGES, tui


def sample_candidate(title="候选标题", thesis="候选论点", hook="候选钩子"):
    return {
        "title": title,
        "thesis": thesis,
        "hook": hook,
        "strategic_relevance": "影响选型的战略相关性",
        "evidence_gaps": ["缺少独立的第二来源验证。"],
        "research_queries": ["测试 查询"],
        "sources": [{"title": title, "url": "https://example.com/x", "origin": "aihot"}],
    }


def sample_hot_item(title="热点标题", source="X：官方账号", score=71):
    return {
        "title": title,
        "summary": "一句摘要。",
        "source_name": source,
        "score": score,
        "links": {"story": "", "original": "https://example.com/x"},
    }


class RenderProgressTests(unittest.TestCase):
    def test_completed_current_and_future_marks(self):
        lines = tui.render_progress("topic_choice", STAGES, color=False).splitlines()
        self.assertEqual(len(lines), len(STAGES))
        self.assertEqual(lines[0], "✓ collect")
        self.assertEqual(lines[1], "→ topic_choice")
        self.assertEqual(lines[2], "  research")
        self.assertEqual(lines[-1], "  completed")

    def test_first_stage_marks_only_current(self):
        lines = tui.render_progress("collect", STAGES, color=False).splitlines()
        self.assertEqual(lines[0], "→ collect")
        self.assertTrue(all(line.startswith("  ") for line in lines[1:]))

    def test_last_stage_marks_everything_completed(self):
        lines = tui.render_progress("completed", STAGES, color=False).splitlines()
        self.assertTrue(all(line.startswith("✓ ") for line in lines[:-1]))
        self.assertEqual(lines[-1], "→ completed")

    def test_unknown_stage_renders_all_stages_plainly(self):
        out = tui.render_progress("does-not-exist", STAGES, color=False)
        self.assertEqual(out.splitlines(), list(STAGES))

    def test_defaults_to_ai_daily_stages(self):
        out = tui.render_progress("does-not-exist", color=False)
        self.assertEqual(out.splitlines(), list(STAGES))


class RenderCandidatesTests(unittest.TestCase):
    def test_shows_title_thesis_and_hook_with_numbering(self):
        cands = [
            sample_candidate("A", "A-thesis", "A-hook"),
            sample_candidate("B", "B-thesis", "B-hook"),
            sample_candidate("C", "C-thesis", "C-hook"),
        ]
        out = tui.render_candidates(cands, color=False)
        self.assertIn("1. A", out)
        self.assertIn("2. B", out)
        self.assertIn("3. C", out)
        self.assertIn("thesis：A-thesis", out)
        self.assertIn("hook：A-hook", out)
        self.assertIn("战略相关性：影响选型的战略相关性", out)

    def test_missing_optional_fields_still_render(self):
        out = tui.render_candidates([{"title": "X", "thesis": "t", "hook": "h"}], color=False)
        self.assertIn("1. X", out)
        self.assertIn("thesis：t", out)
        self.assertIn("hook：h", out)


class PromptChoiceTests(unittest.TestCase):
    def test_retries_until_valid_integer(self):
        answers = iter(["abc", "9", "", "2"])
        result = tui.prompt_choice(3, input_fn=lambda _prompt: next(answers))
        self.assertEqual(result, 2)

    def test_valid_input_returns_immediately(self):
        self.assertEqual(tui.prompt_choice(3, input_fn=lambda _prompt: "3"), 3)

    def test_prompt_mentions_valid_range(self):
        prompts = []

        def fake_input(prompt):
            prompts.append(prompt)
            return "1"

        tui.prompt_choice(3, input_fn=fake_input)
        self.assertIn("1..3", prompts[0])


class PromptOptionalDirectionTests(unittest.TestCase):
    def test_empty_input_returns_empty_string(self):
        self.assertEqual(tui.prompt_optional_direction(input_fn=lambda _prompt: ""), "")
        self.assertEqual(tui.prompt_optional_direction(input_fn=lambda _prompt: "  "), "")

    def test_input_is_stripped(self):
        result = tui.prompt_optional_direction(
            input_fn=lambda _prompt: "  按企业采购视角写，别写开发者教程。  "
        )
        self.assertEqual(result, "按企业采购视角写，别写开发者教程。")


class ColorTests(unittest.TestCase):
    def test_plain_rendering_never_emits_escape_sequences(self):
        progress = tui.render_progress("topic_choice", STAGES, color=False)
        cands = tui.render_candidates([sample_candidate()], color=False)
        self.assertNotIn("\033", progress)
        self.assertNotIn("\033", cands)

    def test_color_rendering_emits_escape_sequences(self):
        progress = tui.render_progress("topic_choice", STAGES, color=True)
        cands = tui.render_candidates([sample_candidate()], color=True)
        self.assertIn("\033", progress)
        self.assertIn("\033", cands)

    def test_supports_color_reflects_isatty(self):
        class FakeTTY(io.StringIO):
            def isatty(self):
                return True

        class FakePipe(io.StringIO):
            def isatty(self):
                return False

        self.assertTrue(tui.supports_color(FakeTTY()))
        self.assertFalse(tui.supports_color(FakePipe()))


class RenderHotTopicsTests(unittest.TestCase):
    def test_ranks_titles_sources_and_scores(self):
        out = tui.render_hot_topics(
            [sample_hot_item("甲", "A 源", 90), sample_hot_item("乙", "B 源", 71)],
            color=False,
        )
        self.assertIn("AIHOT 热点榜", out)
        self.assertIn(" 1. 甲", out)
        self.assertIn("来源：A 源 · 热度 90", out)
        self.assertIn(" 2. 乙", out)
        self.assertIn("来源：B 源 · 热度 71", out)

    def test_empty_items_render_explicit_empty_line(self):
        out = tui.render_hot_topics([], color=False)
        self.assertIn("暂无数据", out)

    def test_summary_shown_when_present_and_skipped_when_empty(self):
        with_summary = tui.render_hot_topics([sample_hot_item()], color=False)
        self.assertIn("一句摘要。", with_summary)
        item = sample_hot_item()
        item["summary"] = ""
        without_summary = tui.render_hot_topics([item], color=False)
        self.assertNotIn("一句摘要。", without_summary)

    def test_plain_rendering_never_emits_escape_sequences(self):
        out = tui.render_hot_topics([sample_hot_item()], color=False)
        self.assertNotIn("\033", out)


class RenderMatrixTests(unittest.TestCase):
    def test_ok_matrix_shows_story_title_id_and_reports(self):
        matrix = {
            "status": "ok",
            "story_id": "uuid-1",
            "story_title": "某事件",
            "reports": [
                {"source_name": "甲社", "title": "报道一",
                 "original_url": "https://example.com/a"},
            ],
        }
        out = tui.render_matrix(matrix, color=False)
        self.assertIn("AIHOT 报道矩阵", out)
        self.assertIn("某事件", out)
        self.assertIn("uuid-1", out)
        self.assertIn("报道：1 条", out)
        self.assertIn("甲社 — 报道一", out)
        self.assertIn("https://example.com/a", out)

    def test_unavailable_matrix_shows_reason(self):
        out = tui.render_matrix(
            {"status": "unavailable", "reason": "无 story 链接"}, color=False
        )
        self.assertIn("不可用", out)
        self.assertIn("无 story 链接", out)

    def test_reports_truncated_after_eight(self):
        matrix = {
            "status": "ok",
            "story_id": "uuid-1",
            "story_title": "某事件",
            "reports": [
                {"source_name": f"s{i}", "title": f"t{i}", "original_url": f"https://e/{i}"}
                for i in range(1, 11)
            ],
        }
        out = tui.render_matrix(matrix, color=False)
        self.assertIn("s1 — t1", out)
        self.assertIn("s8 — t8", out)
        self.assertNotIn("s9 — t9", out)
        self.assertIn("其余 2 条", out)


class RenderEvidenceTests(unittest.TestCase):
    def test_counts_success_and_shows_urls_with_marks(self):
        evidence = [
            {"url": "https://e/1", "status": "fetched", "source_lane": "http"},
            {"url": "https://e/2", "status": "failed", "source_lane": "http",
             "error": "403"},
        ]
        out = tui.render_evidence(evidence, color=False)
        self.assertIn("抓取证据：2 条", out)
        self.assertIn("成功 1", out)
        self.assertIn("✓ https://e/1 [http]", out)
        self.assertIn("✗ https://e/2 [http]", out)


class RenderOsintTests(unittest.TestCase):
    def test_module_with_summary_gets_check_and_snippet(self):
        out = tui.render_osint(
            [{"key": "timeline", "title": "时间线", "summary": "7 月发布。"}],
            gaps=[],
            analysis_status="completed",
            color=False,
        )
        self.assertIn("OSINT 情报档案", out)
        self.assertIn("✓ 时间线（timeline）", out)
        self.assertIn("7 月发布。", out)
        self.assertIn("Codex 分析：completed", out)

    def test_empty_module_gets_dash_mark(self):
        out = tui.render_osint(
            [{"key": "finance", "title": "财务", "summary": "无"}],
            gaps=[],
            color=False,
        )
        self.assertIn("— 财务（finance）", out)

    def test_gaps_are_listed(self):
        out = tui.render_osint(
            [], gaps=["模块「财务」暂无证据"], color=False
        )
        self.assertIn("证据缺口：", out)
        self.assertIn("- 模块「财务」暂无证据", out)


if __name__ == "__main__":
    unittest.main()

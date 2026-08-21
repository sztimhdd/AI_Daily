"""Tests for the deterministic English editorial quality gate."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import quality


def _clean_article(paragraphs=4, sentences=3):
    """A clean English article in the Lead Tech Editor voice."""
    lines = ["# The search budget is the hidden line item", ""]
    for i in range(paragraphs):
        lead = f"**Point {i + 1}.** " if i % 2 == 0 else ""
        lines.append(
            f"{lead}Vendors moved pricing by 15 percent this "
            f"week, and each change is on the public blog ([announcement]"
            f"(https://example.com/{i})). Teams that never capped agent "
            f"retrieval depth saw the bill compound."
        )
        lines.append("")
    lines.append(
        "The risk is concrete: a team without a retrieval ceiling can "
        "double its spend next quarter."
    )
    lines.append("")
    return "\n".join(lines)


class WordCountTests(unittest.TestCase):
    def test_word_count_counts_english_words(self):
        self.assertEqual(quality.word_count("one two three four."), 4)
        self.assertEqual(quality.word_count("a b-c d'e"), 3)
        self.assertEqual(quality.word_count(""), 0)

    def test_module_constants_match_spec(self):
        self.assertEqual(quality.EN_MIN_WORDS, 800)
        self.assertEqual(quality.EN_MAX_WORDS, 1200)
        self.assertEqual(quality.MAX_SENTENCES_PER_PARAGRAPH, 3)

    def test_body_words_exclude_urls(self):
        text = (
            "A sentence with a link "
            "([announcement](https://example.com/posts/one-two-three))."
        )
        # "A sentence with a link announcement" = 6 words; URL path excluded.
        self.assertEqual(quality._body_words(text), 6)


class VerdictTests(unittest.TestCase):
    def test_clean_article_passes(self):
        result = quality.check_en(
            _clean_article(), {"sources": []}, min_words=10, max_words=500
        )
        self.assertEqual(result.verdict, "pass", result.to_dict())

    def test_missing_links_is_evidence_recovery(self):
        text = "# A bare title\n\nNo sources here at all in this paragraph."
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "evidence_recovery", result.to_dict())

    def test_unsupported_certainty_is_evidence_recovery(self):
        text = (
            "# Title\n\nThis will undoubtedly reshape the whole industry "
            "([post](https://example.com/1))."
        )
        result = quality.check_en(
            text, {"sources": []}, min_words=1, max_words=500
        )
        self.assertEqual(result.verdict, "evidence_recovery", result.to_dict())

    def test_walled_failed_source_without_downgrade_is_evidence_recovery(self):
        text = (
            "# Title\n\nThe feature shipped last week "
            "([wechat post](https://mp.weixin.qq.com/s/abc))."
        )
        evidence = {
            "sources": [
                {
                    "url": "https://mp.weixin.qq.com/s/abc",
                    "title": "wechat post",
                    "status": "failed",
                    "source_lane": "cdp",
                }
            ]
        }
        result = quality.check_en(text, evidence, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "evidence_recovery", result.to_dict())

    def test_walled_failed_source_with_downgrade_is_not_recovery(self):
        text = (
            "# Title\n\nThe feature reportedly shipped last week, but the "
            "walled source could not be verified "
            "([wechat post](https://mp.weixin.qq.com/s/abc))."
        )
        evidence = {
            "sources": [
                {
                    "url": "https://mp.weixin.qq.com/s/abc",
                    "title": "wechat post",
                    "status": "failed",
                    "source_lane": "cdp",
                }
            ]
        }
        result = quality.check_en(text, evidence, min_words=1, max_words=500)
        self.assertNotEqual(result.verdict, "evidence_recovery", result.to_dict())

    def test_could_not_be_verified_marker_alone_passes(self):
        # The natural downgrade phrasing, without any "walled source" words,
        # must satisfy the gate on its own (regex regression).
        text = (
            "# Title\n\nThe feature reportedly shipped last week, but it "
            "could not be verified ([post](https://mp.weixin.qq.com/s/abc))."
        )
        evidence = {
            "sources": [
                {
                    "url": "https://mp.weixin.qq.com/s/abc",
                    "title": "post",
                    "status": "failed",
                    "source_lane": "cdp",
                }
            ]
        }
        result = quality.check_en(text, evidence, min_words=1, max_words=500)
        self.assertNotEqual(result.verdict, "evidence_recovery", result.to_dict())

    def test_walled_failed_source_not_cited_does_not_force_recovery(self):
        # A failed-fetch walled URL sitting unused in the package is not a
        # claim, so it must not bounce a clean article back to research.
        text = (
            "# Title\n\nA clean sourced sentence about pricing "
            "([post](https://example.com/1)). A second sentence. A third."
        )
        evidence = {
            "sources": [
                {
                    "url": "https://mp.weixin.qq.com/s/unused",
                    "title": "unused wechat",
                    "status": "failed",
                    "source_lane": "cdp",
                }
            ]
        }
        result = quality.check_en(text, evidence, min_words=1, max_words=500)
        self.assertNotEqual(result.verdict, "evidence_recovery", result.to_dict())

    def test_raw_html_is_revise(self):
        text = (
            "# Title\n\nA sourced sentence ([post](https://example.com/1)). "
            "<div>raw html</div>"
        )
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_short_article_is_revise(self):
        text = (
            "# Title\n\nOnly a handful of words here "
            "([post](https://example.com/1))."
        )
        result = quality.check_en(text, {"sources": []}, min_words=50, max_words=500)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_long_article_is_revise(self):
        text = "# Title\n\n" + ("Long but clean sentence with a source link "
                                "([post](https://example.com/1)). " * 40)
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=10)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_word_count_feedback_tells_the_model_how_to_fix(self):
        short = quality.check_en(
            "A short draft that never reaches the floor.",
            {"sources": []}, min_words=50, max_words=500,
        )
        short_msg = next(
            f.message for f in short.findings if f.check == "word-count"
        )
        self.assertIn("50 minimum", short_msg)
        self.assertIn("expand", short_msg)
        long = quality.check_en(
            "This draft is far longer than the ceiling allows for a single "
            "compact paragraph that keeps going and going and going without "
            "ever stopping to breathe or reach a point.",
            {"sources": []}, min_words=1, max_words=20,
        )
        long_msg = next(
            f.message for f in long.findings if f.check == "word-count"
        )
        self.assertIn("20 maximum", long_msg)
        self.assertIn("trim", long_msg)

    def test_four_sentence_paragraph_is_revise(self):
        text = (
            "# Title\n\nOne sentence here. Two sentences follow. A third "
            "sentence closes. A fourth sentence violates the rule "
            "([post](https://example.com/1))."
        )
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_ai_trace_tag_is_revise(self):
        text = (
            "# Title\n\nA sourced sentence ([post](https://example.com/1)).\n\n"
            "In summary: everything changed."
        )
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_placeholder_is_revise(self):
        text = (
            "# Title\n\nA sourced sentence ([post](https://example.com/1)).\n\n"
            "{[IMG_1]}"
        )
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_de_ai_finding_is_revise(self):
        text = (
            "# Title\n\nThe platform leverages a robust seamless stack "
            "([post](https://example.com/1))."
        )
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_bold_spacing_is_pass_with_notes(self):
        text = (
            "# Title\n\nA sourced sentence ([post](https://example.com/1)). "
            "The**cost**is the hidden line item. A third sentence."
        )
        result = quality.check_en(text, {"sources": []}, min_words=1, max_words=500)
        self.assertEqual(result.verdict, "pass_with_notes", result.to_dict())

    def test_result_serializes_to_dict(self):
        result = quality.check_en(_clean_article(), {"sources": []},
                                  min_words=10, max_words=500)
        data = result.to_dict()
        self.assertEqual(data["verdict"], "pass")
        self.assertIn("word_count", data)


class CraftGateTests(unittest.TestCase):
    """Round 2 gate checks: quote integrity, bold metrics, rhythm, leaks."""

    def _run(self, text, evidence=None):
        return quality.check_en(text, evidence or {"sources": []},
                                min_words=1, max_words=500)

    def test_truncated_quote_fragment_is_revise(self):
        text = (
            "# Title\n\nThe blog says routing stays \"driven by what\". "
            "([post](https://example.com/1))"
        )
        result = self._run(text)
        self.assertEqual(result.verdict, "revise", result.to_dict())
        self.assertTrue(
            any(f.check == "quote-integrity" for f in result.findings),
            result.to_dict(),
        )

    def test_unbalanced_quotes_is_revise(self):
        text = (
            "# Title\n\nA sentence with an \"unclosed quote and a source "
            "([post](https://example.com/1))."
        )
        result = self._run(text)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_complete_quote_passes(self):
        text = (
            "# Title\n\n> same mission, same name, same product, same "
            "roadmap.\n\nThe company said so ([post](https://example.com/1))."
        )
        result = self._run(text)
        self.assertNotIn(
            "quote-integrity",
            [f.check for f in result.findings],
            result.to_dict(),
        )

    def test_quote_comparison_construction_is_not_a_truncated_fragment(self):
        # Regression: '"A" is the 2026 version of "B"' must not trip the
        # truncated-quote heuristic.
        text = (
            "# Title\n\nHe called it the 2026 version of the gateway play, "
            "per ([post](https://example.com/1)). A second sentence. A third."
        )
        result = self._run(text)
        self.assertNotIn(
            "quote-integrity",
            [f.check for f in result.findings],
            result.to_dict(),
        )

    def test_pipeline_leak_is_revise(self):
        text = (
            "# Title\n\nBloomberg's own article returned an HTTP 403 when "
            "checked ([post](https://example.com/1))."
        )
        result = self._run(text)
        self.assertEqual(result.verdict, "revise", result.to_dict())

    def test_unbolded_figures_are_noted(self):
        text = (
            "# Title\n\nThe deal is worth $7 billion and 10T+ tokens daily, "
            "per ([post](https://example.com/1)). A second sentence. A third."
        )
        result = self._run(text)
        self.assertEqual(result.verdict, "pass_with_notes", result.to_dict())
        self.assertTrue(
            any(f.check == "metric-bold" for f in result.findings),
            result.to_dict(),
        )

    def test_bolded_figures_are_clean(self):
        text = (
            "# Title\n\nThe deal is worth **$7 billion**, per "
            "([post](https://example.com/1)). A second sentence. A third."
        )
        result = self._run(text)
        self.assertNotIn(
            "metric-bold", [f.check for f in result.findings], result.to_dict()
        )

    def test_long_sentence_is_noted(self):
        text = (
            "# Title\n\n" + ("word " * 25) + "([post](https://example.com/1)). "
            "A second sentence. A third."
        )
        result = self._run(text)
        self.assertEqual(result.verdict, "pass_with_notes", result.to_dict())
        self.assertTrue(
            any(f.check == "sentence-rhythm" for f in result.findings),
            result.to_dict(),
        )

    def test_passive_voice_is_noted(self):
        text = (
            "# Title\n\nThe figure was not disclosed and the source was not "
            "fetched ([post](https://example.com/1)). A second sentence. A third."
        )
        result = self._run(text)
        self.assertTrue(
            any(f.check == "passive-voice" for f in result.findings),
            result.to_dict(),
        )

    def test_lead_in_ratio_is_noted(self):
        paras = []
        for i in range(4):
            paras.append(
                f"**Lead {i}.** A sourced sentence "
                f"([post](https://example.com/{i})). A second. A third."
            )
        text = "# Title\n\n" + "\n\n".join(paras) + "\n"
        result = self._run(text)
        self.assertTrue(
            any(f.check == "lead-in-ratio" for f in result.findings),
            result.to_dict(),
        )


if __name__ == "__main__":
    unittest.main()

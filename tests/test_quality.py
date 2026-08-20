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
        lines.append(
            f"**Point {i + 1}.** Vendors moved pricing by 15 percent this "
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


if __name__ == "__main__":
    unittest.main()

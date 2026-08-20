"""Tests for the executable 8-category remove-ai-slop contract."""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import deslop

# Written in the compiled author voice (knowledge/author-style.md):
# facts first, cold kicker, no slop. Must pass all 8 categories.
CLEAN_CORPUS = """推理账单这周又改了价。三家服务商同时调整 Token 计费，幅度从 15% 到 40% 不等，公告都挂在各自博客上（[OpenRouter 公告](https://example.com/announce)）。

**钱花在搜索里。** 一次深度研究任务平均要发起二十几次检索调用，这是账单里最容易被忽略的部分。调用次数没有公开口径，只能按公开定价倒推。

但问题不在单价。预算失控的团队，多半是没有限制智能体的检索深度，一层一层查下去，费用成倍往上翻。

风险很具体：不设检索预算上限的团队，下个季度的推理支出可能翻倍。数字以各家公告为准，口径不一致的地方已经标出。"""


class ContractShapeTests(unittest.TestCase):
    def test_contract_covers_exactly_eight_required_categories(self):
        ids = [c["id"] for c in deslop.CATEGORIES]
        self.assertEqual(len(ids), 8)
        self.assertEqual(len(set(ids)), 8)
        for cid in (
            "empty-connectives",
            "template-opening",
            "mechanical-enumeration",
            "over-parallelism",
            "corporate-bookish",
            "marketing-hype",
            "unsupported-certainty",
            "stiff-ending-uplift",
        ):
            self.assertIn(cid, ids)

    def test_every_category_has_name_and_description(self):
        for cat in deslop.CATEGORIES:
            self.assertTrue(cat["name"])
            self.assertTrue(cat["description"])


class CategoryDetectionTests(unittest.TestCase):
    def assertDetects(self, text, category_id):
        findings = deslop.check_text(text)
        self.assertTrue(
            any(f.category == category_id for f in findings),
            f"expected {category_id} findings, got {findings}",
        )

    def test_empty_connectives_detected(self):
        self.assertDetects("此外，系统还优化了缓存。", "empty-connectives")
        self.assertDetects("值得注意的是价格。", "empty-connectives")

    def test_template_opening_detected(self):
        self.assertDetects(
            "随着人工智能的飞速发展，越来越多的团队开始引入智能体。\n\n账单因此变了。",
            "template-opening",
        )

    def test_mechanical_enumeration_detected(self):
        self.assertDetects("首先看成本。其次看延迟。", "mechanical-enumeration")

    def test_single_final_marker_is_not_enumeration(self):
        findings = deslop.check_text("价格改了三次。最后一次幅度最大。")
        self.assertFalse(any(f.category == "mechanical-enumeration" for f in findings))

    def test_over_parallelism_detected(self):
        # absolute pattern: one occurrence is enough
        self.assertDetects("这不仅是技术的升级，更是时代的召唤。", "over-parallelism")
        # soft patterns need two occurrences
        self.assertDetects(
            "不是模型不行，而是预算不行。既想马儿跑，又想马儿不吃草。",
            "over-parallelism",
        )

    def test_corporate_bookish_detected(self):
        self.assertDetects("该平台通过闭环设计赋能业务。", "corporate-bookish")
        self.assertDetects("这件事具有深远的意义。", "corporate-bookish")

    def test_marketing_hype_detected(self):
        self.assertDetects("这次更新堪称变革性的跨越。", "marketing-hype")

    def test_unsupported_certainty_detected(self):
        self.assertDetects("这一趋势必将重塑行业格局。", "unsupported-certainty")

    def test_stiff_ending_uplift_detected(self):
        self.assertDetects(
            "价格还在变。\n\n让我们拭目以待，未来可期。", "stiff-ending-uplift"
        )

    def test_uplift_phrases_mid_article_are_not_ending_uplift(self):
        findings = deslop.check_text(
            "有人说未来可期。\n\n但账单不认这种话，只认数字。"
        )
        self.assertFalse(
            any(f.category == "stiff-ending-uplift" for f in findings)
        )


class CleanCorpusTests(unittest.TestCase):
    def test_clean_corpus_passes_all_categories(self):
        self.assertEqual(deslop.check_text(CLEAN_CORPUS), [])
        self.assertTrue(deslop.is_clean(CLEAN_CORPUS))

    def test_url_content_does_not_trigger_false_positives(self):
        text = "公告在这里：https://example.com/track?word=赋能 数字以公告为准。"
        self.assertEqual(deslop.check_text(text), [])

    def test_check_file_reads_from_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "article.md"
            path.write_text("该平台致力于赋能行业。", encoding="utf-8")
            findings = deslop.check_file(path)
            self.assertTrue(any(f.category == "corporate-bookish" for f in findings))


class EnglishContractTests(unittest.TestCase):
    """English de-AI checks mirror the 8 Chinese categories."""

    # Written in the English author voice (Lead Tech Editor, cold kicker).
    EN_CLEAN = (
        "OpenRouter changed its pricing table again this week. Three "
        "providers moved their token billing by 15% to 40%, each blog post "
        "linked below ([announcement](https://example.com/announce)).\n\n"
        "**The search budget is the hidden line item.** One deep research "
        "task fires twenty-plus retrieval calls, and no vendor publishes a "
        "per-call count, so the number has to be reverse-engineered from "
        "public pricing.\n\n"
        "The problem is not the unit price. Teams that lose control never "
        "capped how deep the agent searches, so the bill compounds layer "
        "by layer.\n\n"
        "The risk is concrete: a team without a retrieval ceiling can double "
        "its inference spend next quarter. Figures follow the vendor posts; "
        "where they disagree, the gap is flagged."
    )

    def assertDetectsEn(self, text, category_id):
        findings = deslop.check_text_en(text)
        self.assertTrue(
            any(f.category == category_id for f in findings),
            f"expected {category_id} findings, got {findings}",
        )

    def test_en_clean_corpus_passes(self):
        self.assertEqual(deslop.check_text_en(self.EN_CLEAN), [])

    def test_en_empty_connectives_detected(self):
        self.assertDetectsEn(
            "Furthermore, the team cut the cache. In conclusion, it helped.",
            "empty-connectives",
        )

    def test_en_template_opening_detected(self):
        self.assertDetectsEn(
            "In today's rapidly evolving world, teams ship agents. The bill changed.",
            "template-opening",
        )

    def test_en_mechanical_enumeration_detected(self):
        self.assertDetectsEn(
            "Firstly, the cost. Secondly, the latency. Finally, the risk.",
            "mechanical-enumeration",
        )

    def test_en_over_parallelism_detected(self):
        self.assertDetectsEn(
            "This is not only cheaper but also faster.", "over-parallelism"
        )

    def test_en_corporate_bookish_detected(self):
        self.assertDetectsEn(
            "The platform leverages a robust, cutting-edge, seamless stack.",
            "corporate-bookish",
        )

    def test_en_marketing_hype_detected(self):
        self.assertDetectsEn(
            "The release is revolutionary and groundbreaking.", "marketing-hype"
        )

    def test_en_unsupported_certainty_detected(self):
        self.assertDetectsEn(
            "This will undoubtedly reshape the industry.", "unsupported-certainty"
        )

    def test_en_stiff_ending_uplift_detected(self):
        self.assertDetectsEn(
            "Prices are still moving.\n\nOnly time will tell. The future is bright.",
            "stiff-ending-uplift",
        )

    def test_en_url_content_does_not_trigger_false_positives(self):
        text = (
            "The post is here: https://example.com/track?word=leverage. "
            "Figures follow the vendor."
        )
        self.assertEqual(deslop.check_text_en(text), [])


class ReportTests(unittest.TestCase):
    def test_report_marks_clean_text_as_pass(self):
        self.assertIn("PASS", deslop.report(deslop.check_text(CLEAN_CORPUS)))

    def test_report_lists_findings_with_category_and_phrase(self):
        findings = deslop.check_text("此外，这件事必将成功。")
        out = deslop.report(findings)
        self.assertIn("empty-connectives", out)
        self.assertIn("unsupported-certainty", out)
        self.assertIn("此外", out)


if __name__ == "__main__":
    unittest.main()

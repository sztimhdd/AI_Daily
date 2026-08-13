"""Tests for assembly: package creation, validation, final mapping.

Assembly is the quality gate before publishing: it validates the draft
(no placeholders, no n8n/debug expressions, non-empty, links intact),
builds outputs/YYYY/MM/DD/<slug>/ with article.md + metadata.json +
sources.md (+ optional images/cover), and writes the final
articles/<date>-<slug>-zh.md.  A missing or invalid cover never blocks.
"""

import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import assemble, cover as cover_mod, paths, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"

ARTICLE = """# AI 搜索预算与个人创作者的研究成本

独立创作者正在为搜索预算付出可计量的成本。

## 预算从哪里来

深度研究类智能体把大部分 token 花在检索调用上，见 [Agent search benchmarks](https://source-a.example.com/posts/agent-search-cost)。

## 这对个人创作者意味着什么

研究成本开始进入个人创作者的账本。出处：[Unique story about research budgets](https://source-b.example.com/notes/solo-research-budget)。
"""


def make_png(width=16, height=9):
    def chunk(tag, payload):
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


class AssembleBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        self.topic = topics.choose_fixture(self.rp, FIXTURES / "topic_fixture.json")

    def tearDown(self):
        self._tmp.cleanup()

    def write_article(self, text=ARTICLE):
        (self.rp.work_dir / "article.md").write_text(text, encoding="utf-8")

    def write_research(self):
        data = {
            "run_id": self.rp.run_id,
            "date": self.rp.date,
            "topic_title": self.topic["title"],
            "slug": self.topic["slug"],
            "questions": [
                {
                    "query": "成本口径",
                    "status": "supported",
                    "evidence": [
                        {
                            "title": "Agent search benchmarks",
                            "url": "https://source-a.example.com/posts/agent-search-cost",
                            "origin": "rss",
                            "excerpt": "Deep-research agents spend most budget on search.",
                        }
                    ],
                }
            ],
            "cross_validation": [],
            "evidence_urls": ["https://source-a.example.com/posts/agent-search-cost"],
        }
        (self.rp.work_dir / "research.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


class AssemblyTests(AssembleBase):
    def test_package_created_with_article_metadata_sources(self):
        self.write_article()
        self.write_research()
        result = assemble.run(self.rp)
        pkg = self.rp.package_dir(self.topic["slug"])
        self.assertEqual(result["status"], "assembled")
        self.assertTrue((pkg / "article.md").is_file())
        self.assertTrue((pkg / "metadata.json").is_file())
        self.assertTrue((pkg / "sources.md").is_file())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["slug"], self.topic["slug"])
        self.assertEqual(meta["date"], "2026-08-12")
        self.assertEqual(meta["title"], self.topic["title"])
        self.assertFalse(meta["has_cover"])

    def test_final_article_written_and_matches_draft(self):
        self.write_article()
        self.write_research()
        assemble.run(self.rp)
        final = self.rp.final_article_path(self.topic["slug"])
        self.assertTrue(final.is_file())
        self.assertEqual(final.read_text(encoding="utf-8"), ARTICLE)

    def test_source_links_preserved_in_package(self):
        self.write_article()
        self.write_research()
        assemble.run(self.rp)
        pkg = self.rp.package_dir(self.topic["slug"])
        sources_md = (pkg / "sources.md").read_text(encoding="utf-8")
        self.assertIn("https://source-a.example.com/posts/agent-search-cost", sources_md)
        self.assertIn("Agent search benchmarks", sources_md)
        article = (pkg / "article.md").read_text(encoding="utf-8")
        self.assertIn("](https://source-a.example.com/posts/agent-search-cost)", article)

    def test_placeholder_images_rejected(self):
        self.write_article(ARTICLE + "\n{[IMG_1]}\n")
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)

    def test_n8n_expression_rejected(self):
        self.write_article(ARTICLE.replace("独立创作者", "{{$json.title}}"))
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)

    def test_empty_article_rejected(self):
        self.write_article("   \n\n")
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)

    def test_article_without_title_rejected(self):
        self.write_article("没有标题的正文。\n")
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)

    def test_missing_article_rejected(self):
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)


class CoverHandlingTests(AssembleBase):
    def test_valid_cover_moves_into_package(self):
        self.write_article()
        self.write_research()
        (self.rp.work_dir / "cover.png").write_bytes(make_png(120, 63))
        assemble.run(self.rp)
        pkg = self.rp.package_dir(self.topic["slug"])
        self.assertTrue((pkg / "images" / "cover.png").is_file())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(meta["has_cover"])
        self.assertEqual(meta["cover"]["width"], 120)

    def test_assemble_succeeds_without_cover(self):
        self.write_article()
        self.write_research()
        result = assemble.run(self.rp)
        pkg = self.rp.package_dir(self.topic["slug"])
        self.assertEqual(result["status"], "assembled")
        self.assertFalse((pkg / "images").exists())

    def test_invalid_cover_skipped_without_blocking(self):
        self.write_article()
        self.write_research()
        (self.rp.work_dir / "cover.png").write_bytes(b"not a real image")
        result = assemble.run(self.rp)
        pkg = self.rp.package_dir(self.topic["slug"])
        self.assertEqual(result["status"], "assembled")
        self.assertFalse((pkg / "images" / "cover.png").exists())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(meta["has_cover"])


class StateMappingTests(AssembleBase):
    def test_final_mapping_recorded_in_state(self):
        self.write_article()
        self.write_research()
        assemble.run(self.rp)
        st = state.read_state(self.rp)
        self.assertIn("package", st["artifacts"])
        self.assertIn("final-article", st["artifacts"])
        self.assertTrue(st["artifacts"]["final-article"].endswith(
            "articles/2026-08-12-ai-search-budget-research-cost-zh.md"))
        self.assertTrue(st["artifacts"]["package"].endswith(
            "outputs/2026/08/12/ai-search-budget-research-cost"))

    def test_resume_returns_without_rebuilding(self):
        self.write_article()
        self.write_research()
        first = assemble.run(self.rp)
        second = assemble.run(self.rp)
        self.assertEqual(first["status"], "assembled")
        self.assertEqual(second["status"], "resumed")


class ResidueValidationTests(AssembleBase):
    """Published-article residue: raw HTML, ellipsis, truncated URLs."""

    def test_clean_article_passes_validation(self):
        self.assertEqual(assemble.validate_article(ARTICLE), [])

    def test_validate_flags_raw_html_tags(self):
        bad = ARTICLE.replace(
            "独立创作者正在为搜索预算付出可计量的成本。",
            "<p><strong>独立创作者</strong>正在为搜索预算付出可计量的成本。</p>",
        )
        problems = assemble.validate_article(bad)
        self.assertTrue(any("raw HTML" in p for p in problems), problems)

    def test_validate_flags_truncated_unclosed_html_tag(self):
        bad = ARTICLE + '\n另一条佐证：<p><strong><a href="https://rese\n'
        problems = assemble.validate_article(bad)
        self.assertTrue(any("raw HTML" in p for p in problems), problems)

    def test_validate_flags_ellipsis_residue(self):
        for fragment in ("OpenRou…。", "预算还在增长..."):
            bad = ARTICLE + f"\n{fragment}\n"
            problems = assemble.validate_article(bad)
            self.assertTrue(any("ellipsis" in p for p in problems),
                            f"{fragment!r}: {problems}")

    def test_validate_flags_truncated_url_fragment(self):
        bad = ARTICLE + "\n详见 https://rese 的报道。\n"
        problems = assemble.validate_article(bad)
        self.assertTrue(any("truncated URL" in p for p in problems), problems)

    def test_full_urls_and_decimals_still_pass(self):
        extra = (
            "\n数字如 2.5x、Qwen3.8-2.4T 与完整链接 "
            "https://source-a.example.com/posts/agent-search-cost 都合法。\n"
        )
        self.assertEqual(assemble.validate_article(ARTICLE + extra), [])

    def test_assemble_rejects_html_residue(self):
        self.write_article(ARTICLE + '\n<p><strong><a href="https://rese…\n')
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)

    def test_assemble_rejects_ellipsis_residue(self):
        self.write_article(ARTICLE.replace("可计量的成本。", "可计量的成本…。"))
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)

    def test_assemble_rejects_truncated_url_fragment(self):
        self.write_article(ARTICLE + "\n详见 https://rese 的报道。\n")
        self.write_research()
        with self.assertRaises(assemble.AssembleError):
            assemble.run(self.rp)


if __name__ == "__main__":
    unittest.main()

"""Black-box end-to-end tests: full fixture chains through the CLI.

These tests exercise the observable contract of the V1 pipeline:
collect -> topic_choice gate -> research -> outline -> draft ->
optional cover -> assembly -> publish, with resume, two-date
isolation, and controlled failure behavior.  They drive ``cli.main``
in-process (no subprocess, no network) and assert on filesystem
artifacts and state.md content only.
"""

import io
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import cli, pipeline, state
from ai_daily.paths import RunPaths

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"
AIHOT_FIXTURE = str(FIXTURES / "aihot_items.json")
TOPIC_FIXTURE = str(FIXTURES / "topic_fixture.json")
DATE_A = "2026-08-12"
SLUG_A = "ai-search-budget-research-cost"


def make_png(width=16, height=9) -> bytes:
    """Minimal valid PNG (RGB, no interlace), mirrors tests/test_cover.py."""
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x10\x20\x30" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def topic_b_dict():
    """A second, complete topic fixture with distinct slug/title."""
    return {
        "title": "开放权重模型的第二次突袭：从 Muse Glimmer 说起",
        "slug": "open-weights-muse-glimmer-surprise",
        "thesis": "开放权重模型正在用突袭式发布打乱闭源节奏，个人开发者需要重新评估部署窗口。",
        "hook": "大家还在盯闭源旗舰，开放权重阵营已经悄悄把模型推上了排行榜。",
        "audience": "独立开发者与小型 AI 产品团队",
        "evidence_gaps": ["Muse Glimmer 的许可证细节缺少官方口径"],
        "research_queries": ["Muse Glimmer 开放权重模型", "OpenRouter 实时排行榜"],
        "direction": "重点写开放权重发布节奏对个人开发者的影响。",
    }


class E2EBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def state_text(self, date=DATE_A):
        return (self.root / ".local" / "runs" / date / "state.md").read_text(encoding="utf-8")

    def step_chain(self, date, topic_fixture=TOPIC_FIXTURE, cover_source=None):
        """Run the step-by-step chain (not the one-shot `run` command)."""
        for argv in (
            ["init", "--root", str(self.root), "--date", date],
            ["collect", "--root", str(self.root), "--date", date,
             "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE],
            ["choose-topic", "--root", str(self.root), "--date", date,
             "--fixture", topic_fixture],
            ["research", "--root", str(self.root), "--date", date,
             "--mode", "fixture"],
            ["outline", "--root", str(self.root), "--date", date],
            ["draft", "--root", str(self.root), "--date", date],
        ):
            code, out, err = self.run_cli(*argv)
            self.assertEqual(code, 0, f"{argv[0]} failed: {err}")
        cov_argv = ["cover", "--root", str(self.root), "--date", date]
        if cover_source:
            cov_argv += ["--source-dir", cover_source]
        code, _, err = self.run_cli(*cov_argv)  # cover is nonblocking either way
        self.assertEqual(code, 0, err)
        for argv in (
            ["assemble", "--root", str(self.root), "--date", date],
            ["publish", "--root", str(self.root), "--date", date,
             "--repo-dir", str(self.root / ".local" / "publish" / date)],
        ):
            code, out, err = self.run_cli(*argv)
            self.assertEqual(code, 0, f"{argv[0]} failed: {err}")


class FullChainCliTests(E2EBase):
    def test_step_by_step_chain_completes_with_package_and_final(self):
        self.step_chain(DATE_A)
        st = self.state_text()
        self.assertIn("- stage: completed", st)
        self.assertIn("publish-mode: local-only", st)
        # nested package + final article + stable mapping
        pkg = self.root / "outputs" / "2026" / "08" / "12" / SLUG_A
        self.assertTrue((pkg / f"{SLUG_A}.md").is_file())
        self.assertTrue((pkg / "metadata.json").is_file())
        self.assertTrue((pkg / "sources.md").is_file())
        final = self.root / "articles" / f"{DATE_A}-{SLUG_A}-zh.md"
        self.assertTrue(final.is_file())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["slug"], SLUG_A)
        self.assertEqual(meta["final_article"], f"articles/{DATE_A}-{SLUG_A}-zh.md")
        self.assertFalse(meta["has_cover"])
        # candidates were exactly 3, each rich (thesis/hook/queries/sources)
        code, out, _ = self.run_cli("candidates", "--root", str(self.root), "--date", DATE_A)
        self.assertEqual(code, 0)
        self.assertEqual(out.count("## 候选 "), 3, out)
        self.assertEqual(out.count("- thesis："), 3)
        self.assertEqual(out.count("- hook："), 3)

    def test_collect_resume_does_not_increment_collect_runs(self):
        self.run_cli("init", "--root", str(self.root), "--date", DATE_A)
        for _ in range(3):
            code, _, err = self.run_cli(
                "collect", "--root", str(self.root), "--date", DATE_A,
                "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE)
            self.assertEqual(code, 0, err)
        self.assertIn("collect_runs: 1", self.state_text())


class TwoDateIsolationTests(E2EBase):
    def test_two_dates_do_not_leak_files(self):
        date_b = "2026-08-13"
        slug_b = topic_b_dict()["slug"]
        topic_b = self.root / "topic_b.json"
        topic_b.write_text(json.dumps(topic_b_dict(), ensure_ascii=False), encoding="utf-8")

        self.step_chain(DATE_A)
        self.step_chain(date_b, topic_fixture=str(topic_b))

        runs = sorted(p.name for p in (self.root / ".local" / "runs").iterdir())
        self.assertEqual(runs, [DATE_A, date_b])
        # date A package holds only slug A; date B only slug B
        self.assertEqual([p.name for p in (self.root / "outputs/2026/08/12").iterdir()], [SLUG_A])
        self.assertEqual([p.name for p in (self.root / "outputs/2026/08/13").iterdir()], [slug_b])
        articles = sorted(p.name for p in (self.root / "articles").iterdir())
        self.assertEqual(articles, [
            f"{DATE_A}-{SLUG_A}-zh.md",
            f"{date_b}-{slug_b}-zh.md",
        ])
        # no cross-date content leakage
        art_b = (self.root / "articles" / f"{date_b}-{slug_b}-zh.md").read_text(encoding="utf-8")
        self.assertNotIn(SLUG_A, art_b)
        st_b = self.state_text(date_b)
        self.assertIn(f"run_id: AI-Daily/{date_b}", st_b)
        self.assertIn("- stage: completed", st_b)


class NoTopicGateTests(E2EBase):
    def test_research_before_choice_is_gated(self):
        self.run_cli("init", "--root", str(self.root), "--date", DATE_A)
        code, _, err = self.run_cli(
            "collect", "--root", str(self.root), "--date", DATE_A,
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE)
        self.assertEqual(code, 0, err)
        for cmd in ("research", "outline", "draft"):
            code, out, err = self.run_cli(cmd, "--root", str(self.root), "--date", DATE_A)
            self.assertEqual(code, 1, f"{cmd} should be gated")
            self.assertIn("topic", (err + out).lower())
        # a gate block is a clean refusal: stage stays at the gate, no fake progress
        st = self.state_text()
        self.assertIn("- stage: topic_choice", st)
        self.assertIn("- status: in_progress", st)

    def test_human_choice_path_records_direction_verbatim(self):
        self.run_cli("init", "--root", str(self.root), "--date", DATE_A)
        self.run_cli("collect", "--root", str(self.root), "--date", DATE_A,
                     "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE)
        code, out, err = self.run_cli(
            "choose-topic", "--root", str(self.root), "--date", DATE_A,
            "--choice", "2", "--direction", "更偏个人创作者视角")
        self.assertEqual(code, 0, err)
        st = self.state_text()
        self.assertIn("topic_choice: human", st)
        self.assertIn("- stage: topic_choice", st)
        # direction kept verbatim in the selected topic record
        selected = json.loads(
            (self.root / ".local" / "runs" / DATE_A / "selected-topic.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(selected["direction"], "更偏个人创作者视角")


class CoverVariantsTests(E2EBase):
    def test_cover_is_adopted_and_packaged(self):
        src = self.root / "exports"
        src.mkdir()
        (src / "ChatGPT Image e2e cover.png").write_bytes(make_png())
        self.step_chain(DATE_A, cover_source=str(src))
        pkg = self.root / "outputs" / "2026" / "08" / "12" / SLUG_A
        self.assertTrue((pkg / "images" / "cover.png").is_file())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(meta["has_cover"])
        self.assertEqual(meta["cover"]["file"], "images/cover.png")
        self.assertIn("- stage: completed", self.state_text())

    def test_no_cover_still_completes(self):
        self.step_chain(DATE_A)  # no --source-dir
        pkg = self.root / "outputs" / "2026" / "08" / "12" / SLUG_A
        self.assertFalse((pkg / "images" / "cover.png").exists())
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(meta["has_cover"])
        self.assertIn("- stage: completed", self.state_text())

    def test_invalid_cover_is_nonblocking(self):
        src = self.root / "exports"
        src.mkdir()
        (src / "ChatGPT Image broken.png").write_bytes(b"not a png at all")
        self.step_chain(DATE_A, cover_source=str(src))
        pkg = self.root / "outputs" / "2026" / "08" / "12" / SLUG_A
        images = pkg / "images"
        self.assertFalse(images.exists() and any(images.iterdir()))
        self.assertIn("- stage: completed", self.state_text())


class AihotFailureTests(E2EBase):
    def test_live_failure_stops_then_fixture_resume_clears_error(self):
        run_paths = RunPaths.for_date(self.root, DATE_A)
        state.init_state(run_paths)

        def broken_fetch(url, timeout=None):
            raise OSError("connection refused")

        with self.assertRaises(pipeline.PipelineError):
            pipeline.run_collect(run_paths, mode="live", fetch=broken_fetch)
        st_failed = self.state_text()
        self.assertIn("- status: failed", st_failed)
        self.assertIn("AIHOT unavailable", st_failed)

        # fixture resume succeeds and clears the recorded error
        code, _, err = self.run_cli(
            "collect", "--root", str(self.root), "--date", DATE_A,
            "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE)
        self.assertEqual(code, 0, err)
        st = self.state_text()
        self.assertIn("- stage: topic_choice", st)
        self.assertIn("- status: in_progress", st)
        # current error is cleared (stage_log keeps immutable history)
        self.assertIn("- last_error:\n", st)  # empty value, error cleared
        self.assertIn("collect_runs: 1", st)  # failed attempt never bumps


class AllRssFailTests(E2EBase):
    def test_all_rss_fail_is_nonblocking(self):
        run_paths = RunPaths.for_date(self.root, DATE_A)
        state.init_state(run_paths)

        def failing_fetch(url, timeout=None):
            raise OSError(f"cannot reach {url}")

        result = pipeline.run_collect(
            run_paths, mode="fixture", aihot_fixture=AIHOT_FIXTURE,
            rss_urls=["https://a.example.com/feed.xml", "https://b.example.com/feed.xml"],
            rss_fetch=failing_fetch)
        self.assertEqual(result["status"], "collected")
        self.assertEqual(result["rss_items"], 0)
        self.assertEqual(result["rss_failures"], 2)
        st = self.state_text()
        self.assertIn("- stage: topic_choice", st)
        self.assertIn("- status: in_progress", st)
        stats = json.loads((run_paths.work_dir / "rss-stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["feeds_failed"], 2)
        # machine-readable failure details must be persisted (UAT R2.2 jq check)
        self.assertIsInstance(stats.get("failures"), list)
        self.assertEqual(len(stats["failures"]), stats["feeds_failed"])
        self.assertEqual(
            {f["url"] for f in stats["failures"]},
            {"https://a.example.com/feed.xml", "https://b.example.com/feed.xml"},
        )
        for failure in stats["failures"]:
            self.assertTrue(failure["error"])
        # candidates still work off AIHOT evidence alone
        code, out, err = self.run_cli("candidates", "--root", str(self.root), "--date", DATE_A)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.count("## 候选 "), 3)


class OutlineEditTests(E2EBase):
    def test_outline_edit_changes_draft_without_recollect(self):
        self.step_chain(DATE_A)
        work = self.root / ".local" / "runs" / DATE_A
        draft_before = (work / "article.md").read_text(encoding="utf-8")
        outline_path = work / "article-outline.md"
        outline_text = outline_path.read_text(encoding="utf-8")
        self.assertIn("collect_runs: 1", self.state_text())

        # human edit: new section bullet + rewritten thesis (outline contract)
        new_thesis = "搜索预算正在成为 AI 创作的隐性主成本，个人创作者必须学会按问题付费。"
        old_thesis = "AI 智能体的成本重心正从模型调用转向搜索与检索预算，个人创作者第一次需要像团队一样管理研究成本。"
        self.assertIn(old_thesis, outline_text)
        edited = outline_text.replace(old_thesis, new_thesis)
        edited = edited.replace(
            "- 风险冷评：给读者的具体警告",
            "- 新增章节：读者的三个自检问题\n- 风险冷评：给读者的具体警告",
        )
        outline_path.write_text(edited, encoding="utf-8")

        code, out, err = self.run_cli("regenerate-outline", "--root", str(self.root), "--date", DATE_A)
        self.assertEqual(code, 0, err)
        draft_after = (work / "article.md").read_text(encoding="utf-8")
        self.assertNotEqual(draft_before, draft_after)
        self.assertIn("## 新增章节：读者的三个自检问题", draft_after)
        self.assertIn(new_thesis, draft_after)
        st = self.state_text()
        self.assertIn("collect_runs: 1", st)  # no re-collect
        self.assertIn("- stage: draft", st)


class ResumeStageTests(E2EBase):
    def test_research_and_draft_resume_without_recollect(self):
        for argv in (
            ["init", "--root", str(self.root), "--date", DATE_A],
            ["collect", "--root", str(self.root), "--date", DATE_A,
             "--mode", "fixture", "--aihot-fixture", AIHOT_FIXTURE],
            ["choose-topic", "--root", str(self.root), "--date", DATE_A,
             "--fixture", TOPIC_FIXTURE],
        ):
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 0, err)
        code, out, err = self.run_cli(
            "research", "--root", str(self.root), "--date", DATE_A,
            "--mode", "fixture",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("generated", out)
        code, out, err = self.run_cli(
            "research", "--root", str(self.root), "--date", DATE_A,
            "--mode", "fixture",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("resumed", out)
        self.run_cli("outline", "--root", str(self.root), "--date", DATE_A)
        work = self.root / ".local" / "runs" / DATE_A
        article = work / "article.md"
        self.assertFalse(article.exists())
        code, out, err = self.run_cli("draft", "--root", str(self.root), "--date", DATE_A)
        self.assertEqual(code, 0, err)
        self.assertIn("generated", out)
        draft_one = article.read_text(encoding="utf-8")
        code, out, err = self.run_cli("draft", "--root", str(self.root), "--date", DATE_A)
        self.assertEqual(code, 0, err)
        self.assertIn("resumed", out)
        self.assertEqual(draft_one, article.read_text(encoding="utf-8"))
        self.assertIn("collect_runs: 1", self.state_text())


if __name__ == "__main__":
    unittest.main()

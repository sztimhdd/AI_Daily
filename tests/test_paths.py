"""Tests for daily run path resolution and date isolation."""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import paths


class RunPathsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_run_id_is_stable_date_based(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.assertEqual(p.run_id, "AI-Daily/2026-08-12")

    def test_run_id_rejects_other_dates(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.assertNotIn("2026-08-11", p.run_id)

    def test_invalid_date_rejected(self):
        with self.assertRaises(paths.RunPathError):
            paths.RunPaths.for_date(self.root, "2026-8-12")
        with self.assertRaises(paths.RunPathError):
            paths.RunPaths.for_date(self.root, "not-a-date")

    def test_pre_selection_state_lives_in_local_runs(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.assertEqual(p.work_dir, self.root / ".local" / "runs" / "2026-08-12")
        self.assertEqual(p.state_file, p.work_dir / "state.md")

    def test_package_dir_is_nested_by_date_and_slug(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        pkg = p.package_dir("ai-search-budget-research-cost")
        self.assertEqual(
            pkg,
            self.root / "outputs" / "2026" / "08" / "12" / "ai-search-budget-research-cost",
        )

    def test_slug_must_be_kebab_case(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        with self.assertRaises(paths.RunPathError):
            p.package_dir("Not A Slug")
        with self.assertRaises(paths.RunPathError):
            p.package_dir("..")

    def test_final_article_path_convention(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        final = p.final_article_path("ai-search-budget-research-cost")
        self.assertEqual(
            final,
            self.root / "articles" / "2026-08-12-ai-search-budget-research-cost-zh.md",
        )

    def test_two_dates_do_not_share_directories(self):
        a = paths.RunPaths.for_date(self.root, "2026-08-12")
        b = paths.RunPaths.for_date(self.root, "2026-08-11")
        self.assertNotEqual(a.work_dir, b.work_dir)
        self.assertNotEqual(a.package_dir("same-slug"), b.package_dir("same-slug"))

    def test_ensure_creates_directories(self):
        p = paths.RunPaths.for_date(self.root, "2026-08-12")
        p.ensure_work_dir()
        self.assertTrue(p.work_dir.is_dir())


if __name__ == "__main__":
    unittest.main()

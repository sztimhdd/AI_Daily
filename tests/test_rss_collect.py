"""Tests for RSS collection: fetch, parse, filter, dedup, stats, pool."""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import rss_collect

FEEDS = pathlib.Path(__file__).resolve().parent / "fixtures" / "feeds"

NOW = "2026-08-12T12:00:00+00:00"


def make_fetcher(extra=None, failing=()):
    table = {
        "https://feeds.example.com/a": (FEEDS / "source_a.xml").read_bytes(),
        "https://feeds.example.com/b": (FEEDS / "source_b.xml").read_bytes(),
        "https://feeds.example.com/broken": (FEEDS / "source_invalid.xml").read_bytes(),
    }
    if extra:
        table.update(extra)

    def fetch(url, timeout):
        if url in failing:
            raise OSError(f"timeout fetching {url}")
        if url not in table:
            raise OSError(f"404 for {url}")
        return table[url]

    return fetch


class RssCollectTests(unittest.TestCase):
    def collect(self, urls, **kw):
        return rss_collect.collect(
            urls, fetch=make_fetcher(), now=NOW, window_hours=96, **kw
        )

    def test_parses_rss2_and_atom_items(self):
        result = self.collect(["https://feeds.example.com/a", "https://feeds.example.com/b"])
        titles = {it["title"] for it in result.items}
        self.assertIn("Agent search benchmarks show cost gap between engines", titles)
        self.assertIn("Unique story about research budgets for solo creators", titles)

    def test_time_filter_removes_old_items(self):
        result = self.collect(["https://feeds.example.com/a"])
        self.assertFalse(any("Old story" in it["title"] for it in result.items))

    def test_url_dedup_across_feeds_ignores_fragment(self):
        result = self.collect(["https://feeds.example.com/a", "https://feeds.example.com/b"])
        urls = [it["url"] for it in result.items]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(
            sum("agent-search-cost" in u for u in urls), 1,
            "duplicate URL across feeds must be collapsed",
        )

    def test_title_dedup_normalized(self):
        result = self.collect(["https://feeds.example.com/a", "https://feeds.example.com/b"])
        titles = [rss_collect.normalize_title(it["title"]) for it in result.items]
        self.assertEqual(len(titles), len(set(titles)))

    def test_failures_recorded_and_nonblocking(self):
        result = self.collect(
            [
                "https://feeds.example.com/a",
                "https://feeds.example.com/missing",
                "https://feeds.example.com/broken",
            ]
        )
        self.assertTrue(result.items, "healthy feed must still contribute")
        failed_urls = {f["url"] for f in result.failures}
        self.assertIn("https://feeds.example.com/missing", failed_urls)
        self.assertIn("https://feeds.example.com/broken", failed_urls)
        for f in result.failures:
            self.assertTrue(f["error"])

    def test_source_statistics(self):
        result = self.collect(["https://feeds.example.com/a", "https://feeds.example.com/b"])
        stats = result.stats
        self.assertEqual(stats["feeds_ok"], 2)
        self.assertEqual(stats["feeds_failed"], 0)
        self.assertGreaterEqual(stats["items_kept"], 3)
        self.assertGreaterEqual(stats["duplicates_removed"], 2)
        self.assertEqual(stats["failures"], [])

    def test_stats_carry_machine_readable_failure_details(self):
        result = self.collect(
            [
                "https://feeds.example.com/a",
                "https://feeds.example.com/broken",
                "https://feeds.example.com/missing",
            ]
        )
        stats = result.stats
        self.assertIsInstance(stats["failures"], list)
        failed = {f["url"]: f["error"] for f in stats["failures"]}
        self.assertIn("https://feeds.example.com/broken", failed)
        self.assertIn("https://feeds.example.com/missing", failed)
        self.assertIn("parse failed", failed["https://feeds.example.com/broken"])
        self.assertIn("fetch failed", failed["https://feeds.example.com/missing"])
        # counts must agree with the machine-readable failure list
        self.assertEqual(len(stats["failures"]), stats["feeds_failed"])
        self.assertEqual(
            stats["feeds_requested"], stats["feeds_ok"] + stats["feeds_failed"]
        )

    def test_pool_is_compressed(self):
        result = self.collect(["https://feeds.example.com/a", "https://feeds.example.com/b"])
        pool = rss_collect.compress_pool(result, max_per_source=1)
        for src in pool["sources"]:
            self.assertLessEqual(len(src["items"]), 1)
        self.assertEqual(pool["totals"]["items_kept"], result.stats["items_kept"])

    def test_pool_markdown_is_short_intelligence_summary(self):
        result = self.collect(["https://feeds.example.com/a", "https://feeds.example.com/b"])
        pool = rss_collect.compress_pool(result, max_per_source=2)
        md = rss_collect.pool_markdown(pool)
        self.assertIn("RSS", md)
        self.assertLess(len(md), 4000, "pool summary must stay compact for model reading")

    def test_empty_feed_list_is_not_an_error(self):
        result = self.collect([])
        self.assertEqual(result.items, [])
        self.assertEqual(result.stats["feeds_ok"], 0)




DC_URL = "https://feeds.example.com/dc"


def make_dc_fetcher():
    return make_fetcher(extra={DC_URL: (FEEDS / "source_dc.xml").read_bytes()})


class DcDateNamespaceTests(unittest.TestCase):
    """dc:date (Dublin Core) must be parsed with its XML namespace."""

    def collect(self):
        return rss_collect.collect([DC_URL], fetch=make_dc_fetcher(), now=NOW, window_hours=96)

    def test_dc_date_fresh_item_kept(self):
        result = self.collect()
        titles = {it["title"] for it in result.items}
        self.assertIn("Fresh story dated with dc namespace", titles)
        fresh = next(it for it in result.items if it["title"].startswith("Fresh"))
        self.assertTrue(fresh["published"].startswith("2026-08-12"))

    def test_dc_date_old_item_filtered_out(self):
        result = self.collect()
        self.assertFalse(any("Ancient" in it["title"] for it in result.items))
        self.assertGreaterEqual(result.stats["items_out_of_window"], 1)

    def test_undated_item_kept_flagged_and_counted(self):
        """Undocumented dates must not silently drop items: they are kept
        with an empty published field and tracked in stats."""
        result = self.collect()
        undated = [it for it in result.items if it["title"].startswith("Undated")]
        self.assertEqual(len(undated), 1)
        self.assertEqual(undated[0]["published"], "")
        self.assertEqual(result.stats["undated_items"], 1)


class StatsSemanticsTests(unittest.TestCase):
    def test_generator_urls_produce_correct_stats(self):
        urls = (u for u in ["https://feeds.example.com/a", "https://feeds.example.com/b"])
        result = rss_collect.collect(urls, fetch=make_fetcher(), now=NOW, window_hours=96)
        self.assertEqual(result.stats["feeds_requested"], 2)
        self.assertEqual(result.stats["feeds_ok"], 2)
        self.assertEqual(result.stats["feeds_failed"], 0)

    def test_feed_contribution_stats(self):
        result = rss_collect.collect(
            ["https://feeds.example.com/a", DC_URL],
            fetch=make_dc_fetcher(),
            now=NOW,
            window_hours=96,
        )
        by_feed = result.stats["by_feed"]
        self.assertEqual(by_feed[DC_URL], 2)  # fresh + undated kept, ancient filtered
        self.assertGreaterEqual(by_feed["https://feeds.example.com/a"], 1)

    def test_out_of_window_counts_include_pubdate_and_dc_date(self):
        result = rss_collect.collect(
            ["https://feeds.example.com/a", DC_URL],
            fetch=make_dc_fetcher(),
            now=NOW,
            window_hours=96,
        )
        self.assertEqual(result.stats["items_out_of_window"], 2)  # old-story + ancient


if __name__ == "__main__":
    unittest.main()

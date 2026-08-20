"""Tests for the unified fetch primitive (http / cdp / zhida lanes)."""

import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import fetch  # noqa: E402
from ai_daily.paths import RunPaths  # noqa: E402

SAMPLE_HTML = """<!doctype html>
<html><head>
<meta property="og:title" content="Test Article">
<meta property="og:description" content="A short summary of the article.">
<title>Fallback Title</title>
</head><body>
<h1>Test Article</h1>
<script>var unused = 1;</script>
<style>.x { color: red; }</style>
<p>Hello world. This is the body.</p>
</body></html>"""


class RouteLaneTests(unittest.TestCase):
    def test_walled_hosts_and_subdomains_route_to_cdp(self):
        for url in (
            "https://www.zhihu.com/question/1",
            "https://zhihu.com/people/someone",
            "https://zhuanlan.zhihu.com/p/123",
            "https://mp.weixin.qq.com/s/abc",
            "https://blog.mp.weixin.qq.com/x",
        ):
            with self.subTest(url=url):
                self.assertEqual(fetch.route_lane(url), "cdp")

    def test_public_hosts_route_to_http(self):
        for url in (
            "https://example.com/a",
            "https://blog.csdn.net/post/1",
            "https://www.weixin.qq.com/help",
            "http://localhost:8000/x",
        ):
            with self.subTest(url=url):
                self.assertEqual(fetch.route_lane(url), "http")


class HttpFetchTests(unittest.TestCase):
    def test_success_extracts_title_summary_and_sha(self):
        result = fetch.http_fetch(
            "https://example.com/a", fetch=lambda url, timeout: SAMPLE_HTML.encode()
        )
        self.assertEqual(result.status, "fetched")
        self.assertEqual(result.source_lane, "http")
        self.assertEqual(result.title, "Test Article")
        self.assertIn("A short summary of the article.", result.markdown)
        self.assertIn("Hello world. This is the body.", result.markdown)
        self.assertNotIn("var unused", result.markdown, "script bodies must be stripped")
        self.assertNotEqual(result.title, "Fallback Title")
        self.assertEqual(result.sha256, hashlib.sha256(result.markdown.encode()).hexdigest())
        self.assertEqual(result.error, "")

    def test_network_error_returns_failed_without_raising(self):
        def boom(url, timeout):
            raise OSError("connection refused")

        result = fetch.http_fetch("https://example.com/x", fetch=boom)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.source_lane, "http")
        self.assertTrue(result.error)
        self.assertIn("connection refused", result.error)

    def test_empty_body_returns_partial(self):
        result = fetch.http_fetch(
            "https://example.com/empty",
            fetch=lambda url, timeout: b"<html><head><title>hi</title></head><body></body></html>",
        )
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.markdown, "")


class CdpFetchTests(unittest.TestCase):
    def test_parses_runner_json_and_uses_saved_text(self):
        body = "这是正文第一段。\n这是正文第二段。"
        stdout = json.dumps(
            {
                "url": "https://mp.weixin.qq.com/s/abc",
                "title": "公众号标题",
                "status": "fetched",
                "text_chars": len(body),
                "text_preview": body[:300],
            },
            ensure_ascii=False,
        )

        def runner(url, out_dir, wait_ms):
            return stdout, f"# 公众号标题\n\n{body}\n"

        result = fetch.cdp_fetch("https://mp.weixin.qq.com/s/abc", runner=runner)
        self.assertEqual(result.status, "fetched")
        self.assertEqual(result.source_lane, "cdp")
        self.assertEqual(result.title, "公众号标题")
        self.assertEqual(result.markdown, body)
        self.assertEqual(result.sha256, hashlib.sha256(body.encode()).hexdigest())

    def test_uses_text_preview_when_no_saved_text(self):
        body = "预览正文内容。"
        stdout = json.dumps(
            {
                "url": "https://zhihu.com/question/1",
                "title": "t",
                "status": "partial",
                "text_chars": 0,
                "text_preview": body,
            },
            ensure_ascii=False,
        )
        result = fetch.cdp_fetch(
            "https://zhihu.com/question/1", runner=lambda url, out, wait: (stdout, "")
        )
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.markdown, body)

    def test_status_passed_through_unchanged(self):
        stdout = json.dumps(
            {
                "url": "https://zhihu.com/question/2",
                "title": "",
                "status": "login_required",
                "text_chars": 0,
                "text_preview": "",
            },
            ensure_ascii=False,
        )
        result = fetch.cdp_fetch(
            "https://zhihu.com/question/2", runner=lambda url, out, wait: (stdout, "")
        )
        self.assertEqual(result.status, "login_required")

    def test_runner_exception_returns_failed_without_raising(self):
        def runner(url, out_dir, wait_ms):
            raise subprocess.SubprocessError("chrome not reachable")

        result = fetch.cdp_fetch("https://zhihu.com/question/3", runner=runner)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.source_lane, "cdp")
        self.assertTrue(result.error)


class FetchTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.run_paths = RunPaths.for_date(self._tmp.name, "2026-08-14")

    def test_idempotent_reuse_after_first_fetch(self):
        calls = []

        def fetcher(url, timeout):
            calls.append(url)
            return SAMPLE_HTML.encode()

        first = fetch.fetch(
            "https://example.com/article", self.run_paths, http_fetcher=fetcher
        )
        self.assertEqual(first.status, "fetched")
        self.assertEqual(calls, ["https://example.com/article"])

        def boom(url, timeout):
            raise AssertionError("cached url must not be re-fetched")

        second = fetch.fetch(
            "https://example.com/article", self.run_paths, http_fetcher=boom
        )
        self.assertEqual(second.sha256, first.sha256)
        self.assertEqual(second.markdown, first.markdown)
        self.assertEqual(second.title, first.title)
        self.assertEqual(second.status, first.status)
        self.assertEqual(calls, ["https://example.com/article"], "must not re-fetch")

    def test_force_refetches_even_when_cached(self):
        calls = []

        def fetcher(url, timeout):
            calls.append(url)
            return SAMPLE_HTML.encode()

        fetch.fetch("https://example.com/f", self.run_paths, http_fetcher=fetcher)
        fetch.fetch(
            "https://example.com/f",
            self.run_paths,
            http_fetcher=fetcher,
            force=True,
        )
        self.assertEqual(len(calls), 2)

    def test_different_lanes_do_not_share_cache(self):
        # HTTP fetch of a walled URL must not shadow a later CDP fetch
        # of the same URL: the lane is part of the idempotency key.
        fetch.fetch(
            "https://www.zhihu.com/question/123",
            self.run_paths,
            lane="http",
            http_fetcher=lambda url, timeout: SAMPLE_HTML.encode(),
        )

        cdp_calls = []

        def cdp_runner(url, out_dir, wait_ms):
            cdp_calls.append(url)
            body = "zhihu cdp 正文"
            stdout = json.dumps(
                {
                    "url": url,
                    "title": "zhihu t",
                    "status": "fetched",
                    "text_preview": body,
                },
                ensure_ascii=False,
            )
            return stdout, f"# zhihu t\n\n{body}\n"

        result = fetch.fetch(
            "https://www.zhihu.com/question/123",
            self.run_paths,
            lane="cdp",
            cdp_runner=cdp_runner,
        )
        self.assertEqual(cdp_calls, ["https://www.zhihu.com/question/123"])
        self.assertEqual(result.source_lane, "cdp")
        self.assertIn("zhihu cdp 正文", result.markdown)

    def test_routing_walled_goes_cdp_public_goes_http(self):
        cdp_calls, http_calls = [], []

        def cdp_runner(url, out_dir, wait_ms):
            cdp_calls.append(url)
            body = "zhihu 正文"
            stdout = json.dumps(
                {
                    "url": url,
                    "title": "zhihu t",
                    "status": "fetched",
                    "text_chars": len(body),
                    "text_preview": body,
                },
                ensure_ascii=False,
            )
            return stdout, f"# zhihu t\n\n{body}\n"

        def http_fetcher(url, timeout):
            http_calls.append(url)
            return SAMPLE_HTML.encode()

        fetch.fetch(
            "https://www.zhihu.com/question/123",
            self.run_paths,
            cdp_runner=cdp_runner,
            http_fetcher=http_fetcher,
        )
        fetch.fetch(
            "https://example.com/open",
            self.run_paths,
            cdp_runner=cdp_runner,
            http_fetcher=http_fetcher,
        )
        self.assertEqual(cdp_calls, ["https://www.zhihu.com/question/123"])
        self.assertEqual(http_calls, ["https://example.com/open"])


class DiscoverTests(unittest.TestCase):
    def test_returns_zhihu_question_links_from_search_page(self):
        def runner(topic, wait_ms):
            self.assertEqual(topic, "AI 产品")
            return [
                {
                    "title": "如何评价最新的 AI 产品发布？",
                    "url": "https://www.zhihu.com/question/12345678",
                }
            ]

        items = fetch.discover("AI 产品", runner=runner)
        self.assertEqual(
            [item["url"] for item in items],
            ["https://www.zhihu.com/question/12345678"],
        )
        self.assertEqual(items[0]["title"], "如何评价最新的 AI 产品发布？")

    def test_no_links_returns_empty_list(self):
        items = fetch.discover("nothing", runner=lambda topic, wait_ms: [])
        self.assertEqual(items, [])

    def test_runner_failure_returns_empty_list(self):
        def boom(topic, wait_ms):
            raise RuntimeError("search script failed")

        self.assertEqual(fetch.discover("x", runner=boom), [])


class CliFetchTests(unittest.TestCase):
    def test_fetch_subcommand_prints_summary_and_preview(self):
        from ai_daily import cli

        fake = fetch.FetchResult(
            url="https://example.com/a",
            title="Example Title",
            markdown="第一行正文。\n第二行正文。",
            sha256="ab" * 32,
            status="fetched",
            source_lane="http",
        )
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("ai_daily.cli.fetch.fetch", return_value=fake) as patched:
            with redirect_stdout(out), redirect_stderr(err):
                code = cli.main(
                    [
                        "fetch",
                        "https://example.com/a",
                        "--root",
                        "/tmp",
                        "--date",
                        "2026-08-14",
                    ]
                )
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn(
            "fetch: fetched lane=http sha256=" + "ab" * 32 + " title=Example Title",
            out.getvalue(),
        )
        self.assertIn("第一行正文。\n第二行正文。", out.getvalue())
        url_arg, kwargs = patched.call_args
        self.assertEqual(url_arg[0], "https://example.com/a")
        self.assertIsNone(kwargs["lane"])


if __name__ == "__main__":
    unittest.main()

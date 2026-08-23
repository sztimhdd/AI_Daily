"""Tests for the official Zhihu CLI community-evidence lane."""

import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import zhihu_lane


def ok_search_payload():
    return {
        "ok": True,
        "items": [
            {
                "Title": "真实经历：我用 DeepSeek 跑生产",
                "AuthorName": "某工程师",
                "ContentText": "跑分没输过，实战没赢过……",
                "Url": "https://www.zhihu.com/question/1/answer/1",
            }
        ],
    }


class SearchZhihuTests(unittest.TestCase):
    def test_ok_payload_normalizes_items(self):
        result = zhihu_lane.search_zhihu(
            "DeepSeek 推理成本", count=5, runner=lambda args: ok_search_payload()
        )
        self.assertEqual(result["status"], "ok")
        item = result["items"][0]
        self.assertEqual(item["title"], "真实经历：我用 DeepSeek 跑生产")
        self.assertEqual(item["author"], "某工程师")
        self.assertEqual(item["url"], "https://www.zhihu.com/question/1/answer/1")
        self.assertIn("跑分没输过", item["content"])

    def test_auth_required_is_honest_unavailable(self):
        def runner(args):
            return {
                "ok": False,
                "error": {"code": "AUTH_REQUIRED",
                          "message": "请登录知乎开放平台并获取 Access Secret"},
            }

        result = zhihu_lane.search_zhihu("q", runner=runner)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("Access Secret", result["reason"])

    def test_missing_binary_is_unavailable_without_crash(self):
        with mock.patch.object(zhihu_lane, "_binary", return_value=None):
            result = zhihu_lane.search_zhihu("q")
        self.assertEqual(result["status"], "unavailable")

    def test_bad_json_is_unavailable(self):
        def runner(args):
            raise ValueError("bad json")

        result = zhihu_lane.search_zhihu("q", runner=runner)
        self.assertEqual(result["status"], "unavailable")


class HotTopicsTests(unittest.TestCase):
    def test_hot_payload_normalizes(self):
        def runner(args):
            return {
                "ok": True,
                "items": [{"Title": "热点一", "Url": "https://www.zhihu.com/question/9"}],
            }

        result = zhihu_lane.hot_topics(limit=3, runner=runner)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["items"][0]["title"], "热点一")

"""Tests for the official Zhihu CLI community-evidence lane."""

import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import zhihu_lane


def ok_search_payload():
    return {
        "Code": 0,
        "Message": "success",
        "Data": {
            "HasMore": False,
            "Items": [
                {
                    "Title": "真实经历：我用 DeepSeek 跑生产",
                    "ContentType": "Answer",
                    "AuthorName": "某工程师",
                    "ContentText": "跑分没输过，实战没赢过……",
                    "Url": "https://www.zhihu.com/question/1/answer/1",
                    "VoteUpCount": 172,
                    "CommentCount": 15,
                }
            ],
        },
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
        self.assertEqual(item["vote_up"], 172)
        self.assertEqual(item["comment_count"], 15)
        self.assertEqual(item["content_type"], "Answer")

    def test_auth_required_is_honest_unavailable(self):
        def runner(args):
            return {
                "Code": 401,
                "Message": "请登录知乎开放平台并获取 Access Secret",
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

    def test_rate_limit_retries_once_then_succeeds(self):
        calls = {"n": 0}

        def runner(args):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"Code": 30001, "Message": "rate limit exceeded",
                        "Data": None}
            return ok_search_payload()

        with mock.patch.object(zhihu_lane, "_RATE_LIMIT_RETRY_DELAY", 0.0):
            result = zhihu_lane.search_zhihu("q", runner=runner)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(calls["n"], 2)


class CommunityVoiceTests(unittest.TestCase):
    def test_community_voice_builds_topic_query_and_normalizes(self):
        topic = {
            "title": "Claude 多入口报错",
            "research_queries": ["Claude 宕机 企业影响"],
        }
        result = zhihu_lane.community_voice(topic, runner=lambda args: ok_search_payload())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query"], "Claude 多入口报错 Claude 宕机 企业影响")
        self.assertEqual(result["items"][0]["author"], "某工程师")
        self.assertEqual(result["items"][0]["vote_up"], 172)

    def test_community_voice_unavailable_never_raises(self):
        topic = {"title": "T"}
        result = zhihu_lane.community_voice(
            topic, runner=lambda args: {"Code": 401, "Message": "no auth"}
        )
        self.assertEqual(result["status"], "unavailable")

    def test_render_community_md_marks_secondary(self):
        data = {
            "topic": "T",
            "query": "q",
            "items": [{
                "title": "真实经历",
                "author": "某工程师",
                "vote_up": 172,
                "comment_count": 15,
                "content": "跑分没输过",
                "url": "https://www.zhihu.com/q/1/a/1",
                "content_type": "Answer",
            }],
            "reason": "",
        }
        md = zhihu_lane.render_community_md(data)
        self.assertIn("二手社区证据", md)
        self.assertIn("某工程师", md)
        self.assertIn("172", md)
        self.assertIn("zhihu.com", md)

    def test_rate_limit_persists_after_retry_is_unavailable(self):
        calls = {"n": 0}

        def runner(args):
            calls["n"] += 1
            return {"Code": 30001, "Message": "rate limit exceeded",
                    "Data": None}

        with mock.patch.object(zhihu_lane, "_RATE_LIMIT_RETRY_DELAY", 0.0):
            result = zhihu_lane.search_zhihu("q", runner=runner)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(calls["n"], 2)


class HotTopicsTests(unittest.TestCase):
    def test_hot_payload_normalizes(self):
        def runner(args):
            return {
                "Code": 0,
                "Message": "success",
                "Data": {
                    "Items": [
                        {"Title": "热点一",
                         "Url": "https://www.zhihu.com/question/9"},
                    ]
                },
            }

        result = zhihu_lane.hot_topics(limit=3, runner=runner)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["items"][0]["title"], "热点一")

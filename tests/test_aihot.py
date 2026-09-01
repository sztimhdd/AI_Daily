"""Tests for the AIHOT discovery input: fixture, live, failure-stop."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import aihot

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "aihot_items.json"
STORY_ID = "123e4567-e89b-12d3-a456-426614174000"
DEEPSEEK_STORY_ID = "3f2c9d1e-8a7b-4f6e-9d2c-1b5a7e9c3f21"


def hot_topics_payload():
    return {
        "schemaVersion": 1,
        "count": 2,
        "items": [
            {
                "rank": 1,
                "title": "DeepSeek Harness 到底是什么？",
                "summary": "DeepSeek Harness 与 V4 Pro 同期发布，社区实测讨论热烈。",
                "sourceCount": 8,
                "signalCount": 21,
                "sourceNames": ["量子位", "机器之心"],
                "latestAt": "2026-08-14T00:00:00Z",
                "links": {
                    "story": f"https://aihot.virxact.com/story/{DEEPSEEK_STORY_ID}"
                },
            },
            {
                "rank": 2,
                "title": "Google 发布 WikiProfile 基准测试",
                "sourceCount": 3,
                "signalCount": 5,
                "sourceNames": ["Google Research"],
                "latestAt": "2026-08-13T22:00:00Z",
                "links": {
                    "story": f"https://aihot.virxact.com/story/{STORY_ID}"
                },
            },
        ],
    }


def story_payload():
    return {
        "schemaVersion": 1,
        "story": {
            "title": "DeepSeek Harness 与 V4 Pro 发布",
            "digest": "DeepSeek 发布 V4 Pro 与配套 Harness 工具链，社区与媒体评价分化。",
            "latest": "段小草发布实测：初步用了用今天新发布的 V4 Pro + Harness。",
            "status": "active",
            "sourceCount": 8,
            "reports": [
                {
                    "title": "DeepSeek 官方发布 V4 Pro 与 Harness",
                    "summary": "官方发布说明。",
                    "source": {"name": "DeepSeek"},
                    "publishedAt": "2026-08-13T08:00:00Z",
                    "links": {
                        "original": "https://api-docs.deepseek.com/news/news0813",
                        "aihot": "https://aihot.virxact.com/items/r1",
                    },
                },
                {
                    "title": "如何评价 8 月 13 日发布的 DeepSeek Harness",
                    "summary": "知乎社区讨论。",
                    "source": {"name": "知乎"},
                    "publishedAt": "2026-08-13T12:00:00Z",
                    "links": {
                        "original": "https://www.zhihu.com/question/2071335529577239335",
                        "aihot": "https://aihot.virxact.com/items/r2",
                    },
                },
            ],
        },
    }


def routed_fetch(hot=None, story=None):
    """Fake AIHOT transport routing hot-topics and stories endpoints."""
    hot = hot or hot_topics_payload()
    story = story or story_payload()

    def fake_fetch(url, timeout):
        if url == f"{aihot.API_BASE}/hot-topics":
            return json.dumps(hot).encode("utf-8")
        if url.startswith(f"{aihot.API_BASE}/stories/"):
            return json.dumps(story).encode("utf-8")
        raise AssertionError(f"unexpected AIHOT url: {url}")

    return fake_fetch


class AihotFixtureTests(unittest.TestCase):
    def test_fixture_items_load_with_required_fields(self):
        items = aihot.load_fixture(FIXTURE)
        self.assertGreaterEqual(len(items), 3)
        for it in items:
            self.assertTrue(it["title"].strip())
            self.assertIn("aihot", it["links"])
            self.assertTrue(it["links"]["aihot"].startswith("https://"))

    def test_fixture_items_keep_source_and_summary(self):
        items = aihot.load_fixture(FIXTURE)
        self.assertTrue(all(it["source_name"] for it in items))
        self.assertTrue(any(it["summary"] for it in items))

    def test_missing_fixture_raises(self):
        with self.assertRaises(aihot.AihotError):
            aihot.load_fixture(pathlib.Path("/nonexistent/aihot.json"))


class AihotLiveTests(unittest.TestCase):
    def test_live_success_parses_items(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        def fake_fetch(url, timeout):
            return json.dumps(payload).encode("utf-8")

        items = aihot.fetch_live(fetch=fake_fetch)
        self.assertEqual(len(items), len(payload["items"]))

    def test_live_http_failure_raises_aihot_error(self):
        def broken_fetch(url, timeout):
            raise OSError("connection refused")

        with self.assertRaises(aihot.AihotError) as ctx:
            aihot.fetch_live(fetch=broken_fetch)
        self.assertIn("connection refused", str(ctx.exception))

    def test_live_bad_status_raises_aihot_error(self):
        def unauthorized(url, timeout):
            raise aihot.AihotHTTPError(401, "unauthorized")

        with self.assertRaises(aihot.AihotError):
            aihot.fetch_live(fetch=unauthorized)

    def test_live_invalid_json_raises_aihot_error(self):
        def garbage(url, timeout):
            return b"<html>not json</html>"

        with self.assertRaises(aihot.AihotError):
            aihot.fetch_live(fetch=garbage)

    def test_never_fabricates_items_on_failure(self):
        """Failure-stop: no training-memory fallback may invent news."""

        def broken_fetch(url, timeout):
            raise OSError("network unreachable")

        result = aihot.collect_items(mode="live", fetch=broken_fetch)
        self.assertEqual(result.items, [])
        self.assertFalse(result.ok)
        self.assertIn("network unreachable", result.error)




class AihotMalformedPayloadTests(unittest.TestCase):
    """Malformed payloads must become controlled failures, never escape."""

    def collect_live(self, body: bytes):
        def fetch(url, timeout):
            return body

        return aihot.collect_items(mode="live", fetch=fetch)

    def test_payload_not_a_dict_returns_failure_zero_items(self):
        result = self.collect_live(b"[1, 2, 3]")
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])
        self.assertTrue(result.error)

    def test_items_not_a_list_returns_failure_zero_items(self):
        result = self.collect_live(json.dumps({"items": "oops"}).encode("utf-8"))
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_missing_items_key_returns_failure_zero_items(self):
        result = self.collect_live(b"{}")
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_non_dict_item_entry_returns_failure_zero_items(self):
        body = json.dumps({"items": ["just a string"]}).encode("utf-8")
        result = self.collect_live(body)
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_wrong_typed_title_returns_failure_zero_items(self):
        body = json.dumps({"items": [{"title": 123}]}).encode("utf-8")
        result = self.collect_live(body)
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_source_string_is_normalized_not_crashed(self):
        body = json.dumps(
            {
                "items": [
                    {
                        "id": "x1",
                        "title": "Source string item",
                        "source": "Reuters Wire",
                        "links": {"aihot": "https://aihot.virxact.com/items/x1"},
                    }
                ]
            }
        ).encode("utf-8")
        result = self.collect_live(body)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.items[0]["source_name"], "Reuters Wire")

    def test_non_dict_links_field_does_not_escape(self):
        body = json.dumps(
            {
                "items": [
                    {
                        "id": "x2",
                        "title": "Bad links item",
                        "links": "https://aihot.virxact.com/items/x2",
                    }
                ]
            }
        ).encode("utf-8")
        result = self.collect_live(body)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.items[0]["links"]["aihot"], "")

    def test_malformed_fixture_returns_failure_zero_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            result = aihot.collect_items(mode="fixture", fixture_path=path)
        self.assertFalse(result.ok)
        self.assertEqual(result.items, [])

    def test_fetch_live_malformed_shapes_raise_aihot_error(self):
        for body in (b"[1,2]", b"{}", json.dumps({"items": {"a": 1}}).encode()):

            def fetch(url, timeout, body=body):
                return body

            with self.assertRaises(aihot.AihotError):
                aihot.fetch_live(fetch=fetch)


class StoryPublicIdTests(unittest.TestCase):
    """Story public ids are parsed strictly: no guessing, no partial matches."""

    def test_valid_story_url_extracts_uuid(self):
        url = f"https://aihot.virxact.com/story/{STORY_ID}"
        self.assertEqual(aihot.extract_story_public_id(url), STORY_ID)

    def test_invalid_story_urls_return_empty(self):
        urls = (
            f"https://aihot.virxact.com/story/{STORY_ID}/",
            f"https://aihot.virxact.com/story/{STORY_ID}/extra",
            f"https://aihot.virxact.com/story/{STORY_ID}?utm=x",
            "https://aihot.virxact.com/story/not-a-uuid",
            "https://aihot.virxact.com/story/",
            "https://aihot.virxact.com/items/cmsqgeo2e02cvroxvpnycl2zi",
            f"http://aihot.virxact.com/story/{STORY_ID}",
            f"https://evil.example.com/story/{STORY_ID}",
            f"https://aihot.virxact.com/story/{STORY_ID.upper()}",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(aihot.extract_story_public_id(url), "")

    def test_non_string_values_return_empty(self):
        for value in (None, 42, ["https://aihot.virxact.com/story/x"]):
            self.assertEqual(aihot.extract_story_public_id(value), "")


class HotTopicsTests(unittest.TestCase):
    def test_fetch_hot_topics_parses_ranked_items(self):
        items = aihot.fetch_hot_topics(fetch=routed_fetch())
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["rank"], 1)
        self.assertEqual(items[0]["title"], "DeepSeek Harness 到底是什么？")
        self.assertEqual(items[0]["source_count"], 8)
        self.assertEqual(
            items[0]["links"]["story"],
            f"https://aihot.virxact.com/story/{DEEPSEEK_STORY_ID}",
        )
        self.assertEqual(items[1]["rank"], 2)

    def test_fetch_hot_topics_http_failure_raises_aihot_error(self):
        def broken(url, timeout):
            raise aihot.AihotHTTPError(500, "boom")

        with self.assertRaises(aihot.AihotError):
            aihot.fetch_hot_topics(fetch=broken)

    def test_fetch_hot_topics_malformed_items_raises(self):
        def garbage(url, timeout):
            return json.dumps({"schemaVersion": 1, "count": 1, "items": "oops"}).encode()

        with self.assertRaises(aihot.AihotError):
            aihot.fetch_hot_topics(fetch=garbage)


class StoryReportTests(unittest.TestCase):
    REQUIRED_FIELDS = (
        "title",
        "summary",
        "source_name",
        "first_party",
        "published_at",
        "original_url",
        "aihot_url",
        "story_id",
        "story_title",
        "story_digest",
        "story_latest",
        "source_count",
        "report_count",
        "story_status",
    )

    def test_fetch_story_normalizes_reports_with_required_fields(self):
        result = aihot.fetch_story(DEEPSEEK_STORY_ID, fetch=routed_fetch())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["story_id"], DEEPSEEK_STORY_ID)
        self.assertEqual(result["story_title"], "DeepSeek Harness 与 V4 Pro 发布")
        self.assertEqual(result["story_status"], "active")
        self.assertEqual(result["source_count"], 8)
        self.assertEqual(result["report_count"], 2)
        self.assertEqual(result["reports"][0]["story_digest"], result["story_digest"])
        self.assertEqual(result["reports"][1]["story_latest"], result["story_latest"])
        for report in result["reports"]:
            for field in self.REQUIRED_FIELDS:
                self.assertIn(field, report, field)
        # first-party heuristic: DeepSeek / api-docs.deepseek.com -> 一手
        self.assertTrue(result["reports"][0]["first_party"])
        # 知乎社区转述 is not first-party
        self.assertFalse(result["reports"][1]["first_party"])
        self.assertEqual(
            result["reports"][0]["original_url"],
            "https://api-docs.deepseek.com/news/news0813",
        )

    def test_fetch_story_404_returns_unavailable_not_raise(self):
        def four_oh_four(url, timeout):
            raise aihot.AihotHTTPError(404, "not found")

        result = aihot.fetch_story(DEEPSEEK_STORY_ID, fetch=four_oh_four)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("404", result["reason"])
        self.assertEqual(result["story_id"], DEEPSEEK_STORY_ID)

    def test_fetch_story_network_error_returns_unavailable(self):
        def broken(url, timeout):
            raise OSError("connection refused")

        result = aihot.fetch_story(DEEPSEEK_STORY_ID, fetch=broken)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("connection refused", result["reason"])

    def test_fetch_story_non_json_returns_unavailable(self):
        def garbage(url, timeout):
            return b"<html>error page</html>"

        result = aihot.fetch_story(DEEPSEEK_STORY_ID, fetch=garbage)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("non-JSON", result["reason"])

    def test_fetch_story_missing_story_object_returns_unavailable(self):
        def empty(url, timeout):
            return json.dumps({"schemaVersion": 1}).encode()

        result = aihot.fetch_story(DEEPSEEK_STORY_ID, fetch=empty)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("no 'story' object", result["reason"])

    def test_fetch_story_invalid_id_never_calls_the_api(self):
        calls = []

        def spy(url, timeout):
            calls.append(url)
            raise AssertionError("invalid id must not reach the API")

        result = aihot.fetch_story("not-a-uuid", fetch=spy)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(calls, [])


class StoryMatrixTests(unittest.TestCase):
    def test_explicit_story_url_bypasses_expired_hot_topic_board(self):
        """A user-pinned AIHOT story remains usable after it leaves Top 10."""
        matrix = aihot.story_matrix_for_topic(
            "完全不同的自定义标题",
            fetch=routed_fetch(hot={
                "schemaVersion": 1,
                "count": 1,
                "items": [{
                    "rank": 1,
                    "title": "另一条仍在热榜的新闻",
                    "links": {
                        "story": f"https://aihot.virxact.com/story/{STORY_ID}"
                    },
                }],
            }),
            source_urls=[
                f"https://aihot.virxact.com/story/{DEEPSEEK_STORY_ID}"
            ],
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)

    def test_match_by_ascii_tokens_builds_ok_matrix(self):
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek Harness 发布", fetch=routed_fetch()
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)
        self.assertEqual(matrix["report_count"], 2)
        self.assertEqual(matrix["reports"][0]["story_id"], DEEPSEEK_STORY_ID)

    def test_match_by_exact_title_builds_ok_matrix(self):
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek Harness 到底是什么？", fetch=routed_fetch()
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)

    def test_match_by_source_url_takes_priority(self):
        source_urls = ["https://api-docs.deepseek.com/news/news0813"]
        board = hot_topics_payload()
        board["items"][0]["links"]["original"] = source_urls[0]
        matrix = aihot.story_matrix_for_topic(
            "无关标题", fetch=routed_fetch(hot=board), source_urls=source_urls
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)

    def test_no_match_returns_unavailable_without_guessing_story(self):
        matrix = aihot.story_matrix_for_topic(
            "AI 搜索预算与个人创作者的研究成本", fetch=routed_fetch()
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("no hot topic matches", matrix["reason"])
        self.assertNotIn("story_id", matrix)
        self.assertEqual(matrix.get("reports", []), [])

    def test_unrelated_hot_topic_story_is_not_force_attached(self):
        # The board has plenty of stories, but none matches the topic.
        board = hot_topics_payload()
        board["items"].append(
            {
                "rank": 3,
                "title": "Meta 开源 Muse Glimmer 登陆 OpenRouter",
                "sourceCount": 2,
                "signalCount": 4,
                "sourceNames": ["Meta"],
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        )
        matrix = aihot.story_matrix_for_topic(
            "个人创作者 AI 研究成本核算", fetch=routed_fetch(hot=board)
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertNotIn("story_id", matrix)

    def test_deepseek_v4_topic_not_matched_by_qwen_platform_story(self):
        # Live regression: "DeepSeek V4 Pro 登陆硅基流动，1M 上下文" was
        # attached to a Qwen story only because both share the 硅基流动
        # CJK bigrams.  With no shared identity tokens the topic must
        # stay unavailable instead of guessing a story id.
        board = hot_topics_payload()
        board["items"].append(
            {
                "rank": 10,
                "title": "Qwen3.8-2.4T-A95B 开源，硅基流动即日上线",
                "sourceCount": 2,
                "signalCount": 3,
                "sourceNames": ["X：硅基流动 SiliconFlow (@SiliconFlowAI)"],
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        )
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek V4 Pro 登陆硅基流动，1M 上下文",
            fetch=routed_fetch(hot=board),
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("no hot topic matches", matrix["reason"])
        self.assertNotIn("story_id", matrix)

    def test_deepseek_v4_topic_matches_deepseek_story_by_identity_tokens(self):
        # The live topic form must still match a DeepSeek story sharing
        # two+ identity tokens (deepseek + v4 + pro), even while the
        # 硅基流动 Qwen story is on the same board.
        board = hot_topics_payload()
        board["items"].append(
            {
                "rank": 10,
                "title": "Qwen3.8-2.4T-A95B 开源，硅基流动即日上线",
                "sourceCount": 2,
                "signalCount": 3,
                "sourceNames": ["X：硅基流动 SiliconFlow (@SiliconFlowAI)"],
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        )
        board["items"].append(
            {
                "rank": 3,
                "title": "DeepSeek V4 Pro 发布，1M 上下文窗口",
                "sourceCount": 8,
                "signalCount": 21,
                "sourceNames": ["量子位"],
                "links": {
                    "story": (
                        f"https://aihot.virxact.com/story/{DEEPSEEK_STORY_ID}"
                    )
                },
            }
        )
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek V4 Pro 登陆硅基流动，1M 上下文",
            fetch=routed_fetch(hot=board),
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)

    def test_deepseek_v4_exact_title_still_matches(self):
        board = hot_topics_payload()
        board["items"].append(
            {
                "rank": 10,
                "title": "Qwen3.8-2.4T-A95B 开源，硅基流动即日上线",
                "sourceCount": 2,
                "signalCount": 3,
                "sourceNames": ["X：硅基流动 SiliconFlow (@SiliconFlowAI)"],
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        )
        board["items"].append(
            {
                "rank": 3,
                "title": "DeepSeek V4 Pro 登陆硅基流动，1M 上下文",
                "sourceCount": 8,
                "signalCount": 21,
                "sourceNames": ["量子位"],
                "links": {
                    "story": (
                        f"https://aihot.virxact.com/story/{DEEPSEEK_STORY_ID}"
                    )
                },
            }
        )
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek V4 Pro 登陆硅基流动，1M 上下文",
            fetch=routed_fetch(hot=board),
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)

    def test_qwen_story_matches_by_single_fused_entity_token(self):
        # A fused product token (qwen3.8-2.4t-a95b) is distinctive enough
        # on its own under the entity rule.
        board = hot_topics_payload()
        board["items"].append(
            {
                "rank": 10,
                "title": "Qwen3.8-2.4T-A95B 开源，硅基流动即日上线",
                "sourceCount": 2,
                "signalCount": 3,
                "sourceNames": ["X：硅基流动 SiliconFlow (@SiliconFlowAI)"],
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        )
        matrix = aihot.story_matrix_for_topic(
            "Qwen3.8-2.4T-A95B 开源",
            fetch=routed_fetch(hot=board),
        )
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], STORY_ID)

    def test_single_generic_ascii_token_is_not_enough_to_match(self):
        # One shared generic word (deepseek) plus nothing else must not
        # decide the match when the rest of the topic is unrelated.
        board = hot_topics_payload()
        board["items"].append(
            {
                "rank": 4,
                "title": "DeepSeek 新模型悄然开源",
                "sourceCount": 2,
                "signalCount": 3,
                "sourceNames": ["量子位"],
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        )
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek V4 Pro 登陆硅基流动，1M 上下文",
            fetch=routed_fetch(hot=board),
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertNotIn("story_id", matrix)

    def test_matched_topic_without_story_link_returns_unavailable(self):
        board = {
            "schemaVersion": 1,
            "count": 1,
            "items": [
                {
                    "rank": 1,
                    "title": "DeepSeek Harness 到底是什么？",
                    "sourceCount": 8,
                    "signalCount": 21,
                    "sourceNames": ["量子位"],
                    "links": {},
                }
            ],
        }
        matrix = aihot.story_matrix_for_topic(
            "DeepSeek Harness 发布", fetch=routed_fetch(hot=board)
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("no valid story link", matrix["reason"])
        self.assertNotIn("story_id", matrix)

    def test_story_404_returns_unavailable_with_reason(self):
        def four_oh_four(url, timeout):
            if url == f"{aihot.API_BASE}/hot-topics":
                return json.dumps(hot_topics_payload()).encode()
            raise aihot.AihotHTTPError(404, "not found")

        matrix = aihot.story_matrix_for_topic(
            "DeepSeek Harness 发布", fetch=four_oh_four
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("404", matrix["reason"])
        self.assertEqual(matrix["story_id"], DEEPSEEK_STORY_ID)

    def test_hot_topics_failure_returns_unavailable(self):
        def broken(url, timeout):
            raise OSError("network unreachable")

        matrix = aihot.story_matrix_for_topic(
            "DeepSeek Harness 发布", fetch=broken
        )
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("hot-topics unavailable", matrix["reason"])


if __name__ == "__main__":
    unittest.main()

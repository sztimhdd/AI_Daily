"""Tests for V2 Initial Research: story matrix, active search, OSINT archive."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import aihot, paths, pipeline, research, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
STORY_ID = "123e4567-e89b-12d3-a456-426614174000"

SEVEN_MODULES = (
    "core_timeline",
    "finance_capital",
    "tech_engineering",
    "ecosystem_moat",
    "community_voices",
    "org_people",
    "editor_direction_check",
)


class _FakeKgClient:
    def synthesize(self, query, max_polls=8):
        return {"status": "completed", "report": "background"}

    def fts_search(self, query, limit=5, lang="zh-CN"):
        return "hit"


_FAKE_KG = _FakeKgClient()
_NO_ZHIHU = lambda args: {"Code": 401, "Message": "no auth"}


def hot_topics_payload():
    return {
        "schemaVersion": 1,
        "count": 1,
        "items": [
            {
                "rank": 1,
                "title": "AI 搜索预算与个人创作者的研究成本",
                "sourceCount": 4,
                "signalCount": 6,
                "sourceNames": ["AIHOT"],
                "latestAt": "2026-08-14T00:00:00Z",
                "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
            }
        ],
    }


def story_payload():
    return {
        "schemaVersion": 1,
        "story": {
            "title": "AI 搜索预算与研究成本",
            "digest": "深度研究产品的搜索调用成本成为关注重点。",
            "latest": "多款产品本周发布定价。",
            "status": "active",
            "sourceCount": 4,
            "reports": [
                {
                    "title": "OpenRouter 发布实时网页搜索基准测试",
                    "summary": "官方博客发布网页搜索基准，关注搜索调用成本与预算。",
                    "source": {"name": "OpenRouter"},
                    "publishedAt": "2026-08-13T10:00:00Z",
                    "links": {
                        "original": "https://openrouter.ai/blog/web-search-benchmark",
                        "aihot": "https://aihot.virxact.com/items/r1",
                    },
                },
                {
                    "title": "深度研究代理搜索预算定价",
                    "summary": "媒体报道定价与成本口径。",
                    "source": {"name": "量子位"},
                    "publishedAt": "2026-08-13T11:00:00Z",
                    "links": {
                        "original": "https://mp.weixin.qq.com/s/deep-research-pricing",
                        "aihot": "https://aihot.virxact.com/items/r2",
                    },
                },
            ],
        },
    }


def make_aihot_fetch(hot=None, story=None):
    """Fake AIHOT transport; both endpoints return canned payloads."""
    hot = hot if hot is not None else hot_topics_payload()
    story = story if story is not None else story_payload()

    def fake_fetch(url, timeout):
        if url == f"{aihot.API_BASE}/hot-topics":
            return json.dumps(hot).encode("utf-8")
        if url.startswith(f"{aihot.API_BASE}/stories/"):
            return json.dumps(story).encode("utf-8")
        raise AssertionError(f"unexpected AIHOT url: {url}")

    return fake_fetch


SAMPLE_HTML = (
    "<html><head>"
    '<meta property="og:title" content="OpenRouter 发布实时网页搜索基准测试">'
    '<meta property="og:description" content="官方博客发布网页搜索基准，'
    "关注搜索调用成本与预算。\"></head>"
    "<body><p>OpenRouter 今天发布实时网页搜索基准测试排行榜，覆盖搜索预算、"
    "定价与评测。工程团队公开了架构与基准数据。社区开发者反馈实测体验。</p>"
    "</body></html>"
)


def make_http_fetcher(body=SAMPLE_HTML):
    def fetcher(url, timeout):
        return body.encode("utf-8")

    return fetcher


def make_broken_http_fetcher():
    def broken(url, timeout):
        raise OSError("connection refused")

    return broken


def make_cdp_runner(status="fetched"):
    def runner(url, out_dir, wait_ms):
        data = {
            "status": status,
            "title": "深度研究代理搜索预算定价",
            "text_preview": "深度研究代理搜索预算定价正文，社区开发者实测反馈。",
        }
        return (
            json.dumps(data),
            "# 深度研究代理搜索预算定价\n\n"
            "深度研究代理搜索预算定价正文，社区开发者实测反馈。",
        )

    return runner


def make_codex_runner(seen=None, result=None):
    def runner(prompt):
        if seen is not None:
            seen.append(prompt)
        if result is not None:
            return result
        return {
            "status": "completed",
            "modules": [
                {
                    "key": "core_timeline",
                    "summary": "OpenRouter 于 8 月 13 日发布网页搜索基准测试。",
                    "gaps": [],
                }
            ],
            "evidence_gaps": ["需要第二来源验证报道中的定价数字。"],
        }

    return runner


class InitialResearchBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths = paths.RunPaths.for_date(self.root, "2026-08-14")
        self.paths.ensure_work_dir()
        state.init_state(self.paths)
        topics.choose_fixture(self.paths, FIXTURES / "topic_fixture.json")

    def tearDown(self):
        self._tmp.cleanup()

    def run_initial(self, **kwargs):
        class _FakeKgClient:
            def synthesize(self, query, max_polls=8):
                return {"status": "completed", "report": "background"}

            def fts_search(self, query, limit=5, lang="zh-CN"):
                return "hit"

        defaults = dict(
            aihot_fetch=make_aihot_fetch(),
            http_fetcher=make_http_fetcher(),
            cdp_runner=make_cdp_runner(),
            codex_runner=make_codex_runner(),
            kg_client=_FakeKgClient(),
            zhihu_runner=_NO_ZHIHU,
        )
        defaults.update(kwargs)
        return research.run_initial(self.paths, **defaults)

    def read_json(self, name):
        return json.loads((self.paths.work_dir / name).read_text(encoding="utf-8"))


class InitialResearchGateTests(InitialResearchBase):
    def test_run_initial_requires_topic_choice(self):
        fresh = paths.RunPaths.for_date(self.root, "2026-08-13")
        fresh.ensure_work_dir()
        state.init_state(fresh)
        with self.assertRaises(topics.TopicGateBlocked):
            research.run_initial(fresh, aihot_fetch=make_aihot_fetch())


class InitialResearchHappyPathTests(InitialResearchBase):
    def test_parse_codex_exec_stdout_accepts_real_item_completed_envelope(self):
        result_payload = json.dumps(
            {"status": "completed", "modules": [], "evidence_gaps": []},
            ensure_ascii=False,
        )
        events = "\n".join([
            '{"type":"turn.started"}',
            '{"type":"item.completed","item":{"id":"item_0",'
            '"type":"agent_message","text":'
            + json.dumps(result_payload)
            + "}}",
            '{"type":"turn.completed","usage":{"input_tokens":1}}',
        ])
        result = research._parse_codex_exec_stdout(events)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["modules"], [])

    def test_topic_source_urls_fill_evidence_when_matrix_has_no_reports(self):
        topic = {
            "sources": [
                {"url": "https://x.com/a", "origin": "aihot"},
                {"url": "https://example.com/b", "origin": "rss"},
            ],
            "research_queries": [],
        }
        matrix = {"status": "unavailable", "reports": []}
        urls = research._initial_url_list(topic, matrix)
        self.assertEqual(urls, ["https://x.com/a", "https://example.com/b"])

    def test_topic_source_urls_are_merged_when_matrix_has_reports(self):
        """Regression: when AIHOT matches a *different* story than the chosen
        topic, the chosen topic's own sources must still be fetched.  The
        matrix reports used to shadow topic.sources entirely, leaving the
        editor's chosen event without any evidence."""
        topic = {
            "sources": [
                {"url": "https://techcrunch.com/2026/08/26/nvidia-acquires-hf/"},
                {"url": "https://example.com/b"},
            ],
            "research_queries": [],
        }
        matrix = {
            "status": "ok",
            "reports": [
                {"original_url": "https://openai.com/index/hf-incident"},
                {"original_url": "https://x.com/frxiaobei/status/1"},
            ],
        }
        urls = research._initial_url_list(topic, matrix)
        # matrix reports first (existing behavior), topic sources merged in,
        # deduplicated, order stable.
        self.assertEqual(
            urls,
            [
                "https://openai.com/index/hf-incident",
                "https://x.com/frxiaobei/status/1",
                "https://techcrunch.com/2026/08/26/nvidia-acquires-hf/",
                "https://example.com/b",
            ],
        )

    def test_topic_sources_deduped_against_matrix_reports(self):
        topic = {
            "sources": [
                {"url": "https://openai.com/index/hf-incident"},
            ],
            "research_queries": [],
        }
        matrix = {
            "status": "ok",
            "reports": [
                {"original_url": "https://openai.com/index/hf-incident"},
            ],
        }
        urls = research._initial_url_list(topic, matrix)
        self.assertEqual(urls, ["https://openai.com/index/hf-incident"])

    def test_analysis_message_with_preamble_still_parses_json(self):
        analysis = {"modules": [], "evidence_gaps": ["gap"]}
        text = (
            "知识库说明：无额外格式要求。\n\n"
            + json.dumps(analysis, ensure_ascii=False)
            + "\n以上为档案。"
        )
        result = research._decode_json_text(text)
        self.assertEqual(result, analysis)

    def test_happy_path_writes_story_matrix(self):
        result = self.run_initial()
        self.assertEqual(result["status"], "generated")
        matrix = self.read_json("story-matrix.json")
        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["story_id"], STORY_ID)
        self.assertEqual(matrix["report_count"], 2)
        self.assertIn("reports", matrix)

    def test_happy_path_writes_initial_evidence_input_file(self):
        self.run_initial()
        evidence = self.read_json("initial-evidence.json")
        self.assertEqual(evidence["topic"]["title"], "AI 搜索预算与个人创作者的研究成本")
        self.assertEqual(len(evidence["sources"]), 2)
        self.assertEqual(evidence["story_matrix"]["status"], "ok")

    def test_osint_json_has_seven_modules_and_fetch_statuses(self):
        result = self.run_initial()
        self.assertEqual(result["analysis_status"], "completed")
        data = self.read_json("initial-osint.json")
        keys = [m["key"] for m in data["modules"]]
        for key in SEVEN_MODULES:
            self.assertIn(key, keys)
        self.assertEqual(data["sources"], data["sources"])
        self.assertEqual(
            {s["url"] for s in data["sources"]},
            {
                "https://openrouter.ai/blog/web-search-benchmark",
                "https://mp.weixin.qq.com/s/deep-research-pricing",
            },
        )
        self.assertTrue(all(s["status"] for s in data["sources"]))
        self.assertTrue(data["evidence_gaps"])
        # analysis summary merged into the archive
        core = next(m for m in data["modules"] if m["key"] == "core_timeline")
        self.assertEqual(
            core["summary"], "OpenRouter 于 8 月 13 日发布网页搜索基准测试。"
        )

    def test_osint_md_is_human_readable_with_modules_and_statuses(self):
        self.run_initial()
        md = (self.paths.work_dir / "initial-osint.md").read_text(encoding="utf-8")
        self.assertIn("# Initial OSINT：", md)
        self.assertIn("## 七模块情报档案", md)
        for title in (
            "核心事实与时间线",
            "财务与资本账本",
            "技术架构与工程实锤",
            "生态博弈与护城河",
            "社区原声与野生实操",
            "组织动荡与人事",
            "主编定向指令核查",
        ):
            self.assertIn(title, md)
        self.assertIn("## 证据缺口", md)
        self.assertIn("## 来源与抓取状态", md)
        self.assertIn("status=fetched", md)
        self.assertIn("https://openrouter.ai/blog/web-search-benchmark", md)
        self.assertIn("摘要：无", md)

    def test_fetched_urls_come_only_from_story_reports(self):
        self.run_initial()
        data = self.read_json("initial-osint.json")
        report_urls = {
            r["original_url"]
            for r in data["story_matrix"].get("reports", [])
            if r.get("original_url")
        }
        fetched = {s["url"] for s in data["sources"]}
        self.assertTrue(fetched)
        self.assertTrue(fetched <= report_urls, f"invented urls: {fetched - report_urls}")

    def test_codex_runner_receives_matrix_and_evidence_prompt(self):
        seen = []
        self.run_initial(codex_runner=make_codex_runner(seen=seen))
        self.assertEqual(len(seen), 1)
        self.assertIn("story matrix", seen[0])
        self.assertIn("抓取证据", seen[0])
        self.assertIn(STORY_ID, seen[0])
        self.assertIn("https://openrouter.ai/blog/web-search-benchmark", seen[0])

    def test_discover_runner_adds_query_driven_urls(self):
        def discover(topic, wait_ms):
            return [{"title": "问题", "url": "https://www.zhihu.com/question/42"}]

        result = self.run_initial(discover_runner=discover)
        self.assertEqual(result["fetched"], 3)
        data = self.read_json("initial-osint.json")
        urls = {s["url"] for s in data["sources"]}
        self.assertIn("https://www.zhihu.com/question/42", urls)

    def test_pipeline_run_initial_research_forwards_fakes(self):
        result = pipeline.run_initial_research(
            self.paths,
            aihot_fetch=make_aihot_fetch(),
            http_fetcher=make_http_fetcher(),
            cdp_runner=make_cdp_runner(),
            codex_runner=make_codex_runner(),
            kg_client=_FAKE_KG,
            zhihu_runner=_NO_ZHIHU,
        )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(
            state.read_state(self.paths)["stage"], "research"
        )

    def test_progress_receives_matrix_evidence_and_analysis_events_in_order(self):
        events = []

        def progress(kind, payload):
            events.append((kind, payload))

        result = self.run_initial(progress=progress)
        kinds = [kind for kind, _ in events]
        self.assertEqual(kinds, ["matrix", "evidence", "analysis_start", "analysis_done"])
        self.assertEqual(events[0][1]["status"], "ok")
        self.assertEqual(len(events[1][1]), 2)
        self.assertEqual(events[2][1], {})
        self.assertEqual(events[3][1]["status"], "completed")
        self.assertEqual(result["status"], "generated")

    def test_pipeline_forwards_progress_callback(self):
        events = []

        def progress(kind, payload):
            events.append(kind)

        pipeline.run_initial_research(
            self.paths,
            aihot_fetch=make_aihot_fetch(),
            http_fetcher=make_http_fetcher(),
            cdp_runner=make_cdp_runner(),
            codex_runner=make_codex_runner(),
            progress=progress,
            kg_client=_FAKE_KG,
            zhihu_runner=_NO_ZHIHU,
        )
        self.assertEqual(events, ["matrix", "evidence", "analysis_start", "analysis_done"])


class InitialResearchUnavailableTests(InitialResearchBase):
    def test_no_hot_topic_match_records_unavailable_without_story(self):
        board = {
            "schemaVersion": 1,
            "count": 1,
            "items": [
                {
                    "rank": 1,
                    "title": "Meta 开源 Muse Glimmer 登陆 OpenRouter",
                    "sourceCount": 2,
                    "signalCount": 4,
                    "sourceNames": ["Meta"],
                    "links": {"story": f"https://aihot.virxact.com/story/{STORY_ID}"},
                }
            ],
        }
        result = self.run_initial(aihot_fetch=make_aihot_fetch(hot=board))
        matrix = self.read_json("story-matrix.json")
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("no hot topic matches", matrix["reason"])
        self.assertNotIn("story_id", matrix)
        data = self.read_json("initial-osint.json")
        self.assertEqual(data["analysis_status"], "completed")  # codex still ran
        self.assertTrue(
            any("story matrix unavailable" in g for g in data["evidence_gaps"])
        )
        self.assertEqual(data["sources"], [])
        for mod in data["modules"]:
            self.assertEqual(mod["evidence"], [])
            self.assertEqual(mod["summary"], "无")

    def test_matched_topic_without_story_link_is_unavailable(self):
        board = {
            "schemaVersion": 1,
            "count": 1,
            "items": [
                {
                    "rank": 1,
                    "title": "AI 搜索预算与个人创作者的研究成本",
                    "sourceCount": 4,
                    "signalCount": 6,
                    "sourceNames": ["AIHOT"],
                    "links": {},
                }
            ],
        }
        self.run_initial(aihot_fetch=make_aihot_fetch(hot=board))
        matrix = self.read_json("story-matrix.json")
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("no valid story link", matrix["reason"])

    def test_story_404_records_unavailable_without_fabrication(self):
        def four_oh_four(url, timeout):
            if url == f"{aihot.API_BASE}/hot-topics":
                return json.dumps(hot_topics_payload()).encode("utf-8")
            raise aihot.AihotHTTPError(404, "not found")

        self.run_initial(aihot_fetch=four_oh_four)
        matrix = self.read_json("story-matrix.json")
        self.assertEqual(matrix["status"], "unavailable")
        self.assertIn("404", matrix["reason"])
        data = self.read_json("initial-osint.json")
        self.assertEqual(data["sources"], [])

    def test_fetch_failure_recorded_as_gap_not_fabricated(self):
        result = self.run_initial(http_fetcher=make_broken_http_fetcher())
        self.assertEqual(result["fetched"], 2)
        data = self.read_json("initial-osint.json")
        statuses = {s["url"]: s["status"] for s in data["sources"]}
        self.assertEqual(
            statuses["https://openrouter.ai/blog/web-search-benchmark"], "failed"
        )
        # the walled URL still used the injected (healthy) cdp lane
        self.assertEqual(
            statuses["https://mp.weixin.qq.com/s/deep-research-pricing"], "fetched"
        )
        self.assertTrue(
            any(
                "https://openrouter.ai/blog/web-search-benchmark 抓取failed" in g
                for g in data["evidence_gaps"]
            ),
            data["evidence_gaps"],
        )
        md = (self.paths.work_dir / "initial-osint.md").read_text(encoding="utf-8")
        self.assertIn("status=failed", md)

    def test_cdp_lane_failure_status_passes_through(self):
        result = self.run_initial(cdp_runner=make_cdp_runner(status="login_required"))
        data = self.read_json("initial-osint.json")
        statuses = {s["url"]: s["status"] for s in data["sources"]}
        self.assertEqual(statuses["https://mp.weixin.qq.com/s/deep-research-pricing"], "login_required")
        self.assertTrue(any("抓取login_required" in g for g in data["evidence_gaps"]))


class InitialResearchAnalysisTests(InitialResearchBase):
    def test_codex_unavailable_keeps_honest_analysis_status(self):
        result = self.run_initial(
            codex_runner=make_codex_runner(
                result={"status": "unavailable", "reason": "codex exec not installed"}
            )
        )
        self.assertEqual(result["analysis_status"], "unavailable")
        data = self.read_json("initial-osint.json")
        self.assertEqual(data["analysis_status"], "unavailable")
        self.assertIn("codex exec not installed", data["analysis_reason"])
        # modules keep the honest placeholder instead of fake analysis
        core = next(m for m in data["modules"] if m["key"] == "core_timeline")
        self.assertNotEqual(core["summary"], "OpenRouter 于 8 月 13 日发布网页搜索基准测试。")

    def test_codex_runner_raising_records_unavailable(self):
        def boom(prompt):
            raise RuntimeError("codex crashed")

        result = self.run_initial(codex_runner=boom)
        self.assertEqual(result["analysis_status"], "unavailable")
        data = self.read_json("initial-osint.json")
        self.assertIn("codex analysis failed", data["analysis_reason"])
        self.assertTrue(data["sources"])

    def test_analysis_gaps_are_merged_into_the_archive(self):
        self.run_initial()
        data = self.read_json("initial-osint.json")
        self.assertIn("需要第二来源验证报道中的定价数字。", data["evidence_gaps"])


class InitialResearchResumeTests(InitialResearchBase):
    def test_resume_skips_rework_and_preserves_artifacts(self):
        calls = {"aihot": 0}
        original = make_aihot_fetch()

        def counting_fetch(url, timeout):
            calls["aihot"] += 1
            return original(url, timeout)

        first = self.run_initial(aihot_fetch=counting_fetch)
        before = (self.paths.work_dir / "initial-osint.json").read_bytes()
        self.assertEqual(calls["aihot"], 2)  # hot-topics + story

        second = self.run_initial(aihot_fetch=counting_fetch)
        self.assertEqual(second["status"], "resumed")
        self.assertEqual(calls["aihot"], 2, "resume must not re-fetch")
        self.assertEqual(
            (self.paths.work_dir / "initial-osint.json").read_bytes(), before
        )

    def test_resume_refuses_stale_osint_for_a_different_topic(self):
        # A leftover OSINT archive from another topic must never silently
        # resume: it would feed the wrong topic's evidence downstream.
        stale = {
            "run_id": "AI-Daily/2026-08-14",
            "date": "2026-08-14",
            "topic_title": "别的选题：GLM-5.3 后训练",
            "slug": "glm-53-post-train",
            "analysis_status": "completed",
            "analysis_reason": "",
            "story_matrix": {},
            "modules": [],
            "evidence_gaps": [],
            "research_queries": [],
            "sources": [{"url": "https://example.com/glm", "title": "GLM",
                         "status": "fetched"}],
        }
        (self.paths.work_dir / "initial-osint.json").write_text(
            json.dumps(stale, ensure_ascii=False), encoding="utf-8"
        )
        (self.paths.work_dir / "initial-osint.md").write_text(
            "# stale\n", encoding="utf-8"
        )

        result = self.run_initial()
        self.assertNotEqual(result["status"], "resumed")
        data = self.read_json("initial-osint.json")
        self.assertEqual(data["topic_title"], "AI 搜索预算与个人创作者的研究成本")

    def test_force_regenerates_artifacts(self):
        calls = {"aihot": 0}
        original = make_aihot_fetch()

        def counting_fetch(url, timeout):
            calls["aihot"] += 1
            return original(url, timeout)

        self.run_initial(aihot_fetch=counting_fetch)
        result = self.run_initial(aihot_fetch=counting_fetch, force=True)
        self.assertEqual(result["status"], "generated")
        self.assertEqual(calls["aihot"], 4)


class CodexExecOutputParseTests(unittest.TestCase):
    """Pure-function regression tests for the codex exec JSONL event stream."""

    def test_jsonl_event_stream_returns_final_json_message(self):
        analysis = {
            "modules": [{"key": "core_timeline", "summary": "发布事实"}],
            "evidence_gaps": [],
        }
        stdout = "\n".join(
            [
                "this line is not JSON",
                '{"type":"log","payload":{"message":"starting codex run"}}',
                (
                    '{"type":"agent_message","payload":{"id":"m1",'
                    '"sender":"assistant","text":"looking up sources"}}'
                ),
                '{"type":"item.completed","item":{"id":"item_0",'
                '"type":"agent_message","text":' + json.dumps(json.dumps(analysis)) + '}}',
            ]
        )
        self.assertEqual(research._parse_codex_exec_stdout(stdout), analysis)

    def test_last_agent_message_payload_text_wins(self):
        analysis = {"modules": [], "evidence_gaps": ["gap"]}
        stdout = "\n".join(
            [
                '{"type":"log","payload":{"message":"boot"}}',
                (
                    '{"type":"agent_message","payload":{"id":"m1",'
                    '"sender":"assistant","text":"not json"}}'
                ),
                json.dumps(
                    {
                        "type": "agent_message",
                        "payload": {
                            "id": "m2",
                            "sender": "assistant",
                            "text": json.dumps(analysis),
                        },
                    }
                ),
            ]
        )
        self.assertEqual(research._parse_codex_exec_stdout(stdout), analysis)

    def test_double_encoded_json_message_is_unwrapped(self):
        analysis = {"modules": [], "evidence_gaps": []}
        text = json.dumps(json.dumps(analysis))
        stdout = json.dumps(
            {
                "type": "agent_message",
                "payload": {"id": "m1", "sender": "assistant", "text": text},
            }
        )
        self.assertEqual(research._parse_codex_exec_stdout(stdout), analysis)

    def test_legacy_single_json_object_is_accepted(self):
        result = {"status": "completed", "modules": [], "evidence_gaps": []}
        self.assertEqual(
            research._parse_codex_exec_stdout(json.dumps(result)), result
        )

    def test_non_json_final_message_returns_unavailable_with_reason(self):
        stdout = "\n".join(
            [
                '{"type":"log","payload":{"message":"boot"}}',
                (
                    '{"type":"agent_message","payload":{"id":"m1",'
                    '"sender":"assistant","text":"抱歉，无法输出 JSON"}}'
                ),
            ]
        )
        result = research._parse_codex_exec_stdout(stdout)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("final message is not JSON", result["reason"])
        self.assertIn("抱歉", result["reason"])

    def test_garbage_stdout_returns_unavailable(self):
        result = research._parse_codex_exec_stdout("not json\nmore garbage\n")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("no usable JSON output", result["reason"])

    def test_run_error_event_returns_unavailable_with_message(self):
        stdout = "\n".join(
            [
                '{"type":"log","payload":{"message":"boot"}}',
                '{"type":"run_error","payload":{"message":"API quota exceeded"}}',
            ]
        )
        result = research._parse_codex_exec_stdout(stdout)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("run error: API quota exceeded", result["reason"])

    def test_default_codex_runner_parses_jsonl_events(self):
        analysis = {"modules": [], "evidence_gaps": []}
        stdout = "\n".join(
            [
                '{"type":"log","payload":{"message":"boot"}}',
                '{"type":"item.completed","item":{"id":"item_0",'
                '"type":"agent_message","text":' + json.dumps(json.dumps(analysis)) + '}}',
            ]
        )
        with mock.patch(
            "ai_daily.research.subprocess.run",
            return_value=mock.Mock(returncode=0, stdout=stdout, stderr=""),
        ):
            result = research._default_codex_runner("prompt")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["modules"], [])

    def test_default_codex_runner_preserves_unavailable_on_garbage(self):
        with mock.patch(
            "ai_daily.research.subprocess.run",
            return_value=mock.Mock(returncode=0, stdout="garbage\n", stderr=""),
        ):
            result = research._default_codex_runner("prompt")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("no usable JSON output", result["reason"])

    def test_default_codex_runner_uses_fallback_binary_when_off_path(self):
        with mock.patch(
            "ai_daily.research.shutil.which", return_value=None
        ), mock.patch(
            "ai_daily.research.subprocess.run",
            return_value=mock.Mock(
                returncode=0, stdout='{"status":"completed"}', stderr=""
            ),
        ) as run:
            result = research._default_codex_runner("prompt")
        self.assertEqual(result["status"], "completed")
        argv0 = run.call_args.args[0][0]
        self.assertEqual(
            argv0, "/Applications/ChatGPT.app/Contents/Resources/codex"
        )


class CodexPromptContractTests(unittest.TestCase):
    def _topic(self):
        return {
            "title": "某事件",
            "direction": "",
            "research_queries": ["成本 预算 定价 口径"],
        }

    def test_prompt_includes_research_contract_rules(self):
        prompt = research._codex_prompt(
            self._topic(), {"status": "ok"}, []
        )
        self.assertIn("证据层级", prompt)
        self.assertIn("引用协议", prompt)
        self.assertIn("冲突", prompt)
        self.assertIn("零捏造", prompt)

    def test_prompt_includes_temporal_red_line_and_current_date(self):
        prompt = research._codex_prompt(
            self._topic(), {"status": "ok"}, []
        )
        self.assertIn("时间红线", prompt)
        self.assertIn("当前系统时间", prompt)
        self.assertIn("[时间未披露]", prompt)

    def test_prompt_includes_research_queries_and_raw_data_rules(self):
        prompt = research._codex_prompt(
            self._topic(), {"status": "ok"}, []
        )
        self.assertIn("成本 预算 定价 口径", prompt)
        self.assertIn("数据零压缩", prompt)
        self.assertIn("微观场景", prompt)


if __name__ == "__main__":
    unittest.main()

"""Tests for topic candidate generation and the human gate."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import paths, state, topics

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def aihot_items():
    payload = json.loads((FIXTURES / "aihot_items.json").read_text(encoding="utf-8"))
    from ai_daily import aihot

    return aihot._normalize(payload["items"])


class CandidateGenerationTests(unittest.TestCase):
    def test_exactly_three_candidates(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        self.assertEqual(len(cands), 3)

    def test_candidates_have_required_editorial_fields(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        for c in cands:
            for field in (
                "title",
                "thesis",
                "hook",
                "evidence_gaps",
                "research_queries",
                "strategic_relevance",
                "sources",
            ):
                self.assertTrue(c[field], f"missing {field} in {c['title']}")
            self.assertTrue(c["sources"][0]["url"].startswith("http"))

    def test_candidates_are_distinct_events(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        titles = {topics.normalize_title(c["title"]) for c in cands}
        self.assertEqual(len(titles), 3)

    def test_duplicate_event_across_aihot_and_rss_counted_once(self):
        rss_dup = [
            {
                "title": aihot_items()[0]["title"],
                "url": "https://elsewhere.example.com/same-story",
                "published": "",
                "summary": "",
                "feed": "https://feeds.example.com/x",
                "origin": "rss",
            }
        ]
        cands = topics.generate_candidates(aihot_items(), rss_items=rss_dup)
        titles = [c["title"] for c in cands]
        self.assertEqual(len(titles), len(set(map(topics.normalize_title, titles))))
        # the merged candidate should carry sources from both origins
        merged = next(c for c in cands if any(
            s["url"] == "https://elsewhere.example.com/same-story" for s in c["sources"]
        ))
        self.assertTrue(any(s["origin"] == "aihot" for s in merged["sources"]))
        self.assertTrue(any(s["origin"] == "rss" for s in merged["sources"]))

    def multi_source_candidates(self):
        rss_dup = [
            {
                "title": aihot_items()[0]["title"],
                "url": "https://elsewhere.example.com/same-story",
                "published": "",
                "summary": "",
                "feed": "https://feeds.example.com/x",
                "origin": "rss",
            }
        ]
        cands = topics.generate_candidates(aihot_items(), rss_items=rss_dup)
        merged = next(
            c for c in cands
            if any(s["url"] == "https://elsewhere.example.com/same-story"
                   for s in c["sources"])
        )
        return cands, merged

    def test_multi_source_cluster_gap_does_not_claim_missing_second_source(self):
        _, merged = self.multi_source_candidates()
        self.assertGreaterEqual(len(merged["sources"]), 2)
        for gap in merged["evidence_gaps"]:
            self.assertNotIn("缺少独立的第二来源", gap)
        self.assertTrue(
            any("交叉核对" in gap for gap in merged["evidence_gaps"]),
            merged["evidence_gaps"],
        )

    def test_single_source_cluster_gap_still_flags_missing_second_source(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        for cand in cands:
            self.assertTrue(
                any("缺少独立的第二来源验证" in gap for gap in cand["evidence_gaps"]),
                cand["title"],
            )

    def test_strategic_relevance_outranks_pure_popularity(self):
        popular = {
            "id": "p1",
            "title": "某明星用 AI 换脸拍短视频走红",
            "summary": "娱乐新闻，热度很高但与企业决策无关。",
            "source_name": "Hot News",
            "links": {"aihot": "https://aihot.virxact.com/items/p1", "original": ""},
            "score": 99,
            "origin": "aihot",
        }
        strategic = {
            "id": "s1",
            "title": "主流推理 API 调整按 Token 计费价格",
            "summary": "多家推理服务商调整定价，企业推理成本结构将重算。",
            "source_name": "Vendor Blog",
            "links": {"aihot": "https://aihot.virxact.com/items/s1", "original": ""},
            "score": 5,
            "origin": "aihot",
        }
        filler = [
            {
                "id": f"f{i}",
                "title": f"地方展会发布新款智能硬件 {i}",
                "summary": "普通产品发布。",
                "source_name": "Media",
                "links": {"aihot": f"https://aihot.virxact.com/items/f{i}", "original": ""},
                "score": 3,
                "origin": "aihot",
            }
            for i in range(4)
        ]
        cands = topics.generate_candidates([popular, strategic] + filler, rss_items=[])
        titles = [c["title"] for c in cands]
        self.assertIn("主流推理 API 调整按 Token 计费价格", titles)
        self.assertNotIn("某明星用 AI 换脸拍短视频走红", titles)

    def test_candidates_markdown_lists_three_options(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        md = topics.candidates_markdown("2026-08-12", cands)
        self.assertIn("选题候选", md)
        self.assertEqual(md.count("## 候选"), 3)


def _pool_item(title, summary="", source="S", origin="aihot", score=80,
               url="https://example.com/x", idx="x"):
    return {
        "id": idx,
        "title": title,
        "summary": summary,
        "source_name": source,
        "links": {"aihot": f"https://aihot.virxact.com/items/{idx}", "original": url},
        "score": score,
        "origin": origin,
    }


def _rss_item(title, source, url, summary=""):
    return {
        "title": title,
        "summary": summary,
        "url": url,
        "published": "",
        "feed": source,
        "origin": "rss",
        "score": 60,
    }


class EditorialVetoTests(unittest.TestCase):
    def test_pr_release_wording_vetoed(self):
        text = "某公司与某巨头达成战略合作，强强联合共同赋能行业智能化升级"
        self.assertIsNotNone(topics.veto_reason(text))

    def test_routine_funding_vetoed(self):
        text = "某 AI 创业公司完成 5000 万美元 A 轮融资，由某基金领投"
        self.assertIsNotNone(topics.veto_reason(text))

    def test_benchmark_only_update_vetoed(self):
        text = "某模型在 MMLU 基准测试上超越 GPT-5，跑分刷新纪录"
        self.assertIsNotNone(topics.veto_reason(text))

    def test_dull_item_is_not_vetoed_by_keywords(self):
        text = "今天天气不错，适合写代码"
        self.assertIsNone(topics.veto_reason(text))

    def test_real_launch_with_hard_facts_survives(self):
        text = "DeepSeek V4 Pro 正式版上线，支持 1M 上下文，MIT 开源，API 定价公布"
        self.assertIsNone(topics.veto_reason(text))

    def test_strategic_funding_with_hard_signal_survives(self):
        text = "某公司完成 10 亿美元融资，用于建设自研 AI 数据中心与算力集群"
        self.assertIsNone(topics.veto_reason(text))


class EicScoreTests(unittest.TestCase):
    def test_info_asymmetry_keywords_score(self):
        info, _, _ = topics.eic_scores("独家：某厂商未披露的内部定价表泄露，首次曝光")
        self.assertGreater(info, 0)

    def test_emotional_trigger_keywords_score(self):
        _, emotion, _ = topics.eic_scores(
            "开发者炸锅：新定价让中小企业被淘汰，引发普遍焦虑"
        )
        self.assertGreater(emotion, 0)

    def test_dull_text_scores_zero(self):
        self.assertEqual(topics.eic_scores("今天天气不错"), (0, 0, 0))


class CandidateGateTests(unittest.TestCase):
    def test_multisource_clusters_preferred_when_supply_allows(self):
        pool = [_pool_item("独家热点事件", "独家内容，热度极高", score=99, idx="hot")]
        for i in range(3):
            title = f"多源战略事件{i}"
            pool.append(_pool_item(title, "战略架构与定价", score=70, idx=f"a{i}"))
            pool.append(_rss_item(title, f"feed{i}-1", f"https://site{i}-1.com/x"))
            pool.append(_rss_item(title, f"feed{i}-2", f"https://site{i}-2.com/x"))
        cands = topics.generate_candidates(pool, rss_items=[])
        self.assertEqual(len(cands), 3)
        self.assertNotIn("独家热点事件", [c["title"] for c in cands])

    def test_single_source_clusters_fill_when_multisource_supply_short(self):
        pool = [
            _pool_item("事件一", "多家推理服务商调整定价，企业成本结构将重算", score=80, idx="1"),
            _pool_item("事件二", "开源模型权重发布，工程团队工作流将改变", score=70, idx="2"),
            _pool_item("事件三", "平台抽成政策调整，生态格局将重排", score=60, idx="3"),
        ]
        cands = topics.generate_candidates(pool, rss_items=[])
        self.assertEqual(len(cands), 3)
        self.assertTrue(all(
            any("独立来源" in g for g in c["evidence_gaps"]) for c in cands
        ))

    def test_vetoed_cluster_excluded_from_candidates(self):
        pool = [
            _pool_item("某公司与某巨头达成战略合作", "强强联合赋能行业", idx="veto"),
            _pool_item("事件一", "多家推理服务商调整定价，企业成本结构将重算", idx="1"),
            _pool_item("事件二", "开源模型权重发布，工程团队工作流将改变", idx="2"),
            _pool_item("事件三", "平台抽成政策调整，生态格局将重排", idx="3"),
        ]
        cands = topics.generate_candidates(pool, rss_items=[])
        self.assertEqual(len(cands), 3)
        self.assertNotIn("某公司与某巨头达成战略合作", [c["title"] for c in cands])

    def test_zero_eic_cluster_sinks_below_triggered_clusters(self):
        pool = [
            _pool_item("今天天气不错", "适合写代码", score=99, idx="dull"),
            _pool_item("事件一", "多家推理服务商调整定价，企业成本结构将重算", score=50, idx="1"),
            _pool_item("事件二", "开源模型权重发布，工程团队工作流将改变", score=50, idx="2"),
            _pool_item("事件三", "平台抽成政策调整，生态格局将重排", score=50, idx="3"),
        ]
        cands = topics.generate_candidates(pool, rss_items=[])
        self.assertEqual(len(cands), 3)
        self.assertNotIn("今天天气不错", [c["title"] for c in cands])

    def test_fewer_than_three_survivors_raises_honestly(self):
        pool = [
            _pool_item("某公司与某巨头达成战略合作", "强强联合赋能行业", idx="v1"),
            _pool_item("某公司完成融资", "由某基金领投", idx="v2"),
            _pool_item("事件一", "多家推理服务商调整定价，企业成本结构将重算", idx="1"),
        ]
        with self.assertRaises(topics.TopicError):
            topics.generate_candidates(pool, rss_items=[])


class CandidateSchemaTests(unittest.TestCase):
    def _valid(self):
        return {
            "title": "事件标题",
            "thesis": "论点说明",
            "research_queries": ["query 关键词"],
            "sources": [{"url": "https://example.com/a"}],
        }

    def test_valid_candidate_passes(self):
        self.assertEqual(topics.validate_candidate(self._valid()), [])

    def test_missing_title_fails(self):
        cand = self._valid()
        cand["title"] = ""
        self.assertTrue(topics.validate_candidate(cand))

    def test_missing_queries_fails(self):
        cand = self._valid()
        cand["research_queries"] = []
        self.assertTrue(topics.validate_candidate(cand))

    def test_missing_or_non_http_urls_fail(self):
        cand = self._valid()
        cand["sources"] = [{"url": "not-a-url"}]
        self.assertTrue(topics.validate_candidate(cand))

    def test_human_choice_rejects_schema_invalid_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_paths = paths.RunPaths.for_date(pathlib.Path(tmp), "2026-08-14")
            run_paths.ensure_work_dir()
            state.init_state(run_paths)
            bad = [self._valid()]
            bad[0]["sources"] = []
            with self.assertRaises(topics.TopicError):
                topics.record_human_choice(run_paths, bad, 1, "")

    def test_insufficient_items_still_reports_honestly(self):
        with self.assertRaises(topics.TopicError):
            topics.generate_candidates(aihot_items()[:1], rss_items=[])


class TopicGateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.paths = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.paths.ensure_work_dir()
        state.init_state(self.paths)

    def tearDown(self):
        self._tmp.cleanup()

    def test_without_choice_research_is_blocked(self):
        with self.assertRaises(topics.TopicGateBlocked):
            topics.require_choice(self.paths)

    def test_fixture_bypass_provides_deterministic_topic(self):
        topic = topics.choose_fixture(self.paths, FIXTURES / "topic_fixture.json")
        self.assertEqual(topic["title"], "AI 搜索预算与个人创作者的研究成本")
        self.assertEqual(topic["slug"], "ai-search-budget-research-cost")
        st = state.read_state(self.paths)
        self.assertEqual(st["topic_choice"], "fixture")
        self.assertEqual(st["slug"], topic["slug"])
        self.assertEqual(st["topic_title"], topic["title"])
        # now the gate passes
        self.assertEqual(topics.require_choice(self.paths)["title"], topic["title"])

    def test_human_choice_preserved_verbatim_with_direction(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        topics.record_human_choice(
            self.paths, cands, choice=2, direction="按企业采购视角写，别写开发者教程。"
        )
        st = state.read_state(self.paths)
        self.assertEqual(st["topic_choice"], "human")
        saved = json.loads(
            (self.paths.work_dir / "selected-topic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(saved["direction"], "按企业采购视角写，别写开发者教程。")
        self.assertEqual(saved["title"], cands[1]["title"])

    def test_human_choice_index_out_of_range_rejected(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        with self.assertRaises(topics.TopicError):
            topics.record_human_choice(self.paths, cands, choice=9)

    def test_simulated_choice_bypasses_human_gate(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        topics.record_simulated_choice(self.paths, cands, choice=2)
        st = state.read_state(self.paths)
        self.assertEqual(st["topic_choice"], "simulated")
        self.assertEqual(st["slug"], cands[1]["slug"])
        self.assertEqual(st["topic_title"], cands[1]["title"])
        self.assertTrue(
            any(
                "topic choice: simulated (unattended mode, candidate 2)" in line
                for line in st["stage_log"]
            ),
            st["stage_log"],
        )
        # the gate accepts the simulated choice; no human wait
        self.assertEqual(topics.require_choice(self.paths)["title"], cands[1]["title"])

    def test_simulated_choice_preserves_candidate_verbatim_empty_direction(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        topic = topics.record_simulated_choice(self.paths, cands, choice=1)
        self.assertEqual(topic["title"], cands[0]["title"])
        self.assertEqual(topic["slug"], cands[0]["slug"])
        self.assertEqual(topic["thesis"], cands[0]["thesis"])
        self.assertEqual(topic["direction"], "")
        saved = json.loads(
            (self.paths.work_dir / "selected-topic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(saved["title"], cands[0]["title"])
        self.assertEqual(saved["slug"], cands[0]["slug"])
        self.assertEqual(saved["direction"], "")

    def test_simulated_choice_index_out_of_range_rejected(self):
        cands = topics.generate_candidates(aihot_items(), rss_items=[])
        with self.assertRaises(topics.TopicError):
            topics.record_simulated_choice(self.paths, cands, choice=9)




class SameEventTargetedTests(unittest.TestCase):
    """Regression targets: mixed-script false splits, generic-token false merges."""

    def test_mixed_ascii_cjk_same_story_not_split(self):
        # One shared ascii token + near-identical CJK body = same event.
        a = "DeepSeek 发布新一代推理模型"
        b = "DeepSeek 新一代推理模型正式发布"
        self.assertTrue(topics.same_event(a, b))

    def test_generic_tokens_do_not_merge_different_events(self):
        # api/app are generic vocabulary, not event identity.
        a = "AI 绘图 App 开放 API 接入"
        b = "AI 编程 App 新增 API 计费"
        self.assertFalse(topics.same_event(a, b))

    def test_generic_tokens_excluded_from_token_set(self):
        toks = topics._ascii_tokens("A new App ships an API plus SDK update")
        for generic in ("app", "api", "sdk", "new", "plus", "update"):
            self.assertNotIn(generic, toks)
        self.assertIn("ships", toks)

    def test_numbered_series_stay_distinct_with_bigram_fallback(self):
        # The bigram fallback must never merge serials that differ by digit.
        a = "地方展会发布新款智能硬件 0"
        b = "地方展会发布新款智能硬件 1"
        self.assertFalse(topics.same_event(a, b))
        self.assertFalse(topics.same_event("Grok 4.5 硬件版发布", "Grok 4.6 硬件版发布"))

    def test_versioned_token_pairs_still_merge(self):
        # Versioned tokens (gpt-5, grok 4.6) carry identity and still cluster.
        self.assertTrue(topics.same_event("Grok 4.6 发布", "xAI 发布 Grok 4.6"))

    def test_cluster_merges_reordered_mixed_title(self):
        items = [
            {"title": "DeepSeek 发布新一代推理模型", "url": "https://x.example.com/1",
             "summary": "", "origin": "rss", "feed": "f1", "score": 0},
            {"title": "DeepSeek 新一代推理模型正式发布", "url": "https://y.example.com/2",
             "summary": "", "origin": "aihot",
             "links": {"aihot": "https://y.example.com/2"}, "score": 0},
        ]
        clusters = topics.cluster_events(items)
        self.assertEqual(len(clusters), 1)




class TopicFixtureErrorTests(TopicGateTests):
    def test_malformed_topic_fixture_wrapped_in_topic_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = pathlib.Path(tmp) / "bad-topic.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(topics.TopicError):
                topics.choose_fixture(self.paths, bad)

    def test_missing_topic_fixture_wrapped_in_topic_error(self):
        with self.assertRaises(topics.TopicError):
            topics.choose_fixture(self.paths, self.root / "does-not-exist.json")

    def test_non_object_topic_fixture_wrapped_in_topic_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = pathlib.Path(tmp) / "list-topic.json"
            bad.write_text("[1, 2, 3]", encoding="utf-8")
            with self.assertRaises(topics.TopicError):
                topics.choose_fixture(self.paths, bad)


if __name__ == "__main__":
    unittest.main()

"""Tests for 04 narrative candidates: evidence routing, generation, HITL."""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import STAGES, narrative, paths, state, topics


def sample_osint():
    return {
        "analysis_status": "completed",
        "modules": [
            {"key": "core_timeline", "title": "时间线", "summary": "8月发布。"},
            {"key": "finance_capital", "title": "财务", "summary": "定价 $0.75/1M"},
            {"key": "tech_engineering", "title": "工程", "summary": "743B 基座"},
            {"key": "ecosystem_moat", "title": "生态", "summary": "无"},
            {"key": "community_voices", "title": "社区", "summary": "V2EX 实测"},
            {"key": "org_people", "title": "人事", "summary": "无"},
            {"key": "editor_direction_check", "title": "主编核查", "summary": "无"},
        ],
        "evidence_gaps": [],
        "sources": [
            {"url": "https://example.com/a", "status": "fetched", "title": "发布"},
        ],
    }


def sample_narrative_candidate():
    return {
        "archetype": "cost_ledger", "title": "账本篇", "hook": "h",
        "thesis": "t", "key_arguments": [], "decision_rule": "d",
        "platform_notes": {"linkedin": "l", "wechat": "w"},
        "evidence_audit": "e",
        "author_stance": "我的判断",
        "personal_scene": "凌晨三点被报警吵醒",
        "kicker": "先别急着上车。",
    }


class StagesOrderTests(unittest.TestCase):
    def test_narrative_stage_follows_research(self):
        self.assertEqual(
            STAGES[STAGES.index("research") + 1], "narrative"
        )


class EvidenceInventoryTests(unittest.TestCase):
    def test_module_signals_map_to_inventory_flags(self):
        inv = narrative.evidence_inventory(sample_osint())
        self.assertTrue(inv["cost_data"])
        self.assertTrue(inv["mechanism_signal"])
        self.assertTrue(inv["community_signal"])
        self.assertTrue(inv["primary_signal"])
        self.assertFalse(inv["org_source"])
        self.assertFalse(inv["policy_text"])

    def test_policy_url_and_org_summary_set_flags(self):
        osint = sample_osint()
        osint["modules"][5]["summary"] = "CEO 离职"
        osint["sources"].append({
            "url": "https://eur-lex.europa.eu/x", "status": "fetched",
            "title": "AI Act",
        })
        inv = narrative.evidence_inventory(osint)
        self.assertTrue(inv["org_source"])
        self.assertTrue(inv["policy_text"])

    def test_no_evidence_means_no_primary_signal(self):
        inv = narrative.evidence_inventory({"modules": [], "sources": [], "evidence_gaps": []})
        self.assertFalse(inv["primary_signal"])

    def test_billion_dollar_terms_set_cost_flag(self):
        osint = sample_osint()
        osint["modules"][1]["summary"] = "无"
        osint["sources"] = [{
            "url": "https://e/x", "status": "fetched",
            "title": "a", "excerpt": "backing up to $105 billion guarantee",
        }]
        self.assertTrue(narrative.evidence_inventory(osint)["cost_data"])


class TensionDetectionTests(unittest.TestCase):
    def test_counter_consensus_hook_detected(self):
        topic = {"title": "X 发布", "hook": "反共识点：大家都盯单价，真账在调用次数"}
        tensions = narrative.tension_detection(topic, sample_osint())
        self.assertIn("consensus_vs_data", tensions)

    def test_price_tension_from_topic(self):
        topic = {"title": "API 涨价", "hook": ""}
        tensions = narrative.tension_detection(topic, sample_osint())
        self.assertIn("price_vs_tco", tensions)


class RouteArchetypeTests(unittest.TestCase):
    def test_cost_and_org_route_to_their_archetypes(self):
        osint = sample_osint()
        osint["modules"][5]["summary"] = "CEO 离职"
        allowed = narrative.route_archetypes(osint, {"consensus_vs_data"})
        self.assertIn("cost_ledger", allowed)
        self.assertNotIn("power_map", allowed)
        self.assertNotIn("decision_brief", allowed)
        self.assertNotIn("compliance_risk", allowed)

    def test_empty_evidence_kills_generation(self):
        with self.assertRaises(narrative.NarrativeError):
            narrative.route_archetypes(
                {"modules": [], "sources": [], "evidence_gaps": []}, set()
            )

    def test_power_map_requires_org_artifact_not_just_org_keywords(self):
        osint = sample_osint()
        osint["modules"][5]["summary"] = "CEO 离职"
        allowed = narrative.route_archetypes(osint, set())
        self.assertNotIn("power_map", allowed)

    def test_power_map_unlocked_by_internal_letter_artifact(self):
        osint = sample_osint()
        osint["modules"][5]["summary"] = "CEO 离职"
        osint["sources"].append({
            "url": "https://example.com/letter", "status": "fetched",
            "title": "内部信", "excerpt": "CEO 内部信确认组织重组与汇报线变化",
        })
        allowed = narrative.route_archetypes(osint, set())
        self.assertIn("power_map", allowed)

    def test_mechanism_teardown_requires_tech_artifact(self):
        osint = sample_osint()
        for m in osint["modules"]:
            if m["key"] == "tech_engineering":
                m["summary"] = "无"
        osint["sources"][0]["excerpt"] = "普通新闻稿"
        allowed = narrative.route_archetypes(osint, set())
        self.assertNotIn("mechanism_teardown", allowed)

    def test_bare_resignation_report_does_not_unlock_power_map(self):
        osint = sample_osint()
        for m in osint["modules"]:
            if m["key"] == "org_people":
                m["summary"] = "无"
        osint["sources"].append({
            "url": "https://example.com/news", "status": "fetched",
            "title": "某大厂 CEO 离职", "excerpt": "人事大调整，内部消息称",
        })
        allowed = narrative.route_archetypes(osint, set())
        self.assertNotIn("power_map", allowed)

    def test_english_mechanism_evidence_opens_mechanism_teardown(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://huggingface.co/blog/x", "status": "fetched",
            "title": "Up to 3.2x Faster Inference with LFM2.5-DSpark",
            "excerpt": ("We release DSpark draft model checkpoints for "
                        "speculative decoding. Up to 3.18x throughput on "
                        "H100, 2.87x on-device."),
        }]
        allowed = narrative.route_archetypes(osint, set())
        self.assertIn("mechanism_teardown", allowed)
        self.assertNotEqual(allowed, ["decision_brief"])


class KillConditionTests(unittest.TestCase):
    def _real_shaped_osint(self, sources):
        return {
            "analysis_status": "completed",
            "modules": [
                {"key": k, "title": t, "summary": "（已采集证据，待分析）"}
                for k, t in (
                    ("core_timeline", "时间线"),
                    ("finance_capital", "财务"),
                    ("tech_engineering", "工程"),
                    ("unclassified", "未归类线索"),
                )
            ],
            "evidence_gaps": [],
            "sources": sources,
        }

    def test_press_release_only_evidence_killed(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/pr", "status": "fetched",
            "title": "某公司宣布战略合作，强强联合赋能行业", "excerpt": "",
        }]
        self.assertIsNotNone(narrative._kill_reason(osint, {}))

    def test_press_release_kill_fires_on_real_research_shape(self):
        osint = self._real_shaped_osint([
            {
                "url": "https://example.com/pr", "status": "fetched",
                "title": "某公司宣布战略合作，强强联合赋能行业", "excerpt": "",
            }
        ])
        self.assertIsNotNone(narrative._kill_reason(osint, {}))

    def test_rumor_kill_fires_on_real_research_shape(self):
        osint = self._real_shaped_osint([
            {
                "url": "https://www.reddit.com/r/ai/x", "status": "fetched",
                "title": "听说是真的", "excerpt": "",
            }
        ])
        self.assertIsNotNone(narrative._kill_reason(osint, {}))

    def test_rumor_only_evidence_killed(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://www.reddit.com/r/ai/x", "status": "fetched",
            "title": "听说是真的", "excerpt": "",
        }]
        self.assertIsNotNone(narrative._kill_reason(osint, {}))

    def test_benchmark_without_method_killed(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/b", "status": "fetched",
            "title": "某模型 benchmark 登顶", "excerpt": "刷新纪录",
        }]
        topic = {"title": "某模型跑分登顶", "hook": ""}
        self.assertIsNotNone(narrative._kill_reason(osint, topic))

    def test_real_evidence_not_killed(self):
        self.assertIsNone(narrative._kill_reason(sample_osint(), {}))

    def test_arxiv_benchmark_not_killed_by_missing_method_keywords(self):
        osint = self._real_shaped_osint([
            {
                "url": "https://arxiv.org/abs/2603.12201", "status": "fetched",
                "title": "benchmark 结果公布", "excerpt": "分数刷新纪录",
            }
        ])
        topic = {"title": "某模型跑分登顶", "hook": "", "thesis": ""}
        self.assertIsNone(narrative._kill_reason(osint, topic))

    def test_kill_reason_names_actual_veto_class(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/f", "status": "fetched",
            "title": "某公司完成 5000 万美元 A 轮融资", "excerpt": "由某基金领投",
        }]
        reason = narrative._kill_reason(osint, {})
        self.assertIsNotNone(reason)
        self.assertIn("融资", reason)


class PromptBestPracticeMatrixTests(unittest.TestCase):
    def _prompt(self, allowed=None):
        topic = {"title": "X 发布", "hook": "", "research_queries": []}
        osint = sample_osint()
        allowed = allowed or narrative.route_archetypes(osint, set())
        return narrative._compile_prompt(topic, osint, allowed, set())

    def test_prompt_includes_hook_patterns_and_denominator(self):
        prompt = self._prompt()
        self.assertIn("HookPatternConfidence", prompt)
        self.assertIn("同任务对照", prompt)
        self.assertIn("denominator", prompt)

    def test_prompt_includes_evidence_ladder_and_citation_format(self):
        prompt = self._prompt()
        self.assertIn("可复现实测artifact", prompt)
        self.assertIn("[机构],[日期],[样本/方法]", prompt)
        self.assertIn("Confirmed/Reported/Inferred/Unknown", prompt)

    def test_prompt_injects_anatomy_only_for_allowed_archetypes(self):
        prompt = self._prompt(allowed=["cost_ledger"])
        self.assertIn("成本与供应链账本", prompt)
        self.assertIn("denominator", prompt)
        self.assertNotIn("生态权力图", prompt)

    def test_prompt_includes_authenticity_four_pack(self):
        prompt = self._prompt()
        self.assertIn("真信度四件套", prompt)
        self.assertIn("只有真正调查过才写得出", prompt)

    def test_prompt_anchors_author_persona_and_stance(self):
        prompt = self._prompt()
        self.assertIn("老兵", prompt)
        self.assertIn("author_stance", prompt)
        self.assertIn("personal_scene", prompt)
        self.assertIn("kicker", prompt)
        self.assertIn("第一人称", prompt)

    def test_prompt_keeps_evidence_discipline_rules(self):
        prompt = self._prompt()
        self.assertIn("Observable", prompt)
        self.assertIn("central tension", prompt)
        self.assertIn("Claim → Observable → Source → Limitation", prompt)
        self.assertIn("decision_rule", prompt)

    def test_prompt_blacklists_consulting_tone(self):
        prompt = self._prompt()
        self.assertIn("综上所述", prompt)
        self.assertIn("一方面", prompt)
        self.assertIn("我们认为", prompt)

    def test_prompt_imposes_compactness_constraints(self):
        prompt = self._prompt()
        self.assertIn("8000 字符", prompt)
        self.assertIn("2-4 条", prompt)

    def test_prompt_bans_consulting_title_phrasing(self):
        prompt = self._prompt(allowed=["decision_brief"])
        self.assertIn("咨询报告", prompt)
        self.assertIn("工程负责人只需要看", prompt)
        self.assertIn("值得关注的N件事", prompt)

    def test_decision_brief_anatomy_title_is_not_consulting(self):
        self.assertNotIn(
            "工程负责人只需要看", narrative._ARCHETYPE_ANATOMY["decision_brief"]
        )
        self.assertIn("别被热搜带节奏", narrative._ARCHETYPE_ANATOMY["decision_brief"])

    def test_prompt_includes_editorial_directive_when_given(self):
        directive = "两个叙事我都不喜欢；请深挖 AGI 前夜的准入与垄断"
        prompt = narrative._compile_prompt(
            {"title": "X 发布", "hook": "", "research_queries": []},
            sample_osint(),
            ["cost_ledger"],
            set(),
            directive=directive,
        )
        self.assertIn("主编退回意见", prompt)
        self.assertIn(directive, prompt)
        self.assertIn("Inferred/Unknown", prompt)

    def test_prompt_includes_kg_background_when_present(self):
        prompt = narrative._compile_prompt(
            {"title": "X 发布", "hook": "", "research_queries": []},
            sample_osint(),
            ["cost_ledger"],
            set(),
            kg_background="## DRAFT\nmemory-bound insight",
        )
        self.assertIn("知识图谱背景", prompt)
        self.assertIn("memory-bound insight", prompt)
        self.assertIn("二手", prompt)
        self.assertIn("不得作为事件证据", prompt)

    def test_prompt_omits_kg_background_when_absent(self):
        prompt = narrative._compile_prompt(
            {"title": "X 发布", "hook": "", "research_queries": []},
            sample_osint(),
            ["cost_ledger"],
            set(),
        )
        self.assertNotIn("Knowledge-Graph Background", prompt)

    def test_prompt_declares_reader_move_and_form_specific_endings(self):
        prompt = self._prompt(allowed=["reported_story"])
        self.assertIn("narrative_form", prompt)
        self.assertIn("reader_move", prompt)
        self.assertIn("ending_mode", prompt)
        self.assertIn("decision_rule 只对行动型叙事必填", prompt)
        self.assertNotIn("开头三段 = Observable（可观察事实）→ Conflict（与主流说法/发布会的冲突）→ Decision", prompt)


class NarrativeV2RegressionTests(unittest.TestCase):
    def test_valuation_rumor_does_not_unlock_cost_route(self):
        osint = sample_osint()
        for module in osint["modules"]:
            module["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/report",
            "status": "fetched",
            "title": "Hugging Face explores a $13 billion acquisition offer",
            "excerpt": "The valuation is discussed in acquisition talks.",
        }]
        self.assertFalse(narrative.evidence_inventory(osint)["cost_data"])

    def test_chinese_financing_round_does_not_unlock_cost_route(self):
        osint = sample_osint()
        for module in osint["modules"]:
            module["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/funding",
            "status": "fetched",
            "title": "完成新一轮融资，估值达到150亿美元",
            "excerpt": "公司正在接触投资人，融资轮与估值仍未披露交易条款。",
        }]
        self.assertFalse(narrative.evidence_inventory(osint)["cost_data"])

    def test_cost_keyword_arr_requires_a_word_boundary(self):
        osint = sample_osint()
        for module in osint["modules"]:
            module["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/story",
            "status": "fetched",
            "title": "The narrative is shifting",
            "excerpt": "The narrative is shifting, but no operating figures were disclosed.",
        }]
        self.assertFalse(narrative.evidence_inventory(osint)["cost_data"])

    def test_acquisition_rumor_does_not_unlock_control_signal(self):
        osint = sample_osint()
        for module in osint["modules"]:
            module["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/report",
            "status": "fetched",
            "title": "Hugging Face 接触潜在收购方",
            "excerpt": "报道没有披露买方、条款或公告。",
        }]
        self.assertFalse(narrative.evidence_inventory(osint)["org_source"])

    def test_non_action_candidate_can_omit_decision_rule(self):
        candidate = {
            "archetype": "decision_brief",
            "narrative_form": "reported_story",
            "reader_move": "reframe",
            "ending_mode": "open_tension",
            "title": "传闻还没有变成事实",
            "hook": "新闻已经跑在事实前面。",
            "thesis": "交易接触不是成交，真正的故事是生态为何提前恐慌。",
            "key_arguments": [{
                "claim": "报道只确认接触",
                "observable": "买方和条款仍未知",
                "source": "example.com",
                "limitation": "没有官方公告",
            }],
            "platform_notes": {"linkedin": "my take", "wechat": "事件拆解"},
            "evidence_audit": "reported, not confirmed",
            "author_stance": "我不接受把传闻写成讣告。",
            "personal_scene": "我把报道和公告两栏并排放在屏幕上。",
            "kicker": "新闻先到了，事实还在路上。",
        }
        self.assertEqual(
            narrative._validate_candidate(candidate, ["decision_brief"]), []
        )

    def test_same_advice_pair_is_rejected(self):
        first = {
            "title": "别急着迁移",
            "thesis": "传闻未证实，先做依赖盘点。",
            "reader_move": "prepare",
            "decision_rule": "先做依赖盘点，再决定是否迁移。",
        }
        second = {
            "title": "今天先查依赖账本",
            "thesis": "收购未证实，先做依赖盘点。",
            "reader_move": "prepare",
            "decision_rule": "先做依赖盘点，再决定是否迁移。",
        }
        errors = narrative.validate_candidate_pair([first, second])
        self.assertTrue(errors)
        self.assertIn("same-advice", errors[0])

    def test_identical_thesis_is_rejected_even_when_reader_move_differs(self):
        first = {
            "thesis": "交易未证实，真正未知的是治理条款。",
            "reader_move": "understand",
        }
        second = {
            "thesis": "交易未证实，真正未知的是治理条款。",
            "reader_move": "imagine",
        }
        errors = narrative.validate_candidate_pair([first, second])
        self.assertTrue(errors)
        self.assertIn("same-advice", errors[0])

    def test_non_action_form_does_not_invent_decision_rule_ending(self):
        self.assertEqual(
            narrative._default_ending("reported_story", "act", ""),
            "open_tension",
        )


class CandidateScoreTests(unittest.TestCase):
    def test_scores_within_unit_range(self):
        scores = narrative.score_candidate(
            sample_narrative_candidate(), sample_osint()
        )
        for key in ("evidence", "conflict", "decision", "freshness"):
            self.assertGreaterEqual(scores[key], 0.0)
            self.assertLessEqual(scores[key], 1.0)

    def test_platform_weighted_totals_differ_by_platform(self):
        scores = narrative.score_candidate(
            sample_narrative_candidate(), sample_osint()
        )
        self.assertIn("linkedin_total", scores)
        self.assertIn("wechat_total", scores)
        self.assertAlmostEqual(
            scores["linkedin_total"],
            round(
                0.35 * scores["evidence"] + 0.30 * scores["decision"]
                + 0.20 * scores["conflict"] + 0.15 * scores["freshness"],
                2,
            ),
            places=2,
        )
        self.assertAlmostEqual(
            scores["wechat_total"],
            round(
                0.30 * scores["conflict"] + 0.25 * scores["evidence"]
                + 0.25 * scores["decision"] + 0.20 * scores["freshness"],
                2,
            ),
            places=2,
        )

    def test_conflict_markers_boost_conflict_score(self):
        blunt = sample_narrative_candidate()
        blunt["thesis"] = "没有张力的平淡表述"
        punchy = sample_narrative_candidate()
        punchy["thesis"] = "与主流说法冲突：这里有一个落差"
        self.assertGreater(
            narrative.score_candidate(punchy, sample_osint())["conflict"],
            narrative.score_candidate(blunt, sample_osint())["conflict"],
        )

    def test_conditional_decision_rule_scores_full(self):
        cand = sample_narrative_candidate()
        cand["decision_rule"] = "当官方确认时重启；只有复现通过才切换"
        self.assertEqual(
            narrative.score_candidate(cand, sample_osint())["decision"], 1.0
        )

    def test_mixed_timestamp_formats_do_not_crash(self):
        osint = sample_osint()
        osint["sources"] = [
            {"url": "https://e/1", "status": "fetched",
             "fetched_at": "2026-08-15T10:00:00Z"},
            {"url": "https://e/2", "status": "fetched",
             "fetched_at": "2026-08-15 10:00:00"},
        ]
        scores = narrative.score_candidate(
            sample_narrative_candidate(), osint
        )
        self.assertIn("freshness", scores)

    def test_scores_are_deterministic(self):
        cand = sample_narrative_candidate()
        self.assertEqual(
            narrative.score_candidate(cand, sample_osint()),
            narrative.score_candidate(cand, sample_osint()),
        )

    def test_run_retries_once_after_truncated_output(self):
        import tempfile as _tf
        from ai_daily import paths as _paths, state as _state, topics as _topics

        calls = {"n": 0}
        valid = {
            "candidates": [
                {
                    "archetype": "reported_story", "title": "标题",
                    "hook": "h", "thesis": "t",
                    "key_arguments": [{
                        "claim": "c", "observable": "o", "source": "s",
                        "limitation": "l", "decision": "d",
                    }],
                    "decision_rule": "r",
                    "platform_notes": {"linkedin": "l", "wechat": "w"},
                    "author_stance": "我的判断",
                    "personal_scene": "凌晨三点被报警吵醒",
                    "kicker": "先别急着上车。",
                    "evidence_audit": "e",
                },
                {
                    "archetype": "reported_story", "title": "标题2",
                    "hook": "h2", "thesis": "t2",
                    "key_arguments": [{
                        "claim": "c", "observable": "o", "source": "s",
                        "limitation": "l", "decision": "d",
                    }],
                    "decision_rule": "r2",
                    "platform_notes": {"linkedin": "l", "wechat": "w"},
                    "author_stance": "我的判断",
                    "personal_scene": "凌晨三点被报警吵醒",
                    "kicker": "先别急着上车。",
                    "evidence_audit": "e",
                },
            ]
        }

        def runner(prompt):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"status": "unavailable",
                        "reason": "codex exec final message is not JSON: {.."}
            return valid

        with _tf.TemporaryDirectory() as tmp:
            rp = _paths.RunPaths.for_date(pathlib.Path(tmp), "2026-08-15")
            rp.ensure_work_dir()
            _state.init_state(rp)
            _topics.choose_fixture(
                rp, pathlib.Path(__file__).resolve().parent
                / "fixtures" / "topic_fixture.json"
            )
            (rp.work_dir / "initial-osint.json").write_text(
                json.dumps(sample_osint(), ensure_ascii=False), encoding="utf-8"
            )
            result = narrative.run(rp, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "generated")
        self.assertEqual(calls["n"], 2)


class NarrativeRunTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-15")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)
        topics.choose_fixture(
            self.run_paths,
            pathlib.Path(__file__).resolve().parent / "fixtures" / "topic_fixture.json",
        )
        (self.run_paths.work_dir / "initial-osint.json").write_text(
            json.dumps(sample_osint(), ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def make_runner(archetype="cost_ledger"):
        def runner(prompt):
            return {
                "candidates": [
                    {
                        "archetype": archetype,
                        "title": "标题一",
                        "hook": "事实。冲突。决策。",
                        "thesis": "论点一",
                        "key_arguments": [{
                            "claim": "成本更低", "observable": "$5 vs $30",
                            "source": "账单", "limitation": "厂商自测",
                            "decision": "可复测",
                        }],
                        "decision_rule": "条件成立才切",
                        "platform_notes": {"linkedin": "LN", "wechat": "WX"},
                        "author_stance": "我的判断",
                        "personal_scene": "凌晨三点被报警吵醒",
                        "kicker": "先别急着上车。",
                        "evidence_audit": "EO 充足",
                    },
                    {
                        "archetype": "reported_story",
                        "title": "标题二",
                        "hook": "事实。冲突。决策。",
                        "thesis": "论点二",
                        "key_arguments": [{
                            "claim": "先观察", "observable": "单一来源",
                            "source": "官方帖", "limitation": "未双源",
                            "decision": "等待复测",
                        }],
                        "decision_rule": "先观察",
                        "platform_notes": {"linkedin": "LN2", "wechat": "WX2"},
                        "author_stance": "我的判断",
                        "personal_scene": "凌晨三点被报警吵醒",
                        "kicker": "先别急着上车。",
                        "evidence_audit": "EO 充足",
                    },
                ]
            }
        return runner

    def test_run_writes_candidates_and_returns_two(self):
        result = narrative.run(
            self.run_paths, codex_runner=self.make_runner(), force=True
        )
        self.assertEqual(result["status"], "generated")
        self.assertEqual(len(result["candidates"]), 2)
        data = json.loads(
            (self.run_paths.work_dir / "narrative-candidates.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(data["candidates"]), 2)
        md = (self.run_paths.work_dir / "narrative-candidates.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("标题一", md)

    def test_archetype_outside_whitelist_rejected(self):
        result = narrative.run(
            self.run_paths, codex_runner=self.make_runner("compliance_risk"),
            force=True,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("compliance_risk", result["reason"])

    def test_resume_skips_regeneration(self):
        calls = {"n": 0}

        def runner(prompt):
            calls["n"] += 1
            return self.make_runner()(prompt)

        first = narrative.run(self.run_paths, codex_runner=runner, force=True)
        second = narrative.run(self.run_paths, codex_runner=runner)
        self.assertEqual(first["status"], "generated")
        self.assertEqual(second["status"], "resumed")
        self.assertEqual(calls["n"], 1)

    def test_apply_directive_records_and_invalidates_candidates(self):
        narrative.run(self.run_paths, codex_runner=self.make_runner(), force=True)
        result = narrative.apply_directive(
            self.run_paths, "两个叙事我都不喜欢，重写"
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["directive"], "两个叙事我都不喜欢，重写")
        st = state.read_state(self.run_paths)
        self.assertEqual(st["narrative_directive"], "两个叙事我都不喜欢，重写")
        self.assertFalse(
            (self.run_paths.work_dir / narrative.NARRATIVE_CANDIDATES_JSON).exists()
        )
        self.assertFalse(
            (self.run_paths.work_dir / narrative.NARRATIVE_CANDIDATES_MD).exists()
        )

    def test_run_injects_directive_into_regeneration_prompt(self):
        narrative.apply_directive(self.run_paths, "AGI 前夜准入与垄断")
        captured = {}

        def runner(prompt):
            captured["prompt"] = prompt
            return self.make_runner()(prompt)

        result = narrative.run(self.run_paths, codex_runner=runner)
        self.assertEqual(result["status"], "generated")
        self.assertIn("AGI 前夜准入与垄断", captured["prompt"])
        self.assertIn("主编退回意见", captured["prompt"])

    def test_resume_refuses_stale_candidates_for_a_different_topic(self):
        # A leftover candidates file from another topic must not resume.
        stale = {
            "run_id": "AI-Daily/2026-08-15",
            "topic_title": "别的选题：GLM-5.3 后训练",
            "allowed_archetypes": ["cost_ledger"],
            "tensions": [],
            "candidates": [],
        }
        (self.run_paths.work_dir / "narrative-candidates.json").write_text(
            json.dumps(stale, ensure_ascii=False), encoding="utf-8"
        )
        (self.run_paths.work_dir / "narrative-candidates.md").write_text(
            "# stale\n", encoding="utf-8"
        )

        result = narrative.run(self.run_paths, codex_runner=self.make_runner())
        self.assertNotEqual(result["status"], "resumed")
        data = json.loads(
            (self.run_paths.work_dir / "narrative-candidates.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["topic_title"], "AI 搜索预算与个人创作者的研究成本")

    def test_resume_records_narrative_stage(self):
        narrative.run(self.run_paths, codex_runner=self.make_runner(), force=True)
        self.assertEqual(
            state.read_state(self.run_paths)["stage"], "narrative"
        )
        narrative.run(self.run_paths, codex_runner=self.make_runner())
        self.assertEqual(
            state.read_state(self.run_paths)["stage"], "narrative"
        )

    def test_non_conforming_candidate_list_rejected(self):
        def runner(prompt):
            return {"candidates": [self.make_runner()(prompt)["candidates"][0]]}

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("non-conforming", result["reason"])

    def test_non_dict_candidate_rejected_cleanly(self):
        def runner(prompt):
            return {"candidates": ["不是对象", None]}

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")

    def test_missing_five_part_argument_fields_rejected(self):
        def runner(prompt):
            payload = self.make_runner()(prompt)
            payload["candidates"][0]["key_arguments"] = [
                {"claim": "只有 claim", "observable": "", "source": "",
                 "limitation": "", "decision": ""}
            ]
            return payload

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("observable", result["reason"])

    def test_missing_evidence_audit_rejected(self):
        def runner(prompt):
            payload = self.make_runner()(prompt)
            del payload["candidates"][0]["evidence_audit"]
            return payload

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("evidence_audit", result["reason"])

    def test_decision_brief_only_fallback(self):
        osint = sample_osint()
        for m in osint["modules"]:
            m["summary"] = "无"
        osint["sources"] = [{
            "url": "https://example.com/x", "status": "fetched", "title": "发布",
        }]
        allowed = narrative.route_archetypes(osint, set())
        self.assertEqual(allowed, ["reported_story"])

    def test_candidate_missing_author_stance_rejected(self):
        def runner(prompt):
            payload = self.make_runner()(prompt)
            del payload["candidates"][0]["author_stance"]
            return payload

        result = narrative.run(self.run_paths, codex_runner=runner, force=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("author_stance", result["reason"])


class NarrativeGateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.run_paths = paths.RunPaths.for_date(self.root, "2026-08-15")
        self.run_paths.ensure_work_dir()
        state.init_state(self.run_paths)

    def tearDown(self):
        self._tmp.cleanup()

    def test_require_narrative_blocks_before_choice(self):
        with self.assertRaises(narrative.NarrativeGateBlocked):
            narrative.require_narrative(self.run_paths)

    def test_record_choice_persists_durable_decision(self):
        candidates = [
            {
                "archetype": "cost_ledger", "title": "账本篇",
                "hook": "h", "thesis": "t", "key_arguments": [],
                "decision_rule": "d",
                "platform_notes": {"linkedin": "l", "wechat": "w"},
                "author_stance": "我的判断",
                "personal_scene": "凌晨三点被报警吵醒",
                "kicker": "先别急着上车。",
                "evidence_audit": "e",
            }
        ]
        chosen = narrative.record_choice(
            self.run_paths, candidates, 1, extra_research="补证：供应商访谈"
        )
        self.assertEqual(chosen["title"], "账本篇")
        selected = json.loads(
            (self.run_paths.work_dir / "selected-narrative.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(selected["archetype"], "cost_ledger")
        st = state.read_state(self.run_paths)
        self.assertEqual(st["narrative_choice"], "human")
        self.assertEqual(st["narrative_title"], "账本篇")
        self.assertEqual(st["narrative_archetype"], "cost_ledger")
        self.assertEqual(narrative.require_narrative(self.run_paths)["title"], "账本篇")

    def test_record_choice_persists_narrative_intent(self):
        candidate = {
            "archetype": "power_map", "title": "谁在看见需求",
            "hook": "h", "thesis": "t", "key_arguments": [],
            "author_stance": "我的判断", "personal_scene": "凌晨三点",
            "kicker": "看见本身就是力量。", "evidence_audit": "e",
            "narrative_form": "strategic_outlook",
            "reader_move": "imagine",
            "ending_mode": "forecast",
        }
        narrative.record_choice(self.run_paths, [candidate], 1)
        st = state.read_state(self.run_paths)
        self.assertEqual(st["narrative_form"], "strategic_outlook")
        self.assertEqual(st["narrative_reader_move"], "imagine")
        self.assertEqual(st["narrative_ending_mode"], "forecast")
        self.assertEqual(narrative.require_narrative(self.run_paths)["title"], "谁在看见需求")

    def test_record_choice_rejects_out_of_range(self):
        with self.assertRaises(narrative.NarrativeError):
            narrative.record_choice(self.run_paths, [], 1)

    def test_record_simulated_choice_marks_unattended(self):
        candidates = [
            {
                "archetype": "cost_ledger", "title": "账本篇",
                "hook": "h", "thesis": "t", "key_arguments": [],
                "decision_rule": "d",
                "platform_notes": {"linkedin": "l", "wechat": "w"},
                "author_stance": "我的判断",
                "personal_scene": "凌晨三点被报警吵醒",
                "kicker": "先别急着上车。",
                "evidence_audit": "e",
            }
        ]
        chosen = narrative.record_simulated_choice(self.run_paths, candidates, 1)
        self.assertEqual(chosen["title"], "账本篇")
        st = state.read_state(self.run_paths)
        self.assertEqual(st["narrative_choice"], "simulated")

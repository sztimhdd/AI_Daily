# 提示词资产迁移矩阵（修订版）

**状态：** 已确认（2026-08-14 用户批准三处修订）｜**来源：** 5 个 legacy n8n JSON、238 节点逐字段只读盘点，字段路径与字符数经主会话抽样复核。

## 决策记录（2026-08-14）

1. **选题简化**：AIHOT 取代 legacy 调研机器。TSV 采集资产（4 车道、词云路由、搜索故障转移、知乎/NewsAPI）整体弃用；仅保留判断层三条规则：Triage VETO 四杀、LCW EIC 三维筛选、REF topicChoserAgent 信源聚类（≥3 家独立信源 + Top3 排序）。
2. **research 封闭证据池**：V1 只消费 collect 产物（`aihot-items.json` + `rss-items.json`），legacy 搜索车道（Intent Router/Tavily/Brave/Firecrawl）整体弃用，仅留 intel 输出契约作参考；主动搜索延后 V1.5。
3. **fetch 平台路由三车道**：墙内平台（zhihu.com / mp.weixin.qq.com 等）= 本地 CDP 浏览器主车道（用户 Chrome 优先、in-app Browser 备选，run 开始做会话预检）；公开 URL = 直接 HTTP → tavily_extract；发现车道延后。抓取失败不阻塞管线，证据降级显式标注；浏览器 2 次找不到元素即熔断；正文存 `.local` 带 URL/sha256/状态，幂等重跑。

## 总览与核验

文件缩写：REF=`workflows/reference/公众号选题写稿配图一体化工作流.json`（94 节点）、LCW=`Long-Content-Writing.json`（42）、RES=`[Atomic] Researcher_Skill.json`（32）、TSV=`[Atomic] Topic_Survey_Skill.json`（26）、UDW=`[Atomic] Universal Draft Writing.json`（44）。五个只读子代理逐字段提取，主会话对 7 个关键字段路径与字符数抽样复核，全部吻合。

## 一、核心编辑 IP（采纳改写 / 采纳原样）

### collect / topic_choice

| 源资产 | 去向 | 处置 | 关键说明 |
|---|---|---|---|
| TSV·Triage Agent | topic_choice | 采纳改写·简化 | 保留 VETO 四杀（PR 通稿/增量更新/无范式融资/无 CTO FOMO）作 AIHOT 池硬过滤；intel 三段结构留给 V1.5 叙事 |
| LCW·Set Discovery Params1 | topic_choice | 采纳改写·简化 | 保留 EIC 三维（信息差/情绪/战略价值）作排序 rubric；mental_models 与 Narrative Agent 重复，合并为单资产 |
| REF·topicChoserAgent | topic_choice | 采纳改写·简化 | 聚类≥3 家独立信源 + 战略评估 + Top3；V1 已有聚类与评分，补信源数检查 |
| REF·Parser[6] | topic_choice | 采纳原样 | 选题 JSON schema（title/search_keywords/justification/urls）转校验器 |
| TSV·Super RSS Pool & Sampler | collect | 弃用（源清单已编译） | 以 `knowledge/rss-catalog.json` 与 rss_collect 的 extractable 子集为准；52 与 93 源口径差异不再追踪 |
| TSV·RSS Time Pre-Filter / Aggregate Intel | collect | 采纳改写 | 拒绝未来>1h、300 字截断、URL 归一化去重、空池熔断，参数化进 rss_collect |
| REF·Top 20 AI RSS Feeds | collect | 已编译 | rss-catalog.json 子集 |

### research + fetch

| 源资产 | 去向 | 处置 | 关键说明 |
|---|---|---|---|
| RES·Message a model（core_directives） | research | 已编译+核对 | research-contract.md 编译来源；比对 6 条 directive 完整性 |
| RES·MCP Payload Adapter | fetch·墙内车道 | 采纳改写 | 浏览器抓取指令（去广告/评论区、抽主文、纯净 Markdown）作为 CDP 车道指令 |
| RES·Intent Router Agent1 路由规则 | fetch·路由表 | 采纳原样 | 原文：URL 匹配 zhihu.com/mp.weixin.qq.com 等登录平台 → 浏览器（A 级定向爆破）；常规 → 无头抓取 |
| RES·Aggregate Intel（80k 截断/去重/来源标记） | fetch·正文规范化 | 采纳改写 | 截断上限按新模型上下文调整 |
| RES·Structured Output Parser / Gateway Output Contract | research→assembly | 采纳改写 | tasks[] 与出口摘要契约转数据类 |
| RES·Tavily Payload Builder / 统一情报洗数据 | 发现车道（V1.5） | 延后 | 查询模板与多引擎降级仅在接入主动搜索时启用 |
| RES·Intent Router Agent1 / Fallback to MCP / Tavily Key A·B / Brave / scrape.do / Apify / Firecrawl VM | — | 弃用 | V1 封闭证据池不需要；scrape.do token 已暴露须轮换 |
| LCW·Parse Selection1 / Parse Editor Feedback | research | 采纳改写 | 时间红线、防幻觉、7 模块格式；"增量弹药不重复大纲"并入 research-contract |
| REF·MaterialOrganizer | research | 采纳改写 | KB 字段 schema 与 research-contract 一致 |
| **知乎直达定向发现（用户提供路径）** | research·定向发现 | 采纳·新路径 | Chrome 走 `zhida.zhihu.com` 输入 topic → AI 回答+来源清单（问题标题/答主/关注赞同）→ 站内搜索桥接 question/answer URL → 逐条 Chrome 抓取回答全文。2026-08-14 全链路实测通过，见验证结果文档第七节 |
| **墙内 CDP 抓取 Skill（用户提供路径）** | fetch·墙内车道 | 采纳·新路径 | `~/.agents/skills/walled-fetch-cdp`：Python + Playwright `connect_over_cdp` 直连本地 Brave/Chrome（不走 Codex Browser Use）。微信全文 816 字、知乎 11,014 字实测 `fetched`；登录态页用用户 Brave（`launch_cdp.sh brave-default`）。见验证结果文档第九节 |

### bilingual_draft

| 源资产 | 去向 | 处置 | 关键说明 |
|---|---|---|---|
| UDW·First Draft Writer1 | EN 起草 | 采纳改写 | 人设/框架/防幻觉已编译；few-shot 过时只作结构参考 |
| UDW·First Draft Writer | ZH 起草 | 采纳改写 | 四大修辞 + 单点扩写≥300 字 + **归因公式（信息源+客观动作+内行诊断、禁"我测试了"冒领）**——需补编译，见质量层 spec §2 |
| REF·First Draft Writer1 / First Draft Writer | 双语初稿 | 采纳改写 | 强制 [1]/[1,3] 引用、[Editor's Note] 兜底、zh 每段≤3 句；搜索补全降级为纯素材写作 |
| LCW·Task Master Agent1 / Parse & Fan-out | 双平台任务契约 | 采纳改写 | hook/conflict/deep_dive/takeaway；黑名单双份收敛为单资产源 |

### quality_layer

| 源资产 | 去向 | 处置 | 关键说明 |
|---|---|---|---|
| REF·Final Editor1 | 质量层·EN 声线 | 采纳改写 | 作者声线 JSON（tone_keywords/avoid phrases/Ban List）抽独立资产 |
| REF·Final Editor2 | 质量层·ZH 声线 | 采纳改写 | 风格克隆 + AI 腔对照表（此外→而且）+ 标题/100-150 字导语/小标题；Drive 代表作样本本地化 |
| REF·去AI味 | 质量层·去AI味 | 已编译+补充 | 8 类检查已编译为 remove-ai-slop.md/deslop.py；占位符保护规则必须保留 |
| REF·Final Editor3 | 质量层·EN 终审 | 采纳改写 | 与 Final Editor1 英文 de-AI 重复，合并 |
| UDW·Final Editor1 | 质量层·EN 节奏 | 采纳改写 | 3-Sentence Rule、1-2 个冷笑括注、Markdown Purity——需补编译 |
| UDW·去AI味 | 质量层·视觉高亮 | 已编译+缺口 | 精准加粗（数据/专有名词/毒舌吐槽）+ 字数保真未单独编译——需补编译 |
| UDW·First Draft Writer（归因公式） | 质量层·证据边界 | 缺口 | 归因公式未进任何 knowledge 文件——需补编译 |

### assembly

| 源资产 | 去向 | 处置 | 关键说明 |
|---|---|---|---|
| REF·中文图文编辑 / Parser2 | assembly | 采纳原样 | 加粗前后空格、>4 行拆分、删 AI 痕迹标签，程序化落地 |
| REF·LLM remover ×2 | assembly | 采纳改写 | 合并为一个排版规范化模块 |
| UDW·output_extractor / Code in JavaScript2 | assembly | 采纳改写 | 文件名/语种路由/H1 提取逻辑复用 |
| REF·Merge Article & Images | — | 弃用 | 与"不加独立图注行"规则冲突（legacy 内部不一致） |

## 二、延后（V1.5 / 未来）

| 源资产 | 去向 | 说明 |
|---|---|---|
| REF·NarrativeGenerator + LCW·Narrative Agent + HITL Narrative Approval | ~~narrative_selection(V1.5)~~ → 已落地（04，2026-08-17） | 双角度互斥保留；6 叙事原型被 2026 三方调研的 8 原型取代；4 字段审批表单映射为 TUI 二选一 + 定向搜证补充。详见 knowledge/narrative-contract.md 与 docs/research/narrative-survey-merge-notes.md |

### narrative 2026 最佳实践（调研报告3 重点，2026-08-17 补编译）

| 资产 | 去向 | 处置 |
|---|---|---|
| 8 原型解剖卡（标题公式/骨架/EO 密度/takeaway） | narrative.py `_ARCHETYPE_ANATOMY` | 采纳原样，仅白名单原型注入提示词 |
| 五类高潜力 hook | narrative.py `_HOOK_PATTERNS` | 采纳原样（HookPatternConfidence，不用 ExpectedCTR） |
| 证据等级阶梯（产品/法律/内部三种语境） | narrative.py `_EVIDENCE_LADDER` | 采纳原样 + 研究引用格式 [机构],[日期],[样本/方法],发现;但[limitation] |
| denominator 规则 / Confirmed-Reported-Inferred-Unknown | 生成提示硬规则 4 | 采纳原样 |
| 真信度四件套 / Observable→Conflict→Decision / 五段证据链 | 生成提示硬规则 1/2/6 + schema 校验 | 采纳并落校验 |
| Reddit/V2EX 作为选题与证据市场（发现问题→可验证假设→一手验证） | 06 定向补证设计输入 | 延后至 06 落地 |
| UDW·Image Adder（A-N 原型库+绝对视觉禁令）+ REF·Image Adder（四原型） | illustration(V1.5) | 与已批准的 visual_plan 合并去重后启用；封面逻辑为新资产 |
| UDW·Structured Output Parser2 | illustration(V1.5) | 活路径插图 schema，与新方案兼容 |
| REF·公众号/LinkedIn MCP 投递、UDW·Final Editor (Universal)、LCW·Parse Pilot Results / Prepare Browser Tasks | delivery(未来) | 浏览器自动化剧本与 SEO 元数据，未来适配器时再评估 |

## 三、弃用 / 基础设施（合并）

- 模型配置节点约 30 个（Gemini pro/flash）：弃用，仅保留"初稿 pro、编辑 flash"成本分层思路。
- Google Drive/Gmail 存储、GitHub 图片上传、Firecrawl VM 启停、scrape.do、Apify、ImgBB、base64 转换：弃用。
- TSV 采集资产（Intent Router、4 车道、Tavily/Brave/知乎/NewsAPI、故障转移）：按决策 1 弃用。
- LCW 7 个孤立实验残留节点（Set Discovery Params/11、旧 HITL、Parse Selectionx、Task Master Agent 等）：弃用，建议人工确认非手动触发路径。
- REF Test-* 夹具节点：弃用，可作样例数据参考。

## 四、缺口（新资产）

1. **双语编辑质量层**（独立质量门）→ 见同目录 `2026-08-14-bilingual-editing-quality-layer.md`。
2. **EN 独立编辑（非翻译）语义**：双轨各自起草，但需显式指令"从证据重写而非翻译"。
3. 叙事选择横向评分标准、outline 显式化（V1.5）。
4. outputs 包校验器（部分已自建）。
5. 封面逻辑、未来 API 适配器（延后）。

## 五、安全与一致性风险

- **凭据暴露**：TSV 5 处（NewsAPI/Tavily×2/Brave/知乎）、UDW ImgBB key、RES scrape.do token 为明文内联，已进 Git 历史，按仓库规范视为暴露并轮换。
- **字数规范**：legacy 5000 词/3000–5000 字与 CONTEXT 的 zh 3500–6000 字 + en 800–1200 词冲突，按 CONTEXT 执行。
- 待统一：target_count 默认 3 vs 5；RSS "93 vs 52"；图注规则冲突；黑名单/mental_models 双份漂移；LCW Extract Brief Text1 悬空引用。
- 墙内抓取依赖浏览器会话：run 开始做会话预检并记入 state；无会话时记 `unavailable` 并降级。

## 六、实测修订（2026-08-14 三车道验证后）

以两个真实墙内 URL 实测定档（详见 `docs/verification/results/2026-08-14-walled-fetch-lane-validation.md`）：

| 平台 | 直连 HTTP | tavily_extract | 本地 Chrome | 路由结论 |
|---|---|---|---|---|
| zhihu.com | 403 反爬 | ✅ 标题+前 3 条高赞回答全文 | ✅ 3 个回答卡片全文可读（登录弹窗不影响文本抽取） | Chrome 主、tavily 兜底 |
| mp.weixin.qq.com | 200，但仅标题+作者+完整摘要（分享页壳，正文不在静态 HTML） | 空结果 | **被浏览器安全策略站点级拦截（不绕行）** | 摘要级可用；全文无可用车道（待用户决策） |

注：上表"全文无可用车道"已被第九节推翻——自有 CDP Skill 通道实测全文 `fetched`；
Browser Use 拦截仍是事实，但不再影响管线（抓取走用户自有工具链）。

微信全文抓取已解决（CDP Skill）；第六节的四选项不再适用。

发现车道同步修订：原"发现延后 V1.5"仅保留"全网主动搜索"；topic 定向的知乎一线素材发现（zhida 直达 → 站内搜索桥接 → Chrome 逐条抓取）实测可用，V1 research 阶段即可按需启用（Codex 会话内执行，不走确定性 CLI）。

## 七、实现落地核验（2026-08-14，资产迁移完成后）

判断层资产已在代码中落地并实测（`src/ai_daily/topics.py`、`research.py`）：

- **VETO**：公关通稿 / 无范式融资 / 增量跑分三类硬过滤（中英双语关键词 + 硬事实信号豁免）。第四条「无 CTO FOMO」改为**排序惩罚**而非硬杀：实测发现关键词硬杀会误伤英文 RSS 主流选题（price war、组织重组等），零 EIC 项现仅在排序中垫底。
- **EIC 三维**：信息差/情绪/战略价值关键词评分进入候选排序，热度降为最后一级 tie-breaker（热度永不压过编辑信号）。
- **信源 ≥3 门槛**：分级落地——当池中 ≥3 个事件拥有 3+ 独立媒体时启用硬门；供给不足时降级为单源候选并如实写缺口。注意：这意味着 GLM-5.3 这类单源事件在多源供给充足时会被淘汰（2026-08-20 实测 Top3 全部 ≥3 源）。
- **Parser[6] schema**：`topics.validate_candidate`（title/research_queries/thesis/sources+http URL），人类/模拟选题落盘前强制校验。
- **research 契约注入**：knowledge/research-contract.md 的 8 条硬规则 + LCW 时间红线（当前系统时间、禁脑补月份日期、[时间未披露] 标注）+ 数据零压缩/微观场景/剥离公关话术，全部注入 Codex OSINT 分析提示；另修复 JSON 输出带前言时无法解析的缺陷。
- **遗留限制**：EIC 的「信息差/情绪」维度在确定性关键词近似下很少触发（真实标题多为产品发布体），战略价值维度主导排序；完整 EIC 语义留给 Codex 判断层（04 叙事阶段继承）。

验证：398 单测全绿 + 17 项 fixture UAT PASS + 真实数据回归（295 簇仅 5 簇被 VETO 命中；Top3 全部 ≥3 独立信源；08-20 live research 分析 completed，时间标注与 [标题](URL) 引用协议可见）。

## 八、bilingual_draft / quality_layer / assembly 落地（2026-08-20，07+08）

双语编辑质量层 spec 的 Python 可检查子集与英文优先闭环已落地：

- **bilingual_draft**：`src/ai_daily/draft_en.py` 从 evidence package 写英文完整稿（Codex 可注入 `codex_runner`，从证据重写、永不翻译）；输入门禁 = 05 审计 `sufficient`（`sufficiency.require_sufficient`）。UDW·First Draft Writer1 的人设/框架与 REF·Final Editor1 的 EN 声线编译为 `knowledge/en-author-style.md`。
- **quality_layer**：`src/ai_daily/quality.py` 实现确定性四道检查的可执行子集——证据边界（无链接/无依据确定性/墙内来源按 fetch 状态逐源降级 = `evidence_recovery`）、去 AI 味（`deslop.check_text_en` 8 类英文检查）、字数 800–1200、每段 ≤3 句、AI 痕迹标签/Markdown 纯度、占位符保护、加粗间距。结果四选一 `pass/pass_with_notes/revise/evidence_recovery`，只检查与打回、不静默改写。
- **assembly**：`src/ai_daily/assemble_en.py` 产出英文自己的标题 slug 包 `outputs/YYYY/MM/DD/<en-slug>/<en-slug>.md` + `sources.md` + `metadata.json`，最终文章映射 `articles/<date>-<en-slug>-en.md`；中文包同步把 `article.md` 改为 `<zh-slug>.md`（两版各用自己语言标题命名，不用通用名 `article`）。封面沿用「图片不阻断正文」。CLI 增 `draft-en` / `assemble-en`。
- **聚类误并修复（BISC）**：`topics.same_event` 的停用词表补齐英文虚词（that/in/is/... 等），消除「brain + that」双 token 误并；真实 BISC 三个无关标题回归全部为 False，合法跨源聚类（DeepSeek / Grok 4.6）保持 True。

验证：546 单测全绿 + `git diff --check` 干净 + `scripts/uat_cli.sh` 17 项 PASS + 子代理 code-review（P1 墙内降级 per-source 与正则、word-count URL 膨胀等已修）。

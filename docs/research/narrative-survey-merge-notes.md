# 叙事方法论三方调研合并笔记

用途：三份独立调研报告（2026 AI 自媒体叙事方法论）的合并工作台。
状态：已收 3/3 份（报告1 = AI自媒体叙事方法论报告_2026.md；报告2 = _v2.md；报告3 = _cdox.md）。裁决已完成，见下方「三方合并裁决」。

## 一致结论（两份都确认，基本可定稿）

- 日常快讯、人事与八卦：废弃为独立原型。
- 算账与商业 → 硬数字账本体（假设/公式/区间或三张账+脚本），空泛"降本增效"禁止。
- 实测类必须含翻车/失败案例 + 可复现步骤；中文横评需产品匿名化免责。
- 新增原型：反共识拆台、政策/合规风险。
- 去 AI 味是流量生死线；LinkedIn 与中文反模式清单高度重合。
- 证据信任排序：一手实测/可复现 > 官方原始 > 社区原话 > 第三方摘要 > AI 总结。
- 中文标题：数字+实测/避坑/成本；"颠覆/革命"式标题已疲劳。
- 证据密度硬规则：每千字至少 1 个可核验数字/代码/原话（具体数值待合并统一）。

## 分歧点（待报告3 + 用户裁决）

1. 生态吃瓜的进化方向：报告1 → 「生态取证体」（commit/时间戳级证据链，抄袭纠纷体）；报告2 → 「人才与组织信号」（离职/收购信号解读）。可能两者都保留为独立原型，待裁决。
2. 账本命名与地位：报告1 → 「供应链账本」独立原型；报告2 → 「成本账本」作为算账子类（未找到独立爆款高频案例）。
3. LinkedIn 主原型：报告1 → 「热辣观点体」轻量帖；报告2 → 「故事驱动决策启示」五步故事体。二者并存还是合并？
4. 硬核拆解：报告1 要求改写（放弃概念科普，强制可证伪判断）；报告2 保留原样+强化（加边界与失败模式）。实质接近，措辞待统一。
5. 「预测汇编/共识地图」仅报告1 提出（低频年度化），报告2 无此原型。
6. LinkedIn 英文赛道政策/反共识案例证据强度：报告1 标「未知」（未找到等量级案例）；报告2 认为存在（360Brew/AI slop 数据化批评）。

## 待办

- 收齐第 3 份后做三方合并，冲突逐条列出交用户裁决。
- 合并产物：knowledge/narrative-contract.md v2026（原型集 + 解剖卡 + 平台差异表 + 反模式黑名单 + 证据密度规则）。
- 联动更新：04 叙事候选生成提示；07 编辑质量层反模式黑名单。

## 三方合并裁决（2026-08-17，用户批准口径）

1. 叙事生成范式从「热点 × 叙事模板」改为「热点 × 可验证冲突 × 证据资产 × 读者决策」（报告3 主框架，1/2 佐证）。
2. 原型集：采用报告3 八原型（FIRST_HAND_TEST / CONTRARIAN_AUDIT / MECHANISM_TEARDOWN / COST_LEDGER / WORKFLOW_PLAYBOOK / POWER_MAP / COMPLIANCE_RISK / DECISION_BRIEF）。报告1「生态取证体」并入 POWER_MAP 的证据链要求（commit/时间戳级）；报告2「人才与组织信号」= POWER_MAP 子形态。
3. 备用形态（不参与每日路由）：预测汇编/共识地图（低频年度化）、故事驱动决策启示（LinkedIn 专属帖）。均不进八选一。
4. 叙事路由前置：先做 EVIDENCE INVENTORY（EO 盘点）→ TENSION DETECTION → 原型白名单，Codex 只能在白名单内选 2 个互补/对立原型；KILL CONDITIONS 硬门槛照报告3 执行。
5. EO 定义 + 密度：中文深度稿每千字 4–6 EO、LinkedIn 单帖 2–4 EO，至少 1 个作者亲自产生的 artifact（log/repo/prompt/账单/截图）。
6. 硬性结构规则：开头 Observable→Conflict→Decision；正文 Claim→Observable→Source→Limitation→Decision；结尾 Decision Rule + 改变判断的触发条件；真信度四件套（≥1 失败 + ≥1 limitation + ≥1 artifact + 1 句只有调查过才写得出的句子）。
7. 反模式黑名单：三份合并去重（LinkedIn：Stop X Start Y / It's not X, it's Y / 无据 Hot take / delve-leverage-game changer / 万能提问结尾；中文：炸裂·颠覆·保姆级·最全·终极 / 空洞金句 / 无信源“业内人士透露” / 工整排比 / 未来已来）。
8. 诚实边界：无公开 CTR 数据 → 字段用 HookPatternConfidence 而非 ExpectedCTR；证据信任排序标记为「编辑策略（推测）」，非统计结论。
9. 候选评分四维 + 平台权重：LinkedIn Evidence .35/Decision .30/Conflict .20/Freshness .15；公众号 Conflict .30/Evidence .25/Decision .25/Freshness .20；知乎 Evidence .35/MechanismDepth .30/Conflict .20/Freshness .15。
10. 报告3 正文中的 cite/turn 标记在编译进 narrative-contract.md 时必须剥离，保留其结论与出处事实。

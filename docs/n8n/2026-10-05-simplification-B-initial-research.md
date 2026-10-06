# 精简重构 B — 选题到初轮研究

[KNOWN][HIGH] Mother draft 9e023eb2-3642-4eff-93b9-3dc3961318b5，49节点；生产 activeVersion 仍为 c94debcc-2fe0-438a-a3df-a1d699740c99。本阶段不发布、不发真实邮件。

## 已验收主线

[KNOWN][HIGH] 执行708验证真实采集材料→5题→合成选题答复→原 Parse Selection1；38条材料、5个候选、用户补充方向和原始来源绑定均保留，未启动研究。

[KNOWN][HIGH] 执行710/711验证真实采集→合成选题→Brave发现→原 Tavily 正文读取：9个请求正文、材料38→46。该轮暴露页面家具图片噪声和未跟进来源引用，因此没有把它判为研究完成。

[KNOWN][HIGH] 712/713/714验证部分抓取失败、全部失败和仅浏览器来源时的降级；715读取真实种子页及其官方引用页，保留原始正文、来源链接、图片alt与失败状态。716单独验证原 Universal Browser Pilot 可只读 X 帖子并返回DOM正文。

[KNOWN][HIGH] 执行717完成当前B的原生集成验收：Topic Survey → 合成选题 → Parse Selection → Brave → Tavily → Browser Pilot 719/720/721 → 同一上下文合并。所选题为“每月 903 美元：美国最重度的 AI 付费用户在买什么？”。公共正文4篇，Browser成功2篇；第3个知乎页面正文读取超时被显式记录，已有材料仍返回。最终材料46条、未审图片候选15个、来源链接11条，publication.state=NOT_PUBLISHED。

[KNOWN][HIGH] B6只在现有 Brief Data Extraction 中增加确定性图片家具过滤：SVG/ICO 及 favicon/logo/icon/avatar/sprite/emoji/badge/spacer/pixel/tracking/analytics 路径不进入候选；正文Markdown图片、普通位图及无扩展名图片继续保留。局部回归测试先RED（icon/logo泄漏）后GREEN。

## 当前数据原则

[KNOWN][HIGH] 一份上下文贯穿 B：topics/materials/selected_topic/human_instructions/target_urls/initial_research/image_candidates/source_links。原始正文保存在 material.retrieval.raw_content；不制造 dossier、work order、receipt 或写作授权快照。

[KNOWN][HIGH] 固定公开来源走确定性 Brave+Tavily；登录墙/社区网页只在 browser_urls 中交给已有 Browser Pilot，只读、失败停止，不换访问路线。图片候选全部 status=unreviewed，采集到不等于可发布。

[INFERRED][HIGH] 下一阶段 C 从 initial_research_ready 直接做一次 Deep 适用性判断。News/Deep 不再并行跑两个提案；News 无 Narrative 人工审批，Deep 只有一次 Narrative 确认/修改。两条分支随后都进入同一个定向补查接口。

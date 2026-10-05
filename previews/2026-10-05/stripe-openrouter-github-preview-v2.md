# Stripe 要买 OpenRouter：模型路由为什么成了支付公司的生意？

![一张空白请求卡经过轨道岔口，通向几条无标记的通道；岔口下方有接住硬币的账务托盘。](https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/n8n/images/20261005/test_visual-native-598/COVER_IMG-630.png)


在编程助手 Cline 里，用户可以给 AI 请求的去向排个序：更看重价格，就把便宜放前面；更在意速度，就优先考虑延迟。看起来只是几行设置，背后却决定了每次请求交给哪家 AI 服务商、花多少钱、等多久。

这类“模型路由”如今进入了 Stripe 的版图。2026 年 8 月 19 日，OpenRouter 告诉用户“加入 Stripe”，Stripe 也宣布已同意收购这家公司。但公告不等于交割完成：交易仍须满足惯常交割条件，OpenRouter 当时预计未来数周完成。

所以，用户眼下最关心的不是收购手续，而是那几行设置还在不在。

## 路由不是选模型，而是选请求怎么走

OpenRouter 是一个模型网关。开发者接入一个接口，就可以把请求发送给多家 AI 模型供应商；每次请求具体走哪一家、用哪个模型，可以由开发者选择，也可以由路由机制决定。

这里有两个不同的问题：用哪个模型，以及请求通过哪家供应商送过去。路由处理的是后一个问题。

2025 年 3 月 23 日，编码助手 Cline 在 3.8.0 版本里加入了“对底层提供商路由排序”设置。发布说明的作者 Nick Baumann 介绍，用户可以按吞吐量、价格或延迟设置优先级；默认方式则在价格与可用性之间取平衡（[Cline 3.8.0 发布记录](https://cline.bot/blog/cline-3-8-0-workflow-integration-account-management-and-provider-optimization)）。

换句话说，模型路由不只是后台的一套技术名词。它可以直接变成用户的选择：预算紧，优先考虑价格；赶时间，优先考虑速度。

Stripe 在公告中把这件事概括得更宏观：OpenRouter 会根据任务复杂度、价格、速度和可靠性动态路由请求。公告还列出 NVIDIA、Zoom 和 Lovable 为 OpenRouter 的用户。

## 路由决定了钱花在哪，也决定账单怎么看

请求走不同的路，成本、速度和可靠性可能都不同。AI 模型通常按 token 计费；token 可以粗略理解为模型处理的文本量。企业用 AI 越多，“这次请求送到哪里”就越像一道财务选择，而不只是工程师才关心的设置。

Cline 的更新记录里，能看到这种选择如何落到日常使用中。Cline 3.8.0 让用户在 VS Code 扩展里查看 Cline 账户的账单、额度消耗和交易历史，不必跳出去另找页面。Cline 团队还称，OpenRouter 的 `usage_details` 让成本追踪更可靠。

一个多月后，Cline v3.14 又为 OpenRouter 和内置 Cline 提供商加入缓存状态界面，让用户看清缓存是否启用。这解决的是“我正在用缓存吗”，并不显示节省金额或缓存命中率。同一份发布记录里提到的 Gemini、Vertex 缓存逻辑和计价更新，则属于其他提供商，不能算到 OpenRouter 名下（[Cline v3.14 发布记录](https://cline.bot/blog/cline-v3-14-improved-gemini-caching-newrule-command-enhanced-checkpoints-key-updates)）。

路由让请求可以在服务商之间选择，账单与状态界面让用户看见部分使用情况。两者放在一起，AI 支出就不再是一笔只知道总数、却看不清去向的费用。

![桌面上几条通道分别通向小票和不同高度的硬币堆，旁边放着一个看不见内部的零钱袋。](https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/n8n/images/20261005/test_visual-native-598/IMG_1-630.png)

*从一笔总数，到看见部分去向。*

## Stripe 看中支出管理，OpenRouter强调中立

Stripe 联合创始人兼 CEO Patrick Collison 在公告中把 OpenRouter 和企业盈利直接联系起来。他的说法是，企业把 token 当作构建 AI 的核心成本；Stripe 与 OpenRouter 将通过智能路由请求、高效使用 token，帮助企业提高盈利能力。

OpenRouter 团队解释为何选择 Stripe时，强调的则是使命和中立性。团队表示，只有少数公司是他们会考虑出售给它们的对象；选择 Stripe，是因为它能让 OpenRouter 做得更多、更快，同时不牺牲使命、中立性和市场地位。团队还提到 Stripe 的客户网络、互联网企业增长数据，以及反欺诈和滥用方面的经验。

这两套说法关注的并不是同一件事：Stripe 谈的是 AI 成本如何影响企业经营，OpenRouter 谈的是加入 Stripe 后如何继续做一个中立的模型网关。

媒体则把交易放进企业管理 AI 支出的趋势里。彭博援引匿名知情人士称，交易金额超过 70 亿美元，并将其与企业寻找低成本 AI 方案的需求联系起来（[Bloomberg](https://www.bloomberg.com/news/articles/2026-08-16/stripe-nears-deal-to-buy-ai-firm-openrouter-for-over-7-billion)）。TechCrunch 的解读是，Stripe 正从收入管理延伸到 AI 支出管理，报道还引用 PitchBook 分析师 Franco Granda 对 AI 资本流动的判断（[TechCrunch](https://techcrunch.com/2026/08/19/stripe-didnt-really-buy-openrouter-because-of-the-singularity/)）。

## “不变”落在用户每天会用到的地方

OpenRouter 在公告中向现有用户承诺：使命、名称、产品、路线图和现有集成不变；对模型与服务商保持平等、中立的承诺，也不会因母公司变化而改变。

这些承诺并不抽象。“现有集成不变”，关系到 Cline 这样的应用能否继续使用路由、账单和缓存状态等功能；“模型平等与中立不变”，关系到平台是否仍按用户设定的条件处理请求；产品和路线图不变，则决定未来会怎样发展。

交易尚未完成，因此现在能说的，是 OpenRouter 已承诺维持这些安排，而不是收购后已经验证它们会如何运作。对用户来说，真正值得留意的也不只是应用能不能打开：路由选项还在不在、账单是否仍看得清、设定的优先级是否仍由自己作主。

Stripe 看中的，或许正是这些看似不起眼的选择：AI 请求最终走哪条路，决定了企业的算力账单落在哪里。

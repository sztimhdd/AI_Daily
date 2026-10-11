# 02 — 主动取材与混合配图

**Parent:** [配图 MVP 规格](../spec.md) · [EPIC 02](../epic-02-content-driven-visuals.md)

**What to build:** 在一个真实 Deep 样本中复用现有取材和图片候选路径，主动寻找贴题源图并规划后交付双语 Markdown。默认源图与生成图混搭，Deep 不默认全生成；用完整真实输入观察模型是否回应作者对原图的要求，不提示必须选择哪张图，也不强制图片数量或每篇必须有 source。没有合适素材时可不含 source 并记录或收窄表达，不硬凑；不得生成冒充真实测试、Demo 或社区截图。只有实际取得的图片或从实际图像读取的可靠视觉摘要才视为已理解图片；缺少能力或授权时报告 `BLOCKED` 并保留稿件。

**Blocked by:** 01 — 现有素材经共同规划器交付双语配图 Markdown。

**参考方法（设计输入，未在 AI Daily 验证）：** [Article Illustrator 与 qiaomu-ppt 取材摘要](../../../docs/research/ai-daily-visual-reference-kb-2026-10-10.md)：先定位视觉用途，区分真实来源素材与解释/氛围生成图；候选元信息只作线索，不能替代实际看图。

**Status:** partially-verified — bounded local UAT passed; broader sourcing and generated-image behavior remain unverified.

> 状态依据：2026-10-10（Halifax），883/884 完成一轮有界 UAT。此状态只记录已见局部行为，不表示整票或 EPIC 完成。

> 历史观察：875 使用缩减且漏掉编辑意见的无效回放输入，不作为原 856 行为证据。877 才是校正输入下的单次观察：3 generated / 0 source，未实际生图，模型内因 UNKNOWN；Deep 对贴题 source 的采用尚未解决。本票用真实 Deep 任务和完整材料观察其到双语 Markdown 的结果，不把观察升级为评分、配额或额外准入门槛。

## 2026-10-10 bounded UAT — partial pass

- 883 reused 879–882 evidence. The free Planner call retained 75 candidates, 19 materials, the 79-character editor note, and three actual image descriptions. Zhihu `ContentText` was present for all 10 results.
- 883 planned one source image and three generated images. The selected source is a community-reposted screenshot of Haiku 5.5's official release post. It provides release background; it does not show a community task benchmark, tier-price table, or task-cost comparison.
- 884 replayed that plan without another Planner call. The selected source passed through the existing download/upload/normalize/Markdown path and appeared in both language editions. The original bodies remained unchanged. No new generated image was created.
- **Locally passed for this ticket's bounded scope:** a real source candidate reached the existing bilingual Markdown delivery path, and the repaired candidate/context handoff preserved its real inputs.
- **Non-blocking limitation:** the image is release background. It does not prove that retrieval found a task-cost benchmark image. The image follows a pricing paragraph, and its caption says that it does not show tiered prices. The controller judged the placement and caption less readable. Observe this in Issue 03's delivered-article review. Do not reopen Issue 02 or rerun the model for this point.
- **Still unverified:** whether community retrieval finds enough task-test/benchmark imagery for this use case, and whether the three generated plans become usable images in delivery. This sample does not prove broad source discovery or generated-image output. Keep the generated items as plans, not completed images.
- The source is context for the release, not proof of a price or task-cost claim. Do not generalize this result to community test-image coverage.

- [ ] 至少一个有真实图片需求且已授权的 Deep 样本，经主动取材和现有候选/规划路径到达配图后的双语 Markdown；源图与生成图按文章需要组合，记录实际选择与未选择原因。
- [ ] 复用现有知乎 API/CLI、Browser Pilot；用户提供明确微信文章 URL 时沿现有能力读取正文内实际图片及图旁语境。
- [ ] 只有实际取得图片或从实际图像读取的可靠视觉摘要才作为图片理解依据；不能把裸 URL、文字标签或旧 prompt 当作看过图片。
- [ ] 没有合适 source 时可不含 source 并记录或收窄表达；若有贴题 source 且作者要求仍未采用，记录原因并将该效果标为未验证/未解决。不得将 News 下载通路或旧 Deep generated 输出作为此效果的替代证明。不设每篇平台配额，不生成冒充真实测试/Demo/社区截图的图片。
- [ ] 缺少登录或能力时明确 `BLOCKED`，不切换模型/provider/harness 或生产取材路径，已保存稿件保留。
- [ ] 复用既有双语 Markdown 验证入口和有效回执；仅验证新边界。

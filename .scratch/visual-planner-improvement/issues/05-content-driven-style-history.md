# 05 — 内容驱动风格与近期封面参考

**Parent:** [配图 MVP 规格](../spec.md) · [EPIC 02](../epic-02-content-driven-visuals.md)

**What to build:** 先明确文章要表达的内容，再决定画面表达和风格。风格库说明适用内容与气氛，封面计划说明主体、构图、配色和手法。最多参考最近三篇不同文章的实际封面图像，或从实际图像读取的可靠视觉摘要，以减少相似观感；不强制轮换。旧 prompt 只辅助理解创作意图，不能替代实际图像。历史不足或读取失败时降级并继续交付正文，读取失败时注明未参考。

**Blocked by:** [04 — 三平台共享无字封面](04-shared-text-free-cover.md)。

**参考方法（设计输入，未在 AI Daily 验证）：** [Baoyu Cover Image 与官方 Gemini 图像输入文档](../../../docs/research/ai-daily-visual-reference-kb-2026-10-10.md)：借鉴内容、色彩与呈现方式的区分。实施前核查当前节点和模型支持的图片输入；参考文档不证明现有链路支持。最近三篇是本项目的软参考规则。

**Status:** partially-verified — controller accepted this ticket's bounded result; actual new style images remain for 03.

> 状态依据：2026-10-10（Halifax），主控按 888/889 的实际历史读取、隔离输入和自由规划回执接受本票范围。此状态不表示真实新风格图或整个 EPIC 已完成。

## 局部验收与边界

- 888 在实际同文件夹 14 天窗口取得 9 项 metadata，下载 4 个包，得到两篇有效封面参考 839/832。实际 canonical 856 为当前文章并被排除；832/827 按真实 content_id 去重；815 无 cover，不充第三个位置。
- 889 实际执行两次历史单图读取和一次自由 Planner。参考描述与 URL 一一对应，只存于独立 recent_cover_references。75 候选、19 材料、79 字符编辑意见与 3 条当前实际描述保持。历史 URL 未进入本篇 source pool，旧 prompt 未冒充视觉观察。
- 规划已使用内容/视觉任务/主体/构图/配色和具体手法。cover 无字约束与正文示意图标签权限均到达最终生图 prompt。实际新风格图片尚未生成，留待 03；不以单次自由规划证明稳定效果。
- 首次 client response-stream 中断已在原任务恢复，未重发既有执行，恢复阶段新增模型和测试均为 0。它不是 n8n 产品错误。旧大响应读取分支在此前两次失败后保持停止。一个本地 helper 对 history prompt 结构的误读已用保存数据修正，无请求重试。
- UAT TEMP 已清理。clean draft `5f4cc08c-b248-47cf-852e-61dcdcd2d86a` 对 `3a57eea3-2ca1-4a5e-9c81-a55e1e0a8697` 业务 diff 空；105 节点，active `96042bba-9621-4571-98b6-976dc819c4fc` 不变。

- [x] 风格说明用途与气氛；规划先写内容和画面表达，再写主体、构图、配色和手法。实际新风格成图仍待 03。
- [x] 近期参考只使用最近三篇不同文章的实际封面图像或从实际图像读取的可靠视觉摘要；prompt 不作为视觉参考。
- [x] 不强制风格轮换。历史不足或读取失败时降级，不阻断正文，也不新增历史账本、向量库或评分系统。

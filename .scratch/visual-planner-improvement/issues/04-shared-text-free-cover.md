# 04 — 三平台共享无字封面

**Parent:** [配图 MVP 规格](../spec.md) · [EPIC 02](../epic-02-content-driven-visuals.md)

**What to build:** LinkedIn、知乎和微信按文章内容复用合适的源图或生成图作为同一张无字封面。保留来源和 Alt 信息，封面不裁切、不叠标题或 Caption，并交付可读的双语 Markdown。封面处理失败时保留稿件，不要求重新生成。

**Blocked by:** 01 — 共同视觉规划。

**参考方法（设计输入，未在 AI Daily 验证）：** [Baoyu Cover Image、KarenSpinner 封面方法](../../../docs/research/ai-daily-visual-reference-kb-2026-10-10.md)：从文章含义和具体对象明确主体、动作关系、构图、配色和手法。保留本项目无字共享封面规则。

**Status:** passed — controller accepted the bounded cover result.

> 状态依据：2026-10-10（Halifax），主控已查看 887 实际封面及双语 Markdown，接受本票范围。此结论不表示其他生成计划或整个 EPIC 完成。

## 已验收局部结果

- 886 为一次自由 Planner 调用。887 实际生成并交付一张 PNG 封面，1672×941，无可见文字，未裁切。双语 metadata 与 Markdown 使用同一 URL，封面 Caption 为空，正文源图保持原有 URL、Alt、Caption 和锚点。
- 受控封面失败检查保留正文和正文源图。其他新规划的正文生成图未在本轮完成，不作为本票封面验收成果。
- Alt 中的“计数器”与实际手刨工具有小差异。主控将其记录为非阻塞，不重抽或追加创作 gate。
- UAT TEMP 已清理。clean draft 为 `83a9ba97-8d03-4127-9c3f-d062cae56372`，对 `04cc31a4-c7fa-4a5f-9510-0f375221c880` 业务 diff 为空。99 节点，active `96042bba-9621-4571-98b6-976dc819c4fc` 不变。

## 当前实现证据

- 只修改 `Deep Visual Planner`、`Parse Deep Visual Plan`、`Assemble Visual Package` 三个现有节点参数；无新增节点或接线。draft 从 `e27ae902-e501-4398-ba86-d4fa868feb60` 更新到 `04cc31a4-c7fa-4a5f-9510-0f375221c880`，active `96042bba-9621-4571-98b6-976dc819c4fc` 与 99 节点数不变。
- Planner 说明封面仅在实际视觉描述确认 source 原图本身无字且适用时原样复用；否则规划无字 generated cover。不得删改真实源图文字，不裁切。无字规则限 cover。封面保留各语言 Alt，不产生 Caption。
- Parser 接受 source role `cover` 和 `cover_field`，继续校验候选 URL、来源及双语结构。已有 body source 的 Alt、Caption、来源和段落锚点处理不变。
- Package 将 cover Caption 置空。既有路径把同一 asset URL 写入两种语言的 cover metadata，并在双语 Markdown 复用；body image caption 仍按原路径插入。封面失败仍走原失败/保稿路径。
- 局部代码检查覆盖 source/generated cover、共享双语 URL、无 cover caption、body source metadata、Markdown 输出及失败保稿。没有执行 workflow、模型、图片、外部 API、Drive 或邮件操作。

- [x] LinkedIn、知乎和微信的双语 Markdown 复用同一张按内容选择的封面图。
- [x] 封面无标题和 Caption，不裁切；来源及 Alt 信息按现有方式保留。
- [x] 封面失败时保留正文和已保存稿件；不要求重新生成封面。

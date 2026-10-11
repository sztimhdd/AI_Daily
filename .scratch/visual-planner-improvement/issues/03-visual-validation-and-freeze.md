# 03 — News/Deep 成品验证与冻结

**Parent:** [配图 MVP 规格](../spec.md) · [EPIC 02](../epic-02-content-driven-visuals.md)

**What to build:** 复用 02 的真实 Deep 取材/规划观察和既有 News 实际源图通路，检查 News 与 Deep 的配图后双语 Markdown；只对必要的新边界补证，不额外制造测试轮次。源图与生成图按内容需要选择，不强迫每篇必须有 source。若 Deep 有贴题 source 且作者要求仍未采用，记录原因并将默认混搭效果标为未验证/未解决；不能以 source 下载通路或旧 Deep 生成输出代替。封面、图片和图注应可打开、可读，图片故障不得丢失正文或另一语言稿。不自动发布或发送邮件。

**Blocked by:**
- [02 — 主动取材与混合配图](02-community-image-sourcing.md)。
- [04 — 三平台共享无字封面](04-shared-text-free-cover.md)。
- [05 — 内容驱动风格与近期封面参考](05-content-driven-style-history.md)。

**Status:** locally-complete — 本轮限定局部功能由主控验收，不表示生产 E2E 或稳定质量认证。

> 状态依据：2026-10-10（Halifax），主控已查看 6 项实际资产，确认混搭、不同画法及两张无可见文字的封面，接受本轮局部功能。890 Deep（3 generated / 1 source）、891 无模型机械组装、892 News（1 generated / 1 source）及四份双语 MD 已保存。此 worker 只做恢复快照和文档，不另做 UAT 或视觉评审。

> 历史会话记录：Harvey 长会话累计两次 Luna client 流中断，已关闭。该会话的 03 阶段只做 budget/getWorkflowDetails，未加 TEMP 或起测试，失败计数 2 保留。后续转为同 Luna 的 fresh 短上下文 UAT03（Averroes，`01a12792-8baa-7aa3-b64a-88c84d6cbab4`）。旧会话数据量可能相关仅为推测，未证实根因。旧大响应分支保持停止。

> News 保存方法：Hypatia 对 892 Normalize Visual Asset 只做一次安全小 metadata 读取，取得真实两资产的 per_language/provenance/placement，结合完整 News fixture 和原版 Assemble/MD 代码机械组装两份 MD。文件记录为 `replayed-from-observed-assets`，并非原生 MD 回读；无新模型、workflow execute 或生成。

> 恢复状态：fresh Mother 为 `88b6ec3f-3738-42e7-82cf-e500a1355fd3`，105 节点、零 TEMP，原生业务 diff 对 `5f4cc08c-b248-47cf-852e-61dcdcd2d86a` 空。完整 native draft 与旧 active `96042bba-9621-4571-98b6-976dc819c4fc`（93 节点）JSON、依赖快照及 hash 已保存。新 draft 尚未激活，未发布或执行恢复。

## 非阻塞项与结论边界

- News 原生 MD 大响应回读尚未解决；本轮以真实已观察资产和原版代码的纯机械组装完成本地交付，不把 replay 写成原生回读。
- Deep 原图是发布素材，News 原图是既有鹈鹕自行车示例图，不能泛化为每篇都会取得核心实测图。个别视觉选择、位置或 Alt/Caption 的读感仍需实际使用改进；不追加评分、创作 gate、修复票框架或新测试。
- 本轮证明有界 News/Deep 图文功能与恢复材料，不证明生产调度、发布链、每日稳定效果或全项目完成。

> 历史观察：875 是缩减且漏掉编辑意见的无效回放输入，不作为原 856 行为证据；877 是校正输入下的单次观察，返回 0 source、未实际生图，模型内因 UNKNOWN。它不证明 Deep 采用或拒绝真实素材的根因。验证只记录实际输入、执行结果和最终交付；单次自由模型成功不代表稳定效果。

- [x] News 与 Deep 各有本地双语 Markdown；News 为 replayed-from-observed-assets，非原生 MD 回读。
- [x] 复用有效回执，取得本轮实际 source/generated 混搭结果；不设每篇 source 配额。
- [x] 主控已查看实际资产，确认共享封面无可见字、未裁切；选图读感限制如实记录。
- [x] 复用既有受控失败保稿结果，保留正文、语言版本和保存状态；未新增失败测试。
- [x] 零 TEMP、native 恢复快照及 hash 已保存；未执行恢复或激活。
- [x] 已记录原图背景/示例用途和非阻塞限制；不由节点 success 或单次响应推断稳定质量，不程序审核、发布或发邮件。

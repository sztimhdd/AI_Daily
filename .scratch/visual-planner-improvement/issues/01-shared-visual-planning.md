# 01 — 现有素材经共同规划器交付双语配图 Markdown

**Parent:** [配图 MVP 规格](../spec.md) · [执行计划](../execution-plan.md#01--现有素材经共同规划器交付双语配图-markdown)

**What to build:** 复用共同 Visual Planner，让 News 和 Deep 按文章内容规划现有真实图片或生成插画，并交付到中英文 Markdown。News 优先真实图片，Deep 可混用。沿用已有 21 种风格并按主题选择；图片数量由内容需要决定。移除 News 正文必须包含 `source_url`、同源最多一张及仅限五种风格的限制。使用既有稿件到 Markdown 的局部路径，不重跑写作。程序只处理素材安全、可用性、路由、插入和失败保稿，不审核创作成果。保留空稿、正文不可取得或 API 报错时保稿且不误发。

**Blocked by:** None — can start immediately.

**Status:** resolved — 2026-10-10 第一票局部技术验收通过（未发布）。Deep 生成分支沿用既有 856 真实回执，Deep 社区选图效果列为 02/03 待验证项。

- [x] News 与 Deep 的保存稿件均可经共同规划路径输出配图后的双语 Markdown；News 优先真实图片，Deep 可混用真实图片和生成插画。 —— News 实际执行（874 规划、876 真实 source 图下载→GitHub 上传→双语 MD）；Deep 本轮只到规划/Parse（877：3 generated、0 source，**不是已生成的 3 张图**），生成与 Markdown 沿用 2026-10-09 的 856 真实生成回执 + prompt 传递检查，本轮未实际生图。
- [x] 规划可使用五种限制以外的既有风格，图片数量按内容决定；不以图片数量或风格作为创作硬门槛。 —— 874 选到 minimalist geometric poster，877 选到 conceptual still life / technical diagram / minimalist geometric poster；节点检查含 5 类外风格传递与无固定数量截断。
- [x] 成功结果能展示在统一的“配图后双语 Markdown”入口，图像位置可读；不重跑写作。 —— 876 产出 zh/en 双语 MD，锚点插入、图注与两种语言正文保留，未重跑写作。
- [x] 图片取得或处理失败时，正文、另一语言稿及已保存状态均保留；空稿、正文不可取得及 API 报错仍不会丢稿或误发。 —— 由本票已有的节点级失败回执满足（planner/parse 报错、未保存跳过均保留双语稿），UAT 未重复注入同一故障。
- [x] URL 输入安全和既有任务路由仍有效；复用能满足本票的有效成功或失败回执，不重复相同测试。 —— 节点检查含未知候选与非公网 URL 拒绝、News/Deep 双路由；复用既有回执，未重复相同测试。

## Implementation checkpoint (2026-10-10, draft only)

改动落在母工作流 `xR7fM1ZhxlMTUy0L` 的运行草稿：draft `96042bba-…`（93 节点）→ `781f637c-…`（92 节点），`activeVersionId` 未变，未 publish/unpublish、未执行 n8n。触点只有五处：`Visual Mode` 输出 0 改接 `Deep Visual Planner`；`Deep Visual Planner` 提示改共同规划并传入 `story_mode`、风格库换成 21 类自然语言库；`Parse Deep Visual Plan` 删 5 风格白名单、`style` 非空描述直接写进生成 prompt；`Assemble Visual Package` 统一取共享计划；删除被替代的 `Prepare News Visual Jobs`（旧的正文含 `source_url` 与同源一图门槛随之消失）。Downstream Split/Loop/Download/Generate/Upload/Normalize 与 Markdown 保存链未改。

局部证据：before snapshot 与 expected-after 原始结果保留在本地忽略目录；当时记录的同一参数源检查为 21/21（改前 11/21），线上版本差异为 1 删 / 3 改 / 1 加连线 / 2 删连线。原始快照未纳入公开文档。

仍未验证：真实模型按新提示挑图（未调用 Planner/生图）；News 真实自然路径（本轮 News 只有 routing/parse 级检查，素材来自真实保存回放稿 837）；社区取材属第二票。临时节点未加、runtime 未跑。

## Answer (2026-10-10 独立局部技术验收)

**结论：** 第一票局部技术验收通过。共享 Visual Planner 与 source 图通路在保存稿件上实际跑通；生产未发布，`activeVersionId` 未变。

线上终态：最终 draft `a1bcbe17-0d47-45a3-bf0f-4d0a32912183`（92 节点），与 coder 交付的 781 业务 native diff 为空（nodesAdded/Removed/Modified、connections 均为 0），TEMP 节点与测试 pinData 已清理，`activeVersionId` 仍为 `96042bba-9621-4571-98b6-976dc819c4fc`，waiting 871/365 未动。

实际通路：874 用保存的 News 稿件（837）经共享 Planner/Parse 选出 1 个 source 任务 + 1 张 generated 封面（minimalist geometric poster）；876 复用该 source 任务实际下载→上传 GitHub→组装双语 MD，源图 HTTP 200 `image/webp` 31,470 bytes，Pillow 解码 914x762，MD 回读与运行输出一致。21/21 节点检查与三个永久节点 config 校验通过。

Deep：877 用校正后的 856 输入（57 候选含 8 个 Arena 候选、18 条匹配材料、原 79 字符 editor_note）实际跑 Planner/Parse，success、planned、warnings 空，返回 3 generated / 0 source（styles：conceptual still life、technical diagram、minimalist geometric poster），**未实际生图**；raw 输出未说明为何未选 source。875 的输入被缩成 1 图/1 材料且漏 `narrative_feedback`，不作为 856 行为证据。

详细回执与原始输出保留在本地忽略目录，未纳入公开文档。

UAT 曾把工作流 ID 末尾的大写 `L` 误读为小写 `l`，在同一路 MCP 用正确 ID 重读成功；这是调用笔误，不是权限阻塞或 provider 失败，保留记录但不计为产品问题。

**仍需 02/03 验证的局限：** Deep 是否会在有合适真实素材时主动选中社区/真实图片，本轮未得到证明（877 单次观察为 0 source，原因未知）。该项列入 02/03 观察项，不新增票、Agent 或程序门槛。本票不宣称 Deep 社区选图效果已解决、非全 E2E 通过，也不宣称稳定创作效果。

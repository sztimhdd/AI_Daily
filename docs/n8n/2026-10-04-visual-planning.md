# 配图编辑接口检查点

## 完成范围

[KNOWN][HIGH] 已完成“保存的编辑稿 → 现有配图编辑 → 计划校验”的隔离测试。正文图由编辑决定，允许零张、一张、多张，封面单独保留。没有新增模型、研究或评分流程；没有生图、上传、邮件或发布。

[KNOWN][HIGH] 增加一个小型 `V2 Visual Input` 绑定未发布编辑稿；修改现有 `V2 Visual Planner`、`Structured Output Parser3`、`V2 Visual Plan Validator`。去掉英文平台硬绑定和正文 1–2 张限制，编号支持 IMG_1…IMG_n。保留现有 15 种可执行插画风格，没有声称支持尚未实现的精确图表渲染。

[KNOWN][HIGH] 结果继续返回 `writing_preview.v1`，新增 `visual_planning_status` 和 `visual_plan`；有效计划位于 `visual_plan` 内，仍使用 `visual_plan_validated.v1`。错误计划或模型错误保留源预览，计划为 null，并返回简短错误码，不改文章，不声称生图完成。未完成文字编辑的输入在模型调用前拒绝。

## 验证

| 执行 | 输入及结果 |
|---|---|
| 601 | 封面＋0 张正文图：真实代码通过，正文保留。 |
| 602 | 封面＋1 张正文图：通过，加粗段落锚点保留。 |
| 603 | 封面＋3 张正文图：通过，编号及段落顺序保留。 |
| 604 | 只将一张图的锚点改成段落片段：返回 planning failed、原文保留。 |
| 605 | 重用已保存的 598 完整编辑稿，真实配图编辑运行 19.810 秒，选择一个封面、一张正文图，校验通过。 |
| 606 | 待审/编辑失败输入：入口拒绝，未调用模型。 |

[KNOWN][HIGH] 601–604 为合成计划的代码测试，绕开模型与 parser，不冒充模型创意；605 为真实模型及 parser 执行。605 的封面是轨道岔口与硬币托盘，正文是可见费用路径与不透明钱袋的对照，采用现有微缩场景风格。它选择一张正文图，不代表恢复固定一张的规则。没有图片产物，未做图片效果验收。

[COMPUTED][HIGH] 新增 8 项本地测试先在缺少新配置时全部失败，最终 8/8 通过。覆盖数量、编号、空输入、非完整/重复/代码锚点、失败保稿和不泄露原始错误。配置校验通过；不是文章审美评分，也不是全仓 CI。克隆仍因 DNS 失败，使用隔离本地目录与 GitHub 连接器保存。

## 当前状态与恢复

[KNOWN][HIGH] Writer `nHxILnDVz541Cu5P`：起点 `9a469034-7a66-4551-aa0a-7e538bbf6078`，最终 `48bf6aef-5cee-491d-8b56-35a9fea02168`，80 节点，active=false、activeVersionId=null。临时 webhook 已删除；保留 `Visual Input → Planner → Validator`，Validator 暂为终点。原中文预览链、母流程、模型与凭据未改。

[KNOWN][HIGH] 本环节尚未连入中文主链。旧编译器仍要求顶层计划及 2–3 个任务，collector、assembler 和 package 仍有正文数量旧限制；已断开 Validator → Compiler，避免错误调用。这些限制尚未修复，不声称整个视觉链支持动态张数。

[INFERRED][HIGH] 下一单元复用现有编译器与图片请求构造：从 `preview.visual_plan` 读取有效计划，零张/一张/多张正文图都不截断；保留源文章和失败返回。然后才接生图/组装及中文主链；不重抽初稿或再建视觉编辑。

## 保存与复现

[KNOWN][HIGH] 同一分支 `n8n-v3-handoff-20261003`：节点参数与两段代码集中在 `src/n8n/visual-planning.nodes.json`，合成 payload 与测试在 `tests/n8n/visual-planning.test.cjs`。模型计划、文章和调用输入保留本地，不提交公开仓库。上述 JSON 是局部节点配置，不是完整工作流导出；恢复使用 n8n 版本历史。

```sh
node --test tests/n8n/visual-planning.test.cjs
```

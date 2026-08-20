# 02 — TUI 交互与进度层

**What to build:** 从选题这第一步开始，终端里可视化展示 run 的阶段进度（当前阶段高亮、已完成打勾、待完成置灰）；选题时用富文本展示 3 个候选（标题 / thesis / hook）并数字选择，把选择落盘为 durable 决策。选择组件做成可复用，供后续叙事选择接入同一套交互。

**Blocked by:** None — can start immediately（选题候选复用 V1 已有的 candidates / choose-topic）

**Status:** completed

- [x] 终端能展示 run 当前阶段 + 已完成/待完成阶段清单（进度可视化，从 collect/选题开始就可见）
- [x] 选题 HITL：终端富文本展示 3 个候选（标题/thesis/hook），数字选择，落盘 topic_choice
- [x] 选择组件可复用，叙事选择（04 票）接入同一套交互
- [x] 无候选 / 无 state / 终端不支持颜色时优雅降级为纯文本，不崩溃
- [x] 纯 stdlib（ANSI 转义 + print + input）实现，不引入第三方 TUI 依赖
- [x] 测试不触真实终端：选择交互用注入输入，渲染函数可捕获输出断言

## 验证记录（2026-08-14）

- 单元/全量测试：286 tests OK（271 基线 + 15 tui 用例），lint 三段干净，diff-check OK。
- PTY 真实交互：`choose-topic`（无参数）在终端显示进度清单（collect ✓、topic_choice →、后续暗淡）、3 个候选富文本（加粗标题 + thesis/hook/战略相关性/证据缺口）、`选择 1..3：` 等待输入。
- 交互实测：选 `2` + 方向「重点讨论工程团队的技能门控」，落盘 `topic_choice: human`、slug `autogpt-agents-md-ai`，direction 原样保留在 selected-topic.json。
- 技术底座：纯 stdlib（ANSI + print + input），`supports_color` 按 isatty 检测，非终端/测试自动降级纯文本，零第三方依赖。

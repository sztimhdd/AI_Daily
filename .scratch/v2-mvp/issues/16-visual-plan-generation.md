# 16 - visual-plan 生成（schema 校验）

**What to build:** 从英文稿 + evidence package 生成受控的 `visual-plan.json`：每张图的插入锚点、叙事目的、风格、英文生图提示词、alt、允许出现的已核实数字、尺寸、模型，并被 schema 校验。

**Blocked by:** None - can start immediately

**Status:** ready-for-agent

- [ ] `visuals.build_plan_prompt(article, evidence)` 产出只含受控字段的提示词
- [ ] `visuals.parse_plan(payload)` 校验 schema，非法图条目返回错误
- [ ] `visuals.run_plan(run_paths, codex_runner)` 写 `visual-plan.json`；plan 空/非法 → 结构化失败

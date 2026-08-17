# 04 — 叙事候选 + HITL 门

**What to build:** 新增 `narrative` 阶段：从 OSINT 档案生成 2–3 个互异的叙事候选（各带 thesis 与角度），用 TUI 让用户选择，把选择落盘为 durable 决策，成为正常路径的第二个 HITL。

**Blocked by:** 03 — Initial Research 阶段

**Status:** completed

- [x] 生成 2 个互异的叙事候选，每个含清晰 thesis 与差异点
- [x] 提供 TUI 供用户选择叙事
- [x] 选择后把叙事决策落盘并写入状态，可追溯
- [x] 未选定叙事前不得进入审计或写作阶段（require_narrative 门禁）
- [x] 恢复语义：从已有候选/选择继续，不重跑 research

验证记录（2026-08-17）：

- 叙事契约 knowledge/narrative-contract.md v2026 落地（三方调研合并裁决 + legacy 附录）。
- 路由实测：08-15 Gemini OSINT 档案 → 反共识拆台 + 成本账本两个互补候选，五段证据链/双平台要点/决策规则全部合规，落盘 narrative-candidates.json/md。
- 421 单测 + 17 项 fixture UAT 全绿。

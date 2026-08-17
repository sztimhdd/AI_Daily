# 05 — 证据充分性审计门

**What to build:** 叙事选定后、写作前，`codex exec` 判断现有 OSINT 证据是否足以支撑该叙事，输出三态判定与（不足时的）原子补证任务清单，落盘机器可读。

**Blocked by:** 04 — 叙事候选 + HITL 门

**Status:** completed

- [x] 输出 sufficient / needs_research / unsupported 三态
- [x] needs_research 时产出具体 research_tasks（原子任务，指明缺口类型与补证方向）
- [x] 审计结果落盘为机器可读，可追溯
- [x] unsupported（核心叙事无法成立）时阻塞并报告原因，不静默换叙事
- [x] 次要论点不足可降级/删除，不打断核心叙事推进

验证记录（2026-08-17）：

- 08-17 NVIDIA/OpenAI PORTS-Pike 真实运行：审计 needs_research（7 条原子任务）→ 两轮真实补证 → 最终收口 needs_research，理由与保守推进路径显式落盘。
- 08-20 GLM-5.3 真实运行同路径验证通过。
- 471+ 单测 + 17 项 fixture UAT 全绿；子代理 code-review 的 4 个 Important 全部修复（循环幂等、审计绑定叙事、重复首审、阻塞退出码）。

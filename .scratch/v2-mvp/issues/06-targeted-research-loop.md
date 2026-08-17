# 06 — 定向补证循环

**What to build:** 消费审计产出的 research_tasks，逐条定向抓取补证，然后重新审计；循环上限两轮，最终产出补强后的 evidence package。

**Blocked by:** 05 — 证据充分性审计门

**Status:** completed

- [x] 逐条消费 research_tasks 做定向抓取（复用 01 车道）
- [x] 补证后重新运行审计门
- [x] 循环上限两轮，防止无限补证
- [x] 补强后的证据合入 evidence package，保留原始来源与 fetch 状态
- [x] 两轮后仍不足时按三态之一收口，不悬挂

验证记录（2026-08-17）：

- 08-17 真实运行：审计 needs_research → 两轮定向补证（zhida 发现 + HTTP 抓取）→ 最终审计收口 needs_research，targeted-evidence.json 与 evidence-package.json 落盘，fetch 状态与 origin 标签完整。
- 循环幂等：完成后重跑不重复调用 Codex；471+ 单测全绿。

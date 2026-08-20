# 11 — 扩展质量门确定性检查

**What to build:** `quality.check_en` 增加五类确定性检查（每类 hit + non-hit 用例）：引语完整性（引号闭合、句尾完整、截断词如「driven by what」）、关键数字加粗、句长与被动语态、加粗引导语段落占比、管线词泄漏（403/fetched/evidence package 等）。

**Blocked by:** 09 — 补编译主编排版与节奏资产

**Status:** ready-for-agent

- [ ] 引语完整性违例 → `revise`（评审问题 3 的确定性防线）
- [ ] 关键数字未加粗、引导语占比 >50% → `revise` 或 `pass_with_notes`（按资产规则定）
- [ ] 句长 >20 词占比、被动语态 → `pass_with_notes`（节奏类）
- [ ] 管线词泄漏 → `revise`（正文禁管线机制）
- [ ] TDD：每类至少 1 命中 + 1 非命中；全量测试绿 + `git diff --check` 干净

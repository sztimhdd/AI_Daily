# 10 — 修订 draft_en 提示词（按 09 资产 + 评审归因）

**What to build:** 修订 `draft_en._compile_prompt`，让英文稿在证据边界不变的前提下，达到主编声线：推断一律用条件句式（If/would/may + 列缺失环节）、降级与立场并存、关键数字加粗、直接引语转 blockquote、加粗引导语段落占比受限、主动语态与缩写、句子 ≤20 词、禁止把管线机制（HTTP 403/fetched/evidence package）写进正文、引用前自查（词数/身份/双方确认逐条核对）、同句不重复挂链。

**Blocked by:** 09 — 补编译主编排版与节奏资产

**Status:** ready-for-agent

- [ ] 提示词逐条对照 `docs/verification/results/2026-08-20-editorial-review-round-1.md` 问题 1/6/7/9/14 的修复措辞
- [ ] 注入的 evidence 仍带 fetch status（降级依据不丢），但新增禁令「抓取状态只进 sources/audit，不进正文」
- [ ] 单测覆盖提示词含全部新硬规则关键词（test_draft_en 增加断言）
- [ ] 全量测试绿 + `git diff --check` 干净

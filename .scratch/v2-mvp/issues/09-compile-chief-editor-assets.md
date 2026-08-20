# 09 — 补编译主编排版与节奏资产

**What to build:** 把 n8n 主编工作流里尚未编译的五条资产落到 knowledge/，使提示词与质量门有单一资产源：视觉高亮（关键数字加粗）、EN 节奏契约（≤20 词句长/主动语态/缩写/句子碎片）、引语 blockquote 组装规则、降级写作协议（降低事实的确定性 ≠ 放弃立场）、**叙事表达力契约**（钩子画面先行、意象先于术语、节奏多样性、单句成段、最强句压轴、张力做 crescendo——来自 Round 1b 表达力重评）。

**Blocked by:** None — can start immediately

**Status:** completed

- [ ] `knowledge/en-author-style.md`（或新文件）补齐四条规则，每条与 n8n 原句一一对应可追溯（REF·Final Editor1/3、UDW·Final Editor1、UDW·去AI味）
- [ ] 降级写作协议明确：fact 降级用 hedged 句式，opinion 仍须 take a stand（消解评审问题 7 的规则冲突）
- [ ] 叙事表达力契约明确：对普通读者「先画面后术语、冲突做成 crescendo、最强一句压轴」，与事实降级不冲突
- [ ] 资产只陈述规则，不含任何提示词实现细节；`git diff --check` 干净
- [ ] 已有测试不受影响（`python3 -m unittest discover -s tests -q` 全绿）

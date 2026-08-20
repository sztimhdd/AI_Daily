# 09 — 补编译主编排版与节奏资产

**What to build:** 把 n8n 主编工作流里尚未编译的四条资产落到 knowledge/，使提示词与质量门有单一资产源：视觉高亮（关键数字加粗）、EN 节奏契约（≤20 词句长/主动语态/缩写/句子碎片）、引语 blockquote 组装规则、降级写作协议（降低事实的确定性 ≠ 放弃立场）。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] `knowledge/en-author-style.md`（或新文件）补齐四条规则，每条与 n8n 原句一一对应可追溯（REF·Final Editor1/3、UDW·Final Editor1、UDW·去AI味）
- [ ] 降级写作协议明确：fact 降级用 hedged 句式，opinion 仍须 take a stand（消解评审问题 7 的规则冲突）
- [ ] 资产只陈述规则，不含任何提示词实现细节；`git diff --check` 干净
- [ ] 已有测试不受影响（`python3 -m unittest discover -s tests -q` 全绿）

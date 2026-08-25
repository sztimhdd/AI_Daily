# Narrative v2 叙事模块重构

**Status:** ready-for-agent

## Problem Statement

当前 04 叙事模块把“读者决策”当成所有文章的共同终点，导致不同新闻都被
压成 CTO 决策快讯，两个候选也常常只是同一建议换标题。

## Solution

恢复原始 n8n 资产中的调查、战略、长期展望、机制解释和故事化能力。叙事形式、
读者阅读后的变化、结尾方式三者分离；只有行动型文章要求 `decision_rule`。
保留证据边界，增加候选对去重和更窄的证据路由。

## Acceptance Criteria

- 收购/估值传闻不会仅凭“亿/美元/收购”关键词解锁成本或控制权叙事。
- 非行动型候选可以没有 `decision_rule`，并能正常进入 Telegram/TUI 和后续
  evidence sufficiency。
- prompt 不再要求所有候选开头和每条论据都以 Decision 收束。
- 两个 thesis、reader_move、行动建议高度相同的候选对会被拒绝。
- 新候选包含 form、reader move、ending mode、作者场景和鲜明立场。
- 现有测试和完整 CLI/UAT 流程保持通过。

## Implementation Decisions

- 修改 narrative 模块、TUI 显示、narrative contract 和对应测试。
- 不修改证据审计的核心门禁，不改变旧 artifact 的读取兼容性。
- 变更通过本地 Markdown ticket 追踪，按阻塞顺序执行。

## Testing Decisions

使用现有 `tests/test_narrative.py` 与 `tests/test_tui.py` 的真实函数调用，
先写红测试，再实现最小改动，最后跑全量测试和 `scripts/uat_cli.sh`。

## Out of Scope

全文 drafting prompt、模型路由、Telegram 凭证和真实新闻抓取策略。

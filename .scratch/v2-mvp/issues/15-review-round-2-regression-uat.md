# 15 — 复评回归 UAT（Round 2 收敛）

**What to build:** 用真实选题重跑全自动链路（collect → draft-en → assemble-en），对新产品再次做双模型主编评审，对照 Round 1 的 15 项问题清单输出收敛报告：逐项标记 已修复/未修复/新增，未修复项写明原因与下一轮归属。

**Blocked by:** 10、11、12、13、14 — 全部修复落地后执行

**Status:** ready-for-agent

- [ ] 真实数据全自动跑出一份英文包（非 fixture）
- [ ] DeepSeek + GPT-5.6 双模型复评（同一主编 prompt）
- [ ] 收敛报告：Round 1 的 P1 全部通过或显式降级为 P2；新增问题单独列出
- [ ] 报告落 `docs/verification/results/2026-08-2x-editorial-review-round-2.md`

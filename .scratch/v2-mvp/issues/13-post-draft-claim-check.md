# 13 — 成稿事实核对（claim-check）

**What to build:** 英文稿在质量门之前增加一轮 claim-check：Codex 逐条核对稿中断言 vs 证据包（数字、引语词数、人物身份、单方/双方措辞），输出 claim_check 列表；确定性子集先行——引语字数、断言语义与链接对应关系可本地校验。核对失败 → `revise` 打回重写，不静默改写。

**Blocked by:** 10 — 修订 draft_en 提示词

**Status:** completed

- [ ] 输出 artifact：`.local/runs/<date>/claim-check.json`，每条 {claim, evidence_url, verdict: ok|mismatch|unsupported}
- [ ] 「four words」数词、「both companies confirmed」单方链接、co-founder 身份三类错误有回归用例
- [ ] mismatch/unsupported 时质量门判定 revise
- [ ] codex runner 可注入（单测不触网）；全量测试绿 + `git diff --check` 干净

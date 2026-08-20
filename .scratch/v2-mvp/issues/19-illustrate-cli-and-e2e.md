# 19 - illustrate CLI + 换话题真实 E2E + git push

**What to build:** `ai_daily illustrate` 命令串联 plan→generate→embed；换一个真实话题跑完整链路（collect→…→配图→assemble-en），文章与图片提交到 GitHub 对应仓库。

**Blocked by:** 18

**Status:** ready-for-agent

- [ ] `illustrate` CLI 命令 + pipeline 编排，nonblocking
- [ ] 换话题真实 E2E 产出英文包 + 图片（真实 Gemini 调用）
- [ ] 文章 + 图片在同一 commit 提交并 push 到 GitHub
- [ ] 终报：包路径、图片清单、GitHub raw URL、单测数

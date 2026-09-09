# 04 — systemd 调度迁移 + Hermes 真实 E2E 交付

**What to build:** 用 systemd timer 替代 launchd 跑工作日每日写作；在 Hermes 上
走一次完整真实 E2E（选题 → … → 生图 → GitHub 发布），证明搬迁后链路端到端可用。

**Blocked by:** 03（Hermes 可运行 + 登录态就绪）

**Status:** ready-for-agent

- [ ] 把 `scripts/daily-telegram.sh` 的语义迁成 Hermes systemd timer（工作日触发），
      失败态与日志可查
- [ ] 一次真实 E2E：换一个话题走全链路，图片经 ChatGPT 网页生图产出并嵌入
- [ ] 文章 + 图片同 commit 发布到 GitHub，raw URL 非 404
- [ ] 终报：包路径、图片清单、GitHub URL、全量测试数、调度状态

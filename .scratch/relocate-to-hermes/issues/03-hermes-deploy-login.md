# 03 — Hermes 落地：clone、迁资产、装 MCP、首次登录

**What to build:** 把仓库与运行时部署到 Hermes，装好生图 MCP，并完成一次
ChatGPT Pro 登录，使 Hermes 具备完整每日运行能力。

**Blocked by:** 01（干净主线）、02（桥代码进主线）

**Status:** ready-for-agent

- [ ] Hermes 上 clone 到固定路径（建议 `~/AI_Daily`），`codex exec --json` 在该
      目录实测可用（受信目录）
- [ ] `.local/telegram.env`、`.local/` 运行态、`knowledge/` 只读资产经 rsync/scp
      迁到 Hermes，不进 Git
- [ ] 安装并固定 `@isen/chatgpt-image-web-mcp@0.3.4`，确认 Node/Chrome 满足前置
- [ ] 首次 ChatGPT Pro 登录建在 WSL 侧 Chrome 专用 profile，`open_chatgpt_browser`
      返回 `composerReady=true`
- [ ] 一次真实生图探针：1 张图落盘 WebP，记录产物路径与耗时

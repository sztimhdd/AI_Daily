# 03 — Hermes 落地：clone、迁资产、装 MCP、首次登录

**What to build:** 把仓库与运行时部署到 Hermes，装好生图 MCP，并完成一次
ChatGPT Pro 登录，使 Hermes 具备完整每日运行能力。

**Blocked by:** 01（干净主线）、02（桥代码进主线）

**Status:** claimed

- [ ] Hermes 上 clone 到固定路径（建议 `~/AI_Daily`），`codex exec --json` 在该
      目录实测可用（受信目录）
- [ ] `.local/telegram.env`、`.local/` 运行态、`knowledge/` 只读资产经 rsync/scp
      迁到 Hermes，不进 Git
- [ ] 安装并固定 `@isen/chatgpt-image-web-mcp@0.3.4`，确认 Node/Chrome 满足前置
- [ ] 首次 ChatGPT Pro 登录建在 WSL 侧 Chrome 专用 profile，`open_chatgpt_browser`
      返回 `composerReady=true`
- [ ] 一次真实生图探针：1 张图落盘 WebP，记录产物路径与耗时

## Answer

前三项已完成：clone 到 `~/AI_Daily`，HEAD 与 origin/main 一致；`codex exec
--json` 在受信目录实测返回 OK（chatgpt 认证）；`telegram.env` 已 scp 迁入
（`knowledge/` 已在 git 内无需迁）；`npx --yes --package=@isen/chatgpt-image
-web-mcp@0.3.4` 可拉起并打印 stdio 就绪；WSLg + Chrome 145 + Node 24 满足前置。

剩余两项（首次登录 + 真实生图探针）需用户在 Hermes 显示器前完成登录，属
HITL，本票状态保留 claimed，待登录后收口。

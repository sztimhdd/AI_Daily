# Spec: AI Daily 整体搬迁到 Hermes PC，图片切换到 ChatGPT 网页生图

## Problem Statement

AI Daily 现在跑在 Mac 上，两个痛点：

1. 图片通道依赖 Gemini/Vertex（`gemini-3.1-flash-image` 走 `gcloud`），端点
   实测返回 HTTP 404，且与用户已订阅的 ChatGPT Pro 生图额度是两本账。
2. Mac 不是常驻主机，`launchd` 定时 + 人机交互依赖用户手边这台机器；用户
   希望工作日的每日写作稳定跑在一台常驻机器上。

用户希望：整条 AI Daily 搬迁到 Hermes PC（192.168.4.100，WSL2 Ubuntu），图片
生成改用 ChatGPT Pro 网页额度（用户已订阅，实测可用），Gemini 依赖下线。

## Solution

从用户视角：

1. 每天由 Hermes 上的 systemd timer 触发写作链，写作用 Codex CLI（Hermes 本地
   `codex`，`auth_mode=chatgpt`，已认证）执行；Telegram 决策通道不变。
2. 文章的正文配图与 LinkedIn 封面由 ChatGPT 网页生图自动产出（复用现成的
   `@isen/chatgpt-image-web-mcp`，不重造浏览器自动化），产物落盘 WebP 后照常
   打包并发布到 GitHub。
3. 图片失败仍是软失败：`needs_human` / 超时 / 非 JSON 都记为 `degraded`，正文
   照发，不阻塞每日交付。

## User Stories

1. As a 每日读者, I want 每个工作日有一篇英文分析发到 GitHub，so that 我在
   LinkedIn 上稳定读到成品。
2. As a 编辑, I want 配图与封面由 ChatGPT 网页额度自动生成，so that 我不再
   为 Gemini 404 手工补图。
3. As a 编辑, I want 图片生成失败（验证码/改版/超时）时正文仍发布并明确标注
   degraded，so that 一次配图失败不会丢掉一篇已写好的稿子。
4. As a 运维者, I want 写作调度跑在常驻的 Hermes 上（systemd timer），so that
   不依赖我手边的 Mac 是否开机。
5. As a 运维者, I want 一次 ChatGPT Pro 登录后长期复用登录态，so that 每日
   生图不需要重复登录。
6. As a 开发者, I want 图片生成走可注入的 runner，so that 单测可以离线 stub
   MCP 而不弹真浏览器。

## Implementation Decisions

- 运行形态：Hermes WSL 上部署仓库 + 运行时，systemd timer 替代 launchd；
  Telegram 是网络层，不变。
- 图片执行通道：新增一个 stdio MCP 客户端，spawn
  `@isen/chatgpt-image-web-mcp@0.3.4`，只调 `open_chatgpt_browser` 与
  `run_batch_image_jobs` 两个工具，不碰其他工具。
- 现有 seam：`visuals.generate_image` 已接受注入式 `gemini_runner`；迁移是把
  默认实现从 Vertex Gemini 换成 ChatGPT 网页桥，`_default_gemini_runner` 的
  语义泛化为「栅格图默认 runner」。`delivery_en` 与 `pipeline` 的调用点不新增
  seam，只让默认实现走新通道。
- 登录态：建在 Hermes WSL 侧的 Google Chrome 专用 profile（与生图 MCP 同域），
  与 Windows 侧 Edge 的微信/知乎登录态互不影响。
- 凭证：`telegram.env`、ChatGPT 登录态、GitHub SSH key 只落在 Hermes 本地，
  不进 Git；`jq` 缺省用 Python 替代，不引入新依赖。

## Testing Decisions

- 好的测试只验证外部行为：给定一个 plan，图片桥把 `prompt` 翻译成一次 MCP
  调用并返回图片字节或结构化失败；不测内部 DOM/浏览器细节。
- 被注入的 `http`/`subprocess` 是测试 seam：离线 stub MCP 的 stdio 往返，覆盖
  成功 / `needs_human` / 超时 / 非 JSON 四条路径，全程不弹浏览器。
- 对齐现有 `tests/test_visuals.py` 的注入风格（runner 注入、manifest 断言）。
- 真实链路用一次 E2E 探针单独验（真实 ChatGPT 登录态），不并入单测。

## Out of Scope

- 不迁移 Windows 侧 Edge 的微信/知乎抓取登录态。
- 不改写叙事/写作质量门，本次只动部署与图片通道。
- 不做多机高可用；Hermes 是唯一运行主机。
- 不绕开 ChatGPT 的服务条款与验证码/付费墙。

## Further Notes

- Hermes 实测：SSH `OHPC` 通，Codex CLI 0.153.1 `codex exec --json` 已认证可
  用，Node 24 / Python 3.12 / git 2.43 齐，GitHub SSH 通，systemd running，
  `/usr/bin/google-chrome` 存在；缺口仅 `jq`。
- 源头（Mac）有 4 个未推送 commit 与 09-08/09-09 两篇未跟踪文章包，必须先
  收口，否则 Hermes clone 到的不是干净最新主线。

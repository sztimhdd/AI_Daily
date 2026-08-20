# 01 — 抓取原语 seam

**What to build:** 一条 `fetch <url>` 命令：输入一个 URL（或一个 topic），按来源自动路由到三条车道——公开网页走 HTTP/tavily、墙内平台（知乎/微信公众号）走本地 CDP 浏览器、定向发现走 zhida——并统一返回可复用的证据载荷（标题、正文 Markdown、sha256、抓取状态、来源车道），正文落盘并可幂等重跑。

**Blocked by:** None — can start immediately

**Status:** completed

- [x] 公开 URL 走 HTTP/tavily 车道，返回正文与状态
- [x] 墙内 URL（zhihu / mp.weixin）走本地 CDP 车道，返回正文与状态
- [x] 发现车道能从一个 topic 得到相关问题/讨论 URL 清单
- [x] 每次抓取结果携带 sha256 与 fetch 状态，落盘后可幂等重跑（同 URL 同哈希不重复抓）
- [x] 统一返回结构对三种车道一致，调用方无需感知底层差异
- [x] 测试用注入 fake，不触真实网络与浏览器

## 验证记录（2026-08-14）

- 单元/全量测试：271 tests OK（254 基线 + 17 fetch 用例）。
- HTTP 车道真实：zhihu 直连 403 → `failed`（正确降级）；mp.weixin 直连得 og:description 摘要 + 分享页壳（`fetched` 但非全文，需 CDP）。
- CDP 车道真实：mp.weixin 全文 1778 字 `fetched`；zhihu 问题回答全文 `fetched`。
- 发现车道真实：`discover("DeepSeek Harness")` 返回 6 条去重 zhihu 问题链接。
- 修复一个 bug：幂等键原先只含 `sha1(url)`，导致 HTTP 缓存遮蔽 CDP；改为 `sha1(lane:url)` 并加回归测试。
- 新增 skill 脚本 `~/.agents/skills/walled-fetch-cdp/scripts/search_zhihu.py`（只读 DOM 提取问题链接）。

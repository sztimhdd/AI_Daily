# 02 — ChatGPT 网页生图桥，Gemini 默认通道下线

**What to build:** 新增一个 stdio MCP 客户端桥接 `@isen/chatgpt-image-web-mcp`，
把 `visuals` 的默认栅格图 runner 从 Vertex Gemini 换成 ChatGPT 网页生图；图片
失败仍是非阻塞软失败。

**Blocked by:** None — 可立即开始（纯代码，离线可测，不依赖 Hermes）

**Status:** claimed

- [ ] 新增模块：spawn `npx --yes --package=@isen/chatgpt-image-web-mcp@0.3.4
      chatgpt-image-web-mcp` 的 stdio MCP 客户端，只调 `open_chatgpt_browser` +
      `run_batch_image_jobs`
- [ ] `visuals` 默认栅格图 runner 泛化：`_default_gemini_runner` 换成 ChatGPT 网页
      桥，`gemini_runner` 注入签名不变，旧 Vertex 路径移除
- [ ] 失败语义：`needs_human` / 超时 / 非 JSON / 无图 均返回结构化 `degraded`，
      正文照发
- [ ] 单测：离线 stub MCP stdio，覆盖 成功 / needs_human / 超时 / 非 JSON 四路，
      不弹浏览器；`git diff --check` 通过

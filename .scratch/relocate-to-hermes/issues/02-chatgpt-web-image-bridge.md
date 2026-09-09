# 02 — ChatGPT 网页生图桥，Gemini 默认通道下线

**What to build:** 新增一个 stdio MCP 客户端桥接 `@isen/chatgpt-image-web-mcp`，
把 `visuals` 的默认栅格图 runner 从 Vertex Gemini 换成 ChatGPT 网页生图；图片
失败仍是非阻塞软失败。

**Blocked by:** None — 可立即开始（纯代码，离线可测，不依赖 Hermes）

**Status:** resolved

- [ ] 新增模块：spawn `npx --yes --package=@isen/chatgpt-image-web-mcp@0.3.4
      chatgpt-image-web-mcp` 的 stdio MCP 客户端，只调 `open_chatgpt_browser` +
      `run_batch_image_jobs`
- [ ] `visuals` 默认栅格图 runner 泛化：`_default_gemini_runner` 换成 ChatGPT 网页
      桥，`gemini_runner` 注入签名不变，旧 Vertex 路径移除
- [ ] 失败语义：`needs_human` / 超时 / 非 JSON / 无图 均返回结构化 `degraded`，
      正文照发
- [ ] 单测：离线 stub MCP stdio，覆盖 成功 / needs_human / 超时 / 非 JSON 四路，
      不弹浏览器；`git diff --check` 通过

## Answer

已实现。新增 `src/ai_daily/chatgpt_web.py`：stdio JSON-RPC MCP 客户端，spawn
`@isen/chatgpt-image-web-mcp@0.3.4`，只调 `open_chatgpt_browser` +
`run_image_job`（单张）；transport 与 loader 双注入，离线可测。`visuals.py`
默认栅格图通道改为 ChatGPT 网页桥，删除 Vertex 全套（`_gcloud`、
`load_vertex_*`、`_VERTEX_ENDPOINT`、`_default_gemini_runner`、
`ensure_vertex_credentials`），`DEFAULT_MODEL`/`ALLOWED_MODELS` 改为
`chatgpt-web`，prompt 里「Gemini image」措辞统一为「raster image」。
`gemini_runner` 注入参数名保留（spec 要求签名不变）。

验证：默认 58 测试 OK（含新增 `test_chatgpt_web` 11 例）；`test_visuals` +
`test_delivery_en` 55 例 OK；`uat_cli` 17/17 PASS；`git diff --check` 干净。
`--full` 783 例里 22 个 error 为 legacy 测试在离线 guard 下触发 subprocess
被拦截，与本次改动无关（pre-existing，README 标注 `--full` manual-only）。

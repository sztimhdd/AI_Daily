# 21 — huggingface.co/blog 抓取只拿到 JS 壳，正文缺失

**Status:** resolved

## 现象（2026-08-21 E2E 实测）

选题候选 1 的官方一手来源 `https://huggingface.co/blog/LiquidAI/lfm25-dspark` 在 OSINT 里标为 `fetched`，但 excerpt 只有页面壳（导航文字 `Hugging Face Models Datasets Spaces …`），没有文章正文。

## 根因修正（2026-08-21 复核）

原假设「JS 壳 / 客户端渲染」**不成立**。复核实测：普通 HTTP 抓取拿到了完整正文（存储 md 11315 字符），文章内容、3.18x/2.87x 基准表、acceptance-rate 细节全部在正文里。真正的问题是**摘录逻辑**：`research._excerpt_with_flag` 取正文前 300 字符并按句号截断，而 HF 页面正文以导航菜单开头，于是 300 字摘录 = 导航，审计只看摘录 → 误判为「页面壳」。

## 直接后果

审计只看到导航摘录，把「官方正文已抓到但摘录截在导航」误判成「官方正文缺失」，导致叙事 1 被判 `unsupported` 并走保守降级。

## Answer（已修复）

- `research.py` 新增 `_first_content_start`：逐句跳过含 ≥2 个导航样板词（sign up / log in / pricing / enterprise / docs / community / follow / upvote 等）且长度 ≥20 的句子，摘录从第一条实质句开始；无实质句时回退原逻辑。
- 真实复核：同一 E2E 存的 HF 全文经新逻辑摘录 = `These add a speculative decoding path … up to 3.18 throughput improvement on a GPU and up to 2.87x on-device.`，导航零泄漏。
- 单测：`EvidenceExcerptBoundaryTests` 新增 3 例（跳过导航前缀 / 无导航时行为不变 / 全导航回退）。
- 结论：此问题不需要 CDP 车道；Tavily / CDP 工具栈仍保留给真正需要 JS 渲染或登录态的页面。

## 关联

- 修复后同一证据包可重跑 05 审计验证叙事 1 是否转为 `sufficient`/`needs_research`（本轮未重跑，作为待验证项）。

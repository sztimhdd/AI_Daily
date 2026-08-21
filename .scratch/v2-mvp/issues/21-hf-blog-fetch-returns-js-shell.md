# 21 — huggingface.co/blog 抓取只拿到 JS 壳，正文缺失

**Status:** needs-triage

## 现象（2026-08-21 E2E 实测）

选题候选 1 的官方一手来源 `https://huggingface.co/blog/LiquidAI/lfm25-dspark` 在 OSINT 里标为 `fetched`，但 excerpt 只有页面壳（导航文字 `Hugging Face Models Datasets Spaces …`），没有文章正文。

## 根因判断

`huggingface.co/blog` 是客户端渲染页面，普通 HTTP 抓取拿到的是静态壳而非内容体。`excerpt_truncated=True`，仅 300 字符的导航文本。

## 直接后果

叙事 1（mechanism_teardown，依赖「草稿模型机制 / 3.18x 实验配置 / 输出不变」）的唯一一手来源正文缺失，05 审计判定 `unsupported` 并正确阻塞，而不是把二手转述写成已确认事实。

## 建议修复方向（待主编确认，本轮不实现）

- 为 `huggingface.co/blog`（及同类客户端渲染页）接入 JS 渲染车道（CDP）或专用内容接口，而非普通 HTTP。
- 抓取结果增加「正文是否真正取到」的判据：正文长度阈值 + 导航壳特征（如 `Models Datasets Spaces`）识别，取到壳时如实标记 `fetched_shell` 而非 `fetched`，避免污染证据充分性判断。

## 关联

- 与本 E2E 的 `unsupported` 阻塞直接相关；修复后可重跑 05 审计，看叙事 1 是否成立。

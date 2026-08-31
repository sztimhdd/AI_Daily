# 自动配图（Gemini Nano Banana）设计 Spec

**状态：** ready-for-agent｜**来源：** 用户确认「同意此设计，开工」，替代网页版 ChatGPT 人工配图链路。

## Problem Statement

英文稿成稿后，配图目前依赖「人工打开网页版 ChatGPT、贴提示词、等它生成+上传+嵌图」的人机交接：风格漂移、事实边界不可审计、无法在定时 codex session 内无人值守。需要把「思考配图 + 生图 + 校验 + 嵌入」收进流水线，用公司报销的 Gemini API 自动完成，文章与图片最终都进入 GitHub 仓库。

## Solution

在 `claim-check=ok` 之后、`assemble-en` 之前，新增一个**可选、非阻塞**的插图阶段（不扩展现有阶段机枚举，走独立 CLI 命令 `illustrate`），产出受控图片并确定性嵌入英文稿：

1. 写作模型生成 `visual-plan.json`：2–4 张正文图外，必须有 1 张 `cover`；每张图包括插入锚点、叙事目的、视觉模式、风格、英文生图提示词、alt、观点型 caption、允许出现的已核实数字、目标尺寸、选用模型。
2. 生图器只吃这张图的受控提示词，调 Gemini Image API；不读整篇文章、不联网、不做事实研究。
3. 返回图先落 `.local/runs/<date>/images/`，做格式/尺寸/数量校验，再转 WebP。
4. 确定性先移除本包旧的 raw-GitHub 图块及 caption，再把 `![](raw-url)` 插到英文稿对应锚点，并把图片清单写进 `metadata.json`。
5. `cover` 不嵌正文：它进入 `images/cover.webp`、metadata 的 `cover`，以及 `linkedin-kit.md` 的预览与可打开 raw URL，供编辑上传到 LinkedIn。
6. 图片缺失时文章仍可打包，但 `images_status` 标记 `degraded`；绝不阻塞正文。

## User Stories

1. 作为主编，我要每张图有明确插入锚点与叙事目的，使配图服务于论证而非装饰。
2. 作为主编，我要生图提示词只引用已核实的数字，使图片不伪造事实。
3. 作为管线维护者，我要生图阶段失败不阻塞正文打包，使一篇稿子缺图也能发布。
4. 作为管线维护者，我要生成图先校验再进包，使损坏/异常尺寸的图不进入发布目录。
5. 作为管线维护者，我要最终图片与文章在同一个 GitHub commit 中，使 raw URL 永远指向真实存在的文件。

## Implementation Decisions

- 新增模块 `src/ai_daily/visuals.py`，暴露纯函数 + 一个 `run(run_paths, ...)` 编排；依赖全部可注入（`codex_runner`、`gemini_runner`、`to_webp`），测试不触网。
- `visual-plan.json` 由写作模型生成（复用 `research._default_codex_runner` 的注入模式）。plan 是 schema 校验对象：`images: [{id, anchor, purpose, visual_mode, style, prompt, alt, caption, allowed_figures, size, model}]`，总数至少 2、至多 5 张；新计划要求 1 张 `cover`。`visual_mode` 会被检查：三张正文图不得同风格/同模式复用。封面风格由模型按文章张力选择，不强制复用正文风格。
- Gemini 生图：默认 `gemini-2.5-flash-image`，提示词走 Vertex AI `generateContent` 接口，返回 base64 PNG；项目与短期 token 由 `gcloud` 读取，**绝不打印**。
- WebP 转码：Pillow（已装 user-site 12.3）；无 Pillow 时降级保留 PNG 并在 manifest 记录原因，不阻塞。
- 嵌入：确定性把 plan 中每张正文图的 `![](url)` 插到 `anchor` 所在段落后；封面记录进 metadata 的 `cover` 字段，不插正文。强制重跑先清理当前包旧图块，防止旧 caption 和新图混排。
- `assemble_en` 采纳 `images/` 目录；visual manifest 的 `cover` 是包的主封面，并同步到 LinkedIn Kit。
- 尺寸默认 2K（2048×2048）；封面允许 Pro/4K，正文图统一 2K。定价见官方表。
- 每图最多一次技术重试（网络失败/无图片返回）；不做创意重试。Fireworks 图解渲染失败时，以 plan 内只含文章事实的 `fallback_image_prompt` 调 Gemini 生出一张编辑插图并标记 `fallback_from=diagram`。

## Testing Decisions

- 每个纯函数至少 1 命中 + 1 非命中用例，延续现有 `unittest` 风格：`visuals.py` 镜像 `cover.py`/`draft_en.py` 的依赖注入。
- Gemini 调用用注入 runner 模拟（不触网、不打印 key）；真实调用只出现在最终 E2E。
- 覆盖：同质正文视觉拒绝、图解失败回退、强制重嵌不残留旧图、视觉封面入 LinkedIn Kit 与 package metadata。
- `illustrate` 的 nonblocking 行为：缺 plan、生图失败、无凭证 → 返回结构化失败，正文仍可 assemble。
- 收尾：全量单测 + `git diff --check` + `scripts/uat_cli.sh` + 换话题真实 E2E（含真实 Gemini 生图 + git push）。

## Out of Scope

- 不自动发起创意重试、不做审美评分循环。
- 不改现有 STAGES 枚举；`illustrate` 是独立命令，不阻塞 `assembly`。
- 不引入 google-genai SDK；用 stdlib urllib 直连。
- 不处理中文版配图（本轮仅英文稿）。

## Further Notes

- Gemini 模型家族与定价以官方为准：Nano Banana 2 (`gemini-3.1-flash-image`) 2K=$0.101/张；Pro (`gemini-3-pro-image`) 2K=$0.134/张。默认 4 张 2K 正文 ≈ $0.40/篇。
- 凭证文件 `.local/gemini.env` 已被 `.gitignore` 覆盖（`git check-ignore` 已确认）。

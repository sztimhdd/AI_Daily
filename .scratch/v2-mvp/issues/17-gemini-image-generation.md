# 17 - Gemini 生图 + WebP 转码

**What to build:** 读 visual-plan 逐图调 Gemini Image API，返回图落 `.local/runs/<date>/images/`，校验后转 WebP；凭证从环境变量或 `.local/gemini.env` 读取，绝不打印。

**Blocked by:** 16

**Status:** ready-for-agent

- [ ] `visuals.load_gemini_key()` 读 env 或 `.local/gemini.env`，缺失返回结构化失败
- [ ] `visuals.generate_image(prompt, model, size, gemini_runner)` 返回 PNG bytes；runner 注入
- [ ] `visuals.to_webp(png_bytes)` 转 WebP；无 Pillow 时降级保留 PNG 并记录原因
- [ ] `visuals.run_generate(run_paths, gemini_runner)` 逐图生成 + 校验 + 落盘 manifest

# 18 - 确定性嵌入 + assemble-en 采纳 images

**What to build:** 把生成的图按 plan 锚点确定性插入英文稿，图片清单写入 metadata；`assemble_en` 采纳 `images/` 目录；缺图不阻塞正文。

**Blocked by:** 17

**Status:** ready-for-agent

- [ ] `visuals.embed(article, plan, urls)` 按锚点插入 `![](url)`，封面不入正文
- [ ] `visuals.build_manifest()` 产出图片清单（filename/alt/width/height/format）
- [ ] `assemble_en` 采纳 `images/`，metadata 记 `images_status` 与图清单
- [ ] 缺图时 `images_status: degraded`，正文仍可打包

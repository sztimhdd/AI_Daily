# 08 — 英文优先产出包

**What to build:** 把英文稿与元数据组装为可发布的英文 package：`article.md` + `sources.md` + `metadata.json`，最终文章走英文路径（`-en.md`），包校验通过。

**Blocked by:** 07 — 英文稿 + 英文质量门

**Status:** completed

- [x] 产出 article + sources + metadata 三件套（英文包用 `article-en.md` / `sources-en.md` / `metadata-en.json`，与中文 `article.md` 并存）
- [x] 最终文章走英文路径（`-en.md`），与中文路径并存不冲突（`paths.final_article_en_path` → `articles/<date>-<slug>-en.md`）
- [x] 产出包通过结构校验（复用 `assemble.validate_article`：H1、占位符、HTML/省略号/截断 URL、链接）
- [x] 能从 package 重建一份可发布的英文文章（`article-en.md` 全文 + `metadata-en.json` 溯源）
- [x] 无封面/部分失败时仍能组装（沿用“图片不阻断正文”规则，`_adopt_cover` 可选）

实现：`src/ai_daily/assemble_en.py`、`paths.py`、`pipeline.py`、`cli.py`（`draft-en`/`assemble-en`）；测试 `tests/test_assemble_en.py`、`tests/test_cli.py`。

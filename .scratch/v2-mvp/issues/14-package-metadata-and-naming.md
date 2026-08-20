# 14 — 打包元数据与命名收尾

**What to build:** `assemble_en` 补全 metadata（quality_gate 结果、evidence_verdict、downgraded、evidence_caveats、source_count、generated_at、seo_title/seo_summary 占位）；`paths.slugify_title` 按词截断（不把标题 punchline 切半）；`_render_sources_md` 归一（failed 来源标题 fallback、非英文标题标注原语言、一手/二手/社媒分类）。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] metadata.quality 与 state 一致（verdict/word_count/downgraded）
- [ ] slug 不再出现「didn-t」式截断与丢词；旧 slug 行为有回归测试
- [ ] sources.md 中 failed 来源显示 `(fetch failed)` 而非裸 URL；中文标题附语言标注
- [ ] 全量测试绿 + `git diff --check` 干净 + `scripts/uat_cli.sh` 17 项 PASS

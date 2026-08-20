# 12 — 证据摘录句尾截断保护

**What to build:** `research.evidence_excerpt` / `_evidence_excerpt` 与 fetch 规范化按完整句子切分：截断只能发生在句尾，绝不把引语/承诺句切成半句；摘录若无法以完整句收尾，宁可删去该句并标记。

**Blocked by:** None — can start immediately

**Status:** completed

- [ ] 回归用例：官方博客「stays driven by what pricing」类句子不再输出半句摘录
- [ ] 摘录边界记录（excerpt_truncated 标记）供下游提示词判断是否可引用
- [ ] 06 补证与 07 起草共用同一保护函数
- [ ] 全量测试绿 + `git diff --check` 干净

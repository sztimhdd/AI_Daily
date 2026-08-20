# 07 — 英文稿 + 英文质量门

**What to build:** 从 evidence package 写英文完整稿（从证据重写，非中文翻译），并过英文质量门：去 AI 味检查与证据边界检查，墙内证据按 fetch 状态降级标注。

**Blocked by:** 06 — 定向补证循环

**Status:** completed

- [x] 产出英文完整稿，内容从证据组织，非中文翻译（`draft_en.run`，Codex 可注入，从 evidence-package 重写）
- [x] 通过英文去 AI 味检查（`deslop.check_text_en` 8 类英文检查）
- [x] 通过证据边界检查：无链接事实不入正文，事实/推断/观点可区分（`quality.check_en`）
- [x] 墙内来源（知乎/微信）证据按 fetch 状态显式降级，不伪装确定（per-source walled-downgrade 硬门）
- [x] 质量门只做检查与打回，不静默改写（`revise`/`evidence_recovery` 打回，不重写）
- [x] 输入门禁 = `sufficient` 或 `needs_research` 走保守降级（`sufficiency.require_writable`：needs_research 自动要求稿子对缺口显式标注，标注到位放行；`unsupported` 才硬阻塞）

实现：`src/ai_daily/draft_en.py`（`accept_downgrade` 语义已并入默认门禁）、`src/ai_daily/quality.py`（`DOWNGRADE_MARKERS`/`has_downgrade_marker`）、`src/ai_daily/sufficiency.py`（`require_writable`）、`knowledge/en-author-style.md`；测试 `tests/test_draft_en.py`、`tests/test_sufficiency.py`、`tests/test_quality.py`（555 tests 全绿）。

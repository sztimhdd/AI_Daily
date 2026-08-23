# 23 — 知乎官方 CLI 社区证据车道

**What to build:** 用知乎开放平台官方 `zhihu-cli`（Skill 0.3.0，CLI 0.3.0）补上长期缺失的社区证据车道：`search zhihu` 返回社区内容+原链接，喂给 03/06 的「社区原声/共识证据」缺口；`hot` 作选题热度信号；不再依赖脆弱的 zhida CDP 桥接。

**Blocked by:** 用户生成 Access Secret（developer.zhihu.com/profile）——live 调用前的唯一阻塞。

**Status:** completed（代码与接线已落地；live 验证待密钥）

- [x] `src/ai_daily/zhihu_lane.py`：injectable runner 包装（search_zhihu / hot_topics），AUTH_REQUIRED/缺二进制/坏 JSON 一律诚实 `unavailable`
- [x] 06 `_execute_tasks`：`缺真实使用反馈/缺社区原声/单一来源/来源冲突` 任务优先走 zhihu lane，条目 `source_lane=zhihu-cli`、`status=found`、带 url/title/author/excerpt，URL 去重；车道失败不阻塞其他任务
- [x] pipeline.run_targeted_loop 透传 `zhihu_runner`
- [x] Skill 装入 `~/.agents/skills/zhihu`；CLI 安装于 `~/Library/Application Support/zhihu-cli/current/zhihu-cli`（SHA-256 校验、不动 PATH、无 sudo）
- [x] 测试：zhihu_lane 5 例 + targeted 2 例；全量 691 tests 绿

验证记录（2026-08-23）：

- 真实探针：`search zhihu` / `hot` 均返回 `AUTH_REQUIRED`（需 Access Secret），未配置时管线按 `unavailable` 如实降级，不伪造社区证据。
- 待用户动作：到 https://developer.zhihu.com/profile 生成 Access Secret 后，通过 stdin 传入（`auth set --secret-stdin`，不回显）；之后即可 live 验证并跑 03/06 真实回归。

升级（2026-08-24，ADR 0002 + 计划 2026-08-24-zhihu-default-community-lane.md）：

- [x] `zhihu_lane.community_voice()` + `render_community_md()`（标注"二手社区证据，非一手事实"）
- [x] 03 live research 默认社区证据源：`run_initial(zhihu_runner=…)` 每次研究跑 1 次有界+缓存社区搜索（`ZHIHU_RESEARCH_BUDGET=1`），条目并入 OSINT sources（`source_lane=zhihu-cli`、`community=true`），`community_voices` 模块补一行声量注记；失败降级不阻塞
- [x] CLI `zhihu` 子命令（`--force`），对齐 `kg`
- [x] 测试：zhihu_lane 10 例、research zhihu 2 例、cli 1 例；全量 708 tests 绿
- [ ] 待配额（实名认证或窗口重置）后：放宽 `ZHIHU_RESEARCH_BUDGET` → 跑 03/06 真实社区证据回归，验证 `community_voices` 与"共识有传播证据"缺口闭合 → 据结果决定是否提升证据等级

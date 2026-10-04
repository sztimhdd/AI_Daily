# AI Daily V3 写作 MVP — 执行计划

[KNOWN][HIGH] 更新：2026-10-04。执行分支：`n8n-v3-handoff-20261003`。本文件接续会话附件 `ai-daily-v3-mvp-next-actions-2026-10-02.md` 的 A–E 计划，并以仓库检查点和原生执行更新状态；不改原产品合同。原交接文档仍是批准、证据、隔离和最终验收范围的依据。

## 目标与执行规则

[INFERRED][HIGH] 从已批准 Story 和结构化研究材料出发，先得到真实中文 News 初稿，再逐环节通过审稿、双语与 Deep、图像、发布包和母流程双入口。只交付 draft/preview，不启用生产发布。

[INFERRED][HIGH] 一次只改一个节点或不可分接口。顺序为：读取当前代码/版本及 payload → 保存恢复点 → 观察失败 → 最小修改 → 固定样本正负例 → 回读实际执行 → GitHub 保存并回读校验。节点绿色不代替正文阅读；mock 输出不证明模型成稿。无新证据不重试；同一分支失败两次停止，不换 provider 掩盖失败。

[INFERRED][HIGH] 复用现有代码、配置、模型和测试；不新增运行框架、授权数据库、策划 Agent 或四套模式工作流。原始运行栈、token、凭据和未审定草稿只保存在本地 `.local/`，不提交公开仓库。代码、可复现的脱敏 fixture、测试、版本差异与简短检查点提交原分支，不合并 main。

## 当前基线

| 对象 | 已知草稿/完成边界 |
|---|---|
| [KNOWN][HIGH] 母流程 `xR7fM1ZhxlMTUy0L` | 上轮草稿 `4473eaa6-212c-4d7f-b94d-27492e70bbf5`；生产 active 与草稿不同。修改前必须再次回读。 |
| [KNOWN][HIGH] Shared Dispatch `qAfs9BDFbdBotgaB` | 上轮草稿 `fb841db9-b24c-4e05-9bbc-5a373b82bdf1`；审批 provenance 已在局测 584 透传。 |
| [KNOWN][HIGH] Writer V2 `nHxILnDVz541Cu5P` | 本轮回读：`ee17d426-9bd3-4325-bb3c-8527c93a808c`，77 节点，active=false，activeVersionId=null。 |
| [KNOWN][HIGH] T03 受控测试 | 587 通过真实 Mapper/Gate/Switch，588 只改调用语言后被 Gate 拒绝。没有 Writer 调用。详见 `2026-10-04-t03-native-verification.md`。 |
| [KNOWN][HIGH] 原正式审批 | 550 是 awaiting_selection；557 不含原 selected approval provenance，不能改称正式批准。测试须使用明确的当前局测授权。 |

[INFERRED][HIGH] T03 标记为“受控测试入口通过”，不标“正式母入口授权已验收”。fresh call-time decision 可由测试驱动构造并绑定当前批准；历史 false 记录不可改写。正式母入口的决定来源留待 E 阶段。

## A — 安全入口与写作准备

- [x] [KNOWN][HIGH] 未发布草稿局测、版本恢复点及外部副作用隔离已有检查点。
- [x] [KNOWN][HIGH] T01：共用 Prepare Writing Handoff 接受直接 ready 与 News 补查 ready；保留结构化材料、引语和历史 false。
- [x] [KNOWN][HIGH] T02：工单映射为 writer_brief.v3 / writer_context.v1；严格中英路由。News 不补 thesis；Deep 无有效判断不能 ready。
- [x] [KNOWN][HIGH] T03：受控调用决定通过原生正负例，见 587/588。正式审批与父子版本仍待 E。

[INFERRED][HIGH] 不重新翻修上游研究体系。补查业务只有“结果校验与合并 → 原编辑复核一次”，复核通过进入共用写作准备。Post-Supplemental Ready 是状态，不再另建业务模块。保留缺口判断和材料绑定，不重新选题；Deep reassessment 继续 hold。

## B — 当前单元：T04 中文 News 初稿

**范围：** [INFERRED][HIGH] 仅 Writer V2 的中文路由及 V2 CN Lead Writer。先不修改其现有提示词和模型。中文 Writer 输出后停止；英文、审稿、图像、上传、邮件、ledger、发布不可达。

- [ ] 回读 557 的完整写作材料与当前草稿。不要用 587/588 的两来源缩减样本验收成稿。
- [ ] 复用仓库历史 fixture，补回真实执行中的完整报道路径、来源说明、支持摘录、引语上下文及未决问题。明确是从历史执行构造的局测输入，不是正式审批或当前新闻核验。
- [ ] 保存当前版本与最小目标子图；用纯逻辑检查确认正例可达中文出口、无决定/错语言/缺材料被拒绝。
- [ ] 将中文输出接至现有 V2 CN Lead Writer。实际模型调用使用 manual 模式；原 Execute Workflow Trigger 不能直接带任意 inputs，必要时使用可删除的 Manual Trigger + 固定 payload 入口。不能用 test_workflow 的模型模拟结果冒充真实写稿。
- [ ] 对每个图变更做原生检查；真实模型正例不 pin 模型。只使用现有已配置 provider，不新增凭据或提高权限。
- [ ] 读取完整正文，核对一个 H1、非空中文正文、报道承诺、多来源角度、采用引语、URL、归属和限定。特别检查模型选择与提供商路由、Cline 账户功能、缓存 UI 与 Gemini/Vertex 改进的区分。
- [ ] 归档输入与原始稿至本地 .local；向用户交付可下载稿件。仓库存可复现 fixture、测试和审阅结论，不提交未审定成稿。
- [ ] 删除临时入口，回读 diff；保存最终 checkpoint 与下一环节。只有正文真实产出及阅读验收完成才标初稿单元通过。

[INFERRED][HIGH] 本票不等于 B 全部完成：随后仍需最小 text-preview 返回合同及对应失败处理。只有实际正文暴露缺陷才修改中文 prompt；不预先叠加模板。

## C — 审稿与其余语言/模式

- [ ] 共用 Contract & Evidence Review 读取当前语言的稿件和证据，解除旧英文节点硬绑定。
- [ ] 正常稿不必逐层风格评审；有缺陷才一次定向修订并重新核对。修订仍不通过则 review_required，不无限循环。
- [ ] 修复中文编辑节点的英文复制配置；事实、数字、原引语及来源不得漂移。
- [ ] 逐项扩展 News/en-US、Deep/zh-CN、Deep/en-US。复用工单和返回合同，不创建四套工作流。
- [ ] 单语失败保留另一语已成功正文；语义检查不能仅由数字/URL 正则替代。

## D — 配图与发布包

- [ ] 复用现有 Visual Planner → Validator → Compiler → Generation → Collector → Article Assembler，先验证一次有图交付。
- [ ] 补齐贯穿 collector/assembler/package 的零图和图像失败旁路，正文不丢失；不是只改 minItems。
- [ ] 按资产 ID 与锚点组装，除图片区块外正文不变。实际查看图片；不把请求尺寸当成实际尺寸，不伪造图片 URL。
- [ ] 英文 Social Kit 只读取正文；kit 失败不丢正文，中文不强制套英文营销模板。
- [ ] 发布包使用真实 draft/preview 状态，无残留占位符和虚构发布 URL。

## E — 母流程双入口

- [ ] direct-ready 与 News 补查 ready 汇入同一准备/调用路径；hold 不得误入 Writer。
- [ ] 正式调用决定引用有效审批及明确语言；模型 ready 不构成授权，历史 false 保留。
- [ ] 明确 Drafting Phase 调用新版 Writer，而非旧 `65KUDdo1G6k3VysU`；以实际子 execution 核实版本。
- [ ] 直接 ready 覆盖 News/Deep × 中英；News reassessment 覆盖中英；Deep reassessment 保持零 Writer 调用。
- [ ] 每条声明成功的组合均有真实父→子→最终 draft 证据。模拟审批不宣称真实邮件投递验收。

## 本轮执行记录

[KNOWN][HIGH] 2026-10-04 启动 T04 前：已回读 Writer 当前版本、仓库规范及历史 557。恢复挂载测试包后，原 73 项接口回归全部通过。完整仓库 clone 仍因 `Could not resolve host: github.com` 失败；不声称其他仓库测试或 CI 通过。

[INFERRED][HIGH] 下一动作：保存并验证完整成稿 fixture，然后执行 B 的单一中文初稿路径。无生产发布授权。
# AI Daily V3 写作 MVP — 执行计划

[KNOWN][HIGH] 更新：2026-10-04。执行分支：`n8n-v3-handoff-20261003`。本文件接续原 A–E 执行计划；原交接中的产品、批准、证据保真和最终验收边界不变。

## 当前结论

[KNOWN][HIGH] T01/T02 与 T03 受控调用入口已有局部验证。T04 已实际调用中文撰稿模型并产出两版全文，但两版内容均未通过验收，暂停继续抽样。未通过的提示词补丁已经回退，临时测试节点已经移除。不能把接口回归通过或执行 success 当作内容通过。

| 对象 | 当前记录 |
|---|---|
| [KNOWN][HIGH] Writer V2 `nHxILnDVz541Cu5P` | 最终草稿 `33f58d70-6b60-4fc8-b98f-32ce2aa73d73`；77 节点；active=false；activeVersionId=null。 |
| [KNOWN][HIGH] 本轮恢复点 | `ee17d426-9bd3-4325-bb3c-8527c93a808c`。恢复前先检查他人是否有后续变更。 |
| [KNOWN][HIGH] 最终业务差异 | 仅增加 `V2 Language Switch` 中文输出 1 → `V2 CN Lead Writer`；中文 Writer 仍为终点。 |
| [KNOWN][HIGH] 母流程 / Shared Dispatch | 本轮未修改；前轮记录分别为 `4473eaa6…` / `fb841db9…`，再动工前必须回读。 |
| [KNOWN][HIGH] 普通手动入口 | 原 `Writer Context Builder` 保存的旧 pin data 在 589 替换了当前材料，尚未清除。 |
| [KNOWN][HIGH] 正式审批 | 550 是 awaiting_selection；557 不含原 selected approval provenance。不得事后补造。 |

## 执行规则

[INFERRED][HIGH] 一次一个节点或不可分接口：读取代码、版本和 payload → 保存恢复点 → 观察失败 → 最小修改 → 固定输入正负例 → 阅读实际输出 → 提交并回读仓库。无新证据不重试；同一分支两次失败就停，不换 provider 掩盖问题。

[INFERRED][HIGH] 复用既有模型、配置、代码与测试，不增加运行框架、授权数据库、重复策划 Agent 或四套模式工作流。只交付 draft/preview，不启用生产发布；历史 false 不改写成新授权。

[INFERRED][HIGH] 代码、脱敏可复现 fixture、测试和检查点保存到本分支，不合并 main。未审定正文、运行栈、token 和凭据仅放本地 `.local/`；不提交公开仓库。文字稿可以作为明确标记的未通过候选交付用户审阅。

## A — 安全入口与写作准备

- [x] [KNOWN][HIGH] T01：共用 Prepare Writing Handoff 支持直接 ready 与 News 补查 ready；结构化材料、引语、人工原话和历史记录保留。
- [x] [KNOWN][HIGH] T02：工单映射为 writer_brief.v3 / writer_context.v1，严格中英路由。News 不补 thesis；Deep 需要有效判断。
- [x] [KNOWN][HIGH] T03：受控调用决定原生正负例 587/588 已验证，详见 `2026-10-04-t03-native-verification.md`。
- [ ] [KNOWN][HIGH] 普通 manual 入口的旧 pin data 清理及全路径再验证。隔离测试入口成功不代表原入口成功。

[INFERRED][HIGH] 补查业务保持“结果校验与合并 → 原编辑复核一次 → 共用写作准备”。Post-Supplemental Ready 是状态，不新建模块。不重新选题或自动再补查；Deep reassessment 继续 hold。

## B — T04 中文 News 初稿：调用已验证，内容未通过

- [x] [KNOWN][HIGH] 回读 557，复用历史 fixture，补回写作材料：8 来源、10 条断言、23 条支持摘录、5 条引语、3 条选中引语、6 个报道段落任务和 1 个未决问题；其中 2 个来源不具事实使用资格。
- [x] [KNOWN][HIGH] 保存恢复点；590 验证完整材料经同代码临时映射器、原 Gate 和 Switch 到达中文出口，尚无正文。
- [x] [KNOWN][HIGH] 只接中文 Writer；591 验证缺调用决定被拒绝；592/593 使用真实模型，不固定模型或 Writer 输出。
- [x] [KNOWN][HIGH] 逐篇通读。592 暴露来源元数据扩写、引语拼接和范围漂移；仅改用户提示词后，593 仍有“没有材料”扩大成“无人测量”及功能归属问题。
- [ ] [KNOWN][HIGH] 正文质量通过。当前为 FAIL，不进行第三次抽样，不进入英文或视觉分支。
- [x] [KNOWN][HIGH] 临时 Manual/Payload/Context Replay 节点全部删除；试验提示词回退。最终版本差异仅保留中文接线。
- [x] [KNOWN][HIGH] 两版未通过候选保存在本地 `.local/t04/`；仓库存测试、fixture、当前提示词与检查点，不存候选正文。
- [ ] [INFERRED][HIGH] 最小 text-preview 返回合同与失败状态，需后续单独验证，不以原始 output 冒充正式发布包。

[KNOWN][HIGH] 详见 `2026-10-04-t04-cn-draft-checkpoint.md`。本地接口集合 74/74 通过，但两版实际文章的已知缺陷检查均失败；这些是不同的验收对象。

[INFERRED][HIGH] 下一动作先处理旧 pin data 的受支持清除方式并验证原输入身份；随后基于已保存失败样本定位写作事实边界，不继续堆禁词或盲抽第三篇，也不通过切换模型掩盖失败。

## C — 审稿与其他语言/模式（未开始）

- [ ] 共用 Contract & Evidence Review 读取当前语种正文和证据，解除旧英文节点硬绑定。
- [ ] 正常稿不强制多轮风格评审；有缺陷才一次定向修订并再次核对。仍不通过则 review_required，不无限循环。
- [ ] 修正中文编辑节点的英文复制配置；保护事实、数值、引语和归属。
- [ ] 依次验证 News/en-US、Deep/zh-CN、Deep/en-US；复用共同工单和输出合同，不新建四套工作流。
- [ ] 单语失败不丢另一语正文；正则检查不冒充完整语义验收。

## D — 配图与发布包（未开始）

- [ ] 复用已有 Planner → Validator → Compiler → Generation → Collector → Assembler，实际查看生成图片并验证一次有图交付。
- [ ] 零图及图片失败旁路贯通 collector/assembler/package，正文不丢；不能只修改 minItems。
- [ ] 按资产 ID 和准确锚点组装，除图片区块外正文不变；不伪造图像 URL，不把请求尺寸当实际尺寸。
- [ ] 英文 Social Kit 只使用正文；失败可降级保留正文，中文不强套英文营销模板。
- [ ] 最终包保持真实 draft/preview 状态，无占位符或虚构发布 URL。

## E — 母流程双入口（未开始）

- [ ] 直接 ready 和 News 补查 ready 汇入共同准备/调用入口，hold 不进 Writer。
- [ ] 本次调用决定有真实批准来源和明确语言；ready 不自行生成权限，历史 false 保留。
- [ ] 明确调用新版 Writer 而非旧 `65KUDdo1G6k3VysU`，通过实际子执行核对版本。
- [ ] 直接 ready 覆盖 News/Deep × 中英；News 补查覆盖中英；Deep 补查保持零 Writer 调用。
- [ ] 每条成功组合均有真实父→子→最终 draft 的连续证据；模拟审批不宣称真实邮件投递成功。

## 验证范围

[KNOWN][HIGH] 本轮使用隔离本地快照及连接器保存；完整仓库 clone 因 `Could not resolve host: github.com` 失败。已运行本地全部 `tests/n8n/*.test.cjs`，未运行其他仓库测试或 CI；没有独立 reviewer。保留这些限制，不标全仓验收完成。

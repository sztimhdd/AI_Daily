# E1 — 一次轻编辑与原稿保留

[KNOWN][HIGH] 2026-10-06。承接用户对四篇 D 初稿的审阅，本轮只执行一次轻编辑，不重跑主笔、不补研究、不生成图片或 Kit、不发布。技术接口通过；稿件仍有明确遗留问题，不标记为终稿通过。

## 实现

[KNOWN][HIGH] Mother / Long-Content-Writing（xR7fM1ZhxlMTUy0L）沿用 D 的逐语言循环。在 Capture Mode Draft 之后加入 Draft Ready for Edit → Light Editor → Capture Light Edit，回到同一循环；无成功初稿时跳过编辑。Aggregate Drafts 保留 drafts，同时收集 previews 与 editing_stage。没有第二个循环、旧工单、授权包装、评分器、冷读 Agent 或新工作流。

[COMPUTED][HIGH] 母流程 53 → 57 节点，新增四个：条件分流、共享编辑、编辑模型、结果捕获。只修改一个既有 Code 节点 Aggregate Drafts；主笔、研究和其他永久节点未变。编辑使用原有编辑模型 gpt-6-luna 与同一凭据，temperature=0.3、maxIterations=1、maxRetries=0、retryOnFail=false，故障不切换供应商。

[KNOWN][HIGH] 编辑读取该篇实际来源原文、story_direction、narrative_feedback、human_instructions 和 light_edit_notes。当前稿件的具体纠错作为输入，不硬编码进通用编辑提示词。原稿不被覆盖；报错、空稿、格式错误、明显错语种标题或原稿有链接而编辑全部丢链接时，预览回退原稿。正常编辑也保留原稿供对照。

[KNOWN][HIGH] 自动校验仅为 structure_title_script_and_nonzero_links_only；它不核实事实、正文语言、每条引用的对应关系或文学质量。链接变化被记录，删除纯方法说明的唯一来源可以删除对应链接。不要把 edits_ready 当成事实终审或发布许可。

## 输入与执行证据

[KNOWN][HIGH] 从原生执行 749/750 回读了原稿实际使用的三个材料条目及叙事快照，保留摘录/partial 标记。这是原稿的实际输入，不是完整 743 研究池，也不是本轮重新核实新闻。750 的 Narrative 原本就是明确标记的合成人工修改测试；本轮保留其 provenance，不冒充历史上真实审批。用户本轮授权的是按审阅要求编辑这四篇。

| 执行 | 类型 | 结果 |
|---|---|---|
| [KNOWN][HIGH] 751 | News 合成输入，中文编辑原生抛错，无模型 | 中文 failed 并返回原稿；英文合成编辑稿保留；原上下文不变；edits_partial。 |
| [KNOWN][HIGH] 752 | Deep 合成输入，中文编辑空输出，无模型 | 中文失败保原稿；英文合成编辑稿及 Narrative 保留；edits_partial。 |
| [KNOWN][HIGH] 753 | 原 749 两稿回放，真实共享编辑各一次 | 两版返回非空编辑稿；原稿与上下文保留；edits_ready。 |
| [KNOWN][HIGH] 754 | 原 750 两稿回放，真实共享编辑各一次 | 两版返回非空编辑稿；原稿与上下文保留；edits_ready。 |

[KNOWN][HIGH] 753/754 的模型执行元数据分别只有两个 Light Edit Model runIndex；本轮共四次真实编辑调用。Writer 分支由临时回放绕过，未运行主笔或研究。native assertion passed=true 证明当前输入在循环后保留，不证明新闻事实或编辑质量。

[COMPUTED][HIGH] 交付四稿的长度及 FNV-1a UTF-16 指纹与原生输出逐一一致；四篇原稿的回放指纹也与 ZIP 中的原文件一致。编辑后字数口径为包含 Markdown 的 UTF-16 字符数：News 中 1333、英 2551；Deep 中 1355、英 2639。没有手工改写模型输出或第二次编辑。

[COMPUTED][HIGH] 本地 node --test tests/n8n/light-edit.test.cjs：11 通过，0 失败。旧 Aggregate 先被三项行为测试证实丢失编辑预览，三项全部 RED 后才改实现；其余测试覆盖错误、空稿、标题、链接全丢、错配及兄弟版本保留。不是完整仓库 CI，也不声称每项测试都单独完成 RED/GREEN。

## 实际读稿结论

[KNOWN][HIGH] 两篇中文已经区分“本机虚拟机也迁到云端”和“模型推理原本在云端”；中文 Deep 的“照常跑完”“谁在线都无所谓”已删除，改为有条件的继续运行描述。两种模式均保留本机文件访问仍需桌面应用的限制；中文 Deep 分别表述会话结束销毁沙盒、删除会话删除副本，没有合并触发条件。

[KNOWN][HIGH] 四稿的独立研究过程说明已去除。中文的转载链接随对应方法自评段删除，直接工程师来源与官方帮助页 URL 保留；英文原有两种不同来源网址均保留。新闻稿把日期、套餐、新旧任务与选项变化提到前面；深度稿的两类依赖判断在开头明确，没有新增宏大战略论点。

[INFERRED][HIGH] 编辑效果并未完全满足要求。中文 Deep 新增小标题“新设置与旧任务各自留在原处”，与本节“选项会被移除”矛盾。它应改为“选项被移除，旧任务留在本机”，但本轮不再编辑，原样输出并在交付说明中标注。

[INFERRED][HIGH] 中文 News 仍在首尾两次解释项目/计划任务不会转到 Claude Code，最后又重复本机文件依赖；开头过密、主来源链接离首段较远，且链接标签仍是英文。中文 Deep 的限定仍有重复，整体仍是带判断的技术解释稿。英文 Deep 的开头判断与末段仍有一定重述，英文 News 段落链接出现较密。轻编辑改善了主要问题，不证明四稿已达到最终出版质量。

[KNOWN][HIGH] 本轮未二次重抽、未人工修正后冒充全自动成稿。阅读检查由执行者本人完成，没有另派独立审查 Agent。

## 清理与恢复

[KNOWN][HIGH] 起点 f9e054b5-62d8-4a7b-bcb9-0ace1ed8dd85；永久 E1 补丁 04b62d87-93d8-4950-a550-fb84a10566ca；清理后 e52c8b19-33eb-4e52-bf88-5dedf94e0125。五枚临时测试节点全部移除，Writer Mode 接线恢复。永久补丁到清理版的原生 diff 五项数组均为空。Aggregate Drafts 仍为终点。

[KNOWN][HIGH] activeVersionId 仍为旧 c94debcc-2fe0-438a-a3df-a1d699740c99，未将新草稿发布上线；不声称整个实例 inactive。原邮件入口与发布侧隔离不变。没有修改旧 81 节点 V2 Writer，也没有发送邮件或运行图片/Kit。E2 配图、F 全链验收与生产发布仍未完成。

## 保存范围

[KNOWN][HIGH] 本提交保存 src/n8n/capture-light-edit.js、collect-mode-drafts.js、light-edit.nodes.json、tests/n8n/light-edit.test.cjs 与本检查点。节点 JSON 是 E1 增量和接线映射，不是全母流程导出。实际稿件和来源输入只交付会话 ZIP，不放入公开仓库；历史主计划未重写，E1 状态以本检查点为准。

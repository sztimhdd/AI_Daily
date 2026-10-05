# 写作 MVP 执行计划

[KNOWN][HIGH] 2026-10-05（America/Halifax）· 分支 n8n-v3-handoff-20261003 · 仅草稿/预览，不启用生产发布。

## 目标

[INFERRED][HIGH] 受众愿意点开、读下去、读完有所得。已批准 Story 与材料 → 初稿 → 现有编辑一次 → 预览。局部问题就地修，不等初稿零瑕疵才编辑；不新增评审 Agent、评分器或研究循环。准确是底线，不是正文主题。

[INFERRED][HIGH] 配图编辑根据编辑稿决定正文图数量、内容和位置，零张、一张、多张均可，封面另算。生成和组装只执行计划，不重写正文；附属环节失败保留已有稿。

## 当前状态

[KNOWN][HIGH] 中文连续预览：597 → 598。原文章配图恢复：630；用户已在浏览器确认 GitHub Markdown 可显示图片。GitHub raw URL 继续作为当前图床，不再维护 ImgBB 并行方案。

[KNOWN][HIGH] 中文预览现已正式连接视觉入口。执行 633 从完整历史工单连续经过 Writer → 中文编辑 → V2 Visual Input；Visual Planner 遭模型服务两次 502，链路按设计降级为纯文字。执行 634 复用 633 的同一编辑稿，从视觉入口重试并完成 Planner → 2 张真实生图 → GitHub 上传 → Asset Collector → Article Assembler；Planner 自主选择 1 封面 + 1 正文图，这是该稿的编辑决定，不是固定配额。执行 635 用 editor-failed/review_required 预览验证在 V2 Visual Input 阻断，Visual Planner 未执行。详见 [中文预览接视觉链检查点](2026-10-05-cn-preview-to-visual.md)。

[KNOWN][HIGH] Writer 中文阶段基线为 e2fe8fc5-ba30-430b-8a33-403fb8e89b87（81 节点、未发布）；相对 8e919b8e-d6f7-408d-95ac-f797416d0bf4 的唯一业务 diff 是 V2 CN Preview → V2 Visual Input 一条连接。当前英文改造后的草稿见下文，不要回退成这个历史基线。原 Writer Context Builder 在手动执行中仍残留旧 pinned/mock data，连接器没有清 pin 动作；该状态只作为手动测试污染记录，不能拿原节点的手动 replay 作为验收证据。封面 16:9 裁切后置。

[KNOWN][HIGH] News 补查后 ready 的受控集成已验收：母执行 652 → 原 Writer integrated 子执行 654 → 母流程验收终点。完整历史材料 8 来源 / 10 断言 / 5 引语及历史授权均保留，2 张真实生成上传、1 张正文图插入、组装未改文；649 缺审批拒绝，651 待审原样返回且不调用 Writer。测试审批为 synthetic，未重跑研究或真实 Gmail HITL。该阶段 Mother 清理后草稿为 4eab367f-e19e-4d39-b8c7-e2a661998a52，46 节点；与验收前 082f4ce5-8c94-4fae-a442-e180d46e330f 业务图差异为空。详见 [News 补查集成检查点](2026-10-05-news-post-research-integration.md)。

[KNOWN][HIGH] News 英文接口已受控验收：664 → 原 Writer 666，一次主笔、一次现有编辑、共用视觉尾部连续返回英文图文；3 张真实生成上传、2 张正文图插入，组装未改文。658/660 语言错配在 Gate 拒绝；661/663 用原生错误传输验证编辑失败原稿返回且不启动配图。调用授权明确为 controlled_test，不伪造正式审批；历史材料及授权保留。详见 [News 英文检查点](2026-10-05-news-english-preview.md)。

[KNOWN][HIGH] 当前 Writer nHxILnDVz541Cu5P 草稿 3f6c0030-d572-4ec1-8ba6-e2d27486326f，81 节点、inactive、无 activeVersion；只复用六个现有英文节点，中文和共用视觉节点未改。Mother 当前草稿 5a2a9835-bf50-497b-a6b8-0c0a362e68f8，46 节点，与 4eab367f 的业务图差异全空。八个母流程 TEMP EN 节点和两枚 Writer 故障探针全部清理。母流程 activeVersionId 仍为旧 c94debcc-2fe0-438a-a3df-a1d699740c99。永久母流程调用仍指定中文，显式英文工单通过不等于生产双语调度已接通。

## 下一步（依次执行）

- [x] **中文预览：** 连续返回初稿与编辑稿，编辑异常保留原稿。
- [x] **图文预览接口：** 中文编辑稿已接入视觉入口；真实视觉规划、生图、GitHub 托管、动态组装及编辑失败阻断均有原生执行证据。636 → 637 与 652 → 654 已分别随母流程直接 ready / 补查后 ready 集成完成连续调用，不再为这个接口重复消耗 Writer + 生图。
- [x] **母流程 direct-ready 中文：** 已接入同一 Writer 调用链。636 → 637 原生验证 parent → child → 中文编辑 → 动态配图 → 3 张真实生图 → GitHub → assembled article。测试使用 synthetic approval provenance，因此不冒充真实 Gmail HITL；integrated child call 未受手动 pinned data 污染。详见 [direct-ready 检查点](2026-10-05-mother-direct-ready-writer.md)。
- [x] **News 补查 ready：** 已回到同一 writing handoff / invocation / child call 链，并以 652 → 654 验收历史完整材料到中文图文返回；不复制 Writer 分支，不重新研究第二次。合成审批与实际模型调用分别记录，不代表真实审批或生产发布通过。Deep supplemental 继续 hold。
- [x] **News 英文接口：** 655 修改前原生 RED → 664/666 实际英文图文返回；复用原主笔/编辑及共用视觉链，News 不强塞 thesis。授权语言错配拦截、编辑失败原稿返回已验证。仅显式 en-US 工单的受控技术预览，未代表最终出版质量或生产双语分发。
- [ ] **其他组合：** 先 Deep 中文，再 Deep 英文；展开材料支持的判断。分别成文、共用接口，不复制四套流程；Deep 补查保持 hold。
- [ ] **后续交付收尾：** 统一处理母流程语言调度、封面比例、Social Kit/交付、真实审批与发布验收。现有英文测试稿还需减少结尾重复、补足读者向来源链接和厘清功能归属；不为这些问题再建评分层。正式发布需单独确认。

## 验收与保存

[INFERRED][HIGH] 每次一个节点或不可分接口：回读与恢复点 → 最小改动 → 复用 payload 测正例和针对性负例 → 看实际产物 → GitHub 保存并回读。不改凭据、不发布、不合并 main；两次无改进停止盲试，定位或编辑已有稿。

[INFERRED][HIGH] 技术看连续交付、身份和失败保稿；阅读看开头、推进和收获。图片 URL、上传回执、200、PNG 头、像素解码、用户显示分别记录，不相互冒充。单元通过不等于全链通过。代码和脱敏测试入库，正文、私有 payload、原始日志与凭据留本地；接口测试不代表全仓 CI。

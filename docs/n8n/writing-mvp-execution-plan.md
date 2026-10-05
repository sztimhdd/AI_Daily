# 写作 MVP 执行计划

[KNOWN][HIGH] 2026-10-05（America/Halifax）· 分支 n8n-v3-handoff-20261003 · 仅草稿/预览，不启用生产发布。

## 目标

[INFERRED][HIGH] 受众愿意点开、读下去、读完有所得。已批准 Story 与材料 → 初稿 → 现有编辑一次 → 预览。局部问题就地修，不等初稿零瑕疵才编辑；不新增评审 Agent、评分器或研究循环。准确是底线，不是正文主题。

[INFERRED][HIGH] 配图编辑根据编辑稿决定正文图数量、内容和位置，零张、一张、多张均可，封面另算。生成和组装只执行计划，不重写正文；附属环节失败保留已有稿。

## 当前状态

[KNOWN][HIGH] 中文连续预览：597 → 598。原文章配图恢复：630；用户已在浏览器确认 GitHub Markdown 可显示图片。GitHub raw URL 继续作为当前图床，不再维护 ImgBB 并行方案。

[KNOWN][HIGH] 中文预览现已正式连接视觉入口。执行 633 从完整历史工单连续经过 Writer → 中文编辑 → V2 Visual Input；Visual Planner 遭模型服务两次 502，链路按设计降级为纯文字。执行 634 复用 633 的同一编辑稿，从视觉入口重试并完成 Planner → 2 张真实生图 → GitHub 上传 → Asset Collector → Article Assembler；Planner 自主选择 1 封面 + 1 正文图，这是该稿的编辑决定，不是固定配额。执行 635 用 editor-failed/review_required 预览验证在 V2 Visual Input 阻断，Visual Planner 未执行。详见 [中文预览接视觉链检查点](2026-10-05-cn-preview-to-visual.md)。

[KNOWN][HIGH] Writer nHxILnDVz541Cu5P：草稿 e2fe8fc5-ba30-430b-8a33-403fb8e89b87，81 节点，未发布。相对 8e919b8e-d6f7-408d-95ac-f797416d0bf4 唯一业务 diff 是 V2 CN Preview → V2 Visual Input 一条连接；临时测试节点已全部清理。原 Writer Context Builder 在手动执行中仍残留旧 pinned/mock data，连接器没有清 pin 动作；该状态只作为手动测试污染记录，不能拿原节点的手动 replay 作为验收证据。封面 16:9 裁切后置。

## 下一步（依次执行）

- [x] **中文预览：** 连续返回初稿与编辑稿，编辑异常保留原稿。
- [x] **图文预览接口：** 中文编辑稿已接入视觉入口；真实视觉规划、生图、GitHub 托管、动态组装及编辑失败阻断均有原生执行证据。暂不为了“同一 execution 全绿”重复消耗一次 Writer + 生图；下一次母流程集成运行同时承担这项最终连续验收。
- [x] **母流程 direct-ready 中文：** 已接入同一 Writer 调用链。636 → 637 原生验证 parent → child → 中文编辑 → 动态配图 → 3 张真实生图 → GitHub → assembled article。测试使用 synthetic approval provenance，因此不冒充真实 Gmail HITL；integrated child call 未受手动 pinned data 污染。详见 [direct-ready 检查点](2026-10-05-mother-direct-ready-writer.md)。
- [ ] **News 补查 ready：** 让 `Receive Selected News Reassessment` 回到同一 writing handoff / invocation / child call 链；不复制 Writer 分支，不重新研究第二次。Deep supplemental 继续 hold。
- [ ] **其他组合：** 逐一验证 News 英文、Deep 中文、Deep 英文；News 讲清事件，不强塞 thesis；Deep 展开材料支持的判断。分别成文、共用接口，不复制四套流程。

## 验收与保存

[INFERRED][HIGH] 每次一个节点或不可分接口：回读与恢复点 → 最小改动 → 复用 payload 测正例和针对性负例 → 看实际产物 → GitHub 保存并回读。不改凭据、不发布、不合并 main；两次无改进停止盲试，定位或编辑已有稿。

[INFERRED][HIGH] 技术看连续交付、身份和失败保稿；阅读看开头、推进和收获。图片 URL、上传回执、200、PNG 头、像素解码、用户显示分别记录，不相互冒充。单元通过不等于全链通过。代码和脱敏测试入库，正文、私有 payload、原始日志与凭据留本地；接口测试不代表全仓 CI。

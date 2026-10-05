# AI Daily V3 — Mother direct-ready 中文写作闭环检查点

## STATUS

[KNOWN][HIGH] 2026-10-05。本单元只接通母流程的 direct-ready 中文写作路径，不改补查路径、邮件、ledger 或发布。

[KNOWN][HIGH] Mother `Long-Content-Writing` 最终草稿版本：`8e06e97c-1ed0-471f-a9be-9e91412a3cf2`，44 节点。工作流对象仍显示 active=true，但 activeVersionId 仍是旧版 `c94debcc-2fe0-438a-a3df-a1d699740c99`；本轮没有发布新草稿。

## RED → GREEN

[KNOWN][HIGH] 修改前，`Research Needed?` 的 false output 没有任何 Writer 路径，RED 检查按预期失败。

[KNOWN][HIGH] 永久改动只有：
1. 新增 `Prepare Writer Invocation` Code 节点；
2. 新增 `Call Universal Draft Writing V2` Execute Workflow 节点；
3. `Research Needed?` false → `Prepare Writer Invocation`；
4. `Prepare Writer Invocation` → `Call Universal Draft Writing V2`。

[KNOWN][HIGH] `Prepare Writer Invocation` 对非 `prepare_writing` 状态直接返回空，保持旧 hold 行为；对 writing_work_order 验证身份、approved title/reader promise 与 preserved approval provenance，然后增加已验证的 `task_config={language:'zh-CN',content_type:'zhihu_longform'}` 与当前调用的 `writer_invocation_decision.v1`。历史授权字段不被改写。

## NATIVE INTEGRATION TEST

[KNOWN][HIGH] 母执行 636 使用执行 598 的完整 Stripe 写作材料，并将 provenance 改造成一个 **synthetic direct-ready approval fixture**。它只用于测试接口形状，`formal_hitl=false`，不能冒充真实 Gmail 选稿。

[KNOWN][HIGH] 636 在 Mother 内经过 `Prepare Writer Invocation`，产生 formal_hitl 形状的 call-time decision，然后通过 `Call Universal Draft Writing V2` 启动 integrated 子执行 637。

[KNOWN][HIGH] 子执行 637 使用原始 `Writer Context Builder`（没有测试 clone），并以 Stripe content_id 通过 `Writer Invocation Gate`。这说明先前只影响手动 replay 的旧 pinned data 没有污染这次 integrated child call。

[KNOWN][HIGH] 637 真实连续完成：
- Writer Context Builder
- Writer Invocation Gate
- 中文 Lead Writer
- 中文编辑
- writing_preview
- Visual Planner
- 图片请求
- 3 次真实生图
- GitHub 上传
- Asset Collector
- Article Assembler

[KNOWN][HIGH] Planner 自主选择 3 张图（1 封面 + 2 正文图），不是固定配额。Collector requested=3 / succeeded=3 / failed=0。

GitHub 资产：
- COVER_IMG: `n8n/images/20261005/test_full-source-dossier-20261002-r2/COVER_IMG-637.png`, blob `286f5d682c2499bb1da9fc8ee12c05a62f8cb85f`
- IMG_1: `n8n/images/20261005/test_full-source-dossier-20261002-r2/IMG_1-637.png`, blob `332909ea4e06966b6892c0ca9557d58f7fcdc2a7`
- IMG_2: `n8n/images/20261005/test_full-source-dossier-20261002-r2/IMG_2-637.png`, blob `cefb2453d79bde9aefa833b08d1d7de768237241`

[KNOWN][HIGH] Mother 636 的终点就是 `Call Universal Draft Writing V2`，收到 `writing_preview.v1`，其中 `assembly_status=completed`、assembled article 为 `READY_WITH_WARNINGS`，正文插入 2 张 body image。唯一 warning 是 COVER_IMG 仍为 1536×1024 generation canvas，相对 16:9 publication 目标为 geometry mismatch；裁切继续后置。

## CLEANUP / PONYTAIL

[KNOWN][HIGH] 两枚临时 direct-ready 测试节点已经删除。相对 Mother 基线 `4473eaa6-212c-4d7f-b94d-27492e70bbf5`，最终原生 diff 仅为上述 2 个节点 + 2 条连接。

[INFERRED][HIGH] 不增加 Receive Writer Output、额外审稿器或第二套 direct-ready 分支；Execute Workflow 的返回值已经是 assembled preview，足够作为本阶段母流程终点。

## BOUNDARY

[KNOWN][HIGH] 636 的 approval provenance 是合成测试数据，因此本轮证明的是 Mother → child → assembled article 的技术闭环和 formal-authorization contract，不是一次真实 Gmail HITL 审批。

[INFERRED][HIGH] 下一单元只处理 post-supplemental-ready News：让 `Receive Selected News Reassessment` 重新进入同一 writing handoff / invocation / child call 链。Deep supplemental 继续 hold。

# AI Daily V3 — 中文预览接入视觉链检查点

## STATUS

[KNOWN][HIGH] 2026-10-05。本单元只做一项永久业务改动：`V2 CN Preview → V2 Visual Input`。未改提示词、模型、凭据、生图接口、图床或组装器。

[KNOWN][HIGH] 最终 Writer 草稿版本：`e2fe8fc5-ba30-430b-8a33-403fb8e89b87`，81 节点，`active=false`、`activeVersionId=null`。相对恢复基线 `8e919b8e-d6f7-408d-95ac-f797416d0bf4` 的原生 diff 只有一条 connection added：`V2 CN Preview → V2 Visual Input`。

## RED → GREEN

[KNOWN][HIGH] 修改前的图检查明确失败：`V2 CN Preview` 没有输出连接到 `V2 Visual Input`。

[KNOWN][HIGH] 加线后 fresh-read 立即通过：中文 preview 输出 0 指向 `V2 Visual Input` 输入 0。没有新增永久节点。

## NATIVE EXECUTIONS

### 632 — 找到旧 pinned data 污染

[KNOWN][HIGH] 598 的 Stripe 完整 writing_work_order 通过临时 webhook 正确进入 `TEMP CN Replay Unwrap`；但原 `Writer Context Builder` 输出被一份旧“军事 AI 情报事件”数据替换。Gate 随即以 `prepared work order missing` 拒绝。该结果证明问题位于手动执行的 pinned/mock state，不是新连接。

[KNOWN][HIGH] 当前 MCP 没有清 pin/mock data 的动作。本轮没有重写 Builder 或保留并行 Builder。只在测试期间复制同一份 Builder 代码绕开 pin，测试完成后删除。

### 633 — Writer → 编辑 → Visual Input 连续到达

[KNOWN][HIGH] 使用 598 原完整工单，并把 controlled-test decision_source 更新为本轮用户批准。临时无 pin Builder 后，执行连续经过 Gate、中文 Writer、中文编辑、Preview 与 V2 Visual Input。

[KNOWN][HIGH] Visual Planner 的模型服务连续两次返回 502 Bad Gateway。Validator 将其转为 `visual_planner_failed`，Image Request Builder 跳过生图，Assembler 保留 2708 字符编辑稿并以 READY_WITH_WARNINGS 返回。降级路径工作正常。

### 634 — 同一编辑稿的视觉重试成功

[KNOWN][HIGH] 为避免重复消耗 Writer，634 直接复用 633 的 `writing_preview.v1` 从 V2 Visual Input 重试。Visual Planner 成功，并自主选择两张图：
- COVER_IMG — HALFTONE_PAPER_COLLAGE
- IMG_1 — HALFTONE_PAPER_COLLAGE，锚点为正文中解释 provider routing 的段落

[KNOWN][HIGH] 两张图片都由真实生成服务产生，并经现有 GitHub upload 节点写入开发分支：
- `n8n/images/20261005/test_full-source-dossier-20261002-r2/COVER_IMG-634.png`
- `n8n/images/20261005/test_full-source-dossier-20261002-r2/IMG_1-634.png`

[KNOWN][HIGH] GitHub 回读 SHA：
- COVER_IMG: `499d79977b29beced0d5baf11e81282e0b6bb7df`
- IMG_1: `a2eb632dd1d48ff1702437e5e912fd8fea3361da`

[KNOWN][HIGH] Collector：requested=2, succeeded=2, failed=0。正文图 1024×1024 为 PASS；封面生成画布 1536×1024，与 publication 16:9 目标不一致，因此保留 `image_geometry_warning:COVER_IMG`，裁切仍后置。Assembler 插入 1 张正文图并单独返回封面。

### 635 — 编辑失败必须不启动配图

[KNOWN][HIGH] 将 633 同一 preview 仅改为 `status=review_required`、`editing_status=failed` 后重放。执行停在 `V2 Visual Input`，错误为 `expected an edited, unpublished preview`；`V2 Visual Planner` 运行次数为 0。

## CLEANUP / PONYTAIL

[KNOWN][HIGH] 所有临时 webhook、unwrap、测试 Builder 和视觉重试入口均已删除。最终节点数恢复为 81。

[INFERRED][HIGH] 不再为了得到一次“全绿 execution”重复跑相同 Writer 和生图。633 已证明 Writer→视觉入口真实连续；634 已证明同一 preview 的视觉后半链真实成功。下一次母流程 direct-ready 集成测试自然承担 parent→child→assembled article 的单 execution 最终验收。

[KNOWN][HIGH] 未发布、未发邮件、未写 production ledger、未合并 main。

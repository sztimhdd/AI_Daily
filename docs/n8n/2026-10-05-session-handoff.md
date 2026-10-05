# AI Daily 写作与配图 MVP — 主控 Agent 交接

[KNOWN][HIGH] 交接日期：2026-10-05；项目时区：America/Halifax。本文件用于新会话直接接管，不要求读取整段聊天。本轮只读核查状态并制作交接，没有修改工作流、执行模型、生图或发布。

## 0. 先读这一页

[KNOWN][HIGH] **不是全流程已经跑通，也不是 GitHub 图床切换仍只有口头计划。** 本轮重新读取执行 627，确认它已成功结束：一张新测试封面经过真实生成、GitHub 上传、资产归一化、收集和组装，返回了预览。原来那篇文章的两张失效配图尚未完成替换及用户可见性验收。

| 状态 | 当前结论 |
|---|---|
| [KNOWN][HIGH] 已完成并有历史运行记录 | 中文初稿→读者向编辑→文字预览；配图计划；动态图片请求；逐张生成/上传；零图与失败保稿；确定性图文组装。它们不是全部在同一次母执行里完成。 |
| [KNOWN][HIGH] 本轮补核实 | 627 为 success，生成并上传的是“暖白背景上的白色纸方块”测试封面，不是原文章的两张配图。 |
| [KNOWN][HIGH] 当前宿主 | 继续修改既有 `[Atomic] Universal Draft Writing V2`，ID `nHxILnDVz541Cu5P`；最新一次元数据读取为 81 节点、inactive、无 activeVersion。没有另建平行的配图工作流。 |
| [KNOWN][HIGH] 仍未完成 | 原文章两张图的可见交付；中文正文链→视觉链的一次连续调用；正式母流程集成；其余模式/语言组合；正式发布。 |
| [INFERRED][HIGH] 下一次最小行动 | 先拿现有 GitHub 测试图检查实际可读取/解码/显示，再恢复原方案两张图的可读预览；不要先重写正文、加审核层或重做架构。 |

[KNOWN][HIGH] 用户最近一次明确图床指令是：**“读我原来的工作流，要么用 GitHub 当图床，要么用 bbimage。”** 当前实现已经选了 GitHub。不要再转向第三种图床或另建内嵌图片存储体系；内嵌仅可作为交付文件的可选包装，不能替代实际托管验证。

## 1. 用户已经定下来的产品与执行原则

[KNOWN][HIGH] **阅读优先：愿意点开 → 读得下去 → 读完有所得。** 用户明确纠正过“证据、可靠、可信”的论文式写作倾向。准确是底线，不是正文主题；局部问题由已有编辑器就地修改，不以初稿不够完美为由反复重抽、重新研究。

[KNOWN][HIGH] **正文图数量由配图编辑读完编辑稿后决定。** 零张、一张、多张都合法，封面另算；数量、画面、图注和位置由文章需要决定，不能固定成“一封面＋一正文图”，也不能把测试样本的张数写成产品配额。

[KNOWN][HIGH] **News 与 Deep 是两种编辑任务。** News 服务普通 AI 兴趣读者，看清事件、背景、不同角度与实际使用，不强制原创 thesis。Deep 是有判断的杂志式分析，不是咨询报告或审计清单；中文和英文分别成文，不要求逐句翻译。Deep 补查复评当前明确 hold，不顺手接成 News 路径。

[KNOWN][HIGH] **/ponytail 持续生效。** 先查已有代码与旧工作流，优先复用、删除、原生节点，再写最少代码。每次只改一个节点或不可分接口，留下恢复点，用复用 payload 测正例与针对性负例，记录实际产物并保存 GitHub。不要新建评分器、重试服务、队列、授权数据库或平行工作流。

[KNOWN][HIGH] **不发布、不合并 main，不擅自变更凭据。** 已有授权覆盖开发分支保存及逐接口局测，不等于启用定时生产、真实邮件、生产 ledger 或浏览器发布。测试时应物理隔离副作用，不能只依赖前置 disabled 节点。

## 2. 仓库、工作流与恢复点

### 2.1 仓库

[KNOWN][HIGH] 仓库：`sztimhdd/AI_Daily`；本轮工作分支：`n8n-v3-handoff-20261003`。本轮读取的分支 HEAD 为：

```text
930f8f1c4975f6f1f902285ec2d7ea64c6325816
```

[KNOWN][HIGH] 这是制作本交接时的读数，不承诺新会话开始时仍是同一 HEAD。默认分支包含历史 Python 管线、历史工作流与已发表文章；找当前改造代码必须显式指定开发分支，不能把默认分支搜索结果当成当前草稿。

### 2.2 工作流定位

| 对象 | ID | 交接说明 |
|---|---|---|
| [KNOWN][HIGH] 当前 Writer | `nHxILnDVz541Cu5P` | `[Atomic] Universal Draft Writing V2`；实际改造目标，V2 名称在此次改造前已经存在。 |
| [KNOWN][HIGH] 母流程 | `xR7fM1ZhxlMTUy0L` | `Long-Content-Writing`；历史 active 与改造 draft 不同，本轮没有重新验收母流程。 |
| [KNOWN][HIGH] Shared Dispatch | `qAfs9BDFbdBotgaB` | 共用分流与工单准备，不另建补查后 Writer 准备器。 |
| [KNOWN][HIGH] 旧 Writer | `65KUDdo1G6k3VysU` | 原交接曾指定的旧目标；后改为复用现成 V2，旧 Writer 不再逐节点翻修。 |
| [KNOWN][HIGH] News Editor | `erbgzbMR5oNmEX2S` | 新闻编辑与原故事补查复评相关。 |
| [KNOWN][HIGH] Deep Editor | `sXFTgr72EKZUUlWL` | 深度编辑。 |
| [KNOWN][HIGH] Story Approval | `gFssJK9jikxTAtYY` | Story 审批候选与决定。 |

[KNOWN][HIGH] 当前 Writer 最后一次元数据读取、可读取版本历史和仓库计划一致指向：

```text
versionId:       6219c4c4-07ca-4c28-8c33-461650764ec3
active:          false
activeVersionId: null
nodeCount:       81
```

[KNOWN][HIGH] 本轮较早一次元数据曾返回 `cec2a332-31f7-4efa-8c56-bd5229b28907`，但随后历史查询找不到该版本；再次读取元数据回到上述 `6219c4c4…`。原因未确认。**不要把 cec2a332 当作可恢复点；执行下一次变更前重新读取元数据与历史。** 本轮未为解释该差异执行任何写入或回退。

| 恢复点 | 意义 |
|---|---|
| [KNOWN][HIGH] `6219c4c4-07ca-4c28-8c33-461650764ec3` | 可读取的 GitHub 图床版本；临时测试入口已移除。 |
| [KNOWN][HIGH] `bc21cf13-35eb-4cc4-8986-c21928185ac1` | 切图床前稳定状态；图片故障诊断节点已清理，仍用旧上传层。 |
| [KNOWN][HIGH] `1ba246e7-9922-4801-89f6-ca7970b7c06a` | 组装器接通后的稳定版本；与 bc21 的业务图在当时核对为空差异。 |
| [KNOWN][HIGH] `c9669757-3429-4ccb-b7fc-0a91fc66ed03` | 真实图片传输 616 完成、组装器改造前的历史恢复点。 |

[KNOWN][HIGH] 本轮原生差异 `bc21… → 6219…` 只有：删除 `Upload to ImgBB`，添加原生 `Upload Image to GitHub`，修改 `V2 Image Asset Normalizer`，替换对应输入及正常/错误出口连线。节点净增为零，没有另建图片工作流。

## 3. 当前逻辑链与断点

[KNOWN][HIGH] 下图是模块级交接，不是整条流程已经连续验收的声明。中文编辑中间适配节点的精确画布名称需在修改前读取实际图，不按图中文字新建节点。

```text
已准备 writing_work_order.v1
  → Execute Workflow Trigger
  → Writer Context Builder
  → Writer Invocation Gate
  → V2 Language Switch
  → V2 CN Lead Writer
  → 现有 CN 编辑输入适配
  → 现有读者向 CN 编辑器
  → CN 阅读预览
       ╳ 尚未完成与下方视觉入口的连续调用验收
  → V2 Visual Input
  → V2 Visual Planner + 原结构化输出解析
  → V2 Visual Plan Validator
  → V2 Visual Prompt Compiler
  → V2 Image Request Builder
  → V2 Has Image Requests
       ├─ 有：Split Out1 → 现有 Loop
       │       → Generate an image
       │       → Image b64 to Binary
       │       → Upload Image to GitHub
       │       → V2 Image Asset Normalizer → Loop
       │       └─ 单图错误同样返回 Normalizer，继续其余图片
       └─ 无：直接进入 Collector
  → V2 Image Asset Collector
  → V2 Article Assembler
  → 当前终点：writing_preview.v1 + assembled_article

V2 EN Social Kit / 旧 Publication Package 后续合同尚未集成，保持隔离。
```

[KNOWN][HIGH] “Post-Supplemental Ready”曾被流程图画成独立模块，实际只是状态/入口概括。直接 ready 与 News 补查后 ready 复用 `Prepare Writing Handoff`。补查接收是代码校验/合并；原 News 编辑最多复核一次缺口和材料绑定，不重新选题，不追加循环研究。

## 4. 哪些结果已经验证，哪些没有

[KNOWN][HIGH] 下列较早测试是历史检查点与聊天记录中的执行依据；本轮没有重跑整套测试。**模拟服务测试、历史回放、真实模型、真实上传与完整母流程是不同层级。**

| 执行/阶段 | 支持的结论 | 不支持的结论 |
|---|---|---|
| [KNOWN][HIGH] 572–579 | 共用工单准备接受直接/补查 ready，检查来源、引语、身份和历史授权边界。 | 正式 Writer 已被调用。 |
| [KNOWN][HIGH] 580–582 | 结构化材料可映射为写作输入；语言冲突拒绝。 | 完整文章已产出。 |
| [KNOWN][HIGH] 583、584、587、588 | 缺少调用决定会停止；审批对象可沿原 parent_context 保留；受控正例通过 Gate，语言错配负例拒绝。 | 557 的历史审批已被补成正式 HITL。 |
| [KNOWN][HIGH] 592、593、594 | 两次真实初稿；后来在已有稿上执行读者向编辑，而非继续重抽。 | 用户喜欢的少量人工收尾版全部由工作流自动完成。 |
| [KNOWN][HIGH] 597 → 598 | 父子调用连续返回中文初稿和编辑稿，不靠人工复制正文。 | 选题→图文母流程已完成。 |
| [KNOWN][HIGH] 599、600 | 编辑异常返回待审并保留初稿；600 是固定响应回放，599 意外调用过编辑模型。 | 异常测试都零模型调用。 |
| [KNOWN][HIGH] 601–606 | 0/1/3 正文图计划接口；605 真实规划，选 1 封面+1 正文图；坏位置、待审稿分别拒绝。 | 每篇必须恰好两张图。 |
| [KNOWN][HIGH] 607–612 | 编译/请求构造支持动态数量，失败返回零请求且保稿。 | 图片已实际生成。 |
| [KNOWN][HIGH] 613–616 | 613–615 为模拟服务多图/失败/零请求；616 为真实原两张图片生成并上传旧图床。 | 原外链长期可用、手机上可见。 |
| [KNOWN][HIGH] 617–622 | 旧组装器 RED→修复；多图按段落排序，坏图只跳过自身；621 使用保存的文章与图片 URL，622 验证无请求连续返文。 | 621 的图片字节已读取、已显示。 |
| [KNOWN][HIGH] 623–625 | 实际封面下载 404；两次原图二进制引用读取失败。 | 整个图床永久失效，或用户设备有问题。 |
| [KNOWN][HIGH] 626 | 1×1 测试 PNG 经原生 GitHub 节点写入开发分支，随后通过仓库接口读回。 | 正式文章配图恢复，或匿名浏览器已成功显示。 |
| [KNOWN][HIGH] **627，本轮重新读取** | **真实测试封面生成→GitHub→Normalizer→Collector→Assembler，success。** | 原两张图恢复、实际图片目视验收、中文正文到图文一条龙。 |

[KNOWN][HIGH] 历史报告出现的 23/23、30/30 等数量是当时对应接口集合的结果，不是本轮新跑，也不是全仓 CI；不要相加后声称整个系统通过。部分历史完整仓库克隆遇到运行环境 DNS 故障，当时用已保存局部代码检查。

### 4.1 执行 627 的可复查收据

[KNOWN][HIGH] 执行时间为 2026-10-05 10:56:06–10:59:14 UTC，即同日 07:56:06–07:59:14 Halifax（UTC−03:00）。状态 `success`，最后节点 `V2 Article Assembler`。

```text
workflow_id: nHxILnDVz541Cu5P
execution_id: 627
content_id: test:github-image-host-native
article_title: GitHub 图床测试
image: COVER_IMG（白色纸方块测试封面）
image_counts: requested=1, succeeded=1, failed=0
body_images_inserted: 0
publication.state: NOT_PUBLISHED

repository path:
n8n/images/20261005/test_github-image-host-native/COVER_IMG-627.png

file blob SHA:
fc5b6bca93ef511fad3cac079766974c0dc8d75f

upload commit:
e7d546ee6dce9cc9f01a2cf869a6a673123635dd

reported file size:
891927 bytes

returned raw URL:
https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/n8n/images/20261005/test_github-image-host-native/COVER_IMG-627.png
```

[KNOWN][HIGH] raw URL 是上传回执返回值，**本交接没有对它进行匿名 HTTP 下载、图片解码或浏览器目视检查**。文中保留该地址是供下一会话定位，不是可见性交付保证。

## 5. 图片交付故障与已经选定的修复方向

### 5.1 故障不是“再换一个字符串就好”

[KNOWN][HIGH] 用户截图确认旧阅读预览不能加载图片。预览只包含外链；交付文件中的地址与后来读取的上传回执不一致。623 对回执封面地址得到 404；624、625 读取历史 616 的二进制引用失败。地址/引用不一致的原因没有查明，不能补写为确定的过期机制或设备故障。

[KNOWN][HIGH] 旧 `illustrated-preview-621.html` 只能当历史排版/文字产物，不能继续作为已修复图文交付。**不要把返回了 download_url、状态 READY 或组装成功当成真的看到了图。**

### 5.2 复用旧实现，而不是引入新图床

[KNOWN][HIGH] 已读取的旧文件为：

```text
archive/legacy-n8n/workflows/2026-08-12/AI-Newsroom-v2.json
```

[KNOWN][HIGH] 该旧版本有 GitHub `Create a file` / `Create a file1` 图片上传节点，路径为 `n8n/images_en/YYYYMMDD/...` 与 `n8n/images/YYYYMMDD/...`。另一方面，改造前当前 Writer 确实有 `Upload to ImgBB`。因此应说“复用了这一旧版的 GitHub 模式”，不能概括成“所有原工作流从来没有 ImgBB”。

[KNOWN][HIGH] 当前原生 GitHub 节点直接用 `binaryData=true`、`binaryPropertyName=image`，写入实际 PNG 字节，再使用响应 `content.download_url`。不要把 Base64 文本当普通文本文件再编码保存。新文件路径包含本次执行 ID，开发阶段写入已有开发分支，不写 main。

[KNOWN][HIGH] 归一化器已经读取 GitHub 响应，本轮仓库 `src/n8n/image-asset-normalizer.js` 与可读取的 6219 版本差异中的实现一致。其仓库 blob SHA 为 `fc742cfc4081c5fbcab4850ee3143c80cf74a2b9`。

### 5.3 必须保留的未完成项

[KNOWN][HIGH] **当前归一化器的 width/height 来自 `generation.requested_size`，不是解码后的图片尺寸。** 627 中的 1536×1024 和几何状态不能被当作实际像素测量证据。后续验证图片字节时再确认真实尺寸；不为此建设审美评分层。

[KNOWN][HIGH] 原方案的封面目标为 16:9，历史生成要求为 3:2；裁切与目视检查未完成。先修图床可读和预览可见，裁切不要夹带进当前故障恢复，后续按已定顺序处理。

[KNOWN][HIGH] 图片进入开发分支不等于文章已经发布；但 raw 链接是远程资源，也不等于离线自包含文件。不要在交付说明里混淆这两种承诺。

## 6. 输入合同与不能丢掉的东西

[KNOWN][HIGH] 现有主合同包括：`writing_work_order.v1`、`writing_handoff.v1`、`writer_context.v1`、`writer_brief.v3`、`writer_invocation_decision.v1`、`writing_preview.v1`、`image_request.v1`、`image_asset.v1`、`assembled_article.v1`。继续复用，不为本环节再建同义 schema。

[KNOWN][HIGH] 历史 `writing_authorized=false`、`research_loop_authorized=false` 与 prepared 工单 `service_invoked=false` 不代表本次永远不能调用；本次调用需单独的决定，不能改写历史收据。调用决定绑定 content/story/mode/title/reader promise/language，受控测试与正式 HITL 不混淆。

[KNOWN][HIGH] 历史审批执行 550 是 `awaiting_selection`，不是 selected 正式审批。557 的完整研究材料可作为局测来源，但旧 parent_context 缺失审批对象，不能事后造出正式审批来源。

[KNOWN][HIGH] `initial:QT01` 与 `supplementary:QT01` 是不同引语。材料原文、来源身份、人工指令、标题与读者承诺保持；完成的历史补查要求不重新激活。News 不凭空补 thesis。

[KNOWN][HIGH] 组装器保留顶层原 `article_markdown` 和已有 `draft_markdown`，把插图后的文章放到 `assembled_article.article_markdown`；封面放独立 `cover_image`，正文图按原段落位置插入。警告只在元数据，不能写进阅读正文。消费者必须读取正确字段，不能因此再加一次文章重写。

[KNOWN][HIGH] 原 `Writer Context Builder` / Trigger 留过旧 pin data，手动测试曾替换成另一篇文章。已验证的父→子调用入口不依赖该 pin；未取得持久清除的证据。不要把临时同代码副本成功写成原入口成功；也不要在新会话直接点击整条母流程测试。

## 7. 保存位置与可复用 payload

### 7.1 新会话优先读的仓库文件

[KNOWN][HIGH] 以下均以分支 `n8n-v3-handoff-20261003` 为定位上下文；除明确注明本轮复读的文件外，清单依据历史保存记录，使用前读取实际内容。

```text
docs/n8n/writing-mvp-execution-plan.md               # 本轮复读，已写入 627 成功
src/n8n/image-asset-normalizer.js                    # 本轮复读，GitHub 版

docs/n8n/2026-10-05-preview-image-delivery.md         # 旧图不可见的问题检查点
docs/n8n/2026-10-04-article-assembly.md              # 617–622；旧上传时代的组装依据
src/n8n/article-assembler.js
src/n8n/image-asset-collector.js
src/n8n/image-binary.js
src/n8n/image-request-builder.js
src/n8n/visual-prompt-compiler.js
src/n8n/visual-planning.nodes.json
src/n8n/cn-line-editor.prompts.json
src/n8n/cn-edit-input.js
src/n8n/cn-preview.js
src/n8n/writer-context-builder.js
src/n8n/writer-invocation-gate.js
src/n8n/prepare-writing-handoff.js
src/n8n/build-shared-dispatch.js

tests/n8n/fixtures/handoff.cjs
tests/n8n/fixtures/writer-news-557.cjs                # 完整材料测试来源的历史保存路径
tests/n8n/article-assembler.test.cjs
tests/n8n/image-assets.test.cjs
tests/n8n/visual-requests.test.cjs
```

[KNOWN][HIGH] 本轮仓库计划 blob SHA：`d3ea604ef28a2761b4a97283a16328980c5eef34`。历史本地代码包在 GitHub 图床替换之前，可能仍包含 ImgBB 正常化实现；**代码以新会话读取的开发分支与 live draft 为准，旧包主要复用材料和回归样本。**

### 7.2 恢复原文章时应复用什么

[KNOWN][HIGH] 原故事是已保存的历史新闻测试稿，标题“Stripe 要买 OpenRouter：模型路由为什么成了支付公司的生意？”。此处仅用于定位原产物，不将稿件中的新闻当成本轮核实的事实。

| 需要的东西 | 来源 |
|---|---|
| [KNOWN][HIGH] 完整研究材料 | 557 衍生 fixture：8 来源、10 断言、5 引语；不是接口测试用的两来源小样本。 |
| [KNOWN][HIGH] 自动编辑稿 | 执行 598。用户喜欢的另一个手工收尾预览是文风参考，不冒充这次自动产物。 |
| [KNOWN][HIGH] 真实配图计划 | 执行 605；一封面、一正文图为这篇稿的实际编辑选择。 |
| [KNOWN][HIGH] 编译后的请求 | 已保存的 605 request 回放材料可重用现有编译器产生，不重新调用配图编辑。 |
| [KNOWN][HIGH] 原图上传记录 | 执行 616；旧链接已出问题，不直接重新包装成“已修复”。 |
| [KNOWN][HIGH] 原图文位置与排版 | 执行 621 / `.local/assembly-real-input.json`；可保留文章与锚点，不沿用坏 URL 作交付。 |
| [KNOWN][HIGH] 新宿主链证明 | 626 小图片上传、627 新测试封面上传。两者都不是上述文章图片。 |

[KNOWN][HIGH] 配套 ZIP 内包含从本轮实际挂载的历史包提取的三份材料：`payloads/visual-plan-605.json`、`payloads/visual-preview-605.json`、`payloads/assembly-input-621-broken-urls.json`。它们是保存材料，不会自动触发调用；旧图 URL 明确标为未修复。新会话需用户上传 ZIP 或经已有仓库/执行记录读取，不能假定本会话 `/mnt/data` 会跨会话存在。

## 8. 下一会话操作顺序：先接管，再修图，再接主链

### A. 只读接管，不重做之前的测试

[INFERRED][HIGH] 先读本文件，读取仓库计划和当前分支 HEAD；调用 `get_workflow_details`、`get_workflow_history`，确认当前草稿、临时节点和宿主节点。若版本变化，先查看原生 diff，不覆盖他人后续改动。

[INFERRED][HIGH] 读取 627 的 `Upload Image to GitHub`、`V2 Image Asset Normalizer`、`V2 Article Assembler`。成功收据已在本文件，复读是确认没有变更，不要再次为“证明 627”重付一次生图费用。

### B. 当前唯一优先故障：实际看到图

[INFERRED][HIGH] 用 627 的真实 raw URL 下载已有文件并解码、显示。检查返回的是图片字节，不是 HTML、错误图或 Base64 文本；仓库授权接口读回与匿名 raw 浏览器访问分开验收。已有工具不能取字节时，明确报告缺的能力，不长时间猜二进制 ID。

[INFERRED][HIGH] 宿主可读后，沿用 598 正文＋605 配图方案恢复原两张图；原图能恢复就不重生，不能恢复则按用户在后续交接中确认的方案重生这两张。使用已有 GitHub 上传链，不重写文章、不重选配图、不换模型兜底。返回 URL 后真正打开图片及阅读页，才称“原图文预览已修复”。

### C. 原故障关闭后才接中文到图文连续调用

[INFERRED][HIGH] 接现有 CN 预览到现有视觉入口。正例从一次调用连续得到可读图文；编辑失败分支保留文字、不误启动配图。之后处理封面目标比例，不建设新评分器。保留动态正文图数量与单图失败降级。

### D. 后续仍按简明计划

[INFERRED][HIGH] 先母流程直接 ready 中文，再 News 补查 ready，最后逐个扩展 News 英文、Deep 中文、Deep 英文。确认实际子工作流版本；保持 Deep 补查 hold。英文 social kit 失败不得丢正文；正式发布另行确认。

### E. 每次收尾必须可接管

[INFERRED][HIGH] 每次只提交本接口所需改动、脱敏测试和短检查点，注明执行 ID、payload 来源、是否真实模型/服务、是否保留旧稿、恢复点和未完成项。删除临时节点后再做版本差异核对。不要将密钥、恢复令牌、原始执行全集或私有材料提交公开仓库。

## 9. 直接粘贴给新会话的接管指令

```text
请接管 AI Daily 写作/配图 MVP，先阅读附件 AI_Daily_Handoff_2026-10-05.md；
有 ZIP 时也读取其中的保存 payload。持续使用 /ponytail，优先复用旧代码和原生节点，
一次一个不可分接口，测试后保存 GitHub，不新建平行工作流。

工作仓库 sztimhdd/AI_Daily，分支 n8n-v3-handoff-20261003。
目标工作流 nHxILnDVz541Cu5P（已有 Universal Draft Writing V2），不是新建 V2。
先只读核对当前草稿、历史及 GitHub HEAD，再决定修改。

已确认 627 完成一次真实测试封面生成→GitHub 上传→资产→组装，
不能继续当成“未知是否完成”；但这不代表原文章两张图恢复或手机能看到图。
先使用现有 627 图片检查实际 raw 文件读取、解码和显示；不要重复生成测试图。
之后复用 598 正文、605 配图计划，修复原两张图的 GitHub 托管预览。
不重新写正文，不另找图床，不用 URL 字符串代替可见性验证。

受众爱读是首要编辑目标；准确是底线，不把文章写成证据审计。
正文图数量、内容和位置由配图编辑根据草稿决定，不能固定张数。
原图片可读后，继续接中文正文链＋视觉链，保持失败保稿。
不得发布、合并 main、修改凭据或运行未隔离的生产母流程。
请报告本次实读状态、最小改动、真实测试和未完成项，不重复整套架构设计。
```

## 10. 证据定位与本轮边界

[KNOWN][HIGH] 本轮新核查的来源是：目标 Writer 元数据、版本历史、`bc21…→6219…` 原生差异、627 指定节点执行结果；GitHub 开发分支 HEAD、简明计划、归一化器源码；以及本会话实际挂载的历史 ZIP 内容。它们支持本交接的状态更新，不意味着重新审核过所有旧执行。

[KNOWN][HIGH] 持久定位：仓库 `docs/n8n/writing-mvp-execution-plan.md`；工作流页面 `https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P`；627 页面 `https://ohca.ddns.net/workflow/nHxILnDVz541Cu5P/executions/627`。工具访问权限/函数以新会话实际提供的 schema 为准，不照搬历史聊天里的 `functions.exec` 封装。

[KNOWN][HIGH] 本轮没有重跑测试、恢复原图片、裁切封面、执行母流程或开启发布。历史 621 预览仍是未完成可见性验收的旧产物，不是本次新交付图文。

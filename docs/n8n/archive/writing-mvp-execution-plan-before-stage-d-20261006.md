# 写作 MVP 执行计划

[KNOWN][HIGH] 2026-10-05（America/Halifax）· 分支 n8n-v3-handoff-20261003 · 仅草稿/预览，不启用生产发布。

## 目标

[KNOWN][HIGH] 当前用户要求：每篇选定文章默认交付zh-CN与en-US两个完整版本，标题、正文、Kit、正文Caption及图片Alt分别对应语言。两版共用批准的故事与材料，独立成文，不要求逐句翻译；成功版本不得因另一版或Kit失败而丢失。封面继续独立字段，不强加展示图注。

[INFERRED][HIGH] 受众愿意点开、读下去、读完有所得。已批准 Story 与材料 → 初稿 → 现有编辑一次 → 预览。局部问题就地修，不等初稿零瑕疵才编辑；不新增评审 Agent、评分器或研究循环。准确是底线，不是正文主题。

[INFERRED][HIGH] 配图编辑根据编辑稿决定正文图数量、内容和位置，零张、一张、多张均可，封面另算。生成和组装只执行计划，不重写正文；附属环节失败保留已有稿。

## 精简重构当前主计划（取代下面历史MVP推进顺序）

- [x] A. 保存10个相关流程的fresh-read基线，确认真实调用与孤立旧节点，物理隔离发布副作用。
- [x] B. 定时/手动采集 → 最多5题（不足明确提示）→ 选1题+补充方向 → 初轮研究；执行717完成公共抓取+Browser合并验收。
- [~] C. 一次Deep适用性判断已完成（729）；News自动方向已验证。待完成：Deep一次Narrative人工确认/修改，以及两分支共用定向补查。
- [ ] D. 保留两个模式Writer（News/Deep），用language参数各生成zh-CN/en-US；移除旧授权包装和旧Writer支线。
- [ ] E. 一次轻编辑；News优先真实来源图片/截图，Deep优先AI插图/示意图；复用上传/资产/组装，图片失败保稿。
- [ ] F. 母流程完整草稿验收后整理旧节点；真实发布保持独立，Kit最后补完。

[KNOWN][HIGH] B当前Mother draft=9e023eb2-3642-4eff-93b9-3dc3961318b5，activeVersion仍=c94debcc-2fe0-438a-a3df-a1d699740c99；执行717最终材料46条、公共正文4、Browser正文2、1条Browser失败显式记录、图片候选15、来源链接11，未发布。

## 历史 MVP 状态（仅作回归参考）

[KNOWN][HIGH] 中文连续预览：597 → 598。原文章配图恢复：630；用户已在浏览器确认 GitHub Markdown 可显示图片。GitHub raw URL 继续作为当前图床，不再维护 ImgBB 并行方案。

[KNOWN][HIGH] 中文预览现已正式连接视觉入口。执行 633 从完整历史工单连续经过 Writer → 中文编辑 → V2 Visual Input；Visual Planner 遭模型服务两次 502，链路按设计降级为纯文字。执行 634 复用 633 的同一编辑稿，从视觉入口重试并完成 Planner → 2 张真实生图 → GitHub 上传 → Asset Collector → Article Assembler；Planner 自主选择 1 封面 + 1 正文图，这是该稿的编辑决定，不是固定配额。执行 635 用 editor-failed/review_required 预览验证在 V2 Visual Input 阻断，Visual Planner 未执行。详见 [中文预览接视觉链检查点](2026-10-05-cn-preview-to-visual.md)。

[KNOWN][HIGH] Writer 中文阶段基线为 e2fe8fc5-ba30-430b-8a33-403fb8e89b87（81 节点、未发布）；相对 8e919b8e-d6f7-408d-95ac-f797416d0bf4 的唯一业务 diff 是 V2 CN Preview → V2 Visual Input 一条连接。当前改造后的草稿见下文，不要回退成这个历史基线。原 Writer Context Builder 在手动执行中仍残留旧 pinned/mock data，连接器没有清 pin 动作；该状态只作为手动测试污染记录，不能拿原节点的手动 replay 作为验收证据。封面 16:9 裁切后置。

[KNOWN][HIGH] News 补查后 ready 的受控集成已验收：母执行 652 → 原 Writer integrated 子执行 654 → 母流程验收终点。完整历史材料 8 来源 / 10 断言 / 5 引语及历史授权均保留，2 张真实生成上传、1 张正文图插入、组装未改文；649 缺审批拒绝，651 待审原样返回且不调用 Writer。测试审批为 synthetic，未重跑研究或真实 Gmail HITL。该阶段 Mother 清理后草稿为 4eab367f-e19e-4d39-b8c7-e2a661998a52，46 节点；与验收前 082f4ce5-8c94-4fae-a442-e180d46e330f 业务图差异为空。详见 [News 补查集成检查点](2026-10-05-news-post-research-integration.md)。

[KNOWN][HIGH] News 英文接口已受控验收：664 → 原 Writer 666，一次主笔、一次现有编辑、共用视觉尾部连续返回英文图文；3 张真实生成上传、2 张正文图插入，组装未改文。658/660 语言错配在 Gate 拒绝；661/663 用原生错误传输验证编辑失败原稿返回且不启动配图。调用授权明确为 controlled_test，不伪造正式审批；历史材料及授权保留。详见 [News 英文检查点](2026-10-05-news-english-preview.md)。

[KNOWN][HIGH] News 英文阶段 Writer nHxILnDVz541Cu5P 草稿为 3f6c0030-d572-4ec1-8ba6-e2d27486326f，81 节点、inactive、无 activeVersion；只复用六个现有英文节点，中文和共用视觉节点未改。该阶段 Mother 草稿为 5a2a9835-bf50-497b-a6b8-0c0a362e68f8，46 节点，与 4eab367f 的业务图差异全空。八个母流程 TEMP EN 节点和两枚 Writer 故障探针全部清理。母流程 activeVersionId 仍为旧 c94debcc-2fe0-438a-a3df-a1d699740c99。该阶段永久母流程调用仍指定中文，后续双语默认改造见下文；不要把旧阶段配置当成当前配置。

[KNOWN][HIGH] Deep 中文技术接口已验收：672 → 原 Writer 674，复用历史 Deep 提案 548 和初始材料（6 来源条目 / 6 断言 / 3 引语），受控 selection 与调用授权均明确标记；一次主笔、一次编辑、2 张真实生成上传、1 张正文图插入，组装未改文。667/668 缺判断拒绝，669/671 编辑错误原稿返回且不启动配图。详见 [Deep 中文检查点](2026-10-05-deep-chinese-preview.md)。

[KNOWN][HIGH] Deep 中文接口阶段 Writer 草稿 e99399b8-e083-4ad4-b820-58b20933a116，81 节点、inactive、无 activeVersion；该轮只改四个现有中文节点及一条出口，复用现有通用预览路由/保稿终点，虽仍使用历史 EN 名称，未复制新节点。Mother 草稿 458e8a54-26e7-4eb9-a14b-903cc8085e4a，46 节点，与该轮起点 5a2a9835 的业务图差异为空；八枚母流程临时节点及两枚 Writer 探针已清理，旧 activeVersionId 不变。

[KNOWN][HIGH] 历史674稿未通过出版质量验收：四条来源链接被编辑全部删除，且有材料外产品概括。后续676只调用原编辑，四个不同来源URL保留；677在676现稿上通过显式局部修正处理动机、配置和时间表达，没有重抽主笔或配图。阅读交付另有三处明确记录的人工微调，不能当成全自动成稿。详见 [中文编辑修复检查点](2026-10-05-cn-editor-link-repair.md)。

[KNOWN][HIGH] 中文修复及Deep英文阶段 Writer fdd4fa39-c4c2-4afc-b865-9cf1a3878b8b，81节点、inactive、无activeVersion。中文修复轮起点e99399b8到终点的原生diff仅CN编辑systemMessage，连接和节点增删为空。三枚临时测试节点已清理；该轮Mother、模型、凭据、英文和视觉节点未改。现有CN输入仍默认review_issues=[]，677证明显式纠错入口可用，不证明自动发现所有问题。

[KNOWN][HIGH] Deep 英文技术接口已验收：681 → 原Writer683，复用548深度提案及557初始材料，正确英文controlled_test授权，原英文主笔和编辑各一次，共用视觉尾部生成上传2张图、插入1张正文图，组装未改文。678/680语言错配在模型前拒绝。永久业务代码、提示词和接线零修改；九枚临时节点已删除，Mother清理版feae2b62-acfe-4d9f-9609-8ab2da7da8ba与起点458e8a54的原生业务diff为空，46节点、旧activeVersion不变。详见 [Deep 英文检查点](2026-10-05-deep-english-preview.md)。

[KNOWN][HIGH] 683自动稿仍需出版编辑：公告当时状态被写成现在时，结尾重复，来源均在末尾。初稿与编辑稿的3个来源网址均保留，未采用第四份报道独有内容，不强制补足配额。本轮交付保留自动产物，未重抽或人工改成假自动终稿。

[KNOWN][HIGH] 默认双语交付已受控验收：692一次经过原调用准备→原each调用→原Writer694中文/695英文→原汇总，返回两版完整包。标题、SEO、发布文案、标签、正文Caption和Alt对应语言；每版本次各生成上传2图、插入1正文图。684第一语种拒绝后保留第二版，688中文Kit抛错保留文章和英文版，前两组零模型；本地20项合同测试通过。详见 [默认双语交付检查点](2026-10-05-default-bilingual-delivery.md)。真实双语样本为Deep；News直接/补查默认双语覆盖是局测，不冒充新News全链运行。

[KNOWN][HIGH] 当前Writer a89919a4-b110-4236-9398-ab716c965e0a，81节点、inactive、无activeVersion；本轮只复用Kit/Parser/Package，增加Assembler→Kit。当前Mother e419a94d-5f80-4f41-8dde-05e00dae4cb2，46节点，复用Prepare/Call/Aggregate，移除旧发布方向连接；旧activeVersion c94debcc不变。八个母流程临时节点、两枚Writer探针全部清理，清理后分别与本轮永久补丁b68fd9c7/37869387的原生diff为空。没有新增永久节点、模型或凭据，没有启用生产。

[KNOWN][HIGH] 692两版仍是自动测试稿而非终稿：英文最终正文缺少来源链接，两版和Kit的公告时间表达、中文动机及Kit归属、文案冗长需收尾。语言检查是script_only，不是事实或语义终审。封面仍独立、无展示图注且保留几何警告。本轮未下载解码图片；上传成功不冒充显示验收。

## 下一步（依次执行）

- [x] **中文预览：** 连续返回初稿与编辑稿，编辑异常保留原稿。
- [x] **图文预览接口：** 中文编辑稿已接入视觉入口；真实视觉规划、生图、GitHub 托管、动态组装及编辑失败阻断均有原生执行证据。636 → 637 与 652 → 654 已分别随母流程直接 ready / 补查后 ready 集成完成连续调用，不再为这个接口重复消耗 Writer + 生图。
- [x] **母流程 direct-ready 中文：** 已接入同一 Writer 调用链。636 → 637 原生验证 parent → child → 中文编辑 → 动态配图 → 3 张真实生图 → GitHub → assembled article。测试使用 synthetic approval provenance，因此不冒充真实 Gmail HITL；integrated child call 未受手动 pinned data 污染。详见 [direct-ready 检查点](2026-10-05-mother-direct-ready-writer.md)。
- [x] **News 补查 ready：** 已回到同一 writing handoff / invocation / child call 链，并以 652 → 654 验收历史完整材料到中文图文返回；不复制 Writer 分支，不重新研究第二次。合成审批与实际模型调用分别记录，不代表真实审批或生产发布通过。Deep supplemental 继续 hold。
- [x] **News 英文接口：** 655 修改前原生 RED → 664/666 实际英文图文返回；复用原主笔/编辑及共用视觉链，News 不强塞 thesis。授权语言错配拦截、编辑失败原稿返回已验证。仅显式 en-US 工单的受控技术预览，未代表最终出版质量或生产双语分发。
- [x] **Deep 中文技术接口：** 672/674 连续返回中文图文，667/668 缺判断拒绝，669/671 编辑异常保稿；四节点最小修改、永久节点零新增。不代表出版质量通过。
- [x] **Deep 中文编辑修复样稿：** 676验证来源保留，677用现有review_issues处理已知局部问题；阅读稿有三处人工微调，复用674图片和原组装器。不追加审核层，不代表自动终审或新News回归通过。
- [x] **Deep 英文技术接口：** 681/683连续返回英文图文，678/680目标语言错配拒绝；复用现有分支、永久改动为零。成稿的时间表达、来源落点与结尾留待出版编辑；Deep补查保持hold。
- [x] **母流程默认双语调度：** 692→694/695从同一故事一次返回中文与英文；保留批准工作标题，交付使用各稿实际H1；原each调用及pairedItem汇总已验证，失败版本不覆盖成功版本。不再默认只出中文。
- [x] **同语言Kit与图片文字：** 复用原Kit/Parser/Package，SEO、文案、标签、正文Caption、Alt匹配语言，文件按语言区分；Kit失败保稿，动态正文图数量保留。仅交付接口通过，不是出版质量通过。
- [ ] **已有双语稿与Kit编辑收尾：** 复用694/695产物，修正时间、来源、动机/归属和冗长；不重跑主笔/视觉来掩盖局部问题，不新增评分层。
- [ ] **后续交付收尾：** 处理封面比例、实际图像显示、真实审批与发布验收。新默认双语配置仍是草稿；正式发布需单独确认，Deep补查保持hold。

## 验收与保存

[INFERRED][HIGH] 每次一个节点或不可分接口：回读与恢复点 → 最小改动 → 复用 payload 测正例和针对性负例 → 看实际产物 → GitHub 保存并回读。不改凭据、不发布、不合并 main；两次无改进停止盲试，定位或编辑已有稿。

[INFERRED][HIGH] 技术看连续交付、身份和失败保稿；阅读看开头、推进和收获。图片 URL、上传回执、200、PNG 头、像素解码、用户显示分别记录，不相互冒充。单元通过不等于全链通过。代码和脱敏测试入库，正文、私有 payload、原始日志与凭据留本地；接口测试不代表全仓 CI。

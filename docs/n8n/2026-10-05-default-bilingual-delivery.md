# 默认中英双语交付：标题、Kit、图片文字分别本地化

## 用户要求与结果

[KNOWN][HIGH] 本轮用户明确要求每篇文章默认生成中英文两个版本，标题、Kit、图片 Caption 对应语言。母执行692一次返回原Writer子执行694（zh-CN）和695（en-US）的完整包，末端断言passed=true、delivery_status=completed。两套文章、Kit、正文Caption和所有Alt实际读取均符合各自语言。不是只改变language字段，也不是把中文文章送去逐句翻译。

[KNOWN][HIGH] 这仅关闭默认双语交付接口，不关闭出版质量：英文最终正文缺少读者向来源链接，两版仍有公告时点被写成当前状态的问题，中文稿有动机直述，中文Kit的“用户现有的使命”归属不当，Kit篇幅仍需收紧。自动产物原样交付，不以人工改稿冒充工作流结果。

## Ponytail 最小实现

[KNOWN][HIGH] 继续复用当前Mother、Writer和Shared Dispatch，没有新增永久节点、模型、凭据、评分器、重试服务或平行工作流。先读原技能和已有图，发现Mother硬编码中文、旧Kit只接受英文、旧Package期待错误的顶层结构且限制1–2正文图。以下均修改现有节点。

[KNOWN][HIGH] Mother的Prepare Writer Invocation保留原审批和身份校验，给同一selected story产生两个独立深拷贝工单：zh-CN/zhihu_longform、en-US/linkedin_article。中文平台沿用原配置，不顺手变更上游受众。两个调用决定各自绑定目标语言，历史材料、授权、标题和读者承诺不改。

[KNOWN][HIGH] 原Call Universal Draft Writing V2改为原生mode=each并等待返回，onError=continueRegularOutput、alwaysOutputData=true。逐个子执行各只接收一个语言工单，保留原Writer的一项输入和.first()假设。原生错误输出通过pairedItem绑定原输入，第一项失败仍执行第二项；684已在实例上证实，不仅依赖上游源码说明。

[KNOWN][HIGH] 复用并启用Aggregate Drafts，按原生pairedItem而非标题猜语言，输出versions['zh-CN']和versions['en-US']。保留各版完整preview、标题、Kit、图片与失败状态。缺少、重复或错配的返回不能标成双语完成；失败不覆盖成功兄弟版本。其旧Drafting Phase输入和通往Prepare Browser Tasks的连接已物理移除，汇总是安全终点，没有接入浏览器、邮件或生产ledger。

[KNOWN][HIGH] 原V2 EN Social Kit保留旧画布名称，实际变为按输入language生成的共用Kit。读取当前assembled_article的实际标题和正文，输出同语言SEO标题、SEO描述、LinkedIn文案与四个标签；不拿批准时的工作标题替代成稿H1。Parser4增加必需language并允许中文标签，原模型与autoFix设置不变。Kit失败用原生错误传输返回原文，不丢成功文章。

[KNOWN][HIGH] 原V2 Publication Package Builder现在在writing_preview.v1上附加publication_package，读取嵌套assembled_article，保留原article_markdown、draft_markdown和图片URL。移除固定正文图数量和强制有封面的旧限制，沿用Assembler的资产检查和警告。包状态DRAFT或REVIEW_REQUIRED，始终NOT_PUBLISHED；DRAFT只表示交付结构，不表示可发布。

[KNOWN][HIGH] 原Visual Planner已按publication_profile.language产生Caption/Alt，本轮没有重写视觉规划。正文Caption必须匹配语言；封面继续独立返回，Alt本地化，没有展示图注，caption保持空串。若以后提供封面Caption也会检查语言。没有共享两版图片的强制约束，本轮每版各生成自己的图，不建立跨语言对图系统。

[KNOWN][HIGH] 标题、Kit、图片文字的检查为script_only：检测明显汉字/拉丁字母错配与字段身份，并不证明每句话语义正确、所有语言混写均能识别或无需人工编辑。错配保留原资产并标待审，不把错误文字重贴语言标签。

## 持久代码与接线

[KNOWN][HIGH] 保存映射：src/n8n/prepare-writer-invocation.js → Mother同名Code；aggregate-drafts.js → Mother Aggregate Drafts；publication-package-builder.js → Writer同名Code；localized-social-kit.json的kit_parameters/parser_parameters → 既有Kit/Parser4。三个Code均runOnceForAllItems；Aggregate启用；Kit设continueRegularOutput/alwaysOutputData。

```text
Mother: Prepare Writer Invocation (2 items)
  -> Call Universal Draft Writing V2 (each, wait, continueRegularOutput)
  -> Aggregate Drafts (terminal)

Writer: 原单语言主笔/编辑/视觉尾部
  -> V2 Article Assembler
  -> V2 EN Social Kit (language-dynamic)
  -> V2 Publication Package Builder

Removed: Drafting Phase -> Aggregate Drafts
Removed: Aggregate Drafts -> Prepare Browser Tasks
```

[KNOWN][HIGH] 新增仓库源文件是保存既有节点的实现，不是新增画布节点。失败编辑仍走原待审返回，不调用视觉/Kit；汇总保留该原稿并标部分交付。直接News、补查后News、直接Deep共用同一调用准备；Deep supplementary仍hold。新双语News只做了离线合同检查，本轮真实双语样本为Deep，不冒称News全链新验收。

## 测试证据

[COMPUTED][HIGH] 原prepare代码Git blob核对为9f8699e6a941dac89e30d2cfa8142874ef7fadc1；新默认测试在原实现下3失败（只返回中文），保留的hold/无审批/Deep补查负例3通过。修改后node --test tests/n8n/bilingual-delivery.test.cjs为20通过、0失败，收尾重跑相同。覆盖三类入口默认双语、原材料和历史授权保留、两语言各0/1/3正文图、错误Kit/标题/图注、逆序返回、第一项失败、缺项、重复和身份错配。仅这些合同测试，不是全仓CI或事实评分。

| 执行 | 内容 | 实际结果 |
|---|---|---|
| [KNOWN][HIGH] 684 → 686/687 | 第一版授权语言错配 | 中文Gate在模型前拒绝；英文合成正文和Kit仍完成，汇总partial。 |
| [KNOWN][HIGH] 688 → 690/691 | 中文Kit原生抛错 | 中文正文保留，Kit为null、待审；英文合成包完成，汇总partial。 |
| [KNOWN][HIGH] 692 → 694/695 | 两语言真实连续调用 | 两版原主笔、编辑、视觉、生图上传、Kit和Package连续返回；汇总completed，末端断言通过。 |

[KNOWN][HIGH] 前两组使用两枚可删除Code探针，真实经过Gate、Assembler、Package和Mother each/aggregate，但正文与英文Kit是合成值，零模型调用。探针删除、恢复原连接且原生diff为空后才运行692。692起止23:18:05.629–23:22:36.318 UTC，没有新研究、真实选稿邮件或发布调用。

[KNOWN][HIGH] 692复用固定提交deba0b5e的历史Deep候选548和初始写作材料557：6来源条目（含2个title_only）、6断言、3引语。两个writing_input相等、独立成文。测试选择明确synthetic；临时授权节点只把本次调用改为controlled_test/user_chat_authorization，保留历史记录，不能将其说成formal_hitl。

| 产物 | 中文694 | 英文695 |
|---|---|---|
| [COMPUTED][HIGH] 初稿字符 | 3414 | 4614 |
| [COMPUTED][HIGH] 编辑稿字符（移除精确插图块） | 2616 | 4009 |
| [COMPUTED][HIGH] 组装稿字符 | 2836 | 4316 |
| [KNOWN][HIGH] 图片请求/成功/失败 | 2/2/0 | 2/2/0 |
| [KNOWN][HIGH] 正文图 | 1 | 1 |
| [COMPUTED][HIGH] SEO标题/描述字符 | 31/71 | 48/158 |
| [COMPUTED][HIGH] Kit文案字符 | 551 | 1379 |

[KNOWN][HIGH] 本次中文H1为“从帮企业收钱到替企业选模型：Stripe 要进入 AI 的花钱环节”，英文H1为“Stripe’s OpenRouter deal brings it closer to where businesses spend on AI”。正文图注分别为“便宜、快捷和稳妥，未必走同一条路。”及“Different tasks can take different routes.”。各包取自己的标题/Kit/图注/Alt，文件名带语言后缀。两张正文图只是本篇选择，不是数量配额。

[KNOWN][HIGH] 两版封面均保留image_geometry_warning:COVER_IMG。生成图片由原GitHub链写入开发分支，保存代码时以图片后的HEAD643fa186cdc81d51ac0510cdd597e8ced7db2e93为父。没有匿名图片下载、像素解码或设备显示新验收；历史宽高来源仍为requested_size，不能当作实际测量。图床无需重换。

## 清理、交付与下一步

[KNOWN][HIGH] Writer起点fdd4fa39-c4c2-4afc-b865-9cf1a3878b8b；永久补丁37869387-3006-45fc-a938-b0e661a5b3c8；探针清理终点a89919a4-b110-4236-9398-ab716c965e0a，81节点、inactive、无activeVersion。永久补丁→清理版diff为空；初始→清理版只有Kit/Parser/Package三节点和Assembler→Kit一条连接。

[KNOWN][HIGH] Mother起点feae2b62-acfe-4d9f-9609-8ab2da7da8ba；永久补丁b68fd9c7-cef7-4aca-98af-430c1d37b8f1；测试版16514d59-c725-43f9-a3b7-a79dd886c657；八节点清理终点e419a94d-5f80-4f41-8dde-05e00dae4cb2，46节点。永久补丁→清理版diff为空；初始→清理版仅Prepare、Call、Aggregate三节点及上述三条接线变化。旧activeVersionId仍c94debcc-2fe0-438a-a3df-a1d699740c99。未发布、未合并main、未改凭据。

[KNOWN][HIGH] 会话交付ai-daily-bilingual-692.zip包含两篇原自动文章、两份对应Kit、提取元数据manifest和说明。Kit文件只加了本地化字段标题，未改其内容；正文没有人工改写。封面URL在manifest、正文图外链在文章；不是离线图片包，也不是原始执行全集导出。文章/Kit/私有payload/恢复令牌不提交公开仓库。

[COMPUTED][HIGH] 交付中文MD SHA256为3912e6b72b5c4d10d54055cdf07253211a8c3be8a8d935660edc2e67e1244039；英文为2a8a03b3ed456918afb00101a1ccef32338bc2d8f16e6a8b65ba4d213be78284。正文源链接检查：中文7处、3个不同网址；英文0处。计数均为JavaScript string.length口径，不是中文字/英文词数。该长度核对和hash不等于全文事实验收。

[INFERRED][HIGH] 下一步针对已有694/695稿件与Kit修正文来源、时间、归属与冗长，再做封面几何/实际显示及正式审批和发布验收。保持双语为默认合同，不回退为显式单语；不为单篇瑕疵重跑全链、新增评分器或额外常驻编辑循环。此次只有作者自审，没有独立第二审查者。

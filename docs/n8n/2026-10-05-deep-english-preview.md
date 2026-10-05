# Deep 英文：复用现有分支的受控技术验收

## 结果与范围

[KNOWN][HIGH] 2026-10-05，母执行681 → 原Writer integrated子执行683 → 母末端断言成功。永久业务代码、提示词、节点和连接零改动；现有英文主笔、一次编辑及共用视觉链已能处理deep_analysis。没有另建Deep分支，没有运行中文链、重新研究或正式发布。

[KNOWN][HIGH] 这不是出版质量通过。自动稿把公告当时的待交割状态写成现在时，结尾重复判断，来源集中在末尾而未放在对应事实附近。保留实际自动稿，不靠再抽主笔或生图掩盖这些缺陷；后续在原编辑与人工收尾处理。

## 基线与材料

[KNOWN][HIGH] 起始开发提交18446b1f9605d8fd949c5ca2ca2e8ea455df36a1；Writer nHxILnDVz541Cu5P版本fdd4fa39-c4c2-4afc-b865-9cf1a3878b8b，81节点、inactive、无activeVersion；Shared Dispatch qAfs9BDFbdBotgaB版本6125e9ed-2270-42c4-b601-8a245adb7455，未改。

[KNOWN][HIGH] 输入复用已保存的Deep候选548和初始写作材料557。通过固定提交18446b1的native-deep-cn-acceptance.nodes.json复用TEMP Deep Fixture代码，再读取固定提交92390c2的handoff.cjs和writer-news-557.cjs。6个来源条目中2个title_only不可用于断言；6条断言、3条引语及原上下文保留。没有使用中文成稿作为英文输入，也没有混入News补查材料。

[KNOWN][HIGH] 原fixture的synthetic_selection、controlled_deep_cn_replay等历史标记保留。当前英文调用另有controlled_test决定，绑定content/story/mode/title/reader promise/en-US，来源指向本次母执行。未改写历史审批，也不冒充真实邮件HITL。英文平台配置为linkedin_article；Deep补查继续hold。

## 原生执行

| 执行 | 验证 | 结果 |
|---|---|---|
| [KNOWN][HIGH] 678 → 680 | 英文工单配中文授权 | 原Writer Invocation Gate报target language mismatch，模型前停止。 |
| [KNOWN][HIGH] 681 → 683 | 正确英文授权，原写作与图文链 | 母末端passed=true，身份/材料/提案、英文正文及图注、来源网址、动态插图、组装文字均通过对应接口断言。 |

[KNOWN][HIGH] 母681运行22:53:09.115–22:54:57.867 UTC；子683运行22:53:09.579–22:54:57.508 UTC，parentExecutionId=681，终点V2 Article Assembler。原英文主笔和原英文编辑各调用一次，各自tool_calls=0。没有旧审核层、额外纠错模型、生产邮件、ledger或浏览器发布调用。

[COMPUTED][HIGH] 初稿5463字符，编辑稿4890字符，均按JavaScript string.length。正文前后均有3个不同来源URL，均属于可用输入来源；未采用第四份报道的独有内容，因此不是编辑丢掉第四条链接，也不需要强加四链接配额。原初稿保留，移除插图块后组装正文与编辑稿逐字符一致。input_judgment_preserved只证明输入提案未变，不是正文语义评分。

[KNOWN][HIGH] Planner本篇选择1封面＋1正文图，请求/成功/失败=2/2/0；封面独立返回，正文插图1张，alt和caption为英文。publication.state=NOT_PUBLISHED、url=null。该数量不是产品配额。

## 图片、局测与阅读边界

[KNOWN][HIGH] 两图仍由原GitHub上传链写入开发分支目录n8n/images/20261005/test_full-source-dossier-20261002-r2/。COVER_IMG-683.png的blob为9fd6722334b293e323d6ec7a3b612b3e6f204cfc，IMG_1-683.png为c612f52b4b88317e5ee29f7b63115b6e77e1d856。上传后分支HEAD为ad34b67183d07a907b298ff07b015cddab6fcfe0；保存本检查点时以该提交为父，不覆盖图片。

[KNOWN][HIGH] 唯一警告image_geometry_warning:COVER_IMG。宽高仍来自requested_size，不是实际解码；本轮未做匿名图片下载、像素或设备显示验收。会话附件deep-en-preview-683.md是原自动图文稿，非离线图片包或终审稿。其SHA256为69e93a4444f80ddcbaea684101e117ca88e929b961ea1f1002364dca1978763b。

[COMPUTED][HIGH] 本地运行node tests/n8n/native-deep-en-acceptance.test.cjs通过：三段Code语法；两种授权配置且不改原对象；0/1/3张正文图正例；组装改文、来源网址替换负例。它只验证可删除验收脚本的这些条件，不是生产代码全仓CI，也不是英文事实/文风评分。

[INFERRED][HIGH] 阅读自审确认文章围绕选定支出分配判断展开，但“The deal has not closed”和“The deal still awaits closing conditions”应收回公告当时；本轮没有取得今天交易状态的证据。后段重复与来源落点仍需编辑；路由及动机解释不得把有归属的公司说法扩为普遍默认行为或已查明动机。此为作者自审，没有第二名独立审查者；不把这些问题写成已经修复。

## 清理与后续

[KNOWN][HIGH] 九个TEMP Deep EN节点及其连接已全部删除。Mother xR7fM1ZhxlMTUy0L起点458e8a54-26e7-4eb9-a14b-903cc8085e4a，测试版db7b771b-4a3e-44be-a329-647e4f355e7f，清理版feae2b62-acfe-4d9f-9609-8ab2da7da8ba。原生起点→清理版diff全部为空，恢复46节点；activeVersionId仍为旧c94debcc-2fe0-438a-a3df-a1d699740c99。Writer最终回读仍为fdd4fa39，81节点、未发布。未改模型/凭据，未合并main。

[INFERRED][HIGH] 下一单元是母流程显式语言调度，再统一收尾封面几何、Social Kit/交付及人工终审；正式审批与发布另行验收。现有各模式/语言的受控接口证据不等于生产双语分发已经接通。保存的是可删除测试配置、一个离线自检和本检查点，不保存正文、凭据或原始执行全集。

# 图片资产到图文预览：检查点

## 结果与改动

[KNOWN][HIGH] 现有 V2 Article Assembler 已适配 writing_preview.v1，成功图片按配图编辑给定的完整段落位置插入，封面单独返回。支持零张、一张、多张正文图；失败、错位或不安全图片仅跳过自身，不丢文字，不重写正文。本轮没有调用写作模型、生图服务、上传或发布。

[KNOWN][HIGH] 原预览 article_markdown 与已有 draft_markdown 原样保留；新增 assembled_article 使用既有 assembled_article.v1，承载插图后的 article_markdown、独立 cover_image 和 body_images。assembly_status 为 completed 或 partial；跳过项在 assembly_skipped_images，警告只留元数据，不写入文章。原 publication.state 始终 NOT_PUBLISHED。

[INFERRED][HIGH] Ponytail 取舍：只修改既有组装器，无永久新增节点、模型或依赖。复用视觉校验器的普通段落规则，按原文位置倒序插入，避免字符串替换的 $& 展开和二次匹配。旧社交包仍使用旧合同，不为兼容它复制一套输出；保持隔离，后续单独适配。

## 实际验证

| 执行 | 结果 |
|---|---|
| 617 → 618 | 复读中断前的原生 RED；同一个零图输入由旧合同报错变为成功返回全文，封面为 null。 |
| 619 | 乱序的封面＋三张正文图，按原段落顺序插入三图；链接、加粗、$& 均保留，封面未混入正文，比例警告未消失。 |
| 620 | 封面失败、正文坏锚点和另一张失败，不影响最后一张插图；返回 partial 和完整原稿/编辑稿。 |
| 621 | 复用保存的 598 编辑稿、605 配图位置与 616 实际上传资产；原生组装返回一张正文图及独立封面，没有重新生成图片。 |
| 622 | 连续执行 Request Builder → 无请求分支 → Collector → Assembler；配图失败时返回纯文字预览，没有执行 HTTP 或模型节点。 |

[KNOWN][HIGH] 618–620 为合成组装样本；621 是已保存正文与已上传图片的衍生回放，不是重新执行 616，也不是选题到成稿全链。621 的输入本来没有 draft_markdown，因此不声称该次保存了未提供的初稿；两版文字保留由其他正负例验证。

[COMPUTED][HIGH] 新增本地七项检查先因实现文件缺失失败，随后 7/7 通过；旧节点实际故障另由 617 证明。最终相关接口集合 30/30，通过。检查零/一/多图、部分失败、完整唯一正文锚点、代码块、重复 ID、不安全 URL、转义、CRLF 与重复组装。不是全仓 CI 或独立 reviewer 验收。

```sh
node --test tests/n8n/article-assembler.test.cjs tests/n8n/image-assets.test.cjs tests/n8n/visual-requests.test.cjs
```

[COMPUTED][HIGH] 同输入和同代码的本地确定性导出：源正文 SHA256 为 ff2c21dd5d4eb5e4ba0314cf47d7fb816a29be4d848c8e2d1b90f37c12199c2f；插图正文为 5240daf0713022a494ddbfe0bb6762f843699a1c0916ba761eccc5ccb5080fbd。移除唯一插入块后与源正文逐字一致。已读取原生 621 正文核对插入位置与资产 URL；阅读页没有人工润色。

## 当前状态与恢复

[KNOWN][HIGH] 重试开始时发现上次已保存 f595e1c6-5117-4983-948a-2054e79ba364 和两枚临时测试节点，直接续接而非重做。稳定恢复点为 c9669757-3429-4ccb-b7fc-0a91fc66ed03；最终版本 1ba246e7-9922-4801-89f6-ca7970b7c06a，81 节点，未发布。两枚临时节点均已删除。

[KNOWN][HIGH] 相对稳定恢复点的原生差异：只修改 Article Assembler 参数；新增 Collector → Assembler；移除 Assembler → EN Social Kit。无永久增删节点，模型、凭据、母流程不变。Assembler 现在为视觉链终点，中文预览到视觉入口仍未接通。

[KNOWN][HIGH] 封面仍是 1536×1024 原图，目标 16:9 裁切未做；GEOMETRY_WARNING 原样保留。本轮通过网页和容器下载现有图片仍未取得字节，容器报域名解析失败，未声称完成图片目视验收。阅读页使用真实在线图片地址，不能离线显示图片。

## 保存与下一步

[KNOWN][HIGH] 分支 n8n-v3-handoff-20261003 保存 src/n8n/article-assembler.js、tests/n8n/article-assembler.test.cjs、本检查点及简明计划。使用已上传的隔离代码快照做本地检查；本轮未重新克隆全仓。实际正文、图片地址与回放输入仅放本地交付包，不把原始执行、旧 pin 数据或恢复令牌提交 GitHub。

[INFERRED][HIGH] 下一单元接通中文预览 → 配图入口 → 图文返回，并验证编辑失败时不误启动配图。封面裁切和图片目视检查仍列为未完成的格式/效果项；不因此增加审稿、评分或研究流程。不重写本轮已保存正文。

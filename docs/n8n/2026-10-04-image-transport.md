# 图片生成与上传：检查点

## 结果

[KNOWN][HIGH] 本轮完成“已准备请求 → 逐图生成 → 上传 → 资产返回”。原生执行 616 使用保存的 605 方案与 598 编辑稿，现有生成服务和上传服务实际返回两张图片：封面 1536×1024、正文图 1024×1024。两项请求均成功，正文与输入一致；没有重新写稿或重新规划配图，没有发布文章。

[KNOWN][HIGH] 封面为 3:2 原始画布，目标发布比例为 16:9，返回 GEOMETRY_WARNING；未裁切，不能声称已经符合封面规格。正文图为 1:1。当前环境无法下载这些返回链接的图片字节，未完成目视验收；本地图片查看页使用实际上传返回的在线 URL，不伪造本地图片或图片质量结论。

## 最小改动

[KNOWN][HIGH] 只新增一个原生 If：有请求才进入 Split，没有请求直接返回原预览。复用原 Split、Loop、HTTP 生成、二进制转换、上传、资产归一化与收集节点，不新增服务或模型、不改正文和配图提示词。

```text
V2 Image Request Builder → V2 Has Image Requests
  有请求 → Split Out1 → Loop Over Items1
                         → Generate an image → Image b64 to Binary → Upload to ImgBB
                         → V2 Image Asset Normalizer → 回到 Loop
             Loop 完成 → V2 Image Asset Collector
  无请求 ─────────────→ V2 Image Asset Collector
```

[KNOWN][HIGH] 生成、二进制转换、上传的原生错误出口均进入资产归一化，再回循环。每张资产从配对的 Split item 读取自己的请求，按 ID 收集。生成失败返回 FAILED 与空资产，不借用别张图；部分失败/全部失败仍返回文章。收集器为本轮终点，未接旧 Assembler。

[INFERRED][HIGH] Ponytail 取舍：不建新的任务队列、错误工作流或重试框架；一条原生空请求分流和三个原生错误出口足以支撑本轮需求。用小数组按 ID 匹配，暂不优化为额外索引层；没有截断编辑器决定的图片数量。

## 验证

| 执行 | 类型与结果 |
|---|---|
| 613 | 合成传输：封面＋三张正文图，真实 Split/Loop/转换/归一化/收集；模拟服务返回四项成功，身份、图注和锚点对应。 |
| 614 | 合成传输：封面生成失败、IMG_1 二进制缺失、IMG_2 上传失败；IMG_3 仍成功。返回 partial，4 请求/1 成功/3 失败，原稿和编辑稿保留。 |
| 615 | 合成空请求：0 请求、skipped，保留两版文字，不执行服务。 |
| 616 | 实际生成与实际上传：2 请求/2 成功/0 失败；封面比例警告保留，文章逐字保留。 |

[KNOWN][HIGH] 613–615 使用明确的测试服务节点，不是图片质量证据。616 改接原有真实 HTTP 节点，沿用已保存的方案，不重抽配图创意；旧测试许可字段原样保留，本次真实生成/上传许可另记在 image_io_test。616 回放源没有 draft_markdown，不能声称该次保存了未提供的初稿；两版文字保留由合成测试和本地回归验证。

[COMPUTED][HIGH] 新增 8 项接口检查先在实现文件缺失时失败，随后通过。最终重跑以下两份入口共 23/23，通过；其中 visual-requests 复用了 8 项规划测试，不重复计为新的检查。范围为本地图片接口，不代表全仓 CI、正式母流程或独立 reviewer 验收。

```sh
node --test tests/n8n/image-assets.test.cjs tests/n8n/visual-requests.test.cjs
```

## 保存与恢复

[KNOWN][HIGH] Writer 为 nHxILnDVz541Cu5P。起点 5ee90f61-ebbe-4562-8022-0a189b87007c；最终 c9669757-3429-4ccb-b7fc-0a91fc66ed03，81 节点，active=false、activeVersionId=null。五个临时节点均已删除，包含最初两个模拟服务节点及最后三个测试入口/断言节点。母流程、中文写作与编辑节点未改。

[KNOWN][HIGH] 最终原生 diff：新增一个 If；修改既有七个节点的参数或错误设置；新增九条连线，移除 Collector → Assembler 一条连线；未删除永久节点。生成 URL、上传配置与凭据没有修改。原有未接通的中文预览到配图入口仍未连接；本轮不等于中文图文主链全通。

[KNOWN][HIGH] 源码在 src/n8n/image-binary.js、image-asset-normalizer.js、image-asset-collector.js；测试在 tests/n8n/image-assets.test.cjs。同分支 n8n-v3-handoff-20261003 保存，不合并 main。完整图片请求、原文和资产 URL 只在本地交付材料；不提交原始执行记录、恢复令牌或凭据。完整仓库克隆受 DNS 故障影响，使用已有隔离快照与连接器，不声称已运行全仓测试。

## 下一步

[INFERRED][HIGH] 复用现有 Article Assembler，把成功正文图放到已选段落后，封面单独返回；零张、多张和单图失败都不丢稿、不再写文章。处理封面裁切与目视检查，然后连接中文预览入口。先用本次资产回放组装，不再次生成同一批图片，不新增质量评分器。

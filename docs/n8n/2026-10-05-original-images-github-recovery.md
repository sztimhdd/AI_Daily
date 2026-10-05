# 原文章图片恢复：GitHub 原图读取检查点

[KNOWN][HIGH] 2026-10-05，现有写作工作流 nHxILnDVz541Cu5P。仅恢复原文章配图交付，不接主链、不发布。

## 本轮结果

[KNOWN][HIGH] 执行 630 使用保存的 605 配图方案和 598 编辑稿，通过现有编译、生图、GitHub 上传、收集与组装，重新生成原方案的封面及正文图。没有调用 Writer、配图 Planner、社交文案或发布节点。一张正文图只是这篇文章的既有选择，不是产品配额。

[KNOWN][HIGH] 随后的无凭据 HTTP GET 实际读取两张新原图，均返回 200，PNG 头有效；头部尺寸分别为封面 1536×1024、正文 1024×1024。630 的组装结果使用下列新地址，封面独立，正文图位于原指定段落后。

- [KNOWN][HIGH] 封面：n8n/images/20261005/test_visual-native-598/COVER_IMG-630.png
- [KNOWN][HIGH] 正文：n8n/images/20261005/test_visual-native-598/IMG_1-630.png
- [KNOWN][HIGH] 图床地址前缀：https://raw.githubusercontent.com/sztimhdd/AI_Daily/n8n-v3-handoff-20261003/

[KNOWN][HIGH] 执行 631 只重读这两张图并尝试用原生 Edit Image 生成检查缩略图，没有重新生图。下载和 PNG 头检查再次成功；缩略图节点因服务器缺少 gm/convert 可执行程序而失败。没有安装依赖、增加转换服务或把缺失程序解释为图片损坏。

[KNOWN][HIGH] 因此验收边界是：上传和公开地址的服务器读取已通过；完整像素解码、人工目视和手机端显示仍未验收。不能再把 HTTP 200 或 PNG 头检查写成“用户已经能看到图片”。封面未裁切为 16:9。

## 交付与简化

[COMPUTED][HIGH] 本地沿用既有 HTML/Markdown，只替换两张旧图片地址，并在阅读页增加两个原图直达链接。正文 HTML 除图像地址外相同；Markdown 逆向替换地址后与旧稿逐字一致。保存的原编辑稿 SHA256：ff2c21dd5d4eb5e4ba0314cf47d7fb816a29be4d848c8e2d1b90f37c12199c2f。

[KNOWN][HIGH] 新阅读文件为 illustrated-preview-github-630.html、stripe-openrouter-github-preview.md；它们在线加载 GitHub 原图，不是离线内嵌图片。没有把历史新闻材料重新核验，也没有修改原文章叙述。

[INFERRED][HIGH] Ponytail 取舍：恢复原图并使用已存在的托管路径；不建并行工作流、不再生成白方块等无关测试图、不增加图片转换设施。一次原生缩略图尝试因缺运行依赖停止，不为此扩大改造。

## 最终工作流与下一步

[KNOWN][HIGH] 七枚临时节点全部删除。最终版本 8e919b8e-d6f7-408d-95ac-f797416d0bf4，81 节点，active=false、activeVersionId=null。对稳定基线 6219c4c4-07ca-4c28-8c33-461650764ec3 的原生 diff 为空；业务节点、连线、提示词、模型和凭据未改变。图床仍为 GitHub，开发资产仍在既有分支。

[KNOWN][HIGH] 本轮未重跑既有全套接口测试，不沿用旧 23/23、30/30 冒充本轮回归。执行 630 是原配图计划到新图片组装的连续运行，不是中文从初稿到图文的连续运行，更不是完整母流程。

[INFERRED][HIGH] 下一步先直接查看这两张原图及新版阅读页，确认实际显示，不再重新生成同批图片。然后仅接中文预览到现有视觉入口，验证编辑失败不启动配图。封面裁切后置；不增加核验文章、评分器或研究循环。

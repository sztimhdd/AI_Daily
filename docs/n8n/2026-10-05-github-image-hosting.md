# GitHub 图片托管切换检查点

## 结论

[KNOWN][HIGH] 旧 n8n 工作流 AI-Newsroom-v2 的图片链是：Generate an image → Image to Base 64 → GitHub Create a file → raw.githubusercontent.com URL → Markdown 合并。中文路径写入 `n8n/images/YYYYMMDD/`，英文路径写入 `n8n/images_en/YYYYMMDD/`。仓库化 AI Daily 后续产物也使用 `outputs/.../images/` 与 `raw.githubusercontent.com/sztimhdd/AI_Daily/main/...`。

[KNOWN][HIGH] 因此当前 V2 视觉链不再使用 ImgBB。旧 `Upload to ImgBB` 已删除，替换为原生 GitHub file/create 节点；现有 GitHub credential 可用。开发阶段写入分支 `n8n-v3-handoff-20261003`，不修改 main。

## 原生验证

- execution 626：1×1 PNG 探针通过 GitHub node 上传，返回 raw.githubusercontent.com URL；随后用 GitHub Contents API 回读，blob SHA 一致。
- execution 627：固定单封面计划走真实 Image Request Builder → Split/Loop → Generate an image → Image b64 to Binary → Upload Image to GitHub → V2 Image Asset Normalizer → Collector → Article Assembler。结果 1 requested / 1 succeeded / 0 failed；GitHub 返回文件大小 1,616,677 bytes，Normalizer 使用 raw download_url，Assembler 独立返回 cover_image。
- 两个探针文件已从开发分支删除；临时 n8n 测试节点也已删除。

## 当前草稿

Writer: `nHxILnDVz541Cu5P`
Version: `6219c4c4-07ca-4c28-8c33-461650764ec3`
Node count: 81
Active: false

相对切换前稳定版本 `1ba246e7-9922-4801-89f6-ca7970b7c06a` 的业务差异只有：
1. 删除 `Upload to ImgBB`。
2. 新增 `Upload Image to GitHub`。
3. `V2 Image Asset Normalizer` 改为读取 GitHub `content.download_url` 和 blob metadata。
4. 上传连线从 ImgBB 改到 GitHub。

[INFERRED][HIGH] Ponytail 取舍：复用旧流程已证明的 GitHub 图床模式，不维护第二套 ImgBB 路径，不新增存储抽象、镜像上传或 fallback 服务。正式发布前将分支参数切换为发布分支/main，并让最终 article package 使用 GitHub 返回的 raw URL。

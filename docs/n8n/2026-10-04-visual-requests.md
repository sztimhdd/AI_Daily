# 配图计划到生图请求：检查点

## 结果

[KNOWN][HIGH] 完成一个接口：已有配图计划 → 现有提示词编译器 → 现有图片请求构造器。没有生成图片、调用模型、上传或发布；中文写稿提示词与配图编辑提示词未修改。

[KNOWN][HIGH] 输入沿用 `writing_preview.v1.visual_plan`。编译结果放入 `compiled_visual_plan`，仍使用 `visual_prompt_compiled.v1`；最终返回同一预览及 `image_requests` 数组，单个请求仍为 `image_request.v1`。正文图零张、一张或多张均完整保留，封面单独算；原文、原稿、语言和文章身份不改。

[INFERRED][HIGH] Ruling：请求先留在一个预览内，到生图 I/O 入口才拆分。这样失败或无请求时仍能返回文章，不为保稿新增分支节点。既有 `Split Out1` 保留但暂时断开。

## 验证

| 执行 | 结果 |
|---|---|
| 607 | 旧编译器面对现有预览输入报错：expected visual_plan_validated.v1, got writing_preview.v1。原生 RED。 |
| 608 | 与 607 相同输入修复后通过：封面＋0 张正文图，得到 1 条请求。 |
| 612 | 封面＋1 张正文图，得到 2 条请求。 |
| 609 | 封面＋3 张正文图，得到 4 条请求，IMG_3 未被截断。 |
| 610 | 上游配图计划失败，返回 0 请求、skipped；两版文字保留。 |
| 611 | 未安装的风格名称导致编译失败；请求跳过，两版文字保留。 |

[KNOWN][HIGH] 608–612 在真实代码节点中运行，不经过模型、HTTP、生图或上传节点；末端测试断言检查原文/原稿/身份、请求数量、场景/图注/锚点及尺寸。原生样本是合成接口输入，不冒充成稿或实际图片。

[COMPUTED][HIGH] 本地最终 `node --test tests/n8n/visual-requests.test.cjs`：15/15 通过（复用 8 项配图测试＋7 项本轮测试）。写代码前新增检查因文件缺失失败；真实旧逻辑故障另由 607 复现，不混称本地旧实现回归。不是全仓 CI，也未做独立 reviewer 验收。

[COMPUTED][HIGH] 保存的 605 计划和完整 598 编辑稿在本地经现有校验器、新编译器和请求构造器回放：得到 COVER_IMG 与 IMG_1 两条请求，文章逐字不变。此次真实素材回放是本地代码运行，不是新的模型创作，也不是原生 605 重跑。完整请求留在本地交付包。

## 保存与恢复

[KNOWN][HIGH] Writer `nHxILnDVz541Cu5P`：起点 `48bf6aef-5cee-491d-8b56-35a9fea02168`，最终 `5ee90f61-ebbe-4562-8022-0a189b87007c`，80 节点，未发布。原生 diff 仅修改两个现有 Code 节点和五条连线；无永久新增/删除节点。三个临时测试节点全部删除，母流程不动。

[KNOWN][HIGH] 当前连线：`V2 Visual Input → V2 Visual Planner → V2 Visual Plan Validator → V2 Visual Prompt Compiler → V2 Image Request Builder`，请求构造器为终点。配图入口仍未接中文主链。

[KNOWN][HIGH] 同分支 `n8n-v3-handoff-20261003` 保存 `src/n8n/visual-prompt-compiler.js`、`src/n8n/image-request-builder.js`、`tests/n8n/visual-requests.test.cjs`。三个文件的远端 blob 哈希均与本地一致；恢复可用原生版本历史。完整仓库克隆仍因 DNS 失败，本地只运行本接口及复用的配图检查。

## 下一步

[INFERRED][HIGH] 复用现有 Split/Loop/生图/上传链：Split 改为拆 `image_requests`，资产归一化改从拆分后的同一请求取配对元数据，不能继续把批量 Request Builder 输出当单图。先验证逐图成功/失败保稿与动态收集，再运行已保存的真实计划；不重抽文章或配图创意。

[KNOWN][HIGH] Collector、Assembler、Package 的旧固定数量和必需封面假设尚未修复；几何裁切也未验证。请求 prepared 不代表图片生成成功，不代表完整图文流程跑通。

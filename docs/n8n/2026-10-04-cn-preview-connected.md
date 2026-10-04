# 中文预览连接检查点

## 结果

[KNOWN][HIGH] 本轮精简计划后，完成一个接口：中文初稿 → 现有中文编辑 → 预览。原生测试父执行 597 调用子执行 598，一次连续返回初稿与编辑稿；不是把两次孤立执行拼成成功。仍是受控测试，不是正式选题/审批母流程或发布验收。

[KNOWN][HIGH] 没有新增模型或评审层，也没改写作/编辑提示词。只增加 `V2 CN Edit Input`（绑定原稿和读者配置）、`V2 CN Preview`（返回两版正文，失败保留原稿），连接现有编辑器，并设置原生错误继续输出。图片链及动态配图要求未修改。

## 原生验证

| 执行 | 实际结果 |
|---|---|
| 595 → 596 | 通过原生 Execute Sub-workflow 调用原 Writer 入口；原 Mapper 使用本次合成输入，Gate 因缺少调用决定拒绝，没有写稿。 |
| 597 → 598 | 历史 557 的完整写作材料，经原 Mapper/Gate/Switch → 真实 CN Writer → 字段绑定 → 真实 CN Editor → Preview。父节点实际收到 `writing_preview.v1`，`status=draft`，保留 `draft_markdown` 与 `article_markdown`，发布状态 `NOT_PUBLISHED`。 |
| 599 | 故障测试清空传给编辑器的正文，预期表达式报错，但实际调用了编辑模型并返回仅标题的“原稿未提供”。旧预览错误地将其标为完成；记录为失败，不隐瞒真实模型调用。 |
| 600 | 直接重放 599 的同一标题型响应，不调用编辑模型。增加非空正文判断后，预览返回 `review_required`、原稿原样保留；通过。 |

[KNOWN][HIGH] 598 使用既有 `cn-writer-native.test.cjs --native-payload` 的材料：8 来源、10 断言、5 引语、3 条选中引语、6 个段落任务。测试传输省去重复的 selected_quotations，由临时输入节点按已有 ref/source_url 重建；未改变材料或制造正式审批。本次调用决定明确为当前用户批准的 controlled_test，历史 false 保留。

[KNOWN][HIGH] 原 Mapper 没有复制或放宽。原生子执行为 `integrated`，596/598 使用当前输入，避开了直接画布 manual 的旧 pin 替换问题。没有执行持久 unpin，不能说保存的 pin 已清除；画布直接手测仍待单独确认。采用实际生产形态的子调用作为后续集成测试入口，不再为清 pin 停滞。

[COMPUTED][HIGH] 本地接口集合最终 80/80 通过。新增 5 项测试先在缺少实现时失败；599 暴露的仅标题问题另补到同一用例，观察到 4/5 → 修复后 5/5。结构检查不是文章审美或事实评分器。

## 阅读结果与边界

[INFERRED][HIGH] 598 编辑稿把应用里的价格/速度选择提到开头，长引语改为连续中文叙述，已形成可读预览。仍有局部重复、路由概括和功能归属可编辑，放在正常同稿修订，不重启研究或整篇抽样。正文完整不等于新闻发布批准。

[KNOWN][HIGH] 交付的 `preview-native-598.md` 保留该次模型正文，没有人工收尾；它是历史材料测试稿，不是当日新闻核验。父返回中的原稿同时保留在执行记录。真实读者偏好以用户审阅为准，未声称完读率提升。

## 保存与恢复

[KNOWN][HIGH] Writer 起点 `da60ed9b-e40c-4185-b65d-65c4bff75e4c`，最终 `9a469034-7a66-4551-aa0a-7e538bbf6078`，79 节点，未发布。最终 diff：新增两个 Code 节点、三条连线、编辑器 `onError=continueRegularOutput` 与 `alwaysOutputData=true`；没有提示词/模型/凭据变化。

[KNOWN][HIGH] 临时父测试借用 Shared Dispatch 的 Stage Input，原 From Parent 和业务代码不动。两个临时父节点及一个子故障节点均已删除。Shared 最终 `478fb3fc-4b3c-4cc9-a1d2-ca85674193f8` 与起点 `fb841db9-b24c-4e05-9bbc-5a373b82bdf1` 的节点/连线 diff 全空，恢复为 7 节点、未发布。真实 Long-Content-Writing 母流程未修改。

[KNOWN][HIGH] 代码存 `src/n8n/cn-edit-input.js`、`src/n8n/cn-preview.js`，测试存 `tests/n8n/cn-preview.test.cjs`。计划更新同一分支，不合并 main。原稿、模型输出及私有日志不提交公开仓库。

```sh
node --test tests/n8n/*.test.cjs
node tests/n8n/cn-writer-native.test.cjs --native-payload '<fresh permission reference>'
```

[KNOWN][HIGH] 第二条只构造测试输入，不执行网络请求；原生执行前需重新读取草稿、连接和用户批准。测试工具在 599 没有实现预期的模型隔离，今后不要只相信 mock 模式名称；检查实际节点运行，并在不需要模型的失败回放中物理避开模型。

[KNOWN][HIGH] Git clone 仍因 DNS 失败；本地使用挂载源快照及远端回读的新文件，仅运行 n8n 接口集合，未声称全仓 CI 或独立 reviewer 通过。没有生产发布、邮件、写表或图像生成。

## 下一步

[INFERRED][HIGH] 进入配图编辑接口：读取完成编辑的草稿，决定正文图数量/类型/位置；检查原 parser、ID、循环、collector、assembler 的固定数量假设，按零张/一张/多张测试。沿用既有视觉编辑，不新增评分体系。

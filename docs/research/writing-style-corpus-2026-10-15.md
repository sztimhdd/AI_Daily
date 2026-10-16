# 中英文写法参考大 JSON

日期：2026-10-15。

主文件：[writing-style-corpus-2026-10-15.json](writing-style-corpus-2026-10-15.json)

压缩参考版：[writing-style-corpus-2026-10-15.compact.json](writing-style-corpus-2026-10-15.compact.json)。124,499 字节，约为完整版的 9.995%；保留605项简写参考、174组前后对照、94条贴题句段及来源许可。它删去重复元数据、长来源正文与位置清单，并筛掉需要补事实的示例，属于内容取舍。

同一911原稿上的一次完整 Humanizer 比较中，压缩版比全量版稍顺，但未解决整篇核查腔。保留为后续写法参考，不把整包注入线上，不新增编辑 Agent。实验和发布决定见[改进汇总](../operations/2026-10-15-editorial-release.md)。

已合并10个 GitHub 来源、607项来源规则/词句/候选项，以及195组正向候选对照（中文127组，英文68组）。来源规则之间允许重叠，以保留各自语境和出处，不把这些数量当作独立规则数。

本 session 扫描120个保存文件，内容去重后为75份；归并300条实际句段，保留759个出现位置。另收录9条用户明确指出的表达和4项旧提示词风险记录。扫描清单内每处引用均已对回原文件。

## JSON 内容

- `sources`：来源、许可、缓存文件摘要。
- `patterns`：来源规则与原始语境、短语或模式。统计类条目只作资料记录。
- `whitelist_candidates`：before/preferred 对照、语言、出处、例子粒度与注意事项。
- `user_flagged_expressions`：用户在本 session 明确批评的表达。
- `session_observations`：实际稿件及 Narrative 的候选问题句段，带文件行号或 JSON 字段。
- `session_files`：扫描范围；相同句段归并后保留各出现位置。
- `prompt_risks`：旧提示词中值得讨论的引导，不把假设写成已证实原因。

## 来源

1. [ai-writing-markers](https://github.com/humzakt/ai-writing-markers/blob/main/markers.json)：现成英文 JSON，87项。
2. [Humanizer](https://github.com/blader/humanizer/blob/main/SKILL.md)：26类及前后示例。
3. [Humanizer Chinese](https://github.com/jiji262/humanizer-chinese/blob/main/SKILL.md)：36类中文模式。
4. [Stop Slop](https://github.com/hardikpandya/stop-slop)：英文短语、结构和例子。
5. [Stop Slop CN](https://github.com/Gawg-AI/stop-slop-cn)：中文短语与替换方向。
6. [Stop Slop ZH](https://github.com/pencil20388-eng/stop-slop-zh)：中文表达列表。
7. [De AI Taste](https://github.com/ruodou233/de-ai-taste/blob/main/references/ai-taste-signals.md)：带语境说明的中文信号库。
8. [中文去 AI 味套件](https://github.com/evelynyaxueke/anti-ai-writing-kit-zh)：相关条目及示例。
9. [Chinese Humanizer](https://github.com/non-convex/chinese-humanizer)：独立概括，不转载长例文。
10. [Renwei Writing](https://github.com/orange2ai/renwei-writing)：独立概括，不转载其完整文本。

## 怎么用

这是资料全集，按当前语言和问题选择少量贴题对照，不建议把整个文件当成每篇文章都必须兑现的指令。来源说某词必须禁用，不等于本项目已采纳。实际出现过的句式，也不等于该次出现一定写坏。

所有好写法均保留为候选或外部参考，尚无逐条用户批准。约10组示例被额外标记：有的来源改后句新增了原句没有的数字、收益或命题，有的需要当篇材料补足语境，不能当成可盲换的白名单。其他条目也未被独立验证语义等价。例子只借写法，不继承人物、数字、经历或事实。

最初整理仅检索、归并和校验 JSON，没有调用生成模型。随后已完成上文说明的同题本地比较；原始实验产物继续保存在 ignored `.local/`。语料本身没有增加运行时、扫描器、Agent 或 n8n 节点，也没有被整包接入线上。部署与通信状态以[改进汇总](../operations/2026-10-15-editorial-release.md)为准。

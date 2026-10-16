# AI 写作文风：社区方法、Humanizer 与实际作品

日期：2026-10-15。围绕 AI Daily 的“核查报告腔、元叙事、反复纠正读者”的实际问题查公开资料。本轮只读，不安装技能、不运行生成模型、不改 n8n、不发布或发邮件。

## 最重要的发现

值得下一步借用的是具体改写示范、作者样本和完整编辑动作。继续把“自然、直接、像人写”改写成另一份原则说明，价值不大。

需要纠正我们此前对 Humanizer 的表述：10月11日整合草案明确只摘取若干原则，10月13日研究也读过原项目；最近单独文风编辑仍是我们自行写的提示词。它们都不能等同于完整原版 Humanizer 在911成稿上的验证失败。

公开作品也提醒：人味不由改动数量、禁词覆盖率或 Agent 数量决定。一个本来有作者声音的段落，少改可能更好；一个本来像报告的 AI 草稿，少改则可能原样保留问题。

## 读了哪些实际内容

| 项目／来源 | 实际阅读 | 直接有用的做法 | 对 AI Daily 的局限 |
| --- | --- | --- | --- |
| [blader/humanizer](https://github.com/blader/humanizer) | 当前 SKILL 的流程、声音指导及相关模式；README 完整 Lisbon 前后例 | 找出具体问题后重写，再复查；支持作者样本；可调整结构 | 项目示例，不是中文新闻受控实验；个别缺口示例仍会保留“资料未记载”的说法 |
| [jiji262/humanizer-chinese](https://github.com/jiji262/humanizer-chinese/blob/main/SKILL.md) | 任务、语体、样本校准、讲义腔、二分句、过度对冲、编辑流程及成对例句 | 中文坏段与好段的具体差别；区别新闻和个人观点文章；完整流程可嵌入现有编辑环节 | 规则较长，部分做法不适合直接全部搬进我们的提示词；没有读到独立的中文新闻质量验证 |
| [non-convex/chinese-humanizer](https://github.com/non-convex/chinese-humanizer/blob/main/references/examples.md) | SKILL 与全部五组写法示例 | 用具体过程替代抽象标签，直接回答问题，减少预设读者误解 | SKILL 同时有要求说明信息缺口的文字；整份照收可能重现核查腔 |
| [orange2ai/renwei-writing](https://github.com/orange2ai/renwei-writing/blob/main/references/case-study.md) | 完整 SKILL、原稿—失败稿—作者接受稿 | 保住作者原有声音，检查改写有没有用文案技巧替换作者表达 | 擅长保护真人草稿；不能凭空给 AI 稿造出作者经验 |
| [gvzdv/claudish-to-english](https://github.com/gvzdv/claudish-to-english) | README 中工作方式与提示词配置；rewrite.sh 和 md-core.sh 的实际 prompt | 独立简化语言、保留事实和技术标识 | 是助手回复/文档简化原型；默认 Markdown prompt 保留结构，与我们要改报告结构的目标有冲突，未找到完整中文新闻前后作品 |
| [anti-ai-writing-kit-zh](https://github.com/evelynyaxueke/anti-ai-writing-kit-zh) | SKILL 的相关章节、完整报告的方法和限制；抽读8份完整输出 | 提供公开的同题、同模型不同条件作品，可直接读原文 | 指标测写作模式覆盖，并非人类读感或事实质量；其部分任务明确要求交代能证明与不能证明什么 |

## 1. Humanizer 与我们刚才的文风编辑有什么不同

原版 [SKILL](https://github.com/blader/humanizer/blob/main/SKILL.md)把识别、草稿、复查与最终改写写成完整操作，并有对应例句。它还让作者样本优先于默认风格规则；嵌入其他任务时可以只交付最终正文。

Lisbon 的完整[前后例](https://github.com/blader/humanizer#full-example)保留旅程、地点、喜好和下次安排，删去导游式赞美与重复拔高。我的读感是 After 更具体、语气更像一个有偏好的人。它仍是项目作者提供的编辑示例，不能宣称原版在我们模型上必然有效。

我们最近的提示词只有改写目标与权限，没有这些成对示范，也没有明确要求先找出一版里仍然存在的具体问题再出终稿。因此“最近新增文风 Agent 几乎没改”，只能否定那份自写提示词，不能替代对完整技能的试验。

原版也不是天然与我们的要求完全一致。其知识缺口示例允许保留材料未记载的陈述；这是事实写作中可能合理的选择，但不是我们希望整篇反复承担的任务。应通过实际稿件判断，不再把项目名当效果证明。

## 2. 中文例子比抽象的文风要求更容易借用

[non-convex 的例子](https://github.com/non-convex/chinese-humanizer/blob/main/references/examples.md)展示了不同领域的改法：先讲一个过程，再引出概念；把一串抽象名词还原为动作和结果；回答技术选择时直接说明适用情况，不先虚构一个读者误解。

这类示范与我们文章里的“先分清”“真正的价值”“这里需要区分”问题更接近。它们展示段落怎样增加理解，而不只是告诉模型“不要像报告”。但其 SKILL 的不确定性处理与防御性写作条目有拉扯，不能因示例好读就认定全文可原样替换。

[jiji262 的中文版本](https://github.com/jiji262/humanizer-chinese/blob/main/SKILL.md)也强调保留信息、允许改变形状，以及按语体处理作者声音。这里最可取的是实际改写动作和例子，不是36条规则的数量。

## 3. 真人样本的作用：提供目标，而不只是提供禁区

Humanizer 和中文移植版都支持样本校准。[Zach H. 的公开文章](https://blog.zhade.dev/posts/2025-03-04-writing-in-the-age-of-ai/)展示了他的提纲、人工起稿和两次 Claude 编辑提示，并说明个人风格指南来自过去文章。

这支持把真实作品作为参照的做法，但没有展示同文对照，且他的主要文字仍由本人写。不能用它证明一套风格指南足以让自动 Writer 产生同样的声音。

Reddit 的[个人声音讨论](https://www.reddit.com/r/ClaudeAI/comments/1sds3gj/modifying_bladerhumanizer_to_mimic_personal/)则是反例：发帖者已经提供过作品，却仍觉得生成结果只有结构像自己。没有看到解决后作品。因此“给样本”值得验证，不是现成保证。

对我们：下一次需要一个具体的好读目标时，应使用已有、认可的真人段落，借节奏、解释方式与判断表达，不借旧文章事实。不要继续从空泛的“普通 AI 爱好者”推导一套假定的作者声线。

## 4. 有作品的中文项目，也可能与我们的目标相反

[中文去 AI 味套件的报告](https://github.com/evelynyaxueke/anti-ai-writing-kit-zh/blob/main/reports/2026-07-20-chinese-anti-ai-writing-skills-comparison-report.md)公开256篇输出。方法声明使用单一生成/评价模型，没有独立人类评审；指标不测实用性、事实质量或读者偏好。

本轮抽读了三个任务的八份完整输出：第一阶段 P1 的无技能/套件/renwei，第一阶段 P2 的无技能/套件/renwei，第二阶段 P8 的无技能/套件。

- P1 的套件版本删掉了无技能稿中替读者总结哪些改善不能成立的段落，直接结束在团队的后续决定。这是有意义的表达差异。
- P2 的图书馆报道中，套件稿仍频繁交代计数口径、数据缺口和不能归因，读起来仍接近我们不想要的报告。原任务本就要求说明数据能证明与不能证明什么，所以不能把这种文风单独归罪于技能。
- P8 的大学 AI 作业政策观点稿有明确主张和具体依据，却仍大量穿插无法归因、不能证明的说明。它可以是合适的政策评论，但不是普通 AI 兴趣长文的现成范本。

因此，我不建议照着这份指标榜选择技能，也不建议给 AI Daily 加载其整套扫描器、回执与规则维护流程。报告最有用的部分是可以读到文章，而不是排名。

## 5. 少改什么时候是对的，什么时候没用

[Renwei 的完整案例](https://github.com/orange2ai/renwei-writing/blob/main/references/case-study.md)公开真人原稿、三轮打磨后的失败稿，以及作者最终接受的版本。失败稿增加文案化修辞、对仗与原稿没有的频率数据；接受稿只改少量绊嘴处，保留原有语气。

这个案例直观说明为什么“更具体、更有画面、更有节奏”也会改坏文章：改写可能制造的是编辑的画面与技巧，而不是作者的表达。

但它的原稿本来就有明确的人在说话。我们上一轮输入是仍然像报告的 AI 稿，少改不能因此算成功。不能拿这个案例反过来给那次几乎无变化的文风编辑作辩护。

## 社区补充与未采用的路线

只读社区调研还找到个人博客里的两次编辑、讨论中的局部编辑示例、以及多轮 AI 改稿反而受读者批评的 HN 个案。它们主要是作者自述或读者评论，不是受控验证。

- [OpenAI 社区编辑协作示例](https://community.openai.com/t/maximizing-your-collaboration-with-chatgpt-tips-and-tricks-for-working-with-your-new-writing-partner/28565)：任务具体、保留原有叙事、指出需要改的段落。
- [HN 原稿与 AI 改写的争论](https://news.ycombinator.com/item?id=45593450)：委派读取报告了原文、提示词与读者反馈线索；父任务二次获取遇到429，未重新阅读全文，不作为本报告最强证据。
- [三层重写经验](https://www.tomsguide.com/ai/i-use-the-3-layer-rewrite-prompt-to-turn-messy-notes-into-fully-developed-ideas-heres-how-it-works)：作者展示组织、澄清与质疑的提示，但最后一层刻意找漏洞与缺证据，不适合再原样塞入我们的文风编辑。

本轮没有找到一份可直接声称已在中文 AI 新闻长文上稳定解决核查腔的公开作品集合。社区的具体示范和原稿可用；万能提示、检测器低分和“很多人说有效”不够支持替换流程。

## 建议的下一步

先保持选定 Narrative、Pro Writer 与上游产物固定。不要再写一份抽象的文风编辑总结，优先把完整原版 Humanizer 用在同一现成稿上做一次本地比较，按 embedded 方式只交付终稿。先看它是否真的重写了问题段落、是否好读、是否保住判断和事实。

这不是新增永久 Agent；可以替换刚才临时文风试验的提示词。若进一步验证声音参照，则另用已有认可段落作样本，不与首轮原版技能验证同时改变输入。原版不奏效，再考虑中文版本，避免又把多个改动混成一次测试。

本轮仅提出这个验证方向，没有执行新模型调用，没有安装技能或更改任何运行配置。

## 阅读记录

公开原文、代码和抽取样本缓存于 `.local/style-web-research-20261015/`。Humanizer 当前文件标记版本3.1.0，与此前研究所记版本相同，本轮没有发现一个可宣称“升级后必然修复”的新版。

缓存的主要文件：humanizer-skill.md、humanizer-readme.md、jiji-skill.md、chinese-humanizer-skill.md、chinese-examples.md、renwei-skill.md、renwei-case-study.md、claudish-md-core.sh、claudish-rewrite.sh、anti-kit-report.md。未执行任何下载项目的代码。

此前本地整合依据：`.local/humanizer-integration-20261011/proposal.md`；此前系统调研：`docs/research/github-writing-projects-review-2026-10-13.md`。这些用于对照已做过的工作，不冒充社区的新证据。

# AI Daily anti-slop 写作参考

日期：2026-10-11。用途：为现有 Writer 与 Light Editor 提供少量可选写作参考，不建立审核、评分或检测机制。

## 检索与范围

本轮完成两条检索路径：Web 搜索使用 `site:github.com` 查询 prompt writing、humanize AI text、style guide、skill、anti-slop；GitHub 原生仓库搜索使用 `anti-slop writing`，命中 `adenaufal/anti-slop-writing`、`jalaalrd/anti-ai-slop-writing`、`ehmo/slopkit` 等。研究者通过 GitHub 文件读取核验了核心来源前三项，并读取了新增的 `jalaalrd/anti-ai-slop-writing` 文件；其余依据为本轮主控接受的来源摘要。

新增库 [jalaalrd/anti-ai-slop-writing](https://github.com/jalaalrd/anti-ai-slop-writing/blob/main/skills/anti-ai-slop-writing/SKILL.md)（blob SHA `3e7ee575681b3faac38b2260aeab7cc60a269450`）把三项并列、被动句、标题和破折号列为硬禁，并包含未核验的 AI 检测断言。它不进入核心参考，也不安装；这些硬规则可能损害体裁、作者声音和正常表达。

## 参考来源

| 来源 | 可借鉴做法 | 适用模块 | 限制 |
|---|---|---|---|
| [Humanizer：SKILL.md](https://github.com/blader/humanizer/blob/main/SKILL.md) | Voice 与 “Not X but Y” 相关建议；保留有信息的对比和合适的观点反应，作者样稿优先。 | Light Editor | 原英文词表不能直接当中文禁词；不是成效证明。 |
| [Stop Slop ZH：SKILL.md](https://github.com/wdkang123/stop-slop-zh/blob/main/SKILL.md) | Core Behavior / Process：保留作者声音、体裁、事实边界、不确定性和有效细节；按体裁决定删、留、改，只动确有问题处。 | 中文 Writer、Light Editor | 按具体文本判断，不把建议变成机械规则；不是成效证明。 |
| [Anti-Slop Writing：English SKILL.md](https://github.com/adenaufal/anti-slop-writing/blob/main/english/SKILL.md) | Structural Rules：问句、命令句和片段句可按表达目的与体裁使用。 | 英文 Writer、Light Editor | 编辑提示不能损害格式和声音；不是成效证明。 |
| [Stop Slop：SKILL.md](https://github.com/hardikpandya/stop-slop/blob/main/SKILL.md) | 借鉴直接、具体和减少重复的方向。 | Light Editor | 不采用全禁对比、被动语态、破折号等硬规则；源码是方法建议，不是效果证据。 |
| [George Orwell, “Politics and the English Language”](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-works/politics-and-the-english-language/) | 让表达服务意义，清除陈词滥调和无效重复；必要时可打破规则。 | Writer、Light Editor | 写作随笔，不是 AI 实验或测评。 |
| [清华大学：胡鞍钢写作建议](https://www.sppm.tsinghua.edu.cn/info/1063/8264.htm) | 考虑读者和发布平台，表达有观点、有内容、有分寸。 | 中文 Writer、Light Editor | 借面向普通读者的原则，不移植深入研究门槛。 |
| [OpenAI：Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) | 指令清楚，必要时用示例；承认模型表现具有非确定性。 | Writer、Light Editor | 只借保留什么、修改什么的短指令思路，不照搬评测框架，也不视为效果证明。 |

以上做法均为参考归纳，不是来源作者的逐字引文，也不证明能稳定改善文章。中文词语选择、保留修辞与删改幅度，应结合当前稿件和体裁决定。

## 候选短 prompt

以下为 AI Daily 根据上述来源与产品取舍**综合拟定**，不是任何来源作者原话；尚未测试：

> 把这篇文章改得更好读，像作者在向感兴趣的人讲一件事。合并重复论述，删掉编辑自述和空泛训话；必要限定跟着事实说清一次。保留有用细节、判断和自然修辞，不添加材料没有的内容。讲完就停，不另造总结金句。只返回完整 Markdown。

## 待执行的开发步骤

最多三步，均待执行；本轮不运行新增测试、不改 workflow：

1. **先定位重复或编辑腔首次出现处。** 定向检查现有 Narrative→Writer→Light 的实际输入与指令，从重复口号或编辑腔首次出现的地方修改现有提示词。Sol 单次改表达后仍重复，既有两轮 Light 也未根治，因此不默认反复运行 Light。检查只读已有材料，不重跑研究、不加节点。若上游要求复述或保留套话，先删该指令；只有问题确在轻编辑时才试上面的 Light 候选。保留作者声音、有效细节和自然修辞。
2. **定位后一次只改一个字段。** 固定模型、effort 和材料，每次只改一个节点的所测字段，局部 before/after 阅读实际句段；不要同时改 Narrative、Writer、Light。a16z 是开发样稿，不是独立验证；另一个题材以后作为留出稿，不向待测模型提供标准答案。本轮不执行新增测试。两次新尝试仍失败就停止该分支、重新检查原因，不靠换模型重置失败计数。
3. **按实际输出问题处理图注或 Kit。** 图注和 Kit 不经过 Light；只在实际看到空泛或重复时，分别调整现有提示词一句，不增加总体终审节点。

## 本轮已知实验记录

同一原稿输入 SHA-256 为 `b0162b65a9abdec4de956de9db4860abe37b04c47b7b644a9e1983798a828b80`，4175 字符。短 prompt 使用 `gpt-6.1-sol`、`low` 运行 CLI 一次，输出 4898 字符，退出码 0，最终消息与 `edited.md` 一致，观察到 0 条工具事件。该运行不是严格的模型单变量 A/B，也没有做事实核验；请求与账本的 shared ID 不同，运行 cwd 位于仓库 `.local` 内，不能排除祖先指令影响。

主控读稿反馈：开头“每月花 903 美元用 AI，听起来像是把能买的聊天会员都买了一遍”以及工具的具体解释读起来更自然；“付费不等于回报”的观点仍有重复，结尾“这篇没有替那些用户算回报”仍属编辑自述，问题未解决。原稿和模型产物保存在 `.local`，本文不复述全文。此反馈是单次读稿观察，不是评分或通过结论。

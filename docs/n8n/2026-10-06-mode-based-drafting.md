# D — 母流程内的两种模式 Writer 与双语初稿

## 范围与结论

[KNOWN][HIGH] 2026-10-06，用户批准继续并要求每回合只完成一个大环节后停下。本轮仅实现D：原始材料上下文 → News Writer或Deep Writer → 中英初稿。未推进轻编辑、配图、Kit、真实邮件或发布。

[KNOWN][HIGH] 执行747/748验证错误与空中文结果不丢英文兄弟稿；749真实News双语、750真实Deep双语均到达初稿汇总及临时断言，返回passed=true。结构通过不等于文稿达到出版质量。

## 最小业务图

```text
Attach Targeted Browser Sources
  -> Draft Languages (zh-CN, en-US)
  -> Draft Language Loop (batchSize=1)
       -> Writer Mode
            news          -> News Writer
            deep_analysis -> Deep Writer
       -> Capture Mode Draft
       -> loop
  -> Aggregate Drafts (terminal)
```

[KNOWN][HIGH] Mother xR7fM1ZhxlMTUy0L复用原Prepare Writer Invocation并改名Draft Languages，复用Aggregate Drafts；移除Call Universal Draft Writing V2和Drafting Phase两枚旧子调用。新增必要的loop/switch、两个模式Agent、共享模型节点及响应捕获，共六节点，母画布49→53。未搬入旧81节点Writer，没有另建工作流或四个语言Writer。其余旧孤立节点留到F清理；节点总数不是核心流程复杂度指标。

[KNOWN][HIGH] 语言只选择表达/平台和沿用的模型：中文deepseek/deepseek-flash，英文gpt-6-luna，使用已有OpenCodex Hermes Local V2凭据。动态模型节点逐次只接收一个语言item；没有故障自动更换模型/供应商。配置显式maxRetries=0，作者节点保留最多两次原生尝试，timeout=120000ms，避免内外层重试叠加。

[KNOWN][HIGH] D直接读取现有materials中的retrieval.raw_content，不生成新简报、逐claim结构或授权回执。原materials、补查状态、来源链接、图片候选、human_instructions、story_direction、narrative_feedback保持；临时两份语言上下文独立，最终保留一份原上下文加drafts['zh-CN'/'en-US']。输出有实际本语言H1、正文与失败信息，没有Kit。

[KNOWN][HIGH] 输入仅检查可写上下文、有效模式、非空来源正文、Deep非空判断和未发布状态；不重新确认人工审批。补查失败但初研有正文仍可起草。捕获响应校验只有H1/非空正文/标题文字系统，validation=structure_and_title_script_only，不是全文语言或事实审计。

## 本轮证据

| 执行 | 输入及调用 | 返回 |
|---|---|---|
| [KNOWN][HIGH] 747 | 合成News上下文；第一语言Code原生抛错，无模型 | drafts_partial，中文failed，英文合成稿保留，原上下文保留。 |
| [KNOWN][HIGH] 748 | 合成Deep已修改Narrative；中文空响应，无模型 | drafts_partial，英文合成稿及Narrative保留。 |
| [KNOWN][HIGH] 749 | 已读取来源节选，真实News Writer两语言 | drafts_ready，中英文均非空，带来源链接。 |
| [KNOWN][HIGH] 750 | 同类来源节选，显式合成的修改后Deep Narrative，真实Deep Writer两语言 | drafts_ready，标题与核心判断保留，包含不依赖本机资源也可运行的反向限定。 |

[KNOWN][HIGH] 749/750是原母流程内新增D节点的真实模型执行，不调用旧Writer子流程，也不重跑研究、编辑、图片或Kit。没有父manual误调用旧Writer生产版的问题。C以前的流程并未在本轮连续执行，邮件输入依旧断开。

[KNOWN][HIGH] 正例使用715/716/743之前读取的工程师原帖、官方帮助页和转载引文的缩减材料；保留正文表述，部分Markdown链接格式简化，明确标记excerpt/partial。不是743完整payload的逐字回放、不是本轮新闻事实核验、也不是三份独立报道。Deep确认和选稿明确synthetic，不冒充用户真实批准该文章。这个窄样本不能证明多方观点充足时的完整新闻广度。

[COMPUTED][HIGH] 本地15项接口测试通过，收尾再次运行相同结果。旧适配器Git blob3f7451fc77fe6e82b3bea9e20c6d54ec0794e54f核对一致，其6项新上下文测试全部失败后才替换。最初尚未生成实现文件的脚手架失败不计为行为RED。其余测试覆盖两种模式、原材料独立复制、Deep缺判断、空来源、补查失败、两种语言、失败/空稿保留、逆序/缺失/重复/身份错配。不是全仓CI；容器DNS无法解析远程仓库，未取得完整仓库运行全套测试。

[COMPUTED][HIGH] 复制保存的自动稿字符数（UTF-16 string.length口径，无末尾换行）：News中文2078/英文3658，Deep中文2073/英文3177。四稿分别有3/2/3/3处来源链接。仅这些初稿，不是轻编辑稿或图文稿。

## 实际读稿发现，不关闭出版质量

[INFERRED][HIGH] News英文围绕事件、旧新运行方式和本机文件条件展开，没有强塞商业论点；Deep两版围绕给定的两类依赖判断展开，保留无需本机文件也能运行的反向限定，未换成通用安全论点。模式任务有差别，但材料偏同一方，不能宣称广泛独立观点覆盖已通过。

[KNOWN][HIGH] 中文News仍写了独立的“这些说法目前来自哪里”段落、来源读取说明，以及“新版把两样东西一起搬走”这类容易误导新旧差异的措辞；原材料说旧版模型推理已经在云端。开头还增加了风扇等未提供细节。引文收录日期不能直接当成原帖日期。中文Deep有“它照常跑完”等过满说法、英文引语和来源方法说明残留。英文稿也有重复限定/结尾，Deep英文发展偏短。

[INFERRED][HIGH] 本轮保留自动原稿，不重抽刷分、不叠加冷读或隐藏编辑。下一大环节的一次轻编辑应就地处理这些问题，再判断编辑输出是否合格。必要事实限定应保留，研究过程说明不应占正文篇幅。

## 恢复点与边界

[KNOWN][HIGH] Mother初始52bcc8e0-414e-4f2e-9d53-af16fca74034；永久D补丁5d701ed6-216e-478a-a872-7f839da9898a；四枚临时节点清理后f9e054b5-62d8-4a7b-bcb9-0ace1ed8dd85。永久补丁→清理版的原生diff全部为空，53节点；activeVersion仍c94debcc-2fe0-438a-a3df-a1d699740c99，未发布新草稿。

[KNOWN][HIGH] V2 Writer nHxILnDVz541Cu5P仍a89919a4-b110-4236-9398-ab716c965e0a，81节点，inactive，无activeVersion，本轮未修改。采集、浏览器、研究模型、凭据配置和C主线也未修改。原旧Writer65KUDdo1G6k3VysU未调用或编辑。

[KNOWN][HIGH] GitHub起点23f79870714aa91346dde20812603548117c980b的主计划落后于已读取的live C2/C3；本轮更新当前A-F状态，旧计划原blob完整另存archive。只提交D实现/合成测试/检查点，不宣称已经补齐此前C2/C3的全部源码快照。live起点仍可原生恢复。

[INFERRED][HIGH] 单一loop是为避免模型子节点与.item跨语言串稿，并保持失败继续；代价是两语言串行执行。作者自审，不是独立审查者。停止在D；下一回合进入E的轻编辑，之后才配图，Kit仍最后处理。

## 源码映射

[KNOWN][HIGH] src/n8n/draft-languages.js、capture-mode-draft.js、collect-mode-drafts.js分别对应Draft Languages、Capture Mode Draft、Aggregate Drafts，均为Code v2/runOnceForAllItems。mode-drafting.nodes.json保留模式提示词、原生loop/switch及动态模型参数；模型凭据仅引用既有连接，不含秘密。tests/n8n/mode-drafting.test.cjs可用node --test单独运行；无网络或凭据依赖。四篇自动稿仅交付会话，不进入公开仓库。

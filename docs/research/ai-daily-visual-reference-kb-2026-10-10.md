# AI Daily 配图一手参考方法（2026-10-10）

**用途：** 为现有 Planner 提炼简短的自拟指导。下列方法摘要依据用户提供的 2026-10-10 一手来源阅读记录；链接指向原作者主仓或官方文档。它们是源项目做法，不是 AI Daily 的实现或效果证据。没有引用原文。

| 源项目方法（来源事实） | AI Daily 自拟借鉴 | 不照搬 |
|---|---|---|
| [Baoyu Article Illustrator 主技能](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-article-illustrator/SKILL.md)、[prompt construction](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-article-illustrator/references/prompt-construction.md) 与 [workflow](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-article-illustrator/references/workflow.md)：先拆内容结构与视觉意图，再描述布局、元素关系、颜色、风格和比例；参考图可承担直接参考、风格或调色板参考；强调概念表达而非机械照字面绘图。 | 先找文章的视觉机会与段落用途，再具体化画面。参考图用途要说清；实际看见图像或可靠摘要后才引用其视觉信息。 | 不采用密度参数、每章节至少一图、大量 prompt 文件或固定 QA 流程。 |
| [Baoyu Cover Image 主技能](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-cover-image/SKILL.md) 与 [自动选择参考](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-cover-image/references/auto-selection.md)：type 表示概念/场景等画面组织任务，palette 表示配色，rendering 表示表现手法，style 是组合预设。主仓当前列有 11 种 palette、7 种 rendering 及 font 维度，这是源项目事实。direct 图片参考需要实际图像输入；style/palette 参考可由看图提取视觉特征写入 prompt。 | 将文章含义与画面表达分开，再描述主体、关系、构图、配色和手法；可用适合内容的现成封面。 | 不复制其固定映射、默认文字、字体维度、确认/密度要求或生成服务。作者未提供图像效果验证，本研究不推断其效果。 |
| [yf-article-illustrator](https://github.com/yf122233455-stack/yf-article-illustrator/blob/main/SKILL.md)：先找能改善理解、结构、记忆、场景或情绪的视觉机会，再选择 illustration、diagram 或 no-image。 | 先判断视觉机会，再按内容选择复用源图、解释性生成图、氛围生成图或不配图；优先复用合适源图。 | 不照搬 shotlist、manifest、QA 脚本或全篇单一风格。 |
| [article-image-prompt](https://github.com/wangcb8i8i/agent-skills/blob/main/article-image-prompt/SKILL.md)：在写生成 prompt 前先明确读者看图应理解什么，并描述分屏、流程方向、配色和视觉锚点。 | 用“希望读者从图中理解什么”帮助解释型配图规划；允许情绪与修辞表达，不要求每张图承载硬论点。 | 不按文章字数分配图片数，不设套餐级别或统一批次流程。 |
| [qiaomu-ppt visual asset acquisition](https://github.com/joeseesun/qiaomu-ppt/blob/main/references/visual-asset-acquisition.md)：区分来源文章截图/图表与生成的解释/氛围图；候选线索包括尺寸、标题、Alt、URL、来源，排除页面装饰，并分开搜图意图和生成 prompt。 | 真实素材与生成素材承担不同用途；元信息用于发现和筛选候选，实际理解图片仍需取得图片或可靠视觉信息。尺寸线索仅帮助找候选。 | 不搬用幻灯片框架、数值评分、审计/权限体系；尺寸或元信息不作为程序创作否决条件，也不等于看过图片。 |
| [KarenSpinner article thumbnail](https://github.com/KarenSpinner/article-thumbnail-skill/blob/main/article-thumbnail/SKILL.md)：读文章提炼论点、语气与具体物件，规划单场景主体、动作、背景、构图和配色；可实际提供角色/风格参考图，生成后看图并修订。 | 封面围绕文章具体对象和动作组织单一画面；仅在现有已授权能力允许时使用实际参考图。 | 不增加固定角色、自动创作审核或无限生成/修图循环。该来源没有本项目所提“最近三篇封面”机制。 |
| [Gemini API image understanding](https://ai.google.dev/gemini-api/docs/image-understanding)：官方示例说明图像可与文字共同输入，也展示多图比较。 | 实施前先检查已授权现有 node/tool 是否支持实际图片输入；仅 URL 或 Alt 不证明模型看过图，能力缺失就报告阻塞。 | 该文档只证明其所述 API 示例，不证明现有 GPT-6 Sol/n8n 链路支持，也不构成更换模型/provider 的建议。 |

## 面向现有 Planner 的自拟指导

1. 先找文章的视觉机会与段落用途，再选择：复用贴题源图、生成解释图、生成氛围图，或不配图。
2. 对要生成的图，说明读者要理解/感受什么，再写主体关系、构图、配色与表现手法。允许隐喻、幽默和情绪表达，不要求每图都是硬论点。
3. 对源图，确认其与文章具体内容贴题，并基于实际取得的图像或可靠视觉信息理解其内容；不要以 URL/Alt 冒充已看图。
4. 封面使用一张无字共享图。最近三篇不同文章封面是用户确认的本项目软参考：仅参考实际封面图像或从实际图像读取的可靠视觉摘要，用于回避相近材质、构图或颜色，不强制轮换。旧 prompt 仅辅助创作意图，不作视觉参考，也不能替代成图。历史不足时用已有图像；读取失败保留正文并如实注明未参考。不得以 URL 或文字标签假装看过图；这不是上述来源项目已验证的机制。
5. 风格名称列表本身不是充分的规划输入；可补充图旁语境或实际图片信息。候选材料与语境可能影响 Planner 对源图的选择，但原因尚未由历史回放证实，不把它写成执行 877 的已知根因。旧 prompt 只辅助创作意图，不是实际看图所得的视觉摘要。

## 证据限制

本研究整理方法，不运行这些技能或生成服务，不评价图像效果，也不证明任何方法已在 AI Daily/n8n/GPT-6 Sol 链路上验证。实施仍需先 fresh-read 当前授权的节点和工具能力，不静默切 harness 或 provider。

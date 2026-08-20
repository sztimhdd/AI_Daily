# 双语编辑质量层 Specification

**状态：** 已确认（提示词资产迁移矩阵批准后的首个 spec）｜**日期：** 2026-08-14

## 1. 目标与定位

双语编辑质量层是每版终稿在 assembly 之前必须通过的独立质量门。中文版与英文版**各自独立验收**：共享选题、证据底座、叙事与插图方案，但文案与编辑处理各自独立，英文版是从证据重写，**永不做中文版的翻译**。任一版本未过门，不得进入该版本的组装与发布；另一版本不受阻塞（Independent edition acceptance，见 CONTEXT.md）。

质量层不替代 research/draft 阶段，而是发布前的最后一道编辑关口。它只做检查与拒绝/打回，不静默改写。

## 2. 资产底座（Provenance）

质量层的规则必须来自单一资产源。已编译资产与待补编译项如下：

| 资产 | 来源节点 | 状态 | 说明 |
|---|---|---|---|
| `knowledge/author-style.md` | UDW·First Draft Writer1、REF·去AI味、REF·中文图文编辑 | 已编译 | 人设、News Peg/Nut Graf/Smart Brevity/Kicker、句子与排版规则 |
| `knowledge/remove-ai-slop.md`（deslop.py 8 类检查） | REF·去AI味 Module1/2/4、REF·中文图文编辑 | 已编译 | 中英黑名单、连接词、模板开头、排比等 |
| `knowledge/research-contract.md` | RES·Message a model core_directives、UDW·First Draft Writer1 防幻觉条款 | 已编译 | 证据层级、引用协议、冲突标注、零捏造 |
| **归因公式契约** | UDW·First Draft Writer（信息源+客观动作+内行诊断；禁"我测试了"冒领） | **待补编译** | 建议新建 `knowledge/attribution-contract.md`，zh/en 各一版 |
| **视觉高亮规则** | UDW·去AI味（精准加粗数据/专有名词/毒舌吐槽；2500 字进出保真） | **待补编译** | 并入 author-style.md 排版节，或质量层 spec 内定义 |
| **EN 节奏契约** | UDW·Final Editor1（3-Sentence Rule、1-2 个冷笑括注、Markdown Purity） | **待补编译** | 建议新建 `knowledge/en-rhythm-contract.md` |
| **EN 声线 JSON** | REF·Final Editor1（tone_keywords/avoid AI phrases/Ban List/惯用短语/隐喻） | **待抽资产** | 从提示词内嵌 JSON 抽为独立资产文件 |
| ZH 声线 | REF·Final Editor2（风格克隆、AI 腔对照表、标题+导语+小标题） | 待补编译 | 代表作样本从 Drive 本地化后入库 |

单一资产源原则：legacy 中黑名单、mental_models、英文 de-AI 规则存在双份漂移（Task Master Agent1 vs Fan-out 兜底；Final Editor1 vs Final Editor3），迁移时各收敛为一份 knowledge 资产。

## 3. 双轨编辑原则

1. **同题同证同叙事，各自成文**：两版共用选题、证据池与叙事 thesis；文案、结构、修辞各按语言独立处理。
2. **EN 非翻译**：英文版必须从证据底座重新组织论证；出现中文直译句式（硬译成语、中式从句）判 revise。
3. **篇幅**：zh 3500–6000 字、en 800–1200 词；篇幅服从信息价值，宁短勿注水；超上限需主编批准（CONTEXT）。
4. **事实一致性**：两版共享的数字、归因、来源必须一致；分歧只能是编辑处理差异，不得是事实漂移。

## 4. 四道检查（每版独立执行）

### 4.1 证据边界检查（最高优先，硬门）

- 事实 / 推断 / 观点三者可区分；厂商公告、基准、价格、引语、第三方背书必须有可追溯证据。
- 每条 sourced claim 内联 `[标题](URL)`；无链接事实不得进入正文。
- 直接引语：引用块 + 署名；来源观察写"据 X 报道"；**归因公式**：信息源 + 客观动作 + 内行诊断，禁止把他人测试写成自己行动（宁缺毋假）。
- **墙内证据状态**：来自 zhihu/mp.weixin 等墙内来源的论断，若正文未抓取成功（fetch 状态 failed/unavailable），必须显式降级标注（如"仅有一手墙内来源、正文未抓取"），不得伪装确定。
- 核心论断证据不足 → 触发证据恢复规则：回 research（优先墙内 fetch 车道）补齐或记录缺失后重写；**不得用免责声明替代研究**。
- 不确定处理三选一：降低断言强度 / 显式标记不确定 / 删除。

### 4.2 声线与人设检查

- ZH：15 年大厂老兵角色锚定；四大修辞法则（反常识破冰 / 概念降维 / 肉痛感 / 冷酷判决）；面向 CTO/架构师，拒绝公关辞令与翻译腔。
- EN：Lead Tech Editor + 冷峻硅谷腔；专业商务英语；tone_keywords 与惯用短语库（来自 EN 声线 JSON）。
- 各语言 Ban List 独立执行：ZH 大厂黑话/机翻腔（赋能/闭环/抓手……），EN（leverage/robust/delve……）。

### 4.3 去AI味检查（可执行）

- 既有 8 类检查（deslop.py）：空泛连接词、模板化开头、机械总分总、过度排比、过度书面化、空泛营销词、无依据确定性、AI 模板结构。
- 本 spec 新增检查项：
  - **视觉高亮**：加粗只用于数据/专有名词/毒舌吐槽，加粗前后各留一个空格；
  - **字数保真**：编辑轮不得增删语义，进出字数差须在容差内（legacy 2500 字进出不差一字的理念）；
  - **AI 痕迹标签清除**：禁"金句：/ 总结：/ [编辑注] / 综上所述"式标签与 XML 残留（Markdown Purity）；
  - **占位符保护**：`{{IMG_X}}` / `![IMG_X](placeholder)` 不得被改写或删除，未替换即报错。

### 4.4 结构与节奏检查

- ZH：段落 ≤3–4 句且 ≤4 行；`**加粗引导语**` 开关键段；冷结尾 Kicker，禁总结式收尾、禁展望未来；标题 + 100–150 字导语 + 小标题；移动端排版。
- EN：3-Sentence Rule（每段 ≤3 句）；注入恰好 1–2 个技术性冷笑括注 `(*...*)`；Bolded Lead-ins 与正文贴合。
- LinkedIn SEO 标题/摘要字段（58/158 字符）属于 delivery 资产，本层只检查正文节奏，SEO 元数据延后到适配器阶段。

### 4.5 双语一致性检查

同一质量门运行两次（zh、en）后，做一次跨版核对：共享数字、归因、来源、叙事 thesis 一致；不一致项必须解释为编辑处理差异，否则打回事实源再核对。

## 5. 门禁与状态语义

每版结果四选一：

| 结果 | 含义 | 后续 |
|---|---|---|
| `pass` | 全部检查通过 | 进入 assembly |
| `pass_with_notes` | 通过但有记录在案的小问题 | 进入 assembly，notes 随包存档 |
| `revise` | 风格/节奏/去AI味不达标 | 该版重写后重过门 |
| `evidence_recovery` | 证据边界硬门未过 | 回 research 补齐（优先墙内 fetch 车道），记录后重写再门禁 |

- 独立验收：一版 `pass` 即可交付该版；另一版继续恢复或修订，互不阻塞。
- 每次门禁结果写入 `.local/runs/<date>/quality/<lang>-report.md` 并记入 run state；禁止静默放行。

## 6. 实现分工（Codex 判断 + Python 确定性）

- **Python（确定性检查）**：黑名单/连接词/排比/模板开头扫描（deslop 扩展 EN 模式）、字数与句长/段长、链接存在性、引用格式、加粗空格、占位符保护、AI 痕迹标签。
- **Codex（编辑判断）**：声线校准、节奏与冷笑括注、事实/推断/观点区分、墙内证据降级判断、证据恢复决策、双语一致性核对。
- 质量报告不入 Git，最终接受结果记入 state 与 outputs 包 metadata。

## 7. 测试与验收

- 单元：每个确定性检查器至少一个命中用例 + 一个非命中用例（沿用现有 202 测试风格，镜像 src/ 结构）。
- UAT 场景：
  - zh `pass` + en `revise` → 仅 zh 可组装，en 重写后重过门（独立验收）；
  - 墙内来源未抓取成功 → 正文含显式降级标注，且该论断不得以确定语气出现；
  - 核心论断无支撑 → `evidence_recovery`，不得以免责声明替代；
  - 无占位符残留、无空 `![]()`、无依赖图像存在的表述（与视觉 spec 一致）；
  - EN 出现中文直译句式 → `revise`；
  - 字数越界 → `revise`（除非有主编批准记录）。

## 8. 明确排除

- 生图与视觉质量（见 2026-08-13-codex-native-visuals-design.md）；research 主动搜索（V1.5）；delivery SEO kit 与公众号/LinkedIn 适配器（未来）；翻译模式（EN 永不做翻译）。

# Research 主动搜证与证据充分性审计门

**状态：** 待用户复核（2026-08-14）｜**性质：** 取代 2026-08-14 prompt-asset-migration-matrix 决策记录第 2 条“research 封闭证据池”与 knowledge/research-contract.md 中“独立联网深搜延后 V1.5”的结论。

## 1. 问题陈述

英文行业分析若只消费 AIHOT/RSS 摘要，无法达到原 n8n 工作流的内容质量。原流程的真实 Research 是双阶段主动搜证，不是封闭池关键词匹配。本 spec 将其“控制逻辑”迁回第一闭环，并把 Narrative 选定后的证据判断固化为强制自动门。

## 2. 双阶段 Research 语义（从 legacy 提取）

### 2.1 Initial Research

用户选题 + 附加研究指令 → 构造 OSINT 调查目标 → 抓取原始材料 → 生成七模块情报档案：

1. 核心事实与时间线
2. 财务与资本账本
3. 技术架构与工程实锤
4. 生态博弈与护城河
5. 社区原声与野生实操
6. 组织动荡与人事
7. 主编定向指令核查

约束（legacy 原文语义，须保留）：数据零压缩、提取微观场景、剥离公关话术、时间红线防幻觉、禁 AI 味。

### 2.2 Targeted Research

叙事/大纲确定后，只寻找大纲中不存在的“增量弹药”：

1. 硬核数据补全（算力成本、API 定价、财报隐藏亏损）
2. 社区与开发者原声（带情绪与具体场景的原话）
3. 事实交叉验证（诉讼进展、判决、官方回应）

第二轮不重复第一轮背景调查，而是针对既定论点寻找“支撑 / 推翻 / 修正”的证据。

### 2.3 底层搜证执行语义（legacy Researcher 内）

```text
研究意图
→ 拆分为原子搜证任务
→ 按来源路由（墙内登录平台→浏览器；普通 URL→抓取；无 URL→全网发现）
→ 抓取失败→浏览器抢救
→ 多来源聚合、URL 去重、截断、来源标记
→ 真实性核查 + 冲突标注
→ 缺口→继续搜索
→ 高可信 Research Brief
```

这四个语义必须保留：两轮研究、任务分解、按来源路由与降级、缺口触发新搜索。

## 3. 证据充分性审计门（强制、自动）

位置：Narrative 选定之后、英文写作之前。

输入：用户选定的叙事、其核心 thesis 与关键论点、Initial OSINT 数据包、已抓取全文、URL、来源类型与时间、已知冲突与 fetch 失败记录。

输出（机器可读）：

```json
{
  "verdict": "sufficient | needs_research | unsupported",
  "claim_coverage": [],
  "evidence_gaps": [],
  "research_tasks": []
}
```

检查清单：

- 核心 thesis 是否有直接证据，而非仅新闻背景
- 关键因果是否有机制或案例支持
- 产品功能/价格/基准/财务数字是否有一手来源
- 是否有独立来源交叉验证
- 是否存在反例或相互冲突的报道
- 知乎/微信/Reddit 内容是用户经验还是可推广事实
- 引用页面是否实际抓取成功
- 时间线是否仍有效
- 是否有足够具体数据、实验、微观场景支撑英文分析

## 4. 自动补证循环

当 `needs_research`，Codex 按缺口生成原子任务，不做泛泛搜索：

| 缺口类型 | 补证方向 |
|---|---|
| 缺官方数据 | 官方文档 / 公告 / 论文 / 财报 |
| 缺真实使用反馈 | zhida.zhihu.com / 知乎 / Reddit / GitHub Issues |
| 缺具体实验 | 技术博客 / 基准 / 复现实验 / 开发者报告 |
| 来源冲突 | 分别抓取双方原文 + 第三方验证 |
| 单一来源 | 搜索独立出处或原始事件来源 |

Python 负责路由、抓取、保存、去重；Codex 负责判断搜什么、证据是否回答了问题。

### 循环边界（最多两轮补证）

```text
第一次审计 → 第一轮补证 → 再审计 → 必要时第二轮补证 → 最终审计
```

最终判定：

- `sufficient`：进入英文写作
- `unsupported`：不能写成确定性结论，停止并报告原因
- 部分次要论点不足但不影响核心叙事：Codex 可删除或降低断言，不问用户
- 核心叙事无法成立：不静默换叙事，异常阻塞交回用户

## 5. 车道映射（n8n → Codex/Python）

| n8n 原车道 | Codex/Python 版本 |
|---|---|
| Google/Tavily 搜索 | Brave Search / Tavily / Codex Search |
| Firecrawl 普通抓取 | 直接 HTTP → Tavily Extract |
| MCP 登录墙抓取 | Brave CDP（walled-fetch-cdp skill） |
| Firecrawl 失败转 MCP | 普通抓取失败 → Brave CDP 抢救 |
| Gemini 情报分析 | `codex exec` |
| Google Drive 情报库 | `.local/runs/<date>/research/` |
| Targeted Research Phase | Python 按 evidence_gaps 再调 Codex + 抓取车道 |

## 6. 与质量层的关系（边界不重叠）

- 本门在 Narrative 之后、写作之前：判断“能不能写”，不够则补证。
- 双语编辑质量层的证据边界检查在 draft 之后、assembly 之前：判断“写出来的有没有越界/无证据断言”，越界则打回重写。

两者共享 evidence recovery 语义，但作用于不同阶段，不得合并为一个门。

## 7. 修订关系

- 取代 prompt-asset-migration-matrix 决策记录第 2 条：research 从封闭证据池改为主动搜证。
- 修订 knowledge/research-contract.md §硬规则 6、§明确不做：允许引入 collect 之外的一手 URL（须来自真实抓取并记录 fetch 状态），保留“零捏造、引用协议、冲突标注、恢复语义”。
- 原矩阵 research+fetch 表中“Intent Router / Tavily Payload Builder / 统一情报洗数据”从“延后/弃用”改为“控制逻辑采纳、执行工具替换”。

## 8. 明确不做（V1）

- 完整 claims/evidence graph、引用质量自动打分
- 无限轮补证；上限两轮
- 用免责声明替代补证（沿用 evidence recovery rule）

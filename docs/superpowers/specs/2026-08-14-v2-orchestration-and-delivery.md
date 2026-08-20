# V2 编排架构与交付顺序（CLI 主控 + 英文优先最小闭环）

**状态：** 待用户复核（2026-08-14）｜**性质：** 取代 2026-08-12 daily-editorial-run-design 中关于运行载体与双语交付顺序的既有决策。

## 1. 目标与取舍原则

优化目标只有四个：**快速、简洁、可用、可靠**。不追求架构最优、安全、企业级控制面。

由此得出两个明确方向：

1. 用 Python CLI 主控流程，Codex 作为可替换的智能 worker 和便利定时器。
2. 先交付一个能产出英文全文的最小真实闭环，再逐层加深，而不是并行铺满所有环节。

## 2. 职责划分

### Python CLI（唯一流程真相）

负责一切不需要 AI 判断的确定性工作：

- 当前阶段与状态机推进（读/写 `.local/runs/<date>/state.md`）
- 产物存在性检查与幂等重跑
- 是否等待用户（`awaiting_topic` / `awaiting_narrative`）
- 抓取路由：AIHOT、RSS、搜索、墙内 CDP、普通 HTTP
- 文件下载与 `.local/` 缓存管理（URL + sha256 + fetch 状态）
- 调用 Codex CLI 并检查退出码与产物
- 失败后从哪里恢复，绝不重新 collect
- 图片失败是否阻断正文（不阻断）

### Codex CLI（智能 worker）

负责需要编辑判断的步骤，每次执行一个明确任务：

- 从 AIHOT 候选中形成三个真正不同的选题
- 根据 topic 制定 research queries
- 阅读抓取材料，生成 OSINT 证据档案并识别缺口
- 提出叙事候选
- 判断证据是否足以支撑用户选定叙事（见 research-sufficiency-audit spec）
- 按证据缺口生成定向补证任务
- 写英文完整稿
- 做英文编辑质量检查

约束：Codex 不承担状态机、不维持全流程记忆、不负责触发与调度。每个 `codex exec` 任务读输入文件、写约定产物、退出。

### Codex Automation（可替换的便利定时器）

仅负责在约定时间唤醒一次 Python CLI。不承载业务流程、不等待用户输入、不是唯一入口。

## 3. 触发与恢复

```text
Codex Automation ──┐
                   ├──> Python CLI 读状态 → 自动推进 → 写状态 → 退出
手动运行同一 CLI ──┘
```

规则：

- 每次激活最多推进一个确定回合，绝不阻塞等待回复。
- 到达 HITL 状态时写 `awaiting_*` 并退出，随后通知用户运行 resume。
- 自动打开 Terminal TUI 是便利功能，不是恢复流程的唯一入口。
- 若实测 Automation 漏跑，只把触发器换成 `launchd`，Python 流程不变。

## 4. HITL 决策点（正常路径两个）

1. 选题（topic）
2. 叙事（narrative）

“是否补证、补什么、补几轮”由 Codex 自动完成，不设 HITL。核心叙事无法被证据支持时，作为异常阻塞交回用户，不静默换叙事。

## 5. 英文优先最小闭环

第一版真实闭环范围：

```text
手动 CLI 启动
→ AIHOT 获取真实热点
→ 生成 3 个选题
→ TUI 选题（HITL）
→ Initial Research（官方/一手 + 普通网页 + 知乎/微信/真实用户反馈）
→ Codex 生成 OSINT 证据档案并识别缺口
→ 叙事候选 + TUI 叙事选择（HITL）
→ 证据充分性审计（强制、自动）
→ Targeted Research（按缺口自动补证）
→ Evidence Package
→ 英文完整稿
→ 英文编辑质量门
→ article.md + sources.md + metadata.json
→ 成功结束
```

第一轮不包含：

- 定时 Automation、launchd
- 中文稿（英文闭环稳定后加入）
- 全量 RSS、复杂 evidence map
- 封面与正文插图、ChatGPT 网页生图
- GitHub 发布、邮件/微信通知

## 6. 增量路径（英文闭环稳定后依次加入）

1. 失败恢复与重复执行测试
2. Research 多来源与证据边界加固
3. 中文稿 + 中文编辑质量门
4. 双语一致性（同题同证同叙事，各自成文，EN 永不翻译）
5. RSS 情报增强
6. 图片增强车道
7. Codex Automation 定时触发
8. 发布适配器

## 7. 明确不做（V1）

- GitHub 远程控制平面、数据库、消息队列、常驻 daemon、通用 DAG 引擎
- 用 Codex 长 session 维持全流程记忆
- 机械复刻 n8n 每个节点为 Python 类
- 为 TUI 引入大型框架

## 8. 对既有文档的修订

- 取代 `2026-08-12-daily-editorial-run-design.md` §Implementation Decisions 中“GitHub 是运行控制与协调层”的定位：V2 以本地 CLI 与 `.local/` 状态为真相，GitHub 仅作发布目标之一。
- 取代同一 spec 中双语并行为默认交付的排序：V2 先英文闭环，中文随后。
- 取代 CONTEXT.md“GitHub control plane”与“scheduled activation 必须先校验 GitHub 状态”为本地状态机语义；若未来重新启用远端控制面再改回。
- 维持 CONTEXT.md 的 evidence recovery rule、independent edition acceptance、human decision point 的语义，仅将其实现载体从 Codex 会话改为 Python CLI 状态机。

## 9. 验证口径

每个闭环阶段结束时，仓库都必须有一个能产出文章的版本；不出现“每个零件都做了但从未完整跑通”的状态。真实运行证据优先于摘要与截图。

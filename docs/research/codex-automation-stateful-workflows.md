# Codex Automation / Tasks / Threads 承载有状态多步骤业务工作流：可行性调查

调查日期：2026-08-12
调查对象：OpenAI Codex（ChatGPT 桌面端 / Web 的 Automations、Scheduled tasks、Threads、Goal mode、worktree 环境）是否适合承载多步骤、跨阶段、可暂停续跑的业务工作流（以 AI Daily 公众号选题-写稿-配图流水线为参照）。

## 结论摘要

Codex 已经具备承载这类工作流的全部原语：同线程周期唤醒（heartbeat）、独立定时任务（standalone cron）、线程恢复（thread/resume）、可暂停续跑的 Goal mode、按聊天隔离且可复用的 worktree。但它目前**没有**提供业务状态机所需要的内建保证：没有错过运行补偿、没有 exactly-once/幂等承诺、没有跨线程共享状态、失败重试与退避仍是开放 feature request。可行架构是：**Codex Automation 只当触发器与执行器，业务状态、阶段产物、幂等记录全部落盘到仓库文件，作为唯一事实来源**。

建议风险等级：**受控原型可行；直接生产迁移风险中-高**（详见 Q8 风险分级表）。

## 方法与来源分级

本报告的所有官方结论均通过实际抓取并打开以下一手页面核实（非搜索摘要）：

- 官方文档（一手）：[developers.openai.com/codex](https://developers.openai.com/codex) 各页（glossary、automations、environments、long-running-work、pets、notifications、app-server、feature-maturity、use-cases）、[learn.chatgpt.com/docs/automations](https://learn.chatgpt.com/docs/automations)、[OpenAI 博客](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)、[OpenAI Cookbook](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)。
- 官方 GitHub 仓库（一手仓库、用户报告）：[openai/codex](https://github.com/openai/codex) 的 issues 与 discussions。Issue 标题与状态均经 GitHub API 逐一核验（20 个 issue + 1 个 discussion，全部真实存在且截至调查日为 open）。
- 社区经验（非官方）：Reddit r/codex。reddit.com 对本机匿名访问返回 403 封锁，故帖子正文与评论通过公开存档 API [Arctic Shift](https://arctic-shift.photon-reddit.com) 获取原文，帖子 ID、标题与发帖时间均与搜索引擎索引交叉验证。所有 Reddit 引用在文中明确标注「非官方」。

---

## Q1：automation heartbeat vs cron 的执行语义

官方词汇表把两者定义为**不同的任务类型**，而不是同一机制的两种配置：

- **Heartbeat**：「A recurring scheduled task that returns ChatGPT to the same chat.」（把 ChatGPT 反复带回同一聊天的周期任务），仅适用于 Desktop app。定义见 [Codex Glossary](https://developers.openai.com/codex/glossary)。
- **Standalone scheduled task**（即"cron 式"独立任务）：「Scheduled task whose runs each start a new chat and report findings in Triage.」（每次运行新开一个聊天，结果汇报到 Triage/Scheduled）。同上出处。
- **Scheduled task in a chat**：「A scheduled task that uses an existing chat's context and returns each run's results to that chat.」。同上出处。

调度能力上的差异（[Codex Automations 文档](https://developers.openai.com/codex/automations)）：

- 聊天内任务支持「minute-based intervals for active follow-up loops, or daily and weekly schedules」——即分钟级间隔的跟进循环，适合做短周期自动续跑。
- 独立任务支持 RFC 5545 自定义调度，官方示例为编辑 RRULE：`RRULE:FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=9;BYMINUTE=0`。

[learn.chatgpt.com 的 Scheduled tasks 页](https://learn.chatgpt.com/docs/automations)给出官方选择准则：「Use a standalone scheduled task when each run should start from the saved prompt. Use a scheduled task in a chat when you want ChatGPT to return to the same chat with its existing context.」

社区侧的印证（非官方）：多名用户默认遇到"每次运行新开 session"的行为，试图用提示词让 automation 留在同一聊天无效，必须显式配置为聊天内任务——[Automations in one session](https://www.reddit.com/r/codex/comments/1tz0lug/)、[How to keep Codex Automation to run in a single chat?](https://www.reddit.com/r/codex/comments/1u9z0gt/)。

**结论**：heartbeat 语义 = 同线程周期唤醒、保留聊天上下文（仅桌面端）；standalone cron 语义 = 每次全新聊天、天然隔离。做状态流转保持必须选前者，做每日干净入口应选后者。

## Q2：同一 thread 连续唤醒是否保留上下文

官方设计上是保留的：

- 聊天内 scheduled task「uses the chat's existing context instead of starting from a new prompt each time」（[Automations](https://developers.openai.com/codex/automations)）。
- app-server API 提供线程级原语：「thread/resume - reopen an existing thread by id so later turn/start calls append to it」，另有 thread/start、thread/fork、turn/steer（[App server 文档](https://developers.openai.com/codex/app-server)）。
- Goal mode 的状态是「durable, thread-scoped state」，记录目标、生命周期、预算与进度，属于当前线程（[Cookbook: Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)，要求 CLI ≥ 0.128.0）。

但没有任何官方页面承诺聊天上下文的保留期限、容量或跨重启持久性，反而存在多个相关 bug：

- [#25779](https://github.com/openai/codex/issues/25779)：session/turn 状态无界增长导致冻结、上下文膨胀（open）。
- [#37403](https://github.com/openai/codex/issues/37403)：resume 线程失败，报「already has an active writer」（open）。
- 非官方：[Codex app auto-archives automations?](https://www.reddit.com/r/codex/comments/1swtp24/) 报告定时运行产物出现在 previous runs 但总是已归档、无生成内容（0 评论，未复现原因）。

**结论**：同线程连续唤醒保留上下文是官方设计与文档化行为，可作为续跑的辅助记忆；但它是聊天级记忆而非业务契约，存在膨胀、冻结与恢复失败的实际缺陷，**不能作为唯一事实来源**。

## Q3：独立 cron run 的状态隔离

- 每次运行新开聊天、结果进 Triage 是官方定义（[Glossary](https://developers.openai.com/codex/glossary)），因此独立 run 之间**默认零共享上下文**。
- Web 端 scheduled tasks「don't keep a local folder or worktree available between runs. Put durable instructions in the task prompt...」（[learn.chatgpt.com](https://learn.chatgpt.com/docs/automations)）——跨 run 的持久信息要写进任务提示词（或仓库/连接器）。
- 隔离路径上的已知缺陷：[#19969](https://github.com/openai/codex/issues/19969) 定时 automation 创建空 session、提示词未注入；[#33503](https://github.com/openai/codex/issues/33503)「Run now」与定时/远程触发的运行拿到的工具清单不一致（都 open）。

**结论**：独立 cron run 的状态隔离是强保证（甚至过强——连提示词注入都有 bug）。跨 run 状态必须显式外部化：任务提示词、仓库内状态文件、连接器数据。

## Q4：自动化能否等待用户输入并续跑

分两层看：

**聊天/交互层——可以表达"等待"**：

- 聊天状态体系包含「Needs input — A chat needs your approval, answer, or another decision.」，以及 Running / Ready / Blocked（[Pets 文档](https://developers.openai.com/codex/pets)）。
- Activity 视图列出「unread, running, or waiting for your response」的聊天（[Notifications 文档](https://developers.openai.com/codex/notifications)）。
- Goal mode 的进度条支持 pause / resume / edit / clear，且「keeps the same sandbox and approval policy and pauses when it needs a decision」（[Long-running work 文档](https://developers.openai.com/codex/long-running-work)）。
- Cookbook 明确 Goal 的停止条件包括「a blocker that requires user input」，且 continuation 是事件驱动的：只在回合结束、无待处理工作、无排队输入、线程空闲的安全边界检查是否继续（[Cookbook: Goals](https://developers.openai.com/codex/using_goals_in_codex)）。
- Automations 文档要求任务提示词写明「when to stop or ask you for input」（[Automations](https://developers.openai.com/codex/automations)）——即"何时停下问人"靠提示词约定。

**无人值守层——没有"阻塞等待人类输入后自动续跑"的保证**：

- Scheduled tasks 在组织策略允许时使用 `approval_policy = "never"` 无人值守运行；若管理策略禁止，则回退到所选权限模式的审批行为；read-only/workspace-write 等模式下越界工具调用会直接失败（[Automations](https://developers.openai.com/codex/automations)、[learn.chatgpt.com](https://learn.chatgpt.com/docs/automations)）。
- [#31584](https://github.com/openai/codex/issues/31584)：automation 在一个 app 工具调用上停滞 6.5 小时，直到用户手动打开生成的线程才恢复——报告者结论是"unreliable for unattended work"（open）。

**结论**：等待用户输入的正确模型是——run 结束、聊天进入 Needs input、人类打开处理、然后由**下一次定时唤醒或手动 resume** 续跑。没有官方文档承诺自动化能在运行中途挂起等待人类输入并从断点自动继续。AI Daily 必须把"等待人工审核"设计为显式状态 + 下一轮唤醒续跑，而不是期望阻塞语义。

## Q5：worktree / local 对文件状态的影响

官方环境模型（[Environments: Modes](https://developers.openai.com/codex/environments/modes)）分 Local / Worktree / Cloud，其中 Local 与 Worktree 都在本机运行。

对定时任务的硬约束（[Automations](https://developers.openai.com/codex/automations)）：「For project-scoped scheduled tasks, keep the machine powered on and the ChatGPT desktop app running. The selected project must still be available on disk when the task is scheduled to run.」——电脑必须开机、应用必须运行、项目路径必须仍在磁盘上。

worktree 的生命周期语义（[Git worktrees 文档](https://developers.openai.com/codex/environments/git-worktrees)）：

- 「Each chat keeps the same associated worktree over time.」——同一聊天反复回到同一 worktree，这是续跑能复用文件状态的基础。
- Codex-managed worktree 定位是轻量、可丢弃的；默认只保留**最近 15 个**，超限或归档聊天时自动删除，但「Before deleting a Codex-managed worktree, Codex saves a snapshot of the work on it」，重开聊天时可恢复；也可关闭自动删除或改用 **permanent worktree**（不自动删除、可多聊天共用）。
- `.worktreeinclude` 用于把 `.env` 等被 gitignore 的文件复制进新 worktree；`AGENTS.override.md` 自动复制。
- Handoff 可让聊天在 Local 与 Worktree 之间迁移。
- Automations 页面专门有「Worktree cleanup for scheduled tasks」警告：高频调度会累积 worktree（[Automations](https://developers.openai.com/codex/automations)）。

相关缺陷与非官方经验：

- [#35946](https://github.com/openai/codex/issues/35946)：macOS 上创建桌面 automation 时不再提供 Worktree 执行选项（open）——worktree 自动化入口本身存在回归。
- 非官方：[Automating a daily Codex routine + git worktrees](https://www.reddit.com/r/codex/comments/1qhvy6u/) 中用户用本地 n8n 拉取 issue、为每个任务开独立 worktree 隔离、再交给 orchestrator agent，是社区通行的隔离模式。

**结论**：worktree 提供按聊天隔离 + 跨 run 复用的文件状态，适合阶段产物暂存；但受 15 个上限、自动清理和入口回归影响，**业务状态必须持久化到 git 跟踪的文件**（提交进仓库），不能只放在 worktree 的未跟踪/未提交文件里。需要长期稳定环境时用 permanent worktree 或 Local 模式。

## Q6：失败、重复执行、幂等与自动推进的已知限制

以下全部来自 openai/codex 官方仓库的 open issue（用户报告，未经官方确认修复，但均经 API 核验真实存在）：

**调度可靠性**

- [#24327](https://github.com/openai/codex/issues/24327)：应用/电脑离线时错过的运行**不会补跑**（missed-run catch-up 是 feature request）；周任务错过一次即顺延一周。
- [#17893](https://github.com/openai/codex/issues/17893)：heartbeat automation 的 next_run_at 正常推进但从不执行。
- [#16938](https://github.com/openai/codex/issues/16938)：automation 标记 Active 但从不运行、不建线程。
- [#38137](https://github.com/openai/codex/issues/38137)：Windows 上 ACTIVE 定时任务跳过了 08:40 的运行。

**时区与 RRULE**

- [#26633](https://github.com/openai/codex/issues/26633)：RRULE 的 BYHOUR 按 UTC 解释，DTSTART;TZID 被忽略（19 条评论）。
- [#36500](https://github.com/openai/codex/issues/36500)：一次性 automation 因时区歧义被静默排到一年之后。
- [#35791](https://github.com/openai/codex/issues/35791)：Windows heartbeat 对多规则 RRULE 计算错误。
- [#28693](https://github.com/openai/codex/issues/28693)：下次运行时间按 UTC 显示且不标注时区。

**挂起与编排**

- [#31584](https://github.com/openai/codex/issues/31584)：automation 在工具调用上无限停滞，需人工打开线程（见 Q4）。
- [#35030](https://github.com/openai/codex/issues/35030)：定时运行在 `list_threads` 上挂起，同样调用在交互任务中成功——不能用 scheduled task 动态编排其他线程作为主控制面。
- [#28080](https://github.com/openai/codex/issues/28080)：线程工具间歇性丢失 handler。
- [#15723](https://github.com/openai/codex/issues/15723)：后台子进程/子代理完成不会唤醒调用方 agent。
- [#32294](https://github.com/openai/codex/issues/32294)：`automation_update` 暴露但无 handler，导致 automation 无法管理。

**失败恢复与成本**

- [#22390](https://github.com/openai/codex/issues/22390)：请求在瞬时容量错误后带退避重试并保留任务状态——该请求仍 open，说明当前无内建等价物；部分工作后终止需人工恢复。
- [#37445](https://github.com/openai/codex/issues/37445)：打开桌面应用会静默消耗 Codex 周配额（每次后台 suggestion 运行固定约 6%）——无人值守自动化有隐性成本风险。

**文档层面的缺失**：本次抓取核验的 automations、glossary、long-running-work、learn.chatgpt.com 各页中，均无 exactly-once、事务、幂等、失败自动重试/指数退避、阶段回滚或跨线程任务图的承诺。[feature-maturity 页](https://developers.openai.com/codex/feature-maturity)定义了 Under development / Experimental / Beta / Stable 四级标签，但未列出 Automations 条目的成熟度——上线前需再确认当前标注。

**结论**：重复唤醒可能重复执行、失败不会自动重试、错过不会补偿。幂等与去重必须由业务层实现（状态文件 + 产物存在性检查 + 副作用幂等键），自动推进必须有显式状态机与预算上限。

## Q7：真实成功案例

**官方一手**

- OpenAI 官方博客报告 GPT-5.3-Codex 从零构建一个设计工具：约 25 小时不间断运行、约 1300 万 tokens、约 3 万行代码，每个里程碑自动跑验证（tests/lint/typecheck）并自我修复。作者强调关键技巧是 **durable project memory**——把 spec、plan、约束与状态写进 markdown 文件让 Codex 反复读取，防止漂移；并明确「This was an experiment, not a production rollout.」（[Run long-horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)）
- 官方 use-cases 页含 Automation 类别（PR 跟进、收件箱摘要等官方示例）：[Codex use cases](https://developers.openai.com/codex/use-cases)。

**社区经验（非官方）**

- [I set up Codex automations for a client...](https://www.reddit.com/r/codex/comments/1u0x46t/)（非官方）：咨询顾问为建筑业客户在专机上部署 Codex automations，连接 Microsoft 栈（项目收件箱、SharePoint、邮件）与行业软件，定时唤醒「读取当前项目材料、判断归属哪个工地、建案例目录、起草回复、推进案例」；其结论是判断密集型工作交给 Codex automation，干净的事件型工作流仍留给 n8n。评论区另一用户以类似方式把专机做成「Codex Claw」机器，做「从多个异构系统抓上下文再聚合推理」的工作。
- [Using Codex agents to process selected GitHub issues all the way to deployment](https://www.reddit.com/r/codex/comments/1tjs2dw/)（非官方）：约 8 个 Codex agent 组成链式流水线——GitHub issue → 准入检查 → 处理 → 独立验证 → PR → 检查 → 合并/部署，任务类别刻意限定为纯静态页面以控制风险面；作者说明这是个人公开实验，并强调审计面应是 issue/PR/验证记录而非原始日志。这是与 AI Daily 最接近的可审计多阶段案例。
- [What scheduled tasks have you setup to buy you back time?](https://www.reddit.com/r/codex/comments/1vfck1n/)（非官方）：高分案例包括——每日工作台账（连接日历、邮件、Codex、Claude、GitHub、Jira、Confluence 收集证据，产出月报/季报并自动补建 Jira）；每周一审查约 8 条 Jenkins 流水线、抽取安全扫描、triage 后建 Jira 工单；SEO/社媒/周报研究。
- [Anyone using Codex Automations?](https://www.reddit.com/r/codex/comments/1r30lf6/)（非官方）：有用户稳定运行三个 automations（每日更新 agents.md、每日更新大项目的 master.md 索引、用 skill 自动测试 ICS 代码与 API）；同一帖中有人报告「MCPs are not allowed in automations」与另一人「MCP works for me in the worktree sandbox」相互矛盾——automation 内连接器/MCP 可用性随版本与环境变化，上线前必须实测。
- [openai/codex discussion #26148](https://github.com/openai/codex/discussions/26148)：用户请求原生 task board 与跨线程上下文路由，说明跨线程共享状态目前缺失，有人因此自建对话外任务图与运行记录。

## Q8：对 AI Daily 的可行架构与风险等级

### 推荐架构：两层调度 + 一个外置状态机

1. **每日入口（standalone cron）**：每天早上一个独立定时任务，职责仅为「创建或发现当天 run，执行一个确定的推进回合」。独立 run 上下文干净、可审计，符合本仓库 `outputs/YYYY/MM/DD/<article-slug>/` 的产物组织。
2. **同线程续跑（in-chat heartbeat）**：若当天 run 处于可自动继续状态，由聊天内分钟级/小时级 heartbeat 做短周期续跑，利用同聊天上下文减少重述成本；进入等待人工状态后停用自动推进。
3. **状态外置**：`runs/YYYY-MM-DD/run.json`（或仓库约定的 metadata.json）是唯一状态真相，记录当前阶段、幂等键、下一步与阻塞原因；聊天上下文只是辅助记忆。草稿、缓存、日志按仓库规范放 `.local/`，不进 Git；状态文件必须进 Git，避免 worktree 清理丢失。
4. **单回合约**：每个回合读状态 → 验证前置产物存在 → 最多执行一个有副作用的阶段 → 原子写入新状态 → 结束。
5. **幂等**：每个外部副作用记录幂等键与结果（搜索批次、图片生成请求、GitHub 提交、发布 ID）；重复唤醒先查幂等记录与产物存在性，不重复执行已完成阶段。
6. **显式状态集**：`new → researched → drafted → imaged → needs_human → published`，加上 `blocked / failed_retryable / failed_terminal`；禁止靠自然语言猜测是否继续；`needs_human` 状态必须由人显式放行。
7. **人工审核闸门**：发布前必须人工确认——这是不可自动越过的状态。

### 风险分级表

| 等级 | 风险 | 依据 |
|---|---|---|
| 高 | 错过运行不补偿、调度器偶发不执行 | [#24327](https://github.com/openai/codex/issues/24327)、[#17893](https://github.com/openai/codex/issues/17893)、[#16938](https://github.com/openai/codex/issues/16938) |
| 高 | RRULE 时区解释错误导致错误时间执行/漏执行 | [#26633](https://github.com/openai/codex/issues/26633)、[#36500](https://github.com/openai/codex/issues/36500)、[#35791](https://github.com/openai/codex/issues/35791) |
| 高 | 无人值守挂起，需人工打开线程才恢复 | [#31584](https://github.com/openai/codex/issues/31584)、[#35030](https://github.com/openai/codex/issues/35030) |
| 高 | 无内建幂等/重试，失败后可能丢部分工作 | [#22390](https://github.com/openai/codex/issues/22390)、文档无 exactly-once 承诺 |
| 中 | worktree 15 上限/自动清理/创建入口回归丢文件状态 | [Git worktrees](https://developers.openai.com/codex/environments/git-worktrees)、[#35946](https://github.com/openai/codex/issues/35946) |
| 中 | 长线程上下文膨胀、resume 失败、运行产物被自动归档 | [#25779](https://github.com/openai/codex/issues/25779)、[#37403](https://github.com/openai/codex/issues/37403)、非官方 [1swtp24](https://www.reddit.com/r/codex/comments/1swtp24/) |
| 中 | 周配额被后台运行静默消耗 | [#37445](https://github.com/openai/codex/issues/37445) |
| 低 | 本机依赖（开机、应用运行、项目路径存在）、`.worktreeinclude` 遗漏 | [Automations](https://developers.openai.com/codex/automations)、[Git worktrees](https://developers.openai.com/codex/environments/git-worktrees) |

### 上线门槛：先跑纵向原型

不要立即迁移完整流水线。先实现四态原型 `new → researched → drafted → needs_human`，验收必须覆盖：

- 相同 Automation 重复唤醒不重复执行已完成阶段；
- 阶段中途制造失败后能从磁盘状态恢复；
- 聊天上下文清空/换新线程后仍能续跑；
- `needs_human` 状态不会被自动越过；
- 连接器不可用时写入可恢复的失败状态；
- 并发运行只有一个获得阶段锁。

原型连续稳定运行至少一周、恢复测试全部通过后，再迁移完整的选题-研究-写作-配图-发布流程。

## 引用列表

官方文档与博客（一手）：

- [Codex Glossary](https://developers.openai.com/codex/glossary)（Heartbeat / Standalone / Scheduled task in a chat 定义）
- [Codex Automations](https://developers.openai.com/codex/automations)（分钟级间隔、RRULE、approval_policy=never、worktree 清理、本机依赖）
- [Scheduled tasks（learn.chatgpt.com）](https://learn.chatgpt.com/docs/automations)（standalone vs in-chat 选择、Web 不保留本地目录）
- [Git worktrees](https://developers.openai.com/codex/environments/git-worktrees)（同聊天同 worktree、15 上限、快照恢复、permanent worktree、.worktreeinclude）
- [Environment modes](https://developers.openai.com/codex/environments/modes)（Local/Worktree/Cloud）
- [Long-running work（Goal mode）](https://developers.openai.com/codex/long-running-work)（pause/resume、需要决策时暂停）
- [Cookbook: Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)（thread-scoped 持久状态、事件驱动 continuation、停止条件含 blocker）
- [Pets](https://developers.openai.com/codex/pets)（Running/Needs input/Ready/Blocked）
- [Notifications](https://developers.openai.com/codex/notifications)（Activity 视图、waiting for your response）
- [App server](https://developers.openai.com/codex/app-server)（thread/start、thread/resume、thread/fork）
- [Feature maturity](https://developers.openai.com/codex/feature-maturity)（四级成熟度标签；未见 Automations 条目）
- [Codex use cases](https://developers.openai.com/codex/use-cases)（Automation 类别）
- [Run long-horizon tasks with Codex（OpenAI 博客）](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)（25 小时实验、durable project memory）

官方 GitHub（openai/codex，均经 API 核验为 open）：[#15723](https://github.com/openai/codex/issues/15723)、[#16938](https://github.com/openai/codex/issues/16938)、[#17893](https://github.com/openai/codex/issues/17893)、[#19969](https://github.com/openai/codex/issues/19969)、[#22390](https://github.com/openai/codex/issues/22390)、[#24327](https://github.com/openai/codex/issues/24327)、[#25779](https://github.com/openai/codex/issues/25779)、[#26633](https://github.com/openai/codex/issues/26633)、[#28080](https://github.com/openai/codex/issues/28080)、[#28693](https://github.com/openai/codex/issues/28693)、[#31584](https://github.com/openai/codex/issues/31584)、[#32294](https://github.com/openai/codex/issues/32294)、[#33503](https://github.com/openai/codex/issues/33503)、[#35030](https://github.com/openai/codex/issues/35030)、[#35791](https://github.com/openai/codex/issues/35791)、[#35946](https://github.com/openai/codex/issues/35946)、[#36500](https://github.com/openai/codex/issues/36500)、[#37403](https://github.com/openai/codex/issues/37403)、[#37445](https://github.com/openai/codex/issues/37445)、[#38137](https://github.com/openai/codex/issues/38137)、[discussion #26148](https://github.com/openai/codex/discussions/26148)

社区（非官方，Reddit r/codex，正文经 Arctic Shift 存档核验）：[1u0x46t](https://www.reddit.com/r/codex/comments/1u0x46t/)、[1tjs2dw](https://www.reddit.com/r/codex/comments/1tjs2dw/)、[1vfck1n](https://www.reddit.com/r/codex/comments/1vfck1n/)、[1qhvy6u](https://www.reddit.com/r/codex/comments/1qhvy6u/)、[1r30lf6](https://www.reddit.com/r/codex/comments/1r30lf6/)、[1tz0lug](https://www.reddit.com/r/codex/comments/1tz0lug/)、[1u9z0gt](https://www.reddit.com/r/codex/comments/1u9z0gt/)、[1swtp24](https://www.reddit.com/r/codex/comments/1swtp24/)

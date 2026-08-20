# 03 — Initial Research 阶段

**What to build:** `research` 命令从“封闭证据池关键词匹配”改为主动搜证：围绕选题的 research queries 抓取一手与墙内来源，生成七模块 OSINT 情报档案（核心事实时间线、财务资本、技术架构、生态博弈、社区原声、组织人事、主编指令核查），并显式列出证据缺口。

**Blocked by:** 01 — 抓取原语 seam；02 — TUI 交互与进度层（选题 HITL 完成）

**Status:** completed

- [x] research 能按选题的 research queries 触发真实抓取（复用 01 车道）
- [x] 产出七模块 OSINT 档案，模块缺素材时写“无”，不脑补
- [x] 档案显式列出证据缺口，作为后续补证输入
- [x] 档案引用的 URL 来自真实抓取且带 fetch 状态，无来源事实不入档案
- [x] 部分车道抓取失败不阻断档案生成，降级并显式标注
- [x] 数据零压缩、时间红线防幻觉、禁 AI 味（沿用 legacy 语义）

验证记录（2026-08-14）：

- 可见终端全量 `python3 -m unittest discover -s tests -q`：352 tests OK。
- 可见终端 `git diff --check`：通过。
- 真实 AIHOT 回归：`DeepSeek-V4-Pro 正式版上线，Agent 能力大幅增强` 命中 story `4f717b32-d278-4c1a-9e48-e10cbfa1c741`，返回 15 条报道；不会再被仅共享“硅基流动”的 Qwen story 误配。
- Codex CLI JSONL 解析已覆盖事件流、非 JSON 日志、双重编码、错误事件和无效输出；失败保持 `unavailable`，不伪装成功。

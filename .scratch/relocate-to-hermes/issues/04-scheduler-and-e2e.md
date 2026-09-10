# 04 — systemd 调度迁移 + Hermes 真实 E2E 交付

**What to build:** 用 systemd timer 替代 launchd 跑工作日每日写作；在 Hermes 上
走一次完整真实 E2E（选题 → … → 生图 → GitHub 发布），证明搬迁后链路端到端可用。

**Blocked by:** 03（Hermes 可运行 + 登录态就绪）

**Status:** resolved

## Progress

- [x] `scripts/daily-telegram-hermes.sh` 落地并入库（PATH + DISPLAY 适配）
- [x] systemd user timer `ai-daily.timer`（OnCalendar Mon..Fri + 30min）enable 并
      验证下一次触发
- [x] service 手动触发：`collect` 成功（aihot=20），Telegram 阶段幂等 offer
- [x] 修复搬迁暴露的阻塞 bug：`build_catalog` 源文件缺失时跳过并记录
      （`[Atomic] Topic_Survey_Skill.json` 在 Mac 上也缺失，非搬迁引入）
- [x] 真实 E2E：换话题全链路 + 生图 + GitHub 发布

## Answer

E2E 完成。真实话题「Anthropic 越权访问对齐评估」走通全链路：Telegram 选题
（候选 3）→ research → narrative（候选 1）→ audit（needs_research，保守降级）
→ draft-en（1028 词，pass_with_notes，弱论断标注）→ illustrate（ChatGPT 网页
生图 4 张，封面 1920×1080）→ assemble-en → linkedin-kit → run-en 发布。

发布产物：`articles/2026-09-09-when-the-sandbox-found-a-network-cable-en.md`，
4 张图在 GitHub raw 全部 HTTP 200。delivery-en.json status=delivered，
publication=remote（re-read hash 校验通过）。

期间修复两个搬迁暴露的真实 bug（已单测覆盖 + 推送）：
1. `build_catalog` 源文件缺失（`[Atomic] Topic_Survey_Skill.json`，Mac 上也缺）
   时跳过并记录，不再硬崩。
2. narrative 判定「选题质量不足」（killed）时退回 topic 阶段重新选题，不再把
   整个 run 打成 failed——解决用户反复撞的「弱选题卡死」。

- [x] 把 `scripts/daily-telegram.sh` 的语义迁成 Hermes systemd timer（工作日触发），
      失败态与日志可查
- [x] 一次真实 E2E：换一个话题走全链路，图片经 ChatGPT 网页生图产出并嵌入
- [x] 文章 + 图片同 commit 发布到 GitHub，raw URL 非 404
- [x] 终报：包路径、图片清单、GitHub URL、验证范围、调度状态

## 2026-09-10 运维收尾

- Mac 的 `com.aidaily.daily` 已 bootout 并持久 disable，消除双主机重复发送。
- Hermes 09-10 自动推进到 completed，文章及 LinkedIn Kit 已远端发布。
- 新增独立 `receipt` 命令：正常交付、部分交付恢复、已交付早退均尝试通知；
  成功后落盘指纹，失败下次重试，不消费 Telegram 用户回复。
- 完成回执使用纯文本，防止 Markdown 解析破坏 URL 中的下划线。
- 真实补发返回 sent，再调用返回 already-sent；两个公开链接 HTTP 200。
- 验证范围：离线回执回归、调度分支回归、CLI fixture UAT；未重跑付费写作/生图。
- 待自然验收：下一工作日全程无重复消息、完成回执自动到达且链接可点击。
  此项尚未发生，不宣称无人值守通知验收已通过。
- 已知限制：远端收信成功与本地标记写入之间若崩溃，可能重复一次通知。

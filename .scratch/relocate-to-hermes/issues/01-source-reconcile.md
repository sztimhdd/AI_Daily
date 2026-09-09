# 01 — 收口 Mac 源头，推出干净主线

**What to build:** 审阅并收口 Mac 上未提交/未推送的改动，让 `origin/main` 变成
干净最新主线，Hermes 才能 clone 到正确起点。

**Blocked by:** None — 可立即开始

**Status:** resolved

- [ ] 列出 4 个未推送 commit 与全部未跟踪文件，区分「用户手改 / 前一代理产物」
- [ ] 09-08 Astra 与 09-09 GPT Image 2.5 两篇英文文章包（article + outputs +
      metadata/sources/images）按现有目录规范纳入版本
- [ ] `outputs/2026/09/02/.../linkedin-kit.md` 的改动经审阅确认归属后提交或保留
- [ ] 全部改动 `git diff --check` 通过，提交并 push，`origin/main` 与本地一致

## Answer

收口完成。远程有 4 个 publish commit（09-08/09-09 成品已在远程），本地 4 个代码
修复 commit + 2 个新提交，其中 publish commit 与远程重复，已用
`rebase --onto origin/main` 丢弃重复项，保留 5 个真实提交（4 代码 + 1 冲突标记
修复），rebase 到最新 origin/main 后 push。净差异 24 文件，481+/59-，`git diff
--check` 干净，48 个离线测试绿，`origin/main` 与本地一致。

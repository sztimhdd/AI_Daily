# Research Contract（V1 编译版）

本文件是从核心知识产权 JSON 编译出的 Codex 执行知识，不是 n8n 运行接口。
运行时只读这份编译知识，不直接解析原始 JSON。

## Provenance（来源追溯）

- `[Atomic] Researcher_Skill.json` → 节点 `Message a model` 的 systemMessage
  `<core_directives>`：证据层级、冲突标注、引用协议、认知工作流。
- `[Atomic] Universal Draft Writing.json` → 节点 `First Draft Writer1` 的
  `<anti_hallucination_and_firewall>`：不得虚构数字、金额与硬件型号。
- `Long-Content-Writing.json` → 增量搜证目标：硬核数据补全、社区原话引用、
  事实交叉验证；“不得虚构、不得情绪化、不得使用比喻”（针对事实字段）。
- `docs/superpowers/specs/2026-08-12-daily-editorial-run-design.md` §Research。

## 硬规则（执行者必须遵守）

1. **围绕关键问题**：研究必须逐条回答选题的 research queries，不做泛泛摘要。
2. **证据层级**：一手来源（官方公告、论文、发布说明）优先于二手转述；
   AIHOT/RSS 摘要属于二手信号，引用时必须保留原始出处链接。
3. **引用协议**：每条重要事实必须带 `[标题](URL)` 形式的来源链接；
   没有链接的事实不得进入 research.md 的“证据”区。
4. **冲突显式标注**：来源互相矛盾时，明确写出冲突双方与各自链接，
   不得抹平分歧；冲突本身记为证据缺口。
5. **不确定处理**：无法充分支持的内容必须三选一——降低断言强度、
   标记为不确定、或直接删除。research.json 中记为 `insufficient`。
6. **零捏造**：不得为了让文章完整而编造数字、引语、来源、实验结果。
   research.md 中出现的所有 URL 必须来自 collect 阶段的证据池。
7. **恢复语义**：研究失败或中断后，从已有 research 产物继续；
   不得因此重新执行 collect，也不得丢弃已引用的证据。
8. **维度控制**：输出维度数量服从选题要求，不注水、不超发。

## V1 产物

- `research.md`：人类可读。结构 = 关键问题 / 证据与来源 / 证据不足 /
  冲突与交叉验证 / 事实边界。
- `research.json`：机器可读。每个问题一条记录，`status ∈ {supported,
  insufficient}`，证据条目含 `title/url/origin/excerpt`。

## 明确不做（V1.5）

- 完整 claims/evidence graph、独立联网深搜、引用质量打分。

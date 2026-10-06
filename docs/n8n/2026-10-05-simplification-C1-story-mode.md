# 精简重构 C1 — 单次 News / Deep 判断

[KNOWN][HIGH] Main draft 15adb281-b77f-4ea1-b7d3-ea71639356d8，49节点；activeVersion仍为 c94debcc-2fe0-438a-a3df-a1d699740c99。本阶段没有接邮件、Writer、配图或发布。

## 设计

[KNOWN][HIGH] 复用孤立旧 Task Master 三件套，重命名为 Story Mode Model / Story Mode Editor / Validate Story Mode Decision，永久节点净增0。旧 Merge Brief→Task Master 与旧 Parse→Drafting Phase(旧Writer65K) 已物理切断。

[KNOWN][HIGH] 输出只有一份 story_direction：mode、working_title、reader_promise、core_judgment、story_path、why_this_mode。News 的 core_judgment 必须为 null；Deep 必须有一个材料支持的鲜明判断。News 直接 stage=story_direction_ready；Deep 进入唯一一次 stage=awaiting_narrative_approval。本步骤不生成补查任务。

[KNOWN][HIGH] Story Mode Editor 只读取有 raw_content 的初研材料、selected_topic、human_instructions、source_links 和初研状态；网页正文是资料而非指令。它不联网、不写稿、不做权限包装。

## 测试

[KNOWN][HIGH] 722 为预期 RED：旧 Parse 接收新 direction 后仍输出两条 legacy creative_blueprint，并沿残留边调用旧 Writer65K；723 因已删除的旧 OpenCodex Local 凭据停止，未成功调用模型或发布。该边随后物理删除，不再重试旧分支。

[COMPUTED][HIGH] 新 validator 本地合同测试 6/6：News 无 thesis、Deep 有判断并等待一次审批、News 强塞 thesis 被拒且保留研究、模型错误保留研究、坏 JSON 保留研究、无正文研究被拒。

[KNOWN][HIGH] 724 第一次原生正例因临时选题探针把 RegExp 当函数调用而停止；725 Topic Survey 成功，产品 C1 尚未运行。探针修正后 726 跑到 Story Mode Editor；初研及 Browser728 成功，但旧 Task Master 模型叶继承的 OpenCodex Local 凭据已不存在。Validator 按设计返回 story_mode_review_required、研究上下文未丢失。

[KNOWN][HIGH] 不新建凭据对象。Story Mode Model 最终复用当前 Deep Editor 已绑定且实例可见的 OpenCodex Hermes Local V2 与 gpt-6.1-sol 配置；这是对旧孤立 Task Master 失效模型叶的替换，Story Mode prompt/合同不变。

[KNOWN][HIGH] 执行729为最终正例，Topic Survey730成功；所选 Cowork 新闻经初研得到9篇正文、46条材料。Story Mode Editor 实际选择 news，理由为材料足以讲清架构变化、使用体验与本机依赖边界，但不足以支撑独立深度判断。core_judgment=null，5步 story_path，stage=story_direction_ready，publication=NOT_PUBLISHED，末端断言 passed=true。

[INFERRED][HIGH] 下一步 C2：Deep 才进入一次 Narrative 确认/修改；News 不等人工 Narrative。两者在方向最终确定后汇入同一个定向补查规划与补充取材接口。

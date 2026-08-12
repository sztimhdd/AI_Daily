# AI_Daily fixture UAT — 2026-08-12

repo: /Users/hai/Projects/Desktop/AI_study/AI_Daily
python: Python 3.14.5
sandbox: /var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC (temp, removed on exit)

$ ai_daily init --root <sandbox> --date 2026-08-12
    initialized run state for 2026-08-12
$ ai_daily collect --mode fixture --aihot-fixture tests/fixtures/aihot_items.json --root <sandbox> --date 2026-08-12
    collect: collected (aihot=14 rss=0)
$ ai_daily candidates --root <sandbox> --date 2026-08-12
    # 选题候选（2026-08-12）

    > 共 3 个候选。回复候选编号即可选定；可附加写作方向，将原样保留。

    ## 候选 1：OpenRouter 推出实时网页搜索基准测试：如何为智能体选择引擎、深度与模型

    - thesis：OpenRouter 发布实时排行榜，系统评测模型、搜索引擎、搜索方法与预算四类配置组合
    - hook：反共识点：大家都盯着模型单价，真正的账单却藏在没人统计的调用次数里。
    - 战略相关性：直接影响企业 AI 预算、采购节奏与供应商选择。
    - 证据缺口：
      - 目前只有 1 个来源报道，缺少独立的第二来源验证。
      - 关键数字缺少官方口径或可复现来源，需要 research 阶段补齐。
    - research queries：
      - openrouter
      - 成本 预算 定价 口径
      - OpenRouter 推出实时网页搜索基准测试：如何为智能体选择引擎、深度与模型
    - 来源：
      - [OpenRouter 推出实时网页搜索基准测试：如何为智能体选择引擎、深度与模型](https://openrouter.ai/blog/announcements/web-search-benchmark)（aihot）

    ## 候选 2：AutoGPT 如何用 AGENTS.md 和技能门控管理 AI 生成的拉取请求

    - thesis：AutoGPT 维护者发现，AI 智能体不会主动阅读文档，因此将指令放在 AGENTS.md 和技能文件中，并置于代码目录旁
    - hook：反共识点：限制 AI 产出的往往不是模型能力，而是团队敢给它开多大的口子。
    - 战略相关性：直接改变工程团队管理 AI 产出的流程、门槛与验收方式。
    - 证据缺口：
      - 目前只有 1 个来源报道，缺少独立的第二来源验证。
      - 关键数字缺少官方口径或可复现来源，需要 research 阶段补齐。
    - research queries：
      - agents.md autogpt
      - 工程实践 流程 门控 验收
      - AutoGPT 如何用 AGENTS.md 和技能门控管理 AI 生成的拉取请求
    - 来源：
      - [AutoGPT 如何用 AGENTS.md 和技能门控管理 AI 生成的拉取请求](https://github.blog/open-source/maintainers/your-contributors-are-ai-first-now-is-your-project)（aihot）

    ## 候选 3：Meta 开源 Muse Glimmer 登陆 OpenRouter

    - thesis：Meta AI 超级智能实验室的首个开放权重模型 Muse Glimmer 已在 OpenRouter 上线
    - hook：反共识点：开放权重不等于能自部署，真正的门槛在权重文件之外。
    - 战略相关性：影响自部署可行性、许可证合规与供应商谈判筹码。
    - 证据缺口：
      - 目前只有 1 个来源报道，缺少独立的第二来源验证。
      - 关键数字缺少官方口径或可复现来源，需要 research 阶段补齐。
    - research queries：
      - glimmer meta muse openrouter
      - 开源 权重 许可证 自部署
      - Meta 开源 Muse Glimmer 登陆 OpenRouter
    - 来源：
      - [Meta 开源 Muse Glimmer 登陆 OpenRouter](https://x.com/OpenRouter/status/2087509478480765218)（aihot）
$ ai_daily choose-topic --fixture tests/fixtures/topic_fixture.json --root <sandbox> --date 2026-08-12
    topic chosen: AI 搜索预算与个人创作者的研究成本 (ai-search-budget-research-cost)
$ ai_daily research --root <sandbox> --date 2026-08-12
    research: generated (/var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/.local/runs/2026-08-12/research.md)
$ ai_daily outline --root <sandbox> --date 2026-08-12
    outline: generated (/var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/.local/runs/2026-08-12/article-outline.md)
$ ai_daily draft --root <sandbox> --date 2026-08-12
    draft: generated (/var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/.local/runs/2026-08-12/article.md)
$ ai_daily cover --root <sandbox> --date 2026-08-12
    cover: skipped (optional): no cover source dir given (cover is optional)
$ ai_daily assemble --root <sandbox> --date 2026-08-12
    assemble: assembled
    - package: /var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/outputs/2026/08/12/ai-search-budget-research-cost
    - final: /var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/articles/2026-08-12-ai-search-budget-research-cost-zh.md
$ ai_daily publish --repo-dir /var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/.local/publish/2026-08-12 --root <sandbox> --date 2026-08-12
    publish: mode=local-only
    - reason: remote unavailable: local-only recovery commit
    - local sha256: e9baa23f94c40370cc0ca59aa9b793e2c974b953ce1c1abc95ac057f39826bb8
    - article: articles/2026-08-12-ai-search-budget-research-cost-zh.md
$ ai_daily status --root <sandbox> --date 2026-08-12
    run: AI-Daily/2026-08-12
    - stage: completed
    - status: completed
    - slug: ai-search-budget-research-cost
    - topic_choice: fixture
    - topic_title: AI 搜索预算与个人创作者的研究成本
    - last_error:
    - updated_at: 2026-08-12T18:05:14-03:00
    counters:
    - collect_runs: 1
    artifacts:
    - aihot-evidence: .local/runs/2026-08-12/aihot-items.json
    - article: .local/runs/2026-08-12/article.md
    - final-article: articles/2026-08-12-ai-search-budget-research-cost-zh.md
    - outline: .local/runs/2026-08-12/article-outline.md
    - package: outputs/2026/08/12/ai-search-budget-research-cost
    - publish-mode: local-only
    - publish-sha256: e9baa23f94c40370cc0ca59aa9b793e2c974b953ce1c1abc95ac057f39826bb8
    - published-article: articles/2026-08-12-ai-search-budget-research-cost-zh.md
    - research: .local/runs/2026-08-12/research.md

## checks
PASS: state.md exists
PASS: stage completed
PASS: publish recorded local-only
PASS: collect_runs incremented exactly once
PASS: no pending error
PASS: package article.md
PASS: package metadata.json
PASS: package sources.md
PASS: final article at articles/<date>-<slug>-zh.md
PASS: final article identical to package copy
PASS: draft has H1
PASS: draft carries source links
PASS: no unresolved image placeholders
PASS: no n8n leftovers
$ ai_daily regenerate-outline --root <sandbox> --date 2026-08-12
    draft rebuilt from edited outline: generated (/var/folders/y4/b7fx08tj715gknw6fdvt0vr80000gn/T/tmp.s5p2peScdC/.local/runs/2026-08-12/article.md)
PASS: outline edit changed the draft
PASS: new section heading present in draft
PASS: collect_runs unchanged after outline edit

## summary
passed: 17
failed: 0
RESULT: PASS

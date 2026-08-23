# ADR 0002: Zhihu CLI as a Default Community-Evidence Source

Status: accepted (code gated behind quota; real-API regression deferred).
Date: 2026-08-24.

## Context

The pipeline's community signals (`community_voices` module, "缺社区原声" /
"缺真实使用反馈" audit gaps) have relied on media relaying community posts
or RSS-derived social URLs. The official Zhihu open-platform CLI (zhihu-lane,
`search_zhihu` / `hot_topics`) gives us real community content with
author, vote counts and comments — currently wired only into the 06
targeted loop as an opportunistic gap-filler.

## Decision

Promote the Zhihu lane from opportunistic to a **default community-evidence
source** in the 03 live research stage, with strict evidence-level rules:

1. **Scope**: one bounded community search per research run for the chosen
   topic (injectable runner, resume-cached, never blocks). The found items
   become OSINT sources (`source_lane="zhihu-cli"`, `community=true`) and a
   one-line `community_voices` enrichment.
2. **Evidence level**: Zhihu content is **community voice / propagation
   evidence** (高赞、经验、声量), never primary fact. Items are normalized
   with author + vote/comment counts; the module note and any downstream use
   must label them as such. They may fill "缺社区原声/缺真实使用反馈" gaps
   and inform narrative voice, but never satisfy a factual evidence
   requirement on their own.
3. **Gates**: the lane must not make a cluster pass the editorial veto or
   kill gates by itself, and must not flip a source set to "纯社区传闻" on
   its own (it appends to real media evidence, never replaces it).
4. **Quota**: `ZHIHU_RESEARCH_BUDGET` is the single knob; the free tier
   stays at 1 search per research run with a persistent query cache.
5. **Real-API regression is deferred** until real-name verification or the
   next quota window; until then all verification is via injectable runners.

## Consequences

- 03 research enriches `community_voices` with real community content,
  directly targeting the "共识有传播证据" gap the audit keeps flagging.
- The 06 targeted loop keeps its budgeted gap-type routing; the two lanes
  share the same evidence-level labeling.
- No change to evidence gates: community voice is additive and labeled.

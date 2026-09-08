# Custom-topic research recovery

## Failure

An editor requested a survey of GPT-6 Astra community use cases. The complete brief became a search query. AIHOT hot-topic matching returned unavailable without searching its item index. Five irrelevant Zhihu snippets remained after failed CDP fetches, and narrative generation stopped with zero fetched sources.

## Implementation plan and contract

1. Preserve the selected title, identity and editorial direction. Compile a separate cached research plan with a subject copied from the brief and bounded, subject-anchored queries.
2. For custom topics, search AIHOT items over seven days; when selected results are empty, query the all pool once. Fetch original links, retaining the search response separately from the event matrix.
3. Reuse the installed Zhihu CLI for one global query and one community query. Planned custom queries do not launch the legacy local-browser search.
4. Bind community cache reuse to both topic and actual query. Preserve CDP recovery hints and propagate explicit research force to source fetching. Discovered URLs are source leads, never editor-pinned story identities.
5. Verify offline query/identity/cache/source-flow regressions, full tests and CLI UAT; then rerun the existing dated research and generate narrative candidates for the editor's decision.

The narrative human gate stays in effect. Discovery summaries are leads, not fetched primary evidence. Search planning failure must remain a research error rather than silently reverting to the original long query.

Custom narrative prompts must honor the requested article form: a community case survey offers alternative ways to organize cases, not an unrelated benchmark audit or a blanket reliability critique. Attribute others' experiences and do not invent personal testing.

Custom candidate pairs may reuse evidence while answering distinct central questions; identical theses still fail. An attributed scene from a source is valid for the legacy `personal_scene` field.

## Verification

- Red/green regressions cover keyword fallback, preserved editorial identity, direction/cache changes, recovery of empty archives, malformed external payloads, empty CDP bodies, original-link identity isolation and candidate evidence reuse.
- 227 relevant tests passed after review corrections. Full suite at the earlier checkpoint ran 762 tests with seven errors, all caused by the missing legacy `[Atomic] Topic_Survey_Skill.json`; no unrelated RSS repair included.
- CLI UAT: 17/17 passed. Source compilation, legacy workflow JSON parsing and `git diff --check` passed.
- Live recovery on 2026-09-08: AIHOT returned 20 keyword matches; repaired Hermes tunnel enabled community original fetching. Final research after removing the unrelated story pin contains 30 source records, 27 fetched, two failed and one verification page. These are records, not 27 independent sources (some URLs repeat across lanes).
- The in-flight research archive was migrated to recovery schema version 1 after verifying its normalized queries, subject identity and nonempty fetched excerpts. A normal `research --mode live` then resumed it without repeating network work.

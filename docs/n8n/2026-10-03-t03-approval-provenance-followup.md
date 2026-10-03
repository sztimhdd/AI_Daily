# AI Daily V3 — T03 approval provenance follow-up

## STATUS

[KNOWN][HIGH] This follow-up fixes the approval-provenance loss found during T03. It does not mark T03 complete and does not connect a Writer.

[KNOWN][HIGH] Shared Dispatch draft version: `fb841db9-b24c-4e05-9bbc-5a373b82bdf1`. Writer V2 draft version: `ee17d426-9bd3-4325-bb3c-8527c93a808c`. Both remain unpublished/inactive.

## ROOT CAUSE

[KNOWN][HIGH] `Parse Editor Feedback` already produced a selected `story_decision.v1` together with `story_approval.v1`, but `Build Shared Dispatch` copied only the older parent context. Targeted research therefore preserved the selected story while losing the approval bundle/decision later needed to prove formal authorization.

[KNOWN][HIGH] Historical Story Approval execution 550 ended at `awaiting_selection`; it is not a formal selected-story receipt. Historical mother execution 557 has the selected story and reassessment result, but its preserved research parent context predates this fix and cannot be retroactively upgraded into formal approval provenance.

## FIX

[KNOWN][HIGH] Ponytail root-cause fix in `Build Shared Dispatch`: reuse the existing `parent_context`, adding only the already-validated `approval_bundle` and selected `decision`. No new schema, table, signature service, or workflow was added.

[KNOWN][HIGH] `Writer Invocation Gate` now resolves formal approval provenance from the existing direct preparation source, its parent context, or reassessment → research work order → parent context. Historical `writing_authorized=false` remains immutable.

## VERIFICATION

[KNOWN][HIGH] Local TDD: the old Shared Dispatch failed the new provenance assertion. The one-line parent-context preservation made it pass. Gate regression likewise failed on nested reassessment provenance before the resolver change and passed afterward.

[COMPUTED][HIGH] Fresh local suite: `node --test tests/n8n/*.test.cjs` → 72 tests, 72 pass, 0 fail.

[KNOWN][HIGH] Native n8n execution 584 exercised `Stage Input → Build Shared Dispatch → Prepare Research Work Order` with a selected News story requiring research. Both nodes returned `parent_context` containing the same `story_approval.v1` and selected `story_decision.v1`; the research work order remained `service_invoked=false`. No Researcher or Writer ran.

[KNOWN][HIGH] Native workflow diffs:
- Shared Dispatch baseline `e621d10c-6bbf-47d2-893f-f9b411d5af05` → `fb841db9-b24c-4e05-9bbc-5a373b82bdf1`: one Code node changed, no graph change.
- Writer baseline `4fa6de79-3527-43ce-a5d9-6b608d9498d0` → `ee17d426-9bd3-4325-bb3c-8527c93a808c`: only Writer Invocation Gate code changed, no graph change.

## REMAINING T03 BLOCKER

[KNOWN][HIGH] No historical execution currently proves a selected formal HITL approval for the 557 story. The current user approval can authorize controlled testing, but must not be relabeled as the historical formal selection.

[KNOWN][HIGH] The platform previously blocked direct submission of a controlled-test authorization payload, so no native positive Gate execution exists yet. The provenance path itself is now preserved and locally accepted by the Gate.

[INFERRED][HIGH] Next T03 step should create the smallest supported fresh call-time decision from preserved provenance and the explicit target language. Do not connect the Chinese Writer until that positive authorization path has native evidence.

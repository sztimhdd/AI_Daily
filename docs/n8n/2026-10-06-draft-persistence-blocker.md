# Ticket 1 — Draft persistence blocked on n8n storage credential

[KNOWN][HIGH] 2026-10-06. Scope: reliable persistence only. No topic collection, research, writers, editor, images, Kit, email sending, publishing, model or credential mutation.

## Required behavior

Persist one bilingual draft bundle after Aggregate Drafts, containing both language draft states, original drafts, edited previews, sources/materials, story direction, human/Narrative context and NOT_PUBLISHED state. One failed language must not overwrite its sibling. Persistence failure must return the original aggregate with an explicit failure receipt and must not rerun upstream writing.

## Baseline and clean stop

[KNOWN][HIGH] Ticket baseline after the source-strength work was Mother xR7fM1ZhxlMTUy0L version 04b0f0c3-81fe-4c35-80b1-bb75c5364f00, equivalent to 3dae201c-7456-478a-ab30-e8492a12e98f. After all storage probes, Mother was restored to dd1aa74b-8cd9-494f-a15d-c3822196327e. Native diff from 84ede00c-6104-4a69-a603-5bab07b6a7b7 to dd1aa74b is empty. Active production version remains c94debcc-2fe0-438a-a3df-a1d699740c99.

## Rejected storage branches

### Existing n8n Data Table

[KNOWN][HIGH] Existing content_ledger was tested first because it was already present. Executions 763–767 used no Writer/Editor/model. A temporary draft_bundle_json column and save/finalize wiring were tested. Even after aligning the legacy Data Table node to the current row/upsert discriminator and current resource-mapper schema, the node returned success/passthrough but external get_data_table_rows returned zero rows. Per the stop-after-two-fixes rule this branch was abandoned. The temporary table column was deleted and workflow changes were rolled back.

### Public GitHub repository

[KNOWN][HIGH] sztimhdd/AI_Daily is public. Draft article storage there would expose review-stage prose, so GitHub is not an acceptable draft store even though image assets already use that repository.

### Google Drive — preferred target, credential blocker

[KNOWN][HIGH] n8n already has credential Google Drive account, id oyXGx0wCxXCS01uO. Node type googleDrive v3 createFromText validates for this design. A private My Drive folder AI Daily Drafts was created through the connected Google Drive account: folder id 1mZl_iGVaWbbqyd5MDa8MIdy9nJ5kkyQf.

[KNOWN][HIGH] Native execution 768 attempted a private JSON draft save. The node returned an error; querying Drive resources through n8n then returned: "The credential Google Drive account needs to be reconnected." MCP exposes no credential refresh/update action, so this cannot be repaired autonomously without changing authentication outside the workflow.

[INFERRED][HIGH] Google Drive remains the preferred implementation after reconnect: Aggregate Drafts -> one create-from-text node -> Finalize Draft Save. The JSON bundle can later be updated/extended by the image/Kit tickets without exposing it publicly.

### Local filesystem

[KNOWN][HIGH] Local storage was tested only after Drive was blocked. 769 verified .n8n is blocked by n8n's file sandbox. 770 used the n8n 2.x default allowed location ~/.n8n-files but the directory does not exist on this instance. Execute Command is unavailable through the instance's node catalog, so creating the directory would require server configuration. Per the stop rule, local storage was abandoned rather than modifying host environment/security settings.

## Failure-preservation evidence

[KNOWN][HIGH] Across the storage probes the persistence finalizer returned the exact Aggregate Drafts payload on save errors. The synthetic fixture deliberately had zh-CN completed and en-US failed; the completed Chinese draft, its original draft, both source materials, English failure status and publication.state=NOT_PUBLISHED remained present. No model or upstream workflow was rerun.

## Minimal user action required

[KNOWN][HIGH] Reconnect the existing n8n credential named Google Drive account. Do not create a new provider, workflow or storage system. After reconnect, rerun one isolated no-model save/readback test, then one injected save-failure fallback test. If both pass, mark Ticket 1 complete and stop before images.

[KNOWN][HIGH] Empty private folder created for the intended target: Google Drive / AI Daily Drafts / 1mZl_iGVaWbbqyd5MDa8MIdy9nJ5kkyQf.

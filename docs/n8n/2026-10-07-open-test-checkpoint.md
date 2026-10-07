# AI Daily n8n open-test checkpoint — 2026-10-07

[KNOWN][HIGH] Scope: restore the real human-in-the-loop draft path and start the first News open test. This checkpoint contains no draft article, private bundle, recipient address, credential, token, or model payload.

## Current Mother

- Workflow: `Long-Content-Writing` (`xR7fM1ZhxlMTUy0L`)
- Current draft after cleanup: `6174b246-c60a-465d-9073-b130edd51395`
- Nodes: 86
- TEMP nodes: 0
- Manual entry restored to `Manual Webhook (OpenClaw) -> Set Discovery Params1`
- Workflow is not activated.
- Draft/package state remains `NOT_PUBLISHED`.

[KNOWN][HIGH] Stage4 permanent wiring before the open test was `37af3ff8-40a5-428d-8a6c-318aad8779c2`. Ticket2 and Ticket3 were already present in that draft: mode-specific visuals, bilingual Kit, private Drive bundle update, and draft notification.

## News open test

[KNOWN][HIGH] Executions 810 and 812 reached the real Topic Selection node with five candidates but failed because the existing Gmail OAuth credential required reconnection.

[KNOWN][HIGH] After the credential was repaired, execution 812's already-generated candidate context was replayed only into the real Topic Selection send-and-wait node. Topic discovery was not rerun.

[KNOWN][HIGH] Execution `815` entered `waiting` at `HITL: Topic Selection1` with no node error. Gmail Sent contains one matching five-topic selection message from this run.

[KNOWN][HIGH] The temporary replay node and temporary Parse Selection binding were then removed. The current Mother draft is back on the normal discovery path while execution 815 remains the independent waiting execution.

## Publication boundary

[KNOWN][HIGH] Current Mother and its actually called Topic Survey, Browser Pilot, News Editor, Deep Editor, and Story Approval workflows contain no public WeChat/LinkedIn publication action. Mother delivery gating and package finalizers retain `publication.state = NOT_PUBLISHED`.

## Next action

[KNOWN][HIGH] Human editor must submit the real topic-selection form from the single message created by execution 815. Do not send another topic-selection message or synthesize the reply.

[INFERRED][HIGH] After that reply, continue execution 815 and inspect the actual research/mode-routing outputs. News must bypass Narrative approval; a Deep classification must stop at the real Narrative approval form.

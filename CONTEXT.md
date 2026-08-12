# Domain Context

## Codex-native workflow

A daily editorial workflow whose orchestrator and operating environment is Codex itself. Codex tasks or automations decide and sequence the work, skills encode repeatable editorial procedures, tools perform bounded external actions, and repository files preserve durable state and deliverables across task runs.

This does **not** mean building a standalone Python or Node application that merely reproduces the old n8n graph and happens to be maintained by Codex.

## Legacy workflow

The n8n workflow preserved at `workflows/reference/公众号选题写稿配图一体化工作流.json`. It is evidence of required behavior and editorial knowledge, not the target runtime architecture.

## Article package

The durable, reviewable output of one editorial run: article body, metadata, sources, and final illustrations stored together under `outputs/YYYY/MM/DD/<article-slug>/`.

## Editorial run

One dated execution of the Codex-native workflow. A run begins from the AIHOT news pool, advances through topic selection, research, narrative selection, writing, illustration, and assembly, and persists its current state outside the conversation.

## Topic candidate

One of exactly three editorially distinct article directions selected from the current AIHOT news pool. A candidate is a proposal for a deep article, not merely a copied news headline.

## Narrative candidate

One of several distinct explanatory theses or storytelling routes for the human-selected topic. Narrative selection occurs only after enough research exists to support meaningful alternatives.

## Human decision point

A durable pause at which Codex presents a versioned decision request and ends the current turn. The run enters an explicit `awaiting_*` state. A later user response—initially in the same Codex conversation, optionally through an email adapter—records one decision and resumes the run. The automation must not remain blocked waiting for a live reply.

The initial workflow has two human decision points: topic selection and narrative selection.

## Decision channel

The transport used to present a human decision request and receive a response. Codex conversation is the primary channel; email may be an adapter and reminder channel. Any future WeChat integration is another adapter, not a separate source of workflow truth. Every channel must reference the same run ID and decision ID.

## GitHub control plane

The durable remote control and coordination layer for Codex Automations. A small versioned state document records whether automation is enabled, the current run and stage, pending decision IDs, and the last successful transition. GitHub Issues, comments, and labels provide a human-visible inbox and audit trail, but do not replace the machine-readable state document.

Every scheduled activation must fetch and validate the GitHub state before doing work. It must stop without side effects when the workflow is disabled, paused, waiting for a human, already complete, or owned by another non-expired execution. Chat history and a local checkout are caches, not the source of truth.

## Illustration workflow validation gap

The first image test verified only that Codex can generate a project-bound raster image without an OpenAI API key. It did not yet verify the complete editorial illustration workflow:

1. Read the article and identify where an illustration materially helps, including the required visual type.
2. Reuse or migrate the rich illustration visual library from the legacy n8n workflow.
3. Generate multiple images, publish them to GitHub, and insert the final Markdown references into the article.

These are deferred validation items. Do not expand the current run retroactively; test them as a separate illustration milestone after the end-to-end editorial flow is complete.

## RSS intelligence pool

The 93 RSS sources are retained as core intellectual-property assets and will be tested with full collection. Code performs fetching, parsing, time filtering, URL/title deduplication, source statistics, and failure recording. Codex reads the compressed intelligence pool for event clustering and editorial judgment; it must not read 93 raw feeds one by one. AIHOT remains a separate curated signal and is merged with the RSS pool before topic selection.

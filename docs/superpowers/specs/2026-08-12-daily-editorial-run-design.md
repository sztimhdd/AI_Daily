# Daily Editorial Run — Specification

## Problem Statement

The legacy n8n workflow produces a daily AI deep-dive article through a long chain of prompts, research tasks, human choices, image generation, and Markdown assembly. The Codex version must preserve the user's editorial intellectual property while making each daily execution independently traceable, editable, resumable, and reviewable. Chat context alone is not sufficient state.

## Solution

Create one independent editorial run instance per calendar day. V1 consumes the AIHOT signal and whatever RSS collection is available, creates three topic candidates, pauses for the user's topic choice, performs targeted research, produces an editable outline and article, optionally creates a cover image, and saves a publishable Markdown package to GitHub. The more elaborate narrative gate, evidence map, full RSS hardening, and multi-image pipeline are staged for V1.5.

Key progress is saved in one daily run state file and a small set of useful artifacts. The current Codex conversation is the human interaction surface; GitHub is the durable place for the final article and important recovery files. V1 must pause for topic choice and can continue from research or draft artifacts after a failure.

## User Stories

1. As the editor, I want one independent run per day, so that daily work never mixes across dates.
2. As the editor, I want each run to have a stable run ID, so that files, decisions, images, and GitHub updates remain connected.
3. As the editor, I want the run to use AIHOT and available RSS enrichment when practical, so that curated signals can be supplemented without blocking daily work.
4. As the editor, I want any RSS collection to run in code, so that the model does not read raw feeds one by one.
5. As the editor, I want an RSS failure not to stop the day, so that incomplete enrichment does not discard the AIHOT workflow.
6. As the editor, I want duplicate stories clustered before selection, so that repeated coverage is not mistaken for separate events.
7. As the editor, I want exactly three topic candidates, so that I can make a focused choice.
8. As the editor, I want each topic to include its thesis, hook, evidence gaps, research queries, and strategic relevance to technology or architecture decisions, so that the choice is editorially meaningful.
9. As the editor, I want to choose a topic in the current Codex conversation, so that no separate interface is required for the first implementation.
10. As the editor, I want my topic choice and extra direction preserved verbatim, so that the workflow respects my intent.
11. As the editor, I want research to answer the key questions behind the selected topic, so that the draft has enough support to be written.
12. As the editor, I want important claims linked to sources and marked uncertain when support is incomplete, so that unsupported assertions do not enter the article silently.
13. As the editor, I want the useful research notes saved with the run, so that I can inspect or reuse them when a draft needs revision.
14. As the editor, I want to edit the outline before drafting, so that I can change structure without restarting research.
15. As the editor, I want a fact-backed first draft, so that writing quality does not hide evidence gaps.
16. As the editor, I want the final draft to inherit my author voice and anti-AI style rules, so that it reads as my publication rather than generic model output.
17. As the editor, I want a useful cover image when appropriate, so that the article can be published without blocking on a full illustration system.
18. As the editor, I want a failed research or draft stage to resume from its last useful artifact, so that completed work is not repeated.
19. As the editor, I want the final Markdown and key artifacts saved to GitHub, so that the article is retrievable outside the chat.

## Implementation Decisions

- The unit of execution is one daily run instance with a stable date-based ID such as `AI-Daily/YYYY-MM-DD`.
- Every run has a durable state record with current stage, status, selected decisions, artifact references, and last error.
- The V1 stage sequence is: `collect → topic_choice → research → outline → draft → optional_cover → assembly → completed`.
- Topic choice is the one mandatory human gate in V1. Narrative guidance is folded into research and outline; a separate narrative choice is a V1.5 option, not a daily requirement.
- AIHOT is the required discovery input. RSS collection is opportunistic in V1: use the full pool when code execution makes it cheap, but RSS failure or incomplete coverage must not block the day.
- The 93 RSS sources remain intellectual-property assets in a source catalog. V1 does not require a complete catalog, health dashboard, or hard all-source success condition.
- The original n8n workflow and four atomic JSON workflows are the user's core intellectual-property sources. Runtime execution does not directly import these JSON files; Codex uses compiled knowledge derived from them with source traceability.
- V1 keeps a compact artifact set: `state.md`, `topic-candidates.md`, `research.md`, `article-outline.md`, `article.md`, and optional `images/cover.png`.
- Research must cite or link important evidence and state uncertainty, but V1 does not require a fully normalized claims/evidence graph.
- Writing retains the evidence-backed draft, author voice, anti-AI style, and Markdown polish rules from the core IP. The final writing pass must use the compiled `remove-ai-slop` style contract or an explicitly equivalent check.
- Topic candidates must state why the event matters to enterprise strategy, architecture, engineering practice, or another concrete reader decision; popularity alone is insufficient.
- V1 image work is optional cover generation. Article-driven visual planning, the legacy visual library, multiple images, GitHub image publication, and automatic Markdown insertion are V1.5.
- GitHub stores the final article and key recovery artifacts. Email, WeChat, scheduled Automation, and a stronger remote control plane are future adapters.
- A failed research or draft stage must not discard completed work; resume from the latest useful artifact.

## Testing Decisions

- Test observable run behavior, not prompt wording or n8n node names.
- Use one real end-to-end daily run as the primary acceptance test.
- Verify that a run creates exactly one stable instance for a date and does not mix another date's artifacts.
- Verify AIHOT produces three meaningful topic candidates and the run stops for the user's choice.
- Verify RSS collection, when attempted, can contribute items without blocking the AIHOT path.
- Verify that without a topic choice the run cannot enter research.
- Verify the selected topic and research/draft artifacts survive a failed continuation.
- Verify editing the outline changes the draft structure without redoing collection or research.
- Verify unsupported claims are marked as uncertain or omitted.
- Verify optional cover generation does not block final Markdown assembly.
- Verify the run can produce publishable Markdown without a cover and writes it to GitHub when available.
- Verify the final article path follows the established convention `articles/YYYY-MM-DD-{slug}-zh.md`, or records an explicit run-directory mapping when the package layout is used.
- Verify the final Markdown and key artifacts are written to GitHub or are clearly reported as local-only when GitHub is unavailable.

## Out of Scope

- Creating or configuring a recurring Codex Automation.
- Email, WeChat, or other external human-decision adapters.
- Multiple concurrent runs, distributed leases, and a database-backed state machine.
- Automatic WeChat/公众号 publishing.
- A complete historical RSS database or search warehouse.
- Reproducing every n8n provider, Gemini-specific tool instruction, Base64 path, Google Drive step, or temporary binary implementation.
- Treating raw prompt text as the runtime interface; prompts must be compiled into stage knowledge, contracts, and checks.

## Further Notes

The first implementation should proceed as short V1 slices: AIHOT topic gate, optional RSS enrichment, research-to-draft with author voice and the compiled `remove-ai-slop` contract, editable outline, and GitHub Markdown delivery. V1.5 can add the separate narrative gate, normalized evidence map, full RSS collection reporting, article-driven illustration planning, the legacy visual library, multiple image generation, GitHub image publication, and automatic Markdown insertion. The earlier conversation tested both human gates, but V1 intentionally requires only the topic gate; the V1.5 illustration gaps remain intentionally deferred.

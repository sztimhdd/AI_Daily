# Daily English Edition Delivery Loop

**Status:** ready-for-agent

## Problem Statement

The English edition can be produced through several individual commands, but it has no daily delivery loop. An editor or automation must remember their order, inspect failures by hand, and manually push the resulting English package to GitHub. The existing fixture UAT verifies only the Chinese pipeline, so a green result does not prove a usable English article, LinkedIn kit, images, or remote package were delivered.

## Solution

Add one resumable English delivery loop that uses the existing English writing, claim review, illustration, kit, assembly, and Git transport seams. It creates a durable delivery summary and makes a best effort to produce and publish a complete package. Editorial-risk signals and enrichment failures are visible in the summary and package metadata, but do not discard a usable article. Only malformed/empty English copy, an identity mismatch, or a required filesystem/package failure stops the loop.

## User Stories

1. As an editor, I can run one command to produce today's English edition without remembering a sequence of subcommands.
2. As an editor, I receive a usable English article even if image generation or LinkedIn-kit generation is unavailable.
3. As an editor, I can see whether each delivery component was generated, resumed, degraded, failed, or published.
4. As an editor, I can re-run the command after a transient failure without paying again for an already generated article or image.
5. As an editor, I receive a GitHub package containing the English article, sources, metadata, accepted images, and kit when ambient Git credentials and the configured target repository are available.
6. As an editor, I can distinguish a factual-review warning from a broken or missing article instead of losing the day's edition to a soft review verdict.
7. As a maintainer, I can run an offline fixture E2E that proves the English delivery order and its degradation/recovery semantics.
8. As a maintainer, I can inspect one machine-readable summary rather than infer the state from multiple command transcripts.

## Implementation Decisions

- Add a single English-delivery orchestrator beside the existing pipeline orchestration. It invokes the existing stage seams in this order: English draft, claim check, illustration, LinkedIn kit, English assembly, then English publishing.
- Add a `run-en` CLI entry point for that orchestrator. Existing individual commands remain available for editorial intervention and recovery.
- The orchestrator persists a delivery summary in the dated run work area and records it in durable state. The summary includes a status and reason for draft, claim check, images, kit, assembly, and publication.
- Claim-check verdicts are recorded in the summary and package metadata. A `mismatch`, `unsupported`, or unavailable review is an editorial warning; it does not block assembly. The existing English draft's hard input checks remain unchanged.
- Illustration and kit remain best-effort. Their failure results in explicit `degraded` delivery information and a still-assembled article package.
- Add an English publisher that selects the English title slug and English final article path, copies the complete English package including the kit and images, and uses the existing Git transport's verified remote-read behavior for the article. Remote failure is reported as local-only/pending, not fabricated as success.
- Avoid a scheduler in this iteration. A Codex scheduled session can invoke `run-en` once the command is proven by repeated daily runs.

## Testing Decisions

- Add observable offline tests at the orchestrator seam using existing injectable writing-model, image-model, and Git transport boundaries.
- Add a fixture English E2E command/script that checks the final package, LinkedIn kit, image degradation behavior, delivery summary, and English publication path.
- Test resume after each external boundary separately: draft, image, kit, and publication.
- Retain focused tests for the existing commands; tests should assert durable artifacts and statuses rather than internal call order alone.
- Run a real topic through `run-en` after offline green. It may use the approved Vertex image route and ambient Git credentials; remote publication is verified from the served files.

## Out of Scope

- Automatic posting to LinkedIn.
- A new scheduler, notification channel, or dashboard.
- Making literary quality or factual-risk labels hard publication blockers.
- Rewriting the Chinese pipeline or changing the topic/narrative human gates.
- Creative retry loops for images.

## Further Notes

- "Delivered" means that a durable local English package exists; GitHub publication is separately represented as remote, local-only, or failed.
- A `degraded` package is intentional evidence for iteration, not a silent success state.

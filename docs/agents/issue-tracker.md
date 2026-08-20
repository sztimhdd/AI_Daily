# Issue tracker: Local Markdown

Issues and specs for this repository live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`.
- The spec is `.scratch/<feature-slug>/spec.md`.
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`; never use one combined ticket file.
- Triage state is recorded as a `Status:` line near the top of each issue file. See `triage-labels.md` for the role strings.
- Comments and conversation history append under a `## Comments` heading.

## Publishing and reading

When a skill says to publish to the issue tracker, create the appropriate file under `.scratch/<feature-slug>/`.

When a skill says to fetch a ticket, read its referenced local Markdown file.

## Wayfinding operations

- Map: `.scratch/<effort>/map.md`, containing notes, decisions so far, and remaining uncertainty.
- Child ticket: `.scratch/<effort>/issues/NN-<slug>.md`, with `Type:`, `Status:`, and `Blocked by:` near the top.
- A ticket is unblocked when each named blocker is `resolved`.
- The frontier is the lowest-numbered open, unblocked, unclaimed ticket.
- Claim work by setting `Status: claimed` before starting.
- Resolve work by adding `## Answer`, setting `Status: resolved`, and linking the finding from the map.

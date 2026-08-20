# Domain docs

## Before exploring

Read the root `CONTEXT.md` and relevant decisions in `docs/adr/`. If a `CONTEXT-MAP.md` is later introduced, follow it to the context-specific documentation instead.

If a referenced domain document does not exist, proceed silently. Domain-modeling work creates missing documentation only when a term or decision has been resolved.

## Layout

AI_Daily is a single-context repository:

```
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

## Vocabulary and decisions

Use the terms defined in `CONTEXT.md` in tickets, hypotheses, tests, and implementation decisions. When an output conflicts with an existing ADR, surface the conflict explicitly rather than silently overriding it.

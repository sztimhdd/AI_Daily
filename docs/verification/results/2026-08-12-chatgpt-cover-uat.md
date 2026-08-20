# Real ChatGPT Web cover UAT — 2026-08-12 (session 20260812-201513)

Scope: external UAT item #4 (real ChatGPT cover export + V1 adoption)
from `docs/verification/README.md`, against the 2026-08-14 fixture
article `ai-search-budget-research-cost`.

## Verdict

**UNAVAILABLE — no usable logged-in ChatGPT Web session exists on any
reachable browser surface. Item #4 was NOT executed: no generation, no
download, no adoption. This is not a success result. Article
completion is NOT blocked — the cover is optional in V1.**

## Surface availability matrix

| Surface | Status | Evidence (local-only session dir) |
|---|---|---|
| In-app browser (browser-client) | unavailable | direct probe: `setupBrowserRuntime()` → "Browser use requires privileged node_repl capabilities"; `mcp__node_repl__js` not exposed in the session |
| Chrome | not running; single profile `Default`; sandboxed profile reuse → chatgpt.com logged out | `recon-result.json`, `shot-01-landing.png` |
| Brave | running (PID 1267) but no `--remote-debugging-port`, live tabs not inspectable; sandboxed profile reuse → chatgpt.com logged out | `recon-brave-result.json`, `shot-02-brave-landing.png` |
| Edge / Safari / others | not running (Edge profile = 4K stub) | `pgrep` checks |

Logged-out DOM evidence (both browsers): the rendered body contained
"Log in to get answers based on saved chats, plus create images and
upload files." plus "Log in" (×2) and "Sign up for free" (×1); no
profile menu; guest composer present. Per the UAT brief: stop, never
force a login.

## What was NOT reached (blocked on session availability)

- Fixed-prompt cover generation in ChatGPT Web. The prompt itself is
  documented in the session dir (`cover-prompt.md`), derived from the
  legacy Image Adder archetype contract, Type A Analyst infographic.
- Download identification: before/after Downloads listings were
  captured; no new file appeared (`downloads-before.txt` vs
  `downloads-after.txt` differ only in parent-dir mtime and the
  appended date line).
- File validation (format/size/dimensions) and sha256 of a real
  export.
- `cli cover --source-dir` adoption into a disposable sandbox root.

## Pipeline impact

None. `python3 -m unittest discover tests` → 208/208 OK. The published
no-cover package `outputs/2026/08/14/ai-search-budget-research-cost/`
is unchanged (`metadata.json` has `has_cover: false`). No product
code, tracked docs, or legacy outputs were modified by this attempt.

## Evidence inventory

All evidence lives in the local-only, uncommitted session directory
`.local/uat/20260812-201513-chatgpt-cover/`. Screenshots stay there
and are deliberately not committed or embedded here; no credentials
were read, printed, or stored.

- `report.md` — full session report this document summarizes
- `cover-prompt.md` — derived fixed prompt + derivation notes
- `recon-result.json` / `shot-01-landing.png` — Chrome profile probe
- `recon-brave-result.json` / `shot-02-brave-landing.png` — Brave
  profile probe
- `downloads-before.txt` / `downloads-after.txt` — Downloads
  baseline/delta
- `chrome-profile/`, `brave-profile/` — sandboxed profile copies
  (disposable)
- `recon.mjs` / `recon-brave.mjs` — probe scripts (Playwright 1.62.1)

## Notes / deviations

- The `apply_patch` tool was nonfunctional during the UAT session
  (patch body arrived empty); evidence files were written via shell
  heredoc instead.
- The first Brave launch attempt hit Chromium singleton handoff
  ("Opening in existing browser session") because the profile copy
  carried the running Brave's `Singleton*` symlinks; it may have
  opened one harmless `about:blank` tab in the user's live Brave.
  Fixed by moving `Singleton*` out of the copy (recoverable `mv` to
  `./trash/`); the second launch was isolated.
- Cookie/localStorage/password/credential files were never read or
  printed; session state was observed only via URL + rendered DOM.

## To re-run when a session exists

1. The user logs into chatgpt.com in any browser (or exposes a CDP
   port on the running browser), or
2. The user exports a cover from the ChatGPT desktop app and drops the
   `ChatGPT Image*` file into a directory, then:
   `PYTHONPATH=src python3 -m ai_daily.cli cover --date <d> --source-dir <dir>`
   against a disposable `--root`.

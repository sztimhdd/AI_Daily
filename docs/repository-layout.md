# Repository layout

The repository separates active development, deliverables, local runtime state, and historical evidence.

| Path | Purpose | Versioned |
| --- | --- | --- |
| `workflows/reference/` | Authoritative legacy behavior reference | Yes |
| `src/` | Codex-native implementation | Yes |
| `tests/` | Deterministic automated checks | Yes |
| `outputs/` | Final article packages and final illustrations | Yes |
| `docs/` | Architecture and operations | Yes |
| `archive/legacy-content/` | Existing articles, images, and drafts | Yes, read-only |
| `archive/legacy-n8n/` | Retired workflows, assets, and infrastructure | Yes, read-only |
| `archive/legacy-tools/` | Retired, redacted utilities | Yes, read-only |
| `.local/` | Secrets, logs, caches, raw responses, temporary files | No |

Do not add new files to `archive/` except during an explicit archival operation. Do not use archived files as mutable application inputs.

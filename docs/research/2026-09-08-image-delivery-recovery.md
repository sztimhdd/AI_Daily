# Image delivery recovery

Keep `gemini-3.1-flash-image`; route Vertex requests through `global` instead
of the previous hard-coded `us-central1` endpoint. No provider fallback.

Delivery contract: missing planned images or a failed kit/publication makes
delivery `partial`, not `delivered`. Retain the assembled text. The workday
scheduler resumes `run-en` directly for partial deliveries, without repeating
research or narrative selection. Existing valid images are reused.

Historical `delivered` records are not automatically rewritten. Inspect their
image manifests before explicitly resuming them. This change does not establish
live model availability; validate one real request before claiming that.

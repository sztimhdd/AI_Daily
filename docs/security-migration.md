# Security migration notes

The retired local publisher contained two hard-coded access tokens. Its archived source now reads `PUBLISH_API_TOKEN` and `WECHATSYNC_TOKEN` from the environment. The authoritative and archived n8n workflows contained an Apify token literal; all detected occurrences in the rebuilt working tree were replaced with `${APIFY_API_TOKEN}`.

Two expired Google credential files from the former outer workspace were intentionally deleted rather than archived. They were not found by filename in the fetched Git history. No secret value is recorded in this document.

During publication preparation on 2026-08-12 a second sweep found one
embedded Event Registry (newsapi.ai) `apiKey` literal in the archived
n8n exports (`archive/legacy-n8n/workflows/2026-08-12/`) and in
`workflows/reference/公众号选题写稿配图一体化工作流.json`. The single
occurrence in each file was replaced with `${EVENT_REGISTRY_API_KEY}`
before the baseline commit was pushed, following the same convention as
the Apify token above. Workflow structure is otherwise unchanged. The
key value must still be treated as exposed and rotated.

Git history was not rewritten. Any credential ever committed elsewhere must still be treated as exposed even if it is expired or no longer present in the current tree. Future credentials belong in environment variables or ignored `.local/secrets/` files.

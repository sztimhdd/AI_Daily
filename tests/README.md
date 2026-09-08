# Tests

Mirror `src/ai_daily/` one-to-one (`test_<module>.py`), plus
`test_pipeline_e2e.py` for black-box CLI chains. Everything runs
offline: live paths are exercised with injected fetchers/transports,
never real network calls, paid APIs, or publication endpoints.

```bash
python3 scripts/test.py                      # default: 48 tests, network/process guard
python3 scripts/test.py tests.test_fetch     # targeted offline module
# python3 scripts/test.py --full             # manual only, same guard
scripts/uat_cli.sh                            # deterministic fixture UAT
```

Never run bare discovery: some legacy tests fail to inject their live fetchers.
The guarded runner fails those paths before launching browsers or reaching APIs.
Browser smoke tests are opt-in via `scripts/test_browser.py` in an installed
Playwright environment: headless, isolated, no CDP/profile and no live sites.

## Fixtures

- `fixtures/aihot_items.json` — 14-item AIHOT payload (`{"items": [...]}`).
- `fixtures/topic_fixture.json` — complete topic-choice fixture bypass.
- `fixtures/feeds/` — RSS fixtures: `source_a.xml`, `source_b.xml`,
  `source_invalid.xml`, `source_dc.xml` (dc:date namespace).

## Naming

Name tests after observable behavior (`test_all_rss_fail_is_nonblocking`),
not after implementation internals. Every stage covers its success path
and at least one failure path.

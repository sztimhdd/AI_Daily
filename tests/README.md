# Tests

Mirror `src/ai_daily/` one-to-one (`test_<module>.py`), plus
`test_pipeline_e2e.py` for black-box CLI chains. Everything runs
offline: live paths are exercised with injected fetchers/transports,
never real network calls, paid APIs, or publication endpoints.

```bash
python3 -m unittest discover tests            # full suite
python3 -m unittest tests.test_pipeline_e2e   # E2E subset
scripts/uat_cli.sh                            # deterministic fixture UAT
```

## Fixtures

- `fixtures/aihot_items.json` — 14-item AIHOT payload (`{"items": [...]}`).
- `fixtures/topic_fixture.json` — complete topic-choice fixture bypass.
- `fixtures/feeds/` — RSS fixtures: `source_a.xml`, `source_b.xml`,
  `source_invalid.xml`, `source_dc.xml` (dc:date namespace).

## Naming

Name tests after observable behavior (`test_all_rss_fail_is_nonblocking`),
not after implementation internals. Every stage covers its success path
and at least one failure path.

# Daily English Edition Delivery Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a resumable daily English package, LinkedIn kit, images when available, and an honest GitHub result through one CLI command.

**Architecture:** A small English delivery orchestrator composes existing draft, review, image, kit, assembly, and Git transport seams. It emits a durable summary and uses degradation rather than editorial soft gates.

**Tech Stack:** Python standard library, unittest, Bash fixture UAT.

**Spec:** `.scratch/daily-en-delivery/spec.md`

## Global Constraints

- Preserve the Chinese `run` command.
- Keep claim review, images, and kit as observable signals rather than delivery blockers.
- Do not log credentials or stage primary-worktree files.
- Use the existing WebP, English-slug, Vertex ADC, and ambient Git conventions.

---

### Task 1: English delivery summary and orchestrator

**Files:**

- Create: `src/ai_daily/delivery_en.py`
- Modify: `src/ai_daily/pipeline.py`
- Test: `tests/test_delivery_en.py`

**Interfaces:**

- Produces `run_delivery_en(run_paths, *, codex_runner=None, gemini_runner=None, force=False) -> dict`.
- Persists `delivery-en.json` with `draft`, `claim_check`, `images`, `linkedin_kit`, `assembly`, and `publication` entries.

- [ ] Write the failing tests.

```python
def test_delivery_keeps_article_when_enrichments_are_unavailable(self):
    result = delivery_en.run_delivery_en(self.rp, codex_runner=self.runner)
    self.assertEqual(result["status"], "delivered")
    self.assertEqual(result["images"]["status"], "degraded")
    self.assertEqual(result["linkedin_kit"]["status"], "degraded")
    self.assertTrue((self.rp.work_dir / "delivery-en.json").is_file())

def test_delivery_stops_when_draft_is_unavailable(self):
    result = delivery_en.run_delivery_en(self.rp, codex_runner=lambda _: {"status": "unavailable", "reason": "down"})
    self.assertEqual(result["status"], "failed")
    self.assertEqual(result["assembly"]["status"], "skipped")
```

- [ ] Run `PYTHONPATH=src python3 -m unittest tests.test_delivery_en -q`; expect the missing-module failure.
- [ ] Implement the smallest orchestration over `draft_en.run`, `claim_check.run`, `visuals.run_illustrate`, `linkedin.run`, and `assemble_en.run`; persist the summary after every terminal outcome.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.test_delivery_en -q && PYTHONPATH=src python3 -m unittest discover -s tests -q`; expect PASS.
- [ ] Commit with `git add src/ai_daily/delivery_en.py src/ai_daily/pipeline.py tests/test_delivery_en.py && git commit -m "feat: add resumable English delivery loop"`.

### Task 2: English package publisher

**Files:**

- Modify: `src/ai_daily/publish.py`
- Modify: `src/ai_daily/delivery_en.py`
- Test: `tests/test_publish.py`
- Test: `tests/test_delivery_en.py`

**Interfaces:**

- Produces `publish_en(run_paths, repo_dir, transport=None, **kwargs) -> PublishResult`.
- The English final article is the returned `published_relpath`; payload includes the English package, kit, and WebP files.

- [ ] Write the failing test.

```python
def test_publish_en_uses_english_paths_and_full_package(self):
    result = publish.publish_en(self.rp, self.publish_root, transport=FakeRemote())
    self.assertTrue(result.published_relpath.endswith("-en.md"))
    self.assertTrue((self.publish_root / self.package_rel / "linkedin-kit.md").is_file())
    self.assertTrue((self.publish_root / self.package_rel / "images" / "01.webp").is_file())
```

- [ ] Run `PYTHONPATH=src python3 -m unittest tests.test_publish.PublishEnTests -q`; expect the missing-function failure.
- [ ] Extract the existing payload/publish logic behind a final-path and package-path selector, then make `publish_en` select `en_slug` and `final_article_en_path` without changing Chinese behavior.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.test_publish tests.test_delivery_en -q && PYTHONPATH=src python3 -m unittest discover -s tests -q`; expect PASS.
- [ ] Commit with `git add src/ai_daily/publish.py src/ai_daily/delivery_en.py tests/test_publish.py tests/test_delivery_en.py && git commit -m "feat: publish complete English delivery packages"`.

### Task 3: `run-en` CLI and fixture E2E

**Files:**

- Modify: `src/ai_daily/cli.py`
- Create: `scripts/uat_en_cli.sh`
- Test: `tests/test_cli.py`
- Test: `tests/test_pipeline_e2e.py`

**Interfaces:**

- Produces `ai_daily run-en`; it prints the durable summary path and exits zero for delivered/degraded output, one for hard draft/package failure.

- [ ] Write the failing CLI tests.

```python
def test_run_en_prints_summary(self):
    with mock.patch.object(cli.pipeline, "run_delivery_en", return_value={"status": "delivered", "summary": pathlib.Path("delivery-en.json")}):
        self.assertEqual(cli.main(["run-en", "--root", str(self.root)]), 0)

def test_run_en_returns_one_for_hard_failure(self):
    with mock.patch.object(cli.pipeline, "run_delivery_en", return_value={"status": "failed", "reason": "draft unavailable"}):
        self.assertEqual(cli.main(["run-en", "--root", str(self.root)]), 1)
```

- [ ] Run the focused test; expect `run-en` to be unknown.
- [ ] Add CLI arguments for the isolated publication repository, remote URL, branch, and force; delegate only to `pipeline.run_delivery_en`.
- [ ] Add an offline UAT that asserts article, sources, metadata, kit, English final article, local-only publishing, degradation, and rerun resume.
- [ ] Run `scripts/uat_en_cli.sh && scripts/uat_cli.sh && PYTHONPATH=src python3 -m unittest discover -s tests -q && git diff --check`; expect all PASS.
- [ ] Commit with `git add src/ai_daily/cli.py scripts/uat_en_cli.sh tests/test_cli.py tests/test_pipeline_e2e.py && git commit -m "test: cover English daily delivery with fixture UAT"`.

### Task 4: Real daily trial and feedback ledger

**Files:**

- Create: `docs/verification/results/<date>-english-delivery-trial.md`
- Create: `outputs/YYYY/MM/DD/<english-slug>/`
- Create: `articles/<date>-<english-slug>-en.md`

**Interfaces:**

- Consumes the completed `run-en` command and a fresh selected narrative.
- Produces a locally durable package, optional remote verification, and a short feedback ledger.

- [ ] Complete the normal research and narrative stages for a fresh topic.
- [ ] Run `PYTHONPATH=src python3 -m ai_daily.cli run-en --root . --date <date> --repo-dir <isolated-publish-repo> --remote-url <repository-url>`.
- [ ] Verify the remote article, kit, metadata, and every listed WebP with raw GitHub responses when a push succeeds.
- [ ] Record editorial observations, operational degradation, cost, and rerun behavior without adding new gates.
- [ ] Commit only the generated package, final English article, and verification record.

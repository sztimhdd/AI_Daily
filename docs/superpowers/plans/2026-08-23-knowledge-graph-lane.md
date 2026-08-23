# Knowledge-Graph Background Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a non-blocking knowledge-graph background lane so the AI_Daily pipeline enriches research, narrative and English writing with deep technical background from the omnigraph LightRAG knowledge graph, without weakening the evidence gates.

**Architecture:** A new `knowledge.py` module speaks MCP JSON-RPC over HTTP to the omnigraph endpoint (`http://47.103.73.20:8767/mcp`, server `omnigraph-kg`). The research stage (live path) fetches a background digest for the chosen topic and persists it as a separate artifact (`kg-background.json` / `kg-background.md`) — explicitly labeled **secondary/background**, never merged into `initial-osint.json` modules so kill/veto/sufficiency gates are untouched. Narrative and English-writing prompts inject the digest as a "mechanism primer" (background only, not citable event evidence). Everything is injectable and degrades to `unavailable`/`degraded` on network failure — never raises.

**Tech Stack:** Python stdlib (`urllib.request`, `json`, `sse` parsing), existing unittest suite, existing CLI (`src/ai_daily/cli.py`), existing research stage (`src/ai_daily/research.py`), existing narrative/writing prompts (`src/ai_daily/narrative.py`, `src/ai_daily/draft_en.py`).

**Spec:** Ad-hoc design agreed in conversation (2026-08-23): trial of the omnigraph MCP (works: `fts_search` fast, `kg_search` job-based 1–4 min, `kg_poll`), integration decision = separate artifact + prompt injection, evidence discipline = KG is secondary background only.

## Global Constraints

- Never raise on KG network failure; return `{"status": "unavailable"/"degraded", ...}`.
- KG content must be labeled secondary/background in every artifact and prompt; it must never satisfy a kill/veto/sufficiency gate.
- Do not mutate `initial-osint.json`'s `modules` list or its evidence gates.
- Credentials: none; never log the endpoint body beyond bounded excerpts.
- Follow existing injection patterns: every network-shaped dependency gets an injectable parameter (like `http_fetcher`/`codex_runner`).
- All new tests live in `tests/test_knowledge.py` and additions to `tests/test_research.py`, `tests/test_narrative.py`, `tests/test_draft_en.py`, `tests/test_cli.py`.

---

### Task 1: `knowledge.py` MCP client

**Files:**
- Create: `src/ai_daily/knowledge.py`
- Test: `tests/test_knowledge.py`

**Interfaces:**
- Produces: `KG_ENDPOINT`, `fetch_background(topic: dict, client=None, timeout: float = 75.0) -> dict`, `MCPClient` class with `fts_search(query, limit=10, lang="zh-CN") -> str`, `kg_search(query) -> dict`, `kg_poll(job_id) -> str`, and `synthesize(query, max_polls=8, poll_interval=30) -> dict`.

- [ ] **Step 1: Write the failing tests** (handshake, fts, kg job/poll, degraded, never-raise)

```python
# tests/test_knowledge.py
import json, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ai_daily import knowledge


def _sse(data):
    return f"event: message\ndata: {json.dumps(data)}\n\n".encode()


class FakeHTTP:
    """Scripted MCP-over-HTTP transport: session header + SSE bodies."""
    def __init__(self, scripts):
        self.scripts = scripts  # list of callables/values
        self.calls = []

    def __call__(self, url, payload, headers=None, timeout=75):
        self.calls.append((url, payload, dict(headers or {})))
        step = self.scripts[len(self.calls) - 1] if len(self.calls) - 1 < len(self.scripts) else self.scripts[-1]
        if callable(step):
            return step(url, payload, headers, timeout)
        status, hdrs, body = step
        return status, hdrs, body


class KnowledgeClientTests(unittest.TestCase):
    def test_fts_search_returns_text(self):
        script = [
            (200, {"Mcp-Session-Id": "s1"}, _sse({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}})),
            (200, {}, _sse({"jsonrpc": "2.0", "id": 100, "result": {"content": [{"type": "text", "text": "draft model 机制"}]}})),
        ]
        http = FakeHTTP(script)
        client = knowledge.MCPClient("http://x/mcp", http=http)
        self.assertEqual(client.fts_search("speculative decoding"), "draft model 机制")

    def test_kg_search_returns_job_id_when_running(self):
        script = [
            (200, {"Mcp-Session-Id": "s1"}, _sse({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}})),
            (200, {}, _sse({"jsonrpc": "2.0", "id": 100, "result": {"content": [{"type": "text", "text": "[kg-running] job_id=abc123"}]}})),
        ]
        client = knowledge.MCPClient("http://x/mcp", http=FakeHTTP(script))
        self.assertEqual(client.kg_search("q")["job_id"], "abc123")

    def test_kg_poll_returns_report(self):
        script = [
            (200, {"Mcp-Session-Id": "s1"}, _sse({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}})),
            (200, {}, _sse({"jsonrpc": "2.0", "id": 100, "result": {"content": [{"type": "text", "text": "## Report\nFull synthesis."}]}})),
        ]
        client = knowledge.MCPClient("http://x/mcp", http=FakeHTTP(script))
        self.assertEqual(client.kg_poll("abc123"), "## Report\nFull synthesis.")

    def test_fetch_background_degrades_on_network_error(self):
        def boom(url, payload, headers, timeout):
            raise OSError("connection refused")
        result = knowledge.fetch_background(
            {"title": "T", "direction": ""}, client=knowledge.MCPClient("http://x/mcp", http=FakeHTTP([boom]))
        )
        self.assertEqual(result["status"], "degraded")
        self.assertIn("refused", result["reason"])
```

- [ ] **Step 2: Run to verify it fails** — `PYTHONPATH=src python3 -m unittest tests.test_knowledge -v` → FAIL (module missing).

- [ ] **Step 3: Implement `src/ai_daily/knowledge.py`**

```python
"""Knowledge-graph background lane (omnigraph LightRAG over MCP).

Secondary/background only: enrich understanding of mechanisms, terms and
best practices.  Never primary evidence; never feeds evidence gates.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

KG_ENDPOINT = "http://47.103.73.20:8767/mcp"
KG_BACKGROUND_JSON = "kg-background.json"
KG_BACKGROUND_MD = "kg-background.md"
_PROTOCOL = "2025-03-26"


def _default_post(url, payload, headers=None, timeout=75.0):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream",
                 **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")


def _parse_sse(body: str) -> dict:
    for line in body.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(body)


class KnowledgeError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, endpoint: str = KG_ENDPOINT, http=None):
        self.endpoint = endpoint
        self._post = http or _default_post
        self._session = None

    def _rpc(self, method: str, params: dict) -> dict:
        headers = {}
        if self._session:
            headers["Mcp-Session-Id"] = self._session
        status, hdrs, body = self._post(
            self.endpoint,
            {"jsonrpc": "2.0", "id": 100, "method": method, "params": params},
            headers=headers,
        )
        sid = hdrs.get("Mcp-Session-Id") or hdrs.get("mcp-session-id")
        if sid:
            self._session = sid
        if status != 200:
            raise KnowledgeError(f"kg http {status}: {body[:200]}")
        return _parse_sse(body)

    def _ensure_session(self):
        if self._session:
            return
        status, hdrs, body = self._post(
            self.endpoint,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": _PROTOCOL, "capabilities": {},
                        "clientInfo": {"name": "ai-daily", "version": "1"}}},
            headers={"Accept": "application/json, text/event-stream"},
        )
        sid = hdrs.get("Mcp-Session-Id") or hdrs.get("mcp-session-id")
        if sid:
            self._session = sid
        if status != 200:
            raise KnowledgeError(f"kg initialize http {status}: {body[:200]}")
        _parse_sse(body)
        self._rpc("notifications/initialized", {})

    def _call_text(self, name: str, arguments: dict) -> str:
        self._ensure_session()
        data = self._rpc("tools/call", {"name": name, "arguments": arguments})
        content = (data.get("result") or {}).get("content") or []
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))

    def fts_search(self, query: str, limit: int = 10, lang: str = "zh-CN") -> str:
        return self._call_text("fts_search", {"query": query, "limit": limit, "lang": lang})

    def kg_search(self, query: str) -> dict:
        text = self._call_text("kg_search", {"query": query})
        m = re.search(r"job_id=([\w-]+)", text)
        if m:
            return {"job_id": m.group(1), "text": text}
        return {"report": text, "text": text}

    def kg_poll(self, job_id: str) -> str:
        return self._call_text("kg_poll", {"job_id": job_id})

    def synthesize(self, query: str, max_polls: int = 8, poll_interval: float = 30.0) -> dict:
        started = self.kg_search(query)
        if "report" in started:
            return {"status": "completed", "report": started["report"]}
        for _ in range(max_polls):
            time.sleep(poll_interval)
            text = self.kg_poll(started["job_id"])
            if "[kg-running]" not in text:
                return {"status": "completed", "report": text}
        return {"status": "pending", "job_id": started["job_id"]}


def fetch_background(topic: dict, client: MCPClient = None,
                     timeout: float = 75.0, max_polls: int = 8) -> dict:
    """Background digest for a topic; never raises."""
    title = (topic or {}).get("title", "")
    direction = (topic or {}).get("direction", "")
    query = f"{title} {'(' + direction + ')' if direction else ''}".strip()
    try:
        c = client or MCPClient(KG_ENDPOINT)
        fts = c.fts_search(title, limit=5)
        kg = c.synthesize(query, max_polls=max_polls)
        return {
            "status": "completed" if kg["status"] == "completed" else "degraded",
            "source_kind": "knowledge_graph",
            "secondary": True,
            "topic": title,
            "query": query,
            "fts": fts[:2000],
            "report": kg.get("report", ""),
            "job_id": kg.get("job_id"),
            "reason": "" if kg["status"] == "completed" else "kg synthesis still pending",
        }
    except Exception as exc:  # noqa: BLE001 - never block the pipeline
        return {
            "status": "degraded",
            "source_kind": "knowledge_graph",
            "secondary": True,
            "topic": title,
            "query": query,
            "fts": "",
            "report": "",
            "reason": f"{type(exc).__name__}: {exc}",
        }


def render_background_md(data: dict) -> str:
    lines = [f"# Knowledge-Graph Background（二手背景，非证据）", ""]
    lines.append(f"- topic: {data.get('topic', '')}")
    lines.append(f"- status: {data.get('status', '')}")
    lines.append(f"- source: omnigraph LightRAG (secondary/background only)")
    if data.get("reason"):
        lines.append(f"- reason: {data['reason']}")
    if data.get("fts"):
        lines += ["", "## Full-text hits", data["fts"].strip()[:2000]]
    if data.get("report"):
        lines += ["", "## Synthesis", data["report"].strip()[:6000]]
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests to verify they pass** — `PYTHONPATH=src python3 -m unittest tests.test_knowledge -v` → OK.

- [ ] **Step 5: Commit**

```bash
git add src/ai_daily/knowledge.py tests/test_knowledge.py
git commit -m "feat: add omnigraph knowledge-graph background client"
```

---

### Task 2: Research-stage persistence + pipeline hook

**Files:**
- Modify: `src/ai_daily/research.py` (signature of `run_initial`, artifact write near the OSINT write)
- Modify: `src/ai_daily/pipeline.py` (`run_initial_research` gains `kg_client=None`)
- Test: `tests/test_research.py`

**Interfaces:**
- Consumes: `knowledge.fetch_background(topic, client=...) -> dict`, `knowledge.KG_BACKGROUND_JSON/MD`, `knowledge.render_background_md(data) -> str`
- Produces: `kg-background.json` + `kg-background.md` in the run dir; `run_initial` return gains `"kg": {...}`.

- [ ] **Step 1: Write the failing test**

```python
# in tests/test_research.py
class KnowledgeBackgroundTests(unittest.TestCase):
    def _run(self, kg_client):
        return research.run_initial(
            self.run_paths,
            aihot_fetch=lambda *a, **k: {"items": []},
            codex_runner=lambda prompt: {"status": "completed",
                "modules": [{"key": "core_timeline", "title": "t", "summary": "s"}]},
            kg_client=kg_client,
        )

    def test_kg_background_artifact_written_and_never_blocks(self):
        from ai_daily import knowledge
        class FakeClient:
            def synthesize(self, query, max_polls=8):
                return {"status": "completed", "report": "## DRAFT\nmemory-bound insight"}
            def fts_search(self, query, limit=5, lang="zh-CN"):
                return "draft model 机制"
        result = self._run(FakeClient())
        j = json.loads((self.run_paths.work_dir / knowledge.KG_BACKGROUND_JSON).read_text())
        self.assertEqual(j["status"], "completed")
        self.assertTrue(j["secondary"])
        md = (self.run_paths.work_dir / knowledge.KG_BACKGROUND_MD).read_text()
        self.assertIn("memory-bound insight", md)

    def test_kg_failure_degrades_without_breaking_research(self):
        class BoomClient:
            def synthesize(self, query, max_polls=8):
                raise OSError("down")
            def fts_search(self, query, limit=5, lang="zh-CN"):
                raise OSError("down")
        result = self._run(BoomClient())
        self.assertIn("status", result)
        self.assertEqual(result["status"], "generated")
        j = json.loads((self.run_paths.work_dir / knowledge.KG_BACKGROUND_JSON).read_text())
        self.assertEqual(j["status"], "degraded")
```

- [ ] **Step 2: Run to verify it fails** — expect `TypeError: run_initial() got an unexpected keyword argument 'kg_client'`.

- [ ] **Step 3: Implement** — add `kg_client=None` to `research.run_initial` and `pipeline.run_initial_research`; after the OSINT write, call `knowledge.fetch_background(topic, client=kg_client)`, write `kg-background.json` + `kg-background.md`, add `"kg": bg` to the returned dict.

- [ ] **Step 4: Run to verify it passes** — `PYTHONPATH=src python3 -m unittest tests.test_research -v` → OK.

- [ ] **Step 5: Commit**

```bash
git add src/ai_daily/research.py src/ai_daily/pipeline.py tests/test_research.py
git commit -m "feat: persist knowledge-graph background in the research stage"
```

---

### Task 3: Narrative prompt injection

**Files:**
- Modify: `src/ai_daily/narrative.py` (`_compile_prompt(..., kg_background: str = "")`, `run()` reads `kg-background.md`)
- Test: `tests/test_narrative.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_prompt_includes_kg_background_when_present(self):
        prompt = narrative._compile_prompt(
            {"title": "X", "hook": "", "research_queries": []},
            sample_osint(), ["cost_ledger"], set(),
            kg_background="## DRAFT\nmemory-bound insight",
        )
        self.assertIn("Knowledge-Graph Background", prompt)
        self.assertIn("memory-bound insight", prompt)
        self.assertIn("二手背景", prompt)

    def test_prompt_omits_kg_background_when_absent(self):
        prompt = narrative._compile_prompt(
            {"title": "X", "hook": "", "research_queries": []},
            sample_osint(), ["cost_ledger"], set())
        self.assertNotIn("Knowledge-Graph Background", prompt)
```

- [ ] **Step 2: Run to verify it fails.**

- [ ] **Step 3: Implement** — add the `kg_background` param; when non-empty, append a labelled section before `<evidence_data>`; in `run()`, load `kg-background.md` if present and pass it.

- [ ] **Step 4: Verify it passes.**

- [ ] **Step 5: Commit** — `git commit -m "feat: inject knowledge-graph background into narrative prompts"`.

---

### Task 4: English writing prompt injection

**Files:**
- Modify: `src/ai_daily/draft_en.py` (`_compile_prompt(..., kg_background: str = "")`, `run()` reads the artifact)
- Test: `tests/test_draft_en.py`

Same shape as Task 3: when `kg_background` is non-empty, prepend a labelled "BACKGROUND PRIMER (knowledge graph, secondary — never cite as event evidence)" section; `run()` loads `kg-background.md`.

- [ ] **Step 1-2: Write failing test** (`test_prompt_includes_kg_primer_when_present`, `test_prompt_omits_when_absent`), verify red.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Verify green.**
- [ ] **Step 5: Commit** — `git commit -m "feat: inject knowledge-graph background into the English draft"`.

---

### Task 5: CLI `kg` subcommand

**Files:**
- Modify: `src/ai_daily/cli.py` (`cmd_kg`, register in `COMMANDS`)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_kg_command_prints_background_status(self):
        with mock.patch.object(cli.pipeline, "run_knowledge_background",
                return_value={"status": "completed", "reason": ""}) as patched:
            code, out, _ = self.run_cli("kg", "--root", self.root, "--date", "2026-08-12")
        self.assertEqual(code, 0)
        self.assertIn("kg background: completed", out)
        patched.assert_called_once()
```

- [ ] **Step 2: Verify red.**
- [ ] **Step 3: Implement** — add `run_knowledge_background` to `pipeline.py` (wraps `knowledge.fetch_background` for the chosen topic + persists artifacts), `cmd_kg` prints status, register in `COMMANDS` and the parser.
- [ ] **Step 4: Verify green.**
- [ ] **Step 5: Commit** — `git commit -m "feat: add kg CLI subcommand"`.

---

### Task 6: Enable omnigraph + real verification + closeout

- [ ] **Step 1:** Back up `~/.codex/config.toml`, set `[mcp_servers.omnigraph] enabled = true` (reversible; note that a Codex restart is needed for in-session MCP tools — the pipeline uses direct HTTP and does not depend on it).
- [ ] **Step 2:** Real verification — `PYTHONPATH=src python3 -m ai_daily.cli kg --root . --date 2026-08-23 --force`; confirm `kg-background.md` contains a real synthesis (topic: Anthropic Mythos 5 or the run's chosen topic).
- [ ] **Step 3:** Full suite + gates: `PYTHONPATH=src python3 -m unittest discover -s tests -q`, `git diff --check`, `bash scripts/uat_cli.sh`.
- [ ] **Step 4:** Self code-review the diff (no subagent tool in this session), fix Critical/Important findings.
- [ ] **Step 5:** Commit remaining changes + `git pull --rebase --autostash origin main && git push origin main`.
- [ ] **Step 6:** Report: 通过/失败/待确认 + 证据（real KG output sample, test counts, uat result, remote HEAD）。

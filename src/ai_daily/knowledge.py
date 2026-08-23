"""Knowledge-graph background lane (omnigraph LightRAG over MCP).

Secondary/background only: enrich understanding of mechanisms, terms and
best practices.  Never primary evidence; never feeds evidence gates.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request

KG_ENDPOINT = "http://47.103.73.20:8767/mcp"
KG_BACKGROUND_JSON = "kg-background.json"
KG_BACKGROUND_MD = "kg-background.md"
_PROTOCOL = "2025-03-26"


def _default_post(url: str, payload: dict, headers: dict = None,
                  timeout: float = 75.0) -> tuple:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **(headers or {}),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")


def _parse_sse(body: str) -> dict:
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    for line in body.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(body)


class KnowledgeError(RuntimeError):
    """Raised when the knowledge graph cannot be reached or parsed."""


class MCPClient:
    """Minimal MCP streamable-HTTP client for the omnigraph server."""

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

    def _ensure_session(self) -> None:
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

    def synthesize(self, query: str, max_polls: int = 8,
                   poll_interval: float = 30.0) -> dict:
        started = self.kg_search(query)
        if "report" in started:
            return {"status": "completed", "report": started["report"]}
        for _ in range(max_polls):
            time.sleep(poll_interval)
            text = self.kg_poll(started["job_id"])
            if "[kg-running]" not in text:
                return {"status": "completed", "report": text}
        return {"status": "pending", "job_id": started["job_id"]}


def _kg_query(topic: dict, query: str = None) -> str:
    """Concept-level KG query: explicit override, else first research query,
    else the topic title (news-event titles rarely match the KG corpus)."""
    if query and query.strip():
        return query.strip()
    queries = (topic or {}).get("research_queries") or []
    for q in queries:
        q = str(q).strip()
        if q and q != (topic or {}).get("title"):
            return q
    return (topic or {}).get("title", "")


def fetch_background(topic: dict, client: MCPClient = None,
                     query: str = None, max_polls: int = 8) -> dict:
    """Background digest for a topic; never raises."""
    title = (topic or {}).get("title", "")
    direction = (topic or {}).get("direction", "")
    concept = _kg_query(topic, query=query)
    query = f"{concept} ({direction})".strip() if direction else concept
    try:
        c = client or MCPClient(KG_ENDPOINT)
        fts = c.fts_search(concept, limit=5)
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
    lines = [
        "# Knowledge-Graph Background（二手背景，非证据）",
        "",
        f"- topic: {data.get('topic', '')}",
        f"- status: {data.get('status', '')}",
        "- source: omnigraph LightRAG (secondary/background only)",
    ]
    if data.get("reason"):
        lines.append(f"- reason: {data['reason']}")
    if data.get("fts"):
        lines += ["", "## Full-text hits", data["fts"].strip()[:2000]]
    if data.get("report"):
        lines += ["", "## Synthesis", data["report"].strip()[:6000]]
    return "\n".join(lines) + "\n"


def persist_background(run_paths, topic: dict, client: MCPClient = None,
                       query: str = None, force: bool = False) -> dict:
    """Fetch (or resume) the KG background for a run; never raises."""
    title = (topic or {}).get("title", "")
    if not force:
        existing = run_paths.work_dir / KG_BACKGROUND_JSON
        if existing.exists():
            try:
                data = json.loads(existing.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            if data.get("topic") == title:
                return {**data, "resumed": True}
    data = fetch_background(topic, client=client, query=query)
    (run_paths.work_dir / KG_BACKGROUND_JSON).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_paths.work_dir / KG_BACKGROUND_MD).write_text(
        render_background_md(data), encoding="utf-8",
    )
    return data

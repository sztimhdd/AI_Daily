"""ChatGPT web image bridge (stdio MCP over @isen/chatgpt-image-web-mcp).

Spawns the reusable MCP server once per image, drives the user's logged-in
ChatGPT Pro session through ``open_chatgpt_browser`` + ``run_image_job``, and
reads the produced raster back into bytes.  The stdio transport and the
result loader are injectable so every path is testable offline.

Failures (``needs_human``, timeout, non-JSON reply, no image) raise
``ChatGPTWebError``; callers downgrade to a soft ``degraded`` result.
"""

from __future__ import annotations

import json
import pathlib
import queue
import subprocess
import tempfile
import threading
import time

MCP_PACKAGE = "@isen/chatgpt-image-web-mcp@0.3.4"
PROTOCOL_VERSION = "2024-11-05"
INIT_TIMEOUT = 120
CALL_TIMEOUT = 480

IMAGE_SUFFIXES = (".png", ".webp", ".jpg", ".jpeg", ".gif", ".avif")


class ChatGPTWebError(RuntimeError):
    """Raised when the web bridge cannot honestly produce an image."""


def default_command() -> list[str]:
    """The npx command that launches the pinned MCP server."""
    return ["npx", "--yes", f"--package={MCP_PACKAGE}", "chatgpt-image-web-mcp"]


class MCPClient:
    """A minimal stdio JSON-RPC MCP client.

    ``send`` and ``recv`` are injectable callables; ``recv(timeout)`` returns
    one line or ``None`` on timeout.  This keeps the protocol layer testable
    without spawning a browser or a subprocess.
    """

    def __init__(self, send, recv):
        self._send = send
        self._recv = recv
        self._next_id = 0
        self._proc = None

    def _request(self, method: str, params=None, timeout: float = CALL_TIMEOUT) -> dict:
        self._next_id += 1
        req_id = self._next_id
        req = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            req["params"] = params
        self._send(json.dumps(req, ensure_ascii=False))
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ChatGPTWebError("mcp reply timeout")
            line = self._recv(remaining)
            if line is None:
                raise ChatGPTWebError("mcp reply timeout")
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                raise ChatGPTWebError("mcp returned non-JSON reply")
            if obj.get("id") != req_id:
                continue
            if "error" in obj:
                message = ((obj.get("error") or {}).get("message") or "mcp error")
                raise ChatGPTWebError(f"mcp error: {str(message)[:200]}")
            return obj.get("result") or {}

    def initialize(self) -> dict:
        return self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "ai-daily", "version": "1.0"},
            },
            timeout=INIT_TIMEOUT,
        )

    def notify_initialized(self) -> None:
        self._send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def call_tool(self, name: str, arguments: dict, timeout: float = CALL_TIMEOUT) -> dict:
        return self._request(
            "tools/call", {"name": name, "arguments": arguments}, timeout=timeout
        )

    def close(self) -> None:
        """Terminate the underlying subprocess when one is attached."""
        proc = self._proc
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.terminate()
        except OSError:
            pass


def _spawn_stdio(command: list[str]):
    """Spawn the MCP server and return (process, send, recv)."""
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    outq: "queue.Queue[str]" = queue.Queue()

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            outq.put(line.rstrip("\n"))

    threading.Thread(target=reader, daemon=True).start()

    def send(line: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def recv(timeout: float):
        try:
            return outq.get(timeout=timeout)
        except queue.Empty:
            return None

    return proc, send, recv


def default_client_factory():
    """Build a real stdio MCP client against the pinned server."""
    proc, send, recv = _spawn_stdio(default_command())
    client = MCPClient(send, recv)
    client._proc = proc
    return client


def _is_needs_human(result: dict) -> bool:
    """Detect the MCP ``needs_human`` signal in a tool result."""
    if result is None:
        return False
    if isinstance(result, dict) and (
        result.get("needs_human") or result.get("needsHuman")
    ):
        return True
    for item in result.get("content") or []:
        text = str(item.get("text") or "") if isinstance(item, dict) else ""
        if "needs_human" in text or "needsHuman" in text or "Just a moment" in text:
            return True
    return False


def _scan_new_image(output_dir: pathlib.Path, before: set) -> bytes | None:
    """Return the bytes of the newest image produced in ``output_dir``."""
    candidates = []
    for path in output_dir.iterdir():
        if not path.is_file() or path.name in before:
            continue
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        candidates.append(path)
    if not candidates:
        return None
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        return newest.read_bytes()
    except OSError:
        return None


def generate_one(
    prompt: str,
    output_dir=None,
    output_stem: str = "image",
    client_factory=None,
    loader=None,
) -> bytes:
    """Generate one image via the ChatGPT web MCP; returns raster bytes.

    ``client_factory`` and ``loader`` are injectable for tests.  ``loader``
    receives ``(output_dir, before_filenames)`` and returns bytes.
    """
    factory = client_factory or default_client_factory
    scan = loader or _scan_new_image
    out_dir = pathlib.Path(output_dir) if output_dir else pathlib.Path(
        tempfile.gettempdir()
    ) / "ai-daily-chatgpt-web"
    out_dir.mkdir(parents=True, exist_ok=True)
    client = factory()
    try:
        client.initialize()
        client.notify_initialized()
        opened = client.call_tool("open_chatgpt_browser", {})
        if _is_needs_human(opened):
            raise ChatGPTWebError("needs_human: login or verification required")
        before = {p.name for p in out_dir.iterdir() if p.is_file()}
        job = client.call_tool(
            "run_image_job",
            {
                "prompt": prompt,
                "outputDir": str(out_dir),
                "outputStem": output_stem,
            },
        )
        if _is_needs_human(job):
            raise ChatGPTWebError("needs_human: generation needs human attention")
        data = scan(out_dir, before)
        if not data:
            raise ChatGPTWebError("no image produced")
        return data
    finally:
        client.close()

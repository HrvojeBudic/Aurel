"""
transport.py — MCP client transports (B1): stdio subprocess + Streamable HTTP.

A ``Transport`` is a bidirectional JSON-RPC message channel: ``send`` one message,
``receive`` the next (bounded by a timeout), ``close``. It is injectable, so the
client seals run against an in-process fake with zero network. Both real
transports are **fail-closed** and **hard-capped**:

  - **StdioTransport** — spawns a subprocess (``argv`` list, never a shell) with a
    **default-deny scrubbed env** (only explicitly passed-through vars survive),
    newline-delimited JSON-RPC on stdout, stderr drained as diagnostics (never
    fed into the protocol), a per-message byte cap and a receive timeout.
  - **HttpTransport** — stdlib ``urllib`` POST of one JSON-RPC message, persisting
    the ``Mcp-Session-Id`` header, honoring HTTP 202 (accepted notification, no
    body), **refusing redirects**, byte-capped and timed out.

Any violation (dead process, timeout, oversize, malformed, redirect) raises
``McpTransportError`` — never a fabricated message.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess  # nosec B404 - stdio MCP servers are launched as an explicit argv, never a shell
import threading
import urllib.error
import urllib.request
from typing import Any, Optional, Protocol, runtime_checkable

DEFAULT_TIMEOUT_S = 30.0
DEFAULT_MAX_BYTES = 8 * 1024 * 1024  # 8 MiB per message
_MINIMAL_PATH = "/usr/bin:/bin"


class McpTransportError(RuntimeError):
    """Fail-closed transport failure. No message was delivered."""


@runtime_checkable
class Transport(Protocol):
    def send(self, message: dict) -> None: ...
    def receive(self, timeout_s: Optional[float] = None) -> dict: ...
    def close(self) -> None: ...


def scrub_env(passthrough: Optional[list[str]] = None) -> dict[str, str]:
    """Default-deny env: empty except explicitly passed-through vars + a PATH.

    Secrets (``*_API_KEY`` etc.) never reach the subprocess unless the operator
    names them in ``passthrough``.
    """
    env: dict[str, str] = {}
    for key in passthrough or []:
        val = os.environ.get(key)
        if val is not None:
            env[key] = val
    env.setdefault("PATH", os.environ.get("PATH", _MINIMAL_PATH))
    return env


class StdioTransport:
    """JSON-RPC over a subprocess's stdin/stdout (newline-delimited)."""

    def __init__(
        self,
        argv: list[str],
        *,
        env_passthrough: Optional[list[str]] = None,
        cwd: Optional[str] = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        max_response_bytes: int = DEFAULT_MAX_BYTES,
    ) -> None:
        if not argv or not isinstance(argv, list):
            raise McpTransportError("argv must be a non-empty list")
        self._timeout = timeout_s
        self._max = max_response_bytes
        self._closed = False
        try:
            self._proc = subprocess.Popen(  # nosec B603 - argv list, shell=False
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=scrub_env(env_passthrough),
                cwd=cwd,
                bufsize=0,
            )
        except (OSError, ValueError) as e:
            raise McpTransportError(f"failed to spawn {argv[0]!r}: {e}")
        self._queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()
        self._stderr = bytearray()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        self._errthread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._errthread.start()

    def _read_stdout(self) -> None:
        buf = bytearray()
        stream = self._proc.stdout
        assert stream is not None
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    if buf:
                        self._queue.put(("msg", bytes(buf)))
                    break
                buf += chunk
                if len(buf) > self._max:
                    self._queue.put(("err", "response exceeded max_response_bytes"))
                    return
                while b"\n" in buf:
                    line, _, rest = buf.partition(b"\n")
                    buf = bytearray(rest)
                    self._queue.put(("msg", bytes(line)))
        except OSError as e:  # pragma: no cover - stream torn down
            self._queue.put(("err", str(e)))
        finally:
            self._queue.put(("eof", None))

    def _drain_stderr(self) -> None:
        stream = self._proc.stderr
        assert stream is not None
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                if len(self._stderr) < self._max:
                    self._stderr += chunk
        except OSError:  # pragma: no cover
            pass

    def send(self, message: dict) -> None:
        if self._closed or self._proc.poll() is not None:
            raise McpTransportError("stdio transport is not alive")
        data = (json.dumps(message) + "\n").encode("utf-8")
        try:
            assert self._proc.stdin is not None
            self._proc.stdin.write(data)
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise McpTransportError(f"send failed: {e}")

    def receive(self, timeout_s: Optional[float] = None) -> dict:
        if self._closed:
            raise McpTransportError("transport closed")
        t = self._timeout if timeout_s is None else timeout_s
        try:
            kind, payload = self._queue.get(timeout=t)
        except queue.Empty:
            raise McpTransportError(f"receive timed out after {t}s")
        if kind == "eof":
            raise McpTransportError("server closed the connection")
        if kind == "err":
            raise McpTransportError(str(payload))
        try:
            decoded = json.loads(bytes(payload).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            raise McpTransportError(f"malformed JSON message: {e}")
        if not isinstance(decoded, dict):
            raise McpTransportError("a JSON-RPC message must be an object")
        return decoded

    @property
    def stderr_text(self) -> str:
        return bytes(self._stderr).decode("utf-8", errors="replace")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        except (OSError, ValueError):  # pragma: no cover
            pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse every HTTP redirect (fail-closed)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise McpTransportError(f"redirect refused ({code} → {newurl})")


class HttpTransport:
    """JSON-RPC over Streamable HTTP: POST one message, read one response."""

    def __init__(
        self,
        url: str,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        max_response_bytes: int = DEFAULT_MAX_BYTES,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> None:
        if not (url.startswith("http://") or url.startswith("https://")):
            raise McpTransportError("url must be http(s)")
        self._url = url
        self._timeout = timeout_s
        self._max = max_response_bytes
        self._extra = dict(extra_headers or {})
        self._session_id: Optional[str] = None
        self._pending: list[dict] = []
        self._opener = urllib.request.build_opener(_NoRedirect())
        self._closed = False

    def send(self, message: dict) -> None:
        if self._closed:
            raise McpTransportError("transport closed")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._extra,
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        data = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(self._url, data=data, headers=headers, method="POST")
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:  # nosec B310 - scheme validated http(s)
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    self._session_id = sid
                status = getattr(resp, "status", resp.getcode())
                if status == 202:
                    return  # accepted notification, no body
                body = resp.read(self._max + 1)
        except McpTransportError:
            raise
        except urllib.error.HTTPError as e:
            raise McpTransportError(f"http {e.code}: {e.reason}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise McpTransportError(f"http request failed: {e}")
        if len(body) > self._max:
            raise McpTransportError("response exceeded max_response_bytes")
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            raise McpTransportError(f"malformed JSON response: {e}")
        if not isinstance(decoded, dict):
            raise McpTransportError("a JSON-RPC message must be an object")
        self._pending.append(decoded)

    def receive(self, timeout_s: Optional[float] = None) -> dict:
        if not self._pending:
            raise McpTransportError("no pending response (call send first)")
        return self._pending.pop(0)

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    def close(self) -> None:
        self._closed = True
        self._pending.clear()

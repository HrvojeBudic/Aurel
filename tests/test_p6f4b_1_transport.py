"""F4B / B1 seal — MCP client transports (real subprocess + real localhost HTTP).

Runs against genuine transports (no in-process fake): a python subprocess for
stdio and a stdlib http.server on 127.0.0.1 for HTTP — deterministic, no external
network. Proves round-trip, hard caps (byte + timeout), env scrubbing, session-id
persistence, HTTP 202, and redirect refusal.
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from agentic_runtime.mcp_client import (
    HttpTransport,
    McpTransportError,
    StdioTransport,
    scrub_env,
)

ECHO = r"""
import sys, json, os
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    msg = json.loads(line)
    resp = {"jsonrpc": "2.0", "id": msg.get("id"),
            "result": {"echo": msg.get("method"),
                       "secret": os.environ.get("MY_SECRET"),
                       "has_path": bool(os.environ.get("PATH"))}}
    sys.stdout.write(json.dumps(resp) + "\n"); sys.stdout.flush()
"""


def _stdio(program, **kw):
    return StdioTransport([sys.executable, "-c", program], **kw)


# --------------------------------------------------------------------------- #
# stdio.
# --------------------------------------------------------------------------- #
def test_stdio_round_trip():
    t = _stdio(ECHO)
    try:
        t.send({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = t.receive(timeout_s=10)
        assert resp["id"] == 1
        assert resp["result"]["echo"] == "ping"
        assert resp["result"]["has_path"] is True
    finally:
        t.close()


def test_stdio_env_is_scrubbed_by_default(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "hunter2")
    t = _stdio(ECHO)
    try:
        t.send({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert t.receive(timeout_s=10)["result"]["secret"] is None  # not leaked
    finally:
        t.close()


def test_stdio_env_passthrough_when_explicit(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "hunter2")
    t = _stdio(ECHO, env_passthrough=["MY_SECRET"])
    try:
        t.send({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert t.receive(timeout_s=10)["result"]["secret"] == "hunter2"
    finally:
        t.close()


def test_stdio_oversize_fails_closed():
    big = "import sys; sys.stdout.write('x' * 5_000_000 + '\\n'); sys.stdout.flush()"
    t = _stdio(big, max_response_bytes=1000)
    try:
        with pytest.raises(McpTransportError):
            t.receive(timeout_s=10)
    finally:
        t.close()


def test_stdio_receive_timeout():
    t = _stdio("import time; time.sleep(5)")
    try:
        with pytest.raises(McpTransportError):
            t.receive(timeout_s=0.3)
    finally:
        t.close()


def test_scrub_env_default_deny(monkeypatch):
    monkeypatch.setenv("SOME_API_KEY", "x")
    env = scrub_env()
    assert "SOME_API_KEY" not in env
    assert "PATH" in env


# --------------------------------------------------------------------------- #
# HTTP (real localhost server).
# --------------------------------------------------------------------------- #
class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        msg = json.loads(body)
        method = msg.get("method")
        if method == "notify":
            self.send_response(202)
            self.end_headers()
            return
        if method == "redirect":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/other")
            self.end_headers()
            return
        if method == "oversize":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"x":"' + b"y" * 2000 + b'"}')
            return
        resp = json.dumps({"jsonrpc": "2.0", "id": msg.get("id"),
                           "result": {"echo": method}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Mcp-Session-Id", "sess-42")
        self.end_headers()
        self.wfile.write(resp)


@pytest.fixture
def http_url():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()


def test_http_round_trip_and_session_id(http_url):
    t = HttpTransport(http_url, timeout_s=10)
    t.send({"jsonrpc": "2.0", "id": 7, "method": "echo"})
    resp = t.receive()
    assert resp["id"] == 7 and resp["result"]["echo"] == "echo"
    assert t.session_id == "sess-42"       # header persisted
    t.close()


def test_http_202_notification_no_body(http_url):
    t = HttpTransport(http_url, timeout_s=10)
    t.send({"jsonrpc": "2.0", "method": "notify"})   # notification
    with pytest.raises(McpTransportError):
        t.receive()                                   # nothing pending
    t.close()


def test_http_refuses_redirect(http_url):
    t = HttpTransport(http_url, timeout_s=10)
    with pytest.raises(McpTransportError):
        t.send({"jsonrpc": "2.0", "id": 1, "method": "redirect"})
    t.close()


def test_http_oversize_fails_closed(http_url):
    t = HttpTransport(http_url, timeout_s=10, max_response_bytes=100)
    with pytest.raises(McpTransportError):
        t.send({"jsonrpc": "2.0", "id": 1, "method": "oversize"})
    t.close()


def test_http_rejects_non_http_scheme():
    with pytest.raises(McpTransportError):
        HttpTransport("ftp://x/")

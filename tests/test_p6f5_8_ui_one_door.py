"""F5.8 seal (server side) — the UI has exactly one mutation door.

Proves structurally that every UI action reduces to `POST /proposals` and that no
other route mutates. Complements the vitest seal (frontClient is the sole fetch/WS
caller) and the fixture-mode honesty (proposals disabled when the server is off).
"""
from __future__ import annotations

import json
import socket

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.front_server import (
    ROUTES,
    ConversationEngine,
    create_front_server,
    mutation_routes,
)


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "answer via the one door", "stub-model", {"total_tokens": 7}


def test_exactly_one_mutation_route():
    muts = mutation_routes()
    assert len(muts) == 1
    assert (muts[0].method, muts[0].path) == ("POST", "/proposals")
    # every other route is read-only.
    assert all(not r.mutation for r in ROUTES if r is not muts[0])


@pytest.fixture
def live_server(monkeypatch):
    monkeypatch.setenv("AUREL_FRONT_SERVER", "1")
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    srv = create_front_server(rt, port=0, conversation_engine=engine)
    srv.serve_forever_background()
    try:
        yield srv
    finally:
        srv.shutdown()


def _http(host, port, method, path, body=None):
    sock = socket.create_connection((host, port), timeout=5)
    try:
        payload = json.dumps(body).encode() if body is not None else b""
        headers = (
            f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n\r\n"
        ).encode()
        sock.sendall(headers + payload)
        raw = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            raw += chunk
    finally:
        sock.close()
    head, _, tail = raw.partition(b"\r\n\r\n")
    status = int(head.split(b" ", 2)[1])
    return status, (json.loads(tail) if tail.strip() else None)


def test_ui_message_action_reduces_to_a_proposal(live_server):
    # A UI "send message" is a converse ProposalEnvelope through POST /proposals.
    status, body = _http(
        live_server.host, live_server.port, "POST", "/proposals",
        {"kind": "converse", "room_id": "signal:main", "operator_identity": "op",
         "role": "operator", "mandate_id": "default", "text": "hi from the UI"})
    assert status == 200
    assert body["wired"] is True and body["reply"]["mode"] == "answer"


def test_reads_never_mutate(live_server):
    # A read leaves the trace unchanged: send a message, read history twice, the
    # second read equals the first (no side effect from reading).
    _http(live_server.host, live_server.port, "POST", "/proposals",
          {"kind": "converse", "room_id": "signal:main", "operator_identity": "op",
           "role": "operator", "mandate_id": "default", "text": "seed"})
    s1, first = _http(live_server.host, live_server.port, "GET",
                      "/read/signal/history?room=signal:main")
    s2, second = _http(live_server.host, live_server.port, "GET",
                       "/read/signal/history?room=signal:main")
    assert s1 == 200 and s2 == 200
    assert first["entries"] == second["entries"]


def test_no_mutation_via_read_verb(live_server):
    # POST to a read path is not routed (only GET reads exist) → 404, never a mutation.
    status, _ = _http(live_server.host, live_server.port, "POST", "/read/library")
    assert status == 404

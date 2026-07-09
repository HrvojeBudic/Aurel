"""F5.1 seal — live read projections behind GET /read/{model}.

Every read is a pure projection over the trace: it equals a direct replay-derived
projection, it is deterministic (same trace ⇒ same bytes), and it writes nothing.
"""
from __future__ import annotations

import json
import socket

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.front_server import (
    ConversationEngine,
    LiveReadModels,
    ProposalDispatcher,
    ReadModelError,
    RoomHistoryProjection,
    WorkOpsChatReadModel,
    WorkOpsMessage,
    create_front_server,
)
from agentic_runtime.front_server.signal import SignalMessage


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "an answer", "stub-model", {"total_tokens": 9}


def _seed(rt):
    """Drive a couple of governed conversations so the trace has projectable events."""
    engine = ConversationEngine(rt, StubRouter())
    d = ProposalDispatcher(rt, conversation_engine=engine)
    sig = SignalMessage(room_id="signal:main", operator_identity="op", role="operator",
                        mandate_id="m1", context_refs=(), text="signal hi")
    d.dispatch(sig.to_proposal())
    d.dispatch(WorkOpsMessage("alpha", "op", "operator", "m1", (), "start alpha").to_proposal())
    return d


# --- purity: live projection == direct replay-derived projection -----------------

def test_signal_history_read_equals_direct_projection():
    rt = build_runtime()
    _seed(rt)
    reads = LiveReadModels(rt)
    status, payload = reads.read("/read/signal/history?room=signal:main")
    assert status == 200 and payload["live"] is True
    direct = [h.to_dict() for h in
              RoomHistoryProjection.from_trace(rt.runtime.trace, "signal:main")]
    assert payload["entries"] == direct
    assert [e["role"] for e in payload["entries"]] == ["operator", "assistant"]


def test_workops_tasks_read_equals_direct_projection():
    rt = build_runtime()
    _seed(rt)
    reads = LiveReadModels(rt)
    _status, payload = reads.read("/read/workops/tasks")
    direct = [t.to_dict() for t in WorkOpsChatReadModel.tasks(rt.runtime.trace)]
    assert payload["tasks"] == direct
    assert direct[0]["task_id"] == "alpha"


def test_workops_history_requires_task():
    rt = build_runtime()
    reads = LiveReadModels(rt)
    status, payload = reads.read("/read/workops/history")
    assert status == 400 and "task" in payload["error"]
    with pytest.raises(ReadModelError):
        reads.build("workops/history", {})


# --- liveness: appending a trace event deterministically changes the read --------

def test_read_is_live_and_deterministic():
    rt = build_runtime()
    d = _seed(rt)
    reads = LiveReadModels(rt)

    first = reads.read("/read/signal/history?room=signal:main")[1]
    # Two reads of the same trace are byte-identical (determinism).
    assert json.dumps(first) == json.dumps(reads.read("/read/signal/history?room=signal:main")[1])

    # Append one more governed turn → the SAME LiveReadModels reflects it (live).
    sig = SignalMessage(room_id="signal:main", operator_identity="op", role="operator",
                        mandate_id="m1", context_refs=(), text="second turn")
    d.dispatch(sig.to_proposal())
    second = reads.read("/read/signal/history?room=signal:main")[1]
    assert len(second["entries"]) == len(first["entries"]) + 2  # operator + assistant
    assert "second turn" in [e["text"] for e in second["entries"]]


def test_reads_never_write_to_the_trace():
    rt = build_runtime()
    _seed(rt)
    reads = LiveReadModels(rt)
    before = len(list(rt.runtime.trace.replay()))
    for path in ("/read/signal/history", "/read/workops/tasks",
                 "/read/workops/history?task=alpha", "/read/approvals", "/read/rooms"):
        reads.read(path)
    after = len(list(rt.runtime.trace.replay()))
    assert after == before  # pure projections, zero writes


def test_unknown_model_is_404():
    rt = build_runtime()
    status, payload = LiveReadModels(rt).read("/read/nope")
    assert status == 404
    assert "signal/history" in payload["known"]


def test_rooms_and_approvals_projections():
    rt = build_runtime()
    _seed(rt)
    reads = LiveReadModels(rt)
    rooms = reads.read("/read/rooms?prefix=workops:")[1]["rooms"]
    assert rooms == ["workops:alpha"]
    audit = reads.read("/read/approvals")[1]
    assert "audit" in audit and isinstance(audit["audit"], list)


# --- end-to-end through the one-door HTTP GET ------------------------------------

def test_read_over_http_end_to_end(monkeypatch):
    monkeypatch.setenv("AUREL_FRONT_SERVER", "1")
    rt = build_runtime()
    _seed(rt)
    engine = ConversationEngine(rt, StubRouter())
    srv = create_front_server(rt, port=0, conversation_engine=engine)
    srv.serve_forever_background()
    try:
        sock = socket.create_connection((srv.host, srv.port), timeout=5)
        sock.sendall((
            "GET /read/workops/tasks HTTP/1.1\r\n"
            f"Host: {srv.host}\r\nConnection: close\r\n\r\n"
        ).encode())
        raw = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            raw += chunk
        sock.close()
        body = json.loads(raw.split(b"\r\n\r\n", 1)[1])
        assert body["live"] is True and body["model"] == "workops/tasks"
        assert body["tasks"][0]["task_id"] == "alpha"
    finally:
        srv.shutdown()

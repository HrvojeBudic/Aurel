"""F5.7 seal — WorkOPS chat on the conversation engine (talk to the LLM through WorkOPS).

Milestone 2: the operator talks to the LLM through the WorkOPS surface using the
SAME `ConversationEngine` as Signal — a different (task-scoped) room, one door.
"""
from __future__ import annotations

import json
import socket

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.front_server import (
    RoomHistoryProjection,
    SignalMessage,
    WorkOpsChatReadModel,
    WorkOpsMessage,
    create_front_server,
    workops_room,
)
from agentic_runtime.front_server.conversation import ConversationEngine
from agentic_runtime.front_server.proposal_dispatcher import (
    ProposalDispatcher,
    ProposalRejected,
)
from agentic_runtime.front_server.websocket import OP_TEXT, build_frame, parse_frame
from agentic_runtime.front_server.workops import (
    CLAIMS_WORKOPS_AI_EDITOR,
    CLAIMS_WORKOPS_CODE_LIVE,
    CLAIMS_WORKOPS_TERMINAL_LIVE,
    flag_enabled,
)


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "WorkOPS is wired to the LLM.", "stub-model", {"total_tokens": 9}


def _msg(text="ship the feature", task="task-42"):
    return WorkOpsMessage(task_id=task, operator_identity="op", role="operator",
                          mandate_id="m1", context_refs=(), text=text)


# --- contract: un-constructible without provenance -------------------------------

def test_workops_message_requires_provenance():
    with pytest.raises(TypeError):
        WorkOpsMessage(task_id="t", operator_identity="op")  # missing fields
    with pytest.raises(ValueError):
        WorkOpsMessage("t", "", "operator", "m1", (), "hi")   # empty identity
    with pytest.raises(ValueError):
        WorkOpsMessage("", "op", "operator", "m1", (), "hi")  # empty task_id
    with pytest.raises(ValueError):
        WorkOpsMessage("t", "op", "operator", "", (), "hi")   # empty mandate


def test_room_is_task_scoped():
    assert _msg(task="abc").room_id == "workops:abc"
    assert workops_room("abc") == "workops:abc"
    with pytest.raises(ValueError):
        workops_room("")


# --- one door: reduces to a `converse` proposal, same as Signal ------------------

def test_message_reduces_to_converse_proposal():
    p = _msg().to_proposal()
    assert p["kind"] == "converse"
    assert p["room_id"] == "workops:task-42"
    assert p["operator_identity"] == "op" and p["mandate_id"] == "m1"
    assert p["text"] == "ship the feature"


def test_workops_message_through_dispatcher_to_llm():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    dispatcher = ProposalDispatcher(rt, conversation_engine=engine)
    result = dispatcher.dispatch(_msg("what next?").to_proposal())
    assert result["wired"] is True
    assert result["reply"]["mode"] == "answer"
    assert result["reply"]["text"] == "WorkOPS is wired to the LLM."
    assert result["reply"]["context_ref"]
    hist = RoomHistoryProjection.from_trace(rt.runtime.trace, "workops:task-42")
    assert [h.role for h in hist] == ["operator", "assistant"]
    assert "what next?" in [h.text for h in hist]


# --- task tracking: pure trace projection, zero own store ------------------------

def test_task_history_and_task_list_from_trace():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    d = ProposalDispatcher(rt, conversation_engine=engine)
    d.dispatch(_msg("start alpha", task="alpha").to_proposal())
    d.dispatch(_msg("continue alpha", task="alpha").to_proposal())
    d.dispatch(_msg("start beta", task="beta").to_proposal())

    trace = rt.runtime.trace
    assert WorkOpsChatReadModel.task_ids(trace) == ["alpha", "beta"]  # sorted, deterministic

    alpha = WorkOpsChatReadModel.history(trace, "alpha")
    assert [h.role for h in alpha] == ["operator", "assistant", "operator", "assistant"]
    assert "start beta" not in [h.text for h in alpha]  # task isolation

    tasks = {t.task_id: t for t in WorkOpsChatReadModel.tasks(trace)}
    assert tasks["alpha"].message_count == 4 and tasks["beta"].message_count == 2
    assert tasks["alpha"].room_id == "workops:alpha"


def test_same_engine_keeps_signal_and_workops_isolated():
    """N6 foundation: Signal and WorkOPS share one engine but keep separate rooms."""
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    d = ProposalDispatcher(rt, conversation_engine=engine)
    sig = SignalMessage(room_id="signal:main", operator_identity="op", role="operator",
                        mandate_id="m1", context_refs=(), text="signal side")
    d.dispatch(sig.to_proposal())
    d.dispatch(_msg("workops side", task="task-9").to_proposal())

    trace = rt.runtime.trace
    assert WorkOpsChatReadModel.task_ids(trace) == ["task-9"]  # signal room excluded
    wo_texts = [h.text for h in WorkOpsChatReadModel.history(trace, "task-9")]
    assert "workops side" in wo_texts and "signal side" not in wo_texts


def test_converse_missing_fields_rejected():
    rt = build_runtime()
    d = ProposalDispatcher(rt, conversation_engine=ConversationEngine(rt, StubRouter()))
    with pytest.raises(ProposalRejected):
        d.dispatch({"kind": "converse", "text": "hi"})  # no room/identity/mandate


# --- end-to-end over the one-door WebSocket --------------------------------------

@pytest.fixture
def ws_server(monkeypatch):
    monkeypatch.setenv("AUREL_FRONT_SERVER", "1")
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    srv = create_front_server(rt, port=0, conversation_engine=engine)
    srv.serve_forever_background()
    try:
        yield srv
    finally:
        srv.shutdown()


def test_workops_over_websocket_end_to_end(ws_server):
    sock = socket.create_connection((ws_server.host, ws_server.port), timeout=5)
    try:
        sock.sendall((
            "GET /ws HTTP/1.1\r\n"
            f"Host: {ws_server.host}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        assert "101" in sock.recv(4096).decode().split("\r\n", 1)[0]
        proposal = json.dumps(_msg("over the wire", task="t-ws").to_proposal()).encode()
        sock.sendall(build_frame(proposal, OP_TEXT, masking_key=b"\x01\x02\x03\x04"))
        frame, _ = parse_frame(sock.recv(65536))
        reply = json.loads(frame.payload)
        assert reply["wired"] is True
        assert reply["reply"]["mode"] == "answer"
        assert reply["reply"]["text"] == "WorkOPS is wired to the LLM."
    finally:
        sock.close()


# --- honesty: deferred Code surface is an explicit UNAVAILABLE seam --------------

def test_code_surface_claims_are_hardwired_false():
    assert CLAIMS_WORKOPS_CODE_LIVE is False
    assert CLAIMS_WORKOPS_TERMINAL_LIVE is False
    assert CLAIMS_WORKOPS_AI_EDITOR is False


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_FRONT_WORKOPS", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_FRONT_WORKOPS", "1")
    assert flag_enabled() is True

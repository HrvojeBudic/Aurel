"""F5.3 seal — Signal chat on the conversation engine (talk to the LLM through Signal)."""
from __future__ import annotations

import json
import socket

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.front_server import (
    RoomHistoryProjection,
    SignalMessage,
    create_front_server,
)
from agentic_runtime.front_server.conversation import ConversationEngine
from agentic_runtime.front_server.proposal_dispatcher import (
    ProposalDispatcher,
    ProposalRejected,
)
from agentic_runtime.front_server.signal import flag_enabled
from agentic_runtime.front_server.websocket import OP_TEXT, build_frame, parse_frame


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "Signal is wired to the LLM.", "stub-model", {"total_tokens": 9}


def _msg(text="hello aurel", room="signal:main"):
    return SignalMessage(room_id=room, operator_identity="op", role="operator",
                         mandate_id="m1", context_refs=(), text=text)


def test_signal_message_requires_provenance():
    with pytest.raises(TypeError):
        SignalMessage(room_id="r", operator_identity="op")
    with pytest.raises(ValueError):
        SignalMessage("r", "", "operator", "m1", (), "hi")
    with pytest.raises(ValueError):
        SignalMessage("r", "op", "operator", "", (), "hi")


def test_message_reduces_to_converse_proposal():
    p = _msg().to_proposal()
    assert p["kind"] == "converse"
    assert p["operator_identity"] == "op" and p["mandate_id"] == "m1"
    assert p["text"] == "hello aurel"


def test_signal_message_through_dispatcher_to_llm():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    dispatcher = ProposalDispatcher(rt, conversation_engine=engine)
    result = dispatcher.dispatch(_msg("what can you do?").to_proposal())
    assert result["wired"] is True
    assert result["reply"]["mode"] == "answer"
    assert result["reply"]["text"] == "Signal is wired to the LLM."
    assert result["reply"]["context_ref"]
    hist = RoomHistoryProjection.from_trace(rt.runtime.trace, "signal:main")
    assert [h.role for h in hist] == ["operator", "assistant"]
    assert "what can you do?" in [h.text for h in hist]


def test_converse_missing_fields_rejected():
    rt = build_runtime()
    d = ProposalDispatcher(rt, conversation_engine=ConversationEngine(rt, StubRouter()))
    with pytest.raises(ProposalRejected):
        d.dispatch({"kind": "converse", "text": "hi"})


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


def test_signal_over_websocket_end_to_end(ws_server):
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
        proposal = json.dumps(_msg("hi over the wire").to_proposal()).encode()
        sock.sendall(build_frame(proposal, OP_TEXT, masking_key=b"\x01\x02\x03\x04"))
        frame, _ = parse_frame(sock.recv(65536))
        reply = json.loads(frame.payload)
        assert reply["wired"] is True
        assert reply["reply"]["mode"] == "answer"
        assert reply["reply"]["text"] == "Signal is wired to the LLM."
    finally:
        sock.close()


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_FRONT_SIGNAL", raising=False)
    assert flag_enabled() is False

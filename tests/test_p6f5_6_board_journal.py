"""F5.6 seal — the Board decision journal.

A Board decision is a record, not an execution: recording it runs nothing. It reaches
action ONLY via "Convert to Proposal" — an `act` through the same one door (dispatcher
→ approval inbox → runtime.submit). The journal is a pure trace projection.
"""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
)
from agentic_runtime.external_ingress import SourceKind, make_tainted
from agentic_runtime.front_server import (
    ApprovalInbox,
    BoardDecision,
    BoardJournal,
    ProposalDispatcher,
)
from agentic_runtime.front_server.board import flag_enabled
from agentic_runtime.mcp_client import McpBridge, McpToolDescriptor, parse_tool_result


class FakeClient:
    server_name = "srv"

    def __init__(self):
        self.calls = []

    def call_tool(self, name, args):
        self.calls.append((name, args))
        return parse_tool_result({"content": [{"type": "text", "text": "ok"}]}, "srv")


def _bridge_echo(rt, client):
    d = McpToolDescriptor(
        name="echo", description=make_tainted("d", SourceKind.MCP_TOOL, "srv"),
        input_schema={"type": "object", "properties": {"q": {"type": "string"}},
                      "required": ["q"]}, descriptor_hash="h", raw={})
    return McpBridge(client, rt).bridge_tool(d)


def _high_card(tool):
    return AgentCard.make(
        name="op", agent_class=AgentClass.EXECUTION, mission="F5.6",
        authority=AuthorityScope(max_risk=RiskLevel.HIGH, allow_network=True),
        allowed_tools=[tool])


def _decision(tool="echo"):
    return BoardDecision.make(
        "adopt weekly backup", rationale="resilience", proposed_tool=tool,
        proposed_args={"q": "hi"}, decided_by="op", risk="high")


# --- contract -------------------------------------------------------------------

def test_board_decision_requires_fields():
    with pytest.raises(ValueError):
        BoardDecision.make("", rationale="r", proposed_tool="t", decided_by="op")
    with pytest.raises(ValueError):
        BoardDecision.make("t", rationale="r", proposed_tool="", decided_by="op")
    with pytest.raises(ValueError):
        BoardDecision.make("t", rationale="r", proposed_tool="x", decided_by="")


def test_convert_to_proposal_is_an_act():
    p = BoardJournal.convert_to_proposal(_decision())
    assert p["kind"] == "act"
    assert p["tool"] == "echo" and p["args"] == {"q": "hi"} and p["risk"] == "high"


# --- journal is a pure trace projection -----------------------------------------

def test_record_projects_to_journal_from_trace():
    rt = build_runtime()
    journal = BoardJournal(rt)
    d = journal.record(_decision())
    entries = BoardJournal.from_trace(rt.runtime.trace)
    assert [e.decision_id for e in entries] == [d.decision_id]
    assert entries[0].title == "adopt weekly backup"
    assert entries[0].proposed_tool == "echo" and entries[0].decided_by == "op"


def test_recording_a_decision_executes_nothing():
    rt = build_runtime()
    client = FakeClient()
    _bridge_echo(rt, client)
    BoardJournal(rt).record(_decision())
    assert client.calls == []  # a record, not an execution


# --- Convert to Proposal reduces to runtime.submit through the one door ----------

def test_convert_reduces_through_one_door_to_submit():
    rt = build_runtime()
    client = FakeClient()
    bname = _bridge_echo(rt, client)
    card = _high_card(bname)
    inbox = ApprovalInbox(rt)
    dispatcher = ProposalDispatcher(rt, approval_inbox=inbox, card=card)

    decision = BoardDecision.make(
        "run echo", rationale="demo", proposed_tool=bname,
        proposed_args={"q": "hi"}, decided_by="op", risk="high")

    act = dispatcher.dispatch(BoardJournal.convert_to_proposal(decision))
    assert act["wired"] is True and act["status"] == "pending"  # governed, not auto-run
    assert client.calls == []                                   # nothing executed yet

    decided = dispatcher.dispatch({"kind": "decide", "request_id": act["request_id"],
                                   "approve": True})
    assert decided["status"] == "executed"
    assert client.calls == [("echo", {"q": "hi"})]              # ran only after approval


# --- live read + flag -----------------------------------------------------------

def test_board_via_live_read_registry():
    from agentic_runtime.front_server import LiveReadModels
    rt = build_runtime()
    BoardJournal(rt).record(_decision())
    status, payload = LiveReadModels(rt).read("/read/board")
    assert status == 200 and payload["live"] is True and payload["model"] == "board"
    assert payload["decisions"][0]["title"] == "adopt weekly backup"


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_FRONT_BOARD", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_FRONT_BOARD", "1")
    assert flag_enabled() is True

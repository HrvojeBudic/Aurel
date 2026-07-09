"""F5.2 seal — persistent approval inbox + two-phase `act` submit.

  1. Phase A: an approval-requiring command defers → pending; DEFERRED is traced;
     nothing executes. The default approval gate is restored afterwards.
  2. Phase B: deny ⇒ not executed; approve ⇒ the operator's decision is applied
     (traced) and, for a cleanly-executing tool, the command runs.
  3. Unknown request ⇒ fail-closed.
  4. Dispatcher: `act` routes to the inbox (pending); `decide` routes to it.
"""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    CommandEnvelope,
    RiskLevel,
)
from agentic_runtime.external_ingress import SourceKind, make_tainted
from agentic_runtime.front_server import ApprovalInbox, ProposalDispatcher
from agentic_runtime.mcp_client import McpBridge, McpToolDescriptor, parse_tool_result


class FakeClient:
    server_name = "srv"

    def __init__(self):
        self.calls = []

    def call_tool(self, name, args):
        self.calls.append((name, args))
        return parse_tool_result({"content": [{"type": "text", "text": "ok"}]}, "srv")


def _high_card(tool):
    return AgentCard.make(
        name="op", agent_class=AgentClass.EXECUTION, mission="F5.2",
        authority=AuthorityScope(max_risk=RiskLevel.HIGH, allow_network=True),
        allowed_tools=[tool])


def _bridge_fake_tool(rt, client):
    d = McpToolDescriptor(
        name="echo", description=make_tainted("d", SourceKind.MCP_TOOL, "srv"),
        input_schema={"type": "object", "properties": {"q": {"type": "string"}},
                      "required": ["q"]}, descriptor_hash="h", raw={})
    return McpBridge(client, rt).bridge_tool(d)


# --------------------------------------------------------------------------- #
# 1 + 2. Two-phase governance, end to end.
# --------------------------------------------------------------------------- #
def test_defer_then_approve_executes():
    rt = build_runtime()
    client = FakeClient()
    bname = _bridge_fake_tool(rt, client)
    inbox = ApprovalInbox(rt)
    card = _high_card(bname)
    cmd = CommandEnvelope.make(card.id, bname, {"q": "hi"}, "mcp", RiskLevel.HIGH, "call")

    gate_before = rt.runtime.approval_gate
    a = inbox.submit_act(cmd, card)
    assert a["status"] == "pending"
    assert client.calls == []                              # nothing executed yet
    assert inbox.pending()[0]["request_id"] == a["request_id"]
    assert rt.runtime.approval_gate is gate_before          # default gate restored
    # DEFERRED is in the immutable audit.
    audit = ApprovalInbox.audit_from_trace(rt.runtime.trace)
    assert any(x["outcome"] == "deferred" for x in audit)

    b = inbox.decide(a["request_id"], approve=True)
    assert b["status"] == "executed"
    assert client.calls == [("echo", {"q": "hi"})]          # ran on approval
    assert inbox.pending() == []                            # cleared
    assert any(x["outcome"] == "approved" for x in
               ApprovalInbox.audit_from_trace(rt.runtime.trace))


def test_defer_then_deny_does_not_execute():
    rt = build_runtime()
    client = FakeClient()
    bname = _bridge_fake_tool(rt, client)
    inbox = ApprovalInbox(rt)
    card = _high_card(bname)
    cmd = CommandEnvelope.make(card.id, bname, {"q": "x"}, "mcp", RiskLevel.HIGH, "call")
    a = inbox.submit_act(cmd, card)
    b = inbox.decide(a["request_id"], approve=False)
    assert b["status"] == "denied"
    assert client.calls == []                              # never executed
    assert inbox.pending() == []


def test_unknown_request_fail_closed():
    rt = build_runtime()
    assert ApprovalInbox(rt).decide("nope", approve=True)["status"] == "unknown_request"


# --------------------------------------------------------------------------- #
# 3. Dispatcher routing (one door).
# --------------------------------------------------------------------------- #
def test_dispatcher_act_and_decide_route_to_inbox():
    rt = build_runtime()
    client = FakeClient()
    bname = _bridge_fake_tool(rt, client)
    card = _high_card(bname)
    inbox = ApprovalInbox(rt)
    d = ProposalDispatcher(rt, approval_inbox=inbox, card=card)

    act = d.dispatch({"kind": "act", "tool": bname, "args": {"q": "hi"},
                      "risk": "high"})
    assert act["wired"] is True and act["status"] == "pending"

    decided = d.dispatch({"kind": "decide", "request_id": act["request_id"],
                          "approve": True})
    assert decided["wired"] is True and decided["status"] == "executed"
    assert client.calls == [("echo", {"q": "hi"})]


def test_dispatcher_decide_requires_fields():
    rt = build_runtime()
    d = ProposalDispatcher(rt, approval_inbox=ApprovalInbox(rt), card=_high_card("x"))
    from agentic_runtime.front_server import ProposalRejected
    with pytest.raises(ProposalRejected):
        d.dispatch({"kind": "decide", "approve": True})     # no request_id

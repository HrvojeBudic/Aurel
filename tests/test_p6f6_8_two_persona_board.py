"""F6.8 seal — two-persona planning → Board option generator (through the one door)."""
from __future__ import annotations

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
    AurelEUDispatcher,
    BoardJournal,
    BoardOption,
    LiveReadModels,
    ProposalDispatcher,
)
from agentic_runtime.mcp_client import McpBridge, McpToolDescriptor, parse_tool_result


class PersonaRouter:
    """Returns a persona-tagged rationale so the two lenses are distinguishable."""

    def complete_with_usage(self, profile, system, user):
        return f"[{profile}] {user}", "stub-model", {"total_tokens": 6}


# --- generator: two explicit persona-diverse options ----------------------------

def test_generate_two_persona_options():
    rt = build_runtime()
    opts = AurelEUDispatcher(rt).generate_options(
        "adopt weekly backup", proposed_tool="write_file",
        proposed_args={"path": "backup.md"}, router=PersonaRouter())
    assert len(opts) == 2
    personas = {o.persona for o in opts}
    assert personas == {"SHADOW", "DEPLOY"}                 # risk-first + opportunity-first
    assert all(isinstance(o, BoardOption) for o in opts)
    # each option carries its lens rationale (distinct framings)
    assert opts[0].rationale != opts[1].rationale


def test_option_converts_to_act_proposal():
    rt = build_runtime()
    opt = AurelEUDispatcher(rt).generate_options(
        "x", proposed_tool="write_file", proposed_args={"path": "p"},
        router=PersonaRouter())[0]
    p = BoardJournal.convert_to_proposal(opt)
    assert p["kind"] == "act" and p["tool"] == "write_file" and p["args"] == {"path": "p"}


# --- options are records (generator, not execution) -----------------------------

def test_options_recorded_and_projected():
    rt = build_runtime()
    au = AurelEUDispatcher(rt)
    journal = BoardJournal(rt)
    for opt in au.generate_options("topic", proposed_tool="t", proposed_args={},
                                   router=PersonaRouter()):
        journal.record_option(opt)
    projected = BoardJournal.options_from_trace(rt.runtime.trace)
    assert len(projected) == 2
    assert {p["persona"] for p in projected} == {"SHADOW", "DEPLOY"}
    # live via /read/board
    payload = LiveReadModels(rt).read("/read/board")[1]
    assert len(payload["options"]) == 2


# --- convert reduces through the one door to runtime.submit ---------------------

class FakeClient:
    server_name = "srv"

    def __init__(self):
        self.calls = []

    def call_tool(self, name, args):
        self.calls.append((name, args))
        return parse_tool_result({"content": [{"type": "text", "text": "ok"}]}, "srv")


def test_option_convert_reduces_to_submit_via_one_door():
    rt = build_runtime()
    client = FakeClient()
    d = McpToolDescriptor(
        name="echo", description=make_tainted("d", SourceKind.MCP_TOOL, "srv"),
        input_schema={"type": "object", "properties": {"q": {"type": "string"}}},
        descriptor_hash="h", raw={})
    bname = McpBridge(client, rt).bridge_tool(d)
    card = AgentCard.make(name="op", agent_class=AgentClass.EXECUTION, mission="F6.8",
                          authority=AuthorityScope(max_risk=RiskLevel.HIGH, allow_network=True),
                          allowed_tools=[bname])
    inbox = ApprovalInbox(rt)
    dispatcher = ProposalDispatcher(rt, approval_inbox=inbox, card=card)

    option = BoardOption(option_id="o1", persona="SHADOW", title="run echo",
                         rationale="demo", proposed_tool=bname, proposed_args={"q": "hi"},
                         risk="high")
    act = dispatcher.dispatch(BoardJournal.convert_to_proposal(option))
    assert act["wired"] is True and act["status"] == "pending"  # governed, not auto-run
    assert client.calls == []
    decided = dispatcher.dispatch({"kind": "decide", "request_id": act["request_id"],
                                   "approve": True})
    assert decided["status"] == "executed"
    assert client.calls == [("echo", {"q": "hi"})]

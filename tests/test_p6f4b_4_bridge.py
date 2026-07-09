"""F4B / B4 seal — bridge external MCP tools into Aurel governance.

  1. inputSchema → ToolContract (types/required) with an unconditional HIGH floor.
  2. bridge_tool registers contract + spec under mcp__<server>__<tool>.
  3. Handler calls the client, returns leak-safe evidence (no raw external text).
  4. End-to-end: the bridged tool runs through runtime.submit (governed); a HIGH
     floor forces approval under a low-ceiling card; an un-bridged tool doesn't exist.
  5. Descriptor pin detects a rug-pull.
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    CommandEnvelope,
    PolicyVerdict,
    RiskLevel,
)
from agentic_runtime.external_ingress import SourceKind, make_tainted
from agentic_runtime.mcp_client import (
    McpBridge,
    McpCallError,
    McpToolDescriptor,
    bridged_name,
    json_schema_to_contract,
    parse_tool_result,
)

SCHEMA = {"type": "object",
          "properties": {"q": {"type": "string"}, "n": {"type": "integer"}},
          "required": ["q"]}


class FakeClient:
    def __init__(self, server_name="srv", result=None, raise_err=False):
        self.server_name = server_name
        self._result = result or parse_tool_result(
            {"content": [{"type": "text", "text": "SECRET-EXTERNAL-TEXT"}]}, server_name)
        self.raise_err = raise_err
        self.calls = []

    def call_tool(self, name, args):
        self.calls.append((name, args))
        if self.raise_err:
            raise McpCallError("boom")
        return self._result


def _descriptor(name="echo", schema=None, desc="a tool", h="hash1"):
    return McpToolDescriptor(
        name=name,
        description=make_tainted(desc, SourceKind.MCP_TOOL, "srv"),
        input_schema=schema if schema is not None else SCHEMA,
        descriptor_hash=h,
        raw={},
    )


# --------------------------------------------------------------------------- #
# 1. schema → contract.
# --------------------------------------------------------------------------- #
def test_schema_to_contract_types_required_and_high_floor():
    c = json_schema_to_contract("mcp__srv__echo", "d", SCHEMA)
    assert c.input_schema["q"].type == "str" and c.input_schema["q"].required is True
    assert c.input_schema["n"].type == "int" and c.input_schema["n"].required is False
    assert c.risk_floor() is RiskLevel.HIGH


def test_high_floor_is_unconditional():
    # A tool whose schema looks utterly benign still floors HIGH (server can't lower).
    c = json_schema_to_contract("mcp__srv__ping", "d", {"type": "object"})
    assert c.risk_floor() is RiskLevel.HIGH


# --------------------------------------------------------------------------- #
# 2 + 3. bridge + handler.
# --------------------------------------------------------------------------- #
def test_bridge_registers_and_handler_is_leak_safe():
    rt = build_runtime()
    sunk = []
    client = FakeClient()
    bridge = McpBridge(client, rt,
                       sink=lambda res, srv: sunk.append((res, srv)))
    bname = bridge.bridge_tool(_descriptor())
    assert bname == bridged_name("srv", "echo") == "mcp__srv__echo"
    assert rt.runtime.contracts.has(bname)
    assert bname in rt.runtime.tools.registered
    # Run the handler directly.
    handler = rt.runtime.tools._tools[bname].handler  # noqa: SLF001
    obs = handler(rt.runtime.tools.sandbox, {"q": "hi"})
    assert obs.success is True
    assert client.calls == [("echo", {"q": "hi"})]
    assert sunk and sunk[0][1] == "srv"
    # Leak-safe: raw external text is NOT in the observation artifacts.
    assert "SECRET-EXTERNAL-TEXT" not in str(obs.artifacts)


# --------------------------------------------------------------------------- #
# 4. end-to-end through submit.
# --------------------------------------------------------------------------- #
def _card(max_risk, tools):
    return AgentCard.make(
        name="mcp-caller", agent_class=AgentClass.EXECUTION, mission="B4",
        authority=AuthorityScope(max_risk=max_risk, allow_network=True),
        allowed_tools=tools,
    )


def test_bridged_tool_runs_through_submit_with_approval():
    # HIGH floor ⇒ policy ALLOW but HITL approval required; with an auto-approver
    # the governed tool actually executes end-to-end.
    from agentic_runtime.hitl import AutoApprover

    rt = build_runtime(approval_gate=AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True))
    client = FakeClient()
    bname = McpBridge(client, rt).bridge_tool(_descriptor())
    card = _card(RiskLevel.HIGH, [bname])
    cmd = CommandEnvelope.make(card.id, bname, {"q": "hi"}, "call", RiskLevel.HIGH, "mcp")
    res = rt.runtime.submit(cmd, card)
    assert res.decision.verdict is PolicyVerdict.ALLOW
    assert client.calls == [("echo", {"q": "hi"})]   # really executed
    assert res.observation.success is True


def test_high_floor_auto_denied_by_default_approver():
    # The default (deny-all) approver blocks a HIGH-risk external call: defence in
    # depth — even an authorized card cannot silently run it.
    rt = build_runtime()
    client = FakeClient()
    bname = McpBridge(client, rt).bridge_tool(_descriptor())
    card = _card(RiskLevel.HIGH, [bname])
    cmd = CommandEnvelope.make(card.id, bname, {"q": "hi"}, "call", RiskLevel.HIGH, "mcp")
    res = rt.runtime.submit(cmd, card)
    assert res.ok is False
    assert client.calls == []                          # blocked at approval


def test_low_card_forces_approval_verdict():
    rt = build_runtime()
    client = FakeClient()
    bname = McpBridge(client, rt).bridge_tool(_descriptor())
    card = _card(RiskLevel.LOW, [bname])
    cmd = CommandEnvelope.make(card.id, bname, {"q": "hi"}, "call", RiskLevel.LOW, "mcp")
    res = rt.runtime.submit(cmd, card)
    assert res.decision.verdict is PolicyVerdict.REQUIRE_APPROVAL
    assert client.calls == []                          # not executed


def test_unbridged_tool_does_not_exist():
    rt = build_runtime()
    assert "mcp__srv__echo" not in rt.runtime.tools.registered
    assert rt.runtime.contracts.has("mcp__srv__echo") is False


# --------------------------------------------------------------------------- #
# 5. pin / rug-pull.
# --------------------------------------------------------------------------- #
def test_verify_pin_detects_rug_pull():
    rt = build_runtime()
    client = FakeClient()
    bridge = McpBridge(client, rt)
    bridge.bridge_tool(_descriptor(h="hash1"))
    assert bridge.verify_pin(_descriptor(h="hash1")) is True      # unchanged
    assert bridge.verify_pin(_descriptor(h="hash2")) is False     # rug-pulled

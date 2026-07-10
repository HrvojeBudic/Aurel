"""F6.2 seal — the mandate scope-enforcement gate (authority, fail-closed).

A command outside its mandate's scope is DENIED before approval; the mandate only
tightens the card's authority (never widens); the gate is byte-identical when
absent (no registry / flag off / default mandate / non fail-closed).
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
from agentic_runtime.governance_enforcement import (
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
)
from agentic_runtime.mandate import (
    Mandate,
    MandateRegistry,
    MandateScope,
    evaluate_mandate_scope_check,
)
from agentic_runtime.mcp_client import McpBridge, McpToolDescriptor, parse_tool_result

FAIL_CLOSED = GovernanceEnforcementConfig(mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED)


# --- pure gate logic ------------------------------------------------------------

def _cmd(tool="write_file", args=None, risk=RiskLevel.LOW):
    return CommandEnvelope.make("card1", tool, args or {}, "r", risk, "eff")


def _mandate(**scope_kw):
    return Mandate(mandate_id="m1", version="v1", scope=MandateScope(**scope_kw))


def test_gate_blocks_path_outside_scope():
    m = _mandate(paths=("clients/x/",))
    r = evaluate_mandate_scope_check(
        _cmd(args={"path": "clients/y/secret"}), None, m, now=0.0)
    assert r.should_block and "outside mandate paths" in r.reason


def test_gate_allows_path_inside_scope():
    m = _mandate(paths=("clients/x/",))
    r = evaluate_mandate_scope_check(
        _cmd(args={"path": "clients/x/report.md"}), None, m, now=0.0)
    assert r.should_block is False


def test_gate_blocks_tool_outside_allowlist():
    m = _mandate(allowed_tools=("read_file",))
    r = evaluate_mandate_scope_check(_cmd(tool="write_file"), None, m, now=0.0)
    assert r.should_block and "not in mandate allow-list" in r.reason


def test_gate_blocks_risk_above_ceiling():
    m = _mandate(max_risk=RiskLevel.LOW)
    r = evaluate_mandate_scope_check(_cmd(risk=RiskLevel.HIGH), None, m, now=0.0)
    assert r.should_block and "exceeds mandate ceiling" in r.reason


def test_gate_fail_closed_on_missing_or_expired():
    assert evaluate_mandate_scope_check(_cmd(), None, None, now=0.0).should_block
    expired = Mandate(mandate_id="m", version="v1",
                      scope=MandateScope(client_id="x"), expires_at=100.0)
    assert evaluate_mandate_scope_check(_cmd(), None, expired, now=200.0).should_block


# --- end-to-end through runtime.submit ------------------------------------------

class FakeClient:
    server_name = "srv"

    def __init__(self):
        self.calls = []

    def call_tool(self, name, args):
        self.calls.append((name, args))
        return parse_tool_result({"content": [{"type": "text", "text": "ok"}]}, "srv")


def _bridge(rt, client, name, props):
    d = McpToolDescriptor(
        name=name, description=make_tainted("d", SourceKind.MCP_TOOL, "srv"),
        input_schema={"type": "object", "properties": props}, descriptor_hash="h", raw={})
    return McpBridge(client, rt).bridge_tool(d)


def _card(tool, mandate_id):
    return AgentCard.make(
        name="op", agent_class=AgentClass.EXECUTION, mission="F6.2",
        authority=AuthorityScope(write_paths=["clients/"], max_risk=RiskLevel.HIGH,
                                 allow_network=True),
        allowed_tools=[tool], mandate_id=mandate_id)


def _mandated_runtime(monkeypatch, *, allowed_tools=()):
    monkeypatch.setenv("AUREL_MANDATE", "1")
    registry = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1",
                scope=MandateScope(paths=("clients/x/",), allowed_tools=tuple(allowed_tools),
                                   max_risk=RiskLevel.HIGH)),
    ])
    return build_runtime(governance_enforcement_config=FAIL_CLOSED,
                         mandate_registry=registry)


def _stderr(res):
    return res.observation.stderr or ""


# The mandate gate runs BEFORE approval, so a block is precisely a "mandate scope"
# denial with zero execution; a pass means no such denial (downstream approval is
# a separate concern, not F6.2).

def test_out_of_mandate_path_denied_before_approval(monkeypatch):
    rt = _mandated_runtime(monkeypatch)
    client = FakeClient()
    bname = _bridge(rt, client, "write_file", {"path": {"type": "string"}})
    card = _card(bname, "client_x")
    cmd = CommandEnvelope.make(card.id, bname, {"path": "clients/y/secret"},
                               "r", RiskLevel.LOW, "write")
    res = rt.runtime.submit(cmd, card)
    assert res.ok is False
    assert "mandate scope" in _stderr(res) and "outside mandate paths" in _stderr(res)
    assert client.calls == []                 # nothing executed


def test_out_of_mandate_tool_denied(monkeypatch):
    rt = _mandated_runtime(monkeypatch, allowed_tools=("mcp__srv__read_file",))
    client = FakeClient()
    bname = _bridge(rt, client, "write_file", {"path": {"type": "string"}})
    card = _card(bname, "client_x")  # card issues write_file, mandate allows only read
    cmd = CommandEnvelope.make(card.id, bname, {"path": "clients/x/ok"},
                               "r", RiskLevel.LOW, "write")
    res = rt.runtime.submit(cmd, card)
    assert res.ok is False and "not in mandate allow-list" in _stderr(res)
    assert client.calls == []


def test_in_mandate_passes_the_gate(monkeypatch):
    rt = _mandated_runtime(monkeypatch)
    client = FakeClient()
    bname = _bridge(rt, client, "write_file", {"path": {"type": "string"}})
    card = _card(bname, "client_x")
    cmd = CommandEnvelope.make(card.id, bname, {"path": "clients/x/report.md"},
                               "r", RiskLevel.LOW, "write")
    res = rt.runtime.submit(cmd, card)
    # In-scope ⇒ the mandate gate does NOT block (a later gate may, that's not F6.2).
    assert "mandate scope" not in _stderr(res)


def test_flag_off_skips_the_gate(monkeypatch):
    monkeypatch.delenv("AUREL_MANDATE", raising=False)
    registry = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1",
                scope=MandateScope(paths=("clients/x/",)))])
    rt = build_runtime(governance_enforcement_config=FAIL_CLOSED, mandate_registry=registry)
    client = FakeClient()
    bname = _bridge(rt, client, "write_file", {"path": {"type": "string"}})
    card = _card(bname, "client_x")
    cmd = CommandEnvelope.make(card.id, bname, {"path": "clients/y/anything"},
                               "r", RiskLevel.LOW, "write")
    res = rt.runtime.submit(cmd, card)
    assert "mandate scope" not in _stderr(res)  # gate skipped despite out-of-scope path


def test_default_sentinel_skips_the_gate(monkeypatch):
    rt = _mandated_runtime(monkeypatch)
    client = FakeClient()
    bname = _bridge(rt, client, "write_file", {"path": {"type": "string"}})
    card = _card(bname, "default")  # default sentinel ⇒ gate skips
    cmd = CommandEnvelope.make(card.id, bname, {"path": "clients/y/anything"},
                               "r", RiskLevel.LOW, "write")
    res = rt.runtime.submit(cmd, card)
    assert "mandate scope" not in _stderr(res)


def test_shadow_mode_does_not_enforce(monkeypatch):
    # Enforcement is G0–G3 only: under SHADOW_ONLY the mandate gate stays quiet.
    monkeypatch.setenv("AUREL_MANDATE", "1")
    registry = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1",
                scope=MandateScope(paths=("clients/x/",)))])
    rt = build_runtime(mandate_registry=registry)  # default = SHADOW_ONLY
    client = FakeClient()
    bname = _bridge(rt, client, "write_file", {"path": {"type": "string"}})
    card = _card(bname, "client_x")
    cmd = CommandEnvelope.make(card.id, bname, {"path": "clients/y/anything"},
                               "r", RiskLevel.LOW, "write")
    res = rt.runtime.submit(cmd, card)
    assert "mandate scope" not in _stderr(res)

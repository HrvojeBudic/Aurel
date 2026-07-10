"""F6.5 seal — Constitution ↔ dispatch wiring (mandate + delegation, else G0)."""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.constitution import DelegationLedger, DelegationWindow
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.front_server import AurelEUDispatcher
from agentic_runtime.front_server.aureleu import CONSTITUTION_VIOLATION_EVENT
from agentic_runtime.identity.autonomy_scale_engine import AutonomyLevel
from agentic_runtime.mandate import Mandate, MandateRegistry, MandateScope

A4 = AutonomyLevel.A4_GOVERNED_TOOL_ACTION


def _runtime_with_mandate(**scope_kw):
    reg = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1", scope=MandateScope(**scope_kw)),
    ])
    return build_runtime(mandate_registry=reg)


def _grant(rt, ceiling=A4, categories=("tool_call",)):
    DelegationLedger(rt).grant(DelegationWindow.make(
        "operator", ceiling, valid_from=0.0, valid_until=1e12,
        action_categories=categories))


def _violations(rt):
    return [e for e in rt.runtime.trace.replay()
            if e.get("kind") == "praxis_event"
            and e.get("event_type") == CONSTITUTION_VIOLATION_EVENT]


# --- both present ⇒ allowed -----------------------------------------------------

def test_dispatch_with_mandate_and_delegation_is_allowed():
    rt = _runtime_with_mandate(paths=("clients/x/",), max_risk=RiskLevel.HIGH)
    _grant(rt)
    au = AurelEUDispatcher(rt)
    auth = au.authorize_dispatch(
        mandate_id="client_x", autonomy_level=A4, category="tool_call", at=1.0,
        tool="write", path="clients/x/report.md", risk=RiskLevel.LOW)
    assert auth.allowed is True and auth.mandate_id == "client_x"
    assert auth.cited_delegation_id and auth.drop_to_g0 is False
    assert _violations(rt) == []


# --- missing delegation ⇒ G0 + notification ------------------------------------

def test_dispatch_without_delegation_drops_to_g0():
    rt = _runtime_with_mandate(paths=("clients/x/",), max_risk=RiskLevel.HIGH)
    # no delegation granted
    au = AurelEUDispatcher(rt)
    auth = au.authorize_dispatch(
        mandate_id="client_x", autonomy_level=A4, category="tool_call", at=1.0,
        tool="write", path="clients/x/report.md", risk=RiskLevel.LOW)
    assert auth.allowed is False and auth.drop_to_g0 is True
    assert "no active delegation" in auth.reason
    assert len(_violations(rt)) == 1 and _violations(rt)[0]["mandate_id"] == "client_x"


# --- out of mandate scope ⇒ DENY -----------------------------------------------

def test_dispatch_out_of_mandate_scope_denied():
    rt = _runtime_with_mandate(paths=("clients/x/",), max_risk=RiskLevel.HIGH)
    _grant(rt)
    au = AurelEUDispatcher(rt)
    auth = au.authorize_dispatch(
        mandate_id="client_x", autonomy_level=A4, category="tool_call", at=1.0,
        tool="write", path="clients/y/secret", risk=RiskLevel.LOW)
    assert auth.allowed is False and "outside mandate paths" in auth.reason
    assert len(_violations(rt)) == 1


def test_dispatch_unknown_mandate_fail_closed():
    rt = _runtime_with_mandate(paths=("clients/x/",))
    _grant(rt)
    au = AurelEUDispatcher(rt)
    auth = au.authorize_dispatch(
        mandate_id="ghost", autonomy_level=A4, category="tool_call", at=1.0)
    assert auth.allowed is False and auth.drop_to_g0 is True
    assert "no valid mandate" in auth.reason


def test_dispatch_expired_mandate_fail_closed():
    reg = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1",
                scope=MandateScope(client_id="x"), expires_at=100.0)])
    rt = build_runtime(mandate_registry=reg)
    _grant(rt)
    auth = AurelEUDispatcher(rt).authorize_dispatch(
        mandate_id="client_x", autonomy_level=A4, category="tool_call", at=200.0)
    assert auth.allowed is False and auth.drop_to_g0 is True


# --- autonomy above the delegated ceiling ⇒ denied ------------------------------

def test_dispatch_above_delegated_ceiling_denied():
    rt = _runtime_with_mandate(client_id="x")
    _grant(rt, ceiling=AutonomyLevel.A2_DRAFT)  # only up to A2
    auth = AurelEUDispatcher(rt).authorize_dispatch(
        mandate_id="client_x", autonomy_level=AutonomyLevel.A5_CONDITIONAL_EXECUTION,
        category="tool_call", at=1.0)
    assert auth.allowed is False and auth.drop_to_g0 is True

"""F6.3 seal — Constitution delegation windows (cite-or-deny, fail-closed → G0)."""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.constitution import (
    DelegationLedger,
    DelegationWindow,
    delegation_grant_ref,
    flag_enabled,
    require_delegation,
)
from agentic_runtime.identity.autonomy_scale_engine import AutonomyLevel


def _window(ceiling=AutonomyLevel.A4_GOVERNED_TOOL_ACTION, *, valid_from=0.0,
            valid_until=0.0, categories=()):
    return DelegationWindow(
        delegation_id="d1", granted_by="operator", autonomy_ceiling=ceiling,
        valid_from=valid_from, valid_until=valid_until, action_categories=categories)


# --- contract ------------------------------------------------------------------

def test_ceiling_cannot_be_denial():
    with pytest.raises(ValueError):
        DelegationWindow("d", "op", AutonomyLevel.A7_DENIED, 0.0, 0.0)
    with pytest.raises(ValueError):
        DelegationWindow("", "op", AutonomyLevel.A2_DRAFT, 0.0, 0.0)


def test_is_active_window():
    w = _window(valid_from=100.0, valid_until=200.0)
    assert w.is_active(150.0) is True
    assert w.is_active(50.0) is False and w.is_active(250.0) is False
    assert _window(valid_until=0.0).is_active(1e12) is True  # 0 ⇒ no expiry


def test_covers_respects_ceiling_and_category():
    w = _window(ceiling=AutonomyLevel.A4_GOVERNED_TOOL_ACTION, categories=("tool_call",))
    assert w.covers(AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION, "tool_call") is True
    assert w.covers(AutonomyLevel.A5_CONDITIONAL_EXECUTION, "tool_call") is False  # above ceiling
    assert w.covers(AutonomyLevel.A4_GOVERNED_TOOL_ACTION, "external_effect") is False  # category


# --- cite-or-deny (fail-closed) -------------------------------------------------

def test_autonomous_action_requires_active_delegation():
    w = _window(ceiling=AutonomyLevel.A4_GOVERNED_TOOL_ACTION,
                valid_from=0.0, valid_until=1000.0)
    ok = require_delegation(AutonomyLevel.A4_GOVERNED_TOOL_ACTION, "tool_call", [w], at=500.0)
    assert ok.allowed and ok.cited_delegation_id == "d1" and ok.drop_to_g0 is False


def test_action_outside_window_drops_to_g0():
    w = _window(valid_from=0.0, valid_until=100.0)
    out = require_delegation(AutonomyLevel.A4_GOVERNED_TOOL_ACTION, "tool_call", [w], at=200.0)
    assert out.allowed is False and out.drop_to_g0 is True
    assert "no active delegation" in out.reason


def test_action_above_ceiling_denied():
    w = _window(ceiling=AutonomyLevel.A2_DRAFT, valid_until=0.0)
    out = require_delegation(AutonomyLevel.A5_CONDITIONAL_EXECUTION, "tool_call", [w], at=1.0)
    assert out.allowed is False and out.drop_to_g0 is True


def test_no_delegations_is_fail_closed():
    out = require_delegation(AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION, "local_write", [], at=1.0)
    assert out.allowed is False and out.drop_to_g0 is True


def test_denied_level_never_covered():
    w = _window(ceiling=AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK, valid_until=0.0)
    out = require_delegation(AutonomyLevel.A7_DENIED, "high_risk", [w], at=1.0)
    assert out.allowed is False  # constitutional floor: A7 stays denied


# --- governed record: grant + projection from trace -----------------------------

def test_grant_projects_from_trace():
    rt = build_runtime()
    ledger = DelegationLedger(rt)
    w = DelegationWindow.make("operator", AutonomyLevel.A4_GOVERNED_TOOL_ACTION,
                              valid_from=0.0, valid_until=1000.0,
                              action_categories=("tool_call",), consent_ref="c1")
    ledger.grant(w)
    windows = DelegationLedger.from_trace(rt.runtime.trace)
    assert len(windows) == 1
    d = windows[0]
    assert d.delegation_id == w.delegation_id and d.granted_by == "operator"
    assert d.autonomy_ceiling is AutonomyLevel.A4_GOVERNED_TOOL_ACTION
    assert d.action_categories == ("tool_call",) and d.consent_ref == "c1"

    active = DelegationLedger.active(rt.runtime.trace, at=500.0)
    assert [a.delegation_id for a in active] == [w.delegation_id]
    assert delegation_grant_ref(windows, at=500.0) == w.delegation_id
    assert delegation_grant_ref(windows, at=2000.0) == ""  # expired ⇒ no ref


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_CONSTITUTION", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_CONSTITUTION", "1")
    assert flag_enabled() is True

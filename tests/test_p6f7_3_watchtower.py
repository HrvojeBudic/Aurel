"""F7.3 seal — Watchtower read-only alert derivation + HQ.Command / CORP flip.

Watchtower derives governance alerts from facts already in the trace + ledger and
surfaces them — visibility, never authority (never blocks, never executes). Every
alert cites its source (un-constructible without a `source_ref`); rules are
deterministic; the flag-off world is a byte-identical UNAVAILABLE seam.
"""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.budget import BudgetLedger, BudgetPolicy
from agentic_runtime.core_types import BudgetDecisionRecord
from agentic_runtime.corp import (
    AlertKind,
    AlertSeverity,
    WatchtowerAlert,
    default_corp_registry,
    derive_alerts,
)
from agentic_runtime.front_server import CorpReadModel, HQCommandReadModel, LiveReadModels
from agentic_runtime.mandate import DEFAULT_MANDATE_ID


class _FakeTrace:
    def __init__(self, events):
        self._events = events

    def replay(self):
        return iter(self._events)


def _budget_deny(mandate_id=DEFAULT_MANDATE_ID):
    return {"kind": "budget_decision", "metric": "max_estimated_cost_cents",
            "verdict": "deny", "used": 600, "limit": 500, "mandate_id": mandate_id}


def _blocked_run(mandate_id=DEFAULT_MANDATE_ID):
    return {"kind": "runtime_status_transition", "run_id": "run-a", "to": "rejected",
            "reason_code": "mandate_scope", "mandate_id": mandate_id}


def _cvio(mandate_id=DEFAULT_MANDATE_ID):
    return {"kind": "praxis_event", "event_type": "constitution_violation",
            "summary": f"CVIO|{mandate_id}|out_of_window", "mandate_id": mandate_id}


# --- alert no-overclaim ---------------------------------------------------------

def test_alert_requires_source_ref():
    with pytest.raises(ValueError):
        WatchtowerAlert(AlertKind.BUDGET_DENY, AlertSeverity.CRITICAL, "m", source_ref="")


def test_alert_id_is_deterministic():
    a = WatchtowerAlert(AlertKind.BUDGET_DENY, AlertSeverity.CRITICAL, "m", source_ref="s")
    b = WatchtowerAlert(AlertKind.BUDGET_DENY, AlertSeverity.CRITICAL, "other", source_ref="s")
    assert a.alert_id == b.alert_id                     # id from (kind, source_ref) only


# --- trace-derived rules --------------------------------------------------------

def test_budget_deny_becomes_critical_alert_with_client():
    reg = default_corp_registry()
    alerts = derive_alerts(_FakeTrace([_budget_deny()]), corp_registry=reg)
    assert len(alerts) == 1
    a = alerts[0]
    assert a.kind is AlertKind.BUDGET_DENY and a.severity is AlertSeverity.CRITICAL
    assert a.source_ref and a.mandate_id == DEFAULT_MANDATE_ID
    assert a.client_id == "client-zero"                 # resolved via corp registry


def test_blocked_run_becomes_mandate_block_alert():
    alerts = derive_alerts(_FakeTrace([_blocked_run()]))
    assert len(alerts) == 1 and alerts[0].kind is AlertKind.MANDATE_BLOCK
    assert alerts[0].severity is AlertSeverity.CRITICAL


def test_needs_human_is_warn_not_critical():
    ev = _blocked_run()
    ev["to"] = "needs_human"
    alerts = derive_alerts(_FakeTrace([ev]))
    assert alerts[0].severity is AlertSeverity.WARN


def test_non_blocked_transition_produces_no_alert():
    ev = _blocked_run()
    ev["to"] = "running"
    assert derive_alerts(_FakeTrace([ev])) == []


def test_constitution_violation_becomes_alert():
    alerts = derive_alerts(_FakeTrace([_cvio()]))
    assert len(alerts) == 1
    assert alerts[0].kind is AlertKind.CONSTITUTION_VIOLATION
    assert "out_of_window" in alerts[0].message


# --- ledger threshold rule ------------------------------------------------------

def test_budget_threshold_from_ledger_snapshot():
    led = BudgetLedger(policy=BudgetPolicy(max_tool_calls_per_run=2))
    led.begin_run("r", "a", "i")
    led.charge_tool("a")
    led.charge_tool("a")                                # 2/2 ⇒ >80%
    alerts = derive_alerts(None, led)
    kinds = {a.kind for a in alerts}
    assert AlertKind.BUDGET_THRESHOLD in kinds
    thr = next(a for a in alerts if a.kind is AlertKind.BUDGET_THRESHOLD)
    assert thr.source_ref == "budget_threshold:tool_calls"


def test_no_ledger_skips_threshold_rule():
    # No ledger ⇒ threshold rule is skipped, never invented.
    assert derive_alerts(_FakeTrace([]), None) == []


# --- pending-approval rule ------------------------------------------------------

def test_pending_approval_from_inbox():
    class _Inbox:
        def pending(self):
            return [{"request_id": "r1", "tool": "write_file", "mandate_id": DEFAULT_MANDATE_ID}]

    alerts = derive_alerts(_FakeTrace([]), inbox=_Inbox(), corp_registry=default_corp_registry())
    assert len(alerts) == 1 and alerts[0].kind is AlertKind.APPROVAL_PENDING
    assert alerts[0].source_ref == "approval_pending:r1"
    assert alerts[0].client_id == "client-zero"


# --- dedup + ordering -----------------------------------------------------------

def test_dedup_and_severity_ordering():
    events = [_budget_deny(), _budget_deny(), _cvio(), _blocked_run()]
    events.append({"kind": "runtime_status_transition", "run_id": "run-a", "to": "needs_human",
                   "reason_code": "await", "mandate_id": DEFAULT_MANDATE_ID})
    alerts = derive_alerts(_FakeTrace(events))
    # identical budget denies dedup by source_ref
    assert sum(1 for a in alerts if a.kind is AlertKind.BUDGET_DENY) == 1
    # sorted most-severe first: the WARN (needs_human) is last
    assert alerts[-1].severity is AlertSeverity.WARN
    assert all(a.severity is AlertSeverity.CRITICAL for a in alerts[:-1])


# --- flag-off byte-identical seams ----------------------------------------------

def test_hq_watchtower_off_is_byte_identical(monkeypatch):
    monkeypatch.delenv("AUREL_WATCHTOWER", raising=False)
    rt = build_runtime()
    d = HQCommandReadModel.from_runtime(rt).to_dict()
    assert d["watchtower"] == {"status": "UNAVAILABLE", "owner": "F7",
                               "reason": "Watchtower alert feed is F7; not live in F5",
                               "alerts": []}
    assert d["claims_watchtower_live"] is False


def test_corp_alerts_off_is_unavailable_seam(monkeypatch):
    monkeypatch.delenv("AUREL_WATCHTOWER", raising=False)
    rt = build_runtime()
    view = CorpReadModel.from_runtime(rt).portfolio_view()
    assert view["alerts"]["status"] == "UNAVAILABLE" and view["alerts"]["owner"] == "F7.3"
    assert view["claims_alerts_live"] is False


# --- flag-on live flip ----------------------------------------------------------

def _seed_deny(rt):
    rt.runtime.trace.append_budget_decision(BudgetDecisionRecord.make(
        run_id="run-a", intent_id="i", issuer_card_id="card-1",
        metric="max_estimated_cost_cents", verdict="deny", used=600, limit=500,
        mandate_id=DEFAULT_MANDATE_ID))


def test_hq_watchtower_on_is_live(monkeypatch):
    monkeypatch.setenv("AUREL_WATCHTOWER", "1")
    rt = build_runtime()
    _seed_deny(rt)
    d = HQCommandReadModel.from_runtime(rt).to_dict()
    assert d["watchtower"]["status"] == "LIVE"
    assert d["watchtower"]["count"] == 1
    assert d["watchtower"]["alerts"][0]["kind"] == "budget_deny"
    assert d["claims_watchtower_live"] is True


def test_corp_alerts_on_is_live_via_registry(monkeypatch):
    monkeypatch.setenv("AUREL_WATCHTOWER", "1")
    rt = build_runtime()
    _seed_deny(rt)
    status, payload = LiveReadModels(rt).read("/read/corp/portfolio")
    assert status == 200
    assert payload["alerts"]["status"] == "LIVE" and payload["alerts"]["count"] == 1
    assert payload["claims_alerts_live"] is True

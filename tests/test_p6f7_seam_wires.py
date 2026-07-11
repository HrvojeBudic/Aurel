"""F7 seam wires — make klijent nula executable, not just projectable.

Two quick wires closing forward seams the F7 slices left:
  * the shared skill library is exposed on the inner runtime, so the Reflex
    Flywheel KPI (F7.9) can go live once the library has usage;
  * a `corp_risk_add` proposal is routed through the one door to the governed
    Risk Register write (F7.7) — operator metadata appended like the Board journal.
"""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import CapabilityState, CommandEnvelope, RiskLevel
from agentic_runtime.corp import RiskEntry, RiskRegisterProjection
from agentic_runtime.front_server import LiveReadModels, ProposalDispatcher
from agentic_runtime.front_server.proposal_dispatcher import ProposalRejected


# --- wire 1: skill library → Reflex Flywheel KPI --------------------------------

def test_runtime_exposes_shared_skill_library():
    rt = build_runtime()
    assert rt.runtime.skills is rt.skills          # the wire: same shared library


def test_corp_kpi_goes_live_with_skill_usage():
    rt = build_runtime()
    cmd = CommandEnvelope.make(issuer_card_id="c", tool="write_file", args={},
                               rationale="r", declared_risk=RiskLevel.LOW,
                               expected_effect="e")
    sk = rt.skills.observe_success("s1", "desc", [cmd], "env-sig", {})
    sk.state = CapabilityState.REFLEX
    sk.success_count = 3
    status, payload = LiveReadModels(rt).read("/read/corp/kpi")
    assert status == 200
    assert payload["reflex"]["status"] == "AVAILABLE"   # was UNAVAILABLE before the wire
    assert payload["reflex"]["rate"] == 1.0


def test_corp_kpi_still_unavailable_without_usage():
    # A fresh runtime has an empty library ⇒ honestly UNAVAILABLE (never a fake 0%).
    rt = build_runtime()
    _, payload = LiveReadModels(rt).read("/read/corp/kpi")
    assert payload["reflex"]["status"] == "UNAVAILABLE"


# --- wire 2: corp_risk_add through the one door ---------------------------------

def test_risk_proposal_routes_to_governed_record():
    rt = build_runtime()
    dispatcher = ProposalDispatcher(rt)   # no inbox/card needed for a corp record
    entry = RiskEntry(risk_id="rk1", job_id="job-a", client_id="acme",
                      likelihood=3, impact=4, tier=RiskLevel.HIGH,
                      description="vendor lock-in")
    res = dispatcher.dispatch(entry.risk_proposal())
    assert res["accepted"] is True and res["wired"] is True
    assert res["risk_id"] == "rk1" and "governed corp risk record" in res["reduction"]

    # the record is now in the trace-projected register (F7.7)
    proj = RiskRegisterProjection.from_trace(rt.runtime.trace)
    ids = [e.risk_id for e in proj.entries()]
    assert ids == ["rk1"]
    rk1 = proj.entries()[0]
    assert rk1.likelihood == 3 and rk1.impact == 4


def test_risk_proposal_carries_mandate_id():
    rt = build_runtime()
    dispatcher = ProposalDispatcher(rt)
    payload = RiskEntry(risk_id="rk2", likelihood=1, impact=1).risk_proposal()
    payload["mandate_id"] = "m-alpha"
    dispatcher.dispatch(payload)
    stamped = [ev for ev in rt.runtime.trace.replay()
               if ev.get("event_type") == "risk_entry" and ev.get("mandate_id") == "m-alpha"]
    assert stamped


def test_invalid_risk_args_fail_closed():
    rt = build_runtime()
    dispatcher = ProposalDispatcher(rt)
    bad = {"kind": "act", "tool": "corp_risk_add",
           "args": {"risk_id": "x", "likelihood": 99}}    # out of 1..5
    with pytest.raises(ProposalRejected):
        dispatcher.dispatch(bad)


def test_non_corp_act_still_needs_inbox():
    # a normal tool act with no inbox/card stays the honest unwired path (F5.2).
    rt = build_runtime()
    res = ProposalDispatcher(rt).dispatch({"kind": "act", "tool": "write_file", "args": {}})
    assert res["wired"] is False

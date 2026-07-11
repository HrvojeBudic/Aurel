"""F7.7 seal — Risk Register v1 (governed entries + likelihood×impact heatmap).

A risk is a governed trace record (a hash-chained praxis event), not ephemeral
state — the register + heatmap are pure projections that survive replay. Entry-in
is a one-door proposal; deletion is a status change, never a pop; auto-detection is
a declared LATER seam.
"""
from __future__ import annotations

import pytest

from agentic_runtime.core_types import RiskLevel
from agentic_runtime.corp import (
    RiskEntry,
    RiskRegisterProjection,
    RiskStatus,
    record_risk,
)
from agentic_runtime.corp.risk_register import CLAIMS_AUTO_RISK_DETECTION
from agentic_runtime.trace import InMemoryTraceLedger


def _entry(risk_id="r1", likelihood=3, impact=4, status=RiskStatus.OPEN, **kw):
    return RiskEntry(risk_id=risk_id, job_id="job-a", client_id="acme",
                     description=kw.get("description", "vendor lock-in | risk"),
                     likelihood=likelihood, impact=impact, tier=RiskLevel.HIGH,
                     mitigation=kw.get("mitigation", "diversify"), status=status)


# --- no-overclaim / validation ----------------------------------------------------

def test_entry_validates_scale_and_id():
    with pytest.raises(ValueError):
        RiskEntry(risk_id="")
    with pytest.raises(ValueError):
        RiskEntry(risk_id="r", likelihood=0)
    with pytest.raises(ValueError):
        RiskEntry(risk_id="r", impact=6)


def test_score_is_likelihood_times_impact():
    assert _entry(likelihood=3, impact=4).score == 12


# --- summary round-trip survives free text ----------------------------------------

def test_summary_roundtrip_with_pipes_in_text():
    e = _entry(description="a|b|c", mitigation="x|y")
    back = RiskEntry.from_summary(e.to_summary())
    assert back is not None and back.to_dict() == e.to_dict()   # pipes survive


def test_from_summary_rejects_foreign_marks():
    assert RiskEntry.from_summary("CVIO|m|reason") is None       # not a risk mark


# --- governed write ⇒ trace record ⇒ projection -----------------------------------

def test_record_writes_a_governed_praxis_event():
    trace = InMemoryTraceLedger("run-x")
    before = len(list(trace.replay()))
    record_risk(trace, _entry(), mandate_id="m-alpha")
    events = [ev for ev in trace.replay() if ev.get("event_type") == "risk_entry"]
    assert len(events) == 1
    assert events[0]["kind"] == "praxis_event" and events[0]["mandate_id"] == "m-alpha"
    assert len(list(trace.replay())) == before + 1              # exactly one append


def test_projection_rebuilds_register_from_trace():
    trace = InMemoryTraceLedger("run-x")
    record_risk(trace, _entry("r1", 2, 3))
    record_risk(trace, _entry("r2", 5, 5))
    proj = RiskRegisterProjection.from_trace(trace)
    ids = [e.risk_id for e in proj.entries()]
    assert ids == ["r1", "r2"]                                  # deterministic order
    r2 = next(e for e in proj.entries() if e.risk_id == "r2")
    assert r2.likelihood == 5 and r2.impact == 5


def test_heatmap_from_projection():
    trace = InMemoryTraceLedger("run-x")
    record_risk(trace, _entry("r1", 3, 4))
    record_risk(trace, _entry("r2", 3, 4))                      # same cell
    record_risk(trace, _entry("r3", 1, 1))
    heat = RiskRegisterProjection.from_trace(trace).heatmap()
    cell = next(c for c in heat if c["likelihood"] == 3 and c["impact"] == 4)
    assert cell["count"] == 2 and cell["score"] == 12
    assert any(c["likelihood"] == 1 and c["impact"] == 1 for c in heat)


# --- deletion is a status change, never a pop -------------------------------------

def test_deletion_is_a_status_change():
    trace = InMemoryTraceLedger("run-x")
    record_risk(trace, _entry("r1", 3, 4, status=RiskStatus.OPEN))
    record_risk(trace, _entry("r1", 3, 4, status=RiskStatus.CLOSED))  # "delete" = close
    proj = RiskRegisterProjection.from_trace(trace)
    # the risk_id is still present (history kept), latest status wins
    latest = next(e for e in proj.entries() if e.risk_id == "r1")
    assert latest.status is RiskStatus.CLOSED
    assert proj.active() == []                                  # closed ⇒ off the heatmap
    assert proj.heatmap() == []


# --- one door + LATER seam --------------------------------------------------------

def test_risk_proposal_is_one_door_payload():
    payload = _entry().risk_proposal()
    assert payload["kind"] == "act" and payload["tool"] == "corp_risk_add"
    assert payload["args"]["risk_id"] == "r1"


def test_auto_detection_is_a_declared_later_seam():
    trace = InMemoryTraceLedger("run-x")
    record_risk(trace, _entry())
    d = RiskRegisterProjection.from_trace(trace).to_dict()
    assert d["claims_auto_detection"] is False and CLAIMS_AUTO_RISK_DETECTION is False

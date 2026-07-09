"""F5.5 seal — the HQ.Command read-model (run status + approvals + budget + Watchtower seam).

A pure composition of live views: run status and the approval audit come from the
trace; budget burn from the live ledger; the Watchtower alert feed is an explicit
UNAVAILABLE seam (F7), never a fabricated alert. Zero writes.
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RuntimeStatusTransitionRecord
from agentic_runtime.front_server import (
    CLAIMS_WATCHTOWER_LIVE,
    HQCommandReadModel,
    LiveReadModels,
)


def _seed_transitions(rt):
    trace = rt.runtime.trace
    for run_id, frm, to, rc in (
        ("run-a", "planned", "running", "dispatch"),
        ("run-a", "running", "succeeded", "verified"),
        ("run-b", "planned", "blocked", "approval_required"),
    ):
        trace.append_status_transition(RuntimeStatusTransitionRecord.make(
            run_id=run_id, intent_id="i", issuer_card_id="card-1",
            from_status=frm, to_status=to, reason_code=rc, message="m"))


# --- run status projection --------------------------------------------------------

def test_run_status_is_latest_per_run():
    rt = build_runtime()
    _seed_transitions(rt)
    hq = HQCommandReadModel.from_runtime(rt)
    runs = {r["run_id"]: r for r in hq.run_status()}
    assert runs["run-a"]["status"] == "succeeded"      # latest transition wins
    assert runs["run-a"]["transitions"] == 2
    assert runs["run-b"]["status"] == "blocked"
    assert runs["run-b"]["reason_code"] == "approval_required"
    # deterministic order by run_id
    assert [r["run_id"] for r in hq.run_status()] == ["run-a", "run-b"]


# --- budget burn (live snapshot) --------------------------------------------------

def test_budget_burn_present_and_live():
    rt = build_runtime()
    hq = HQCommandReadModel.from_runtime(rt)
    budget = hq.budget()
    assert budget["status"] == "AVAILABLE"
    assert "policy" in budget and "usage" in budget


def test_budget_unavailable_without_ledger():
    hq = HQCommandReadModel(trace=build_runtime().runtime.trace, budget=None)
    assert hq.budget()["status"] == "UNAVAILABLE"


# --- approvals (audit + optional pending) ----------------------------------------

def test_approvals_audit_from_trace_pending_seam():
    rt = build_runtime()
    hq = HQCommandReadModel.from_runtime(rt)  # no inbox injected
    ap = hq.approvals()
    assert isinstance(ap["audit"], list)
    assert ap["pending"] == [] and ap["pending_source"] == "unavailable"


def test_pending_present_when_inbox_injected():
    rt = build_runtime()

    class _StubInbox:
        def pending(self):
            return [{"request_id": "r1", "tool": "x"}]

    hq = HQCommandReadModel.from_runtime(rt, inbox=_StubInbox())
    ap = hq.approvals()
    assert ap["pending_source"] == "inbox"
    assert ap["pending"][0]["request_id"] == "r1"


# --- Watchtower / predictive declared seams --------------------------------------

def test_watchtower_and_predictive_are_unavailable_seams():
    rt = build_runtime()
    d = HQCommandReadModel.from_runtime(rt).to_dict()
    assert d["watchtower"]["status"] == "UNAVAILABLE" and d["watchtower"]["owner"] == "F7"
    assert d["watchtower"]["alerts"] == []
    assert d["predictive"]["status"] == "UNAVAILABLE"
    assert d["claims_watchtower_live"] is False and CLAIMS_WATCHTOWER_LIVE is False


# --- purity + live-read integration ----------------------------------------------

def test_hq_command_is_zero_write():
    rt = build_runtime()
    _seed_transitions(rt)
    before = len(list(rt.runtime.trace.replay()))
    HQCommandReadModel.from_runtime(rt).to_dict()
    after = len(list(rt.runtime.trace.replay()))
    assert after == before


def test_hq_command_via_live_read_registry():
    rt = build_runtime()
    _seed_transitions(rt)
    status, payload = LiveReadModels(rt).read("/read/hq/command")
    assert status == 200 and payload["live"] is True and payload["model"] == "hq/command"
    assert {r["run_id"] for r in payload["runs"]} == {"run-a", "run-b"}
    assert payload["budget"]["status"] == "AVAILABLE"
    assert payload["watchtower"]["status"] == "UNAVAILABLE"
    assert payload["claims_watchtower_live"] is False

"""F5.9 seal — the derived Front v1 exit seal + north-star run projection.

Derived, never declared: SEALED only when every slice has both an importable module
and a present report; a missing report BLOCKS deterministically. Overclaim guards
are hard-wired False; the north-star run is replayable from the trace.
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.front_projection import FrontRunProjection
from agentic_runtime.front_seal import (
    F5_SLICES,
    F5_UNAVAILABLE,
    ItemStatus,
    SealStatus,
    build_f5_exit_seal,
)
from agentic_runtime.front_server import (
    ConversationEngine,
    ProposalDispatcher,
    SignalMessage,
    WorkOpsMessage,
)


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "answer", "stub-model", {"total_tokens": 7}


# --- derived seal ---------------------------------------------------------------

def test_seal_is_sealed_with_all_slices_present():
    seal = build_f5_exit_seal()
    assert seal.status is SealStatus.SEALED and seal.sealed is True
    assert all(i.status is ItemStatus.PASSED for i in seal.items)
    assert len(seal.items) == len(F5_SLICES) == 12


def test_missing_report_blocks_deterministically(tmp_path):
    # A reports dir with no F5 reports ⇒ every item BLOCKED ⇒ seal BLOCKED.
    seal = build_f5_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED and seal.sealed is False
    assert all(i.status is ItemStatus.BLOCKED for i in seal.items)
    # ...but every module still imports (only the reports are missing).
    assert all(i.module_present for i in seal.items)


def test_all_overclaim_guards_false():
    seal = build_f5_exit_seal()
    assert seal.claims_remote_websocket is False
    assert seal.claims_wss_tls is False
    assert seal.claims_aureleu_dispatcher_live is False
    assert seal.claims_watchtower_live is False
    assert seal.claims_workops_ai_editor is False
    assert seal.claims_library_time_travel is False
    d = seal.to_dict()
    assert all(d[k] is False for k in d if k.startswith("claims_"))


def test_unavailable_registry_has_owners():
    seal = build_f5_exit_seal()
    assert len(seal.unavailable) == len(F5_UNAVAILABLE) >= 5
    ids = {u.surface_id for u in seal.unavailable}
    assert {"wss_tls_remote_transport", "aureleu_role_fluid_dispatcher",
            "watchtower_alerts", "workops_ai_editor", "library_time_travel"} <= ids
    assert all(u.reason and u.future_owner for u in seal.unavailable)


# --- north-star run projection --------------------------------------------------

def test_north_star_run_is_replayable_from_trace():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    d = ProposalDispatcher(rt, conversation_engine=engine)
    # operator intent through Signal, and a WorkOPS turn — both governed, one door.
    d.dispatch(SignalMessage("signal:main", "op", "operator", "m1", (), "hello").to_proposal())
    d.dispatch(WorkOpsMessage("task-1", "op", "operator", "m1", (), "work").to_proposal())

    proj = FrontRunProjection(rt).to_dict()
    assert proj["replayable"] is True
    assert [e["role"] for e in proj["signal_history"]] == ["operator", "assistant"]
    assert proj["workops_tasks"][0]["task_id"] == "task-1"
    assert "min_truth_state" in proj["library"] and proj["library"]["assets_count"] > 0


def test_projection_is_zero_write():
    rt = build_runtime()
    before = len(list(rt.runtime.trace.replay()))
    FrontRunProjection(rt).to_dict()
    after = len(list(rt.runtime.trace.replay()))
    assert after == before

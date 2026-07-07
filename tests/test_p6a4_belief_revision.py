"""A4 seal — belief revision: update / retract / forget.

Proves the A4 invariants:

1. `mem_update` supersedes the prior version: old `superseded_by` set + intervals
   closed, new `revises` old; A0 `belief_history` / `is_current` now reflect it,
   and A2's edge-view (`detect_supersession_chain`) agrees with the record-view.
2. `retract` closes intervals honestly (no longer current), record preserved.
3. `mem_delete` == non-destructive forget (record inactive but kept for audit) and
   is FORBIDDEN on protected memory (canon/policy, rejected/audit).
4. An agent cannot elevate trust via update (agent → verified is denied).
5. Unknown id fails closed.
6. Exactly one governance row per op; zero `StateTransitionRecord`.
7. No-collapse: unrelated records + existing write/promote/link/retrieve unchanged.
"""

from __future__ import annotations

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.memory_asof import AsOfView
from agentic_runtime.memory_bitemporal import BiTemporalStamp
from agentic_runtime.memory_governance import MemoryRevisionRequest
from agentic_runtime.memory_graph import detect_supersession_chain
from agentic_runtime.memory_revision import retract
from agentic_runtime.memory_tools import MemoryToolSession
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a4"


def _harness():
    trace = InMemoryTraceLedger(run_id=RUN)
    fabric = MemoryFabric()
    fabric.bind_trace(trace)
    budget = BudgetLedger()
    return fabric, trace, budget


def _seed(fabric, content, *, truth="raw", writer="operator"):
    return fabric.request_write(MemoryWriteRequest(
        content=content, proposed_truth_state=MemoryTruthState(truth),
        writer_kind=writer, source_run_id=RUN)).record


def _rev_rows(trace, op):
    return [e for e in trace.replay()
            if e["kind"] == "memory_governance" and e["action"] == op]


def _state_rows(trace):
    return [e for e in trace.replay() if e["kind"] == "state_transition"]


def _is_current(rec):
    return BiTemporalStamp.from_record(rec).is_current()


# 1 ─ update supersedes; record + edge views of supersession agree.
def test_update_supersedes_and_views_agree():
    fabric, trace, budget = _harness()
    old = _seed(fabric, "the meeting is on Monday", truth="candidate")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    result = session.invoke("mem_update", {
        "memory_id": old.memory_id, "content": "the meeting is on Tuesday"})
    new_id = result["new_memory_id"]

    assert result["ok"] is True and result["verdict"] == "allow"
    assert new_id and new_id != old.memory_id
    new = fabric.by_id[new_id]

    # Record-field supersession + interval closure (A0 fields now written).
    assert old.superseded_by == new_id
    assert old.valid_to is not None and old.transaction_to is not None
    assert new.revises == old.memory_id
    assert _is_current(old) is False
    assert _is_current(new) is True

    # A0 belief_history is now live and consistent from either end.
    view = AsOfView.from_fabric(fabric)
    chain_records = [r.memory_id for r in view.belief_history(new_id)]
    assert chain_records == [old.memory_id, new_id]
    assert [r.memory_id for r in view.belief_history(old.memory_id)] == [old.memory_id, new_id]

    # A2 reconciliation: the edge-view agrees with the record-view.
    assert detect_supersession_chain(fabric.graph, old.memory_id) == [old.memory_id, new_id]

    # One governance row for the op; no StateTransitionRecord; one charge.
    assert len(_rev_rows(trace, "update")) == 1
    assert _rev_rows(trace, "update")[0]["verdict"] == "allow"
    assert len(_state_rows(trace)) == 0
    assert budget.memory_writes == 1
    assert budget.sandbox_executions == 0


# 2 ─ retract closes intervals honestly; record preserved.
def test_retract_closes_intervals():
    fabric, trace, budget = _harness()
    rec = _seed(fabric, "temporary belief", truth="candidate")

    decision = retract(fabric, MemoryRevisionRequest(
        op="retract", memory_id=rec.memory_id,
        writer_kind="operator", source_run_id=RUN))

    assert decision.allowed is True
    assert _is_current(rec) is False
    assert rec.valid_to is not None and rec.transaction_to is not None
    assert rec.memory_id in fabric.by_id          # preserved, not deleted
    assert len(_rev_rows(trace, "retract")) == 1
    assert len(_state_rows(trace)) == 0


# 3 ─ mem_delete == non-destructive forget; forbidden on protected memory.
def test_forget_non_destructive_and_forbidden_on_protected():
    fabric, trace, budget = _harness()
    ephemeral = _seed(fabric, "forgettable note")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    forgotten = session.invoke("mem_delete", {"memory_id": ephemeral.memory_id})
    assert forgotten["ok"] is True and forgotten["op"] == "forget"
    # Non-destructive: the record stays for audit, but is now inactive.
    assert ephemeral.memory_id in fabric.by_id
    assert fabric.by_id[ephemeral.memory_id].truth_state is MemoryTruthState.EXPIRED
    assert fabric.by_id[ephemeral.memory_id].is_active() is False

    # FORBIDDEN on canon (policy/identity).
    canon = fabric.assert_canon("never forget this policy", source="operator")
    denied_canon = session.invoke("mem_delete", {"memory_id": canon.memory_id})
    assert denied_canon["ok"] is False
    assert denied_canon["reason_code"] == "revision_forbidden_on_protected"
    assert canon.memory_id in fabric.by_id and fabric.by_id[canon.memory_id].is_active()

    # FORBIDDEN on rejected (audit): a denied write is kept as a rejected record.
    fabric.request_write(MemoryWriteRequest(
        content="agent tries canon", proposed_truth_state=MemoryTruthState.CANON,
        writer_kind="agent", source_run_id=RUN))
    rejected_id = fabric.rejected[-1].memory_id
    denied_audit = session.invoke("mem_delete", {"memory_id": rejected_id})
    assert denied_audit["ok"] is False
    assert denied_audit["reason_code"] == "revision_forbidden_on_protected"


# 4 ─ an agent cannot elevate trust via update.
def test_agent_cannot_elevate_trust_via_update():
    fabric, trace, budget = _harness()
    old = _seed(fabric, "unverified claim", truth="candidate")
    agent = MemoryToolSession(fabric, budget, writer_kind="agent")

    result = agent.invoke("mem_update", {
        "memory_id": old.memory_id, "content": "now I declare it true",
        "truth_state": "verified"})

    assert result["ok"] is False
    assert result["reason_code"] == "agent_cannot_write_restricted"
    # Old belief untouched: not superseded, still current, no successor stored.
    assert old.superseded_by is None
    assert _is_current(old) is True
    assert result["new_memory_id"] == ""
    assert budget.memory_writes == 1              # the attempt is still charged once


# 5 ─ unknown id fails closed for both revision tools.
def test_unknown_id_fails_closed():
    fabric, trace, budget = _harness()
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    upd = session.invoke("mem_update", {"memory_id": "mem_nope", "content": "x"})
    assert upd["ok"] is False and upd["reason_code"] == "unknown_memory"

    dele = session.invoke("mem_delete", {"memory_id": "mem_nope"})
    assert dele["ok"] is False and dele["reason_code"] == "unknown_memory"


# 6 ─ no-collapse: unrelated records + write/promote/link/retrieve unchanged.
def test_no_collapse_unrelated_records_untouched():
    fabric, trace, budget = _harness()
    keep = _seed(fabric, "stable fact about the sky", truth="candidate")
    old = _seed(fabric, "changeable fact", truth="candidate")
    # promote + link still work alongside revision.
    fabric.promote(keep.memory_id, MemoryTruthState.VERIFIED,
                   evidence_refs=["ev"], actor="operator")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")
    session.invoke("mem_update", {"memory_id": old.memory_id, "content": "changed"})

    # The unrelated record is completely untouched by the revision.
    assert keep.superseded_by is None
    assert _is_current(keep) is True
    assert keep.truth_state is MemoryTruthState.VERIFIED
    # Retrieval still surfaces active current records.
    contents = [r.content for r in fabric.retrieve("sky", k=5)]
    assert "stable fact about the sky" in contents

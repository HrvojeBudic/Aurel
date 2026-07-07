"""A4 — Belief revision: governed update / retract / forget.

Three governed primitives that revise an *existing* memory without ever
destroying the audit trail:

* ``apply_update`` — supersede a belief with a new version. The old record's
  belief interval is closed (``valid_to``/``transaction_to`` = now), it points
  forward (``superseded_by``) and is marked ``DEPRECATED``; the new version points
  back (``revises``). The new belief is re-scored through ``evaluate_write`` (so an
  agent can never elevate trust via an "update"). A ``SUPERSEDES`` edge is also
  written so A2's edge-view and the record-view of supersession **agree**, which
  in turn makes A0's ``belief_history`` / ``is_current`` live.
* ``retract`` — withdraw a belief: close its intervals and mark it ``DEPRECATED``.
* ``forget`` — retention only: mark the record ``EXPIRED`` (inactive) and close the
  transaction interval. **Non-destructive** — the record and its governed history
  stay in the store; nothing is popped or deleted.

Every op emits exactly **one** ``MemoryGovernanceRecord`` (``action`` =
``update``/``retract``/``forget``) — the trace stays the single source of truth —
and produces no ``StateTransitionRecord``. ``FORGET``/revision is fail-closed on
protected memory (canon/policy, rejected/audit) and on unknown ids.

Durability note (A3): to keep a single governance row per op, these primitives
bypass the ``request_write``/``link`` funnels and store the new version via the
*base* ``MemoryFabric._store`` — so on a ``DurableMemoryFabric`` revision mutations
are NOT written to the JSONL cache. The trace records every revision; projecting
those revision rows back onto the durable store is deferred (A7/A8).
"""

from __future__ import annotations

from typing import Any

from .core_types import (MemoryGovernanceRecord, MemoryTruthState, TruthStatus,
                         now)
from .memory import MemoryFabric
from .memory_governance import MemoryRevisionDecision, MemoryRevisionRequest


def apply_update(fabric: Any, req: MemoryRevisionRequest) -> MemoryRevisionDecision:
    req.op = "update"
    target = fabric.by_id.get(req.memory_id)
    decision = fabric.policy.evaluate_revision(req, target, getattr(fabric, "_trace", None))
    _trace_revision(fabric, decision, req)
    if decision.allowed:
        _execute_update(fabric, decision, req)
    return decision


def retract(fabric: Any, req: MemoryRevisionRequest) -> MemoryRevisionDecision:
    req.op = "retract"
    target = fabric.by_id.get(req.memory_id)
    decision = fabric.policy.evaluate_revision(req, target, getattr(fabric, "_trace", None))
    _trace_revision(fabric, decision, req)
    if decision.allowed and decision.target is not None:
        t = now()
        rec = decision.target
        rec.valid_to = t
        rec.transaction_to = t              # belief withdrawn ⇒ no longer current
        rec.truth_status = TruthStatus.DEPRECATED
    return decision


def forget(fabric: Any, req: MemoryRevisionRequest) -> MemoryRevisionDecision:
    req.op = "forget"
    target = fabric.by_id.get(req.memory_id)
    decision = fabric.policy.evaluate_revision(req, target, getattr(fabric, "_trace", None))
    _trace_revision(fabric, decision, req)
    if decision.allowed and decision.target is not None:
        rec = decision.target
        # Retention only: mark inactive, keep the record + its history for audit.
        rec.transaction_to = now()
        rec.truth_state = MemoryTruthState.EXPIRED
        rec.truth_status = TruthStatus.DEPRECATED
    return decision


# --------------------------------------------------------------------------- #
#  internals
# --------------------------------------------------------------------------- #
def _execute_update(fabric: Any, decision: MemoryRevisionDecision,
                    req: MemoryRevisionRequest) -> None:
    from .memory_graph import MemoryEdge, MemoryRelation

    old = decision.target
    new = decision.new_record
    if old is None or new is None:            # defensive; allow ⇒ both present
        return
    t = now()
    # Close the old belief and point it forward.
    old.valid_to = t
    old.transaction_to = t
    old.superseded_by = new.memory_id
    old.truth_status = TruthStatus.DEPRECATED
    # The new version revises the old and begins its belief now.
    new.revises = old.memory_id
    new.transaction_from = t
    # Store the successor via the BASE store (no durable mirror — see module doc).
    MemoryFabric._store(fabric, new)
    # Reconcile with A2: new SUPERSEDES old, so edge-view and record-view agree.
    edge = MemoryEdge.make(
        from_id=new.memory_id,
        to_id=old.memory_id,
        relation=MemoryRelation.SUPERSEDES,
        writer_kind=req.writer_kind,
        created_by=req.created_by or req.writer_kind,
        source_run_id=req.source_run_id,
        source_trace_ids=list(req.source_trace_ids),
        evidence_refs=list(req.evidence_refs),
        confidence=new.confidence,
    )
    fabric.graph.add(edge)


def _trace_revision(fabric: Any, decision: MemoryRevisionDecision,
                    req: MemoryRevisionRequest) -> None:
    """Anchor exactly one memory-governance row for the revision (allow or deny)."""
    trace = getattr(fabric, "_trace", None)
    if trace is None or not hasattr(trace, "append_memory_event"):
        return
    target = decision.target
    from_state = target.truth_state.value if target is not None else ""
    if decision.op == "update" and decision.allowed and decision.new_record is not None:
        to_state = decision.new_record.truth_state.value
        details = {"target_id": req.memory_id,
                   "new_memory_id": decision.new_record.memory_id}
    elif decision.op == "retract":
        to_state = "deprecated"
        details = {"target_id": req.memory_id}
    elif decision.op == "forget":
        to_state = MemoryTruthState.EXPIRED.value
        details = {"target_id": req.memory_id}
    else:
        to_state = from_state
        details = {"target_id": req.memory_id}
    rec = MemoryGovernanceRecord.make(
        run_id=req.source_run_id or "",
        agent_id=req.created_by or req.writer_kind,
        action=decision.op,
        verdict="allow" if decision.allowed else "deny",
        memory_id=req.memory_id,
        from_state=from_state,
        to_state=to_state,
        reason_code=decision.reason_code,
        message=decision.message,
        evidence_refs=list(req.evidence_refs),
        source_trace_ids=list(req.source_trace_ids),
        confidence=req.confidence,
        details=details,
    )
    trace.append_memory_event(rec)


__all__ = ["apply_update", "retract", "forget"]

"""P0.9 — Memory Write Governance & Provenance Seal tests."""

from __future__ import annotations

import pytest

from agentic_runtime import (
    MemoryFabric,
    MemoryTruthState,
    MemoryWritePolicy,
    MemoryWriteRequest,
    build_runtime,
)
from agentic_runtime.core_types import Intent, TruthStatus
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_test"


def _fabric():
    trace = InMemoryTraceLedger(run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(trace)
    return fab, trace


def _req(**kw):
    base = dict(content="a fact", source_run_id=RUN)
    base.update(kw)
    return MemoryWriteRequest(**base)


def _gov_rows(trace):
    return [r for r in trace.replay() if r.get("kind") == "memory_governance"]


# --------------------------------------------------------------------------- #
# 1. Agent cannot write verified/procedural/canon directly.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("state", [
    MemoryTruthState.VERIFIED,
    MemoryTruthState.PROCEDURAL,
    MemoryTruthState.CANON,
])
def test_agent_cannot_write_restricted_directly(state):
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="agent", proposed_truth_state=state))
    assert not dec.allowed
    assert dec.reason_code == "agent_cannot_write_restricted"
    assert fab.stats()["L3"] == 0 and fab.stats()["L5_canon"] == 0


# --------------------------------------------------------------------------- #
# 2. Memory write requires a valid trace reference.
# --------------------------------------------------------------------------- #
def test_write_requires_trace_reference():
    fab, trace = _fabric()
    dec = fab.request_write(_req(source_run_id="", writer_kind="runtime"))
    assert not dec.allowed
    assert dec.reason_code == "missing_trace_reference"
    # The denial is itself recorded.
    assert any(r["verdict"] == "deny" for r in _gov_rows(trace))


def test_write_rejects_unknown_run_id():
    fab, _ = _fabric()
    dec = fab.request_write(_req(source_run_id="some_other_run", writer_kind="runtime"))
    assert not dec.allowed
    assert dec.reason_code == "invalid_trace_reference"


def test_write_rejects_unknown_trace_ids():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 source_trace_ids=["txn_does_not_exist"]))
    assert not dec.allowed
    assert dec.reason_code == "invalid_trace_reference"


# --------------------------------------------------------------------------- #
# 3. Failed runs cannot create success/procedural memory.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("state", [
    MemoryTruthState.VERIFIED,
    MemoryTruthState.PROCEDURAL,
])
def test_failed_run_cannot_write_success(state):
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=state,
                                 run_succeeded=False))
    assert not dec.allowed
    assert dec.reason_code == "failed_run_cannot_write_success"


# --------------------------------------------------------------------------- #
# 4. Untrusted tool output can only become candidate.
# --------------------------------------------------------------------------- #
def test_untrusted_output_stays_candidate():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.VERIFIED,
                                 trust="untrusted"))
    assert dec.allowed
    assert dec.effective_truth_state is MemoryTruthState.CANDIDATE
    assert dec.record.truth_state is MemoryTruthState.CANDIDATE


# --------------------------------------------------------------------------- #
# 5. Candidate can be promoted to verified with evidence.
# --------------------------------------------------------------------------- #
def test_candidate_promotes_to_verified_with_evidence():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANDIDATE))
    mid = dec.record.memory_id

    no_ev = fab.promote(mid, MemoryTruthState.VERIFIED)
    assert not no_ev.allowed
    assert no_ev.reason_code == "promotion_requires_evidence"

    ok = fab.promote(mid, MemoryTruthState.VERIFIED, evidence_refs=["txn_1"])
    assert ok.allowed
    assert fab.by_id[mid].truth_state is MemoryTruthState.VERIFIED


# --------------------------------------------------------------------------- #
# 6. Procedural memory requires repeated successful traces.
# --------------------------------------------------------------------------- #
def test_procedural_requires_repeated_success():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANDIDATE))
    mid = dec.record.memory_id
    fab.promote(mid, MemoryTruthState.VERIFIED, evidence_refs=["txn_1"])

    once = fab.promote(mid, MemoryTruthState.PROCEDURAL, success_trace_ids=["txn_1"])
    assert not once.allowed
    assert once.reason_code == "promotion_requires_repeated_success"

    twice = fab.promote(mid, MemoryTruthState.PROCEDURAL,
                        success_trace_ids=["txn_1", "txn_2"])
    assert twice.allowed
    assert fab.by_id[mid].truth_state is MemoryTruthState.PROCEDURAL


# --------------------------------------------------------------------------- #
# 7. Canon memory requires explicit approval.
# --------------------------------------------------------------------------- #
def test_canon_requires_explicit_approval():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANDIDATE))
    mid = dec.record.memory_id
    fab.promote(mid, MemoryTruthState.VERIFIED, evidence_refs=["txn_1"])
    fab.promote(mid, MemoryTruthState.PROCEDURAL,
                success_trace_ids=["txn_1", "txn_2"])

    denied = fab.promote(mid, MemoryTruthState.CANON, approved=False)
    assert not denied.allowed
    assert denied.reason_code == "promotion_requires_approval"

    approved = fab.promote(mid, MemoryTruthState.CANON, approved=True)
    assert approved.allowed
    assert fab.by_id[mid].truth_state is MemoryTruthState.CANON


def test_agent_cannot_assert_canon_without_approval_via_write():
    fab, _ = _fabric()
    # Even a runtime writer cannot mint canon without approval.
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANON))
    assert not dec.allowed
    assert dec.reason_code == "canon_requires_approval"


# --------------------------------------------------------------------------- #
# 8. Memory write and denial are traced.
# --------------------------------------------------------------------------- #
def test_memory_write_is_traced():
    fab, trace = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.EPISODIC))
    assert dec.allowed
    rows = _gov_rows(trace)
    assert any(r["verdict"] == "allow" and r["action"] == "write" for r in rows)


def test_memory_write_denial_is_traced():
    fab, trace = _fabric()
    fab.request_write(_req(writer_kind="agent",
                           proposed_truth_state=MemoryTruthState.VERIFIED))
    rows = _gov_rows(trace)
    assert any(r["verdict"] == "deny"
               and r["reason_code"] == "agent_cannot_write_restricted"
               for r in rows)


def test_promotion_is_traced():
    fab, trace = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANDIDATE))
    fab.promote(dec.record.memory_id, MemoryTruthState.VERIFIED,
                evidence_refs=["txn_1"])
    assert any(r["action"] == "promote" and r["verdict"] == "allow"
               for r in _gov_rows(trace))


# --------------------------------------------------------------------------- #
# 9. Expired memory is not active.
# --------------------------------------------------------------------------- #
def test_expired_memory_is_not_active():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANDIDATE,
                                 expiry_policy={"kind": "ttl", "ttl_s": 0}))
    rec = dec.record
    assert dec.allowed
    assert rec.is_expired()
    assert not rec.is_active()
    # Expired records are excluded from retrieval.
    assert rec not in fab.retrieve(rec.content, k=10)


# --------------------------------------------------------------------------- #
# 10. Provenance: no record is created without provenance.
# --------------------------------------------------------------------------- #
def test_every_record_has_provenance():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 created_by="card_007",
                                 source_command_id="cmd_42",
                                 proposed_truth_state=MemoryTruthState.EPISODIC,
                                 confidence=0.8))
    rec = dec.record
    assert rec.memory_id
    assert rec.created_at > 0
    assert rec.created_by == "card_007"
    assert rec.source_run_id == RUN
    assert rec.source_command_id == "cmd_42"
    assert rec.truth_state is MemoryTruthState.EPISODIC
    assert rec.promotion_state == "none"  # promotion tracked only for L3+ states
    assert isinstance(rec.expiry_policy, dict)


def test_candidate_record_promotion_state():
    fab, _ = _fabric()
    dec = fab.request_write(_req(writer_kind="runtime",
                                 proposed_truth_state=MemoryTruthState.CANDIDATE))
    assert dec.record.promotion_state == "candidate"


# --------------------------------------------------------------------------- #
# Policy unit-level: pure decision logic, no trace bound.
# --------------------------------------------------------------------------- #
def test_policy_illegal_promotion():
    pol = MemoryWritePolicy()
    ok, code, _ = pol.evaluate_promotion(
        MemoryTruthState.CANDIDATE, MemoryTruthState.CANON,
        evidence_refs=["e"], success_trace_ids=["t"], approved=True)
    assert not ok
    assert code == "illegal_promotion"


# --------------------------------------------------------------------------- #
# Integration: a full governed run produces only governed, traced memory and
# never canon/procedural from the agent path; demo-style assert_canon works.
# --------------------------------------------------------------------------- #
def test_kernel_run_writes_only_governed_memory(tmp_path):
    # Default planner emits a read-only list_dir plan, which still drives the
    # governed runtime memory writes we care about here.
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(),
    )
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope, RiskLevel
    card = AgentCard.make(
        name="A", agent_class=AgentClass.EXECUTION, mission="m",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["write_file", "read_file", "list_dir"],
    )
    entity = kernel.spawn(card)
    entity.run(Intent.make("inspect the workspace"))

    # No agent-authored record is verified/procedural/canon.
    for rec in kernel.memory.by_id.values():
        if rec.created_by == card.id:
            assert rec.truth_state in (MemoryTruthState.RAW, MemoryTruthState.EPISODIC)
        assert rec.source_run_id, "record missing provenance run id"

    # Every memory mutation appears in the trace.
    gov = [r for r in kernel.trace.replay() if r.get("kind") == "memory_governance"]
    assert gov, "memory writes must be traced"


def test_assert_canon_still_works(tmp_path):
    kernel = build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path)))
    rec = kernel.memory.assert_canon("never delete prod", source="operator")
    assert rec is not None
    assert rec.truth_state is MemoryTruthState.CANON
    assert rec.truth_status is TruthStatus.VERIFIED
    assert kernel.memory.stats()["L5_canon"] == 1

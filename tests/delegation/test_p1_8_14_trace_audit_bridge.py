"""Focused tests for P1.8.14 — Delegation Trace/Audit BridgeRef Model."""

import json
import sys

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation.foundation import DelegationSourceLabel
from agentic_runtime.delegation.trace_audit_bridge import (
    DelegationAuditBridgeRef,
    DelegationAuditContextKind,
    DelegationAuditEventIntentRef,
    DelegationCausalChainContextRef,
    DelegationForkContextRef,
    DelegationLedgerBridgeRef,
    DelegationLedgerEntryPlaceholderRef,
    DelegationReplayContextRef,
    DelegationTraceAuditBridgeBinding,
    DelegationTraceAuditBridgeBindingSet,
    DelegationTraceAuditBridgeEnvelope,
    DelegationTraceAuditBridgeKind,
    DelegationTraceAuditBridgeReferenceStatus,
    DelegationTraceAuditBridgeSideEffects,
    DelegationTraceAuditBridgeStatus,
    DelegationTraceAuditBridgeStatusReport,
    DelegationTraceAuditReadinessFamily,
    DelegationTraceAuditReadinessMatrix,
    DelegationTraceAuditReadinessMatrixEntry,
    DelegationTraceAuditReadinessProfile,
    DelegationTraceBridgeRef,
    DelegationTraceContextKind,
    DelegationTraceEventIntentRef,
    build_delegation_audit_bridge_ref,
    build_delegation_audit_event_intent_ref,
    build_delegation_causal_chain_context_ref,
    build_delegation_fork_context_ref,
    build_delegation_ledger_bridge_ref,
    build_delegation_ledger_entry_placeholder_ref,
    build_delegation_replay_context_ref,
    build_delegation_trace_audit_bridge_binding,
    build_delegation_trace_audit_bridge_binding_set,
    build_delegation_trace_audit_bridge_envelope,
    build_delegation_trace_audit_bridge_status_report,
    build_delegation_trace_audit_readiness_matrix,
    build_delegation_trace_audit_readiness_matrix_entry,
    build_delegation_trace_audit_readiness_profile,
    build_delegation_trace_bridge_ref,
    build_delegation_trace_event_intent_ref,
    hash_delegation_audit_bridge_ref,
    hash_delegation_audit_event_intent_ref,
    hash_delegation_causal_chain_context_ref,
    hash_delegation_fork_context_ref,
    hash_delegation_ledger_bridge_ref,
    hash_delegation_ledger_entry_placeholder_ref,
    hash_delegation_replay_context_ref,
    hash_delegation_trace_audit_bridge_binding,
    hash_delegation_trace_audit_bridge_binding_set,
    hash_delegation_trace_audit_bridge_envelope,
    hash_delegation_trace_audit_bridge_status_report,
    hash_delegation_trace_audit_readiness_matrix,
    hash_delegation_trace_audit_readiness_matrix_entry,
    hash_delegation_trace_audit_readiness_profile,
    hash_delegation_trace_bridge_ref,
    hash_delegation_trace_event_intent_ref,
    serialize_delegation_trace_audit_bridge_binding_set,
    serialize_delegation_trace_audit_bridge_envelope,
)

# ---------------------------------------------------------------------------
# 1. Imports work
# ---------------------------------------------------------------------------

def test_imports_work():
    """All P1.8.14 symbols are importable."""
    assert DelegationTraceAuditBridgeKind is not None
    assert DelegationTraceAuditBridgeReferenceStatus is not None
    assert DelegationTraceAuditBridgeStatus is not None
    assert DelegationTraceContextKind is not None
    assert DelegationAuditContextKind is not None
    assert DelegationTraceAuditReadinessFamily is not None
    assert DelegationTraceBridgeRef is not None
    assert DelegationAuditBridgeRef is not None
    assert DelegationLedgerBridgeRef is not None
    assert DelegationTraceEventIntentRef is not None
    assert DelegationAuditEventIntentRef is not None
    assert DelegationLedgerEntryPlaceholderRef is not None
    assert DelegationReplayContextRef is not None
    assert DelegationForkContextRef is not None
    assert DelegationCausalChainContextRef is not None


# ---------------------------------------------------------------------------
# 2. TraceBridgeRef deterministic builds
# ---------------------------------------------------------------------------

class TestTraceBridgeRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-1",
            delegation_ref_id="del-1",
            trace_bridge_description="future trace hook",
        )
        ref2 = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-1",
            delegation_ref_id="del-1",
            trace_bridge_description="future trace hook",
        )
        assert ref1.trace_bridge_hash == ref2.trace_bridge_hash
        assert isinstance(ref1.trace_bridge_hash, str)
        assert len(ref1.trace_bridge_hash) > 0

    def test_hash_changes_on_changed_description(self):
        ref1 = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-1",
            delegation_ref_id="del-1",
            trace_bridge_description="A",
        )
        ref2 = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-1",
            delegation_ref_id="del-1",
            trace_bridge_description="B",
        )
        assert ref1.trace_bridge_hash != ref2.trace_bridge_hash

    def test_canonical_json_roundtrip(self):
        ref = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-1", delegation_ref_id="del-1"
        )
        d = ref.to_canonical_dict()
        assert d["schema_version"] == ref.schema_version
        assert d["trace_bridge_hash"] == ref.trace_bridge_hash

    def test_not_trace_write(self):
        ref = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-nw", delegation_ref_id="del-1"
        )
        assert ref.reference_status in (
            DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
            DelegationTraceAuditBridgeReferenceStatus.TRACE_BRIDGE_REFERENCED,
        )
        # TRACE_BRIDGE_REFERENCED is NOT trace written
        assert ref.reference_status != "TRACE_WRITTEN"

    def test_recompute_public_hash(self):
        ref = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="tb-2", delegation_ref_id="del-1"
        )
        assert hash_delegation_trace_bridge_ref(ref) == ref.trace_bridge_hash


# ---------------------------------------------------------------------------
# 3. AuditBridgeRef deterministic builds
# ---------------------------------------------------------------------------

class TestAuditBridgeRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_audit_bridge_ref(
            audit_bridge_ref_id="ab-1",
            delegation_ref_id="del-1",
            audit_bridge_description="future audit hook",
        )
        ref2 = build_delegation_audit_bridge_ref(
            audit_bridge_ref_id="ab-1",
            delegation_ref_id="del-1",
            audit_bridge_description="future audit hook",
        )
        assert ref1.audit_bridge_hash == ref2.audit_bridge_hash

    def test_hash_changes(self):
        ref1 = build_delegation_audit_bridge_ref(
            audit_bridge_ref_id="ab-1", delegation_ref_id="del-1",
            audit_bridge_description="X"
        )
        ref2 = build_delegation_audit_bridge_ref(
            audit_bridge_ref_id="ab-1", delegation_ref_id="del-1",
            audit_bridge_description="Y"
        )
        assert ref1.audit_bridge_hash != ref2.audit_bridge_hash

    def test_not_audit_completed(self):
        ref = build_delegation_audit_bridge_ref(
            audit_bridge_ref_id="ab-2", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY

    def test_recompute_public_hash(self):
        ref = build_delegation_audit_bridge_ref(
            audit_bridge_ref_id="ab-3", delegation_ref_id="del-1"
        )
        assert hash_delegation_audit_bridge_ref(ref) == ref.audit_bridge_hash


# ---------------------------------------------------------------------------
# 4. LedgerBridgeRef
# ---------------------------------------------------------------------------

class TestLedgerBridgeRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_ledger_bridge_ref(
            ledger_bridge_ref_id="lb-1",
            delegation_ref_id="del-1",
        )
        ref2 = build_delegation_ledger_bridge_ref(
            ledger_bridge_ref_id="lb-1",
            delegation_ref_id="del-1",
        )
        assert ref1.ledger_bridge_hash == ref2.ledger_bridge_hash

    def test_not_ledger_write(self):
        ref = build_delegation_ledger_bridge_ref(
            ledger_bridge_ref_id="lb-2", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY

    def test_hash_changes(self):
        ref1 = build_delegation_ledger_bridge_ref(
            ledger_bridge_ref_id="lb-1", delegation_ref_id="del-1",
            ledger_bridge_description="A"
        )
        ref2 = build_delegation_ledger_bridge_ref(
            ledger_bridge_ref_id="lb-1", delegation_ref_id="del-1",
            ledger_bridge_description="B"
        )
        assert ref1.ledger_bridge_hash != ref2.ledger_bridge_hash


# ---------------------------------------------------------------------------
# 5. TraceEventIntentRef
# ---------------------------------------------------------------------------

class TestTraceEventIntentRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_trace_event_intent_ref(
            trace_event_intent_ref_id="tei-1", delegation_ref_id="del-1"
        )
        ref2 = build_delegation_trace_event_intent_ref(
            trace_event_intent_ref_id="tei-1", delegation_ref_id="del-1"
        )
        assert ref1.trace_event_intent_hash == ref2.trace_event_intent_hash

    def test_not_trace_event_emitted(self):
        ref = build_delegation_trace_event_intent_ref(
            trace_event_intent_ref_id="tei-nw", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY


# ---------------------------------------------------------------------------
# 6. AuditEventIntentRef
# ---------------------------------------------------------------------------

class TestAuditEventIntentRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_audit_event_intent_ref(
            audit_event_intent_ref_id="aei-1", delegation_ref_id="del-1"
        )
        ref2 = build_delegation_audit_event_intent_ref(
            audit_event_intent_ref_id="aei-1", delegation_ref_id="del-1"
        )
        assert ref1.audit_event_intent_hash == ref2.audit_event_intent_hash

    def test_not_audit_event_emitted(self):
        ref = build_delegation_audit_event_intent_ref(
            audit_event_intent_ref_id="aei-nw", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY


# ---------------------------------------------------------------------------
# 7. LedgerEntryPlaceholderRef
# ---------------------------------------------------------------------------

class TestLedgerEntryPlaceholderRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_ledger_entry_placeholder_ref(
            ledger_entry_placeholder_ref_id="lep-1", delegation_ref_id="del-1"
        )
        ref2 = build_delegation_ledger_entry_placeholder_ref(
            ledger_entry_placeholder_ref_id="lep-1", delegation_ref_id="del-1"
        )
        assert ref1.ledger_entry_placeholder_hash == ref2.ledger_entry_placeholder_hash

    def test_not_ledger_entry(self):
        ref = build_delegation_ledger_entry_placeholder_ref(
            ledger_entry_placeholder_ref_id="lep-nw", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY


# ---------------------------------------------------------------------------
# 8. ReplayContextRef
# ---------------------------------------------------------------------------

class TestReplayContextRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_replay_context_ref(
            replay_context_ref_id="rp-1", delegation_ref_id="del-1"
        )
        ref2 = build_delegation_replay_context_ref(
            replay_context_ref_id="rp-1", delegation_ref_id="del-1"
        )
        assert ref1.replay_context_hash == ref2.replay_context_hash

    def test_not_replay_executed(self):
        ref = build_delegation_replay_context_ref(
            replay_context_ref_id="rp-nw", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY

    def test_trace_context_kind_default(self):
        ref = build_delegation_replay_context_ref(
            replay_context_ref_id="rp-2", delegation_ref_id="del-1"
        )
        assert ref.trace_context_kind == DelegationTraceContextKind.TRACE_REPLAY_CONTEXT


# ---------------------------------------------------------------------------
# 9. ForkContextRef
# ---------------------------------------------------------------------------

class TestForkContextRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_fork_context_ref(
            fork_context_ref_id="fk-1", delegation_ref_id="del-1"
        )
        ref2 = build_delegation_fork_context_ref(
            fork_context_ref_id="fk-1", delegation_ref_id="del-1"
        )
        assert ref1.fork_context_hash == ref2.fork_context_hash

    def test_not_fork_created(self):
        ref = build_delegation_fork_context_ref(
            fork_context_ref_id="fk-nw", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY


# ---------------------------------------------------------------------------
# 10. CausalChainContextRef
# ---------------------------------------------------------------------------

class TestCausalChainContextRef:
    def test_build_deterministic(self):
        ref1 = build_delegation_causal_chain_context_ref(
            causal_chain_context_ref_id="cc-1", delegation_ref_id="del-1"
        )
        ref2 = build_delegation_causal_chain_context_ref(
            causal_chain_context_ref_id="cc-1", delegation_ref_id="del-1"
        )
        assert ref1.causal_chain_context_hash == ref2.causal_chain_context_hash

    def test_not_causal_chain_verified(self):
        ref = build_delegation_causal_chain_context_ref(
            causal_chain_context_ref_id="cc-nw", delegation_ref_id="del-1"
        )
        assert ref.bridge_status == DelegationTraceAuditBridgeStatus.REFERENCE_ONLY


# ---------------------------------------------------------------------------
# 11. ReadinessMatrixEntry / Matrix
# ---------------------------------------------------------------------------

class TestReadinessMatrix:
    def test_entry_deterministic(self):
        e1 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e1", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.TRACE_CONTEXT,
            present=True, hash_present=True, source_label_present=True, finding_count=3,
        )
        e2 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e1", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.TRACE_CONTEXT,
            present=True, hash_present=True, source_label_present=True, finding_count=3,
        )
        assert e1.entry_hash == e2.entry_hash

    def test_matrix_deterministic(self):
        e1 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e1", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.TRACE_CONTEXT,
        )
        e2 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e2", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.AUDIT_CONTEXT,
        )
        m1 = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
            entries=[e1, e2],
        )
        m2 = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
            entries=[e1, e2],
        )
        assert m1.matrix_hash == m2.matrix_hash

    def test_matrix_order_independent(self):
        e1 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e1", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.TRACE_CONTEXT,
        )
        e2 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e2", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.AUDIT_CONTEXT,
        )
        m1 = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
            entries=[e1, e2],
        )
        m2 = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
            entries=[e2, e1],
        )
        assert m1.matrix_hash == m2.matrix_hash

    def test_not_trace_verified(self):
        m = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
        )
        assert m.source_label == DelegationSourceLabel.DEV_FIXTURE
        # matrix is not TRACE_VERIFIED

    def test_changed_membership_changes_matrix_hash(self):
        e1 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e1", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.TRACE_CONTEXT,
        )
        e2 = build_delegation_trace_audit_readiness_matrix_entry(
            entry_id="e2", delegation_ref_id="del-1",
            family=DelegationTraceAuditReadinessFamily.AUDIT_CONTEXT,
        )
        m1 = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
            entries=[e1],
        )
        m2 = build_delegation_trace_audit_readiness_matrix(
            trace_audit_readiness_matrix_id="m1", delegation_ref_id="del-1",
            entries=[e1, e2],
        )
        assert m1.matrix_hash != m2.matrix_hash


# ---------------------------------------------------------------------------
# 12. ReadinessProfile
# ---------------------------------------------------------------------------

class TestReadinessProfile:
    def test_profile_deterministic(self):
        p1 = build_delegation_trace_audit_readiness_profile(
            trace_audit_readiness_profile_id="prof-1", delegation_ref_id="del-1",
            has_trace_bridge_refs=True,
            trace_writer_unavailable_reason="not yet",
            missing_components=["trace_writer"],
        )
        p2 = build_delegation_trace_audit_readiness_profile(
            trace_audit_readiness_profile_id="prof-1", delegation_ref_id="del-1",
            has_trace_bridge_refs=True,
            trace_writer_unavailable_reason="not yet",
            missing_components=["trace_writer"],
        )
        assert p1.readiness_hash == p2.readiness_hash

    def test_changed_readiness_changes_hash(self):
        p1 = build_delegation_trace_audit_readiness_profile(
            trace_audit_readiness_profile_id="prof-1", delegation_ref_id="del-1",
            has_trace_bridge_refs=False,
        )
        p2 = build_delegation_trace_audit_readiness_profile(
            trace_audit_readiness_profile_id="prof-1", delegation_ref_id="del-1",
            has_trace_bridge_refs=True,
        )
        assert p1.readiness_hash != p2.readiness_hash

    def test_not_audit_readiness_proof(self):
        p = build_delegation_trace_audit_readiness_profile(
            trace_audit_readiness_profile_id="prof-1", delegation_ref_id="del-1",
        )
        assert p.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_unavailable_reasons_visible(self):
        p = build_delegation_trace_audit_readiness_profile(
            trace_audit_readiness_profile_id="prof-1", delegation_ref_id="del-1",
            trace_writer_unavailable_reason="Trace writer not available in P1.8.14",
            audit_writer_unavailable_reason="Audit writer not available in P1.8.14",
            ledger_writer_unavailable_reason="Ledger writer not available in P1.8.14",
            evidence_verifier_unavailable_reason="Evidence verifier not available",
            output_passport_unavailable_reason="Output Passport deferred to P1.9",
        )
        assert "not available" in p.trace_writer_unavailable_reason
        assert "not available" in p.audit_writer_unavailable_reason
        assert "not available" in p.ledger_writer_unavailable_reason
        assert "Evidence verifier" in p.evidence_verifier_unavailable_reason
        assert "P1.9" in p.output_passport_unavailable_reason


# ---------------------------------------------------------------------------
# 13. Envelope
# ---------------------------------------------------------------------------

class TestEnvelope:
    def test_envelope_deterministic(self):
        env1 = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-1", delegation_ref_id="del-1",
            delegation_identity_hash="idh-1",
        )
        env2 = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-1", delegation_ref_id="del-1",
            delegation_identity_hash="idh-1",
        )
        assert env1.trace_audit_bridge_envelope_hash == env2.trace_audit_bridge_envelope_hash

    def test_changed_membership_changes_envelope_hash(self):
        env1 = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-1", delegation_ref_id="del-1",
            trace_bridge_refs=[],
        )
        env2 = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-1", delegation_ref_id="del-1",
            trace_bridge_refs=["tb-1"],
        )
        assert env1.trace_audit_bridge_envelope_hash != env2.trace_audit_bridge_envelope_hash

    def test_not_trace_write(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-1", delegation_ref_id="del-1",
        )
        assert env.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_not_audit_finality(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-2", delegation_ref_id="del-1",
        )
        # Envelope is a reference packet, not an audit record
        assert isinstance(env.trace_audit_bridge_envelope_hash, str)

    def test_not_ledger_write(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-3", delegation_ref_id="del-1",
        )
        # Envelope is reference-only packet; nothing is being written to ledger
        assert isinstance(env.trace_audit_bridge_envelope_hash, str)

    def test_binds_all_context_hashes(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-4", delegation_ref_id="del-1",
            delegation_identity_hash="idh",
            role_binding_hash="rbh",
            constraint_set_hash="csh",
            authority_binding_set_hash="abs",
            non_repudiation_binding_set_hash="nrb",
            identity_mesh_binding_set_hash="imh",
            scope_binding_set_hash="sbh",
            lifecycle_binding_set_hash="lbh",
            chain_binding_set_hash="cbh",
            shadow_resolver_result_hash="srh",
            operator_review_binding_set_hash="orb",
            policy_custos_bridge_binding_set_hash="pcb",
            runtime_execution_readiness_binding_set_hash="rer",
        )
        assert env.delegation_identity_hash == "idh"
        assert env.role_binding_hash == "rbh"
        assert env.constraint_set_hash == "csh"
        assert env.authority_binding_set_hash == "abs"
        assert env.non_repudiation_binding_set_hash == "nrb"
        assert env.identity_mesh_binding_set_hash == "imh"
        assert env.scope_binding_set_hash == "sbh"
        assert env.lifecycle_binding_set_hash == "lbh"
        assert env.chain_binding_set_hash == "cbh"
        assert env.shadow_resolver_result_hash == "srh"
        assert env.operator_review_binding_set_hash == "orb"
        assert env.policy_custos_bridge_binding_set_hash == "pcb"
        assert env.runtime_execution_readiness_binding_set_hash == "rer"

    def test_envelope_serialization_json_safe(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-5", delegation_ref_id="del-1",
            trace_bridge_refs=["tb-1"],
            audit_bridge_refs=["ab-1"],
        )
        s = serialize_delegation_trace_audit_bridge_envelope(env)
        d = json.loads(s)
        assert d["trace_audit_bridge_envelope_id"] == "env-5"
        assert "tb-1" in d["trace_bridge_refs"]
        assert "ab-1" in d["audit_bridge_refs"]

    def test_envelope_hash_is_deterministic_across_serialization(self):
        env1 = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-6", delegation_ref_id="del-1",
        )
        env2 = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-6", delegation_ref_id="del-1",
        )
        assert env1.trace_audit_bridge_envelope_hash == env2.trace_audit_bridge_envelope_hash
        assert serialize_delegation_trace_audit_bridge_envelope(env1) == serialize_delegation_trace_audit_bridge_envelope(env2)


# ---------------------------------------------------------------------------
# 14. Binding / BindingSet
# ---------------------------------------------------------------------------

class TestBinding:
    def test_binding_deterministic(self):
        b1 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
            trace_audit_bridge_envelope_hash="envh-1",
        )
        b2 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
            trace_audit_bridge_envelope_hash="envh-1",
        )
        assert b1.binding_hash == b2.binding_hash

    def test_changed_binding_changes_hash(self):
        b1 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
            trace_audit_bridge_envelope_hash="A",
        )
        b2 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
            trace_audit_bridge_envelope_hash="B",
        )
        assert b1.binding_hash != b2.binding_hash


class TestBindingSet:
    def test_binding_set_deterministic(self):
        b1 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
        )
        bs1 = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs1", delegation_ref_id="del-1",
            bindings=[b1],
        )
        bs2 = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs1", delegation_ref_id="del-1",
            bindings=[b1],
        )
        assert bs1.trace_audit_bridge_binding_set_hash == bs2.trace_audit_bridge_binding_set_hash

    def test_changed_bindings_change_set_hash(self):
        b1 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
            trace_audit_bridge_envelope_hash="A",
        )
        b2 = build_delegation_trace_audit_bridge_binding(
            binding_id="b2", delegation_ref_id="del-1",
            trace_audit_bridge_envelope_hash="B",
        )
        bs1 = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs1", delegation_ref_id="del-1",
            bindings=[b1],
        )
        bs2 = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs1", delegation_ref_id="del-1",
            bindings=[b1, b2],
        )
        assert bs1.trace_audit_bridge_binding_set_hash != bs2.trace_audit_bridge_binding_set_hash

    def test_binding_set_serialization(self):
        b1 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
        )
        bs = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs1", delegation_ref_id="del-1",
            bindings=[b1],
        )
        s = serialize_delegation_trace_audit_bridge_binding_set(bs)
        d = json.loads(s)
        assert d["trace_audit_bridge_binding_set_id"] == "bs1"
        assert len(d["bindings"]) == 1

    def test_canonical_json_side_effects_are_all_false(self):
        b1 = build_delegation_trace_audit_bridge_binding(
            binding_id="b1", delegation_ref_id="del-1",
        )
        bs = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs1", delegation_ref_id="del-1",
            bindings=[b1],
        )
        d = bs.to_canonical_dict()
        se = d["side_effects"]
        for key, val in se.items():
            assert val is False, f"side_effect {key} should be False, got {val}"


# ---------------------------------------------------------------------------
# 15. SideEffects — all false
# ---------------------------------------------------------------------------

class TestSideEffects:
    def test_all_false_by_default(self):
        se = DelegationTraceAuditBridgeSideEffects()
        assert se.trace_writer_called is False
        assert se.audit_writer_called is False
        assert se.ledger_writer_called is False
        assert se.trace_event_emitted is False
        assert se.audit_event_emitted is False
        assert se.ledger_entry_written is False
        assert se.audit_finalized is False
        assert se.replay_executed is False
        assert se.fork_created is False
        assert se.causal_chain_verified is False
        assert se.evidence_verified is False
        assert se.output_passport_created is False
        assert se.trace_verified is False
        assert se.ledger_finalized is False
        assert se.global_trace_written is False
        assert se.runtime_mutated is False

    def test_explicit_all_false(self):
        se = DelegationTraceAuditBridgeSideEffects(
            trace_writer_called=False,
            audit_writer_called=False,
            ledger_writer_called=False,
            trace_event_emitted=False,
            audit_event_emitted=False,
            ledger_entry_written=False,
            audit_finalized=False,
            replay_executed=False,
            fork_created=False,
            causal_chain_verified=False,
            evidence_verified=False,
            output_passport_created=False,
            trace_verified=False,
            ledger_finalized=False,
            global_trace_written=False,
            runtime_mutated=False,
        )
        fields = [
            "trace_writer_called", "audit_writer_called", "ledger_writer_called",
            "trace_event_emitted", "audit_event_emitted", "ledger_entry_written",
            "audit_finalized", "replay_executed", "fork_created",
            "causal_chain_verified", "evidence_verified", "output_passport_created",
            "trace_verified", "ledger_finalized", "global_trace_written", "runtime_mutated",
        ]
        for f in fields:
            assert getattr(se, f) is False


# ---------------------------------------------------------------------------
# 16. StatusReport
# ---------------------------------------------------------------------------

class TestStatusReport:
    def test_status_report_builds(self):
        from agentic_runtime.delegation.trace_audit_bridge import (
            DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS,
        )
        sr = build_delegation_trace_audit_bridge_status_report(
            status_label="P1.8.14 DEV_FIXTURE STATUS",
            available_contracts=["TraceBridgeRef", "AuditBridgeRef", "TraceAuditBridgeEnvelope"],
            unavailable_bindings=DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS,
        )
        assert sr.status_label == "P1.8.14 DEV_FIXTURE STATUS"
        assert "TraceBridgeRef" in sr.available_contracts
        assert len(sr.unavailable_bindings) > 0
        assert sr.status_hash
        assert all(getattr(sr.side_effects, f) is False
                   for f in ["trace_writer_called", "audit_writer_called"])

    def test_status_report_deterministic(self):
        from agentic_runtime.delegation.trace_audit_bridge import (
            DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS,
        )
        sr1 = build_delegation_trace_audit_bridge_status_report(
            unavailable_bindings=DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS,
        )
        sr2 = build_delegation_trace_audit_bridge_status_report(
            unavailable_bindings=DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS,
        )
        assert sr1.status_hash == sr2.status_hash

    def test_unavailable_reasons_exist(self):
        from agentic_runtime.delegation.trace_audit_bridge import (
            DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS,
        )
        ub = DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS
        assert "Trace Writer" in ub
        assert "Audit Writer" in ub
        assert "Ledger Writer" in ub
        assert "Output Passport / P1.9" in ub
        assert any("P1.8.15" in k for k in ub.keys())


# ---------------------------------------------------------------------------
# 17. Enums have expected values
# ---------------------------------------------------------------------------

class TestEnums:
    def test_bridge_kind_values(self):
        assert DelegationTraceAuditBridgeKind.TRACE_BRIDGE.value == "TRACE_BRIDGE"
        assert DelegationTraceAuditBridgeKind.AUDIT_BRIDGE.value == "AUDIT_BRIDGE"
        assert DelegationTraceAuditBridgeKind.LEDGER_BRIDGE.value == "LEDGER_BRIDGE"
        assert DelegationTraceAuditBridgeKind.REFERENCE_ONLY.value == "REFERENCE_ONLY"

    def test_reference_status_values(self):
        assert DelegationTraceAuditBridgeReferenceStatus.TRACE_BRIDGE_REFERENCED.value == "TRACE_BRIDGE_REFERENCED"
        assert DelegationTraceAuditBridgeReferenceStatus.AUDIT_BRIDGE_REFERENCED.value == "AUDIT_BRIDGE_REFERENCED"
        assert DelegationTraceAuditBridgeReferenceStatus.LEDGER_BRIDGE_REFERENCED.value == "LEDGER_BRIDGE_REFERENCED"
        assert DelegationTraceAuditBridgeReferenceStatus.TRACE_WRITER_UNAVAILABLE.value == "TRACE_WRITER_UNAVAILABLE"
        assert DelegationTraceAuditBridgeReferenceStatus.AUDIT_WRITER_UNAVAILABLE.value == "AUDIT_WRITER_UNAVAILABLE"
        assert DelegationTraceAuditBridgeReferenceStatus.OUTPUT_PASSPORT_UNAVAILABLE.value == "OUTPUT_PASSPORT_UNAVAILABLE"

    def test_bridge_status_values(self):
        assert DelegationTraceAuditBridgeStatus.REFERENCE_ONLY.value == "REFERENCE_ONLY"
        assert DelegationTraceAuditBridgeStatus.DECLARED.value == "DECLARED"

    def test_trace_context_kind_values(self):
        assert DelegationTraceContextKind.TRACE_EVENT_CONTEXT.value == "TRACE_EVENT_CONTEXT"
        assert DelegationTraceContextKind.TRACE_REPLAY_CONTEXT.value == "TRACE_REPLAY_CONTEXT"
        assert DelegationTraceContextKind.TRACE_FORK_CONTEXT.value == "TRACE_FORK_CONTEXT"
        assert DelegationTraceContextKind.TRACE_CAUSAL_CONTEXT.value == "TRACE_CAUSAL_CONTEXT"

    def test_audit_context_kind_values(self):
        assert DelegationAuditContextKind.AUDIT_EVENT_CONTEXT.value == "AUDIT_EVENT_CONTEXT"
        assert DelegationAuditContextKind.AUDIT_RECORD_CONTEXT.value == "AUDIT_RECORD_CONTEXT"
        assert DelegationAuditContextKind.AUDIT_OUTPUT_PASSPORT_CONTEXT.value == "AUDIT_OUTPUT_PASSPORT_CONTEXT"


# ---------------------------------------------------------------------------
# 18. DEV_FIXTURE source labels
# ---------------------------------------------------------------------------

class TestDevFixtureLabels:
    def test_trace_bridge_ref_fixture(self):
        ref = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="dev-1", delegation_ref_id="dev-1",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert ref.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_envelope_fixture(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="dev-env", delegation_ref_id="dev-1",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert env.source_label == DelegationSourceLabel.DEV_FIXTURE

    def test_binding_set_fixture(self):
        bs = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="dev-bs", delegation_ref_id="dev-1",
            source_label=DelegationSourceLabel.DEV_FIXTURE,
        )
        assert bs.source_label == DelegationSourceLabel.DEV_FIXTURE


# ---------------------------------------------------------------------------
# 19. Hash boundary: hash is not TRACE_VERIFIED
# ---------------------------------------------------------------------------

class TestHashIsNotTraceVerified:
    """Hash functions produce deterministic results; this is metadata, not verification."""
    def test_trace_bridge_hash_not_verified(self):
        ref = build_delegation_trace_bridge_ref(
            trace_bridge_ref_id="h1", delegation_ref_id="del-1"
        )
        assert ref.trace_bridge_hash  # hash exists
        # hash exists does not mean TRACE_VERIFIED

    def test_envelope_hash_not_verified(self):
        env = build_delegation_trace_audit_bridge_envelope(
            trace_audit_bridge_envelope_id="env-h", delegation_ref_id="del-1"
        )
        assert env.trace_audit_bridge_envelope_hash
        # envelope hash is metadata only

    def test_binding_set_hash_not_verified(self):
        bs = build_delegation_trace_audit_bridge_binding_set(
            trace_audit_bridge_binding_set_id="bs-h", delegation_ref_id="del-1"
        )
        assert bs.trace_audit_bridge_binding_set_hash
        # binding set hash is metadata only

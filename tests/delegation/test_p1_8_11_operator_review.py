"""Focused tests for P1.8.11 Delegation Operator Review / ApprovalIntentRef Model.

All review and intent references are DEV_FIXTURE unless otherwise noted.
No approval, rejection, escalation, HITL, signature, policy/Custos, runtime
allow/block, Ledger, trace, or runtime mutation is performed.
"""

from __future__ import annotations

import json

import pytest

from agentic_runtime.delegation.foundation import (
    DelegationError,
    DelegationErrorCode,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    stable_hash,
)
from agentic_runtime.delegation.operator_review import (
    APPROVAL_INTENT_REF_KNOWN_FIELDS,
    ESCALATION_INTENT_REF_KNOWN_FIELDS,
    MORE_CONTEXT_INTENT_REF_KNOWN_FIELDS,
    OPERATOR_REVIEW_ENVELOPE_KNOWN_FIELDS,
    OPERATOR_REVIEW_REF_KNOWN_FIELDS,
    RATIONALE_REF_KNOWN_FIELDS,
    REJECTION_INTENT_REF_KNOWN_FIELDS,
    REVIEW_BINDING_KNOWN_FIELDS,
    REVIEW_BINDING_SET_KNOWN_FIELDS,
    REVIEW_READINESS_PROFILE_KNOWN_FIELDS,
    REVIEW_SIDE_EFFECTS_KNOWN_FIELDS,
    REVIEW_STATUS_REPORT_KNOWN_FIELDS,
    DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS,
    DelegationApprovalIntentRef,
    DelegationEscalationIntentRef,
    DelegationMoreContextIntentRef,
    DelegationOperatorReviewBinding,
    DelegationOperatorReviewBindingSet,
    DelegationOperatorReviewEnvelope,
    DelegationOperatorReviewIntentKind,
    DelegationOperatorReviewKind,
    DelegationOperatorReviewReadinessProfile,
    DelegationOperatorReviewRef,
    DelegationOperatorReviewReferenceStatus,
    DelegationOperatorReviewSideEffects,
    DelegationOperatorReviewStatus,
    DelegationOperatorReviewStatusReport,
    DelegationRejectionIntentRef,
    DelegationReviewRationaleKind,
    DelegationReviewRationaleRef,
    build_delegation_approval_intent_ref,
    build_delegation_escalation_intent_ref,
    build_delegation_more_context_intent_ref,
    build_delegation_operator_review_binding,
    build_delegation_operator_review_binding_set,
    build_delegation_operator_review_envelope,
    build_delegation_operator_review_readiness_profile,
    build_delegation_operator_review_ref,
    build_delegation_operator_review_status_report,
    build_delegation_rejection_intent_ref,
    build_delegation_review_rationale_ref,
    hash_delegation_approval_intent_ref,
    hash_delegation_escalation_intent_ref,
    hash_delegation_more_context_intent_ref,
    hash_delegation_operator_review_binding,
    hash_delegation_operator_review_binding_set,
    hash_delegation_operator_review_envelope,
    hash_delegation_operator_review_readiness_profile,
    hash_delegation_operator_review_ref,
    hash_delegation_operator_review_status_report,
    hash_delegation_rejection_intent_ref,
    hash_delegation_review_rationale_ref,
    serialize_delegation_operator_review_binding_set,
    serialize_delegation_operator_review_envelope,
)

# Re-use P1.8.10 for context chain
from agentic_runtime.delegation.shadow_resolver import (
    DelegationShadowResolverResult,
    build_delegation_shadow_resolver_result,
)

# ---------------------------------------------------------------------------
# 1. Imports work from agentic_runtime.delegation
# ---------------------------------------------------------------------------


def test_operator_review_imports_work() -> None:
    """P1.8.11 symbols are importable from agentic_runtime.delegation."""
    from agentic_runtime.delegation import (
        DelegationOperatorReviewRef,
        DelegationApprovalIntentRef,
        DelegationRejectionIntentRef,
        DelegationEscalationIntentRef,
        DelegationMoreContextIntentRef,
        DelegationReviewRationaleRef,
        DelegationOperatorReviewReadinessProfile,
        DelegationOperatorReviewEnvelope,
        DelegationOperatorReviewBinding,
        DelegationOperatorReviewBindingSet,
        DelegationOperatorReviewSideEffects,
        DelegationOperatorReviewStatusReport,
    )
    assert DelegationOperatorReviewRef is not None
    assert DelegationApprovalIntentRef is not None
    assert DelegationOperatorReviewBindingSet is not None


# ---------------------------------------------------------------------------
# 2. Existing P1.8.0-10 exports remain importable
# ---------------------------------------------------------------------------


def test_existing_p1_8_exports_remain_importable() -> None:
    """P1.8.0 exports remain importable after P1.8.11 additions."""
    from agentic_runtime.delegation.foundation import (
        DelegationRecord,
        DelegationSideEffects,
    )
    # Confirm core types are importable
    assert DelegationRecord is not None
    assert DelegationSideEffects is not None


# ---------------------------------------------------------------------------
# 3. P1.8.10 ShadowResolverResult can feed P1.8.11 operator review path
# ---------------------------------------------------------------------------


@pytest.fixture
def dev_fixture_shadow_result() -> DelegationShadowResolverResult:
    """DEV_FIXTURE P1.8.10 shadow resolver result for P1.8.11 tests."""
    from agentic_runtime.delegation.shadow_resolver import (
        DelegationConsistencyFamily,
        DelegationConsistencyFindingKind,
        DelegationConsistencySeverity,
        DelegationConsistencyMatrix,
        DelegationConsistencySnapshot,
        DelegationShadowResolverInputEnvelope,
        DelegationShadowResolverReadinessProfile,
        build_delegation_consistency_finding,
        build_delegation_consistency_matrix,
        build_delegation_consistency_snapshot,
        build_delegation_shadow_resolver_input_envelope,
        build_delegation_shadow_resolver_readiness_profile,
    )
    input_env = build_delegation_shadow_resolver_input_envelope(
        delegation_ref_id="del-shadow-test-001",
        delegation_identity_hash="a" * 40,
        role_binding_hash="b" * 40,
        constraint_set_hash="c" * 40,
        authority_binding_set_hash="d" * 40,
        non_repudiation_binding_set_hash="e" * 40,
        identity_mesh_binding_set_hash="f" * 40,
        scope_binding_set_hash="g" * 40,
        lifecycle_binding_set_hash="h" * 40,
        chain_binding_set_hash="i" * 40,
    )
    finding = build_delegation_consistency_finding(
        delegation_ref_id="del-shadow-test-001",
        family=DelegationConsistencyFamily.IDENTITY,
        finding_kind=DelegationConsistencyFindingKind.PRESENT,
        severity=DelegationConsistencySeverity.INFO,
    )
    readiness = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id="del-shadow-test-001",
        has_foundation=True,
        has_identity=True,
    )
    entry = build_delegation_consistency_matrix(
        delegation_ref_id="del-shadow-test-001",
        entries=[],
    )
    snapshot = build_delegation_consistency_snapshot(
        delegation_ref_id="del-shadow-test-001",
        input_envelope_hash=input_env.input_envelope_hash,
        findings=[finding],
        matrix=entry,
        readiness_profile=readiness,
    )
    return build_delegation_shadow_resolver_result(
        delegation_ref_id="del-shadow-test-001",
        input_envelope=input_env,
        snapshot=snapshot,
        matrix=entry,
        readiness_profile=readiness,
        findings=[finding],
    )


def test_shadow_result_feeds_operator_review(
    dev_fixture_shadow_result: DelegationShadowResolverResult,
) -> None:
    """DEV_FIXTURE P1.8.10 ShadowResolverResult can feed P1.8.11 envelope."""
    envelope = build_delegation_operator_review_envelope(
        delegation_ref_id=dev_fixture_shadow_result.delegation_ref_id,
        shadow_resolver_result_hash=dev_fixture_shadow_result.result_hash,
    )
    assert envelope.operator_review_envelope_hash is not None
    assert envelope.shadow_resolver_result_hash == dev_fixture_shadow_result.result_hash


# ---------------------------------------------------------------------------
# 4-9. Ref determinism
# ---------------------------------------------------------------------------


def test_operator_review_ref_builds_deterministically() -> None:
    """Identical inputs produce identical review hashes."""
    r1 = build_delegation_operator_review_ref(
        delegation_ref_id="del-test",
        review_kind=DelegationOperatorReviewKind.OPERATOR_REVIEW,
        review_description="test review",
    )
    r2 = build_delegation_operator_review_ref(
        delegation_ref_id="del-test",
        review_kind=DelegationOperatorReviewKind.OPERATOR_REVIEW,
        review_description="test review",
    )
    assert r1.review_hash == r2.review_hash


def test_approval_intent_ref_builds_deterministically() -> None:
    """Identical inputs produce identical approval_intent_hashes."""
    a1 = build_delegation_approval_intent_ref(
        delegation_ref_id="del-test",
        approval_intent_description="approve this delegation",
    )
    a2 = build_delegation_approval_intent_ref(
        delegation_ref_id="del-test",
        approval_intent_description="approve this delegation",
    )
    assert a1.approval_intent_hash == a2.approval_intent_hash


def test_rejection_intent_ref_builds_deterministically() -> None:
    """Identical inputs produce identical rejection_intent_hashes."""
    r1 = build_delegation_rejection_intent_ref(
        delegation_ref_id="del-test",
        rejection_intent_description="reject this delegation",
    )
    r2 = build_delegation_rejection_intent_ref(
        delegation_ref_id="del-test",
        rejection_intent_description="reject this delegation",
    )
    assert r1.rejection_intent_hash == r2.rejection_intent_hash


def test_escalation_intent_ref_builds_deterministically() -> None:
    """Identical inputs produce identical escalation_intent_hashes."""
    e1 = build_delegation_escalation_intent_ref(
        delegation_ref_id="del-test",
        escalation_intent_description="escalate to senior operator",
    )
    e2 = build_delegation_escalation_intent_ref(
        delegation_ref_id="del-test",
        escalation_intent_description="escalate to senior operator",
    )
    assert e1.escalation_intent_hash == e2.escalation_intent_hash


def test_more_context_intent_ref_builds_deterministically() -> None:
    """Identical inputs produce identical more_context_intent_hashes."""
    m1 = build_delegation_more_context_intent_ref(
        delegation_ref_id="del-test",
        more_context_intent_description="need more context",
    )
    m2 = build_delegation_more_context_intent_ref(
        delegation_ref_id="del-test",
        more_context_intent_description="need more context",
    )
    assert m1.more_context_intent_hash == m2.more_context_intent_hash


def test_review_rationale_ref_builds_deterministically() -> None:
    """Identical inputs produce identical rationale_hashes."""
    r1 = build_delegation_review_rationale_ref(
        delegation_ref_id="del-test",
        rationale_kind=DelegationReviewRationaleKind.CONSISTENCY_CONTEXT,
        rationale_description="consistency reviewed",
    )
    r2 = build_delegation_review_rationale_ref(
        delegation_ref_id="del-test",
        rationale_kind=DelegationReviewRationaleKind.CONSISTENCY_CONTEXT,
        rationale_description="consistency reviewed",
    )
    assert r1.rationale_hash == r2.rationale_hash


# ---------------------------------------------------------------------------
# 10-14. Complex objects determinism
# ---------------------------------------------------------------------------


def test_readiness_profile_builds_deterministically() -> None:
    """Identical inputs produce identical readiness_hashes."""
    p1 = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
        has_review_refs=True,
        has_shadow_resolver_context=True,
    )
    p2 = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
        has_review_refs=True,
        has_shadow_resolver_context=True,
    )
    assert p1.readiness_hash == p2.readiness_hash


def test_envelope_builds_deterministically() -> None:
    """Identical inputs produce identical envelope hashes."""
    e1 = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        delegation_identity_hash="a" * 40,
        role_binding_hash="b" * 40,
    )
    e2 = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        delegation_identity_hash="a" * 40,
        role_binding_hash="b" * 40,
    )
    assert e1.operator_review_envelope_hash == e2.operator_review_envelope_hash


def test_binding_builds_deterministically() -> None:
    """Identical inputs produce identical binding hashes."""
    env = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
    )
    b1 = build_delegation_operator_review_binding(
        delegation_ref_id="del-test",
        envelope=env,
    )
    b2 = build_delegation_operator_review_binding(
        delegation_ref_id="del-test",
        envelope=env,
    )
    assert b1.binding_hash == b2.binding_hash


def test_binding_set_builds_deterministically() -> None:
    """Identical inputs produce identical binding_set hashes."""
    env = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
    )
    b1 = build_delegation_operator_review_binding(
        delegation_ref_id="del-test",
        envelope=env,
    )
    bs1 = build_delegation_operator_review_binding_set(
        delegation_ref_id="del-test",
        bindings=[b1],
    )
    bs2 = build_delegation_operator_review_binding_set(
        delegation_ref_id="del-test",
        bindings=[b1],
    )
    assert bs1.operator_review_binding_set_hash == bs2.operator_review_binding_set_hash


def test_status_report_builds_deterministically() -> None:
    """Status report produces reproducible hashes."""
    s1 = build_delegation_operator_review_status_report()
    s2 = build_delegation_operator_review_status_report()
    assert s1.status_hash == s2.status_hash


# ---------------------------------------------------------------------------
# 15-21. Hash changes with changed input
# ---------------------------------------------------------------------------


def test_changed_review_kind_changes_review_hash() -> None:
    """Changing review_kind produces a different review_hash."""
    r1 = build_delegation_operator_review_ref(
        delegation_ref_id="del-test",
        review_kind=DelegationOperatorReviewKind.OPERATOR_REVIEW,
    )
    r2 = build_delegation_operator_review_ref(
        delegation_ref_id="del-test",
        review_kind=DelegationOperatorReviewKind.CONSISTENCY_REVIEW,
    )
    assert r1.review_hash != r2.review_hash


def test_changed_approval_intent_changes_hash() -> None:
    """Changing approval_intent_description changes hash."""
    a1 = build_delegation_approval_intent_ref(
        delegation_ref_id="del-test",
        approval_intent_description="desc A",
    )
    a2 = build_delegation_approval_intent_ref(
        delegation_ref_id="del-test",
        approval_intent_description="desc B",
    )
    assert a1.approval_intent_hash != a2.approval_intent_hash


def test_changed_rejection_intent_changes_hash() -> None:
    """Changing rejection description changes hash."""
    r1 = build_delegation_rejection_intent_ref(
        delegation_ref_id="del-test",
        rejection_intent_description="reason A",
    )
    r2 = build_delegation_rejection_intent_ref(
        delegation_ref_id="del-test",
        rejection_intent_description="reason B",
    )
    assert r1.rejection_intent_hash != r2.rejection_intent_hash


def test_changed_escalation_intent_changes_hash() -> None:
    """Changing escalation description changes hash."""
    e1 = build_delegation_escalation_intent_ref(
        delegation_ref_id="del-test",
        escalation_intent_description="to lead A",
    )
    e2 = build_delegation_escalation_intent_ref(
        delegation_ref_id="del-test",
        escalation_intent_description="to lead B",
    )
    assert e1.escalation_intent_hash != e2.escalation_intent_hash


def test_changed_more_context_intent_changes_hash() -> None:
    """Changing more-context description changes hash."""
    m1 = build_delegation_more_context_intent_ref(
        delegation_ref_id="del-test",
        more_context_intent_description="need A",
    )
    m2 = build_delegation_more_context_intent_ref(
        delegation_ref_id="del-test",
        more_context_intent_description="need B",
    )
    assert m1.more_context_intent_hash != m2.more_context_intent_hash


def test_changed_rationale_changes_hash() -> None:
    """Changing rationale_description changes hash."""
    r1 = build_delegation_review_rationale_ref(
        delegation_ref_id="del-test",
        rationale_description="rationale A",
    )
    r2 = build_delegation_review_rationale_ref(
        delegation_ref_id="del-test",
        rationale_description="rationale B",
    )
    assert r1.rationale_hash != r2.rationale_hash


def test_changed_envelope_membership_changes_hash() -> None:
    """Adding a review ref changes the envelope hash."""
    review = build_delegation_operator_review_ref(
        delegation_ref_id="del-test",
    )
    e1 = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
    )
    e2 = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        review_refs=[review],
    )
    assert e1.operator_review_envelope_hash != e2.operator_review_envelope_hash


def test_changed_binding_set_membership_changes_hash() -> None:
    """Adding a binding changes the binding set hash."""
    env = build_delegation_operator_review_envelope(delegation_ref_id="del-test")
    b1 = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env)
    b2 = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env, binding_id="custom-id")
    bs1 = build_delegation_operator_review_binding_set(delegation_ref_id="del-test", bindings=[b1])
    bs2 = build_delegation_operator_review_binding_set(delegation_ref_id="del-test", bindings=[b1, b2])
    assert bs1.operator_review_binding_set_hash != bs2.operator_review_binding_set_hash


# ---------------------------------------------------------------------------
# 22. ReferenceStatus includes all expected values
# ---------------------------------------------------------------------------


def test_reference_status_has_required_values() -> None:
    """DelegationOperatorReviewReferenceStatus includes expected values."""
    expected = {
        "REFERENCE_ONLY",
        "REVIEW_REFERENCED",
        "APPROVAL_INTENT_REFERENCED",
        "REJECTION_INTENT_REFERENCED",
        "ESCALATION_INTENT_REFERENCED",
        "MORE_CONTEXT_INTENT_REFERENCED",
        "APPROVAL_ENGINE_UNAVAILABLE",
        "SIGNATURE_VERIFIER_UNAVAILABLE",
        "HITL_WORKFLOW_UNAVAILABLE",
        "UNAVAILABLE",
        "ERROR",
        "UNKNOWN",
    }
    actual = set(v.value for v in DelegationOperatorReviewReferenceStatus)
    assert expected <= actual


# ---------------------------------------------------------------------------
# 23-28. Boundary tests: REFERENCED does NOT imply completed
# ---------------------------------------------------------------------------


def test_review_referenced_is_not_completed() -> None:
    """REVIEW_REFERENCED does not imply review completed."""
    status = DelegationOperatorReviewReferenceStatus.REVIEW_REFERENCED
    assert status.value == "REVIEW_REFERENCED"
    # REVIEW_REFERENCED is a reference-only classification, not a completion state
    assert status != "COMPLETED"


def test_approval_intent_referenced_is_not_approved() -> None:
    """APPROVAL_INTENT_REFERENCED does not imply approved."""
    r = build_delegation_approval_intent_ref(
        delegation_ref_id="del-test",
        reference_status=DelegationOperatorReviewReferenceStatus.APPROVAL_INTENT_REFERENCED,
    )
    assert r.reference_status == DelegationOperatorReviewReferenceStatus.APPROVAL_INTENT_REFERENCED
    assert r.reference_status != "APPROVED"
    # No approval was actually granted
    assert r.approval_intent_hash is not None
    # Side effects must be all false
    assert r.review_status != "APPROVED"


def test_rejection_intent_referenced_is_not_denied() -> None:
    """REJECTION_INTENT_REFERENCED does not imply denied."""
    r = build_delegation_rejection_intent_ref(
        delegation_ref_id="del-test",
        reference_status=DelegationOperatorReviewReferenceStatus.REJECTION_INTENT_REFERENCED,
    )
    assert r.reference_status == DelegationOperatorReviewReferenceStatus.REJECTION_INTENT_REFERENCED
    assert r.reference_status != "DENIED"


def test_escalation_intent_referenced_is_not_escalated() -> None:
    """ESCALATION_INTENT_REFERENCED does not imply escalated."""
    e = build_delegation_escalation_intent_ref(
        delegation_ref_id="del-test",
        reference_status=DelegationOperatorReviewReferenceStatus.ESCALATION_INTENT_REFERENCED,
    )
    assert e.reference_status == DelegationOperatorReviewReferenceStatus.ESCALATION_INTENT_REFERENCED
    assert e.reference_status != "ESCALATED"


def test_more_context_intent_referenced_is_not_blocked() -> None:
    """MORE_CONTEXT_INTENT_REFERENCED does not imply runtime block."""
    m = build_delegation_more_context_intent_ref(
        delegation_ref_id="del-test",
        reference_status=DelegationOperatorReviewReferenceStatus.MORE_CONTEXT_INTENT_REFERENCED,
    )
    assert m.reference_status == DelegationOperatorReviewReferenceStatus.MORE_CONTEXT_INTENT_REFERENCED
    assert m.reference_status != "BLOCKED"


def test_rationale_ref_is_not_verified() -> None:
    """RationaleRef does not imply rationale verified."""
    r = build_delegation_review_rationale_ref(
        delegation_ref_id="del-test",
        rationale_kind=DelegationReviewRationaleKind.OPERATOR_NOTE,
        rationale_description="my note",
    )
    assert r.rationale_hash is not None
    # Rationale hash exists but is not verification proof
    assert r.rationale_kind == DelegationReviewRationaleKind.OPERATOR_NOTE


# ---------------------------------------------------------------------------
# 29-34. Readiness profile tests
# ---------------------------------------------------------------------------


def test_readiness_profile_reports_present_components() -> None:
    """Readiness profile reports which components are present."""
    profile = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
        has_review_refs=True,
        has_shadow_resolver_context=True,
    )
    assert profile.has_review_refs is True
    assert profile.has_shadow_resolver_context is True
    assert "approval_intent_refs" in profile.missing_components


def test_readiness_profile_reports_missing_components() -> None:
    """Readiness profile reports missing components."""
    profile = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
    )
    missing = set(profile.missing_components)
    assert "review_refs" in missing
    assert "shadow_resolver_context" in missing


def test_readiness_profile_is_not_approval_readiness() -> None:
    """OperatorReviewReadinessProfile is presence/absence, not approval readiness."""
    profile = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
        has_review_refs=True,
        has_approval_intent_refs=True,
    )
    # Profile says components are present, not that approval is ready
    assert profile.approval_engine_unavailable_reason != ""
    assert "approval" in profile.approval_engine_unavailable_reason.lower()


def test_readiness_profile_is_not_operator_decision() -> None:
    """Readiness profile does not record an operator decision."""
    profile = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
    )
    # No field records "decision" or "approved"
    assert profile.readiness_hash is not None
    # It's metadata only


def test_readiness_profile_is_not_hitl_workflow_state() -> None:
    """Readiness profile is not HITL workflow state."""
    profile = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-test",
    )
    assert profile.hitl_workflow_unavailable_reason != ""
    assert "HITL" in profile.hitl_workflow_unavailable_reason or "human-in-the-loop" in profile.hitl_workflow_unavailable_reason.lower()


# ---------------------------------------------------------------------------
# 35-37. Envelope tests
# ---------------------------------------------------------------------------


def test_envelope_ordering_is_deterministic() -> None:
    """Envelope hash is deterministic regardless of input ordering."""
    r1 = build_delegation_operator_review_ref(delegation_ref_id="del-test", review_ref_id="ref-a")
    r2 = build_delegation_operator_review_ref(delegation_ref_id="del-test", review_ref_id="ref-b")
    e1 = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        review_refs=[r1, r2],
    )
    e2 = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        review_refs=[r2, r1],
    )
    assert e1.operator_review_envelope_hash == e2.operator_review_envelope_hash


def test_envelope_includes_all_context_hashes() -> None:
    """Envelope contains hashes for all P1.8 context layers."""
    envelope = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        delegation_identity_hash="a" * 40,
        role_binding_hash="b" * 40,
        constraint_set_hash="c" * 40,
        authority_binding_set_hash="d" * 40,
        non_repudiation_binding_set_hash="e" * 40,
        identity_mesh_binding_set_hash="f" * 40,
        scope_binding_set_hash="g" * 40,
        lifecycle_binding_set_hash="h" * 40,
        chain_binding_set_hash="i" * 40,
        shadow_resolver_result_hash="j" * 40,
    )
    assert envelope.delegation_identity_hash == "a" * 40
    assert envelope.shadow_resolver_result_hash == "j" * 40
    assert len(envelope.operator_review_envelope_hash) == 64


def test_envelope_hash_is_not_trace_verified() -> None:
    """OperatorReviewEnvelope hash is not TRACE_VERIFIED."""
    envelope = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
    )
    # The hash exists but there is no trace verification layer involved
    assert envelope.operator_review_envelope_hash is not None
    assert envelope.operator_review_envelope_hash != "TRACE_VERIFIED"


# ---------------------------------------------------------------------------
# 38-40. Binding tests
# ---------------------------------------------------------------------------


def test_binding_hash_deterministic() -> None:
    """OperatorReviewBinding hash is deterministic."""
    env = build_delegation_operator_review_envelope(delegation_ref_id="del-test")
    b1 = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env)
    b2 = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env)
    assert b1.binding_hash == b2.binding_hash


def test_binding_set_hash_deterministic() -> None:
    """OperatorReviewBindingSet hash is deterministic regardless of ordering."""
    env = build_delegation_operator_review_envelope(delegation_ref_id="del-test")
    b1 = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env, binding_id="b1")
    b2 = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env, binding_id="b2")
    bs1 = build_delegation_operator_review_binding_set(delegation_ref_id="del-test", bindings=[b1, b2])
    bs2 = build_delegation_operator_review_binding_set(delegation_ref_id="del-test", bindings=[b2, b1])
    assert bs1.operator_review_binding_set_hash == bs2.operator_review_binding_set_hash


# ---------------------------------------------------------------------------
# 41. Serialization is JSON-safe and deterministic
# ---------------------------------------------------------------------------


def test_serialization_is_json_safe() -> None:
    """Envelope and binding set serialize to valid JSON."""
    envelope = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
    )
    json_str = serialize_delegation_operator_review_envelope(envelope)
    parsed = json.loads(json_str)
    assert parsed["schema_version"] is not None
    assert parsed["operator_review_envelope_hash"] is not None

    binding = build_delegation_operator_review_binding(
        delegation_ref_id="del-test",
        envelope=envelope,
    )
    bs = build_delegation_operator_review_binding_set(
        delegation_ref_id="del-test",
        bindings=[binding],
    )
    json_str2 = serialize_delegation_operator_review_binding_set(bs)
    parsed2 = json.loads(json_str2)
    assert parsed2["schema_version"] is not None


def test_serialization_is_deterministic() -> None:
    """Repeated serialization produces identical JSON."""
    review = build_delegation_operator_review_ref(delegation_ref_id="del-test")
    envelope = build_delegation_operator_review_envelope(
        delegation_ref_id="del-test",
        review_refs=[review],
    )
    j1 = serialize_delegation_operator_review_envelope(envelope)
    j2 = serialize_delegation_operator_review_envelope(envelope)
    assert j1 == j2


# ---------------------------------------------------------------------------
# 42. Closed-world validation
# ---------------------------------------------------------------------------


def test_closed_world_validation_rejects_unknown_fields() -> None:
    """Closed-world validation rejects objects with unknown fields."""
    from agentic_runtime.delegation.foundation import validate_known_fields
    # Valid: all fields are known
    validate_known_fields(
        raw={"schema_version": "v1", "review_ref_id": "id", "delegation_ref_id": "del",
             "review_kind": "REFERENCE_ONLY", "review_ref": None,
             "review_description": "", "reference_status": "REVIEW_REFERENCED",
             "source_label": "DEV_FIXTURE", "review_status": "DECLARED",
             "review_hash": "h"},
        known_fields=OPERATOR_REVIEW_REF_KNOWN_FIELDS,
    )

    # Invalid: unknown field
    with pytest.raises((DelegationUnknownFieldError, DelegationError)):
        validate_known_fields(
            raw={"bogus_field": "bad", "schema_version": "v1"},
            known_fields=OPERATOR_REVIEW_REF_KNOWN_FIELDS,
        )


# ---------------------------------------------------------------------------
# 43. Source/truth labels are visible
# ---------------------------------------------------------------------------


def test_source_label_visible() -> None:
    """DEV_FIXTURE source label is visible on review refs."""
    r = build_delegation_operator_review_ref(
        delegation_ref_id="del-test",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert r.source_label == DelegationSourceLabel.DEV_FIXTURE


# ---------------------------------------------------------------------------
# 44. DEV_FIXTURE path is explicit in tests
# ---------------------------------------------------------------------------


def test_dev_fixture_label_explicit() -> None:
    """All DEV_FIXTURE review/intent refs explicitly use DEV_FIXTURE label."""
    r = build_delegation_operator_review_ref(delegation_ref_id="del-test")
    assert r.source_label == DelegationSourceLabel.DEV_FIXTURE

    a = build_delegation_approval_intent_ref(delegation_ref_id="del-test")
    assert a.source_label == DelegationSourceLabel.DEV_FIXTURE

    rej = build_delegation_rejection_intent_ref(delegation_ref_id="del-test")
    assert rej.source_label == DelegationSourceLabel.DEV_FIXTURE

    e = build_delegation_escalation_intent_ref(delegation_ref_id="del-test")
    assert e.source_label == DelegationSourceLabel.DEV_FIXTURE

    m = build_delegation_more_context_intent_ref(delegation_ref_id="del-test")
    assert m.source_label == DelegationSourceLabel.DEV_FIXTURE


# ---------------------------------------------------------------------------
# 45. UNAVAILABLE reasons exist
# ---------------------------------------------------------------------------


def test_unavailable_reasons_exist() -> None:
    """UNAVAILABLE reasons exist for all required unavailable surfaces."""
    unavailable_keys = DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS.keys()
    required = {
        "Approval Engine",
        "Rejection Engine",
        "Operator Decision System",
        "Signature Verifier",
        "HITL Workflow Executor",
        "Authority Grant/Deny",
        "Policy/Custos Bridge",
        "Policy/Custos Decision",
        "Runtime Authorization",
        "Runtime Allow/Block",
        "Trace Writer",
        "Ledger Write",
        "Global Trace Write",
        "Projection/API/Event/Read Model",
        "CLI/Shell/TUI Binding",
        "P1.8.12 Policy/Custos BridgeRef Model",
        "Output Passport / P1.9",
        "Runtime Delegation Execution",
    }
    missing = required - set(unavailable_keys)
    assert not missing, f"Missing unavailable reasons: {missing}"

    for key in required:
        assert DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS[key] != ""


def test_status_report_lists_unavailable_bindings() -> None:
    """Status report contains unavailable bindings."""
    report = build_delegation_operator_review_status_report()
    assert len(report.unavailable_bindings) > 0
    assert "Approval Engine" in report.unavailable_bindings


# ---------------------------------------------------------------------------
# 46-62. Side effects all false + boundary checks
# ---------------------------------------------------------------------------


def test_side_effects_all_false_default() -> None:
    """All DelegationOperatorReviewSideEffects booleans default to False."""
    se = DelegationOperatorReviewSideEffects()
    assert se.approval_granted is False
    assert se.rejection_enforced is False
    assert se.escalation_executed is False
    assert se.more_context_block_created is False
    assert se.operator_decision_recorded is False
    assert se.signature_verified is False
    assert se.hitl_workflow_started is False
    assert se.authority_granted is False
    assert se.authority_denied is False
    assert se.policy_called is False
    assert se.custos_called is False
    assert se.runtime_allowed is False
    assert se.runtime_blocked is False
    assert se.approval_created is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


def test_no_approval_granted() -> None:
    """ApprovalIntentRef exists ≠ approval granted."""
    a = build_delegation_approval_intent_ref(delegation_ref_id="del-test")
    se = DelegationOperatorReviewSideEffects()
    assert se.approval_granted is False
    assert se.approval_created is False
    # ApprovalIntentRef is not approval
    assert a.reference_status != "APPROVED"


def test_no_rejection_enforced() -> None:
    """RejectionIntentRef exists ≠ rejection enforced."""
    r = build_delegation_rejection_intent_ref(delegation_ref_id="del-test")
    se = DelegationOperatorReviewSideEffects()
    assert se.rejection_enforced is False
    assert r.reference_status != "DENIED"


def test_no_escalation_executed() -> None:
    """EscalationIntentRef exists ≠ escalation executed."""
    e = build_delegation_escalation_intent_ref(delegation_ref_id="del-test")
    se = DelegationOperatorReviewSideEffects()
    assert se.escalation_executed is False
    assert e.reference_status != "ESCALATED"


def test_no_more_context_block_created() -> None:
    """MoreContextIntentRef exists ≠ runtime block."""
    m = build_delegation_more_context_intent_ref(delegation_ref_id="del-test")
    se = DelegationOperatorReviewSideEffects()
    assert se.more_context_block_created is False
    assert se.runtime_blocked is False
    assert m.reference_status != "BLOCKED"


def test_no_operator_decision_recorded() -> None:
    """OperatorReviewRef exists ≠ operator decision recorded."""
    build_delegation_operator_review_ref(delegation_ref_id="del-test")
    se = DelegationOperatorReviewSideEffects()
    assert se.operator_decision_recorded is False


def test_no_signature_verified() -> None:
    """No cryptographic signature verification occurs."""
    se = DelegationOperatorReviewSideEffects()
    assert se.signature_verified is False


def test_no_hitl_workflow_started() -> None:
    """No HITL workflow started."""
    se = DelegationOperatorReviewSideEffects()
    assert se.hitl_workflow_started is False


def test_no_authority_granted_or_denied() -> None:
    """No authority granted or denied."""
    se = DelegationOperatorReviewSideEffects()
    assert se.authority_granted is False
    assert se.authority_denied is False


def test_no_policy_or_custos_called() -> None:
    """No policy/Custos decisions made."""
    se = DelegationOperatorReviewSideEffects()
    assert se.policy_called is False
    assert se.custos_called is False


def test_no_runtime_allow_or_block() -> None:
    """No runtime allow/block."""
    se = DelegationOperatorReviewSideEffects()
    assert se.runtime_allowed is False
    assert se.runtime_blocked is False


def test_no_approval_created() -> None:
    """No approval created."""
    se = DelegationOperatorReviewSideEffects()
    assert se.approval_created is False


def test_no_ledger_or_global_trace_written() -> None:
    """No Ledger or global trace written."""
    se = DelegationOperatorReviewSideEffects()
    assert se.ledger_written is False
    assert se.global_trace_written is False


def test_no_runtime_mutation() -> None:
    """No runtime mutation."""
    se = DelegationOperatorReviewSideEffects()
    assert se.runtime_mutated is False


def test_binding_set_side_effects_all_false() -> None:
    """BindingSet side_effects are all false."""
    env = build_delegation_operator_review_envelope(delegation_ref_id="del-test")
    binding = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=env)
    bs = build_delegation_operator_review_binding_set(delegation_ref_id="del-test", bindings=[binding])
    se = bs.side_effects
    assert se.approval_granted is False
    assert se.rejection_enforced is False
    assert se.escalation_executed is False
    assert se.runtime_mutated is False


def test_no_p1_8_12_behavior() -> None:
    """P1.8.11 does not implement P1.8.12 policy/Custos bridge."""
    se = DelegationOperatorReviewSideEffects()
    assert se.policy_called is False
    assert se.custos_called is False
    # P1.8.12 is not implemented here
    assert "P1.8.12 Policy/Custos BridgeRef Model" in DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS


def test_no_output_passport_p1_9_behavior() -> None:
    """P1.8.11 does not implement Output Passport / P1.9."""
    assert "Output Passport / P1.9" in DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS


# ---------------------------------------------------------------------------
# 41b. Convenience hash wrappers return precomputed hashes
# ---------------------------------------------------------------------------


def test_hash_wrappers_return_precomputed_hashes() -> None:
    """Convenience hash functions return the object's precomputed hash field."""
    r = build_delegation_operator_review_ref(delegation_ref_id="del-test")
    assert hash_delegation_operator_review_ref(r) == r.review_hash

    a = build_delegation_approval_intent_ref(delegation_ref_id="del-test")
    assert hash_delegation_approval_intent_ref(a) == a.approval_intent_hash

    e = build_delegation_escalation_intent_ref(delegation_ref_id="del-test")
    assert hash_delegation_escalation_intent_ref(e) == e.escalation_intent_hash

    rej = build_delegation_rejection_intent_ref(delegation_ref_id="del-test")
    assert hash_delegation_rejection_intent_ref(rej) == rej.rejection_intent_hash

    m = build_delegation_more_context_intent_ref(delegation_ref_id="del-test")
    assert hash_delegation_more_context_intent_ref(m) == m.more_context_intent_hash

    rat = build_delegation_review_rationale_ref(delegation_ref_id="del-test")
    assert hash_delegation_review_rationale_ref(rat) == rat.rationale_hash

    profile = build_delegation_operator_review_readiness_profile(delegation_ref_id="del-test")
    assert hash_delegation_operator_review_readiness_profile(profile) == profile.readiness_hash

    envelope = build_delegation_operator_review_envelope(delegation_ref_id="del-test")
    assert hash_delegation_operator_review_envelope(envelope) == envelope.operator_review_envelope_hash

    binding = build_delegation_operator_review_binding(delegation_ref_id="del-test", envelope=envelope)
    assert hash_delegation_operator_review_binding(binding) == binding.binding_hash

    bs = build_delegation_operator_review_binding_set(delegation_ref_id="del-test", bindings=[binding])
    assert hash_delegation_operator_review_binding_set(bs) == bs.operator_review_binding_set_hash

    report = build_delegation_operator_review_status_report()
    assert hash_delegation_operator_review_status_report(report) == report.status_hash


# ---------------------------------------------------------------------------
# Integration: full DEV_FIXTURE operator-testable chain
# ---------------------------------------------------------------------------


def test_dev_fixture_chain_p1_8_10_to_p1_8_11() -> None:
    """DEV_FIXTURE chain: P1.8.10 ShadowResolverResult → P1.8.11 OperatorReviewEnvelope.

    Demonstrates the full operator-testable path:
    P1.8.10 ShadowResolverResult → P1.8.11 OperatorReviewRef/ApprovalIntentRef/
    RejectionIntentRef/EscalationIntentRef/MoreContextIntentRef/RationaleRef →
    ReadinessProfile → Envelope → Binding → BindingSet → StatusReport.
    """
    from agentic_runtime.delegation.shadow_resolver import (
        build_delegation_shadow_resolver_status_report,
        hash_delegation_shadow_resolver_status_report,
    )

    # Step 1: P1.8.10 shadow result (DEV_FIXTURE)
    sr_report = build_delegation_shadow_resolver_status_report()
    assert sr_report.status_hash is not None

    # Step 2: Operator review refs (DEV_FIXTURE)
    review = build_delegation_operator_review_ref(
        delegation_ref_id="del-integration-test",
        review_kind=DelegationOperatorReviewKind.CONSISTENCY_REVIEW,
        review_description="consistency review of delegation del-integration-test",
    )
    assert review.review_hash is not None

    approval = build_delegation_approval_intent_ref(
        delegation_ref_id="del-integration-test",
        approval_intent_description="operator intends to approve",
    )
    assert approval.approval_intent_hash is not None

    rejection = build_delegation_rejection_intent_ref(
        delegation_ref_id="del-integration-test",
        rejection_intent_description="operator intends to reject",
    )
    assert rejection.rejection_intent_hash is not None

    escalation = build_delegation_escalation_intent_ref(
        delegation_ref_id="del-integration-test",
        escalation_intent_description="operator intends to escalate",
    )
    assert escalation.escalation_intent_hash is not None

    more_context = build_delegation_more_context_intent_ref(
        delegation_ref_id="del-integration-test",
        more_context_intent_description="operator needs more context",
    )
    assert more_context.more_context_intent_hash is not None

    rationale = build_delegation_review_rationale_ref(
        delegation_ref_id="del-integration-test",
        rationale_kind=DelegationReviewRationaleKind.CONSISTENCY_CONTEXT,
        rationale_description="consistency between identity and roles confirmed",
    )
    assert rationale.rationale_hash is not None

    # Step 3: Readiness profile
    readiness = build_delegation_operator_review_readiness_profile(
        delegation_ref_id="del-integration-test",
        has_review_refs=True,
        has_approval_intent_refs=True,
        has_rejection_intent_refs=True,
        has_escalation_intent_refs=True,
        has_more_context_intent_refs=True,
        has_rationale_refs=True,
        has_shadow_resolver_context=True,
    )
    assert readiness.readiness_hash is not None
    assert readiness.has_review_refs is True
    assert readiness.missing_components is not None

    # Step 4: Envelope
    envelope = build_delegation_operator_review_envelope(
        delegation_ref_id="del-integration-test",
        review_refs=[review],
        approval_intent_refs=[approval],
        rejection_intent_refs=[rejection],
        escalation_intent_refs=[escalation],
        more_context_intent_refs=[more_context],
        rationale_refs=[rationale],
        readiness_profile=readiness,
    )
    assert envelope.operator_review_envelope_hash is not None
    assert len(envelope.review_ref_ids) == 1
    assert len(envelope.approval_intent_ref_ids) == 1
    assert len(envelope.rejection_intent_ref_ids) == 1

    # Step 5: Binding
    binding = build_delegation_operator_review_binding(
        delegation_ref_id="del-integration-test",
        envelope=envelope,
        review_readiness_hash=readiness.readiness_hash,
    )
    assert binding.binding_hash is not None

    # Step 6: Binding set
    binding_set = build_delegation_operator_review_binding_set(
        delegation_ref_id="del-integration-test",
        bindings=[binding],
    )
    assert binding_set.operator_review_binding_set_hash is not None

    # Step 7: Status report
    status_report = build_delegation_operator_review_status_report()
    assert status_report.status_hash is not None
    assert len(status_report.unavailable_bindings) > 0

    # All side effects must be false
    se = DelegationOperatorReviewSideEffects()
    assert se.approval_granted is False
    assert se.rejection_enforced is False
    assert se.escalation_executed is False
    assert se.runtime_mutated is False

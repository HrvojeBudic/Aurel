"""Focused P1.8.8 lifecycle model tests (DEV_FIXTURE).

All lifecycle refs are reference-only; no runtime expiry, revocation,
suspension, renewal, supersession, enforcement, scheduling, permission
removal, authority mutation, policy/Custos, approval, trace, or Ledger
behavior is implemented or claimed.
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.delegation import (
    DelegationLifecycleSideEffects as LfSE,
    DelegationExpiryRef,
    DelegationLifecycleBinding,
    DelegationLifecycleBindingSet,
    DelegationLifecycleEnvelope,
    DelegationLifecycleEventKind,
    DelegationLifecycleReadinessProfile,
    DelegationLifecycleReferenceStatus,
    DelegationLifecycleSideEffects,
    DelegationLifecycleStatus,
    DelegationLifecycleStatusReport,
    DelegationRenewalRef,
    DelegationRevocationReasonKind,
    DelegationRevocationReasonRef,
    DelegationRevocationRef,
    DelegationSupersessionRef,
    DelegationSuspensionRef,
    DelegationError,
    DelegationScopeBindingSet,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    DELEGATION_LIFECYCLE_UNAVAILABLE_BINDINGS,
    build_delegation_expiry_ref,
    build_delegation_lifecycle_binding,
    build_delegation_lifecycle_binding_set,
    build_delegation_lifecycle_envelope,
    build_delegation_lifecycle_readiness_profile,
    build_delegation_lifecycle_status_report,
    build_delegation_renewal_ref,
    build_delegation_revocation_reason_ref,
    build_delegation_revocation_ref,
    build_delegation_scope_binding_set,
    build_delegation_supersession_ref,
    build_delegation_suspension_ref,
    hash_delegation_expiry_ref,
    hash_delegation_lifecycle_binding_set,
    hash_delegation_lifecycle_envelope,
    hash_delegation_lifecycle_readiness_profile,
    hash_delegation_renewal_ref,
    hash_delegation_revocation_reason_ref,
    hash_delegation_revocation_ref,
    hash_delegation_supersession_ref,
    hash_delegation_suspension_ref,
    serialize_delegation_lifecycle_binding_set,
    serialize_delegation_lifecycle_envelope,
)
from agentic_runtime.delegation.foundation import (
    DelegationSourceLabel as DSL,
    validate_known_fields,
)

# ---------------------------------------------------------------------------
# Reusable DEV_FIXTURE helpers
# ---------------------------------------------------------------------------

_DELEGATION_REF_ID = "P1.8.8-test-delegation-ref"
_ID_HASH = "abc123def456"
_ROLE_HASH = "role-111"
_CONSTRAINT_HASH = "constraint-111"
_AUTHORITY_HASH = "authority-111"
_EVIDENCE_HASH = "evidence-111"
_MESH_HASH = "mesh-111"
_SCOPE_HASH = "scope-111"


def _make_scope_binding_set() -> DelegationScopeBindingSet:
    """Build a minimal P1.8.7 ScopeBindingSet as feeder for lifecycle path."""
    return build_delegation_scope_binding_set(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
    )


# ===========================================================================
# 1. Imports / existing exports remain importable
# ===========================================================================


def test_imports_work():
    """All P1.8.8 lifecycle symbols import."""
    assert DelegationExpiryRef is not None
    assert DelegationLifecycleSideEffects is not None


def test_existing_p180_exports_remain():
    """P1.8.0 DelegationRecord remains importable."""
    from agentic_runtime.delegation import DelegationRecord
    assert DelegationRecord is not None


def test_existing_p187_exports_remain():
    """P1.8.7 ScopeBindingSet remains importable."""
    scope_set = _make_scope_binding_set()
    assert scope_set is not None
    assert scope_set.delegation_ref_id == _DELEGATION_REF_ID


def test_p187_scope_binding_set_feeds_p188_lifecycle_path():
    """P1.8.7 ScopeBindingSet can feed P1.8.8 lifecycle path with scope hash."""
    scope_set = _make_scope_binding_set()
    assert scope_set.scope_binding_set_hash
    # Feed scope hash into lifecycle envelope
    envelope = build_delegation_lifecycle_envelope(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=scope_set.scope_binding_set_hash,
        lifecycle_readiness_hash="readiness-hash-1",
    )
    assert envelope.scope_binding_set_hash == scope_set.scope_binding_set_hash


# ===========================================================================
# 2. Enums exist
# ===========================================================================


def test_lifecycle_event_kind_enum():
    assert DelegationLifecycleEventKind.EXPIRY.value == "EXPIRY"
    assert DelegationLifecycleEventKind.REVOCATION.value == "REVOCATION"
    assert DelegationLifecycleEventKind.SUSPENSION.value == "SUSPENSION"
    assert DelegationLifecycleEventKind.RENEWAL.value == "RENEWAL"
    assert DelegationLifecycleEventKind.SUPERSESSION.value == "SUPERSESSION"
    assert DelegationLifecycleEventKind.REASON.value == "REASON"
    assert DelegationLifecycleEventKind.UNKNOWN.value == "UNKNOWN"


def test_lifecycle_reference_status_enum():
    assert DelegationLifecycleReferenceStatus.REFERENCE_ONLY.value == "REFERENCE_ONLY"
    assert DelegationLifecycleReferenceStatus.EXPIRY_REFERENCED.value == "EXPIRY_REFERENCED"
    assert DelegationLifecycleReferenceStatus.REVOCATION_REFERENCED.value == "REVOCATION_REFERENCED"
    assert DelegationLifecycleReferenceStatus.SUSPENSION_REFERENCED.value == "SUSPENSION_REFERENCED"
    assert DelegationLifecycleReferenceStatus.RENEWAL_REFERENCED.value == "RENEWAL_REFERENCED"
    assert DelegationLifecycleReferenceStatus.SUPERSESSION_REFERENCED.value == "SUPERSESSION_REFERENCED"
    assert DelegationLifecycleReferenceStatus.ENFORCEMENT_UNAVAILABLE.value == "ENFORCEMENT_UNAVAILABLE"
    assert DelegationLifecycleReferenceStatus.SCHEDULER_UNAVAILABLE.value == "SCHEDULER_UNAVAILABLE"
    assert DelegationLifecycleReferenceStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert DelegationLifecycleReferenceStatus.ERROR.value == "ERROR"
    assert DelegationLifecycleReferenceStatus.UNKNOWN.value == "UNKNOWN"


def test_lifecycle_status_enum():
    assert DelegationLifecycleStatus.REFERENCE_ONLY.value == "REFERENCE_ONLY"
    assert DelegationLifecycleStatus.DECLARED.value == "DECLARED"
    assert DelegationLifecycleStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert DelegationLifecycleStatus.ERROR.value == "ERROR"
    assert DelegationLifecycleStatus.UNKNOWN.value == "UNKNOWN"


def test_revocation_reason_kind_enum():
    assert DelegationRevocationReasonKind.OPERATOR_DECLARED.value == "OPERATOR_DECLARED"
    assert DelegationRevocationReasonKind.POLICY_CONTEXT.value == "POLICY_CONTEXT"
    assert DelegationRevocationReasonKind.AUTHORITY_CONTEXT.value == "AUTHORITY_CONTEXT"
    assert DelegationRevocationReasonKind.SCOPE_CONTEXT.value == "SCOPE_CONTEXT"
    assert DelegationRevocationReasonKind.RISK_CONTEXT.value == "RISK_CONTEXT"
    assert DelegationRevocationReasonKind.EVIDENCE_CONTEXT.value == "EVIDENCE_CONTEXT"
    assert DelegationRevocationReasonKind.UNKNOWN.value == "UNKNOWN"


# ===========================================================================
# 3. ExpiryRef builds deterministically
# ===========================================================================


def test_expiry_ref_builds_deterministic():
    a = build_delegation_expiry_ref("expiry-2026-Q3", _DELEGATION_REF_ID)
    b = build_delegation_expiry_ref("expiry-2026-Q3", _DELEGATION_REF_ID)
    assert a.expiry_hash == b.expiry_hash
    assert a.expiry_ref_id == b.expiry_ref_id
    assert a.schema_version == "delegation_expiry_ref.v1"
    assert a.reference_status == DelegationLifecycleReferenceStatus.EXPIRY_REFERENCED
    assert a.lifecycle_status == DelegationLifecycleStatus.DECLARED
    assert a.source_label == DelegationSourceLabel.DEV_FIXTURE


def test_expiry_ref_hash_changes_on_different_ref():
    a = build_delegation_expiry_ref("expiry-2026-Q3", _DELEGATION_REF_ID)
    b = build_delegation_expiry_ref("expiry-2027-Q1", _DELEGATION_REF_ID)
    assert a.expiry_hash != b.expiry_hash


def test_expiry_ref_hash_changes_on_different_description():
    a = build_delegation_expiry_ref("expiry-X", _DELEGATION_REF_ID,
                                   expiry_description="desc A")
    b = build_delegation_expiry_ref("expiry-X", _DELEGATION_REF_ID,
                                   expiry_description="desc B")
    assert a.expiry_hash != b.expiry_hash


# ===========================================================================
# 4. RevocationRef builds deterministically
# ===========================================================================


def test_revocation_ref_builds_deterministic():
    a = build_delegation_revocation_ref("revoke-001", _DELEGATION_REF_ID)
    b = build_delegation_revocation_ref("revoke-001", _DELEGATION_REF_ID)
    assert a.revocation_hash == b.revocation_hash
    assert a.revocation_ref_id == b.revocation_ref_id


def test_revocation_ref_hash_changes_on_reason_ref_id():
    a = build_delegation_revocation_ref("revoke-001", _DELEGATION_REF_ID,
                                        reason_ref_id="reason-1")
    b = build_delegation_revocation_ref("revoke-001", _DELEGATION_REF_ID,
                                        reason_ref_id="reason-2")
    assert a.revocation_hash != b.revocation_hash


def test_revocation_ref_hash_changes_on_desc():
    a = build_delegation_revocation_ref("revoke-001", _DELEGATION_REF_ID,
                                       revocation_description="d1")
    b = build_delegation_revocation_ref("revoke-001", _DELEGATION_REF_ID,
                                       revocation_description="d2")
    assert a.revocation_hash != b.revocation_hash


# ===========================================================================
# 5. SuspensionRef builds deterministically
# ===========================================================================


def test_suspension_ref_builds_deterministic():
    a = build_delegation_suspension_ref("suspend-001", _DELEGATION_REF_ID)
    b = build_delegation_suspension_ref("suspend-001", _DELEGATION_REF_ID)
    assert a.suspension_hash == b.suspension_hash
    assert a.suspension_ref_id == b.suspension_ref_id


def test_suspension_ref_hash_changes():
    a = build_delegation_suspension_ref("suspend-001", _DELEGATION_REF_ID)
    b = build_delegation_suspension_ref("suspend-002", _DELEGATION_REF_ID)
    assert a.suspension_hash != b.suspension_hash


# ===========================================================================
# 6. RenewalRef builds deterministically
# ===========================================================================


def test_renewal_ref_builds_deterministic():
    a = build_delegation_renewal_ref("renew-001", _DELEGATION_REF_ID)
    b = build_delegation_renewal_ref("renew-001", _DELEGATION_REF_ID)
    assert a.renewal_hash == b.renewal_hash


def test_renewal_ref_hash_changes():
    a = build_delegation_renewal_ref("renew-001", _DELEGATION_REF_ID)
    b = build_delegation_renewal_ref("renew-002", _DELEGATION_REF_ID)
    assert a.renewal_hash != b.renewal_hash


# ===========================================================================
# 7. SupersessionRef builds deterministically
# ===========================================================================


def test_supersession_ref_builds_deterministic():
    a = build_delegation_supersession_ref("super-001", _DELEGATION_REF_ID)
    b = build_delegation_supersession_ref("super-001", _DELEGATION_REF_ID)
    assert a.supersession_hash == b.supersession_hash


def test_supersession_ref_hash_changes_with_superseded_by():
    a = build_delegation_supersession_ref("super-001", _DELEGATION_REF_ID,
                                          superseded_by_ref="old-del-1")
    b = build_delegation_supersession_ref("super-001", _DELEGATION_REF_ID,
                                          superseded_by_ref="old-del-2")
    assert a.supersession_hash != b.supersession_hash


# ===========================================================================
# 8. ReasonRef builds deterministically
# ===========================================================================


def test_reason_ref_builds_deterministic():
    a = build_delegation_revocation_reason_ref("reason-001", _DELEGATION_REF_ID)
    b = build_delegation_revocation_reason_ref("reason-001", _DELEGATION_REF_ID)
    assert a.reason_hash == b.reason_hash
    assert a.reason_ref_id == b.reason_ref_id


def test_reason_ref_hash_changes_on_kind():
    a = build_delegation_revocation_reason_ref(
        "reason-001", _DELEGATION_REF_ID,
        reason_kind=DelegationRevocationReasonKind.RISK_CONTEXT)
    b = build_delegation_revocation_reason_ref(
        "reason-001", _DELEGATION_REF_ID,
        reason_kind=DelegationRevocationReasonKind.SCOPE_CONTEXT)
    assert a.reason_hash != b.reason_hash


def test_reason_ref_hash_changes_on_description():
    a = build_delegation_revocation_reason_ref(
        "reason-001", _DELEGATION_REF_ID, reason_description="alpha")
    b = build_delegation_revocation_reason_ref(
        "reason-001", _DELEGATION_REF_ID, reason_description="beta")
    assert a.reason_hash != b.reason_hash


# ===========================================================================
# 9. LifecycleReadinessProfile
# ===========================================================================


def test_readiness_profile_builds_deterministic():
    a = build_delegation_lifecycle_readiness_profile(_DELEGATION_REF_ID)
    b = build_delegation_lifecycle_readiness_profile(_DELEGATION_REF_ID)
    assert a.readiness_hash == b.readiness_hash


def test_readiness_profile_hash_changes():
    a = build_delegation_lifecycle_readiness_profile(_DELEGATION_REF_ID)
    b = build_delegation_lifecycle_readiness_profile(
        _DELEGATION_REF_ID, has_expiry_refs=True)
    assert a.readiness_hash != b.readiness_hash


def test_readiness_profile_reports_present_components():
    profile = build_delegation_lifecycle_readiness_profile(
        _DELEGATION_REF_ID,
        has_expiry_refs=True,
        has_revocation_refs=True,
    )
    assert profile.has_expiry_refs is True
    assert profile.has_revocation_refs is True
    assert profile.has_suspension_refs is False


def test_readiness_profile_reports_missing_components():
    profile = build_delegation_lifecycle_readiness_profile(
        _DELEGATION_REF_ID,
        missing_components=["expiry", "revocation"],
    )
    missing = list(profile.missing_components)
    assert "expiry" in missing
    assert "revocation" in missing


def test_readiness_profile_is_not_scheduler_active():
    profile = build_delegation_lifecycle_readiness_profile(_DELEGATION_REF_ID)
    assert "Scheduler" in profile.scheduler_unavailable_reason
    assert "reference-only" in profile.scheduler_unavailable_reason


def test_readiness_profile_is_not_enforcement_guarantee():
    profile = build_delegation_lifecycle_readiness_profile(_DELEGATION_REF_ID)
    assert "Enforcement" in profile.enforcement_unavailable_reason
    assert "not P1.8.8" in profile.enforcement_unavailable_reason


# ===========================================================================
# 10. LifecycleEnvelope
# ===========================================================================


def _make_envelope() -> DelegationLifecycleEnvelope:
    return build_delegation_lifecycle_envelope(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        lifecycle_readiness_hash="readiness-001",
    )


def test_envelope_builds_deterministic():
    a = _make_envelope()
    b = _make_envelope()
    assert a.lifecycle_envelope_hash == b.lifecycle_envelope_hash


def test_envelope_hash_changes_with_membership():
    a = _make_envelope()
    b = build_delegation_lifecycle_envelope(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        lifecycle_readiness_hash="readiness-001",
        expiry_refs=["expiry-1"],
    )
    assert a.lifecycle_envelope_hash != b.lifecycle_envelope_hash


def test_envelope_ordering_deterministic():
    a = build_delegation_lifecycle_envelope(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        lifecycle_readiness_hash="r1",
        expiry_refs=["b-exp", "a-exp", "c-exp"],
    )
    b = build_delegation_lifecycle_envelope(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        lifecycle_readiness_hash="r1",
        expiry_refs=["a-exp", "b-exp", "c-exp"],
    )
    assert a.lifecycle_envelope_hash == b.lifecycle_envelope_hash


def test_envelope_serialization_json_safe():
    envelope = _make_envelope()
    js = serialize_delegation_lifecycle_envelope(envelope)
    assert isinstance(js, str)
    data = json.loads(js)
    assert data["schema_version"] == "delegation_lifecycle_envelope.v1"


# ===========================================================================
# 11. LifecycleBinding
# ===========================================================================


def _make_binding() -> DelegationLifecycleBinding:
    envelope = _make_envelope()
    return build_delegation_lifecycle_binding(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        lifecycle_envelope_hash=envelope.lifecycle_envelope_hash,
        lifecycle_readiness_hash="readiness-001",
    )


def test_binding_builds_deterministic():
    a = _make_binding()
    b = _make_binding()
    assert a.binding_hash == b.binding_hash


# ===========================================================================
# 12. LifecycleBindingSet
# ===========================================================================


def _make_binding_set():
    binding = _make_binding()
    return build_delegation_lifecycle_binding_set(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        bindings=[binding],
    )


def test_binding_set_builds_deterministic():
    a = _make_binding_set()
    b = _make_binding_set()
    assert a.lifecycle_binding_set_hash == b.lifecycle_binding_set_hash


def test_binding_set_hash_changes_on_membership():
    a = _make_binding_set()
    b1 = _make_binding()
    b2 = build_delegation_lifecycle_binding(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        lifecycle_envelope_hash=_make_envelope().lifecycle_envelope_hash,
        lifecycle_readiness_hash="readiness-002",
    )
    bs = build_delegation_lifecycle_binding_set(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=_SCOPE_HASH,
        bindings=[b1, b2],
    )
    assert a.lifecycle_binding_set_hash != bs.lifecycle_binding_set_hash


def test_binding_set_serialization_json_safe():
    bs = _make_binding_set()
    js = serialize_delegation_lifecycle_binding_set(bs)
    assert isinstance(js, str)
    data = json.loads(js)
    assert data["schema_version"] == "delegation_lifecycle_binding_set.v1"


# ===========================================================================
# 13. Hash helper functions return stable ref hashes
# ===========================================================================


def test_hash_expiry_ref():
    ref = build_delegation_expiry_ref("exp-test", _DELEGATION_REF_ID)
    assert hash_delegation_expiry_ref(ref) == ref.expiry_hash


def test_hash_revocation_ref():
    ref = build_delegation_revocation_ref("rev-test", _DELEGATION_REF_ID)
    assert hash_delegation_revocation_ref(ref) == ref.revocation_hash


def test_hash_suspension_ref():
    ref = build_delegation_suspension_ref("sus-test", _DELEGATION_REF_ID)
    assert hash_delegation_suspension_ref(ref) == ref.suspension_hash


def test_hash_renewal_ref():
    ref = build_delegation_renewal_ref("ren-test", _DELEGATION_REF_ID)
    assert hash_delegation_renewal_ref(ref) == ref.renewal_hash


def test_hash_supersession_ref():
    ref = build_delegation_supersession_ref("sup-test", _DELEGATION_REF_ID)
    assert hash_delegation_supersession_ref(ref) == ref.supersession_hash


def test_hash_reason_ref():
    ref = build_delegation_revocation_reason_ref("rea-test", _DELEGATION_REF_ID)
    assert hash_delegation_revocation_reason_ref(ref) == ref.reason_hash


def test_hash_readiness_profile():
    profile = build_delegation_lifecycle_readiness_profile(_DELEGATION_REF_ID)
    assert hash_delegation_lifecycle_readiness_profile(profile) == profile.readiness_hash


def test_hash_envelope():
    envelope = _make_envelope()
    assert hash_delegation_lifecycle_envelope(envelope) == envelope.lifecycle_envelope_hash


def test_hash_binding_set():
    bs = _make_binding_set()
    assert hash_delegation_lifecycle_binding_set(bs) == bs.lifecycle_binding_set_hash


# ===========================================================================
# 14. LifecycleStatusReport
# ===========================================================================


def test_status_report_builds():
    report = build_delegation_lifecycle_status_report()
    assert report.status_label == DSL.DEV_FIXTURE
    assert "DelegationExpiryRef" in report.available_contracts
    assert "Runtime Expiry Engine" in report.unavailable_bindings
    assert report.status_hash


def test_status_report_identical_builds_identical_hash():
    a = build_delegation_lifecycle_status_report()
    b = build_delegation_lifecycle_status_report()
    assert a.status_hash == b.status_hash


def test_status_report_unavailable_surfaces_present():
    report = build_delegation_lifecycle_status_report()
    una = dict(report.unavailable_bindings)
    assert "Projection/API/Event/Read Model" in una
    assert "CLI/Shell/TUI Binding" in una
    assert "Ledger Write" in una
    assert "Global Trace Write" in una
    assert "Runtime Expiry Engine" in una
    assert "Runtime Revocation Engine" in una
    assert "Scheduler/Timer Activation" in una
    assert "P1.8.9 Chain/Handoff Model" in una
    assert "Output Passport / P1.9" in una
    assert "Runtime Delegation Execution" in una


# ===========================================================================
# 15. Side effects all false
# ===========================================================================


def test_side_effects_all_false_default():
    se = DelegationLifecycleSideEffects()
    assert se.runtime_expired is False
    assert se.runtime_revoked is False
    assert se.runtime_suspended is False
    assert se.authority_renewed is False
    assert se.delegation_superseded is False
    assert se.permission_removed is False
    assert se.scheduler_activated is False
    assert se.runtime_cancelled is False
    assert se.policy_called is False
    assert se.custos_called is False
    assert se.approval_created is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


def test_side_effects_all_false_factory():
    se = DelegationLifecycleSideEffects.all_false()
    for field_name in [
        "runtime_expired", "runtime_revoked", "runtime_suspended",
        "authority_renewed", "delegation_superseded", "permission_removed",
        "scheduler_activated", "runtime_cancelled", "policy_called",
        "custos_called", "approval_created", "ledger_written",
        "global_trace_written", "runtime_mutated",
    ]:
        assert getattr(se, field_name) is False


def test_side_effects_in_binding_set():
    bs = _make_binding_set()
    assert isinstance(bs.side_effects, DelegationLifecycleSideEffects)
    assert bs.side_effects.runtime_expired is False
    assert bs.side_effects.runtime_revoked is False
    assert bs.side_effects.runtime_suspended is False


# ===========================================================================
# 16. Closed-world validation
# ===========================================================================


def test_closed_world_expiry_ref_rejects_unknown():
    from agentic_runtime.delegation.lifecycle import EXPIRY_REF_KNOWN_FIELDS
    with pytest.raises(DelegationUnknownFieldError):
        DelegationExpiryRef.from_dict({
            "expiry_ref": "x", "delegation_ref_id": "y",
            "not_a_field": True,
        })


def test_closed_world_envelope_rejects_unknown():
    with pytest.raises(DelegationUnknownFieldError):
        DelegationLifecycleEnvelope.from_dict({
            "delegation_ref_id": "x",
            "delegation_identity_hash": "h1",
            "role_binding_hash": "h2",
            "constraint_set_hash": "h3",
            "authority_binding_set_hash": "h4",
            "non_repudiation_binding_set_hash": "h5",
            "identity_mesh_binding_set_hash": "h6",
            "scope_binding_set_hash": "h7",
            "lifecycle_readiness_hash": "h8",
            "fake_enforce": True,
        })


def test_closed_world_binding_set_rejects_unknown():
    with pytest.raises(DelegationUnknownFieldError):
        DelegationLifecycleBindingSet.from_dict({
            "delegation_ref_id": "x",
            "delegation_identity_hash": "h1",
            "role_binding_hash": "h2",
            "constraint_set_hash": "h3",
            "authority_binding_set_hash": "h4",
            "non_repudiation_binding_set_hash": "h5",
            "identity_mesh_binding_set_hash": "h6",
            "scope_binding_set_hash": "h7",
            "extra_field": 1,
        })


# ===========================================================================
# 17. No runtime expiry / revocation / suspension / renewal / supersession
# ===========================================================================


def test_expiry_ref_is_not_runtime_expiry():
    """Expiry ref describes expiry metadata; it does not expire runtime delegation."""
    ref = build_delegation_expiry_ref("expiry-X", _DELEGATION_REF_ID)
    assert ref.reference_status == DelegationLifecycleReferenceStatus.EXPIRY_REFERENCED
    # EXPIRY_REFERENCED != runtime expired
    assert ref.reference_status != "runtime_expired"
    # Source label is DEV_FIXTURE, not LIVE
    assert ref.source_label == DSL.DEV_FIXTURE


def test_revocation_ref_is_not_runtime_revocation():
    ref = build_delegation_revocation_ref("revoke-X", _DELEGATION_REF_ID)
    assert ref.reference_status == DelegationLifecycleReferenceStatus.REVOCATION_REFERENCED
    assert ref.source_label == DSL.DEV_FIXTURE


def test_suspension_ref_is_not_runtime_pause():
    ref = build_delegation_suspension_ref("suspend-X", _DELEGATION_REF_ID)
    assert ref.reference_status == DelegationLifecycleReferenceStatus.SUSPENSION_REFERENCED
    assert ref.source_label == DSL.DEV_FIXTURE


def test_renewal_ref_is_not_authority_renewal():
    ref = build_delegation_renewal_ref("renew-X", _DELEGATION_REF_ID)
    assert ref.reference_status == DelegationLifecycleReferenceStatus.RENEWAL_REFERENCED
    assert ref.source_label == DSL.DEV_FIXTURE


def test_supersession_ref_is_not_invalidation():
    ref = build_delegation_supersession_ref("super-X", _DELEGATION_REF_ID)
    assert ref.reference_status == DelegationLifecycleReferenceStatus.SUPERSESSION_REFERENCED
    assert ref.source_label == DSL.DEV_FIXTURE


def test_reason_ref_is_not_verified_reason():
    ref = build_delegation_revocation_reason_ref("reason-X", _DELEGATION_REF_ID)
    assert ref.lifecycle_status == DelegationLifecycleStatus.DECLARED
    assert ref.source_label == DSL.DEV_FIXTURE
    # DECLARED != verified


def test_lifecycle_hash_is_not_trace_verified():
    envelope = _make_envelope()
    assert envelope.source_label == DSL.DEV_FIXTURE
    assert envelope.source_label != DSL.TRACE_VERIFIED


def test_binding_set_hash_is_not_proof_of_revocation_or_expiry():
    bs = _make_binding_set()
    assert bs.source_label == DSL.DEV_FIXTURE
    assert bs.source_label != DSL.TRACE_VERIFIED


# ===========================================================================
# 18. DEV_FIXTURE labels visible
# ===========================================================================


def test_dev_fixture_labels_visible():
    expiry = build_delegation_expiry_ref("e", _DELEGATION_REF_ID)
    assert expiry.source_label == DSL.DEV_FIXTURE
    reason = build_delegation_revocation_reason_ref("r", _DELEGATION_REF_ID)
    assert reason.source_label == DSL.DEV_FIXTURE
    report = build_delegation_lifecycle_status_report()
    assert report.status_label == DSL.DEV_FIXTURE
    envelope = _make_envelope()
    assert envelope.source_label == DSL.DEV_FIXTURE


# ===========================================================================
# 19. Envelope binds P1.8.0-P1.8.7 hashes without runtime lifecycle claim
# ===========================================================================


def test_envelope_binds_all_context_hashes():
    scope_set = _make_scope_binding_set()
    envelope = build_delegation_lifecycle_envelope(
        delegation_ref_id=_DELEGATION_REF_ID,
        delegation_identity_hash=_ID_HASH,
        role_binding_hash=_ROLE_HASH,
        constraint_set_hash=_CONSTRAINT_HASH,
        authority_binding_set_hash=_AUTHORITY_HASH,
        non_repudiation_binding_set_hash=_EVIDENCE_HASH,
        identity_mesh_binding_set_hash=_MESH_HASH,
        scope_binding_set_hash=scope_set.scope_binding_set_hash,
        lifecycle_readiness_hash="r1",
    )
    assert envelope.delegation_identity_hash == _ID_HASH
    assert envelope.role_binding_hash == _ROLE_HASH
    assert envelope.constraint_set_hash == _CONSTRAINT_HASH
    assert envelope.authority_binding_set_hash == _AUTHORITY_HASH
    assert envelope.non_repudiation_binding_set_hash == _EVIDENCE_HASH
    assert envelope.identity_mesh_binding_set_hash == _MESH_HASH
    assert envelope.scope_binding_set_hash is not None
    assert envelope.lifecycle_readiness_hash == "r1"


# ===========================================================================
# 20. round-trip from_dict consistency
# ===========================================================================


def test_expiry_ref_round_trip():
    ref = build_delegation_expiry_ref("exp-rt", _DELEGATION_REF_ID)
    d = ref.to_canonical_dict()
    reloaded = DelegationExpiryRef.from_dict(d)
    assert reloaded.expiry_hash == ref.expiry_hash


def test_envelope_round_trip():
    env = _make_envelope()
    d = env.to_canonical_dict()
    reloaded = DelegationLifecycleEnvelope.from_dict(d)
    assert reloaded.lifecycle_envelope_hash == env.lifecycle_envelope_hash


def test_binding_set_round_trip():
    bs = _make_binding_set()
    d = bs.to_canonical_dict()
    reloaded = DelegationLifecycleBindingSet.from_dict(d)
    assert reloaded.lifecycle_binding_set_hash == bs.lifecycle_binding_set_hash

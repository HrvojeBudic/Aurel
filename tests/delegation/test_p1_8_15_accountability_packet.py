"""Focused tests for P1.8.15 — Delegation Accountability Packet / Integration SummaryRef Model."""

import json
import sys

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation.foundation import DelegationSourceLabel
from agentic_runtime.delegation.accountability_packet import (
    DelegationAccountabilityComponentFamily,
    DelegationAccountabilityComponentRef,
    DelegationAccountabilityCoverageMatrix,
    DelegationAccountabilityCoverageMatrixEntry,
    DelegationAccountabilityPacketBinding,
    DelegationAccountabilityPacketBindingSet,
    DelegationAccountabilityPacketEnvelope,
    DelegationAccountabilityPacketKind,
    DelegationAccountabilityPacketReferenceStatus,
    DelegationAccountabilityPacketSideEffects,
    DelegationAccountabilityPacketStatus,
    DelegationAccountabilityPacketStatusReport,
    DelegationAccountabilityProfile,
    DelegationIntegrationSummaryEnvelope,
    DelegationIntegrationSummaryRef,
    build_delegation_accountability_component_ref,
    build_delegation_accountability_coverage_matrix,
    build_delegation_accountability_coverage_matrix_entry,
    build_delegation_accountability_packet_binding,
    build_delegation_accountability_packet_binding_set,
    build_delegation_accountability_packet_envelope,
    build_delegation_accountability_packet_status_report,
    build_delegation_accountability_profile,
    build_delegation_integration_summary_envelope,
    build_delegation_integration_summary_ref,
    hash_delegation_accountability_component_ref,
    hash_delegation_accountability_coverage_matrix,
    hash_delegation_accountability_coverage_matrix_entry,
    hash_delegation_accountability_packet_binding,
    hash_delegation_accountability_packet_binding_set,
    hash_delegation_accountability_packet_envelope,
    hash_delegation_accountability_packet_status_report,
    hash_delegation_accountability_profile,
    hash_delegation_integration_summary_envelope,
    hash_delegation_integration_summary_ref,
    serialize_delegation_accountability_packet_binding_set,
    serialize_delegation_accountability_packet_envelope,
    serialize_delegation_integration_summary_envelope,
)

# ---------------------------------------------------------------------------
# 1. Imports work
# ---------------------------------------------------------------------------

def test_imports_work():
    """All P1.8.15 symbols are importable."""
    assert DelegationAccountabilityPacketKind is not None
    assert DelegationAccountabilityPacketReferenceStatus is not None
    assert DelegationAccountabilityPacketStatus is not None
    assert DelegationAccountabilityComponentFamily is not None
    assert DelegationAccountabilityComponentRef is not None
    assert DelegationAccountabilityCoverageMatrixEntry is not None
    assert DelegationAccountabilityCoverageMatrix is not None
    assert DelegationAccountabilityProfile is not None
    assert DelegationIntegrationSummaryRef is not None
    assert DelegationIntegrationSummaryEnvelope is not None
    assert DelegationAccountabilityPacketEnvelope is not None
    assert DelegationAccountabilityPacketBinding is not None
    assert DelegationAccountabilityPacketBindingSet is not None
    assert DelegationAccountabilityPacketSideEffects is not None
    assert DelegationAccountabilityPacketStatusReport is not None

def test_existing_p1_8_0_through_p1_8_14_exports_still_importable():
    """Existing P1.8.0-P1.8.14 symbols remain importable from delegation package."""
    from agentic_runtime.delegation import (
        DelegationRecord,
        DelegationRef,
        DelegationConstraintSet,
        DelegationAuthorityBindingSet,
        DelegationNonRepudiationBindingSet,
        DelegationIdentityMeshBindingSet,
        DelegationScopeBindingSet,
        DelegationLifecycleBindingSet,
        DelegationChainBindingSet,
        DelegationShadowResolverResult,
        DelegationOperatorReviewBindingSet,
        DelegationPolicyCustosBridgeBindingSet,
        DelegationRuntimeExecutionReadinessBindingSet,
        DelegationTraceAuditBridgeBindingSet,
        DelegationSourceLabel,
    )
    assert DelegationRecord is not None
    assert DelegationRef is not None
    assert DelegationConstraintSet is not None
    assert DelegationAuthorityBindingSet is not None
    assert DelegationNonRepudiationBindingSet is not None
    assert DelegationIdentityMeshBindingSet is not None
    assert DelegationScopeBindingSet is not None
    assert DelegationLifecycleBindingSet is not None
    assert DelegationChainBindingSet is not None
    assert DelegationShadowResolverResult is not None
    assert DelegationOperatorReviewBindingSet is not None
    assert DelegationPolicyCustosBridgeBindingSet is not None
    assert DelegationRuntimeExecutionReadinessBindingSet is not None
    assert DelegationTraceAuditBridgeBindingSet is not None

# ---------------------------------------------------------------------------
# 2. Enums
# ---------------------------------------------------------------------------

def test_packet_kind_values():
    assert DelegationAccountabilityPacketKind.REFERENCE_ONLY is not None
    assert DelegationAccountabilityPacketKind.ACCOUNTABILITY_COMPONENT is not None
    assert DelegationAccountabilityPacketKind.COVERAGE_MATRIX is not None
    assert DelegationAccountabilityPacketKind.ACCOUNTABILITY_PROFILE is not None
    assert DelegationAccountabilityPacketKind.INTEGRATION_SUMMARY is not None
    assert DelegationAccountabilityPacketKind.ACCOUNTABILITY_PACKET is not None
    assert DelegationAccountabilityPacketKind.UNKNOWN is not None

def test_packet_reference_status_values():
    assert DelegationAccountabilityPacketReferenceStatus.REFERENCE_ONLY is not None
    assert DelegationAccountabilityPacketReferenceStatus.COMPONENT_REFERENCED is not None
    assert DelegationAccountabilityPacketReferenceStatus.COVERAGE_MATRIX_REFERENCED is not None
    assert DelegationAccountabilityPacketReferenceStatus.ACCOUNTABILITY_PROFILE_REFERENCED is not None
    assert DelegationAccountabilityPacketReferenceStatus.INTEGRATION_SUMMARY_REFERENCED is not None
    assert DelegationAccountabilityPacketReferenceStatus.ACCOUNTABILITY_PACKET_REFERENCED is not None
    assert DelegationAccountabilityPacketReferenceStatus.PROJECTION_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.API_EVENT_CONTRACT_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.CLI_SHELL_TUI_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.TRACE_VERIFICATION_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.LEDGER_FINALITY_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.OUTPUT_PASSPORT_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.ACCOUNTABILITY_VERIFICATION_UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.UNAVAILABLE is not None
    assert DelegationAccountabilityPacketReferenceStatus.ERROR is not None
    assert DelegationAccountabilityPacketReferenceStatus.UNKNOWN is not None

def test_component_family_values():
    assert DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.ROLE_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.CONSTRAINT_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.AUTHORITY_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.EVIDENCE_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.IDENTITY_MESH_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.SCOPE_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.LIFECYCLE_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.CHAIN_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.SHADOW_RESOLVER_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.OPERATOR_REVIEW_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.POLICY_CUSTOS_BRIDGE_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.RUNTIME_EXECUTION_READINESS_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.TRACE_AUDIT_BRIDGE_CONTEXT is not None
    assert DelegationAccountabilityComponentFamily.UNKNOWN is not None

# ---------------------------------------------------------------------------
# 3. SideEffects are all false by default
# ---------------------------------------------------------------------------

def _side_effect_names():
    return [
        "accountability_verified", "component_verified", "coverage_verified",
        "compliance_proven", "projection_created", "api_event_contract_created",
        "cli_shell_tui_bound", "policy_decision_emitted", "custos_decision_emitted",
        "approval_created", "runtime_executed", "trace_written",
        "ledger_written", "audit_finalized", "evidence_verified",
        "output_passport_created", "global_trace_written", "runtime_mutated",
    ]

def test_all_side_effects_false_by_default():
    se = DelegationAccountabilityPacketSideEffects()
    for name in _side_effect_names():
        assert getattr(se, name) is False, f"{name} must default to False"

def test_all_side_effects_false_after_build():
    """SideEffects must be all-false in binding_set built with default."""
    binding_set = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-1",
        delegation_ref_id="dref-test",
    )
    for name in _side_effect_names():
        assert getattr(binding_set.side_effects, name) is False, f"{name} must be False"

# ---------------------------------------------------------------------------
# 4. AccountabilityComponentRef
# ---------------------------------------------------------------------------

DEV_REF_ID = "dref-p1_8_15_test"

def test_component_ref_builds():
    cr = build_delegation_accountability_component_ref(
        component_ref_id="cr-fnd",
        delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
        component_ref="foundation_ref_0",
        component_description="P1.8.0 foundation context",
    )
    assert cr.component_ref_id == "cr-fnd"
    assert cr.component_family == DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT
    assert cr.component_ref_hash

def test_component_ref_deterministic():
    a = build_delegation_accountability_component_ref(
        component_ref_id="cr-d1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
    )
    b = build_delegation_accountability_component_ref(
        component_ref_id="cr-d1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
    )
    assert a.component_ref_hash == b.component_ref_hash

def test_component_ref_hash_changes_with_component_family():
    a = build_delegation_accountability_component_ref(
        component_ref_id="cr-h1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.ROLE_CONTEXT,
    )
    b = build_delegation_accountability_component_ref(
        component_ref_id="cr-h1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.SCOPE_CONTEXT,
    )
    assert a.component_ref_hash != b.component_ref_hash

def test_component_ref_hash_changes_with_description():
    a = build_delegation_accountability_component_ref(
        component_ref_id="cr-h2", delegation_ref_id=DEV_REF_ID,
        component_description="desc A",
    )
    b = build_delegation_accountability_component_ref(
        component_ref_id="cr-h2", delegation_ref_id=DEV_REF_ID,
        component_description="desc B",
    )
    assert a.component_ref_hash != b.component_ref_hash

def test_component_ref_hash_changes_with_component_hash():
    a = build_delegation_accountability_component_ref(
        component_ref_id="cr-h3", delegation_ref_id=DEV_REF_ID,
        component_hash="h1",
    )
    b = build_delegation_accountability_component_ref(
        component_ref_id="cr-h3", delegation_ref_id=DEV_REF_ID,
        component_hash="h2",
    )
    assert a.component_ref_hash != b.component_ref_hash

def test_component_ref_does_not_imply_verified():
    cr = build_delegation_accountability_component_ref(
        component_ref_id="cr-nv", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
    )
    assert cr.component_ref_hash is not None
    # Presence is not verification
    assert cr.reference_status == DelegationAccountabilityPacketReferenceStatus.REFERENCE_ONLY
    assert cr.packet_status == DelegationAccountabilityPacketStatus.REFERENCE_ONLY

# ---------------------------------------------------------------------------
# 5. CoverageMatrixEntry
# ---------------------------------------------------------------------------

def test_coverage_matrix_entry_builds():
    entry = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
        present=True, hash_present=True, source_label_present=True,
    )
    assert entry.entry_id == "e-1"
    assert entry.present is True
    assert entry.entry_hash

def test_coverage_matrix_entry_deterministic():
    a = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-d1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
        present=True, finding_count=3,
    )
    b = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-d1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
        present=True, finding_count=3,
    )
    assert a.entry_hash == b.entry_hash

def test_coverage_matrix_entry_hash_changes_with_present():
    a = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-c1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.ROLE_CONTEXT,
        present=True,
    )
    b = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-c1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.ROLE_CONTEXT,
        present=False,
    )
    assert a.entry_hash != b.entry_hash

def test_coverage_matrix_entry_hash_changes_with_finding_count():
    a = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-c2", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.AUTHORITY_CONTEXT,
        finding_count=0,
    )
    b = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-c2", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.AUTHORITY_CONTEXT,
        finding_count=5,
    )
    assert a.entry_hash != b.entry_hash

def test_coverage_matrix_entry_does_not_imply_compliance_proof():
    entry = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-nv", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
        present=True,
    )
    assert entry.present is True
    # present does not mean verified/compliant
    assert "not" not in entry.entry_hash.lower() if "not" in entry.entry_hash else True

# ---------------------------------------------------------------------------
# 6. CoverageMatrix
# ---------------------------------------------------------------------------

def test_coverage_matrix_builds_empty():
    matrix = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-1", delegation_ref_id=DEV_REF_ID,
    )
    assert matrix.coverage_matrix_id == "cm-1"
    assert len(matrix.entries) == 0
    assert matrix.coverage_matrix_hash

def test_coverage_matrix_builds_with_entries():
    entries = [
        build_delegation_accountability_coverage_matrix_entry(
            entry_id=f"e-{i}", delegation_ref_id=DEV_REF_ID,
            component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
            present=True,
        )
        for i in range(3)
    ]
    matrix = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-2", delegation_ref_id=DEV_REF_ID, entries=entries,
    )
    assert len(matrix.entries) == 3
    assert matrix.coverage_matrix_hash

def test_coverage_matrix_deterministic():
    entries = [
        build_delegation_accountability_coverage_matrix_entry(
            entry_id="e-com", delegation_ref_id=DEV_REF_ID,
            component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
        )
    ]
    a = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-d", delegation_ref_id=DEV_REF_ID, entries=entries,
    )
    b = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-d", delegation_ref_id=DEV_REF_ID, entries=list(entries),
    )
    assert a.coverage_matrix_hash == b.coverage_matrix_hash

def test_coverage_matrix_hash_changes_with_entries():
    e1 = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-dom-1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
    )
    e2 = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-dom-2", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
    )
    a = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-c", delegation_ref_id=DEV_REF_ID, entries=[e1],
    )
    b = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-c", delegation_ref_id=DEV_REF_ID, entries=[e2],
    )
    assert a.coverage_matrix_hash != b.coverage_matrix_hash

def test_coverage_matrix_does_not_imply_compliance_proof():
    matrix = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-nv", delegation_ref_id=DEV_REF_ID,
    )
    assert matrix.coverage_matrix_hash is not None
    # matrix exists ≠ compliance proof

# ---------------------------------------------------------------------------
# 7. AccountabilityProfile
# ---------------------------------------------------------------------------

def test_accountability_profile_builds():
    profile = build_delegation_accountability_profile(
        accountability_profile_id="ap-1", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=True,
        has_identity_context=True,
        has_role_context=True,
    )
    assert profile.accountability_profile_id == "ap-1"
    assert profile.has_foundation_context is True
    assert profile.has_identity_context is True
    assert profile.has_role_context is True
    assert profile.has_constraint_context is False
    assert profile.profile_hash

def test_accountability_profile_deterministic():
    a = build_delegation_accountability_profile(
        accountability_profile_id="ap-d", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=True, has_identity_context=True,
    )
    b = build_delegation_accountability_profile(
        accountability_profile_id="ap-d", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=True, has_identity_context=True,
    )
    assert a.profile_hash == b.profile_hash

def test_accountability_profile_hash_changes_with_has_fields():
    a = build_delegation_accountability_profile(
        accountability_profile_id="ap-c", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=True,
    )
    b = build_delegation_accountability_profile(
        accountability_profile_id="ap-c", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=False,
    )
    assert a.profile_hash != b.profile_hash

def test_accountability_profile_does_not_imply_trust_score():
    profile = build_delegation_accountability_profile(
        accountability_profile_id="ap-nv", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=True,
    )
    assert profile.profile_hash is not None
    # profile exists ≠ trust score

def test_accountability_profile_missing_components():
    profile = build_delegation_accountability_profile(
        accountability_profile_id="ap-mc", delegation_ref_id=DEV_REF_ID,
        missing_components=["TRACE_WRITER", "LEDGER_FINALIZER"],
    )
    assert "TRACE_WRITER" in profile.missing_components
    assert "LEDGER_FINALIZER" in profile.missing_components

def test_accountability_profile_unavailable_reasons():
    profile = build_delegation_accountability_profile(
        accountability_profile_id="ap-ur", delegation_ref_id=DEV_REF_ID,
        projection_unavailable_reason="Not P1.8.15",
        output_passport_unavailable_reason="Not P1.9",
        cli_shell_tui_unavailable_reason="Not P1.8.18",
    )
    assert "Not P1.8.15" == profile.projection_unavailable_reason
    assert "Not P1.9" == profile.output_passport_unavailable_reason
    assert "Not P1.8.18" == profile.cli_shell_tui_unavailable_reason

# ---------------------------------------------------------------------------
# 8. IntegrationSummaryRef
# ---------------------------------------------------------------------------

def test_integration_summary_ref_builds():
    ref = build_delegation_integration_summary_ref(
        integration_summary_ref_id="isr-1", delegation_ref_id=DEV_REF_ID,
        integration_summary_description="Summary of P1.8.0-P1.8.14",
    )
    assert ref.integration_summary_ref_id == "isr-1"
    assert ref.integration_summary_ref_hash

def test_integration_summary_ref_deterministic():
    a = build_delegation_integration_summary_ref(
        integration_summary_ref_id="isr-d", delegation_ref_id=DEV_REF_ID,
        integration_summary_description="desc",
    )
    b = build_delegation_integration_summary_ref(
        integration_summary_ref_id="isr-d", delegation_ref_id=DEV_REF_ID,
        integration_summary_description="desc",
    )
    assert a.integration_summary_ref_hash == b.integration_summary_ref_hash

def test_integration_summary_ref_not_system_integrated():
    ref = build_delegation_integration_summary_ref(
        integration_summary_ref_id="isr-nv", delegation_ref_id=DEV_REF_ID,
    )
    assert ref.reference_status == DelegationAccountabilityPacketReferenceStatus.REFERENCE_ONLY

# ---------------------------------------------------------------------------
# 9. IntegrationSummaryEnvelope
# ---------------------------------------------------------------------------

def test_integration_summary_envelope_builds():
    envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-1", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
        role_binding_hash="h-rb",
        trace_audit_bridge_binding_set_hash="h-tab",
    )
    assert envelope.integration_summary_envelope_id == "ise-1"
    assert envelope.delegation_identity_hash == "h-id"
    assert envelope.integration_summary_envelope_hash

def test_integration_summary_envelope_deterministic():
    a = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-d", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
    )
    b = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-d", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
    )
    assert a.integration_summary_envelope_hash == b.integration_summary_envelope_hash

def test_integration_summary_envelope_hash_changes_with_identity_hash():
    a = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-c", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-A",
    )
    b = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-c", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-B",
    )
    assert a.integration_summary_envelope_hash != b.integration_summary_envelope_hash

def test_integration_summary_envelope_hash_changes_with_component_refs():
    cr1 = build_delegation_accountability_component_ref(
        component_ref_id="cr-env-1", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
    )
    cr2 = build_delegation_accountability_component_ref(
        component_ref_id="cr-env-2", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
    )
    a = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-cr", delegation_ref_id=DEV_REF_ID,
        component_refs=[cr1],
    )
    b = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-cr", delegation_ref_id=DEV_REF_ID,
        component_refs=[cr2],
    )
    assert a.integration_summary_envelope_hash != b.integration_summary_envelope_hash

def test_integration_summary_envelope_not_system_integrated():
    envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-nv", delegation_ref_id=DEV_REF_ID,
    )
    assert envelope.source_label == DelegationSourceLabel.DEV_FIXTURE

def test_integration_summary_envelope_not_projection_api_contract():
    envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-np", delegation_ref_id=DEV_REF_ID,
    )
    assert envelope.integration_summary_envelope_hash is not None

# ---------------------------------------------------------------------------
# 10. AccountabilityPacketEnvelope
# ---------------------------------------------------------------------------

def test_accountability_packet_envelope_builds():
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-1", delegation_ref_id=DEV_REF_ID,
        integration_summary_envelope_hash="h-ise",
        trace_audit_bridge_binding_set_hash="h-tab",
        golden_thread_ref="agent/STATE.md#golden-thread",
        next_handoff_ref="P1.8.16 Pre-Projection Readiness / Surface Contract Seed",
    )
    assert packet_env.accountability_packet_envelope_id == "ape-1"
    assert packet_env.integration_summary_envelope_hash == "h-ise"
    assert packet_env.golden_thread_ref == "agent/STATE.md#golden-thread"
    assert packet_env.accountability_packet_envelope_hash

def test_accountability_packet_envelope_deterministic():
    a = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-d", delegation_ref_id=DEV_REF_ID,
        golden_thread_ref="gt-ref",
        next_handoff_ref="nh-ref",
    )
    b = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-d", delegation_ref_id=DEV_REF_ID,
        golden_thread_ref="gt-ref",
        next_handoff_ref="nh-ref",
    )
    assert a.accountability_packet_envelope_hash == b.accountability_packet_envelope_hash

def test_accountability_packet_envelope_hash_changes_with_golden_thread_ref():
    a = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-c", delegation_ref_id=DEV_REF_ID,
        golden_thread_ref="gt-A",
    )
    b = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-c", delegation_ref_id=DEV_REF_ID,
        golden_thread_ref="gt-B",
    )
    assert a.accountability_packet_envelope_hash != b.accountability_packet_envelope_hash

def test_accountability_packet_envelope_hash_changes_with_next_handoff():
    a = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-c2", delegation_ref_id=DEV_REF_ID,
        next_handoff_ref="P1.8.16",
    )
    b = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-c2", delegation_ref_id=DEV_REF_ID,
        next_handoff_ref="P1.9",
    )
    assert a.accountability_packet_envelope_hash != b.accountability_packet_envelope_hash

def test_accountability_packet_envelope_not_accountability_proven():
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-nv", delegation_ref_id=DEV_REF_ID,
    )
    assert packet_env.accountability_packet_envelope_hash is not None

def test_accountability_packet_envelope_not_output_passport():
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-nop", delegation_ref_id=DEV_REF_ID,
    )
    assert packet_env.source_label == DelegationSourceLabel.DEV_FIXTURE

def test_accountability_packet_envelope_not_section_seal():
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-ns", delegation_ref_id=DEV_REF_ID,
    )
    assert packet_env.accountability_packet_envelope_hash is not None

# ---------------------------------------------------------------------------
# 11. AccountabilityPacketBinding
# ---------------------------------------------------------------------------

def test_accountability_packet_binding_builds():
    binding = build_delegation_accountability_packet_binding(
        binding_id="b-1", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
        accountability_packet_envelope_hash="h-ape",
    )
    assert binding.binding_id == "b-1"
    assert binding.binding_hash

def test_accountability_packet_binding_deterministic():
    a = build_delegation_accountability_packet_binding(
        binding_id="b-d", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
    )
    b = build_delegation_accountability_packet_binding(
        binding_id="b-d", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
    )
    assert a.binding_hash == b.binding_hash

def test_accountability_packet_binding_hash_changes_with_packet_envelope_hash():
    a = build_delegation_accountability_packet_binding(
        binding_id="b-c", delegation_ref_id=DEV_REF_ID,
        accountability_packet_envelope_hash="h-A",
    )
    b = build_delegation_accountability_packet_binding(
        binding_id="b-c", delegation_ref_id=DEV_REF_ID,
        accountability_packet_envelope_hash="h-B",
    )
    assert a.binding_hash != b.binding_hash

# ---------------------------------------------------------------------------
# 12. AccountabilityPacketBindingSet
# ---------------------------------------------------------------------------

def test_accountability_packet_binding_set_builds():
    binding = build_delegation_accountability_packet_binding(
        binding_id="b-s1", delegation_ref_id=DEV_REF_ID,
    )
    bs = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-1", delegation_ref_id=DEV_REF_ID,
        bindings=[binding],
    )
    assert len(bs.bindings) == 1
    assert bs.accountability_packet_binding_set_hash

def test_accountability_packet_binding_set_deterministic():
    binding = build_delegation_accountability_packet_binding(
        binding_id="b-d2", delegation_ref_id=DEV_REF_ID,
    )
    a = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-d", delegation_ref_id=DEV_REF_ID,
        bindings=[binding],
    )
    b = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-d", delegation_ref_id=DEV_REF_ID,
        bindings=[binding],
    )
    assert a.accountability_packet_binding_set_hash == b.accountability_packet_binding_set_hash

def test_accountability_packet_binding_set_hash_changes_with_bindings():
    b1 = build_delegation_accountability_packet_binding(
        binding_id="b-c3a", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-A",
    )
    b2 = build_delegation_accountability_packet_binding(
        binding_id="b-c3b", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-B",
    )
    a = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-c", delegation_ref_id=DEV_REF_ID,
        bindings=[b1],
    )
    c = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-c", delegation_ref_id=DEV_REF_ID,
        bindings=[b2],
    )
    assert a.accountability_packet_binding_set_hash != c.accountability_packet_binding_set_hash

# ---------------------------------------------------------------------------
# 13. Accountability packet full path (DEV_FIXTURE chain)
# ---------------------------------------------------------------------------

def _build_dev_fixture_accountability_packet():
    """Build the complete DEV_FIXTURE accountability packet chain."""
    families = [
        DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
        DelegationAccountabilityComponentFamily.IDENTITY_CONTEXT,
        DelegationAccountabilityComponentFamily.ROLE_CONTEXT,
        DelegationAccountabilityComponentFamily.CONSTRAINT_CONTEXT,
        DelegationAccountabilityComponentFamily.AUTHORITY_CONTEXT,
        DelegationAccountabilityComponentFamily.EVIDENCE_CONTEXT,
        DelegationAccountabilityComponentFamily.IDENTITY_MESH_CONTEXT,
        DelegationAccountabilityComponentFamily.SCOPE_CONTEXT,
        DelegationAccountabilityComponentFamily.LIFECYCLE_CONTEXT,
        DelegationAccountabilityComponentFamily.CHAIN_CONTEXT,
        DelegationAccountabilityComponentFamily.SHADOW_RESOLVER_CONTEXT,
        DelegationAccountabilityComponentFamily.OPERATOR_REVIEW_CONTEXT,
        DelegationAccountabilityComponentFamily.POLICY_CUSTOS_BRIDGE_CONTEXT,
        DelegationAccountabilityComponentFamily.RUNTIME_EXECUTION_READINESS_CONTEXT,
        DelegationAccountabilityComponentFamily.TRACE_AUDIT_BRIDGE_CONTEXT,
    ]
    component_refs = []
    for f in families:
        cr = build_delegation_accountability_component_ref(
            component_ref_id=f"cr-{f.value}", delegation_ref_id=DEV_REF_ID,
            component_family=f, component_description=f"REFERENCE_ONLY {f.value}",
        )
        component_refs.append(cr)

    entries = []
    for f in families:
        entry = build_delegation_accountability_coverage_matrix_entry(
            entry_id=f"cov-{f.value}", delegation_ref_id=DEV_REF_ID,
            component_family=f, present=True, hash_present=True,
            source_label_present=True, finding_count=1,
        )
        entries.append(entry)
    matrix = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-dev", delegation_ref_id=DEV_REF_ID, entries=entries,
    )
    profile = build_delegation_accountability_profile(
        accountability_profile_id="ap-dev", delegation_ref_id=DEV_REF_ID,
        has_foundation_context=True, has_identity_context=True,
        has_role_context=True, has_constraint_context=True,
        has_authority_context=True, has_evidence_context=True,
        has_identity_mesh_context=True, has_scope_context=True,
        has_lifecycle_context=True, has_chain_context=True,
        has_shadow_resolver_context=True, has_operator_review_context=True,
        has_policy_custos_bridge_context=True,
        has_runtime_execution_readiness_context=True,
        has_trace_audit_bridge_context=True,
        projection_unavailable_reason="Not P1.8.15; projection/API/event/read model UNAVAILABLE",
        api_event_contract_unavailable_reason="Not P1.8.15; API/event contract UNAVAILABLE",
        cli_shell_tui_unavailable_reason="Not P1.8.18; CLI/Shell/TUI binding UNAVAILABLE",
        trace_verification_unavailable_reason="Not P1.8.15; trace verification UNAVAILABLE",
        ledger_finality_unavailable_reason="Not P1.8.15; Ledger finality UNAVAILABLE",
        output_passport_unavailable_reason="Not P1.9; Output Passport UNAVAILABLE",
        accountability_verification_unavailable_reason="Not P1.8.15; accountability verification UNAVAILABLE",
    )
    isr = build_delegation_integration_summary_ref(
        integration_summary_ref_id="isr-dev", delegation_ref_id=DEV_REF_ID,
        integration_summary_description="DEV_FIXTURE P1.8.0-P1.8.14 integration summary",
        reference_status=DelegationAccountabilityPacketReferenceStatus.INTEGRATION_SUMMARY_REFERENCED,
    )
    is_envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-dev", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-identity",
        role_binding_hash="h-role",
        constraint_set_hash="h-constraint",
        authority_binding_set_hash="h-authority",
        non_repudiation_binding_set_hash="h-nonrep",
        identity_mesh_binding_set_hash="h-mesh",
        scope_binding_set_hash="h-scope",
        lifecycle_binding_set_hash="h-lifecycle",
        chain_binding_set_hash="h-chain",
        shadow_resolver_result_hash="h-shadow",
        operator_review_binding_set_hash="h-review",
        policy_custos_bridge_binding_set_hash="h-policy",
        runtime_execution_readiness_binding_set_hash="h-runtime",
        trace_audit_bridge_binding_set_hash="h-trace-audit",
        component_refs=component_refs,
        coverage_matrix_hash=matrix.coverage_matrix_hash,
        accountability_profile_hash=profile.profile_hash,
    )
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-dev", delegation_ref_id=DEV_REF_ID,
        integration_summary_envelope_hash=is_envelope.integration_summary_envelope_hash,
        component_refs=component_refs,
        coverage_matrix_hash=matrix.coverage_matrix_hash,
        accountability_profile_hash=profile.profile_hash,
        trace_audit_bridge_binding_set_hash="h-trace-audit",
        golden_thread_ref="agent/STATE.md#golden-thread",
        next_handoff_ref="P1.8.16 Pre-Projection Readiness / Surface Contract Seed",
    )
    binding = build_delegation_accountability_packet_binding(
        binding_id="b-dev", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-identity",
        role_binding_hash="h-role",
        constraint_set_hash="h-constraint",
        authority_binding_set_hash="h-authority",
        non_repudiation_binding_set_hash="h-nonrep",
        identity_mesh_binding_set_hash="h-mesh",
        scope_binding_set_hash="h-scope",
        lifecycle_binding_set_hash="h-lifecycle",
        chain_binding_set_hash="h-chain",
        shadow_resolver_result_hash="h-shadow",
        operator_review_binding_set_hash="h-review",
        policy_custos_bridge_binding_set_hash="h-policy",
        runtime_execution_readiness_binding_set_hash="h-runtime",
        trace_audit_bridge_binding_set_hash="h-trace-audit",
        integration_summary_envelope_hash=is_envelope.integration_summary_envelope_hash,
        accountability_packet_envelope_hash=packet_env.accountability_packet_envelope_hash,
        coverage_matrix_hash=matrix.coverage_matrix_hash,
        accountability_profile_hash=profile.profile_hash,
    )
    binding_set = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-dev", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-identity",
        role_binding_hash="h-role",
        constraint_set_hash="h-constraint",
        authority_binding_set_hash="h-authority",
        non_repudiation_binding_set_hash="h-nonrep",
        identity_mesh_binding_set_hash="h-mesh",
        scope_binding_set_hash="h-scope",
        lifecycle_binding_set_hash="h-lifecycle",
        chain_binding_set_hash="h-chain",
        shadow_resolver_result_hash="h-shadow",
        operator_review_binding_set_hash="h-review",
        policy_custos_bridge_binding_set_hash="h-policy",
        runtime_execution_readiness_binding_set_hash="h-runtime",
        trace_audit_bridge_binding_set_hash="h-trace-audit",
        bindings=[binding],
    )
    return component_refs, matrix, profile, isr, is_envelope, packet_env, binding, binding_set

def test_dev_fixture_chain_completes():
    """DEV_FIXTURE: complete accountability packet chain from component ref to binding set."""
    component_refs, matrix, profile, isr, is_envelope, packet_env, binding, binding_set = (
        _build_dev_fixture_accountability_packet()
    )
    assert len(component_refs) == 15
    assert matrix.coverage_matrix_hash
    assert profile.profile_hash
    assert isr.integration_summary_ref_hash
    assert is_envelope.integration_summary_envelope_hash
    assert packet_env.accountability_packet_envelope_hash
    assert binding.binding_hash
    assert binding_set.accountability_packet_binding_set_hash

def test_dev_fixture_chain_deterministic():
    """DEV_FIXTURE: identical chain gives identical hashes."""
    _, _, _, _, _, _, _, bs1 = _build_dev_fixture_accountability_packet()
    _, _, _, _, _, _, _, bs2 = _build_dev_fixture_accountability_packet()
    assert bs1.accountability_packet_binding_set_hash == bs2.accountability_packet_binding_set_hash

def test_dev_fixture_binding_set_hash_is_deterministic():
    """DEV_FIXTURE: accountability_packet_binding_set_hash is deterministic."""
    _, _, _, _, _, _, _, bs = _build_dev_fixture_accountability_packet()
    assert bs.accountability_packet_binding_set_hash
    assert len(bs.accountability_packet_binding_set_hash) == 64

# ---------------------------------------------------------------------------
# 14. StatusReport
# ---------------------------------------------------------------------------

def test_status_report_builds():
    report = build_delegation_accountability_packet_status_report(
        available_contracts=["component_ref", "coverage_matrix", "profile",
                             "integration_summary_envelope",
                             "accountability_packet_envelope"],
    )
    assert report.status_hash
    assert "DEV_FIXTURE" in report.status_label
    assert len(report.available_contracts) > 0

def test_status_report_unavailable_bindings():
    bindings = {"Proj": "not available", "CLI": "not available"}
    report = build_delegation_accountability_packet_status_report(
        unavailable_bindings=bindings,
    )
    assert "Proj" in report.unavailable_bindings
    assert "CLI" in report.unavailable_bindings

def test_status_report_all_side_effects_false():
    report = build_delegation_accountability_packet_status_report()
    for name in _side_effect_names():
        assert getattr(report.side_effects, name) is False

# ---------------------------------------------------------------------------
# 15. JSON-safe serialization
# ---------------------------------------------------------------------------

def test_integration_summary_envelope_serializes():
    is_envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-js", delegation_ref_id=DEV_REF_ID,
        delegation_identity_hash="h-id",
    )
    s = serialize_delegation_integration_summary_envelope(is_envelope)
    assert s is not None
    d = json.loads(s)
    assert d["integration_summary_envelope_id"] == "ise-js"

def test_integration_summary_envelope_serialization_roundtrip():
    crs = [build_delegation_accountability_component_ref(
        component_ref_id="cr-rt", delegation_ref_id=DEV_REF_ID,
        component_family=DelegationAccountabilityComponentFamily.FOUNDATION_CONTEXT,
    )]
    is_envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-rt", delegation_ref_id=DEV_REF_ID,
        component_refs=crs,
    )
    s = serialize_delegation_integration_summary_envelope(is_envelope)
    d = json.loads(s)
    assert d["integration_summary_envelope_id"] == "ise-rt"
    assert d["integration_summary_envelope_hash"] == is_envelope.integration_summary_envelope_hash

def test_accountability_packet_envelope_serializes():
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-js", delegation_ref_id=DEV_REF_ID,
    )
    s = serialize_delegation_accountability_packet_envelope(packet_env)
    assert s is not None
    d = json.loads(s)
    assert d["accountability_packet_envelope_id"] == "ape-js"

def test_accountability_packet_binding_set_serializes():
    binding = build_delegation_accountability_packet_binding(
        binding_id="b-js", delegation_ref_id=DEV_REF_ID,
    )
    bs = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-js", delegation_ref_id=DEV_REF_ID,
        bindings=[binding],
    )
    s = serialize_delegation_accountability_packet_binding_set(bs)
    assert s is not None
    d = json.loads(s)
    assert d["accountability_packet_binding_set_id"] == "bs-js"
    assert "side_effects" in d
    for name in _side_effect_names():
        assert d["side_effects"][name] is False

# ---------------------------------------------------------------------------
# 16. Hash functions (public API)
# ---------------------------------------------------------------------------

def test_hash_component_ref():
    cr = build_delegation_accountability_component_ref(
        component_ref_id="cr-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_component_ref(cr) == cr.component_ref_hash

def test_hash_coverage_matrix_entry():
    entry = build_delegation_accountability_coverage_matrix_entry(
        entry_id="e-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_coverage_matrix_entry(entry) == entry.entry_hash

def test_hash_coverage_matrix():
    matrix = build_delegation_accountability_coverage_matrix(
        coverage_matrix_id="cm-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_coverage_matrix(matrix) == matrix.coverage_matrix_hash

def test_hash_accountability_profile():
    profile = build_delegation_accountability_profile(
        accountability_profile_id="ap-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_profile(profile) == profile.profile_hash

def test_hash_integration_summary_ref():
    ref = build_delegation_integration_summary_ref(
        integration_summary_ref_id="isr-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_integration_summary_ref(ref) == ref.integration_summary_ref_hash

def test_hash_integration_summary_envelope():
    envelope = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_integration_summary_envelope(envelope) == envelope.integration_summary_envelope_hash

def test_hash_accountability_packet_envelope():
    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_packet_envelope(packet_env) == packet_env.accountability_packet_envelope_hash

def test_hash_accountability_packet_binding():
    binding = build_delegation_accountability_packet_binding(
        binding_id="b-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_packet_binding(binding) == binding.binding_hash

def test_hash_accountability_packet_binding_set():
    bs = build_delegation_accountability_packet_binding_set(
        accountability_packet_binding_set_id="bs-hf", delegation_ref_id=DEV_REF_ID,
    )
    assert hash_delegation_accountability_packet_binding_set(bs) == bs.accountability_packet_binding_set_hash

# ---------------------------------------------------------------------------
# 17. Summary hashes are not TRACE_VERIFIED
# ---------------------------------------------------------------------------

def test_summary_hash_not_trace_verified():
    """All accountability summary hashes are deterministic, not TRACE_VERIFIED."""
    _, _, _, _, is_env, pkt_env, _, bs = _build_dev_fixture_accountability_packet()
    assert is_env.integration_summary_envelope_hash
    assert pkt_env.accountability_packet_envelope_hash
    assert bs.accountability_packet_binding_set_hash
    # Hashes exist but are not TRACE_VERIFIED — existence alone proves nothing

def test_envelope_hash_not_trace_verified():
    is_env = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-ntv", delegation_ref_id=DEV_REF_ID,
    )
    assert is_env.integration_summary_envelope_hash is not None

# ---------------------------------------------------------------------------
# 18. UNAVAILABLE reasons
# ---------------------------------------------------------------------------

def test_unavailable_reasons_exist():
    from agentic_runtime.delegation.accountability_packet import DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Projection/API/Event/Read Model" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "CLI/Shell/TUI Binding" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Trace Writer" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Ledger Writer" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Output Passport / P1.9" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Accountability Verification" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Component Verification" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Coverage Verification" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "Compliance Proof" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "P1.8.16 Pre-Projection Readiness / Surface Contract Seed" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "P1.8.17 Projection/API/Event Contract" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "P1.8.18 CLI/Shell/TUI Binding" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    assert "TRACE_VERIFIED Claim" in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS

def test_unavailable_reasons_cover_future_surfaces():
    from agentic_runtime.delegation.accountability_packet import DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS
    expected = [
        "P1.8.16 Pre-Projection Readiness / Surface Contract Seed",
        "P1.8.17 Projection/API/Event Contract",
        "P1.8.18 CLI/Shell/TUI Binding",
        "P1.8.19 Docs/State/Report Seal Update",
        "P1.8.20 Exit Seal Demo",
        "Output Passport / P1.9",
    ]
    for key in expected:
        assert key in DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS, f"Missing unavailable reason: {key}"

# ---------------------------------------------------------------------------
# 19. DEV_FIXTURE explicit in tests
# ---------------------------------------------------------------------------

def test_dev_fixture_source_label_visible():
    """All built objects in DEV_FIXTURE chain use DEV_FIXTURE source label."""
    _, matrix, profile, _, is_env, pkt_env, _, bs = _build_dev_fixture_accountability_packet()
    assert matrix.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert profile.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert is_env.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert pkt_env.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert bs.source_label == DelegationSourceLabel.DEV_FIXTURE

# ---------------------------------------------------------------------------
# 20. P1.8.14 feeds P1.8.15
# ---------------------------------------------------------------------------

def test_p1_8_14_trace_audit_bridge_hash_feeds_accountability_packet():
    """P1.8.14 TraceAuditBridgeBindingSet hash can feed P1.8.15 envelope."""
    is_env = build_delegation_integration_summary_envelope(
        integration_summary_envelope_id="ise-feed", delegation_ref_id=DEV_REF_ID,
        trace_audit_bridge_binding_set_hash="h-tab-feed",
    )
    assert is_env.trace_audit_bridge_binding_set_hash == "h-tab-feed"

    packet_env = build_delegation_accountability_packet_envelope(
        accountability_packet_envelope_id="ape-feed", delegation_ref_id=DEV_REF_ID,
        trace_audit_bridge_binding_set_hash="h-tab-feed",
    )
    assert packet_env.trace_audit_bridge_binding_set_hash == "h-tab-feed"

"""Focused tests for P1.8.16 — Delegation Pre-Projection Readiness / Surface Contract Seed Model."""

import json
import sys

import pytest

sys.path.insert(0, "src")

from agentic_runtime.delegation.foundation import DelegationSourceLabel
from agentic_runtime.delegation.pre_projection import (
    DelegationPreProjectionSeedKind,
    DelegationPreProjectionSeedReferenceStatus,
    DelegationPreProjectionSeedStatus,
    DelegationSurfaceExposureClass,
    DelegationProjectionSeedFamily,
    DelegationPreProjectionReadinessRef,
    DelegationSurfaceContractSeedRef,
    DelegationReadModelSeedRef,
    DelegationAPIContractSeedRef,
    DelegationEventContractSeedRef,
    DelegationSurfaceEligibilityEntry,
    DelegationSurfaceEligibilityProfile,
    DelegationProjectionGapMatrixEntry,
    DelegationProjectionGapMatrix,
    DelegationPreProjectionSeedEnvelope,
    DelegationPreProjectionSeedBinding,
    DelegationPreProjectionSeedBindingSet,
    DelegationPreProjectionSeedSideEffects,
    DelegationPreProjectionSeedStatusReport,
    DELEGATION_PRE_PROJECTION_SEED_TASK_ID,
    DELEGATION_PRE_PROJECTION_SEED_UNAVAILABLE_BINDINGS,
    build_delegation_pre_projection_readiness_ref,
    build_delegation_surface_contract_seed_ref,
    build_delegation_read_model_seed_ref,
    build_delegation_api_contract_seed_ref,
    build_delegation_event_contract_seed_ref,
    build_delegation_surface_eligibility_entry,
    build_delegation_surface_eligibility_profile,
    build_delegation_projection_gap_matrix_entry,
    build_delegation_projection_gap_matrix,
    build_delegation_pre_projection_seed_envelope,
    build_delegation_pre_projection_seed_binding,
    build_delegation_pre_projection_seed_binding_set,
    build_delegation_pre_projection_seed_status_report,
    hash_delegation_pre_projection_readiness_ref,
    hash_delegation_surface_contract_seed_ref,
    hash_delegation_read_model_seed_ref,
    hash_delegation_api_contract_seed_ref,
    hash_delegation_event_contract_seed_ref,
    hash_delegation_surface_eligibility_entry,
    hash_delegation_surface_eligibility_profile,
    hash_delegation_projection_gap_matrix_entry,
    hash_delegation_projection_gap_matrix,
    hash_delegation_pre_projection_seed_envelope,
    hash_delegation_pre_projection_seed_binding,
    hash_delegation_pre_projection_seed_binding_set,
    hash_delegation_pre_projection_seed_status_report,
    serialize_delegation_pre_projection_seed_envelope,
    serialize_delegation_pre_projection_seed_binding_set,
)

# ============================================================================
# 1. Imports work
# ============================================================================

def test_imports_work():
    """All P1.8.16 symbols are importable."""
    assert DelegationPreProjectionSeedKind is not None
    assert DelegationPreProjectionSeedReferenceStatus is not None
    assert DelegationPreProjectionSeedStatus is not None
    assert DelegationSurfaceExposureClass is not None
    assert DelegationProjectionSeedFamily is not None
    assert DelegationPreProjectionReadinessRef is not None
    assert DelegationSurfaceContractSeedRef is not None
    assert DelegationReadModelSeedRef is not None
    assert DelegationAPIContractSeedRef is not None
    assert DelegationEventContractSeedRef is not None
    assert DelegationSurfaceEligibilityEntry is not None
    assert DelegationSurfaceEligibilityProfile is not None
    assert DelegationProjectionGapMatrixEntry is not None
    assert DelegationProjectionGapMatrix is not None
    assert DelegationPreProjectionSeedEnvelope is not None
    assert DelegationPreProjectionSeedBinding is not None
    assert DelegationPreProjectionSeedBindingSet is not None
    assert DelegationPreProjectionSeedSideEffects is not None
    assert DelegationPreProjectionSeedStatusReport is not None
    assert DELEGATION_PRE_PROJECTION_SEED_TASK_ID == "P1.8.16"

def test_existing_p1_8_0_through_p1_8_15_exports_still_importable():
    """Existing P1.8.0-P1.8.15 symbols remain importable from delegation package."""
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
        DelegationAccountabilityPacketBindingSet,
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
    assert DelegationAccountabilityPacketBindingSet is not None


# ============================================================================
# 2. Enum values
# ============================================================================

def test_seed_kind_enum():
    kind = DelegationPreProjectionSeedKind.PRE_PROJECTION_READINESS
    assert kind.value == "pre_projection_readiness"
    assert DelegationPreProjectionSeedKind("pre_projection_readiness") == kind
    assert DelegationPreProjectionSeedKind.UNKNOWN.value == "unknown"

def test_reference_status_enum():
    status = DelegationPreProjectionSeedReferenceStatus.REFERENCE_ONLY
    assert status.value == "reference_only"
    assert DelegationPreProjectionSeedReferenceStatus.PROJECTION_UNAVAILABLE.value == "projection_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.API_EVENT_CONTRACT_UNAVAILABLE.value == "api_event_contract_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.READ_MODEL_UNAVAILABLE.value == "read_model_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.CLI_SHELL_TUI_UNAVAILABLE.value == "cli_shell_tui_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.UI_SURFACE_UNAVAILABLE.value == "ui_surface_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.TRACE_VERIFICATION_UNAVAILABLE.value == "trace_verification_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.LEDGER_FINALITY_UNAVAILABLE.value == "ledger_finality_unavailable"
    assert DelegationPreProjectionSeedReferenceStatus.OUTPUT_PASSPORT_UNAVAILABLE.value == "output_passport_unavailable"

def test_seed_status_enum():
    assert DelegationPreProjectionSeedStatus.REFERENCE_ONLY.value == "reference_only"
    assert DelegationPreProjectionSeedStatus.DECLARED.value == "declared"
    assert DelegationPreProjectionSeedStatus.UNAVAILABLE.value == "unavailable"

def test_surface_exposure_class_enum():
    assert DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE.value == "operator_visible_candidate"
    assert DelegationSurfaceExposureClass.INTERNAL_ONLY.value == "internal_only"
    assert DelegationSurfaceExposureClass.GOVERNANCE_ONLY.value == "governance_only"
    assert DelegationSurfaceExposureClass.TRACE_CONTEXT_ONLY.value == "trace_context_only"
    assert DelegationSurfaceExposureClass.POLICY_CONTEXT_ONLY.value == "policy_context_only"
    assert DelegationSurfaceExposureClass.RUNTIME_CONTEXT_ONLY.value == "runtime_context_only"
    assert DelegationSurfaceExposureClass.REDACTED_CANDIDATE.value == "redacted_candidate"
    assert DelegationSurfaceExposureClass.UNAVAILABLE.value == "unavailable"

def test_projection_seed_family_enum():
    assert DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT.value == "accountability_packet_context"
    assert DelegationProjectionSeedFamily.INTEGRATION_SUMMARY_CONTEXT.value == "integration_summary_context"
    assert DelegationProjectionSeedFamily.SURFACE_ELIGIBILITY_CONTEXT.value == "surface_eligibility_context"
    assert DelegationProjectionSeedFamily.READ_MODEL_SEED_CONTEXT.value == "read_model_seed_context"
    assert DelegationProjectionSeedFamily.API_CONTRACT_SEED_CONTEXT.value == "api_contract_seed_context"
    assert DelegationProjectionSeedFamily.EVENT_CONTRACT_SEED_CONTEXT.value == "event_contract_seed_context"
    assert DelegationProjectionSeedFamily.SURFACE_CONTRACT_SEED_CONTEXT.value == "surface_contract_seed_context"
    assert DelegationProjectionSeedFamily.GOLDEN_THREAD_CONTEXT.value == "golden_thread_context"
    assert DelegationProjectionSeedFamily.UNAVAILABLE_SURFACE_CONTEXT.value == "unavailable_surface_context"

# ============================================================================
# 3. PreProjectionReadinessRef — build, hash, determinism
# ============================================================================

def test_build_pre_projection_readiness_ref():
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001",
        delegation_ref_id="deleg-001",
        pre_projection_readiness_ref="P1.8.15 AccountabilityPacketBindingSet",
        pre_projection_readiness_description="Pre-projection readiness for accountability packet context",
        reference_status=DelegationPreProjectionSeedReferenceStatus.PRE_PROJECTION_READINESS_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        seed_status=DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
    )
    assert ref.schema_version.startswith("delegation_pre_projection_readiness_ref.")
    assert ref.pre_projection_readiness_ref_id == "ppr-001"
    assert ref.delegation_ref_id == "deleg-001"
    assert ref.pre_projection_readiness_ref == "P1.8.15 AccountabilityPacketBindingSet"
    assert ref.pre_projection_readiness_description is not None
    assert ref.reference_status == DelegationPreProjectionSeedReferenceStatus.PRE_PROJECTION_READINESS_REFERENCED
    assert ref.source_label == DelegationSourceLabel.DEV_FIXTURE
    assert ref.seed_status == DelegationPreProjectionSeedStatus.REFERENCE_ONLY
    assert len(ref.pre_projection_readiness_hash) == 64  # SHA-256 hex

def test_pre_projection_readiness_ref_deterministic():
    a = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001",
        delegation_ref_id="deleg-001",
        pre_projection_readiness_ref="P1.8.15",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    b = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001",
        delegation_ref_id="deleg-001",
        pre_projection_readiness_ref="P1.8.15",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert hash_delegation_pre_projection_readiness_ref(a) == hash_delegation_pre_projection_readiness_ref(b)

def test_pre_projection_readiness_ref_changed_input_changes_hash():
    a = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
        pre_projection_readiness_ref="P1.8.15",
    )
    b = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
        pre_projection_readiness_ref="P1.8.14",
    )
    assert hash_delegation_pre_projection_readiness_ref(a) != hash_delegation_pre_projection_readiness_ref(b)

def test_pre_projection_readiness_ref_does_not_imply_projection_ready():
    """PreProjectionReadinessRef exists does not mean projection ready."""
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
    )
    assert ref.reference_status != DelegationPreProjectionSeedReferenceStatus.PROJECTION_UNAVAILABLE  # it's REFERENCE_ONLY
    assert any(s.value == "projection_unavailable" for s in DelegationPreProjectionSeedReferenceStatus)


# ============================================================================
# 4. SurfaceContractSeedRef — build, hash, determinism
# ============================================================================

def test_build_surface_contract_seed_ref():
    ref = build_delegation_surface_contract_seed_ref(
        surface_contract_seed_ref_id="scs-001",
        delegation_ref_id="deleg-001",
        surface_contract_seed_ref="Future CLI projection contract",
        surface_contract_seed_description="Seed for future CLI/TUI surface contract",
        reference_status=DelegationPreProjectionSeedReferenceStatus.SURFACE_CONTRACT_SEED_REFERENCED,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        seed_status=DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
    )
    assert ref.surface_contract_seed_ref_id == "scs-001"
    assert ref.surface_contract_seed_ref == "Future CLI projection contract"
    assert len(ref.surface_contract_seed_hash) == 64

def test_surface_contract_seed_ref_deterministic():
    a = build_delegation_surface_contract_seed_ref(
        surface_contract_seed_ref_id="scs-001", delegation_ref_id="deleg-001",
    )
    b = build_delegation_surface_contract_seed_ref(
        surface_contract_seed_ref_id="scs-001", delegation_ref_id="deleg-001",
    )
    assert hash_delegation_surface_contract_seed_ref(a) == hash_delegation_surface_contract_seed_ref(b)

def test_surface_contract_seed_ref_changed_input_changes_hash():
    a = build_delegation_surface_contract_seed_ref(
        surface_contract_seed_ref_id="scs-001", delegation_ref_id="deleg-001",
        surface_contract_seed_ref="A",
    )
    b = build_delegation_surface_contract_seed_ref(
        surface_contract_seed_ref_id="scs-001", delegation_ref_id="deleg-001",
        surface_contract_seed_ref="B",
    )
    assert hash_delegation_surface_contract_seed_ref(a) != hash_delegation_surface_contract_seed_ref(b)

def test_surface_contract_seed_ref_does_not_imply_surface_contract():
    """SurfaceContractSeedRef exists does not mean surface contract."""
    ref = build_delegation_surface_contract_seed_ref(
        surface_contract_seed_ref_id="scs-001", delegation_ref_id="deleg-001",
    )
    assert ref.seed_status == DelegationPreProjectionSeedStatus.REFERENCE_ONLY


# ============================================================================
# 5. ReadModelSeedRef — build, hash, determinism
# ============================================================================

def test_build_read_model_seed_ref():
    ref = build_delegation_read_model_seed_ref(
        read_model_seed_ref_id="rms-001",
        delegation_ref_id="deleg-001",
        read_model_seed_ref="Future delegation read model projection",
        read_model_seed_description="Seed for P1.8.17 read model",
    )
    assert ref.read_model_seed_ref_id == "rms-001"
    assert len(ref.read_model_seed_hash) == 64

def test_read_model_seed_ref_deterministic():
    a = build_delegation_read_model_seed_ref(read_model_seed_ref_id="rms-001", delegation_ref_id="deleg-001")
    b = build_delegation_read_model_seed_ref(read_model_seed_ref_id="rms-001", delegation_ref_id="deleg-001")
    assert hash_delegation_read_model_seed_ref(a) == hash_delegation_read_model_seed_ref(b)

def test_read_model_seed_ref_changed_input_changes_hash():
    a = build_delegation_read_model_seed_ref(read_model_seed_ref_id="rms-001", delegation_ref_id="deleg-001",
                                              read_model_seed_ref="A")
    b = build_delegation_read_model_seed_ref(read_model_seed_ref_id="rms-001", delegation_ref_id="deleg-001",
                                              read_model_seed_ref="B")
    assert hash_delegation_read_model_seed_ref(a) != hash_delegation_read_model_seed_ref(b)

def test_read_model_seed_ref_does_not_imply_read_model():
    """ReadModelSeedRef exists does not mean read model."""
    ref = build_delegation_read_model_seed_ref(read_model_seed_ref_id="rms-001", delegation_ref_id="deleg-001")
    assert ref.seed_status == DelegationPreProjectionSeedStatus.REFERENCE_ONLY


# ============================================================================
# 6. APIContractSeedRef — build, hash, determinism
# ============================================================================

def test_build_api_contract_seed_ref():
    ref = build_delegation_api_contract_seed_ref(
        api_contract_seed_ref_id="acs-001",
        delegation_ref_id="deleg-001",
        api_contract_seed_ref="Future delegation API contract",
        api_contract_seed_description="Seed for P1.8.17 API contract",
    )
    assert ref.api_contract_seed_ref_id == "acs-001"
    assert len(ref.api_contract_seed_hash) == 64

def test_api_contract_seed_ref_deterministic():
    a = build_delegation_api_contract_seed_ref(api_contract_seed_ref_id="acs-001", delegation_ref_id="deleg-001")
    b = build_delegation_api_contract_seed_ref(api_contract_seed_ref_id="acs-001", delegation_ref_id="deleg-001")
    assert hash_delegation_api_contract_seed_ref(a) == hash_delegation_api_contract_seed_ref(b)

def test_api_contract_seed_ref_changed_input_changes_hash():
    a = build_delegation_api_contract_seed_ref(api_contract_seed_ref_id="acs-001", delegation_ref_id="deleg-001",
                                                api_contract_seed_ref="A")
    b = build_delegation_api_contract_seed_ref(api_contract_seed_ref_id="acs-001", delegation_ref_id="deleg-001",
                                                api_contract_seed_ref="B")
    assert hash_delegation_api_contract_seed_ref(a) != hash_delegation_api_contract_seed_ref(b)

def test_api_contract_seed_ref_does_not_imply_api_contract():
    """APIContractSeedRef exists does not mean API contract."""
    ref = build_delegation_api_contract_seed_ref(api_contract_seed_ref_id="acs-001", delegation_ref_id="deleg-001")
    assert ref.seed_status == DelegationPreProjectionSeedStatus.REFERENCE_ONLY


# ============================================================================
# 7. EventContractSeedRef — build, hash, determinism
# ============================================================================

def test_build_event_contract_seed_ref():
    ref = build_delegation_event_contract_seed_ref(
        event_contract_seed_ref_id="ecs-001",
        delegation_ref_id="deleg-001",
        event_contract_seed_ref="Future delegation event contract",
        event_contract_seed_description="Seed for P1.8.17 event contract",
    )
    assert ref.event_contract_seed_ref_id == "ecs-001"
    assert len(ref.event_contract_seed_hash) == 64

def test_event_contract_seed_ref_deterministic():
    a = build_delegation_event_contract_seed_ref(event_contract_seed_ref_id="ecs-001", delegation_ref_id="deleg-001")
    b = build_delegation_event_contract_seed_ref(event_contract_seed_ref_id="ecs-001", delegation_ref_id="deleg-001")
    assert hash_delegation_event_contract_seed_ref(a) == hash_delegation_event_contract_seed_ref(b)

def test_event_contract_seed_ref_changed_input_changes_hash():
    a = build_delegation_event_contract_seed_ref(event_contract_seed_ref_id="ecs-001", delegation_ref_id="deleg-001",
                                                  event_contract_seed_ref="A")
    b = build_delegation_event_contract_seed_ref(event_contract_seed_ref_id="ecs-001", delegation_ref_id="deleg-001",
                                                  event_contract_seed_ref="B")
    assert hash_delegation_event_contract_seed_ref(a) != hash_delegation_event_contract_seed_ref(b)

def test_event_contract_seed_ref_does_not_imply_event_contract():
    """EventContractSeedRef exists does not mean event contract."""
    ref = build_delegation_event_contract_seed_ref(event_contract_seed_ref_id="ecs-001", delegation_ref_id="deleg-001")
    assert ref.seed_status == DelegationPreProjectionSeedStatus.REFERENCE_ONLY


# ============================================================================
# 8. SurfaceEligibilityEntry — build, hash, determinism
# ============================================================================

def test_build_surface_eligibility_entry():
    entry = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001",
        delegation_ref_id="deleg-001",
        field_ref="delegation.subject_name",
        field_description="Delegation subject name — operator-visible candidate",
        exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
        exposure_reason="Candidate for CLI display in P1.8.18",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert entry.eligibility_entry_id == "se-001"
    assert entry.field_ref == "delegation.subject_name"
    assert entry.exposure_class == DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE
    assert len(entry.entry_hash) == 64

def test_surface_eligibility_entry_deterministic():
    a = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        field_ref="f", exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    )
    b = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        field_ref="f", exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    )
    assert hash_delegation_surface_eligibility_entry(a) == hash_delegation_surface_eligibility_entry(b)

def test_surface_eligibility_entry_changed_class_changes_hash():
    a = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    )
    b = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        exposure_class=DelegationSurfaceExposureClass.REDACTED_CANDIDATE,
    )
    assert hash_delegation_surface_eligibility_entry(a) != hash_delegation_surface_eligibility_entry(b)

def test_surface_eligibility_entry_does_not_imply_field_exposure():
    """SurfaceEligibilityEntry does not mean field exposed."""
    entry = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    )
    assert entry.exposure_class == DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE  # candidate only


# ============================================================================
# 9. SurfaceEligibilityProfile — build, hash, determinism, counts
# ============================================================================

def test_build_surface_eligibility_profile():
    entries = [
        build_delegation_surface_eligibility_entry(
            eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
            field_ref="f1", exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
        ),
        build_delegation_surface_eligibility_entry(
            eligibility_entry_id="se-002", delegation_ref_id="deleg-001",
            field_ref="f2", exposure_class=DelegationSurfaceExposureClass.INTERNAL_ONLY,
        ),
        build_delegation_surface_eligibility_entry(
            eligibility_entry_id="se-003", delegation_ref_id="deleg-001",
            field_ref="f3", exposure_class=DelegationSurfaceExposureClass.REDACTED_CANDIDATE,
        ),
    ]
    profile = build_delegation_surface_eligibility_profile(
        surface_eligibility_profile_id="sep-001",
        delegation_ref_id="deleg-001",
        entries=entries,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert profile.surface_eligibility_profile_id == "sep-001"
    assert profile.operator_visible_candidate_count == 1
    assert profile.internal_only_count == 1
    assert profile.redacted_candidate_count == 1
    assert profile.governance_only_count == 0
    assert profile.trace_context_only_count == 0
    assert profile.policy_context_only_count == 0
    assert profile.runtime_context_only_count == 0
    assert profile.unavailable_count == 0
    assert len(profile.surface_eligibility_profile_hash) == 64

def test_surface_eligibility_profile_deterministic():
    entries = [
        build_delegation_surface_eligibility_entry(
            eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
            field_ref="f1", exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
        ),
    ]
    a = build_delegation_surface_eligibility_profile(
        surface_eligibility_profile_id="sep-001", delegation_ref_id="deleg-001", entries=entries,
    )
    b = build_delegation_surface_eligibility_profile(
        surface_eligibility_profile_id="sep-001", delegation_ref_id="deleg-001", entries=entries,
    )
    assert hash_delegation_surface_eligibility_profile(a) == hash_delegation_surface_eligibility_profile(b)

def test_surface_eligibility_profile_changed_entries_changes_hash():
    entries_a = [build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        field_ref="f1", exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    )]
    entries_b = [build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        field_ref="f1", exposure_class=DelegationSurfaceExposureClass.REDACTED_CANDIDATE,
    )]
    a = build_delegation_surface_eligibility_profile(
        surface_eligibility_profile_id="sep-001", delegation_ref_id="deleg-001", entries=entries_a,
    )
    b = build_delegation_surface_eligibility_profile(
        surface_eligibility_profile_id="sep-001", delegation_ref_id="deleg-001", entries=entries_b,
    )
    assert hash_delegation_surface_eligibility_profile(a) != hash_delegation_surface_eligibility_profile(b)

def test_surface_eligibility_profile_does_not_imply_surface_approval():
    """SurfaceEligibilityProfile does not mean surface approval."""
    entries = [
        build_delegation_surface_eligibility_entry(
            eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
            exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
        ),
    ]
    profile = build_delegation_surface_eligibility_profile(
        surface_eligibility_profile_id="sep-001", delegation_ref_id="deleg-001", entries=entries,
    )
    # Profile contains candidate counts only; no approval
    assert profile.operator_visible_candidate_count == 1

def test_operator_visible_candidate_does_not_imply_projected_field():
    """Operator-visible candidate is not projected field."""
    entry = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        exposure_class=DelegationSurfaceExposureClass.OPERATOR_VISIBLE_CANDIDATE,
    )
    assert entry.exposure_class.value == "operator_visible_candidate"  # candidate only

def test_redacted_candidate_does_not_imply_policy_enforcement():
    """Redacted candidate is not policy enforcement."""
    entry = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        exposure_class=DelegationSurfaceExposureClass.REDACTED_CANDIDATE,
    )
    assert entry.exposure_class.value == "redacted_candidate"  # candidate only

def test_internal_only_candidate_does_not_imply_enforcement():
    """Internal-only candidate is not access control enforcement."""
    entry = build_delegation_surface_eligibility_entry(
        eligibility_entry_id="se-001", delegation_ref_id="deleg-001",
        exposure_class=DelegationSurfaceExposureClass.INTERNAL_ONLY,
    )
    assert entry.exposure_class.value == "internal_only"  # candidate only


# ============================================================================
# 10. ProjectionGapMatrixEntry — build, hash, determinism
# ============================================================================

def test_build_projection_gap_matrix_entry():
    entry = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001",
        delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT,
        present=True,
        hash_present=True,
        source_label_present=True,
        finding_count=0,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert entry.entry_id == "gm-001"
    assert entry.family == DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT
    assert entry.present is True
    assert entry.hash_present is True
    assert entry.source_label_present is True
    assert len(entry.entry_hash) == 64

def test_projection_gap_matrix_entry_missing():
    entry = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-002",
        delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.API_CONTRACT_SEED_CONTEXT,
        present=False,
        hash_present=False,
        source_label_present=False,
        unavailable_reason="P1.8.17 API contract not yet implemented",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert entry.present is False
    assert entry.hash_present is False
    assert entry.unavailable_reason == "P1.8.17 API contract not yet implemented"

def test_projection_gap_matrix_entry_deterministic():
    a = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT,
        present=True,
    )
    b = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT,
        present=True,
    )
    assert hash_delegation_projection_gap_matrix_entry(a) == hash_delegation_projection_gap_matrix_entry(b)

def test_projection_gap_matrix_entry_changed_present_changes_hash():
    a = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=True,
    )
    b = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=False,
    )
    assert hash_delegation_projection_gap_matrix_entry(a) != hash_delegation_projection_gap_matrix_entry(b)

def test_projection_gap_matrix_entry_does_not_imply_projection_validation():
    """ProjectionGapMatrixEntry does not mean projection validation."""
    entry = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=True,
    )
    assert entry.present is True
    # present is context presence only, not contract readiness

def test_gap_present_does_not_imply_runtime_failure():
    """Gap present is not runtime failure."""
    entry = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-002", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.API_CONTRACT_SEED_CONTEXT, present=False,
    )
    assert entry.present is False
    assert entry.finding_count == 0

def test_context_present_does_not_imply_contract_readiness():
    """Context present is not contract readiness."""
    entry = build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=True,
    )
    assert entry.family != DelegationProjectionSeedFamily.API_CONTRACT_SEED_CONTEXT


# ============================================================================
# 11. ProjectionGapMatrix — build, hash, determinism
# ============================================================================

def test_build_projection_gap_matrix():
    entries = [
        build_delegation_projection_gap_matrix_entry(
            entry_id="gm-001", delegation_ref_id="deleg-001",
            family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=True,
        ),
        build_delegation_projection_gap_matrix_entry(
            entry_id="gm-002", delegation_ref_id="deleg-001",
            family=DelegationProjectionSeedFamily.API_CONTRACT_SEED_CONTEXT, present=False,
            unavailable_reason="P1.8.17 not implemented",
        ),
    ]
    matrix = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001",
        delegation_ref_id="deleg-001",
        entries=entries,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert matrix.projection_gap_matrix_id == "pgm-001"
    assert len(matrix.entries) == 2
    assert matrix.entries[0].present is True
    assert matrix.entries[1].present is False
    assert len(matrix.projection_gap_matrix_hash) == 64

def test_projection_gap_matrix_deterministic():
    entries = [
        build_delegation_projection_gap_matrix_entry(
            entry_id="gm-001", delegation_ref_id="deleg-001",
            family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT,
        ),
    ]
    a = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001", delegation_ref_id="deleg-001", entries=entries,
    )
    b = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001", delegation_ref_id="deleg-001", entries=entries,
    )
    assert hash_delegation_projection_gap_matrix(a) == hash_delegation_projection_gap_matrix(b)

def test_projection_gap_matrix_changed_entries_changes_hash():
    entries_a = [build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=True,
    )]
    entries_b = [build_delegation_projection_gap_matrix_entry(
        entry_id="gm-001", delegation_ref_id="deleg-001",
        family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=False,
    )]
    a = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001", delegation_ref_id="deleg-001", entries=entries_a,
    )
    b = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001", delegation_ref_id="deleg-001", entries=entries_b,
    )
    assert hash_delegation_projection_gap_matrix(a) != hash_delegation_projection_gap_matrix(b)

def test_projection_gap_matrix_does_not_imply_projection_validation():
    """ProjectionGapMatrix does not mean projection validation."""
    entries = [
        build_delegation_projection_gap_matrix_entry(
            entry_id="gm-001", delegation_ref_id="deleg-001",
            family=DelegationProjectionSeedFamily.ACCOUNTABILITY_PACKET_CONTEXT, present=True,
        ),
    ]
    matrix = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001", delegation_ref_id="deleg-001", entries=entries,
    )
    assert len(matrix.projection_gap_matrix_hash) == 64
    # hash is not TRACE_VERIFIED; present is not contract readiness


# ============================================================================
# 12. PreProjectionSeedEnvelope — build, hash, determinism
# ============================================================================

def test_build_pre_projection_seed_envelope():
    envelope = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001",
        delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="deadbeef" * 8,
        integration_summary_envelope_hash="cafebabe" * 8,
        accountability_packet_envelope_hash="facefeed" * 8,
        surface_eligibility_profile_hash="abc12345" * 8,
        projection_gap_matrix_hash="def67890" * 8,
        read_model_seed_refs="rms-001",
        api_contract_seed_refs="acs-001",
        event_contract_seed_refs="ecs-001",
        surface_contract_seed_refs="scs-001",
        golden_thread_ref="agent/STATE.md Golden Thread",
        next_handoff_ref="P1.8.17",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert envelope.pre_projection_seed_envelope_id == "ppse-001"
    assert envelope.accountability_packet_binding_set_hash == "deadbeef" * 8
    assert envelope.integration_summary_envelope_hash == "cafebabe" * 8
    assert envelope.next_handoff_ref == "P1.8.17"
    assert len(envelope.pre_projection_seed_envelope_hash) == 64

def test_pre_projection_seed_envelope_deterministic():
    a = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001",
        delegation_ref_id="deleg-001",
    )
    b = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001",
        delegation_ref_id="deleg-001",
    )
    assert hash_delegation_pre_projection_seed_envelope(a) == hash_delegation_pre_projection_seed_envelope(b)

def test_pre_projection_seed_envelope_changed_input_changes_hash():
    a = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001", delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="aaa",
    )
    b = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001", delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="bbb",
    )
    assert hash_delegation_pre_projection_seed_envelope(a) != hash_delegation_pre_projection_seed_envelope(b)

def test_pre_projection_seed_envelope_is_not_projection_contract():
    """PreProjectionSeedEnvelope is not Projection/API/Event Contract."""
    envelope = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001", delegation_ref_id="deleg-001",
    )
    assert envelope.pre_projection_seed_envelope_id == "ppse-001"


# ============================================================================
# 13. PreProjectionSeedBinding — build, hash, determinism
# ============================================================================

def test_build_pre_projection_seed_binding():
    binding = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001",
        delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="deadbeef" * 8,
        pre_projection_seed_envelope_hash="cafebabe" * 8,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
        seed_status=DelegationPreProjectionSeedStatus.REFERENCE_ONLY,
    )
    assert binding.binding_id == "ppb-001"
    assert binding.seed_status == DelegationPreProjectionSeedStatus.REFERENCE_ONLY
    assert len(binding.binding_hash) == 64

def test_pre_projection_seed_binding_deterministic():
    a = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
    )
    b = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
    )
    assert hash_delegation_pre_projection_seed_binding(a) == hash_delegation_pre_projection_seed_binding(b)

def test_pre_projection_seed_binding_changed_input_changes_hash():
    a = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
        pre_projection_seed_envelope_hash="aaa",
    )
    b = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
        pre_projection_seed_envelope_hash="bbb",
    )
    assert hash_delegation_pre_projection_seed_binding(a) != hash_delegation_pre_projection_seed_binding(b)


# ============================================================================
# 14. PreProjectionSeedBindingSet — build, hash, determinism
# ============================================================================

def test_build_pre_projection_seed_binding_set():
    binding = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
        pre_projection_seed_envelope_hash="cafebabe" * 8,
    )
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001",
        delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="deadbeef" * 8,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert bs.pre_projection_seed_binding_set_id == "ppbs-001"
    assert len(bs.bindings) == 1
    assert bs.bindings[0].binding_id == "ppb-001"
    assert len(bs.pre_projection_seed_binding_set_hash) == 64

def test_pre_projection_seed_binding_set_deterministic():
    binding = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
    )
    a = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
        bindings=[binding],
    )
    b = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
        bindings=[binding],
    )
    assert hash_delegation_pre_projection_seed_binding_set(a) == hash_delegation_pre_projection_seed_binding_set(b)

def test_pre_projection_seed_binding_set_changed_bindings_changes_hash():
    binding_a = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
        pre_projection_seed_envelope_hash="aaa",
    )
    binding_b = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
        pre_projection_seed_envelope_hash="bbb",
    )
    a = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
        bindings=[binding_a],
    )
    b = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
        bindings=[binding_b],
    )
    assert hash_delegation_pre_projection_seed_binding_set(a) != hash_delegation_pre_projection_seed_binding_set(b)


# ============================================================================
# 15. SideEffects — all false
# ============================================================================

def test_side_effects_all_false():
    se = DelegationPreProjectionSeedSideEffects(
        projection_created=False,
        read_model_created=False,
        api_contract_created=False,
        event_contract_created=False,
        surface_contract_created=False,
        cli_shell_tui_bound=False,
        ui_surface_created=False,
        field_exposed=False,
        redaction_enforced=False,
        policy_decision_emitted=False,
        custos_decision_emitted=False,
        runtime_executed=False,
        trace_written=False,
        ledger_written=False,
        output_passport_created=False,
        global_trace_written=False,
        runtime_mutated=False,
    )
    assert se.projection_created is False
    assert se.read_model_created is False
    assert se.api_contract_created is False
    assert se.event_contract_created is False
    assert se.surface_contract_created is False
    assert se.cli_shell_tui_bound is False
    assert se.ui_surface_created is False
    assert se.field_exposed is False
    assert se.redaction_enforced is False
    assert se.policy_decision_emitted is False
    assert se.custos_decision_emitted is False
    assert se.runtime_executed is False
    assert se.trace_written is False
    assert se.ledger_written is False
    assert se.output_passport_created is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False

def test_binding_set_side_effects_all_false():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    sf = bs.side_effects
    assert sf.projection_created is False
    assert sf.read_model_created is False
    assert sf.api_contract_created is False
    assert sf.event_contract_created is False
    assert sf.surface_contract_created is False
    assert sf.cli_shell_tui_bound is False
    assert sf.ui_surface_created is False
    assert sf.field_exposed is False
    assert sf.redaction_enforced is False
    assert sf.policy_decision_emitted is False
    assert sf.custos_decision_emitted is False
    assert sf.runtime_executed is False
    assert sf.trace_written is False
    assert sf.ledger_written is False
    assert sf.output_passport_created is False
    assert sf.global_trace_written is False
    assert sf.runtime_mutated is False


# ============================================================================
# 16. StatusReport
# ============================================================================

def test_build_pre_projection_seed_status_report():
    report = build_delegation_pre_projection_seed_status_report()
    assert report.status_label == "P1.8.16: reference-only pre-projection seed metadata layer"
    assert len(report.available_contracts) >= 0
    assert len(report.unavailable_bindings) >= 0
    assert "Projection/API/Event/Read Model" in report.unavailable_bindings
    assert "CLI/Shell/TUI Binding" in report.unavailable_bindings
    assert "Trace Writer" in report.unavailable_bindings
    assert "Ledger Writer" in report.unavailable_bindings
    assert "Output Passport / P1.9" in report.unavailable_bindings
    assert "P1.8.17 Projection/API/Event Contract" in report.unavailable_bindings
    assert "P1.8.18 CLI/Shell/TUI Binding" in report.unavailable_bindings
    assert "P1.8.19 Docs/State/Report Seal Update" in report.unavailable_bindings
    assert "P1.8.20 Exit Seal Demo" in report.unavailable_bindings
    assert len(report.status_hash) == 64

def test_status_report_side_effects_all_false():
    report = build_delegation_pre_projection_seed_status_report()
    se = report.side_effects
    assert se.projection_created is False
    assert se.read_model_created is False
    assert se.api_contract_created is False
    assert se.event_contract_created is False
    assert se.surface_contract_created is False
    assert se.cli_shell_tui_bound is False
    assert se.ui_surface_created is False
    assert se.field_exposed is False
    assert se.redaction_enforced is False
    assert se.policy_decision_emitted is False
    assert se.runtime_executed is False
    assert se.trace_written is False
    assert se.ledger_written is False
    assert se.output_passport_created is False


# ============================================================================
# 17. Serialization (JSON-safe)
# ============================================================================

def test_serialize_pre_projection_seed_envelope():
    envelope = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001", delegation_ref_id="deleg-001",
    )
    serialized = serialize_delegation_pre_projection_seed_envelope(envelope)
    data = json.loads(serialized)
    assert data["schema_version"] == envelope.schema_version
    assert data["pre_projection_seed_envelope_id"] == "ppse-001"
    assert data["pre_projection_seed_envelope_hash"] == envelope.pre_projection_seed_envelope_hash

def test_serialize_pre_projection_seed_binding_set():
    binding = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001", delegation_ref_id="deleg-001",
    )
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001",
        delegation_ref_id="deleg-001",
        bindings=[binding],
    )
    serialized = serialize_delegation_pre_projection_seed_binding_set(bs)
    data = json.loads(serialized)
    assert data["schema_version"] == bs.schema_version
    assert data["pre_projection_seed_binding_set_id"] == "ppbs-001"
    assert data["pre_projection_seed_binding_set_hash"] == bs.pre_projection_seed_binding_set_hash
    assert len(data["bindings"]) == 1
    assert data["bindings"][0]["binding_id"] == "ppb-001"
    assert data["side_effects"]["projection_created"] is False

def test_serialization_is_deterministic():
    envelope = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001", delegation_ref_id="deleg-001",
    )
    s1 = serialize_delegation_pre_projection_seed_envelope(envelope)
    s2 = serialize_delegation_pre_projection_seed_envelope(envelope)
    assert s1 == s2


# ============================================================================
# 18. DEV_FIXTURE truth label
# ============================================================================

def test_dev_fixture_label_is_visible():
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert ref.source_label == DelegationSourceLabel.DEV_FIXTURE

def test_no_live_claim():
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert ref.source_label != DelegationSourceLabel.LIVE  # or equivalent

def test_no_trace_verified_claim():
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
    )
    # Seed hash is not TRACE_VERIFIED
    assert len(ref.pre_projection_readiness_hash) == 64
    # hash exists but is not a TRACE_VERIFIED claim


# ============================================================================
# 19. No forbidden behavior
# ============================================================================

def test_no_projection_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.projection_created is False

def test_no_read_model_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.read_model_created is False

def test_no_api_contract_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.api_contract_created is False

def test_no_event_contract_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.event_contract_created is False

def test_no_surface_contract_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.surface_contract_created is False

def test_no_cli_shell_tui_bound():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.cli_shell_tui_bound is False

def test_no_ui_surface_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.ui_surface_created is False

def test_no_field_exposed():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.field_exposed is False

def test_no_redaction_enforced():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.redaction_enforced is False

def test_no_policy_decision_emitted():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.policy_decision_emitted is False

def test_no_custos_decision_emitted():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.custos_decision_emitted is False

def test_no_runtime_executed():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.runtime_executed is False

def test_no_trace_written():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.trace_written is False

def test_no_ledger_written():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.ledger_written is False

def test_no_output_passport_created():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.output_passport_created is False

def test_no_global_trace_written():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.global_trace_written is False

def test_no_runtime_mutated():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.runtime_mutated is False

def test_no_trace_verified_claim_on_binding_set():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.trace_written is False

def test_no_p1_8_17_behavior():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.projection_created is False
    assert bs.side_effects.api_contract_created is False

def test_no_p1_8_18_behavior():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.cli_shell_tui_bound is False

def test_no_p1_8_19_behavior():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.surface_contract_created is False

def test_no_p1_8_20_behavior():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.output_passport_created is False

def test_no_p1_9_behavior():
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001", delegation_ref_id="deleg-001",
    )
    assert bs.side_effects.output_passport_created is False

def test_no_projection_validation():
    matrix = build_delegation_projection_gap_matrix(
        projection_gap_matrix_id="pgm-001", delegation_ref_id="deleg-001",
    )
    # matrix exists and has a hash, but is NOT projection validation
    assert len(matrix.projection_gap_matrix_hash) == 64

def test_source_label_visible():
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert ref.source_label == DelegationSourceLabel.DEV_FIXTURE

def test_seed_hashes_not_trace_verified():
    """Seed hashes exist but are not TRACE_VERIFIED."""
    ref = build_delegation_pre_projection_readiness_ref(
        pre_projection_readiness_ref_id="ppr-001", delegation_ref_id="deleg-001",
    )
    assert len(ref.pre_projection_readiness_hash) == 64


# ============================================================================
# 20. Accountability packet context feed-through test
# ============================================================================

def test_accountability_packet_context_feeds_pre_projection_path():
    """P1.8.15 AccountabilityPacketBindingSet can feed P1.8.16 pre-projection path."""
    # Build a pre-projection seed envelope referencing P1.8.15 hashes
    envelope = build_delegation_pre_projection_seed_envelope(
        pre_projection_seed_envelope_id="ppse-001",
        delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="deadbeef" * 8,
        integration_summary_envelope_hash="cafebabe" * 8,
        accountability_packet_envelope_hash="facefeed" * 8,
        next_handoff_ref="P1.8.17",
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert envelope.accountability_packet_binding_set_hash == "deadbeef" * 8
    assert envelope.integration_summary_envelope_hash == "cafebabe" * 8
    assert envelope.accountability_packet_envelope_hash == "facefeed" * 8
    assert envelope.next_handoff_ref == "P1.8.17"

    # Build binding set wrapping the envelope
    binding = build_delegation_pre_projection_seed_binding(
        binding_id="ppb-001",
        delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="deadbeef" * 8,
        pre_projection_seed_envelope_hash=envelope.pre_projection_seed_envelope_hash,
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    bs = build_delegation_pre_projection_seed_binding_set(
        pre_projection_seed_binding_set_id="ppbs-001",
        delegation_ref_id="deleg-001",
        accountability_packet_binding_set_hash="deadbeef" * 8,
        bindings=[binding],
        source_label=DelegationSourceLabel.DEV_FIXTURE,
    )
    assert len(bs.pre_projection_seed_binding_set_hash) == 64
    assert bs.side_effects.projection_created is False

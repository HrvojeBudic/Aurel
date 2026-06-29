"""Tests for P2.5-B handoff context / availability read model."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.cross_surface_handoff_context import (
    P2_5_A_COMMIT_REF,
    P2_5_A_PACK_ID,
    P2_5_A_REPORT_HASH_COMMIT_REF,
    P2_5_A_REPORT_PATH,
    P2_5_B_DEPENDENCY_PACK,
    P2_5_B_NEXT_PACK,
    P2_5_B_OFFICIAL_SECTION_NAME,
    P2_5_B_PACK_CHECKPOINT_IDS,
    P2_5_B_PACK_ID,
    P2_5_B_SECTION_ID,
    CrossSurfaceAvailabilityStatus,
    CrossSurfaceConflictKind,
    CrossSurfaceConflictSeverity,
    CrossSurfaceContextItem,
    CrossSurfaceContextKind,
    CrossSurfaceContinuityKind,
    CrossSurfaceExplanationKind,
    CrossSurfaceHandoffAvailability,
    CrossSurfaceHandoffConflict,
    CrossSurfaceHandoffContextGate,
    CrossSurfaceHandoffContextGateStatus,
    CrossSurfaceHandoffContextResult,
    CrossSurfaceHandoffContextSnapshot,
    CrossSurfaceHandoffContinuity,
    CrossSurfaceHandoffExplanation,
    CrossSurfaceHandoffContextTruthBoundary,
    P25BHandoffContextResult,
    P25BSideEffectProof,
    assert_availability_is_not_permission_enforcement,
    assert_conflict_is_not_resolution,
    assert_context_snapshot_is_not_context_transfer,
    assert_context_snapshot_is_not_memory_write,
    assert_continuity_is_not_persistence,
    assert_explanation_is_not_approval,
    assert_explanation_is_not_operator_confirmation,
    assert_p2_5_b_does_not_start_future_work,
    build_cross_surface_context_item,
    build_cross_surface_context_snapshot,
    build_cross_surface_handoff_availability,
    build_cross_surface_handoff_conflict,
    build_cross_surface_handoff_context_gate,
    build_cross_surface_handoff_context_result,
    build_cross_surface_handoff_continuity,
    build_cross_surface_handoff_explanation,
    build_p2_5_b_handoff_context_result,
    build_p2_5_b_side_effect_proof,
    render_cross_surface_handoff_context_summary,
    serialize_p2_5_b_result,
)


def test_module_imports_p2_5_b() -> None:
    import agentic_runtime.aurel_shell.cross_surface_handoff_context  # noqa: F401


def test_p2_5_b_pack_identity_and_dependency_constants() -> None:
    assert P2_5_B_PACK_ID == "P2.5-B"
    assert P2_5_B_SECTION_ID == "P2.5"
    assert P2_5_B_OFFICIAL_SECTION_NAME == "Cross-Surface Handoff"
    assert P2_5_B_DEPENDENCY_PACK == P2_5_A_PACK_ID
    assert P2_5_B_NEXT_PACK == "P2.5-C"
    assert P2_5_B_PACK_CHECKPOINT_IDS == (
        "P2.5.6",
        "P2.5.7",
        "P2.5.8",
        "P2.5.9",
        "P2.5.10",
    )
    assert P2_5_A_COMMIT_REF
    assert P2_5_A_REPORT_HASH_COMMIT_REF


def test_dependency_gate_represents_p2_5_a_and_omni_ignore_policy() -> None:
    gate = build_cross_surface_handoff_context_gate(repo_evidence_gate_passed=True)
    assert isinstance(gate, CrossSurfaceHandoffContextGate)
    assert gate.dependency_pack == "P2.5-A"
    assert gate.dependency_report_ref == P2_5_A_REPORT_PATH
    assert gate.dependency_commit_ref == P2_5_A_COMMIT_REF
    assert "validation" in gate.dependency_validation_ref.lower()
    assert "foundation_result" in gate.dependency_handoff_foundation_result_ref
    assert "no_route_boundary" in gate.dependency_no_route_boundary_ref
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status == CrossSurfaceHandoffContextGateStatus.READY


def test_gate_blocks_when_repo_evidence_fails() -> None:
    gate = build_cross_surface_handoff_context_gate(repo_evidence_gate_passed=False)
    assert gate.gate_status == CrossSurfaceHandoffContextGateStatus.BLOCKED


def test_closed_world_enums() -> None:
    assert {item.value for item in CrossSurfaceHandoffContextGateStatus} == {
        "READY",
        "BLOCKED",
        "PARTIAL",
        "ERROR",
    }
    assert {item.value for item in CrossSurfaceContextKind} == {
        "COMMAND_RESULT_CONTEXT",
        "COMMAND_PROPOSAL_CONTEXT",
        "SURFACE_CONTEXT_REF",
        "WINDOW_CONTEXT_REF",
        "OBJECT_CONTEXT_REF",
        "ARTIFACT_CONTEXT_REF",
        "SYSTEM_STATUS_CONTEXT",
        "OPERATOR_ATTENTION_CONTEXT",
        "DEV_FIXTURE_CONTEXT",
        "UNKNOWN_UNAVAILABLE",
    }
    assert {item.value for item in CrossSurfaceContinuityKind} == {
        "CARRY_LABEL",
        "CARRY_REFERENCE",
        "CARRY_SURFACE_SOURCE",
        "CARRY_SURFACE_TARGET",
        "CARRY_INTENT",
        "CARRY_LIMITATION",
        "CARRY_UNAVAILABLE_REASON",
        "DEV_FIXTURE_CONTINUITY",
        "UNKNOWN_UNAVAILABLE",
    }
    assert {item.value for item in CrossSurfaceConflictSeverity} == {
        "INFO",
        "WARNING",
        "BLOCKING",
        "ERROR",
    }
    assert {item.value for item in CrossSurfaceAvailabilityStatus} == {
        "AVAILABLE_READ_MODEL_ONLY",
        "PARTIAL",
        "UNAVAILABLE",
        "BLOCKED",
        "ERROR",
    }
    assert "NOT_CONTEXT_TRANSFER" in {
        item.value for item in CrossSurfaceHandoffContextTruthBoundary
    }


def test_p2_5_6_context_snapshot_and_items_are_read_only_refs() -> None:
    snapshot = build_cross_surface_context_snapshot(
        handoff_foundation_result_ref="p2_5_a_foundation_result::fixture",
    )
    assert isinstance(snapshot, CrossSurfaceHandoffContextSnapshot)
    assert len(snapshot.context_items) >= 3
    assert snapshot.handoff_foundation_result_ref == "p2_5_a_foundation_result::fixture"
    assert snapshot.is_context_transfer is False
    assert snapshot.memory_written is False
    assert snapshot.storage_written is False
    assert snapshot.trace_written is False
    assert snapshot.runtime_mutated is False
    for item in snapshot.context_items:
        assert isinstance(item, CrossSurfaceContextItem)
        assert item.is_persisted is False
        assert item.is_transferred is False
        assert item.memory_written is False
        assert item.storage_written is False
        assert item.trace_written is False
        json.dumps(item.to_canonical_dict())
    assert_context_snapshot_is_not_memory_write(snapshot)
    assert_context_snapshot_is_not_context_transfer(snapshot)


def test_p2_5_6_context_item_rejects_persistence_transfer_or_writes() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceContextItem(
            context_item_id="bad",
            context_kind=CrossSurfaceContextKind.DEV_FIXTURE_CONTEXT,
            context_ref="bad",
            context_label="bad",
            source_ref="bad",
            included_for_explanation=True,
            is_persisted=True,
            is_transferred=False,
            memory_written=False,
            storage_written=False,
            trace_written=False,
            truth_label="bad",
            limitations=(),
        )


def test_p2_5_7_continuity_carry_forward_metadata_only() -> None:
    continuity = build_cross_surface_handoff_continuity(
        handoff_foundation_result_ref="foundation",
        continuity_kind=CrossSurfaceContinuityKind.CARRY_REFERENCE,
        carry_forward_label="Carry foundation ref",
        carry_forward_ref="foundation",
    )
    assert isinstance(continuity, CrossSurfaceHandoffContinuity)
    assert continuity.required_later is True
    assert continuity.persisted_now is False
    assert continuity.memory_mutated is False
    assert continuity.object_copied is False
    assert continuity.object_moved is False
    assert continuity.storage_written is False
    assert continuity.trace_written is False
    assert json.dumps(continuity.to_canonical_dict())
    assert_continuity_is_not_persistence(continuity)


def test_p2_5_7_continuity_rejects_object_copy_or_persistence() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffContinuity(
            continuity_id="bad",
            handoff_foundation_result_ref="foundation",
            continuity_kind=CrossSurfaceContinuityKind.CARRY_REFERENCE,
            carry_forward_label="bad",
            carry_forward_ref="bad",
            required_later=True,
            persisted_now=False,
            memory_mutated=False,
            object_copied=True,
            object_moved=False,
            storage_written=False,
            trace_written=False,
            truth_label="bad",
            limitations=(),
        )


def test_p2_5_8_conflict_record_is_not_resolution_or_runtime_block() -> None:
    conflict = build_cross_surface_handoff_conflict(
        conflict_kind=CrossSurfaceConflictKind.TARGET_REQUIRES_LATER_PERMISSION,
        severity=CrossSurfaceConflictSeverity.INFO,
        message="permission later",
        context_ref="context",
        surface_ref="corp",
        payload_ref="payload",
        required_action_later="future permission pack",
    )
    assert isinstance(conflict, CrossSurfaceHandoffConflict)
    assert conflict.resolves_conflict is False
    assert conflict.runtime_blocked is False
    assert conflict.runtime_mutated is False
    assert conflict.required_action_later == "future permission pack"
    assert json.dumps(conflict.to_canonical_dict())
    assert_conflict_is_not_resolution(conflict)


def test_p2_5_8_conflict_rejects_resolution_claim() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffConflict(
            conflict_id="bad",
            conflict_kind=CrossSurfaceConflictKind.CONTEXT_INCOMPLETE,
            severity=CrossSurfaceConflictSeverity.WARNING,
            message="bad",
            context_ref="context",
            surface_ref="hq",
            payload_ref="payload",
            blocks_contract_read_model=False,
            resolves_conflict=True,
            runtime_blocked=False,
            runtime_mutated=False,
            required_action_later="later",
            truth_label="bad",
            limitations=(),
        )


def test_p2_5_9_availability_readiness_is_not_permission_enforcement() -> None:
    conflict = build_cross_surface_handoff_conflict(
        conflict_kind=CrossSurfaceConflictKind.TARGET_REQUIRES_LATER_ROUTE_RUNTIME,
        severity=CrossSurfaceConflictSeverity.INFO,
        message="route later",
    )
    availability = build_cross_surface_handoff_availability(
        handoff_foundation_result_ref="foundation",
        conflicts=(conflict,),
    )
    assert isinstance(availability, CrossSurfaceHandoffAvailability)
    assert availability.availability_status == CrossSurfaceAvailabilityStatus.AVAILABLE_READ_MODEL_ONLY
    assert availability.available_read_model_only is True
    assert len(availability.unavailable_reasons) >= 5
    assert availability.conflicts == (conflict,)
    assert availability.requires_ui_later is True
    assert availability.requires_route_runtime_later is True
    assert availability.requires_permission_later is True
    assert availability.requires_approval_later is True
    assert availability.is_permission_decision is False
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert availability.activates_approval is False
    assert_availability_is_not_permission_enforcement(availability)


def test_p2_5_9_availability_rejects_permission_decision() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffAvailability(
            availability_id="bad",
            handoff_foundation_result_ref="foundation",
            availability_status=CrossSurfaceAvailabilityStatus.AVAILABLE_READ_MODEL_ONLY,
            available_read_model_only=True,
            unavailable_reasons=(),
            conflicts=(),
            requires_ui_later=True,
            requires_route_runtime_later=True,
            requires_permission_later=True,
            requires_approval_later=True,
            is_permission_decision=True,
            grants_permission=False,
            denies_permission=False,
            activates_approval=False,
            truth_label="bad",
            limitations=(),
        )


def test_p2_5_10_explanation_and_context_result_execute_nothing() -> None:
    snapshot = build_cross_surface_context_snapshot(
        handoff_foundation_result_ref="foundation",
    )
    continuity = build_cross_surface_handoff_continuity(
        handoff_foundation_result_ref="foundation",
        continuity_kind=CrossSurfaceContinuityKind.CARRY_LIMITATION,
        carry_forward_label="limitation",
        carry_forward_ref="boundary",
    )
    conflict = build_cross_surface_handoff_conflict(
        conflict_kind=CrossSurfaceConflictKind.TARGET_REQUIRES_LATER_UI,
        severity=CrossSurfaceConflictSeverity.INFO,
        message="ui later",
    )
    availability = build_cross_surface_handoff_availability(
        handoff_foundation_result_ref="foundation",
        conflicts=(conflict,),
    )
    explanation = build_cross_surface_handoff_explanation(
        explanation_kind=CrossSurfaceExplanationKind.WHAT_IS_NOT_EXECUTED,
        summary="nothing executes",
        context_refs=tuple(item.context_item_id for item in snapshot.context_items),
        continuity_refs=(continuity.continuity_id,),
        conflict_refs=(conflict.conflict_id,),
        availability_ref=availability.availability_id,
    )
    result = build_cross_surface_handoff_context_result(
        handoff_foundation_result_ref="foundation",
        context_snapshot=snapshot,
        continuity_items=(continuity,),
        conflict_items=(conflict,),
        availability=availability,
        explanations=(explanation,),
    )
    assert isinstance(explanation, CrossSurfaceHandoffExplanation)
    assert explanation.is_approval is False
    assert explanation.is_operator_confirmation is False
    assert explanation.executes_handoff is False
    assert explanation.executes_route is False
    assert explanation.switches_surface is False
    assert isinstance(result, CrossSurfaceHandoffContextResult)
    assert result.is_transition_result is False
    assert result.is_route_result is False
    assert result.is_live_ui is False
    assert result.is_source_of_truth is False
    assert result.transfers_context is False
    assert result.persists_context is False
    assert result.resolves_conflicts is False
    assert result.enforces_permissions is False
    assert result.mutates_runtime is False
    assert result.writes_storage is False
    assert result.writes_memory is False
    assert result.writes_trace is False
    assert_explanation_is_not_approval(explanation)
    assert_explanation_is_not_operator_confirmation(explanation)


def test_p2_5_10_pack_result_serializes_deterministically_and_next_pack() -> None:
    result = build_p2_5_b_handoff_context_result()
    assert isinstance(result, P25BHandoffContextResult)
    assert result.next_pack == P2_5_B_NEXT_PACK
    assert result.next_pack == "P2.5-C"
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False
    payload_a = serialize_p2_5_b_result(result)
    payload_b = serialize_p2_5_b_result(build_p2_5_b_handoff_context_result())
    assert payload_a == payload_b
    decoded = json.loads(payload_a)
    assert decoded["pack_id"] == "P2.5-B"
    assert decoded["context_result"]["is_route_result"] is False
    summary = render_cross_surface_handoff_context_summary(result)
    assert "P2.5-B" in summary
    assert "Claims LIVE: False" in summary
    assert_p2_5_b_does_not_start_future_work(result)


def test_side_effect_proof_all_fields_false() -> None:
    proof = build_p2_5_b_side_effect_proof()
    assert isinstance(proof, P25BSideEffectProof)
    for key, value in proof.to_canonical_dict().items():
        if key == "version_tag":
            continue
        assert value is False, key


def test_side_effect_proof_rejects_any_true_field() -> None:
    with pytest.raises(AurelShellValidationError):
        P25BSideEffectProof(memory_written=True)


def test_p2_5_b_does_not_start_future_packs() -> None:
    result = build_p2_5_b_handoff_context_result()
    proof = result.side_effect_proof
    assert proof.p2_5_c_started is False
    assert proof.p2_6_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False
    assert "P2.5-C" == result.next_pack

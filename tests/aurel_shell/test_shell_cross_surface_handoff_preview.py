"""Tests for P2.5-C handoff preview / confirmation boundary."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.cross_surface_handoff_preview import (
    P2_5_B_COMMIT_REF,
    P2_5_B_REPORT_HASH_COMMIT_REF,
    P2_5_B_REPORT_PATH,
    P2_5_C_DEPENDENCY_PACK,
    P2_5_C_NEXT_PACK,
    P2_5_C_OFFICIAL_SECTION_NAME,
    P2_5_C_PACK_CHECKPOINT_IDS,
    P2_5_C_PACK_ID,
    P2_5_C_SECTION_ID,
    CrossSurfaceConfirmationRequirementKind,
    CrossSurfaceHandoffExplanationBundle,
    CrossSurfaceHandoffPreviewContent,
    CrossSurfaceHandoffPreviewGate,
    CrossSurfaceHandoffPreviewGateStatus,
    CrossSurfaceHandoffPreviewRequest,
    CrossSurfaceHandoffPreviewResult,
    CrossSurfaceHandoffPreviewTruthBoundary,
    CrossSurfaceOperatorConfirmationIntentBoundary,
    CrossSurfaceOperatorConfirmationRequirement,
    CrossSurfacePreviewContentKind,
    CrossSurfacePreviewRequestKind,
    CrossSurfacePreviewResultStatus,
    P25CHandoffPreviewResult,
    P25CSideEffectProof,
    assert_confirmation_intent_is_not_authorization,
    assert_confirmation_requirement_is_not_consent,
    assert_explanation_bundle_is_not_approval,
    assert_no_confirmation_boundary_is_active,
    assert_no_execution_boundary_is_active,
    assert_p2_5_c_does_not_start_future_work,
    assert_preview_is_not_ui,
    assert_preview_request_is_not_operator_prompt,
    assert_preview_result_is_not_execution,
    build_cross_surface_handoff_explanation_bundle,
    build_cross_surface_handoff_preview_content,
    build_cross_surface_handoff_preview_gate,
    build_cross_surface_handoff_preview_request,
    build_cross_surface_handoff_preview_result,
    build_cross_surface_operator_confirmation_intent_boundary,
    build_cross_surface_operator_confirmation_requirement,
    build_p2_5_c_handoff_preview_result,
    build_p2_5_c_side_effect_proof,
    render_cross_surface_handoff_preview_summary,
    serialize_p2_5_c_result,
)


def test_module_imports_p2_5_c() -> None:
    import agentic_runtime.aurel_shell.cross_surface_handoff_preview  # noqa: F401


def test_p2_5_c_pack_identity_and_dependency_constants() -> None:
    assert P2_5_C_PACK_ID == "P2.5-C"
    assert P2_5_C_SECTION_ID == "P2.5"
    assert P2_5_C_OFFICIAL_SECTION_NAME == "Cross-Surface Handoff"
    assert P2_5_C_DEPENDENCY_PACK == "P2.5-B"
    assert P2_5_C_NEXT_PACK == "P2.5-D"
    assert P2_5_C_PACK_CHECKPOINT_IDS == (
        "P2.5.11",
        "P2.5.12",
        "P2.5.13",
        "P2.5.14",
        "P2.5.15",
    )
    assert P2_5_B_COMMIT_REF
    assert P2_5_B_REPORT_HASH_COMMIT_REF


def test_dependency_gate_represents_p2_5_b_and_omni_ignore_policy() -> None:
    gate = build_cross_surface_handoff_preview_gate(repo_evidence_gate_passed=True)
    assert isinstance(gate, CrossSurfaceHandoffPreviewGate)
    assert gate.dependency_pack == "P2.5-B"
    assert gate.dependency_report_ref == P2_5_B_REPORT_PATH
    assert gate.dependency_commit_ref == P2_5_B_COMMIT_REF
    assert "validation" in gate.dependency_validation_ref.lower()
    assert "context_result" in gate.dependency_context_result_ref
    assert "availability" in gate.dependency_availability_ref
    assert "explanation" in gate.dependency_explanation_ref
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status == CrossSurfaceHandoffPreviewGateStatus.READY


def test_gate_blocks_when_repo_evidence_fails() -> None:
    gate = build_cross_surface_handoff_preview_gate(repo_evidence_gate_passed=False)
    assert gate.gate_status == CrossSurfaceHandoffPreviewGateStatus.BLOCKED


def test_closed_world_enums() -> None:
    assert {item.value for item in CrossSurfaceHandoffPreviewGateStatus} == {
        "READY",
        "BLOCKED",
        "PARTIAL",
        "ERROR",
    }
    assert {item.value for item in CrossSurfacePreviewRequestKind} == {
        "INSPECT_HANDOFF",
        "REVIEW_CONTEXT",
        "REVIEW_CONFLICTS",
        "REVIEW_AVAILABILITY",
        "REVIEW_EXPLANATION",
        "CONFIRMATION_REQUIRED_LATER",
        "DEV_FIXTURE_PREVIEW",
        "UNKNOWN_UNAVAILABLE",
    }
    assert {item.value for item in CrossSurfacePreviewContentKind} == {
        "SOURCE_TARGET_SUMMARY",
        "PAYLOAD_SUMMARY",
        "CONTEXT_SUMMARY",
        "CONTINUITY_SUMMARY",
        "CONFLICT_SUMMARY",
        "AVAILABILITY_SUMMARY",
        "EXPLANATION_SUMMARY",
        "NO_EXECUTION_WARNING",
        "DEV_FIXTURE_CONTENT",
        "UNKNOWN_UNAVAILABLE",
    }
    assert {item.value for item in CrossSurfaceConfirmationRequirementKind} == {
        "OPERATOR_REVIEW_REQUIRED_LATER",
        "OPERATOR_CONFIRMATION_REQUIRED_LATER",
        "APPROVAL_REQUIRED_LATER",
        "PERMISSION_REQUIRED_LATER",
        "ROUTE_RUNTIME_REQUIRED_LATER",
        "UI_REQUIRED_LATER",
        "DEV_FIXTURE_REQUIREMENT",
        "UNKNOWN_UNAVAILABLE",
    }
    assert {item.value for item in CrossSurfacePreviewResultStatus} == {
        "PREVIEW_READY_CONTRACT_ONLY",
        "PARTIAL",
        "UNAVAILABLE",
        "BLOCKED",
        "ERROR",
    }
    assert "NOT_PREVIEW_UI" in {
        item.value for item in CrossSurfaceHandoffPreviewTruthBoundary
    }


def test_p2_5_c_reuses_p2_5_b_context_result() -> None:
    result = build_p2_5_c_handoff_preview_result()
    assert isinstance(result, P25CHandoffPreviewResult)
    assert result.dependency_pack == "P2.5-B"
    assert result.handoff_context_result_ref.startswith("p2_5_b_context_result::")
    assert result.preview_gate.dependency_context_result_ref == result.handoff_context_result_ref
    assert result.preview_request.handoff_context_result_ref == result.handoff_context_result_ref
    assert len(result.preview_content_items) >= 1
    assert result.explanation_bundle.explanation_refs


def test_preview_request_builds_and_serializes() -> None:
    request = build_cross_surface_handoff_preview_request(
        handoff_context_result_ref="p2_5_b_context_result::fixture",
    )
    assert request.renders_ui is False
    assert request.asks_real_operator is False
    assert request.records_consent is False
    assert request.executes_handoff is False
    assert request.executes_route is False
    assert request.switches_surface is False
    payload = request.to_canonical_dict()
    assert payload["request_kind"] == request.request_kind.value
    assert_preview_is_not_ui(request)
    assert_preview_request_is_not_operator_prompt(request)


def test_preview_request_rejects_execution_flags() -> None:
    with pytest.raises(AurelShellValidationError):
        CrossSurfaceHandoffPreviewRequest(
            preview_request_id="bad",
            handoff_context_result_ref="ref",
            request_kind=CrossSurfacePreviewRequestKind.DEV_FIXTURE_PREVIEW,
            requested_summary="bad",
            source_surface_id="hq",
            target_surface_id="corp",
            renders_ui=True,
            asks_real_operator=False,
            records_consent=False,
            executes_handoff=False,
            executes_route=False,
            switches_surface=False,
            truth_label="bad",
            limitations=(),
        )


def test_preview_content_builds_and_serializes() -> None:
    content = build_cross_surface_handoff_preview_content(
        content_kind=CrossSurfacePreviewContentKind.CONTEXT_SUMMARY,
        content_label="Context summary",
        source_ref="snapshot_ref",
        context_refs=("ctx1",),
    )
    assert content.is_rendered_ui is False
    assert content.creates_panel is False
    assert content.creates_modal is False
    assert content.executes_action is False
    payload = content.to_canonical_dict()
    assert payload["content_kind"] == "CONTEXT_SUMMARY"


def test_explanation_bundle_is_not_approval() -> None:
    bundle = build_cross_surface_handoff_explanation_bundle(
        handoff_context_result_ref="p2_5_b_context_result::fixture",
        explanation_refs=("exp1",),
        content_refs=("content1",),
        summary="Grouped explanations only",
    )
    assert bundle.is_approval is False
    assert bundle.is_authorization is False
    assert bundle.is_operator_confirmation is False
    assert bundle.executes_handoff is False
    assert bundle.executes_route is False
    assert_explanation_bundle_is_not_approval(bundle)


def test_operator_confirmation_requirement_future_only() -> None:
    requirement = build_cross_surface_operator_confirmation_requirement()
    assert requirement.required_later is True
    assert requirement.records_real_consent is False
    assert requirement.creates_confirmation_ui is False
    assert requirement.activates_approval is False
    assert requirement.enforces_permission is False
    assert_confirmation_requirement_is_not_consent(requirement)


def test_confirmation_intent_boundary_is_active() -> None:
    requirement = build_cross_surface_operator_confirmation_requirement()
    boundary = build_cross_surface_operator_confirmation_intent_boundary(
        confirmation_requirement_ref=requirement.requirement_id,
    )
    assert boundary.boundary_active is True
    assert boundary.prevents_authorization is True
    assert boundary.prevents_permission_decision is True
    assert boundary.prevents_approval_activation is True
    assert boundary.prevents_consent_recording is True
    assert boundary.prevents_operator_prompt is True
    assert boundary.prevents_execution is True
    assert boundary.prevents_route_execution is True
    assert boundary.prevents_surface_switch is True
    assert_confirmation_intent_is_not_authorization(boundary)


def test_preview_result_boundaries_and_no_execution() -> None:
    result = build_p2_5_c_handoff_preview_result()
    preview_result = result.preview_result
    assert preview_result.no_confirmation_boundary_active is True
    assert preview_result.no_execution_boundary_active is True
    assert preview_result.executes_handoff is False
    assert preview_result.is_transition_result is False
    assert preview_result.is_route_result is False
    assert preview_result.is_live_ui is False
    assert preview_result.is_source_of_truth is False
    assert preview_result.renders_preview_ui is False
    assert preview_result.creates_explanation_panel is False
    assert preview_result.creates_confirmation_modal is False
    assert preview_result.records_real_consent is False
    assert preview_result.mutates_runtime is False
    assert preview_result.writes_memory is False
    assert preview_result.writes_trace is False
    assert preview_result.writes_storage is False
    assert_no_confirmation_boundary_is_active(preview_result)
    assert_no_execution_boundary_is_active(preview_result)
    assert_preview_result_is_not_execution(preview_result)


def test_deterministic_serialization() -> None:
    first = build_p2_5_c_handoff_preview_result()
    second = build_p2_5_c_handoff_preview_result()
    assert serialize_p2_5_c_result(first) == serialize_p2_5_c_result(second)


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_5_c_side_effect_proof()
    assert isinstance(proof, P25CSideEffectProof)
    for field_name in (
        "cross_surface_ui_created",
        "preview_ui_created",
        "explanation_panel_ui_created",
        "confirmation_modal_created",
        "operator_confirmation_ui_created",
        "real_operator_consent_recorded",
        "consent_state_created",
        "approval_created",
        "approval_activated",
        "authorization_created",
        "permission_enforcement_created",
        "permission_granted",
        "permission_denied",
        "runtime_blocking_created",
        "custos_integration_created",
        "mneme_integration_created",
        "handoff_execution_created",
        "surface_runtime_switch_created",
        "active_navigation_mutation_created",
        "route_execution_created",
        "route_handler_created",
        "route_runtime_created",
        "command_execution_created",
        "command_router_created",
        "command_handler_created",
        "command_invocation_created",
        "tool_invocation_created",
        "workflow_dispatch_created",
        "api_server_created",
        "http_routes_created",
        "event_bus_created",
        "runtime_events_emitted",
        "memory_written",
        "trace_written",
        "storage_written",
        "runtime_mutated",
        "source_of_truth_created",
        "live_claimed",
        "trace_verified_claimed",
        "release_scope_claimed",
        "product_behavior_claimed",
        "p2_5_d_started",
        "p2_6_started",
        "p2_7_started",
        "p2_10_started",
        "p2_13_started",
    ):
        assert getattr(proof, field_name) is False


def test_p2_5_c_does_not_start_future_work() -> None:
    result = build_p2_5_c_handoff_preview_result()
    assert result.next_pack == "P2.5-D"
    assert result.starts_future_work is False
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert_p2_5_c_does_not_start_future_work(result)


def test_read_only_summary_renders_without_ui_claim() -> None:
    result = build_p2_5_c_handoff_preview_result()
    summary = render_cross_surface_handoff_preview_summary(result)
    assert "P2.5-C" in summary
    assert "Handoff Preview Boundary" in summary
    assert "No-confirmation boundary: True" in summary
    assert "No-execution boundary: True" in summary


def test_pack_result_builds_full_pipeline() -> None:
    result = build_p2_5_c_handoff_preview_result(source_surface_id="hub", target_surface_id="ide")
    assert result.preview_request.source_surface_id == "hub"
    assert result.preview_request.target_surface_id == "ide"
    assert isinstance(result.preview_result, CrossSurfaceHandoffPreviewResult)
    assert isinstance(result.explanation_bundle, CrossSurfaceHandoffExplanationBundle)
    assert isinstance(
        result.confirmation_requirement,
        CrossSurfaceOperatorConfirmationRequirement,
    )
    assert isinstance(
        result.confirmation_intent_boundary,
        CrossSurfaceOperatorConfirmationIntentBoundary,
    )

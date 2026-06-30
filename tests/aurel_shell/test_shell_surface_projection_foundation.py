"""Tests for P2.6-A surface projection / API / event bridge foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.cross_surface_handoff_section_projection import (
    build_p2_5_d_handoff_section_result,
)
from agentic_runtime.aurel_shell.surface_projection_foundation import (
    OFFICIAL_ACTIVE_SURFACE_NAMES,
    P2_5_D_COMMIT_REF,
    P2_5_D_REPORT_PATH,
    P2_6_A_DEPENDENCY_PACK,
    P2_6_A_NEXT_PACK,
    P2_6_A_OFFICIAL_SECTION_NAME,
    P2_6_A_PACK_CHECKPOINT_IDS,
    P2_6_A_PACK_ID,
    P2_6_A_SECTION_ID,
    P26ASideEffectProof,
    P26ASurfaceProjectionResult,
    SurfaceProjectionApiExposureMode,
    SurfaceProjectionAvailabilityStatus,
    SurfaceProjectionEventKind,
    SurfaceProjectionGateStatus,
    SurfaceProjectionKind,
    SurfaceProjectionTruthBoundary,
    assert_api_contract_is_not_server,
    assert_endpoint_schema_is_not_route_handler,
    assert_event_envelope_is_not_event_bus,
    assert_event_stream_descriptor_is_not_live_stream,
    assert_no_event_bus_boundary_is_active,
    assert_no_live_bridge_boundary_is_active,
    assert_no_server_boundary_is_active,
    assert_omni_evidence_is_ignored_by_operator_instruction,
    assert_p2_6_a_does_not_start_future_work,
    assert_p2_6_a_side_effects_all_false,
    assert_projection_availability_is_not_permission,
    assert_projection_is_not_source_of_truth,
    assert_projection_is_not_ui,
    assert_section_gate_depends_on_p2_5_d,
    assert_surface_scope_uses_official_surfaces,
    build_p2_6_a_side_effect_proof,
    build_p2_6_a_surface_projection_result,
    build_surface_projection_api_exposure,
    build_surface_projection_availability,
    build_surface_projection_event_envelope,
    build_surface_projection_event_stream_descriptor,
    build_surface_projection_foundation_result,
    build_surface_projection_gate,
    build_surface_projection_identity,
    build_surface_projection_no_event_bus_boundary,
    build_surface_projection_no_server_boundary,
    build_surface_projection_scope,
    render_surface_projection_contract_summary,
    serialize_p2_6_a_result,
)
from agentic_runtime.aurel_shell.surface_registry import (
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
)


@pytest.fixture(scope="module")
def result() -> P26ASurfaceProjectionResult:
    return build_p2_6_a_surface_projection_result()


# ---------------------------------------------------------------------------
# Gate / dependency tests
# ---------------------------------------------------------------------------


def test_pack_constants_are_p2_6_a() -> None:
    assert P2_6_A_PACK_ID == "P2.6-A"
    assert P2_6_A_SECTION_ID == "P2.6"
    assert P2_6_A_OFFICIAL_SECTION_NAME == "Surface Projection / API / Event Bridge"
    assert P2_6_A_DEPENDENCY_PACK == "P2.5-D"
    assert P2_6_A_NEXT_PACK == "P2.6-B"
    assert P2_6_A_PACK_CHECKPOINT_IDS == (
        "P2.6.0",
        "P2.6.1",
        "P2.6.2",
        "P2.6.3",
        "P2.6.4",
        "P2.6.5",
    )


def test_p2_5_d_dependency_section_seal_represented() -> None:
    section_result = build_p2_5_d_handoff_section_result()
    gate = build_surface_projection_gate(section_result)
    assert gate.dependency_pack == "P2.5-D"
    assert gate.dependency_report_ref == P2_5_D_REPORT_PATH
    assert gate.dependency_commit_ref == P2_5_D_COMMIT_REF
    assert gate.dependency_section_seal_ref
    assert "SEALED_CONTRACT_SCOPE" in gate.dependency_section_seal_ref
    assert gate.dependency_readiness_audit_ref
    assert gate.dependency_contract_scope_demo_ref


def test_p2_5_d_readiness_audit_and_demo_referenced(result: P26ASurfaceProjectionResult) -> None:
    gate = result.projection_gate
    assert "contract_scope=true" in gate.dependency_readiness_audit_ref
    assert gate.dependency_contract_scope_demo_ref


def test_repo_evidence_gate_passed_and_omni_ignored(result: P26ASurfaceProjectionResult) -> None:
    gate = result.projection_gate
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)


def test_gate_rejects_wrong_dependency_pack() -> None:
    gate = build_surface_projection_gate()
    object.__setattr__(gate, "dependency_pack", "P2.4-D")
    with pytest.raises(AurelShellValidationError):
        assert_section_gate_depends_on_p2_5_d(gate)


def test_p2_6_section_title_not_attention_inbox(result: P26ASurfaceProjectionResult) -> None:
    # discarded Attention / Notification / Inbox direction must not appear
    assert result.official_section_name == "Surface Projection / API / Event Bridge"
    blob = serialize_p2_6_a_result(result).lower()
    assert "attention" not in blob
    assert "notification" not in blob
    assert "inbox" not in blob


def test_p2_6_a_does_not_start_future_work(result: P26ASurfaceProjectionResult) -> None:
    assert result.starts_future_work is False
    assert result.next_pack == "P2.6-B"
    proof = result.side_effect_proof
    assert proof.p2_6_b_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False
    assert_p2_6_a_does_not_start_future_work(result)


# ---------------------------------------------------------------------------
# P2.6.0 gate
# ---------------------------------------------------------------------------


def test_projection_gate_builds_and_status_closed_world(result: P26ASurfaceProjectionResult) -> None:
    gate = result.projection_gate
    assert isinstance(gate.gate_status, SurfaceProjectionGateStatus)
    assert gate.gate_status is SurfaceProjectionGateStatus.READY
    assert gate.section_id == "P2.6"
    assert gate.official_section_name == "Surface Projection / API / Event Bridge"
    assert gate.truth_label == SurfaceProjectionTruthBoundary.SECTION_GATE_ONLY.value


def test_gate_serializes_deterministically() -> None:
    a = build_surface_projection_gate()
    b = build_surface_projection_gate()
    assert a.gate_hash == b.gate_hash
    assert json.loads(json.dumps(a.to_canonical_dict()))


# ---------------------------------------------------------------------------
# P2.6.1 identity / scope
# ---------------------------------------------------------------------------


def test_projection_identity_builds(result: P26ASurfaceProjectionResult) -> None:
    identity = result.projection_identity
    assert isinstance(identity.projection_kind, SurfaceProjectionKind)
    assert identity.is_ui is False
    assert identity.is_source_of_truth is False
    assert identity.claims_live is False
    assert identity.claims_trace_verified is False
    assert_projection_is_not_ui(identity)
    assert_projection_is_not_source_of_truth(identity)


def test_projection_kind_closed_world() -> None:
    identity = build_surface_projection_identity()
    assert identity.projection_kind in set(SurfaceProjectionKind)


def test_projection_scope_uses_official_surface_set(result: P26ASurfaceProjectionResult) -> None:
    scope = result.projection_scope
    assert tuple(scope.surface_ids) == tuple(CANONICAL_SURFACE_ORDER)
    assert scope.official_surface_set == OFFICIAL_ACTIVE_SURFACE_NAMES
    assert scope.switches_surface is False
    assert scope.executes_route is False
    assert scope.mutates_navigation is False
    assert_surface_scope_uses_official_surfaces(scope)


def test_official_surface_set_is_seven_lock() -> None:
    assert OFFICIAL_ACTIVE_SURFACE_NAMES == (
        "Aurel CRO",
        "HQ",
        "CORP",
        "HUB",
        "IDE",
        "SYSTEM",
        "Settings",
    )
    assert len(CANONICAL_SURFACE_ORDER) == 7


def test_old_surface_taxonomy_not_active(result: P26ASurfaceProjectionResult) -> None:
    scope = result.projection_scope
    for old in OLD_SURFACE_TAXONOMY:
        assert old not in scope.surface_ids
        assert old not in scope.official_surface_set


def test_scope_switches_surface_rejected() -> None:
    scope = build_surface_projection_scope()
    object.__setattr__(scope, "switches_surface", True)
    with pytest.raises(AurelShellValidationError):
        assert_surface_scope_uses_official_surfaces(scope)


# ---------------------------------------------------------------------------
# P2.6.2 API exposure / no-server boundary
# ---------------------------------------------------------------------------


def test_api_exposure_mode_closed_world(result: P26ASurfaceProjectionResult) -> None:
    exposure = result.api_exposure
    assert exposure.exposure_mode in set(SurfaceProjectionApiExposureMode)
    assert exposure.exposure_mode is (
        SurfaceProjectionApiExposureMode.READ_MODEL_SCHEMA_ONLY
    )


def test_api_exposure_is_not_server(result: P26ASurfaceProjectionResult) -> None:
    exposure = result.api_exposure
    assert exposure.external_access_enabled is False
    assert exposure.http_server_created is False
    assert exposure.http_routes_created is False
    assert exposure.route_handler_created is False
    assert exposure.runtime_handler_created is False
    assert_api_contract_is_not_server(exposure)
    assert_endpoint_schema_is_not_route_handler(exposure)


def test_no_server_boundary_active(result: P26ASurfaceProjectionResult) -> None:
    boundary = result.no_server_boundary
    assert boundary.boundary_active is True
    assert boundary.prevents_api_server is True
    assert boundary.prevents_http_routes is True
    assert boundary.prevents_route_handlers is True
    assert boundary.prevents_external_access is True
    assert boundary.prevents_runtime_handler is True
    assert_no_server_boundary_is_active(boundary)


def test_api_exposure_server_created_rejected() -> None:
    exposure = build_surface_projection_api_exposure()
    object.__setattr__(exposure, "http_server_created", True)
    with pytest.raises(AurelShellValidationError):
        assert_api_contract_is_not_server(exposure)


def test_no_server_boundary_inactive_rejected() -> None:
    boundary = build_surface_projection_no_server_boundary()
    object.__setattr__(boundary, "boundary_active", False)
    with pytest.raises(AurelShellValidationError):
        assert_no_server_boundary_is_active(boundary)


# ---------------------------------------------------------------------------
# P2.6.3 event envelope / stream / no-event-bus boundary
# ---------------------------------------------------------------------------


def test_event_envelope_kind_closed_world(result: P26ASurfaceProjectionResult) -> None:
    envelope = result.event_envelope
    assert envelope.event_kind in set(SurfaceProjectionEventKind)
    assert envelope.is_runtime_event is False
    assert envelope.emits_runtime_event is False
    assert envelope.writes_trace is False
    assert_event_envelope_is_not_event_bus(envelope)


def test_event_envelope_trace_ref_is_report_reference(result: P26ASurfaceProjectionResult) -> None:
    # trace_ref is a report/evidence reference only, not a trace write
    assert result.event_envelope.trace_ref == P2_5_D_REPORT_PATH
    assert result.event_envelope.writes_trace is False


def test_event_stream_descriptor_is_not_live_stream(result: P26ASurfaceProjectionResult) -> None:
    descriptor = result.event_stream_descriptor
    assert descriptor.is_live_stream is False
    assert descriptor.websocket_created is False
    assert descriptor.sse_created is False
    assert descriptor.subscriber_created is False
    assert descriptor.dispatcher_created is False
    assert descriptor.runtime_bridge_created is False
    assert_event_stream_descriptor_is_not_live_stream(descriptor)


def test_no_event_bus_boundary_active(result: P26ASurfaceProjectionResult) -> None:
    boundary = result.no_event_bus_boundary
    assert boundary.boundary_active is True
    assert boundary.prevents_event_bus is True
    assert boundary.prevents_event_dispatch is True
    assert boundary.prevents_live_stream is True
    assert boundary.prevents_websocket is True
    assert boundary.prevents_sse is True
    assert boundary.prevents_runtime_bridge is True
    assert boundary.prevents_runtime_dispatch is True
    assert_no_event_bus_boundary_is_active(boundary)


def test_event_envelope_emits_runtime_event_rejected() -> None:
    envelope = build_surface_projection_event_envelope()
    object.__setattr__(envelope, "emits_runtime_event", True)
    with pytest.raises(AurelShellValidationError):
        assert_event_envelope_is_not_event_bus(envelope)


def test_event_stream_websocket_rejected() -> None:
    descriptor = build_surface_projection_event_stream_descriptor()
    object.__setattr__(descriptor, "websocket_created", True)
    with pytest.raises(AurelShellValidationError):
        assert_event_stream_descriptor_is_not_live_stream(descriptor)


# ---------------------------------------------------------------------------
# P2.6.4 availability / unavailable-state
# ---------------------------------------------------------------------------


def test_availability_status_closed_world(result: P26ASurfaceProjectionResult) -> None:
    availability = result.availability
    assert availability.availability_status in set(SurfaceProjectionAvailabilityStatus)
    assert availability.availability_status is (
        SurfaceProjectionAvailabilityStatus.AVAILABLE_CONTRACT_ONLY
    )


def test_availability_is_not_permission(result: P26ASurfaceProjectionResult) -> None:
    availability = result.availability
    assert availability.grants_permission is False
    assert availability.denies_permission is False
    assert availability.activates_approval is False
    assert availability.enforces_policy is False
    assert_projection_availability_is_not_permission(availability)


def test_availability_unavailable_capabilities_and_future_packs(result: P26ASurfaceProjectionResult) -> None:
    availability = result.availability
    unavailable = availability.unavailable_capabilities
    for cap in (
        "live API server",
        "HTTP routes",
        "event bus",
        "runtime bridge",
        "CLI binding",
        "Shell execution binding",
        "TUI binding",
        "P2.7 binding",
        "P2.10 multi-client behavior",
        "P2.13 operator-testable product behavior",
        "trace write",
        "memory write",
        "storage write",
        "runtime mutation",
    ):
        assert cap in unavailable
    assert "P2.6-B" in availability.future_pack_refs
    assert "P2.7" in availability.future_pack_refs
    assert "P2.10" in availability.future_pack_refs
    assert "P2.13" in availability.future_pack_refs
    # serializes
    assert json.loads(json.dumps(availability.to_canonical_dict()))


def test_availability_grants_permission_rejected() -> None:
    availability = build_surface_projection_availability()
    object.__setattr__(availability, "grants_permission", True)
    with pytest.raises(AurelShellValidationError):
        assert_projection_availability_is_not_permission(availability)


# ---------------------------------------------------------------------------
# P2.6.5 foundation result / no-live-bridge boundary
# ---------------------------------------------------------------------------


def test_foundation_result_no_live_bridge(result: P26ASurfaceProjectionResult) -> None:
    foundation = result.foundation_result
    assert foundation.no_live_bridge_boundary_active is True
    assert foundation.is_live_bridge is False
    assert foundation.creates_api_server is False
    assert foundation.creates_event_bus is False
    assert foundation.creates_runtime_dispatch is False
    assert foundation.creates_cli_binding is False
    assert foundation.creates_product_behavior is False
    assert_no_live_bridge_boundary_is_active(foundation)


def test_foundation_result_serializes_deterministically() -> None:
    a = build_surface_projection_foundation_result()
    b = build_surface_projection_foundation_result()
    assert a.foundation_result_hash == b.foundation_result_hash


def test_foundation_live_bridge_rejected() -> None:
    foundation = build_surface_projection_foundation_result()
    object.__setattr__(foundation, "is_live_bridge", True)
    with pytest.raises(AurelShellValidationError):
        assert_no_live_bridge_boundary_is_active(foundation)


def test_result_builds_and_serializes(result: P26ASurfaceProjectionResult) -> None:
    blob = serialize_p2_6_a_result(result)
    loaded = json.loads(blob)
    assert loaded["pack_id"] == "P2.6-A"
    assert loaded["section_id"] == "P2.6"
    assert loaded["next_pack"] == "P2.6-B"
    # deterministic
    assert serialize_p2_6_a_result(result) == blob


def test_render_summary_is_text(result: P26ASurfaceProjectionResult) -> None:
    summary = render_surface_projection_contract_summary(result)
    assert "P2.6 Surface Projection / API / Event Bridge" in summary
    assert "pack=P2.6-A" in summary
    assert "no_live_bridge=true" in summary
    assert "next=P2.6-B" in summary


# ---------------------------------------------------------------------------
# Side-effect / no-authority proof
# ---------------------------------------------------------------------------


def test_side_effect_proof_all_false(result: P26ASurfaceProjectionResult) -> None:
    proof = result.side_effect_proof
    assert isinstance(proof, P26ASideEffectProof)
    from dataclasses import fields

    for field in fields(proof):
        assert getattr(proof, field.name) is False
    assert_p2_6_a_side_effects_all_false(proof)


def test_side_effect_proof_truthy_rejected() -> None:
    proof = build_p2_6_a_side_effect_proof()
    object.__setattr__(proof, "api_server_created", True)
    with pytest.raises(AurelShellValidationError):
        assert_p2_6_a_side_effects_all_false(proof)


def test_result_claims_are_all_false(result: P26ASurfaceProjectionResult) -> None:
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False


def test_truth_labels_carry_not_live_and_not_release(result: P26ASurfaceProjectionResult) -> None:
    labels = result.truth_labels
    assert SurfaceProjectionTruthBoundary.NOT_LIVE.value in labels
    assert SurfaceProjectionTruthBoundary.NOT_TRACE_VERIFIED.value in labels
    assert SurfaceProjectionTruthBoundary.NOT_RELEASE_SCOPE.value in labels
    assert SurfaceProjectionTruthBoundary.NO_LIVE_BRIDGE_BOUNDARY.value in labels


def test_canonical_surface_ids_match_registry(result: P26ASurfaceProjectionResult) -> None:
    assert tuple(result.canonical_surface_ids) == tuple(CANONICAL_SURFACE_ORDER)

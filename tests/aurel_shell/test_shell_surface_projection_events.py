"""Tests for P2.6-C surface projection event bridge boundary contracts."""

from __future__ import annotations

import json
from dataclasses import fields

from agentic_runtime.aurel_shell.surface_projection_events import (
    P2_6_B_IMPLEMENTATION_COMMIT_REF,
    P2_6_B_REPORT_PATH,
    P2_6_C_DEPENDENCY_PACK,
    P2_6_C_NEXT_PACK,
    P2_6_C_OFFICIAL_SECTION_NAME,
    P2_6_C_PACK_CHECKPOINT_IDS,
    P2_6_C_PACK_ID,
    P2_6_C_SECTION_ID,
    P26CSideEffectProof,
    P26CSurfaceProjectionEventBridgeResult,
    SurfaceProjectionDeliveryMode,
    SurfaceProjectionEventBridgeGateStatus,
    SurfaceProjectionEventBridgeTruthBoundary,
    SurfaceProjectionEventKind,
    SurfaceProjectionSubscriptionMode,
    assert_causality_ref_is_not_trace_write,
    assert_delivery_descriptor_is_not_delivery_channel,
    assert_event_envelope_is_not_runtime_event,
    assert_event_envelope_registry_is_not_dispatcher,
    assert_event_kind_catalog_is_not_event_bus,
    assert_evidence_ref_is_not_trace_verified,
    assert_no_live_stream_boundary_is_active,
    assert_no_runtime_dispatch_boundary_is_active,
    assert_p2_6_c_does_not_start_future_work,
    assert_p2_6_c_side_effects_all_false,
    assert_subscription_descriptor_is_not_subscriber_runtime,
    build_p2_6_c_side_effect_proof,
    build_p2_6_c_surface_projection_event_bridge_result,
    build_surface_projection_delivery_descriptor,
    build_surface_projection_event_bridge_boundary_result,
    build_surface_projection_event_bridge_gate,
    build_surface_projection_event_causality_ref,
    build_surface_projection_event_correlation_ref,
    build_surface_projection_event_envelope_entry,
    build_surface_projection_event_envelope_registry,
    build_surface_projection_event_evidence_ref,
    build_surface_projection_event_kind_catalog,
    build_surface_projection_event_kind_spec,
    build_surface_projection_event_payload_schema_ref,
    build_surface_projection_event_source_target_mapping,
    build_surface_projection_no_live_stream_boundary,
    build_surface_projection_no_runtime_dispatch_boundary,
    build_surface_projection_subscription_descriptor,
    render_surface_projection_event_contract_summary,
    serialize_p2_6_c_result,
)
from agentic_runtime.aurel_shell.surface_projection_schemas import P2_6_B_PACK_ID
from agentic_runtime.aurel_shell.surface_registry import (
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
)


def test_pack_constants_are_p2_6_c() -> None:
    assert P2_6_C_PACK_ID == "P2.6-C"
    assert P2_6_C_SECTION_ID == "P2.6"
    assert P2_6_C_OFFICIAL_SECTION_NAME == "Surface Projection / API / Event Bridge"
    assert P2_6_C_DEPENDENCY_PACK == "P2.6-B"
    assert P2_6_C_NEXT_PACK == "P2.6-D"
    assert P2_6_C_PACK_CHECKPOINT_IDS == (
        "P2.6.11",
        "P2.6.12",
        "P2.6.13",
        "P2.6.14",
        "P2.6.15",
    )


def test_p2_6_b_dependency_gate_represented() -> None:
    gate = build_surface_projection_event_bridge_gate()
    assert gate.dependency_pack == P2_6_B_PACK_ID
    assert gate.dependency_report_ref == P2_6_B_REPORT_PATH
    assert gate.dependency_commit_ref == P2_6_B_IMPLEMENTATION_COMMIT_REF
    assert gate.dependency_schema_expansion_result_ref
    assert gate.dependency_no_live_endpoint_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P26BSideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status is SurfaceProjectionEventBridgeGateStatus.READY


def test_p2_6_section_title_not_attention_inbox() -> None:
    result = build_p2_6_c_surface_projection_event_bridge_result()
    assert result.official_section_name == "Surface Projection / API / Event Bridge"
    blob = serialize_p2_6_c_result(result).lower()
    assert "attention" not in blob
    assert "notification" not in blob
    assert "inbox" not in blob


def test_p2_6_c_does_not_start_future_work() -> None:
    result = build_p2_6_c_surface_projection_event_bridge_result()
    assert result.next_pack == "P2.6-D"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_6_d_started is False
    assert result.side_effect_proof.p2_7_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_6_c_does_not_start_future_work(result)


def test_event_bridge_gate_status_closed_world() -> None:
    gate = build_surface_projection_event_bridge_gate()
    assert gate.gate_status in set(SurfaceProjectionEventBridgeGateStatus)
    assert gate.truth_label == (
        SurfaceProjectionEventBridgeTruthBoundary.EVENT_BRIDGE_GATE_ONLY.value
    )


def test_event_kind_closed_world() -> None:
    assert {kind.value for kind in SurfaceProjectionEventKind} == {
        "SURFACE_REGISTRY_PROJECTED_CONTRACT",
        "LOCAL_NAVIGATION_PROJECTED_CONTRACT",
        "WINDOW_STATE_PROJECTED_CONTRACT",
        "COMMAND_PALETTE_PROJECTED_CONTRACT",
        "CROSS_SURFACE_HANDOFF_PROJECTED_CONTRACT",
        "SECTION_SEAL_PROJECTED_CONTRACT",
        "SCHEMA_EXPANSION_PROJECTED_CONTRACT",
        "DEV_FIXTURE_EVENT",
        "UNKNOWN_UNAVAILABLE",
    }


def test_event_envelope_registry_builds_and_is_not_runtime() -> None:
    registry = build_surface_projection_event_envelope_registry()
    assert registry.section_id == "P2.6"
    assert registry.created_for_pack == "P2.6-C"
    assert len(registry.entries) == len(SurfaceProjectionEventKind)
    assert registry.is_event_bus is False
    assert registry.is_dispatcher is False
    assert registry.emits_runtime_events is False
    assert_event_envelope_registry_is_not_dispatcher(registry)
    for entry in registry.entries:
        assert entry.available_as_runtime_event is False
        assert_event_envelope_is_not_runtime_event(entry)


def test_event_registry_and_catalog_serialize_deterministically() -> None:
    catalog_a = build_surface_projection_event_kind_catalog()
    catalog_b = build_surface_projection_event_kind_catalog()
    registry_a = build_surface_projection_event_envelope_registry(catalog_a)
    registry_b = build_surface_projection_event_envelope_registry(catalog_b)
    assert catalog_a.catalog_hash == catalog_b.catalog_hash
    assert registry_a.registry_hash == registry_b.registry_hash
    assert json.loads(json.dumps(registry_a.to_canonical_dict()))


def test_event_kind_catalog_builds_and_is_not_bus_or_dispatcher() -> None:
    catalog = build_surface_projection_event_kind_catalog()
    assert catalog.event_kinds == tuple(SurfaceProjectionEventKind)
    assert len(catalog.event_kind_specs) == len(SurfaceProjectionEventKind)
    assert catalog.is_event_bus is False
    assert catalog.is_dispatcher is False
    assert_event_kind_catalog_is_not_event_bus(catalog)
    spec = build_surface_projection_event_kind_spec(
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    )
    assert spec.is_runtime_event is False
    assert spec.emits_runtime_event is False


def test_payload_schema_ref_points_to_p2_6_b_contract() -> None:
    ref = build_surface_projection_event_payload_schema_ref(
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    )
    assert ref.source_pack == "P2.6-B"
    assert ref.source_schema_ref.startswith("P2.6-B:")
    assert ref.is_payload_execution is False
    assert ref.mutates_payload is False


def test_source_target_mapping_uses_official_surfaces_without_switching() -> None:
    mapping = build_surface_projection_event_source_target_mapping(
        SurfaceProjectionEventKind.LOCAL_NAVIGATION_PROJECTED_CONTRACT
    )
    assert mapping.source_surface_ids == CANONICAL_SURFACE_ORDER
    assert mapping.target_surface_ids == CANONICAL_SURFACE_ORDER
    assert mapping.official_surface_set == (
        "Aurel CRO",
        "HQ",
        "CORP",
        "HUB",
        "IDE",
        "SYSTEM",
        "Settings",
    )
    assert mapping.switches_surface is False
    assert mapping.executes_route is False
    assert mapping.mutates_navigation is False


def test_old_surface_taxonomy_not_active() -> None:
    result = build_p2_6_c_surface_projection_event_bridge_result()
    for mapping in result.source_target_mappings:
        for old_surface in OLD_SURFACE_TAXONOMY:
            assert old_surface not in mapping.source_surface_ids
            assert old_surface not in mapping.target_surface_ids
            assert old_surface not in mapping.official_surface_set


def test_causality_correlation_evidence_refs_do_not_write_trace_or_link_runtime() -> None:
    causality = build_surface_projection_event_causality_ref()
    correlation = build_surface_projection_event_correlation_ref()
    evidence = build_surface_projection_event_evidence_ref()
    assert causality.writes_trace is False
    assert causality.creates_trace_event is False
    assert causality.claims_trace_verified is False
    assert correlation.runtime_link_created is False
    assert correlation.mutates_runtime_context is False
    assert evidence.claims_trace_verified is False
    assert evidence.writes_trace is False
    assert_causality_ref_is_not_trace_write(causality)
    assert_evidence_ref_is_not_trace_verified(evidence)


def test_refs_serialize_deterministically() -> None:
    assert (
        build_surface_projection_event_causality_ref().causality_hash
        == build_surface_projection_event_causality_ref().causality_hash
    )
    assert (
        build_surface_projection_event_correlation_ref().correlation_hash
        == build_surface_projection_event_correlation_ref().correlation_hash
    )
    assert (
        build_surface_projection_event_evidence_ref().evidence_hash
        == build_surface_projection_event_evidence_ref().evidence_hash
    )


def test_subscription_and_delivery_descriptors_are_contract_only() -> None:
    subscription = build_surface_projection_subscription_descriptor()
    delivery = build_surface_projection_delivery_descriptor()
    assert subscription.subscription_mode is SurfaceProjectionSubscriptionMode.CONTRACT_ONLY
    assert subscription.creates_subscriber_runtime is False
    assert subscription.creates_subscription_runtime is False
    assert delivery.delivery_mode is SurfaceProjectionDeliveryMode.CONTRACT_ONLY
    assert delivery.creates_delivery_channel is False
    assert delivery.creates_delivery_runtime is False
    assert delivery.sends_message is False
    assert_subscription_descriptor_is_not_subscriber_runtime(subscription)
    assert_delivery_descriptor_is_not_delivery_channel(delivery)


def test_no_live_stream_boundary_active() -> None:
    boundary = build_surface_projection_no_live_stream_boundary()
    assert boundary.boundary_active is True
    assert boundary.prevents_websocket is True
    assert boundary.prevents_sse is True
    assert boundary.prevents_live_stream is True
    assert boundary.prevents_subscriber_runtime is True
    assert boundary.prevents_delivery_runtime is True
    assert_no_live_stream_boundary_is_active(boundary)


def test_no_runtime_dispatch_boundary_active() -> None:
    boundary = build_surface_projection_no_runtime_dispatch_boundary()
    assert boundary.boundary_active is True
    assert boundary.prevents_event_bus is True
    assert boundary.prevents_event_dispatcher is True
    assert boundary.prevents_event_dispatch is True
    assert boundary.prevents_runtime_event_emission is True
    assert boundary.prevents_runtime_bridge is True
    assert boundary.prevents_runtime_dispatch is True
    assert boundary.prevents_api_event_bridge_runtime is True
    assert boundary.prevents_trace_write is True
    assert_no_runtime_dispatch_boundary_is_active(boundary)


def test_event_bridge_boundary_result_has_no_runtime_creation() -> None:
    result = build_surface_projection_event_bridge_boundary_result()
    assert result.creates_event_bus is False
    assert result.creates_event_dispatcher is False
    assert result.creates_event_dispatch is False
    assert result.creates_subscriber_runtime is False
    assert result.creates_delivery_runtime is False
    assert result.creates_live_stream is False
    assert result.creates_runtime_event_emission is False
    assert result.creates_runtime_bridge is False
    assert result.creates_runtime_dispatch is False
    assert result.creates_api_event_bridge_runtime is False
    assert result.writes_trace is False
    assert result.writes_memory is False
    assert result.writes_storage is False
    assert result.creates_cli_binding is False
    assert result.creates_product_behavior is False
    assert_no_live_stream_boundary_is_active(result.no_live_stream_boundary)
    assert_no_runtime_dispatch_boundary_is_active(result.no_runtime_dispatch_boundary)


def test_pack_result_serializes_and_renders_summary() -> None:
    result = build_p2_6_c_surface_projection_event_bridge_result()
    assert isinstance(result, P26CSurfaceProjectionEventBridgeResult)
    serialized = serialize_p2_6_c_result(result)
    assert json.loads(serialized)
    assert (
        result.result_hash
        == build_p2_6_c_surface_projection_event_bridge_result().result_hash
    )
    summary = render_surface_projection_event_contract_summary(result)
    assert "P2.6-C" in summary
    assert "no_live_stream=True" in summary
    assert "no_runtime_dispatch=True" in summary


def test_truth_labels_include_required_boundaries() -> None:
    result = build_p2_6_c_surface_projection_event_bridge_result()
    labels = set(result.truth_labels)
    assert SurfaceProjectionEventBridgeTruthBoundary.NOT_LIVE.value in labels
    assert SurfaceProjectionEventBridgeTruthBoundary.NOT_TRACE_VERIFIED.value in labels
    assert SurfaceProjectionEventBridgeTruthBoundary.NOT_PRODUCT_BEHAVIOR.value in labels
    assert SurfaceProjectionEventBridgeTruthBoundary.NO_LIVE_STREAM_BOUNDARY.value in labels
    assert (
        SurfaceProjectionEventBridgeTruthBoundary.NO_RUNTIME_DISPATCH_BOUNDARY.value
        in labels
    )
    assert SurfaceProjectionEventBridgeTruthBoundary.NO_TRACE_WRITE_BOUNDARY.value in labels


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_6_c_side_effect_proof()
    assert isinstance(proof, P26CSideEffectProof)
    for field in fields(proof):
        assert getattr(proof, field.name) is False
    assert_p2_6_c_side_effects_all_false(proof)


def test_result_side_effects_and_claims_all_false() -> None:
    result = build_p2_6_c_surface_projection_event_bridge_result()
    proof = result.side_effect_proof
    assert proof.event_bus_created is False
    assert proof.event_dispatcher_created is False
    assert proof.event_subscriber_runtime_created is False
    assert proof.subscription_runtime_created is False
    assert proof.delivery_runtime_created is False
    assert proof.delivery_channel_created is False
    assert proof.websocket_stream_created is False
    assert proof.sse_stream_created is False
    assert proof.live_stream_created is False
    assert proof.runtime_event_emitted is False
    assert proof.runtime_bridge_created is False
    assert proof.runtime_dispatch_created is False
    assert proof.api_event_bridge_runtime_created is False
    assert proof.trace_written is False
    assert proof.memory_written is False
    assert proof.storage_written is False
    assert proof.projection_ui_created is False
    assert proof.api_server_created is False
    assert proof.http_routes_created is False
    assert proof.route_handler_created is False
    assert proof.live_endpoint_created is False
    assert proof.live_query_execution_created is False
    assert proof.surface_switch_created is False
    assert proof.navigation_mutation_created is False
    assert proof.route_execution_created is False
    assert proof.command_execution_created is False
    assert proof.command_router_created is False
    assert proof.command_handler_created is False
    assert proof.workflow_dispatch_created is False
    assert proof.tool_invocation_created is False
    assert proof.cli_binding_created is False
    assert proof.shell_execution_binding_created is False
    assert proof.tui_binding_created is False
    assert proof.approval_created is False
    assert proof.approval_activated is False
    assert proof.authorization_created is False
    assert proof.permission_enforcement_created is False
    assert proof.permission_granted is False
    assert proof.permission_denied is False
    assert proof.custos_integration_created is False
    assert proof.mneme_integration_created is False
    assert proof.runtime_mutated is False
    assert proof.source_of_truth_created is False
    assert proof.live_claimed is False
    assert proof.trace_verified_claimed is False
    assert proof.release_scope_claimed is False
    assert proof.product_behavior_claimed is False
    assert proof.p2_6_d_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False

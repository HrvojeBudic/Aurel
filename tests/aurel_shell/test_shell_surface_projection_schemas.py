"""Tests for P2.6-B surface projection schema expansion contracts."""

from __future__ import annotations

import json
from dataclasses import fields

from agentic_runtime.aurel_shell.surface_projection_schemas import (
    P2_6_A_COMMIT_REF,
    P2_6_A_REPORT_PATH,
    P2_6_B_DEPENDENCY_PACK,
    P2_6_B_NEXT_PACK,
    P2_6_B_OFFICIAL_SECTION_NAME,
    P2_6_B_PACK_CHECKPOINT_IDS,
    P2_6_B_PACK_ID,
    P2_6_B_SECTION_ID,
    P26BSideEffectProof,
    P26BSurfaceProjectionSchemaResult,
    SurfaceProjectionQueryMode,
    SurfaceProjectionResponseStatus,
    SurfaceProjectionSchemaGateStatus,
    SurfaceProjectionSchemaKind,
    SurfaceProjectionSchemaTruthBoundary,
    assert_error_envelope_is_not_runtime_error_handler,
    assert_filter_sort_pagination_do_not_execute,
    assert_no_live_endpoint_boundary_is_active,
    assert_p2_6_b_does_not_start_future_work,
    assert_p2_6_b_side_effects_all_false,
    assert_query_contract_is_not_live_query,
    assert_response_envelope_is_not_http_response,
    assert_schema_inventory_is_not_storage,
    assert_schema_registry_is_not_source_of_truth,
    assert_surface_schema_is_not_ui,
    build_default_surface_projection_schemas,
    build_p2_6_b_side_effect_proof,
    build_p2_6_b_surface_projection_schema_result,
    build_surface_projection_error_envelope,
    build_surface_projection_filter_contract,
    build_surface_projection_no_live_endpoint_boundary,
    build_surface_projection_pagination_contract,
    build_surface_projection_query_contract,
    build_surface_projection_read_model_registry,
    build_surface_projection_schema_gate,
    build_surface_projection_schema_inventory,
    build_surface_projection_schema_version,
    build_surface_projection_sort_contract,
    build_surface_specific_projection_schema,
    render_surface_projection_schema_contract_summary,
    serialize_p2_6_b_result,
)
from agentic_runtime.aurel_shell.surface_registry import (
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
)


def test_pack_constants_are_p2_6_b() -> None:
    assert P2_6_B_PACK_ID == "P2.6-B"
    assert P2_6_B_SECTION_ID == "P2.6"
    assert P2_6_B_OFFICIAL_SECTION_NAME == "Surface Projection / API / Event Bridge"
    assert P2_6_B_DEPENDENCY_PACK == "P2.6-A"
    assert P2_6_B_NEXT_PACK == "P2.6-C"
    assert P2_6_B_PACK_CHECKPOINT_IDS == (
        "P2.6.6",
        "P2.6.7",
        "P2.6.8",
        "P2.6.9",
        "P2.6.10",
    )


def test_p2_6_a_dependency_gate_represented() -> None:
    gate = build_surface_projection_schema_gate()
    assert gate.dependency_pack == "P2.6-A"
    assert gate.dependency_report_ref == P2_6_A_REPORT_PATH
    assert gate.dependency_commit_ref == P2_6_A_COMMIT_REF
    assert gate.dependency_foundation_result_ref
    assert gate.dependency_no_server_boundary_ref
    assert gate.dependency_no_event_bus_boundary_ref
    assert gate.dependency_side_effect_proof_ref == "P26ASideEffectProof:all_false"
    assert gate.repo_evidence_gate_passed is True
    assert gate.omni_evidence_required is False
    assert gate.omni_evidence_ignored_by_operator_instruction is True
    assert gate.gate_status is SurfaceProjectionSchemaGateStatus.READY


def test_p2_6_section_title_not_attention_inbox() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    assert result.official_section_name == "Surface Projection / API / Event Bridge"
    blob = serialize_p2_6_b_result(result).lower()
    assert "attention" not in blob
    assert "notification" not in blob
    assert "inbox" not in blob


def test_p2_6_b_does_not_start_future_work() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    assert result.next_pack == "P2.6-C"
    assert result.starts_future_work is False
    assert result.side_effect_proof.p2_6_c_started is False
    assert result.side_effect_proof.p2_7_started is False
    assert result.side_effect_proof.p2_10_started is False
    assert result.side_effect_proof.p2_13_started is False
    assert_p2_6_b_does_not_start_future_work(result)


def test_schema_gate_status_closed_world() -> None:
    gate = build_surface_projection_schema_gate()
    assert gate.gate_status in set(SurfaceProjectionSchemaGateStatus)
    assert gate.truth_label == SurfaceProjectionSchemaTruthBoundary.SCHEMA_GATE_ONLY


def test_read_model_registry_builds_and_is_not_source_of_truth() -> None:
    registry = build_surface_projection_read_model_registry()
    assert registry.section_id == "P2.6"
    assert registry.created_for_pack == "P2.6-B"
    assert len(registry.entries) == len(SurfaceProjectionSchemaKind)
    assert registry.duplicates_source_of_truth is False
    assert registry.is_source_of_truth is False
    assert registry.is_storage is False
    assert_schema_registry_is_not_source_of_truth(registry)


def test_read_model_registry_serializes_deterministically() -> None:
    a = build_surface_projection_read_model_registry()
    b = build_surface_projection_read_model_registry()
    assert a.registry_hash == b.registry_hash
    assert json.loads(json.dumps(a.to_canonical_dict()))


def test_schema_inventory_builds_and_is_not_storage() -> None:
    inventory = build_surface_projection_schema_inventory()
    assert inventory.section_id == "P2.6"
    assert inventory.created_for_pack == "P2.6-B"
    assert len(inventory.schema_versions) == len(SurfaceProjectionSchemaKind)
    assert inventory.missing_schemas == ()
    assert inventory.duplicates_source_of_truth is False
    assert inventory.is_storage is False
    assert_schema_inventory_is_not_storage(inventory)


def test_schema_version_builds_deterministically() -> None:
    version = build_surface_projection_schema_version(
        SurfaceProjectionSchemaKind.SURFACE_REGISTRY_SCHEMA
    )
    assert version.schema_kind is SurfaceProjectionSchemaKind.SURFACE_REGISTRY_SCHEMA
    assert version.compatible_pack == "P2.6-B"
    assert version.breaking_change is False
    assert version.version_hash


def test_surface_schema_kind_closed_world() -> None:
    assert {kind.value for kind in SurfaceProjectionSchemaKind} == {
        "SURFACE_REGISTRY_SCHEMA",
        "LOCAL_NAVIGATION_SCHEMA",
        "WINDOW_STATE_SCHEMA",
        "COMMAND_PALETTE_SCHEMA",
        "CROSS_SURFACE_HANDOFF_SCHEMA",
        "SECTION_SEAL_SCHEMA",
        "DEV_FIXTURE_SCHEMA",
        "UNKNOWN_UNAVAILABLE",
    }


def test_default_surface_schemas_represent_required_schema_kinds() -> None:
    schemas = build_default_surface_projection_schemas()
    kinds = {schema.schema_kind for schema in schemas}
    assert kinds == set(SurfaceProjectionSchemaKind)
    assert SurfaceProjectionSchemaKind.SURFACE_REGISTRY_SCHEMA in kinds
    assert SurfaceProjectionSchemaKind.LOCAL_NAVIGATION_SCHEMA in kinds
    assert SurfaceProjectionSchemaKind.WINDOW_STATE_SCHEMA in kinds
    assert SurfaceProjectionSchemaKind.COMMAND_PALETTE_SCHEMA in kinds
    assert SurfaceProjectionSchemaKind.CROSS_SURFACE_HANDOFF_SCHEMA in kinds
    assert SurfaceProjectionSchemaKind.SECTION_SEAL_SCHEMA in kinds


def test_surface_specific_schema_uses_official_surfaces_and_refs() -> None:
    schema = build_surface_specific_projection_schema(
        SurfaceProjectionSchemaKind.SURFACE_REGISTRY_SCHEMA
    )
    assert schema.surface_ids == CANONICAL_SURFACE_ORDER
    assert schema.official_surface_set == (
        "Aurel CRO",
        "HQ",
        "CORP",
        "HUB",
        "IDE",
        "SYSTEM",
        "Settings",
    )
    assert schema.source_contract_refs
    assert schema.required_fields
    assert schema.optional_fields
    assert schema.duplicates_source_of_truth is False
    assert schema.is_ui_schema is False
    assert schema.is_product_schema is False
    assert schema.mutates_state is False
    assert_surface_schema_is_not_ui(schema)


def test_old_surface_taxonomy_not_active() -> None:
    schemas = build_default_surface_projection_schemas()
    for schema in schemas:
        for old_surface in OLD_SURFACE_TAXONOMY:
            assert old_surface not in schema.surface_ids
            assert old_surface not in schema.official_surface_set


def test_response_envelope_is_not_live_http_response() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    envelope = result.response_envelope
    assert envelope.status is SurfaceProjectionResponseStatus.OK_CONTRACT_ONLY
    assert envelope.is_http_response is False
    assert envelope.requires_server is False
    assert envelope.requires_route_handler is False
    assert_response_envelope_is_not_http_response(envelope)


def test_error_envelope_is_not_runtime_error_handler() -> None:
    envelope = build_surface_projection_error_envelope()
    assert envelope.status is SurfaceProjectionResponseStatus.ERROR_CONTRACT_ONLY
    assert envelope.is_runtime_error_handler is False
    assert envelope.throws_exception is False
    assert envelope.writes_trace is False
    assert_error_envelope_is_not_runtime_error_handler(envelope)


def test_envelopes_serialize_deterministically() -> None:
    a = build_p2_6_b_surface_projection_schema_result().response_envelope
    b = build_p2_6_b_surface_projection_schema_result().response_envelope
    assert a.envelope_hash == b.envelope_hash
    error_a = build_surface_projection_error_envelope()
    error_b = build_surface_projection_error_envelope()
    assert error_a.envelope_hash == error_b.envelope_hash


def test_query_filter_sort_pagination_contracts_are_static_grammar() -> None:
    filter_contract = build_surface_projection_filter_contract()
    sort_contract = build_surface_projection_sort_contract()
    pagination_contract = build_surface_projection_pagination_contract()
    query = build_surface_projection_query_contract(
        filter_contract,
        sort_contract,
        pagination_contract,
    )
    assert query.query_mode is SurfaceProjectionQueryMode.CONTRACT_ONLY
    assert query.executes_live_query is False
    assert query.queries_runtime_state is False
    assert query.queries_database is False
    assert query.queries_storage is False
    assert filter_contract.executes_filter is False
    assert filter_contract.filters_runtime_state is False
    assert filter_contract.filters_database is False
    assert sort_contract.executes_sort is False
    assert sort_contract.sorts_runtime_state is False
    assert sort_contract.sorts_database is False
    assert pagination_contract.executes_pagination is False
    assert pagination_contract.paginates_runtime_state is False
    assert pagination_contract.paginates_database is False
    assert_query_contract_is_not_live_query(query)
    assert_filter_sort_pagination_do_not_execute(
        filter_contract=filter_contract,
        sort_contract=sort_contract,
        pagination_contract=pagination_contract,
    )


def test_query_contract_serializes_deterministically() -> None:
    a = build_surface_projection_query_contract()
    b = build_surface_projection_query_contract()
    assert a.contract_hash == b.contract_hash
    assert json.loads(json.dumps(a.to_canonical_dict()))


def test_no_live_endpoint_boundary_active() -> None:
    boundary = build_surface_projection_no_live_endpoint_boundary()
    assert boundary.boundary_active is True
    assert boundary.prevents_api_server is True
    assert boundary.prevents_http_routes is True
    assert boundary.prevents_route_handlers is True
    assert boundary.prevents_live_endpoint is True
    assert boundary.prevents_live_query is True
    assert boundary.prevents_database_query_runtime is True
    assert boundary.prevents_storage_query_runtime is True
    assert boundary.prevents_runtime_bridge is True
    assert_no_live_endpoint_boundary_is_active(boundary)


def test_schema_expansion_result_has_no_live_runtime_creation() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    expansion = result.schema_expansion_result
    assert expansion.creates_api_server is False
    assert expansion.creates_http_routes is False
    assert expansion.creates_route_handlers is False
    assert expansion.creates_live_endpoint is False
    assert expansion.creates_live_query is False
    assert expansion.creates_database_query_runtime is False
    assert expansion.creates_event_bus is False
    assert expansion.creates_runtime_bridge is False
    assert expansion.creates_cli_binding is False
    assert expansion.creates_product_behavior is False
    assert_no_live_endpoint_boundary_is_active(expansion.no_live_endpoint_boundary)


def test_pack_result_serializes_and_renders_summary() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    assert isinstance(result, P26BSurfaceProjectionSchemaResult)
    serialized = serialize_p2_6_b_result(result)
    assert json.loads(serialized)
    assert result.result_hash == build_p2_6_b_surface_projection_schema_result().result_hash
    summary = render_surface_projection_schema_contract_summary(result)
    assert "P2.6-B" in summary
    assert "no_live_endpoint=True" in summary


def test_truth_labels_include_required_boundaries() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    labels = set(result.truth_labels)
    assert SurfaceProjectionSchemaTruthBoundary.NOT_LIVE.value in labels
    assert SurfaceProjectionSchemaTruthBoundary.NOT_TRACE_VERIFIED.value in labels
    assert SurfaceProjectionSchemaTruthBoundary.NOT_PRODUCT_BEHAVIOR.value in labels
    assert SurfaceProjectionSchemaTruthBoundary.NO_LIVE_ENDPOINT_BOUNDARY.value in labels
    assert SurfaceProjectionSchemaTruthBoundary.NO_LIVE_QUERY_BOUNDARY.value in labels


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_6_b_side_effect_proof()
    assert isinstance(proof, P26BSideEffectProof)
    for field in fields(proof):
        assert getattr(proof, field.name) is False
    assert_p2_6_b_side_effects_all_false(proof)


def test_result_side_effects_and_claims_all_false() -> None:
    result = build_p2_6_b_surface_projection_schema_result()
    proof = result.side_effect_proof
    assert proof.projection_ui_created is False
    assert proof.api_server_created is False
    assert proof.http_routes_created is False
    assert proof.route_handler_created is False
    assert proof.live_endpoint_created is False
    assert proof.live_query_execution_created is False
    assert proof.database_query_runtime_created is False
    assert proof.storage_query_runtime_created is False
    assert proof.websocket_stream_created is False
    assert proof.sse_stream_created is False
    assert proof.event_bus_created is False
    assert proof.event_dispatch_created is False
    assert proof.runtime_bridge_created is False
    assert proof.runtime_dispatch_created is False
    assert proof.runtime_events_emitted is False
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
    assert proof.memory_written is False
    assert proof.trace_written is False
    assert proof.storage_written is False
    assert proof.runtime_mutated is False
    assert proof.source_of_truth_created is False
    assert proof.live_claimed is False
    assert proof.trace_verified_claimed is False
    assert proof.release_scope_claimed is False
    assert proof.product_behavior_claimed is False
    assert proof.p2_6_c_started is False
    assert proof.p2_7_started is False
    assert proof.p2_10_started is False
    assert proof.p2_13_started is False
    assert result.claims_live is False
    assert result.claims_trace_verified is False
    assert result.claims_release_scope is False
    assert result.claims_product_behavior is False
    assert result.starts_future_work is False

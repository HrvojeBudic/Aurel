from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    ExpandedP3ReadinessStatus,
    build_expanded_p3_readiness_matrix,
    build_flow_compatibility_read_model,
    build_flow_demo_bundle,
    build_flow_observation_frame,
    build_flow_protocol_boundary,
    build_flow_protocol_envelope,
    serialize_flow_protocol_boundary,
)
from agentic_runtime.aurel_flow.demo import run_runtime_behavior_demo


def test_protocol_boundary_exposes_schema_version_metadata() -> None:
    boundary = build_flow_protocol_boundary()
    schema_names = {schema.schema_name for schema in boundary.schema_versions}

    for required in (
        "workflow_graph",
        "workflow_run",
        "scheduler_decision",
        "runtime_event",
        "runtime_event_stream",
        "runtime_behavior_read_model",
    ):
        assert required in schema_names, required
    for schema in boundary.schema_versions:
        assert schema.schema_version == "v1"
        assert schema.contract_version.endswith(".v1")


def test_serialization_contract_is_deterministic_canonical_json() -> None:
    boundary = build_flow_protocol_boundary()
    contract = boundary.serialization_contract

    assert contract.serialization_format == "canonical_json_sorted_keys"
    assert contract.hash_algorithm == "sha256"
    assert contract.deterministic_serialization is True
    assert serialize_flow_protocol_boundary(boundary) == serialize_flow_protocol_boundary(
        build_flow_protocol_boundary()
    )


def test_protocol_boundary_migration_claims_fail_closed() -> None:
    boundary = build_flow_protocol_boundary()

    assert boundary.migration_active is False
    assert boundary.rust_code_present is False
    assert boundary.go_code_present is False
    assert boundary.generated_schema_toolchain_present is False
    for forbidden in (
        "migration_active",
        "rust_code_present",
        "go_code_present",
        "generated_schema_toolchain_present",
    ):
        with pytest.raises(AurelFlowValidationError):
            replace(boundary, **{forbidden: True})


def test_compatibility_read_model_no_rust_active_claim() -> None:
    compatibility = build_flow_compatibility_read_model()

    assert compatibility.portable_to_rust_core is True
    assert compatibility.portable_to_proto_schema is True
    assert compatibility.rust_core_active is False
    assert compatibility.python_is_implementation_truth is True
    with pytest.raises(AurelFlowValidationError):
        replace(compatibility, rust_core_active=True)
    with pytest.raises(AurelFlowValidationError):
        replace(compatibility, python_is_implementation_truth=False)


def test_protocol_envelope_binds_payload_hash_to_schema() -> None:
    boundary = build_flow_protocol_boundary()
    schema = boundary.schema_versions[0]
    bundle = build_flow_demo_bundle()

    first = build_flow_protocol_envelope(
        bundle.graph, schema, payload_kind="workflow_graph"
    )
    second = build_flow_protocol_envelope(
        bundle.graph, schema, payload_kind="workflow_graph"
    )
    assert first.payload_hash == second.payload_hash
    assert first.schema.schema_name == "workflow_graph"


def test_expanded_p3_readiness_matrix_covers_p3_10_to_p3_20() -> None:
    matrix = build_expanded_p3_readiness_matrix()
    checkpoints = tuple(item.checkpoint for item in matrix.items)

    assert checkpoints == tuple(f"P3.{n}" for n in range(10, 21))
    assert matrix.implemented_count == 0
    for item in matrix.items:
        assert isinstance(item.status, ExpandedP3ReadinessStatus)
        assert item.implemented is False
    with pytest.raises(AurelFlowValidationError):
        replace(matrix.items[0], implemented=True)
    with pytest.raises(AurelFlowValidationError):
        replace(matrix, implemented_count=1)


def test_observation_frame_has_no_exporter() -> None:
    behavior = run_runtime_behavior_demo()
    frame = build_flow_observation_frame(behavior)

    assert frame.opentelemetry_integrated is False
    assert frame.network_export_available is False
    assert "OpenTelemetry" in frame.export_unavailable_reason
    metric_names = {metric.metric_name for metric in frame.process_metrics}
    assert "flow.events.count" in metric_names
    assert "flow.pauses.count" in metric_names
    for metric in frame.process_metrics + frame.projection_metrics:
        assert metric.exported is False
        assert metric.exporter == "NONE"
    with pytest.raises(AurelFlowValidationError):
        replace(frame, opentelemetry_integrated=True)
    with pytest.raises(AurelFlowValidationError):
        replace(frame.process_metrics[0], exported=True)


def test_observation_frame_is_deterministic() -> None:
    first = build_flow_observation_frame(run_runtime_behavior_demo())
    second = build_flow_observation_frame(run_runtime_behavior_demo())

    assert first.frame_hash == second.frame_hash
    assert first.frame_id == second.frame_id

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowAutonomyLevel,
    FlowCapabilityWiringStatus,
    FlowPathTemperature,
    build_flow_autonomy_profile_read_model,
    build_flow_governance_profile_read_model,
    build_flow_hot_cold_matrix,
    build_flow_persistence_status_projection,
    build_flow_runtime_wiring_read_model,
)

REQUIRED_CAPABILITIES = (
    "WorkflowGraph",
    "WorkflowRun",
    "SchedulerDecision",
    "RuntimeEvent",
    "RuntimeBehaviorReadModel",
    "PauseResumeSignals",
    "RetryRecoveryRollbackCandidates",
    "FlowCliBinding",
    "RuntimeSubmitBridge",
    "TraceBridge",
    "PolicyCustosBridge",
    "Persistence",
    "PythonRustHybridCore",
)


def test_wiring_matrix_classifies_required_capabilities() -> None:
    matrix = build_flow_hot_cold_matrix()
    capabilities = {entry.capability for entry in matrix.entries}

    for required in REQUIRED_CAPABILITIES:
        assert required in capabilities, required


def test_wiring_matrix_statuses_are_closed_world() -> None:
    matrix = build_flow_hot_cold_matrix()

    for entry in matrix.entries:
        assert isinstance(entry.status, FlowCapabilityWiringStatus)
        assert isinstance(entry.temperature, FlowPathTemperature)
    assert (
        matrix.hot_local_count + matrix.cold_not_wired_count + matrix.future_count
        == len(matrix.entries)
    )


def test_wiring_matrix_statuses_are_honest() -> None:
    matrix = build_flow_hot_cold_matrix()
    by_capability = {entry.capability: entry for entry in matrix.entries}

    assert (
        by_capability["RuntimeSubmitBridge"].status
        is FlowCapabilityWiringStatus.RUNTIME_SUBMIT_NOT_WIRED
    )
    assert by_capability["TraceBridge"].status is FlowCapabilityWiringStatus.TRACE_NOT_WIRED
    assert (
        by_capability["PolicyCustosBridge"].status
        is FlowCapabilityWiringStatus.POLICY_NOT_WIRED
    )
    assert (
        by_capability["Persistence"].status
        is FlowCapabilityWiringStatus.PERSISTENCE_UNAVAILABLE
    )
    assert (
        by_capability["FlowCliBinding"].status is FlowCapabilityWiringStatus.CLI_READ_ONLY
    )
    assert by_capability["TraceBridge"].owning_phase == "P5"
    assert by_capability["PolicyCustosBridge"].owning_phase == "P9"


def test_wiring_read_model_integration_booleans_fail_closed() -> None:
    wiring = build_flow_runtime_wiring_read_model()

    assert wiring.runtime_submit_wired is False
    assert wiring.trace_wired is False
    assert wiring.policy_wired is False
    assert wiring.persistence_wired is False
    assert wiring.rust_core_active is False
    assert wiring.cli_read_only_wired is True
    for forbidden in ("runtime_submit_wired", "trace_wired", "rust_core_active"):
        with pytest.raises(AurelFlowValidationError):
            replace(wiring, **{forbidden: True})


def test_wiring_read_model_is_deterministic() -> None:
    first = build_flow_runtime_wiring_read_model()
    second = build_flow_runtime_wiring_read_model()

    assert first.read_model_hash == second.read_model_hash
    assert first.matrix.matrix_hash == second.matrix.matrix_hash


def test_persistence_projection_is_unavailable_and_honest() -> None:
    projection = build_flow_persistence_status_projection()

    assert projection.persisted is False
    assert projection.persistence_label == "UNAVAILABLE_PERSISTENCE"
    assert projection.external_event_store is False
    assert projection.projection_store is False
    assert projection.future_storage_boundary is True
    assert projection.append_only_readiness.append_only_shape_present is True
    assert projection.append_only_readiness.persisted is False
    assert projection.replay_cursor_readiness.replay_available is False
    assert "in-memory" in projection.reason
    with pytest.raises(AurelFlowValidationError):
        replace(projection, persisted=True)


def test_autonomy_profile_visibility_grants_nothing() -> None:
    profile = build_flow_autonomy_profile_read_model()

    assert profile.current_autonomy_level is FlowAutonomyLevel.A3_INTERNAL_PAUSE_RESUME
    assert (
        profile.max_allowed_autonomy_level
        is FlowAutonomyLevel.A5_EXECUTION_PROPOSAL_READY
    )
    assert profile.approval_mode == "OPERATOR_DECIDES"
    assert profile.execution_available is False
    assert profile.autonomy_granted_by_this_read_model is False
    with pytest.raises(AurelFlowValidationError):
        replace(profile, execution_available=True)


def test_autonomy_a6_a7_are_future_only() -> None:
    profile = build_flow_autonomy_profile_read_model()
    by_level = {item.level: item for item in profile.level_projections}

    a6 = by_level[FlowAutonomyLevel.A6_BOUNDED_AUTO_EXECUTION]
    a7 = by_level[FlowAutonomyLevel.A7_ADAPTIVE_AUTONOMY]
    assert a6.available_in_p3 is False
    assert a6.future_marker == "FUTURE_P4"
    assert a7.available_in_p3 is False
    assert a7.future_marker == "FUTURE_LATER"
    for level, item in by_level.items():
        if level not in (a6.level, a7.level):
            assert item.available_in_p3 is True


def test_governance_profile_states_core_law() -> None:
    profile = build_flow_governance_profile_read_model()

    assert profile.entity_proposes is True
    assert profile.runtime_disposes is True
    assert profile.operator_decides is True
    assert profile.custos_authorizes_marker == "FUTURE_P9"
    assert profile.trace_proves_marker == "FUTURE_P5"
    assert profile.policy_enforced_by_flow is False
    with pytest.raises(AurelFlowValidationError):
        replace(profile, policy_enforced_by_flow=True)

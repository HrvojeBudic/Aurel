"""P4-EXEC-A contract types / truth labels tests."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_exec import (
    ADMISSION_GATE_ORDER,
    AUREL_EXEC_CONTRACT_VERSION,
    AUREL_EXEC_PACK_ID,
    FORBIDDEN_EXEC_TRUTH_LABELS,
    AlgedonicSignalKind,
    AurelExecValidationError,
    ExecAdmissionGateKind,
    ExecAdmissionState,
    ExecCustosStatus,
    ExecLifecycleState,
    ExecPolicyStatus,
    ExecTraceStatus,
    ExecTruthLabel,
    ExecutionFailureClass,
    ExecutionMode,
    ExecutionPlasticityLevel,
    ExecutionTopologyKind,
    RecoveryActionKind,
    TraceBindingStatus,
    build_dev_fixture_admission_request,
)


def test_package_imports_cleanly_and_contract_version_exists():
    import agentic_runtime.aurel_exec as aurel_exec

    assert aurel_exec.AUREL_EXEC_CONTRACT_VERSION == "aurel_exec.v1"
    assert AUREL_EXEC_CONTRACT_VERSION == "aurel_exec.v1"
    assert AUREL_EXEC_PACK_ID == "P4-EXEC-A"


def test_exec_truth_label_is_closed_world_with_no_trace_verified_member():
    # TRACE_BOUND was added by P4-EXEC-B for real captured runtime trace refs.
    assert {label.value for label in ExecTruthLabel} == {
        "LIVE",
        "TRACE_BOUND",
        "DEV_FIXTURE",
        "SIMULATED",
        "UNAVAILABLE",
        "ERROR",
        "RUNTIME_SUBMIT_UNAVAILABLE",
        "TRACE_BOUND_UNAVAILABLE",
        "TRACE_VERIFIED_UNAVAILABLE",
        "POLICY_SHADOW",
        "POLICY_ENFORCED_UNAVAILABLE",
    }
    assert "TRACE_VERIFIED" not in ExecTruthLabel.__members__
    assert ExecTruthLabel.LIVE in FORBIDDEN_EXEC_TRUTH_LABELS


def test_admission_state_vocabulary_is_exact():
    assert {state.value for state in ExecAdmissionState} == {
        "ADMIT",
        "HOLD",
        "REJECT",
        "REQUIRE_OPERATOR",
        "REQUIRE_POLICY",
        "REQUIRE_VERIFIER",
        "REQUIRE_CONTEXT_REFRESH",
        "ERROR",
    }


def test_lifecycle_is_closed_world_with_no_verified_or_completed_member():
    # P4-EXEC-B legitimately added the submit-aware states because a real
    # governed bridge now exists; SUCCEEDED means runtime submit success only.
    assert {state.value for state in ExecLifecycleState} == {
        "CANDIDATE",
        "ADMITTED",
        "LEASED",
        "SESSION_BOUND",
        "ATTEMPT_PENDING",
        "READY_TO_SUBMIT",
        "RUNNING",
        "SUBMITTED",
        "SUCCEEDED",
        "FAILED",
        "BLOCKED",
        "ERROR",
    }
    for forbidden in ("EXECUTED", "COMPLETED", "VERIFIED", "TRACE_VERIFIED", "PROVEN"):
        assert forbidden not in ExecLifecycleState.__members__


def test_lifecycle_transition_maps_are_total_over_the_enum():
    from agentic_runtime.aurel_exec import (
        ATTEMPT_LIFECYCLE_TRANSITIONS,
        JOB_LIFECYCLE_TRANSITIONS,
    )

    assert set(JOB_LIFECYCLE_TRANSITIONS) == set(ExecLifecycleState)
    assert set(ATTEMPT_LIFECYCLE_TRANSITIONS) == set(ExecLifecycleState)
    # attempt-only states are unreachable for jobs and vice versa
    assert JOB_LIFECYCLE_TRANSITIONS[ExecLifecycleState.READY_TO_SUBMIT] == ()
    assert JOB_LIFECYCLE_TRANSITIONS[ExecLifecycleState.SUBMITTED] == ()
    assert ATTEMPT_LIFECYCLE_TRANSITIONS[ExecLifecycleState.CANDIDATE] == ()
    assert ATTEMPT_LIFECYCLE_TRANSITIONS[ExecLifecycleState.SESSION_BOUND] == ()


def test_execution_mode_and_topology_vocabularies():
    assert {mode.value for mode in ExecutionMode} == {
        "TOOL",
        "MODEL",
        "TERMINAL",
        "CODE",
        "CONVERSATION",
        "COMPOSITE",
        "UNAVAILABLE",
        "ERROR",
    }
    assert {kind.value for kind in ExecutionTopologyKind} == {
        "SINGLE_IN_PROCESS",
        "LINEAR",
        "CASCADE",
        "PARALLEL_FANOUT",
        "SUPERVISOR",
        "FILTER_CHAIN",
        "UNAVAILABLE",
        "ERROR",
    }


def test_plasticity_failure_recovery_algedonic_vocabularies():
    assert {level.value for level in ExecutionPlasticityLevel} == {
        "STATIC_TEMPLATE",
        "DYNAMIC_SELECTION",
        "PRE_EXECUTION_GENERATION",
        "IN_EXECUTION_EDITING_UNAVAILABLE",
        "UNAVAILABLE",
        "ERROR",
    }
    assert {cls.value for cls in ExecutionFailureClass} == {
        "NONE",
        "INVALID_SOURCE",
        "MISSING_REQUIREMENT",
        "POLICY_REQUIRED",
        "OPERATOR_REQUIRED",
        "VERIFIER_REQUIRED",
        "CONTEXT_REFRESH_REQUIRED",
        "LEASE_INVALID",
        "LEASE_EXPIRED",
        "LEASE_REVOKED",
        "RUNTIME_SUBMIT_UNAVAILABLE",
        "ERROR",
    }
    assert {kind.value for kind in RecoveryActionKind} == {
        "NONE",
        "HOLD",
        "REJECT",
        "REQUIRE_OPERATOR",
        "REQUIRE_POLICY",
        "REQUIRE_VERIFIER",
        "REQUIRE_CONTEXT_REFRESH",
        "ESCALATE",
        "UNAVAILABLE",
        "ERROR",
    }
    assert {kind.value for kind in AlgedonicSignalKind} == {
        "NONE",
        "BUDGET_EXHAUSTION",
        "RETRY_STORM",
        "SEMANTIC_SILENT_FAILURE",
        "SANDBOX_ANOMALY",
        "POLICY_VIOLATION",
        "TRACE_BINDING_FAILURE",
        "OPERATOR_ESCALATION",
        "UNAVAILABLE",
        "ERROR",
    }


def test_trace_binding_status_has_no_bound_or_verified_member():
    assert {status.value for status in TraceBindingStatus} == {
        "UNAVAILABLE",
        "TRACE_BOUND_UNAVAILABLE",
        "TRACE_VERIFIED_UNAVAILABLE",
        "ERROR",
    }
    for forbidden in ("BOUND", "TRACE_BOUND", "VERIFIED", "TRACE_VERIFIED"):
        assert forbidden not in TraceBindingStatus.__members__


def test_policy_custos_trace_statuses_cannot_claim_enforcement_or_proof():
    assert "ENFORCED" not in ExecPolicyStatus.__members__
    assert "ENFORCED" not in ExecCustosStatus.__members__
    assert "AUTHORIZED" not in ExecCustosStatus.__members__
    assert "VERIFIED" not in ExecTraceStatus.__members__
    assert "TRACE_VERIFIED" not in ExecTraceStatus.__members__


def test_gate_order_is_the_full_eight_gate_chain():
    assert ADMISSION_GATE_ORDER == (
        ExecAdmissionGateKind.SOURCE_VALIDITY,
        ExecAdmissionGateKind.P3_READINESS_MARKER,
        ExecAdmissionGateKind.AUTHORITY_REF,
        ExecAdmissionGateKind.SANDBOX_PROFILE,
        ExecAdmissionGateKind.BUDGET_REF,
        ExecAdmissionGateKind.VERIFIER_REQUIREMENT,
        ExecAdmissionGateKind.TRACE_BINDING_AVAILABILITY,
        ExecAdmissionGateKind.POLICY_CUSTOS_AVAILABILITY,
    )


def test_deterministic_serialization_and_stable_hash():
    request_a = build_dev_fixture_admission_request()
    request_b = build_dev_fixture_admission_request()
    assert request_a.to_canonical_dict() == request_b.to_canonical_dict()
    assert request_a.request_hash == request_b.request_hash
    changed = build_dev_fixture_admission_request(request_id="exec-req-other")
    assert changed.request_hash != request_a.request_hash


def test_unknown_fields_are_rejected():
    with pytest.raises(TypeError):
        build_dev_fixture_admission_request(runtime_submit=True)


def test_live_truth_label_is_unconstructible_on_requests():
    with pytest.raises(AurelExecValidationError):
        build_dev_fixture_admission_request(truth_label=ExecTruthLabel.LIVE)

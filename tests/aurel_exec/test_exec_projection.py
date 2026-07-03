"""P4-EXEC-A ExecProjection / P4-EXEC-B handoff frame tests."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    FUTURE_RUNTIME_BRIDGE_STEPS,
    AurelExecValidationError,
    ExecAdmissionState,
    ExecAttemptGuardState,
    ExecLeaseProjectionState,
    ExecLifecycleState,
    ExecUnavailableSystem,
    build_dev_fixture_admission_request,
    build_exec_projection,
    build_p4_exec_a_handoff_frame,
    create_exec_job,
    create_execution_attempt,
    decide_admission,
    issue_execution_lease,
    revoke_execution_lease,
    validate_execution_lease,
)


def _full_slice():
    request = build_dev_fixture_admission_request()
    decision = decide_admission(request)
    job = create_exec_job(decision, source_p3_candidate_ref=request.source_p3_candidate_ref)
    lease = issue_execution_lease(
        decision, request, exec_job_id=job.exec_job_id, issued_at_tick=1, expires_at_tick=100
    )
    validation = validate_execution_lease(lease, current_tick=5)
    attempt, _ = create_execution_attempt(job, lease, current_tick=5)
    return request, decision, job, lease, validation, attempt


def test_projection_shows_full_admission_lease_job_attempt_state():
    _, decision, job, lease, validation, attempt = _full_slice()
    projection = build_exec_projection(
        decision, lease=lease, lease_validation=validation, job=job, attempt=attempt
    )
    assert projection.admission_state is ExecAdmissionState.ADMIT
    assert projection.lease_state is ExecLeaseProjectionState.LEASE_VALID
    assert projection.job_state is ExecLifecycleState.ADMITTED
    assert (
        projection.attempt_guard_state
        is ExecAttemptGuardState.ATTEMPT_PENDING_WITH_VALID_LEASE
    )


def test_projection_without_lease_is_blocked():
    decision = decide_admission(build_dev_fixture_admission_request())
    projection = build_exec_projection(decision)
    assert projection.lease_state is ExecLeaseProjectionState.NO_LEASE
    assert projection.attempt_guard_state is ExecAttemptGuardState.BLOCKED_NO_VALID_LEASE


def test_projection_shows_revoked_lease_honestly():
    _, decision, job, lease, _, _ = _full_slice()
    revoked = revoke_execution_lease(lease)
    validation = validate_execution_lease(revoked, current_tick=5)
    projection = build_exec_projection(
        decision, lease=revoked, lease_validation=validation, job=job
    )
    assert projection.lease_state is ExecLeaseProjectionState.LEASE_REVOKED
    assert projection.attempt_guard_state is ExecAttemptGuardState.BLOCKED_NO_VALID_LEASE


def test_projection_marks_runtime_submit_trace_policy_unavailable():
    decision = decide_admission(build_dev_fixture_admission_request())
    projection = build_exec_projection(decision)
    assert projection.runtime_submit_available is False
    assert projection.trace_verified_available is False
    assert projection.policy_enforcement_available is False
    assert "P4-EXEC-B" in projection.runtime_submit_unavailable_reason
    assert "P5" in projection.trace_verified_unavailable_reason
    assert "P9" in projection.policy_enforcement_unavailable_reason
    systems = {reason.system for reason in projection.unavailable_reasons}
    assert ExecUnavailableSystem.RUNTIME_SUBMIT in systems
    assert ExecUnavailableSystem.TRACE_VERIFICATION in systems
    assert ExecUnavailableSystem.CUSTOS_ENFORCEMENT in systems


def test_projection_availability_claims_are_unconstructible():
    decision = decide_admission(build_dev_fixture_admission_request())
    projection = build_exec_projection(decision)
    for boundary_field in (
        "runtime_submit_available",
        "trace_verified_available",
        "policy_enforcement_available",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, read_only=False)


def test_projection_is_read_only_and_frozen():
    decision = decide_admission(build_dev_fixture_admission_request())
    projection = build_exec_projection(decision)
    assert projection.read_only is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        projection.admission_state = ExecAdmissionState.REJECT  # type: ignore[misc]


def test_handoff_frame_names_consumable_ids_and_bound_scope():
    _, decision, job, lease, _, attempt = _full_slice()
    frame = build_p4_exec_a_handoff_frame(decision, lease=lease, job=job, attempt=attempt)
    assert frame.admission_decision_id == decision.decision_id
    assert frame.execution_lease_id == lease.lease_id
    assert frame.exec_job_id == job.exec_job_id
    assert frame.attempt_id == attempt.attempt_id
    assert frame.allowed_execution_mode == lease.scope.allowed_execution_mode.value
    assert frame.allowed_tool_name == lease.scope.allowed_tool_name
    assert frame.allowed_args_hash == lease.scope.allowed_args_hash
    assert frame.sandbox_profile == lease.scope.sandbox_profile


def test_handoff_frame_names_full_future_bridge_chain():
    decision = decide_admission(build_dev_fixture_admission_request())
    frame = build_p4_exec_a_handoff_frame(decision)
    assert frame.future_bridge_steps == FUTURE_RUNTIME_BRIDGE_STEPS
    assert frame.future_bridge_steps == (
        "ExecJob",
        "ExecutionLease",
        "ExecutionAttempt",
        "CommandEnvelope",
        "AgenticRuntime.submit()",
        "ExecutionOutcome",
    )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(frame, future_bridge_steps=("ExecJob",))


def test_handoff_frame_is_not_p4_exec_b_and_wires_nothing():
    decision = decide_admission(build_dev_fixture_admission_request())
    frame = build_p4_exec_a_handoff_frame(decision)
    assert frame.is_p4_exec_b is False
    assert frame.runtime_submit_wired is False
    assert frame.execution_performed is False
    for boundary_field in ("is_p4_exec_b", "runtime_submit_wired", "execution_performed"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(frame, **{boundary_field: True})
    assert frame.runtime_submit_unavailable.future_p4_exec_b_required is True
    owners = {req.future_owner for req in frame.bridge_requirements}
    assert {"P4-EXEC-B", "P5 AurelTrace", "P9 Custos"} <= owners
    for requirement in frame.bridge_requirements:
        assert requirement.is_implemented is False

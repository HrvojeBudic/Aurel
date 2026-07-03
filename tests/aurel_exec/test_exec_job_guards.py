"""P4-EXEC-A ExecJob / ExecutionAttempt lease-before-attempt guard tests."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecLifecycleState,
    ExecutionAttempt,
    ExecTruthLabel,
    build_dev_fixture_admission_request,
    create_exec_job,
    create_execution_attempt,
    decide_admission,
    issue_execution_lease,
    revoke_execution_lease,
)


def _admitted_job_and_lease(*, expires_at_tick=100):
    request = build_dev_fixture_admission_request()
    decision = decide_admission(request)
    job = create_exec_job(decision, source_p3_candidate_ref=request.source_p3_candidate_ref)
    lease = issue_execution_lease(
        decision,
        request,
        exec_job_id=job.exec_job_id,
        issued_at_tick=1,
        expires_at_tick=expires_at_tick,
    )
    return request, decision, job, lease


def test_job_is_created_only_from_admit_decision():
    request, decision, job, _ = _admitted_job_and_lease()
    assert job.admission_decision_id == decision.decision_id
    assert job.lifecycle_state is ExecLifecycleState.ADMITTED

    held = decide_admission(
        build_dev_fixture_admission_request(requested_sandbox_profile=None)
    )
    with pytest.raises(AurelExecValidationError) as excinfo:
        create_exec_job(held, source_p3_candidate_ref="ref")
    assert excinfo.value.code is AurelExecErrorCode.JOB_DENIED


def test_job_is_not_execution():
    _, _, job, _ = _admitted_job_and_lease()
    for name in ("submit", "dispatch", "execute", "run", "runtime_submit_called"):
        assert not hasattr(job, name)
    assert job.truth_label is ExecTruthLabel.DEV_FIXTURE


def test_attempt_is_created_under_valid_lease_and_never_submits():
    _, _, job, lease = _admitted_job_and_lease()
    attempt, validation = create_execution_attempt(job, lease, current_tick=5)
    assert validation.valid
    assert attempt.exec_job_id == job.exec_job_id
    assert attempt.lease_id == lease.lease_id
    assert attempt.lifecycle_state is ExecLifecycleState.ATTEMPT_PENDING
    assert attempt.runtime_submit_called is False


def test_attempt_is_denied_with_expired_lease():
    _, _, job, lease = _admitted_job_and_lease(expires_at_tick=10)
    with pytest.raises(AurelExecValidationError) as excinfo:
        create_execution_attempt(job, lease, current_tick=10)
    assert excinfo.value.code is AurelExecErrorCode.LEASE_EXPIRED


def test_attempt_is_denied_with_revoked_lease():
    _, _, job, lease = _admitted_job_and_lease()
    revoked = revoke_execution_lease(lease)
    with pytest.raises(AurelExecValidationError) as excinfo:
        create_execution_attempt(job, revoked, current_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.LEASE_REVOKED


def test_attempt_is_denied_when_lease_belongs_to_another_job():
    _, decision, job, _ = _admitted_job_and_lease()
    request = build_dev_fixture_admission_request()
    other_lease = issue_execution_lease(
        decide_admission(request),
        request,
        exec_job_id="exec-job-other",
        issued_at_tick=1,
    )
    with pytest.raises(AurelExecValidationError) as excinfo:
        create_execution_attempt(job, other_lease, current_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.LEASE_JOB_MISMATCH


def test_attempt_claiming_runtime_submit_is_unconstructible():
    with pytest.raises(AurelExecValidationError) as excinfo:
        ExecutionAttempt(
            attempt_id="exec-attempt-x",
            exec_job_id="exec-job-x",
            lease_id="exec-lease-x",
            lifecycle_state=ExecLifecycleState.ATTEMPT_PENDING,
            truth_label=ExecTruthLabel.DEV_FIXTURE,
            runtime_submit_called=True,
        )
    assert excinfo.value.code is AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM


def test_attempt_without_lease_reference_is_unconstructible():
    with pytest.raises(AurelExecValidationError):
        ExecutionAttempt(
            attempt_id="exec-attempt-x",
            exec_job_id="exec-job-x",
            lease_id="  ",
            lifecycle_state=ExecLifecycleState.ATTEMPT_PENDING,
            truth_label=ExecTruthLabel.DEV_FIXTURE,
        )

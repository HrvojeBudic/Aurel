"""P4-EXEC-A execution lease kernel tests."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecLeaseDenied,
    ExecTruthLabel,
    LeaseDenialReason,
    LeaseRevocationState,
    build_dev_fixture_admission_request,
    decide_admission,
    issue_execution_lease,
    revoke_execution_lease,
    validate_execution_lease,
)


def _admitted():
    request = build_dev_fixture_admission_request()
    decision = decide_admission(request)
    return request, decision


def _lease(**overrides):
    request, decision = _admitted()
    kwargs = {
        "exec_job_id": "exec-job-test",
        "issued_at_tick": 1,
        "expires_at_tick": 100,
        "max_attempts": 1,
    }
    kwargs.update(overrides)
    return issue_execution_lease(decision, request, **kwargs)


def test_lease_is_issued_only_from_admit_decision_and_binds_scope():
    request, decision = _admitted()
    lease = issue_execution_lease(
        decision, request, exec_job_id="exec-job-test", issued_at_tick=1
    )
    assert lease.admission_decision_id == decision.decision_id
    assert lease.scope.allowed_execution_mode is request.requested_execution_mode
    assert lease.scope.allowed_tool_name == request.requested_tool_name
    assert lease.scope.allowed_args_hash == request.requested_args_hash
    assert lease.scope.sandbox_profile == request.requested_sandbox_profile
    assert lease.scope.budget_scope_ref == request.requested_budget_ref
    assert lease.scope.authority_scope_ref == request.requested_authority_ref
    assert lease.scope.policy_snapshot_ref == request.requested_policy_context_ref
    assert lease.revocation_state is LeaseRevocationState.NOT_REVOKED


def test_lease_is_denied_for_every_non_admit_decision():
    for overrides in (
        {"source_p3_candidate_ref": ""},  # REJECT
        {"requested_sandbox_profile": None},  # HOLD
        {"requested_authority_ref": None},  # REQUIRE_OPERATOR
        {"requested_policy_context_ref": None},  # REQUIRE_POLICY
    ):
        request = build_dev_fixture_admission_request(**overrides)
        decision = decide_admission(request)
        with pytest.raises(ExecLeaseDenied) as excinfo:
            issue_execution_lease(
                decision, request, exec_job_id="exec-job-test", issued_at_tick=1
            )
        assert excinfo.value.denial_reason is LeaseDenialReason.DECISION_NOT_ADMIT


def test_lease_is_denied_on_decision_request_mismatch():
    request, decision = _admitted()
    other = build_dev_fixture_admission_request(request_id="exec-req-other")
    with pytest.raises(ExecLeaseDenied) as excinfo:
        issue_execution_lease(decision, other, exec_job_id="exec-job-test", issued_at_tick=1)
    assert excinfo.value.denial_reason is LeaseDenialReason.DECISION_REQUEST_MISMATCH


def test_valid_lease_validates_before_expiry():
    lease = _lease()
    result = validate_execution_lease(lease, current_tick=50)
    assert result.valid
    assert not result.expired
    assert not result.revoked


def test_expired_lease_is_invalid():
    lease = _lease(expires_at_tick=10)
    result = validate_execution_lease(lease, current_tick=10)
    assert not result.valid
    assert result.expired
    assert result.missing_requirements


def test_revoked_lease_is_invalid():
    revoked = revoke_execution_lease(_lease())
    assert revoked.revoked
    assert revoked.revocation_state is LeaseRevocationState.REVOKED
    result = validate_execution_lease(revoked, current_tick=2)
    assert not result.valid
    assert result.revoked


def test_revocation_returns_new_lease_and_original_is_untouched():
    lease = _lease()
    revoked = revoke_execution_lease(lease)
    assert revoked is not lease
    assert not lease.revoked
    with pytest.raises(dataclasses.FrozenInstanceError):
        lease.revoked = True  # type: ignore[misc]


def test_validation_result_cannot_claim_valid_while_expired_or_revoked():
    from agentic_runtime.aurel_exec import LeaseValidationResult

    with pytest.raises(AurelExecValidationError):
        LeaseValidationResult(
            valid=True,
            reason="impossible",
            lease_id="exec-lease-x",
            expired=True,
            revoked=False,
            truth_label=ExecTruthLabel.DEV_FIXTURE,
        )


def test_lease_window_and_max_attempts_fail_closed():
    with pytest.raises(AurelExecValidationError):
        _lease(expires_at_tick=1)  # expiry not after issuance
    with pytest.raises(AurelExecValidationError):
        _lease(max_attempts=0)


def test_lease_cannot_claim_live_and_is_not_execution():
    lease = _lease()
    assert lease.truth_label is ExecTruthLabel.DEV_FIXTURE
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(lease, truth_label=ExecTruthLabel.LIVE)
    for name in ("submit", "dispatch", "execute", "run"):
        assert not hasattr(lease, name)


def test_lease_hash_is_deterministic():
    request, decision = _admitted()
    lease_a = issue_execution_lease(
        decision, request, exec_job_id="exec-job-test", issued_at_tick=1
    )
    lease_b = issue_execution_lease(
        decision, request, exec_job_id="exec-job-test", issued_at_tick=1
    )
    assert lease_a.lease_hash == lease_b.lease_hash
    assert lease_a.lease_id == lease_b.lease_id

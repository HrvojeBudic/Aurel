"""P4-EXEC-E failure classification tests — deterministic taxonomy."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecutionMode,
    FAILURE_METADATA,
    FailureClass,
    FailureSeverity,
    VerificationStatus,
    build_execution_verification_request,
    build_profile_only_verifier_hook,
    classify_execution_failure,
    classify_pre_submit_block,
    decide_verification,
    normalize_runtime_result,
)
from tests.aurel_exec._bridge_helpers import RecordingFakeRuntime, _FakeCard


class _Cmd:
    id = "cmd_x"


def _outcome(*, succeed=True):
    return normalize_runtime_result(
        RecordingFakeRuntime(succeed=succeed).submit(_Cmd(), _FakeCard()),
        attempt_id="exec-attempt-a",
        exec_job_id="exec-job-a",
        session_id="exec-session-a",
        tool_name="read_file",
        command_id="cmd_x",
    )


def _verify(outcome, **kwargs):
    request = build_execution_verification_request(
        outcome, requested_execution_mode=ExecutionMode.TOOL
    )
    return decide_verification(request, outcome, **kwargs)


def test_failure_classifier_maps_known_failures_deterministically():
    ok = _outcome()
    hook = build_profile_only_verifier_hook()
    passed = _verify(ok, hook=hook, evidence_refs=("evidence:x",))
    inconclusive = _verify(ok, hook=hook)
    bad = _outcome(succeed=False)
    failed = _verify(bad, hook=hook)
    # success + PASSED -> NONE
    assert classify_execution_failure(ok, passed).failure_class is FailureClass.NONE
    # success + no decision / inconclusive -> VERIFIER_UNAVAILABLE
    assert (
        classify_execution_failure(ok, None).failure_class
        is FailureClass.VERIFIER_UNAVAILABLE
    )
    assert (
        classify_execution_failure(ok, inconclusive).failure_class
        is FailureClass.VERIFIER_UNAVAILABLE
    )
    # runtime tool failure -> TOOL_ERROR
    assert (
        classify_execution_failure(bad, None).failure_class is FailureClass.TOOL_ERROR
    )
    # failed verification over a failed outcome -> classified from the outcome
    assert (
        classify_execution_failure(bad, failed).failure_class is FailureClass.TOOL_ERROR
    )
    # determinism: same inputs, same classification id/hash
    first = classify_execution_failure(bad, None)
    second = classify_execution_failure(bad, None)
    assert first == second
    assert first.classification_hash == second.classification_hash


def test_failed_verification_creates_failure_classification():
    ok = _outcome()
    hook = build_profile_only_verifier_hook()
    inconclusive = _verify(ok, hook=hook)
    # force a FAILED semantic verification over a successful runtime outcome
    failed_semantic = dataclasses.replace(
        inconclusive,
        verification_status=VerificationStatus.FAILED,
        reason="semantic guard rejected the output",
    )
    classification = classify_execution_failure(ok, failed_semantic)
    assert classification.failure_class is FailureClass.VERIFICATION_FAILED
    assert classification.severity is FailureSeverity.URGENT
    assert classification.operator_action_required is True


def test_metadata_table_is_total_and_structurally_enforced():
    assert set(FAILURE_METADATA) == set(FailureClass)
    classification = classify_execution_failure(_outcome(succeed=False), None)
    # metadata contradicting the taxonomy table is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(classification, severity=FailureSeverity.INFO)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(classification, retryable=False)


def test_classification_is_not_recovery_and_grants_no_authority():
    classification = classify_execution_failure(_outcome(succeed=False), None)
    assert classification.executes_recovery is False
    assert classification.grants_authority is False
    for boundary_field in ("executes_recovery", "grants_authority"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(classification, **{boundary_field: True})
    for verb in ("recover", "retry", "repair", "rollback", "execute"):
        assert not hasattr(classification, verb)


def test_pre_submit_blocks_classify_deterministically():
    lease = classify_pre_submit_block("LEASE_EXPIRED", exec_job_id="exec-job-a")
    assert lease.failure_class is FailureClass.LEASE_INVALID
    mode = classify_pre_submit_block(
        "UNSUPPORTED_EXECUTION_MODE", exec_job_id="exec-job-a"
    )
    assert mode.failure_class is FailureClass.MODE_UNAVAILABLE
    unknown = classify_pre_submit_block("SOMETHING_ELSE", exec_job_id="exec-job-a")
    assert unknown.failure_class is FailureClass.UNKNOWN_ERROR
    assert unknown.severity is FailureSeverity.CRITICAL


def test_failure_class_and_severity_vocabularies_are_exact():
    assert {c.value for c in FailureClass} == {
        "NONE",
        "RUNTIME_ERROR",
        "POLICY_BLOCKED",
        "LEASE_INVALID",
        "MODE_UNAVAILABLE",
        "VERIFICATION_FAILED",
        "VERIFIER_UNAVAILABLE",
        "OUTPUT_CONTRACT_FAILED",
        "TOOL_ERROR",
        "TIMEOUT",
        "RESOURCE_EXHAUSTED",
        "UNKNOWN_ERROR",
    }
    assert {s.value for s in FailureSeverity} == {
        "INFO",
        "WARNING",
        "ERROR",
        "URGENT",
        "CRITICAL",
    }

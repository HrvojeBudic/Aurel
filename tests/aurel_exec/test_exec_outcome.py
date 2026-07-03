"""P4-EXEC-B ExecutionOutcome normalization tests."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTruthLabel,
    ExecutionOutcome,
    ExecutionOutcomeStatus,
    normalize_runtime_result,
)
from tests.aurel_exec._bridge_helpers import (
    RecordingFakeRuntime,
    _FakeCard,
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)

_IDS = dict(
    attempt_id="exec-attempt-x",
    exec_job_id="exec-job-x",
    session_id="exec-session-x",
    tool_name="read_file",
    command_id="cmd_x",
)


def _fake_result(*, succeed=True, with_transition=True):
    fake = RecordingFakeRuntime(succeed=succeed, with_transition=with_transition)

    class _Cmd:
        id = "cmd_x"

    return fake.submit(_Cmd(), _FakeCard())


def test_normalization_preserves_runtime_success():
    outcome = normalize_runtime_result(_fake_result(succeed=True), **_IDS)
    assert outcome.success is True
    assert outcome.runtime_status is ExecutionOutcomeStatus.RUNTIME_SUCCESS
    assert outcome.runtime_submit_called is True
    assert outcome.result_summary == "fake file content"
    assert outcome.verifier_passed is True
    assert outcome.rollback_performed is False
    assert outcome.trace_ref == "txn_fake_0001"
    assert outcome.truth_label is ExecTruthLabel.LIVE


def test_execution_outcome_preserves_runtime_failure():
    outcome = normalize_runtime_result(_fake_result(succeed=False), **_IDS)
    assert outcome.success is False
    assert outcome.runtime_status is ExecutionOutcomeStatus.RUNTIME_FAILURE
    assert outcome.error_category == "tool_failure"
    assert "FileNotFoundError" in (outcome.error_message or "")
    # the failure is preserved in the summary, not rewritten into success
    assert "FileNotFoundError" in outcome.result_summary


def test_outcome_is_deterministic_for_the_same_result():
    result = _fake_result()
    first = normalize_runtime_result(result, **_IDS)
    second = normalize_runtime_result(result, **_IDS)
    assert first == second
    assert first.outcome_hash == second.outcome_hash


def test_outcome_without_transition_has_no_trace_ref():
    outcome = normalize_runtime_result(_fake_result(with_transition=False), **_IDS)
    assert outcome.trace_ref is None


def test_outcome_cannot_claim_semantic_success_or_trace_verification():
    outcome = normalize_runtime_result(_fake_result(), **_IDS)
    assert outcome.semantic_success is False
    assert outcome.trace_verified is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(outcome, semantic_success=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(outcome, trace_verified=True)


def test_outcome_cannot_claim_success_without_submit_or_status_agreement():
    outcome = normalize_runtime_result(_fake_result(), **_IDS)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(outcome, runtime_submit_called=False)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(outcome, runtime_status=ExecutionOutcomeStatus.RUNTIME_FAILURE)


def test_outcome_status_vocabulary_has_no_semantic_or_verified_member():
    assert {status.value for status in ExecutionOutcomeStatus} == {
        "RUNTIME_SUCCESS",
        "RUNTIME_FAILURE",
        "BLOCKED",
        "ERROR",
        "UNAVAILABLE",
    }
    for forbidden in ("SEMANTIC_SUCCESS", "VERIFIED", "TRACE_VERIFIED", "PROVEN"):
        assert forbidden not in ExecutionOutcomeStatus.__members__


def test_bridge_outcome_matches_normalization_end_to_end():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    assert isinstance(execution.outcome, ExecutionOutcome)
    assert execution.outcome.attempt_id == attempt.attempt_id
    assert execution.outcome.command_id == execution.result.command_id
    assert execution.outcome.tool_name == "read_file"

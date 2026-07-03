"""P4-EXEC-E algedonic signal tests — urgent visibility, not authority."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AlgedonicEscalationKind,
    AlgedonicSeverity,
    AurelExecValidationError,
    FailureClass,
    FailureSeverity,
    classify_execution_failure,
    classify_pre_submit_block,
    create_algedonic_signal_if_needed,
    normalize_runtime_result,
)
from tests.aurel_exec._bridge_helpers import RecordingFakeRuntime, _FakeCard


class _Cmd:
    id = "cmd_x"


def _classification_for(failure_class: FailureClass):
    base = classify_pre_submit_block("SOMETHING_ELSE", exec_job_id="exec-job-a")
    from agentic_runtime.aurel_exec import FAILURE_METADATA

    severity, retryable, recoverable, operator = FAILURE_METADATA[failure_class]
    return dataclasses.replace(
        base,
        failure_class=failure_class,
        severity=severity,
        retryable=retryable,
        recoverable=recoverable,
        operator_action_required=operator,
        reason=f"test {failure_class.value}",
    )


def test_algedonic_signal_emitted_for_critical_failure():
    critical = _classification_for(FailureClass.UNKNOWN_ERROR)  # CRITICAL severity
    signal = create_algedonic_signal_if_needed(critical, created_at_tick=9)
    assert signal is not None
    assert signal.severity is AlgedonicSeverity.CRITICAL
    assert signal.signal_kind is AlgedonicEscalationKind.UNKNOWN_CRITICAL
    assert signal.operator_attention_required is True
    assert signal.failure_classification_id == critical.failure_classification_id
    # deterministic: same classification, same signal
    again = create_algedonic_signal_if_needed(critical, created_at_tick=9)
    assert again == signal


def test_urgent_failures_signal_and_lower_severities_do_not():
    urgent = _classification_for(FailureClass.POLICY_BLOCKED)  # URGENT
    assert create_algedonic_signal_if_needed(urgent) is not None
    error_level = _classification_for(FailureClass.TOOL_ERROR)  # ERROR
    assert create_algedonic_signal_if_needed(error_level) is None
    warning_level = _classification_for(FailureClass.VERIFIER_UNAVAILABLE)  # WARNING
    assert create_algedonic_signal_if_needed(warning_level) is None
    ok = _classification_for(FailureClass.NONE)  # INFO
    assert create_algedonic_signal_if_needed(ok) is None


def test_signal_kinds_map_deterministically():
    cases = {
        FailureClass.POLICY_BLOCKED: AlgedonicEscalationKind.POLICY_CONFLICT,
        FailureClass.VERIFICATION_FAILED: AlgedonicEscalationKind.VERIFICATION_FAILURE,
        FailureClass.OUTPUT_CONTRACT_FAILED: AlgedonicEscalationKind.VERIFICATION_FAILURE,
        FailureClass.RESOURCE_EXHAUSTED: AlgedonicEscalationKind.RESOURCE_EXHAUSTION,
        FailureClass.UNKNOWN_ERROR: AlgedonicEscalationKind.UNKNOWN_CRITICAL,
    }
    for failure_class, expected_kind in cases.items():
        signal = create_algedonic_signal_if_needed(_classification_for(failure_class))
        assert signal is not None, failure_class
        assert signal.signal_kind is expected_kind, failure_class
    # repeated failure evidence overrides the kind
    repeated = create_algedonic_signal_if_needed(
        _classification_for(FailureClass.UNKNOWN_ERROR), repeated_failure=True
    )
    assert repeated.signal_kind is AlgedonicEscalationKind.REPEATED_FAILURE


def test_algedonic_signal_does_not_grant_authority():
    signal = create_algedonic_signal_if_needed(
        _classification_for(FailureClass.UNKNOWN_ERROR)
    )
    assert signal.grants_authority is False
    assert signal.bypasses_custos is False
    assert signal.executes_action is False
    for boundary_field in ("grants_authority", "bypasses_custos", "executes_action"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(signal, **{boundary_field: True})
    for verb in ("execute", "authorize", "approve", "escalate_execute", "bypass"):
        assert not hasattr(signal, verb)
    assert "authority remains with the operator and P9" in signal.message


def test_severity_and_kind_vocabularies_are_exact():
    assert {s.value for s in AlgedonicSeverity} == {
        "INFO",
        "WARNING",
        "URGENT",
        "CRITICAL",
    }
    assert {k.value for k in AlgedonicEscalationKind} == {
        "RUNTIME_FAILURE",
        "POLICY_CONFLICT",
        "VERIFICATION_FAILURE",
        "REPEATED_FAILURE",
        "RESOURCE_EXHAUSTION",
        "UNSAFE_MODE_REQUEST",
        "UNKNOWN_CRITICAL",
    }


def test_full_chain_from_real_shaped_outcome():
    outcome = normalize_runtime_result(
        RecordingFakeRuntime(succeed=False).submit(_Cmd(), _FakeCard()),
        attempt_id="exec-attempt-a",
        exec_job_id="exec-job-a",
        session_id="exec-session-a",
        tool_name="read_file",
        command_id="cmd_x",
    )
    classification = classify_execution_failure(outcome, None)
    # TOOL_ERROR is ERROR severity -> visible in classification, no pain signal
    assert classification.severity is FailureSeverity.ERROR
    assert create_algedonic_signal_if_needed(classification) is None

"""P4-EXEC-B ExecutionOutcome — normalized runtime result view.

An ExecutionOutcome is the P4-normalized view of what the governed runtime
actually returned. It is not P5 proof, and it is not semantic success:
``semantic_success`` is structurally False in this pack because no semantic
verifier engine exists yet — runtime submit success (observation + state
verifier) is a runtime fact, not a verified task result. Runtime failures
are preserved honestly, never rewritten.

This module never imports or touches the runtime kernel: it consumes the
CommandResult-shaped object that the ExecRuntimeBridge already captured.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_nonempty,
    stable_hash,
)

EXECUTION_OUTCOME_VERSION = "execution_outcome.v1"

_SUMMARY_MAX_CHARS = 400


class ExecutionOutcomeStatus(str, Enum):
    """Closed-world runtime outcome status. There is no VERIFIED or
    SEMANTIC_SUCCESS member: those belong to P5 and a future verifier."""

    RUNTIME_SUCCESS = "RUNTIME_SUCCESS"
    RUNTIME_FAILURE = "RUNTIME_FAILURE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ExecutionOutcome(_ExecCanonicalMixin):
    """P4-normalized runtime result. Not proof, not semantic success."""

    outcome_id: str
    attempt_id: str
    exec_job_id: str
    session_id: str
    success: bool
    runtime_submit_called: bool
    runtime_status: ExecutionOutcomeStatus
    result_summary: str
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_OUTCOME_VERSION
    command_id: str | None = None
    tool_name: str | None = None
    error_category: str | None = None
    error_message: str | None = None
    verifier_passed: bool | None = None
    rollback_performed: bool | None = None
    trace_ref: str | None = None
    semantic_success: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "outcome_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "attempt_id", code=AurelExecErrorCode.EMPTY_ATTEMPT_ID)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "session_id", code=AurelExecErrorCode.EMPTY_SESSION_ID)
        require_nonempty(self, "result_summary", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "semantic_success", "trace_verified")
        if self.success and not self.runtime_submit_called:
            raise AurelExecValidationError(
                "an outcome cannot claim success without a runtime submit",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="success",
            )
        if self.success != (self.runtime_status is ExecutionOutcomeStatus.RUNTIME_SUCCESS):
            raise AurelExecValidationError(
                "success flag and runtime_status must agree",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_status",
            )

    @property
    def outcome_hash(self) -> str:
        return stable_hash(self)


def _truncate(text: str) -> str:
    if len(text) <= _SUMMARY_MAX_CHARS:
        return text
    return text[:_SUMMARY_MAX_CHARS] + "...[truncated]"


def normalize_runtime_result(
    result: Any,
    *,
    attempt_id: str,
    exec_job_id: str,
    session_id: str,
    tool_name: str,
    command_id: str,
) -> ExecutionOutcome:
    """Normalize a CommandResult-shaped runtime result into ExecutionOutcome.

    Deterministic given the result; preserves failure honestly. ``result``
    must expose ``observation`` (success/stdout/stderr), ``verifier``
    (passed), ``decision`` (verdict), ``rolled_back``, and ``transition``
    — the shape ``AgenticRuntime.submit()`` actually returns.
    """
    observation = result.observation
    verifier = result.verifier
    runtime_success = bool(observation.success and verifier.passed)

    error_category: str | None = None
    error_message: str | None = None
    if not runtime_success:
        if not observation.success:
            error_category = "tool_failure"
            error_message = _truncate(observation.stderr or "tool execution failed")
        else:
            error_category = "verifier_failure"
            error_message = _truncate(
                getattr(verifier, "reason", "") or "state verifier did not pass"
            )
        verdict = getattr(result.decision, "verdict", None)
        verdict_value = getattr(verdict, "value", None)
        if verdict_value and verdict_value != "allow":
            error_category = f"policy_{verdict_value}"

    summary_source = observation.stdout if runtime_success else (error_message or "")
    result_summary = _truncate(summary_source) or (
        "runtime submit completed with empty output"
    )

    transition = result.transition
    trace_ref = getattr(transition, "id", None) if transition is not None else None

    outcome_id = "exec-outcome-" + stable_hash((attempt_id, command_id))[:16]
    return ExecutionOutcome(
        outcome_id=outcome_id,
        attempt_id=attempt_id,
        exec_job_id=exec_job_id,
        session_id=session_id,
        success=runtime_success,
        runtime_submit_called=True,
        runtime_status=(
            ExecutionOutcomeStatus.RUNTIME_SUCCESS
            if runtime_success
            else ExecutionOutcomeStatus.RUNTIME_FAILURE
        ),
        result_summary=result_summary,
        truth_label=ExecTruthLabel.LIVE,
        command_id=command_id,
        tool_name=tool_name,
        error_category=error_category,
        error_message=error_message,
        verifier_passed=bool(verifier.passed),
        rollback_performed=bool(result.rolled_back),
        trace_ref=trace_ref,
    )

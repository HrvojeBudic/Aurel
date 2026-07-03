"""P4-EXEC-E deterministic failure classification.

Failure taxonomy comes before recovery: every known outcome/verification
failure maps deterministically to a closed-world ``FailureClass`` with a
severity and retryable/recoverable/operator metadata via a total mapping
table. Classification is a read model — it executes no recovery, grants no
authority, and repairs nothing. Fields stay primitive/serializable so a
future non-Python substrate can emit the same shapes.
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
from .exec_verification import ExecutionVerificationDecision, VerificationStatus

FAILURE_CLASSIFICATION_VERSION = "failure_classification.v1"


class FailureClass(str, Enum):
    NONE = "NONE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    LEASE_INVALID = "LEASE_INVALID"
    MODE_UNAVAILABLE = "MODE_UNAVAILABLE"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    VERIFIER_UNAVAILABLE = "VERIFIER_UNAVAILABLE"
    OUTPUT_CONTRACT_FAILED = "OUTPUT_CONTRACT_FAILED"
    TOOL_ERROR = "TOOL_ERROR"
    TIMEOUT = "TIMEOUT"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class FailureSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


# Total deterministic metadata table:
# FailureClass -> (severity, retryable, recoverable, operator_action_required)
FAILURE_METADATA: dict[FailureClass, tuple[FailureSeverity, bool, bool, bool]] = {
    FailureClass.NONE: (FailureSeverity.INFO, False, False, False),
    FailureClass.RUNTIME_ERROR: (FailureSeverity.ERROR, False, True, True),
    FailureClass.POLICY_BLOCKED: (FailureSeverity.URGENT, False, False, True),
    FailureClass.LEASE_INVALID: (FailureSeverity.WARNING, False, True, True),
    FailureClass.MODE_UNAVAILABLE: (FailureSeverity.WARNING, False, True, True),
    FailureClass.VERIFICATION_FAILED: (FailureSeverity.URGENT, False, True, True),
    FailureClass.VERIFIER_UNAVAILABLE: (FailureSeverity.WARNING, False, True, True),
    FailureClass.OUTPUT_CONTRACT_FAILED: (FailureSeverity.URGENT, False, True, True),
    FailureClass.TOOL_ERROR: (FailureSeverity.ERROR, True, True, True),
    FailureClass.TIMEOUT: (FailureSeverity.ERROR, True, True, True),
    FailureClass.RESOURCE_EXHAUSTED: (FailureSeverity.URGENT, False, False, True),
    FailureClass.UNKNOWN_ERROR: (FailureSeverity.CRITICAL, False, False, True),
}
"""Retryable is metadata only: automatic retry stays unavailable in P4."""


@dataclass(frozen=True)
class FailureClassification(_ExecCanonicalMixin):
    """Deterministic failure verdict. Not recovery, not authority."""

    failure_classification_id: str
    exec_job_id: str
    attempt_id: str
    outcome_id: str
    failure_class: FailureClass
    severity: FailureSeverity
    retryable: bool
    recoverable: bool
    operator_action_required: bool
    reason: str
    truth_label: ExecTruthLabel
    contract_version: str = FAILURE_CLASSIFICATION_VERSION
    verification_decision_id: str | None = None
    executes_recovery: bool = False
    grants_authority: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "failure_classification_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "executes_recovery", "grants_authority")
        expected = FAILURE_METADATA[self.failure_class]
        if (
            self.severity,
            self.retryable,
            self.recoverable,
            self.operator_action_required,
        ) != expected:
            raise AurelExecValidationError(
                f"classification metadata for {self.failure_class.value} must "
                "match the deterministic taxonomy table",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="failure_class",
            )

    @property
    def classification_hash(self) -> str:
        return stable_hash(self)


def _classification(
    failure_class: FailureClass,
    reason: str,
    *,
    exec_job_id: str,
    attempt_id: str,
    outcome_id: str,
    verification_decision_id: str | None = None,
) -> FailureClassification:
    severity, retryable, recoverable, operator = FAILURE_METADATA[failure_class]
    return FailureClassification(
        failure_classification_id="exec-failure-"
        + stable_hash((outcome_id, failure_class.value, verification_decision_id))[:16],
        exec_job_id=exec_job_id,
        attempt_id=attempt_id,
        outcome_id=outcome_id,
        failure_class=failure_class,
        severity=severity,
        retryable=retryable,
        recoverable=recoverable,
        operator_action_required=operator,
        reason=reason,
        truth_label=ExecTruthLabel.LIVE,
        verification_decision_id=verification_decision_id,
    )


def classify_execution_failure(
    outcome: Any,
    verification_decision: ExecutionVerificationDecision | None = None,
) -> FailureClassification:
    """Deterministically classify one outcome (+ optional verification).

    Same inputs, same classification. Mapping:
    runtime tool failure → TOOL_ERROR; verifier-stage runtime failure →
    VERIFICATION_FAILED; policy verdict failure → POLICY_BLOCKED; unknown
    runtime failure → UNKNOWN_ERROR; success + PASSED → NONE; success +
    UNAVAILABLE/INCONCLUSIVE/REQUIRES_OPERATOR_REVIEW → VERIFIER_UNAVAILABLE;
    success + FAILED verification → VERIFICATION_FAILED.
    """
    ids = dict(
        exec_job_id=outcome.exec_job_id,
        attempt_id=outcome.attempt_id,
        outcome_id=outcome.outcome_id,
        verification_decision_id=(
            verification_decision.verification_decision_id
            if verification_decision is not None
            else None
        ),
    )
    if not outcome.success:
        category = outcome.error_category or ""
        message = (outcome.error_message or "runtime failure")[:200]
        if category.startswith("policy_"):
            return _classification(
                FailureClass.POLICY_BLOCKED, f"policy verdict blocked: {message}", **ids
            )
        if category == "tool_failure":
            if "timeout" in message.lower() or "timed out" in message.lower():
                return _classification(
                    FailureClass.TIMEOUT, f"tool timed out: {message}", **ids
                )
            return _classification(
                FailureClass.TOOL_ERROR, f"tool execution failed: {message}", **ids
            )
        if category == "verifier_failure":
            return _classification(
                FailureClass.VERIFICATION_FAILED,
                f"runtime state verifier failed: {message}",
                **ids,
            )
        return _classification(
            FailureClass.UNKNOWN_ERROR, f"unclassified runtime failure: {message}", **ids
        )

    if verification_decision is None:
        return _classification(
            FailureClass.VERIFIER_UNAVAILABLE,
            "runtime succeeded but no verification decision exists; runtime "
            "success is not semantic success",
            **ids,
        )
    status = verification_decision.verification_status
    if status is VerificationStatus.PASSED:
        return _classification(
            FailureClass.NONE,
            "runtime succeeded and verification passed with evidence; "
            "P5 proof still required for trace verification",
            **ids,
        )
    if status is VerificationStatus.FAILED:
        return _classification(
            FailureClass.VERIFICATION_FAILED,
            f"verification failed: {verification_decision.reason[:200]}",
            **ids,
        )
    if status is VerificationStatus.ERROR:
        return _classification(
            FailureClass.UNKNOWN_ERROR,
            f"verification decision in ERROR state: {verification_decision.reason[:200]}",
            **ids,
        )
    return _classification(
        FailureClass.VERIFIER_UNAVAILABLE,
        f"verification {status.value}: {verification_decision.reason[:200]}",
        **ids,
    )


def classify_pre_submit_block(
    error_code: str,
    *,
    exec_job_id: str,
    attempt_id: str = "attempt-unbound",
    outcome_id: str = "outcome-none-blocked-pre-submit",
) -> FailureClassification:
    """Classify a fail-closed pre-submit block (no outcome exists).

    Maps lease guard codes → LEASE_INVALID and mode/tool guard codes →
    MODE_UNAVAILABLE; anything else → UNKNOWN_ERROR. Deterministic.
    """
    lease_codes = {
        "LEASE_INVALID",
        "LEASE_EXPIRED",
        "LEASE_REVOKED",
        "LEASE_SCOPE_MISMATCH",
        "LEASE_JOB_MISMATCH",
    }
    mode_codes = {"UNSUPPORTED_EXECUTION_MODE", "UNSUPPORTED_TOOL"}
    if error_code in lease_codes:
        failure_class = FailureClass.LEASE_INVALID
        reason = f"submission blocked pre-kernel by lease guard: {error_code}"
    elif error_code in mode_codes:
        failure_class = FailureClass.MODE_UNAVAILABLE
        reason = f"submission blocked pre-kernel by mode guard: {error_code}"
    else:
        failure_class = FailureClass.UNKNOWN_ERROR
        reason = f"submission blocked pre-kernel by unclassified guard: {error_code}"
    return _classification(
        failure_class,
        reason,
        exec_job_id=exec_job_id,
        attempt_id=attempt_id,
        outcome_id=outcome_id,
    )

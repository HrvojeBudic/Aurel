"""P4-EXEC-A AurelExec foundation errors.

Structured, fail-closed error surface for the AurelExec admission and lease
foundation. Raising these errors is contract validation only — it does not
execute, dispatch, submit, retry, roll back, or authorize anything.
"""

from __future__ import annotations

from enum import Enum


class AurelExecErrorCode(str, Enum):
    # request / contract shape
    EMPTY_REQUEST_ID = "EMPTY_REQUEST_ID"
    EMPTY_DECISION_ID = "EMPTY_DECISION_ID"
    EMPTY_LEASE_ID = "EMPTY_LEASE_ID"
    EMPTY_JOB_ID = "EMPTY_JOB_ID"
    EMPTY_ATTEMPT_ID = "EMPTY_ATTEMPT_ID"
    EMPTY_FIELD = "EMPTY_FIELD"
    # truth / boundary posture
    FORBIDDEN_TRUTH_LABEL = "FORBIDDEN_TRUTH_LABEL"
    FORBIDDEN_BOUNDARY_CLAIM = "FORBIDDEN_BOUNDARY_CLAIM"
    # admission
    DECISION_REQUEST_MISMATCH = "DECISION_REQUEST_MISMATCH"
    # lease
    LEASE_DENIED = "LEASE_DENIED"
    LEASE_INVALID = "LEASE_INVALID"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    LEASE_REVOKED = "LEASE_REVOKED"
    LEASE_JOB_MISMATCH = "LEASE_JOB_MISMATCH"
    INVALID_LEASE_WINDOW = "INVALID_LEASE_WINDOW"
    INVALID_MAX_ATTEMPTS = "INVALID_MAX_ATTEMPTS"
    REVOCATION_STATE_MISMATCH = "REVOCATION_STATE_MISMATCH"
    # job / attempt guards
    JOB_DENIED = "JOB_DENIED"
    ATTEMPT_DENIED = "ATTEMPT_DENIED"
    # lifecycle / session / bridge (P4-EXEC-B)
    INVALID_LIFECYCLE_TRANSITION = "INVALID_LIFECYCLE_TRANSITION"
    EMPTY_SESSION_ID = "EMPTY_SESSION_ID"
    INVALID_SESSION_WINDOW = "INVALID_SESSION_WINDOW"
    SESSION_INVALID = "SESSION_INVALID"
    SESSION_REQUIRED = "SESSION_REQUIRED"
    SESSION_JOB_MISMATCH = "SESSION_JOB_MISMATCH"
    UNSUPPORTED_EXECUTION_MODE = "UNSUPPORTED_EXECUTION_MODE"
    UNSUPPORTED_TOOL = "UNSUPPORTED_TOOL"
    LEASE_SCOPE_MISMATCH = "LEASE_SCOPE_MISMATCH"
    BRIDGE_REQUEST_MISMATCH = "BRIDGE_REQUEST_MISMATCH"
    SUBMIT_STATE_INVALID = "SUBMIT_STATE_INVALID"
    RUNTIME_KERNEL_INVALID = "RUNTIME_KERNEL_INVALID"
    # queue / worker / claim / checkpoint (P4-EXEC-C)
    QUEUE_ENTRY_INVALID = "QUEUE_ENTRY_INVALID"
    QUEUE_STATE_INVALID = "QUEUE_STATE_INVALID"
    WORKER_UNAVAILABLE = "WORKER_UNAVAILABLE"
    WORKER_KIND_UNAVAILABLE = "WORKER_KIND_UNAVAILABLE"
    DOUBLE_CLAIM_BLOCKED = "DOUBLE_CLAIM_BLOCKED"
    CLAIM_STATE_INVALID = "CLAIM_STATE_INVALID"
    CLAIM_MISMATCH = "CLAIM_MISMATCH"
    CHECKPOINT_INVALID = "CHECKPOINT_INVALID"
    ROLLBACK_UNAVAILABLE = "ROLLBACK_UNAVAILABLE"
    ERROR = "ERROR"


class AurelExecError(Exception):
    """Base error for the AurelExec foundation."""


class AurelExecValidationError(AurelExecError):
    """Fail-closed validation error carrying a structured code and field."""

    def __init__(self, message: str, *, code: AurelExecErrorCode, field: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


def reject(message: str, *, code: AurelExecErrorCode, field: str) -> None:
    raise AurelExecValidationError(message, code=code, field=field)

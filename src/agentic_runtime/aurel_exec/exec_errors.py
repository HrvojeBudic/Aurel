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

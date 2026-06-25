"""Path governance error taxonomy (P1.7.0)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PathGovernanceErrorCode(str, Enum):
    PATH_GOVERNANCE_UNAVAILABLE = "PATH_GOVERNANCE_UNAVAILABLE"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_ENUM = "INVALID_ENUM"
    INVALID_VERSION = "INVALID_VERSION"
    INVALID_SOURCE_LABEL = "INVALID_SOURCE_LABEL"
    INVALID_TRUST_LABEL = "INVALID_TRUST_LABEL"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    CANONICALIZATION_NOT_AVAILABLE = "CANONICALIZATION_NOT_AVAILABLE"
    RESOLVER_NOT_AVAILABLE = "RESOLVER_NOT_AVAILABLE"
    CLI_NOT_AVAILABLE = "CLI_NOT_AVAILABLE"
    PROJECTION_NOT_AVAILABLE = "PROJECTION_NOT_AVAILABLE"
    ENFORCEMENT_NOT_AVAILABLE = "ENFORCEMENT_NOT_AVAILABLE"
    TRACE_HOOK_NOT_AVAILABLE = "TRACE_HOOK_NOT_AVAILABLE"
    POLICY_BRIDGE_NOT_AVAILABLE = "POLICY_BRIDGE_NOT_AVAILABLE"


@dataclass(frozen=True)
class PathGovernanceStructuredError:
    code: PathGovernanceErrorCode
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class PathGovernanceError(ValueError):
    """Base error for path governance foundation operations."""

    def __init__(
        self,
        message: str,
        *,
        code: PathGovernanceErrorCode | None = None,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.details = details

    def to_structured(self) -> PathGovernanceStructuredError:
        return PathGovernanceStructuredError(
            code=self.code or PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
            message=str(self),
            field=self.field,
            details=self.details,
        )


class PathGovernanceValidationError(PathGovernanceError):
    """Raised when path governance payload fails closed-world or enum validation."""


class PathGovernanceUnknownFieldError(PathGovernanceValidationError):
    """Raised when an unknown field is present — closed-world enforcement."""


class PathGovernanceSerializationError(PathGovernanceError):
    """Raised when canonical serialization fails."""

"""Policy Card error taxonomy (P1.6.0).

Small, explicit error classes for policy card loading, validation,
serialization, and hashing. All errors inherit from PolicyCardError
which itself inherits from ValueError — consistent with the repo
convention of per-module ValueError subclasses.
"""
from __future__ import annotations


class PolicyCardError(ValueError):
    """Base error for all policy card operations."""


class PolicyCardValidationError(PolicyCardError):
    """Raised when a policy card fails structured validation."""


class PolicyCardSerializationError(PolicyCardError):
    """Raised when canonical serialization fails."""


class PolicyCardHashError(PolicyCardError):
    """Raised when canonical hash computation fails."""


class PolicyCardUnknownFieldError(PolicyCardValidationError):
    """Raised when an unknown top-level field is found — closed-world enforcement."""


class PolicyCardUnsafeFieldError(PolicyCardValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""


# ---------------------------------------------------------------------------
# Behavioral Contract errors (P1.6.2)
# ---------------------------------------------------------------------------


class BehavioralContractError(PolicyCardError):
    """Base error for all behavioral contract operations."""


class BehavioralContractValidationError(BehavioralContractError):
    """Raised when a behavioral contract fails structured validation."""


class BehavioralContractSerializationError(BehavioralContractError):
    """Raised when canonical serialization fails."""


class BehavioralContractHashError(BehavioralContractError):
    """Raised when canonical hash computation fails."""


class BehavioralContractUnknownFieldError(BehavioralContractValidationError):
    """Raised when an unknown top-level field is found — closed-world enforcement."""


class BehavioralContractUnsafeFieldError(BehavioralContractValidationError):
    """Raised when a dangerous metadata key or unsafe field is detected."""

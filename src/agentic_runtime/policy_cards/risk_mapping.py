"""Risk vocabulary mapping seed (P1.6.11).

This module deliberately does not unify all Aurel risk vocabularies. It is a
small, explicit bridge from runtime-like and identity/approval strings into the
P1.6 policy-card RiskTier vocabulary used by Custos v0.

Unknown present values map conservatively. Unsupported value types fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .errors import PolicyRiskMappingError
from .risk_tiers import RiskTier


@dataclass(frozen=True)
class RiskMappingResult:
    """Deterministic result of translating one risk vocabulary value."""

    normalized_tier: str | None
    source_family: str
    source_value: str | None
    known: bool
    conservative: bool
    reason_code: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "conservative": self.conservative,
            "known": self.known,
            "normalized_tier": self.normalized_tier,
            "reason_code": self.reason_code,
            "source_family": self.source_family,
            "source_value": self.source_value,
        }


_RUNTIME_RISK_MAP: dict[str, str] = {
    "TRIVIAL": RiskTier.R0.value,
    "LOW": RiskTier.R1.value,
    "MEDIUM": RiskTier.R3.value,
    "HIGH": RiskTier.R4.value,
    "CRITICAL": RiskTier.R6.value,
}

_APPROVAL_RISK_MAP: dict[str, str] = {
    "R0": RiskTier.R0.value,
    "R1": RiskTier.R1.value,
    "R2": RiskTier.R2.value,
    "R3": RiskTier.R3.value,
    "R4": RiskTier.R4.value,
    "R5": RiskTier.R5.value,
    "R6": RiskTier.R6.value,
}

_IDENTITY_RISK_MAP: dict[str, str] = {
    "NONE": RiskTier.R0.value,
    "TRIVIAL": RiskTier.R0.value,
    "LOW": RiskTier.R1.value,
    "LIMITED": RiskTier.R2.value,
    "MEDIUM": RiskTier.R3.value,
    "MODERATE": RiskTier.R3.value,
    "HIGH": RiskTier.R4.value,
    "ELEVATED": RiskTier.R4.value,
    "DANGEROUS": RiskTier.R5.value,
    "CRITICAL": RiskTier.R6.value,
    "FORBIDDEN": RiskTier.R6.value,
}

_CONSERVATIVE_UNKNOWN_TIER = RiskTier.R5.value


def _coerce_value(value: object, source_family: str) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, RiskMappingResult):
        return value.normalized_tier, value.source_value
    if isinstance(value, RiskTier):
        return value.value, value.value
    if isinstance(value, Enum) and isinstance(value.value, str):
        raw = value.value.strip()
        if not raw:
            raise PolicyRiskMappingError(f"{source_family} risk value cannot be empty")
        return raw.upper(), raw
    if isinstance(value, bool) or not isinstance(value, str):
        raise PolicyRiskMappingError(
            f"{source_family} risk value must be a string or RiskTier"
        )
    raw = value.strip()
    if not raw:
        raise PolicyRiskMappingError(f"{source_family} risk value cannot be empty")
    return raw.upper(), raw


def _result(
    *,
    normalized_tier: str | None,
    source_family: str,
    source_value: str | None,
    known: bool,
    conservative: bool,
    reason_code: str,
) -> RiskMappingResult:
    return RiskMappingResult(
        normalized_tier=normalized_tier,
        source_family=source_family,
        source_value=source_value,
        known=known,
        conservative=conservative,
        reason_code=reason_code,
    )


def _unknown(source_family: str, source_value: str | None) -> RiskMappingResult:
    return _result(
        normalized_tier=_CONSERVATIVE_UNKNOWN_TIER,
        source_family=source_family,
        source_value=source_value,
        known=False,
        conservative=True,
        reason_code="UNKNOWN_RISK_CONSERVATIVE",
    )


def map_runtime_risk_to_policy_tier(value: object) -> RiskMappingResult:
    """Map runtime risk strings into P1.6 RiskTier values."""
    normalized, raw = _coerce_value(value, "runtime")
    if normalized is None:
        return _result(
            normalized_tier=None,
            source_family="runtime",
            source_value=None,
            known=False,
            conservative=False,
            reason_code="RISK_NOT_PROVIDED",
        )
    if normalized in _RUNTIME_RISK_MAP:
        tier = _RUNTIME_RISK_MAP[normalized]
        return _result(
            normalized_tier=tier,
            source_family="runtime",
            source_value=raw,
            known=True,
            conservative=tier in {RiskTier.R5.value, RiskTier.R6.value},
            reason_code="RUNTIME_RISK_MAPPED",
        )
    if normalized in _APPROVAL_RISK_MAP:
        return map_approval_risk_to_policy_tier(normalized)
    return _unknown("runtime", raw)


def map_approval_risk_to_policy_tier(value: object) -> RiskMappingResult:
    """Map approval risk classes (R0-R6) into policy tiers."""
    normalized, raw = _coerce_value(value, "approval")
    if normalized is None:
        return _result(
            normalized_tier=None,
            source_family="approval",
            source_value=None,
            known=False,
            conservative=False,
            reason_code="RISK_NOT_PROVIDED",
        )
    if normalized in _APPROVAL_RISK_MAP:
        tier = _APPROVAL_RISK_MAP[normalized]
        reason = "APPROVAL_RISK_MAPPED"
        conservative = tier in {RiskTier.R5.value, RiskTier.R6.value}
        if tier == RiskTier.R5.value:
            reason = "APPROVAL_RISK_R5_CONSERVATIVE"
        elif tier == RiskTier.R6.value:
            reason = "APPROVAL_RISK_R6_CONSERVATIVE"
        return _result(
            normalized_tier=tier,
            source_family="approval",
            source_value=raw,
            known=True,
            conservative=conservative,
            reason_code=reason,
        )
    return _unknown("approval", raw)


def map_identity_risk_to_policy_tier(value: object) -> RiskMappingResult:
    """Map identity/autonomy risk strings into policy tiers."""
    normalized, raw = _coerce_value(value, "identity")
    if normalized is None:
        return _result(
            normalized_tier=None,
            source_family="identity",
            source_value=None,
            known=False,
            conservative=False,
            reason_code="RISK_NOT_PROVIDED",
        )
    if normalized in _IDENTITY_RISK_MAP:
        tier = _IDENTITY_RISK_MAP[normalized]
        return _result(
            normalized_tier=tier,
            source_family="identity",
            source_value=raw,
            known=True,
            conservative=tier in {RiskTier.R5.value, RiskTier.R6.value},
            reason_code="IDENTITY_RISK_MAPPED",
        )
    if normalized in _APPROVAL_RISK_MAP:
        return map_approval_risk_to_policy_tier(normalized)
    return _unknown("identity", raw)


def normalize_risk_tier(value: object) -> RiskMappingResult:
    """Normalize known policy/runtime/approval/identity risk values.

    Unknown present values map to R5 with an explicit conservative reason code.
    Missing values remain missing so callers can distinguish absent context from
    an unknown provided vocabulary value.
    """
    if isinstance(value, RiskMappingResult):
        return value
    normalized, raw = _coerce_value(value, "policy")
    if normalized is None:
        return _result(
            normalized_tier=None,
            source_family="policy",
            source_value=None,
            known=False,
            conservative=False,
            reason_code="RISK_NOT_PROVIDED",
        )
    if normalized in _APPROVAL_RISK_MAP:
        return _result(
            normalized_tier=_APPROVAL_RISK_MAP[normalized],
            source_family="policy",
            source_value=raw,
            known=True,
            conservative=normalized in {RiskTier.R5.value, RiskTier.R6.value},
            reason_code="POLICY_RISK_TIER_PASSTHROUGH",
        )
    if normalized in _RUNTIME_RISK_MAP:
        return map_runtime_risk_to_policy_tier(normalized)
    if normalized in _IDENTITY_RISK_MAP:
        return map_identity_risk_to_policy_tier(normalized)
    return _unknown("policy", raw)

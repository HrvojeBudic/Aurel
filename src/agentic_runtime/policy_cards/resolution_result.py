"""Policy Resolution Result types (P1.6.10 — Custos v0).

Deterministic, hash-ready result structures for shadow-mode policy resolution:
per-family decisions and the aggregated ResolvedPolicySet.

Architectural law:
  - These structures describe judgment, not enforcement.
  - Shadow actions answer "what WOULD happen if enforcement were active".
  - P1.6.10 never disposes; it only proposes a judgment.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping

from .resolution_context import EnforcementMode


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PolicyFamily(str, Enum):
    """Policy card families the resolver can adjudicate. Mirrors PolicyCardKind."""
    RISK_TIER = "risk_tier"
    HUMAN_OVERSIGHT = "human_oversight"
    DATA_RESIDENCY = "data_residency"
    TOOL_PERMISSION = "tool_permission"
    MEMORY_WRITE = "memory_write"
    PROMPT = "prompt"
    SANDBOX = "sandbox"


class FamilyDecision(str, Enum):
    """Per-family (and aggregated) decision label."""
    ALLOW = "allow"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


class ShadowAction(str, Enum):
    """Shadow-mode effective action — explicit WOULD_* semantics."""
    WOULD_ALLOW = "would_allow"
    WOULD_WARN = "would_warn"
    WOULD_REQUIRE_APPROVAL = "would_require_approval"
    WOULD_DENY = "would_deny"
    WOULD_NOT_APPLY = "would_not_apply"
    WOULD_ERROR = "would_error"


# Strictest-wins ordering rank. Higher = stricter / wins.
_DECISION_RANK: dict[FamilyDecision, int] = {
    FamilyDecision.NOT_APPLICABLE: 0,
    FamilyDecision.ALLOW: 1,
    FamilyDecision.WARN: 2,
    FamilyDecision.REQUIRE_APPROVAL: 3,
    FamilyDecision.ERROR: 3,  # conservative: error escalates to approval level
    FamilyDecision.DENY: 4,
}

_DECISION_TO_SHADOW: dict[FamilyDecision, ShadowAction] = {
    FamilyDecision.ALLOW: ShadowAction.WOULD_ALLOW,
    FamilyDecision.WARN: ShadowAction.WOULD_WARN,
    FamilyDecision.REQUIRE_APPROVAL: ShadowAction.WOULD_REQUIRE_APPROVAL,
    FamilyDecision.DENY: ShadowAction.WOULD_DENY,
    FamilyDecision.NOT_APPLICABLE: ShadowAction.WOULD_NOT_APPLY,
    FamilyDecision.ERROR: ShadowAction.WOULD_ERROR,
}


def decision_rank(decision: FamilyDecision) -> int:
    """Strictest-wins rank for a decision (higher wins)."""
    return _DECISION_RANK[decision]


def decision_to_shadow_action(decision: FamilyDecision) -> ShadowAction:
    """Map a family decision to its shadow action."""
    return _DECISION_TO_SHADOW[decision]


# ---------------------------------------------------------------------------
# Per-family decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyFamilyDecision:
    family: PolicyFamily
    decision: FamilyDecision
    effective_shadow_action: ShadowAction
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    approval_requirements: tuple[str, ...] = ()
    applicable_card_ids: tuple[str, ...] = ()
    source_hashes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


def policy_family_decision_to_canonical_dict(
    fd: PolicyFamilyDecision,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "family": fd.family.value,
        "decision": fd.decision.value,
        "effective_shadow_action": fd.effective_shadow_action.value,
        "reason_codes": sorted(fd.reason_codes),
        "warnings": sorted(fd.warnings),
        "violations": sorted(fd.violations),
        "approval_requirements": sorted(fd.approval_requirements),
        "applicable_card_ids": sorted(fd.applicable_card_ids),
        "source_hashes": sorted(fd.source_hashes),
        "metadata": dict(sorted(dict(fd.metadata).items(), key=lambda i: i[0])),
    }
    return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Aggregated resolved policy set
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedPolicySet:
    resolution_id: str
    context_hash: str
    enforcement_mode: EnforcementMode
    overall_decision: FamilyDecision
    effective_shadow_action: ShadowAction
    family_decisions: tuple[PolicyFamilyDecision, ...] = ()
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    approval_requirements: tuple[str, ...] = ()
    applicable_card_ids: tuple[str, ...] = ()
    source_hashes: tuple[str, ...] = ()
    canonical_hash: str | None = None
    conflict_resolution: dict[str, Any] | None = None
    conflict_hash: str | None = None
    resolution_trace: dict[str, Any] | None = None
    resolution_trace_hash: str | None = None
    resolution_trace_id: str | None = None
    violation_trace: dict[str, Any] | None = None
    violation_trace_hash: str | None = None
    violation_trace_id: str | None = None

    # -- shadow convenience predicates ------------------------------------

    @property
    def would_allow(self) -> bool:
        return self.effective_shadow_action == ShadowAction.WOULD_ALLOW

    @property
    def would_warn(self) -> bool:
        return self.effective_shadow_action == ShadowAction.WOULD_WARN

    @property
    def would_require_approval(self) -> bool:
        return self.effective_shadow_action == ShadowAction.WOULD_REQUIRE_APPROVAL

    @property
    def would_deny(self) -> bool:
        return self.effective_shadow_action == ShadowAction.WOULD_DENY

    def with_canonical_hash(self) -> "ResolvedPolicySet":
        """Return a copy with canonical_hash populated (hash excludes itself)."""
        return replace(self, canonical_hash=compute_resolved_policy_set_hash(self))


def resolved_policy_set_to_canonical_dict(
    rps: ResolvedPolicySet,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    """Deterministic canonical dict. The canonical_hash field is excluded from
    the hashed representation (it cannot hash itself)."""
    result: dict[str, Any] = {
        "resolution_id": rps.resolution_id,
        "context_hash": rps.context_hash,
        "enforcement_mode": rps.enforcement_mode.value,
        "overall_decision": rps.overall_decision.value,
        "effective_shadow_action": rps.effective_shadow_action.value,
        "family_decisions": [
            policy_family_decision_to_canonical_dict(fd)
            for fd in sorted(rps.family_decisions, key=lambda d: d.family.value)
        ],
        "reason_codes": sorted(rps.reason_codes),
        "warnings": sorted(rps.warnings),
        "violations": sorted(rps.violations),
        "approval_requirements": sorted(rps.approval_requirements),
        "applicable_card_ids": sorted(rps.applicable_card_ids),
        "source_hashes": sorted(rps.source_hashes),
    }
    if include_hash and rps.canonical_hash is not None:
        result["canonical_hash"] = rps.canonical_hash
    if include_hash and rps.conflict_hash is not None:
        result["conflict_hash"] = rps.conflict_hash
    if include_hash and rps.conflict_resolution is not None:
        result["conflict_resolution"] = rps.conflict_resolution
    if include_hash and rps.resolution_trace is not None:
        result["resolution_trace"] = rps.resolution_trace
    if include_hash and rps.resolution_trace_hash is not None:
        result["resolution_trace_hash"] = rps.resolution_trace_hash
    if include_hash and rps.resolution_trace_id is not None:
        result["resolution_trace_id"] = rps.resolution_trace_id
    if include_hash and rps.violation_trace is not None:
        result["violation_trace"] = rps.violation_trace
    if include_hash and rps.violation_trace_hash is not None:
        result["violation_trace_hash"] = rps.violation_trace_hash
    if include_hash and rps.violation_trace_id is not None:
        result["violation_trace_id"] = rps.violation_trace_id
    return dict(sorted(result.items(), key=lambda i: i[0]))


def serialize_resolved_policy_set_canonical(rps: ResolvedPolicySet) -> str:
    canonical = resolved_policy_set_to_canonical_dict(rps, include_hash=False)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def compute_resolved_policy_set_hash(rps: ResolvedPolicySet) -> str:
    canonical = serialize_resolved_policy_set_canonical(rps)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

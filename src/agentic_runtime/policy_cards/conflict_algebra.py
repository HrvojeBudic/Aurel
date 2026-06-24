"""Policy Conflict Algebra & Strictest-Wins Rules (P1.6.13).

Deterministic, JSON-safe, hash-ready conflict algebra for Custos shadow
policy decisions. This module formalizes conflict detection, ranking,
classification, and deterministic resolution.

P1.6.13 makes Custos explain why one shadow decision beats another.
It formalizes conflict — it does NOT enforce policy decisions, activate
approvals, block commands, or change runtime sandbox behavior.

Core law:
  - The strictest valid policy outcome wins.
  - Ambiguity must be explicit.
  - Adapter errors must be explicit.
  - Unknown context must be conservative.
  - Tie-breaks must be deterministic.
  - Everything must be hash-ready and trace-ready.
  - Nothing is enforced.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping, Sequence

if TYPE_CHECKING:
    from .resolution_context import PolicyResolutionContext  # pragma: no cover
    from .resolution_result import (  # pragma: no cover
        FamilyDecision,
        PolicyFamily,
        PolicyFamilyDecision,
    )


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PolicyDecisionRank(int, Enum):
    """Strictness rank for a policy decision. Higher = stricter / wins.

    ERROR is the conservative highest rank for adapter failure, policy design
    error, insufficient context, unknown decision, or invalid result shape.
    ERROR does not mean 'raise and crash'.
    """
    NOT_APPLICABLE = 0
    ALLOW = 1
    WARN = 2
    REQUIRE_APPROVAL = 3
    DENY = 4
    ERROR = 5


class PolicyConflictType(str, Enum):
    """Deterministic conflict taxonomy for shadow governance."""
    STRICTNESS_CONFLICT = "strictness_conflict"
    FAMILY_CONFLICT = "family_conflict"
    SCOPE_CONFLICT = "scope_conflict"
    RISK_MAPPING_CONFLICT = "risk_mapping_conflict"
    APPROVAL_REQUIREMENT_CONFLICT = "approval_requirement_conflict"
    SANDBOX_POSTURE_CONFLICT = "sandbox_posture_conflict"
    DATA_RESIDENCY_CONFLICT = "data_residency_conflict"
    TOOL_PERMISSION_CONFLICT = "tool_permission_conflict"
    PROMPT_AUTHORITY_CONFLICT = "prompt_authority_conflict"
    MEMORY_WRITE_CONFLICT = "memory_write_conflict"
    CONSERVATIVE_UNKNOWN_CONTEXT = "conservative_unknown_context"
    POLICY_DESIGN_ERROR = "policy_design_error"
    ADAPTER_ERROR = "adapter_error"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class PolicyConflictSeverity(str, Enum):
    """Conflict severity classification."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyConflictResolutionStrategy(str, Enum):
    """Resolution strategy for handling conflicting policy decisions."""
    STRICTEST_WINS = "strictest_wins"
    CONSERVATIVE_UNKNOWN = "conservative_unknown"
    STABLE_TIE_BREAK = "stable_tie_break"
    NO_APPLICABLE_POLICY = "no_applicable_policy"
    ADAPTER_ERROR_CAPTURED = "adapter_error_captured"


# ---------------------------------------------------------------------------
# Family order for stable tie-break
# ---------------------------------------------------------------------------

_FAMILY_ORDER: frozenset[str] = frozenset({
    "risk_tier",
    "human_oversight",
    "data_residency",
    "tool_permission",
    "memory_write",
    "prompt",
    "sandbox",
})

_FAMILY_ORDER_INDEX: dict[str, int] = {f: i for i, f in enumerate(sorted(_FAMILY_ORDER))}


# ---------------------------------------------------------------------------
# Normalization maps
# ---------------------------------------------------------------------------

_WOULD_TO_RANK: dict[str, PolicyDecisionRank] = {
    "would_not_apply": PolicyDecisionRank.NOT_APPLICABLE,
    "would_allow": PolicyDecisionRank.ALLOW,
    "would_warn": PolicyDecisionRank.WARN,
    "would_require_approval": PolicyDecisionRank.REQUIRE_APPROVAL,
    "would_deny": PolicyDecisionRank.DENY,
    "would_error": PolicyDecisionRank.ERROR,
}

_DECISION_TO_RANK: dict[str, PolicyDecisionRank] = {
    "not_applicable": PolicyDecisionRank.NOT_APPLICABLE,
    "allow": PolicyDecisionRank.ALLOW,
    "warn": PolicyDecisionRank.WARN,
    "require_approval": PolicyDecisionRank.REQUIRE_APPROVAL,
    "deny": PolicyDecisionRank.DENY,
    "error": PolicyDecisionRank.ERROR,
}

_EXTENDED_LABEL_TO_RANK: dict[str, PolicyDecisionRank] = {
    **_WOULD_TO_RANK,
    **_DECISION_TO_RANK,
    "block": PolicyDecisionRank.DENY,
    "blocked": PolicyDecisionRank.DENY,
    "approval_required": PolicyDecisionRank.REQUIRE_APPROVAL,
    "adapter_error": PolicyDecisionRank.ERROR,
    "unknown_error": PolicyDecisionRank.ERROR,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicySpecificityScore:
    """Deterministic secondary tie-break ranking for same-rank decisions.

    Specificity is a tie-break ONLY after strictness. Specific ALLOW must
    never override general DENY. Specific WARN must never override DENY.
    """
    scope_specificity: int = 0
    family_specificity: int = 0
    risk_specificity: int = 0
    tool_specificity: int = 0
    action_specificity: int = 0
    data_specificity: int = 0
    sandbox_specificity: int = 0
    total_score: int = 0

    def __post_init__(self) -> None:
        computed = (
            self.scope_specificity
            + self.family_specificity
            + self.risk_specificity
            + self.tool_specificity
            + self.action_specificity
            + self.data_specificity
            + self.sandbox_specificity
        )
        if self.total_score != 0 and self.total_score != computed:
            object.__setattr__(self, "total_score", computed)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "scope_specificity": self.scope_specificity,
            "family_specificity": self.family_specificity,
            "risk_specificity": self.risk_specificity,
            "tool_specificity": self.tool_specificity,
            "action_specificity": self.action_specificity,
            "data_specificity": self.data_specificity,
            "sandbox_specificity": self.sandbox_specificity,
            "total_score": self.total_score,
        }


@dataclass(frozen=True)
class PolicyPrecedenceRule:
    """Encodes stable tie-break: rank > specificity > family_order > lexical."""
    rank_priority: int = 0
    specificity_priority: int = 0
    family_priority: int = 0
    card_priority: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "rank_priority": self.rank_priority,
            "specificity_priority": self.specificity_priority,
            "family_priority": self.family_priority,
            "card_priority": self.card_priority,
        }


@dataclass(frozen=True)
class PolicyConflict:
    """Single conflict record between policy decisions."""
    conflict_type: PolicyConflictType
    severity: PolicyConflictSeverity
    description: str
    involved_families: tuple[str, ...] = ()
    decision_ranks: tuple[str, ...] = ()
    family_decisions_count: int = 0

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "involved_families": sorted(self.involved_families),
            "decision_ranks": sorted(self.decision_ranks),
            "family_decisions_count": self.family_decisions_count,
        }


@dataclass(frozen=True)
class PolicyConflictSet:
    """Collection of policy conflicts with deterministic canonical representation."""
    conflicts: tuple[PolicyConflict, ...] = ()
    total_decisions: int = 0
    distinct_families: int = 0
    distinct_ranks: int = 0

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "conflicts": [c.to_canonical_dict() for c in self.conflicts],
            "total_decisions": self.total_decisions,
            "distinct_families": self.distinct_families,
            "distinct_ranks": self.distinct_ranks,
        }

    def compute_hash(self) -> str:
        canonical = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicyConflictResolution:
    """Resolved outcome of strictest-wins conflict algebra."""
    winning_rank: PolicyDecisionRank = PolicyDecisionRank.NOT_APPLICABLE
    winning_family: str | None = None
    winning_card_ids: tuple[str, ...] = ()
    strategy: PolicyConflictResolutionStrategy = PolicyConflictResolutionStrategy.NO_APPLICABLE_POLICY
    family_decision_count: int = 0
    distinct_ranks: tuple[str, ...] = ()
    conflict_codes: tuple[PolicyConflictType, ...] = ()
    all_decisions: tuple[dict[str, Any], ...] = ()
    conflict_set: PolicyConflictSet | None = None
    summary: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "winning_rank": self.winning_rank.name,
            "winning_family": self.winning_family,
            "winning_card_ids": sorted(self.winning_card_ids),
            "strategy": self.strategy.value,
            "family_decision_count": self.family_decision_count,
            "distinct_ranks": sorted(self.distinct_ranks),
            "conflict_codes": sorted(c.value for c in self.conflict_codes),
            "summary": self.summary,
        }
        if self.conflict_set is not None:
            result["conflict_set"] = self.conflict_set.to_canonical_dict()
        return result

    def compute_hash(self) -> str:
        canonical = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StrictestWinsResult:
    """Convenience result bundling the conflict resolution with its hash."""
    resolution: PolicyConflictResolution
    conflict_hash: str
    family_decision_count: int = 0

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "resolution": self.resolution.to_canonical_dict(),
            "conflict_hash": self.conflict_hash,
            "family_decision_count": self.family_decision_count,
        }


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def normalize_policy_decision_rank(
    decision: object,
) -> PolicyDecisionRank:
    """Map a FamilyDecision, ShadowAction, or string to a PolicyDecisionRank.

    Unknown present values map conservatively to ERROR.
    None / empty string returns NOT_APPLICABLE.
    """
    if decision is None:
        return PolicyDecisionRank.NOT_APPLICABLE

    # Handle enum objects
    raw: str | None = None
    if hasattr(decision, "value"):
        raw = str(getattr(decision, "value"))
    elif isinstance(decision, str):
        raw = decision.strip().lower()

    if not raw:
        return PolicyDecisionRank.NOT_APPLICABLE

    lowered = raw.lower()
    # Direct int enum lookup
    if isinstance(decision, PolicyDecisionRank):
        return decision

    # WOULD_* / decision label lookups
    rank = _EXTENDED_LABEL_TO_RANK.get(lowered)
    if rank is not None:
        return rank

    # Conservative: unknown present value
    return PolicyDecisionRank.ERROR


def decision_rank_value(rank: PolicyDecisionRank) -> int:
    """Numeric value for ranking. Higher = stricter."""
    return int(rank)


def rank_is_stricter(a: PolicyDecisionRank, b: PolicyDecisionRank) -> bool:
    """True if rank a outranks (is stricter than) rank b."""
    return int(a) > int(b)


def strictest_rank(ranks: Sequence[PolicyDecisionRank]) -> PolicyDecisionRank:
    """Returns the highest (strictest) rank from a collection."""
    if not ranks:
        return PolicyDecisionRank.NOT_APPLICABLE
    return max(ranks, key=int)


def _family_name_from_fd(fd: object) -> str:
    """Extract family name as a plain string from a family decision object.
    Handles str-Enum members that don't coerce via str() in Python 3.12+."""
    fam = getattr(fd, "family", "")
    if hasattr(fam, "value"):
        return str(getattr(fam, "value"))
    return str(fam or "")


def _family_index(family_name: str | None) -> int:
    if family_name is None:
        return 999
    return _FAMILY_ORDER_INDEX.get(family_name.lower(), 999)


# ---------------------------------------------------------------------------
# Specificity scoring
# ---------------------------------------------------------------------------


def compute_specificity_score(
    family_decision: object,
) -> PolicySpecificityScore:
    """Compute a deterministic specificity score for a family decision.

    Specificity is a tie-break ONLY after strictness rank. Higher specificity
    never allows a less-strict decision to override a stricter decision.
    """
    scores: dict[str, int] = {
        "scope_specificity": 0,
        "family_specificity": 0,
        "risk_specificity": 0,
        "tool_specificity": 0,
        "action_specificity": 0,
        "data_specificity": 0,
        "sandbox_specificity": 0,
    }

    fd = family_decision
    reasons: tuple[str, ...] = tuple(getattr(fd, "reason_codes", ()) or ())
    fam_val = _family_name_from_fd(fd).lower() if hasattr(fd, "family") else ""
    card_ids: tuple[str, ...] = tuple(getattr(fd, "applicable_card_ids", ()) or ())
    approval: tuple[str, ...] = tuple(getattr(fd, "approval_requirements", ()) or ())
    violations: tuple[str, ...] = tuple(getattr(fd, "violations", ()) or ())
    meta: Mapping[str, Any] = dict(getattr(fd, "metadata", {}) or {})

    # Scope specificity: tool/action scoped > family-wide
    if card_ids:
        scores["scope_specificity"] = min(3, len(card_ids))
    if any("TOOL_" in r for r in reasons):
        scores["scope_specificity"] = max(scores["scope_specificity"], 4)
    if any("SANDBOX_" in r for r in reasons):
        scores["scope_specificity"] = max(scores["scope_specificity"], 4)

    # Family specificity
    if fam_val:
        scores["family_specificity"] = 1

    # Risk specificity: explicit risk tier / ceiling
    if any("RISK_" in r for r in reasons):
        scores["risk_specificity"] = min(5, 1 + len([r for r in reasons if "RISK_" in r]))
    if meta.get("risk_tier"):
        scores["risk_specificity"] = max(scores["risk_specificity"], 3)

    # Tool specificity
    if any("TOOL_" in r for r in reasons):
        scores["tool_specificity"] = min(5, 1 + len([r for r in reasons if "TOOL_" in r]))

    # Action specificity: approval requirements, violations
    if approval:
        scores["action_specificity"] = min(5, 1 + len(approval))
    if violations:
        scores["action_specificity"] = max(scores["action_specificity"], 3)

    # Data specificity
    if any("DATA_" in r for r in reasons):
        scores["data_specificity"] = min(5, 1 + len([r for r in reasons if "DATA_" in r]))

    # Sandbox specificity
    if any("SANDBOX_" in r for r in reasons):
        scores["sandbox_specificity"] = min(5, 1 + len([r for r in reasons if "SANDBOX_" in r]))

    total = sum(scores.values())
    return PolicySpecificityScore(
        scope_specificity=scores["scope_specificity"],
        family_specificity=scores["family_specificity"],
        risk_specificity=scores["risk_specificity"],
        tool_specificity=scores["tool_specificity"],
        action_specificity=scores["action_specificity"],
        data_specificity=scores["data_specificity"],
        sandbox_specificity=scores["sandbox_specificity"],
        total_score=total,
    )


def stable_decision_sort_key(fd: object) -> tuple[int, int, int, str]:
    """Deterministic sort key: rank descending, specificity descending,
    family lexical order, card IDs lexical."""
    rank_val = int(normalize_policy_decision_rank(getattr(fd, "decision", None)))
    specificity = compute_specificity_score(fd).total_score
    fam_name = _family_name_from_fd(fd).lower() if hasattr(fd, "family") else ""
    card_ids = tuple(sorted(getattr(fd, "applicable_card_ids", ()) or ()))
    card_key = "|".join(card_ids) if card_ids else fam_name
    # Negative rank/specificity for descending order
    return (-rank_val, -specificity, _family_index(fam_name), card_key)


# ---------------------------------------------------------------------------
# Conflict classification
# ---------------------------------------------------------------------------


def classify_policy_conflicts(
    *,
    family_decisions: Sequence[object],
    context: object | None = None,
) -> PolicyConflictSet:
    """Classify conflicts across a set of family decisions.

    Detects rank, family, risk, approval, sandbox, data, tool, prompt,
    memory, adapter error, and context-related conflict types.
    """
    fds = tuple(family_decisions)
    conflicts: list[PolicyConflict] = []

    if not fds:
        return PolicyConflictSet(conflicts=(), total_decisions=0)

    # Map decisions to ranks
    norm_map: dict[str, PolicyDecisionRank] = {}
    ranks: set[PolicyDecisionRank] = set()
    error_families: list[str] = []
    families: set[str] = set()
    applicable: list[object] = []

    for fd in fds:
        fam = _family_name_from_fd(fd) if hasattr(fd, "family") else ""
        decision = getattr(fd, "decision", None)
        rank = normalize_policy_decision_rank(decision)
        norm_map[fam] = rank
        ranks.add(rank)
        families.add(fam)
        if rank == PolicyDecisionRank.ERROR:
            error_families.append(fam)
        if rank != PolicyDecisionRank.NOT_APPLICABLE:
            applicable.append(fd)

    total = len(fds)

    # ADAPTER_ERROR
    if error_families:
        conflicts.append(PolicyConflict(
            conflict_type=PolicyConflictType.ADAPTER_ERROR,
            severity=PolicyConflictSeverity.CRITICAL,
            description=f"adapter error in family(s): {', '.join(sorted(error_families))}",
            involved_families=tuple(sorted(error_families)),
            decision_ranks=tuple(r.name for r in ranks),
            family_decisions_count=total,
        ))

    # INSUFFICIENT_CONTEXT — check context fields
    ctx_fields_present = 0
    if context is not None:
        for attr in ("risk_tier", "tool_name", "tool_category", "prompt_source_types",
                     "data_classes", "memory_write_intent"):
            val = getattr(context, attr, None)
            if val and (isinstance(val, bool) or (isinstance(val, (list, tuple)) and len(val) > 0)):
                ctx_fields_present += 1
    if ctx_fields_present == 0 and context is not None:
        conflicts.append(PolicyConflict(
            conflict_type=PolicyConflictType.INSUFFICIENT_CONTEXT,
            severity=PolicyConflictSeverity.HIGH,
            description="no actionable fields present in resolution context",
            involved_families=tuple(sorted(families)),
            decision_ranks=tuple(r.name for r in ranks),
            family_decisions_count=total,
        ))

    # STRICTNESS_CONFLICT: ranks differ
    if len(ranks) > 1:
        rank_names = sorted(r.name for r in ranks)
        strictest = strictest_rank(list(ranks))
        conflicts.append(PolicyConflict(
            conflict_type=PolicyConflictType.STRICTNESS_CONFLICT,
            severity=PolicyConflictSeverity.HIGH if strictest >= PolicyDecisionRank.DENY else PolicyConflictSeverity.MEDIUM,
            description=f"multiple decision ranks present: {rank_names}",
            involved_families=tuple(sorted(families)),
            decision_ranks=tuple(rank_names),
            family_decisions_count=total,
        ))

    # FAMILY_CONFLICT: multiple families with applicable outcomes
    if len(applicable) > 1:
        fams = sorted({str(getattr(f, "family", "")) for f in applicable})
        if len(fams) > 1:
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.FAMILY_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM,
                description=f"multiple applicable families: {fams}",
                involved_families=tuple(fams),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

    # Per-family metadata conflict detection
    _check_metadata_conflicts(fds, norm_map, conflicts)

    return PolicyConflictSet(
        conflicts=tuple(conflicts),
        total_decisions=total,
        distinct_families=len(families),
        distinct_ranks=len(ranks),
    )


def _check_metadata_conflicts(
    fds: Sequence[object],
    norm_map: dict[str, PolicyDecisionRank],
    conflicts: list[PolicyConflict],
) -> None:
    """Inspect reason_codes across families for specific taxonomy signals."""
    total = len(fds)
    ranks: set[PolicyDecisionRank] = set(norm_map.values())

    for fd in fds:
        fam = _family_name_from_fd(fd)
        reasons: tuple[str, ...] = tuple(getattr(fd, "reason_codes", ()) or ())
        approvals: tuple[str, ...] = tuple(getattr(fd, "approval_requirements", ()) or ())
        violations: tuple[str, ...] = tuple(getattr(fd, "violations", ()) or ())
        decision = getattr(fd, "decision", None)
        rank = normalize_policy_decision_rank(decision)

        # RISK_MAPPING_CONFLICT
        if any("RISK_" in r for r in reasons):
            if rank not in (PolicyDecisionRank.ALLOW, PolicyDecisionRank.NOT_APPLICABLE):
                conflicts.append(PolicyConflict(
                    conflict_type=PolicyConflictType.RISK_MAPPING_CONFLICT,
                    severity=PolicyConflictSeverity.LOW if rank == PolicyDecisionRank.WARN else PolicyConflictSeverity.MEDIUM,
                    description=f"risk-related conflict in {fam}: {[r for r in reasons if 'RISK_' in r]}",
                    involved_families=(fam,),
                    decision_ranks=tuple(r.name for r in ranks),
                    family_decisions_count=total,
                ))

        # APPROVAL_REQUIREMENT_CONFLICT
        if approvals and len(approvals) > 0:
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.APPROVAL_REQUIREMENT_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM,
                description=f"approval required by {fam}: {sorted(approvals)}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # SANDBOX_POSTURE_CONFLICT
        if any("SANDBOX_" in r for r in reasons):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.SANDBOX_POSTURE_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM,
                description=f"sandbox posture conflict in {fam}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # DATA_RESIDENCY_CONFLICT
        if any("DATA_" in r for r in reasons):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.DATA_RESIDENCY_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM if rank >= PolicyDecisionRank.REQUIRE_APPROVAL else PolicyConflictSeverity.LOW,
                description=f"data residency conflict in {fam}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # TOOL_PERMISSION_CONFLICT
        if any("TOOL_" in r for r in reasons):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.TOOL_PERMISSION_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM,
                description=f"tool permission conflict in {fam}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # PROMPT_AUTHORITY_CONFLICT
        if any("PROMPT_" in r for r in reasons):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.PROMPT_AUTHORITY_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM,
                description=f"prompt authority conflict in {fam}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # MEMORY_WRITE_CONFLICT
        if any("MEMORY_" in r for r in reasons):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.MEMORY_WRITE_CONFLICT,
                severity=PolicyConflictSeverity.MEDIUM,
                description=f"memory write conflict in {fam}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # CONSERVATIVE_UNKNOWN_CONTEXT
        if any("UNKNOWN" in r for r in reasons):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.CONSERVATIVE_UNKNOWN_CONTEXT,
                severity=PolicyConflictSeverity.HIGH if rank >= PolicyDecisionRank.REQUIRE_APPROVAL else PolicyConflictSeverity.LOW,
                description=f"unknown context in {fam}: {[r for r in reasons if 'UNKNOWN' in r]}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))

        # POLICY_DESIGN_ERROR — invalid/incompatible shape
        if violations and any("incompatible" in v.lower() or "invalid" in v.lower() for v in violations):
            conflicts.append(PolicyConflict(
                conflict_type=PolicyConflictType.POLICY_DESIGN_ERROR,
                severity=PolicyConflictSeverity.CRITICAL,
                description=f"policy design error in {fam}",
                involved_families=(fam,),
                decision_ranks=tuple(r.name for r in ranks),
                family_decisions_count=total,
            ))


# ---------------------------------------------------------------------------
# Strictest-wins resolution
# ---------------------------------------------------------------------------


def _fd_to_dict(fd: object) -> dict[str, Any]:
    """Serialize a family decision to a deterministic dict for evidence."""
    fam = _family_name_from_fd(fd)
    decision_val = getattr(fd, "decision", "")
    decision = str(getattr(decision_val, "value", decision_val))
    reasons: tuple[str, ...] = tuple(getattr(fd, "reason_codes", ()) or ())
    card_ids: tuple[str, ...] = tuple(getattr(fd, "applicable_card_ids", ()) or ())
    return {
        "family": fam,
        "decision": decision,
        "rank": normalize_policy_decision_rank(decision).name,
        "reason_codes": sorted(reasons),
        "applicable_card_ids": sorted(card_ids),
    }


def resolve_policy_conflicts_strictest_wins(
    *,
    family_decisions: Sequence[object],
    context: object | None = None,
) -> PolicyConflictResolution:
    """Resolve conflicts using strictest-wins deterministic algebra.

    Args:
        family_decisions: sequence of PolicyFamilyDecision-like objects.
        context: optional PolicyResolutionContext for classification.

    Returns:
        PolicyConflictResolution with winning rank, family, strategy, conflict
        codes, and all evidence preserved.
    """
    fds = tuple(family_decisions)

    # Empty: no applicable policy
    if not fds:
        return PolicyConflictResolution(
            winning_rank=PolicyDecisionRank.NOT_APPLICABLE,
            strategy=PolicyConflictResolutionStrategy.NO_APPLICABLE_POLICY,
            summary="no policy-family decisions provided — no applicable policy",
        )

    # Map ranks
    decision_ranks: dict[str, PolicyDecisionRank] = {}
    all_card_ids: list[str] = []
    for fd in fds:
        decision = getattr(fd, "decision", None)
        rank = normalize_policy_decision_rank(decision)
        fam = _family_name_from_fd(fd)
        decision_ranks[fam] = rank
        card_ids = getattr(fd, "applicable_card_ids", ())
        if isinstance(card_ids, (list, tuple)):
            all_card_ids.extend(str(c) for c in card_ids)

    applicable = [
        fd for fd in fds
        if normalize_policy_decision_rank(getattr(fd, "decision", None))
        != PolicyDecisionRank.NOT_APPLICABLE
    ]

    # Single decision: return directly
    if len(applicable) == 1:
        fd = applicable[0]
        rank = normalize_policy_decision_rank(getattr(fd, "decision", None))
        fam = _family_name_from_fd(fd)
        card_ids = tuple(sorted(str(c) for c in (getattr(fd, "applicable_card_ids", ()) or ())))
        distinct = tuple(sorted({r.name for r in (rank,)}))
        return PolicyConflictResolution(
            winning_rank=rank,
            winning_family=fam,
            winning_card_ids=card_ids,
            strategy=PolicyConflictResolutionStrategy.STRICTEST_WINS,
            family_decision_count=len(fds),
            distinct_ranks=distinct,
            conflict_codes=(),
            all_decisions=tuple(_fd_to_dict(fd) for fd in fds),
            conflict_set=classify_policy_conflicts(
                family_decisions=fds, context=context,
            ),
            summary=f"single applicable family '{fam}' — {rank.name.lower()}",
        )

    # Multiple decisions: strictest-wins
    if not applicable:
        return PolicyConflictResolution(
            winning_rank=PolicyDecisionRank.NOT_APPLICABLE,
            strategy=PolicyConflictResolutionStrategy.NO_APPLICABLE_POLICY,
            family_decision_count=len(fds),
            distinct_ranks=tuple(sorted({r.name for r in decision_ranks.values()})),
            all_decisions=tuple(_fd_to_dict(fd) for fd in fds),
            conflict_set=classify_policy_conflicts(
                family_decisions=fds, context=context,
            ),
            summary="no applicable family decisions — no applicable policy",
        )

    # Find strictest rank among applicable
    ranks = [normalize_policy_decision_rank(getattr(fd, "decision", None)) for fd in applicable]
    strictest = strictest_rank(ranks)

    # Find candidates at strictest rank
    candidates = [
        fd for fd in applicable
        if normalize_policy_decision_rank(getattr(fd, "decision", None)) == strictest
    ]

    # Deterministic winner selection: specificity -> family order -> card ID lexical
    winner = candidates[0] if len(candidates) == 1 else max(
        candidates,
        key=lambda fd: (
            compute_specificity_score(fd).total_score,
            -_family_index(_family_name_from_fd(fd)),
        ),
    )
    if len(candidates) > 1 and all(
        compute_specificity_score(fd).total_score
        == compute_specificity_score(winner).total_score
        and _family_index(_family_name_from_fd(fd))
        == _family_index(_family_name_from_fd(winner))
        for fd in candidates
    ):
        # Fall back to lexical card ID tie-break
        def _card_ids_key(fd: object) -> str:
            cids = tuple(sorted(str(c) for c in (getattr(fd, "applicable_card_ids", ()) or ())))
            return "|".join(cids) if cids else _family_name_from_fd(fd)

        winner = min(candidates, key=_card_ids_key)

    win_rank = normalize_policy_decision_rank(getattr(winner, "decision", None))
    win_fam = _family_name_from_fd(winner)
    win_cards = tuple(sorted(str(c) for c in (getattr(winner, "applicable_card_ids", ()) or ())))

    # Determine strategy
    has_error = any(
        normalize_policy_decision_rank(getattr(fd, "decision", None)) == PolicyDecisionRank.ERROR
        for fd in fds
    )
    distinct_ranks_set = {normalize_policy_decision_rank(getattr(fd, "decision", None)) for fd in fds}
    distinct_ranks_names = tuple(sorted(r.name for r in distinct_ranks_set))

    if has_error:
        strategy = PolicyConflictResolutionStrategy.ADAPTER_ERROR_CAPTURED
    elif len(distinct_ranks_set) > 1:
        strategy = PolicyConflictResolutionStrategy.STRICTEST_WINS
    else:
        strategy = PolicyConflictResolutionStrategy.STABLE_TIE_BREAK

    conflict_set = classify_policy_conflicts(family_decisions=fds, context=context)
    conflict_codes = tuple(c.conflict_type for c in conflict_set.conflicts)

    summary_parts = [f"{win_rank.name.lower()} by {win_fam}"]
    if has_error:
        summary_parts.append("(adapter errors captured)")
    if len(candidates) > 1:
        summary_parts.append("(tie-broken by specificity)")

    return PolicyConflictResolution(
        winning_rank=win_rank,
        winning_family=win_fam,
        winning_card_ids=win_cards,
        strategy=strategy,
        family_decision_count=len(fds),
        distinct_ranks=distinct_ranks_names,
        conflict_codes=conflict_codes,
        all_decisions=tuple(_fd_to_dict(fd) for fd in fds),
        conflict_set=conflict_set,
        summary=" ".join(summary_parts),
    )

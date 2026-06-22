"""P1.5.7 — Evidence-to-Claim Binding + Sparse Binding Readiness.

Binds evaluation evidence (CapabilityEvidenceRecord) to capability claims.
Binding is claim impact modeling — it is NOT claim verification.

Does NOT verify capabilities, mutate final claim status, create VERIFIED status,
or implement Sparse Context Compiler / SSA / subquadratic model attention.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .capability_evidence import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
    capability_evidence_record_to_dict,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ClaimBindingRelationship(str, Enum):
    SUPPORTS = "SUPPORTS"
    PARTIALLY_SUPPORTS = "PARTIALLY_SUPPORTS"
    WEAKENS = "WEAKENS"
    CONFLICTS = "CONFLICTS"
    BLOCKS = "BLOCKS"
    INSUFFICIENT = "INSUFFICIENT"
    IRRELEVANT = "IRRELEVANT"
    UNKNOWN = "UNKNOWN"


class ClaimBindingStatus(str, Enum):
    DRAFT = "DRAFT"
    BOUND = "BOUND"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTED = "CONFLICTED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    REJECTED = "REJECTED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class ClaimSupportLevel(str, Enum):
    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    UNKNOWN = "UNKNOWN"


class ClaimConflictLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P157_INVARIANTS: tuple[str, ...] = (
    "INV-P157-01: Evidence-to-claim binding does not verify capability.",
    "INV-P157-02: Binding does not mutate final claim status.",
    "INV-P157-03: SUPPORTS requires usable evidence.",
    "INV-P157-04: Strong evidence creates strong support, not verification.",
    "INV-P157-05: Conflicted evidence blocks support.",
    "INV-P157-06: Revoked/invalid evidence cannot support claim.",
    "INV-P157-07: Stale evidence cannot strongly support claim by default.",
    "INV-P157-08: No numeric scoring is introduced.",
    "INV-P157-09: Binding decisions are inputs to later verification levels.",
    "INV-P157-10: P1.5.8 is the next module.",
    "INV-P157-SC-01: Sparse-context evidence can bind to sparse-related claims.",
    "INV-P157-SC-02: Lost-context-risk evidence can weaken or block a claim.",
    "INV-P157-SC-03: Sparse binding does not implement Sparse Context Compiler, retrieval router, evidence graph builder, SSA or true subquadratic attention.",
)

_STRENGTH_TO_SUPPORT: dict[CapabilityEvidenceStrength, ClaimSupportLevel] = {
    CapabilityEvidenceStrength.NONE: ClaimSupportLevel.NONE,
    CapabilityEvidenceStrength.WEAK: ClaimSupportLevel.WEAK,
    CapabilityEvidenceStrength.ADEQUATE: ClaimSupportLevel.MODERATE,
    CapabilityEvidenceStrength.STRONG: ClaimSupportLevel.STRONG,
    CapabilityEvidenceStrength.CONFLICTED: ClaimSupportLevel.NONE,
    CapabilityEvidenceStrength.UNKNOWN: ClaimSupportLevel.UNKNOWN,
}

_BLOCKING_STATUSES = frozenset({
    CapabilityEvidenceStatus.INVALID,
    CapabilityEvidenceStatus.REVOKED,
    CapabilityEvidenceStatus.REJECTED,
    CapabilityEvidenceStatus.CONFLICTED,
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceClaimBinding:
    binding_id: str

    claim_id: str
    capability_id: str | None

    evidence_id: str
    source_result_ids: tuple[str, ...]
    source_result_set_ids: tuple[str, ...]

    relationship: ClaimBindingRelationship
    status: ClaimBindingStatus

    support_level: ClaimSupportLevel
    conflict_level: ClaimConflictLevel

    evidence_status: str
    evidence_strength: str
    evidence_kind: str

    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    summary: str = ""


@dataclass(frozen=True)
class EvidenceClaimBindingPolicy:
    policy_id: str

    require_usable_evidence_for_support: bool = True
    block_conflicted_evidence: bool = True
    block_revoked_or_invalid_evidence: bool = True
    allow_stale_evidence_to_support: bool = False
    allow_single_evidence_to_verify_claim: bool = False

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceClaimBindingDecision:
    decision_id: str
    claim_id: str
    capability_id: str | None

    bindings: tuple[EvidenceClaimBinding, ...]

    aggregate_relationship: ClaimBindingRelationship
    aggregate_status: ClaimBindingStatus
    aggregate_support_level: ClaimSupportLevel
    aggregate_conflict_level: ClaimConflictLevel

    usable_evidence_ids: tuple[str, ...]
    insufficient_evidence_ids: tuple[str, ...]
    conflicted_evidence_ids: tuple[str, ...]
    blocked_evidence_ids: tuple[str, ...]

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    summary: str = ""


@dataclass(frozen=True)
class EvidenceClaimBindingReport:
    report_id: str
    status: str
    summary: str

    bindings_created: int
    binding_decisions_created: int

    sparse_binding_ready: bool

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    next_module: str


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def build_default_evidence_claim_binding_policy() -> EvidenceClaimBindingPolicy:
    return EvidenceClaimBindingPolicy(
        policy_id="default_p157",
        require_usable_evidence_for_support=True,
        block_conflicted_evidence=True,
        block_revoked_or_invalid_evidence=True,
        allow_stale_evidence_to_support=False,
        allow_single_evidence_to_verify_claim=False,
    )


# ---------------------------------------------------------------------------
# Evidence-to-claim binding
# ---------------------------------------------------------------------------


def bind_evidence_to_claim(
    *,
    binding_id: str,
    claim_id: str,
    evidence: CapabilityEvidenceRecord,
    capability_id: str | None = None,
    policy: EvidenceClaimBindingPolicy | None = None,
) -> EvidenceClaimBinding:
    if policy is None:
        policy = build_default_evidence_claim_binding_policy()

    estatus = evidence.status
    estrength = evidence.strength

    relationship: ClaimBindingRelationship
    binding_status: ClaimBindingStatus
    support_level: ClaimSupportLevel
    conflict_level: ClaimConflictLevel
    warnings: list[str] = list(evidence.warnings)
    blockers_list: list[str] = list(evidence.blockers)

    # USABLE + STRONG
    if estatus == CapabilityEvidenceStatus.USABLE and estrength == CapabilityEvidenceStrength.STRONG:
        relationship = ClaimBindingRelationship.SUPPORTS
        binding_status = ClaimBindingStatus.BOUND
        support_level = ClaimSupportLevel.STRONG
        conflict_level = ClaimConflictLevel.NONE

    # USABLE + ADEQUATE
    elif estatus == CapabilityEvidenceStatus.USABLE and estrength == CapabilityEvidenceStrength.ADEQUATE:
        relationship = ClaimBindingRelationship.SUPPORTS
        binding_status = ClaimBindingStatus.BOUND
        support_level = ClaimSupportLevel.MODERATE
        conflict_level = ClaimConflictLevel.NONE

    # USABLE + WEAK
    elif estatus == CapabilityEvidenceStatus.USABLE and estrength == CapabilityEvidenceStrength.WEAK:
        relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
        binding_status = ClaimBindingStatus.INSUFFICIENT
        support_level = ClaimSupportLevel.WEAK
        conflict_level = ClaimConflictLevel.NONE
        warnings.append("weak evidence partially supports claim")

    # CANDIDATE
    elif estatus == CapabilityEvidenceStatus.CANDIDATE:
        if estrength in (CapabilityEvidenceStrength.ADEQUATE, CapabilityEvidenceStrength.STRONG):
            relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            binding_status = ClaimBindingStatus.BOUND
            support_level = ClaimSupportLevel.WEAK
        else:
            relationship = ClaimBindingRelationship.INSUFFICIENT
            binding_status = ClaimBindingStatus.INSUFFICIENT
            support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.NONE
        warnings.append("CANDIDATE evidence is not yet final")

    # INSUFFICIENT
    elif estatus == CapabilityEvidenceStatus.INSUFFICIENT:
        relationship = ClaimBindingRelationship.INSUFFICIENT
        binding_status = ClaimBindingStatus.INSUFFICIENT
        support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.NONE

    # CONFLICTED
    elif estatus == CapabilityEvidenceStatus.CONFLICTED:
        relationship = ClaimBindingRelationship.CONFLICTS
        binding_status = ClaimBindingStatus.CONFLICTED
        support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.HIGH
        if policy.block_conflicted_evidence:
            blockers_list.append("CONFLICTED evidence blocked by policy")

    # STALE
    elif estatus == CapabilityEvidenceStatus.STALE:
        if policy.allow_stale_evidence_to_support:
            relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            binding_status = ClaimBindingStatus.BOUND
            support_level = ClaimSupportLevel.WEAK
        else:
            relationship = ClaimBindingRelationship.WEAKENS
            binding_status = ClaimBindingStatus.STALE
            support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.LOW
        warnings.append("STALE evidence may be out of date")

    # EXPIRED
    elif estatus == CapabilityEvidenceStatus.EXPIRED:
        relationship = ClaimBindingRelationship.WEAKENS
        binding_status = ClaimBindingStatus.STALE
        support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.MEDIUM
        warnings.append("EXPIRED evidence weakens claim")

    # REVOKED
    elif estatus == CapabilityEvidenceStatus.REVOKED:
        relationship = ClaimBindingRelationship.BLOCKS
        binding_status = ClaimBindingStatus.BLOCKED
        support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.HIGH
        if policy.block_revoked_or_invalid_evidence:
            blockers_list.append("REVOKED evidence blocked by policy")

    # INVALID
    elif estatus == CapabilityEvidenceStatus.INVALID:
        relationship = ClaimBindingRelationship.BLOCKS
        binding_status = ClaimBindingStatus.INVALID
        support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.HIGH
        if policy.block_revoked_or_invalid_evidence:
            blockers_list.append("INVALID evidence blocked by policy")

    # REJECTED
    elif estatus == CapabilityEvidenceStatus.REJECTED:
        relationship = ClaimBindingRelationship.BLOCKS
        binding_status = ClaimBindingStatus.REJECTED
        support_level = ClaimSupportLevel.NONE
        conflict_level = ClaimConflictLevel.HIGH

    # DRAFT / UNKNOWN
    else:
        relationship = ClaimBindingRelationship.UNKNOWN
        binding_status = ClaimBindingStatus.UNKNOWN
        support_level = ClaimSupportLevel.UNKNOWN
        conflict_level = ClaimConflictLevel.UNKNOWN

    return EvidenceClaimBinding(
        binding_id=binding_id,
        claim_id=claim_id,
        capability_id=capability_id or evidence.capability_id,
        evidence_id=evidence.evidence_id,
        source_result_ids=evidence.source_result_ids,
        source_result_set_ids=evidence.source_result_set_ids,
        relationship=relationship,
        status=binding_status,
        support_level=support_level,
        conflict_level=conflict_level,
        evidence_status=estatus.value,
        evidence_strength=estrength.value,
        evidence_kind=evidence.kind.value,
        limitations=evidence.limitations,
        warnings=tuple(warnings),
        blockers=tuple(blockers_list),
        summary=(
            f"Evidence {evidence.evidence_id!r} → {relationship.value} claim {claim_id!r} "
            f"(support={support_level.value}, conflict={conflict_level.value})"
        ),
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_evidence_claim_binding(
    binding: EvidenceClaimBinding,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not binding.binding_id or not binding.binding_id.strip():
        issues.append("binding_id must not be empty")

    if not binding.claim_id or not binding.claim_id.strip():
        issues.append("claim_id must not be empty")

    if not binding.evidence_id or not binding.evidence_id.strip():
        issues.append("evidence_id must not be empty")

    # No VERIFIED anywhere
    if "VERIFIED" in binding.status.value:
        issues.append("VERIFIED status is forbidden in P1.5.7")
    if "VERIFIED" in binding.relationship.value:
        issues.append("VERIFIED relationship is forbidden in P1.5.7")
    if "VERIFIED" in binding.summary.upper():
        issues.append("summary must not claim VERIFIED")

    # BOUND cannot use UNKNOWN relationship
    if binding.status == ClaimBindingStatus.BOUND and binding.relationship == ClaimBindingRelationship.UNKNOWN:
        issues.append("BOUND status cannot use UNKNOWN relationship")

    # SUPPORTS requires MODERATE or STRONG support
    if binding.relationship == ClaimBindingRelationship.SUPPORTS:
        if binding.support_level not in (ClaimSupportLevel.MODERATE, ClaimSupportLevel.STRONG):
            issues.append("SUPPORTS requires MODERATE or STRONG support level")

    # SUPPORTS cannot have HIGH/CRITICAL conflict
    if binding.relationship == ClaimBindingRelationship.SUPPORTS:
        if binding.conflict_level in (ClaimConflictLevel.HIGH, ClaimConflictLevel.CRITICAL):
            issues.append("SUPPORTS cannot have HIGH or CRITICAL conflict level")

    # SUPPORTS with INVALID/REVOKED/REJECTED/CONFLICTED evidence
    if binding.relationship in (ClaimBindingRelationship.SUPPORTS, ClaimBindingRelationship.PARTIALLY_SUPPORTS):
        if binding.evidence_status in ("INVALID", "REVOKED", "REJECTED", "CONFLICTED"):
            issues.append(
                f"SUPPORTS/PARTIALLY_SUPPORTS cannot use "
                f"{binding.evidence_status} evidence"
            )

    # CONFLICTS requires conflict level or warning/blocker
    if binding.relationship == ClaimBindingRelationship.CONFLICTS:
        if binding.conflict_level == ClaimConflictLevel.NONE:
            if not binding.warnings and not binding.blockers:
                issues.append("CONFLICTS requires conflict level > NONE or at least one warning/blocker")

    # BLOCKS requires blocker or warning
    if binding.relationship == ClaimBindingRelationship.BLOCKS:
        if not binding.blockers and not binding.warnings:
            issues.append("BLOCKS requires at least one blocker or warning")

    # INVALID status requires blocker
    if binding.status == ClaimBindingStatus.INVALID:
        if not binding.blockers:
            issues.append("INVALID status requires at least one blocker")

    return tuple(issues)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_evidence_claim_bindings(
    *,
    decision_id: str,
    claim_id: str,
    bindings: tuple[EvidenceClaimBinding, ...],
    capability_id: str | None = None,
    policy: EvidenceClaimBindingPolicy | None = None,
) -> EvidenceClaimBindingDecision:
    if policy is None:
        policy = build_default_evidence_claim_binding_policy()

    all_warnings: list[str] = []
    all_blockers: list[str] = []

    usable_ids: list[str] = []
    insufficient_ids: list[str] = []
    conflicted_ids: list[str] = []
    blocked_ids: list[str] = []

    for b in bindings:
        all_warnings.extend(b.warnings)
        all_blockers.extend(b.blockers)

        if b.relationship in (ClaimBindingRelationship.SUPPORTS, ClaimBindingRelationship.PARTIALLY_SUPPORTS):
            usable_ids.append(b.evidence_id)
        elif b.relationship == ClaimBindingRelationship.INSUFFICIENT:
            insufficient_ids.append(b.evidence_id)
        elif b.relationship == ClaimBindingRelationship.CONFLICTS:
            conflicted_ids.append(b.evidence_id)
        elif b.relationship == ClaimBindingRelationship.BLOCKS:
            blocked_ids.append(b.evidence_id)
        elif b.status == ClaimBindingStatus.INVALID:
            blocked_ids.append(b.evidence_id)
        elif b.status == ClaimBindingStatus.REJECTED:
            blocked_ids.append(b.evidence_id)
        elif b.status == ClaimBindingStatus.STALE:
            insufficient_ids.append(b.evidence_id)

    aggregate_relationship: ClaimBindingRelationship
    aggregate_status: ClaimBindingStatus
    aggregate_support: ClaimSupportLevel
    aggregate_conflict: ClaimConflictLevel

    # No bindings
    if not bindings:
        aggregate_relationship = ClaimBindingRelationship.INSUFFICIENT
        aggregate_status = ClaimBindingStatus.INSUFFICIENT
        aggregate_support = ClaimSupportLevel.NONE
        aggregate_conflict = ClaimConflictLevel.NONE

    # BLOCKS / INVALID / REJECTED dominates
    elif blocked_ids:
        aggregate_relationship = ClaimBindingRelationship.BLOCKS
        aggregate_status = ClaimBindingStatus.BLOCKED
        aggregate_support = ClaimSupportLevel.NONE
        aggregate_conflict = _highest_conflict(bindings, ClaimConflictLevel.HIGH)

    # CONFLICTS dominates
    elif conflicted_ids:
        aggregate_relationship = ClaimBindingRelationship.CONFLICTS
        aggregate_status = ClaimBindingStatus.CONFLICTED
        aggregate_support = ClaimSupportLevel.NONE
        aggregate_conflict = _highest_conflict(bindings, ClaimConflictLevel.HIGH)

    # All SUPPORTS with strong/mod support
    elif all(
        b.relationship == ClaimBindingRelationship.SUPPORTS
        for b in bindings
    ):
        support_levels = {b.support_level for b in bindings}
        if ClaimSupportLevel.STRONG in support_levels:
            aggregate_relationship = ClaimBindingRelationship.SUPPORTS
            aggregate_status = ClaimBindingStatus.BOUND
            aggregate_support = ClaimSupportLevel.STRONG
        elif ClaimSupportLevel.MODERATE in support_levels:
            aggregate_relationship = ClaimBindingRelationship.SUPPORTS
            aggregate_status = ClaimBindingStatus.BOUND
            aggregate_support = ClaimSupportLevel.MODERATE
        else:
            aggregate_relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            aggregate_status = ClaimBindingStatus.BOUND
            aggregate_support = ClaimSupportLevel.WEAK
        aggregate_conflict = ClaimConflictLevel.NONE

    # Mixed — partial
    elif usable_ids:
        if insufficient_ids:
            aggregate_relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            aggregate_status = ClaimBindingStatus.INSUFFICIENT
        else:
            aggregate_relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            aggregate_status = ClaimBindingStatus.BOUND
        aggregate_support = _combine_support(bindings)
        aggregate_conflict = _highest_conflict(bindings, ClaimConflictLevel.LOW)

    # Stale-only
    elif all(b.status == ClaimBindingStatus.STALE for b in bindings):
        aggregate_relationship = ClaimBindingRelationship.INSUFFICIENT
        aggregate_status = ClaimBindingStatus.STALE
        aggregate_support = ClaimSupportLevel.NONE
        aggregate_conflict = ClaimConflictLevel.LOW

    # Everything else = insufficient
    else:
        aggregate_relationship = ClaimBindingRelationship.INSUFFICIENT
        aggregate_status = ClaimBindingStatus.INSUFFICIENT
        aggregate_support = ClaimSupportLevel.NONE
        aggregate_conflict = _highest_conflict(bindings, ClaimConflictLevel.NONE)

    return EvidenceClaimBindingDecision(
        decision_id=decision_id,
        claim_id=claim_id,
        capability_id=capability_id,
        bindings=bindings,
        aggregate_relationship=aggregate_relationship,
        aggregate_status=aggregate_status,
        aggregate_support_level=aggregate_support,
        aggregate_conflict_level=aggregate_conflict,
        usable_evidence_ids=tuple(usable_ids),
        insufficient_evidence_ids=tuple(insufficient_ids),
        conflicted_evidence_ids=tuple(conflicted_ids),
        blocked_evidence_ids=tuple(blocked_ids),
        warnings=tuple(all_warnings),
        blockers=tuple(all_blockers),
        summary=(
            f"Claim {claim_id!r}: {aggregate_relationship.value} "
            f"(support={aggregate_support.value}, conflict={aggregate_conflict.value}, "
            f"bindings={len(bindings)})"
        ),
    )


def _highest_conflict(
    bindings: tuple[EvidenceClaimBinding, ...],
    minimum: ClaimConflictLevel,
) -> ClaimConflictLevel:
    levels: set[ClaimConflictLevel] = {b.conflict_level for b in bindings}
    for lvl in (ClaimConflictLevel.CRITICAL, ClaimConflictLevel.HIGH, ClaimConflictLevel.MEDIUM, ClaimConflictLevel.LOW, ClaimConflictLevel.NONE):
        if lvl in levels:
            return lvl
    return minimum


def _combine_support(
    bindings: tuple[EvidenceClaimBinding, ...],
) -> ClaimSupportLevel:
    levels = {b.support_level for b in bindings}
    for lvl in (ClaimSupportLevel.STRONG, ClaimSupportLevel.MODERATE, ClaimSupportLevel.WEAK, ClaimSupportLevel.NONE):
        if lvl in levels:
            return lvl
    return ClaimSupportLevel.UNKNOWN


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p157_evidence_claim_binding_report(
    *,
    bindings_created: int = 0,
    binding_decisions_created: int = 0,
    sparse_binding_ready: bool = False,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvidenceClaimBindingReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p157_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvidenceClaimBindingReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.7 Evidence-to-Claim Binding {status}. "
            f"Bindings: {bindings_created}, "
            f"Decisions: {binding_decisions_created}. "
            f"Sparse binding ready: {sparse_binding_ready}. "
            f"Next: P1.5.8."
        ),
        bindings_created=bindings_created,
        binding_decisions_created=binding_decisions_created,
        sparse_binding_ready=sparse_binding_ready,
        objects_added=(
            "ClaimBindingRelationship",
            "ClaimBindingStatus",
            "ClaimSupportLevel",
            "ClaimConflictLevel",
            "EvidenceClaimBinding",
            "EvidenceClaimBindingPolicy",
            "EvidenceClaimBindingDecision",
            "EvidenceClaimBindingReport",
        ),
        invariants=P157_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.8 — Benchmark Hygiene Guard",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def evidence_claim_binding_policy_to_dict(
    policy: EvidenceClaimBindingPolicy,
) -> dict[str, object]:
    return {
        "policy_id": policy.policy_id,
        "require_usable_evidence_for_support": policy.require_usable_evidence_for_support,
        "block_conflicted_evidence": policy.block_conflicted_evidence,
        "block_revoked_or_invalid_evidence": policy.block_revoked_or_invalid_evidence,
        "allow_stale_evidence_to_support": policy.allow_stale_evidence_to_support,
        "allow_single_evidence_to_verify_claim": policy.allow_single_evidence_to_verify_claim,
        "warnings": list(policy.warnings),
        "blockers": list(policy.blockers),
    }


def evidence_claim_binding_to_dict(
    binding: EvidenceClaimBinding,
) -> dict[str, object]:
    return {
        "binding_id": binding.binding_id,
        "claim_id": binding.claim_id,
        "capability_id": binding.capability_id,
        "evidence_id": binding.evidence_id,
        "source_result_ids": list(binding.source_result_ids),
        "source_result_set_ids": list(binding.source_result_set_ids),
        "relationship": binding.relationship.value,
        "status": binding.status.value,
        "support_level": binding.support_level.value,
        "conflict_level": binding.conflict_level.value,
        "evidence_status": binding.evidence_status,
        "evidence_strength": binding.evidence_strength,
        "evidence_kind": binding.evidence_kind,
        "limitations": list(binding.limitations),
        "warnings": list(binding.warnings),
        "blockers": list(binding.blockers),
        "summary": binding.summary,
    }


def evidence_claim_binding_decision_to_dict(
    decision: EvidenceClaimBindingDecision,
) -> dict[str, object]:
    return {
        "decision_id": decision.decision_id,
        "claim_id": decision.claim_id,
        "capability_id": decision.capability_id,
        "bindings": [evidence_claim_binding_to_dict(b) for b in decision.bindings],
        "aggregate_relationship": decision.aggregate_relationship.value,
        "aggregate_status": decision.aggregate_status.value,
        "aggregate_support_level": decision.aggregate_support_level.value,
        "aggregate_conflict_level": decision.aggregate_conflict_level.value,
        "usable_evidence_ids": list(decision.usable_evidence_ids),
        "insufficient_evidence_ids": list(decision.insufficient_evidence_ids),
        "conflicted_evidence_ids": list(decision.conflicted_evidence_ids),
        "blocked_evidence_ids": list(decision.blocked_evidence_ids),
        "warnings": list(decision.warnings),
        "blockers": list(decision.blockers),
        "summary": decision.summary,
    }


def evidence_claim_binding_report_to_dict(
    report: EvidenceClaimBindingReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "bindings_created": report.bindings_created,
        "binding_decisions_created": report.binding_decisions_created,
        "sparse_binding_ready": report.sparse_binding_ready,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


# ---------------------------------------------------------------------------
# Example helpers
# ---------------------------------------------------------------------------


def example_usable_evidence_record() -> CapabilityEvidenceRecord:
    from .capability_evidence import CapabilityEvidenceKind

    return CapabilityEvidenceRecord(
        evidence_id="ev_example_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
        claim_id="claim_example_001",
        source_result_ids=("result_001",),
        evidence_refs=("ref_ev_001", "ref_ev_002"),
        summary="Example USABLE/STRONG evidence from evaluation.",
    )


def example_sparse_evidence_record() -> CapabilityEvidenceRecord:
    from .capability_evidence import CapabilityEvidenceKind

    return CapabilityEvidenceRecord(
        evidence_id="ev_sparse_example",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.ADEQUATE,
        claim_id="claim_sparse_context_001",
        source_result_ids=("result_sc_001",),
        evidence_refs=("ref_sc_ev_001",),
        summary=(
            "Example sparse context evaluation evidence. "
            "Sparse Context Compiler NOT implemented."
        ),
    )


__all__ = [
    "ClaimBindingRelationship",
    "ClaimBindingStatus",
    "ClaimSupportLevel",
    "ClaimConflictLevel",
    "EvidenceClaimBinding",
    "EvidenceClaimBindingPolicy",
    "EvidenceClaimBindingDecision",
    "EvidenceClaimBindingReport",
    "P157_INVARIANTS",
    "build_default_evidence_claim_binding_policy",
    "bind_evidence_to_claim",
    "validate_evidence_claim_binding",
    "aggregate_evidence_claim_bindings",
    "build_p157_evidence_claim_binding_report",
    "evidence_claim_binding_policy_to_dict",
    "evidence_claim_binding_to_dict",
    "evidence_claim_binding_decision_to_dict",
    "evidence_claim_binding_report_to_dict",
    "example_usable_evidence_record",
    "example_sparse_evidence_record",
]

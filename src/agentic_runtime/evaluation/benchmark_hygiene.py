"""P1.5.8 — Benchmark Hygiene Guard + Sparse Hygiene Readiness.

Assesses benchmark, fixture, dataset, source, and context hygiene before
benchmark-derived evidence is allowed to strongly support a claim.

This module does NOT run benchmarks, execute evaluations, create
EvaluationResult, verify capability, mutate final claim status, call LLMs/tools,
or implement Sparse Context Compiler / SSA / subquadratic model attention.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum

from .evidence_claim_binding import (
    ClaimBindingRelationship,
    ClaimBindingStatus,
    ClaimConflictLevel,
    ClaimSupportLevel,
    EvidenceClaimBinding,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BenchmarkHygieneStatus(str, Enum):
    CLEAN = "CLEAN"
    ACCEPTABLE = "ACCEPTABLE"
    DEGRADED = "DEGRADED"
    CONTAMINATED = "CONTAMINATED"
    STALE = "STALE"
    INSUFFICIENT_PROVENANCE = "INSUFFICIENT_PROVENANCE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class BenchmarkHygieneRisk(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class BenchmarkContaminationType(str, Enum):
    NONE = "NONE"
    TRAINING_CONTAMINATION = "TRAINING_CONTAMINATION"
    CONTEXT_LEAKAGE = "CONTEXT_LEAKAGE"
    FIXTURE_LEAKAGE = "FIXTURE_LEAKAGE"
    ANSWER_KEY_EXPOSURE = "ANSWER_KEY_EXPOSURE"
    RETRIEVAL_LEAKAGE = "RETRIEVAL_LEAKAGE"
    SOURCE_OVEREXPOSURE = "SOURCE_OVEREXPOSURE"
    OPERATOR_HINT_LEAKAGE = "OPERATOR_HINT_LEAKAGE"
    OVERFIT_FIXTURE = "OVERFIT_FIXTURE"
    STALE_FIXTURE = "STALE_FIXTURE"
    DUPLICATE_CASE = "DUPLICATE_CASE"

    LOST_CONTEXT_RISK = "LOST_CONTEXT_RISK"
    CONTRADICTION_OMISSION = "CONTRADICTION_OMISSION"
    MULTI_HOP_EDGE_MISSING = "MULTI_HOP_EDGE_MISSING"

    UNKNOWN = "UNKNOWN"


class BenchmarkFreshnessStatus(str, Enum):
    CURRENT = "CURRENT"
    RECENT = "RECENT"
    AGING = "AGING"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class BenchmarkRepresentativeness(str, Enum):
    REPRESENTATIVE = "REPRESENTATIVE"
    PARTIAL = "PARTIAL"
    NARROW = "NARROW"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
    TOY_ONLY = "TOY_ONLY"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P158_INVARIANTS: tuple[str, ...] = (
    "INV-P158-01: Benchmark-derived evidence cannot strongly support a claim unless hygiene is acceptable.",
    "INV-P158-02: Hygiene guard does not run benchmarks.",
    "INV-P158-03: Hygiene guard does not execute evaluations.",
    "INV-P158-04: Hygiene guard does not verify capability.",
    "INV-P158-05: Critical contamination blocks support.",
    "INV-P158-06: Answer key exposure is critical contamination.",
    "INV-P158-07: Unknown provenance cannot produce strong support by default.",
    "INV-P158-08: Stale benchmarks are downgraded by default.",
    "INV-P158-09: Hygiene may downgrade binding support but never increase it.",
    "INV-P158-10: No numeric hygiene score is introduced.",
    "INV-P158-11: P1.5.9 is the next module.",
    "INV-P158-SC-01: Context leakage is benchmark hygiene risk.",
    "INV-P158-SC-02: Retrieval leakage is benchmark hygiene risk.",
    "INV-P158-SC-03: Lost-context risk may downgrade evidence impact.",
    "INV-P158-SC-04: Contradiction omission may downgrade evidence impact.",
    "INV-P158-SC-05: Multi-hop edge missing may downgrade evidence impact.",
    "INV-P158-SC-06: Sparse hygiene does not implement Sparse Context Compiler, retrieval router, evidence graph builder, SSA or true subquadratic attention.",
)


_SPARSE_HYGIENE_TYPES: frozenset[BenchmarkContaminationType] = frozenset({
    BenchmarkContaminationType.CONTEXT_LEAKAGE,
    BenchmarkContaminationType.RETRIEVAL_LEAKAGE,
    BenchmarkContaminationType.SOURCE_OVEREXPOSURE,
    BenchmarkContaminationType.LOST_CONTEXT_RISK,
    BenchmarkContaminationType.CONTRADICTION_OMISSION,
    BenchmarkContaminationType.MULTI_HOP_EDGE_MISSING,
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchmarkFixtureBoundary:
    fixture_id: str
    fixture_name: str

    source_refs: tuple[str, ...]
    dataset_refs: tuple[str, ...]
    gold_label_refs: tuple[str, ...]
    expected_output_refs: tuple[str, ...]
    answer_key_refs: tuple[str, ...]

    created_at: str | None
    updated_at: str | None
    version: str | None

    known_exposure_refs: tuple[str, ...]
    allowed_context_refs: tuple[str, ...]
    forbidden_context_refs: tuple[str, ...]

    negative_control_refs: tuple[str, ...]
    adversarial_case_refs: tuple[str, ...]
    sparse_context_refs: tuple[str, ...]

    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    summary: str


@dataclass(frozen=True)
class BenchmarkHygieneAssessment:
    assessment_id: str
    fixture_id: str

    hygiene_status: BenchmarkHygieneStatus
    contamination_risk: BenchmarkHygieneRisk
    freshness_status: BenchmarkFreshnessStatus
    representativeness: BenchmarkRepresentativeness

    contamination_types: tuple[BenchmarkContaminationType, ...]

    evidence_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    context_refs: tuple[str, ...]

    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    summary: str


@dataclass(frozen=True)
class BenchmarkHygienePolicy:
    policy_id: str

    require_fixture_provenance: bool
    block_high_contamination: bool
    block_answer_key_exposure: bool
    block_unknown_source_for_strong_support: bool
    downgrade_stale_benchmarks: bool
    require_negative_controls_for_strong_support: bool
    require_representative_fixture_for_strong_support: bool

    warnings: tuple[str, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkHygieneDecision:
    decision_id: str
    assessment: BenchmarkHygieneAssessment

    evidence_usable_for_claim_support: bool
    max_allowed_support_level: ClaimSupportLevel

    recommended_binding_relationship: ClaimBindingRelationship
    recommended_binding_status: ClaimBindingStatus

    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    summary: str


@dataclass(frozen=True)
class BenchmarkHygieneReport:
    report_id: str
    status: str
    summary: str

    assessments_created: int
    decisions_created: int

    sparse_hygiene_ready: bool

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    next_module: str


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def build_default_benchmark_hygiene_policy() -> BenchmarkHygienePolicy:
    return BenchmarkHygienePolicy(
        policy_id="default_p158",
        require_fixture_provenance=True,
        block_high_contamination=True,
        block_answer_key_exposure=True,
        block_unknown_source_for_strong_support=True,
        downgrade_stale_benchmarks=True,
        require_negative_controls_for_strong_support=True,
        require_representative_fixture_for_strong_support=True,
        warnings=(),
        blockers=(),
    )


# ---------------------------------------------------------------------------
# Boundary validation and classification
# ---------------------------------------------------------------------------


def validate_benchmark_fixture_boundary(
    boundary: BenchmarkFixtureBoundary,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not boundary.fixture_id or not boundary.fixture_id.strip():
        issues.append("fixture_id must not be empty")

    if not boundary.fixture_name or not boundary.fixture_name.strip():
        issues.append("fixture_name must not be empty")

    if not boundary.source_refs and not boundary.dataset_refs:
        issues.append("missing fixture provenance: source_refs and dataset_refs are empty")

    allowed = set(boundary.allowed_context_refs)
    known = set(boundary.known_exposure_refs)

    gold_in_context = _overlap(boundary.gold_label_refs, allowed)
    if gold_in_context:
        issues.append(
            "gold label refs exposed in allowed context: " + ", ".join(gold_in_context)
        )

    expected_in_context = _overlap(boundary.expected_output_refs, allowed)
    if expected_in_context:
        issues.append(
            "expected output refs exposed in allowed context: " + ", ".join(expected_in_context)
        )

    answer_in_context = _overlap(boundary.answer_key_refs, allowed)
    answer_in_exposure = _overlap(boundary.answer_key_refs, known)
    answer_exposure = _dedupe(answer_in_context + answer_in_exposure)
    if answer_exposure:
        issues.append("answer key exposure detected: " + ", ".join(answer_exposure))

    forbidden_overlap = _overlap(boundary.forbidden_context_refs, allowed)
    if forbidden_overlap:
        issues.append(
            "forbidden context refs overlap allowed context refs: "
            + ", ".join(forbidden_overlap)
        )

    return tuple(issues)


def classify_contamination_risk(
    boundary: BenchmarkFixtureBoundary,
) -> tuple[BenchmarkHygieneRisk, tuple[BenchmarkContaminationType, ...]]:
    risks: list[BenchmarkHygieneRisk] = []
    contamination_types: list[BenchmarkContaminationType] = []

    allowed = set(boundary.allowed_context_refs)
    known = set(boundary.known_exposure_refs)

    answer_exposed = bool(
        _overlap(boundary.answer_key_refs, allowed)
        or _overlap(boundary.answer_key_refs, known)
        or _contains_token(_all_boundary_text(boundary), "answer key exposure", "answer_key_exposure")
    )
    if answer_exposed:
        risks.append(BenchmarkHygieneRisk.CRITICAL)
        _add_unique(contamination_types, BenchmarkContaminationType.ANSWER_KEY_EXPOSURE)

    expected_exposed = bool(
        _overlap(boundary.expected_output_refs, allowed)
        or _overlap(boundary.expected_output_refs, known)
    )
    if expected_exposed:
        risks.append(BenchmarkHygieneRisk.HIGH)
        _add_unique(contamination_types, BenchmarkContaminationType.CONTEXT_LEAKAGE)

    gold_exposed = bool(
        _overlap(boundary.gold_label_refs, allowed)
        or _overlap(boundary.gold_label_refs, known)
    )
    if gold_exposed:
        risks.append(BenchmarkHygieneRisk.HIGH)
        _add_unique(contamination_types, BenchmarkContaminationType.FIXTURE_LEAKAGE)

    forbidden_overlap = _overlap(boundary.forbidden_context_refs, allowed)
    if forbidden_overlap:
        risks.append(BenchmarkHygieneRisk.CRITICAL)
        _add_unique(contamination_types, BenchmarkContaminationType.CONTEXT_LEAKAGE)

    text = _all_boundary_text(boundary)
    if _contains_token(text, "fixture leakage", "fixture_leakage"):
        risks.append(BenchmarkHygieneRisk.HIGH)
        _add_unique(contamination_types, BenchmarkContaminationType.FIXTURE_LEAKAGE)

    if _contains_token(text, "context leakage", "context_leakage"):
        risks.append(BenchmarkHygieneRisk.HIGH)
        _add_unique(contamination_types, BenchmarkContaminationType.CONTEXT_LEAKAGE)

    if _contains_token(text, "retrieval leakage", "retrieval_leakage"):
        risks.append(BenchmarkHygieneRisk.HIGH)
        _add_unique(contamination_types, BenchmarkContaminationType.RETRIEVAL_LEAKAGE)

    if _contains_token(text, "source overexposure", "source_overexposure", "overexposed source"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.SOURCE_OVEREXPOSURE)

    if _contains_token(text, "operator hint", "operator_hint"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.OPERATOR_HINT_LEAKAGE)

    if _contains_token(text, "overfit", "over-fit"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.OVERFIT_FIXTURE)

    if _contains_token(text, "duplicate case", "duplicate_case"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.DUPLICATE_CASE)

    if _contains_token(text, "stale fixture", "stale_fixture"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.STALE_FIXTURE)

    if _contains_token(text, "lost context", "lost_context"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.LOST_CONTEXT_RISK)

    if _contains_token(text, "contradiction omission", "contradiction_omission"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.CONTRADICTION_OMISSION)

    if _contains_token(text, "multi-hop edge missing", "multi_hop_edge_missing", "multihop edge missing"):
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.MULTI_HOP_EDGE_MISSING)

    if boundary.known_exposure_refs and not risks:
        risks.append(BenchmarkHygieneRisk.MEDIUM)
        _add_unique(contamination_types, BenchmarkContaminationType.TRAINING_CONTAMINATION)

    if not boundary.source_refs and not boundary.dataset_refs:
        risks.append(BenchmarkHygieneRisk.UNKNOWN)
        _add_unique(contamination_types, BenchmarkContaminationType.UNKNOWN)

    if not contamination_types:
        _add_unique(contamination_types, BenchmarkContaminationType.NONE)

    return _combine_risks(tuple(risks)), tuple(contamination_types)


def classify_freshness_status(
    *,
    created_at: str | None,
    updated_at: str | None,
) -> BenchmarkFreshnessStatus:
    if updated_at and updated_at.strip():
        normalized = updated_at.strip().lower()
        if "expired" in normalized:
            return BenchmarkFreshnessStatus.EXPIRED
        if "stale" in normalized:
            return BenchmarkFreshnessStatus.STALE
        today = datetime.now(timezone.utc).date().isoformat()
        if updated_at.strip().startswith(today):
            return BenchmarkFreshnessStatus.CURRENT
        return BenchmarkFreshnessStatus.RECENT

    if created_at and created_at.strip():
        normalized = created_at.strip().lower()
        if "expired" in normalized:
            return BenchmarkFreshnessStatus.EXPIRED
        if "stale" in normalized:
            return BenchmarkFreshnessStatus.STALE
        return BenchmarkFreshnessStatus.AGING

    return BenchmarkFreshnessStatus.UNKNOWN


# ---------------------------------------------------------------------------
# Assessment and decision
# ---------------------------------------------------------------------------


def assess_benchmark_hygiene(
    *,
    assessment_id: str,
    boundary: BenchmarkFixtureBoundary,
    representativeness: BenchmarkRepresentativeness = BenchmarkRepresentativeness.UNKNOWN,
    evidence_refs: tuple[str, ...] = (),
    source_refs: tuple[str, ...] = (),
    context_refs: tuple[str, ...] = (),
    policy: BenchmarkHygienePolicy | None = None,
) -> BenchmarkHygieneAssessment:
    if policy is None:
        policy = build_default_benchmark_hygiene_policy()

    effective_boundary = boundary
    if context_refs:
        effective_boundary = replace(
            boundary,
            allowed_context_refs=_dedupe(boundary.allowed_context_refs + context_refs),
        )

    validation_issues = validate_benchmark_fixture_boundary(effective_boundary)
    contamination_risk, contamination_types = classify_contamination_risk(effective_boundary)
    freshness_status = classify_freshness_status(
        created_at=boundary.created_at,
        updated_at=boundary.updated_at,
    )

    warnings: list[str] = list(boundary.warnings)
    blockers: list[str] = list(boundary.blockers)

    for issue in validation_issues:
        if _is_blocking_boundary_issue(issue):
            blockers.append(issue)
        else:
            warnings.append(issue)

    if policy.require_fixture_provenance and not boundary.source_refs and not boundary.dataset_refs:
        warnings.append("fixture provenance required by policy")

    if (
        policy.block_answer_key_exposure
        and BenchmarkContaminationType.ANSWER_KEY_EXPOSURE in contamination_types
    ):
        blockers.append("answer key exposure blocked by policy")

    if policy.block_high_contamination and contamination_risk == BenchmarkHygieneRisk.HIGH:
        blockers.append("HIGH contamination blocked by policy")

    if contamination_risk == BenchmarkHygieneRisk.CRITICAL:
        blockers.append("CRITICAL contamination blocks support")

    if (
        policy.require_negative_controls_for_strong_support
        and not boundary.negative_control_refs
    ):
        warnings.append("negative controls missing; strong support is not allowed by default")

    if policy.require_representative_fixture_for_strong_support:
        if representativeness == BenchmarkRepresentativeness.UNKNOWN:
            warnings.append("representativeness unknown; strong support is not allowed by default")
        elif representativeness != BenchmarkRepresentativeness.REPRESENTATIVE:
            warnings.append(
                f"representativeness is {representativeness.value}; strong support is capped"
            )

    if freshness_status in (BenchmarkFreshnessStatus.STALE, BenchmarkFreshnessStatus.EXPIRED):
        warnings.append(f"benchmark freshness is {freshness_status.value}")

    if BenchmarkContaminationType.STALE_FIXTURE in contamination_types:
        warnings.append("stale fixture risk detected")

    if any(t in _SPARSE_HYGIENE_TYPES for t in contamination_types):
        warnings.append("sparse context hygiene risk detected")

    limitations = _dedupe(boundary.limitations)
    warnings_tuple = _dedupe(tuple(warnings))
    blockers_tuple = _dedupe(tuple(blockers))

    hygiene_status = _resolve_assessment_status(
        contamination_risk=contamination_risk,
        freshness_status=freshness_status,
        representativeness=representativeness,
        contamination_types=contamination_types,
        warnings=warnings_tuple,
        blockers=blockers_tuple,
        has_provenance=bool(boundary.source_refs or boundary.dataset_refs),
    )

    assessment_source_refs = _dedupe(source_refs + boundary.source_refs + boundary.dataset_refs)
    assessment_context_refs = _dedupe(
        context_refs + boundary.allowed_context_refs + boundary.sparse_context_refs
    )

    return BenchmarkHygieneAssessment(
        assessment_id=assessment_id,
        fixture_id=boundary.fixture_id,
        hygiene_status=hygiene_status,
        contamination_risk=contamination_risk,
        freshness_status=freshness_status,
        representativeness=representativeness,
        contamination_types=contamination_types,
        evidence_refs=evidence_refs,
        source_refs=assessment_source_refs,
        context_refs=assessment_context_refs,
        limitations=limitations,
        warnings=warnings_tuple,
        blockers=blockers_tuple,
        summary=(
            f"Benchmark fixture {boundary.fixture_id!r}: hygiene={hygiene_status.value}, "
            f"risk={contamination_risk.value}, freshness={freshness_status.value}, "
            f"representativeness={representativeness.value}"
        ),
    )


def resolve_hygiene_decision(
    *,
    decision_id: str,
    assessment: BenchmarkHygieneAssessment,
    policy: BenchmarkHygienePolicy | None = None,
) -> BenchmarkHygieneDecision:
    if policy is None:
        policy = build_default_benchmark_hygiene_policy()

    warnings = list(assessment.warnings) + list(policy.warnings)
    blockers = list(assessment.blockers) + list(policy.blockers)

    usable = True
    max_support = ClaimSupportLevel.STRONG
    relationship = ClaimBindingRelationship.SUPPORTS
    status = ClaimBindingStatus.BOUND

    if (
        assessment.contamination_risk == BenchmarkHygieneRisk.CRITICAL
        or assessment.hygiene_status == BenchmarkHygieneStatus.BLOCKED
    ):
        usable = False
        max_support = ClaimSupportLevel.NONE
        relationship = ClaimBindingRelationship.BLOCKS
        status = ClaimBindingStatus.BLOCKED
        blockers.append("hygiene decision blocks support due to critical or blocked hygiene")

    elif (
        assessment.contamination_risk == BenchmarkHygieneRisk.HIGH
        or assessment.hygiene_status == BenchmarkHygieneStatus.CONTAMINATED
    ):
        if policy.block_high_contamination:
            usable = False
            max_support = ClaimSupportLevel.NONE
            relationship = ClaimBindingRelationship.BLOCKS
            status = ClaimBindingStatus.BLOCKED
            blockers.append("hygiene decision blocks support due to high contamination")
        else:
            max_support = ClaimSupportLevel.WEAK
            relationship = ClaimBindingRelationship.INSUFFICIENT
            status = ClaimBindingStatus.INSUFFICIENT
            warnings.append("high contamination caps support at WEAK")

    elif assessment.hygiene_status == BenchmarkHygieneStatus.INSUFFICIENT_PROVENANCE:
        max_support = ClaimSupportLevel.WEAK
        relationship = ClaimBindingRelationship.INSUFFICIENT
        status = ClaimBindingStatus.INSUFFICIENT
        warnings.append("insufficient provenance caps support at WEAK")

    elif assessment.hygiene_status == BenchmarkHygieneStatus.STALE:
        if policy.downgrade_stale_benchmarks:
            max_support = ClaimSupportLevel.WEAK
            relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            status = ClaimBindingStatus.STALE
            warnings.append("stale benchmark caps support at WEAK")

    elif assessment.hygiene_status == BenchmarkHygieneStatus.DEGRADED:
        max_support = _degraded_support_cap(assessment)
        relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
        status = ClaimBindingStatus.BOUND
        warnings.append(f"degraded hygiene caps support at {max_support.value}")

    elif assessment.hygiene_status == BenchmarkHygieneStatus.UNKNOWN:
        max_support = ClaimSupportLevel.WEAK
        relationship = ClaimBindingRelationship.INSUFFICIENT
        status = ClaimBindingStatus.UNKNOWN
        warnings.append("unknown hygiene caps support at WEAK")

    if (
        max_support == ClaimSupportLevel.STRONG
        and policy.require_negative_controls_for_strong_support
        and any("negative control" in w.lower() for w in warnings)
    ):
        max_support = ClaimSupportLevel.MODERATE
        relationship = ClaimBindingRelationship.SUPPORTS
        warnings.append("negative controls required for STRONG support")

    if (
        max_support == ClaimSupportLevel.STRONG
        and policy.require_representative_fixture_for_strong_support
        and assessment.representativeness != BenchmarkRepresentativeness.REPRESENTATIVE
    ):
        max_support = ClaimSupportLevel.MODERATE
        relationship = ClaimBindingRelationship.SUPPORTS
        warnings.append("representative fixture required for STRONG support")

    if (
        max_support == ClaimSupportLevel.STRONG
        and policy.block_unknown_source_for_strong_support
        and assessment.hygiene_status == BenchmarkHygieneStatus.INSUFFICIENT_PROVENANCE
    ):
        max_support = ClaimSupportLevel.WEAK
        relationship = ClaimBindingRelationship.INSUFFICIENT
        warnings.append("unknown source cannot strongly support by default")

    warnings_tuple = _dedupe(tuple(warnings))
    blockers_tuple = _dedupe(tuple(blockers))

    return BenchmarkHygieneDecision(
        decision_id=decision_id,
        assessment=assessment,
        evidence_usable_for_claim_support=usable,
        max_allowed_support_level=max_support,
        recommended_binding_relationship=relationship,
        recommended_binding_status=status,
        warnings=warnings_tuple,
        blockers=blockers_tuple,
        summary=(
            f"Hygiene decision {decision_id!r}: usable={usable}, "
            f"max_support={max_support.value}, relationship={relationship.value}"
        ),
    )


def apply_hygiene_to_evidence_binding(
    *,
    binding: EvidenceClaimBinding,
    hygiene_decision: BenchmarkHygieneDecision,
) -> EvidenceClaimBinding:
    capped_support = _cap_support(
        original=binding.support_level,
        cap=hygiene_decision.max_allowed_support_level,
    )

    relationship = binding.relationship
    status = binding.status
    conflict_level = binding.conflict_level

    if not hygiene_decision.evidence_usable_for_claim_support:
        capped_support = ClaimSupportLevel.NONE
        relationship = hygiene_decision.recommended_binding_relationship
        status = hygiene_decision.recommended_binding_status
        if relationship == ClaimBindingRelationship.BLOCKS:
            conflict_level = _raise_conflict_floor(conflict_level, ClaimConflictLevel.HIGH)

    elif capped_support == ClaimSupportLevel.NONE:
        if binding.relationship in (
            ClaimBindingRelationship.SUPPORTS,
            ClaimBindingRelationship.PARTIALLY_SUPPORTS,
        ):
            relationship = ClaimBindingRelationship.INSUFFICIENT
            status = ClaimBindingStatus.INSUFFICIENT

    elif capped_support == ClaimSupportLevel.WEAK:
        if binding.relationship == ClaimBindingRelationship.SUPPORTS:
            relationship = ClaimBindingRelationship.PARTIALLY_SUPPORTS
            status = ClaimBindingStatus.INSUFFICIENT

    elif capped_support == ClaimSupportLevel.MODERATE:
        if binding.relationship == ClaimBindingRelationship.SUPPORTS:
            relationship = ClaimBindingRelationship.SUPPORTS

    warnings = _dedupe(binding.warnings + hygiene_decision.warnings)
    blockers = _dedupe(binding.blockers + hygiene_decision.blockers)
    limitations = _dedupe(
        binding.limitations
        + (
            f"hygiene decision {hygiene_decision.decision_id} capped support at {capped_support.value}",
        )
    )

    return EvidenceClaimBinding(
        binding_id=binding.binding_id,
        claim_id=binding.claim_id,
        capability_id=binding.capability_id,
        evidence_id=binding.evidence_id,
        source_result_ids=binding.source_result_ids,
        source_result_set_ids=binding.source_result_set_ids,
        relationship=relationship,
        status=status,
        support_level=capped_support,
        conflict_level=conflict_level,
        evidence_status=binding.evidence_status,
        evidence_strength=binding.evidence_strength,
        evidence_kind=binding.evidence_kind,
        limitations=limitations,
        warnings=warnings,
        blockers=blockers,
        summary=(
            f"{binding.summary} Hygiene applied: max_support="
            f"{hygiene_decision.max_allowed_support_level.value}."
        ).strip(),
    )


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p158_benchmark_hygiene_report(
    *,
    assessments_created: int = 0,
    decisions_created: int = 0,
    sparse_hygiene_ready: bool = False,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> BenchmarkHygieneReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p158_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return BenchmarkHygieneReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.8 Benchmark Hygiene Guard {status}. "
            f"Assessments: {assessments_created}, decisions: {decisions_created}. "
            f"Sparse hygiene ready: {sparse_hygiene_ready}. "
            f"Next: P1.5.9."
        ),
        assessments_created=assessments_created,
        decisions_created=decisions_created,
        sparse_hygiene_ready=sparse_hygiene_ready,
        objects_added=(
            "BenchmarkHygieneStatus",
            "BenchmarkHygieneRisk",
            "BenchmarkContaminationType",
            "BenchmarkFreshnessStatus",
            "BenchmarkRepresentativeness",
            "BenchmarkFixtureBoundary",
            "BenchmarkHygieneAssessment",
            "BenchmarkHygienePolicy",
            "BenchmarkHygieneDecision",
            "BenchmarkHygieneReport",
        ),
        invariants=P158_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.9 — Adversarial Evaluation Cases",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def benchmark_fixture_boundary_to_dict(
    boundary: BenchmarkFixtureBoundary,
) -> dict[str, object]:
    return {
        "fixture_id": boundary.fixture_id,
        "fixture_name": boundary.fixture_name,
        "source_refs": list(boundary.source_refs),
        "dataset_refs": list(boundary.dataset_refs),
        "gold_label_refs": list(boundary.gold_label_refs),
        "expected_output_refs": list(boundary.expected_output_refs),
        "answer_key_refs": list(boundary.answer_key_refs),
        "created_at": boundary.created_at,
        "updated_at": boundary.updated_at,
        "version": boundary.version,
        "known_exposure_refs": list(boundary.known_exposure_refs),
        "allowed_context_refs": list(boundary.allowed_context_refs),
        "forbidden_context_refs": list(boundary.forbidden_context_refs),
        "negative_control_refs": list(boundary.negative_control_refs),
        "adversarial_case_refs": list(boundary.adversarial_case_refs),
        "sparse_context_refs": list(boundary.sparse_context_refs),
        "limitations": list(boundary.limitations),
        "warnings": list(boundary.warnings),
        "blockers": list(boundary.blockers),
        "summary": boundary.summary,
    }


def benchmark_hygiene_policy_to_dict(
    policy: BenchmarkHygienePolicy,
) -> dict[str, object]:
    return {
        "policy_id": policy.policy_id,
        "require_fixture_provenance": policy.require_fixture_provenance,
        "block_high_contamination": policy.block_high_contamination,
        "block_answer_key_exposure": policy.block_answer_key_exposure,
        "block_unknown_source_for_strong_support": policy.block_unknown_source_for_strong_support,
        "downgrade_stale_benchmarks": policy.downgrade_stale_benchmarks,
        "require_negative_controls_for_strong_support": policy.require_negative_controls_for_strong_support,
        "require_representative_fixture_for_strong_support": policy.require_representative_fixture_for_strong_support,
        "warnings": list(policy.warnings),
        "blockers": list(policy.blockers),
    }


def benchmark_hygiene_assessment_to_dict(
    assessment: BenchmarkHygieneAssessment,
) -> dict[str, object]:
    return {
        "assessment_id": assessment.assessment_id,
        "fixture_id": assessment.fixture_id,
        "hygiene_status": assessment.hygiene_status.value,
        "contamination_risk": assessment.contamination_risk.value,
        "freshness_status": assessment.freshness_status.value,
        "representativeness": assessment.representativeness.value,
        "contamination_types": [t.value for t in assessment.contamination_types],
        "evidence_refs": list(assessment.evidence_refs),
        "source_refs": list(assessment.source_refs),
        "context_refs": list(assessment.context_refs),
        "limitations": list(assessment.limitations),
        "warnings": list(assessment.warnings),
        "blockers": list(assessment.blockers),
        "summary": assessment.summary,
    }


def benchmark_hygiene_decision_to_dict(
    decision: BenchmarkHygieneDecision,
) -> dict[str, object]:
    return {
        "decision_id": decision.decision_id,
        "assessment": benchmark_hygiene_assessment_to_dict(decision.assessment),
        "evidence_usable_for_claim_support": decision.evidence_usable_for_claim_support,
        "max_allowed_support_level": decision.max_allowed_support_level.value,
        "recommended_binding_relationship": decision.recommended_binding_relationship.value,
        "recommended_binding_status": decision.recommended_binding_status.value,
        "warnings": list(decision.warnings),
        "blockers": list(decision.blockers),
        "summary": decision.summary,
    }


def benchmark_hygiene_report_to_dict(
    report: BenchmarkHygieneReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "assessments_created": report.assessments_created,
        "decisions_created": report.decisions_created,
        "sparse_hygiene_ready": report.sparse_hygiene_ready,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


# ---------------------------------------------------------------------------
# Example helpers
# ---------------------------------------------------------------------------


def example_clean_benchmark_fixture_boundary() -> BenchmarkFixtureBoundary:
    return BenchmarkFixtureBoundary(
        fixture_id="fixture_clean_001",
        fixture_name="Clean representative benchmark fixture",
        source_refs=("source:benchmark_spec",),
        dataset_refs=("dataset:fixture_clean",),
        gold_label_refs=("gold:fixture_clean",),
        expected_output_refs=("expected:fixture_clean",),
        answer_key_refs=("answer_key:fixture_clean",),
        created_at="2026-06-21",
        updated_at="2026-06-21",
        version="v1",
        known_exposure_refs=(),
        allowed_context_refs=("source:benchmark_spec",),
        forbidden_context_refs=("gold:fixture_clean", "expected:fixture_clean", "answer_key:fixture_clean"),
        negative_control_refs=("negative:fixture_clean",),
        adversarial_case_refs=("adversarial:fixture_clean",),
        sparse_context_refs=(),
        limitations=(),
        warnings=(),
        blockers=(),
        summary="Example fixture with provenance and no known leakage.",
    )


def example_leaky_benchmark_fixture_boundary() -> BenchmarkFixtureBoundary:
    return BenchmarkFixtureBoundary(
        fixture_id="fixture_leaky_001",
        fixture_name="Leaky benchmark fixture",
        source_refs=("source:benchmark_spec",),
        dataset_refs=("dataset:fixture_leaky",),
        gold_label_refs=("gold:fixture_leaky",),
        expected_output_refs=("expected:fixture_leaky",),
        answer_key_refs=("answer_key:fixture_leaky",),
        created_at="2026-06-21",
        updated_at="2026-06-21",
        version="v1",
        known_exposure_refs=("answer_key:fixture_leaky",),
        allowed_context_refs=("source:benchmark_spec", "answer_key:fixture_leaky"),
        forbidden_context_refs=("answer_key:fixture_leaky",),
        negative_control_refs=(),
        adversarial_case_refs=(),
        sparse_context_refs=("context_leakage:fixture_leaky",),
        limitations=("answer key exposure fixture for hygiene demonstration",),
        warnings=(),
        blockers=(),
        summary="Example fixture with answer key exposure.",
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _overlap(left: tuple[str, ...], right: set[str]) -> tuple[str, ...]:
    return tuple(ref for ref in left if ref in right)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _add_unique(
    values: list[BenchmarkContaminationType],
    value: BenchmarkContaminationType,
) -> None:
    if value not in values:
        values.append(value)


def _all_boundary_text(boundary: BenchmarkFixtureBoundary) -> tuple[str, ...]:
    return (
        boundary.fixture_id,
        boundary.fixture_name,
        *boundary.source_refs,
        *boundary.dataset_refs,
        *boundary.gold_label_refs,
        *boundary.expected_output_refs,
        *boundary.answer_key_refs,
        *(boundary.known_exposure_refs),
        *(boundary.allowed_context_refs),
        *(boundary.forbidden_context_refs),
        *(boundary.negative_control_refs),
        *(boundary.adversarial_case_refs),
        *(boundary.sparse_context_refs),
        *(boundary.limitations),
        *(boundary.warnings),
        *(boundary.blockers),
        boundary.summary,
    )


def _contains_token(values: tuple[str, ...], *tokens: str) -> bool:
    haystack = " ".join(v.lower() for v in values if v)
    return any(token.lower() in haystack for token in tokens)


def _combine_risks(
    risks: tuple[BenchmarkHygieneRisk, ...],
) -> BenchmarkHygieneRisk:
    if not risks:
        return BenchmarkHygieneRisk.NONE
    for risk in (
        BenchmarkHygieneRisk.CRITICAL,
        BenchmarkHygieneRisk.HIGH,
        BenchmarkHygieneRisk.MEDIUM,
        BenchmarkHygieneRisk.UNKNOWN,
        BenchmarkHygieneRisk.LOW,
    ):
        if risk in risks:
            return risk
    return BenchmarkHygieneRisk.NONE


def _is_blocking_boundary_issue(issue: str) -> bool:
    lowered = issue.lower()
    return (
        "fixture_id" in lowered
        or "fixture_name" in lowered
        or "answer key exposure" in lowered
        or "forbidden context" in lowered
    )


def _resolve_assessment_status(
    *,
    contamination_risk: BenchmarkHygieneRisk,
    freshness_status: BenchmarkFreshnessStatus,
    representativeness: BenchmarkRepresentativeness,
    contamination_types: tuple[BenchmarkContaminationType, ...],
    warnings: tuple[str, ...],
    blockers: tuple[str, ...],
    has_provenance: bool,
) -> BenchmarkHygieneStatus:
    if blockers:
        return BenchmarkHygieneStatus.BLOCKED

    if contamination_risk == BenchmarkHygieneRisk.CRITICAL:
        return BenchmarkHygieneStatus.CONTAMINATED

    if contamination_risk == BenchmarkHygieneRisk.HIGH:
        return BenchmarkHygieneStatus.CONTAMINATED

    if not has_provenance:
        return BenchmarkHygieneStatus.INSUFFICIENT_PROVENANCE

    if (
        freshness_status in (BenchmarkFreshnessStatus.STALE, BenchmarkFreshnessStatus.EXPIRED)
        or BenchmarkContaminationType.STALE_FIXTURE in contamination_types
    ):
        return BenchmarkHygieneStatus.STALE

    if (
        contamination_risk == BenchmarkHygieneRisk.MEDIUM
        or any(t in _SPARSE_HYGIENE_TYPES for t in contamination_types)
        or representativeness in (
            BenchmarkRepresentativeness.NARROW,
            BenchmarkRepresentativeness.SYNTHETIC_ONLY,
            BenchmarkRepresentativeness.TOY_ONLY,
            BenchmarkRepresentativeness.UNKNOWN,
        )
        or warnings
    ):
        return BenchmarkHygieneStatus.DEGRADED

    if contamination_risk == BenchmarkHygieneRisk.NONE and freshness_status in (
        BenchmarkFreshnessStatus.CURRENT,
        BenchmarkFreshnessStatus.RECENT,
    ):
        return BenchmarkHygieneStatus.CLEAN

    return BenchmarkHygieneStatus.ACCEPTABLE


def _degraded_support_cap(
    assessment: BenchmarkHygieneAssessment,
) -> ClaimSupportLevel:
    if any(
        t in assessment.contamination_types
        for t in (
            BenchmarkContaminationType.LOST_CONTEXT_RISK,
            BenchmarkContaminationType.CONTRADICTION_OMISSION,
            BenchmarkContaminationType.MULTI_HOP_EDGE_MISSING,
        )
    ):
        return ClaimSupportLevel.WEAK
    return ClaimSupportLevel.MODERATE


def _cap_support(
    *,
    original: ClaimSupportLevel,
    cap: ClaimSupportLevel,
) -> ClaimSupportLevel:
    order = (
        ClaimSupportLevel.NONE,
        ClaimSupportLevel.WEAK,
        ClaimSupportLevel.MODERATE,
        ClaimSupportLevel.STRONG,
    )
    if original not in order or cap not in order:
        return original if original == ClaimSupportLevel.UNKNOWN else cap
    if order.index(original) <= order.index(cap):
        return original
    return cap


def _raise_conflict_floor(
    original: ClaimConflictLevel,
    floor: ClaimConflictLevel,
) -> ClaimConflictLevel:
    order = (
        ClaimConflictLevel.NONE,
        ClaimConflictLevel.LOW,
        ClaimConflictLevel.MEDIUM,
        ClaimConflictLevel.HIGH,
        ClaimConflictLevel.CRITICAL,
    )
    if original not in order:
        return floor
    if order.index(original) >= order.index(floor):
        return original
    return floor

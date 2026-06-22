"""P1.5.10 — Baseline Comparison Model + Sparse Comparison Readiness.

Compares current evaluation evidence metadata against a known baseline
using categorical signals only. Comparison is not verification.

This module does NOT run evaluations, benchmarks, or adversarial cases,
create EvaluationResult or CapabilityEvidenceRecord, verify capability,
mutate claims, call LLMs/tools, or implement Sparse Context Compiler.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationVerdict,
    evaluation_result_to_dict,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BaselineReferenceKind(str, Enum):
    EVALUATION_RESULT = "EVALUATION_RESULT"
    RESULT_SET = "RESULT_SET"
    CAPABILITY_EVIDENCE = "CAPABILITY_EVIDENCE"
    EVIDENCE_BINDING = "EVIDENCE_BINDING"
    HYGIENE_DECISION = "HYGIENE_DECISION"
    ADVERSARIAL_COVERAGE = "ADVERSARIAL_COVERAGE"
    SPARSE_CONTEXT_SIGNAL = "SPARSE_CONTEXT_SIGNAL"
    MANUAL_REFERENCE = "MANUAL_REFERENCE"
    UNKNOWN = "UNKNOWN"


class BaselineStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANDIDATE = "CANDIDATE"
    DEPRECATED = "DEPRECATED"
    STALE = "STALE"
    INVALID = "INVALID"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ComparisonDimension(str, Enum):
    OUTCOME = "OUTCOME"
    VERDICT = "VERDICT"
    CONFIDENCE_CLASS = "CONFIDENCE_CLASS"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    FAILURE_MODES = "FAILURE_MODES"
    SUPPORT_LEVEL = "SUPPORT_LEVEL"
    CONFLICT_LEVEL = "CONFLICT_LEVEL"
    HYGIENE_STATUS = "HYGIENE_STATUS"
    CONTAMINATION_RISK = "CONTAMINATION_RISK"
    ADVERSARIAL_COVERAGE = "ADVERSARIAL_COVERAGE"
    NEGATIVE_CONTROL_COVERAGE = "NEGATIVE_CONTROL_COVERAGE"

    SPARSE_CONTEXT_QUALITY = "SPARSE_CONTEXT_QUALITY"
    EVIDENCE_RECALL = "EVIDENCE_RECALL"
    LOST_CONTEXT_RISK = "LOST_CONTEXT_RISK"
    MULTI_HOP_TRACE_INTEGRITY = "MULTI_HOP_TRACE_INTEGRITY"
    CONTRADICTION_SURVIVAL = "CONTRADICTION_SURVIVAL"
    CONTEXT_BUDGET_EFFICIENCY = "CONTEXT_BUDGET_EFFICIENCY"
    GOVERNED_CONTEXT_SELECTION = "GOVERNED_CONTEXT_SELECTION"
    AUTHORITY_AWARE_RETRIEVAL = "AUTHORITY_AWARE_RETRIEVAL"

    UNKNOWN = "UNKNOWN"


class ComparisonSignal(str, Enum):
    IMPROVED = "IMPROVED"
    DEGRADED = "DEGRADED"
    UNCHANGED = "UNCHANGED"
    MIXED = "MIXED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INCOMPARABLE = "INCOMPARABLE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ComparisonConfidence(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P1510_INVARIANTS: tuple[str, ...] = (
    "INV-P1510-01: Baseline comparison does not verify capability.",
    "INV-P1510-02: Baseline comparison does not execute evaluation.",
    "INV-P1510-03: Baseline comparison does not run benchmarks.",
    "INV-P1510-04: Baseline comparison does not execute adversarial cases.",
    "INV-P1510-05: Improved over baseline is improvement signal, not verification.",
    "INV-P1510-06: Invalid or blocked baselines cannot produce high-confidence improvement.",
    "INV-P1510-07: Stale baselines downgrade confidence by default.",
    "INV-P1510-08: Hygiene/adversarial coverage matter for improvement confidence.",
    "INV-P1510-09: No numeric scoring is introduced.",
    "INV-P1510-10: P1.5.11 is the next module.",
    "INV-P1510-SC-01: Sparse-context baseline dimensions are first-class comparison dimensions.",
    "INV-P1510-SC-02: Lost-context risk comparison is categorical, not numeric.",
    "INV-P1510-SC-03: Sparse comparison does not implement Sparse Context Compiler, retrieval router, evidence graph builder, SSA or true subquadratic attention.",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaselineReference:
    baseline_id: str
    kind: BaselineReferenceKind
    status: BaselineStatus

    source_ref: str | None
    result_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    binding_refs: tuple[str, ...]
    hygiene_refs: tuple[str, ...]
    adversarial_case_refs: tuple[str, ...]

    created_at: str | None
    updated_at: str | None
    version: str | None

    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    summary: str


@dataclass(frozen=True)
class BaselineComparisonInput:
    comparison_id: str

    baseline: BaselineReference
    current_ref: BaselineReference

    dimensions: tuple[ComparisonDimension, ...]

    baseline_result: EvaluationResult | None
    current_result: EvaluationResult | None

    baseline_evidence_refs: tuple[str, ...]
    current_evidence_refs: tuple[str, ...]

    baseline_hygiene_refs: tuple[str, ...]
    current_hygiene_refs: tuple[str, ...]

    baseline_adversarial_case_refs: tuple[str, ...]
    current_adversarial_case_refs: tuple[str, ...]

    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    summary: str


@dataclass(frozen=True)
class BaselineComparisonDecision:
    comparison_id: str

    signal: ComparisonSignal
    confidence: ComparisonConfidence

    dimensions_compared: tuple[ComparisonDimension, ...]
    improved_dimensions: tuple[ComparisonDimension, ...]
    degraded_dimensions: tuple[ComparisonDimension, ...]
    unchanged_dimensions: tuple[ComparisonDimension, ...]
    inconclusive_dimensions: tuple[ComparisonDimension, ...]

    baseline_id: str
    current_id: str

    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    summary: str


@dataclass(frozen=True)
class BaselineComparisonPolicy:
    policy_id: str

    require_same_baseline_kind: bool
    require_active_baseline_for_high_confidence: bool
    block_invalid_or_blocked_baselines: bool
    downgrade_stale_baseline_confidence: bool
    require_hygiene_for_improvement: bool
    require_adversarial_coverage_for_improvement: bool
    allow_numeric_scores: bool

    warnings: tuple[str, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class BaselineComparisonReport:
    report_id: str
    status: str
    summary: str

    comparisons_created: int
    baseline_refs_created: int

    sparse_comparison_ready: bool

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    next_module: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_OUTCOME_RANK: dict[EvaluationOutcome, int] = {
    EvaluationOutcome.PASSED: 6,
    EvaluationOutcome.PARTIAL: 5,
    EvaluationOutcome.INCONCLUSIVE: 4,
    EvaluationOutcome.SKIPPED: 3,
    EvaluationOutcome.FAILED: 2,
    EvaluationOutcome.BLOCKED: 1,
    EvaluationOutcome.ERROR: 0,
}

_VERDICT_RANK: dict[EvaluationVerdict, int] = {
    EvaluationVerdict.SUPPORTED: 7,
    EvaluationVerdict.PARTIALLY_SUPPORTED: 6,
    EvaluationVerdict.INSUFFICIENT_EVIDENCE: 4,
    EvaluationVerdict.CONFLICTED: 3,
    EvaluationVerdict.UNSUPPORTED: 2,
    EvaluationVerdict.REJECTED: 1,
    EvaluationVerdict.BLOCKED: 0,
    EvaluationVerdict.UNKNOWN: -1,
}

_CONFIDENCE_RANK: dict[EvaluationConfidenceClass, int] = {
    EvaluationConfidenceClass.HIGH: 4,
    EvaluationConfidenceClass.MODERATE: 3,
    EvaluationConfidenceClass.LOW: 2,
    EvaluationConfidenceClass.NONE: 1,
    EvaluationConfidenceClass.UNKNOWN: 0,
}

_EVIDENCE_QUALITY_RANK: dict[EvaluationEvidenceQuality, int] = {
    EvaluationEvidenceQuality.STRONG: 6,
    EvaluationEvidenceQuality.ADEQUATE: 5,
    EvaluationEvidenceQuality.WEAK: 4,
    EvaluationEvidenceQuality.NONE: 3,
    EvaluationEvidenceQuality.STALE: 2,
    EvaluationEvidenceQuality.CONFLICTED: 1,
    EvaluationEvidenceQuality.UNKNOWN: 0,
}

_FAILURE_MODE_BADNESS: dict[EvaluationFailureMode, int] = {
    EvaluationFailureMode.NONE: 0,
    EvaluationFailureMode.MISSING_EVIDENCE: 2,
    EvaluationFailureMode.INSUFFICIENT_EVIDENCE: 3,
    EvaluationFailureMode.STALE_EVIDENCE: 3,
    EvaluationFailureMode.CONFLICTED_EVIDENCE: 5,
    EvaluationFailureMode.CRITERION_FAILED: 4,
    EvaluationFailureMode.REQUIRED_CRITERION_FAILED: 6,
    EvaluationFailureMode.SCOPE_MISMATCH: 4,
    EvaluationFailureMode.SUBJECT_MISMATCH: 4,
    EvaluationFailureMode.EVALUATOR_UNAVAILABLE: 3,
    EvaluationFailureMode.EVALUATOR_ERROR: 5,
    EvaluationFailureMode.INVALID_INPUT: 5,
    EvaluationFailureMode.POLICY_BLOCKED: 6,
    EvaluationFailureMode.AUTHORITY_BLOCKED: 6,
    EvaluationFailureMode.CONSENT_REQUIRED: 4,
    EvaluationFailureMode.BENCHMARK_CONTAMINATION_RISK: 6,
    EvaluationFailureMode.REWARD_HACKING_RISK: 5,
    EvaluationFailureMode.UNKNOWN: 1,
}

_SPARSE_FAILURE_MODES: dict[ComparisonDimension, frozenset[EvaluationFailureMode]] = {
    ComparisonDimension.SPARSE_CONTEXT_QUALITY: frozenset({
        EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
        EvaluationFailureMode.CRITERION_FAILED,
    }),
    ComparisonDimension.EVIDENCE_RECALL: frozenset({
        EvaluationFailureMode.MISSING_EVIDENCE,
        EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
    }),
    ComparisonDimension.LOST_CONTEXT_RISK: frozenset({
        EvaluationFailureMode.MISSING_EVIDENCE,
        EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
    }),
    ComparisonDimension.MULTI_HOP_TRACE_INTEGRITY: frozenset({
        EvaluationFailureMode.MISSING_EVIDENCE,
        EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
    }),
    ComparisonDimension.CONTRADICTION_SURVIVAL: frozenset({
        EvaluationFailureMode.CONFLICTED_EVIDENCE,
    }),
    ComparisonDimension.CONTEXT_BUDGET_EFFICIENCY: frozenset({
        EvaluationFailureMode.INSUFFICIENT_EVIDENCE,
    }),
    ComparisonDimension.GOVERNED_CONTEXT_SELECTION: frozenset({
        EvaluationFailureMode.POLICY_BLOCKED,
        EvaluationFailureMode.SCOPE_MISMATCH,
    }),
    ComparisonDimension.AUTHORITY_AWARE_RETRIEVAL: frozenset({
        EvaluationFailureMode.AUTHORITY_BLOCKED,
    }),
}

_NUMERIC_SCORE_PATTERN = re.compile(
    r"\b(score|delta|percent|percentage|improvement_rate)\b.*\b\d+(\.\d+)?\b"
    r"|\b\d+(\.\d+)?\s*%"
    r"|\bimprovement_score\b"
    r"|\bbaseline_delta\b",
    re.IGNORECASE,
)

_CRITICAL_DIMENSIONS = frozenset({
    ComparisonDimension.OUTCOME,
    ComparisonDimension.VERDICT,
    ComparisonDimension.EVIDENCE_QUALITY,
    ComparisonDimension.HYGIENE_STATUS,
    ComparisonDimension.ADVERSARIAL_COVERAGE,
})


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def build_default_baseline_comparison_policy() -> BaselineComparisonPolicy:
    return BaselineComparisonPolicy(
        policy_id="baseline_comparison_policy_default",
        require_same_baseline_kind=True,
        require_active_baseline_for_high_confidence=True,
        block_invalid_or_blocked_baselines=True,
        downgrade_stale_baseline_confidence=True,
        require_hygiene_for_improvement=True,
        require_adversarial_coverage_for_improvement=True,
        allow_numeric_scores=False,
        warnings=(),
        blockers=(),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enum_val(v: Enum) -> str:
    return v.value


def _has_refs(ref: BaselineReference) -> bool:
    return bool(
        ref.source_ref
        or ref.result_refs
        or ref.evidence_refs
        or ref.binding_refs
        or ref.hygiene_refs
        or ref.adversarial_case_refs
    )


def _ref_text_fields(ref: BaselineReference) -> tuple[str, ...]:
    return ref.summary, *ref.warnings, *ref.blockers


def _contains_numeric_score(texts: tuple[str, ...]) -> bool:
    combined = " ".join(texts)
    return bool(_NUMERIC_SCORE_PATTERN.search(combined))


def _compare_ranks(
    baseline_rank: int,
    current_rank: int,
) -> ComparisonSignal:
    if baseline_rank < 0 or current_rank < 0:
        return ComparisonSignal.INCONCLUSIVE
    if current_rank > baseline_rank:
        return ComparisonSignal.IMPROVED
    if current_rank < baseline_rank:
        return ComparisonSignal.DEGRADED
    return ComparisonSignal.UNCHANGED


def _compare_failure_scores(
    baseline_score: int,
    current_score: int,
) -> ComparisonSignal:
    if current_score < baseline_score:
        return ComparisonSignal.IMPROVED
    if current_score > baseline_score:
        return ComparisonSignal.DEGRADED
    return ComparisonSignal.UNCHANGED


def _worst_failure_score(modes: tuple[EvaluationFailureMode, ...]) -> int:
    if not modes or modes == (EvaluationFailureMode.NONE,):
        return 0
    return max(_FAILURE_MODE_BADNESS.get(m, 1) for m in modes if m != EvaluationFailureMode.NONE)


def _sparse_failure_score(
    modes: tuple[EvaluationFailureMode, ...],
    dimension: ComparisonDimension,
) -> int | None:
    related = _SPARSE_FAILURE_MODES.get(dimension)
    if related is None:
        return None
    hits = [m for m in modes if m in related]
    if not hits:
        return 0
    return max(_FAILURE_MODE_BADNESS.get(m, 1) for m in hits)


def _resolve_confidence(
    *,
    signal: ComparisonSignal,
    baseline: BaselineReference,
    current: BaselineReference,
    policy: BaselineComparisonPolicy,
    warnings: tuple[str, ...],
    blockers: tuple[str, ...],
) -> ComparisonConfidence:
    if blockers or signal in (ComparisonSignal.BLOCKED, ComparisonSignal.INCOMPARABLE):
        return ComparisonConfidence.INSUFFICIENT
    if signal == ComparisonSignal.INCONCLUSIVE:
        return ComparisonConfidence.INSUFFICIENT
    if signal == ComparisonSignal.UNKNOWN:
        return ComparisonConfidence.UNKNOWN

    confidence = ComparisonConfidence.MODERATE

    if (
        policy.require_active_baseline_for_high_confidence
        and baseline.status == BaselineStatus.ACTIVE
        and current.status == BaselineStatus.ACTIVE
        and signal in (ComparisonSignal.IMPROVED, ComparisonSignal.UNCHANGED)
        and not warnings
    ):
        confidence = ComparisonConfidence.HIGH

    if policy.downgrade_stale_baseline_confidence and baseline.status == BaselineStatus.STALE:
        confidence = ComparisonConfidence.LOW

    if baseline.status in (BaselineStatus.INVALID, BaselineStatus.BLOCKED, BaselineStatus.UNKNOWN):
        confidence = ComparisonConfidence.INSUFFICIENT

    if signal in (ComparisonSignal.MIXED, ComparisonSignal.DEGRADED):
        confidence = ComparisonConfidence.LOW

    if (
        policy.require_active_baseline_for_high_confidence
        and baseline.status != BaselineStatus.ACTIVE
        and signal == ComparisonSignal.IMPROVED
    ):
        confidence = ComparisonConfidence.LOW

    return confidence


def _apply_improvement_guards(
    *,
    signal: ComparisonSignal,
    baseline: BaselineReference,
    current: BaselineReference,
    policy: BaselineComparisonPolicy,
    warnings: list[str],
) -> ComparisonSignal:
    if signal != ComparisonSignal.IMPROVED:
        return signal

    adjusted = signal
    if policy.require_hygiene_for_improvement:
        if baseline.hygiene_refs and not current.hygiene_refs:
            warnings.append(
                "Improvement downgraded: current lacks hygiene refs present in baseline"
            )
            adjusted = ComparisonSignal.MIXED

    if policy.require_adversarial_coverage_for_improvement:
        if baseline.adversarial_case_refs and not current.adversarial_case_refs:
            warnings.append(
                "Improvement downgraded: current lacks adversarial coverage present in baseline"
            )
            adjusted = ComparisonSignal.MIXED

    return adjusted


def _aggregate_signal(signals: tuple[ComparisonSignal, ...]) -> ComparisonSignal:
    if not signals:
        return ComparisonSignal.INCONCLUSIVE
    if ComparisonSignal.BLOCKED in signals:
        return ComparisonSignal.BLOCKED
    if ComparisonSignal.INCOMPARABLE in signals:
        return ComparisonSignal.INCOMPARABLE
    if all(s == ComparisonSignal.IMPROVED for s in signals):
        return ComparisonSignal.IMPROVED
    if all(s == ComparisonSignal.UNCHANGED for s in signals):
        return ComparisonSignal.UNCHANGED
    if all(s == ComparisonSignal.INCONCLUSIVE for s in signals):
        return ComparisonSignal.INCONCLUSIVE
    if ComparisonSignal.DEGRADED in signals and ComparisonSignal.IMPROVED not in signals:
        return ComparisonSignal.DEGRADED
    if ComparisonSignal.IMPROVED in signals and ComparisonSignal.DEGRADED in signals:
        return ComparisonSignal.MIXED
    if ComparisonSignal.DEGRADED in signals:
        return ComparisonSignal.DEGRADED
    if ComparisonSignal.IMPROVED in signals:
        return ComparisonSignal.IMPROVED
    return ComparisonSignal.MIXED


def _make_decision(
    *,
    comparison_id: str,
    baseline: BaselineReference,
    current: BaselineReference,
    signal: ComparisonSignal,
    confidence: ComparisonConfidence,
    dimensions_compared: tuple[ComparisonDimension, ...],
    improved: tuple[ComparisonDimension, ...],
    degraded: tuple[ComparisonDimension, ...],
    unchanged: tuple[ComparisonDimension, ...],
    inconclusive: tuple[ComparisonDimension, ...],
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> BaselineComparisonDecision:
    return BaselineComparisonDecision(
        comparison_id=comparison_id,
        signal=signal,
        confidence=confidence,
        dimensions_compared=dimensions_compared,
        improved_dimensions=improved,
        degraded_dimensions=degraded,
        unchanged_dimensions=unchanged,
        inconclusive_dimensions=inconclusive,
        baseline_id=baseline.baseline_id,
        current_id=current.baseline_id,
        warnings=warnings,
        blockers=blockers,
        summary=(
            f"Baseline comparison {comparison_id!r}: signal={signal.value}, "
            f"confidence={confidence.value}. "
            f"Improved={len(improved)}, degraded={len(degraded)}, "
            f"unchanged={len(unchanged)}, inconclusive={len(inconclusive)}."
        ),
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_baseline_reference(
    baseline: BaselineReference,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not baseline.baseline_id or not baseline.baseline_id.strip():
        issues.append("baseline_id must not be empty")

    if baseline.status == BaselineStatus.ACTIVE:
        if baseline.kind == BaselineReferenceKind.UNKNOWN:
            issues.append("ACTIVE baseline cannot have UNKNOWN kind")
        if not _has_refs(baseline):
            issues.append("ACTIVE baseline requires at least one reference")

    if baseline.status in (BaselineStatus.INVALID, BaselineStatus.BLOCKED):
        if not baseline.blockers:
            issues.append(f"{baseline.status.value} baseline requires at least one blocker")

    if baseline.status == BaselineStatus.STALE and not baseline.warnings:
        issues.append("STALE baseline should include a warning")

    if baseline.status == BaselineStatus.UNKNOWN:
        if not baseline.warnings and not baseline.blockers:
            issues.append("UNKNOWN status requires warning or blocker")

    if _contains_numeric_score(_ref_text_fields(baseline)):
        issues.append("baseline must not contain numeric score claims in summary/warnings/blockers")

    return tuple(issues)


def validate_baseline_comparison_input(
    inp: BaselineComparisonInput,
    policy: BaselineComparisonPolicy | None = None,
) -> tuple[str, ...]:
    policy = policy or build_default_baseline_comparison_policy()
    issues: list[str] = []

    if not inp.comparison_id or not inp.comparison_id.strip():
        issues.append("comparison_id must not be empty")

    issues.extend(validate_baseline_reference(inp.baseline))
    issues.extend(validate_baseline_reference(inp.current_ref))

    if policy.block_invalid_or_blocked_baselines:
        if inp.baseline.status in (BaselineStatus.INVALID, BaselineStatus.BLOCKED):
            issues.append(f"baseline status {inp.baseline.status.value} blocks comparison")
        if inp.current_ref.status in (BaselineStatus.INVALID, BaselineStatus.BLOCKED):
            issues.append(f"current reference status {inp.current_ref.status.value} blocks comparison")

    if not inp.dimensions:
        issues.append("comparison requires at least one dimension")

    if ComparisonDimension.UNKNOWN in inp.dimensions:
        issues.append("UNKNOWN dimension is not allowed in comparison")

    if policy.require_same_baseline_kind and inp.baseline.kind != inp.current_ref.kind:
        issues.append(
            f"baseline kind mismatch: {inp.baseline.kind.value} vs {inp.current_ref.kind.value}"
        )

    combined_text = (
        inp.summary,
        *inp.warnings,
        *inp.blockers,
    )
    if not policy.allow_numeric_scores and _contains_numeric_score(combined_text):
        issues.append("numeric score usage is not allowed under default policy")

    return tuple(issues)


# ---------------------------------------------------------------------------
# Comparison engines
# ---------------------------------------------------------------------------


def _compare_dimension_on_results(
    dimension: ComparisonDimension,
    baseline_result: EvaluationResult,
    current_result: EvaluationResult,
) -> ComparisonSignal:
    if dimension == ComparisonDimension.OUTCOME:
        return _compare_ranks(
            _OUTCOME_RANK.get(baseline_result.outcome, -1),
            _OUTCOME_RANK.get(current_result.outcome, -1),
        )
    if dimension == ComparisonDimension.VERDICT:
        return _compare_ranks(
            _VERDICT_RANK.get(baseline_result.verdict, -1),
            _VERDICT_RANK.get(current_result.verdict, -1),
        )
    if dimension == ComparisonDimension.CONFIDENCE_CLASS:
        return _compare_ranks(
            _CONFIDENCE_RANK.get(baseline_result.confidence, -1),
            _CONFIDENCE_RANK.get(current_result.confidence, -1),
        )
    if dimension == ComparisonDimension.EVIDENCE_QUALITY:
        return _compare_ranks(
            _EVIDENCE_QUALITY_RANK.get(baseline_result.evidence_quality, -1),
            _EVIDENCE_QUALITY_RANK.get(current_result.evidence_quality, -1),
        )
    if dimension == ComparisonDimension.FAILURE_MODES:
        baseline_score = _worst_failure_score(baseline_result.failure_modes)
        current_score = _worst_failure_score(current_result.failure_modes)
        return _compare_failure_scores(baseline_score, current_score)

    if dimension in _SPARSE_FAILURE_MODES:
        baseline_score = _sparse_failure_score(baseline_result.failure_modes, dimension)
        current_score = _sparse_failure_score(current_result.failure_modes, dimension)
        if baseline_score is None or current_score is None:
            return ComparisonSignal.INCONCLUSIVE
        return _compare_failure_scores(baseline_score, current_score)

    return ComparisonSignal.INCONCLUSIVE


def compare_evaluation_results(
    *,
    comparison_id: str,
    baseline: BaselineReference,
    current: BaselineReference,
    baseline_result: EvaluationResult,
    current_result: EvaluationResult,
    dimensions: tuple[ComparisonDimension, ...],
    policy: BaselineComparisonPolicy | None = None,
) -> BaselineComparisonDecision:
    policy = policy or build_default_baseline_comparison_policy()
    warnings: list[str] = []
    blockers: list[str] = []

    if policy.block_invalid_or_blocked_baselines:
        if baseline.status in (BaselineStatus.INVALID, BaselineStatus.BLOCKED):
            blockers.append(f"baseline {baseline.baseline_id!r} is {baseline.status.value}")
        if current.status in (BaselineStatus.INVALID, BaselineStatus.BLOCKED):
            blockers.append(f"current {current.baseline_id!r} is {current.status.value}")

    if blockers:
        return _make_decision(
            comparison_id=comparison_id,
            baseline=baseline,
            current=current,
            signal=ComparisonSignal.BLOCKED,
            confidence=ComparisonConfidence.INSUFFICIENT,
            dimensions_compared=dimensions,
            improved=(),
            degraded=(),
            unchanged=(),
            inconclusive=dimensions,
            blockers=tuple(blockers),
        )

    improved: list[ComparisonDimension] = []
    degraded: list[ComparisonDimension] = []
    unchanged: list[ComparisonDimension] = []
    inconclusive: list[ComparisonDimension] = []

    for dimension in dimensions:
        signal = _compare_dimension_on_results(dimension, baseline_result, current_result)
        if signal == ComparisonSignal.IMPROVED:
            improved.append(dimension)
        elif signal == ComparisonSignal.DEGRADED:
            degraded.append(dimension)
        elif signal == ComparisonSignal.UNCHANGED:
            unchanged.append(dimension)
        else:
            inconclusive.append(dimension)

    raw_signal = _aggregate_signal(tuple(
        _compare_dimension_on_results(d, baseline_result, current_result) for d in dimensions
    ))
    if degraded and any(d in _CRITICAL_DIMENSIONS for d in degraded) and raw_signal == ComparisonSignal.IMPROVED:
        raw_signal = ComparisonSignal.MIXED
        warnings.append("Critical dimension degraded; cannot classify as fully improved")

    signal = _apply_improvement_guards(
        signal=raw_signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=warnings,
    )

    confidence = _resolve_confidence(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=tuple(warnings),
        blockers=(),
    )

    return _make_decision(
        comparison_id=comparison_id,
        baseline=baseline,
        current=current,
        signal=signal,
        confidence=confidence,
        dimensions_compared=dimensions,
        improved=tuple(improved),
        degraded=tuple(degraded),
        unchanged=tuple(unchanged),
        inconclusive=tuple(inconclusive),
        warnings=tuple(warnings),
    )


def compare_adversarial_coverage(
    *,
    comparison_id: str,
    baseline: BaselineReference,
    current: BaselineReference,
    baseline_case_refs: tuple[str, ...],
    current_case_refs: tuple[str, ...],
    policy: BaselineComparisonPolicy | None = None,
) -> BaselineComparisonDecision:
    policy = policy or build_default_baseline_comparison_policy()
    dimension = ComparisonDimension.ADVERSARIAL_COVERAGE
    warnings: list[str] = []

    if not baseline_case_refs and not current_case_refs:
        signal = ComparisonSignal.INCONCLUSIVE
        improved: tuple[ComparisonDimension, ...] = ()
        degraded: tuple[ComparisonDimension, ...] = ()
        unchanged: tuple[ComparisonDimension, ...] = ()
        inconclusive = (dimension,)
    elif current_case_refs == baseline_case_refs and current_case_refs:
        signal = ComparisonSignal.UNCHANGED
        improved = ()
        degraded = ()
        unchanged = (dimension,)
        inconclusive = ()
    elif set(baseline_case_refs).issubset(set(current_case_refs)) and len(current_case_refs) > len(baseline_case_refs):
        signal = ComparisonSignal.IMPROVED
        improved = (dimension,)
        degraded = ()
        unchanged = ()
        inconclusive = ()
    elif set(current_case_refs).issubset(set(baseline_case_refs)) and len(current_case_refs) < len(baseline_case_refs):
        signal = ComparisonSignal.DEGRADED
        improved = ()
        degraded = (dimension,)
        unchanged = ()
        inconclusive = ()
    elif current_case_refs and not baseline_case_refs:
        signal = ComparisonSignal.IMPROVED
        improved = (dimension,)
        degraded = ()
        unchanged = ()
        inconclusive = ()
    elif baseline_case_refs and not current_case_refs:
        signal = ComparisonSignal.DEGRADED
        improved = ()
        degraded = (dimension,)
        unchanged = ()
        inconclusive = ()
    else:
        signal = ComparisonSignal.MIXED
        improved = ()
        degraded = ()
        unchanged = ()
        inconclusive = (dimension,)

    signal = _apply_improvement_guards(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=warnings,
    )

    confidence = _resolve_confidence(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=tuple(warnings),
        blockers=(),
    )

    return _make_decision(
        comparison_id=comparison_id,
        baseline=baseline,
        current=current,
        signal=signal,
        confidence=confidence,
        dimensions_compared=(dimension,),
        improved=improved,
        degraded=degraded,
        unchanged=unchanged,
        inconclusive=inconclusive,
        warnings=tuple(warnings),
    )


def compare_hygiene_refs(
    *,
    comparison_id: str,
    baseline: BaselineReference,
    current: BaselineReference,
    baseline_hygiene_refs: tuple[str, ...],
    current_hygiene_refs: tuple[str, ...],
    policy: BaselineComparisonPolicy | None = None,
) -> BaselineComparisonDecision:
    policy = policy or build_default_baseline_comparison_policy()
    dimension = ComparisonDimension.HYGIENE_STATUS
    warnings: list[str] = []

    if not baseline_hygiene_refs and not current_hygiene_refs:
        signal = ComparisonSignal.INCONCLUSIVE
        improved = ()
        degraded = ()
        unchanged = ()
        inconclusive = (dimension,)
    elif current_hygiene_refs and not baseline_hygiene_refs:
        signal = ComparisonSignal.IMPROVED
        improved = (dimension,)
        degraded = ()
        unchanged = ()
        inconclusive = ()
    elif baseline_hygiene_refs and not current_hygiene_refs:
        signal = ComparisonSignal.DEGRADED
        improved = ()
        degraded = (dimension,)
        unchanged = ()
        inconclusive = ()
    elif current_hygiene_refs == baseline_hygiene_refs:
        signal = ComparisonSignal.UNCHANGED
        improved = ()
        degraded = ()
        unchanged = (dimension,)
        inconclusive = ()
    else:
        signal = ComparisonSignal.INCONCLUSIVE
        improved = ()
        degraded = ()
        unchanged = ()
        inconclusive = (dimension,)

    signal = _apply_improvement_guards(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=warnings,
    )

    confidence = _resolve_confidence(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=tuple(warnings),
        blockers=(),
    )

    return _make_decision(
        comparison_id=comparison_id,
        baseline=baseline,
        current=current,
        signal=signal,
        confidence=confidence,
        dimensions_compared=(dimension,),
        improved=improved,
        degraded=degraded,
        unchanged=unchanged,
        inconclusive=inconclusive,
        warnings=tuple(warnings),
    )


def resolve_baseline_comparison_decision(
    *,
    comparison_id: str,
    baseline: BaselineReference,
    current: BaselineReference,
    dimension_signals: tuple[BaselineComparisonDecision, ...],
    policy: BaselineComparisonPolicy | None = None,
) -> BaselineComparisonDecision:
    policy = policy or build_default_baseline_comparison_policy()
    warnings: list[str] = []
    blockers: list[str] = []

    if not dimension_signals:
        return _make_decision(
            comparison_id=comparison_id,
            baseline=baseline,
            current=current,
            signal=ComparisonSignal.INCONCLUSIVE,
            confidence=ComparisonConfidence.INSUFFICIENT,
            dimensions_compared=(),
            improved=(),
            degraded=(),
            unchanged=(),
            inconclusive=(),
            warnings=("No dimension signals provided",),
        )

    if policy.require_same_baseline_kind and baseline.kind != current.kind:
        return _make_decision(
            comparison_id=comparison_id,
            baseline=baseline,
            current=current,
            signal=ComparisonSignal.INCOMPARABLE,
            confidence=ComparisonConfidence.INSUFFICIENT,
            dimensions_compared=(),
            improved=(),
            degraded=(),
            unchanged=(),
            inconclusive=(),
            blockers=(f"kind mismatch: {baseline.kind.value} vs {current.kind.value}",),
        )

    signals = tuple(d.signal for d in dimension_signals)
    signal = _aggregate_signal(signals)

    improved: list[ComparisonDimension] = []
    degraded: list[ComparisonDimension] = []
    unchanged: list[ComparisonDimension] = []
    inconclusive: list[ComparisonDimension] = []
    compared: list[ComparisonDimension] = []

    for decision in dimension_signals:
        compared.extend(decision.dimensions_compared)
        improved.extend(decision.improved_dimensions)
        degraded.extend(decision.degraded_dimensions)
        unchanged.extend(decision.unchanged_dimensions)
        inconclusive.extend(decision.inconclusive_dimensions)
        warnings.extend(decision.warnings)
        blockers.extend(decision.blockers)

    if ComparisonSignal.BLOCKED in signals:
        signal = ComparisonSignal.BLOCKED

    signal = _apply_improvement_guards(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=warnings,
    )

    confidence = _resolve_confidence(
        signal=signal,
        baseline=baseline,
        current=current,
        policy=policy,
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )

    return _make_decision(
        comparison_id=comparison_id,
        baseline=baseline,
        current=current,
        signal=signal,
        confidence=confidence,
        dimensions_compared=tuple(compared),
        improved=tuple(improved),
        degraded=tuple(degraded),
        unchanged=tuple(unchanged),
        inconclusive=tuple(inconclusive),
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def example_active_baseline_reference() -> BaselineReference:
    return BaselineReference(
        baseline_id="baseline_example_active",
        kind=BaselineReferenceKind.EVALUATION_RESULT,
        status=BaselineStatus.ACTIVE,
        source_ref="source_baseline_001",
        result_refs=("result_baseline_001",),
        evidence_refs=("evidence_baseline_001",),
        binding_refs=(),
        hygiene_refs=("hygiene_baseline_001",),
        adversarial_case_refs=("adv_negative_control_001", "adv_contradiction_trap_001"),
        created_at="2026-06-01T00:00:00+00:00",
        updated_at="2026-06-21T00:00:00+00:00",
        version="1.0",
        limitations=("Reference metadata only; not verification",),
        warnings=(),
        blockers=(),
        summary="Active baseline reference for categorical comparison only.",
    )


def example_current_baseline_reference() -> BaselineReference:
    return BaselineReference(
        baseline_id="baseline_example_current",
        kind=BaselineReferenceKind.EVALUATION_RESULT,
        status=BaselineStatus.ACTIVE,
        source_ref="source_current_001",
        result_refs=("result_current_001",),
        evidence_refs=("evidence_current_001",),
        binding_refs=(),
        hygiene_refs=("hygiene_current_001",),
        adversarial_case_refs=(
            "adv_negative_control_001",
            "adv_contradiction_trap_001",
            "adv_sparse_context_omission_trap_001",
        ),
        created_at="2026-06-21T00:00:00+00:00",
        updated_at="2026-06-21T00:00:00+00:00",
        version="1.0",
        limitations=("Current reference metadata only; not verification",),
        warnings=(),
        blockers=(),
        summary="Current reference for categorical comparison only.",
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_p1510_baseline_comparison_report(
    *,
    comparisons_created: int = 0,
    baseline_refs_created: int = 0,
    sparse_comparison_ready: bool = False,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> BaselineComparisonReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p1510_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return BaselineComparisonReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.10 Baseline Comparison Model {status}. "
            f"Comparisons: {comparisons_created}, baseline refs: {baseline_refs_created}. "
            f"Sparse comparison ready: {sparse_comparison_ready}. "
            f"Next: P1.5.11."
        ),
        comparisons_created=comparisons_created,
        baseline_refs_created=baseline_refs_created,
        sparse_comparison_ready=sparse_comparison_ready,
        objects_added=(
            "BaselineReferenceKind",
            "BaselineStatus",
            "ComparisonDimension",
            "ComparisonSignal",
            "ComparisonConfidence",
            "BaselineReference",
            "BaselineComparisonInput",
            "BaselineComparisonDecision",
            "BaselineComparisonPolicy",
            "BaselineComparisonReport",
        ),
        invariants=P1510_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.11 — Regression Detection Seed",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def baseline_reference_to_dict(
    ref: BaselineReference,
) -> dict[str, object]:
    return {
        "baseline_id": ref.baseline_id,
        "kind": _enum_val(ref.kind),
        "status": _enum_val(ref.status),
        "source_ref": ref.source_ref,
        "result_refs": list(ref.result_refs),
        "evidence_refs": list(ref.evidence_refs),
        "binding_refs": list(ref.binding_refs),
        "hygiene_refs": list(ref.hygiene_refs),
        "adversarial_case_refs": list(ref.adversarial_case_refs),
        "created_at": ref.created_at,
        "updated_at": ref.updated_at,
        "version": ref.version,
        "limitations": list(ref.limitations),
        "warnings": list(ref.warnings),
        "blockers": list(ref.blockers),
        "summary": ref.summary,
    }


def baseline_comparison_input_to_dict(
    inp: BaselineComparisonInput,
) -> dict[str, object]:
    return {
        "comparison_id": inp.comparison_id,
        "baseline": baseline_reference_to_dict(inp.baseline),
        "current_ref": baseline_reference_to_dict(inp.current_ref),
        "dimensions": [_enum_val(d) for d in inp.dimensions],
        "baseline_result": (
            evaluation_result_to_dict(inp.baseline_result)
            if inp.baseline_result is not None
            else None
        ),
        "current_result": (
            evaluation_result_to_dict(inp.current_result)
            if inp.current_result is not None
            else None
        ),
        "baseline_evidence_refs": list(inp.baseline_evidence_refs),
        "current_evidence_refs": list(inp.current_evidence_refs),
        "baseline_hygiene_refs": list(inp.baseline_hygiene_refs),
        "current_hygiene_refs": list(inp.current_hygiene_refs),
        "baseline_adversarial_case_refs": list(inp.baseline_adversarial_case_refs),
        "current_adversarial_case_refs": list(inp.current_adversarial_case_refs),
        "warnings": list(inp.warnings),
        "blockers": list(inp.blockers),
        "summary": inp.summary,
    }


def baseline_comparison_decision_to_dict(
    decision: BaselineComparisonDecision,
) -> dict[str, object]:
    return {
        "comparison_id": decision.comparison_id,
        "signal": _enum_val(decision.signal),
        "confidence": _enum_val(decision.confidence),
        "dimensions_compared": [_enum_val(d) for d in decision.dimensions_compared],
        "improved_dimensions": [_enum_val(d) for d in decision.improved_dimensions],
        "degraded_dimensions": [_enum_val(d) for d in decision.degraded_dimensions],
        "unchanged_dimensions": [_enum_val(d) for d in decision.unchanged_dimensions],
        "inconclusive_dimensions": [_enum_val(d) for d in decision.inconclusive_dimensions],
        "baseline_id": decision.baseline_id,
        "current_id": decision.current_id,
        "warnings": list(decision.warnings),
        "blockers": list(decision.blockers),
        "summary": decision.summary,
    }


def baseline_comparison_policy_to_dict(
    policy: BaselineComparisonPolicy,
) -> dict[str, object]:
    return {
        "policy_id": policy.policy_id,
        "require_same_baseline_kind": policy.require_same_baseline_kind,
        "require_active_baseline_for_high_confidence": policy.require_active_baseline_for_high_confidence,
        "block_invalid_or_blocked_baselines": policy.block_invalid_or_blocked_baselines,
        "downgrade_stale_baseline_confidence": policy.downgrade_stale_baseline_confidence,
        "require_hygiene_for_improvement": policy.require_hygiene_for_improvement,
        "require_adversarial_coverage_for_improvement": policy.require_adversarial_coverage_for_improvement,
        "allow_numeric_scores": policy.allow_numeric_scores,
        "warnings": list(policy.warnings),
        "blockers": list(policy.blockers),
    }


def baseline_comparison_report_to_dict(
    report: BaselineComparisonReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "comparisons_created": report.comparisons_created,
        "baseline_refs_created": report.baseline_refs_created,
        "sparse_comparison_ready": report.sparse_comparison_ready,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }

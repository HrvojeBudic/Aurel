"""P1.5.1 — Evaluation Object Model.

Stable result language for the Evaluation Mirror: status, outcome, verdict,
confidence class, evidence quality, failure modes, criterion results,
evaluation results, and result sets.

Core law: EvaluationResult does not verify capability by itself.
PASS does not mean VERIFIED. No fake numeric capability score.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvaluationResultStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    ERROR = "ERROR"


class EvaluationOutcome(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class EvaluationVerdict(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONFLICTED = "CONFLICTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class EvaluationConfidenceClass(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class EvaluationEvidenceQuality(str, Enum):
    NONE = "NONE"
    WEAK = "WEAK"
    ADEQUATE = "ADEQUATE"
    STRONG = "STRONG"
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class EvaluationFailureMode(str, Enum):
    NONE = "NONE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTED_EVIDENCE = "CONFLICTED_EVIDENCE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    CRITERION_FAILED = "CRITERION_FAILED"
    REQUIRED_CRITERION_FAILED = "REQUIRED_CRITERION_FAILED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    SUBJECT_MISMATCH = "SUBJECT_MISMATCH"
    EVALUATOR_UNAVAILABLE = "EVALUATOR_UNAVAILABLE"
    EVALUATOR_ERROR = "EVALUATOR_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    AUTHORITY_BLOCKED = "AUTHORITY_BLOCKED"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    BENCHMARK_CONTAMINATION_RISK = "BENCHMARK_CONTAMINATION_RISK"
    REWARD_HACKING_RISK = "REWARD_HACKING_RISK"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

P151_INVARIANTS: tuple[str, ...] = (
    "INV-P151-01: Evaluation object model is closed-world.",
    "INV-P151-02: EvaluationResult does not verify capability by itself.",
    "INV-P151-03: PASS does not imply VERIFIED.",
    "INV-P151-04: SUPPORTED requires adequate/strong evidence.",
    "INV-P151-05: BLOCKED requires blockers.",
    "INV-P151-06: FAILED requires failure modes.",
    "INV-P151-07: ERROR requires error failure mode.",
    "INV-P151-08: CONFLICTED evidence blocks SUPPORTED aggregate verdict.",
    "INV-P151-09: Aggregation is categorical, not fake numeric scoring.",
    "INV-P151-10: Evidence refs are not proof of truth by themselves.",
    "INV-P151-11: P1.5.2 is the next module.",
)

_ADEQUATE_QUALITIES = frozenset({
    EvaluationEvidenceQuality.ADEQUATE,
    EvaluationEvidenceQuality.STRONG,
})

_ERROR_FAILURE_MODES = frozenset({
    EvaluationFailureMode.EVALUATOR_ERROR,
    EvaluationFailureMode.INVALID_INPUT,
    EvaluationFailureMode.UNKNOWN,
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationCriterionResult:
    criterion_id: str
    outcome: EvaluationOutcome
    verdict: EvaluationVerdict
    evidence_quality: EvaluationEvidenceQuality
    failure_modes: tuple[EvaluationFailureMode, ...] = ()
    summary: str = ""
    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    result_id: str
    run_id: str
    status: EvaluationResultStatus
    outcome: EvaluationOutcome
    verdict: EvaluationVerdict
    confidence: EvaluationConfidenceClass
    evidence_quality: EvaluationEvidenceQuality
    criterion_results: tuple[EvaluationCriterionResult, ...] = ()
    failure_modes: tuple[EvaluationFailureMode, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationResultSet:
    result_set_id: str
    run_id: str
    results: tuple[EvaluationResult, ...]
    aggregate_outcome: EvaluationOutcome
    aggregate_verdict: EvaluationVerdict
    aggregate_confidence: EvaluationConfidenceClass
    aggregate_evidence_quality: EvaluationEvidenceQuality
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class EvaluationObjectModelReport:
    report_id: str
    status: str  # READY, DEGRADED, BLOCKED
    summary: str
    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    next_module: str = "P1.5.2 — Capability Evidence Record"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_evaluation_criterion_result(
    result: EvaluationCriterionResult,
) -> tuple[str, ...]:
    """Validate a criterion result. Returns blockers. Does not mutate."""
    errors: list[str] = []

    if not result.criterion_id or not result.criterion_id.strip():
        errors.append("criterion_id must not be empty")

    if result.verdict == EvaluationVerdict.SUPPORTED:
        if not result.evidence_refs:
            errors.append("SUPPORTED verdict requires evidence_refs")
        if result.evidence_quality not in _ADEQUATE_QUALITIES:
            errors.append(
                f"SUPPORTED verdict requires ADEQUATE or STRONG evidence quality, "
                f"got {result.evidence_quality.value}"
            )

    if result.outcome == EvaluationOutcome.BLOCKED and not result.blockers:
        errors.append("BLOCKED outcome requires blockers")

    if result.outcome == EvaluationOutcome.FAILED and not result.failure_modes:
        errors.append("FAILED outcome requires failure_modes")

    if result.outcome == EvaluationOutcome.ERROR:
        if not any(fm in _ERROR_FAILURE_MODES for fm in result.failure_modes):
            errors.append("ERROR outcome requires EVALUATOR_ERROR, INVALID_INPUT, or UNKNOWN failure mode")

    return tuple(errors)


def validate_evaluation_result(result: EvaluationResult) -> tuple[str, ...]:
    """Validate an evaluation result. Returns blockers. Does not mutate."""
    errors: list[str] = []

    if not result.result_id or not result.result_id.strip():
        errors.append("result_id must not be empty")
    if not result.run_id or not result.run_id.strip():
        errors.append("run_id must not be empty")

    if result.status == EvaluationResultStatus.COMPLETED and not result.criterion_results:
        errors.append("COMPLETED status requires criterion_results")

    if result.verdict == EvaluationVerdict.SUPPORTED:
        if result.evidence_quality not in _ADEQUATE_QUALITIES:
            errors.append(
                f"SUPPORTED verdict requires ADEQUATE or STRONG evidence quality, "
                f"got {result.evidence_quality.value}"
            )

    if result.outcome == EvaluationOutcome.BLOCKED and not result.blockers:
        errors.append("BLOCKED outcome requires blockers")

    if result.outcome == EvaluationOutcome.FAILED and not result.failure_modes:
        errors.append("FAILED outcome requires failure_modes")

    if result.outcome == EvaluationOutcome.ERROR:
        if not any(fm in _ERROR_FAILURE_MODES for fm in result.failure_modes):
            errors.append("ERROR outcome requires EVALUATOR_ERROR, INVALID_INPUT, or UNKNOWN failure mode")

    for cr in result.criterion_results:
        errors.extend(validate_evaluation_criterion_result(cr))

    return tuple(errors)


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------


def _worst_evidence_quality(
    qualities: tuple[EvaluationEvidenceQuality, ...],
) -> EvaluationEvidenceQuality:
    if not qualities:
        return EvaluationEvidenceQuality.NONE
    priority = {
        EvaluationEvidenceQuality.CONFLICTED: 0,
        EvaluationEvidenceQuality.NONE: 1,
        EvaluationEvidenceQuality.UNKNOWN: 2,
        EvaluationEvidenceQuality.WEAK: 3,
        EvaluationEvidenceQuality.STALE: 4,
        EvaluationEvidenceQuality.ADEQUATE: 5,
        EvaluationEvidenceQuality.STRONG: 6,
    }
    return min(qualities, key=lambda q: priority.get(q, 99))


def _confidence_from_evidence(quality: EvaluationEvidenceQuality) -> EvaluationConfidenceClass:
    mapping = {
        EvaluationEvidenceQuality.STRONG: EvaluationConfidenceClass.HIGH,
        EvaluationEvidenceQuality.ADEQUATE: EvaluationConfidenceClass.MODERATE,
        EvaluationEvidenceQuality.WEAK: EvaluationConfidenceClass.LOW,
        EvaluationEvidenceQuality.NONE: EvaluationConfidenceClass.NONE,
        EvaluationEvidenceQuality.UNKNOWN: EvaluationConfidenceClass.UNKNOWN,
        EvaluationEvidenceQuality.CONFLICTED: EvaluationConfidenceClass.UNKNOWN,
        EvaluationEvidenceQuality.STALE: EvaluationConfidenceClass.LOW,
    }
    return mapping.get(quality, EvaluationConfidenceClass.UNKNOWN)


def resolve_evaluation_result_from_criteria(
    *,
    result_id: str,
    run_id: str,
    criterion_results: tuple[EvaluationCriterionResult, ...],
    evidence_refs: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
) -> EvaluationResult:
    """Resolve an EvaluationResult from criterion results. Does NOT verify capability."""
    if not result_id or not result_id.strip():
        raise ValueError("result_id must not be empty")
    if not run_id or not run_id.strip():
        raise ValueError("run_id must not be empty")

    all_evidence = evidence_refs + tuple(
        ref for cr in criterion_results for ref in cr.evidence_refs
    )
    all_blockers = tuple(b for cr in criterion_results for b in cr.blockers)
    all_warnings = tuple(w for cr in criterion_results for w in cr.warnings)
    all_failure_modes = tuple(fm for cr in criterion_results for fm in cr.failure_modes)

    # 1. No criterion results
    if not criterion_results:
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.INCONCLUSIVE,
            verdict=EvaluationVerdict.INSUFFICIENT_EVIDENCE,
            confidence=EvaluationConfidenceClass.NONE,
            evidence_quality=EvaluationEvidenceQuality.NONE,
            criterion_results=(),
            failure_modes=(EvaluationFailureMode.INSUFFICIENT_EVIDENCE,),
            evidence_refs=evidence_refs,
            limitations=limitations,
            summary="No criterion results — insufficient evidence",
        )

    # 2. Any criterion BLOCKED
    if any(cr.outcome == EvaluationOutcome.BLOCKED for cr in criterion_results):
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.BLOCKED,
            verdict=EvaluationVerdict.BLOCKED,
            confidence=EvaluationConfidenceClass.NONE,
            evidence_quality=_worst_evidence_quality(
                tuple(cr.evidence_quality for cr in criterion_results)
            ),
            criterion_results=criterion_results,
            failure_modes=all_failure_modes,
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            blockers=all_blockers,
            summary="Evaluation blocked by criterion blocker(s)",
        )

    # 3. Any CONFLICTED
    if any(
        cr.verdict == EvaluationVerdict.CONFLICTED
        or cr.evidence_quality == EvaluationEvidenceQuality.CONFLICTED
        for cr in criterion_results
    ):
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.INCONCLUSIVE,
            verdict=EvaluationVerdict.CONFLICTED,
            confidence=EvaluationConfidenceClass.UNKNOWN,
            evidence_quality=EvaluationEvidenceQuality.CONFLICTED,
            criterion_results=criterion_results,
            failure_modes=all_failure_modes + (EvaluationFailureMode.CONFLICTED_EVIDENCE,),
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            summary="Conflicting evidence detected",
        )

    # 4. Required criterion failure
    if EvaluationFailureMode.REQUIRED_CRITERION_FAILED in all_failure_modes:
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.FAILED,
            verdict=EvaluationVerdict.REJECTED,
            confidence=EvaluationConfidenceClass.LOW,
            evidence_quality=_worst_evidence_quality(
                tuple(cr.evidence_quality for cr in criterion_results)
            ),
            criterion_results=criterion_results,
            failure_modes=all_failure_modes,
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            summary="Required criterion failed — rejected",
        )

    # 5. Any ERROR
    if any(cr.outcome == EvaluationOutcome.ERROR for cr in criterion_results):
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.ERROR,
            outcome=EvaluationOutcome.ERROR,
            verdict=EvaluationVerdict.UNKNOWN,
            confidence=EvaluationConfidenceClass.UNKNOWN,
            evidence_quality=EvaluationEvidenceQuality.UNKNOWN,
            criterion_results=criterion_results,
            failure_modes=all_failure_modes or (EvaluationFailureMode.EVALUATOR_ERROR,),
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            summary="Evaluator error during evaluation",
        )

    # Check for usable evidence
    has_usable_evidence = bool(all_evidence) and any(
        cr.evidence_quality in _ADEQUATE_QUALITIES for cr in criterion_results
    )

    outcomes = {cr.outcome for cr in criterion_results}

    # 6. All passed + adequate/strong evidence
    if outcomes == {EvaluationOutcome.PASSED} and has_usable_evidence:
        eq = _worst_evidence_quality(tuple(cr.evidence_quality for cr in criterion_results))
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.PASSED,
            verdict=EvaluationVerdict.SUPPORTED,
            confidence=_confidence_from_evidence(eq),
            evidence_quality=eq,
            criterion_results=criterion_results,
            failure_modes=(),
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            summary="All criteria passed with adequate evidence — SUPPORTED (not VERIFIED)",
        )

    # 7. No usable evidence
    if not has_usable_evidence:
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.INCONCLUSIVE,
            verdict=EvaluationVerdict.INSUFFICIENT_EVIDENCE,
            confidence=EvaluationConfidenceClass.NONE,
            evidence_quality=EvaluationEvidenceQuality.NONE,
            criterion_results=criterion_results,
            failure_modes=all_failure_modes + (EvaluationFailureMode.INSUFFICIENT_EVIDENCE,),
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            summary="Insufficient evidence for supported verdict",
        )

    # 8. Mixed results
    if EvaluationOutcome.FAILED in outcomes:
        return EvaluationResult(
            result_id=result_id.strip(),
            run_id=run_id.strip(),
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.FAILED,
            verdict=EvaluationVerdict.UNSUPPORTED,
            confidence=EvaluationConfidenceClass.LOW,
            evidence_quality=_worst_evidence_quality(
                tuple(cr.evidence_quality for cr in criterion_results)
            ),
            criterion_results=criterion_results,
            failure_modes=all_failure_modes or (EvaluationFailureMode.CRITERION_FAILED,),
            evidence_refs=all_evidence,
            limitations=limitations,
            warnings=all_warnings,
            summary="One or more criteria failed",
        )

    # Partial / mixed pass
    return EvaluationResult(
        result_id=result_id.strip(),
        run_id=run_id.strip(),
        status=EvaluationResultStatus.COMPLETED,
        outcome=EvaluationOutcome.PARTIAL,
        verdict=EvaluationVerdict.PARTIALLY_SUPPORTED,
        confidence=EvaluationConfidenceClass.MODERATE,
        evidence_quality=_worst_evidence_quality(
            tuple(cr.evidence_quality for cr in criterion_results)
        ),
        criterion_results=criterion_results,
        failure_modes=all_failure_modes,
        evidence_refs=all_evidence,
        limitations=limitations,
        warnings=all_warnings,
        summary="Mixed criterion results — partially supported",
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

_OUTCOME_PRIORITY = {
    EvaluationOutcome.BLOCKED: 0,
    EvaluationOutcome.ERROR: 1,
    EvaluationOutcome.FAILED: 2,
    EvaluationOutcome.INCONCLUSIVE: 3,
    EvaluationOutcome.PARTIAL: 4,
    EvaluationOutcome.SKIPPED: 5,
    EvaluationOutcome.PASSED: 6,
}

_VERDICT_PRIORITY = {
    EvaluationVerdict.BLOCKED: 0,
    EvaluationVerdict.REJECTED: 1,
    EvaluationVerdict.CONFLICTED: 2,
    EvaluationVerdict.UNSUPPORTED: 3,
    EvaluationVerdict.INSUFFICIENT_EVIDENCE: 4,
    EvaluationVerdict.UNKNOWN: 5,
    EvaluationVerdict.PARTIALLY_SUPPORTED: 6,
    EvaluationVerdict.SUPPORTED: 7,
}


def aggregate_evaluation_results(
    *,
    result_set_id: str,
    run_id: str,
    results: tuple[EvaluationResult, ...],
) -> EvaluationResultSet:
    """Aggregate evaluation results categorically. No numeric scoring."""
    if not result_set_id or not result_set_id.strip():
        raise ValueError("result_set_id must not be empty")
    if not run_id or not run_id.strip():
        raise ValueError("run_id must not be empty")

    if not results:
        return EvaluationResultSet(
            result_set_id=result_set_id.strip(),
            run_id=run_id.strip(),
            results=(),
            aggregate_outcome=EvaluationOutcome.INCONCLUSIVE,
            aggregate_verdict=EvaluationVerdict.UNKNOWN,
            aggregate_confidence=EvaluationConfidenceClass.NONE,
            aggregate_evidence_quality=EvaluationEvidenceQuality.NONE,
            blockers=("No evaluation results to aggregate",),
            summary="Empty result set — inconclusive",
        )

    all_blockers = tuple(b for r in results for b in r.blockers)
    all_warnings = tuple(w for r in results for w in r.warnings)

    # Categorical dominance
    worst_outcome = min(results, key=lambda r: _OUTCOME_PRIORITY.get(r.outcome, 99)).outcome
    worst_verdict = min(results, key=lambda r: _VERDICT_PRIORITY.get(r.verdict, 99)).verdict

    # SUPPORTED only if ALL results are SUPPORTED with adequate/strong evidence
    if worst_outcome == EvaluationOutcome.PASSED and worst_verdict == EvaluationVerdict.SUPPORTED:
        if all(
            r.verdict == EvaluationVerdict.SUPPORTED
            and r.evidence_quality in _ADEQUATE_QUALITIES
            for r in results
        ):
            agg_verdict = EvaluationVerdict.SUPPORTED
            agg_outcome = EvaluationOutcome.PASSED
        else:
            agg_verdict = EvaluationVerdict.PARTIALLY_SUPPORTED
            agg_outcome = EvaluationOutcome.PARTIAL
    else:
        agg_outcome = worst_outcome
        agg_verdict = worst_verdict

    qualities = tuple(r.evidence_quality for r in results)
    agg_quality = _worst_evidence_quality(qualities)
    agg_confidence = _confidence_from_evidence(agg_quality)

    return EvaluationResultSet(
        result_set_id=result_set_id.strip(),
        run_id=run_id.strip(),
        results=results,
        aggregate_outcome=agg_outcome,
        aggregate_verdict=agg_verdict,
        aggregate_confidence=agg_confidence,
        aggregate_evidence_quality=agg_quality,
        blockers=all_blockers,
        warnings=all_warnings,
        summary=f"Aggregated {len(results)} result(s): {agg_outcome.value}/{agg_verdict.value}",
    )


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p151_object_model_report(
    *,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvaluationObjectModelReport:
    """Build P1.5.1 object model report."""
    objects = (
        "EvaluationResultStatus", "EvaluationOutcome", "EvaluationVerdict",
        "EvaluationConfidenceClass", "EvaluationEvidenceQuality", "EvaluationFailureMode",
        "EvaluationCriterionResult", "EvaluationResult", "EvaluationResultSet",
        "EvaluationObjectModelReport",
    )

    if blockers:
        status = "BLOCKED"
        summary = f"P1.5.1 object model BLOCKED: {len(blockers)} blocker(s)."
    elif warnings:
        status = "DEGRADED"
        summary = f"P1.5.1 object model DEGRADED: {len(warnings)} warning(s)."
    else:
        status = "READY"
        summary = "P1.5.1 Evaluation Object Model READY. Next: P1.5.2 — Capability Evidence Record."

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p151_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return EvaluationObjectModelReport(
        report_id=report_id,
        status=status,
        summary=summary,
        objects_added=objects,
        invariants=P151_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.2 — Capability Evidence Record",
    )


# ---------------------------------------------------------------------------
# Example builders (for CLI / tests)
# ---------------------------------------------------------------------------


def example_supported_criterion_result() -> EvaluationCriterionResult:
    """Example PASSED/SUPPORTED criterion result with adequate evidence."""
    return EvaluationCriterionResult(
        criterion_id="core_governance_present",
        outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        summary="Governance artifacts present",
        evidence_refs=("ev_governance_1",),
    )


def example_supported_evaluation_result() -> EvaluationResult:
    """Example resolved SUPPORTED result — does NOT verify capability."""
    return resolve_evaluation_result_from_criteria(
        result_id="result_example_1",
        run_id="run_example_1",
        criterion_results=(example_supported_criterion_result(),),
        evidence_refs=("ev_governance_1",),
        limitations=("small fixture set",),
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def _enum_val(v: Enum) -> str:
    return v.value


def evaluation_criterion_result_to_dict(result: EvaluationCriterionResult) -> dict[str, object]:
    return {
        "criterion_id": result.criterion_id,
        "outcome": _enum_val(result.outcome),
        "verdict": _enum_val(result.verdict),
        "evidence_quality": _enum_val(result.evidence_quality),
        "failure_modes": [_enum_val(fm) for fm in result.failure_modes],
        "summary": result.summary,
        "evidence_refs": list(result.evidence_refs),
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
    }


def evaluation_result_to_dict(result: EvaluationResult) -> dict[str, object]:
    return {
        "result_id": result.result_id,
        "run_id": result.run_id,
        "status": _enum_val(result.status),
        "outcome": _enum_val(result.outcome),
        "verdict": _enum_val(result.verdict),
        "confidence": _enum_val(result.confidence),
        "evidence_quality": _enum_val(result.evidence_quality),
        "criterion_results": [
            evaluation_criterion_result_to_dict(cr) for cr in result.criterion_results
        ],
        "failure_modes": [_enum_val(fm) for fm in result.failure_modes],
        "evidence_refs": list(result.evidence_refs),
        "limitations": list(result.limitations),
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "summary": result.summary,
    }


def evaluation_result_set_to_dict(result_set: EvaluationResultSet) -> dict[str, object]:
    return {
        "result_set_id": result_set.result_set_id,
        "run_id": result_set.run_id,
        "results": [evaluation_result_to_dict(r) for r in result_set.results],
        "aggregate_outcome": _enum_val(result_set.aggregate_outcome),
        "aggregate_verdict": _enum_val(result_set.aggregate_verdict),
        "aggregate_confidence": _enum_val(result_set.aggregate_confidence),
        "aggregate_evidence_quality": _enum_val(result_set.aggregate_evidence_quality),
        "blockers": list(result_set.blockers),
        "warnings": list(result_set.warnings),
        "summary": result_set.summary,
    }


def evaluation_object_model_report_to_dict(
    report: EvaluationObjectModelReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


__all__ = [
    "EvaluationResultStatus", "EvaluationOutcome", "EvaluationVerdict",
    "EvaluationConfidenceClass", "EvaluationEvidenceQuality", "EvaluationFailureMode",
    "EvaluationCriterionResult", "EvaluationResult", "EvaluationResultSet",
    "EvaluationObjectModelReport",
    "P151_INVARIANTS",
    "validate_evaluation_criterion_result", "validate_evaluation_result",
    "resolve_evaluation_result_from_criteria", "aggregate_evaluation_results",
    "build_p151_object_model_report",
    "example_supported_criterion_result", "example_supported_evaluation_result",
    "evaluation_criterion_result_to_dict", "evaluation_result_to_dict",
    "evaluation_result_set_to_dict", "evaluation_object_model_report_to_dict",
]

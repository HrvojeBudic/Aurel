"""P1.5.2 mapping from evaluation results to capability evidence."""
from __future__ import annotations

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
    capability_evidence_from_evaluation_result,
    capability_evidence_from_result_set,
)
from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationResultSet,
    EvaluationVerdict,
    aggregate_evaluation_results,
    example_supported_evaluation_result,
    resolve_evaluation_result_from_criteria,
)


def test_supported_evaluation_result_maps_to_usable_evidence():
    result = example_supported_evaluation_result()
    rec = capability_evidence_from_evaluation_result(
        evidence_id="ev1", result=result,
    )
    assert rec.status == CapabilityEvidenceStatus.USABLE
    assert rec.strength in (CapabilityEvidenceStrength.ADEQUATE, CapabilityEvidenceStrength.STRONG)


def test_partially_supported_maps_to_candidate():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.PARTIAL,
        verdict=EvaluationVerdict.PARTIALLY_SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=("ev1",),
    )
    result = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
        evidence_refs=("ev1",),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.CANDIDATE


def test_insufficient_evidence_maps_to_insufficient():
    result = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.INSUFFICIENT


def test_conflicted_result_maps_to_conflicted_evidence():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.INCONCLUSIVE,
        verdict=EvaluationVerdict.CONFLICTED,
        evidence_quality=EvaluationEvidenceQuality.CONFLICTED,
    )
    result = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.CONFLICTED


def test_rejected_result_maps_to_rejected_evidence():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.FAILED,
        verdict=EvaluationVerdict.REJECTED,
        evidence_quality=EvaluationEvidenceQuality.WEAK,
        failure_modes=(EvaluationFailureMode.REQUIRED_CRITERION_FAILED,),
    )
    result = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.REJECTED


def test_blocked_result_maps_to_invalid_evidence():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.BLOCKED,
        verdict=EvaluationVerdict.BLOCKED,
        evidence_quality=EvaluationEvidenceQuality.NONE,
        blockers=("blocked",),
    )
    result = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1", criterion_results=(cr,),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.INVALID


def test_error_result_maps_to_invalid_evidence():
    result = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.ERROR,
        outcome=EvaluationOutcome.ERROR, verdict=EvaluationVerdict.UNKNOWN,
        confidence=EvaluationConfidenceClass.UNKNOWN,
        evidence_quality=EvaluationEvidenceQuality.UNKNOWN,
        failure_modes=(EvaluationFailureMode.EVALUATOR_ERROR,),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.INVALID


def test_stale_evidence_quality_maps_to_stale_status():
    result = EvaluationResult(
        result_id="r1", run_id="run1",
        status=EvaluationResultStatus.COMPLETED,
        outcome=EvaluationOutcome.PASSED, verdict=EvaluationVerdict.SUPPORTED,
        confidence=EvaluationConfidenceClass.LOW,
        evidence_quality=EvaluationEvidenceQuality.STALE,
        evidence_refs=("ev1",),
    )
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status == CapabilityEvidenceStatus.STALE


def test_mapping_does_not_create_verified_status():
    result = example_supported_evaluation_result()
    rec = capability_evidence_from_evaluation_result(evidence_id="ev1", result=result)
    assert rec.status.value != "VERIFIED"
    assert "VERIFIED" not in {v.value for v in CapabilityEvidenceStatus}


def test_result_set_mapping():
    result = example_supported_evaluation_result()
    rs = aggregate_evaluation_results(
        result_set_id="rs1", run_id="run1", results=(result,),
    )
    rec = capability_evidence_from_result_set(evidence_id="ev_rs", result_set=rs)
    assert rec.kind.value == "EVALUATION_RESULT_SET"
    assert rec.status.value != "VERIFIED"

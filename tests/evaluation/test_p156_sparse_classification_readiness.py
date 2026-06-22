"""Sparse classification readiness tests — P1.5.6."""
from __future__ import annotations

from agentic_runtime.evaluation.result_classification import (
    CriterionClassificationInput,
    EvaluationObservation,
    EvaluationObservationStatus,
    EvaluationObservationType,
    classify_criterion_observation,
    classify_result_from_criterion_decisions,
    build_p156_result_classification_report,
)
from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchemaItem,
    EvaluationCriterionApplicability,
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
)
from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
)
from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationEvidenceQuality,
    EvaluationOutcome,
    EvaluationVerdict,
)


def _make_criterion(
    criterion_id: str = "crit_sc_001",
    kind: EvaluationCriterionKind = EvaluationCriterionKind.SPARSE_CONTEXT_QUALITY,
) -> EvaluationCriteriaSchemaItem:
    return EvaluationCriteriaSchemaItem(
        criterion_id=criterion_id,
        kind=kind,
        name="Sparse Test Criterion",
        description="A sparse test criterion.",
        severity=EvaluationCriterionSeverity.MEDIUM,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE,
        applicable_failure_modes=(),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.OUTPUT,
        ),
    )


def _make_sparse_obs(obs_type: EvaluationObservationType, evidence_refs=("ref_sc_01",)) -> EvaluationObservation:
    return EvaluationObservation(
        observation_id=f"obs_{obs_type.value.lower()}",
        observation_type=obs_type,
        status=EvaluationObservationStatus.PRESENT,
        evidence_refs=evidence_refs,
        source_ref="ds_sparse",
        trace_refs=("trace_001",),
        context_refs=("ctx_001",),
        summary=f"Sparse observation: {obs_type.value}",
    )


def test_sparse_context_observation_can_be_classified():
    obs = _make_sparse_obs(EvaluationObservationType.SPARSE_CONTEXT_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED


def test_retrieval_trace_observation_can_be_classified():
    obs = _make_sparse_obs(EvaluationObservationType.RETRIEVAL_TRACE_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED


def test_evidence_graph_observation_can_be_classified():
    obs = _make_sparse_obs(EvaluationObservationType.EVIDENCE_GRAPH_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED


def test_context_budget_observation_can_be_classified():
    obs = _make_sparse_obs(EvaluationObservationType.CONTEXT_BUDGET_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED


def test_lost_context_risk_observation_can_be_classified():
    obs = _make_sparse_obs(EvaluationObservationType.LOST_CONTEXT_RISK_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED


def test_lost_context_risk_missing_evidence_insufficient():
    obs = EvaluationObservation(
        observation_id="obs_lcr_missing",
        observation_type=EvaluationObservationType.LOST_CONTEXT_RISK_OBSERVATION,
        status=EvaluationObservationStatus.MISSING,
        summary="Lost context risk observation is MISSING.",
    )
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.INSUFFICIENT_EVIDENCE


def test_contradiction_survival_conflict_maps_to_conflicted():
    obs = EvaluationObservation(
        observation_id="obs_contra",
        observation_type=EvaluationObservationType.CONTRADICTION_SURVIVAL_OBSERVATION,
        status=EvaluationObservationStatus.CONFLICTED,
        summary="Contradiction survival observation is CONFLICTED.",
        warnings=("evidence_conflict",),
    )
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.CONFLICTED


def test_multi_hop_trace_observation_can_be_classified():
    obs = _make_sparse_obs(EvaluationObservationType.MULTI_HOP_TRACE_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED


def test_sparse_classification_does_not_run_sparse_compiler():
    # Classification of sparse observations does not refer to any compiler object
    obs = _make_sparse_obs(EvaluationObservationType.SPARSE_CONTEXT_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    # No reference to SparseContextCompiler in summary or string repr
    assert "SparseContextCompiler" not in str(d)
    assert "SparseContextCompiler" not in d.summary
    assert "sparse_context_compiler" not in str(d).lower()


def test_sparse_classification_does_not_claim_ssa_implemented():
    obs = _make_sparse_obs(EvaluationObservationType.SPARSE_CONTEXT_OBSERVATION)
    cin = CriterionClassificationInput(
        run_id="r_sc",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert "subquadratic" not in str(d).lower()
    assert "ssa" not in str(d).lower()
    assert "SparseAttention" not in str(d)


def test_sparse_classification_does_not_claim_subquadratic_model_implemented():
    report = build_p156_result_classification_report(sparse_classification_ready=True)
    assert "subquadratic" not in report.summary.lower()
    assert "ssa" not in report.summary.lower()


def test_report_sparse_ready_flag():
    report = build_p156_result_classification_report(sparse_classification_ready=True)
    assert report.sparse_classification_ready is True

    report2 = build_p156_result_classification_report(sparse_classification_ready=False)
    assert report2.sparse_classification_ready is False

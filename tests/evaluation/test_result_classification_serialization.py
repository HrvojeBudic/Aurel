"""Serialization tests — P1.5.6."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.result_classification import (
    CriterionClassificationDecision,
    CriterionClassificationInput,
    EvaluationObservation,
    EvaluationObservationStatus,
    EvaluationObservationType,
    ResultClassificationDecision,
    ResultClassificationInput,
    ResultClassificationPolicy,
    ResultClassificationReport,
    build_default_result_classification_policy,
    build_p156_result_classification_report,
    classify_criterion_observation,
    criterion_classification_decision_to_dict,
    criterion_classification_input_to_dict,
    evaluation_observation_to_dict,
    result_classification_decision_to_dict,
    result_classification_input_to_dict,
    result_classification_policy_to_dict,
    result_classification_report_to_dict,
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
    EvaluationConfidenceClass,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationVerdict,
)
from agentic_runtime.evaluation.evaluation_run_envelope import (
    GovernedEvaluationRunEnvelope,
    example_ready_run_envelope,
)


def _make_criterion(
    criterion_id: str = "crit_001",
) -> EvaluationCriteriaSchemaItem:
    return EvaluationCriteriaSchemaItem(
        criterion_id=criterion_id,
        kind=EvaluationCriterionKind.CORRECTNESS,
        name="Test Criterion",
        description="A test criterion.",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.TEST_RESULT,
        applicable_failure_modes=(),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.OUTPUT,
        ),
    )


def _make_obs() -> EvaluationObservation:
    return EvaluationObservation(
        observation_id="obs_001",
        observation_type=EvaluationObservationType.TEST_RESULT,
        status=EvaluationObservationStatus.PRESENT,
        source_ref="ref_src",
        evidence_refs=("ref_ev_001",),
        trace_refs=("ref_trace_001",),
        context_refs=("ref_ctx_001",),
        summary="Test observation",
        notes=("note1",),
        warnings=("warn1",),
        blockers=("block1",),
    )


def test_evaluation_observation_json_serializable():
    d = evaluation_observation_to_dict(_make_obs())
    s = json.dumps(d)
    assert isinstance(s, str)
    assert "obs_001" in s
    assert "TEST_RESULT" in s
    # Tuples become lists
    assert "ref_ev_001" in s


def test_criterion_classification_input_json_serializable():
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=_make_obs(),
        required=True,
        blocking=False,
    )
    d = criterion_classification_input_to_dict(cin)
    s = json.dumps(d)
    assert "crit_001" in s


def test_criterion_classification_decision_json_serializable():
    obs = _make_obs()
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    d = criterion_classification_decision_to_dict(decision)
    s = json.dumps(d)
    assert "crit_001" in s
    assert "SUPPORTED" in s


def test_result_classification_input_json_serializable():
    envelope = example_ready_run_envelope()
    rin = ResultClassificationInput(
        run_envelope=envelope,
        observations=(_make_obs(),),
    )
    d = result_classification_input_to_dict(rin)
    s = json.dumps(d)
    assert isinstance(s, str)


def test_result_classification_decision_json_serializable():
    obs = _make_obs()
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    rcd = ResultClassificationDecision(
        run_id="r1",
        status="READY",
        outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        confidence=EvaluationConfidenceClass.MODERATE,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        criterion_decisions=(d1,),
        evidence_refs=("ref_01",),
    )
    d = result_classification_decision_to_dict(rcd)
    s = json.dumps(d)
    assert "READY" in s


def test_result_classification_policy_json_serializable():
    policy = build_default_result_classification_policy()
    d = result_classification_policy_to_dict(policy)
    assert d["require_evidence_for_supported"] is True
    s = json.dumps(d)
    assert "default_p156" in s


def test_result_classification_report_json_serializable():
    report = build_p156_result_classification_report(sparse_classification_ready=True)
    d = result_classification_report_to_dict(report)
    s = json.dumps(d)
    assert "P1.5.6" in s
    assert "P1.5.7" in s

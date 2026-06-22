"""Scope guard tests — P1.5.6."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.result_classification import (
    CriterionClassificationDecision,
    CriterionClassificationInput,
    EvaluationObservation,
    EvaluationObservationStatus,
    EvaluationObservationType,
    ResultClassificationDecision,
    ResultClassificationInput,
    ResultClassificationPolicy,
    build_default_result_classification_policy,
    build_p156_result_classification_report,
    classify_criterion_observation,
    classify_result_from_criterion_decisions,
    classify_result_from_observations,
    criterion_decision_to_result,
    result_classification_to_evaluation_result,
    validate_evaluation_observation,
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
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationVerdict,
)


def _make_criterion(
    criterion_id: str = "crit_001",
    kind: EvaluationCriterionKind = EvaluationCriterionKind.CORRECTNESS,
) -> EvaluationCriteriaSchemaItem:
    return EvaluationCriteriaSchemaItem(
        criterion_id=criterion_id,
        kind=kind,
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
        evidence_refs=("ref_ev_001",),
        summary="Test observation",
    )


def make_supported_decision(criterion_id: str = "crit_001") -> CriterionClassificationDecision:
    obs = _make_obs()
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(criterion_id),
        observation=obs,
        required=True,
        blocking=False,
    )
    return classify_criterion_observation(classification_input=cin)


def test_p156_does_not_call_llm_or_tools():
    # No function in P1.5.6 should reference LLM or tool execution
    funcs = [
        validate_evaluation_observation,
        build_default_result_classification_policy,
        classify_criterion_observation,
        criterion_decision_to_result,
        classify_result_from_criterion_decisions,
        result_classification_to_evaluation_result,
        classify_result_from_observations,
        build_p156_result_classification_report,
    ]
    for f in funcs:
        src = inspect.getsource(f)
        assert "llm_judge" not in src.lower() or "LLM_JUDGE_OUTPUT" in src, f"{f.__name__} references LLM judge execution"
        # LLM_JUDGE_OUTPUT as enum value is fine; actual LLM calls are not
        assert "call_tool" not in src.lower(), f"{f.__name__} calls tools"


def test_p156_does_not_run_benchmarks():
    # No benchmark execution
    funcs = [classify_criterion_observation, classify_result_from_observations]
    for f in funcs:
        src = inspect.getsource(f)
        assert "benchmark" not in src.lower(), f"{f.__name__} runs benchmarks"


def test_p156_does_not_execute_evaluation():
    # Classification does not execute evaluation or run commands
    d = make_supported_decision()
    assert d.verdict == EvaluationVerdict.SUPPORTED
    # This is classification, not execution


def test_p156_does_not_verify_capability():
    d = make_supported_decision()
    result = criterion_decision_to_result(d)
    assert result.verdict != "VERIFIED"
    assert result.outcome != "VERIFIED"
    # The string "VERIFIED" should not appear in the verdict
    assert result.verdict.value != "VERIFIED"


def test_p156_does_not_bind_evidence_to_claim():
    d = make_supported_decision()
    result = criterion_decision_to_result(d)
    # No evidence-to-claim binding link exists
    assert not hasattr(result, "bound_claim")
    assert not hasattr(result, "evidence_bindings")
    assert not hasattr(result, "claim_links")


def test_p156_does_not_create_capability_evidence_record_as_truth():
    d = make_supported_decision()
    result = criterion_decision_to_result(d)
    assert not hasattr(result, "capability_evidence_record")
    assert not hasattr(result, "evidence_record")
    assert not hasattr(result, "CapabilityEvidenceRecord")


def test_p156_does_not_introduce_numeric_score():
    src = inspect.getsource(classify_criterion_observation)
    assert "score =" not in src or "numeric" not in src.lower()
    # No numeric scores in any model
    d = make_supported_decision()
    s = str(d)
    # ConfidenceClass is categorical, not numeric
    assert d.confidence.value in ("NONE", "LOW", "MODERATE", "HIGH")


def test_p156_does_not_implement_sparse_context_compiler():
    # No Sparse Context Compiler is created or imported
    src = inspect.getsource(classify_criterion_observation)
    assert "SparseContextCompiler" not in src


def test_p156_does_not_implement_hub_runtime():
    # No Hub runtime execution
    src = inspect.getsource(classify_result_from_observations)
    assert "hub_runtime" not in src.lower()
    assert "A_HUB" not in src or "SPARSE_CONTEXT" not in src


def test_p156_prepares_p157_evidence_to_claim_binding():
    report = build_p156_result_classification_report()
    assert "P1.5.7" in report.next_module
    assert "Evidence-to-Claim Binding" in report.next_module or "evidence" in report.next_module.lower()

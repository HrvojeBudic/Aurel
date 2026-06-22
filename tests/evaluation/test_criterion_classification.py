"""Criterion classification tests — P1.5.6."""
from __future__ import annotations

from agentic_runtime.evaluation.result_classification import (
    CriterionClassificationInput,
    EvaluationObservation,
    EvaluationObservationStatus,
    EvaluationObservationType,
    classify_criterion_observation,
    criterion_decision_to_result,
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
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationVerdict,
)


def _make_criterion(
    criterion_id: str = "crit_001",
    requirement_level: EvaluationCriterionRequirementLevel = EvaluationCriterionRequirementLevel.REQUIRED,
) -> EvaluationCriteriaSchemaItem:
    return EvaluationCriteriaSchemaItem(
        criterion_id=criterion_id,
        kind=EvaluationCriterionKind.CORRECTNESS,
        name="Test Criterion",
        description="A test criterion.",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=requirement_level,
        evidence_requirement=EvaluationCriterionEvidenceRequirement.TEST_RESULT,
        applicable_failure_modes=(),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.OUTPUT,
        ),
    )


def _make_obs(
    observation_id: str = "obs_001",
    observation_type: EvaluationObservationType = EvaluationObservationType.TEST_RESULT,
    status: EvaluationObservationStatus = EvaluationObservationStatus.PRESENT,
    evidence_refs: tuple[str, ...] = (),
    source_ref: str | None = None,
    trace_refs: tuple[str, ...] = (),
    context_refs: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> EvaluationObservation:
    return EvaluationObservation(
        observation_id=observation_id,
        observation_type=observation_type,
        status=status,
        source_ref=source_ref,
        evidence_refs=evidence_refs,
        trace_refs=trace_refs,
        context_refs=context_refs,
        summary="Test observation",
        warnings=warnings,
        blockers=blockers,
    )


def test_present_with_strong_evidence():
    obs = _make_obs(evidence_refs=("ev1", "ev2"))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED
    assert d.evidence_quality == EvaluationEvidenceQuality.STRONG


def test_present_with_single_evidence_adequate():
    obs = _make_obs(evidence_refs=("ev1",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict == EvaluationVerdict.SUPPORTED
    assert d.evidence_quality == EvaluationEvidenceQuality.ADEQUATE


def test_missing_optional_is_inconclusive():
    obs = _make_obs(status=EvaluationObservationStatus.MISSING)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(requirement_level=EvaluationCriterionRequirementLevel.OPTIONAL),
        observation=obs,
        required=False,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.outcome == EvaluationOutcome.INCONCLUSIVE


def test_decision_includes_criterion_id():
    obs = _make_obs(evidence_refs=("ev1",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("my_criterion_id"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.criterion_id == "my_criterion_id"


def test_unknown_with_policy_allow_true():
    from agentic_runtime.evaluation.result_classification import ResultClassificationPolicy

    policy = ResultClassificationPolicy(
        policy_id="test_policy",
        allow_unknown_observation_to_pass=True,
    )
    obs = _make_obs(status=EvaluationObservationStatus.UNKNOWN)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=False,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin, policy=policy)
    assert d.verdict == EvaluationVerdict.UNKNOWN


def test_decision_summary_is_not_empty():
    obs = _make_obs(evidence_refs=("ev1",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.summary


def test_evidence_refs_preserved():
    obs = _make_obs(evidence_refs=("ev_a", "ev_b"))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert "ev_a" in d.evidence_refs
    assert "ev_b" in d.evidence_refs


def test_input_evidence_refs_override_obs():
    obs = _make_obs(evidence_refs=("obs_ev",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
        evidence_refs=("input_ev",),
    )
    d = classify_criterion_observation(classification_input=cin)
    assert "input_ev" in d.evidence_refs

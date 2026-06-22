"""Core result classification tests — P1.5.6."""
from __future__ import annotations

from agentic_runtime.evaluation.result_classification import (
    CriterionClassificationInput,
    EvaluationObservation,
    EvaluationObservationStatus,
    EvaluationObservationType,
    build_default_result_classification_policy,
    classify_criterion_observation,
    classify_result_from_criterion_decisions,
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


def _make_observation(
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


# ---------------------------------------------------------------------------
# Observation type/status
# ---------------------------------------------------------------------------


def test_observation_type_closed_world():
    assert EvaluationObservationType.STATIC_REVIEW.value == "STATIC_REVIEW"
    assert EvaluationObservationType.FIXTURE_RESULT.value == "FIXTURE_RESULT"
    assert EvaluationObservationType.TEST_RESULT.value == "TEST_RESULT"
    assert EvaluationObservationType.HUMAN_REVIEW.value == "HUMAN_REVIEW"
    assert EvaluationObservationType.LLM_JUDGE_OUTPUT.value == "LLM_JUDGE_OUTPUT"
    assert EvaluationObservationType.TOOL_OUTPUT.value == "TOOL_OUTPUT"
    assert EvaluationObservationType.POLICY_DECISION.value == "POLICY_DECISION"
    assert EvaluationObservationType.TRUST_EVIDENCE.value == "TRUST_EVIDENCE"
    assert EvaluationObservationType.CAPABILITY_EVIDENCE.value == "CAPABILITY_EVIDENCE"
    assert EvaluationObservationType.SPARSE_CONTEXT_OBSERVATION.value == "SPARSE_CONTEXT_OBSERVATION"
    assert EvaluationObservationType.RETRIEVAL_TRACE_OBSERVATION.value == "RETRIEVAL_TRACE_OBSERVATION"
    assert EvaluationObservationType.EVIDENCE_GRAPH_OBSERVATION.value == "EVIDENCE_GRAPH_OBSERVATION"
    assert EvaluationObservationType.CONTEXT_BUDGET_OBSERVATION.value == "CONTEXT_BUDGET_OBSERVATION"
    assert EvaluationObservationType.LOST_CONTEXT_RISK_OBSERVATION.value == "LOST_CONTEXT_RISK_OBSERVATION"
    assert EvaluationObservationType.CONTRADICTION_SURVIVAL_OBSERVATION.value == "CONTRADICTION_SURVIVAL_OBSERVATION"
    assert EvaluationObservationType.MULTI_HOP_TRACE_OBSERVATION.value == "MULTI_HOP_TRACE_OBSERVATION"
    assert EvaluationObservationType.UNKNOWN.value == "UNKNOWN"


def test_observation_status_closed_world():
    assert EvaluationObservationStatus.PRESENT.value == "PRESENT"
    assert EvaluationObservationStatus.MISSING.value == "MISSING"
    assert EvaluationObservationStatus.PARTIAL.value == "PARTIAL"
    assert EvaluationObservationStatus.CONFLICTED.value == "CONFLICTED"
    assert EvaluationObservationStatus.BLOCKED.value == "BLOCKED"
    assert EvaluationObservationStatus.INVALID.value == "INVALID"
    assert EvaluationObservationStatus.UNKNOWN.value == "UNKNOWN"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_observation_rejects_empty_id():
    obs = _make_observation(observation_id="")
    issues = validate_evaluation_observation(obs)
    assert any("observation_id" in i for i in issues)


def test_validate_blocked_observation_requires_blocker():
    obs = _make_observation(status=EvaluationObservationStatus.BLOCKED, blockers=())
    issues = validate_evaluation_observation(obs)
    assert any("BLOCKED" in i for i in issues)


def test_validate_invalid_observation_requires_blocker():
    obs = _make_observation(status=EvaluationObservationStatus.INVALID, blockers=())
    issues = validate_evaluation_observation(obs)
    assert any("INVALID" in i for i in issues)


def test_validate_conflicted_observation_requires_warning_or_blocker():
    obs = _make_observation(status=EvaluationObservationStatus.CONFLICTED, warnings=(), blockers=())
    issues = validate_evaluation_observation(obs)
    assert any("CONFLICTED" in i for i in issues)


def test_validate_present_without_refs_warns():
    obs = _make_observation(
        status=EvaluationObservationStatus.PRESENT,
        evidence_refs=(),
        source_ref=None,
        trace_refs=(),
        context_refs=(),
    )
    issues = validate_evaluation_observation(obs)
    assert any("WEAK" in i for i in issues)


def test_default_policy_safe_values():
    policy = build_default_result_classification_policy()
    assert policy.require_evidence_for_supported is True
    assert policy.block_on_conflicted_evidence is True
    assert policy.block_on_missing_required_evidence is True
    assert policy.allow_unknown_observation_to_pass is False


# ---------------------------------------------------------------------------
# Criterion classification
# ---------------------------------------------------------------------------


def test_present_observation_with_evidence_supported():
    obs = _make_observation(evidence_refs=("ref_ev_001", "ref_ev_002"))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.PASSED
    assert decision.verdict == EvaluationVerdict.SUPPORTED
    assert decision.evidence_quality in (EvaluationEvidenceQuality.ADEQUATE, EvaluationEvidenceQuality.STRONG)


def test_present_observation_without_evidence_is_weak_or_partial():
    obs = _make_observation(evidence_refs=(), source_ref="ref_src_001")
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    # with default policy (require_evidence_for_supported=True), no evidence refs —> PARTIAL
    assert decision.outcome == EvaluationOutcome.PARTIAL
    assert decision.verdict == EvaluationVerdict.PARTIALLY_SUPPORTED


def test_missing_required_observation_insufficient_evidence():
    obs = _make_observation(status=EvaluationObservationStatus.MISSING)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(requirement_level=EvaluationCriterionRequirementLevel.REQUIRED),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.INCONCLUSIVE
    assert decision.verdict == EvaluationVerdict.INSUFFICIENT_EVIDENCE
    assert EvaluationFailureMode.MISSING_EVIDENCE in decision.failure_modes


def test_missing_blocking_observation_failed():
    obs = _make_observation(status=EvaluationObservationStatus.MISSING)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(requirement_level=EvaluationCriterionRequirementLevel.BLOCKING),
        observation=obs,
        required=True,
        blocking=True,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.FAILED
    assert decision.verdict == EvaluationVerdict.REJECTED
    assert EvaluationFailureMode.REQUIRED_CRITERION_FAILED in decision.failure_modes
    assert EvaluationFailureMode.MISSING_EVIDENCE in decision.failure_modes


def test_conflicted_observation_conflicted_verdict():
    obs = _make_observation(status=EvaluationObservationStatus.CONFLICTED, warnings=("conflict",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.INCONCLUSIVE
    assert decision.verdict == EvaluationVerdict.CONFLICTED
    assert decision.evidence_quality == EvaluationEvidenceQuality.CONFLICTED


def test_blocked_observation_blocked_verdict():
    obs = _make_observation(status=EvaluationObservationStatus.BLOCKED, blockers=("blocked_reason",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.BLOCKED
    assert decision.verdict == EvaluationVerdict.BLOCKED


def test_invalid_observation_unsupported_or_error():
    obs = _make_observation(status=EvaluationObservationStatus.INVALID, blockers=("invalid_reason",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.ERROR
    assert decision.verdict == EvaluationVerdict.UNSUPPORTED
    assert EvaluationFailureMode.INVALID_INPUT in decision.failure_modes


def test_unknown_observation_cannot_pass():
    obs = _make_observation(status=EvaluationObservationStatus.UNKNOWN)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome != EvaluationOutcome.PASSED
    assert decision.verdict != EvaluationVerdict.SUPPORTED


def test_blocking_failure_adds_required_criterion_failed():
    obs = _make_observation(status=EvaluationObservationStatus.MISSING)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(requirement_level=EvaluationCriterionRequirementLevel.BLOCKING),
        observation=obs,
        required=True,
        blocking=True,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert EvaluationFailureMode.REQUIRED_CRITERION_FAILED in decision.failure_modes


def test_supported_requires_evidence_under_default_policy():
    obs = _make_observation(evidence_refs=(), source_ref="ref_src_001")
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    # With default policy (require_evidence_for_supported=True), no evidence refs should NOT produce SUPPORTED
    assert decision.verdict != EvaluationVerdict.SUPPORTED


def test_present_observation_can_support_with_evidence():
    obs = _make_observation(evidence_refs=("ref_ev_001",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=True,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.verdict == EvaluationVerdict.SUPPORTED


def test_partial_observation_is_partially_supported():
    obs = _make_observation(status=EvaluationObservationStatus.PARTIAL)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion(),
        observation=obs,
        required=False,
        blocking=False,
    )
    decision = classify_criterion_observation(classification_input=cin)
    assert decision.outcome == EvaluationOutcome.PARTIAL
    assert decision.verdict == EvaluationVerdict.PARTIALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Result classification from criterion decisions
# ---------------------------------------------------------------------------


def test_no_decisions_insufficient_evidence():
    decision = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(),
    )
    assert decision.outcome == EvaluationOutcome.INCONCLUSIVE
    assert decision.verdict == EvaluationVerdict.INSUFFICIENT_EVIDENCE


def test_all_supported_results_passed_supported():
    obs = _make_observation(evidence_refs=("ref_01",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    obs2 = _make_observation(evidence_refs=("ref_02",))
    cin2 = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_002"),
        observation=obs2,
        required=True,
        blocking=False,
    )
    d2 = classify_criterion_observation(classification_input=cin2)

    result = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(d1, d2),
    )
    assert result.outcome == EvaluationOutcome.PASSED
    assert result.verdict == EvaluationVerdict.SUPPORTED


def test_conflicted_decision_dominates():
    obs = _make_observation(evidence_refs=("ref_01",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    obs2 = _make_observation(status=EvaluationObservationStatus.CONFLICTED, warnings=("conflict",))
    cin2 = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_002"),
        observation=obs2,
        required=True,
        blocking=False,
    )
    d2 = classify_criterion_observation(classification_input=cin2)

    result = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(d1, d2),
    )
    assert result.verdict == EvaluationVerdict.CONFLICTED
    assert result.outcome == EvaluationOutcome.INCONCLUSIVE


def test_blocked_decision_dominates():
    obs = _make_observation(evidence_refs=("ref_01",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    obs2 = _make_observation(status=EvaluationObservationStatus.BLOCKED, blockers=("blocked",))
    cin2 = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_002"),
        observation=obs2,
        required=True,
        blocking=False,
    )
    d2 = classify_criterion_observation(classification_input=cin2)

    result = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(d1, d2),
    )
    assert result.verdict == EvaluationVerdict.BLOCKED
    assert result.outcome == EvaluationOutcome.BLOCKED


def test_required_failure_rejects_result():
    obs = _make_observation(status=EvaluationObservationStatus.MISSING)
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001", requirement_level=EvaluationCriterionRequirementLevel.BLOCKING),
        observation=obs,
        required=True,
        blocking=True,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    obs2 = _make_observation(evidence_refs=("ref_02",))
    cin2 = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_002"),
        observation=obs2,
        required=True,
        blocking=False,
    )
    d2 = classify_criterion_observation(classification_input=cin2)

    result = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(d1, d2),
    )
    assert result.verdict == EvaluationVerdict.REJECTED
    assert result.outcome == EvaluationOutcome.FAILED


def test_mixed_decisions_partially_supported():
    obs = _make_observation(evidence_refs=("ref_01",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    obs2 = _make_observation(evidence_refs=(), source_ref="ref_src")
    cin2 = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_002"),
        observation=obs2,
        required=True,
        blocking=False,
    )
    d2 = classify_criterion_observation(classification_input=cin2)

    # d1 is SUPPORTED, d2 is PARTIALLY_SUPPORTED —> mixed
    result = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(d1, d2),
    )
    assert result.verdict == EvaluationVerdict.PARTIALLY_SUPPORTED
    assert result.outcome == EvaluationOutcome.PARTIAL


def test_missing_required_evidence_cannot_support():
    obs = _make_observation(evidence_refs=("ref_01",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d1 = classify_criterion_observation(classification_input=cin)

    obs2 = _make_observation(status=EvaluationObservationStatus.MISSING)
    cin2 = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_002", requirement_level=EvaluationCriterionRequirementLevel.REQUIRED),
        observation=obs2,
        required=True,
        blocking=False,
    )
    d2 = classify_criterion_observation(classification_input=cin2)

    result = classify_result_from_criterion_decisions(
        run_id="r1",
        result_id="result_001",
        decisions=(d1, d2),
    )
    # d2 is INSUFFICIENT_EVIDENCE, so result should not be SUPPORTED
    assert result.verdict != EvaluationVerdict.SUPPORTED


def test_no_numeric_score():
    obs = _make_observation(evidence_refs=("ref_01",))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    s = str(d)
    assert "0." not in s or "score" not in s.lower()


def test_verdict_never_verified():
    # No classification decision should produce VERIFIED
    obs = _make_observation(evidence_refs=("ref_01", "ref_02", "ref_03"))
    cin = CriterionClassificationInput(
        run_id="r1",
        criterion=_make_criterion("crit_001"),
        observation=obs,
        required=True,
        blocking=False,
    )
    d = classify_criterion_observation(classification_input=cin)
    assert d.verdict.value != "VERIFIED"
    assert d.outcome.value != "VERIFIED"

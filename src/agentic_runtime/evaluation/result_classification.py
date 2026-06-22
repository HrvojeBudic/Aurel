"""P1.5.6 — Result Classification Engine + Sparse Classification Readiness.

Translates supplied evaluation observations into standardized evaluation result
semantics. Classification is not verification — it does NOT execute evaluation,
call LLMs/tools, verify capability, or bind evidence to claims.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .evaluation_criteria_schema import (
    EvaluationCriteriaSchemaItem,
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionRequirementLevel,
    criteria_schema_item_to_dict,
)
from .evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationVerdict,
    evaluation_criterion_result_to_dict,
    evaluation_result_to_dict,
)
from .evaluation_run_envelope import (
    EvaluationRunEvidenceRequirement,
    GovernedEvaluationRunEnvelope,
    governed_evaluation_run_envelope_to_dict,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvaluationObservationType(str, Enum):
    STATIC_REVIEW = "STATIC_REVIEW"
    FIXTURE_RESULT = "FIXTURE_RESULT"
    TEST_RESULT = "TEST_RESULT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    LLM_JUDGE_OUTPUT = "LLM_JUDGE_OUTPUT"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    POLICY_DECISION = "POLICY_DECISION"
    TRUST_EVIDENCE = "TRUST_EVIDENCE"
    CAPABILITY_EVIDENCE = "CAPABILITY_EVIDENCE"

    SPARSE_CONTEXT_OBSERVATION = "SPARSE_CONTEXT_OBSERVATION"
    RETRIEVAL_TRACE_OBSERVATION = "RETRIEVAL_TRACE_OBSERVATION"
    EVIDENCE_GRAPH_OBSERVATION = "EVIDENCE_GRAPH_OBSERVATION"
    CONTEXT_BUDGET_OBSERVATION = "CONTEXT_BUDGET_OBSERVATION"
    LOST_CONTEXT_RISK_OBSERVATION = "LOST_CONTEXT_RISK_OBSERVATION"
    CONTRADICTION_SURVIVAL_OBSERVATION = "CONTRADICTION_SURVIVAL_OBSERVATION"
    MULTI_HOP_TRACE_OBSERVATION = "MULTI_HOP_TRACE_OBSERVATION"

    UNKNOWN = "UNKNOWN"


class EvaluationObservationStatus(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    CONFLICTED = "CONFLICTED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


P156_INVARIANTS: tuple[str, ...] = (
    "INV-P156-01: Result classification does not verify capability.",
    "INV-P156-02: Classification does not execute evaluation.",
    "INV-P156-03: Classification only interprets supplied observations.",
    "INV-P156-04: Unknown observations cannot pass.",
    "INV-P156-05: Missing required evidence cannot produce SUPPORTED.",
    "INV-P156-06: Conflicted evidence blocks SUPPORTED.",
    "INV-P156-07: Blocking criterion failure produces REQUIRED_CRITERION_FAILED.",
    "INV-P156-08: No numeric scoring is introduced.",
    "INV-P156-09: Conversion to EvaluationResult does not create capability evidence.",
    "INV-P156-10: P1.5.7 is the next module.",
    "INV-P156-SC-01: Sparse-context observations can be classified.",
    "INV-P156-SC-02: Lost context risk classification is metadata-based, not solved by engine.",
    "INV-P156-SC-03: Classification does not implement Sparse Context Compiler, retrieval router, evidence graph builder, SSA or true subquadratic attention.",
)

_SPARSE_OBSERVATION_TYPES: frozenset[EvaluationObservationType] = frozenset({
    EvaluationObservationType.SPARSE_CONTEXT_OBSERVATION,
    EvaluationObservationType.RETRIEVAL_TRACE_OBSERVATION,
    EvaluationObservationType.EVIDENCE_GRAPH_OBSERVATION,
    EvaluationObservationType.CONTEXT_BUDGET_OBSERVATION,
    EvaluationObservationType.LOST_CONTEXT_RISK_OBSERVATION,
    EvaluationObservationType.CONTRADICTION_SURVIVAL_OBSERVATION,
    EvaluationObservationType.MULTI_HOP_TRACE_OBSERVATION,
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationObservation:
    observation_id: str
    observation_type: EvaluationObservationType
    status: EvaluationObservationStatus

    source_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    trace_refs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()

    summary: str = ""
    notes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CriterionClassificationInput:
    run_id: str
    criterion: EvaluationCriteriaSchemaItem
    observation: EvaluationObservation

    required: bool
    blocking: bool

    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CriterionClassificationDecision:
    criterion_id: str

    outcome: EvaluationOutcome
    verdict: EvaluationVerdict
    confidence: EvaluationConfidenceClass
    evidence_quality: EvaluationEvidenceQuality

    failure_modes: tuple[EvaluationFailureMode, ...] = ()

    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    summary: str = ""


@dataclass(frozen=True)
class ResultClassificationInput:
    run_envelope: GovernedEvaluationRunEnvelope
    observations: tuple[EvaluationObservation, ...]

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultClassificationDecision:
    run_id: str

    status: str  # aggregate status (READY, DEGRADED, BLOCKED, INCONCLUSIVE)
    outcome: EvaluationOutcome
    verdict: EvaluationVerdict
    confidence: EvaluationConfidenceClass
    evidence_quality: EvaluationEvidenceQuality

    criterion_decisions: tuple[CriterionClassificationDecision, ...] = ()
    failure_modes: tuple[EvaluationFailureMode, ...] = ()

    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    summary: str = ""


@dataclass(frozen=True)
class ResultClassificationPolicy:
    policy_id: str

    require_evidence_for_supported: bool = True
    block_on_conflicted_evidence: bool = True
    block_on_missing_required_evidence: bool = True
    allow_unknown_observation_to_pass: bool = False

    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultClassificationReport:
    report_id: str
    status: str
    summary: str

    classifications_created: int
    criterion_decisions_created: int

    sparse_classification_ready: bool

    objects_added: tuple[str, ...]
    invariants: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    next_module: str


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_evaluation_observation(
    observation: EvaluationObservation,
) -> tuple[str, ...]:
    issues: list[str] = []

    if not observation.observation_id or not observation.observation_id.strip():
        issues.append("observation_id must not be empty")

    if observation.observation_type == EvaluationObservationType.UNKNOWN:
        issues.append("observation_type is UNKNOWN — cannot produce SUPPORTED")

    if observation.status == EvaluationObservationStatus.BLOCKED:
        if not observation.blockers:
            issues.append("BLOCKED observation requires at least one blocker")

    if observation.status == EvaluationObservationStatus.INVALID:
        if not observation.blockers:
            issues.append("INVALID observation requires at least one blocker")

    if observation.status == EvaluationObservationStatus.CONFLICTED:
        if not observation.warnings and not observation.blockers:
            issues.append("CONFLICTED observation requires warning or blocker")

    if observation.status == EvaluationObservationStatus.PRESENT:
        if not observation.evidence_refs and not observation.source_ref and not observation.trace_refs and not observation.context_refs:
            issues.append("PRESENT observation without any refs (evidence/source/trace/context) — evidence quality will be WEAK")

    return tuple(issues)


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def build_default_result_classification_policy() -> ResultClassificationPolicy:
    return ResultClassificationPolicy(
        policy_id="default_p156",
        require_evidence_for_supported=True,
        block_on_conflicted_evidence=True,
        block_on_missing_required_evidence=True,
        allow_unknown_observation_to_pass=False,
    )


# ---------------------------------------------------------------------------
# Criterion classification
# ---------------------------------------------------------------------------


def classify_criterion_observation(
    *,
    classification_input: CriterionClassificationInput,
    policy: ResultClassificationPolicy | None = None,
) -> CriterionClassificationDecision:
    if policy is None:
        policy = build_default_result_classification_policy()

    obs = classification_input.observation
    crit = classification_input.criterion
    required = classification_input.required
    blocking = classification_input.blocking

    evidence_refs = classification_input.evidence_refs or obs.evidence_refs
    warnings: list[str] = list(classification_input.warnings) + list(obs.warnings)
    blockers_list: list[str] = list(classification_input.blockers) + list(obs.blockers)
    failure_modes: list[EvaluationFailureMode] = []

    outcome: EvaluationOutcome
    verdict: EvaluationVerdict
    evidence_quality: EvaluationEvidenceQuality
    confidence: EvaluationConfidenceClass

    # MISSING observation
    if obs.status == EvaluationObservationStatus.MISSING:
        evidence_quality = EvaluationEvidenceQuality.NONE
        if blocking:
            outcome = EvaluationOutcome.FAILED
            verdict = EvaluationVerdict.REJECTED
            failure_modes.append(EvaluationFailureMode.REQUIRED_CRITERION_FAILED)
            failure_modes.append(EvaluationFailureMode.MISSING_EVIDENCE)
            blockers_list.append(f"blocking criterion {crit.criterion_id!r} has MISSING observation")
        elif required:
            outcome = EvaluationOutcome.INCONCLUSIVE
            verdict = EvaluationVerdict.INSUFFICIENT_EVIDENCE
            failure_modes.append(EvaluationFailureMode.MISSING_EVIDENCE)
            failure_modes.append(EvaluationFailureMode.INSUFFICIENT_EVIDENCE)
        else:
            outcome = EvaluationOutcome.INCONCLUSIVE
            verdict = EvaluationVerdict.INSUFFICIENT_EVIDENCE
            failure_modes.append(EvaluationFailureMode.MISSING_EVIDENCE)

        confidence = EvaluationConfidenceClass.LOW
        warnings.append(f"missing observation for criterion {crit.criterion_id!r}")

    # CONFLICTED observation
    elif obs.status == EvaluationObservationStatus.CONFLICTED:
        outcome = EvaluationOutcome.INCONCLUSIVE
        verdict = EvaluationVerdict.CONFLICTED
        evidence_quality = EvaluationEvidenceQuality.CONFLICTED
        confidence = EvaluationConfidenceClass.LOW
        failure_modes.append(EvaluationFailureMode.CONFLICTED_EVIDENCE)
        if policy.block_on_conflicted_evidence and blocking:
            blockers_list.append(f"blocking criterion {crit.criterion_id!r} has CONFLICTED observation")

    # BLOCKED observation
    elif obs.status == EvaluationObservationStatus.BLOCKED:
        outcome = EvaluationOutcome.BLOCKED
        verdict = EvaluationVerdict.BLOCKED
        evidence_quality = EvaluationEvidenceQuality.NONE
        confidence = EvaluationConfidenceClass.NONE
        blockers_list.append(f"observation BLOCKED for criterion {crit.criterion_id!r}")

    # INVALID observation
    elif obs.status == EvaluationObservationStatus.INVALID:
        outcome = EvaluationOutcome.ERROR
        verdict = EvaluationVerdict.UNSUPPORTED
        evidence_quality = EvaluationEvidenceQuality.NONE
        confidence = EvaluationConfidenceClass.NONE
        failure_modes.append(EvaluationFailureMode.INVALID_INPUT)
        blockers_list.append(f"observation INVALID for criterion {crit.criterion_id!r}")

    # UNKNOWN observation
    elif obs.status == EvaluationObservationStatus.UNKNOWN:
        if policy.allow_unknown_observation_to_pass:
            outcome = EvaluationOutcome.INCONCLUSIVE
            verdict = EvaluationVerdict.UNKNOWN
            evidence_quality = EvaluationEvidenceQuality.UNKNOWN
            confidence = EvaluationConfidenceClass.LOW
            failure_modes.append(EvaluationFailureMode.UNKNOWN)
        else:
            outcome = EvaluationOutcome.INCONCLUSIVE
            verdict = EvaluationVerdict.INSUFFICIENT_EVIDENCE
            evidence_quality = EvaluationEvidenceQuality.UNKNOWN
            confidence = EvaluationConfidenceClass.LOW
            failure_modes.append(EvaluationFailureMode.UNKNOWN)
            warnings.append(f"UNKNOWN observation for criterion {crit.criterion_id!r}")

    # PRESENT or PARTIAL observation
    elif obs.status in (EvaluationObservationStatus.PRESENT, EvaluationObservationStatus.PARTIAL):
        has_evidence = bool(evidence_refs)
        has_other_refs = bool(obs.source_ref or obs.trace_refs or obs.context_refs)

        if has_evidence:
            evidence_quality = EvaluationEvidenceQuality.ADEQUATE
            if len(evidence_refs) >= 2:
                evidence_quality = EvaluationEvidenceQuality.STRONG
            outcome = EvaluationOutcome.PASSED
            verdict = EvaluationVerdict.SUPPORTED
            confidence = EvaluationConfidenceClass.MODERATE
            if evidence_quality == EvaluationEvidenceQuality.STRONG:
                confidence = EvaluationConfidenceClass.HIGH
        elif has_other_refs and not policy.require_evidence_for_supported:
            evidence_quality = EvaluationEvidenceQuality.WEAK
            outcome = EvaluationOutcome.PASSED
            verdict = EvaluationVerdict.SUPPORTED
            confidence = EvaluationConfidenceClass.LOW
        elif has_other_refs:
            evidence_quality = EvaluationEvidenceQuality.WEAK
            outcome = EvaluationOutcome.PARTIAL
            verdict = EvaluationVerdict.PARTIALLY_SUPPORTED
            confidence = EvaluationConfidenceClass.LOW
            warnings.append(f"no evidence refs for criterion {crit.criterion_id!r}, only source/trace/context refs")
        else:
            evidence_quality = EvaluationEvidenceQuality.WEAK
            outcome = EvaluationOutcome.PARTIAL
            verdict = EvaluationVerdict.PARTIALLY_SUPPORTED
            confidence = EvaluationConfidenceClass.LOW
            if required:
                warnings.append(f"PRESENT observation for criterion {crit.criterion_id!r} has no refs — evidence quality WEAK")

        if obs.status == EvaluationObservationStatus.PARTIAL:
            outcome = EvaluationOutcome.PARTIAL
            verdict = EvaluationVerdict.PARTIALLY_SUPPORTED
            warnings.append(f"PARTIAL observation for criterion {crit.criterion_id!r}")

    else:
        # Fallback — should not happen with closed-world enum
        outcome = EvaluationOutcome.INCONCLUSIVE
        verdict = EvaluationVerdict.UNKNOWN
        evidence_quality = EvaluationEvidenceQuality.UNKNOWN
        confidence = EvaluationConfidenceClass.LOW
        warnings.append(f"unexpected observation status for criterion {crit.criterion_id!r}")

    return CriterionClassificationDecision(
        criterion_id=crit.criterion_id,
        outcome=outcome,
        verdict=verdict,
        confidence=confidence,
        evidence_quality=evidence_quality,
        failure_modes=tuple(failure_modes),
        evidence_refs=evidence_refs,
        warnings=tuple(warnings),
        blockers=tuple(blockers_list),
        summary=(
            f"Criterion {crit.criterion_id!r}: {outcome.value}/{verdict.value} "
            f"(quality={evidence_quality.value}, confidence={confidence.value})"
        ),
    )


def criterion_decision_to_result(
    decision: CriterionClassificationDecision,
) -> EvaluationCriterionResult:
    return EvaluationCriterionResult(
        criterion_id=decision.criterion_id,
        outcome=decision.outcome,
        verdict=decision.verdict,
        evidence_quality=decision.evidence_quality,
        failure_modes=decision.failure_modes,
        summary=decision.summary,
        evidence_refs=decision.evidence_refs,
        warnings=decision.warnings,
        blockers=decision.blockers,
    )


# ---------------------------------------------------------------------------
# Result classification
# ---------------------------------------------------------------------------


def classify_result_from_criterion_decisions(
    *,
    run_id: str,
    result_id: str,
    decisions: tuple[CriterionClassificationDecision, ...],
    policy: ResultClassificationPolicy | None = None,
) -> ResultClassificationDecision:
    if policy is None:
        policy = build_default_result_classification_policy()

    all_warnings: list[str] = []
    all_blockers: list[str] = []
    all_failure_modes: list[EvaluationFailureMode] = []
    all_evidence_refs: set[str] = set()

    for d in decisions:
        all_warnings.extend(d.warnings)
        all_blockers.extend(d.blockers)
        all_failure_modes.extend(d.failure_modes)
        all_evidence_refs.update(d.evidence_refs)

    outcome: EvaluationOutcome
    verdict: EvaluationVerdict
    evidence_quality: EvaluationEvidenceQuality
    confidence: EvaluationConfidenceClass
    status: str

    if not decisions:
        outcome = EvaluationOutcome.INCONCLUSIVE
        verdict = EvaluationVerdict.INSUFFICIENT_EVIDENCE
        evidence_quality = EvaluationEvidenceQuality.NONE
        confidence = EvaluationConfidenceClass.NONE
        status = "INCONCLUSIVE_NO_DECISIONS"
        all_blockers.append("no criterion classification decisions present")

    else:
        outcomes = {d.outcome for d in decisions}
        verdicts = {d.verdict for d in decisions}
        qualities = {d.evidence_quality for d in decisions}

        # BLOCKED dominates
        if EvaluationOutcome.BLOCKED in outcomes or EvaluationVerdict.BLOCKED in verdicts:
            outcome = EvaluationOutcome.BLOCKED
            verdict = EvaluationVerdict.BLOCKED
            evidence_quality = EvaluationEvidenceQuality.NONE
            confidence = EvaluationConfidenceClass.NONE
            if all_blockers:
                status = "BLOCKED"
            else:
                status = "DEGRADED_BLOCKED"

        # CONFLICTED dominates
        elif EvaluationVerdict.CONFLICTED in verdicts or EvaluationEvidenceQuality.CONFLICTED in qualities:
            outcome = EvaluationOutcome.INCONCLUSIVE
            verdict = EvaluationVerdict.CONFLICTED
            evidence_quality = EvaluationEvidenceQuality.CONFLICTED
            confidence = EvaluationConfidenceClass.LOW
            status = "DEGRADED_CONFLICTED"

        # REQUIRED_CRITERION_FAILED
        elif EvaluationVerdict.REJECTED in verdicts:
            outcome = EvaluationOutcome.FAILED
            verdict = EvaluationVerdict.REJECTED
            evidence_quality = EvaluationEvidenceQuality.NONE
            confidence = EvaluationConfidenceClass.NONE
            status = "REJECTED"

        # INSUFFICIENT_EVIDENCE on any
        elif EvaluationVerdict.INSUFFICIENT_EVIDENCE in verdicts:
            outcome = EvaluationOutcome.INCONCLUSIVE
            verdict = EvaluationVerdict.INSUFFICIENT_EVIDENCE
            evidence_quality = EvaluationEvidenceQuality.WEAK
            confidence = EvaluationConfidenceClass.LOW
            status = "DEGRADED_INSUFFICIENT"

        # All SUPPORTED
        elif verdicts == {EvaluationVerdict.SUPPORTED}:
            outcome = EvaluationOutcome.PASSED
            verdict = EvaluationVerdict.SUPPORTED
            evidence_quality = EvaluationEvidenceQuality.ADEQUATE
            if EvaluationEvidenceQuality.STRONG in qualities:
                evidence_quality = EvaluationEvidenceQuality.STRONG
            confidence = EvaluationConfidenceClass.MODERATE
            if evidence_quality == EvaluationEvidenceQuality.STRONG:
                confidence = EvaluationConfidenceClass.HIGH
            status = "READY"

        # Mixed
        else:
            outcome = EvaluationOutcome.PARTIAL
            verdict = EvaluationVerdict.PARTIALLY_SUPPORTED
            evidence_quality = EvaluationEvidenceQuality.ADEQUATE
            if EvaluationEvidenceQuality.STRONG in qualities:
                evidence_quality = EvaluationEvidenceQuality.STRONG
            elif EvaluationEvidenceQuality.WEAK in qualities and EvaluationEvidenceQuality.CONFLICTED in qualities:
                evidence_quality = EvaluationEvidenceQuality.WEAK
            confidence = EvaluationConfidenceClass.MODERATE
            status = "DEGRADED_MIXED"

    return ResultClassificationDecision(
        run_id=run_id,
        status=status,
        outcome=outcome,
        verdict=verdict,
        confidence=confidence,
        evidence_quality=evidence_quality,
        criterion_decisions=decisions,
        failure_modes=tuple(all_failure_modes),
        evidence_refs=tuple(sorted(all_evidence_refs)),
        warnings=tuple(all_warnings),
        blockers=tuple(all_blockers),
        summary=(
            f"Result {result_id}: {outcome.value}/{verdict.value} "
            f"({len(decisions)} criteria, quality={evidence_quality.value})"
        ),
    )


def result_classification_to_evaluation_result(
    *,
    result_id: str,
    decision: ResultClassificationDecision,
) -> EvaluationResult:
    criterion_results = tuple(
        criterion_decision_to_result(d) for d in decision.criterion_decisions
    )

    result_status: EvaluationResultStatus
    if decision.blockers:
        result_status = EvaluationResultStatus.BLOCKED
    elif decision.verdict in (EvaluationVerdict.REJECTED, EvaluationVerdict.UNSUPPORTED):
        result_status = EvaluationResultStatus.ERROR
    elif decision.outcome == EvaluationOutcome.PASSED:
        result_status = EvaluationResultStatus.COMPLETED
    else:
        result_status = EvaluationResultStatus.COMPLETED

    return EvaluationResult(
        result_id=result_id,
        run_id=decision.run_id,
        status=result_status,
        outcome=decision.outcome,
        verdict=decision.verdict,
        confidence=decision.confidence,
        evidence_quality=decision.evidence_quality,
        criterion_results=criterion_results,
        failure_modes=decision.failure_modes,
        evidence_refs=decision.evidence_refs,
        warnings=decision.warnings,
        blockers=decision.blockers,
        summary=decision.summary,
    )


def classify_result_from_observations(
    *,
    result_id: str,
    classification_input: ResultClassificationInput,
    policy: ResultClassificationPolicy | None = None,
) -> ResultClassificationDecision:
    if policy is None:
        policy = build_default_result_classification_policy()

    run_envelope = classification_input.run_envelope
    criteria = run_envelope.criteria_resolution.criteria
    observations = classification_input.observations

    warnings: list[str] = list(classification_input.warnings)

    if not observations:
        return ResultClassificationDecision(
            run_id=run_envelope.run_id,
            status="INCONCLUSIVE_NO_OBSERVATIONS",
            outcome=EvaluationOutcome.INCONCLUSIVE,
            verdict=EvaluationVerdict.INSUFFICIENT_EVIDENCE,
            confidence=EvaluationConfidenceClass.NONE,
            evidence_quality=EvaluationEvidenceQuality.NONE,
            blockers=("no observations supplied",),
            summary="No observations supplied — cannot classify.",
        )

    if not criteria:
        return ResultClassificationDecision(
            run_id=run_envelope.run_id,
            status="INCONCLUSIVE_NO_CRITERIA",
            outcome=EvaluationOutcome.INCONCLUSIVE,
            verdict=EvaluationVerdict.INSUFFICIENT_EVIDENCE,
            confidence=EvaluationConfidenceClass.NONE,
            evidence_quality=EvaluationEvidenceQuality.NONE,
            blockers=("no criteria in run envelope",),
            summary="No criteria in run envelope — cannot classify.",
        )

    # Match observations to criteria conservatively
    # Simple approach: pair observations to criteria by order, wrapping if needed
    decisions: list[CriterionClassificationDecision] = []
    used_obs_indices: set[int] = set()

    for i, criterion in enumerate(criteria):
        required = criterion.requirement_level in (
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionRequirementLevel.BLOCKING,
        )
        blocking = criterion.requirement_level == EvaluationCriterionRequirementLevel.BLOCKING

        # Look for a matching observation
        matched_obs: EvaluationObservation | None = None

        for j, obs in enumerate(observations):
            if j in used_obs_indices:
                continue
            # Simple matching: check if source_ref or any refs mention criterion_id
            refs_text = " ".join(filter(None, [
                obs.source_ref or "",
                *obs.evidence_refs,
                *obs.trace_refs,
                *obs.context_refs,
            ]))
            if criterion.criterion_id in refs_text:
                matched_obs = obs
                used_obs_indices.add(j)
                break

        # If no specific match, use first unused observation
        if matched_obs is None:
            for j, obs in enumerate(observations):
                if j not in used_obs_indices:
                    matched_obs = obs
                    used_obs_indices.add(j)
                    if criterion.criterion_id not in (obs.source_ref or ""):
                        warnings.append(
                            f"observation {obs.observation_id!r} mapped to criterion "
                            f"{criterion.criterion_id!r} without explicit match"
                        )
                    break

        if matched_obs is None:
            # Create synthetic MISSING observation for this criterion
            matched_obs = EvaluationObservation(
                observation_id=f"obs_missing_{criterion.criterion_id}",
                observation_type=EvaluationObservationType.UNKNOWN,
                status=EvaluationObservationStatus.MISSING,
                summary=f"auto-generated missing observation for criterion {criterion.criterion_id!r}",
                blockers=("no observation available",),
            )

        cin = CriterionClassificationInput(
            run_id=run_envelope.run_id,
            criterion=criterion,
            observation=matched_obs,
            required=required,
            blocking=blocking,
            evidence_refs=run_envelope.evidence_refs + matched_obs.evidence_refs,
        )
        decisions.append(classify_criterion_observation(classification_input=cin, policy=policy))

    return classify_result_from_criterion_decisions(
        run_id=run_envelope.run_id,
        result_id=result_id,
        decisions=tuple(decisions),
        policy=policy,
    )


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def build_p156_result_classification_report(
    *,
    classifications_created: int = 0,
    criterion_decisions_created: int = 0,
    sparse_classification_ready: bool = False,
    warnings: tuple[str, ...] = (),
    blockers: tuple[str, ...] = (),
) -> ResultClassificationReport:
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "DEGRADED"
    else:
        status = "READY"

    ts = datetime.now(timezone.utc).isoformat()
    report_id = "p156_" + hashlib.sha256(ts.encode()).hexdigest()[:16]

    return ResultClassificationReport(
        report_id=report_id,
        status=status,
        summary=(
            f"P1.5.6 Result Classification Engine {status}. "
            f"Classifications: {classifications_created}, "
            f"Criterion decisions: {criterion_decisions_created}. "
            f"Sparse classification ready: {sparse_classification_ready}. "
            f"Next: P1.5.7."
        ),
        classifications_created=classifications_created,
        criterion_decisions_created=criterion_decisions_created,
        sparse_classification_ready=sparse_classification_ready,
        objects_added=(
            "EvaluationObservationType",
            "EvaluationObservationStatus",
            "EvaluationObservation",
            "CriterionClassificationInput",
            "CriterionClassificationDecision",
            "ResultClassificationInput",
            "ResultClassificationDecision",
            "ResultClassificationPolicy",
            "ResultClassificationReport",
        ),
        invariants=P156_INVARIANTS,
        warnings=warnings,
        blockers=blockers,
        next_module="P1.5.7 — Evidence-to-Claim Binding",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def evaluation_observation_to_dict(
    observation: EvaluationObservation,
) -> dict[str, object]:
    return {
        "observation_id": observation.observation_id,
        "observation_type": observation.observation_type.value,
        "status": observation.status.value,
        "source_ref": observation.source_ref,
        "evidence_refs": list(observation.evidence_refs),
        "trace_refs": list(observation.trace_refs),
        "context_refs": list(observation.context_refs),
        "summary": observation.summary,
        "notes": list(observation.notes),
        "warnings": list(observation.warnings),
        "blockers": list(observation.blockers),
    }


def criterion_classification_input_to_dict(
    inp: CriterionClassificationInput,
) -> dict[str, object]:
    return {
        "run_id": inp.run_id,
        "criterion": criteria_schema_item_to_dict(inp.criterion),
        "observation": evaluation_observation_to_dict(inp.observation),
        "required": inp.required,
        "blocking": inp.blocking,
        "evidence_refs": list(inp.evidence_refs),
        "warnings": list(inp.warnings),
        "blockers": list(inp.blockers),
    }


def criterion_classification_decision_to_dict(
    decision: CriterionClassificationDecision,
) -> dict[str, object]:
    return {
        "criterion_id": decision.criterion_id,
        "outcome": decision.outcome.value,
        "verdict": decision.verdict.value,
        "confidence": decision.confidence.value,
        "evidence_quality": decision.evidence_quality.value,
        "failure_modes": [fm.value for fm in decision.failure_modes],
        "evidence_refs": list(decision.evidence_refs),
        "warnings": list(decision.warnings),
        "blockers": list(decision.blockers),
        "summary": decision.summary,
    }


def result_classification_input_to_dict(
    inp: ResultClassificationInput,
) -> dict[str, object]:
    return {
        "run_envelope": governed_evaluation_run_envelope_to_dict(inp.run_envelope),
        "observations": [evaluation_observation_to_dict(o) for o in inp.observations],
        "warnings": list(inp.warnings),
        "blockers": list(inp.blockers),
    }


def result_classification_decision_to_dict(
    decision: ResultClassificationDecision,
) -> dict[str, object]:
    return {
        "run_id": decision.run_id,
        "status": decision.status,
        "outcome": decision.outcome.value,
        "verdict": decision.verdict.value,
        "confidence": decision.confidence.value,
        "evidence_quality": decision.evidence_quality.value,
        "criterion_decisions": [criterion_classification_decision_to_dict(d) for d in decision.criterion_decisions],
        "failure_modes": [fm.value for fm in decision.failure_modes],
        "evidence_refs": list(decision.evidence_refs),
        "warnings": list(decision.warnings),
        "blockers": list(decision.blockers),
        "summary": decision.summary,
    }


def result_classification_policy_to_dict(
    policy: ResultClassificationPolicy,
) -> dict[str, object]:
    return {
        "policy_id": policy.policy_id,
        "require_evidence_for_supported": policy.require_evidence_for_supported,
        "block_on_conflicted_evidence": policy.block_on_conflicted_evidence,
        "block_on_missing_required_evidence": policy.block_on_missing_required_evidence,
        "allow_unknown_observation_to_pass": policy.allow_unknown_observation_to_pass,
        "warnings": list(policy.warnings),
        "blockers": list(policy.blockers),
    }


def result_classification_report_to_dict(
    report: ResultClassificationReport,
) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "status": report.status,
        "summary": report.summary,
        "classifications_created": report.classifications_created,
        "criterion_decisions_created": report.criterion_decisions_created,
        "sparse_classification_ready": report.sparse_classification_ready,
        "objects_added": list(report.objects_added),
        "invariants": list(report.invariants),
        "warnings": list(report.warnings),
        "blockers": list(report.blockers),
        "next_module": report.next_module,
    }


# ---------------------------------------------------------------------------
# Example helpers
# ---------------------------------------------------------------------------


def example_observation() -> EvaluationObservation:
    return EvaluationObservation(
        observation_id="obs_example_001",
        observation_type=EvaluationObservationType.STATIC_REVIEW,
        status=EvaluationObservationStatus.PRESENT,
        source_ref="ref_static_001",
        evidence_refs=("ref_ev_001", "ref_ev_002"),
        summary="Example static review observation with evidence.",
    )


def example_sparse_observation() -> EvaluationObservation:
    return EvaluationObservation(
        observation_id="obs_sparse_example",
        observation_type=EvaluationObservationType.SPARSE_CONTEXT_OBSERVATION,
        status=EvaluationObservationStatus.PRESENT,
        source_ref="ds_sparse_context_quality",
        evidence_refs=("ref_sc_evidence_001",),
        trace_refs=("trace_sc_001",),
        context_refs=("ctx_sc_001",),
        summary="Example sparse context quality observation. Sparse Context Compiler NOT implemented.",
    )


__all__ = [
    "EvaluationObservationType",
    "EvaluationObservationStatus",
    "EvaluationObservation",
    "CriterionClassificationInput",
    "CriterionClassificationDecision",
    "ResultClassificationInput",
    "ResultClassificationDecision",
    "ResultClassificationPolicy",
    "ResultClassificationReport",
    "P156_INVARIANTS",
    "validate_evaluation_observation",
    "build_default_result_classification_policy",
    "classify_criterion_observation",
    "criterion_decision_to_result",
    "classify_result_from_criterion_decisions",
    "result_classification_to_evaluation_result",
    "classify_result_from_observations",
    "build_p156_result_classification_report",
    "evaluation_observation_to_dict",
    "criterion_classification_input_to_dict",
    "criterion_classification_decision_to_dict",
    "result_classification_input_to_dict",
    "result_classification_decision_to_dict",
    "result_classification_policy_to_dict",
    "result_classification_report_to_dict",
    "example_observation",
    "example_sparse_observation",
]

"""P1.5.5 run envelope validation tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
    EvaluationCriteriaSchemaItem,
    EvaluationCriteriaSchemaRegistry,
    EvaluationCriteriaSchemaResolution,
    EvaluationCriterionApplicability,
    build_default_criteria_schema_for_subject_type,
    resolve_criteria_for_subject,
)
from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    build_evaluation_subject,
)
from agentic_runtime.evaluation.evaluation_objects import EvaluationFailureMode
from agentic_runtime.evaluation.evaluation_run_envelope import (
    EvaluationEvaluatorType,
    EvaluationRunEvidenceRequirement,
    EvaluationRunIntent,
    EvaluationRunMode,
    EvaluationRunStatus,
    GovernedEvaluationRunEnvelope,
    build_governed_evaluation_run_envelope,
    validate_governed_evaluation_run_envelope,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectOrigin,
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
)


def _make_item(requirement_level, evidence_req, criterion_id="crit_test", kind=None):
    return EvaluationCriteriaSchemaItem(
        criterion_id=criterion_id,
        kind=kind or EvaluationCriterionKind.GROUNDEDNESS,
        name="Test",
        description="t",
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=requirement_level,
        evidence_requirement=evidence_req,
        applicable_failure_modes=(EvaluationFailureMode.NONE,),
        applicability=EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        ),
    )


def _make_entry(subject_id="subj_test", status=EvaluationSubjectStatus.REGISTERED):
    subject = build_evaluation_subject(
        subject_id=subject_id,
        subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        domain=EvaluationDomain.AUREL_CORE,
    )
    return EvaluationSubjectRegistryEntry(
        entry_id="entry_" + subject_id,
        subject=subject,
        status=status,
        origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
    )


def _make_resolution(criteria=(), blockers=()):
    return EvaluationCriteriaSchemaResolution(
        subject_id="subj_test",
        schema_ids=("schema_001",),
        criteria=criteria,
        required_criteria=tuple(c.criterion_id for c in criteria if c.requirement_level in (EvaluationCriterionRequirementLevel.REQUIRED, EvaluationCriterionRequirementLevel.BLOCKING)),
        blocking_criteria=tuple(c.criterion_id for c in criteria if c.requirement_level == EvaluationCriterionRequirementLevel.BLOCKING),
        blockers=blockers,
    )


class TestValidateEnvelope:
    def test_validate_rejects_empty_run_id(self):
        entry = _make_entry()
        item = _make_item(EvaluationCriterionRequirementLevel.OPTIONAL, EvaluationCriterionEvidenceRequirement.NONE)
        resolution = _make_resolution(criteria=(item,))
        envelope = GovernedEvaluationRunEnvelope(
            run_id="", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False
        assert any("run_id" in b for b in v.blockers)

    def test_validate_rejects_unknown_intent(self):
        entry = _make_entry()
        item = _make_item(EvaluationCriterionRequirementLevel.OPTIONAL, EvaluationCriterionEvidenceRequirement.NONE)
        resolution = _make_resolution(criteria=(item,))
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_001", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.UNKNOWN, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_rejects_unknown_mode(self):
        entry = _make_entry()
        item = _make_item(EvaluationCriterionRequirementLevel.OPTIONAL, EvaluationCriterionEvidenceRequirement.NONE)
        resolution = _make_resolution(criteria=(item,))
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_002", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.UNKNOWN,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_rejects_unknown_evaluator(self):
        entry = _make_entry()
        item = _make_item(EvaluationCriterionRequirementLevel.OPTIONAL, EvaluationCriterionEvidenceRequirement.NONE)
        resolution = _make_resolution(criteria=(item,))
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_003", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.UNKNOWN,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_blocks_invalid_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.INVALID)
        resolution = _make_resolution()
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_004", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_blocks_rejected_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.REJECTED)
        resolution = _make_resolution()
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_005", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_blocks_suspended_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.SUSPENDED)
        resolution = _make_resolution()
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_006", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_blocks_no_criteria(self):
        entry = _make_entry()
        resolution = _make_resolution(criteria=())
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_007", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_validate_blocks_unsatisfied_required_evidence(self):
        entry = _make_entry()
        item = _make_item(EvaluationCriterionRequirementLevel.REQUIRED, EvaluationCriterionEvidenceRequirement.EVIDENCE_REF)
        resolution = _make_resolution(criteria=(item,))
        # Evidence requirement REQUIRED but not satisfied
        ev_req = EvaluationRunEvidenceRequirement(
            requirement_id="ev_req_crit_test",
            evidence_requirement=EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
            required=True,
            satisfied=False,
            evidence_refs=(),
            missing_reason="no evidence",
        )
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_008", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.CAPABILITY_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_requirements=(ev_req,),
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

    def test_ready_envelope_cannot_have_blockers(self):
        entry = _make_entry()
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        registry = EvaluationCriteriaSchemaRegistry(registry_id="r2", schemas=(schema,))
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)

        envelope = build_governed_evaluation_run_envelope(
            run_id="run_valid",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.status == EvaluationRunStatus.READY
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is True

    def test_sparse_context_check_without_sparse_blocks(self):
        entry = _make_entry()
        item = _make_item(EvaluationCriterionRequirementLevel.OPTIONAL, EvaluationCriterionEvidenceRequirement.NONE)
        resolution = _make_resolution(criteria=(item,))
        envelope = GovernedEvaluationRunEnvelope(
            run_id="run_sparse_fail", status=EvaluationRunStatus.DRAFT,
            intent=EvaluationRunIntent.SPARSE_CONTEXT_CHECK, mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry, criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            sparse_context_required=False,
        )
        v = validate_governed_evaluation_run_envelope(envelope)
        assert v.valid is False

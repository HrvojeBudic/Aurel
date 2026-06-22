"""P1.5.5 core run envelope tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
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
    build_evidence_requirements_from_criteria,
    build_governed_evaluation_run_envelope,
)
from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchemaItem,
    EvaluationCriteriaSchemaRegistry,
    EvaluationCriteriaSchemaResolution,
    EvaluationCriterionApplicability,
    build_default_criteria_schema_for_subject_type,
    resolve_criteria_for_subject,
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
        name="Test criterion",
        description="test",
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
        required_criteria=(c.criterion_id for c in criteria if c.requirement_level in (EvaluationCriterionRequirementLevel.REQUIRED, EvaluationCriterionRequirementLevel.BLOCKING)),
        blocking_criteria=(c.criterion_id for c in criteria if c.requirement_level == EvaluationCriterionRequirementLevel.BLOCKING),
        blockers=blockers,
    )


class TestEnums:
    def test_run_status_closed_world(self):
        assert EvaluationRunStatus("DRAFT") == EvaluationRunStatus.DRAFT
        assert EvaluationRunStatus("READY") == EvaluationRunStatus.READY
        assert EvaluationRunStatus("BLOCKED") == EvaluationRunStatus.BLOCKED
        assert EvaluationRunStatus("INVALID") == EvaluationRunStatus.INVALID

    def test_run_intent_closed_world(self):
        assert EvaluationRunIntent("CAPABILITY_CHECK") == EvaluationRunIntent.CAPABILITY_CHECK
        assert EvaluationRunIntent("SPARSE_CONTEXT_CHECK") == EvaluationRunIntent.SPARSE_CONTEXT_CHECK
        assert EvaluationRunIntent("UNKNOWN") == EvaluationRunIntent.UNKNOWN

    def test_run_mode_closed_world(self):
        assert EvaluationRunMode("DRY_RUN") == EvaluationRunMode.DRY_RUN
        assert EvaluationRunMode("LLM_JUDGE_PLANNED") == EvaluationRunMode.LLM_JUDGE_PLANNED

    def test_evaluator_type_closed_world(self):
        assert EvaluationEvaluatorType("DETERMINISTIC") == EvaluationEvaluatorType.DETERMINISTIC
        assert EvaluationEvaluatorType("LLM_JUDGE") == EvaluationEvaluatorType.LLM_JUDGE


class TestEvidenceRequirements:
    def test_build_evidence_requirements_from_criteria(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria)
        assert len(reqs) == 1

    def test_required_criteria_create_required_evidence_requirements(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria)
        assert reqs[0].required is True

    def test_blocking_criteria_create_required_evidence_requirements(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.BLOCKING,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria)
        assert reqs[0].required is True

    def test_optional_criteria_create_not_required(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.OPTIONAL,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria)
        assert reqs[0].required is False

    def test_none_evidence_skipped(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.NONE,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria)
        assert len(reqs) == 0

    def test_evidence_refs_satisfy_requirements(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria, evidence_refs=("ref_001",))
        assert reqs[0].satisfied is True

    def test_no_evidence_refs_unsatisfies_required(self):
        criteria = (_make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        ),)
        reqs = build_evidence_requirements_from_criteria(criteria)
        assert reqs[0].satisfied is False
        assert reqs[0].missing_reason is not None


class TestBuildEnvelope:
    def test_build_ready_envelope(self):
        entry = _make_entry()
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        registry = EvaluationCriteriaSchemaRegistry(registry_id="r", schemas=(schema,))
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)

        envelope = build_governed_evaluation_run_envelope(
            run_id="run_test_001",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.run_id == "run_test_001"
        assert envelope.status == EvaluationRunStatus.READY
        assert len(envelope.blockers) == 0
        assert len(envelope.evidence_requirements) > 0

    def test_invalid_subject_status_blocks(self):
        entry = _make_entry(status=EvaluationSubjectStatus.REJECTED)
        resolution = _make_resolution()
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_blocked",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.status == EvaluationRunStatus.BLOCKED
        assert len(envelope.blockers) > 0

    def test_no_criteria_blocks(self):
        entry = _make_entry()
        resolution = _make_resolution(criteria=())
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_no_crit",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=(),
        )
        assert envelope.status == EvaluationRunStatus.BLOCKED

    def test_unknown_evaluator_blocks(self):
        entry = _make_entry()
        item = _make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        )
        resolution = _make_resolution(criteria=(item,))
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_unk_eval",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.UNKNOWN,
            evidence_refs=("ref_001",),
        )
        assert envelope.status == EvaluationRunStatus.BLOCKED

    def test_unsatisfied_required_evidence_blocks(self):
        entry = _make_entry()
        item = _make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        )
        resolution = _make_resolution(criteria=(item,))
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_no_ev",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=(),  # no evidence refs
        )
        assert envelope.status == EvaluationRunStatus.BLOCKED

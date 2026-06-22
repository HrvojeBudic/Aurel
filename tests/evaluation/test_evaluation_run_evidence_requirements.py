"""P1.5.5 evidence requirement derivation tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
    EvaluationCriteriaSchemaItem,
    EvaluationCriterionApplicability,
)
from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
)
from agentic_runtime.evaluation.evaluation_objects import EvaluationFailureMode
from agentic_runtime.evaluation.evaluation_run_envelope import (
    build_evidence_requirements_from_criteria,
    build_governed_evaluation_run_envelope,
    EvaluationEvaluatorType,
    EvaluationRunIntent,
    EvaluationRunMode,
    EvaluationRunStatus,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectOrigin,
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
)
from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchemaResolution,
)
from agentic_runtime.evaluation.evaluation_foundation import build_evaluation_subject


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


class TestEvidenceDerivation:
    def test_retrieval_trace_evidence_sets_retrieval_required(self):
        entry = _make_entry()
        item = _make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.RETRIEVAL_TRACE,
        )
        resolution = EvaluationCriteriaSchemaResolution(
            subject_id="subj_test",
            schema_ids=("s",),
            criteria=(item,),
            required_criteria=("crit_test",),
            blocking_criteria=(),
        )
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_rt",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.retrieval_trace_required is True

    def test_context_trace_evidence_sets_context_trace_required(self):
        entry = _make_entry()
        item = _make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE,
        )
        resolution = EvaluationCriteriaSchemaResolution(
            subject_id="subj_test",
            schema_ids=("s",),
            criteria=(item,),
            required_criteria=("crit_test",),
            blocking_criteria=(),
        )
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_ct",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.context_trace_required is True

    def test_evidence_graph_sets_evidence_graph_required(self):
        entry = _make_entry()
        item = _make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.EVIDENCE_GRAPH,
        )
        resolution = EvaluationCriteriaSchemaResolution(
            subject_id="subj_test",
            schema_ids=("s",),
            criteria=(item,),
            required_criteria=("crit_test",),
            blocking_criteria=(),
        )
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_eg",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.evidence_graph_required is True

    def test_lost_context_risk_criterion_sets_lost_context_required(self):
        entry = _make_entry()
        item = _make_item(
            EvaluationCriterionRequirementLevel.REQUIRED,
            EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE,
            kind=EvaluationCriterionKind.LOST_CONTEXT_RISK,
        )
        resolution = EvaluationCriteriaSchemaResolution(
            subject_id="subj_test",
            schema_ids=("s",),
            criteria=(item,),
            required_criteria=("crit_test",),
            blocking_criteria=(),
        )
        envelope = build_governed_evaluation_run_envelope(
            run_id="run_lcr",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_001",),
        )
        assert envelope.lost_context_risk_required is True

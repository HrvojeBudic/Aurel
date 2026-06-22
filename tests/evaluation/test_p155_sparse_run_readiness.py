"""P1.5.5 sparse run readiness tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchemaRegistry,
    EvaluationCriterionKind,
    build_default_sparse_criteria_schema,
    resolve_criteria_for_subject,
)
from agentic_runtime.evaluation.evaluation_run_envelope import (
    EvaluationEvaluatorType,
    EvaluationRunIntent,
    EvaluationRunMode,
    EvaluationRunStatus,
    build_governed_evaluation_run_envelope,
    example_sparse_ready_run_envelope,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    example_registered_sparse_context_subject,
)


class TestSparseRunReadiness:
    def test_sparse_context_check_sets_sparse_required(self):
        entry = example_registered_sparse_context_subject()
        schema = build_default_sparse_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(registry_id="r", schemas=(schema,))
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)

        envelope = build_governed_evaluation_run_envelope(
            run_id="run_sc_check",
            intent=EvaluationRunIntent.SPARSE_CONTEXT_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_sc",),
        )
        assert envelope.sparse_context_required is True

    def test_sparse_criterion_sets_sparse_required(self):
        entry = example_registered_sparse_context_subject()
        schema = build_default_sparse_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(registry_id="r2", schemas=(schema,))
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)

        envelope = build_governed_evaluation_run_envelope(
            run_id="run_sc_crit",
            intent=EvaluationRunIntent.CAPABILITY_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_sc",),
        )
        # SPARSE_CONTEXT_QUALITY criterion should set sparse_context_required
        assert envelope.sparse_context_required is True

    def test_sparse_run_envelope_does_not_run_sparse_compiler(self):
        envelope = example_sparse_ready_run_envelope()
        assert envelope.status == EvaluationRunStatus.READY
        # Envelope is metadata only — no execution
        assert not hasattr(envelope, 'execute')
        assert not hasattr(envelope, 'run')

    def test_sparse_run_envelope_does_not_claim_ssa_implemented(self):
        envelope = example_sparse_ready_run_envelope()
        combined = envelope.summary.lower()
        if "ssa" in combined:
            assert "not" in combined

    def test_sparse_run_envelope_does_not_claim_subquadratic_model_implemented(self):
        envelope = example_sparse_ready_run_envelope()
        combined = envelope.summary.lower()
        if "subquadratic" in combined:
            assert "not" in combined

    def test_sparse_run_has_retrieval_context_trace_requirements(self):
        entry = example_registered_sparse_context_subject()
        schema = build_default_sparse_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(registry_id="r3", schemas=(schema,))
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)

        envelope = build_governed_evaluation_run_envelope(
            run_id="run_sc_traces",
            intent=EvaluationRunIntent.SPARSE_CONTEXT_CHECK,
            mode=EvaluationRunMode.STATIC_REVIEW,
            subject_entry=entry,
            criteria_resolution=resolution,
            evaluator_type=EvaluationEvaluatorType.DETERMINISTIC,
            evidence_refs=("ref_sc",),
        )
        assert envelope.retrieval_trace_required is True
        assert envelope.context_trace_required is True
        assert envelope.evidence_graph_required is True
        assert envelope.lost_context_risk_required is True

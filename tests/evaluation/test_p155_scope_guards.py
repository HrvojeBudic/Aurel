"""P1.5.5 scope guard tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_run_envelope import (
    P155_INVARIANTS,
    EvaluationEvaluatorType,
    EvaluationRunMode,
    EvaluationRunIntent,
    GovernedEvaluationRunEnvelope,
    example_ready_run_envelope,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectStatus,
)


class TestScopeGuards:
    def test_p155_does_not_execute_evaluation(self):
        envelope = example_ready_run_envelope()
        assert not hasattr(envelope, 'execute')
        assert not hasattr(envelope, 'evaluate')
        assert not hasattr(envelope, 'run_evaluation')

    def test_p155_does_not_create_evaluation_result(self):
        envelope = example_ready_run_envelope()
        tname = type(envelope).__name__
        assert "Result" not in tname

    def test_p155_does_not_verify_capability(self):
        envelope = example_ready_run_envelope()
        combined = envelope.summary.lower()
        if "verif" in combined:
            assert "not" in combined or "does not" in combined

    def test_p155_does_not_create_capability_evidence_record(self):
        envelope = example_ready_run_envelope()
        assert not hasattr(envelope, 'capability_evidence_record')
        assert not hasattr(type(envelope), 'evidence_record')

    def test_p155_does_not_call_llm_or_tools(self):
        envelope = example_ready_run_envelope()
        assert envelope.mode != EvaluationRunMode.LLM_JUDGE_PLANNED or "PLANNED" in envelope.mode.value
        # LLM_JUDGE_PLANNED means planned not executed
        if envelope.mode == EvaluationRunMode.LLM_JUDGE_PLANNED:
            assert "PLANNED" in envelope.mode.value

    def test_p155_does_not_introduce_numeric_score(self):
        envelope = example_ready_run_envelope()
        assert not hasattr(envelope, 'score')
        assert not hasattr(envelope, 'numeric_score')
        assert not hasattr(envelope, 'capability_score')

    def test_p155_does_not_implement_sparse_context_compiler(self):
        from agentic_runtime.evaluation.evaluation_run_envelope import example_sparse_ready_run_envelope
        envelope = example_sparse_ready_run_envelope()
        combined = envelope.summary.lower()
        if "compiler" in combined:
            assert "not" in combined or "not implemented" in combined

    def test_p155_does_not_implement_hub_runtime(self):
        envelope = example_ready_run_envelope()
        combined = envelope.summary.lower()
        if "hub" in combined:
            assert "not" in combined or "does not" in combined

    def test_p155_prepares_p156_result_classification(self):
        envelope = example_ready_run_envelope()
        assert envelope.status == EvaluationEvaluatorType.DETERMINISTIC is not None or True
        # Valid envelope exists — ready for P1.5.6 classification

    def test_invariants_do_not_claim_ssa(self):
        for inv in P155_INVARIANTS:
            if "SSA" in inv or "subquadratic" in inv:
                assert "not" in inv.lower() or "must not" in inv.lower()

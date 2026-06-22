"""P1.5.4 scope guard tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    build_evaluation_subject,
)
from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchema,
    EvaluationCriteriaSchemaItem,
    EvaluationCriterionApplicability,
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
    P154_INVARIANTS,
    build_default_criteria_schema_for_subject_type,
    build_default_sparse_criteria_schema,
    validate_evaluation_criteria_schema,
)
from agentic_runtime.evaluation.evaluation_objects import EvaluationFailureMode


class TestScopeGuards:
    def test_p154_does_not_run_evaluation(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        # The schema is read-only; it does not produce an EvaluationResult
        assert not hasattr(schema, 'run')
        assert not hasattr(schema, 'evaluate')

    def test_p154_does_not_create_evaluation_result(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        # Schema type is not an evaluation result
        tname = type(schema).__name__
        assert "Result" not in tname
        assert "Schema" in tname

    def test_p154_does_not_verify_capability(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        combined = (schema.summary + " " + " ".join(c.description for c in schema.criteria)).lower()
        if "verif" in combined:
            assert "does not" in combined or "not verify" in combined

    def test_p154_does_not_introduce_numeric_score(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        # No score fields on schema items
        for item in schema.criteria:
            assert not hasattr(item, 'score')
            assert not hasattr(item, 'numeric_score')
            assert not hasattr(item, 'capability_score')

    def test_p154_does_not_implement_sparse_context_compiler(self):
        sparse_schema = build_default_sparse_criteria_schema()
        combined = sparse_schema.summary.lower()
        if "compiler" in combined:
            assert "not implemented" in combined

    def test_p154_does_not_implement_hub_runtime(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        combined = (schema.summary + " " + " ".join(c.description for c in schema.criteria)).lower()
        if "hub" in combined:
            assert "not implement" in combined or "does not" in combined

    def test_p154_prepares_p155_run_envelope(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        # Schema exists and is valid — ready for P1.5.5 run envelope
        issues = validate_evaluation_criteria_schema(schema)
        assert len(issues) == 0

    def test_invariants_do_not_claim_ssa(self):
        for inv in P154_INVARIANTS:
            if "SSA" in inv or "subquadratic" in inv:
                assert "not" in inv.lower() or "must not" in inv.lower()

    def test_invariants_do_not_claim_compiler_implemented(self):
        for inv in P154_INVARIANTS:
            if "compiler" in inv.lower():
                assert "not" in inv.lower() or "implement" not in inv.lower()

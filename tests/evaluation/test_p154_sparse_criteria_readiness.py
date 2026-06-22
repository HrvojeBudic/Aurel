"""P1.5.4 sparse criteria readiness tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    _SPARSE_CRITERION_KINDS,
    build_default_sparse_criteria_schema,
    validate_criteria_schema_item,
    validate_evaluation_criteria_schema,
)


class TestSparseCriteriaExistence:
    def test_sparse_context_quality_criterion_exists(self):
        schema = build_default_sparse_criteria_schema()
        kinds = {c.kind for c in schema.criteria}
        assert EvaluationCriterionKind.SPARSE_CONTEXT_QUALITY in kinds

    def test_evidence_recall_criterion_exists(self):
        schema = build_default_sparse_criteria_schema()
        kinds = {c.kind for c in schema.criteria}
        assert EvaluationCriterionKind.EVIDENCE_RECALL in kinds

    def test_context_budget_efficiency_criterion_exists(self):
        schema = build_default_sparse_criteria_schema()
        kinds = {c.kind for c in schema.criteria}
        assert EvaluationCriterionKind.CONTEXT_BUDGET_EFFICIENCY in kinds

    def test_lost_context_risk_criterion_exists(self):
        schema = build_default_sparse_criteria_schema()
        kinds = {c.kind for c in schema.criteria}
        assert EvaluationCriterionKind.LOST_CONTEXT_RISK in kinds

    def test_governed_context_selection_criterion_exists(self):
        schema = build_default_sparse_criteria_schema()
        kinds = {c.kind for c in schema.criteria}
        assert EvaluationCriterionKind.GOVERNED_CONTEXT_SELECTION in kinds

    def test_authority_aware_retrieval_criterion_exists(self):
        schema = build_default_sparse_criteria_schema()
        kinds = {c.kind for c in schema.criteria}
        assert EvaluationCriterionKind.AUTHORITY_AWARE_RETRIEVAL in kinds


class TestSparseCriteriaNonClaims:
    def test_sparse_criteria_do_not_claim_compiler_implemented(self):
        schema = build_default_sparse_criteria_schema()
        for item in schema.criteria:
            combined = " ".join((
                item.description,
                " ".join(item.non_goals),
                " ".join(item.limitations),
            )).lower()
            if "compiler" in combined:
                assert "not implemented" in combined or "does not" in combined

    def test_sparse_criteria_do_not_claim_ssa_implemented(self):
        schema = build_default_sparse_criteria_schema()
        for item in schema.criteria:
            combined = " ".join((
                item.description,
                " ".join(item.non_goals),
                " ".join(item.limitations),
            )).lower()
            if "ssa" in combined:
                assert "not implemented" in combined or "does not" in combined

    def test_sparse_criteria_do_not_claim_subquadratic_model_implemented(self):
        schema = build_default_sparse_criteria_schema()
        for item in schema.criteria:
            combined = " ".join((
                item.description,
                " ".join(item.non_goals),
                " ".join(item.limitations),
            )).lower()
            if "subquadratic" in combined:
                assert "not implemented" in combined or "does not" in combined

    def test_sparse_criteria_require_context_or_retrieval_trace(self):
        schema = build_default_sparse_criteria_schema()
        sparse_kinds = set(_SPARSE_CRITERION_KINDS)
        for item in schema.criteria:
            if item.kind in sparse_kinds:
                # At minimum, sparse criteria should have more than NONE evidence
                assert item.evidence_requirement != EvaluationCriterionEvidenceRequirement.NONE or item.limitations


class TestSparseCounts:
    def test_sparse_criterion_kinds_count(self):
        assert len(_SPARSE_CRITERION_KINDS) >= 8

    def test_sparse_schema_is_valid(self):
        schema = build_default_sparse_criteria_schema()
        issues = validate_evaluation_criteria_schema(schema)
        assert len(issues) == 0

    def test_sparse_schema_criteria_count(self):
        schema = build_default_sparse_criteria_schema()
        assert len(schema.criteria) >= 6

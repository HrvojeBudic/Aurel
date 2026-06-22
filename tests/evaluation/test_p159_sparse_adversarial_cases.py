"""P1.5.9 sparse adversarial readiness and default case set tests."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialCaseType,
    build_default_adversarial_case_set,
    validate_adversarial_case,
)


def _case_types() -> set[AdversarialCaseType]:
    return {c.case_type for c in build_default_adversarial_case_set()}


class TestDefaultCaseSet:
    def test_default_case_set_contains_negative_control(self):
        assert AdversarialCaseType.NEGATIVE_CONTROL in _case_types()

    def test_default_case_set_contains_contradiction_trap(self):
        assert AdversarialCaseType.CONTRADICTION_TRAP in _case_types()

    def test_default_case_set_contains_missing_evidence_trap(self):
        assert AdversarialCaseType.MISSING_EVIDENCE_TRAP in _case_types()

    def test_default_case_set_contains_stale_evidence_trap(self):
        assert AdversarialCaseType.STALE_EVIDENCE_TRAP in _case_types()

    def test_default_case_set_contains_authority_inversion_trap(self):
        assert AdversarialCaseType.AUTHORITY_INVERSION_TRAP in _case_types()

    def test_default_case_set_contains_prompt_injection_trap(self):
        assert AdversarialCaseType.PROMPT_INJECTION_TRAP in _case_types()

    def test_default_case_set_contains_policy_bypass_trap(self):
        assert AdversarialCaseType.POLICY_BYPASS_TRAP in _case_types()

    def test_default_case_set_contains_claim_overgeneralization_trap(self):
        assert AdversarialCaseType.CLAIM_OVERGENERALIZATION_TRAP in _case_types()

    def test_default_case_set_contains_benchmark_leakage_trap(self):
        assert AdversarialCaseType.BENCHMARK_LEAKAGE_TRAP in _case_types()

    def test_default_case_set_contains_sparse_context_omission_trap(self):
        assert AdversarialCaseType.SPARSE_CONTEXT_OMISSION_TRAP in _case_types()

    def test_default_case_set_contains_lost_context_trap(self):
        assert AdversarialCaseType.LOST_CONTEXT_TRAP in _case_types()

    def test_default_case_set_contains_multi_hop_trace_trap(self):
        assert AdversarialCaseType.MULTI_HOP_TRACE_TRAP in _case_types()

    def test_default_case_set_contains_needle_in_context_trap(self):
        assert AdversarialCaseType.NEEDLE_IN_CONTEXT_TRAP in _case_types()

    def test_default_cases_are_schema_only(self):
        for case in build_default_adversarial_case_set():
            validation = validate_adversarial_case(case)
            assert validation.valid, validation.blockers
            assert any("schema" in lim.lower() for lim in case.limitations)
            assert "without execution" in case.summary.lower() or "not executed" in " ".join(case.limitations).lower()


class TestSparseReadiness:
    def test_sparse_adversarial_cases_do_not_run_sparse_compiler(self):
        src = inspect.getsource(build_default_adversarial_case_set)
        assert "SparseContextCompiler" not in src
        assert "run_sparse" not in src.lower()

    def test_sparse_adversarial_cases_do_not_claim_ssa_implemented(self):
        for case in build_default_adversarial_case_set():
            if case.sparse_context_required:
                combined = " ".join(case.limitations + (case.summary,)).lower()
                assert "ssa" not in combined or "not implemented" in combined

    def test_sparse_adversarial_cases_do_not_claim_subquadratic_model_implemented(self):
        src = inspect.getsource(build_default_adversarial_case_set)
        assert "subquadratic" not in src.lower()

    def test_context_budget_pressure_case_is_schema_only(self):
        case = next(
            c for c in build_default_adversarial_case_set()
            if c.case_type == AdversarialCaseType.CONTEXT_BUDGET_PRESSURE_TRAP
        )
        assert case.sparse_context_required is True
        assert validate_adversarial_case(case).valid

    def test_needle_in_context_case_is_schema_only(self):
        case = next(
            c for c in build_default_adversarial_case_set()
            if c.case_type == AdversarialCaseType.NEEDLE_IN_CONTEXT_TRAP
        )
        assert case.sparse_context_required is True
        assert validate_adversarial_case(case).valid

    def test_lost_context_case_is_schema_only(self):
        case = next(
            c for c in build_default_adversarial_case_set()
            if c.case_type == AdversarialCaseType.LOST_CONTEXT_TRAP
        )
        assert case.sparse_context_required is True
        assert validate_adversarial_case(case).valid

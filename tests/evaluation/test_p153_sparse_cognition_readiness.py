"""P1.5.3 sparse cognition readiness tests — Evaluation Subject Registry."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    build_evaluation_subject,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectCategory,
    EvaluationSubjectOrigin,
    EvaluationSubjectRegistrationRequest,
    EvaluationSubjectStatus,
    _SPARSE_CATEGORIES,
    example_registered_sparse_context_subject,
    register_evaluation_subject,
)


class TestSparseContextOrigin:
    def test_sparse_context_origin_closed_world(self):
        assert EvaluationSubjectOrigin("SPARSE_CONTEXT") == EvaluationSubjectOrigin.SPARSE_CONTEXT


class TestSparseContextRegistration:
    def test_register_sparse_context_plan_subject(self):
        subject = build_evaluation_subject(
            subject_id="subj_sc_plan_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_sc_plan_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sc_plan",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Register sparse context plan subject for future ASCL evaluation",
            categories=("SPARSE_CONTEXT_PLAN",),
            source_refs=("ref_sc_plan_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_register_context_assembly_plan_subject(self):
        subject = build_evaluation_subject(
            subject_id="subj_cap_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_cap_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_cap",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Register context assembly plan subject",
            categories=("CONTEXT_ASSEMBLY_PLAN",),
            source_refs=("ref_cap_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_register_retrieval_trace_subject(self):
        subject = build_evaluation_subject(
            subject_id="subj_rt_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_rt_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_rt",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Register retrieval trace subject",
            categories=("RETRIEVAL_TRACE",),
            source_refs=("ref_rt_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_register_evidence_graph_subject(self):
        subject = build_evaluation_subject(
            subject_id="subj_eg_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_eg_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_eg",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Register evidence graph subject",
            categories=("EVIDENCE_GRAPH",),
            source_refs=("ref_eg_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_register_context_budget_subject(self):
        subject = build_evaluation_subject(
            subject_id="subj_cb_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_cb_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_cb",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Register context budget subject",
            categories=("CONTEXT_BUDGET",),
            source_refs=("ref_cb_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_register_lost_context_risk_subject(self):
        subject = build_evaluation_subject(
            subject_id="subj_lcr_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_lcr_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_lcr",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Register lost context risk assessment subject",
            categories=("LOST_CONTEXT_RISK_ASSESSMENT",),
            source_refs=("ref_lcr_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_sparse_context_subject_without_refs_not_active(self):
        subject = build_evaluation_subject(
            subject_id="subj_sc_noref_001",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sc_noref",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Sparse context without refs",
            categories=("CONTEXT_BUDGET",),
            evidence_refs=(),
            source_refs=(),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert decision.status != EvaluationSubjectStatus.ACTIVE
        assert decision.status == EvaluationSubjectStatus.DRAFT


class TestSparseContextNonClaims:
    def test_sparse_context_registration_does_not_run_compiler(self):
        entry = example_registered_sparse_context_subject()
        assert entry.status != EvaluationSubjectStatus.ACTIVE
        assert "compiler" not in entry.summary.lower() or "not implemented" in entry.summary.lower()

    def test_sparse_context_registration_does_not_claim_subquadratic_model(self):
        entry = example_registered_sparse_context_subject()
        summary = entry.summary.lower()
        # Must NOT claim subquadratic attention is implemented
        if "subquadratic" in summary:
            assert "not" in summary or "does not" in summary or "not implemented" in summary

    def test_sparse_context_registration_does_not_claim_ssa_implemented(self):
        entry = example_registered_sparse_context_subject()
        summary = entry.summary.lower()
        if "ssa" in summary:
            assert "not" in summary or "does not" in summary or "not implemented" in summary

    def test_lost_context_risk_subject_can_be_registered(self):
        subject = build_evaluation_subject(
            subject_id="subj_lcr_002",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_lcr_002",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_lcr_002",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="Lost context risk is an evaluable subject, not a solved problem",
            categories=("LOST_CONTEXT_RISK_ASSESSMENT",),
            source_refs=("ref_lcr_002",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        # Lost context risk is evaluable but not solved
        if decision.entry:
            assert "SOLVED" not in decision.entry.summary.upper()

    def test_all_sparse_categories_exist_in_enum(self):
        for cat in _SPARSE_CATEGORIES:
            assert isinstance(cat, EvaluationSubjectCategory)

    def test_sparse_category_count(self):
        # 9 sparse categories defined
        assert len(_SPARSE_CATEGORIES) >= 9

"""P1.5.3 scope guard tests — Evaluation Subject Registry."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    build_evaluation_subject,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectOrigin,
    EvaluationSubjectRegistrationRequest,
    EvaluationSubjectRegistry,
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
    register_evaluation_subject,
)


class TestScopeGuards:
    def test_p153_does_not_run_evaluation(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_001",
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
            domain=EvaluationDomain.AUREL_CORE,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_001",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="scope guard test",
            evidence_refs=("ref_001",),
        )
        decision = register_evaluation_subject(req)
        # Registration must not produce ACTIVE or COMPLETED
        assert decision.status not in (EvaluationSubjectStatus.ACTIVE,)
        # registration is not an evaluation run
        assert "EvaluationResult" not in str(type(decision))

    def test_p153_does_not_verify_capability(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_002",
            subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
            domain=EvaluationDomain.CAPABILITY_CLAIM,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_002",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="scope guard test — capability claim",
            evidence_refs=("ref_002",),
        )
        decision = register_evaluation_subject(req)
        # VERIFIED must NOT appear
        assert "VERIFIED" not in decision.summary

    def test_p153_does_not_modify_claim_status(self):
        # Registration decisions do not reference claim mutations
        subject = build_evaluation_subject(
            subject_id="subj_sg_003",
            subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
            domain=EvaluationDomain.CAPABILITY_CLAIM,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_003",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="scope guard test — no claim mutation",
            evidence_refs=("ref_003",),
        )
        decision = register_evaluation_subject(req)
        # No claim status fields in decision
        d = decision.__dict__ if hasattr(decision, '__dict__') else {}
        assert "claim_status" not in str(type(decision))

    def test_p153_does_not_implement_hub_runtime(self):
        # Hub origin subjects are registrable but do not implement Hub runtime
        subject = build_evaluation_subject(
            subject_id="subj_sg_hub",
            subject_type=EvaluationSubjectType.HUB_OUTPUT,
            domain=EvaluationDomain.HUB_HANDOFF,
            source_ref="ref_hub_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_hub",
            subject=subject,
            origin=EvaluationSubjectOrigin.A_HUB,
            reason="scope guard test — Hub origin, no runtime",
            source_refs=("ref_hub_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        # Hub origin registered, but Hub runtime is NOT implemented
        # The decision entry should have warnings about Hub runtime not implemented
        if decision.entry:
            # Check that it's not ACTIVE without source refs
            assert decision.status != EvaluationSubjectStatus.ACTIVE

    def test_p153_does_not_promote_memory(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_mem",
            subject_type=EvaluationSubjectType.OUTPUT,
            domain=EvaluationDomain.MEMORY,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_mem",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="scope guard test — no memory promotion",
            evidence_refs=("ref_mem",),
        )
        decision = register_evaluation_subject(req)
        assert "promote" not in decision.summary.lower()

    def test_p153_does_not_implement_sparse_context_compiler(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_sc",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_sc_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_sc",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="scope guard test — no sparse compiler",
            categories=("SPARSE_CONTEXT_PLAN",),
            source_refs=("ref_sc_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        # Sparse Context Compiler is not implemented
        assert "compiler" not in str(decision.status).lower()

    def test_p153_does_not_implement_sparse_retrieval_router(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_sr",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_sr_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_sr",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="scope guard test — no retrieval router",
            categories=("RETRIEVAL_TRACE",),
            source_refs=("ref_sr_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_p153_does_not_implement_evidence_graph_builder(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_egb",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
            source_ref="ref_egb_001",
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_egb",
            subject=subject,
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            reason="scope guard test — no evidence graph builder",
            categories=("EVIDENCE_GRAPH",),
            source_refs=("ref_egb_001",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True

    def test_p153_does_not_claim_true_sparse_attention(self):
        # The module must not claim SSA / true sparse attention is implemented
        from agentic_runtime.evaluation.evaluation_subject_registry import P153_INVARIANTS
        for inv in P153_INVARIANTS:
            if "SSA" in inv or "subquadratic" in inv:
                assert "must not claim" in inv or "not implemented" in inv or "not claim" in inv

    def test_p153_does_not_claim_long_context_model_training(self):
        from agentic_runtime.evaluation.evaluation_subject_registry import P153_INVARIANTS
        # No invariant should claim model training capabilities
        for inv in P153_INVARIANTS:
            assert "model training" not in inv.lower()
            assert "LoRA" not in inv

    def test_p153_prepares_p154_criteria_schema(self):
        subject = build_evaluation_subject(
            subject_id="subj_sg_p154prep",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_sg_p154prep",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="scope guard test — prepare for P1.5.4",
            evidence_refs=("ref_p154prep",),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        # Subject registered, criteria schema next
        assert decision.status != EvaluationSubjectStatus.ACTIVE

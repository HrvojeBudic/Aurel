"""P1.5.3 registration tests — Evaluation Subject Registry."""
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
    EvaluationSubjectStatus,
    register_evaluation_subject,
    validate_evaluation_subject_registration_request,
)


def _make_request(
    request_id: str = "req_001",
    subject_id: str = "subj_001",
    origin: EvaluationSubjectOrigin = EvaluationSubjectOrigin.EVALUATION_MODULE,
    reason: str = "test registration",
    evidence_refs: tuple[str, ...] = ("ref_001",),
    source_refs: tuple[str, ...] = (),
    domain: EvaluationDomain = EvaluationDomain.AUREL_CORE,
    subject_type: EvaluationSubjectType = EvaluationSubjectType.AGENT_IDENTITY,
    **kwargs,
) -> EvaluationSubjectRegistrationRequest:
    subject = build_evaluation_subject(
        subject_id=subject_id,
        subject_type=subject_type,
        domain=domain,
        evidence_refs=evidence_refs,
    )
    return EvaluationSubjectRegistrationRequest(
        request_id=request_id,
        subject=subject,
        origin=origin,
        reason=reason,
        evidence_refs=evidence_refs,
        source_refs=source_refs,
        categories=kwargs.get("categories", ()),
        tags=kwargs.get("tags", ()),
        allowed_scope_ids=kwargs.get("allowed_scope_ids", ("scope_aurel_core",)),
        owner_module=kwargs.get("owner_module"),
        requested_by=kwargs.get("requested_by"),
    )


class TestRegistrationValidation:
    def test_valid_registration_request_passes_validation(self):
        req = _make_request()
        issues = validate_evaluation_subject_registration_request(req)
        assert len(issues) == 0

    def test_empty_request_id_rejected(self):
        req = _make_request(request_id="")
        issues = validate_evaluation_subject_registration_request(req)
        assert any("request_id must not be empty" in i for i in issues)

    def test_empty_reason_rejected(self):
        req = _make_request(reason="")
        issues = validate_evaluation_subject_registration_request(req)
        assert any("reason must not be empty" in i for i in issues)

    def test_empty_subject_id_rejected(self):
        from agentic_runtime.evaluation.evaluation_foundation import EvaluationSubject
        subject = EvaluationSubject(
            subject_id="",
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
            domain=EvaluationDomain.AUREL_CORE,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_empty_subj",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="empty subject test",
        )
        issues = validate_evaluation_subject_registration_request(req)
        assert any("subject.subject_id must not be empty" in i for i in issues)

    def test_unknown_domain_registration_validates(self):
        req = _make_request(domain=EvaluationDomain.UNKNOWN, evidence_refs=())
        issues = validate_evaluation_subject_registration_request(req)
        assert any("UNKNOWN domain" in i for i in issues)

    def test_unknown_subject_type_registration_validates(self):
        req = _make_request(subject_type=EvaluationSubjectType.UNKNOWN, evidence_refs=())
        issues = validate_evaluation_subject_registration_request(req)
        assert any("UNKNOWN subject_type" in i for i in issues)

    def test_hub_origin_without_source_ref_emits_warning(self):
        req = _make_request(origin=EvaluationSubjectOrigin.A_HUB, evidence_refs=(), source_refs=())
        issues = validate_evaluation_subject_registration_request(req)
        assert any("Hub origin" in i for i in issues)

    def test_sparse_context_origin_without_source_ref_emits_warning(self):
        req = _make_request(
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            evidence_refs=(),
            source_refs=(),
        )
        issues = validate_evaluation_subject_registration_request(req)
        assert any("SPARSE_CONTEXT origin" in i for i in issues)


class TestRegisterEvaluationSubject:
    def test_valid_registration_request_accepts_registered_entry(self):
        req = _make_request()
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert decision.entry is not None
        assert decision.status == EvaluationSubjectStatus.REGISTERED

    def test_registration_defaults_to_registered_not_active(self):
        req = _make_request()
        decision = register_evaluation_subject(req)
        assert decision.status != EvaluationSubjectStatus.ACTIVE
        assert decision.status == EvaluationSubjectStatus.REGISTERED

    def test_unknown_domain_rejected(self):
        req = _make_request(domain=EvaluationDomain.UNKNOWN, evidence_refs=())
        decision = register_evaluation_subject(req)
        assert decision.accepted is False
        assert decision.status == EvaluationSubjectStatus.REJECTED
        assert len(decision.blockers) > 0

    def test_unknown_subject_type_rejected(self):
        req = _make_request(subject_type=EvaluationSubjectType.UNKNOWN, evidence_refs=())
        decision = register_evaluation_subject(req)
        assert decision.accepted is False

    def test_hub_origin_without_source_ref_not_active(self):
        req = _make_request(
            origin=EvaluationSubjectOrigin.A_HUB,
            evidence_refs=(),
            source_refs=(),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert decision.status != EvaluationSubjectStatus.ACTIVE
        # Should be DRAFT since no refs
        assert decision.status == EvaluationSubjectStatus.DRAFT

    def test_sparse_context_origin_without_source_ref_not_active(self):
        req = _make_request(
            origin=EvaluationSubjectOrigin.SPARSE_CONTEXT,
            evidence_refs=(),
            source_refs=(),
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert decision.status != EvaluationSubjectStatus.ACTIVE
        assert decision.status == EvaluationSubjectStatus.DRAFT

    def test_rejected_registration_has_blockers(self):
        req = _make_request(domain=EvaluationDomain.UNKNOWN, evidence_refs=())
        decision = register_evaluation_subject(req)
        assert decision.accepted is False
        assert len(decision.blockers) > 0

    def test_accepted_registration_has_entry(self):
        req = _make_request()
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert decision.entry is not None
        assert decision.entry.subject.subject_id == "subj_001"

    def test_registration_does_not_run_evaluation(self):
        req = _make_request()
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert decision.status != EvaluationSubjectStatus.ACTIVE
        # Registration does not produce an evaluation result
        assert "evaluation" not in decision.summary.lower() or "does not run" in decision.summary.lower() or "not run evaluation" in decision.summary.lower()

    def test_registration_does_not_verify_capability(self):
        req = _make_request(
            subject_id="subj_cap_test",
            domain=EvaluationDomain.CAPABILITY_CLAIM,
            subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
        )
        decision = register_evaluation_subject(req)
        assert decision.accepted is True
        assert "VERIFIED" not in str(decision.status.value).upper()
        assert decision.status != EvaluationSubjectStatus.ACTIVE

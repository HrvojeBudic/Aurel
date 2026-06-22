"""P1.5.3 core object tests — Evaluation Subject Registry."""
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
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
    validate_evaluation_subject_registry_entry,
)


def _make_entry(
    entry_id: str = "entry_001",
    subject_id: str = "subj_001",
    status: EvaluationSubjectStatus = EvaluationSubjectStatus.REGISTERED,
    origin: EvaluationSubjectOrigin = EvaluationSubjectOrigin.EVALUATION_MODULE,
    allowed_scope_ids: tuple[str, ...] = ("scope_aurel_core",),
    evidence_refs: tuple[str, ...] = ("ref_001",),
    blockers: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
    summary: str = "test entry",
    **kwargs,
) -> EvaluationSubjectRegistryEntry:
    subject = build_evaluation_subject(
        subject_id=subject_id,
        subject_type=kwargs.get("subject_type", EvaluationSubjectType.AGENT_IDENTITY),
        domain=kwargs.get("domain", EvaluationDomain.AUREL_CORE),
        evidence_refs=evidence_refs,
    )
    return EvaluationSubjectRegistryEntry(
        entry_id=entry_id,
        subject=subject,
        status=status,
        origin=origin,
        allowed_scope_ids=allowed_scope_ids,
        evidence_refs=evidence_refs,
        blockers=blockers,
        warnings=warnings,
        limitations=limitations,
        summary=summary,
        categories=kwargs.get("categories", ()),
    )


class TestEvaluationSubjectStatus:
    def test_evaluation_subject_status_closed_world(self):
        assert EvaluationSubjectStatus("DRAFT") == EvaluationSubjectStatus.DRAFT
        assert EvaluationSubjectStatus("REGISTERED") == EvaluationSubjectStatus.REGISTERED
        assert EvaluationSubjectStatus("ACTIVE") == EvaluationSubjectStatus.ACTIVE
        assert EvaluationSubjectStatus("SUSPENDED") == EvaluationSubjectStatus.SUSPENDED
        assert EvaluationSubjectStatus("DEPRECATED") == EvaluationSubjectStatus.DEPRECATED
        assert EvaluationSubjectStatus("REJECTED") == EvaluationSubjectStatus.REJECTED
        assert EvaluationSubjectStatus("INVALID") == EvaluationSubjectStatus.INVALID
        assert EvaluationSubjectStatus("UNKNOWN") == EvaluationSubjectStatus.UNKNOWN


class TestEvaluationSubjectOrigin:
    def test_evaluation_subject_origin_closed_world(self):
        assert EvaluationSubjectOrigin("AUREL_CORE") == EvaluationSubjectOrigin.AUREL_CORE
        assert EvaluationSubjectOrigin("SPARSE_CONTEXT") == EvaluationSubjectOrigin.SPARSE_CONTEXT
        assert EvaluationSubjectOrigin("A_HUB") == EvaluationSubjectOrigin.A_HUB
        assert EvaluationSubjectOrigin("S_HUB") == EvaluationSubjectOrigin.S_HUB
        assert EvaluationSubjectOrigin("L_HUB") == EvaluationSubjectOrigin.L_HUB
        assert EvaluationSubjectOrigin("IDE") == EvaluationSubjectOrigin.IDE
        assert EvaluationSubjectOrigin("UNKNOWN") == EvaluationSubjectOrigin.UNKNOWN


class TestEvaluationSubjectCategory:
    def test_evaluation_subject_category_closed_world(self):
        assert EvaluationSubjectCategory("STANDARD") == EvaluationSubjectCategory.STANDARD
        assert EvaluationSubjectCategory("SPARSE_CONTEXT_PLAN") == EvaluationSubjectCategory.SPARSE_CONTEXT_PLAN
        assert EvaluationSubjectCategory("CONTEXT_BUDGET") == EvaluationSubjectCategory.CONTEXT_BUDGET
        assert EvaluationSubjectCategory("LOST_CONTEXT_RISK_ASSESSMENT") == EvaluationSubjectCategory.LOST_CONTEXT_RISK_ASSESSMENT


class TestBuildRegistryEntry:
    def test_build_registry_entry(self):
        entry = _make_entry()
        assert entry.entry_id == "entry_001"
        assert entry.subject.subject_id == "subj_001"
        assert entry.status == EvaluationSubjectStatus.REGISTERED

    def test_validate_entry_rejects_empty_entry_id(self):
        entry = _make_entry(entry_id="")
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("entry_id must not be empty" in i for i in issues)

    def test_validate_entry_rejects_empty_subject_id(self):
        from agentic_runtime.evaluation.evaluation_foundation import EvaluationSubject
        subject = EvaluationSubject(
            subject_id="",
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
            domain=EvaluationDomain.AUREL_CORE,
        )
        entry = EvaluationSubjectRegistryEntry(
            entry_id="entry_001",
            subject=subject,
            status=EvaluationSubjectStatus.REGISTERED,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
        )
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("subject.subject_id must not be empty" in i for i in issues)

    def test_active_entry_requires_allowed_scope_or_reason(self):
        entry = _make_entry(status=EvaluationSubjectStatus.ACTIVE, allowed_scope_ids=(), summary="")
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("ACTIVE status requires" in i for i in issues)

    def test_active_entry_with_allowed_scope_valid(self):
        entry = _make_entry(status=EvaluationSubjectStatus.ACTIVE, allowed_scope_ids=("scope_aurel_core",))
        issues = validate_evaluation_subject_registry_entry(entry)
        assert not any("ACTIVE status requires" in i for i in issues)

    def test_rejected_entry_requires_blocker(self):
        entry = _make_entry(status=EvaluationSubjectStatus.REJECTED, blockers=())
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("REJECTED status requires" in i for i in issues)

    def test_invalid_entry_requires_blocker(self):
        entry = _make_entry(status=EvaluationSubjectStatus.INVALID, blockers=())
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("INVALID status requires" in i for i in issues)

    def test_unknown_origin_requires_warning_or_blocker(self):
        entry = _make_entry(origin=EvaluationSubjectOrigin.UNKNOWN, warnings=(), blockers=())
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("UNKNOWN origin requires" in i for i in issues)

    def test_unknown_status_requires_warning_or_blocker(self):
        entry = _make_entry(status=EvaluationSubjectStatus.UNKNOWN, warnings=(), blockers=())
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("UNKNOWN status requires" in i for i in issues)

    def test_active_cannot_have_unknown_domain(self):
        entry = _make_entry(
            status=EvaluationSubjectStatus.ACTIVE,
            domain=EvaluationDomain.UNKNOWN,
        )
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("ACTIVE subject cannot have UNKNOWN domain" in i for i in issues)

    def test_active_cannot_have_unknown_subject_type(self):
        entry = _make_entry(
            status=EvaluationSubjectStatus.ACTIVE,
            subject_type=EvaluationSubjectType.UNKNOWN,
        )
        issues = validate_evaluation_subject_registry_entry(entry)
        assert any("ACTIVE subject cannot have UNKNOWN subject_type" in i for i in issues)

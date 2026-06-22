"""P1.5.3 serialization and link tests — Evaluation Subject Registry."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    build_evaluation_subject,
)
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectCategory,
    EvaluationSubjectOrigin,
    EvaluationSubjectRegistrationDecision,
    EvaluationSubjectRegistrationRequest,
    EvaluationSubjectRegistry,
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectRegistryReport,
    EvaluationSubjectStatus,
    build_p153_subject_registry_report,
    evaluation_subject_registration_decision_to_dict,
    evaluation_subject_registration_request_to_dict,
    evaluation_subject_registry_entry_to_dict,
    evaluation_subject_registry_report_to_dict,
    evaluation_subject_registry_to_dict,
    example_registered_core_subject,
    example_subject_registry,
    list_evaluation_subjects,
    register_evaluation_subject,
    resolve_evaluation_subject,
    validate_evaluation_subject_registry,
)


class TestSerialization:
    def test_registry_entry_json_serializable(self):
        entry = example_registered_core_subject()
        d = evaluation_subject_registry_entry_to_dict(entry)
        s = json.dumps(d)
        assert "entry_example_core" in s
        assert "REGISTERED" in s
        assert "AUREL_CORE" in s

    def test_registration_request_json_serializable(self):
        subject = build_evaluation_subject(
            subject_id="subj_ser_001",
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
            domain=EvaluationDomain.AUREL_CORE,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_ser_001",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="serialization test",
            categories=("STANDARD",),
        )
        d = evaluation_subject_registration_request_to_dict(req)
        s = json.dumps(d)
        assert "req_ser_001" in s
        assert "standarD" in s.lower() or "STANDARD" in s

    def test_registration_decision_json_serializable(self):
        subject = build_evaluation_subject(
            subject_id="subj_dec_001",
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
            domain=EvaluationDomain.AUREL_CORE,
        )
        req = EvaluationSubjectRegistrationRequest(
            request_id="req_dec_001",
            subject=subject,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
            reason="decision serialization test",
            evidence_refs=("ref_001",),
        )
        decision = register_evaluation_subject(req)
        d = evaluation_subject_registration_decision_to_dict(decision)
        s = json.dumps(d)
        assert "req_dec_001" in s
        assert "true" in s.lower() or d["accepted"] is True

    def test_registry_json_serializable(self):
        registry = example_subject_registry()
        d = evaluation_subject_registry_to_dict(registry)
        s = json.dumps(d)
        assert "registry_p153_example" in s
        assert len(d["entries"]) == 2

    def test_registry_with_sparse_context_subject_json_serializable(self):
        registry = example_subject_registry()
        d = evaluation_subject_registry_to_dict(registry)
        s = json.dumps(d)
        assert "CONTEXT_BUDGET" in s
        assert "SPARSE_CONTEXT" in s
        assert "SSA" in s or "sparse" in s.lower()

    def test_registry_report_json_serializable(self):
        report = build_p153_subject_registry_report(entries_registered=5, entries_rejected=2)
        d = evaluation_subject_registry_report_to_dict(report)
        s = json.dumps(d)
        assert "p153_" in s
        assert "REGISTERABLE_SUBJECTS_ONLY" in s
        assert "P1.5.4" in s


class TestResolveAndList:
    def test_resolve_existing_subject(self):
        registry = example_subject_registry()
        entry = resolve_evaluation_subject(registry, "subj_aurel_core_governance")
        assert entry is not None
        assert entry.subject.subject_id == "subj_aurel_core_governance"

    def test_resolve_unknown_subject_returns_none(self):
        registry = example_subject_registry()
        entry = resolve_evaluation_subject(registry, "nonexistent")
        assert entry is None

    def test_resolve_empty_subject_id_returns_none(self):
        registry = example_subject_registry()
        assert resolve_evaluation_subject(registry, "") is None

    def test_list_subjects_by_domain(self):
        registry = example_subject_registry()
        results = list_evaluation_subjects(registry, domain=EvaluationDomain.AUREL_CORE)
        assert len(results) >= 1
        assert all(e.subject.domain == EvaluationDomain.AUREL_CORE for e in results)

    def test_list_subjects_by_status(self):
        registry = example_subject_registry()
        results = list_evaluation_subjects(registry, status=EvaluationSubjectStatus.REGISTERED)
        assert len(results) >= 1
        assert all(e.status == EvaluationSubjectStatus.REGISTERED for e in results)

    def test_list_subjects_by_origin(self):
        registry = example_subject_registry()
        results = list_evaluation_subjects(
            registry, origin=EvaluationSubjectOrigin.SPARSE_CONTEXT
        )
        assert len(results) >= 1
        assert all(e.origin == EvaluationSubjectOrigin.SPARSE_CONTEXT for e in results)

    def test_list_subjects_by_category(self):
        registry = example_subject_registry()
        results = list_evaluation_subjects(
            registry, category=EvaluationSubjectCategory.CONTEXT_BUDGET
        )
        assert len(results) >= 1
        assert all(EvaluationSubjectCategory.CONTEXT_BUDGET in e.categories for e in results)

    def test_list_subjects_by_type(self):
        registry = example_subject_registry()
        results = list_evaluation_subjects(
            registry, subject_type=EvaluationSubjectType.AGENT_IDENTITY
        )
        assert len(results) >= 1
        assert all(e.subject.subject_type == EvaluationSubjectType.AGENT_IDENTITY for e in results)


class TestRegistryValidation:
    def test_validate_registry_rejects_duplicate_entry_ids(self):
        from agentic_runtime.evaluation.evaluation_subject_registry import (
            example_registered_core_subject,
        )
        entry = example_registered_core_subject()
        # Create two entries with same entry_id but different subjects
        subject2 = build_evaluation_subject(
            subject_id="subj_002",
            subject_type=EvaluationSubjectType.PROCEDURE,
            domain=EvaluationDomain.AUREL_CORE,
        )
        entry2 = EvaluationSubjectRegistryEntry(
            entry_id=entry.entry_id,  # same entry_id
            subject=subject2,
            status=EvaluationSubjectStatus.REGISTERED,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
        )
        registry = EvaluationSubjectRegistry(
            registry_id="test_dup_entry",
            entries=(entry, entry2),
        )
        issues = validate_evaluation_subject_registry(registry)
        assert any("duplicate entry_id" in i for i in issues)

    def test_validate_registry_rejects_duplicate_subject_ids(self):
        from agentic_runtime.evaluation.evaluation_subject_registry import (
            example_registered_core_subject,
        )
        entry = example_registered_core_subject()
        # Create another entry with same subject_id
        entry2 = EvaluationSubjectRegistryEntry(
            entry_id="entry_diff_002",
            subject=entry.subject,  # same subject
            status=EvaluationSubjectStatus.REGISTERED,
            origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
        )
        registry = EvaluationSubjectRegistry(
            registry_id="test_dup_subj",
            entries=(entry, entry2),
        )
        issues = validate_evaluation_subject_registry(registry)
        assert any("duplicate subject_id" in i for i in issues)

    def test_valid_registry_passes_validation(self):
        registry = example_subject_registry()
        issues = validate_evaluation_subject_registry(registry)
        assert len(issues) == 0

    def test_validate_registry_rejects_empty_registry_id(self):
        registry = EvaluationSubjectRegistry(registry_id="", entries=())
        issues = validate_evaluation_subject_registry(registry)
        assert any("registry_id must not be empty" in i for i in issues)

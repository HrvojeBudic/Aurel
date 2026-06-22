"""P1.5.4 criteria resolution tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
    build_evaluation_subject,
)
from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchemaItem,
    EvaluationCriteriaSchemaRegistry,
    EvaluationCriterionApplicability,
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
    build_default_criteria_schema_for_subject_type,
    resolve_criteria_for_subject,
)
from agentic_runtime.evaluation.evaluation_objects import EvaluationFailureMode
from agentic_runtime.evaluation.evaluation_subject_registry import (
    EvaluationSubjectOrigin,
    EvaluationSubjectRegistryEntry,
    EvaluationSubjectStatus,
)


def _make_entry(
    subject_id: str = "subj_001",
    status: EvaluationSubjectStatus = EvaluationSubjectStatus.REGISTERED,
    domain: EvaluationDomain = EvaluationDomain.AUREL_CORE,
    subject_type: EvaluationSubjectType = EvaluationSubjectType.AGENT_IDENTITY,
) -> EvaluationSubjectRegistryEntry:
    subject = build_evaluation_subject(
        subject_id=subject_id,
        subject_type=subject_type,
        domain=domain,
    )
    return EvaluationSubjectRegistryEntry(
        entry_id="entry_" + subject_id,
        subject=subject,
        status=status,
        origin=EvaluationSubjectOrigin.EVALUATION_MODULE,
    )


def _make_registry(
    *schemas,
    registry_id: str = "reg_001",
) -> EvaluationCriteriaSchemaRegistry:
    return EvaluationCriteriaSchemaRegistry(
        registry_id=registry_id,
        schemas=schemas,
    )


class TestResolveCriteria:
    def test_resolve_criteria_for_registered_subject(self):
        entry = _make_entry()
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        registry = _make_registry(schema)
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.blockers) == 0
        assert len(resolution.criteria) >= 4
        assert len(resolution.required_criteria) > 0
        assert len(resolution.blocking_criteria) > 0

    def test_resolve_criteria_for_active_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.ACTIVE)
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        registry = _make_registry(schema)
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.blockers) == 0

    def test_resolve_criteria_blocks_rejected_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.REJECTED)
        registry = _make_registry()
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.blockers) > 0

    def test_resolve_criteria_blocks_invalid_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.INVALID)
        registry = _make_registry()
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.blockers) > 0

    def test_resolve_criteria_blocks_suspended_subject(self):
        entry = _make_entry(status=EvaluationSubjectStatus.SUSPENDED)
        registry = _make_registry()
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.blockers) > 0

    def test_resolve_criteria_blocks_no_matching_schema(self):
        entry = _make_entry(
            domain=EvaluationDomain.CAPABILITY_CLAIM,
            subject_type=EvaluationSubjectType.CAPABILITY_CLAIM,
        )
        registry = _make_registry()
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.blockers) > 0
        assert "no criteria schema found" in resolution.blockers[0]

    def test_resolve_criteria_filters_by_domain(self):
        entry = _make_entry()
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        # Also add a schema for a different domain
        other_schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUTONOMY,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        registry = _make_registry(schema, other_schema)
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        # Only the Aurel Core schema matches the entry's domain
        assert len(resolution.schema_ids) == 1
        assert len(resolution.criteria) > 0

    def test_resolve_criteria_filters_by_subject_type(self):
        entry = _make_entry()
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        other_schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.PROCEDURE,
        )
        registry = _make_registry(schema, other_schema)
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.schema_ids) == 1
        assert resolution.schema_ids[0] == schema.schema_id

    def test_resolution_lists_required_and_blocking_criteria(self):
        entry = _make_entry()
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        registry = _make_registry(schema)
        resolution = resolve_criteria_for_subject(subject_entry=entry, registry=registry)
        assert len(resolution.required_criteria) > 0
        assert len(resolution.blocking_criteria) > 0
        # All blocking criteria are also in required
        assert set(resolution.blocking_criteria).issubset(set(resolution.required_criteria))

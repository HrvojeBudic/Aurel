"""P1.5.4 core criteria schema tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
)
from agentic_runtime.evaluation.evaluation_objects import EvaluationFailureMode
from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchema,
    EvaluationCriteriaSchemaItem,
    EvaluationCriterionApplicability,
    EvaluationCriterionEvidenceRequirement,
    EvaluationCriterionKind,
    EvaluationCriterionRequirementLevel,
    EvaluationCriterionSeverity,
    build_default_criteria_schema_for_subject_type,
    validate_criteria_schema_item,
    validate_criterion_applicability,
    validate_evaluation_criteria_schema,
)


def _make_item(
    criterion_id: str = "crit_001",
    kind: EvaluationCriterionKind = EvaluationCriterionKind.GROUNDEDNESS,
    name: str = "Test criterion",
    requirement_level: EvaluationCriterionRequirementLevel = EvaluationCriterionRequirementLevel.REQUIRED,
    evidence_requirement: EvaluationCriterionEvidenceRequirement = EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
    domain: EvaluationDomain = EvaluationDomain.AUREL_CORE,
    subject_type: EvaluationSubjectType = EvaluationSubjectType.AGENT_IDENTITY,
    limitations: tuple[str, ...] = (),
    non_goals: tuple[str, ...] = (),
    description: str = "test",
) -> EvaluationCriteriaSchemaItem:
    return EvaluationCriteriaSchemaItem(
        criterion_id=criterion_id,
        kind=kind,
        name=name,
        description=description,
        severity=EvaluationCriterionSeverity.HIGH,
        requirement_level=requirement_level,
        evidence_requirement=evidence_requirement,
        applicable_failure_modes=(EvaluationFailureMode.NONE,),
        applicability=EvaluationCriterionApplicability(
            domain=domain,
            subject_type=subject_type,
        ),
        limitations=limitations,
        non_goals=non_goals,
    )


def _make_schema(
    schema_id: str = "schema_001",
    name: str = "Test Schema",
    domain: EvaluationDomain = EvaluationDomain.AUREL_CORE,
    subject_type: EvaluationSubjectType = EvaluationSubjectType.AGENT_IDENTITY,
    criteria: tuple[EvaluationCriteriaSchemaItem, ...] | None = None,
) -> EvaluationCriteriaSchema:
    if criteria is None:
        criteria = (_make_item(),)
    return EvaluationCriteriaSchema(
        schema_id=schema_id,
        name=name,
        description="test schema",
        domain=domain,
        subject_type=subject_type,
        criteria=criteria,
    )


class TestEnums:
    def test_criterion_kind_closed_world(self):
        assert EvaluationCriterionKind("CORRECTNESS") == EvaluationCriterionKind.CORRECTNESS
        assert EvaluationCriterionKind("GROUNDEDNESS") == EvaluationCriterionKind.GROUNDEDNESS
        assert EvaluationCriterionKind("SPARSE_CONTEXT_QUALITY") == EvaluationCriterionKind.SPARSE_CONTEXT_QUALITY
        assert EvaluationCriterionKind("EVIDENCE_RECALL") == EvaluationCriterionKind.EVIDENCE_RECALL
        assert EvaluationCriterionKind("LOST_CONTEXT_RISK") == EvaluationCriterionKind.LOST_CONTEXT_RISK
        assert EvaluationCriterionKind("UNKNOWN") == EvaluationCriterionKind.UNKNOWN

    def test_criterion_severity_closed_world(self):
        assert EvaluationCriterionSeverity("INFO") == EvaluationCriterionSeverity.INFO
        assert EvaluationCriterionSeverity("CRITICAL") == EvaluationCriterionSeverity.CRITICAL

    def test_requirement_level_closed_world(self):
        assert EvaluationCriterionRequirementLevel("OPTIONAL") == EvaluationCriterionRequirementLevel.OPTIONAL
        assert EvaluationCriterionRequirementLevel("BLOCKING") == EvaluationCriterionRequirementLevel.BLOCKING

    def test_evidence_requirement_closed_world(self):
        assert EvaluationCriterionEvidenceRequirement("NONE") == EvaluationCriterionEvidenceRequirement.NONE
        assert EvaluationCriterionEvidenceRequirement("CONTEXT_TRACE") == EvaluationCriterionEvidenceRequirement.CONTEXT_TRACE
        assert EvaluationCriterionEvidenceRequirement("RETRIEVAL_TRACE") == EvaluationCriterionEvidenceRequirement.RETRIEVAL_TRACE
        assert EvaluationCriterionEvidenceRequirement("EVIDENCE_GRAPH") == EvaluationCriterionEvidenceRequirement.EVIDENCE_GRAPH


class TestApplicabilityValidation:
    def test_validate_applicability_rejects_unknown_domain(self):
        applicability = EvaluationCriterionApplicability(
            domain=EvaluationDomain.UNKNOWN,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        issues = validate_criterion_applicability(applicability)
        assert any("UNKNOWN" in i for i in issues)

    def test_validate_applicability_rejects_unknown_subject_type(self):
        applicability = EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.UNKNOWN,
        )
        issues = validate_criterion_applicability(applicability)
        assert any("UNKNOWN" in i for i in issues)

    def test_validate_applicability_accepts_known(self):
        applicability = EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        issues = validate_criterion_applicability(applicability)
        assert len(issues) == 0


class TestSchemaItemValidation:
    def test_validate_schema_item_rejects_empty_id(self):
        item = _make_item(criterion_id="")
        issues = validate_criteria_schema_item(item)
        assert any("criterion_id must not be empty" in i for i in issues)

    def test_validate_schema_item_rejects_empty_name(self):
        item = _make_item(name="")
        issues = validate_criteria_schema_item(item)
        assert any("name must not be empty" in i for i in issues)

    def test_unknown_kind_cannot_be_required(self):
        item = _make_item(
            kind=EvaluationCriterionKind.UNKNOWN,
            requirement_level=EvaluationCriterionRequirementLevel.REQUIRED,
        )
        issues = validate_criteria_schema_item(item)
        assert any("UNKNOWN" in i and "cannot be" in i for i in issues)

    def test_unknown_kind_cannot_be_blocking(self):
        item = _make_item(
            kind=EvaluationCriterionKind.UNKNOWN,
            requirement_level=EvaluationCriterionRequirementLevel.BLOCKING,
            evidence_requirement=EvaluationCriterionEvidenceRequirement.EVIDENCE_REF,
        )
        issues = validate_criteria_schema_item(item)
        assert any("UNKNOWN" in i and "cannot be" in i for i in issues)

    def test_unknown_kind_optional_is_ok(self):
        item = _make_item(
            kind=EvaluationCriterionKind.UNKNOWN,
            requirement_level=EvaluationCriterionRequirementLevel.OPTIONAL,
        )
        issues = validate_criteria_schema_item(item)
        assert not any("cannot be" in i for i in issues)

    def test_blocking_criterion_requires_evidence_or_limitations(self):
        item = _make_item(
            requirement_level=EvaluationCriterionRequirementLevel.BLOCKING,
            evidence_requirement=EvaluationCriterionEvidenceRequirement.NONE,
            limitations=(),
        )
        issues = validate_criteria_schema_item(item)
        assert any("BLOCKING" in i for i in issues)

    def test_blocking_criterion_with_limitations_ok(self):
        item = _make_item(
            requirement_level=EvaluationCriterionRequirementLevel.BLOCKING,
            evidence_requirement=EvaluationCriterionEvidenceRequirement.NONE,
            limitations=("Evidence requirement deferred to P3 substrate",),
        )
        issues = validate_criteria_schema_item(item)
        assert not any("BLOCKING" in i for i in issues)


class TestSchemaValidation:
    def test_schema_rejects_empty_schema_id(self):
        schema = _make_schema(schema_id="")
        issues = validate_evaluation_criteria_schema(schema)
        assert any("schema_id must not be empty" in i for i in issues)

    def test_schema_rejects_empty_name(self):
        schema = _make_schema(name="")
        issues = validate_evaluation_criteria_schema(schema)
        assert any("schema name must not be empty" in i for i in issues)

    def test_schema_rejects_empty_criteria(self):
        schema = _make_schema(criteria=())
        issues = validate_evaluation_criteria_schema(schema)
        assert any("criteria must not be empty" in i for i in issues)

    def test_schema_rejects_duplicate_criterion_ids(self):
        item = _make_item(criterion_id="dup_id")
        schema = _make_schema(criteria=(item, item))
        issues = validate_evaluation_criteria_schema(schema)
        assert any("duplicate criterion_id" in i for i in issues)

    def test_schema_rejects_unknown_domain(self):
        schema = _make_schema(domain=EvaluationDomain.UNKNOWN)
        issues = validate_evaluation_criteria_schema(schema)
        assert any("UNKNOWN domain" in i for i in issues)

    def test_schema_rejects_unknown_subject_type(self):
        schema = _make_schema(subject_type=EvaluationSubjectType.UNKNOWN)
        issues = validate_evaluation_criteria_schema(schema)
        assert any("UNKNOWN subject_type" in i for i in issues)

    def test_valid_schema_passes(self):
        schema = _make_schema()
        issues = validate_evaluation_criteria_schema(schema)
        assert len(issues) == 0


class TestDefaultSchema:
    def test_default_schema_has_criteria(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        assert len(schema.criteria) >= 4
        assert schema.domain == EvaluationDomain.AUREL_CORE
        assert schema.subject_type == EvaluationSubjectType.AGENT_IDENTITY

    def test_default_schema_is_valid(self):
        schema = build_default_criteria_schema_for_subject_type(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
        )
        issues = validate_evaluation_criteria_schema(schema)
        assert len(issues) == 0

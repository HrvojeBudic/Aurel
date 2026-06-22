"""P1.5.4 criteria serialization tests."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.evaluation.evaluation_criteria_schema import (
    EvaluationCriteriaSchemaRegistry,
    EvaluationCriteriaSchemaResolution,
    EvaluationCriterionApplicability,
    build_default_criteria_schema_for_subject_type,
    build_default_sparse_criteria_schema,
    build_p154_criteria_schema_report,
    criteria_schema_item_to_dict,
    criteria_schema_registry_to_dict,
    criteria_schema_report_to_dict,
    criteria_schema_resolution_to_dict,
    criteria_schema_to_dict,
    criterion_applicability_to_dict,
    example_criteria_schema,
    example_sparse_criteria_schema,
    list_criteria_schemas,
)
from agentic_runtime.evaluation.evaluation_foundation import (
    EvaluationDomain,
    EvaluationSubjectType,
)


class TestSerialization:
    def test_criterion_applicability_json_serializable(self):
        applicability = EvaluationCriterionApplicability(
            domain=EvaluationDomain.AUREL_CORE,
            subject_type=EvaluationSubjectType.AGENT_IDENTITY,
            origin_filter=("AUREL_CORE",),
            category_filter=("STANDARD",),
        )
        d = criterion_applicability_to_dict(applicability)
        s = json.dumps(d)
        assert "AUREL_CORE" in s
        assert "STANDARD" in s

    def test_criteria_schema_item_json_serializable(self):
        schema = example_criteria_schema()
        item = schema.criteria[0]
        d = criteria_schema_item_to_dict(item)
        s = json.dumps(d)
        assert "criterion_id" in d
        assert "kind" in d
        assert d["kind"] in ("GROUNDEDNESS", object())

    def test_criteria_schema_json_serializable(self):
        schema = example_criteria_schema()
        d = criteria_schema_to_dict(schema)
        s = json.dumps(d)
        assert "schema_id" in s
        assert len(d["criteria"]) >= 4

    def test_criteria_schema_registry_json_serializable(self):
        schema = example_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(
            registry_id="reg_ser_001",
            schemas=(schema,),
        )
        d = criteria_schema_registry_to_dict(registry)
        s = json.dumps(d)
        assert "reg_ser_001" in s
        assert len(d["schemas"]) == 1

    def test_criteria_schema_resolution_json_serializable(self):
        resolution = EvaluationCriteriaSchemaResolution(
            subject_id="subj_test",
            schema_ids=("schema_001",),
            criteria=(),
            required_criteria=("crit_001",),
            blocking_criteria=("crit_001",),
            summary="test",
        )
        d = criteria_schema_resolution_to_dict(resolution)
        s = json.dumps(d)
        assert "subj_test" in s

    def test_criteria_schema_report_json_serializable(self):
        report = build_p154_criteria_schema_report(schemas_created=2, criteria_created=10, sparse_criteria_ready=True)
        d = criteria_schema_report_to_dict(report)
        s = json.dumps(d)
        assert "p154_" in s
        assert "P1.5.5" in s
        assert d["sparse_criteria_ready"] is True


class TestListSchemas:
    def test_list_schemas_by_domain(self):
        core_schema = example_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(
            registry_id="reg_list",
            schemas=(core_schema,),
        )
        results = list_criteria_schemas(registry, domain=EvaluationDomain.AUREL_CORE)
        assert len(results) == 1

    def test_list_schemas_no_match(self):
        core_schema = example_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(
            registry_id="reg_list",
            schemas=(core_schema,),
        )
        results = list_criteria_schemas(registry, domain=EvaluationDomain.AUTONOMY)
        assert len(results) == 0

    def test_list_schemas_by_subject_type(self):
        core_schema = example_criteria_schema()
        registry = EvaluationCriteriaSchemaRegistry(
            registry_id="reg_list",
            schemas=(core_schema,),
        )
        results = list_criteria_schemas(registry, subject_type=EvaluationSubjectType.AGENT_IDENTITY)
        assert len(results) == 1

    def test_sparse_schema_serializable(self):
        schema = example_sparse_criteria_schema()
        d = criteria_schema_to_dict(schema)
        s = json.dumps(d)
        assert "sparse" in d["name"].lower() or "SPARSE" in s
        assert len(d["criteria"]) >= 5

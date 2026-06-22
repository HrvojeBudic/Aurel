"""P1.5.9 registry tests — Adversarial Evaluation Cases."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialAttackSurface,
    AdversarialCaseRegistry,
    AdversarialCaseSeverity,
    AdversarialCaseStatus,
    AdversarialCaseType,
    AdversarialEvaluationCase,
    AdversarialExpectedOutcome,
    adversarial_case_registry_to_dict,
    list_adversarial_cases,
    register_adversarial_case,
    validate_adversarial_case_registry,
)


def _make_case(**kwargs) -> AdversarialEvaluationCase:
    defaults = {
        "case_id": "adv_test_001",
        "name": "Test adversarial case",
        "case_type": AdversarialCaseType.NEGATIVE_CONTROL,
        "status": AdversarialCaseStatus.ACTIVE,
        "severity": AdversarialCaseSeverity.MEDIUM,
        "attack_surfaces": (AdversarialAttackSurface.EVIDENCE,),
        "expected_outcome": AdversarialExpectedOutcome.SHOULD_PASS,
        "applies_to_domains": ("AUREL_CORE",),
        "applies_to_subject_types": (),
        "applies_to_criteria_kinds": (),
        "fixture_refs": (),
        "hygiene_assessment_refs": (),
        "source_refs": (),
        "evidence_refs": (),
        "context_refs": (),
        "adversarial_input_refs": (),
        "expected_safe_behavior": "Decline unsupported claims.",
        "expected_failure_behavior": "Accept unsupported claims.",
        "required_detection_signals": (),
        "required_failure_modes": (),
        "sparse_context_required": False,
        "multi_hop_required": False,
        "contradiction_required": False,
        "operator_review_required": False,
        "limitations": ("Schema only",),
        "warnings": (),
        "blockers": (),
        "summary": "Schema-only adversarial case definition.",
    }
    defaults.update(kwargs)
    return AdversarialEvaluationCase(**defaults)


def _empty_registry() -> AdversarialCaseRegistry:
    return AdversarialCaseRegistry(
        registry_id="adv_registry_test",
        cases=(),
        warnings=(),
        blockers=(),
        summary="test registry",
    )


class TestRegistry:
    def test_register_valid_case(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(),
        )
        assert len(registry.cases) == 1
        assert registry.cases[0].case_id == "adv_test_001"

    def test_register_duplicate_case_id_blocks(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(case_id="adv_test_001", name="duplicate"),
        )
        assert len(registry.cases) == 1
        assert any("duplicate case_id" in b for b in registry.blockers)

    def test_registry_validation_rejects_empty_registry_id(self):
        registry = AdversarialCaseRegistry(
            registry_id="",
            cases=(),
            warnings=(),
            blockers=(),
            summary="",
        )
        issues = validate_adversarial_case_registry(registry)
        assert any("registry_id must not be empty" in i for i in issues)

    def test_registry_validation_rejects_duplicate_ids(self):
        case = _make_case()
        registry = AdversarialCaseRegistry(
            registry_id="adv_registry_test",
            cases=(case, case),
            warnings=(),
            blockers=(),
            summary="",
        )
        issues = validate_adversarial_case_registry(registry)
        assert any("duplicate case_id" in i for i in issues)

    def test_registry_validation_rejects_invalid_active_case(self):
        registry = AdversarialCaseRegistry(
            registry_id="adv_registry_test",
            cases=(_make_case(case_id="", name="bad"),),
            warnings=(),
            blockers=(),
            summary="",
        )
        issues = validate_adversarial_case_registry(registry)
        assert any("case_id must not be empty" in i for i in issues)

    def test_list_cases_by_type(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(case_id="a1", case_type=AdversarialCaseType.NEGATIVE_CONTROL),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(
                case_id="a2",
                case_type=AdversarialCaseType.CONTRADICTION_TRAP,
                contradiction_required=True,
            ),
        )
        results = list_adversarial_cases(registry, case_type=AdversarialCaseType.NEGATIVE_CONTROL)
        assert len(results) == 1
        assert results[0].case_id == "a1"

    def test_list_cases_by_severity(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(case_id="a1", severity=AdversarialCaseSeverity.LOW),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(case_id="a2", severity=AdversarialCaseSeverity.HIGH),
        )
        results = list_adversarial_cases(registry, severity=AdversarialCaseSeverity.HIGH)
        assert len(results) == 1
        assert results[0].case_id == "a2"

    def test_list_cases_by_attack_surface(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(
                case_id="a1",
                attack_surfaces=(AdversarialAttackSurface.POLICY,),
            ),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(
                case_id="a2",
                attack_surfaces=(AdversarialAttackSurface.EVIDENCE,),
            ),
        )
        results = list_adversarial_cases(
            registry,
            attack_surface=AdversarialAttackSurface.POLICY,
        )
        assert len(results) == 1
        assert results[0].case_id == "a1"

    def test_list_cases_by_status(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(case_id="a1", status=AdversarialCaseStatus.ACTIVE),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(case_id="a2", status=AdversarialCaseStatus.DRAFT),
        )
        results = list_adversarial_cases(registry, status=AdversarialCaseStatus.DRAFT)
        assert len(results) == 1
        assert results[0].case_id == "a2"

    def test_adversarial_registry_json_serializable(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(),
        )
        payload = adversarial_case_registry_to_dict(registry)
        json.dumps(payload)
        assert payload["registry_id"] == "adv_registry_test"
        assert len(payload["cases"]) == 1

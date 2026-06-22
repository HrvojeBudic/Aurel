"""P1.5.9 resolution tests — Adversarial Evaluation Cases."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialAttackSurface,
    AdversarialCaseSeverity,
    AdversarialCaseStatus,
    AdversarialCaseType,
    AdversarialEvaluationCase,
    AdversarialExpectedOutcome,
    build_default_adversarial_case_registry,
    register_adversarial_case,
    resolve_adversarial_cases_for_subject,
)
from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialCaseRegistry,
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
        "applies_to_subject_types": ("AGENT_IDENTITY",),
        "applies_to_criteria_kinds": ("GROUNDEDNESS",),
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


class TestResolution:
    def test_resolve_cases_for_subject_domain_and_type(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(case_id="match"),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(
                case_id="nomatch",
                applies_to_domains=("IDENTITY",),
                applies_to_subject_types=("PROCEDURE",),
            ),
        )
        results = resolve_adversarial_cases_for_subject(
            registry=registry,
            domain="AUREL_CORE",
            subject_type="AGENT_IDENTITY",
        )
        assert len(results) == 1
        assert results[0].case_id == "match"

    def test_resolve_cases_active_by_default(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(case_id="active", status=AdversarialCaseStatus.ACTIVE),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(case_id="draft", status=AdversarialCaseStatus.DRAFT),
        )
        results = resolve_adversarial_cases_for_subject(
            registry=registry,
            domain="AUREL_CORE",
            subject_type="AGENT_IDENTITY",
        )
        assert len(results) == 1
        assert results[0].case_id == "active"

    def test_resolve_cases_include_inactive_when_requested(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(case_id="active", status=AdversarialCaseStatus.ACTIVE),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(case_id="draft", status=AdversarialCaseStatus.DRAFT),
        )
        results = resolve_adversarial_cases_for_subject(
            registry=registry,
            domain="AUREL_CORE",
            subject_type="AGENT_IDENTITY",
            include_inactive=True,
        )
        assert len(results) == 2

    def test_resolve_cases_by_criteria_kind(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(
                case_id="grounded",
                applies_to_criteria_kinds=("GROUNDEDNESS",),
            ),
        )
        registry = register_adversarial_case(
            registry=registry,
            case=_make_case(
                case_id="policy",
                applies_to_criteria_kinds=("POLICY_COMPLIANCE",),
            ),
        )
        results = resolve_adversarial_cases_for_subject(
            registry=registry,
            domain="AUREL_CORE",
            subject_type="AGENT_IDENTITY",
            criteria_kind="GROUNDEDNESS",
        )
        assert len(results) == 1
        assert results[0].case_id == "grounded"

    def test_resolve_generic_cases_when_domain_or_type_empty(self):
        registry = register_adversarial_case(
            registry=_empty_registry(),
            case=_make_case(
                case_id="generic",
                applies_to_domains=(),
                applies_to_subject_types=(),
            ),
        )
        results = resolve_adversarial_cases_for_subject(
            registry=registry,
            domain="ANY_DOMAIN",
            subject_type="ANY_TYPE",
        )
        assert len(results) == 1
        assert results[0].case_id == "generic"

    def test_resolve_does_not_execute_cases(self):
        src = inspect.getsource(resolve_adversarial_cases_for_subject)
        assert "run_case" not in src
        assert "execute_case" not in src
        assert "EvaluationResult(" not in src

    def test_default_registry_resolves_cases(self):
        registry = build_default_adversarial_case_registry()
        results = resolve_adversarial_cases_for_subject(
            registry=registry,
            domain="AUREL_CORE",
            subject_type="AGENT_IDENTITY",
        )
        assert len(results) >= 10

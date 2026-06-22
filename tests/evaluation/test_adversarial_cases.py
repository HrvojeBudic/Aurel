"""P1.5.9 core object and validation tests — Adversarial Evaluation Cases."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialAttackSurface,
    AdversarialCaseSeverity,
    AdversarialCaseStatus,
    AdversarialCaseType,
    AdversarialEvaluationCase,
    AdversarialExpectedOutcome,
    adversarial_case_to_dict,
    adversarial_case_validation_to_dict,
    validate_adversarial_case,
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


class TestAdversarialEnums:
    def test_adversarial_case_type_closed_world(self):
        assert AdversarialCaseType("NEGATIVE_CONTROL") == AdversarialCaseType.NEGATIVE_CONTROL
        assert AdversarialCaseType("SPARSE_CONTEXT_OMISSION_TRAP") == AdversarialCaseType.SPARSE_CONTEXT_OMISSION_TRAP
        assert AdversarialCaseType("UNKNOWN") == AdversarialCaseType.UNKNOWN

    def test_adversarial_case_status_closed_world(self):
        assert AdversarialCaseStatus("DRAFT") == AdversarialCaseStatus.DRAFT
        assert AdversarialCaseStatus("ACTIVE") == AdversarialCaseStatus.ACTIVE
        assert AdversarialCaseStatus("REJECTED") == AdversarialCaseStatus.REJECTED
        assert AdversarialCaseStatus("UNKNOWN") == AdversarialCaseStatus.UNKNOWN

    def test_adversarial_case_severity_closed_world(self):
        assert AdversarialCaseSeverity("LOW") == AdversarialCaseSeverity.LOW
        assert AdversarialCaseSeverity("CRITICAL") == AdversarialCaseSeverity.CRITICAL
        assert AdversarialCaseSeverity("UNKNOWN") == AdversarialCaseSeverity.UNKNOWN

    def test_attack_surface_closed_world(self):
        assert AdversarialAttackSurface("CONTEXT") == AdversarialAttackSurface.CONTEXT
        assert AdversarialAttackSurface("SPARSE_CONTEXT") == AdversarialAttackSurface.SPARSE_CONTEXT
        assert AdversarialAttackSurface("UNKNOWN") == AdversarialAttackSurface.UNKNOWN

    def test_expected_outcome_closed_world(self):
        assert AdversarialExpectedOutcome("SHOULD_PASS") == AdversarialExpectedOutcome.SHOULD_PASS
        assert AdversarialExpectedOutcome("SHOULD_MARK_CONFLICTED") == AdversarialExpectedOutcome.SHOULD_MARK_CONFLICTED
        assert AdversarialExpectedOutcome("UNKNOWN") == AdversarialExpectedOutcome.UNKNOWN


class TestAdversarialCaseValidation:
    def test_validate_case_rejects_empty_case_id(self):
        case = _make_case(case_id="")
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("case_id must not be empty" in b for b in validation.blockers)

    def test_validate_case_rejects_empty_name(self):
        case = _make_case(name="")
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("name must not be empty" in b for b in validation.blockers)

    def test_active_case_rejects_unknown_case_type(self):
        case = _make_case(case_type=AdversarialCaseType.UNKNOWN)
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("UNKNOWN case_type" in b for b in validation.blockers)

    def test_active_case_requires_expected_safe_behavior(self):
        case = _make_case(expected_safe_behavior="")
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("expected_safe_behavior" in b for b in validation.blockers)

    def test_active_case_requires_expected_failure_behavior(self):
        case = _make_case(expected_failure_behavior="")
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("expected_failure_behavior" in b for b in validation.blockers)

    def test_active_case_requires_known_expected_outcome(self):
        case = _make_case(expected_outcome=AdversarialExpectedOutcome.UNKNOWN)
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("UNKNOWN expected_outcome" in b for b in validation.blockers)

    def test_high_critical_case_requires_attack_surface(self):
        case = _make_case(
            severity=AdversarialCaseSeverity.HIGH,
            attack_surfaces=(),
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("attack surface" in b for b in validation.blockers)

    def test_rejected_case_requires_blocker(self):
        case = _make_case(
            status=AdversarialCaseStatus.REJECTED,
            blockers=(),
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("REJECTED status requires" in b for b in validation.blockers)

    def test_invalid_case_requires_blocker(self):
        case = _make_case(
            status=AdversarialCaseStatus.INVALID,
            blockers=(),
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("INVALID status requires" in b for b in validation.blockers)

    def test_case_validation_rejects_execution_claim(self):
        case = _make_case(summary="This case will run benchmark fixtures immediately.")
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("run benchmark" in b for b in validation.blockers)

    def test_case_validation_rejects_verification_claim(self):
        case = _make_case(expected_safe_behavior="This will verify capability after trap survival.")
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("verification" in b for b in validation.blockers)


class TestTrapSemantics:
    def test_sparse_context_omission_trap_requires_sparse_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.SPARSE_CONTEXT_OMISSION_TRAP,
            sparse_context_required=False,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("sparse_context_required" in b for b in validation.blockers)

    def test_lost_context_trap_requires_sparse_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.LOST_CONTEXT_TRAP,
            sparse_context_required=False,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid

    def test_needle_in_context_trap_requires_sparse_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.NEEDLE_IN_CONTEXT_TRAP,
            sparse_context_required=False,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid

    def test_context_budget_pressure_trap_requires_sparse_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.CONTEXT_BUDGET_PRESSURE_TRAP,
            sparse_context_required=False,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid

    def test_multi_hop_trace_trap_requires_multi_hop_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.MULTI_HOP_TRACE_TRAP,
            multi_hop_required=False,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("multi_hop_required" in b for b in validation.blockers)

    def test_contradiction_trap_requires_contradiction_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.CONTRADICTION_TRAP,
            contradiction_required=False,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid
        assert any("contradiction_required" in b for b in validation.blockers)

    def test_contradiction_survival_trap_requires_contradiction_flag(self):
        case = _make_case(
            case_type=AdversarialCaseType.CONTRADICTION_SURVIVAL_TRAP,
            contradiction_required=False,
            sparse_context_required=True,
        )
        validation = validate_adversarial_case(case)
        assert not validation.valid


class TestSerialization:
    def test_adversarial_case_json_serializable(self):
        case = _make_case()
        payload = adversarial_case_to_dict(case)
        json.dumps(payload)
        assert payload["case_type"] == "NEGATIVE_CONTROL"
        assert payload["status"] == "ACTIVE"

    def test_adversarial_validation_json_serializable(self):
        validation = validate_adversarial_case(_make_case())
        payload = adversarial_case_validation_to_dict(validation)
        json.dumps(payload)
        assert payload["valid"] is True

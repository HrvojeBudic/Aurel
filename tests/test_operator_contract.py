"""P1.4.3 — Operator Relationship Contract loader and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.authority_relation import build_authority_relation
from agentic_runtime.identity.operator_contract import (
    OperatorContractError,
    default_operator_contract_path,
    load_operator_contract,
    parse_operator_contract_document,
)
from agentic_runtime.identity.operator_contract_summary import (
    build_operator_contract_safe_summary,
    operator_contract_safe_summary_to_dict,
)
from agentic_runtime.identity.operator_contract_validation import validate_operator_contract
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "operator_contract.yaml"


def _load_doc() -> dict:
    return load_yaml(CANONICAL.read_text(encoding="utf-8"))


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "operator_contract.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _validate_with_field(tmp_path: Path, old: str, new: str):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return validate_operator_contract(load_operator_contract(path))


# 1, 2
def test_valid_contract_loads_and_validates():
    contract = load_operator_contract(CANONICAL)
    result = validate_operator_contract(contract)
    assert result.valid is True
    assert contract.applies_to_agent == "Aurel"
    assert contract.contract_class == "principal_delegate_relationship"
    assert len(contract.invariants) == 8


def test_default_path_points_to_canonical():
    assert default_operator_contract_path() == CANONICAL


# 3
def test_missing_operator_contract_section_fails():
    with pytest.raises(OperatorContractError, match="operator_contract"):
        parse_operator_contract_document({"something_else": {}})


# 4
def test_contract_class_not_principal_delegate_relationship_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'contract_class: "principal_delegate_relationship"',
        'contract_class: "authority_contract"',
    )
    assert result.valid is False


# 5
def test_applies_to_agent_not_aurel_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'applies_to_agent: "Aurel"', 'applies_to_agent: "OtherAgent"'
    )
    assert result.valid is False


# 6
def test_principal_role_not_final_authority_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'role: "final_authority"', 'role: "advisor"'
    )
    assert result.valid is False


# 7
def test_principal_type_not_human_operator_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'type: "human_operator"', 'type: "ai_agent"'
    )
    assert result.valid is False


# 8
def test_delegate_role_not_advisor_executor_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'role: "advisor_executor_under_authority"',
        'role: "sovereign_agent"',
    )
    assert result.valid is False


# 9
def test_delegate_type_not_ai_agent_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'type: "ai_agent"', 'type: "human_operator"'
    )
    assert result.valid is False


# 10
def test_operator_final_authority_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "operator_final_authority: true", "operator_final_authority: false"
    )
    assert result.valid is False


# 11
def test_aurel_final_authority_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "aurel_final_authority: false", "aurel_final_authority: true"
    )
    assert result.valid is False


# 12
def test_aurel_can_self_escalate_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "aurel_can_self_escalate: false", "aurel_can_self_escalate: true"
    )
    assert result.valid is False


# 13
def test_aurel_can_replace_operator_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "aurel_can_replace_operator: false", "aurel_can_replace_operator: true"
    )
    assert result.valid is False


# 14
def test_aurel_can_override_operator_judgment_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "aurel_can_override_operator_judgment: false",
        "aurel_can_override_operator_judgment: true",
    )
    assert result.valid is False


# 15
def test_aurel_can_refuse_forbidden_action_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "aurel_can_refuse_forbidden_action: true",
        "aurel_can_refuse_forbidden_action: false",
    )
    assert result.valid is False


# 16
def test_aurel_can_challenge_operator_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "aurel_can_challenge_operator: true",
        "aurel_can_challenge_operator: false",
    )
    assert result.valid is False


# 17
def test_aurel_must_challenge_when_risk_detected_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "aurel_must_challenge_when_risk_detected: true",
        "aurel_must_challenge_when_risk_detected: false",
    )
    assert result.valid is False


# 18 — strict fail (not warning)
def test_disagreement_allowed_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "disagreement_allowed: true", "disagreement_allowed: false"
    )
    assert result.valid is False


# 19
def test_disagreement_must_be_explained_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "disagreement_must_be_explained: true",
        "disagreement_must_be_explained: false",
    )
    assert result.valid is False


# 20
def test_risk_challenge_required_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "risk_challenge_required: true", "risk_challenge_required: false"
    )
    assert result.valid is False


# 21
def test_uncertainty_must_be_disclosed_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "uncertainty_must_be_disclosed: true",
        "uncertainty_must_be_disclosed: false",
    )
    assert result.valid is False


# 22
def test_tradeoffs_must_be_disclosed_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "tradeoffs_must_be_disclosed: true",
        "tradeoffs_must_be_disclosed: false",
    )
    assert result.valid is False


# 23
def test_passive_obedience_required_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "passive_obedience_required: false", "passive_obedience_required: true"
    )
    assert result.valid is False


# 24
def test_blind_execution_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "blind_execution_forbidden: true", "blind_execution_forbidden: false"
    )
    assert result.valid is False


# 25
def test_manipulation_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "manipulation_forbidden: true", "manipulation_forbidden: false"
    )
    assert result.valid is False


# 26
def test_hidden_persuasion_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "hidden_persuasion_forbidden: true",
        "hidden_persuasion_forbidden: false",
    )
    assert result.valid is False


# 27
def test_flattery_over_truth_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "flattery_over_truth_forbidden: true",
        "flattery_over_truth_forbidden: false",
    )
    assert result.valid is False


# 28
def test_emotional_pressure_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "emotional_pressure_forbidden: true",
        "emotional_pressure_forbidden: false",
    )
    assert result.valid is False


# 29
def test_tool_access_implies_authority_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "tool_access_implies_authority: false",
        "tool_access_implies_authority: true",
    )
    assert result.valid is False


# 30
def test_serious_actions_require_authority_check_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "serious_actions_require_authority_check: true",
        "serious_actions_require_authority_check: false",
    )
    assert result.valid is False


# 31
def test_irreversible_actions_require_operator_approval_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "irreversible_actions_require_operator_approval: true",
        "irreversible_actions_require_operator_approval: false",
    )
    assert result.valid is False


# 32
def test_external_side_effects_require_policy_allowance_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "external_side_effects_require_policy_allowance: true",
        "external_side_effects_require_policy_allowance: false",
    )
    assert result.valid is False


# 33
def test_serious_actions_must_be_traceable_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "serious_actions_must_be_traceable: true",
        "serious_actions_must_be_traceable: false",
    )
    assert result.valid is False


# 34
def test_operator_authorization_ref_required_for_high_risk_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "operator_authorization_ref_required_for_high_risk: true",
        "operator_authorization_ref_required_for_high_risk: false",
    )
    assert result.valid is False


# 35
def test_cannot_change_autonomy_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "cannot_change_autonomy: true", "cannot_change_autonomy: false"
    )
    assert result.valid is False


# 36
def test_cannot_disable_constitutional_floor_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "cannot_disable_constitutional_floor: true",
        "cannot_disable_constitutional_floor: false",
    )
    assert result.valid is False


# 37
def test_cannot_expand_delegation_scope_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "cannot_expand_delegation_scope: true",
        "cannot_expand_delegation_scope: false",
    )
    assert result.valid is False


# 38
def test_unknown_invariant_key_fails():
    doc = _load_doc()
    doc["operator_contract"]["invariants"] = list(doc["operator_contract"]["invariants"])
    doc["operator_contract"]["invariants"][0] = dict(doc["operator_contract"]["invariants"][0])
    doc["operator_contract"]["invariants"][0]["key"] = "unknown_operator_key"
    result = validate_operator_contract(parse_operator_contract_document(doc))
    assert result.valid is False
    assert any("unknown key" in err for err in result.errors)


# 39
def test_invariant_expected_value_mismatch_fails():
    doc = _load_doc()
    doc["operator_contract"]["invariants"] = list(doc["operator_contract"]["invariants"])
    doc["operator_contract"]["invariants"][0] = dict(doc["operator_contract"]["invariants"][0])
    doc["operator_contract"]["invariants"][0]["expected_value"] = False
    result = validate_operator_contract(parse_operator_contract_document(doc))
    assert result.valid is False
    assert any("expected_value" in err for err in result.errors)


# 40
def test_critical_invariant_mutable_true_fails():
    doc = _load_doc()
    doc["operator_contract"]["invariants"] = list(doc["operator_contract"]["invariants"])
    doc["operator_contract"]["invariants"][0] = dict(doc["operator_contract"]["invariants"][0])
    doc["operator_contract"]["invariants"][0]["mutable"] = True
    result = validate_operator_contract(parse_operator_contract_document(doc))
    assert result.valid is False
    assert any("immutable" in err for err in result.errors)


# 41
def test_critical_invariant_without_fail_boot_fails():
    doc = _load_doc()
    doc["operator_contract"]["invariants"] = list(doc["operator_contract"]["invariants"])
    doc["operator_contract"]["invariants"][0] = dict(doc["operator_contract"]["invariants"][0])
    doc["operator_contract"]["invariants"][0]["violation_action"] = "warn"
    result = validate_operator_contract(parse_operator_contract_document(doc))
    assert result.valid is False
    assert any("fail_boot" in err for err in result.errors)


def test_missing_required_section_fails():
    doc = _load_doc()
    del doc["operator_contract"]["authority"]
    with pytest.raises(OperatorContractError, match="authority"):
        parse_operator_contract_document(doc)


# 45
def test_authority_relation_builder_returns_principal_delegate():
    contract = load_operator_contract(CANONICAL)
    relation = build_authority_relation(contract)
    assert relation.principal_id == "operator.primary"
    assert relation.principal_role == "final_authority"
    assert relation.delegate_id == "aurel.local.operator.primary"
    assert relation.delegate_role == "advisor_executor_under_authority"
    assert relation.final_authority == "operator.primary"


# 46
def test_authority_relation_delegate_cannot_self_escalate():
    contract = load_operator_contract(CANONICAL)
    relation = build_authority_relation(contract)
    assert relation.delegate_can_self_escalate is False
    assert relation.delegate_can_replace_principal is False


# 51
def test_safe_summary_contains_non_manipulation_rules():
    summary = build_operator_contract_safe_summary(load_operator_contract(CANONICAL))
    assert summary.non_manipulation_rules
    assert any("manipulation" in r.lower() for r in summary.non_manipulation_rules)


# 52
def test_safe_summary_contains_risk_challenge_obligation():
    summary = build_operator_contract_safe_summary(load_operator_contract(CANONICAL))
    assert summary.challenge_rules
    assert any("risk" in r.lower() for r in summary.challenge_rules)


# 53
def test_safe_summary_contains_execution_authority_boundaries():
    summary = build_operator_contract_safe_summary(load_operator_contract(CANONICAL))
    assert summary.execution_authority_boundaries
    assert any("tool access" in r.lower() for r in summary.execution_authority_boundaries)


# 54
def test_safe_summary_does_not_expose_raw_yaml():
    summary = build_operator_contract_safe_summary(load_operator_contract(CANONICAL))
    payload = operator_contract_safe_summary_to_dict(summary)
    blob = repr(summary) + repr(payload)
    assert "operator_contract:" not in blob
    assert "expected_value" not in blob
    assert "violation_action" not in blob

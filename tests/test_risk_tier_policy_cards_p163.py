"""Tests for P1.6.3 - Risk Tier Policy Card Model."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards import (
    DEFAULT_RISK_ACTION_CLASS_MAPPINGS,
    DEFAULT_RISK_TIER_DEFINITIONS,
    REQUIRED_RISK_TIERS,
    RISK_TIER_POLICY_CARD_SCHEMA_VERSION,
    SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS,
    EvidenceExpectation,
    OversightLevel,
    PolicyCardKind,
    ReversibilityLevel,
    RiskActionClass,
    RiskActionClassMapping,
    RiskTier,
    RiskTierDefinition,
    RiskTierPolicyCard,
    RiskTierPolicyCardUnknownFieldError,
    RiskTierPolicyCardUnsafeFieldError,
    RiskTierPolicyCardValidationError,
    compute_risk_tier_policy_card_hash,
    create_default_risk_tier_policy_card,
    export_risk_tier_policy_schema,
    get_risk_tier_policy_schema,
    is_supported_risk_tier_policy_schema_version,
    load_risk_tier_policy_card_from_dict,
    risk_tier_policy_card_to_canonical_dict,
    serialize_risk_tier_policy_card_canonical,
    validate_risk_tier_policy_card,
    validate_risk_tier_policy_card_dict,
    validate_risk_tier_policy_schema_version,
)
import agentic_runtime.policy_cards.risk_tiers as risk_tiers_module


def _default_dict() -> dict:
    return risk_tier_policy_card_to_canonical_dict(
        create_default_risk_tier_policy_card()
    )


def _tier(data: dict, tier: str) -> dict:
    for item in data["tiers"]:
        if item["tier"] == tier:
            return item
    raise AssertionError(f"tier not found: {tier}")


def _remove_tier(data: dict, tier: str) -> None:
    data["tiers"] = [item for item in data["tiers"] if item["tier"] != tier]


def _messages(result) -> str:
    return " ".join(error.message for error in result.errors)


def test_default_risk_tier_policy_card_valid():
    card = create_default_risk_tier_policy_card()
    assert isinstance(card, RiskTierPolicyCard)
    result = validate_risk_tier_policy_card(card)
    assert result.valid
    assert result.errors == ()
    assert isinstance(result.canonical_hash, str)
    assert len(result.canonical_hash) == 64


def test_required_tiers_exist_in_default_card():
    card = create_default_risk_tier_policy_card()
    tiers = {definition.tier for definition in card.tiers}
    assert tiers == set(REQUIRED_RISK_TIERS)
    assert {tier.value for tier in tiers} == {"R0", "R1", "R2", "R3", "R4", "R5", "R6"}


@pytest.mark.parametrize("invalid_tier", ["R9", "SUPER_ADMIN_RISK", "UNBOUNDED"])
def test_invalid_tier_rejected(invalid_tier: str):
    data = _default_dict()
    _tier(data, "R2")["tier"] = invalid_tier
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert invalid_tier in _messages(result)
    with pytest.raises(RiskTierPolicyCardValidationError, match=invalid_tier):
        load_risk_tier_policy_card_from_dict(data)


@pytest.mark.parametrize("missing_tier", ["R5", "R6"])
def test_missing_required_tier_rejected(missing_tier: str):
    data = _default_dict()
    _remove_tier(data, missing_tier)
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert missing_tier in _messages(result)


def test_duplicate_tier_rejected():
    data = _default_dict()
    data["tiers"].append(dict(_tier(data, "R3")))
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "duplicate" in _messages(result).lower()


def test_r5_must_require_explicit_confirmation():
    data = _default_dict()
    _tier(data, "R5")["default_requires_explicit_confirmation"] = False
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "explicit Operator confirmation" in _messages(result)


@pytest.mark.parametrize(
    "field_name",
    [
        "default_requires_trace",
        "default_requires_evidence",
        "default_requires_approval",
    ],
)
def test_r5_must_require_trace_evidence_and_approval(field_name: str):
    data = _default_dict()
    _tier(data, "R5")[field_name] = False
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)


def test_r6_must_be_denied():
    card = create_default_risk_tier_policy_card()
    r6 = next(definition for definition in card.tiers if definition.tier == RiskTier.R6)
    assert r6.oversight == OversightLevel.DENIED
    assert r6.reversibility == ReversibilityLevel.DENIED
    assert not r6.default_allows_execution
    assert validate_risk_tier_policy_card(card).valid


@pytest.mark.parametrize(
    "field_name",
    [
        "default_allows_external_egress",
        "default_allows_memory_write",
        "default_allows_tool_write",
        "default_allows_execution",
    ],
)
def test_r6_cannot_be_permissive(field_name: str):
    data = _default_dict()
    _tier(data, "R6")[field_name] = True
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "R6" in _messages(result)


@pytest.mark.parametrize(
    ("tier", "field_name", "unsafe_value"),
    [
        ("R6", "reversibility", "reversible"),
        ("R5", "oversight", "none"),
        ("R4", "default_requires_approval", False),
        ("R1", "default_allows_tool_write", True),
    ],
)
def test_reversibility_and_oversight_consistency(
    tier: str,
    field_name: str,
    unsafe_value,
):
    data = _default_dict()
    _tier(data, tier)[field_name] = unsafe_value
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert tier in _messages(result)


def test_action_class_mapping_valid():
    card = create_default_risk_tier_policy_card()
    mapping = RiskActionClassMapping(
        action_class=RiskActionClass.SEND_EMAIL,
        default_tier=RiskTier.R5,
        description="Email send is irreversible external communication.",
    )
    modified = RiskTierPolicyCard(
        policy_card=card.policy_card,
        schema_version=card.schema_version,
        tiers=card.tiers,
        action_class_mappings=(mapping,),
        metadata=card.metadata,
    )
    assert validate_risk_tier_policy_card(modified).valid


def test_invalid_action_class_mapping_rejected():
    data = _default_dict()
    data["action_class_mappings"][0]["action_class"] = "superuser_override"
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "superuser_override" in _messages(result)


def test_policy_card_compatibility_requires_risk_tier_kind():
    card = create_default_risk_tier_policy_card()
    assert card.policy_card.kind == PolicyCardKind.RISK_TIER
    data = _default_dict()
    data["policy_card"]["kind"] = "generic"
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "risk_tier" in _messages(result)


def test_closed_world_unknown_top_level_field_rejected():
    data = _default_dict()
    data["risk_override_backdoor"] = True
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "risk_override_backdoor" in _messages(result)
    with pytest.raises(RiskTierPolicyCardUnknownFieldError, match="risk_override_backdoor"):
        load_risk_tier_policy_card_from_dict(data)


def test_closed_world_unknown_nested_definition_field_rejected():
    data = _default_dict()
    _tier(data, "R0")["future_resolver_hint"] = True
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "future_resolver_hint" in _messages(result)


def test_dangerous_metadata_rejected():
    data = _default_dict()
    data["metadata"] = {"operator_not_required": True}
    result = validate_risk_tier_policy_card_dict(data)
    assert not result.valid
    assert "operator_not_required" in _messages(result)
    with pytest.raises(RiskTierPolicyCardUnsafeFieldError, match="operator_not_required"):
        load_risk_tier_policy_card_from_dict(data)


def test_safe_metadata_accepted():
    data = _default_dict()
    data["metadata"] = {"owner_note": "default risk tier policy"}
    card = load_risk_tier_policy_card_from_dict(data)
    assert card.metadata == {"owner_note": "default risk tier policy"}
    assert validate_risk_tier_policy_card(card).valid


def test_deterministic_serialization():
    card_a = create_default_risk_tier_policy_card()
    card_b = load_risk_tier_policy_card_from_dict(_default_dict())
    assert serialize_risk_tier_policy_card_canonical(card_a) == (
        serialize_risk_tier_policy_card_canonical(card_b)
    )
    parsed = json.loads(serialize_risk_tier_policy_card_canonical(card_a))
    assert parsed["schema_version"] == "1.0"
    assert parsed["policy_card"]["kind"] == "risk_tier"


def test_hash_stability():
    card_a = create_default_risk_tier_policy_card()
    card_b = load_risk_tier_policy_card_from_dict(_default_dict())
    assert compute_risk_tier_policy_card_hash(card_a) == (
        compute_risk_tier_policy_card_hash(card_b)
    )


def test_schema_export_deterministic():
    schema_a = export_risk_tier_policy_schema()
    schema_b = get_risk_tier_policy_schema()
    assert schema_a == schema_b
    assert json.dumps(schema_a, sort_keys=True) == json.dumps(schema_b, sort_keys=True)
    assert schema_a["schema_version"] == "1.0"
    assert schema_a["required_tiers"] == ["R0", "R1", "R2", "R3", "R4", "R5", "R6"]


def test_schema_version_helpers():
    assert RISK_TIER_POLICY_CARD_SCHEMA_VERSION == "1.0"
    assert SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS == ("1.0",)
    assert is_supported_risk_tier_policy_schema_version("1.0")
    assert not is_supported_risk_tier_policy_schema_version("2.0")
    assert validate_risk_tier_policy_schema_version("1.0").valid
    assert not validate_risk_tier_policy_schema_version("2.0").valid


def test_default_schema_constants_are_model_objects():
    assert len(DEFAULT_RISK_TIER_DEFINITIONS) == 7
    assert all(isinstance(definition, RiskTierDefinition) for definition in DEFAULT_RISK_TIER_DEFINITIONS)
    assert DEFAULT_RISK_ACTION_CLASS_MAPPINGS
    assert all(isinstance(mapping, RiskActionClassMapping) for mapping in DEFAULT_RISK_ACTION_CLASS_MAPPINGS)
    assert any(
        mapping.action_class == RiskActionClass.SEND_EMAIL
        and mapping.default_tier == RiskTier.R5
        for mapping in DEFAULT_RISK_ACTION_CLASS_MAPPINGS
    )


def test_reversible_and_compensatable_remain_distinct():
    assert ReversibilityLevel.REVERSIBLE.value == "reversible"
    assert ReversibilityLevel.COMPENSATABLE.value == "compensatable"
    assert ReversibilityLevel.REVERSIBLE != ReversibilityLevel.COMPENSATABLE


def test_evidence_expectations_include_r5_and_r6_semantics():
    data = _default_dict()
    assert _tier(data, "R5")["evidence_expectation"] == (
        EvidenceExpectation.TRACE_SHADOW_DIFF_EXPLICIT_CONFIRMATION.value
    )
    assert _tier(data, "R6")["evidence_expectation"] == (
        EvidenceExpectation.DENIAL_TRACE.value
    )


def test_no_runtime_resolver_classifier_or_enforcement_implemented():
    forbidden_api_names = {
        "classify_action_risk_tier",
        "classify_risk_tier",
        "resolve_risk_tier_policy",
        "enforce_risk_tier_policy",
        "simulate_risk_tier_policy",
        "write_risk_tier_trace_hook",
    }
    for name in forbidden_api_names:
        assert not hasattr(risk_tiers_module, name)

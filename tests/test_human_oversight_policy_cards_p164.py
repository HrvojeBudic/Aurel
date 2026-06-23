"""Tests for P1.6.4 - Human Oversight Policy Card Model."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards import (
    DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES,
    DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS,
    HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSION,
    REQUIRED_HUMAN_OVERSIGHT_RISK_TIERS,
    SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS,
    ConfirmationRequirement,
    HumanOversightAction,
    HumanOversightEscalationRule,
    HumanOversightLevel,
    HumanOversightMode,
    HumanOversightPolicyCard,
    HumanOversightPolicyCardUnknownFieldError,
    HumanOversightPolicyCardUnsafeFieldError,
    HumanOversightPolicyCardValidationError,
    HumanOversightTrigger,
    OversightEvidenceRequirement,
    OversightEvidenceType,
    PolicyCardKind,
    ReviewerRequirement,
    RiskTier,
    RiskTierOversightMapping,
    compute_human_oversight_policy_card_hash,
    create_default_human_oversight_policy_card,
    export_human_oversight_policy_schema,
    get_human_oversight_policy_schema,
    human_oversight_policy_card_to_canonical_dict,
    is_supported_human_oversight_policy_schema_version,
    load_human_oversight_policy_card_from_dict,
    serialize_human_oversight_policy_card_canonical,
    validate_human_oversight_policy_card,
    validate_human_oversight_policy_card_dict,
    validate_human_oversight_policy_schema_version,
)
import agentic_runtime.policy_cards.human_oversight as ho_module


def _default_dict() -> dict:
    return human_oversight_policy_card_to_canonical_dict(
        create_default_human_oversight_policy_card()
    )


def _mapping(data: dict, tier: str) -> dict:
    for item in data["risk_tier_mappings"]:
        if item["risk_tier"] == tier:
            return item
    raise AssertionError(f"tier mapping not found: {tier}")


def _remove_mapping(data: dict, tier: str) -> None:
    data["risk_tier_mappings"] = [
        item for item in data["risk_tier_mappings"] if item["risk_tier"] != tier
    ]


def _messages(result) -> str:
    return " ".join(error.message for error in result.errors)


# ---------------------------------------------------------------------------
# 17.1 Default Human Oversight Policy Card Valid
# ---------------------------------------------------------------------------


def test_default_human_oversight_policy_card_valid():
    card = create_default_human_oversight_policy_card()
    assert isinstance(card, HumanOversightPolicyCard)
    result = validate_human_oversight_policy_card(card)
    assert result.valid
    assert result.errors == ()
    assert isinstance(result.canonical_hash, str)
    assert len(result.canonical_hash) == 64


# ---------------------------------------------------------------------------
# 17.2 Required Risk Tier Mappings Exist
# ---------------------------------------------------------------------------


def test_required_tier_mappings_exist_in_default_card():
    card = create_default_human_oversight_policy_card()
    tiers = {mapping.risk_tier for mapping in card.risk_tier_mappings}
    assert tiers == set(REQUIRED_HUMAN_OVERSIGHT_RISK_TIERS)
    assert {tier.value for tier in tiers} == {"R0", "R1", "R2", "R3", "R4", "R5", "R6"}


# ---------------------------------------------------------------------------
# 17.3 Invalid Risk Tier Rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("invalid_tier", ["R9", "SUPER_ADMIN_RISK", "UNBOUNDED"])
def test_invalid_tier_rejected(invalid_tier: str):
    data = _default_dict()
    _mapping(data, "R2")["risk_tier"] = invalid_tier
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert invalid_tier in _messages(result)
    with pytest.raises(HumanOversightPolicyCardValidationError, match=invalid_tier):
        load_human_oversight_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 17.4 Missing Required Mapping Rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_tier", ["R5", "R6"])
def test_missing_required_mapping_rejected(missing_tier: str):
    data = _default_dict()
    _remove_mapping(data, missing_tier)
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert missing_tier in _messages(result)


# ---------------------------------------------------------------------------
# 17.5 Duplicate Mapping Rejected
# ---------------------------------------------------------------------------


def test_duplicate_mapping_rejected():
    data = _default_dict()
    data["risk_tier_mappings"].append(dict(_mapping(data, "R3")))
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "duplicate" in _messages(result).lower()


# ---------------------------------------------------------------------------
# 17.6 R4 Requires Approval Or Stricter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_level", ["none", "notify_only", "review_recommended"])
def test_r4_requires_approval_or_stricter_level(bad_level: str):
    data = _default_dict()
    _mapping(data, "R4")["oversight_level"] = bad_level
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R4" in _messages(result)


@pytest.mark.parametrize("bad_action", ["notify_operator", "request_review"])
def test_r4_requires_approval_or_stricter_action(bad_action: str):
    data = _default_dict()
    _mapping(data, "R4")["action"] = bad_action
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R4" in _messages(result)


def test_r4_accepts_approval_required():
    data = _default_dict()
    _mapping(data, "R4")["oversight_level"] = "approval_required"
    _mapping(data, "R4")["oversight_mode"] = "approval"
    _mapping(data, "R4")["action"] = "request_approval"
    card = load_human_oversight_policy_card_from_dict(data)
    assert validate_human_oversight_policy_card(card).valid


# ---------------------------------------------------------------------------
# 17.7 R5 Requires Explicit Confirmation
# ---------------------------------------------------------------------------


def test_r5_requires_explicit_confirmation():
    data = _default_dict()
    _mapping(data, "R5")["oversight_level"] = "approval_required"
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)
    assert "explicit_confirmation" in _messages(result)


def test_r5_requires_explicit_confirmation_action():
    data = _default_dict()
    _mapping(data, "R5")["action"] = "request_approval"
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)


def test_r5_requires_explicit_confirmation_mode():
    data = _default_dict()
    _mapping(data, "R5")["oversight_mode"] = "approval"
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)


# ---------------------------------------------------------------------------
# 17.8 R5 Requires Strong Confirmation Requirement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field_name", [
    "requires_explicit_confirmation",
    "preview_required",
    "evidence_required",
    "operator_identity_required",
])
def test_r5_requires_strong_confirmation_fields(field_name: str):
    data = _default_dict()
    r5 = _mapping(data, "R5")
    r5["confirmation_requirement"][field_name] = False
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)


def test_r5_missing_confirmation_requirement():
    data = _default_dict()
    _mapping(data, "R5")["confirmation_requirement"] = {
        "requires_explicit_confirmation": False,
        "confirmation_phrase_required": False,
        "preview_required": False,
        "shadow_diff_required": False,
        "reason_required": False,
        "evidence_required": False,
        "operator_identity_required": False,
    }
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)


def test_r5_missing_reviewer_requirement():
    data = _default_dict()
    _mapping(data, "R5")["reviewer_requirement"] = {
        "operator_required": False,
    }
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R5" in _messages(result)


# ---------------------------------------------------------------------------
# 17.9 R6 Must Deny
# ---------------------------------------------------------------------------


def test_r6_must_deny():
    card = create_default_human_oversight_policy_card()
    r6 = next(m for m in card.risk_tier_mappings if m.risk_tier == RiskTier.R6)
    assert r6.oversight_level == HumanOversightLevel.DENY
    assert r6.oversight_mode == HumanOversightMode.DENY
    assert r6.action == HumanOversightAction.DENY_ACTION
    assert validate_human_oversight_policy_card(card).valid


@pytest.mark.parametrize("bad_level", ["none", "notify_only", "approval_required"])
def test_r6_cannot_be_non_deny_level(bad_level: str):
    data = _default_dict()
    _mapping(data, "R6")["oversight_level"] = bad_level
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R6" in _messages(result)


def test_r6_cannot_be_non_deny_action():
    data = _default_dict()
    _mapping(data, "R6")["action"] = "request_approval"
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R6" in _messages(result)


# ---------------------------------------------------------------------------
# 17.10 R6 Cannot Be Approvable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_level", [
    "approval_required",
    "explicit_confirmation_required",
    "dual_review_required",
    "governance_board_required",
    "notify_only",
    "review_recommended",
])
def test_r6_cannot_be_approvable(bad_level: str):
    data = _default_dict()
    _mapping(data, "R6")["oversight_level"] = bad_level
    # Also fix mode/action to match the bad_level
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "R6" in _messages(result)


# ---------------------------------------------------------------------------
# 17.11 Invalid Oversight Level Rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_level", [
    "silent_approval",
    "auto_confirm",
    "super_admin_override",
])
def test_invalid_oversight_level_rejected(bad_level: str):
    data = _default_dict()
    _mapping(data, "R0")["oversight_level"] = bad_level
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    with pytest.raises(HumanOversightPolicyCardValidationError):
        load_human_oversight_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 17.12 Invalid Oversight Mode Rejected
# ---------------------------------------------------------------------------


def test_invalid_oversight_mode_rejected():
    data = _default_dict()
    _mapping(data, "R1")["oversight_mode"] = "magic_mode"
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    with pytest.raises(HumanOversightPolicyCardValidationError):
        load_human_oversight_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 17.13 Invalid Trigger/Action Rejected
# ---------------------------------------------------------------------------


def test_invalid_escalation_trigger_rejected():
    data = _default_dict()
    data["escalation_rules"] = [{
        "trigger": "super_trigger",
        "action": "notify_operator",
        "description": "test",
    }]
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    with pytest.raises(HumanOversightPolicyCardValidationError):
        load_human_oversight_policy_card_from_dict(data)


def test_invalid_escalation_action_rejected():
    data = _default_dict()
    data["escalation_rules"] = [{
        "trigger": "risk_tier_at_or_above",
        "action": "magic_action",
        "description": "test",
    }]
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid


def test_valid_escalation_rule_accepted():
    data = _default_dict()
    data["escalation_rules"] = [{
        "trigger": "risk_tier_at_or_above",
        "action": "request_approval",
        "minimum_risk_tier": "R4",
        "description": "valid rule",
    }]
    card = load_human_oversight_policy_card_from_dict(data)
    assert len(card.escalation_rules) == 1
    assert validate_human_oversight_policy_card(card).valid


# ---------------------------------------------------------------------------
# 17.14 Dangerous Metadata Rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_key", [
    "operator_not_required",
    "auto_approve",
    "skip_approval",
    "skip_confirmation",
    "bypass_policy",
    "bypass_oversight",
    "silent_approval",
    "approval_grant",
])
def test_dangerous_metadata_rejected(bad_key: str):
    data = _default_dict()
    data["metadata"] = {bad_key: True}
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert bad_key in _messages(result)
    with pytest.raises(HumanOversightPolicyCardUnsafeFieldError, match=bad_key):
        load_human_oversight_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 17.15 Safe Metadata Accepted
# ---------------------------------------------------------------------------


def test_safe_metadata_accepted():
    data = _default_dict()
    data["metadata"] = {"owner_note": "default oversight policy"}
    card = load_human_oversight_policy_card_from_dict(data)
    assert card.metadata == {"owner_note": "default oversight policy"}
    assert validate_human_oversight_policy_card(card).valid


# ---------------------------------------------------------------------------
# 17.16 PolicyCard Compatibility
# ---------------------------------------------------------------------------


def test_policy_card_compatibility_requires_human_oversight_kind():
    card = create_default_human_oversight_policy_card()
    assert card.policy_card.kind == PolicyCardKind.HUMAN_OVERSIGHT
    data = _default_dict()
    data["policy_card"]["kind"] = "risk_tier"
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "human_oversight" in _messages(result)


# ---------------------------------------------------------------------------
# 17.17 Closed-World Unknown Field Rejected
# ---------------------------------------------------------------------------


def test_closed_world_unknown_top_level_field_rejected():
    data = _default_dict()
    data["approval_backdoor"] = True
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "approval_backdoor" in _messages(result)
    with pytest.raises(HumanOversightPolicyCardUnknownFieldError, match="approval_backdoor"):
        load_human_oversight_policy_card_from_dict(data)


def test_closed_world_unknown_nested_field_rejected():
    data = _default_dict()
    _mapping(data, "R0")["future_resolver_hint"] = True
    result = validate_human_oversight_policy_card_dict(data)
    assert not result.valid
    assert "future_resolver_hint" in _messages(result)


# ---------------------------------------------------------------------------
# 17.18 Deterministic Serialization
# ---------------------------------------------------------------------------


def test_deterministic_serialization():
    card_a = create_default_human_oversight_policy_card()
    card_b = load_human_oversight_policy_card_from_dict(_default_dict())
    assert serialize_human_oversight_policy_card_canonical(card_a) == (
        serialize_human_oversight_policy_card_canonical(card_b)
    )
    parsed = json.loads(serialize_human_oversight_policy_card_canonical(card_a))
    assert parsed["schema_version"] == "1.0"
    assert parsed["policy_card"]["kind"] == "human_oversight"


# ---------------------------------------------------------------------------
# 17.19 Hash Stability
# ---------------------------------------------------------------------------


def test_hash_stability():
    card_a = create_default_human_oversight_policy_card()
    card_b = load_human_oversight_policy_card_from_dict(_default_dict())
    assert compute_human_oversight_policy_card_hash(card_a) == (
        compute_human_oversight_policy_card_hash(card_b)
    )


# ---------------------------------------------------------------------------
# 17.20 Schema Export Deterministic
# ---------------------------------------------------------------------------


def test_schema_export_deterministic():
    schema_a = export_human_oversight_policy_schema()
    schema_b = get_human_oversight_policy_schema()
    assert schema_a == schema_b
    assert json.dumps(schema_a, sort_keys=True) == json.dumps(schema_b, sort_keys=True)
    assert schema_a["schema_version"] == "1.0"
    assert schema_a["required_tiers"] == ["R0", "R1", "R2", "R3", "R4", "R5", "R6"]


def test_schema_version_helpers():
    assert HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSION == "1.0"
    assert SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS == ("1.0",)
    assert is_supported_human_oversight_policy_schema_version("1.0")
    assert not is_supported_human_oversight_policy_schema_version("2.0")
    assert validate_human_oversight_policy_schema_version("1.0").valid
    assert not validate_human_oversight_policy_schema_version("2.0").valid


# ---------------------------------------------------------------------------
# 17.21 Existing P1.6.0-P1.6.3 Tests Still Pass (sanity check from this file)
# ---------------------------------------------------------------------------


def test_default_schema_constants_are_model_objects():
    assert len(DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS) == 7
    assert all(isinstance(m, RiskTierOversightMapping)
               for m in DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS)
    assert DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES
    assert all(isinstance(r, HumanOversightEscalationRule)
               for r in DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES)
    assert any(
        m.risk_tier == RiskTier.R5
        and m.oversight_level == HumanOversightLevel.EXPLICIT_CONFIRMATION_REQUIRED
        for m in DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS
    )


# ---------------------------------------------------------------------------
# 17.22 No Runtime Approval Flow
# ---------------------------------------------------------------------------


def test_no_runtime_approval_engine_implemented():
    forbidden_api_names = {
        "resolve_oversight_policy",
        "enforce_oversight_policy",
        "approve_action",
        "confirm_action",
        "pause_workflow_for_approval",
        "execute_approval_workflow",
        "simulate_oversight",
        "write_oversight_trace_hook",
    }
    for name in forbidden_api_names:
        assert not hasattr(ho_module, name), f"Should not have {name}"


# ---------------------------------------------------------------------------
# Additional edge case tests
# ---------------------------------------------------------------------------


def test_enhanced_confirmation_requirement_with_expiry():
    cr = ConfirmationRequirement(
        requires_explicit_confirmation=True,
        confirmation_phrase_required=True,
        preview_required=True,
        expires_after_seconds=300,
    )
    assert cr.requires_explicit_confirmation
    assert cr.expires_after_seconds == 300


def test_confirmation_requirement_rejects_negative_expiry():
    with pytest.raises(HumanOversightPolicyCardValidationError, match="expires_after_seconds"):
        ConfirmationRequirement(
            requires_explicit_confirmation=True,
            expires_after_seconds=-1,
        )


def test_reviewer_requirement_accepts_role():
    rr = ReviewerRequirement(
        operator_required=True,
        required_reviewer_role="security_officer",
    )
    assert rr.required_reviewer_role == "security_officer"
    assert rr.operator_required


def test_default_card_has_seven_mappings():
    card = create_default_human_oversight_policy_card()
    assert len(card.risk_tier_mappings) == 7


def test_r1_none_oversight_level_accepted():
    data = _default_dict()
    _mapping(data, "R1")["oversight_level"] = "none"
    _mapping(data, "R1")["oversight_mode"] = "none"
    _mapping(data, "R1")["action"] = "notify_operator"
    card = load_human_oversight_policy_card_from_dict(data)
    assert validate_human_oversight_policy_card(card).valid


def test_dangerous_top_level_field_in_load():
    data = _default_dict()
    data["auto_approve"] = True
    with pytest.raises(HumanOversightPolicyCardUnsafeFieldError, match="auto_approve"):
        load_human_oversight_policy_card_from_dict(data)


def test_unknown_schema_version_rejected():
    data = _default_dict()
    data["schema_version"] = "999.0"
    with pytest.raises(HumanOversightPolicyCardValidationError):
        load_human_oversight_policy_card_from_dict(data)


def test_missing_schema_version_rejected():
    data = _default_dict()
    del data["schema_version"]
    with pytest.raises(HumanOversightPolicyCardValidationError, match="schema_version"):
        load_human_oversight_policy_card_from_dict(data)


def test_post_init_rejects_invalid_bool():
    with pytest.raises(HumanOversightPolicyCardValidationError):
        ConfirmationRequirement(requires_explicit_confirmation="yes")  # type: ignore[arg-type]

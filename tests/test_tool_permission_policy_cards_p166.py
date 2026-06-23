"""Unit tests for Tool Permission Policy Card model (P1.6.6).

Covers 21 test categories:
  1. Default card validity
  2. Default decision is deny
  3. Unknown tool category denied
  4. Credential access denied
  5. External API / network egress not open
  6. Shell command requires governance
  7. Execute/delete/config-write requires governance
  8. Data residency compatibility (protected classes)
  9. Invalid tool category rejected
  10. Invalid permission type rejected
  11. Invalid permission decision rejected
  12. Broad allow-all rejected
  13. Dangerous metadata rejected
  14. Safe metadata accepted
  15. PolicyCard compatibility
  16. Closed-world unknown field rejected
  17. Deterministic serialization
  18. Hash stability
  19. Schema export deterministic
  20. No runtime enforcement
  21. Existing P1.6 tests still pass
"""
from __future__ import annotations

from copy import deepcopy

import pytest as pytest

from src.agentic_runtime.policy_cards.tool_permissions import (
    ToolCategory,
    ToolIdentityMatcher,
    ToolMatchMode,
    ToolPermissionCondition,
    ToolPermissionDecision,
    ToolPermissionPolicyCard,
    ToolPermissionRule,
    ToolPermissionType,
    ToolPermissionValidationIssue,
    ToolPermissionValidationResult,
    ToolScopeType,
    compute_tool_permission_policy_card_hash,
    create_default_tool_permission_policy_card,
    load_tool_permission_policy_card_from_dict,
    serialize_tool_permission_policy_card_canonical,
    tool_permission_policy_card_to_canonical_dict,
    validate_tool_permission_policy_card,
    validate_tool_permission_policy_card_dict,
)
from src.agentic_runtime.policy_cards.tool_permission_schema import (
    TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSION,
    export_tool_permission_policy_schema,
    get_tool_permission_policy_schema,
    is_supported_tool_permission_policy_schema_version,
    validate_tool_permission_policy_schema_version,
)
from src.agentic_runtime.policy_cards.errors import (
    ToolPermissionPolicyCardError,
    ToolPermissionPolicyCardUnsafeFieldError,
    ToolPermissionPolicyCardUnknownFieldError,
    ToolPermissionPolicyCardValidationError,
    PolicyCardError,
)
from src.agentic_runtime.policy_cards.models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)


# ───────────────────────── Helpers ─────────────────────────


def _make_default_card() -> ToolPermissionPolicyCard:
    return create_default_tool_permission_policy_card()


def _to_dict(card: ToolPermissionPolicyCard) -> dict:
    from src.agentic_runtime.policy_cards.serialization import (
        policy_card_to_canonical_dict,
    )

    return {
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
        "permission_rules": [
            {
                "matcher": {
                    "match_mode": r.matcher.match_mode.value,
                    "tool_name": r.matcher.tool_name,
                    "tool_id": r.matcher.tool_id,
                    "tool_category": r.matcher.tool_category.value if r.matcher.tool_category else None,
                    "provider": r.matcher.provider,
                    "namespace": r.matcher.namespace,
                },
                "permission_type": r.permission_type.value,
                "decision": r.decision.value,
                "risk_ceiling": r.risk_ceiling,
                "required_oversight": r.required_oversight,
                "allowed_data_classes": list(r.allowed_data_classes),
                "forbidden_data_classes": list(r.forbidden_data_classes),
                "allowed_scopes": [s.value for s in r.allowed_scopes],
                "conditions": [
                    {
                        "condition_type": c.condition_type,
                        "value": c.value,
                        "description": c.description,
                    }
                    for c in r.conditions
                ],
                "sandbox_required": r.sandbox_required,
                "trace_required": r.trace_required,
                "evidence_required": r.evidence_required,
                "description": r.description,
            }
            for r in card.permission_rules
        ],
        "default_decision": card.default_decision.value,
        "metadata": dict(card.metadata),
    }


# ───────────────────────── 1. Default card validity ─────────────────────────


def test_default_card_is_valid():
    card = _make_default_card()
    result = validate_tool_permission_policy_card(card)
    assert result.valid, f"unexpected errors: {result.errors}"
    assert card.schema_version == TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSION
    assert card.default_decision == ToolPermissionDecision.DENY
    assert card.policy_card.kind == PolicyCardKind.TOOL_PERMISSION


# ───────────────────────── 2. Default decision is deny ─────────────────────────


def test_default_decision_is_deny():
    card = _make_default_card()
    assert card.default_decision == ToolPermissionDecision.DENY


def test_allow_default_decision_rejected():
    data = _to_dict(_make_default_card())
    data["default_decision"] = "allow"
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 3. Unknown tool category denied ─────────────────────────


def test_unknown_tool_category_denied():
    data = _to_dict(_make_default_card())
    for rule in data["permission_rules"]:
        if rule["matcher"].get("tool_category") == "unknown":
            rule["decision"] = "allow"
            break
    else:
        # Add a new unknown+allow rule
        data["permission_rules"].append({
            "matcher": {
                "match_mode": "category",
                "tool_category": "unknown",
            },
            "permission_type": "read",
            "decision": "allow",
            "description": "bad unknown allow",
        })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 4. Credential access denied ─────────────────────────


def test_credential_access_denied():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "shell",
        },
        "permission_type": "credential_access",
        "decision": "allow",
        "description": "should be rejected",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 5. External API / network egress not open ─────────────────────────


def test_network_simple_allow_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "network",
        },
        "permission_type": "network",
        "decision": "allow",
        "description": "bad network allow",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


def test_external_egress_simple_allow_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "network",
        },
        "permission_type": "external_egress",
        "decision": "allow",
        "description": "bad egress allow",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 6. Shell command requires governance ─────────────────────────


def test_shell_command_simple_allow_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "shell",
        },
        "permission_type": "shell_command",
        "decision": "allow",
        "sandbox_required": False,
        "description": "bad simple shell allow",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


def test_shell_command_with_sandbox_passes():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "shell",
        },
        "permission_type": "shell_command",
        "decision": "sandbox_required",
        "sandbox_required": True,
        "trace_required": True,
        "risk_ceiling": "R3",
        "description": "shell with sandbox",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert result.valid, f"unexpected errors: {result.errors}"


# ───────────────────────── 7. Execute/delete/config-write requires governance ─────────────────────────


def test_delete_simple_allow_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "filesystem",
        },
        "permission_type": "delete",
        "decision": "allow",
        "description": "bad delete allow",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


def test_config_write_simple_allow_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "internal_runtime",
        },
        "permission_type": "configuration_write",
        "decision": "allow",
        "description": "bad config write allow",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 8. Data residency compatibility ─────────────────────────


def test_credentials_exposed_externally_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "external_api",
        },
        "permission_type": "external_egress",
        "decision": "approval_required",
        "allowed_data_classes": ["credentials"],
        "forbidden_data_classes": [],
        "description": "exposing credentials",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


def test_sensitive_personal_data_exposed_rejected():
    data = _to_dict(_make_default_card())
    rule = {
        "matcher": {
            "match_mode": "category",
            "tool_category": "external_api",
        },
        "permission_type": "model_call",
        "decision": "allow",
        "allowed_data_classes": ["sensitive_personal_data"],
        "forbidden_data_classes": [],
        "description": "exposing spd",
    }
    data["permission_rules"].append(rule)
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 9. Invalid tool category rejected ─────────────────────────


def test_invalid_tool_category_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "nonexistent_category",
        },
        "permission_type": "read",
        "decision": "deny",
        "description": "bad category",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 10. Invalid permission type rejected ─────────────────────────


def test_invalid_permission_type_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "filesystem",
        },
        "permission_type": "nonexistent_perm_type",
        "decision": "deny",
        "description": "bad perm type",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 11. Invalid permission decision rejected ─────────────────────────


def test_invalid_permission_decision_rejected():
    data = _to_dict(_make_default_card())
    data["permission_rules"].append({
        "matcher": {
            "match_mode": "category",
            "tool_category": "filesystem",
        },
        "permission_type": "read",
        "decision": "nonexistent_decision",
        "description": "bad decision",
    })
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 12. Broad allow-all rejected ─────────────────────────


def test_broad_allow_all_rejected():
    # Use load + validate directly to get specific error codes
    from src.agentic_runtime.policy_cards.tool_permissions import (
        ToolIdentityMatcher,
        ToolMatchMode,
        ToolPermissionRule,
        ToolPermissionType,
        ToolPermissionDecision,
    )
    card = _make_default_card()
    bad_rule = ToolPermissionRule(
        matcher=ToolIdentityMatcher(match_mode=ToolMatchMode.CATEGORY),
        permission_type=ToolPermissionType.READ,
        decision=ToolPermissionDecision.ALLOW,
        description="broad allow-all",
    )
    from dataclasses import replace
    bad_card = replace(card, permission_rules=card.permission_rules + (bad_rule,))
    result = validate_tool_permission_policy_card(bad_card)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "BROAD_ALLOW_ALL_MATCHER" in error_codes


# ───────────────────────── 13. Dangerous metadata rejected ─────────────────────────


def test_allow_all_tools_metadata_rejected():
    data = _to_dict(_make_default_card())
    data["metadata"]["allow_all_tools"] = True
    with pytest.raises(ToolPermissionPolicyCardUnsafeFieldError):
        load_tool_permission_policy_card_from_dict(data)


def test_bypass_tool_policy_metadata_rejected():
    data = _to_dict(_make_default_card())
    data["metadata"]["bypass_tool_policy"] = True
    with pytest.raises(ToolPermissionPolicyCardUnsafeFieldError):
        load_tool_permission_policy_card_from_dict(data)


def test_shell_unrestricted_metadata_rejected():
    data = _to_dict(_make_default_card())
    data["metadata"]["shell_unrestricted"] = True
    with pytest.raises(ToolPermissionPolicyCardUnsafeFieldError):
        load_tool_permission_policy_card_from_dict(data)


def test_operator_not_required_metadata_rejected():
    data = _to_dict(_make_default_card())
    data["metadata"]["operator_not_required"] = True
    with pytest.raises(ToolPermissionPolicyCardUnsafeFieldError):
        load_tool_permission_policy_card_from_dict(data)


# ───────────────────────── 14. Safe metadata accepted ─────────────────────────


def test_safe_metadata_accepted():
    data = _to_dict(_make_default_card())
    data["metadata"]["owner_note"] = "test note"
    data["metadata"]["created_by"] = "test suite"
    card = load_tool_permission_policy_card_from_dict(data)
    assert "owner_note" in card.metadata
    assert "created_by" in card.metadata


# ───────────────────────── 15. PolicyCard compatibility ─────────────────────────


def test_wrong_policy_card_kind_rejected():
    data = _to_dict(_make_default_card())
    data["policy_card"]["kind"] = "risk_tier"
    result = validate_tool_permission_policy_card_dict(data)
    assert not result.valid


def test_correct_policy_card_kind_accepted():
    card = _make_default_card()
    assert card.policy_card.kind == PolicyCardKind.TOOL_PERMISSION


# ───────────────────────── 16. Closed-world unknown field rejected ─────────────────────────


def test_unknown_top_level_field_rejected():
    data = _to_dict(_make_default_card())
    data["tool_override_backdoor"] = True
    with pytest.raises(ToolPermissionPolicyCardUnsafeFieldError):
        load_tool_permission_policy_card_from_dict(data)


def test_truly_unknown_field_rejected():
    data = _to_dict(_make_default_card())
    data["nonexistent_field"] = True
    with pytest.raises(ToolPermissionPolicyCardUnknownFieldError):
        load_tool_permission_policy_card_from_dict(data)


# ───────────────────────── 17. Deterministic serialization ─────────────────────────


def test_serialization_deterministic():
    card1 = _make_default_card()
    card2 = _make_default_card()
    s1 = serialize_tool_permission_policy_card_canonical(card1)
    s2 = serialize_tool_permission_policy_card_canonical(card2)
    assert s1 == s2


def test_serialization_produces_valid_json():
    card = _make_default_card()
    s = serialize_tool_permission_policy_card_canonical(card)
    import json

    parsed = json.loads(s)
    assert isinstance(parsed, dict)


# ───────────────────────── 18. Hash stability ─────────────────────────


def test_hash_stable():
    card1 = _make_default_card()
    card2 = _make_default_card()
    h1 = compute_tool_permission_policy_card_hash(card1)
    h2 = compute_tool_permission_policy_card_hash(card2)
    assert h1 == h2
    assert len(h1) == 64


def test_hash_changes_with_metadata():
    data = _to_dict(_make_default_card())
    data["metadata"]["test_key"] = "value"
    card2 = load_tool_permission_policy_card_from_dict(data)
    assert compute_tool_permission_policy_card_hash(_make_default_card()) != compute_tool_permission_policy_card_hash(card2)


# ───────────────────────── 19. Schema export deterministic ─────────────────────────


def test_schema_export_has_required_keys():
    schema = export_tool_permission_policy_schema()
    for key in (
        "schema_version",
        "supported_versions",
        "required_fields",
        "optional_fields",
        "forbidden_fields",
        "canonical_fields",
        "rule_required_fields",
        "dangerous_field_names",
        "dangerous_metadata_keys",
        "dangerous_permission_types",
        "high_risk_permission_types",
        "default_deny_categories",
    ):
        assert key in schema, f"missing key: {key}"


def test_is_supported_schema_version():
    assert is_supported_tool_permission_policy_schema_version("1.0")
    assert not is_supported_tool_permission_policy_schema_version("0.9")
    assert not is_supported_tool_permission_policy_schema_version("")
    assert not is_supported_tool_permission_policy_schema_version(None)  # type: ignore[arg-type]


def test_validate_schema_version():
    result = validate_tool_permission_policy_schema_version("1.0")
    assert result.valid
    result = validate_tool_permission_policy_schema_version("2.0")
    assert not result.valid
    assert any(e.code == "UNSUPPORTED_SCHEMA_VERSION" for e in result.errors)


def test_get_schema_same_as_export():
    assert get_tool_permission_policy_schema() == export_tool_permission_policy_schema()


# ───────────────────────── 20. No runtime enforcement ─────────────────────────


def test_no_runtime_methods_on_card():
    card = _make_default_card()
    forbidden_attrs = {
        "enforce", "resolve", "execute", "block_network",
        "run_sandbox", "check_permission", "apply_policy",
        "gateway", "registry", "path_enforce",
    }
    for attr in forbidden_attrs:
        assert not hasattr(card, attr), f"card should not have {attr}"
        assert not callable(getattr(card, attr, None))


# ───────────────────────── Edge cases ─────────────────────────


def test_load_empty_dict_raises():
    with pytest.raises(ToolPermissionPolicyCardValidationError):
        load_tool_permission_policy_card_from_dict({})


def test_load_schema_version_invalid():
    data = _to_dict(_make_default_card())
    data["schema_version"] = "99.99"
    with pytest.raises(ToolPermissionPolicyCardValidationError):
        load_tool_permission_policy_card_from_dict(data)


def test_error_hierarchy():
    assert issubclass(ToolPermissionPolicyCardValidationError, ToolPermissionPolicyCardError)
    assert issubclass(ToolPermissionPolicyCardError, PolicyCardError)
    assert issubclass(ToolPermissionPolicyCardError, ValueError)

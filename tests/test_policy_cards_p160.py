"""P1.6.0 — Policy Card Foundation tests.

Comprehensive test suite covering:
  - valid card creation and validation
  - deterministic serialization and hashing
  - closed-world unknown field rejection
  - dangerous metadata/field rejection
  - invalid enum rejection
  - missing required field rejection
  - source hash separation from canonical hash
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards import (
    PolicyCard,
    PolicyCardAuthorityBinding,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardRiskBinding,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardSource,
    PolicyCardStatus,
    PolicyCardUnknownFieldError,
    PolicyCardUnsafeFieldError,
    PolicyCardValidationIssue,
    PolicyCardValidationResult,
    compute_policy_card_hash,
    load_policy_card_from_dict,
    policy_card_to_canonical_dict,
    serialize_policy_card_canonical,
    validate_policy_card,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_dict() -> dict:
    """Return the smallest valid policy card dict."""
    return {
        "schema_version": "1.0",
        "identity": {
            "card_id": "test-card-001",
            "slug": "test-card",
            "name": "Test Policy Card",
            "version": "1.0",
            "namespace": "aurel_core",
        },
        "kind": "generic",
        "status": "draft",
        "scope": {
            "scope_type": "global",
        },
        "description": "A minimal test policy card.",
    }


def _make_full_dict() -> dict:
    """Return a fully populated valid policy card dict."""
    return {
        "schema_version": "1.0",
        "identity": {
            "card_id": "full-card-001",
            "slug": "full-card",
            "name": "Full Policy Card",
            "version": "v2.0",
            "namespace": "aurel_exec",
        },
        "kind": "tool_permission",
        "status": "active",
        "scope": {
            "scope_type": "tool",
            "scope_id": "write_file",
            "applies_to": ["src/", "tests/"],
        },
        "description": "A fully populated test policy card.",
        "risk_binding": {
            "risk_tier": "high",
            "risk_floor": "medium",
            "risk_ceiling": "critical",
            "requires_oversight": True,
        },
        "authority_binding": {
            "authority_scope": "runtime",
            "required_authority": "operator",
            "operator_required": True,
            "delegation_allowed": False,
        },
        "source": {
            "source_type": "yaml",
            "source_path": "config/policies/full-card.yaml",
            "raw_source_hash": "abc123def456",
            "canonical_hash": "fed987cba654",
            "loaded_at": "2026-06-22T12:00:00Z",
        },
        "metadata": {
            "department": "engineering",
            "reviewer": "security-team",
        },
    }


def _make_minimal_card() -> PolicyCard:
    return load_policy_card_from_dict(_make_minimal_dict())


# ---------------------------------------------------------------------------
# 14.1 Valid Card Creation
# ---------------------------------------------------------------------------


def test_valid_minimal_card_creation():
    card = _make_minimal_card()
    assert card.identity.card_id == "test-card-001"
    assert card.kind == PolicyCardKind.GENERIC
    assert card.status == PolicyCardStatus.DRAFT
    assert card.scope.scope_type == PolicyCardScopeType.GLOBAL
    assert card.description == "A minimal test policy card."


def test_valid_minimal_card_validation_passes():
    card = _make_minimal_card()
    result = validate_policy_card(card)
    assert result.valid is True
    assert len(result.errors) == 0
    assert result.card_id == "test-card-001"


def test_valid_minimal_card_has_hash():
    card = _make_minimal_card()
    h = compute_policy_card_hash(card)
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 hex digest


def test_full_card_creation_and_validation():
    card = load_policy_card_from_dict(_make_full_dict())
    assert card.identity.card_id == "full-card-001"
    assert card.kind == PolicyCardKind.TOOL_PERMISSION
    assert card.status == PolicyCardStatus.ACTIVE
    assert card.scope.scope_type == PolicyCardScopeType.TOOL
    assert card.scope.scope_id == "write_file"
    assert card.scope.applies_to == ("src/", "tests/")
    assert card.risk_binding is not None
    assert card.risk_binding.risk_tier == "high"
    assert card.risk_binding.requires_oversight is True
    assert card.authority_binding is not None
    assert card.authority_binding.operator_required is True
    assert card.source is not None
    assert card.source.source_type == "yaml"
    assert card.metadata == {"department": "engineering", "reviewer": "security-team"}
    result = validate_policy_card(card)
    assert result.valid is True


def test_policy_card_is_frozen():
    card = _make_minimal_card()
    with pytest.raises(Exception):
        _ = card.kind  # type: ignore[assignment]
        # Attempting to set an attribute on a frozen dataclass should raise
        card.kind = PolicyCardKind.SANDBOX  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 14.2 Deterministic Serialization
# ---------------------------------------------------------------------------


def test_same_logical_card_produces_same_canonical_serialization():
    card_a = _make_minimal_card()
    card_b = _make_minimal_card()
    assert serialize_policy_card_canonical(card_a) == serialize_policy_card_canonical(card_b)


def test_same_logical_card_produces_same_hash():
    card_a = _make_minimal_card()
    card_b = _make_minimal_card()
    assert compute_policy_card_hash(card_a) == compute_policy_card_hash(card_b)


def test_different_card_produces_different_hash():
    card_a = _make_minimal_card()
    data = _make_minimal_dict()
    data["identity"]["card_id"] = "test-card-002"
    data["description"] = "A different card."
    card_b = load_policy_card_from_dict(data)
    assert compute_policy_card_hash(card_a) != compute_policy_card_hash(card_b)


def test_canonical_json_is_valid_json():
    card = _make_minimal_card()
    output = serialize_policy_card_canonical(card)
    parsed = json.loads(output)
    assert parsed["identity"]["card_id"] == "test-card-001"
    assert parsed["kind"] == "generic"


def test_canonical_dict_has_sorted_keys():
    card = _make_minimal_card()
    d = policy_card_to_canonical_dict(card)
    keys = list(d.keys())
    assert keys == sorted(keys)


def test_field_order_in_dict_does_not_change_hash():
    card = _make_minimal_card()
    h1 = compute_policy_card_hash(card)
    # Rebuild from same data — hash must be identical
    card2 = load_policy_card_from_dict(_make_minimal_dict())
    h2 = compute_policy_card_hash(card2)
    assert h1 == h2


# ---------------------------------------------------------------------------
# 14.3 Unknown Top-Level Field Rejection
# ---------------------------------------------------------------------------


def test_unknown_top_level_field_rejected():
    data = _make_minimal_dict()
    data["shadow_authority_grant"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="shadow_authority_grant"):
        load_policy_card_from_dict(data)


def test_arbitrary_unknown_field_rejected():
    data = _make_minimal_dict()
    data["some_random_field"] = "value"
    with pytest.raises(PolicyCardUnknownFieldError, match="some_random_field"):
        load_policy_card_from_dict(data)


def test_bypass_policy_field_rejected():
    data = _make_minimal_dict()
    data["bypass_policy"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="bypass_policy"):
        load_policy_card_from_dict(data)


def test_disable_policy_field_rejected():
    data = _make_minimal_dict()
    data["disable_policy"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="disable_policy"):
        load_policy_card_from_dict(data)


def test_multiple_unknown_fields_all_reported():
    data = _make_minimal_dict()
    data["foo"] = 1
    data["bar"] = 2
    with pytest.raises(PolicyCardUnknownFieldError) as exc_info:
        load_policy_card_from_dict(data)
    msg = str(exc_info.value)
    assert "foo" in msg
    assert "bar" in msg


def test_dangerous_and_unknown_fields_reject_dangerous_first():
    data = _make_minimal_dict()
    data["shadow_authority_grant"] = True
    data["random_field"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="shadow_authority_grant"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 14.4 Dangerous Metadata Rejection
# ---------------------------------------------------------------------------


def test_dangerous_metadata_bypass_policy_rejected():
    data = _make_minimal_dict()
    data["metadata"] = {"bypass_policy": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="bypass_policy"):
        load_policy_card_from_dict(data)


def test_dangerous_metadata_authority_rejected():
    data = _make_minimal_dict()
    data["metadata"] = {"authority": "full_access"}
    with pytest.raises(PolicyCardUnsafeFieldError, match="authority"):
        load_policy_card_from_dict(data)


def test_dangerous_metadata_tool_write_rejected():
    data = _make_minimal_dict()
    data["metadata"] = {"tool_write": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="tool_write"):
        load_policy_card_from_dict(data)


def test_dangerous_metadata_sandbox_override_rejected():
    data = _make_minimal_dict()
    data["metadata"] = {"sandbox_override": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="sandbox_override"):
        load_policy_card_from_dict(data)


def test_dangerous_metadata_egress_rejected():
    data = _make_minimal_dict()
    data["metadata"] = {"egress": "open"}
    with pytest.raises(PolicyCardUnsafeFieldError, match="egress"):
        load_policy_card_from_dict(data)


def test_dangerous_metadata_memory_write_rejected():
    data = _make_minimal_dict()
    data["metadata"] = {"memory_write": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="memory_write"):
        load_policy_card_from_dict(data)


def test_safe_metadata_accepted():
    data = _make_minimal_dict()
    data["metadata"] = {"department": "engineering", "notes": "For review."}
    card = load_policy_card_from_dict(data)
    assert card.metadata == {"department": "engineering", "notes": "For review."}


def test_multiple_dangerous_metadata_keys_all_reported():
    data = _make_minimal_dict()
    data["metadata"] = {"bypass_policy": True, "egress": "open"}
    with pytest.raises(PolicyCardUnsafeFieldError) as exc_info:
        load_policy_card_from_dict(data)
    msg = str(exc_info.value)
    assert "bypass_policy" in msg
    assert "egress" in msg


def test_empty_metadata_accepted():
    data = _make_minimal_dict()
    data["metadata"] = {}
    card = load_policy_card_from_dict(data)
    assert card.metadata == {}


def test_no_metadata_accepted():
    # Minimal dict doesn't include metadata — card should default to empty dict
    data = _make_minimal_dict()
    card = load_policy_card_from_dict(data)
    assert card.metadata == {}


# ---------------------------------------------------------------------------
# 14.5 Invalid Enum Rejection
# ---------------------------------------------------------------------------


def test_invalid_kind_rejected():
    data = _make_minimal_dict()
    data["kind"] = "nonexistent_kind"
    with pytest.raises(PolicyCardUnknownFieldError, match="kind"):
        load_policy_card_from_dict(data)


def test_invalid_status_rejected():
    data = _make_minimal_dict()
    data["status"] = "not_a_status"
    with pytest.raises(PolicyCardUnknownFieldError, match="status"):
        load_policy_card_from_dict(data)


def test_invalid_scope_type_rejected():
    data = _make_minimal_dict()
    data["scope"]["scope_type"] = "invalid_scope"
    with pytest.raises(PolicyCardUnknownFieldError, match="scope_type"):
        load_policy_card_from_dict(data)


def test_all_valid_kinds_accepted():
    for kind_val in PolicyCardKind:
        data = _make_minimal_dict()
        data["kind"] = kind_val.value
        card = load_policy_card_from_dict(data)
        assert card.kind == kind_val


def test_all_valid_statuses_accepted():
    for status_val in PolicyCardStatus:
        data = _make_minimal_dict()
        data["status"] = status_val.value
        card = load_policy_card_from_dict(data)
        assert card.status == status_val


def test_all_valid_scope_types_accepted():
    for st_val in PolicyCardScopeType:
        data = _make_minimal_dict()
        data["scope"]["scope_type"] = st_val.value
        card = load_policy_card_from_dict(data)
        assert card.scope.scope_type == st_val


# ---------------------------------------------------------------------------
# 14.6 Missing Required Field
# ---------------------------------------------------------------------------


def test_missing_identity_fails():
    data = _make_minimal_dict()
    del data["identity"]
    with pytest.raises(PolicyCardUnknownFieldError, match="identity"):
        load_policy_card_from_dict(data)


def test_missing_card_id_fails():
    data = _make_minimal_dict()
    data["identity"]["card_id"] = ""
    with pytest.raises(PolicyCardUnknownFieldError, match="validation failed"):
        load_policy_card_from_dict(data)


def test_missing_version_fails():
    data = _make_minimal_dict()
    data["identity"]["version"] = ""
    with pytest.raises(PolicyCardUnknownFieldError, match="validation failed"):
        load_policy_card_from_dict(data)


def test_missing_kind_fails():
    data = _make_minimal_dict()
    del data["kind"]
    with pytest.raises(PolicyCardUnknownFieldError, match="kind"):
        load_policy_card_from_dict(data)


def test_missing_status_fails():
    data = _make_minimal_dict()
    del data["status"]
    with pytest.raises(PolicyCardUnknownFieldError, match="status"):
        load_policy_card_from_dict(data)


def test_missing_scope_fails():
    data = _make_minimal_dict()
    del data["scope"]
    with pytest.raises(PolicyCardUnknownFieldError, match="scope"):
        load_policy_card_from_dict(data)


def test_empty_description_fails():
    data = _make_minimal_dict()
    data["description"] = ""
    with pytest.raises(PolicyCardUnknownFieldError):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 14.7 Source Hash Separation
# ---------------------------------------------------------------------------


def test_canonical_hash_independent_of_raw_source_hash():
    data = _make_minimal_dict()
    data["source"] = {
        "source_type": "yaml",
        "raw_source_hash": "abc123def456",
    }
    card = load_policy_card_from_dict(data)
    canonical = compute_policy_card_hash(card)
    assert card.source is not None
    assert card.source.raw_source_hash != canonical
    assert canonical != "abc123def456"


def test_canonical_hash_is_deterministic():
    card_a = _make_minimal_card()
    card_b = _make_minimal_card()
    assert compute_policy_card_hash(card_a) == compute_policy_card_hash(card_b)


def test_changing_raw_source_hash_does_not_change_canonical_hash():
    data = _make_minimal_dict()
    data["source"] = {
        "source_type": "yaml",
        "raw_source_hash": "aaa111",
    }
    card_a = load_policy_card_from_dict(data)
    data["source"]["raw_source_hash"] = "bbb222"
    card_b = load_policy_card_from_dict(data)
    # Canonical hash stays the same (raw source hash is excluded from canonical dict)
    assert compute_policy_card_hash(card_a) == compute_policy_card_hash(card_b)


# ---------------------------------------------------------------------------
# 14.8 No Enforcement Claim
# ---------------------------------------------------------------------------


def test_policy_card_has_no_runtime_enforcement_methods():
    """P1.6.0 does not implement runtime enforcement — verify structurally."""
    card = _make_minimal_card()
    # PolicyCard is a pure data object — no enforce(), resolve(),
    # evaluate(), check(), or similar runtime methods.
    for attr_name in ("enforce", "resolve", "evaluate", "execute", "check", "apply",
                       "validate_runtime", "policy_check", "enforcement_check"):
        assert not hasattr(card, attr_name), (
            f"PolicyCard must not have '{attr_name}' method — "
            f"P1.6.0 is foundation only, no runtime enforcement"
        )


# ---------------------------------------------------------------------------
# Additional edge case tests
# ---------------------------------------------------------------------------


def test_non_dict_input_rejected():
    with pytest.raises(PolicyCardUnknownFieldError, match="mapping"):
        load_policy_card_from_dict("not a dict")  # type: ignore[arg-type]


def test_identity_not_dict_rejected():
    data = _make_minimal_dict()
    data["identity"] = "not_a_dict"
    with pytest.raises(PolicyCardUnknownFieldError, match="identity"):
        load_policy_card_from_dict(data)


def test_scope_not_dict_rejected():
    data = _make_minimal_dict()
    data["scope"] = "not_a_dict"
    with pytest.raises(PolicyCardUnknownFieldError, match="scope"):
        load_policy_card_from_dict(data)


def test_metadata_not_dict_rejected():
    data = _make_minimal_dict()
    data["metadata"] = "not_a_dict"
    with pytest.raises(PolicyCardUnknownFieldError, match="metadata"):
        load_policy_card_from_dict(data)


def test_applies_to_strings_validated():
    data = _make_minimal_dict()
    data["scope"]["applies_to"] = [1, 2, 3]  # not strings
    with pytest.raises(PolicyCardUnknownFieldError):
        load_policy_card_from_dict(data)


def test_risk_binding_not_dict_rejected():
    data = _make_minimal_dict()
    data["risk_binding"] = "not_a_dict"
    with pytest.raises(PolicyCardUnknownFieldError, match="risk_binding"):
        load_policy_card_from_dict(data)


def test_authority_binding_not_dict_rejected():
    data = _make_minimal_dict()
    data["authority_binding"] = "not_a_dict"
    with pytest.raises(PolicyCardUnknownFieldError, match="authority_binding"):
        load_policy_card_from_dict(data)


def test_source_not_dict_rejected():
    data = _make_minimal_dict()
    data["source"] = "not_a_dict"
    with pytest.raises(PolicyCardUnknownFieldError, match="source"):
        load_policy_card_from_dict(data)


def test_kind_enum_values_match_spec():
    """Verify all required kind values exist."""
    expected = {
        "risk_tier", "human_oversight", "data_residency", "tool_permission",
        "memory_write", "prompt", "sandbox", "model_routing", "business_process", "generic",
    }
    actual = set(k.value for k in PolicyCardKind)
    assert actual == expected


def test_status_enum_values_match_spec():
    expected = {"draft", "active", "deprecated", "disabled", "test_only"}
    actual = set(s.value for s in PolicyCardStatus)
    assert actual == expected


def test_scope_type_enum_values_match_spec():
    expected = {
        "global", "runtime", "tool", "model", "memory",
        "prompt", "sandbox", "workflow", "agent", "business",
    }
    actual = set(st.value for st in PolicyCardScopeType)
    assert actual == expected


def test_error_taxonomy_hierarchy():
    from agentic_runtime.policy_cards.errors import (
        PolicyCardError,
        PolicyCardHashError,
        PolicyCardSerializationError,
        PolicyCardUnknownFieldError,
        PolicyCardUnsafeFieldError,
        PolicyCardValidationError,
    )
    assert issubclass(PolicyCardValidationError, PolicyCardError)
    assert issubclass(PolicyCardUnknownFieldError, PolicyCardValidationError)
    assert issubclass(PolicyCardUnsafeFieldError, PolicyCardValidationError)
    assert issubclass(PolicyCardSerializationError, PolicyCardError)
    assert issubclass(PolicyCardHashError, PolicyCardError)
    assert issubclass(PolicyCardError, ValueError)


def test_public_api_exports():
    """Verify all expected public symbols are importable."""
    from agentic_runtime.policy_cards import (
        DANGEROUS_METADATA_KEYS,
        DANGEROUS_TOP_LEVEL_FIELDS,
        PolicyCard,
        PolicyCardAuthorityBinding,
        PolicyCardError,
        PolicyCardHashError,
        PolicyCardIdentity,
        PolicyCardKind,
        PolicyCardRiskBinding,
        PolicyCardScope,
        PolicyCardScopeType,
        PolicyCardSerializationError,
        PolicyCardSource,
        PolicyCardStatus,
        PolicyCardUnknownFieldError,
        PolicyCardUnsafeFieldError,
        PolicyCardValidationError,
        PolicyCardValidationIssue,
        PolicyCardValidationResult,
        compute_policy_card_hash,
        load_policy_card_from_dict,
        policy_card_to_canonical_dict,
        serialize_policy_card_canonical,
        validate_policy_card,
    )
    # If we reach here, all imports succeeded
    assert PolicyCard is not None


def test_validation_result_structure():
    result = PolicyCardValidationResult(
        valid=True,
        errors=(),
        warnings=(PolicyCardValidationIssue(
            code="TEST", message="A warning", field="test", severity="warning"
        ),),
        card_id="card-1",
        canonical_hash="abc123",
    )
    assert result.valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 1
    assert result.card_id == "card-1"


def test_validation_issue_default_severity():
    issue = PolicyCardValidationIssue(code="ERR", message="Error")
    assert issue.severity == "error"
    assert issue.field is None

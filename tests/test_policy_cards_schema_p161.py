"""P1.6.1 — Policy Card Schema tests.

Comprehensive test suite covering:
  - schema version acceptance/rejection
  - required field presence
  - optional field acceptance
  - forbidden field rejection
  - unknown field rejection
  - runtime-future field rejection
  - dangerous metadata rejection
  - safe metadata acceptance
  - schema export determinism
  - canonical field stability
  - schema version validation helpers
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards import (
    POLICY_CARD_CANONICAL_FIELDS,
    POLICY_CARD_FORBIDDEN_FIELDS,
    POLICY_CARD_OPTIONAL_FIELDS,
    POLICY_CARD_REQUIRED_FIELDS,
    POLICY_CARD_SCHEMA_VERSION,
    SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS,
    PolicyCardUnknownFieldError,
    PolicyCardUnsafeFieldError,
    compute_policy_card_hash,
    export_policy_card_schema,
    get_policy_card_schema,
    is_supported_policy_card_schema_version,
    load_policy_card_from_dict,
    policy_card_to_canonical_dict,
    serialize_policy_card_canonical,
    validate_policy_card_schema_version,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_dict() -> dict:
    return {
        "schema_version": "1.0",
        "identity": {
            "card_id": "schema-test-001",
            "slug": "schema-test",
            "name": "Schema Test Card",
            "version": "1.0",
            "namespace": "aurel_core",
        },
        "kind": "generic",
        "status": "draft",
        "scope": {
            "scope_type": "global",
        },
        "description": "A schema test policy card.",
    }


# ---------------------------------------------------------------------------
# 13.1 Schema Version Accepted
# ---------------------------------------------------------------------------


def test_current_schema_version_1_0_accepted():
    data = _base_dict()
    data["schema_version"] = "1.0"
    card = load_policy_card_from_dict(data)
    assert card.schema_version == "1.0"


def test_schema_version_participates_in_canonical_hash():
    card = load_policy_card_from_dict(_base_dict())
    canonical = policy_card_to_canonical_dict(card)
    assert canonical["schema_version"] == "1.0"


# ---------------------------------------------------------------------------
# 13.2 Unsupported Schema Version Rejected
# ---------------------------------------------------------------------------


def test_unsupported_version_999_0_rejected():
    data = _base_dict()
    data["schema_version"] = "999.0"
    with pytest.raises(PolicyCardUnknownFieldError, match="999.0"):
        load_policy_card_from_dict(data)


def test_unsupported_version_0_0_rejected():
    data = _base_dict()
    data["schema_version"] = "0.0"
    with pytest.raises(PolicyCardUnknownFieldError, match="0.0"):
        load_policy_card_from_dict(data)


def test_unsupported_version_experimental_rejected():
    data = _base_dict()
    data["schema_version"] = "experimental"
    with pytest.raises(PolicyCardUnknownFieldError, match="experimental"):
        load_policy_card_from_dict(data)


def test_unsupported_version_unknown_rejected():
    data = _base_dict()
    data["schema_version"] = "unknown"
    with pytest.raises(PolicyCardUnknownFieldError, match="unknown"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 13.3 Missing Schema Version Behavior
# ---------------------------------------------------------------------------


def test_missing_schema_version_rejected():
    data = _base_dict()
    del data["schema_version"]
    with pytest.raises(PolicyCardUnknownFieldError, match="schema_version"):
        load_policy_card_from_dict(data)


def test_empty_schema_version_rejected():
    data = _base_dict()
    data["schema_version"] = ""
    with pytest.raises(PolicyCardUnknownFieldError, match="schema_version"):
        load_policy_card_from_dict(data)


def test_blank_schema_version_rejected():
    data = _base_dict()
    data["schema_version"] = "   "
    with pytest.raises(PolicyCardUnknownFieldError, match="schema_version"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 13.4 Required Fields Centralized
# ---------------------------------------------------------------------------


def test_required_fields_tuple_present_and_nonempty():
    assert isinstance(POLICY_CARD_REQUIRED_FIELDS, tuple)
    assert len(POLICY_CARD_REQUIRED_FIELDS) > 0


def test_schema_version_in_required_fields():
    assert "schema_version" in POLICY_CARD_REQUIRED_FIELDS


def test_missing_kind_fails_with_structured_error():
    data = _base_dict()
    del data["kind"]
    with pytest.raises(PolicyCardUnknownFieldError, match="kind"):
        load_policy_card_from_dict(data)


def test_missing_status_fails_with_structured_error():
    data = _base_dict()
    del data["status"]
    with pytest.raises(PolicyCardUnknownFieldError, match="status"):
        load_policy_card_from_dict(data)


def test_missing_scope_fails():
    data = _base_dict()
    del data["scope"]
    with pytest.raises(PolicyCardUnknownFieldError, match="scope"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 13.5 Optional Fields Accepted
# ---------------------------------------------------------------------------


def test_optional_risk_binding_accepted():
    data = _base_dict()
    data["risk_binding"] = {
        "risk_tier": "high",
        "requires_oversight": True,
    }
    card = load_policy_card_from_dict(data)
    assert card.risk_binding is not None
    assert card.risk_binding.risk_tier == "high"


def test_optional_authority_binding_accepted():
    data = _base_dict()
    data["authority_binding"] = {
        "authority_scope": "runtime",
        "operator_required": True,
    }
    card = load_policy_card_from_dict(data)
    assert card.authority_binding is not None
    assert card.authority_binding.operator_required is True


def test_optional_source_accepted():
    data = _base_dict()
    data["source"] = {
        "source_type": "yaml",
        "source_path": "config/policy.yaml",
    }
    card = load_policy_card_from_dict(data)
    assert card.source is not None
    assert card.source.source_type == "yaml"


def test_optional_metadata_accepted():
    data = _base_dict()
    data["metadata"] = {"owner_note": "test"}
    card = load_policy_card_from_dict(data)
    assert card.metadata == {"owner_note": "test"}


def test_all_optionals_together_accepted():
    data = _base_dict()
    data["risk_binding"] = {"risk_tier": "low"}
    data["authority_binding"] = {"authority_scope": "agent"}
    data["source"] = {"source_type": "inline"}
    data["metadata"] = {"audit": "pass"}
    card = load_policy_card_from_dict(data)
    assert card.risk_binding is not None
    assert card.authority_binding is not None
    assert card.source is not None
    assert card.metadata == {"audit": "pass"}


# ---------------------------------------------------------------------------
# 13.6 Forbidden Fields Rejected
# ---------------------------------------------------------------------------


def test_authority_grant_rejected():
    data = _base_dict()
    data["authority_grant"] = "admin"
    with pytest.raises(PolicyCardUnsafeFieldError, match="authority_grant"):
        load_policy_card_from_dict(data)


def test_policy_bypass_rejected():
    data = _base_dict()
    data["policy_bypass"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="policy_bypass"):
        load_policy_card_from_dict(data)


def test_grant_authority_rejected():
    data = _base_dict()
    data["grant_authority"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="grant_authority"):
        load_policy_card_from_dict(data)


def test_skip_trace_rejected():
    data = _base_dict()
    data["skip_trace"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="skip_trace"):
        load_policy_card_from_dict(data)


def test_unrestricted_rejected():
    data = _base_dict()
    data["unrestricted"] = True
    with pytest.raises(PolicyCardUnsafeFieldError, match="unrestricted"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 13.7 Unknown Fields Rejected
# ---------------------------------------------------------------------------


def test_random_field_rejected():
    data = _base_dict()
    data["some_random_future_control"] = True
    with pytest.raises(PolicyCardUnknownFieldError, match="some_random_future_control"):
        load_policy_card_from_dict(data)


def test_multiple_unknown_fields_all_reported():
    data = _base_dict()
    data["alpha"] = 1
    data["beta"] = 2
    with pytest.raises(PolicyCardUnknownFieldError) as exc_info:
        load_policy_card_from_dict(data)
    msg = str(exc_info.value)
    assert "alpha" in msg
    assert "beta" in msg


# ---------------------------------------------------------------------------
# 13.8 Dangerous Metadata Rejected
# ---------------------------------------------------------------------------


def test_metadata_operator_not_required_rejected():
    data = _base_dict()
    data["metadata"] = {"operator_not_required": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="operator_not_required"):
        load_policy_card_from_dict(data)


def test_metadata_evidence_bypass_rejected():
    data = _base_dict()
    data["metadata"] = {"evidence_bypass": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="evidence_bypass"):
        load_policy_card_from_dict(data)


def test_metadata_delegation_grant_rejected():
    data = _base_dict()
    data["metadata"] = {"delegation_grant": True}
    with pytest.raises(PolicyCardUnsafeFieldError, match="delegation_grant"):
        load_policy_card_from_dict(data)


def test_metadata_network_access_rejected():
    data = _base_dict()
    data["metadata"] = {"network_access": "open"}
    with pytest.raises(PolicyCardUnsafeFieldError, match="network_access"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# 13.9 Safe Metadata Accepted
# ---------------------------------------------------------------------------


def test_safe_metadata_owner_note_accepted():
    data = _base_dict()
    data["metadata"] = {"owner_note": "review later"}
    card = load_policy_card_from_dict(data)
    assert card.metadata == {"owner_note": "review later"}


def test_safe_metadata_source_reference_accepted():
    data = _base_dict()
    data["metadata"] = {"source_reference": "internal"}
    card = load_policy_card_from_dict(data)
    assert card.metadata == {"source_reference": "internal"}


def test_safe_metadata_review_hint_accepted():
    data = _base_dict()
    data["metadata"] = {"review_hint": "needs governance review later"}
    card = load_policy_card_from_dict(data)
    assert card.metadata == {"review_hint": "needs governance review later"}


# ---------------------------------------------------------------------------
# 13.10 Schema Export Deterministic
# ---------------------------------------------------------------------------


def test_schema_export_is_deterministic():
    export_a = export_policy_card_schema()
    export_b = export_policy_card_schema()
    assert export_a == export_b


def test_get_policy_card_schema_equals_export():
    assert get_policy_card_schema() == export_policy_card_schema()


def test_schema_export_contains_version():
    export = export_policy_card_schema()
    assert export["schema_version"] == "1.0"


def test_schema_export_contains_required_fields():
    export = export_policy_card_schema()
    assert "schema_version" in export["required_fields"]
    assert "identity" in export["required_fields"]
    assert "kind" in export["required_fields"]


def test_schema_export_contains_field_categories():
    export = export_policy_card_schema()
    categories = export["field_categories"]
    assert "control" in categories
    assert "governance" in categories
    assert "source" in categories
    assert "descriptive" in categories
    assert "identity" in categories
    assert "runtime_future" in categories
    assert "schema_version" in categories["control"]
    assert "risk_binding" in categories["governance"]


def test_schema_export_contains_dangerous_metadata_keys():
    export = export_policy_card_schema()
    dmk = export["dangerous_metadata_keys"]
    assert "authority" in dmk
    assert "bypass_policy" in dmk
    assert "evidence_bypass" in dmk


# ---------------------------------------------------------------------------
# 13.11 Canonical Fields Stable
# ---------------------------------------------------------------------------


def test_canonical_fields_tuple_present():
    assert isinstance(POLICY_CARD_CANONICAL_FIELDS, tuple)
    assert len(POLICY_CARD_CANONICAL_FIELDS) > 0
    assert "schema_version" in POLICY_CARD_CANONICAL_FIELDS


def test_same_card_same_schema_version_produces_same_hash():
    card_a = load_policy_card_from_dict(_base_dict())
    card_b = load_policy_card_from_dict(_base_dict())
    assert compute_policy_card_hash(card_a) == compute_policy_card_hash(card_b)


def test_different_card_different_hash():
    data_a = _base_dict()
    data_a["description"] = "Card A"
    data_b = _base_dict()
    data_b["description"] = "Card B"
    card_a = load_policy_card_from_dict(data_a)
    card_b = load_policy_card_from_dict(data_b)
    assert compute_policy_card_hash(card_a) != compute_policy_card_hash(card_b)


def test_same_card_same_json():
    card_a = load_policy_card_from_dict(_base_dict())
    card_b = load_policy_card_from_dict(_base_dict())
    assert serialize_policy_card_canonical(card_a) == serialize_policy_card_canonical(card_b)


# ---------------------------------------------------------------------------
# 13.12 Schema Version Helpers
# ---------------------------------------------------------------------------


def test_is_supported_returns_true_for_1_0():
    assert is_supported_policy_card_schema_version("1.0") is True


def test_is_supported_returns_false_for_999():
    assert is_supported_policy_card_schema_version("999.0") is False


def test_is_supported_returns_false_for_empty():
    assert is_supported_policy_card_schema_version("") is False


def test_validate_schema_version_1_0_passes():
    result = validate_policy_card_schema_version("1.0")
    assert result.valid is True
    assert len(result.errors) == 0


def test_validate_schema_version_999_fails():
    result = validate_policy_card_schema_version("999.0")
    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "UNSUPPORTED_SCHEMA_VERSION"


def test_validate_schema_version_empty_fails():
    result = validate_policy_card_schema_version("")
    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "MISSING_SCHEMA_VERSION"


def test_validate_schema_version_none_fails():
    result = validate_policy_card_schema_version(None)
    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "MISSING_SCHEMA_VERSION"


# ---------------------------------------------------------------------------
# Runtime-future field rejection
# ---------------------------------------------------------------------------


def test_runtime_future_resolver_rejected():
    data = _base_dict()
    data["resolver"] = "some_resolver"
    with pytest.raises(PolicyCardUnknownFieldError, match="resolver"):
        load_policy_card_from_dict(data)


def test_runtime_future_enforcement_rejected():
    data = _base_dict()
    data["enforcement"] = True
    with pytest.raises(PolicyCardUnknownFieldError, match="enforcement"):
        load_policy_card_from_dict(data)


def test_runtime_future_conditions_rejected():
    data = _base_dict()
    data["conditions"] = []
    with pytest.raises(PolicyCardUnknownFieldError, match="conditions"):
        load_policy_card_from_dict(data)


# ---------------------------------------------------------------------------
# Schema constants sanity
# ---------------------------------------------------------------------------


def test_schema_version_is_1_0():
    assert POLICY_CARD_SCHEMA_VERSION == "1.0"


def test_supported_versions_is_tuple():
    assert isinstance(SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS, tuple)


def test_supported_versions_contains_1_0():
    assert "1.0" in SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS


def test_optional_fields_is_tuple():
    assert isinstance(POLICY_CARD_OPTIONAL_FIELDS, tuple)


def test_forbidden_fields_is_frozenset():
    assert isinstance(POLICY_CARD_FORBIDDEN_FIELDS, frozenset)


def test_required_and_optional_are_disjoint():
    req = set(POLICY_CARD_REQUIRED_FIELDS)
    opt = set(POLICY_CARD_OPTIONAL_FIELDS)
    assert req.isdisjoint(opt)


def test_no_required_in_forbidden():
    assert set(POLICY_CARD_REQUIRED_FIELDS).isdisjoint(POLICY_CARD_FORBIDDEN_FIELDS)


def test_schema_export_is_valid_json():
    export = export_policy_card_schema()
    serialized = json.dumps(export, sort_keys=True)
    parsed = json.loads(serialized)
    assert parsed == export

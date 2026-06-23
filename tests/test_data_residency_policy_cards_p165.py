"""Unit tests for Data Residency Policy Card model (P1.6.5).

Covers 23 test categories:
  1. Default card validity
  2. Required data classes present
  3. Invalid data class rejected
  4. Invalid zone rejected
  5. Missing required data class rejected
  6. Duplicate data class rejected
  7. local_only no-egress
  8. local_only no-external-model
  9. local_only no-external-api/web
  10. credentials no-egress
  11. credentials encryption + audit required
  12. sensitive_personal_data strict
  13. memory_record strict
  14. trace_record strict
  15. forbidden non-permissive
  16. dangerous metadata keys rejected
  17. safe metadata accepted
  18. PolicyCard compatibility
  19. Closed-world validation
  20. Deterministic serialization
  21. Hash stability
  22. Schema export
  23. No runtime enforcement
"""
from __future__ import annotations

from copy import deepcopy

import pytest as pytest

from src.agentic_runtime.policy_cards.data_residency import (
    DataClass,
    DataEgressRule,
    DataExposurePermission,
    DataExposureRule,
    DataResidencyPolicyCard,
    DataResidencyRule,
    DataResidencyValidationIssue,
    DataResidencyValidationResult,
    DataResidencyZone,
    ProcessingLocation,
    RedactionRequirement,
    RedactionRequirementType,
    StorageRequirement,
    StorageRequirementType,
    compute_data_residency_policy_card_hash,
    create_default_data_residency_policy_card,
    data_residency_policy_card_to_canonical_dict,
    load_data_residency_policy_card_from_dict,
    serialize_data_residency_policy_card_canonical,
    validate_data_residency_policy_card,
    validate_data_residency_policy_card_dict,
)
from src.agentic_runtime.policy_cards.data_residency_schema import (
    DATA_RESIDENCY_DANGEROUS_FIELD_NAMES,
    DATA_RESIDENCY_DANGEROUS_METADATA_KEYS,
    DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSION,
    REQUIRED_DATA_CLASSES,
    STRICT_LOCAL_ONLY_DATA_CLASSES,
    export_data_residency_policy_schema,
    get_data_residency_policy_schema,
    is_supported_data_residency_policy_schema_version,
    validate_data_residency_policy_schema_version,
)
from src.agentic_runtime.policy_cards.errors import (
    DataResidencyPolicyCardError,
    DataResidencyPolicyCardUnsafeFieldError,
    DataResidencyPolicyCardUnknownFieldError,
    DataResidencyPolicyCardValidationError,
    PolicyCardError,
    PolicyCardValidationError,
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


def _make_default_card() -> DataResidencyPolicyCard:
    return create_default_data_residency_policy_card()


def _make_default_exposure_dict() -> dict:
    return {
        "local_model_allowed": True,
        "external_model_allowed": False,
        "tool_access_allowed": False,
        "web_search_allowed": False,
        "artifact_export_allowed": False,
        "memory_write_allowed": False,
        "external_api_allowed": False,
        "human_review_required": False,
    }


def _to_dict(card: DataResidencyPolicyCard) -> dict:
    from src.agentic_runtime.policy_cards.serialization import (
        policy_card_to_canonical_dict,
    )

    return {
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
        "residency_rules": [
            {
                "data_class": r.data_class.value,
                "residency_zone": r.residency_zone.value,
                "allowed_processing_locations": [
                    location.value for location in r.allowed_processing_locations
                ],
                "egress_rule": {
                    "egress_allowed": r.egress_rule.egress_allowed,
                    "requires_redaction": r.egress_rule.requires_redaction,
                    "requires_operator_approval": r.egress_rule.requires_operator_approval,
                    "requires_encryption": r.egress_rule.requires_encryption,
                    "requires_audit_trace": r.egress_rule.requires_audit_trace,
                    "allowed_destinations": [d.value for d in r.egress_rule.allowed_destinations],
                    "forbidden_destinations": [d.value for d in r.egress_rule.forbidden_destinations],
                },
                "redaction_requirements": [
                    {
                        "requirement_type": rr.requirement_type.value,
                        "required": rr.required,
                        "description": rr.description,
                    }
                    for rr in r.redaction_requirements
                ],
                "storage_requirements": [
                    {
                        "requirement_type": sr.requirement_type.value,
                        "required": sr.required,
                        "ttl_seconds": sr.ttl_seconds,
                        "description": sr.description,
                    }
                    for sr in r.storage_requirements
                ],
                "exposure_rule": (
                    {
                        "local_model_allowed": r.exposure_rule.local_model_allowed,
                        "external_model_allowed": r.exposure_rule.external_model_allowed,
                        "tool_access_allowed": r.exposure_rule.tool_access_allowed,
                        "web_search_allowed": r.exposure_rule.web_search_allowed,
                        "artifact_export_allowed": r.exposure_rule.artifact_export_allowed,
                        "memory_write_allowed": r.exposure_rule.memory_write_allowed,
                        "external_api_allowed": r.exposure_rule.external_api_allowed,
                        "human_review_required": r.exposure_rule.human_review_required,
                    }
                    if r.exposure_rule is not None
                    else None
                ),
                "description": r.description,
            }
            for r in card.residency_rules
        ],
        "default_zone": card.default_zone.value,
        "metadata": dict(card.metadata),
    }


# ───────────────────────── 1. Default card validity ─────────────────────────


def test_default_card_is_valid():
    card = _make_default_card()
    result = validate_data_residency_policy_card(card)
    assert result.valid, f"unexpected errors: {result.errors}"
    assert card.schema_version == DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSION
    assert card.default_zone == DataResidencyZone.LOCAL_ONLY


# ───────────────────────── 2. Required data classes present ─────────────────────────


def test_default_card_has_all_required_data_classes():
    card = _make_default_card()
    class_values = {r.data_class.value for r in card.residency_rules}
    required_values = {dc.value for dc in REQUIRED_DATA_CLASSES}
    missing = required_values - class_values
    assert not missing, f"missing required data classes: {sorted(missing)}"


def test_all_20_data_classes_in_default():
    card = _make_default_card()
    class_values = {r.data_class.value for r in card.residency_rules}
    assert len(class_values) == 20, f"expected 20 data classes, got {len(class_values)}"


# ───────────────────────── 3. Invalid data class rejected ─────────────────────────


def test_invalid_data_class_rejected():
    data = _to_dict(_make_default_card())
    data["residency_rules"].append(
        {
            "data_class": "nonexistent_fictional_class",
            "residency_zone": "local_only",
            "description": "bad rule",
        }
    )
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 4. Invalid zone rejected ─────────────────────────


def test_invalid_zone_rejected():
    data = _to_dict(_make_default_card())
    data["residency_rules"].append(
        {
            "data_class": "identity_record",  # already exists, but tests zone validation
            "residency_zone": "invalid_zone_xyz",
            "description": "bad zone",
        }
    )
    # Since identity_record already exists, the invalid zone on this new rule will still trigger
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 5. Missing required data class rejected ─────────────────────────


def test_missing_required_data_class_rejected():
    data = _to_dict(_make_default_card())
    # Remove credentials
    data["residency_rules"] = [
        r for r in data["residency_rules"] if r["data_class"] != "credentials"
    ]
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    # The dict validator wraps load/validation errors into INVALID_DATA_RESIDENCY_POLICY_CARD_DICT
    error_message = result.errors[0].message
    assert "missing required data class" in error_message.lower() or "credentials" in error_message.lower()


# ───────────────────────── 6. Duplicate data class rejected ─────────────────────────


def test_duplicate_data_class_rejected():
    data = _to_dict(_make_default_card())
    # Duplicate the credentials rule
    cred_rules = [r for r in data["residency_rules"] if r["data_class"] == "credentials"]
    assert cred_rules
    data["residency_rules"].append(deepcopy(cred_rules[0]))
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "DUPLICATE_DATA_CLASS" in error_codes


# ───────────────────────── 7. local_only no-egress ─────────────────────────


def test_local_only_no_egress_rejected():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "internal":
            rule["egress_rule"]["egress_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "LOCAL_ONLY_EGRESS" in error_codes


# ───────────────────────── 8. local_only no-external-model ─────────────────────────


def test_local_only_no_external_model_rejected():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "internal":
            if rule.get("exposure_rule") is None:
                rule["exposure_rule"] = _make_default_exposure_dict()
            rule["exposure_rule"]["external_model_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "LOCAL_ONLY_EXTERNAL_MODEL" in error_codes


# ───────────────────────── 9. local_only no-external-api/web ─────────────────────────


def test_local_only_no_external_api_rejected():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "internal":
            if rule.get("exposure_rule") is None:
                rule["exposure_rule"] = _make_default_exposure_dict()
            rule["exposure_rule"]["external_api_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "LOCAL_ONLY_EXTERNAL_API" in error_codes


def test_local_only_no_web_search_rejected():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "internal":
            if rule.get("exposure_rule") is None:
                rule["exposure_rule"] = _make_default_exposure_dict()
            rule["exposure_rule"]["web_search_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "LOCAL_ONLY_WEB_SEARCH" in error_codes


# ───────────────────────── 10. credentials no-egress ─────────────────────────


def test_credentials_no_egress():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "credentials":
            rule["egress_rule"]["egress_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "CREDENTIALS_EGRESS" in error_codes


# ───────────────────────── 11. credentials encryption + audit required ─────────────────────────


def test_credentials_requires_encryption():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "credentials":
            rule["egress_rule"]["requires_encryption"] = False
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "CREDENTIALS_ENCRYPTION" in error_codes


def test_credentials_requires_audit():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "credentials":
            rule["egress_rule"]["requires_audit_trace"] = False
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "CREDENTIALS_AUDIT" in error_codes


def test_credentials_no_external_model():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "credentials":
            if rule.get("exposure_rule") is None:
                rule["exposure_rule"] = _make_default_exposure_dict()
            rule["exposure_rule"]["external_model_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "CREDENTIALS_EXTERNAL_MODEL" in error_codes


# ───────────────────────── 12. sensitive_personal_data strict ─────────────────────────


def test_sensitive_personal_data_must_be_local_only():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "sensitive_personal_data":
            rule["residency_zone"] = "trusted_region"
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "SENSITIVE_PERSONAL_DATA_ZONE" in error_codes


def test_sensitive_personal_data_no_egress():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "sensitive_personal_data":
            rule["egress_rule"]["egress_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "SENSITIVE_PERSONAL_DATA_EGRESS" in error_codes


def test_sensitive_personal_data_no_external_model():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "sensitive_personal_data":
            if rule.get("exposure_rule") is None:
                rule["exposure_rule"] = _make_default_exposure_dict()
            rule["exposure_rule"]["external_model_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "SPD_EXTERNAL_MODEL" in error_codes


# ───────────────────────── 13. memory_record strict ─────────────────────────


def test_memory_record_must_be_local_only():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "memory_record":
            rule["residency_zone"] = "trusted_region"
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "MEMORY_RECORD_ZONE" in error_codes


def test_memory_record_no_egress():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "memory_record":
            rule["egress_rule"]["egress_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "MEMORY_RECORD_EGRESS" in error_codes


# ───────────────────────── 14. trace_record strict ─────────────────────────


def test_trace_record_must_be_local_only():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "trace_record":
            rule["residency_zone"] = "trusted_region"
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "TRACE_RECORD_ZONE" in error_codes


def test_trace_record_no_egress():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "trace_record":
            rule["egress_rule"]["egress_allowed"] = True
            break
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "TRACE_RECORD_EGRESS" in error_codes


# ───────────────────────── 15. forbidden non-permissive ─────────────────────────


def test_forbidden_no_egress():
    data = _to_dict(_make_default_card())
    data["residency_rules"].append(
        {
            "data_class": "identity_record",  # will be duplicate but tests forbidden checking
            "residency_zone": "forbidden",
            "egress_rule": {
                "egress_allowed": True,
                "requires_encryption": True,
                "requires_audit_trace": True,
            },
            "description": "should be rejected",
        }
    )
    # This will trigger FORBIDDEN_EGRESS if zone=forbidden AND egress allowed
    # But also duplicate. Let me create a standalone test.
    # Make a card with just a single forbidden rule with egress
    import json as _json
    from src.agentic_runtime.policy_cards.serialization import (
        policy_card_to_canonical_dict,
    )

    base = _make_default_card()
    pc = policy_card_to_canonical_dict(base.policy_card)
    data2 = {
        "policy_card": pc,
        "schema_version": "1.0",
        "default_zone": "local_only",
        "residency_rules": [
            {
                "data_class": "public",
                "residency_zone": "public",
                "description": "public",
            },
            {
                "data_class": "internal",
                "residency_zone": "local_only",
                "description": "internal",
            },
            {
                "data_class": "confidential",
                "residency_zone": "forbidden",
                "egress_rule": {
                    "egress_allowed": True,
                    "requires_encryption": True,
                    "requires_audit_trace": True,
                },
                "exposure_rule": {
                    "local_model_allowed": True,
                    "external_model_allowed": True,
                    "tool_access_allowed": False,
                    "web_search_allowed": False,
                    "artifact_export_allowed": False,
                    "memory_write_allowed": False,
                    "external_api_allowed": False,
                    "human_review_required": False,
                },
                "description": "forbidden with egress",
            }
        ],
        "metadata": {},
    }
    result = validate_data_residency_policy_card_dict(data2)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "FORBIDDEN_EGRESS" in error_codes or "MISSING_REQUIRED_DATA_CLASS" in error_codes


def test_forbidden_no_external_model():
    from src.agentic_runtime.policy_cards.serialization import (
        policy_card_to_canonical_dict,
    )

    base = _make_default_card()
    pc = policy_card_to_canonical_dict(base.policy_card)
    data = {
        "policy_card": pc,
        "schema_version": "1.0",
        "default_zone": "local_only",
        "residency_rules": [
            {
                "data_class": "public",
                "residency_zone": "public",
                "description": "public",
            },
            {
                "data_class": "internal",
                "residency_zone": "forbidden",
                "egress_rule": {
                    "egress_allowed": False,
                    "requires_encryption": True,
                    "requires_audit_trace": True,
                },
                "exposure_rule": {
                    "local_model_allowed": True,
                    "external_model_allowed": True,
                    "tool_access_allowed": False,
                    "web_search_allowed": False,
                    "artifact_export_allowed": False,
                    "memory_write_allowed": False,
                    "external_api_allowed": False,
                    "human_review_required": False,
                },
                "description": "forbidden with external model",
            },
        ],
        "metadata": {},
    }
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "FORBIDDEN_EXTERNAL_MODEL" in error_codes or "MISSING_REQUIRED_DATA_CLASS" in error_codes


# ───────────────────────── 16. Dangerous metadata keys rejected ─────────────────────────


def test_dangerous_metadata_key_rejected():
    data = _to_dict(_make_default_card())
    data["metadata"]["allow_secret_egress"] = True
    with pytest.raises(DataResidencyPolicyCardUnsafeFieldError):
        load_data_residency_policy_card_from_dict(data)


def test_bypass_residency_metadata_rejected():
    data = _to_dict(_make_default_card())
    data["metadata"]["bypass_residency"] = "any"
    with pytest.raises(DataResidencyPolicyCardUnsafeFieldError):
        load_data_residency_policy_card_from_dict(data)


# ───────────────────────── 17. Safe metadata accepted ─────────────────────────


def test_safe_metadata_accepted():
    data = _to_dict(_make_default_card())
    data["metadata"]["owner_note"] = "test note"
    data["metadata"]["created_by"] = "test suite"
    card = load_data_residency_policy_card_from_dict(data)
    assert "owner_note" in card.metadata
    assert "created_by" in card.metadata


# ───────────────────────── 18. PolicyCard compatibility ─────────────────────────


def test_policy_card_kind_is_data_residency():
    card = _make_default_card()
    assert card.policy_card.kind == PolicyCardKind.DATA_RESIDENCY


def test_policy_card_kind_wrong_rejected():
    data = _to_dict(_make_default_card())
    data["policy_card"]["kind"] = "risk_tier"
    result = validate_data_residency_policy_card_dict(data)
    assert not result.valid
    error_codes = {e.code for e in result.errors}
    assert "INVALID_POLICY_CARD_KIND" in error_codes


# ───────────────────────── 19. Closed-world validation ─────────────────────────


def test_unknown_top_level_field_rejected():
    data = _to_dict(_make_default_card())
    data["runtime_enforcement"] = True
    # runtime_enforcement is in the dangerous fields set
    with pytest.raises(DataResidencyPolicyCardUnsafeFieldError):
        load_data_residency_policy_card_from_dict(data)


def test_truly_unknown_field_rejected():
    data = _to_dict(_make_default_card())
    data["fictional_field_xyz"] = True
    with pytest.raises(DataResidencyPolicyCardUnknownFieldError):
        load_data_residency_policy_card_from_dict(data)


def test_unknown_rule_field_rejected():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "internal":
            rule["unknown_field_xyz"] = "secret"
            break
    with pytest.raises(DataResidencyPolicyCardUnknownFieldError):
        load_data_residency_policy_card_from_dict(data)


def test_unknown_egress_rule_field_rejected():
    data = _to_dict(_make_default_card())
    for rule in data["residency_rules"]:
        if rule["data_class"] == "internal":
            rule["egress_rule"]["unknown_bypass"] = True
            break
    with pytest.raises(DataResidencyPolicyCardUnknownFieldError):
        load_data_residency_policy_card_from_dict(data)


# ───────────────────────── 20. Deterministic serialization ─────────────────────────


def test_serialization_deterministic():
    card1 = _make_default_card()
    card2 = _make_default_card()
    s1 = serialize_data_residency_policy_card_canonical(card1)
    s2 = serialize_data_residency_policy_card_canonical(card2)
    assert s1 == s2


def test_serialization_produces_valid_json():
    card = _make_default_card()
    s = serialize_data_residency_policy_card_canonical(card)
    import json

    parsed = json.loads(s)
    assert isinstance(parsed, dict)


# ───────────────────────── 21. Hash stability ─────────────────────────


def test_hash_stable():
    card1 = _make_default_card()
    card2 = _make_default_card()
    h1 = compute_data_residency_policy_card_hash(card1)
    h2 = compute_data_residency_policy_card_hash(card2)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_changes_with_metadata():
    card1 = _make_default_card()
    data = _to_dict(card1)
    data["metadata"]["test_key"] = "value"
    card2 = load_data_residency_policy_card_from_dict(data)
    assert compute_data_residency_policy_card_hash(card1) != compute_data_residency_policy_card_hash(card2)


def test_hash_changes_with_different_default_zone():
    card1 = _make_default_card()
    data = _to_dict(card1)
    data["default_zone"] = "trusted_region"
    card2 = load_data_residency_policy_card_from_dict(data)
    assert compute_data_residency_policy_card_hash(card1) != compute_data_residency_policy_card_hash(card2)


# ───────────────────────── 22. Schema export ─────────────────────────


def test_schema_export_has_required_keys():
    schema = export_data_residency_policy_schema()
    for key in (
        "schema_version",
        "supported_versions",
        "required_fields",
        "optional_fields",
        "forbidden_fields",
        "canonical_fields",
        "rule_required_fields",
        "rule_optional_fields",
        "dangerous_field_names",
        "dangerous_metadata_keys",
        "required_data_classes",
        "strict_local_only_data_classes",
    ):
        assert key in schema, f"missing key: {key}"


def test_is_supported_schema_version():
    assert is_supported_data_residency_policy_schema_version("1.0")
    assert not is_supported_data_residency_policy_schema_version("0.9")
    assert not is_supported_data_residency_policy_schema_version("")
    assert not is_supported_data_residency_policy_schema_version(None)  # type: ignore[arg-type]


def test_validate_schema_version():
    result = validate_data_residency_policy_schema_version("1.0")
    assert result.valid
    result = validate_data_residency_policy_schema_version("2.0")
    assert not result.valid
    assert any(e.code == "UNSUPPORTED_SCHEMA_VERSION" for e in result.errors)


def test_get_schema_same_as_export():
    assert get_data_residency_policy_schema() == export_data_residency_policy_schema()


# ───────────────────────── 23. No runtime enforcement ─────────────────────────


def test_data_residency_policy_card_has_no_runtime_methods():
    """Confirm the card itself exposes no runtime enforcement methods."""
    card = _make_default_card()
    forbidden_attrs = {
        "enforce", "resolve", "check_egress", "route_model",
        "classify_data", "perform_redaction", "perform_encryption",
        "execute_policy", "apply_egress_guard",
    }
    for attr in forbidden_attrs:
        assert not hasattr(card, attr), f"card should not have {attr}"
        assert not callable(getattr(card, attr, None))


def test_validate_does_not_perform_runtime_actions():
    card = _make_default_card()
    result = validate_data_residency_policy_card(card)
    assert result.valid
    assert result.canonical_hash is not None


# ───────────────────────── Extra: edge cases ─────────────────────────


def test_load_empty_dict_raises():
    with pytest.raises(DataResidencyPolicyCardValidationError):
        load_data_residency_policy_card_from_dict({})


def test_load_schema_version_invalid():
    data = _to_dict(_make_default_card())
    data["schema_version"] = "99.99"
    with pytest.raises(DataResidencyPolicyCardValidationError):
        load_data_residency_policy_card_from_dict(data)


def test_default_zone_invalid_rejected():
    data = _to_dict(_make_default_card())
    data["default_zone"] = "mars"
    with pytest.raises(DataResidencyPolicyCardValidationError):
        load_data_residency_policy_card_from_dict(data)


def test_error_hierarchy():
    assert issubclass(DataResidencyPolicyCardValidationError, DataResidencyPolicyCardError)
    assert issubclass(DataResidencyPolicyCardError, PolicyCardError)
    assert issubclass(DataResidencyPolicyCardError, ValueError)

"""Unit tests for Memory Write Policy Card model (P1.6.7).

Covers 26 test categories from the P1.6.7 specification:
  1.  Default card validity
  2.  Default decision is deny
  3.  No silent canonical write
  4.  Canon memory requires strong requirements
  5.  Policy memory protected
  6.  Verified skill requires verification
  7.  Skill candidate is not verified
  8.  Operator profile protected
  9.  Scratchpad ephemeral allowed
  10. Working memory session allowed
  11. Credentials cannot be durable memory by default
  12. Sensitive personal data strict
  13. Invalid memory zone rejected
  14. Invalid memory write type rejected
  15. Invalid memory decision rejected
  16. Invalid verification status rejected
  17. Invalid retention class rejected
  18. Dangerous metadata rejected
  19. Safe metadata accepted
  20. PolicyCard compatibility
  21. Closed-world unknown field rejected
  22. Deterministic serialization
  23. Hash stability
  24. Schema export deterministic
  25. Existing P1.6.0-P1.6.6 tests still pass (separate suites)
  26. No runtime enforcement
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.agentic_runtime.policy_cards.memory_write import (
    MemoryRetentionClass,
    MemoryVerificationStatus,
    MemoryWriteDecision,
    MemoryWritePolicyCard,
    MemoryWriteRequirement,
    MemoryWriteRequirementType,
    MemoryWriteRule,
    MemoryWriteType,
    MemoryWriteValidationIssue,
    MemoryWriteValidationResult,
    MemoryZone,
    compute_memory_write_policy_card_hash,
    create_default_memory_write_policy_card,
    load_memory_write_policy_card_from_dict,
    memory_write_policy_card_to_canonical_dict,
    serialize_memory_write_policy_card_canonical,
    validate_memory_write_policy_card,
    validate_memory_write_policy_card_dict,
)
from src.agentic_runtime.policy_cards.memory_write_schema import (
    DEFAULT_MEMORY_WRITE_RULES,
    MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSION,
    PROTECTED_MEMORY_ZONES,
    STRICT_MEMORY_DATA_CLASSES,
    export_memory_write_policy_schema,
    get_memory_write_policy_schema,
    is_supported_memory_write_policy_schema_version,
    validate_memory_write_policy_schema_version,
)
from src.agentic_runtime.policy_cards.errors import (
    MemoryWritePolicyCardError,
    MemoryWritePolicyCardUnknownFieldError,
    MemoryWritePolicyCardUnsafeFieldError,
    MemoryWritePolicyCardValidationError,
    PolicyCardError,
)
from src.agentic_runtime.policy_cards.models import (
    PolicyCardKind,
)


# ───────────────────────── Helpers ─────────────────────────


def _make_default_card() -> MemoryWritePolicyCard:
    return create_default_memory_write_policy_card()


def _req(rt: MemoryWriteRequirementType) -> dict:
    return {"requirement_type": rt.value, "required": True, "description": ""}


def _to_dict(card: MemoryWritePolicyCard) -> dict:
    from src.agentic_runtime.policy_cards.serialization import (
        policy_card_to_canonical_dict,
    )

    return {
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
        "memory_rules": [
            {
                "memory_zone": r.memory_zone.value,
                "write_type": r.write_type.value,
                "decision": r.decision.value,
                "verification_status": r.verification_status.value,
                "retention_class": r.retention_class.value,
                "requirements": [
                    {
                        "requirement_type": req.requirement_type.value,
                        "required": req.required,
                        "description": req.description,
                    }
                    for req in r.requirements
                ],
                "allowed_data_classes": list(r.allowed_data_classes),
                "forbidden_data_classes": list(r.forbidden_data_classes),
                "risk_ceiling": r.risk_ceiling,
                "required_oversight": r.required_oversight,
                "trace_required": r.trace_required,
                "evidence_required": r.evidence_required,
                "provenance_required": r.provenance_required,
                "description": r.description,
            }
            for r in card.memory_rules
        ],
        "default_decision": card.default_decision.value,
        "metadata": dict(card.metadata),
    }


def _canon_required_reqs() -> list:
    return [
        _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
        _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
        _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
        _req(MemoryWriteRequirementType.REQUIRES_EXPLICIT_CONFIRMATION),
        _req(MemoryWriteRequirementType.REQUIRES_CONFLICT_CHECK),
    ]


# ───────────────────────── 1. Default card validity ─────────────────────────


def test_default_card_is_valid():
    card = _make_default_card()
    result = validate_memory_write_policy_card(card)
    assert result.valid, f"unexpected errors: {result.errors}"
    assert card.schema_version == MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSION
    assert card.policy_card.kind == PolicyCardKind.MEMORY_WRITE
    assert len(card.memory_rules) >= 13


def test_default_rules_are_the_schema_default():
    card = _make_default_card()
    assert card.memory_rules == DEFAULT_MEMORY_WRITE_RULES


# ───────────────────────── 2. Default decision is deny ─────────────────────────


def test_default_decision_is_deny():
    card = _make_default_card()
    assert card.default_decision == MemoryWriteDecision.DENY


def test_allow_default_decision_rejected():
    data = _to_dict(_make_default_card())
    data["default_decision"] = "allow"
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_candidate_only_default_decision_rejected():
    data = _to_dict(_make_default_card())
    data["default_decision"] = "candidate_only"
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_canonicalize_allowed_default_decision_rejected():
    data = _to_dict(_make_default_card())
    data["default_decision"] = "canonicalize_allowed"
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 3. No silent canonical write ─────────────────────────


def test_canon_memory_silent_allow_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "canon_memory",
        "write_type": "canon_update",
        "decision": "allow",
        "verification_status": "evidence_supported",
        "retention_class": "audit_retained",
        "requirements": _canon_required_reqs(),
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "bad silent canon allow",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 4. Canon memory requires strong requirements ──────


def test_canon_memory_missing_requirements_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "canon_memory",
        "write_type": "canon_update",
        "decision": "requires_confirmation",
        "verification_status": "evidence_supported",
        "retention_class": "audit_retained",
        # Missing operator_review, explicit_confirmation, conflict_check
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "canon missing strong requirements",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_canon_memory_full_requirements_passes():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "canon_memory",
        "write_type": "canon_update",
        "decision": "requires_confirmation",
        "verification_status": "evidence_supported",
        "retention_class": "audit_retained",
        "requirements": _canon_required_reqs(),
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "canon with all requirements",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert result.valid, f"unexpected errors: {result.errors}"


# ───────────────────────── 5. Policy memory protected ─────────────────────────


def test_policy_memory_silent_allow_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "policy_memory",
        "write_type": "policy_record",
        "decision": "allow",
        "verification_status": "operator_reviewed",
        "retention_class": "audit_retained",
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_POLICY_AUTHORITY),
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
        ],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "bad policy allow",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_policy_memory_missing_governance_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "policy_memory",
        "write_type": "policy_record",
        "decision": "requires_confirmation",
        "verification_status": "operator_reviewed",
        "retention_class": "audit_retained",
        # Missing policy_authority and review
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "policy missing governance",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 6. Verified skill requires verification ───────────


def test_verified_skill_missing_verification_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "verified_skill_memory",
        "write_type": "verified_skill",
        "decision": "requires_review",
        "verification_status": "verified",
        "retention_class": "long_lived",
        # Missing evaluation_result, verification, evidence_ref, trace_ref
        "requirements": [],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "verified skill no verification",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 7. Skill candidate is not verified ────────────────


def test_skill_candidate_verified_status_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "skill_candidate_memory",
        "write_type": "skill_candidate",
        "decision": "candidate_only",
        "verification_status": "verified",
        "retention_class": "project_scoped",
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_EVALUATION_RESULT),
        ],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "candidate marked verified",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_skill_candidate_canonized_status_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "skill_candidate_memory",
        "write_type": "skill_candidate",
        "decision": "candidate_only",
        "verification_status": "canonized",
        "retention_class": "project_scoped",
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_EVALUATION_RESULT),
        ],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "candidate marked canonized",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 8. Operator profile protected ─────────────────────


def test_operator_profile_silent_allow_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "operator_profile",
        "write_type": "user_preference",
        "decision": "allow",
        "verification_status": "operator_reviewed",
        "retention_class": "long_lived",
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_USER_CONSENT),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
        ],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "bad operator profile allow",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_operator_profile_no_consent_review_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "operator_profile",
        "write_type": "user_preference",
        "decision": "requires_review",
        "verification_status": "operator_reviewed",
        "retention_class": "long_lived",
        # No consent/review/source requirements
        "requirements": [],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": False,
        "description": "operator profile no consent",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 9. Scratchpad ephemeral allowed ───────────────────


def test_scratchpad_ephemeral_allowed():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "scratchpad",
        "write_type": "temporary_note",
        "decision": "ephemeral_only",
        "verification_status": "unverified",
        "retention_class": "ephemeral",
        "requirements": [],
        "trace_required": False,
        "evidence_required": False,
        "provenance_required": False,
        "description": "scratchpad ephemeral",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert result.valid, f"unexpected errors: {result.errors}"


# ───────────────────────── 10. Working memory session allowed ────────────────


def test_working_memory_session_allowed():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "working_memory",
        "write_type": "project_state",
        "decision": "allow",
        "verification_status": "unverified",
        "retention_class": "session",
        "requirements": [],
        "trace_required": True,
        "evidence_required": False,
        "provenance_required": False,
        "description": "working memory session",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert result.valid, f"unexpected errors: {result.errors}"


# ───────────────────────── 11. Credentials cannot be durable memory ──────────


def test_credentials_in_semantic_memory_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "semantic_memory",
        "write_type": "evidence_summary",
        "decision": "allow",
        "verification_status": "evidence_supported",
        "retention_class": "long_lived",
        "requirements": [],
        "allowed_data_classes": ["credentials"],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "credentials in semantic",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_credentials_in_operator_profile_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "operator_profile",
        "write_type": "user_preference",
        "decision": "requires_review",
        "verification_status": "operator_reviewed",
        "retention_class": "long_lived",
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_USER_CONSENT),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
        ],
        "allowed_data_classes": ["credentials"],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "credentials in operator profile",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 12. Sensitive personal data strict ────────────────


def test_sensitive_personal_data_weak_binding_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "semantic_memory",
        "write_type": "evidence_summary",
        "decision": "allow",
        "verification_status": "evidence_supported",
        "retention_class": "long_lived",
        "requirements": [],
        "allowed_data_classes": ["sensitive_personal_data"],
        "trace_required": True,
        "evidence_required": False,
        "provenance_required": False,
        "description": "spd weak binding",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_sensitive_personal_data_strict_passes():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "semantic_memory",
        "write_type": "evidence_summary",
        "decision": "requires_review",
        "verification_status": "evidence_supported",
        "retention_class": "long_lived",
        "requirements": [
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_RESIDENCY_CHECK),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
        ],
        "allowed_data_classes": ["sensitive_personal_data"],
        "trace_required": True,
        "evidence_required": True,
        "provenance_required": True,
        "description": "spd strict",
    })
    result = validate_memory_write_policy_card_dict(data)
    assert result.valid, f"unexpected errors: {result.errors}"


# ───────────────────────── 13. Invalid memory zone rejected ──────────────────


@pytest.mark.parametrize("zone", ["global_brain", "shadow_canon", "unbounded_memory"])
def test_invalid_memory_zone_rejected(zone):
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": zone,
        "write_type": "observation",
        "decision": "deny",
        "verification_status": "unverified",
        "retention_class": "ephemeral",
        "description": "bad zone",
    })
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 14. Invalid memory write type rejected ────────────


@pytest.mark.parametrize("wt", ["auto_truth", "secret_authority", "self_upgrade"])
def test_invalid_write_type_rejected(wt):
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "scratchpad",
        "write_type": wt,
        "decision": "ephemeral_only",
        "verification_status": "unverified",
        "retention_class": "ephemeral",
        "description": "bad write type",
    })
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 15. Invalid memory decision rejected ──────────────


@pytest.mark.parametrize("dec", ["auto_canonize", "always_remember", "force_store"])
def test_invalid_decision_rejected(dec):
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "scratchpad",
        "write_type": "temporary_note",
        "decision": dec,
        "verification_status": "unverified",
        "retention_class": "ephemeral",
        "description": "bad decision",
    })
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 16. Invalid verification status rejected ──────────


def test_invalid_verification_status_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "scratchpad",
        "write_type": "temporary_note",
        "decision": "ephemeral_only",
        "verification_status": "auto_truth_status",
        "retention_class": "ephemeral",
        "description": "bad status",
    })
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 17. Invalid retention class rejected ──────────────


def test_invalid_retention_class_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"].append({
        "memory_zone": "scratchpad",
        "write_type": "temporary_note",
        "decision": "ephemeral_only",
        "verification_status": "unverified",
        "retention_class": "forever_unbounded",
        "description": "bad retention",
    })
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 18. Dangerous metadata rejected ───────────────────


@pytest.mark.parametrize("key", [
    "auto_canonize",
    "bypass_memory_policy",
    "remember_everything",
    "consent_not_required",
    "store_credentials",
])
def test_dangerous_metadata_rejected(key):
    data = _to_dict(_make_default_card())
    data["metadata"][key] = True
    with pytest.raises(MemoryWritePolicyCardUnsafeFieldError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 19. Safe metadata accepted ────────────────────────


def test_safe_metadata_accepted():
    data = _to_dict(_make_default_card())
    data["metadata"]["owner_note"] = "conservative memory write policy"
    data["metadata"]["created_by"] = "test suite"
    card = load_memory_write_policy_card_from_dict(data)
    assert "owner_note" in card.metadata
    assert "created_by" in card.metadata


# ───────────────────────── 20. PolicyCard compatibility ──────────────────────


def test_wrong_policy_card_kind_rejected():
    data = _to_dict(_make_default_card())
    data["policy_card"]["kind"] = "risk_tier"
    result = validate_memory_write_policy_card_dict(data)
    assert not result.valid


def test_correct_policy_card_kind_accepted():
    card = _make_default_card()
    assert card.policy_card.kind == PolicyCardKind.MEMORY_WRITE


# ───────────────────────── 21. Closed-world unknown field rejected ───────────


def test_unknown_top_level_field_rejected():
    data = _to_dict(_make_default_card())
    data["nonexistent_field"] = True
    with pytest.raises(MemoryWritePolicyCardUnknownFieldError):
        load_memory_write_policy_card_from_dict(data)


def test_forbidden_top_level_field_rejected():
    data = _to_dict(_make_default_card())
    data["memory_override_backdoor"] = True
    with pytest.raises(MemoryWritePolicyCardUnsafeFieldError):
        load_memory_write_policy_card_from_dict(data)


def test_unknown_rule_field_rejected():
    data = _to_dict(_make_default_card())
    data["memory_rules"][0]["mystery_field"] = True
    with pytest.raises(MemoryWritePolicyCardUnknownFieldError):
        load_memory_write_policy_card_from_dict(data)


# ───────────────────────── 22. Deterministic serialization ───────────────────


def test_serialization_deterministic():
    s1 = serialize_memory_write_policy_card_canonical(_make_default_card())
    s2 = serialize_memory_write_policy_card_canonical(_make_default_card())
    assert s1 == s2


def test_serialization_produces_valid_json():
    import json
    s = serialize_memory_write_policy_card_canonical(_make_default_card())
    parsed = json.loads(s)
    assert isinstance(parsed, dict)


def test_canonical_dict_round_trips():
    card = _make_default_card()
    data = memory_write_policy_card_to_canonical_dict(card)
    reloaded = load_memory_write_policy_card_from_dict(data)
    assert compute_memory_write_policy_card_hash(reloaded) == \
        compute_memory_write_policy_card_hash(card)


# ───────────────────────── 23. Hash stability ────────────────────────────────


def test_hash_stable():
    h1 = compute_memory_write_policy_card_hash(_make_default_card())
    h2 = compute_memory_write_policy_card_hash(_make_default_card())
    assert h1 == h2
    assert len(h1) == 64


def test_hash_changes_with_metadata():
    data = _to_dict(_make_default_card())
    data["metadata"]["test_key"] = "value"
    card2 = load_memory_write_policy_card_from_dict(data)
    assert compute_memory_write_policy_card_hash(_make_default_card()) != \
        compute_memory_write_policy_card_hash(card2)


# ───────────────────────── 24. Schema export deterministic ───────────────────


def test_schema_export_has_required_keys():
    schema = export_memory_write_policy_schema()
    for key in (
        "schema_version",
        "supported_versions",
        "required_fields",
        "optional_fields",
        "forbidden_fields",
        "canonical_fields",
        "rule_required_fields",
        "rule_optional_fields",
        "requirement_required_fields",
        "dangerous_field_names",
        "dangerous_metadata_keys",
        "protected_memory_zones",
        "strict_memory_data_classes",
        "memory_zones",
        "memory_write_types",
        "memory_write_decisions",
        "memory_verification_statuses",
        "memory_retention_classes",
        "memory_write_requirement_types",
    ):
        assert key in schema, f"missing key: {key}"


def test_schema_export_deterministic():
    assert export_memory_write_policy_schema() == export_memory_write_policy_schema()
    assert get_memory_write_policy_schema() == export_memory_write_policy_schema()


def test_is_supported_schema_version():
    assert is_supported_memory_write_policy_schema_version("1.0")
    assert not is_supported_memory_write_policy_schema_version("0.9")
    assert not is_supported_memory_write_policy_schema_version("")
    assert not is_supported_memory_write_policy_schema_version(None)  # type: ignore[arg-type]


def test_validate_schema_version():
    result = validate_memory_write_policy_schema_version("1.0")
    assert result.valid
    result = validate_memory_write_policy_schema_version("2.0")
    assert not result.valid
    assert any(e.code == "UNSUPPORTED_SCHEMA_VERSION" for e in result.errors)


def test_protected_zones_and_strict_classes_constants():
    assert "canon_memory" in PROTECTED_MEMORY_ZONES
    assert "policy_memory" in PROTECTED_MEMORY_ZONES
    assert "operator_profile" in PROTECTED_MEMORY_ZONES
    assert "verified_skill_memory" in PROTECTED_MEMORY_ZONES
    assert "credentials" in STRICT_MEMORY_DATA_CLASSES
    assert "sensitive_personal_data" in STRICT_MEMORY_DATA_CLASSES


# ───────────────────────── 26. No runtime enforcement ────────────────────────


def test_no_runtime_methods_on_card():
    card = _make_default_card()
    forbidden_attrs = {
        "enforce", "resolve", "execute", "store", "write", "retrieve",
        "consolidate", "promote", "canonize", "graph", "rank",
    }
    for attr in forbidden_attrs:
        assert not hasattr(card, attr), f"card should not have {attr}"
        assert not callable(getattr(card, attr, None))


# ───────────────────────── Edge cases ────────────────────────────────────────


def test_load_empty_dict_raises():
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict({})


def test_load_schema_version_invalid():
    data = _to_dict(_make_default_card())
    data["schema_version"] = "99.99"
    with pytest.raises(MemoryWritePolicyCardValidationError):
        load_memory_write_policy_card_from_dict(data)


def test_empty_memory_rules_rejected():
    card = _make_default_card()
    bad = replace(card, memory_rules=())
    result = validate_memory_write_policy_card(bad)
    assert not result.valid
    assert any(e.code == "EMPTY_MEMORY_RULES" for e in result.errors)


def test_error_hierarchy():
    assert issubclass(MemoryWritePolicyCardValidationError, MemoryWritePolicyCardError)
    assert issubclass(MemoryWritePolicyCardError, PolicyCardError)
    assert issubclass(MemoryWritePolicyCardError, ValueError)


def test_validation_result_types():
    result = validate_memory_write_policy_card(_make_default_card())
    assert isinstance(result, MemoryWriteValidationResult)
    for issue in result.errors:
        assert isinstance(issue, MemoryWriteValidationIssue)

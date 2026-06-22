"""Tests for P1.6.2 — Behavioral Contract Schema.

Covers:
- Valid contract creation, validation, canonicalization, hashing
- Schema versioning
- Closed-world validation (unknown fields, dangerous fields)
- Metadata safety
- Enum validation
- policy_card_refs shape validation
- Deterministic serialization
- Schema export determinism
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards.contract_schema import (
    BEHAVIORAL_CONTRACT_SCHEMA_VERSION,
    SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS,
    export_behavioral_contract_schema,
    get_behavioral_contract_schema,
    is_supported_behavioral_contract_schema_version,
    validate_behavioral_contract_schema_version,
)
from agentic_runtime.policy_cards.contracts import (
    BehavioralContract,
    BehavioralContractEscalationAction,
    BehavioralContractEscalationRule,
    BehavioralContractEscalationTrigger,
    BehavioralContractEvidenceRequirement,
    BehavioralContractEvidenceType,
    BehavioralContractIdentity,
    BehavioralContractObligation,
    BehavioralContractObligationType,
    BehavioralContractPostcondition,
    BehavioralContractPostconditionType,
    BehavioralContractPrecondition,
    BehavioralContractPreconditionType,
    BehavioralContractProhibition,
    BehavioralContractProhibitionType,
    BehavioralContractScope,
    BehavioralContractScopeType,
    BehavioralContractSource,
    BehavioralContractStatus,
    BehavioralContractSubject,
    BehavioralContractSubjectType,
    BehavioralContractValidationIssue,
    BehavioralContractValidationResult,
    behavioral_contract_to_canonical_dict,
    compute_behavioral_contract_hash,
    load_behavioral_contract_from_dict,
    serialize_behavioral_contract_canonical,
    validate_behavioral_contract,
)
from agentic_runtime.policy_cards.errors import (
    BehavioralContractValidationError,
    BehavioralContractUnknownFieldError,
    BehavioralContractUnsafeFieldError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_contract_dict() -> dict:
    return {
        "schema_version": "1.0",
        "identity": {
            "contract_id": "test-contract-1",
            "slug": "test-contract",
            "name": "Test Contract",
            "version": "1.0.0",
            "namespace": "aurel.test",
        },
        "status": "active",
        "subject": {
            "subject_type": "agent",
        },
        "scope": {
            "scope_type": "global",
        },
        "policy_card_refs": [],
        "obligations": [],
        "prohibitions": [],
        "preconditions": [],
        "postconditions": [],
        "evidence_requirements": [],
        "escalation_rules": [],
    }


def _make_full_contract_dict() -> dict:
    return {
        "schema_version": "1.0",
        "identity": {
            "contract_id": "test-contract-full",
            "slug": "test-full-contract",
            "name": "Full Test Contract",
            "version": "2.0.0",
            "namespace": "aurel.test.full",
        },
        "status": "active",
        "subject": {
            "subject_type": "agent",
            "subject_id": "agent-42",
            "applies_to": ["aurel-core"],
        },
        "scope": {
            "scope_type": "runtime",
            "scope_id": "runtime-main",
            "applies_to": ["main"],
        },
        "policy_card_refs": ["pc-001", "pc-002"],
        "obligations": [
            {
                "obligation_type": "must_emit_trace",
                "description": "Agent must emit trace events",
                "required": True,
            },
        ],
        "prohibitions": [
            {
                "prohibition_type": "must_not_skip_trace",
                "description": "Agent must not skip trace",
                "strict": True,
            },
        ],
        "preconditions": [
            {
                "precondition_type": "policy_resolved",
                "description": "Policy must be resolved first",
                "required": True,
            },
        ],
        "postconditions": [
            {
                "postcondition_type": "trace_written",
                "description": "Trace must be written after action",
                "required": True,
            },
        ],
        "evidence_requirements": [
            {
                "evidence_type": "trace_event",
                "required": True,
                "description": "Trace event evidence",
            },
        ],
        "escalation_rules": [
            {
                "trigger": "risk_tier_above_threshold",
                "action": "request_operator_approval",
                "description": "Escalate high risk",
            },
        ],
        "source": {
            "source_type": "file",
            "source_path": "/test/contract.yaml",
        },
        "metadata": {"owner_note": "test contract"},
    }


# ---------------------------------------------------------------------------
# Valid creation, validation, hash
# ---------------------------------------------------------------------------

class TestValidContractCreation:

    def test_minimal_contract_loads(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        assert contract.schema_version == "1.0"
        assert contract.identity.contract_id == "test-contract-1"
        assert contract.status == BehavioralContractStatus.ACTIVE
        assert contract.subject.subject_type == BehavioralContractSubjectType.AGENT
        assert contract.scope.scope_type == BehavioralContractScopeType.GLOBAL
        assert contract.policy_card_refs == ()

    def test_full_contract_loads(self):
        data = _make_full_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        assert contract.identity.contract_id == "test-contract-full"
        assert contract.subject.subject_id == "agent-42"
        assert contract.policy_card_refs == ("pc-001", "pc-002")
        assert len(contract.obligations) == 1
        assert len(contract.prohibitions) == 1
        assert len(contract.preconditions) == 1
        assert len(contract.postconditions) == 1
        assert len(contract.evidence_requirements) == 1
        assert len(contract.escalation_rules) == 1
        assert contract.source is not None
        assert contract.metadata == {"owner_note": "test contract"}

    def test_validate_minimal_contract(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        result = validate_behavioral_contract(contract)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_full_contract(self):
        data = _make_full_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        result = validate_behavioral_contract(contract)
        assert result.valid
        assert len(result.errors) == 0

    def test_compute_hash_minimal(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        h = compute_behavioral_contract_hash(contract)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_hash_deterministic(self):
        data = _make_full_contract_dict()
        c1 = load_behavioral_contract_from_dict(data)
        c2 = load_behavioral_contract_from_dict(data)
        assert compute_behavioral_contract_hash(c1) == compute_behavioral_contract_hash(c2)

    def test_different_contract_different_hash(self):
        c1 = load_behavioral_contract_from_dict(_make_minimal_contract_dict())
        c2 = load_behavioral_contract_from_dict(_make_full_contract_dict())
        assert compute_behavioral_contract_hash(c1) != compute_behavioral_contract_hash(c2)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

class TestSchemaVersioning:

    def test_schema_1_0_accepted(self):
        data = _make_minimal_contract_dict()
        data["schema_version"] = "1.0"
        contract = load_behavioral_contract_from_dict(data)
        assert contract.schema_version == "1.0"

    def test_unsupported_schema_version_rejected(self):
        data = _make_minimal_contract_dict()
        data["schema_version"] = "99.0"
        with pytest.raises(BehavioralContractValidationError, match="schema_version"):
            load_behavioral_contract_from_dict(data)

    def test_missing_schema_version_rejected(self):
        data = _make_minimal_contract_dict()
        del data["schema_version"]
        with pytest.raises(BehavioralContractValidationError, match="schema_version"):
            load_behavioral_contract_from_dict(data)

    def test_empty_schema_version_rejected(self):
        data = _make_minimal_contract_dict()
        data["schema_version"] = ""
        with pytest.raises(BehavioralContractValidationError, match="schema_version"):
            load_behavioral_contract_from_dict(data)

    def test_null_schema_version_rejected(self):
        data = _make_minimal_contract_dict()
        data["schema_version"] = None
        with pytest.raises(BehavioralContractValidationError, match="schema_version"):
            load_behavioral_contract_from_dict(data)

    def test_schema_version_validate_fn_accepts_1_0(self):
        result = validate_behavioral_contract_schema_version("1.0")
        assert result.valid

    def test_schema_version_validate_fn_rejects_99(self):
        result = validate_behavioral_contract_schema_version("99.0")
        assert not result.valid
        assert len(result.errors) == 1

    def test_is_supported_returns_true_for_1_0(self):
        assert is_supported_behavioral_contract_schema_version("1.0")

    def test_is_supported_returns_false_for_99(self):
        assert not is_supported_behavioral_contract_schema_version("99.0")


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

class TestMissingRequiredFields:

    def test_missing_identity_rejected(self):
        data = _make_minimal_contract_dict()
        del data["identity"]
        with pytest.raises(BehavioralContractValidationError, match="identity"):
            load_behavioral_contract_from_dict(data)

    def test_missing_subject_rejected(self):
        data = _make_minimal_contract_dict()
        del data["subject"]
        with pytest.raises(BehavioralContractValidationError, match="subject"):
            load_behavioral_contract_from_dict(data)

    def test_missing_scope_rejected(self):
        data = _make_minimal_contract_dict()
        del data["scope"]
        with pytest.raises(BehavioralContractValidationError, match="scope"):
            load_behavioral_contract_from_dict(data)

    def test_missing_status_rejected(self):
        data = _make_minimal_contract_dict()
        del data["status"]
        with pytest.raises(BehavioralContractValidationError, match="status"):
            load_behavioral_contract_from_dict(data)

    def test_empty_identity_contract_id_rejected(self):
        data = _make_minimal_contract_dict()
        data["identity"]["contract_id"] = ""
        with pytest.raises(BehavioralContractValidationError, match="identity.contract_id"):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# Unknown top-level fields
# ---------------------------------------------------------------------------

class TestUnknownTopLevelFieldsRejected:

    def test_single_unknown_field_rejected(self):
        data = _make_minimal_contract_dict()
        data["unknown_field"] = "value"
        with pytest.raises(BehavioralContractUnknownFieldError, match="unknown_field"):
            load_behavioral_contract_from_dict(data)

    def test_multiple_unknown_fields_rejected(self):
        data = _make_minimal_contract_dict()
        data["foo"] = 1
        data["bar"] = 2
        with pytest.raises(BehavioralContractUnknownFieldError):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# Dangerous top-level fields
# ---------------------------------------------------------------------------

class TestDangerousTopLevelFieldsRejected:

    def test_authority_grant_rejected(self):
        data = _make_minimal_contract_dict()
        data["authority_grant"] = True
        with pytest.raises(BehavioralContractUnsafeFieldError, match="authority_grant"):
            load_behavioral_contract_from_dict(data)

    def test_bypass_policy_rejected(self):
        data = _make_minimal_contract_dict()
        data["bypass_policy"] = True
        with pytest.raises(BehavioralContractUnsafeFieldError, match="bypass_policy"):
            load_behavioral_contract_from_dict(data)

    def test_skip_trace_rejected(self):
        data = _make_minimal_contract_dict()
        data["skip_trace"] = True
        with pytest.raises(BehavioralContractUnsafeFieldError, match="skip_trace"):
            load_behavioral_contract_from_dict(data)

    def test_disable_contract_rejected(self):
        data = _make_minimal_contract_dict()
        data["disable_contract"] = True
        with pytest.raises(BehavioralContractUnsafeFieldError):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# Metadata safety
# ---------------------------------------------------------------------------

class TestMetadataSafety:

    def test_dangerous_metadata_operator_not_required_rejected(self):
        data = _make_minimal_contract_dict()
        data["metadata"] = {"operator_not_required": True}
        with pytest.raises(BehavioralContractUnsafeFieldError, match="operator_not_required"):
            load_behavioral_contract_from_dict(data)

    def test_dangerous_metadata_authority_rejected(self):
        data = _make_minimal_contract_dict()
        data["metadata"] = {"authority": "elevated"}
        with pytest.raises(BehavioralContractUnsafeFieldError, match="authority"):
            load_behavioral_contract_from_dict(data)

    def test_safe_metadata_accepted(self):
        data = _make_minimal_contract_dict()
        data["metadata"] = {"owner_note": "for testing", "review_hint": "check obligations"}
        contract = load_behavioral_contract_from_dict(data)
        assert contract.metadata["owner_note"] == "for testing"
        assert contract.metadata["review_hint"] == "check obligations"

    def test_no_metadata_accepted(self):
        data = _make_full_contract_dict()
        del data["metadata"]
        contract = load_behavioral_contract_from_dict(data)
        assert contract.metadata == {}


# ---------------------------------------------------------------------------
# Invalid enum values
# ---------------------------------------------------------------------------

class TestInvalidEnumValues:

    def test_invalid_subject_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["subject"]["subject_type"] = "not_a_subject"
        with pytest.raises(BehavioralContractValidationError, match="subject_type"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_scope_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["scope"]["scope_type"] = "not_a_scope"
        with pytest.raises(BehavioralContractValidationError, match="scope_type"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_status_rejected(self):
        data = _make_minimal_contract_dict()
        data["status"] = "not_a_status"
        with pytest.raises(BehavioralContractValidationError, match="status"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_obligation_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["obligations"] = [{"obligation_type": "invalid_type",
                                 "description": "test", "required": True}]
        with pytest.raises(BehavioralContractValidationError, match="obligations"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_prohibition_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["prohibitions"] = [{"prohibition_type": "invalid_type",
                                  "description": "test", "strict": True}]
        with pytest.raises(BehavioralContractValidationError, match="prohibitions"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_evidence_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["evidence_requirements"] = [{"evidence_type": "invalid_type",
                                           "description": "test"}]
        with pytest.raises(BehavioralContractValidationError, match="evidence_requirements"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_precondition_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["preconditions"] = [{"precondition_type": "invalid_type",
                                   "description": "test"}]
        with pytest.raises(BehavioralContractValidationError, match="preconditions"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_postcondition_type_rejected(self):
        data = _make_minimal_contract_dict()
        data["postconditions"] = [{"postcondition_type": "invalid_type",
                                    "description": "test"}]
        with pytest.raises(BehavioralContractValidationError, match="postconditions"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_escalation_trigger_rejected(self):
        data = _make_minimal_contract_dict()
        data["escalation_rules"] = [{"trigger": "invalid_trigger",
                                      "action": "deny_action"}]
        with pytest.raises(BehavioralContractValidationError, match="escalation_rules"):
            load_behavioral_contract_from_dict(data)

    def test_invalid_escalation_action_rejected(self):
        data = _make_minimal_contract_dict()
        data["escalation_rules"] = [{"trigger": "uncertain_authority",
                                      "action": "invalid_action"}]
        with pytest.raises(BehavioralContractValidationError, match="escalation_rules"):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# policy_card_refs validation
# ---------------------------------------------------------------------------

class TestPolicyCardRefsValidation:

    def test_non_list_policy_card_refs_rejected(self):
        data = _make_minimal_contract_dict()
        data["policy_card_refs"] = "not-a-list"
        with pytest.raises(BehavioralContractValidationError, match="policy_card_refs"):
            load_behavioral_contract_from_dict(data)

    def test_non_string_ref_in_list_rejected(self):
        data = _make_minimal_contract_dict()
        data["policy_card_refs"] = ["valid", 123]
        with pytest.raises(BehavioralContractValidationError, match="policy_card_refs"):
            load_behavioral_contract_from_dict(data)

    def test_empty_policy_card_refs_accepted(self):
        data = _make_minimal_contract_dict()
        data["policy_card_refs"] = []
        contract = load_behavioral_contract_from_dict(data)
        assert contract.policy_card_refs == ()

    def test_valid_policy_card_refs_loads(self):
        data = _make_minimal_contract_dict()
        data["policy_card_refs"] = ["pc-abc", "pc-xyz"]
        contract = load_behavioral_contract_from_dict(data)
        assert contract.policy_card_refs == ("pc-abc", "pc-xyz")


# ---------------------------------------------------------------------------
# Deterministic serialization
# ---------------------------------------------------------------------------

class TestDeterministicSerialization:

    def test_same_contract_same_json(self):
        data = _make_full_contract_dict()
        c1 = load_behavioral_contract_from_dict(data)
        c2 = load_behavioral_contract_from_dict(data)
        assert serialize_behavioral_contract_canonical(c1) == serialize_behavioral_contract_canonical(c2)

    def test_same_contract_same_hash(self):
        data = _make_full_contract_dict()
        c1 = load_behavioral_contract_from_dict(data)
        c2 = load_behavioral_contract_from_dict(data)
        assert compute_behavioral_contract_hash(c1) == compute_behavioral_contract_hash(c2)

    def test_canonical_dict_has_expected_keys(self):
        data = _make_full_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        d = behavioral_contract_to_canonical_dict(contract)
        expected_keys = {"escalation_rules", "evidence_requirements", "identity",
                         "metadata", "obligations", "policy_card_refs",
                         "postconditions", "preconditions", "prohibitions",
                         "schema_version", "scope", "source", "status", "subject"}
        assert set(d.keys()) == expected_keys

    def test_serialization_is_valid_json(self):
        data = _make_full_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        s = serialize_behavioral_contract_canonical(contract)
        parsed = json.loads(s)
        assert isinstance(parsed, dict)

    def test_hash_not_sensitive_to_metadata_order(self):
        c1 = load_behavioral_contract_from_dict({
            **_make_minimal_contract_dict(),
            "metadata": {"a": "1", "b": "2"},
        })
        c2 = load_behavioral_contract_from_dict({
            **_make_minimal_contract_dict(),
            "metadata": {"b": "2", "a": "1"},
        })
        assert compute_behavioral_contract_hash(c1) == compute_behavioral_contract_hash(c2)

    def test_hash_not_sensitive_to_obligation_order(self):
        d1 = {**_make_minimal_contract_dict(), "obligations": [
            {"obligation_type": "must_emit_trace", "description": "a", "required": True},
            {"obligation_type": "must_report_failure", "description": "b", "required": True},
        ]}
        d2 = {**_make_minimal_contract_dict(), "obligations": [
            {"obligation_type": "must_report_failure", "description": "b", "required": True},
            {"obligation_type": "must_emit_trace", "description": "a", "required": True},
        ]}
        c1 = load_behavioral_contract_from_dict(d1)
        c2 = load_behavioral_contract_from_dict(d2)
        assert compute_behavioral_contract_hash(c1) == compute_behavioral_contract_hash(c2)

    def test_hash_not_sensitive_to_ref_order(self):
        d1 = {**_make_minimal_contract_dict(), "policy_card_refs": ["b", "a"]}
        d2 = {**_make_minimal_contract_dict(), "policy_card_refs": ["a", "b"]}
        c1 = load_behavioral_contract_from_dict(d1)
        c2 = load_behavioral_contract_from_dict(d2)
        assert compute_behavioral_contract_hash(c1) == compute_behavioral_contract_hash(c2)

    def test_different_contract_different_json(self):
        c1 = load_behavioral_contract_from_dict(_make_minimal_contract_dict())
        c2 = load_behavioral_contract_from_dict(_make_full_contract_dict())
        assert serialize_behavioral_contract_canonical(c1) != serialize_behavioral_contract_canonical(c2)


# ---------------------------------------------------------------------------
# Source handling
# ---------------------------------------------------------------------------

class TestSourceHandling:

    def test_source_is_optional(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        assert contract.source is None

    def test_source_with_all_fields_loads(self):
        data = {**_make_minimal_contract_dict(), "source": {
            "source_type": "test", "source_path": "/tmp",
            "raw_source_hash": "abc123", "canonical_hash": "def456",
            "loaded_at": "2025-01-01T00:00:00Z",
        }}
        contract = load_behavioral_contract_from_dict(data)
        assert contract.source is not None
        assert contract.source.source_type == "test"
        assert contract.source.source_path == "/tmp"

    def test_source_with_minimal_fields_loads(self):
        data = {**_make_minimal_contract_dict(), "source": {"source_type": "inline"}}
        contract = load_behavioral_contract_from_dict(data)
        assert contract.source is not None
        assert contract.source.source_type == "inline"
        assert contract.source.source_path is None

    def test_source_empty_source_type_rejected(self):
        data = {**_make_minimal_contract_dict(), "source": {"source_type": ""}}
        with pytest.raises(BehavioralContractValidationError, match="source_type"):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# Schema export determinism
# ---------------------------------------------------------------------------

class TestSchemaExport:

    def test_export_is_dict(self):
        schema = export_behavioral_contract_schema()
        assert isinstance(schema, dict)

    def test_export_has_schema_version(self):
        schema = export_behavioral_contract_schema()
        assert schema["schema_version"] == "1.0"

    def test_supported_versions_contains_1_0(self):
        schema = export_behavioral_contract_schema()
        assert "1.0" in schema["supported_versions"]

    def test_field_categories_present(self):
        schema = export_behavioral_contract_schema()
        cats = schema["field_categories"]
        for cat in ("control", "identity", "subject", "behavior",
                     "evidence", "source", "descriptive", "runtime_future"):
            assert cat in cats, f"missing category: {cat}"

    def test_schema_export_deterministic(self):
        s1 = json.dumps(export_behavioral_contract_schema(), sort_keys=True)
        s2 = json.dumps(export_behavioral_contract_schema(), sort_keys=True)
        assert s1 == s2

    def test_get_schema_same_as_export(self):
        assert get_behavioral_contract_schema() == export_behavioral_contract_schema()


# ---------------------------------------------------------------------------
# Structural / non-runtime checks
# ---------------------------------------------------------------------------

class TestStructuralChecks:

    def test_contracts_not_have_runtime_enforcement_field(self):
        """Behavioral contracts must not ship a runtime_enforcement field."""
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        assert not hasattr(contract, "runtime_enforcement")

    def test_contracts_not_have_enforcer_field(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        assert not hasattr(contract, "enforcer")

    def test_contracts_not_have_resolver_field(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        assert not hasattr(contract, "resolver")


# ---------------------------------------------------------------------------
# Enum exhaustiveness checks
# ---------------------------------------------------------------------------

class TestEnumExhaustiveness:

    def test_status_has_5_values(self):
        assert len(BehavioralContractStatus) == 5

    def test_subject_type_has_11_values(self):
        assert len(BehavioralContractSubjectType) == 11

    def test_scope_type_has_13_values(self):
        assert len(BehavioralContractScopeType) == 13

    def test_obligation_type_has_13_values(self):
        assert len(BehavioralContractObligationType) == 13

    def test_prohibition_type_has_12_values(self):
        assert len(BehavioralContractProhibitionType) == 12

    def test_precondition_type_has_11_values(self):
        assert len(BehavioralContractPreconditionType) == 11

    def test_postcondition_type_has_10_values(self):
        assert len(BehavioralContractPostconditionType) == 10

    def test_evidence_type_has_12_values(self):
        assert len(BehavioralContractEvidenceType) == 12

    def test_escalation_trigger_has_11_values(self):
        assert len(BehavioralContractEscalationTrigger) == 11

    def test_escalation_action_has_6_values(self):
        assert len(BehavioralContractEscalationAction) == 6


# ---------------------------------------------------------------------------
# Scalar field validation
# ---------------------------------------------------------------------------

class TestScalarFieldValidation:

    def test_non_dict_obligation_rejected(self):
        data = _make_minimal_contract_dict()
        data["obligations"] = ["not-a-dict"]
        with pytest.raises(BehavioralContractValidationError, match="obligations"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_prohibition_rejected(self):
        data = _make_minimal_contract_dict()
        data["prohibitions"] = ["not-a-dict"]
        with pytest.raises(BehavioralContractValidationError, match="prohibitions"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_evidence_rejected(self):
        data = _make_minimal_contract_dict()
        data["evidence_requirements"] = ["not-a-dict"]
        with pytest.raises(BehavioralContractValidationError, match="evidence_requirements"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_escalation_rejected(self):
        data = _make_minimal_contract_dict()
        data["escalation_rules"] = ["not-a-dict"]
        with pytest.raises(BehavioralContractValidationError, match="escalation_rules"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_source_rejected(self):
        data = _make_minimal_contract_dict()
        data["source"] = "not-a-dict"
        with pytest.raises(BehavioralContractValidationError, match="source"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_identity_rejected(self):
        data = _make_minimal_contract_dict()
        data["identity"] = "not-a-dict"
        with pytest.raises(BehavioralContractValidationError, match="identity"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_subject_rejected(self):
        data = _make_minimal_contract_dict()
        data["subject"] = "not-a-dict"
        with pytest.raises(BehavioralContractValidationError, match="subject"):
            load_behavioral_contract_from_dict(data)

    def test_non_dict_scope_rejected(self):
        data = _make_minimal_contract_dict()
        data["scope"] = "not-a-dict"
        with pytest.raises(BehavioralContractValidationError, match="scope"):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# Runtime-future field rejection
# ---------------------------------------------------------------------------

class TestRuntimeFutureRejection:

    def test_runtime_enforcement_field_rejected(self):
        data = _make_minimal_contract_dict()
        data["runtime_enforcement"] = True
        with pytest.raises(BehavioralContractUnknownFieldError, match="runtime_enforcement"):
            load_behavioral_contract_from_dict(data)

    def test_enforcer_field_rejected(self):
        data = _make_minimal_contract_dict()
        data["enforcer"] = "strict"
        with pytest.raises(BehavioralContractUnknownFieldError, match="enforcer"):
            load_behavioral_contract_from_dict(data)

    def test_resolver_field_rejected(self):
        data = _make_minimal_contract_dict()
        data["resolver"] = {"type": "strict"}
        with pytest.raises(BehavioralContractUnknownFieldError, match="resolver"):
            load_behavioral_contract_from_dict(data)

    def test_actions_field_rejected(self):
        data = _make_minimal_contract_dict()
        data["actions"] = []
        with pytest.raises(BehavioralContractUnknownFieldError, match="actions"):
            load_behavioral_contract_from_dict(data)


# ---------------------------------------------------------------------------
# Immutability checks
# ---------------------------------------------------------------------------

class TestImmutability:

    def test_contract_is_frozen(self):
        data = _make_minimal_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        with pytest.raises(Exception):
            contract.schema_version = "2.0"  # type: ignore[misc]

    def test_identity_is_frozen(self):
        ident = BehavioralContractIdentity(
            contract_id="x", slug="x", name="x", version="1", namespace="x")
        with pytest.raises(Exception):
            ident.contract_id = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Full validations of sub-object types
# ---------------------------------------------------------------------------

class TestAllEnumsAccepted:

    def test_all_statuses_accepted(self):
        for status in BehavioralContractStatus:
            data = {**_make_minimal_contract_dict(), "status": status.value}
            contract = load_behavioral_contract_from_dict(data)
            assert contract.status == status

    def test_all_subject_types_accepted(self):
        for st in BehavioralContractSubjectType:
            data = _make_minimal_contract_dict()
            data["subject"]["subject_type"] = st.value
            contract = load_behavioral_contract_from_dict(data)
            assert contract.subject.subject_type == st

    def test_all_scope_types_accepted(self):
        for sc in BehavioralContractScopeType:
            data = _make_minimal_contract_dict()
            data["scope"]["scope_type"] = sc.value
            contract = load_behavioral_contract_from_dict(data)
            assert contract.scope.scope_type == sc


# ---------------------------------------------------------------------------
# ValidationResult fields
# ---------------------------------------------------------------------------

class TestValidationResult:

    def test_valid_result_has_contract_id(self):
        data = _make_full_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        result = validate_behavioral_contract(contract)
        assert result.contract_id == "test-contract-full"

    def test_valid_result_has_hash(self):
        data = _make_full_contract_dict()
        contract = load_behavioral_contract_from_dict(data)
        result = validate_behavioral_contract(contract)
        assert result.canonical_hash is not None
        assert len(result.canonical_hash) == 64

    def test_validation_issue_is_frozen(self):
        issue = BehavioralContractValidationIssue(
            code="TEST", message="test", field="x", severity="error")
        with pytest.raises(Exception):
            issue.code = "CHANGED"  # type: ignore[misc]

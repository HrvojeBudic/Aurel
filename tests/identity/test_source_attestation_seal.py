"""P1.4.12 source attestation seal tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.doctrine_registry import get_external_doctrine_input
from agentic_runtime.identity.external_doctrine import doctrine_grants_capability
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.operator_contract_validation import validate_operator_contract
from agentic_runtime.identity.source_attestation import (
    SOURCE_ATTESTATION_NON_GOALS,
    SourceAttestation,
    SourceKind,
    SourceValidationStatus,
    build_doctrine_source_attestation,
    build_source_attestation,
    build_source_attestation_from_validation_result,
    hash_canonical_source,
    hash_raw_source,
    source_attestation_to_dict,
)
from agentic_runtime.identity.source_bundle import load_identity_source_bundle


def test_p1412_raw_hash_proves_raw_input_not_typed_subset():
    typed = {"operator": "human"}
    raw = "operator: human\nshadow_authority_grant: true\n"
    raw_without_extra = "operator: human\n"
    assert hash_raw_source(raw) != hash_raw_source(raw_without_extra)
    assert hash_canonical_source(typed) == hash_canonical_source({"operator": "human"})


def test_p1412_canonical_hash_proves_interpreted_object():
    assert hash_canonical_source({"b": 2, "a": 1}) == hash_canonical_source({"a": 1, "b": 2})


def test_p1412_unknown_authority_field_is_rejected_and_attested():
    path = Path("config/aurel/operator_contract.yaml")
    raw = path.read_text(encoding="utf-8").replace(
        "operator_contract:\n",
        "operator_contract:\n  shadow_authority_grant: true\n",
        1,
    )
    typed = load_operator_contract(path)
    attestation = build_source_attestation_from_validation_result(
        source_kind=SourceKind.OPERATOR_CONTRACT,
        source_path=path,
        raw_source=raw,
        typed_object=typed,
        validation_result=validate_operator_contract(typed),
        validator_name="operator_contract_validator",
        validator_version="1.0.0",
    )
    assert attestation.validation_status == SourceValidationStatus.REJECTED_UNKNOWN_FIELDS
    assert attestation.rejected_unknown_fields == ("operator_contract.shadow_authority_grant",)


def test_p1412_identity_bundle_has_attestation_for_every_source():
    bundle = load_identity_source_bundle()
    assert len(bundle.attestations) == 7
    assert all(att.raw_source_hash for att in bundle.attestations.values())
    assert all(att.canonical_typed_hash for att in bundle.attestations.values())


def test_p1412_doctrine_registry_attestation_does_not_grant_capability():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    attestation = build_doctrine_source_attestation(doctrine)
    assert not doctrine_grants_capability(doctrine)
    assert attestation.source_kind == SourceKind.EXTERNAL_DOCTRINE
    assert "hash_does_not_grant_capability" in source_attestation_to_dict(attestation)["non_goals"]


def test_p1412_hash_attestation_does_not_claim_tamperproof_signature():
    assert "not_cryptographically_signed" in SOURCE_ATTESTATION_NON_GOALS
    assert "not_tamper_proof_storage" in SOURCE_ATTESTATION_NON_GOALS


def test_p1412_source_kind_is_closed_world():
    with pytest.raises(ValueError, match="unknown source_kind"):
        build_source_attestation(
            source_kind="not_a_source_kind",  # type: ignore[arg-type]
            source_path=None,
            raw_source="x",
            typed_object={},
            validation_status=SourceValidationStatus.VALID,
            validator_name="validator",
        )


def test_p1412_validation_status_is_closed_world():
    with pytest.raises(ValueError, match="unknown validation_status"):
        build_source_attestation(
            source_kind=SourceKind.CONFIG,
            source_path=None,
            raw_source="x",
            typed_object={},
            validation_status="VALIDISH",  # type: ignore[arg-type]
            validator_name="validator",
        )


def test_p1412_attestation_schema_version_and_validator_are_required():
    attestation = build_source_attestation(
        source_kind=SourceKind.CONFIG,
        source_path=None,
        raw_source="x",
        typed_object={},
        validation_status=SourceValidationStatus.VALID,
        validator_name="validator",
    )
    broken = SourceAttestation(**{**attestation.__dict__, "schema_version": ""})
    payload = source_attestation_to_dict(broken)
    assert payload["schema_version"] == ""
    assert attestation.validator_name == "validator"

"""P1.4.12 source attestation tests."""
from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from agentic_runtime.identity.source_attestation import (
    SOURCE_ATTESTATION_NON_GOALS,
    SOURCE_ATTESTATION_SCHEMA_VERSION,
    SourceAttestation,
    SourceKind,
    SourceValidationStatus,
    build_source_attestation,
    source_attestation_to_dict,
    source_hash_pair,
    validate_source_attestation,
)


@dataclass(frozen=True)
class _Source:
    name: str


def test_source_attestation_contains_raw_and_canonical_hashes():
    attestation = build_source_attestation(
        source_kind=SourceKind.CONFIG,
        source_path=None,
        raw_source="name: test\n",
        typed_object=_Source("test"),
        validation_status=SourceValidationStatus.VALID,
        validator_name="test_validator",
    )
    assert attestation.raw_source_hash
    assert attestation.canonical_typed_hash
    assert attestation.raw_source_hash != attestation.canonical_typed_hash
    assert attestation.schema_version == SOURCE_ATTESTATION_SCHEMA_VERSION


def test_source_attestation_is_json_serializable():
    attestation = build_source_attestation(
        source_kind=SourceKind.REPORT,
        source_path=None,
        raw_source="report text",
        typed_object={"report": "text"},
        validation_status=SourceValidationStatus.VALID,
        validator_name="report_validator",
    )
    payload = source_attestation_to_dict(attestation)
    assert json.loads(json.dumps(payload)) == payload


def test_missing_raw_source_fails():
    with pytest.raises(ValueError, match="raw_source is required"):
        build_source_attestation(
            source_kind=SourceKind.CONFIG,
            source_path=None,
            raw_source="",
            typed_object={},
            validation_status=SourceValidationStatus.VALID,
            validator_name="validator",
        )


def test_unknown_source_kind_fails():
    with pytest.raises(ValueError, match="unknown source_kind"):
        build_source_attestation(
            source_kind="unknown",  # type: ignore[arg-type]
            source_path=None,
            raw_source="x",
            typed_object={},
            validation_status=SourceValidationStatus.VALID,
            validator_name="validator",
        )


def test_invalid_hash_format_fails():
    attestation = SourceAttestation(
        attestation_id="id",
        schema_version=SOURCE_ATTESTATION_SCHEMA_VERSION,
        source_kind=SourceKind.CONFIG,
        source_path=None,
        source_name="config",
        raw_source_hash="bad",
        canonical_typed_hash="also_bad",
        hash_algorithm="sha256",
        validation_status=SourceValidationStatus.VALID,
        validator_name="validator",
        validator_version=None,
        rejected_unknown_fields=(),
        warnings=(),
        errors=(),
        created_at="now",
        evidence_refs=(),
    )
    errors = validate_source_attestation(attestation)
    assert "invalid raw_source_hash" in errors
    assert "invalid canonical_typed_hash" in errors


def test_attestation_validation_rejects_missing_validator():
    attestation = build_source_attestation(
        source_kind=SourceKind.CONFIG,
        source_path=None,
        raw_source="x",
        typed_object={},
        validation_status=SourceValidationStatus.VALID,
        validator_name="validator",
    )
    broken = SourceAttestation(**{**attestation.__dict__, "validator_name": ""})
    assert "empty validator_name" in validate_source_attestation(broken)


def test_rejected_unknown_fields_status_requires_field_list():
    attestation = build_source_attestation(
        source_kind=SourceKind.CONFIG,
        source_path=None,
        raw_source="x",
        typed_object={},
        validation_status=SourceValidationStatus.REJECTED_UNKNOWN_FIELDS,
        validator_name="validator",
        rejected_unknown_fields=("config.shadow_authority_grant",),
    )
    broken = SourceAttestation(**{**attestation.__dict__, "rejected_unknown_fields": ()})
    assert "REJECTED_UNKNOWN_FIELDS requires rejected_unknown_fields" in validate_source_attestation(broken)


def test_invalid_status_requires_errors():
    attestation = build_source_attestation(
        source_kind=SourceKind.CONFIG,
        source_path=None,
        raw_source="x",
        typed_object={},
        validation_status=SourceValidationStatus.INVALID,
        validator_name="validator",
        errors=("bad",),
    )
    broken = SourceAttestation(**{**attestation.__dict__, "errors": ()})
    assert "INVALID status requires errors" in validate_source_attestation(broken)


def test_source_hash_pair_separates_raw_and_canonical_hashes():
    attestation = build_source_attestation(
        source_kind=SourceKind.CONFIG,
        source_path=None,
        raw_source="name: test\n",
        typed_object={"name": "test"},
        validation_status=SourceValidationStatus.VALID,
        validator_name="validator",
    )
    pair = source_hash_pair(attestation)
    assert pair.raw_source_hash == attestation.raw_source_hash
    assert pair.canonical_typed_hash == attestation.canonical_typed_hash
    assert pair.raw_source_hash != pair.canonical_typed_hash


def test_attestation_does_not_claim_trust():
    assert "hash_does_not_prove_trust" in SOURCE_ATTESTATION_NON_GOALS
    assert "hash_does_not_grant_capability" in SOURCE_ATTESTATION_NON_GOALS
    assert "not_cryptographically_signed" in SOURCE_ATTESTATION_NON_GOALS

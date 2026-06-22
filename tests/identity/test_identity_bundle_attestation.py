"""P1.4.12 identity source bundle attestation tests."""
from __future__ import annotations

from pathlib import Path

from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.operator_contract_validation import validate_operator_contract
from agentic_runtime.identity.source_attestation import (
    SourceKind,
    SourceValidationStatus,
    build_source_attestation_from_validation_result,
    validate_source_attestations,
)
from agentic_runtime.identity.source_bundle import (
    load_identity_source_bundle,
    validate_identity_source_bundle,
)


def test_identity_source_bundle_includes_attestations():
    bundle = load_identity_source_bundle()
    assert bundle.attestations
    assert SourceKind.OPERATOR_CONTRACT in bundle.attestations


def test_identity_bundle_has_attestation_for_every_source():
    bundle = load_identity_source_bundle()
    assert set(bundle.attestations) == {
        SourceKind.IDENTITY_KERNEL,
        SourceKind.PERSONA_MANIFEST,
        SourceKind.OPERATOR_CONTRACT,
        SourceKind.COMMUNICATION_MODES,
        SourceKind.IDENTITY_PROMPT_COMPILER,
        SourceKind.SELF_MODEL_POLICY,
        SourceKind.AGENT_IDENTITY_CARD_CONFIG,
    }
    assert validate_source_attestations(tuple(bundle.attestations.values())) == ()
    assert validate_identity_source_bundle(bundle) == ()


def test_identity_bundle_attestations_have_raw_and_canonical_hashes():
    bundle = load_identity_source_bundle()
    for kind, attestation in bundle.attestations.items():
        assert attestation.raw_source_hash == bundle.raw_hashes[kind.value]
        assert attestation.canonical_typed_hash == bundle.canonical_hashes[kind.value]
        assert attestation.validation_status == SourceValidationStatus.VALID
        assert attestation.validator_name


def test_operator_contract_attestation_records_rejected_unknown_fields():
    path = Path("config/aurel/operator_contract.yaml")
    raw = path.read_text(encoding="utf-8")
    raw_with_unknown = raw.replace(
        "operator_contract:\n",
        "operator_contract:\n  shadow_authority_grant: true\n",
        1,
    )
    typed = load_operator_contract(path)
    result = validate_operator_contract(typed)
    attestation = build_source_attestation_from_validation_result(
        source_kind=SourceKind.OPERATOR_CONTRACT,
        source_path=path,
        raw_source=raw_with_unknown,
        typed_object=typed,
        validation_result=result,
        validator_name="operator_contract_validator",
        validator_version="1.0.0",
    )
    assert attestation.validation_status == SourceValidationStatus.REJECTED_UNKNOWN_FIELDS
    assert "operator_contract.shadow_authority_grant" in attestation.rejected_unknown_fields
    assert any("shadow_authority_grant" in error for error in attestation.errors)

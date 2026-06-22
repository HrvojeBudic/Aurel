"""P1.4.12 external doctrine source attestation tests."""
from __future__ import annotations

from agentic_runtime.identity.doctrine_registry import get_external_doctrine_input
from agentic_runtime.identity.external_doctrine import doctrine_grants_capability
from agentic_runtime.identity.source_attestation import (
    SourceKind,
    SourceValidationStatus,
    build_doctrine_source_attestation,
    source_attestation_to_dict,
    validate_source_attestation,
)


def test_external_doctrine_has_full_attestation():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    attestation = build_doctrine_source_attestation(doctrine)
    assert attestation.source_kind == SourceKind.EXTERNAL_DOCTRINE
    assert attestation.source_name == "agentic_os_asymmetric_teardown"
    assert attestation.raw_source_hash
    assert attestation.canonical_typed_hash
    assert attestation.validation_status == SourceValidationStatus.VALID
    assert validate_source_attestation(attestation) == ()


def test_doctrine_attestation_is_json_serializable():
    doctrine = get_external_doctrine_input("aether_v0_2")
    payload = source_attestation_to_dict(build_doctrine_source_attestation(doctrine))
    assert payload["source_kind"] == "external_doctrine"
    assert payload["source_name"] == "aether_v0_2"
    assert "hash_does_not_grant_capability" in payload["non_goals"]


def test_doctrine_attestation_does_not_grant_capability():
    doctrine = get_external_doctrine_input("abos_design_principles_v1")
    attestation = build_doctrine_source_attestation(doctrine)
    assert not doctrine_grants_capability(doctrine)
    assert "hash_does_not_grant_capability" in source_attestation_to_dict(attestation)["non_goals"]

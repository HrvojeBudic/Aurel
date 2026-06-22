"""P1.4.11 doctrine seal tests."""
from __future__ import annotations

import pytest

from agentic_runtime.identity.doctrine_mapping import map_doctrine_to_roadmap
from agentic_runtime.identity.doctrine_registry import (
    _DOCTRINE_REGISTRY,
    evaluate_doctrine_assimilation,
    get_external_doctrine_input,
    validate_doctrine_registry,
)
from agentic_runtime.identity.external_doctrine import (
    DoctrineAssimilationStatus,
    DoctrineSourceType,
    ExternalDoctrineInput,
    compute_doctrine_source_hash,
    doctrine_grants_capability,
)


@pytest.fixture(autouse=True)
def _clear_doctrine_registry():
    _DOCTRINE_REGISTRY.clear()
    yield
    _DOCTRINE_REGISTRY.clear()


def _doctrine(**overrides: object) -> ExternalDoctrineInput:
    data: dict[str, object] = {
        "doctrine_id": "seal_test",
        "name": "Seal Test Doctrine",
        "version": "1",
        "source_type": DoctrineSourceType.OPERATOR_NOTE,
        "source_path": "external://seal/test",
        "source_hash": compute_doctrine_source_hash("seal_test", "Seal Test Doctrine"),
        "ingested_at": "2026-06-21T00:00:00Z",
        "summary": "Seal test doctrine.",
        "key_principles": ("doctrine is not capability",),
        "assimilation_status": DoctrineAssimilationStatus.REFERENCE_ONLY,
        "mapped_roadmap_modules": (),
        "claim_boundaries": (),
        "risk_notes": ("Do not overclaim.",),
        "operator_accepted": True,
        "capability_evidence_refs": (),
    }
    data.update(overrides)
    return ExternalDoctrineInput(**data)  # type: ignore[arg-type]


def test_p1411_external_doctrine_does_not_grant_capability():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    assert not doctrine_grants_capability(doctrine)
    decision = evaluate_doctrine_assimilation(doctrine)
    assert "does not grant capability" in decision.reason


def test_p1411_roadmap_influencing_is_not_implementation():
    doctrine = get_external_doctrine_input("abos_design_principles_v1")
    decision = evaluate_doctrine_assimilation(doctrine)
    assert doctrine.assimilation_status == DoctrineAssimilationStatus.ROADMAP_INFLUENCING
    assert all(i.implementation_status == "not_implemented_by_doctrine" for i in decision.roadmap_impacts)


def test_p1411_agentic_os_does_not_claim_production_sandbox():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    decision = evaluate_doctrine_assimilation(doctrine)
    assert any("production sandboxing" in claim for claim in decision.blocked_claims)
    assert any("production-grade sandboxing" in claim for claim in decision.blocked_claims)


def test_p1411_abos_does_not_claim_business_deployment():
    doctrine = get_external_doctrine_input("abos_design_principles_v1")
    decision = evaluate_doctrine_assimilation(doctrine)
    assert any("ABOS deployment" in claim for claim in decision.blocked_claims)


def test_p1411_aether_does_not_claim_multimodal_intelligence():
    doctrine = get_external_doctrine_input("aether_v0_2")
    decision = evaluate_doctrine_assimilation(doctrine)
    assert any("multimodal intelligence extraction" in claim for claim in decision.blocked_claims)


def test_p1411_doctrine_requires_source_hash():
    doctrine = _doctrine(source_hash="")
    errors = validate_doctrine_registry((doctrine,))
    assert any("missing source_hash" in error for error in errors)


def test_p1411_doctrine_does_not_override_existing_roadmap_numbers():
    doctrine = _doctrine(
        assimilation_status=DoctrineAssimilationStatus.ROADMAP_INFLUENCING,
        mapped_roadmap_modules=("ABOS-1 External Replacement",),
        claim_boundaries=("Does not grant capability.",),
    )
    errors = validate_doctrine_registry((doctrine,))
    assert any("cannot renumber roadmap module" in error for error in errors)


def test_p1411_rejected_doctrine_cannot_create_roadmap_impact():
    rejected = _doctrine(assimilation_status=DoctrineAssimilationStatus.REJECTED)
    decision = evaluate_doctrine_assimilation(rejected)
    assert not decision.accepted
    assert decision.roadmap_impacts == ()
    assert map_doctrine_to_roadmap(rejected) == ()

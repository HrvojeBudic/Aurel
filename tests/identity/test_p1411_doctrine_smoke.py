"""Identity-scoped P1.4.11 doctrine smoke tests."""
from __future__ import annotations

from agentic_runtime.identity.doctrine_registry import (
    evaluate_doctrine_assimilation,
    list_external_doctrine_inputs,
    validate_doctrine_registry,
)
from agentic_runtime.identity.external_doctrine import DoctrineAssimilationStatus


def test_identity_doctrine_registry_seed_smoke():
    doctrines = list_external_doctrine_inputs()
    assert {d.doctrine_id for d in doctrines} == {
        "agentic_os_asymmetric_teardown",
        "abos_design_principles_v1",
        "aether_v0_2",
    }
    assert validate_doctrine_registry(doctrines) == ()


def test_identity_doctrine_source_hashes_and_mappings_smoke():
    for doctrine in list_external_doctrine_inputs():
        assert doctrine.source_hash
        assert doctrine.mapped_roadmap_modules
        assert doctrine.claim_boundaries
        assert doctrine.assimilation_status == DoctrineAssimilationStatus.ROADMAP_INFLUENCING


def test_identity_doctrine_roadmap_influence_is_not_implementation_smoke():
    for doctrine in list_external_doctrine_inputs():
        decision = evaluate_doctrine_assimilation(doctrine)
        assert decision.accepted
        assert decision.roadmap_impacts
        assert all(
            impact.implementation_status == "not_implemented_by_doctrine"
            for impact in decision.roadmap_impacts
        )

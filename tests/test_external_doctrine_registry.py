"""P1.4.11 External Doctrine Assimilation Registry tests."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.identity.doctrine_claim_boundaries import doctrine_claim_boundaries
from agentic_runtime.identity.doctrine_mapping import map_doctrine_to_roadmap
from agentic_runtime.identity.doctrine_registry import (
    _DOCTRINE_REGISTRY,
    evaluate_doctrine_assimilation,
    get_external_doctrine_input,
    list_external_doctrine_inputs,
    register_external_doctrine_input,
    validate_doctrine_registry,
)
from agentic_runtime.identity.external_doctrine import (
    DoctrineAssimilationStatus,
    DoctrineSourceType,
    ExternalDoctrineInput,
    RoadmapImpactType,
    compute_doctrine_source_hash,
    doctrine_assimilation_decision_to_dict,
    doctrine_grants_capability,
)


@pytest.fixture(autouse=True)
def _clear_doctrine_registry():
    _DOCTRINE_REGISTRY.clear()
    yield
    _DOCTRINE_REGISTRY.clear()


def _valid_doctrine(**overrides: object) -> ExternalDoctrineInput:
    data: dict[str, object] = {
        "doctrine_id": "operator_note_test",
        "name": "Operator Note Test",
        "version": "1",
        "source_type": DoctrineSourceType.OPERATOR_NOTE,
        "source_path": "external://operator/note/test",
        "source_hash": compute_doctrine_source_hash("operator_note_test", "Operator Note Test"),
        "ingested_at": "2026-06-21T00:00:00Z",
        "summary": "Test doctrine.",
        "key_principles": ("roadmap influence",),
        "assimilation_status": DoctrineAssimilationStatus.REFERENCE_ONLY,
        "mapped_roadmap_modules": (),
        "claim_boundaries": (),
        "risk_notes": ("Do not overclaim.",),
        "operator_accepted": True,
        "capability_evidence_refs": (),
    }
    data.update(overrides)
    return ExternalDoctrineInput(**data)  # type: ignore[arg-type]


def test_external_doctrine_input_has_source_hash():
    for doctrine in list_external_doctrine_inputs():
        assert doctrine.source_hash
        assert len(doctrine.source_hash) == 64


def test_doctrine_registry_lists_initial_inputs():
    ids = {d.doctrine_id for d in list_external_doctrine_inputs()}
    assert ids == {
        "agentic_os_asymmetric_teardown",
        "abos_design_principles_v1",
        "aether_v0_2",
    }


def test_doctrine_registry_has_unique_ids():
    doctrines = list_external_doctrine_inputs()
    ids = [d.doctrine_id for d in doctrines]
    assert len(ids) == len(set(ids))
    assert validate_doctrine_registry(doctrines) == ()


def test_doctrine_can_be_registered():
    doctrine = _valid_doctrine()
    registered = register_external_doctrine_input(doctrine)
    assert registered == doctrine
    assert get_external_doctrine_input("operator_note_test") == doctrine


def test_agentic_os_maps_to_runtime_and_eval_modules():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    impacts = map_doctrine_to_roadmap(doctrine)
    modules = {impact.roadmap_module for impact in impacts}
    assert "P1.5 Evaluation Mirror" in modules
    assert "P9 Secure Backend Arena" in modules
    assert "P20 Sovereign Agentic OS Seal" in modules


def test_abos_maps_to_business_governance_modules():
    doctrine = get_external_doctrine_input("abos_design_principles_v1")
    modules = {impact.roadmap_module for impact in map_doctrine_to_roadmap(doctrine)}
    assert "P18 Business Cockpit" in modules
    assert "P21.8 ABOS Deployment Layer" in modules


def test_aether_maps_to_research_intelligence_modules():
    doctrine = get_external_doctrine_input("aether_v0_2")
    modules = {impact.roadmap_module for impact in map_doctrine_to_roadmap(doctrine)}
    assert "P19 Aurel Researcher" in modules
    assert "P21.5 Scientific / Strategic Research Lab" in modules


def test_doctrine_status_roadmap_influencing_is_not_implemented():
    doctrine = get_external_doctrine_input("abos_design_principles_v1")
    decision = evaluate_doctrine_assimilation(doctrine)
    assert doctrine.assimilation_status == DoctrineAssimilationStatus.ROADMAP_INFLUENCING
    assert all(i.implementation_status == "not_implemented_by_doctrine" for i in decision.roadmap_impacts)


def test_doctrine_does_not_grant_capability():
    doctrine = get_external_doctrine_input("aether_v0_2")
    decision = evaluate_doctrine_assimilation(doctrine)
    assert not doctrine_grants_capability(doctrine)
    assert "does not grant capability" in decision.reason


def test_doctrine_decision_is_json_serializable():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    payload = doctrine_assimilation_decision_to_dict(evaluate_doctrine_assimilation(doctrine))
    assert json.loads(json.dumps(payload)) == payload


def test_doctrine_impact_types_are_closed_world():
    doctrine = get_external_doctrine_input("agentic_os_asymmetric_teardown")
    for impact in map_doctrine_to_roadmap(doctrine):
        assert impact.impact_type in set(RoadmapImpactType)


def test_doctrine_claim_boundaries_block_overclaims():
    doctrine = get_external_doctrine_input("abos_design_principles_v1")
    boundaries = doctrine_claim_boundaries(doctrine)
    assert any("ABOS deployment" in boundary for boundary in boundaries)
    assert any("P1.4.10 blocks" in boundary for boundary in boundaries)


def test_doctrine_without_hash_is_rejected():
    doctrine = _valid_doctrine(source_hash="")
    errors = validate_doctrine_registry((doctrine,))
    assert any("missing source_hash" in error for error in errors)


def test_doctrine_without_status_is_rejected():
    doctrine = _valid_doctrine(assimilation_status=None)
    errors = validate_doctrine_registry((doctrine,))
    assert any("missing assimilation_status" in error for error in errors)


def test_rejected_doctrine_does_not_map_to_roadmap():
    doctrine = _valid_doctrine(
        assimilation_status=DoctrineAssimilationStatus.REJECTED,
        mapped_roadmap_modules=("P99 Future Slot",),
    )
    assert map_doctrine_to_roadmap(doctrine) == ()
    errors = validate_doctrine_registry((doctrine,))
    assert any("rejected doctrine cannot create roadmap impact" in error for error in errors)


def test_implemented_status_requires_existing_capability_evidence():
    doctrine = _valid_doctrine(
        assimilation_status=DoctrineAssimilationStatus.IMPLEMENTED,
        mapped_roadmap_modules=("P1.5 Evaluation Mirror",),
        claim_boundaries=("Does not grant capability.",),
    )
    errors = validate_doctrine_registry((doctrine,))
    assert any("implemented status requires capability evidence" in error for error in errors)


def test_operator_not_accepted_doctrine_cannot_become_canon():
    doctrine = _valid_doctrine(
        assimilation_status=DoctrineAssimilationStatus.CANON_COMPATIBLE,
        operator_accepted=False,
    )
    errors = validate_doctrine_registry((doctrine,))
    assert any("operator acceptance is required" in error for error in errors)


def test_doctrine_mapping_does_not_renumber_existing_roadmap():
    doctrine = _valid_doctrine(
        assimilation_status=DoctrineAssimilationStatus.ROADMAP_INFLUENCING,
        mapped_roadmap_modules=("D1 External Number",),
        claim_boundaries=("Does not grant capability.",),
    )
    errors = validate_doctrine_registry((doctrine,))
    assert any("cannot renumber roadmap module" in error for error in errors)


def test_doctrine_registry_validation_detects_duplicate_ids():
    doctrine = _valid_doctrine()
    errors = validate_doctrine_registry((doctrine, doctrine))
    assert any("duplicate doctrine_id" in error for error in errors)

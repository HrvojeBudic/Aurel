"""P5.20 — P5-to-P6/P8/P9 handoff contracts (contract-only, not implementation)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    P5HandoffContract,
    P5HandoffTarget,
    build_all_p5_handoff_contracts,
    build_p5_to_p6_handoff,
    build_p5_to_p8_handoff,
    build_p5_to_p9_handoff,
)


def test_all_three_handoffs_build():
    p6, p8, p9 = build_all_p5_handoff_contracts()
    assert p6.contract.target_domain is P5HandoffTarget.P6_DATA_OBJECT_PLANE
    assert p8.contract.target_domain is P5HandoffTarget.P8_ATLAS_MODEL_ROUTER
    assert p9.contract.target_domain is P5HandoffTarget.P9_CUSTOS_POLICY_RUNTIME


def test_each_contract_has_required_sections():
    for handoff in build_all_p5_handoff_contracts():
        c = handoff.contract
        assert c.provided_artifacts
        assert c.required_invariants
        assert c.consumption_rules
        assert c.unavailable_claims
        assert c.risks
        assert c.implements_target_domain is False


def test_p6_handoff_names_object_plane_as_downstream_owned():
    p6 = build_p5_to_p6_handoff()
    provided = set(p6.contract.provided_artifacts)
    owned = set(p6.contract.downstream_owned)
    assert "EvidenceRef" in provided
    assert "TraceExportManifest" in provided
    # ObjectRef/DataRef/ArtifactRef are P6-owned, NOT provided by P5.
    assert "ObjectRef" in owned
    assert "DataRef" in owned
    assert "ArtifactRef" in owned
    assert "ObjectRef" not in provided


def test_p8_handoff_does_not_route_models():
    p8 = build_p5_to_p8_handoff()
    owned = set(p8.contract.downstream_owned)
    assert "model routing" in owned
    assert "model selection" in owned
    assert any("does not" in claim and "model router" in claim for claim in p8.contract.unavailable_claims)


def test_p9_handoff_does_not_enforce_policy():
    p9 = build_p5_to_p9_handoff()
    owned = set(p9.contract.downstream_owned)
    assert "policy enforcement" in owned
    assert any("enforce" in claim and "policy" in claim for claim in p9.contract.unavailable_claims)


def test_handoffs_are_deterministic():
    a = [h.to_dict() for h in build_all_p5_handoff_contracts()]
    b = [h.to_dict() for h in build_all_p5_handoff_contracts()]
    assert a == b


def test_handoff_cannot_claim_implementation():
    p6 = build_p5_to_p6_handoff()
    with pytest.raises(AurelTraceError):
        P5HandoffContract(
            handoff_id="h",
            target_domain=P5HandoffTarget.P6_DATA_OBJECT_PLANE,
            provided_artifacts=("EvidenceRef",),
            downstream_owned=("ObjectRef",),
            required_invariants=(),
            consumption_rules=(),
            unavailable_claims=("P5 does not implement P6",),
            risks=(),
            implements_target_domain=True,
        )
    # sanity: the real contract is well-formed
    assert p6.contract.implements_target_domain is False

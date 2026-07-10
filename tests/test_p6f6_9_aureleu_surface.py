"""F6.9 seal — the AUREL_CRO surface read-model (AurelEU home), one door preserved."""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.constitution import DelegationLedger, DelegationWindow
from agentic_runtime.front_server import (
    AurelEUDispatcher,
    AurelEUReadModel,
    LiveReadModels,
    ROUTES,
    mutation_routes,
)
from agentic_runtime.identity.autonomy_scale_engine import AutonomyLevel
from agentic_runtime.mandate import Mandate, MandateRegistry, MandateScope


def _runtime():
    reg = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1", scope=MandateScope(client_id="x"))])
    return build_runtime(mandate_registry=reg)


def test_aureleu_read_model_composes_governance_state():
    rt = _runtime()
    DelegationLedger(rt).grant(DelegationWindow.make(
        "operator", AutonomyLevel.A4_GOVERNED_TOOL_ACTION, valid_until=1e12))
    AurelEUDispatcher(rt).switch_persona("signal:main", "challenger")  # SHADOW switch

    d = AurelEUReadModel(rt).to_dict()
    assert d["mandates"] == ["client_x"]
    assert len(d["delegations"]) == 1
    assert d["delegations"][0]["autonomy_ceiling"] == "A4_GOVERNED_TOOL_ACTION"
    assert d["persona_switches"] and d["persona_switches"][-1]["to"] == "SHADOW"
    assert d["dn"]["verifier_veto"] == "absolute"
    assert d["claims_aureleu_dispatcher_live"] is True   # F6: flipped live


def test_aureleu_via_live_read_registry():
    rt = _runtime()
    status, payload = LiveReadModels(rt).read("/read/aureleu")
    assert status == 200 and payload["live"] is True and payload["model"] == "aureleu"
    assert payload["mandates"] == ["client_x"]
    assert payload["claims_aureleu_dispatcher_live"] is True


def test_aureleu_read_is_zero_write():
    rt = _runtime()
    reads = LiveReadModels(rt)
    before = len(list(rt.runtime.trace.replay()))
    reads.read("/read/aureleu")
    reads.read("/read/aureleu/dn")
    after = len(list(rt.runtime.trace.replay()))
    assert after == before


def test_surface_preserves_one_door():
    # AUREL_CRO adds only read models — the single mutation route is untouched.
    muts = mutation_routes()
    assert len(muts) == 1 and muts[0].path == "/proposals"
    assert all(not r.mutation for r in ROUTES if r is not muts[0])

"""F6.10 seal — the derived F6 exit seal + north-star run projection."""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.constitution import DelegationLedger, DelegationWindow
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.f6_projection import F6RunProjection
from agentic_runtime.f6_seal import (
    F6_SLICES,
    ItemStatus,
    SealStatus,
    build_f6_exit_seal,
)
from agentic_runtime.front_server import (
    AurelEUDispatcher,
    ConversationEngine,
    ProposalDispatcher,
    SignalMessage,
)
from agentic_runtime.identity.autonomy_scale_engine import AutonomyLevel
from agentic_runtime.mandate import Mandate, MandateRegistry, MandateScope


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "ok", "stub-model", {"total_tokens": 5}


# --- derived seal ---------------------------------------------------------------

def test_seal_is_sealed_with_all_slices():
    seal = build_f6_exit_seal()
    assert seal.status is SealStatus.SEALED and seal.sealed is True
    assert all(i.status is ItemStatus.PASSED for i in seal.items)
    assert len(seal.items) == len(F6_SLICES) == 11


def test_missing_report_blocks(tmp_path):
    seal = build_f6_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED and seal.sealed is False
    assert all(i.module_present for i in seal.items)  # modules import; only reports missing


def test_f5_seams_flipped_live_and_scifi_guards_false():
    seal = build_f6_exit_seal()
    flipped = {s for s, _ in seal.flipped_from_f5}
    assert {"aureleu_role_fluid_dispatcher", "mandate_resolution_enforcement"} == flipped
    assert seal.claims_aureleu_dispatcher_live is True
    assert seal.claims_mandate_enforcement_live is True
    # SCI-FI sovereignty features are hard-wired False
    assert seal.claims_multi_jurisdiction_sovereigns is False
    assert seal.claims_zero_knowledge_federation is False
    assert seal.claims_crypto_nonrepudiation_ledger is False


def test_unavailable_registry_parks_scifi():
    ids = {u.surface_id for u in build_f6_exit_seal().unavailable}
    assert {"multi_jurisdiction_sovereigns", "zero_knowledge_federation",
            "crypto_nonrepudiation_ledger"} <= ids


# --- north-star scenario end-to-end ---------------------------------------------

def test_north_star_run_end_to_end(monkeypatch):
    monkeypatch.setenv("AUREL_MANDATE", "1")
    monkeypatch.setenv("AUREL_AURELEU", "1")
    reg = MandateRegistry.from_mandates([
        Mandate(mandate_id="client_x", version="v1",
                scope=MandateScope(paths=("clients/x/",), max_risk=RiskLevel.HIGH))])
    rt = build_runtime(mandate_registry=reg)

    # operator delegates autonomy up to A4 for tool calls
    DelegationLedger(rt).grant(DelegationWindow.make(
        "operator", AutonomyLevel.A4_GOVERNED_TOOL_ACTION, valid_from=0.0,
        valid_until=1e12, action_categories=("tool_call",)))

    # 1. Signal intent under the mandate → AurelEU resolves persona (traced switch)
    engine = ConversationEngine(rt, StubRouter())
    aureleu = AurelEUDispatcher(rt)
    d = ProposalDispatcher(rt, conversation_engine=engine, aureleu=aureleu)
    d.dispatch(SignalMessage("signal:main", "op", "operator", "client_x", (),
                             "back up the client repo").to_proposal())

    A4 = AutonomyLevel.A4_GOVERNED_TOOL_ACTION
    # 2. an in-scope dispatch is authorized (mandate + delegation both hold)
    ok = aureleu.authorize_dispatch(mandate_id="client_x", autonomy_level=A4,
                                    category="tool_call", at=1.0, tool="write",
                                    path="clients/x/backup.md", risk=RiskLevel.LOW)
    assert ok.allowed is True and ok.cited_delegation_id
    # 3. an out-of-scope dispatch is denied → constitution violation
    bad = aureleu.authorize_dispatch(mandate_id="client_x", autonomy_level=A4,
                                     category="tool_call", at=1.0, tool="write",
                                     path="clients/y/secret", risk=RiskLevel.LOW)
    assert bad.allowed is False and bad.drop_to_g0 is True

    # 4. the whole chain is replayable from the trace
    proj = F6RunProjection(rt).to_dict()
    assert proj["replayable"] is True
    assert proj["aureleu"]["mandates"] == ["client_x"]
    assert proj["aureleu"]["claims_aureleu_dispatcher_live"] is True
    assert proj["aureleu"]["persona_switches"]                      # persona was resolved
    assert len(proj["constitution_violations"]) == 1               # the out-of-scope denial
    assert [e["role"] for e in proj["signal_history"]] == ["operator", "assistant"]

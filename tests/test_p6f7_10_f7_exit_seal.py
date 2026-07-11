"""F7.10 seal — the derived F7 exit seal + klijent-nula north-star projection."""
from __future__ import annotations

import argparse

from agentic_runtime import build_runtime
from agentic_runtime.cli_modules.f7_commands import cmd_corp_seal
from agentic_runtime.core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    RiskLevel,
    RuntimeStatusTransitionRecord,
)
from agentic_runtime.corp import RiskEntry, record_risk
from agentic_runtime.f7_projection import F7RunProjection
from agentic_runtime.f7_seal import (
    F7_SLICES,
    ItemStatus,
    SealStatus,
    build_f7_exit_seal,
)
from agentic_runtime.mandate import DEFAULT_MANDATE_ID


# --- derived seal ---------------------------------------------------------------

def test_seal_is_sealed_with_all_slices():
    seal = build_f7_exit_seal()
    assert seal.status is SealStatus.SEALED and seal.sealed is True
    assert all(i.status is ItemStatus.PASSED for i in seal.items)
    assert len(seal.items) == len(F7_SLICES) == 11


def test_missing_report_blocks(tmp_path):
    seal = build_f7_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED and seal.sealed is False
    assert all(i.module_present for i in seal.items)   # modules import; only reports missing


def test_f6_seams_flipped_live_and_scifi_guards_false():
    seal = build_f7_exit_seal()
    flipped = {s for s, _ in seal.flipped_from_f6}
    assert {"watchtower_alerts", "full_approval_workbench"} == flipped
    assert seal.claims_watchtower_alerts_live is True
    assert seal.claims_full_approval_workbench_live is True
    assert seal.claims_output_passport_complete is True
    # SCI-FI Business Plane features are hard-wired False
    assert seal.claims_business_simulator is False
    assert seal.claims_value_risk_studio is False
    assert seal.claims_rnd_knowledge_transfer_nlp is False
    assert seal.claims_forecasting is False


def test_unavailable_registry_parks_later_and_scifi():
    ids = {u.surface_id for u in build_f7_exit_seal().unavailable}
    assert {"forecasting_burn_eta", "auto_risk_detection", "billing_console"} <= ids
    assert {"business_simulator", "value_risk_studio", "rnd_knowledge_transfer_nlp"} <= ids


def test_blocked_seal_does_not_claim_flips(tmp_path):
    # A BLOCKED seal must not claim the flips live (derived, never self-assigned).
    seal = build_f7_exit_seal(reports_dir=str(tmp_path))
    assert seal.claims_watchtower_alerts_live is False
    assert seal.claims_full_approval_workbench_live is False


# --- CLI ------------------------------------------------------------------------

def test_cli_corp_seal_returns_sealed(capsys):
    rc = cmd_corp_seal(argparse.Namespace(json=False))
    assert rc == 0
    assert "SEALED" in capsys.readouterr().out


# --- north-star scenario end-to-end (klijent nula) ------------------------------

def _seed_client_zero_run(rt):
    """A klijent-nula run under the default mandate: in-scope run + a budget deny."""
    trace = rt.runtime.trace
    budget = rt.runtime.budget
    # 1. an in-scope run under klijent nula's default mandate reaches success
    for frm, to, rc in (("planned", "running", "dispatch"), ("running", "completed", "verified")):
        trace.append_status_transition(RuntimeStatusTransitionRecord.make(
            run_id="job-zero-run", intent_id="i", issuer_card_id="card-1",
            from_status=frm, to_status=to, reason_code=rc, message="m",
            mandate_id=DEFAULT_MANDATE_ID))
    # 2. cost attributed to the default mandate
    budget.begin_run("job-zero-run", "card-1", "i")
    budget.set_mandate(DEFAULT_MANDATE_ID)
    budget.charge_llm(usage=None, usd=0.20)
    # 3. an out-of-scope attempt is denied → a Watchtower-visible budget deny
    trace.append_budget_decision(BudgetDecisionRecord.make(
        run_id="job-zero-run", intent_id="i", issuer_card_id="card-1",
        metric="max_estimated_cost_cents", verdict="deny", used=600, limit=500,
        mandate_id=DEFAULT_MANDATE_ID))
    # 4. an approval receipt + a governed risk entry
    trace.append_approval_receipt(ApprovalReceiptRecord.make(
        run_id="job-zero-run", issuer_card_id="card-1", request_id="rq", receipt_id="rc",
        tool="write_file", risk_class="low", outcome="approve", reason="ok",
        decided_by="operator", mandate_id=DEFAULT_MANDATE_ID))
    record_risk(trace, RiskEntry(risk_id="rk1", job_id="job-zero", client_id="client-zero",
                                 likelihood=2, impact=3, tier=RiskLevel.MEDIUM),
                mandate_id=DEFAULT_MANDATE_ID)


def test_north_star_run_end_to_end(monkeypatch):
    monkeypatch.setenv("AUREL_WATCHTOWER", "1")
    rt = build_runtime()
    _seed_client_zero_run(rt)

    proj = F7RunProjection(rt).to_dict()
    assert proj["replayable"] is True

    # portfolio: klijent nula → job-zero → the run, with cost
    client = next(c for c in proj["portfolio"]["clients"] if c["client_id"] == "client-zero")
    job = next(j for j in client["jobs"] if j["job_id"] == "job-zero")
    assert {r["run_id"] for r in job["runs"]} == {"job-zero-run"}
    assert job["runs"][0]["status"] == "completed"

    # cost attributed to klijent nula
    assert proj["cost"]["available"] is True
    assert round(proj["cost"]["by_client"]["client-zero"]["estimated_cost_cents"], 3) == 20.0

    # the out-of-scope deny surfaces as a live Watchtower alert
    assert proj["watchtower"]["status"] == "LIVE"
    assert any(a["kind"] == "budget_deny" for a in proj["watchtower"]["alerts"])

    # the Output Passport for job-zero verifies (intact chain PASSes)
    assert proj["evidence_passport"]["output_passport"] is True
    assert proj["evidence_passport"]["verified"] is True

    # the governed risk entry is in the register
    assert [r["risk_id"] for r in proj["risks"]["entries"]] == ["rk1"]

    # budget governance is a live projection (default mandate is UNBOUNDED, honest)
    assert proj["budget_governance"]["available"] is True

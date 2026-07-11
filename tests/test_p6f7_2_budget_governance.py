"""F7.2 seal — budget governance (allocation vs. spend per client / job / mandate).

A report, never enforcement: allocation from `MandateScope.budget_cents`, spent
from F7.1 cost attribution, remaining = allocation − spent, deny_count from the
trace. A mandate with no cap is UNBOUNDED (never a fabricated number); an
unresolvable mandate is UNAVAILABLE; forecasting stays a declared UNAVAILABLE seam.
"""
from __future__ import annotations

from agentic_runtime.budget import BudgetLedger
from agentic_runtime.core_types import BudgetDecisionRecord, RiskLevel
from agentic_runtime.corp import (
    CLIENT_ZERO_ID,
    ClientBudgetView,
    CorpRegistry,
    JobRecord,
    client_zero,
)
from agentic_runtime.mandate import (
    DEFAULT_MANDATE_ID,
    Mandate,
    MandateRegistry,
    MandateScope,
    default_mandate,
)
from agentic_runtime.trace import InMemoryTraceLedger


def _bounded_mandate(mid="m-bounded", cents=1000.0):
    return Mandate(mandate_id=mid, version="v1",
                   scope=MandateScope(client_id=CLIENT_ZERO_ID, budget_cents=cents,
                                      max_risk=RiskLevel.MEDIUM))


def _registry_with_bounded_job():
    """Klijent nula with one job under a bounded mandate (1000 cents cap)."""
    mandate = _bounded_mandate()
    mreg = MandateRegistry.from_mandates([default_mandate(), mandate])
    job = JobRecord(job_id="job-bounded", client_id=CLIENT_ZERO_ID,
                    mandate_ids=(mandate.mandate_id,))
    return CorpRegistry.from_records([client_zero()], [job], mandate_registry=mreg), mandate


def _charge(ledger, mandate_id, usd):
    ledger.begin_run("r", "a", "i")
    ledger.set_mandate(mandate_id)
    ledger.charge_llm(usage=None, usd=usd)      # usd*100 cents


# --- allocation from mandate ------------------------------------------------------

def test_allocation_from_bounded_mandate():
    reg, mandate = _registry_with_bounded_job()
    led = BudgetLedger()
    _charge(led, mandate.mandate_id, usd=2.00)   # 200 cents spent
    view = ClientBudgetView.build(led, reg)
    m = view.by_mandate[mandate.mandate_id]
    assert m["allocation_status"] == "AVAILABLE"
    assert m["allocation_cents"] == 1000.0
    assert round(m["spent_cents"], 3) == 200.0
    assert round(m["remaining_cents"], 3) == 800.0   # 1000 - 200


def test_rollup_to_job_and_client():
    reg, mandate = _registry_with_bounded_job()
    led = BudgetLedger()
    _charge(led, mandate.mandate_id, usd=1.50)   # 150 cents
    view = ClientBudgetView.build(led, reg)
    job = view.by_job["job-bounded"]
    assert job["allocation_cents"] == 1000.0 and round(job["spent_cents"], 3) == 150.0
    assert round(job["remaining_cents"], 3) == 850.0
    client = view.by_client[CLIENT_ZERO_ID]
    assert client["allocation_cents"] == 1000.0 and round(client["remaining_cents"], 3) == 850.0


# --- unbounded / unavailable honesty ----------------------------------------------

def test_no_cap_mandate_is_unbounded():
    # klijent nula's default mandate has budget_cents == 0 ⇒ UNBOUNDED, not a fake 0.
    from agentic_runtime.corp import default_corp_registry
    reg = default_corp_registry()
    led = BudgetLedger()
    _charge(led, DEFAULT_MANDATE_ID, usd=0.50)
    view = ClientBudgetView.build(led, reg)
    m = view.by_mandate[DEFAULT_MANDATE_ID]
    assert m["allocation_status"] == "UNBOUNDED"
    assert m["allocation_cents"] is None and m["remaining_cents"] is None
    assert round(m["spent_cents"], 3) == 50.0           # spend still shown honestly


def test_unresolvable_mandate_is_unavailable():
    # A job referencing a mandate the registry can't resolve ⇒ UNAVAILABLE (fail-closed).
    mreg = MandateRegistry.from_mandates([default_mandate()])
    job = JobRecord(job_id="j", client_id=CLIENT_ZERO_ID, mandate_ids=("ghost",))
    # build the corp registry without validating (no mandate_registry given at build)
    reg = CorpRegistry.from_records([client_zero()], [job])
    view = ClientBudgetView.build(BudgetLedger(), reg, mandate_registry=mreg)
    assert view.by_mandate["ghost"]["allocation_status"] == "UNAVAILABLE"
    assert view.by_mandate["ghost"]["allocation_cents"] is None


def test_no_corp_registry_unavailable():
    view = ClientBudgetView.build(BudgetLedger(), None)
    assert view.available is False and "no corp registry" in view.reason


# --- deny count from trace --------------------------------------------------------

def test_deny_count_from_trace():
    reg, mandate = _registry_with_bounded_job()
    trace = InMemoryTraceLedger("run-x")
    for _ in range(2):
        trace.append_budget_decision(BudgetDecisionRecord.make(
            run_id="run-x", intent_id="i", issuer_card_id="a",
            metric="max_estimated_cost_cents", verdict="deny", used=1200, limit=1000,
            mandate_id=mandate.mandate_id))
    view = ClientBudgetView.build(BudgetLedger(), reg, trace)
    assert view.by_mandate[mandate.mandate_id]["deny_count"] == 2
    assert view.by_job["job-bounded"]["deny_count"] == 2


# --- forecasting stays a seam -----------------------------------------------------

def test_forecasting_is_unavailable_seam():
    reg, _ = _registry_with_bounded_job()
    d = ClientBudgetView.build(BudgetLedger(), reg).to_dict()
    assert d["available"] is True
    assert d["forecasting"]["status"] == "UNAVAILABLE"    # this view never predicts


def test_spent_unknown_without_ledger():
    reg, mandate = _registry_with_bounded_job()
    view = ClientBudgetView.build(None, reg)              # no ledger ⇒ spend unknown
    m = view.by_mandate[mandate.mandate_id]
    assert m["allocation_cents"] == 1000.0                # allocation still known
    assert m["spent_cents"] is None and m["remaining_cents"] is None  # honest, not zero

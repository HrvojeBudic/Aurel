"""F7.1 seal — cost attribution (per-mandate bucket + client pivot).

The ledger gains an additive `per_mandate` bucket that fills only while a mandate
context is bound (so the no-mandate world is byte-identical), plus mandate stamping
on budget-decision trace records. `CostAttributionView` pivots that up through the
Corp registry to job → client. Attribution is a report, never a verdict.
"""
from __future__ import annotations

from agentic_runtime.budget import BudgetLedger
from agentic_runtime.corp import (
    CLIENT_ZERO_ID,
    JOB_ZERO_ID,
    CostAttributionView,
    JobRecord,
    client_zero,
    default_corp_registry,
)
from agentic_runtime.mandate import DEFAULT_MANDATE_ID, default_registry


class _Usage:
    """Minimal TokenUsage stand-in (substantiated real usage)."""

    def __init__(self, prompt=100, completion=50, total=150, reasoning=0):
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = total
        self.reasoning_tokens = reasoning


def _charge_run(ledger: BudgetLedger, mandate_id: str, *, usd=0.10):
    ledger.begin_run("run-1", "agent-1", "intent-1")
    ledger.set_mandate(mandate_id)
    ledger.precheck_command("cmd-1", "write_file", "agent-1")
    ledger.charge_tool("agent-1")
    ledger.charge_sandbox_execution()
    ledger.charge_memory_write()
    ledger.charge_llm(usage=_Usage(), usd=usd)


# --- byte-identical when no mandate is set --------------------------------------

def _strip_ts(per_run):
    return {rid: {k: v for k, v in d.items() if k != "started_at"}
            for rid, d in per_run.items()}


def test_no_mandate_context_is_byte_identical():
    a = BudgetLedger()
    _charge_run(a, "")            # set_mandate("") ⇒ no mandate bound
    b = BudgetLedger()
    # Same charges without ever calling set_mandate at all.
    b.begin_run("run-1", "agent-1", "intent-1")
    b.precheck_command("cmd-1", "write_file", "agent-1")
    b.charge_tool("agent-1")
    b.charge_sandbox_execution()
    b.charge_memory_write()
    b.charge_llm(usage=_Usage(), usd=0.10)
    assert a.per_mandate == {} and b.per_mandate == {}          # bucket never created
    assert a.snapshot() == b.snapshot()                          # existing output identical
    assert _strip_ts(a.per_run) == _strip_ts(b.per_run)         # counters identical (ts aside)


# --- per-mandate bucket fills under a mandate ------------------------------------

def test_charges_accrue_to_per_mandate_bucket():
    led = BudgetLedger()
    _charge_run(led, "m-alpha", usd=0.10)
    bucket = led.per_mandate["m-alpha"]
    assert bucket["commands"] == 1
    assert bucket["tool_calls"] == 1
    assert bucket["sandbox_executions"] == 1
    assert bucket["memory_writes"] == 1
    assert bucket["llm_calls"] == 1
    assert bucket["estimated_tokens"] == 150
    assert round(bucket["estimated_cost_cents"], 3) == 10.0      # 0.10 usd -> 10 cents
    assert bucket["substantiated_charges"] == 1                  # real usage
    assert bucket["estimate_only_charges"] == 0


def test_estimate_only_charge_is_marked_honestly():
    led = BudgetLedger()
    led.begin_run("r", "a", "i")
    led.set_mandate("m")
    led.charge_llm(usage=None, usd=0.01)                        # no real usage -> estimate
    assert led.per_mandate["m"]["estimate_only_charges"] == 1
    assert led.per_mandate["m"]["substantiated_charges"] == 0


def test_two_mandates_are_separated():
    led = BudgetLedger()
    led.begin_run("r", "a", "i")
    led.set_mandate("m1")
    led.charge_tool("a")
    led.set_mandate("m2")
    led.charge_tool("a")
    led.charge_tool("a")
    assert led.per_mandate["m1"]["tool_calls"] == 1
    assert led.per_mandate["m2"]["tool_calls"] == 2


# --- CostAttributionView pivot --------------------------------------------------

def test_view_pivots_mandate_to_job_to_client():
    reg = default_corp_registry()                               # klijent nula, job under DEFAULT_MANDATE_ID
    led = BudgetLedger()
    _charge_run(led, DEFAULT_MANDATE_ID, usd=0.10)
    view = CostAttributionView.from_ledger(led, reg)
    assert view.available is True
    assert view.by_mandate[DEFAULT_MANDATE_ID]["tool_calls"] == 1
    assert view.by_job[JOB_ZERO_ID]["client_id"] == CLIENT_ZERO_ID
    assert view.by_job[JOB_ZERO_ID]["metrics"]["tool_calls"] == 1
    assert view.by_client[CLIENT_ZERO_ID]["tool_calls"] == 1
    assert round(view.by_client[CLIENT_ZERO_ID]["estimated_cost_cents"], 3) == 10.0
    assert view.unattributed["tool_calls"] == 0.0


def test_view_reports_unattributed_mandate_honestly():
    reg = default_corp_registry()
    led = BudgetLedger()
    _charge_run(led, "orphan-mandate", usd=0.05)               # referenced by no job
    view = CostAttributionView.from_ledger(led, reg)
    assert view.by_job == {}                                    # nothing pivoted
    assert view.unattributed["tool_calls"] == 1.0
    assert round(view.unattributed["estimated_cost_cents"], 3) == 5.0


def test_view_without_corp_registry_is_mandate_only():
    led = BudgetLedger()
    _charge_run(led, "m", usd=0.05)
    view = CostAttributionView.from_ledger(led, None)
    assert view.available is True and "no corp registry" in view.reason
    assert view.by_mandate["m"]["tool_calls"] == 1
    assert view.unattributed["tool_calls"] == 1.0              # can't pivot ⇒ honest unattributed


def test_view_unavailable_without_ledger():
    view = CostAttributionView.from_ledger(None, default_corp_registry())
    assert view.available is False
    assert "no budget ledger" in view.reason
    assert view.by_mandate == {}


# --- trace cross-check ----------------------------------------------------------

def _seed(trace):
    """Prime the ledger with one entry so budget decisions are traced.

    `BudgetLedger._trace_budget` guards with ``if not self._trace`` and an
    ``InMemoryTraceLedger`` defines ``__len__``, so an empty ledger is falsy and
    the first budget decision on it is skipped (a pre-existing quirk; in a real
    run the trace already carries status transitions). We seed like reality does.
    """
    from agentic_runtime.core_types import BudgetDecisionRecord
    trace.append_budget_decision(BudgetDecisionRecord.make(
        run_id="seed", intent_id="seed", issuer_card_id="seed",
        metric="seed", verdict="allow", used=0, limit=1))


def test_trace_crosscheck_matches_ledger_cost():
    from agentic_runtime.trace import InMemoryTraceLedger

    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    led = BudgetLedger()
    led.bind_trace(trace)
    led.begin_run("run-x", "agent-1", "intent-1")
    led.set_mandate("m-cross")
    led.charge_llm(usage=_Usage(), usd=0.20)                   # 20 cents, traced with mandate_id

    from_trace = CostAttributionView.cost_cents_by_mandate_from_trace(trace)
    ledger_cost = led.per_mandate["m-cross"]["estimated_cost_cents"]
    assert round(from_trace["m-cross"], 3) == round(ledger_cost, 3) == 20.0


def test_trace_records_carry_mandate_id():
    from agentic_runtime.trace import InMemoryTraceLedger

    trace = InMemoryTraceLedger("run-y")
    _seed(trace)
    led = BudgetLedger()
    led.bind_trace(trace)
    led.begin_run("run-y", "agent-1", "intent-1")
    led.set_mandate("m-stamp")
    led.charge_tool("agent-1")
    stamped = [ev for ev in trace.replay()
               if ev.get("kind") == "budget_decision" and ev.get("mandate_id") == "m-stamp"]
    assert stamped, "budget-decision records should carry the bound mandate_id"


def test_empty_mandate_id_not_stamped_in_trace():
    from agentic_runtime.trace import InMemoryTraceLedger

    trace = InMemoryTraceLedger("run-z")
    _seed(trace)
    led = BudgetLedger()
    led.bind_trace(trace)
    led.begin_run("run-z", "agent-1", "intent-1")
    # no set_mandate ⇒ current_mandate_id "" ⇒ budget records omit mandate_id (F6.1 default)
    led.charge_tool("agent-1")
    real = [ev for ev in trace.replay()
            if ev.get("kind") == "budget_decision" and ev.get("metric") != "seed"]
    assert real and all("mandate_id" not in ev for ev in real)

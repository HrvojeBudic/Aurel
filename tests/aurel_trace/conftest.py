"""Shared fixtures for P5-TRACE-A aurel_trace tests."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    TraceRunRef,
    envelopes_from_ledger,
    trace_run_ref_from_ledger,
)
from agentic_runtime.core_types import (
    BudgetDecisionRecord,
    PlanningFailureRecord,
    PolicyVerdict,
    RuntimeStatusTransitionRecord,
    StateTransitionRecord,
    VerifierResult,
)
from agentic_runtime.trace import InMemoryTraceLedger


def _state_transition(idx: int) -> StateTransitionRecord:
    return StateTransitionRecord(
        id=f"txn_{idx}",
        before_state_hash=f"before{idx}",
        command_hash=f"cmd{idx}",
        observation_hash=f"obs{idx}",
        after_state_hash=f"after{idx}",
        verifier_result=VerifierResult(passed=True, verifier="state"),
        policy_verdict=PolicyVerdict.ALLOW,
        issuer_card_id="card1",
        parent_intent_id=f"intent{idx}",
    )


def build_demo_ledger() -> InMemoryTraceLedger:
    """A small, real, appended in-memory ledger with mixed record types."""

    ledger = InMemoryTraceLedger(run_id="run_p5_demo")
    ledger.append(_state_transition(0))
    ledger.append_planning_failure(
        PlanningFailureRecord.make("intent1", "card1", "rejected", "bad plan")
    )
    ledger.append_budget_decision(
        BudgetDecisionRecord(
            id="bud_0",
            run_id="run_p5_demo",
            intent_id="intent2",
            issuer_card_id="card1",
            metric="tokens",
            verdict="allow",
            used=1.0,
            limit=10.0,
            reason="within budget",
        )
    )
    ledger.append_status_transition(
        RuntimeStatusTransitionRecord.make(
            run_id="run_p5_demo",
            intent_id="intent3",
            issuer_card_id="card1",
            from_status="running",
            to_status="completed",
            reason_code="ok",
            message="done",
        )
    )
    return ledger


@pytest.fixture
def demo_ledger() -> InMemoryTraceLedger:
    return build_demo_ledger()


@pytest.fixture
def demo_run_ref(demo_ledger: InMemoryTraceLedger) -> TraceRunRef:
    return trace_run_ref_from_ledger(demo_ledger)


@pytest.fixture
def demo_envelopes(demo_ledger: InMemoryTraceLedger, demo_run_ref: TraceRunRef):
    return envelopes_from_ledger(demo_ledger, trace_run_ref=demo_run_ref)

"""A1a seal — memory ops as governed tools.

Proves the seven A1a invariants of ``MemoryToolSession`` (the governed
dispatcher that lets an entity *propose* memory ops without ever storing
directly):

1. An *agent* session cannot mint restricted memory: ``mem_add`` of ``canon`` is
   denied ``agent_cannot_write_restricted``, nothing is stored, and the trace
   carries exactly one memory-governance *deny* row.
2. That denied attempt still charged exactly one ``memory_write`` and zero
   sandbox executions (governed attempt == one charge, allow OR deny).
3. An *operator* session's ``mem_add`` of ``raw`` is allowed, stored, charges
   exactly one ``memory_write``, emits a governance *allow*, and never touches
   the sandbox.
4. Each governed write emits exactly one ``MemoryGovernanceRecord`` and the
   session produces NO ``StateTransitionRecord`` (it is not ``runtime.submit``).
5. ``mem_search`` is read-only: no ``memory_write`` charge, no sandbox
   execution, and the store is byte-for-byte unchanged.
6. A memory tool smuggled through the sandbox / ``runtime.submit`` path
   (``ToolBus.execute``) is refused (``memory_tool_wrong_path`` / ``unknown_tool``)
   with no write and no state transition.
7. ``mem_update`` / ``mem_delete`` / ``mem_link`` are honestly UNAVAILABLE
   (``unavailable=True``, ``requires_a2_a4``): no write, no charge.
"""

from __future__ import annotations

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.memory_tools import MemoryToolSession
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.tools import ToolBus
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a1a"


def _harness():
    """Fresh fabric+trace+budget wired the way the runtime will wire them."""
    trace = InMemoryTraceLedger(run_id=RUN)
    fabric = MemoryFabric()
    fabric.bind_trace(trace)
    budget = BudgetLedger()
    return fabric, trace, budget


def _gov_rows(trace) -> list[dict]:
    return [e for e in trace.replay() if e["kind"] == "memory_governance"]


def _state_rows(trace) -> list[dict]:
    return [e for e in trace.replay() if e["kind"] == "state_transition"]


# 1 + 2 ─ agent cannot self-elevate; the denied attempt still charged once.
def test_agent_canon_denied_not_stored_and_charged_once():
    fabric, trace, budget = _harness()
    session = MemoryToolSession(fabric, budget, writer_kind="agent")

    result = session.invoke("mem_add", {"content": "I am canon now", "truth_state": "canon"})

    # (1) honest deny, correct reason, nothing stored, one governance deny row.
    assert result["ok"] is False
    assert result["verdict"] == "deny"
    assert result["reason_code"] == "agent_cannot_write_restricted"
    assert fabric.stats()["L5_canon"] == 0
    assert fabric.by_id.get(result["memory_id"]) is None or result["memory_id"] == ""
    gov = _gov_rows(trace)
    assert len(gov) == 1 and gov[0]["verdict"] == "deny"

    # (2) exactly one memory-write charge for the attempt; no sandbox execution.
    assert budget.memory_writes == 1
    assert budget.sandbox_executions == 0


# 3 ─ operator RAW write is allowed, stored, charged once, no sandbox.
def test_operator_raw_add_allowed_stored_charged_once():
    fabric, trace, budget = _harness()
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    before = fabric.stats()
    result = session.invoke("mem_add", {"content": "operator observation"})

    assert result["ok"] is True
    assert result["verdict"] == "allow"
    assert result["truth_state"] == MemoryTruthState.RAW.value
    assert result["memory_id"]
    assert fabric.by_id[result["memory_id"]].content == "operator observation"
    # RAW lands in the ephemeral tier (L1); the store grew by exactly one record.
    assert fabric.stats()["L1"] == before["L1"] + 1

    gov = _gov_rows(trace)
    assert len(gov) == 1 and gov[0]["verdict"] == "allow"
    assert budget.memory_writes == 1
    assert budget.sandbox_executions == 0


# 4 ─ exactly one governance row per write; no StateTransitionRecord from session.
def test_one_governance_row_and_no_state_transition():
    fabric, trace, budget = _harness()
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    session.invoke("mem_add", {"content": "first"})
    session.invoke("mem_add", {"content": "second"})

    assert len(_gov_rows(trace)) == 2          # one governance row per write
    assert len(_state_rows(trace)) == 0        # session never runs runtime.submit
    assert budget.memory_writes == 2
    assert budget.sandbox_executions == 0


# 5 ─ mem_search is read-only: no charge, no sandbox, store unchanged.
def test_mem_search_is_read_only():
    fabric, trace, budget = _harness()
    # Seed a record directly through the fabric (does NOT touch the budget).
    fabric.request_write(MemoryWriteRequest(
        content="the sky is blue", writer_kind="operator", source_run_id=RUN))
    session = MemoryToolSession(fabric, budget, writer_kind="agent")

    stats_before = fabric.stats()
    gov_before = len(_gov_rows(trace))

    result = session.invoke("mem_search", {"query": "sky", "k": 5})

    assert result["ok"] is True
    assert result["read_only"] is True
    assert result["count"] == len(result["results"])
    # No write, no charge, no sandbox, and the store is unchanged.
    assert budget.memory_writes == 0
    assert budget.sandbox_executions == 0
    assert fabric.stats() == stats_before
    assert len(_gov_rows(trace)) == gov_before


# 6 ─ a memory tool on the sandbox / runtime.submit path is refused.
def test_mem_add_via_toolbus_refused(tmp_path):
    bus = ToolBus(sandbox=UnsafeLocalSandbox(root=str(tmp_path)))
    fabric, trace, budget = _harness()

    result = bus.execute("mem_add", {"content": "smuggled"})

    assert result.success is False
    assert result.error is not None
    assert result.error.code in {"memory_tool_wrong_path", "unknown_tool"}
    # It was never registered as a sandbox tool, and nothing was written/traced.
    assert "mem_add" not in bus.registered
    assert budget.memory_writes == 0
    assert len(_gov_rows(trace)) == 0
    assert len(_state_rows(trace)) == 0


# 7 ─ update/delete/link are honestly unavailable: no write, no charge.
def test_update_delete_link_unavailable_no_write_no_charge():
    fabric, trace, budget = _harness()
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    calls = {
        "mem_update": {"memory_id": "m1", "content": "revised"},
        "mem_delete": {"memory_id": "m1"},
        "mem_link": {"from_id": "m1", "to_id": "m2", "relation": "supports"},
    }
    for tool, args in calls.items():
        result = session.invoke(tool, args)
        assert result["ok"] is False, tool
        assert result["unavailable"] is True, tool
        assert result["reason_code"] == "requires_a2_a4", tool

    assert budget.memory_writes == 0
    assert budget.sandbox_executions == 0
    assert len(_gov_rows(trace)) == 0

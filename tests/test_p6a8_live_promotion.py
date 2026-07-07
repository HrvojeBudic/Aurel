"""A8 seal — live promotion wiring + durable fail-closed (final Track A phase).

A8a (durable factory / fail-closed fallback):
1. flag ON + a working backend ⇒ ``build_runtime`` wires a ``DurableMemoryFabric``.
2. flag ON + an unavailable backend ⇒ FAIL CLOSED to the in-RAM ``MemoryFabric``,
   honestly non-durable (never a fake durability claim).
3. flag OFF (default) ⇒ a plain in-RAM ``MemoryFabric`` (byte-identical to today).

A8b (live promotion driver):
4. command memory routes through the governed funnel — one charge + one write row
   for the candidate, promotions traced (no bypass).
5. promotion monotonicity: two distinct successful traces ⇒ procedural; a failed
   run promotes nothing (the P0.9 law), and the bridge writes as ``runtime`` (an
   agent cannot drive it or self-elevate).
6. the driver is flag-gated and wired into the runtime (OFF ⇒ never runs).
"""

from __future__ import annotations

from agentic_runtime import (MemoryFabric, MemoryTruthState, MemoryWriteRequest,
                             build_runtime)
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.durable_memory import DurableMemoryFabric
from agentic_runtime.evaluation.memory_promotion_bridge import (
    MemoryCandidateBridge, command_signature)
from agentic_runtime.memory_persistence import ExternalMemoryBackend, FileMemoryBackend
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a8"
FLAG = "AUREL_DURABLE_MEMORY"


def _kernel(tmp_path):
    return build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
                         trace_dir=str(tmp_path))


# 1 ─ A8a: flag ON + working backend ⇒ DurableMemoryFabric.
def test_a8a_durable_on_wires_durable_fabric(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    kernel = _kernel(tmp_path)
    assert isinstance(kernel.memory, DurableMemoryFabric)
    assert kernel.memory.durable_enabled is True


# 2 ─ A8a: durable requested but backend unavailable ⇒ fail closed to in-RAM.
def test_durable_unavailable_fails_closed_in_ram(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    kernel = build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
                           trace_dir=str(tmp_path),
                           memory_backend=ExternalMemoryBackend(uri="s3://nope"))
    # Still builds; honestly in-RAM (not durable), no fake durability.
    assert isinstance(kernel.memory, MemoryFabric)
    assert not isinstance(kernel.memory, DurableMemoryFabric)
    assert getattr(kernel.memory, "durable_enabled", False) is False
    # The runtime remains fully functional in RAM.
    d = kernel.memory.request_write(MemoryWriteRequest(
        content="in-ram works", writer_kind="operator",
        source_run_id=kernel.trace.run_id))
    assert d.allowed


# 3 ─ A8a: flag OFF ⇒ plain in-RAM fabric (byte-identical wiring).
def test_a8a_flag_off_byte_identical(tmp_path, monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    kernel = _kernel(tmp_path)
    assert type(kernel.memory) is MemoryFabric      # exactly the pre-A8 fabric
    assert kernel.runtime._durable_memory_enabled is False
    assert kernel.runtime._memory_promotion_bridge is None   # never constructed


def _valid_trace_ids(fab, trace, n):
    """Real trace-entry ids (from seeded governed writes) for source_trace_ids."""
    for i in range(n):
        fab.request_write(MemoryWriteRequest(
            content=f"seed {i}", writer_kind="operator", source_run_id=RUN))
    return [e.id for e in trace]


def _mem_rows(trace, action, memory_id):
    return [e for e in trace.replay()
            if e["kind"] == "memory_governance" and e["action"] == action
            and e["memory_id"] == memory_id]


# 4 + 5 ─ A8b: governance-routed promotion, monotonicity, failed-run, runtime-only.
def test_a8b_promotion_monotonicity_and_governance():
    trace = InMemoryTraceLedger(run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(trace)
    budget = BudgetLedger()
    t1, t2 = _valid_trace_ids(fab, trace, 2)

    bridge = MemoryCandidateBridge()
    sig = command_signature("build", {"target": "x"})

    # First verified success ⇒ candidate created + promoted to verified (evidence).
    o1 = bridge.observe(fabric=fab, budget=budget, signature=sig,
                        content="procedure candidate", run_id=RUN,
                        trace_id=t1, run_succeeded=True)
    mem_id = o1.memory_id
    assert fab.by_id[mem_id].truth_state is MemoryTruthState.VERIFIED
    # Runtime-authored, not agent — an agent cannot drive this path.
    assert fab.by_id[mem_id].created_by == "runtime"

    # Second DISTINCT successful trace ⇒ verified → procedural.
    o2 = bridge.observe(fabric=fab, budget=budget, signature=sig,
                        content="procedure candidate", run_id=RUN,
                        trace_id=t2, run_succeeded=True)
    assert o2.promoted_to == MemoryTruthState.PROCEDURAL.value
    assert fab.by_id[mem_id].truth_state is MemoryTruthState.PROCEDURAL

    # A failed run promotes NOTHING (P0.9) and does not regress the state.
    o3 = bridge.observe(fabric=fab, budget=budget, signature=sig,
                        content="procedure candidate", run_id=RUN,
                        trace_id=t2, run_succeeded=False)
    assert o3.reason_code == "failed_run_no_promotion"
    assert bridge.state_for(sig) == MemoryTruthState.PROCEDURAL.value

    # Governance routing: exactly one CANDIDATE write (one charge) + traced promotions.
    assert budget.memory_writes == 1                       # only the candidate write
    assert len(_mem_rows(trace, "write", mem_id)) == 1     # one governance write row
    assert len(_mem_rows(trace, "promote", mem_id)) == 2   # verified + procedural


# 6 ─ A8b wiring: the driver is flag-gated on the runtime.
def test_a8b_wired_and_flag_gated(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    on = _kernel(tmp_path)
    assert on.runtime._durable_memory_enabled is True

    monkeypatch.delenv(FLAG, raising=False)
    off = build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path / "off")),
                        trace_dir=str(tmp_path / "off"))
    assert off.runtime._durable_memory_enabled is False

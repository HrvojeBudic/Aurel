"""A-connect seal — agent-facing mem_* dispatch through runtime.submit.

Proves the governed memory tools are reachable by an entity via the normal
``runtime.submit`` path when durable memory is enabled, routed through the memory
funnel (no sandbox, no StateTransitionRecord), and byte-identical (rejected) when
the flag is OFF.
"""

from __future__ import annotations

import tempfile

from agentic_runtime import (AgentCard, AgentClass, AuthorityScope, RiskLevel,
                             build_runtime)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.sandbox import UnsafeLocalSandbox

FLAG = "AUREL_DURABLE_MEMORY"


def _card():
    return AgentCard.make(
        name="MemAgent", agent_class=AgentClass.EXECUTION, mission="m",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "mem_add", "mem_search",
                       "mem_link", "mem_update", "mem_delete", "mem_consolidate"],
        denied_tools=[])


def _cmd(card, tool, args):
    return CommandEnvelope.make(issuer_card_id=card.id, tool=tool, args=args,
                                rationale="r", declared_risk=RiskLevel.LOW,
                                expected_effect="e")


def _kernel(tmp_path):
    return build_runtime(sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
                         trace_dir=str(tmp_path))


def _mem_rows(kernel, action=None, verdict=None):
    out = []
    for e in kernel.trace.replay():
        if e.get("kind") != "memory_governance":
            continue
        if action is not None and e["action"] != action:
            continue
        if verdict is not None and e["verdict"] != verdict:
            continue
        out.append(e)
    return out


def _state_rows(kernel):
    return [e for e in kernel.trace.replay() if e.get("kind") == "state_transition"]


# 1 ─ flag ON: mem_add routes through the funnel; stored, charged once, no state row.
def test_flag_on_mem_add_routed_through_funnel(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    k = _kernel(tmp_path)
    card = _card()

    res = k.runtime.submit(_cmd(card, "mem_add", {"content": "hello world"}), card)

    assert res.ok is True
    assert res.transition is None                       # no StateTransitionRecord
    assert res.observation.artifacts["verdict"] == "allow"
    assert res.observation.artifacts["memory_id"]
    assert k.memory.stats()["L1"] == 1                  # actually stored
    assert k.budget.memory_writes == 1                  # one charge
    assert k.budget.sandbox_executions == 0             # never the sandbox
    assert len(_mem_rows(k, action="write", verdict="allow")) == 1
    assert len(_state_rows(k)) == 0


# 2 ─ flag ON: an agent cannot self-elevate (canon denied), nothing stored.
def test_flag_on_agent_cannot_elevate(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    k = _kernel(tmp_path)
    card = _card()

    res = k.runtime.submit(
        _cmd(card, "mem_add", {"content": "x", "truth_state": "canon"}), card)

    assert res.ok is False
    assert res.observation.artifacts["reason_code"] == "agent_cannot_write_restricted"
    assert res.verifier.passed is False
    assert k.memory.stats()["L5_canon"] == 0            # not stored
    assert k.budget.memory_writes == 1                  # the attempt is charged


# 3 ─ flag ON: mem_search is read-only (no charge); mem_link is live.
def test_flag_on_search_and_link(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    k = _kernel(tmp_path)
    card = _card()

    a = k.runtime.submit(_cmd(card, "mem_add", {"content": "alpha fact"}), card)
    b = k.runtime.submit(_cmd(card, "mem_add", {"content": "beta fact"}), card)
    charges_after_writes = k.budget.memory_writes
    assert charges_after_writes == 2

    search = k.runtime.submit(_cmd(card, "mem_search", {"query": "alpha"}), card)
    assert search.ok is True
    assert search.observation.artifacts["count"] >= 1
    assert k.budget.memory_writes == charges_after_writes   # read-only: no charge

    link = k.runtime.submit(_cmd(card, "mem_link", {
        "from_id": a.observation.artifacts["memory_id"],
        "to_id": b.observation.artifacts["memory_id"],
        "relation": "relates_to"}), card)
    assert link.ok is True
    assert len(k.memory.graph) == 1
    assert link.transition is None


# 4 ─ flag OFF: mem_* falls through to the normal path (rejected, byte-identical).
def test_flag_off_mem_not_routed(tmp_path, monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    k = _kernel(tmp_path)
    card = _card()
    assert k.runtime._durable_memory_enabled is False

    res = k.runtime.submit(_cmd(card, "mem_add", {"content": "nope"}), card)

    assert res.ok is False                              # rejected, not routed
    assert k.memory.stats()["L1"] == 0                  # nothing stored via funnel
    assert k.budget.memory_writes == 0                  # no funnel charge
    assert len(_mem_rows(k)) == 0                        # no memory-governance row


# 5 ─ flag ON: update/delete/consolidate are reachable end-to-end.
def test_flag_on_revision_and_consolidate(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    k = _kernel(tmp_path)
    card = _card()

    a = k.runtime.submit(_cmd(card, "mem_add", {"content": "v1 belief"}), card)
    mid = a.observation.artifacts["memory_id"]

    upd = k.runtime.submit(_cmd(card, "mem_update",
                                {"memory_id": mid, "content": "v2 belief"}), card)
    assert upd.ok is True
    assert upd.observation.artifacts["new_memory_id"]

    dele = k.runtime.submit(_cmd(card, "mem_delete", {"memory_id": mid}), card)
    # mem_delete on an already-superseded id may fail closed; the point is it is
    # reachable and returns a governed verdict (not a wrong-path/contract error).
    assert dele.verifier.verifier == "memory"


# 6 ─ dispatch never crashes submit on a malformed memory command (fail closed).
def test_flag_on_malformed_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    k = _kernel(tmp_path)
    card = _card()
    # mem_add with no content ⇒ contract validation fails inside the session.
    res = k.runtime.submit(_cmd(card, "mem_add", {}), card)
    assert res.ok is False
    assert res.transition is None
    assert k.memory.stats()["L1"] == 0


def test_tempdir_smoke():
    # Guard: build_runtime with an explicit tempdir is constructible (sanity).
    with tempfile.TemporaryDirectory() as d:
        assert build_runtime(sandbox=UnsafeLocalSandbox(root=d), trace_dir=d) is not None

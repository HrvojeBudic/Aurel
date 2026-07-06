"""M1 — the retain hook (opt-in) done-conditions.

With ``retain_states=True`` a run must persist a CAS node for every
``after_state_hash`` in its trace plus the genesis ``initial_state_hash``, and
each committed hash must equal the trace transition's recorded hash exactly.
With the flag OFF nothing is written to the CAS and metadata is unchanged
(no ``initial_state_hash`` key, ``genesis_hash == GENESIS``).
"""
from __future__ import annotations

import json
from pathlib import Path

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope, StateTransitionRecord
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.trace import GENESIS

_META_KEYS_TODAY = {
    "run_id", "status", "final_status", "started_at",
    "updated_at", "checkpoint_every", "genesis_hash",
}


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="M1 Agent", agent_class=AgentClass.EXECUTION, mission="retain test",
        authority=AuthorityScope(
            write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "run_tests", "list_dir"],
    )


def _cmd(card: AgentCard, tool: str, args: dict) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale="m1", declared_risk=RiskLevel.LOW, expected_effect="m1")


def _kernel(tmp_path, *, retain: bool, store: StateStore | None = None):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=str(tmp_path / "traces"),
        retain_states=retain,
        state_store=store,
    )


def _metadata(kernel, tmp_path) -> dict:
    md_path = Path(tmp_path / "traces") / "runs" / kernel.trace.run_id / "metadata.json"
    return json.loads(md_path.read_text(encoding="utf-8"))


def _after_hashes(kernel) -> list[str]:
    return [e.after_state_hash for e in kernel.trace
            if isinstance(e, StateTransitionRecord)]


def test_retained_run_persists_every_after_state_and_initial(tmp_path):
    store = StateStore(str(tmp_path / "traces"))
    kernel = _kernel(tmp_path, retain=True, store=store)
    card = _card()

    r1 = kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A1\n"}), card)
    r2 = kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A2\n"}), card)
    r3 = kernel.runtime.submit(_cmd(card, "read_file", {"path": "src/a.py"}), card)
    assert r1.ok and r2.ok and r3.ok

    afters = _after_hashes(kernel)
    assert len(afters) == 3
    for h in afters:                       # every transition's post-state is retained
        assert store.has(h)

    md = _metadata(kernel, tmp_path)       # genesis state retained + recorded
    assert "initial_state_hash" in md
    assert store.has(md["initial_state_hash"])


def test_committed_cas_hash_equals_trace_after_state_hash(tmp_path):
    store = StateStore(str(tmp_path / "traces"))
    kernel = _kernel(tmp_path, retain=True, store=store)
    card = _card()

    r1 = kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A1\n"}), card)
    r2 = kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/b.py", "content": "B1\n"}), card)

    # the exact hash the trace recorded is the exact CAS key — and materializing
    # it reproduces a tree whose state_hash is identical.
    assert store.has(r1.transition.after_state_hash)
    assert store.has(r2.transition.after_state_hash)
    assert r1.transition.after_state_hash != r2.transition.after_state_hash

    dest = str(tmp_path / "restored")
    store.materialize(r2.transition.after_state_hash, dest)
    assert UnsafeLocalSandbox(root=dest).state_hash() == r2.transition.after_state_hash


def test_flag_off_writes_no_cas_and_unchanged_metadata(tmp_path):
    kernel = _kernel(tmp_path, retain=False)   # default off, no store created
    card = _card()

    kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A1\n"}), card)
    kernel.runtime.submit(_cmd(card, "read_file", {"path": "src/a.py"}), card)

    # no CAS directory is ever created
    assert not (Path(tmp_path / "traces") / "states").exists()

    # metadata schema is exactly today's: no initial_state_hash, genesis == GENESIS
    md = _metadata(kernel, tmp_path)
    assert set(md.keys()) == _META_KEYS_TODAY
    assert "initial_state_hash" not in md
    assert md["genesis_hash"] == GENESIS

    # trace still verifies as before
    assert kernel.trace.verify_persisted()["ok"]


def test_flag_off_with_store_present_never_writes(tmp_path):
    # Even if a store is handed in, the OFF flag must fire no CAS writes at all.
    store = StateStore(str(tmp_path / "traces"))
    kernel = _kernel(tmp_path, retain=False, store=store)
    card = _card()

    kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A1\n"}), card)
    kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A2\n"}), card)

    assert not (Path(tmp_path / "traces") / "states").exists()
    md = _metadata(kernel, tmp_path)
    assert "initial_state_hash" not in md

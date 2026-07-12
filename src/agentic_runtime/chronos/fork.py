"""F8.0 — Chronos fork: mint ephemeral child runs from parent transitions (read-only on parent)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..sandbox import UnsafeLocalSandbox
from ..worldline import ForkError, ForkResult, WorldLineForest
from ._util import state_transitions

SandboxFactory = Callable[[str], Any]


def _default_sandbox_factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


@dataclass(frozen=True)
class ChronosForkResult:
    parent_run_id: str
    transition_index: int
    parent_entry_hash: str
    child_run_id: str
    fork_id: str
    parent_state_hash: str
    fork_result: ForkResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_run_id": self.parent_run_id,
            "transition_index": self.transition_index,
            "parent_entry_hash": self.parent_entry_hash,
            "child_run_id": self.child_run_id,
            "fork_id": self.fork_result.fork_ref.fork_id,
            "parent_state_hash": self.fork_result.fork_ref.parent_state_hash,
        }


class ChronosFork:
    """Fork a child run at a parent transition index."""

    @classmethod
    def fork_at(
        cls,
        trace_dir: str,
        run_id: str,
        transition_n: int,
        *,
        sandbox_factory: Optional[SandboxFactory] = None,
    ) -> ChronosForkResult:
        transitions = state_transitions(trace_dir, run_id)
        if transition_n < 0 or transition_n >= len(transitions):
            raise ForkError(
                f"transition index {transition_n} out of range "
                f"(run has {len(transitions)} state_transition event(s))"
            )
        entry_hash = transitions[transition_n].get("entry_hash", "")
        if not entry_hash:
            raise ForkError(f"transition {transition_n} has no entry_hash")

        factory = sandbox_factory or _default_sandbox_factory
        forest = WorldLineForest(trace_dir)
        fork_result = forest.fork(run_id, entry_hash, sandbox_factory=factory)
        return ChronosForkResult(
            parent_run_id=run_id,
            transition_index=transition_n,
            parent_entry_hash=entry_hash,
            child_run_id=fork_result.child_run_id,
            fork_id=fork_result.fork_ref.fork_id,
            parent_state_hash=fork_result.fork_ref.parent_state_hash,
            fork_result=fork_result,
        )

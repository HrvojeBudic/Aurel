"""F8.0 — Chronos replay: deterministic state reconstruction audit (read-only)."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..aurel_trace.replay_readiness import (
    ReplayReadinessStatus,
    assess_replay_readiness,
    build_trace_time_slice_ref,
)
from ..aurel_trace.trace_refs import TraceRunRef
from ..sandbox import UnsafeLocalSandbox
from ..trace import PersistentTraceLedger
from ..worldline import CheckoutError, WorldLineForest
from ._util import state_transitions

SandboxFactory = Callable[[str], Any]


def _default_sandbox_factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


@dataclass(frozen=True)
class ReplayResult:
    run_id: str
    replayable: bool
    reason: str
    checked_count: int
    mismatch_at: Optional[int]
    final_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "replayable": self.replayable,
            "reason": self.reason,
            "checked_count": self.checked_count,
            "mismatch_at": self.mismatch_at,
            "final_hash": self.final_hash,
        }


class ChronosReplay:
    """Read-only replay audit over a persisted run."""

    @classmethod
    def from_run(
        cls,
        trace_dir: str,
        run_id: str,
        *,
        sandbox_factory: Optional[SandboxFactory] = None,
    ) -> ReplayResult:
        ledger = PersistentTraceLedger(base_dir=trace_dir, run_id=run_id)
        report = ledger.verify_persisted()
        if not report.get("ok"):
            return ReplayResult(
                run_id=run_id,
                replayable=False,
                reason=str(report.get("reason", "trace verification failed")),
                checked_count=0,
                mismatch_at=None,
                final_hash="",
            )

        transitions = state_transitions(trace_dir, run_id)
        final_hash = report.get("final_chain_hash") or ledger.head

        run_ref = TraceRunRef(
            trace_run_id=run_id,
            ledger_backend="persistent",
            chain_head_hash=final_hash,
            event_count=len(transitions),
        )
        slice_ref = build_trace_time_slice_ref(
            start_ref=run_id,
            end_ref=run_id,
            trace_run_ref=run_ref,
            chain_head_hash=final_hash,
        )
        present = ["trace_run_ref", "chain_head_hash", "event_range"]
        if transitions:
            present.append("canonical_event_refs")
        readiness = assess_replay_readiness(
            time_slice_ref=slice_ref,
            required_inputs=("trace_run_ref", "chain_head_hash"),
            present_inputs=tuple(present),
        )
        if readiness.status is ReplayReadinessStatus.UNAVAILABLE:
            return ReplayResult(
                run_id=run_id,
                replayable=False,
                reason=readiness.unavailable_reason or "replay readiness UNAVAILABLE",
                checked_count=0,
                mismatch_at=None,
                final_hash=final_hash,
            )

        if not transitions:
            return ReplayResult(
                run_id=run_id,
                replayable=True,
                reason="no state transitions to reconstruct",
                checked_count=0,
                mismatch_at=None,
                final_hash=final_hash,
            )

        factory = sandbox_factory or _default_sandbox_factory
        forest = WorldLineForest(trace_dir)
        for index, event in enumerate(transitions):
            entry_hash = event.get("entry_hash", "")
            expected = event.get("payload", {}).get("after_state_hash", "")
            if not entry_hash or not expected:
                return ReplayResult(
                    run_id=run_id,
                    replayable=False,
                    reason=f"transition {index} missing entry_hash or after_state_hash",
                    checked_count=index,
                    mismatch_at=index,
                    final_hash=final_hash,
                )
            try:
                root = tempfile.mkdtemp(prefix="chronos_replay_")
                sandbox = factory(root)
                forest.checkout(run_id, entry_hash, sandbox_factory=lambda _: sandbox)
            except CheckoutError as exc:
                return ReplayResult(
                    run_id=run_id,
                    replayable=False,
                    reason=str(exc),
                    checked_count=index,
                    mismatch_at=index,
                    final_hash=final_hash,
                )
            reconstructed = sandbox.state_hash()
            if reconstructed != expected:
                return ReplayResult(
                    run_id=run_id,
                    replayable=False,
                    reason=(
                        f"state mismatch at transition {index}: "
                        f"reconstructed {reconstructed!r} != recorded {expected!r}"
                    ),
                    checked_count=index + 1,
                    mismatch_at=index,
                    final_hash=final_hash,
                )

        last_after = transitions[-1].get("payload", {}).get("after_state_hash", "")
        return ReplayResult(
            run_id=run_id,
            replayable=True,
            reason="all transitions reconstruct recorded state",
            checked_count=len(transitions),
            mismatch_at=None,
            final_hash=last_after or final_hash,
        )

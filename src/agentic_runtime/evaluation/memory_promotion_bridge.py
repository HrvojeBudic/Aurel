"""A8b — Live promotion driver: command outcomes → governed procedure candidates.

(The masterplan names this ``evaluation/memory_candidate_bridge.py``, but that file
already exists as the P1.5.18 evaluation→candidate *contract-derivation* bridge — a
different concern — so this A8b driver lives beside it under a distinct name. See
the A8 report drift note.)

When durable memory is enabled, the runtime feeds each *verified* command outcome
to :class:`MemoryCandidateBridge`, which submits a CANDIDATE memory for the
command's stable signature and drives its promotion up the P0.9 ladder as the same
work succeeds repeatedly:

    candidate --(evidence: 1 verified success)--> verified
    verified  --(>= min distinct successful traces)--> procedural

All writes/promotions route through the EXISTING governed funnel
(``fabric.request_write`` / ``fabric.promote``) — no bypass, one governance row per
op — so the P0.9 laws hold structurally:

* **Failed runs never promote.** A non-succeeding outcome is ignored: it adds no
  success trace and drives no promotion (governance would deny it anyway).
* **Monotonic.** Promotion only ever moves up the ladder, gated by evidence and
  repeated success; the bridge never demotes and never proposes CANON.
* **Runtime proposes, governance disposes.** The bridge writes as ``runtime`` and
  cannot self-elevate past what ``evaluate_write``/``evaluate_promotion`` allow.

Deterministic and stdlib-only: signatures are content hashes, and the promotion
decision is a pure function of the distinct successful trace count.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core_types import MemoryTruthState


@dataclass
class _CandidateState:
    memory_id: str
    truth_state: MemoryTruthState
    success_traces: set[str] = field(default_factory=set)


@dataclass
class BridgeOutcome:
    memory_id: str = ""
    truth_state: str = ""
    promoted_to: str = ""            # "" when no promotion happened this observe
    reason_code: str = "observed"


class MemoryCandidateBridge:
    """Accumulates verified successes per command signature and drives governed
    promotion. Holds only in-memory bookkeeping; the fabric holds the truth."""

    def __init__(self, min_repeated_success: int = 2) -> None:
        self.min_repeated_success = max(2, int(min_repeated_success))
        self._by_sig: dict[str, _CandidateState] = {}

    def observe(
        self,
        *,
        fabric: Any,
        budget: Any,
        signature: str,
        content: str,
        run_id: str,
        trace_id: str,
        run_succeeded: bool,
        created_by: str = "runtime",
    ) -> BridgeOutcome:
        # P0.9: a failed run cannot create or promote success memory. Do nothing.
        if not run_succeeded:
            return BridgeOutcome(reason_code="failed_run_no_promotion")

        from ..memory_governance import MemoryWriteRequest

        st = self._by_sig.get(signature)
        if st is None:
            # First verified success ⇒ submit a governed CANDIDATE (one charge, one row).
            budget.charge_memory_write()
            decision = fabric.request_write(MemoryWriteRequest(
                content=content,
                proposed_truth_state=MemoryTruthState.CANDIDATE,
                writer_kind="runtime",
                created_by=created_by,
                source_run_id=run_id,
                source_trace_ids=[trace_id] if trace_id else [],
                evidence_refs=[trace_id] if trace_id else [],
                confidence=0.6,
                run_succeeded=True,
            ))
            if not decision.allowed or decision.record is None:
                return BridgeOutcome(reason_code=decision.reason_code)
            st = _CandidateState(decision.record.memory_id, MemoryTruthState.CANDIDATE)
            if trace_id:
                st.success_traces.add(trace_id)
            self._by_sig[signature] = st
        elif trace_id:
            st.success_traces.add(trace_id)

        promoted_to = self._drive_promotion(fabric, st)
        return BridgeOutcome(
            memory_id=st.memory_id,
            truth_state=st.truth_state.value,
            promoted_to=promoted_to,
            reason_code="promoted" if promoted_to else "observed",
        )

    def state_for(self, signature: str) -> str:
        st = self._by_sig.get(signature)
        return st.truth_state.value if st else ""

    def _drive_promotion(self, fabric: Any, st: _CandidateState) -> str:
        """Move ``st`` up the ladder as far as governance allows. Returns the
        highest state promoted TO this call (``""`` if none)."""
        promoted_to = ""
        # candidate → verified needs evidence (a verified success trace).
        if st.truth_state is MemoryTruthState.CANDIDATE and st.success_traces:
            d = fabric.promote(
                st.memory_id, MemoryTruthState.VERIFIED,
                evidence_refs=sorted(st.success_traces), actor="runtime")
            if d.allowed:
                st.truth_state = MemoryTruthState.VERIFIED
                promoted_to = MemoryTruthState.VERIFIED.value
        # verified → procedural needs >= min distinct successful traces.
        if (st.truth_state is MemoryTruthState.VERIFIED
                and len(st.success_traces) >= self.min_repeated_success):
            d = fabric.promote(
                st.memory_id, MemoryTruthState.PROCEDURAL,
                success_trace_ids=sorted(st.success_traces), actor="runtime")
            if d.allowed:
                st.truth_state = MemoryTruthState.PROCEDURAL
                promoted_to = MemoryTruthState.PROCEDURAL.value
        return promoted_to


def command_signature(tool: str, args: Any) -> str:
    """A stable, deterministic key for a command (tool + canonical args hash)."""
    from ..core_types import canonical_json, sha
    return f"{tool}|{sha(canonical_json(args))[:16]}"


__all__ = ["MemoryCandidateBridge", "BridgeOutcome", "command_signature"]

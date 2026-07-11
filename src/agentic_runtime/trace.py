"""
trace.py — Trace ledger backends with tamper-evident persistence (P0.6).

Two backends are supported:
  - InMemoryTraceLedger: process-local hash chain.
  - PersistentTraceLedger: append-only JSONL evidence with checkpoints + receipt.
"""
from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, Protocol, Union

try:
    import fcntl  # POSIX advisory file locking for cross-process single-writer
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None

if TYPE_CHECKING:
    from .worldline import ForkRef
    from .trace_anchor import AnchorSink

from .core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    MemoryGovernanceRecord,
    PraxisEventRecord,
    SandboxAttestationRecord,
    SandboxViolationRecord,
    RuntimeStatusTransitionRecord,
    PlanningFailureRecord,
    PolicyVerdict,
    StateTransitionRecord,
    ToolContractViolationRecord,
    VerifierResult,
    canonical_json,
    new_id,
    now,
    sha,
)

TraceEntry = Union[
    StateTransitionRecord,
    PlanningFailureRecord,
    RuntimeStatusTransitionRecord,
    BudgetDecisionRecord,
    MemoryGovernanceRecord,
    ToolContractViolationRecord,
    ApprovalReceiptRecord,
    PraxisEventRecord,
    SandboxViolationRecord,
    SandboxAttestationRecord,
]
TraceEvent = dict[str, Any]

GENESIS = sha("AGENTIC_RUNTIME_GENESIS")


class TraceOwnershipError(RuntimeError):
    """Raised when a second process appends to an open run it does not own."""


class TraceLedgerBackend(Protocol):
    @property
    def run_id(self) -> str: ...
    @property
    def head(self) -> str: ...
    def append(self, rec: StateTransitionRecord) -> StateTransitionRecord: ...
    def append_planning_failure(self, rec: PlanningFailureRecord) -> PlanningFailureRecord: ...
    def append_status_transition(
        self, rec: RuntimeStatusTransitionRecord
    ) -> RuntimeStatusTransitionRecord: ...
    def append_budget_decision(self, rec: BudgetDecisionRecord) -> BudgetDecisionRecord: ...
    def append_memory_event(self, rec: MemoryGovernanceRecord) -> MemoryGovernanceRecord: ...
    def append_tool_contract_violation(self, rec: ToolContractViolationRecord) -> ToolContractViolationRecord: ...
    def append_approval_receipt(self, rec: ApprovalReceiptRecord) -> ApprovalReceiptRecord: ...
    def append_praxis_event(self, rec: PraxisEventRecord) -> PraxisEventRecord: ...
    def append_sandbox_violation(self, rec: SandboxViolationRecord) -> SandboxViolationRecord: ...
    def append_sandbox_attestation(self, rec: SandboxAttestationRecord) -> SandboxAttestationRecord: ...
    def planning_failures(self) -> list[PlanningFailureRecord]: ...
    def verify_chain(self) -> tuple[bool, Optional[int]]: ...
    def replay(self) -> Iterator[dict]: ...
    def export(self) -> str: ...
    def merkle_root(self) -> str: ...
    def seal_run(self, final_status: str, verification_summary: Optional[dict] = None) -> dict: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[TraceEntry]: ...


class InMemoryTraceLedger:
    """Original process-local hash-chained ledger."""

    def __init__(self, run_id: Optional[str] = None) -> None:
        self._entries: list[TraceEntry] = []
        self._run_id = run_id or new_id("run")
        self._last_receipt: dict[str, Any] | None = None
        self._started_at = now()

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def head(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS

    def append(self, rec: StateTransitionRecord) -> StateTransitionRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_planning_failure(self, rec: PlanningFailureRecord) -> PlanningFailureRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_status_transition(
        self, rec: RuntimeStatusTransitionRecord
    ) -> RuntimeStatusTransitionRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_budget_decision(self, rec: BudgetDecisionRecord) -> BudgetDecisionRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_memory_event(self, rec: MemoryGovernanceRecord) -> MemoryGovernanceRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_tool_contract_violation(
        self, rec: ToolContractViolationRecord
    ) -> ToolContractViolationRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_approval_receipt(self, rec: ApprovalReceiptRecord) -> ApprovalReceiptRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_praxis_event(self, rec: PraxisEventRecord) -> PraxisEventRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_sandbox_violation(self, rec: SandboxViolationRecord) -> SandboxViolationRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def append_sandbox_attestation(
        self, rec: SandboxAttestationRecord
    ) -> SandboxAttestationRecord:
        rec.prev_entry_hash = self.head
        rec.entry_hash = sha(rec.prev_entry_hash, rec.payload_hash())
        self._entries.append(rec)
        return rec

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[TraceEntry]:
        return iter(self._entries)

    def planning_failures(self) -> list[PlanningFailureRecord]:
        return [e for e in self._entries if isinstance(e, PlanningFailureRecord)]

    def verify_chain(self) -> tuple[bool, Optional[int]]:
        prev = GENESIS
        for i, rec in enumerate(self._entries):
            if rec.prev_entry_hash != prev:
                return False, i
            expected = sha(rec.prev_entry_hash, rec.payload_hash())
            if rec.entry_hash != expected:
                return False, i
            prev = rec.entry_hash
        return True, None

    def replay(self) -> Iterator[dict]:
        for rec in self._entries:
            if isinstance(rec, PlanningFailureRecord):
                yield {
                    "kind": "planning_failure",
                    "issuer": rec.issuer_card_id,
                    "status": rec.status,
                    "reason": rec.reason,
                    "intent_id": rec.intent_id,
                }
            elif isinstance(rec, RuntimeStatusTransitionRecord):
                ev: dict[str, Any] = {
                    "kind": "runtime_status_transition",
                    "issuer": rec.issuer_card_id,
                    "run_id": rec.run_id,
                    "from": rec.from_status,
                    "to": rec.to_status,
                    "reason_code": rec.reason_code,
                }
                if rec.mandate_id:  # F6: additive, empty ⇒ dict unchanged
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, BudgetDecisionRecord):
                ev = {
                    "kind": "budget_decision",
                    "issuer": rec.issuer_card_id,
                    "metric": rec.metric,
                    "verdict": rec.verdict,
                    "used": rec.used,
                    "limit": rec.limit,
                }
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, MemoryGovernanceRecord):
                ev = {
                    "kind": "memory_governance",
                    "issuer": rec.agent_id,
                    "action": rec.action,
                    "verdict": rec.verdict,
                    "memory_id": rec.memory_id,
                    "from": rec.from_state,
                    "to": rec.to_state,
                    "reason_code": rec.reason_code,
                    # A7 (closes the A2/A3/A4 "D2" seam): surface the governance
                    # details so a pure trace replay can reconstruct the memory
                    # graph (link: edge_id/from_id/to_id/relation) and belief
                    # revisions (update: target_id/new_memory_id).
                    "details": dict(rec.details),
                }
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, ToolContractViolationRecord):
                yield {
                    "kind": "tool_contract_violation",
                    "issuer": rec.issuer_card_id,
                    "tool": rec.tool,
                    "phase": rec.phase,
                    "code": rec.code,
                    "reason": rec.reason,
                }
            elif isinstance(rec, ApprovalReceiptRecord):
                ev = {
                    "kind": "approval_receipt",
                    "issuer": rec.issuer_card_id,
                    "tool": rec.tool,
                    "risk_class": rec.risk_class,
                    "outcome": rec.outcome,
                    "reason": rec.reason,
                    "decided_by": rec.decided_by,
                }
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, PraxisEventRecord):
                ev = {
                    "kind": "praxis_event",
                    "issuer": rec.agent_id,
                    "event_type": rec.event_type,
                    "subject_id": rec.subject_id,
                    "summary": rec.summary,
                }
                # F7 CAS-pointer: payloads too large for the 500-char summary
                # ride in `details`. Additive — empty ⇒ dict unchanged.
                if rec.details:
                    ev["details"] = dict(rec.details)
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, SandboxViolationRecord):
                yield {
                    "kind": "sandbox_violation",
                    "issuer": rec.issuer_card_id,
                    "profile": rec.profile_name,
                    "tool": rec.tool,
                    "action": rec.attempted_action,
                    "reason": rec.reason,
                    "path": rec.attempted_path,
                }
            elif isinstance(rec, SandboxAttestationRecord):
                yield {
                    "kind": "sandbox_attestation",
                    "backend": rec.backend,
                    "available": rec.available,
                    "hard_isolated": rec.hard_isolated,
                    "reason": rec.reason,
                    "probe": rec.probe,
                    "host": rec.host,
                }
            else:
                yield {
                    "kind": "state_transition",
                    "issuer": rec.issuer_card_id,
                    "verdict": rec.policy_verdict.value,
                    "before": rec.before_state_hash[:12],
                    "after": rec.after_state_hash[:12],
                    "verified": rec.verifier_result.passed,
                    "verifier": rec.verifier_result.verifier,
                }

    def export(self) -> str:
        return json.dumps([r.to_dict() for r in self._entries], default=str, indent=2)

    def merkle_root(self) -> str:
        if not self._entries:
            return GENESIS
        # Leaves recompute from live payload fields so tampered records change the root.
        layer = [sha(r.prev_entry_hash, r.payload_hash()) for r in self._entries]
        while len(layer) > 1:
            nxt = []
            for i in range(0, len(layer), 2):
                a = layer[i]
                b = layer[i + 1] if i + 1 < len(layer) else layer[i]
                nxt.append(sha(a, b))
            layer = nxt
        return layer[0]

    def seal_run(self, final_status: str, verification_summary: Optional[dict] = None) -> dict:
        if verification_summary is None:
            ok, broken = self.verify_chain()
            verification_summary = {"ok": ok, "broken_index": broken}
        self._last_receipt = {
            "run_id": self.run_id,
            "final_status": final_status,
            "event_count": len(self._entries),
            "final_chain_hash": self.head,
            "verification_summary": verification_summary,
            "started_at": self._started_at,
            "ended_at": now(),
        }
        return self._last_receipt


class PersistentTraceLedger:
    """Append-only JSONL trace evidence with checkpoint and receipt sealing."""

    def __init__(
        self,
        base_dir: str = ".traces",
        run_id: Optional[str] = None,
        checkpoint_every: int = 5,
        parent_ref: "ForkRef | None" = None,
        anchor_sink: "AnchorSink | None" = None,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.run_id = run_id or new_id("run")
        self.checkpoint_every = max(1, int(checkpoint_every))
        # M2 — serialize the append path (head read → event build → jsonl write)
        # so concurrent writers can never interleave sequence numbers. The
        # in-process lock guards threads; the advisory file lock guards processes.
        self._append_lock = threading.RLock()
        self._anchor_sink = anchor_sink
        self.run_dir = self.base_dir / "runs" / self.run_id
        self.events_path = self.run_dir / "events.jsonl"
        self.checkpoints_path = self.run_dir / "checkpoints.jsonl"
        self.receipt_path = self.run_dir / "receipt.json"
        self.metadata_path = self.run_dir / "metadata.json"
        self._entries: list[TraceEntry] = []
        self._events: list[TraceEvent] = []
        self._checkpoint_head = GENESIS
        self._started_at = now()
        # M1 — genesis world-state address (set only for retained runs). When
        # None the metadata carries no initial_state_hash key (byte-identical to
        # today); when set it makes fork-from-genesis verifiable.
        self._initial_state_hash: Optional[str] = None
        # M3 — forked genesis. A forked run chains its event ledger from the
        # parent's ``child_genesis_hash`` instead of GENESIS; the checkpoint
        # chain stays on GENESIS. parent_ref=None is byte-for-byte today
        # (self._genesis == GENESIS everywhere it is used below).
        self._parent_ref = parent_ref
        self._genesis = parent_ref.child_genesis_hash if parent_ref is not None else GENESIS

        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events_path.touch(exist_ok=True)
        self.checkpoints_path.touch(exist_ok=True)
        if self.metadata_path.exists():
            self._load_existing()
        else:
            self._write_metadata(status="open")

    @property
    def head(self) -> str:
        return self._events[-1]["entry_hash"] if self._events else self._genesis

    @contextmanager
    def _write_guard(self) -> Iterator[None]:
        """Serialize the append path within and across processes.

        The in-process ``RLock`` prevents thread interleaving; an advisory
        exclusive lock on the events file prevents a second process from
        interleaving sequence numbers. Cross-process ownership is enforced so a
        stale second writer fails closed rather than corrupting the chain.
        """
        with self._append_lock:
            lock_fh = None
            if fcntl is not None:
                lock_fh = open(self.events_path, "a", encoding="utf-8")
                try:
                    fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
                except OSError as e:  # pragma: no cover - platform dependent
                    lock_fh.close()
                    raise TraceOwnershipError(
                        f"could not acquire trace write lock: {e}"
                    ) from e
            try:
                yield
            finally:
                if lock_fh is not None:
                    try:
                        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
                    finally:
                        lock_fh.close()

    def _locked_append(
        self,
        build_event: Callable[[str, int, Any], TraceEvent],
        rec: Any,
    ) -> Any:
        """Atomic append: head read → event build → jsonl write → checkpoint."""
        with self._write_guard():
            rec.prev_entry_hash = self.head
            event = build_event(self.run_id, len(self._events) + 1, rec)
            # F6: persist a non-empty mandate_id so it survives reload. Additive —
            # empty/absent ⇒ payload + entry_hash byte-identical to pre-F6 traces.
            mandate_id = getattr(rec, "mandate_id", "")
            if mandate_id and isinstance(event.get("payload"), dict):
                event["payload"]["mandate_id"] = mandate_id
                event["entry_hash"] = _entry_hash(event)
            rec.entry_hash = event["entry_hash"]
            self._events.append(event)
            self._entries.append(rec)
            _append_jsonl(self.events_path, event)
            self._maybe_checkpoint(event)
        return rec

    def append(self, rec: StateTransitionRecord) -> StateTransitionRecord:
        return self._locked_append(_state_transition_event, rec)

    def append_planning_failure(self, rec: PlanningFailureRecord) -> PlanningFailureRecord:
        return self._locked_append(_planning_failure_event, rec)

    def append_status_transition(
        self, rec: RuntimeStatusTransitionRecord
    ) -> RuntimeStatusTransitionRecord:
        return self._locked_append(_runtime_status_event, rec)

    def append_budget_decision(self, rec: BudgetDecisionRecord) -> BudgetDecisionRecord:
        return self._locked_append(_budget_decision_event, rec)

    def append_memory_event(self, rec: MemoryGovernanceRecord) -> MemoryGovernanceRecord:
        return self._locked_append(_memory_governance_event, rec)

    def append_tool_contract_violation(
        self, rec: ToolContractViolationRecord
    ) -> ToolContractViolationRecord:
        return self._locked_append(_tool_contract_violation_event, rec)

    def append_approval_receipt(self, rec: ApprovalReceiptRecord) -> ApprovalReceiptRecord:
        return self._locked_append(_approval_receipt_event, rec)

    def append_praxis_event(self, rec: PraxisEventRecord) -> PraxisEventRecord:
        return self._locked_append(_praxis_event, rec)

    def append_sandbox_violation(self, rec: SandboxViolationRecord) -> SandboxViolationRecord:
        return self._locked_append(_sandbox_violation_event, rec)

    def append_sandbox_attestation(
        self, rec: SandboxAttestationRecord
    ) -> SandboxAttestationRecord:
        return self._locked_append(_sandbox_attestation_event, rec)

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[TraceEntry]:
        return iter(self._entries)

    def planning_failures(self) -> list[PlanningFailureRecord]:
        return [e for e in self._entries if isinstance(e, PlanningFailureRecord)]

    def verify_chain(self) -> tuple[bool, Optional[int]]:
        report = self.verify_persisted()
        return report["ok"], report["broken_index"]

    def verify_persisted(self) -> dict[str, Any]:
        events = _load_jsonl(self.events_path)
        ok, broken, reason, final_hash = _verify_events(events, self.run_id, genesis=self._genesis)
        if not ok:
            return {
                "ok": False,
                "broken_index": broken,
                "reason": reason,
                "event_count": len(events),
            }

        cps = _load_jsonl(self.checkpoints_path)
        ok_cp, reason_cp = _verify_checkpoints(
            events, cps, self.checkpoint_every, self.run_id
        )
        if not ok_cp:
            return {
                "ok": False,
                "broken_index": None,
                "reason": reason_cp,
                "event_count": len(events),
            }

        if self.receipt_path.exists():
            receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
            if receipt.get("run_id") != self.run_id:
                return {
                    "ok": False,
                    "broken_index": None,
                    "reason": "receipt run_id mismatch",
                    "event_count": len(events),
                }
            if receipt.get("event_count") != len(events):
                return {
                    "ok": False,
                    "broken_index": None,
                    "reason": "receipt event_count mismatch",
                    "event_count": len(events),
                }
            if receipt.get("final_chain_hash") != final_hash:
                return {
                    "ok": False,
                    "broken_index": None,
                    "reason": "receipt final_chain_hash mismatch",
                    "event_count": len(events),
                }

        # M2 — external anchor check. A full re-forge (rewriting events,
        # checkpoints, and receipt so the internal chain re-verifies) still
        # cannot match the merkle root committed outside the agent's write
        # domain. The anchor records the root over the first ``sequence`` events;
        # we recompute that prefix and require a match. A ledger shorter than the
        # anchored prefix means events were truncated — also a tamper.
        anchored = False
        sink = self._resolve_anchor_sink()
        if sink is not None:
            latest = sink.latest(self.run_id)
            if latest is not None:
                anchored = True
                seq = latest.sequence
                if len(events) < seq:
                    return {
                        "ok": False,
                        "broken_index": None,
                        "reason": "anchored events truncated (possible re-forge)",
                        "event_count": len(events),
                        "anchored": True,
                    }
                prefix_root = _merkle_root_of_events(events[:seq])
                if latest.merkle_root != prefix_root:
                    return {
                        "ok": False,
                        "broken_index": None,
                        "reason": "anchor merkle_root mismatch (possible re-forge)",
                        "event_count": len(events),
                        "anchored": True,
                    }

        return {
            "ok": True,
            "broken_index": None,
            "reason": "",
            "event_count": len(events),
            "final_chain_hash": final_hash,
            "anchored": anchored,
        }

    def _resolve_anchor_sink(self):
        """Anchor sink bound to this ledger, or the default when one exists."""
        if self._anchor_sink is not None:
            return self._anchor_sink
        try:
            from .trace_anchor import default_anchor_sink

            sink = default_anchor_sink()
            # Only use it for verification if it actually holds an anchor for
            # this run — never invent one.
            return sink if sink.latest(self.run_id) is not None else None
        except Exception:  # noqa: BLE001
            return None

    def replay(self) -> Iterator[dict]:
        for rec in self._entries:
            if isinstance(rec, PlanningFailureRecord):
                yield {
                    "kind": "planning_failure",
                    "issuer": rec.issuer_card_id,
                    "status": rec.status,
                    "reason": rec.reason,
                    "intent_id": rec.intent_id,
                }
            elif isinstance(rec, RuntimeStatusTransitionRecord):
                ev: dict[str, Any] = {
                    "kind": "runtime_status_transition",
                    "issuer": rec.issuer_card_id,
                    "run_id": rec.run_id,
                    "from": rec.from_status,
                    "to": rec.to_status,
                    "reason_code": rec.reason_code,
                }
                if rec.mandate_id:  # F6: additive, empty ⇒ dict unchanged
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, BudgetDecisionRecord):
                ev = {
                    "kind": "budget_decision",
                    "issuer": rec.issuer_card_id,
                    "metric": rec.metric,
                    "verdict": rec.verdict,
                    "used": rec.used,
                    "limit": rec.limit,
                }
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, MemoryGovernanceRecord):
                ev = {
                    "kind": "memory_governance",
                    "issuer": rec.agent_id,
                    "action": rec.action,
                    "verdict": rec.verdict,
                    "memory_id": rec.memory_id,
                    "from": rec.from_state,
                    "to": rec.to_state,
                    "reason_code": rec.reason_code,
                    # A7 (closes the A2/A3/A4 "D2" seam): surface the governance
                    # details so a pure trace replay can reconstruct the memory
                    # graph (link: edge_id/from_id/to_id/relation) and belief
                    # revisions (update: target_id/new_memory_id).
                    "details": dict(rec.details),
                }
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, ToolContractViolationRecord):
                yield {
                    "kind": "tool_contract_violation",
                    "issuer": rec.issuer_card_id,
                    "tool": rec.tool,
                    "phase": rec.phase,
                    "code": rec.code,
                    "reason": rec.reason,
                }
            elif isinstance(rec, ApprovalReceiptRecord):
                ev = {
                    "kind": "approval_receipt",
                    "issuer": rec.issuer_card_id,
                    "tool": rec.tool,
                    "risk_class": rec.risk_class,
                    "outcome": rec.outcome,
                    "reason": rec.reason,
                    "decided_by": rec.decided_by,
                }
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, PraxisEventRecord):
                ev = {
                    "kind": "praxis_event",
                    "issuer": rec.agent_id,
                    "event_type": rec.event_type,
                    "subject_id": rec.subject_id,
                    "summary": rec.summary,
                }
                # F7 CAS-pointer: payloads too large for the 500-char summary
                # ride in `details`. Additive — empty ⇒ dict unchanged.
                if rec.details:
                    ev["details"] = dict(rec.details)
                if rec.mandate_id:
                    ev["mandate_id"] = rec.mandate_id
                yield ev
            elif isinstance(rec, SandboxViolationRecord):
                yield {
                    "kind": "sandbox_violation",
                    "issuer": rec.issuer_card_id,
                    "profile": rec.profile_name,
                    "tool": rec.tool,
                    "action": rec.attempted_action,
                    "reason": rec.reason,
                    "path": rec.attempted_path,
                }
            elif isinstance(rec, SandboxAttestationRecord):
                yield {
                    "kind": "sandbox_attestation",
                    "backend": rec.backend,
                    "available": rec.available,
                    "hard_isolated": rec.hard_isolated,
                    "reason": rec.reason,
                    "probe": rec.probe,
                    "host": rec.host,
                }
            else:
                yield {
                    "kind": "state_transition",
                    "issuer": rec.issuer_card_id,
                    "verdict": rec.policy_verdict.value,
                    "before": rec.before_state_hash[:12],
                    "after": rec.after_state_hash[:12],
                    "verified": rec.verifier_result.passed,
                    "verifier": rec.verifier_result.verifier,
                }

    def export(self) -> str:
        return json.dumps([r.to_dict() for r in self._entries], default=str, indent=2)

    def merkle_root(self) -> str:
        if not self._events:
            return GENESIS
        # Leaves recompute from live event fields so tampered payloads change the root.
        layer = [_entry_hash(e) for e in self._events]
        while len(layer) > 1:
            nxt = []
            for i in range(0, len(layer), 2):
                a = layer[i]
                b = layer[i + 1] if i + 1 < len(layer) else layer[i]
                nxt.append(sha(a, b))
            layer = nxt
        return layer[0]

    def seal_run(self, final_status: str, verification_summary: Optional[dict] = None) -> dict:
        if verification_summary is None:
            verification_summary = self.verify_persisted()
        anchor_receipt = self._anchor_now(final=True)
        receipt = {
            "run_id": self.run_id,
            "final_status": final_status,
            "event_count": len(self._events),
            "final_chain_hash": self.head,
            "verification_summary": verification_summary,
            "started_at": self._started_at,
            "ended_at": now(),
        }
        if anchor_receipt is not None:
            receipt["anchor"] = {
                "sink": anchor_receipt.sink,
                "anchor_id": anchor_receipt.anchor_id,
                "sequence": anchor_receipt.sequence,
                "merkle_root": anchor_receipt.merkle_root,
            }
        self.receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._write_metadata(status="sealed", final_status=final_status)
        return receipt

    def _anchor_now(self, final: bool = False):
        """Commit the current merkle root to the external anchor sink, if any."""
        if self._anchor_sink is None:
            return None
        try:
            return self._anchor_sink.anchor(
                self.run_id, len(self._events), self.merkle_root()
            )
        except Exception:  # noqa: BLE001 - anchoring must never break a run
            return None

    def _maybe_checkpoint(self, event: TraceEvent) -> None:
        seq = event["sequence"]
        if seq % self.checkpoint_every != 0:
            return
        cp = {
            "run_id": self.run_id,
            "sequence": seq,
            "previous_checkpoint_hash": self._checkpoint_head,
            "chain_head": event["entry_hash"],
        }
        cp["checkpoint_hash"] = sha(canonical_json(cp))
        _append_jsonl(self.checkpoints_path, cp)
        self._checkpoint_head = cp["checkpoint_hash"]
        # Anchor periodically so a re-forge is caught even before seal.
        self._anchor_now()

    def record_initial_state_hash(self, state_hash: str) -> None:
        """Record the genesis world-state address in metadata (retained runs).

        Additive: only ever called on a retained run's first submit. Non-retained
        runs never invoke it, so their metadata is unchanged.
        """
        self._initial_state_hash = state_hash
        status, final_status = "open", ""
        if self.metadata_path.exists():
            md = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            status = md.get("status", "open")
            final_status = md.get("final_status", "")
        self._write_metadata(status=status, final_status=final_status)

    def _load_existing(self) -> None:
        md = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self._started_at = md.get("started_at", now())
        self._initial_state_hash = md.get("initial_state_hash")
        # M3 — recover the (possibly forked) genesis from persisted metadata so a
        # reloaded child run verifies from its own genesis without a parent_ref.
        self._genesis = md.get("genesis_hash", GENESIS)
        events = _load_jsonl(self.events_path)
        for ev in events:
            self._events.append(ev)
            self._entries.append(_record_from_event(ev))
        cps = _load_jsonl(self.checkpoints_path)
        if cps:
            self._checkpoint_head = cps[-1]["checkpoint_hash"]

    def _write_metadata(self, status: str, final_status: str = "") -> None:
        md = {
            "run_id": self.run_id,
            "status": status,
            "final_status": final_status,
            "started_at": self._started_at,
            "updated_at": now(),
            "checkpoint_every": self.checkpoint_every,
            "genesis_hash": self._genesis,
        }
        if self._initial_state_hash is not None:
            md["initial_state_hash"] = self._initial_state_hash
        self.metadata_path.write_text(
            json.dumps(md, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _state_transition_event(run_id: str, sequence: int, rec: StateTransitionRecord) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "state_transition",
        "agent_id": rec.issuer_card_id,
        "command_hash": rec.command_hash,
        "observation_hash": rec.observation_hash,
        "verifier_hash": sha(canonical_json(rec.verifier_result.to_dict())),
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "before_state_hash": rec.before_state_hash,
            "after_state_hash": rec.after_state_hash,
            "policy_verdict": rec.policy_verdict.value,
            "parent_intent_id": rec.parent_intent_id,
            "verifier_result": rec.verifier_result.to_dict(),
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _planning_failure_event(run_id: str, sequence: int, rec: PlanningFailureRecord) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "planning_failure",
        "agent_id": rec.issuer_card_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "intent_id": rec.intent_id,
            "status": rec.status,
            "reason": rec.reason,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _runtime_status_event(
    run_id: str,
    sequence: int,
    rec: RuntimeStatusTransitionRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "runtime_status_transition",
        "agent_id": rec.issuer_card_id,
        "command_hash": rec.command_hash,
        "observation_hash": rec.observation_hash,
        "verifier_hash": rec.verifier_hash,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "intent_id": rec.intent_id,
            "from_status": rec.from_status,
            "to_status": rec.to_status,
            "reason_code": rec.reason_code,
            "message": rec.message,
            "evidence_refs": rec.evidence_refs,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _budget_decision_event(
    run_id: str,
    sequence: int,
    rec: BudgetDecisionRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "budget_decision",
        "agent_id": rec.issuer_card_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "intent_id": rec.intent_id,
            "metric": rec.metric,
            "verdict": rec.verdict,
            "used": rec.used,
            "limit": rec.limit,
            "reason": rec.reason,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _memory_governance_event(
    run_id: str,
    sequence: int,
    rec: MemoryGovernanceRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "memory_governance",
        "agent_id": rec.agent_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "action": rec.action,
            "verdict": rec.verdict,
            "memory_id": rec.memory_id,
            "from_state": rec.from_state,
            "to_state": rec.to_state,
            "reason_code": rec.reason_code,
            "message": rec.message,
            "evidence_refs": rec.evidence_refs,
            "source_trace_ids": rec.source_trace_ids,
            "confidence": rec.confidence,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _tool_contract_violation_event(
    run_id: str,
    sequence: int,
    rec: ToolContractViolationRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "tool_contract_violation",
        "agent_id": rec.issuer_card_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "tool": rec.tool,
            "phase": rec.phase,
            "code": rec.code,
            "reason": rec.reason,
            "arg": rec.arg,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _approval_receipt_event(
    run_id: str,
    sequence: int,
    rec: ApprovalReceiptRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "approval_receipt",
        "agent_id": rec.issuer_card_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "request_id": rec.request_id,
            "receipt_id": rec.receipt_id,
            "tool": rec.tool,
            "risk_class": rec.risk_class,
            "outcome": rec.outcome,
            "reason": rec.reason,
            "decided_by": rec.decided_by,
            "preview_summary": rec.preview_summary,
            "approved_scope": rec.approved_scope,
            "trace_id": rec.trace_id,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _praxis_event(
    run_id: str,
    sequence: int,
    rec: PraxisEventRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "praxis_event",
        "agent_id": rec.agent_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "event_type": rec.event_type,
            "subject_id": rec.subject_id,
            "summary": rec.summary,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _sandbox_violation_event(
    run_id: str,
    sequence: int,
    rec: SandboxViolationRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "sandbox_violation",
        "agent_id": rec.issuer_card_id,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "profile_name": rec.profile_name,
            "tool": rec.tool,
            "attempted_action": rec.attempted_action,
            "reason": rec.reason,
            "attempted_path": rec.attempted_path,
            "severity": rec.severity,
            "details": rec.details,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _sandbox_attestation_event(
    run_id: str,
    sequence: int,
    rec: SandboxAttestationRecord,
) -> TraceEvent:
    event = {
        "event_id": rec.id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": rec.created_at,
        "event_type": "sandbox_attestation",
        "agent_id": None,
        "command_hash": None,
        "observation_hash": None,
        "verifier_hash": None,
        "prev_entry_hash": rec.prev_entry_hash,
        "payload": {
            "backend": rec.backend,
            "available": rec.available,
            "hard_isolated": rec.hard_isolated,
            "reason": rec.reason,
            "probe": rec.probe,
            "host": rec.host,
        },
    }
    event["entry_hash"] = _entry_hash(event)
    return event


def _record_from_event(ev: TraceEvent) -> TraceEntry:
    payload = ev.get("payload", {})
    if ev.get("event_type") == "planning_failure":
        rec = PlanningFailureRecord(
            id=ev["event_id"],
            intent_id=payload.get("intent_id", ""),
            issuer_card_id=ev.get("agent_id") or "",
            status=payload.get("status", ""),
            reason=payload.get("reason", ""),
            details=payload.get("details", {}),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
        return rec
    if ev.get("event_type") == "runtime_status_transition":
        return RuntimeStatusTransitionRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            intent_id=payload.get("intent_id", ""),
            issuer_card_id=ev.get("agent_id", ""),
            from_status=payload.get("from_status", ""),
            to_status=payload.get("to_status", ""),
            reason_code=payload.get("reason_code", ""),
            message=payload.get("message", ""),
            evidence_refs=payload.get("evidence_refs", []),
            details=payload.get("details", {}),
            command_hash=ev.get("command_hash"),
            observation_hash=ev.get("observation_hash"),
            verifier_hash=ev.get("verifier_hash"),
            mandate_id=payload.get("mandate_id", ""),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "budget_decision":
        return BudgetDecisionRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            intent_id=payload.get("intent_id", ""),
            issuer_card_id=ev.get("agent_id", ""),
            metric=payload.get("metric", ""),
            verdict=payload.get("verdict", ""),
            used=payload.get("used", 0.0),
            limit=payload.get("limit", 0.0),
            reason=payload.get("reason", ""),
            details=payload.get("details", {}),
            mandate_id=payload.get("mandate_id", ""),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "memory_governance":
        return MemoryGovernanceRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            agent_id=ev.get("agent_id", ""),
            action=payload.get("action", ""),
            verdict=payload.get("verdict", ""),
            memory_id=payload.get("memory_id", ""),
            from_state=payload.get("from_state", ""),
            to_state=payload.get("to_state", ""),
            reason_code=payload.get("reason_code", ""),
            message=payload.get("message", ""),
            evidence_refs=payload.get("evidence_refs", []),
            source_trace_ids=payload.get("source_trace_ids", []),
            confidence=payload.get("confidence", 0.0),
            details=payload.get("details", {}),
            mandate_id=payload.get("mandate_id", ""),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "tool_contract_violation":
        return ToolContractViolationRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            issuer_card_id=ev.get("agent_id", ""),
            tool=payload.get("tool", ""),
            phase=payload.get("phase", ""),
            code=payload.get("code", ""),
            reason=payload.get("reason", ""),
            arg=payload.get("arg", ""),
            details=payload.get("details", {}),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "approval_receipt":
        return ApprovalReceiptRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            issuer_card_id=ev.get("agent_id", ""),
            request_id=payload.get("request_id", ""),
            receipt_id=payload.get("receipt_id", ""),
            tool=payload.get("tool", ""),
            risk_class=payload.get("risk_class", ""),
            outcome=payload.get("outcome", ""),
            reason=payload.get("reason", ""),
            decided_by=payload.get("decided_by", ""),
            preview_summary=payload.get("preview_summary", ""),
            approved_scope=payload.get("approved_scope", []),
            trace_id=payload.get("trace_id", ""),
            mandate_id=payload.get("mandate_id", ""),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "praxis_event":
        return PraxisEventRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            agent_id=ev.get("agent_id", ""),
            event_type=payload.get("event_type", ""),
            subject_id=payload.get("subject_id", ""),
            summary=payload.get("summary", ""),
            details=payload.get("details", {}),
            mandate_id=payload.get("mandate_id", ""),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "sandbox_violation":
        return SandboxViolationRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            issuer_card_id=ev.get("agent_id", ""),
            profile_name=payload.get("profile_name", ""),
            tool=payload.get("tool", ""),
            attempted_action=payload.get("attempted_action", ""),
            reason=payload.get("reason", ""),
            attempted_path=payload.get("attempted_path", ""),
            severity=payload.get("severity", "deny"),
            details=payload.get("details", {}),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )
    if ev.get("event_type") == "sandbox_attestation":
        return SandboxAttestationRecord(
            id=ev["event_id"],
            run_id=ev.get("run_id", ""),
            backend=payload.get("backend", ""),
            available=payload.get("available", False),
            hard_isolated=payload.get("hard_isolated", False),
            reason=payload.get("reason", ""),
            probe=payload.get("probe", ""),
            host=payload.get("host", {}),
            created_at=ev.get("timestamp", now()),
            prev_entry_hash=ev.get("prev_entry_hash", ""),
            entry_hash=ev.get("entry_hash", ""),
        )

    vr = payload.get("verifier_result", {})
    rec = StateTransitionRecord(
        id=ev["event_id"],
        before_state_hash=payload.get("before_state_hash", ""),
        command_hash=ev.get("command_hash") or "",
        observation_hash=ev.get("observation_hash") or "",
        after_state_hash=payload.get("after_state_hash", ""),
        verifier_result=VerifierResult(
            passed=vr.get("passed", False),
            verifier=vr.get("verifier", ""),
            evidence=vr.get("evidence", {}),
            reason=vr.get("reason", ""),
            code=vr.get("code", ""),
        ),
        policy_verdict=PolicyVerdict(payload.get("policy_verdict", PolicyVerdict.DENY.value)),
        issuer_card_id=ev.get("agent_id") or "",
        parent_intent_id=payload.get("parent_intent_id"),
        created_at=ev.get("timestamp", now()),
        prev_entry_hash=ev.get("prev_entry_hash", ""),
        entry_hash=ev.get("entry_hash", ""),
    )
    return rec


def _entry_hash(event: TraceEvent) -> str:
    body = dict(event)
    body.pop("entry_hash", None)
    return sha(canonical_json(body))


def _merkle_root_of_events(events: list[TraceEvent]) -> str:
    """Merkle root over on-disk events — must match ``merkle_root`` on live events."""
    if not events:
        return GENESIS
    layer = [_entry_hash(e) for e in events]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else layer[i]
            nxt.append(sha(a, b))
        layer = nxt
    return layer[0]


def _append_jsonl(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(item))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _verify_events(
    events: list[dict[str, Any]], run_id: str, genesis: str = GENESIS
) -> tuple[bool, Optional[int], str, str]:
    prev = genesis
    for i, event in enumerate(events):
        seq = i + 1
        if event.get("run_id") != run_id:
            return False, i, "run_id mismatch", prev
        if event.get("sequence") != seq:
            return False, i, "sequence mismatch", prev
        if event.get("prev_entry_hash") != prev:
            return False, i, "prev hash mismatch", prev
        expected = _entry_hash(event)
        if event.get("entry_hash") != expected:
            return False, i, "entry hash mismatch", prev
        prev = event["entry_hash"]
    return True, None, "", prev


def _verify_checkpoints(
    events: list[dict[str, Any]],
    checkpoints: list[dict[str, Any]],
    checkpoint_every: int,
    run_id: str,
) -> tuple[bool, str]:
    expected_sequences = list(range(checkpoint_every, len(events) + 1, checkpoint_every))
    if len(checkpoints) != len(expected_sequences):
        return False, "checkpoint count mismatch"
    prev_cp = GENESIS
    for cp, seq in zip(checkpoints, expected_sequences):
        if cp.get("run_id") != run_id:
            return False, "checkpoint run_id mismatch"
        if cp.get("sequence") != seq:
            return False, "checkpoint sequence mismatch"
        if cp.get("previous_checkpoint_hash") != prev_cp:
            return False, "checkpoint previous hash mismatch"
        expected = {
            "run_id": run_id,
            "sequence": seq,
            "previous_checkpoint_hash": prev_cp,
            "chain_head": events[seq - 1]["entry_hash"],
        }
        expected_hash = sha(canonical_json(expected))
        if cp.get("checkpoint_hash") != expected_hash:
            return False, "checkpoint hash mismatch"
        prev_cp = cp["checkpoint_hash"]
    return True, ""


# Backward compatibility: existing code imports TraceLedger.
TraceLedger = InMemoryTraceLedger

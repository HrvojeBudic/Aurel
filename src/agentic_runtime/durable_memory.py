"""A3 — DurableMemoryFabric: persistence as a projection over the governed trace.

`DurableMemoryFabric` is a `MemoryFabric` that additionally *mirrors* every
governed write (record) and edge to a durable backend, and can *rebuild* the
in-RAM store from that backend. It is never a second source of truth:

* **Trace = single source of truth.** On rebuild, every persisted entry is
  re-verified against the bound trace — its ``source_trace_ids`` must all be
  known trace entries AND the trace must carry a governed *allow* event for it.
  Anything unanchored is **quarantined** (never silently trusted); the decisions
  are returned as a hash-chainable :class:`DurableMemoryGovernanceRecord` report.
* **Flag load-bearing / additive.** Persistence happens only when
  ``AUREL_DURABLE_MEMORY`` is enabled (read once at construction). With the flag
  OFF the fabric touches no disk and is byte-identical to a plain `MemoryFabric`.
* **No-overclaim.** With an unavailable backend (``available is False``), nothing
  is persisted or loaded — no faked durability.

Scope (A3): projection + re-verification + quarantine. It does NOT revise or
retract (A4), does not re-rank retrieval (A6), and is not wired into
``build_runtime``/entity (A8).
"""

from __future__ import annotations

from typing import Any, Optional

from .core_types import (DurableMemoryGovernanceRecord, MemoryRecord, MemoryTier,
                         MemoryTruthState, TruthStatus)
from .memory import MemoryFabric
from .memory_bitemporal import _flag_enabled
from .memory_governance import MemoryLinkDecision, MemoryLinkRequest
from .memory_graph import MemoryEdge, MemoryRelation

# JSONL entry kinds.
_KIND_RECORD = "record"
_KIND_EDGE = "edge"


def record_to_entry(rec: MemoryRecord) -> dict[str, Any]:
    """A durable JSONL entry for a record. Drops the (recomputable) embedding so
    the log stays compact and deterministic — ``_store`` regenerates it on admit."""
    data = rec.to_dict()
    data.pop("embedding", None)
    return {"kind": _KIND_RECORD, "data": data}


def record_from_dict(data: dict[str, Any]) -> MemoryRecord:
    d = dict(data)
    d.pop("embedding", None)
    d["tier"] = MemoryTier(d["tier"])
    d["truth_status"] = TruthStatus(d["truth_status"])
    d["truth_state"] = MemoryTruthState(d["truth_state"])
    return MemoryRecord(**d)


def edge_to_entry(edge: MemoryEdge) -> dict[str, Any]:
    return {"kind": _KIND_EDGE, "data": edge.to_dict()}


def edge_from_dict(data: dict[str, Any]) -> MemoryEdge:
    d = dict(data)
    d["relation"] = MemoryRelation(d["relation"])
    return MemoryEdge(**d)


class DurableMemoryFabric(MemoryFabric):
    """A trace-projecting, persistence-mirroring memory fabric."""

    def __init__(self, backend: Any = None, *, embedder: Any = None,
                 ephemeral_size: int = 24, policy: Any = None) -> None:
        super().__init__(embedder, ephemeral_size, policy)
        self.backend = backend
        # Read the flag ONCE at construction: flag OFF ⇒ byte-identical to base.
        self._persist_enabled = _flag_enabled()
        self.quarantine_report: list[DurableMemoryGovernanceRecord] = []

    # -- durability posture --------------------------------------------- #
    @property
    def durable_enabled(self) -> bool:
        return bool(
            self._persist_enabled
            and self.backend is not None
            and getattr(self.backend, "available", False)
        )

    # -- write mirroring (governed path only) --------------------------- #
    def _store(self, rec: MemoryRecord) -> MemoryRecord:
        # The base funnel already traced + governed the write before _store runs;
        # we only mirror the admitted record. Append-only: promotions re-store and
        # thus append a new version line.
        stored = super()._store(rec)
        if self.durable_enabled:
            self.backend.append(record_to_entry(stored))
        return stored

    def link(self, request: MemoryLinkRequest) -> MemoryLinkDecision:
        decision = super().link(request)
        if self.durable_enabled and decision.allowed and decision.edge is not None:
            self.backend.append(edge_to_entry(decision.edge))
        return decision

    # -- rebuild (projection over the trace) ---------------------------- #
    def load(self, trace: Any = None) -> list[DurableMemoryGovernanceRecord]:
        """Rebuild the in-RAM store from the backend, re-verified against the
        trace. Returns the admit/quarantine report (also on ``quarantine_report``).
        Flag OFF / unavailable backend ⇒ no-op empty report (byte-identical)."""
        report: list[DurableMemoryGovernanceRecord] = []
        self.quarantine_report = report
        if not self.durable_enabled:
            return report

        trace = trace if trace is not None else self._trace
        run_id = str(getattr(trace, "run_id", "") or "")
        known_ids, allow_writes, allow_links = self._trace_index(trace)
        entries = self.backend.load()

        # Records: append-only ⇒ the LAST version per memory_id is current. Keep
        # first-seen order for deterministic admission.
        order: list[str] = []
        latest: dict[str, dict[str, Any]] = {}
        for e in entries:
            if e.get("kind") != _KIND_RECORD:
                continue
            mid = str(e.get("data", {}).get("memory_id", ""))
            if mid not in latest:
                order.append(mid)
            latest[mid] = e

        admitted: set[str] = set()
        for mid in order:
            rec = record_from_dict(latest[mid]["data"])
            ok, reason = self._record_anchored(rec, known_ids, allow_writes)
            report.append(DurableMemoryGovernanceRecord.make(
                run_id=run_id, action="load_record",
                verdict="admit" if ok else "quarantine",
                memory_id=rec.memory_id, reason_code=reason,
                source_trace_ids=list(rec.source_trace_ids)))
            if ok:
                MemoryFabric._store(self, rec)   # non-persisting admit
                admitted.add(rec.memory_id)

        # Edges after records: an edge to a quarantined endpoint is quarantined.
        for e in entries:
            if e.get("kind") != _KIND_EDGE:
                continue
            edge = edge_from_dict(e["data"])
            ok, reason = self._edge_anchored(edge, known_ids, allow_links, admitted)
            report.append(DurableMemoryGovernanceRecord.make(
                run_id=run_id, action="load_edge",
                verdict="admit" if ok else "quarantine",
                memory_id=edge.edge_id, reason_code=reason,
                source_trace_ids=list(edge.source_trace_ids)))
            if ok:
                self.graph.add(edge)

        return report

    def quarantined(self) -> list[DurableMemoryGovernanceRecord]:
        return [r for r in self.quarantine_report if r.verdict == "quarantine"]

    # -- re-verification helpers ---------------------------------------- #
    def _trace_index(self, trace: Any) -> tuple[set, set, set]:
        known_ids: set[Any] = set()
        allow_writes: set[Any] = set()
        allow_links: set[Any] = set()
        if trace is None:
            return known_ids, allow_writes, allow_links
        known_ids = {getattr(e, "id", None) for e in trace}
        for ev in trace.replay():
            if ev.get("kind") != "memory_governance" or ev.get("verdict") != "allow":
                continue
            action = ev.get("action")
            if action in ("write", "promote"):
                allow_writes.add(ev.get("memory_id"))
            elif action == "link":
                allow_links.add(ev.get("memory_id"))
        return known_ids, allow_writes, allow_links

    def _record_anchored(self, rec: MemoryRecord, known_ids: set,
                         allow_writes: set) -> tuple[bool, str]:
        if any(t not in known_ids for t in rec.source_trace_ids):
            return False, "unverified_source_trace"
        if rec.memory_id not in allow_writes:
            return False, "unanchored_no_governance_event"
        return True, "anchored"

    def _edge_anchored(self, edge: MemoryEdge, known_ids: set, allow_links: set,
                       admitted: set) -> tuple[bool, str]:
        if edge.edge_id not in allow_links:
            return False, "unanchored_no_governance_event"
        if any(t not in known_ids for t in edge.source_trace_ids):
            return False, "unverified_source_trace"
        if edge.from_id not in admitted or edge.to_id not in admitted:
            return False, "endpoint_quarantined"
        return True, "anchored"


__all__ = [
    "DurableMemoryFabric",
    "record_to_entry",
    "record_from_dict",
    "edge_to_entry",
    "edge_from_dict",
]

"""A7 — Memory Explorer: a read-only projection of memory state from the trace.

`MemoryProjection` reconstructs the memory picture **only** from the governed
trace's memory-governance events (and, optionally, the A3 durable store for record
*content*). It is a projection, never an authority: it mints nothing, writes
nothing, and holds no fabric. The trace remains the single source of truth.

Reconstructs, from the ordered ``memory_governance`` replay events:

* **current records** — allowed writes/promotions/update-successors, minus any
  record later superseded (A4 update), retracted, or forgotten;
* **belief history** — the supersession chain (A4 ``update`` rows carry
  ``target_id`` → ``new_memory_id`` in ``details``);
* **graph** — typed edges (A2 ``link`` rows carry ``from_id``/``to_id``/``relation``
  in ``details``);
* **rejected** — governance *deny* rows (kept for audit).

This closes the A2/A3/A4 "D2" seam: those specifics used to live only in the
governance-row ``details``, which ``trace.replay()`` dropped — so a pure trace
replay could not rebuild the graph/revision views. A7 surfaces ``details`` in
``replay()``, and this projection consumes it.

Determinism: every list is sorted by a stable key (never ``hash()``). Fail-closed:
an empty/absent trace ⇒ empty views; content is ``None`` when no durable store is
supplied (honest, never fabricated).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

_WRITE_ACTIONS = ("write", "promote")
_RETIRE_ACTIONS = ("retract", "forget")


@dataclass
class ProjectedEdge:
    from_id: str
    to_id: str
    relation: str
    edge_id: str = ""

    def key(self) -> tuple:
        return (self.from_id, self.to_id, self.relation, self.edge_id)


@dataclass
class MemoryProjection:
    """A read-only snapshot rebuilt from trace memory-governance events."""

    current_ids: list[str] = field(default_factory=list)
    states: dict[str, str] = field(default_factory=dict)
    edges: list[ProjectedEdge] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    _superseded_by: dict[str, str] = field(default_factory=dict)
    _revises: dict[str, str] = field(default_factory=dict)
    _content: dict[str, str] = field(default_factory=dict)

    # -- construction ---------------------------------------------------- #
    @staticmethod
    def from_trace(trace: Any, backend: Any = None) -> "MemoryProjection":
        events = []
        if trace is not None and hasattr(trace, "replay"):
            events = [e for e in trace.replay() if e.get("kind") == "memory_governance"]
        return MemoryProjection.from_events(events, backend=backend)

    @staticmethod
    def from_events(events: list[dict], backend: Any = None) -> "MemoryProjection":
        proj = MemoryProjection()
        written: list[str] = []
        retired: set[str] = set()
        for ev in events:
            action = ev.get("action", "")
            verdict = ev.get("verdict", "")
            mid = ev.get("memory_id", "")
            details = ev.get("details", {}) or {}
            if action in _WRITE_ACTIONS:
                if verdict == "allow":
                    written.append(mid)
                    proj.states[mid] = ev.get("to", "")
                else:
                    proj.rejected.append({
                        "action": action,
                        "reason_code": ev.get("reason_code", ""),
                        "to": ev.get("to", ""),
                    })
            elif action == "link":
                if verdict == "allow":
                    proj.edges.append(ProjectedEdge(
                        from_id=str(details.get("from_id", "")),
                        to_id=str(details.get("to_id", "")),
                        relation=str(details.get("relation", "")),
                        edge_id=str(details.get("edge_id", "")),
                    ))
            elif action == "update":
                if verdict == "allow":
                    old = str(details.get("target_id", ""))
                    new = str(details.get("new_memory_id", ""))
                    if old:
                        proj._superseded_by[old] = new
                        retired.add(old)
                    if new:
                        proj._revises[new] = old
                        written.append(new)
                        proj.states[new] = ev.get("to", "")
                    # A4 materializes supersession as a SUPERSEDES edge (new→old)
                    # in the graph *inside* the update op (no separate link row, per
                    # A4-D1). Reconstruct that same edge from the update details so
                    # the trace-only graph matches the live fabric graph.
                    if old and new:
                        proj.edges.append(ProjectedEdge(
                            from_id=new, to_id=old, relation="supersedes"))
            elif action in _RETIRE_ACTIONS:
                if verdict == "allow" and mid:
                    retired.add(mid)

        # Current = allowed writes/successors (first-seen order), minus retired.
        proj.current_ids = [m for m in _dedupe(written) if m and m not in retired]
        proj.edges.sort(key=lambda e: e.key())
        proj.rejected.sort(key=lambda r: (r["action"], r["reason_code"]))

        # Optional content enrichment from the durable store (A3), by memory_id.
        if backend is not None and getattr(backend, "available", False):
            for entry in backend.load():
                if entry.get("kind") == "record":
                    data = entry.get("data", {})
                    rid = str(data.get("memory_id", ""))
                    if rid:
                        proj._content[rid] = str(data.get("content", ""))
        return proj

    @staticmethod
    def from_as_of_records(records: list[Any], backend: Any = None) -> "MemoryProjection":
        """Build a read-only snapshot from an A0 as-of record set (F8.4)."""
        proj = MemoryProjection()
        ids: set[str] = set()
        for rec in records:
            mid = str(getattr(rec, "memory_id", "") or getattr(rec, "id", "") or "")
            if mid:
                ids.add(mid)
        for rec in records:
            mid = str(getattr(rec, "memory_id", "") or getattr(rec, "id", "") or "")
            if not mid:
                continue
            proj.current_ids.append(mid)
            ts = getattr(rec, "truth_state", "")
            proj.states[mid] = ts.value if hasattr(ts, "value") else str(ts)
            nxt = getattr(rec, "superseded_by", None)
            if nxt and str(nxt) in ids:
                proj._superseded_by[mid] = str(nxt)
            prev = getattr(rec, "revises", None)
            if prev and str(prev) in ids:
                proj._revises[mid] = str(prev)
        proj.current_ids = sorted(set(proj.current_ids))
        if backend is not None and getattr(backend, "available", False):
            for entry in backend.load():
                if entry.get("kind") == "record":
                    data = entry.get("data", {})
                    rid = str(data.get("memory_id", ""))
                    if rid:
                        proj._content[rid] = str(data.get("content", ""))
        return proj

    # -- read-only views ------------------------------------------------- #
    def belief_history(self, memory_id: str) -> list[str]:
        """The supersession chain containing ``memory_id``, oldest → newest.
        Fail-closed: an id the trace never mentions ⇒ ``[]``."""
        known = set(self._superseded_by) | set(self._revises.values()) \
            | set(self._revises) | set(self._superseded_by.values()) \
            | set(self.states)
        if memory_id not in known:
            return []
        seen = {memory_id}
        back: list[str] = []
        cur = memory_id
        while cur in self._revises and self._revises[cur] and self._revises[cur] not in seen:
            cur = self._revises[cur]
            seen.add(cur)
            back.append(cur)
        chain = list(reversed(back)) + [memory_id]
        cur = memory_id
        while cur in self._superseded_by and self._superseded_by[cur] \
                and self._superseded_by[cur] not in seen:
            cur = self._superseded_by[cur]
            seen.add(cur)
            chain.append(cur)
        return chain

    def edge_tuples(self) -> list[tuple[str, str, str]]:
        """Deterministic ``(from_id, to_id, relation)`` triples."""
        return [(e.from_id, e.to_id, e.relation) for e in self.edges]

    def content_for(self, memory_id: str) -> Optional[str]:
        """Record content if a durable store was supplied, else ``None`` (honest)."""
        return self._content.get(memory_id)

    def records(self) -> list[dict]:
        out = []
        for mid in self.current_ids:
            out.append({
                "memory_id": mid,
                "truth_state": self.states.get(mid, ""),
                "content": self._content.get(mid),
            })
        return out

    def to_dict(self) -> dict:
        return {
            "current_count": len(self.current_ids),
            "current_ids": list(self.current_ids),
            "edges": [list(t) for t in self.edge_tuples()],
            "edge_count": len(self.edges),
            "rejected_count": len(self.rejected),
            "rejected": list(self.rejected),
            "content_available": bool(self._content),
        }


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


__all__ = ["MemoryProjection", "ProjectedEdge"]

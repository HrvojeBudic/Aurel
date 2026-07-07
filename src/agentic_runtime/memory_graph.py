"""A2 — Typed relation graph over memory records.

A thin, governed, **append-only** graph laid *beside* the memory store. Records
stay the atoms; edges express typed relations between them (`SUPERSEDES`,
`CONTRADICTS`, `SUPPORTS`, `RELATES_TO`, `DERIVED_FROM`). Every edge is written
only through the governed funnel (`MemoryWritePolicy.evaluate_link` →
`MemoryFabric.link` → one `MemoryGovernanceRecord(action="link")`); nothing here
mutates a record, touches retrieval, or writes the trace itself.

Boundary (cross-cutting invariants):

* **Edges are governed writes.** No path adds a `MemoryEdge` except through the
  fabric funnel. `SUPERSEDES`/`CONTRADICTS` are evidence-gated; unknown endpoints
  and unknown relations fail closed. An edge never carries a truth state, so it
  can never elevate a record's trust — that stays the promotion ladder's job.
* **Append-only / deterministic.** The index is an insertion-ordered list; reads
  preserve insertion order and never sort by the (uuid) ``edge_id`` or ``hash()``.
* **Bi-temporal, like records (A0).** An edge carries default-open valid/
  transaction stamps so a later phase can close a belief without deleting history.
* **A2 is edge-only.** Supersession is expressed as a `SUPERSEDES` *edge* (walk it
  with `detect_supersession_chain`); A2 does NOT write `MemoryRecord.superseded_by`
  or close any interval — record-field supersession + belief revision are A4.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

from .core_types import canonical_json, new_id, now, sha


class MemoryRelation(str, Enum):
    """Closed-world typed relations. Unknown strings fail closed at governance."""

    SUPERSEDES = "supersedes"        # from_id is the newer belief that replaces to_id
    CONTRADICTS = "contradicts"      # from_id conflicts with to_id
    SUPPORTS = "supports"            # from_id is corroborating evidence for to_id
    RELATES_TO = "relates_to"        # generic association
    DERIVED_FROM = "derived_from"    # from_id was derived/summarized from to_id
    SUMMARIZES = "summarizes"        # A5: from_id is a consolidated summary of to_id


# Relations that assert a change to the belief landscape must carry evidence, so
# an agent cannot cheaply retire or refute a memory by fiat.
EVIDENCE_GATED_RELATIONS = frozenset({MemoryRelation.SUPERSEDES, MemoryRelation.CONTRADICTS})


@dataclass(frozen=True)
class MemoryEdge:
    """An immutable, bi-temporal typed edge between two memory records.

    Frozen: append-only history. Provenance mirrors a governed write; the four
    default-open stamps mirror A0's :class:`BiTemporalStamp` so an edge belief can
    later be closed (A4) without deleting the record of it having held.
    """

    edge_id: str
    from_id: str
    to_id: str
    relation: MemoryRelation
    writer_kind: str = "system"
    created_by: str = ""
    source_run_id: str = ""
    source_trace_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.5
    created_at: float = field(default_factory=now)
    # A0-style bi-temporal stamps (default-open ⇒ current).
    valid_from: Optional[float] = None
    valid_to: Optional[float] = None
    transaction_from: Optional[float] = None
    transaction_to: Optional[float] = None

    @staticmethod
    def make(*, from_id: str, to_id: str, relation: MemoryRelation,
             **kw) -> "MemoryEdge":
        return MemoryEdge(id_or_edge_id(), from_id, to_id, relation, **kw)

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "memory_edge",
            "edge_id": self.edge_id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation": self.relation.value,
            "writer_kind": self.writer_kind,
            "created_by": self.created_by,
            "source_run_id": self.source_run_id,
            "source_trace_ids": self.source_trace_ids,
            "evidence_refs": self.evidence_refs,
            "confidence": self.confidence,
        }))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["relation"] = self.relation.value
        return d


def id_or_edge_id() -> str:
    """A fresh edge id. Factored out so ``make`` reads cleanly."""
    return new_id("mem_edge")


class MemoryGraphIndex:
    """Append-only edge store with insertion-ordered adjacency reads.

    Determinism is structural: ``_edges`` is a list in insertion order and every
    read returns a filtered view of it (never sorted by the uuid ``edge_id``).
    Every lookup fails closed — an unknown id yields ``[]``, never a guess.
    """

    def __init__(self) -> None:
        self._edges: list[MemoryEdge] = []
        self._out: dict[str, list[MemoryEdge]] = {}
        self._in: dict[str, list[MemoryEdge]] = {}

    def add(self, edge: MemoryEdge) -> MemoryEdge:
        self._edges.append(edge)
        self._out.setdefault(edge.from_id, []).append(edge)
        self._in.setdefault(edge.to_id, []).append(edge)
        return edge

    def all_edges(self) -> list[MemoryEdge]:
        return list(self._edges)

    def edges_from(self, memory_id: str) -> list[MemoryEdge]:
        return list(self._out.get(memory_id, []))

    def edges_to(self, memory_id: str) -> list[MemoryEdge]:
        return list(self._in.get(memory_id, []))

    def neighbors(self, memory_id: str,
                  relation: Optional[MemoryRelation] = None) -> list[str]:
        """Ids reachable by an outgoing edge, optionally filtered by relation.
        Insertion-ordered, de-duplicated keeping first occurrence."""
        out: list[str] = []
        for e in self._out.get(memory_id, []):
            if relation is not None and e.relation is not relation:
                continue
            if e.to_id not in out:
                out.append(e.to_id)
        return out

    def by_relation(self, relation: MemoryRelation) -> list[MemoryEdge]:
        return [e for e in self._edges if e.relation is relation]

    def knows(self, memory_id: str) -> bool:
        return memory_id in self._out or memory_id in self._in

    def __len__(self) -> int:
        return len(self._edges)


def detect_supersession_chain(index: MemoryGraphIndex, memory_id: str) -> list[str]:
    """The `SUPERSEDES` chain containing ``memory_id``, oldest → newest.

    ``A SUPERSEDES B`` ⇒ A is newer than B. From the seed we walk to the oldest
    (following outgoing `SUPERSEDES`: seed supersedes an older node) then to the
    newest (following incoming `SUPERSEDES`: a newer node supersedes seed). Cycle-
    guarded and deterministic (first insertion-ordered edge wins at each step).
    Fail-closed: an id the graph has never seen ⇒ ``[]``.
    """
    if not index.knows(memory_id):
        return []
    seen = {memory_id}

    # Walk backward to the oldest: seed --SUPERSEDES--> older.
    back: list[str] = []
    cur = memory_id
    while True:
        older = [e.to_id for e in index.edges_from(cur)
                 if e.relation is MemoryRelation.SUPERSEDES and e.to_id not in seen]
        if not older:
            break
        nxt = older[0]
        seen.add(nxt)
        back.append(nxt)
        cur = nxt

    chain: list[str] = list(reversed(back)) + [memory_id]

    # Walk forward to the newest: newer --SUPERSEDES--> seed.
    cur = memory_id
    while True:
        newer = [e.from_id for e in index.edges_to(cur)
                 if e.relation is MemoryRelation.SUPERSEDES and e.from_id not in seen]
        if not newer:
            break
        nxt = newer[0]
        seen.add(nxt)
        chain.append(nxt)
        cur = nxt

    return chain


__all__ = [
    "MemoryRelation",
    "EVIDENCE_GATED_RELATIONS",
    "MemoryEdge",
    "MemoryGraphIndex",
    "detect_supersession_chain",
]

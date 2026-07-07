"""
memory_governance.py — Memory Write Governance & Provenance (P0.9).

Memory is an attack surface: a hallucinated or failed-run conclusion that lands
in durable memory becomes a future operating assumption (memory poisoning). This
module gates every memory write and promotion:

  - Agents may NOT directly write verified / procedural / canon memory.
  - Failed runs may NOT create success (verified/procedural/canon) memory.
  - Untrusted tool output can only ever become CANDIDATE memory.
  - Every write requires a valid trace reference (a real run + known trace ids).
  - Promotion is gated:
        candidate  -> verified    requires evidence
        verified   -> procedural  requires repeated successful traces
        procedural -> canon       requires explicit approval

Every decision (allow / deny / promote) is emitted to the trace ledger by the
MemoryFabric, so no memory mutation is invisible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .core_types import (
    MemoryRecord,
    MemoryTier,
    MemoryTruthState,
    TruthStatus,
)

# Writer classes that are NOT permitted to author trusted knowledge directly.
AGENT_WRITER = "agent"

# States an agent (or untrusted source) may never mint directly.
_RESTRICTED_DIRECT = {
    MemoryTruthState.VERIFIED,
    MemoryTruthState.PROCEDURAL,
    MemoryTruthState.CANON,
}

_SUCCESS_STATES = {
    MemoryTruthState.VERIFIED,
    MemoryTruthState.PROCEDURAL,
    MemoryTruthState.CANON,
}

MIN_REPEATED_SUCCESS = 2


def tier_for_state(state: MemoryTruthState) -> MemoryTier:
    return {
        MemoryTruthState.RAW: MemoryTier.EPHEMERAL,
        MemoryTruthState.EPISODIC: MemoryTier.EPISODIC,
        MemoryTruthState.CANDIDATE: MemoryTier.SEMANTIC,
        MemoryTruthState.VERIFIED: MemoryTier.SEMANTIC,
        MemoryTruthState.PROCEDURAL: MemoryTier.PROCEDURAL,
        MemoryTruthState.CANON: MemoryTier.CANON,
        MemoryTruthState.REJECTED: MemoryTier.EPHEMERAL,
        MemoryTruthState.EXPIRED: MemoryTier.EPHEMERAL,
    }[state]


def state_for_tier(tier: MemoryTier) -> MemoryTruthState:
    return {
        MemoryTier.EPHEMERAL: MemoryTruthState.RAW,
        MemoryTier.EPISODIC: MemoryTruthState.EPISODIC,
        MemoryTier.SEMANTIC: MemoryTruthState.CANDIDATE,
        MemoryTier.PROCEDURAL: MemoryTruthState.PROCEDURAL,
        MemoryTier.CANON: MemoryTruthState.CANON,
    }[tier]


def _default_truth_status(state: MemoryTruthState) -> TruthStatus:
    if state in _SUCCESS_STATES:
        return TruthStatus.VERIFIED
    if state is MemoryTruthState.REJECTED:
        return TruthStatus.CONTRADICTED
    return TruthStatus.ASSERTED


def _promotion_state(state: MemoryTruthState) -> str:
    if state in (
        MemoryTruthState.CANDIDATE,
        MemoryTruthState.VERIFIED,
        MemoryTruthState.PROCEDURAL,
        MemoryTruthState.CANON,
    ):
        return state.value
    return "none"


@dataclass
class MemoryWriteRequest:
    content: str
    proposed_truth_state: MemoryTruthState = MemoryTruthState.RAW
    writer_kind: str = "system"          # agent | runtime | verifier | operator | system
    created_by: str = ""
    source_run_id: str = ""
    source_command_id: Optional[str] = None
    source_trace_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.5
    importance: float = 0.5
    run_succeeded: Optional[bool] = None
    trust: str = "trusted"               # trusted | untrusted
    approved: bool = False
    truth_status: Optional[TruthStatus] = None
    expiry_policy: dict[str, Any] = field(default_factory=lambda: {"kind": "none"})
    links: list[str] = field(default_factory=list)


@dataclass
class MemoryLinkRequest:
    """A2 — a proposed typed edge between two existing memory records. The
    ``writer_kind`` is set by whoever constructs the request (the runtime), never
    by a tool arg, so an agent cannot self-elevate. ``relation`` is a
    ``MemoryRelation`` *value* (validated closed-world at governance)."""

    from_id: str
    to_id: str
    relation: str
    writer_kind: str = "system"          # agent | runtime | verifier | operator | system
    created_by: str = ""
    source_run_id: str = ""
    source_trace_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class MemoryLinkDecision:
    allowed: bool
    relation: str
    reason_code: str
    message: str
    edge: Optional[Any] = None           # a MemoryEdge when allowed, else None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "relation": self.relation,
            "reason_code": self.reason_code,
            "message": self.message,
            "edge_id": getattr(self.edge, "edge_id", "") if self.edge else "",
        }


@dataclass
class MemoryWriteDecision:
    allowed: bool
    effective_truth_state: MemoryTruthState
    reason_code: str
    message: str
    record: Optional[MemoryRecord] = None
    action: str = "write"
    from_state: str = ""

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "effective_truth_state": self.effective_truth_state.value,
            "reason_code": self.reason_code,
            "message": self.message,
            "action": self.action,
            "from_state": self.from_state,
            "memory_id": self.record.memory_id if self.record else "",
        }


class MemoryWritePolicy:
    """Pure decision logic; performs no I/O and emits no trace itself."""

    def __init__(self, min_repeated_success: int = MIN_REPEATED_SUCCESS) -> None:
        self.min_repeated_success = min_repeated_success

    # ---- writes ------------------------------------------------------- #
    def evaluate_write(
        self,
        req: MemoryWriteRequest,
        trace: Any = None,
    ) -> MemoryWriteDecision:
        proposed = req.proposed_truth_state

        # 1. Trace reference is mandatory.
        if not req.source_run_id:
            return self._deny(proposed, "missing_trace_reference",
                              "memory write requires a source_run_id")
        if trace is not None:
            run_id = getattr(trace, "run_id", None)
            if run_id is not None and req.source_run_id != run_id:
                return self._deny(proposed, "invalid_trace_reference",
                                  "source_run_id does not match the active run")
            if req.source_trace_ids:
                known = {getattr(e, "id", None) for e in trace}
                missing = [t for t in req.source_trace_ids if t not in known]
                if missing:
                    return self._deny(proposed, "invalid_trace_reference",
                                      f"unknown source_trace_ids: {missing}")

        # 2. Agents cannot directly mint trusted knowledge.
        if req.writer_kind == AGENT_WRITER and proposed in _RESTRICTED_DIRECT:
            return self._deny(proposed, "agent_cannot_write_restricted",
                              f"agents may not directly write {proposed.value} memory")

        # 3. Canon always requires explicit approval (operator or approved flag).
        if proposed is MemoryTruthState.CANON and not (
            req.approved or req.writer_kind == "operator"
        ):
            return self._deny(proposed, "canon_requires_approval",
                              "canon memory requires explicit approval")

        # 4. Failed runs cannot create success memory.
        if req.run_succeeded is False and proposed in _SUCCESS_STATES:
            return self._deny(proposed, "failed_run_cannot_write_success",
                              "a failed run cannot create success/procedural memory")

        # 5. Untrusted tool output can only ever become candidate.
        effective = proposed
        reason_code = "allowed"
        message = "memory write allowed"
        if req.trust == "untrusted" and proposed in _RESTRICTED_DIRECT:
            effective = MemoryTruthState.CANDIDATE
            reason_code = "downgraded_untrusted"
            message = "untrusted output downgraded to candidate"

        record = self._build_record(req, effective)
        return MemoryWriteDecision(True, effective, reason_code, message, record=record)

    # ---- promotions --------------------------------------------------- #
    def evaluate_promotion(
        self,
        current: MemoryTruthState,
        target: MemoryTruthState,
        *,
        evidence_refs: Optional[list[str]] = None,
        success_trace_ids: Optional[list[str]] = None,
        approved: bool = False,
    ) -> tuple[bool, str, str]:
        if current is MemoryTruthState.CANDIDATE and target is MemoryTruthState.VERIFIED:
            if not evidence_refs:
                return False, "promotion_requires_evidence", \
                    "candidate -> verified requires evidence_refs"
            return True, "promoted_verified", "candidate promoted to verified with evidence"

        if current is MemoryTruthState.VERIFIED and target is MemoryTruthState.PROCEDURAL:
            distinct = len(set(success_trace_ids or []))
            if distinct < self.min_repeated_success:
                return False, "promotion_requires_repeated_success", \
                    f"verified -> procedural requires >= {self.min_repeated_success} distinct successful traces"
            return True, "promoted_procedural", "verified promoted to procedural after repeated success"

        if current is MemoryTruthState.PROCEDURAL and target is MemoryTruthState.CANON:
            if not approved:
                return False, "promotion_requires_approval", \
                    "procedural -> canon requires explicit approval"
            return True, "promoted_canon", "procedural promoted to canon with approval"

        return False, "illegal_promotion", \
            f"illegal promotion {current.value} -> {target.value}"

    # ---- links (A2) --------------------------------------------------- #
    def evaluate_link(
        self,
        req: MemoryLinkRequest,
        known_ids: set[str],
        trace: Any = None,
    ) -> MemoryLinkDecision:
        """Pure decision for a typed edge write. Performs no I/O; ``known_ids`` is
        the fabric's current record-id set so endpoint existence is decided here
        (fail-closed) rather than by the caller."""
        from .memory_graph import (EVIDENCE_GATED_RELATIONS, MemoryEdge,
                                    MemoryRelation)

        # 1. Relation must be a known, closed-world type.
        try:
            relation = MemoryRelation(req.relation)
        except ValueError:
            return self._link_deny(req.relation, "illegal_relation",
                                   f"unknown memory relation: {req.relation!r}")

        # 2. Trace reference is mandatory (same discipline as evaluate_write).
        if not req.source_run_id:
            return self._link_deny(relation.value, "missing_trace_reference",
                                   "memory edge requires a source_run_id")
        if trace is not None:
            run_id = getattr(trace, "run_id", None)
            if run_id is not None and req.source_run_id != run_id:
                return self._link_deny(relation.value, "invalid_trace_reference",
                                       "source_run_id does not match the active run")
            if req.source_trace_ids:
                known = {getattr(e, "id", None) for e in trace}
                missing = [t for t in req.source_trace_ids if t not in known]
                if missing:
                    return self._link_deny(relation.value, "invalid_trace_reference",
                                           f"unknown source_trace_ids: {missing}")

        # 3. Both endpoints must exist (fail-closed) and be distinct.
        for endpoint in (req.from_id, req.to_id):
            if endpoint not in known_ids:
                return self._link_deny(relation.value, "unknown_endpoint",
                                       f"unknown memory endpoint: {endpoint!r}")
        if req.from_id == req.to_id:
            return self._link_deny(relation.value, "self_link_forbidden",
                                   "an edge may not connect a memory to itself")

        # 4. Belief-changing relations must carry evidence — an agent cannot
        #    retire or refute a memory (or thereby launder trust) by fiat.
        if relation in EVIDENCE_GATED_RELATIONS and not req.evidence_refs:
            return self._link_deny(relation.value, "link_requires_evidence",
                                   f"{relation.value} edges require evidence_refs")

        edge = MemoryEdge.make(
            from_id=req.from_id,
            to_id=req.to_id,
            relation=relation,
            writer_kind=req.writer_kind,
            created_by=req.created_by or req.writer_kind,
            source_run_id=req.source_run_id,
            source_trace_ids=list(req.source_trace_ids),
            evidence_refs=list(req.evidence_refs),
            confidence=req.confidence,
        )
        return MemoryLinkDecision(True, relation.value, "allowed",
                                  "memory edge allowed", edge=edge)

    # ---- helpers ------------------------------------------------------ #
    def _deny(self, proposed: MemoryTruthState, reason_code: str,
              message: str) -> MemoryWriteDecision:
        return MemoryWriteDecision(False, proposed, reason_code, message, record=None)

    def _link_deny(self, relation: str, reason_code: str,
                   message: str) -> MemoryLinkDecision:
        return MemoryLinkDecision(False, relation, reason_code, message, edge=None)

    def _build_record(self, req: MemoryWriteRequest,
                      state: MemoryTruthState) -> MemoryRecord:
        truth_status = req.truth_status or _default_truth_status(state)
        return MemoryRecord.make(
            tier=tier_for_state(state),
            content=req.content,
            source=req.created_by or req.writer_kind,
            truth_status=truth_status,
            confidence=req.confidence,
            importance=req.importance,
            links=list(req.links),
            created_by=req.created_by or req.writer_kind,
            source_run_id=req.source_run_id,
            source_command_id=req.source_command_id,
            source_trace_ids=list(req.source_trace_ids),
            evidence_refs=list(req.evidence_refs),
            truth_state=state,
            promotion_state=_promotion_state(state),
            expiry_policy=dict(req.expiry_policy or {"kind": "none"}),
        )

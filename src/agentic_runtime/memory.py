"""
memory.py — The Memory Fabric (Hrvoje §6.2).

NOT chat history. NOT infinite RAG. Five tiers, each with different physics.

Embeddings: deterministic char-ngram hashing via hashlib (not Python hash()).
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import deque
from typing import Any, Optional, Protocol

from .core_types import (MemoryGovernanceRecord, MemoryRecord, MemoryTier,
                         MemoryTruthState, TruthStatus, now)
from .memory_governance import (MemoryWriteDecision, MemoryWritePolicy,
                                MemoryWriteRequest, state_for_tier)


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """Char-3gram hashing into a fixed-dim bag, L2-normalized."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _bucket(self, gram: str) -> int:
        digest = hashlib.sha256(gram.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % self.dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        t = re.sub(r"\s+", " ", text.lower())
        toks = [t[i:i + 3] for i in range(max(1, len(t) - 2))]
        for g in toks:
            vec[self._bucket(g)] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class MemoryFabric:
    def __init__(self, embedder: Optional[Embedder] = None,
                 ephemeral_size: int = 24,
                 policy: Optional[MemoryWritePolicy] = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self.L1: deque[MemoryRecord] = deque(maxlen=ephemeral_size)
        self.L2: list[MemoryRecord] = []
        self.L3: list[MemoryRecord] = []
        self.L4: list[MemoryRecord] = []          # procedural memory records
        self.L5: list[MemoryRecord] = []
        self.rejected: list[MemoryRecord] = []    # denied writes, kept for audit
        self.by_id: dict[str, MemoryRecord] = {}
        self.policy = policy or MemoryWritePolicy()
        self._trace: Any = None

    def bind_trace(self, trace: Any) -> None:
        """Attach a trace ledger so every memory mutation is auditable."""
        self._trace = trace

    # ---- governed write path (P0.9) ----------------------------------- #
    def request_write(self, request: MemoryWriteRequest) -> MemoryWriteDecision:
        decision = self.policy.evaluate_write(request, trace=self._trace)
        self._trace_memory(
            action="write",
            verdict="allow" if decision.allowed else "deny",
            decision=decision,
            agent_id=request.created_by or request.writer_kind,
            run_id=request.source_run_id,
            from_state="",
            to_state=decision.effective_truth_state.value,
            evidence_refs=request.evidence_refs,
            source_trace_ids=request.source_trace_ids,
            confidence=request.confidence,
        )
        if decision.allowed and decision.record is not None:
            self._store(decision.record)
        elif decision.record is None:
            # Denials are preserved (inactive) for audit / forensics.
            rejected = self.policy._build_record(request, MemoryTruthState.REJECTED)
            rejected.truth_state = MemoryTruthState.REJECTED
            rejected.promotion_state = "rejected"
            self.rejected.append(rejected)
            self.by_id[rejected.memory_id] = rejected
        return decision

    def promote(self, memory_id: str, target: MemoryTruthState, *,
                evidence_refs: Optional[list[str]] = None,
                success_trace_ids: Optional[list[str]] = None,
                approved: bool = False,
                actor: str = "operator") -> MemoryWriteDecision:
        rec = self.by_id.get(memory_id)
        if rec is None:
            decision = MemoryWriteDecision(
                False, target, "unknown_memory",
                f"no memory record {memory_id}", action="promote")
            self._trace_memory(
                action="promote", verdict="deny", decision=decision,
                agent_id=actor, run_id=getattr(self._trace, "run_id", ""),
                from_state="", to_state=target.value)
            return decision

        current = rec.truth_state
        ok, reason_code, message = self.policy.evaluate_promotion(
            current, target,
            evidence_refs=evidence_refs,
            success_trace_ids=success_trace_ids,
            approved=approved,
        )
        decision = MemoryWriteDecision(
            ok, target if ok else current, reason_code, message,
            record=rec if ok else None, action="promote",
            from_state=current.value)
        self._trace_memory(
            action="promote",
            verdict="allow" if ok else "deny",
            decision=decision,
            agent_id=actor,
            run_id=rec.source_run_id or getattr(self._trace, "run_id", ""),
            from_state=current.value,
            to_state=target.value,
            evidence_refs=evidence_refs or [],
            source_trace_ids=success_trace_ids or [],
            confidence=rec.confidence,
        )
        if ok:
            self._relocate(rec, target)
            rec.truth_state = target
            rec.promotion_state = target.value
            if evidence_refs:
                rec.evidence_refs = list({*rec.evidence_refs, *evidence_refs})
        return decision

    def remember(self, rec: MemoryRecord, *, writer_kind: str = "system",
                 run_succeeded: Optional[bool] = None, trust: str = "trusted",
                 source_run_id: Optional[str] = None) -> MemoryRecord:
        """Backward-compatible store: routes a pre-built record through
        governance so legacy callers also gain provenance + trace."""
        trace_run = getattr(self._trace, "run_id", "") if self._trace is not None else ""
        run_id = source_run_id or rec.source_run_id or trace_run or "run_local"
        req = MemoryWriteRequest(
            content=rec.content,
            proposed_truth_state=state_for_tier(rec.tier),
            writer_kind=writer_kind,
            created_by=rec.source,
            source_run_id=run_id,
            source_command_id=rec.source_command_id,
            source_trace_ids=list(rec.links or rec.source_trace_ids),
            evidence_refs=list(rec.evidence_refs),
            confidence=rec.confidence,
            importance=rec.importance,
            run_succeeded=run_succeeded,
            trust=trust,
            truth_status=rec.truth_status,
            expiry_policy=dict(rec.expiry_policy or {"kind": "none"}),
            links=list(rec.links),
        )
        decision = self.request_write(req)
        return decision.record if decision.record is not None else rec

    def assert_canon(self, content: str, source: str = "operator") -> MemoryRecord:
        run_id = getattr(self._trace, "run_id", "") if self._trace is not None else ""
        decision = self.request_write(MemoryWriteRequest(
            content=content,
            proposed_truth_state=MemoryTruthState.CANON,
            writer_kind="operator",
            created_by=source,
            source_run_id=run_id or "run_local",
            confidence=1.0,
            importance=1.0,
            truth_status=TruthStatus.VERIFIED,
            approved=True,
        ))
        return decision.record

    # ---- internal storage --------------------------------------------- #
    def _store(self, rec: MemoryRecord) -> MemoryRecord:
        if rec.embedding is None and rec.tier in (
                MemoryTier.SEMANTIC, MemoryTier.EPISODIC,
                MemoryTier.PROCEDURAL, MemoryTier.CANON):
            rec.embedding = self.embedder.embed(rec.content)
        if rec.tier is MemoryTier.EPHEMERAL:
            self.L1.append(rec)
        elif rec.tier is MemoryTier.EPISODIC:
            self.L2.append(rec)
        elif rec.tier is MemoryTier.SEMANTIC:
            self.L3.append(rec)
        elif rec.tier is MemoryTier.PROCEDURAL:
            self.L4.append(rec)
        elif rec.tier is MemoryTier.CANON:
            self.L5.append(rec)
        self.by_id[rec.memory_id] = rec
        return rec

    def _relocate(self, rec: MemoryRecord, target: MemoryTruthState) -> None:
        from .memory_governance import tier_for_state
        new_tier = tier_for_state(target)
        if new_tier is rec.tier:
            return
        for bucket in (self.L2, self.L3, self.L4, self.L5):
            if rec in bucket:
                bucket.remove(rec)
                break
        rec.tier = new_tier
        self._store(rec)

    def _trace_memory(self, *, action: str, verdict: str,
                     decision: MemoryWriteDecision, agent_id: str,
                     run_id: str, from_state: str, to_state: str,
                     evidence_refs: Optional[list[str]] = None,
                     source_trace_ids: Optional[list[str]] = None,
                     confidence: float = 0.0) -> None:
        if self._trace is None or not hasattr(self._trace, "append_memory_event"):
            return
        rec = MemoryGovernanceRecord.make(
            run_id=run_id or "",
            agent_id=agent_id or "",
            action=action,
            verdict=verdict,
            memory_id=decision.record.memory_id if decision.record else "",
            from_state=from_state,
            to_state=to_state,
            reason_code=decision.reason_code,
            message=decision.message,
            evidence_refs=evidence_refs or [],
            source_trace_ids=source_trace_ids or [],
            confidence=confidence,
        )
        self._trace.append_memory_event(rec)

    def active_records(self, at: Optional[float] = None) -> list[MemoryRecord]:
        return [r for r in self.by_id.values() if r.is_active(at)]

    def decay_pass(self, rate: float = 0.02) -> int:
        deprecated = 0
        for rec in self.L3:
            idle = now() - rec.last_used
            rec.decay += rate * (1.0 + idle / 3600.0)
            if rec.decay > 1.0 and rec.truth_status is not TruthStatus.DEPRECATED:
                rec.truth_status = TruthStatus.DEPRECATED
                deprecated += 1
        return deprecated

    def retrieve(self, query: str, k: int = 5) -> list[MemoryRecord]:
        q = self.embedder.embed(query)
        t = now()
        scored: list[tuple[float, MemoryRecord]] = []
        for rec in self.L3:
            if rec.truth_status is TruthStatus.DEPRECATED:
                continue
            if not rec.is_active(t):
                continue
            relevance = cosine(q, rec.embedding or [])
            recency = math.exp(-(t - rec.last_used) / 3600.0)
            score = (0.5 * relevance + 0.3 * recency + 0.2 * rec.confidence)
            score *= (0.5 + 0.5 * rec.importance)
            scored.append((score, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [r for _, r in scored[:k]]
        for r in top:
            r.last_used = t
            r.usage_count += 1
            r.decay = max(0.0, r.decay - 0.1)
        canon = [r for r in self.L5
                 if r.truth_status is not TruthStatus.DEPRECATED and r.is_active(t)]
        return canon + list(self.L1)[-3:] + top

    def assemble_context(self, query: str, k: int = 5) -> str:
        recs = self.retrieve(query, k)
        lines = []
        for r in recs:
            tag = r.tier.value.split("_")[1].upper()
            lines.append(f"[{tag}|{r.truth_status.value}|c={r.confidence:.2f}] {r.content}")
        return "\n".join(lines)

    def stats(self) -> dict:
        return {"L1": len(self.L1), "L2": len(self.L2),
                "L3": len(self.L3), "L4_procedural": len(self.L4),
                "L5_canon": len(self.L5), "rejected": len(self.rejected)}

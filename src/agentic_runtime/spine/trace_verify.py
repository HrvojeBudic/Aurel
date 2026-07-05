"""SPINE-LIVE-3 — persistent trace replay verifier (real TRACE_VERIFIED).

The kernel already hash-chains every transition and ``PersistentTraceLedger``
already streams events to ``events.jsonl``. What was missing is an *independent*
reader that trusts nothing in memory: it loads the bytes on disk and recomputes
the whole chain, so ``TRACE_VERIFIED`` becomes constructible only from a real
recomputation match.

This is the **only** place in the repo where a verified verdict may originate:

    trace_verified = (recomputed_head_hash == persisted_head_hash)

A tampered event changes its recomputed entry hash and fails closed to TAMPERED.
Verification proves integrity; it grants no authority and no permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..core_types import new_id, now

# Same-package reuse of the canonical on-disk recomputation primitives. These
# are the exact rules PersistentTraceLedger writes with, so recomputing with
# them from disk is a true independent check, not a second implementation.
from ..trace import _load_jsonl, _verify_events

TRACE_VERIFIED_EVIDENCE_VERSION = "trace_verified_evidence.v1"


class TraceVerifiedLabel(str, Enum):
    VERIFIED = "VERIFIED"        # chain recomputed from disk and matched
    TAMPERED = "TAMPERED"        # a persisted event failed recomputation
    UNAVAILABLE = "UNAVAILABLE"  # no persisted trace to verify
    ERROR = "ERROR"


def _events_path(base_dir: str | Path, run_id: str) -> Path:
    return Path(base_dir) / "runs" / run_id / "events.jsonl"


@dataclass(frozen=True)
class TraceVerifiedEvidenceRef:
    """Proof a persisted trace recomputed cleanly from disk. Never authority."""

    evidence_id: str
    contract_version: str
    run_id: str
    base_dir: str
    event_count: int
    recomputed_head_hash: str
    persisted_head_hash: str
    label: TraceVerifiedLabel
    reason: str
    produced_at: float
    authority_granted: bool = False
    permission_granted: bool = False

    @property
    def trace_verified(self) -> bool:
        return (
            self.label is TraceVerifiedLabel.VERIFIED
            and bool(self.recomputed_head_hash)
            and self.recomputed_head_hash == self.persisted_head_hash
        )

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "contract_version": self.contract_version,
            "run_id": self.run_id,
            "base_dir": self.base_dir,
            "event_count": self.event_count,
            "recomputed_head_hash": self.recomputed_head_hash,
            "persisted_head_hash": self.persisted_head_hash,
            "label": self.label.value,
            "reason": self.reason,
            "produced_at": self.produced_at,
            "trace_verified": self.trace_verified,
        }


def _evidence(
    run_id: str,
    base_dir: str | Path,
    *,
    event_count: int,
    recomputed_head_hash: str,
    persisted_head_hash: str,
    label: TraceVerifiedLabel,
    reason: str,
) -> TraceVerifiedEvidenceRef:
    return TraceVerifiedEvidenceRef(
        evidence_id=new_id("tvev"),
        contract_version=TRACE_VERIFIED_EVIDENCE_VERSION,
        run_id=run_id,
        base_dir=str(base_dir),
        event_count=event_count,
        recomputed_head_hash=recomputed_head_hash,
        persisted_head_hash=persisted_head_hash,
        label=label,
        reason=reason,
        produced_at=now(),
    )


def verify_persisted_trace(base_dir: str | Path, run_id: str) -> TraceVerifiedEvidenceRef:
    """Independently recompute a persisted trace's hash chain from disk bytes."""
    path = _events_path(base_dir, run_id)
    if not path.exists():
        return _evidence(
            run_id, base_dir,
            event_count=0,
            recomputed_head_hash="",
            persisted_head_hash="",
            label=TraceVerifiedLabel.UNAVAILABLE,
            reason=f"no persisted events at {path}",
        )
    events = _load_jsonl(path)
    if not events:
        return _evidence(
            run_id, base_dir,
            event_count=0,
            recomputed_head_hash="",
            persisted_head_hash="",
            label=TraceVerifiedLabel.UNAVAILABLE,
            reason="persisted trace is empty",
        )
    persisted_head = str(events[-1].get("entry_hash", ""))
    ok, broken, reason, recomputed_head = _verify_events(events, run_id)
    if ok:
        return _evidence(
            run_id, base_dir,
            event_count=len(events),
            recomputed_head_hash=recomputed_head,
            persisted_head_hash=persisted_head,
            label=TraceVerifiedLabel.VERIFIED,
            reason="",
        )
    return _evidence(
        run_id, base_dir,
        event_count=len(events),
        recomputed_head_hash="",
        persisted_head_hash=persisted_head,
        label=TraceVerifiedLabel.TAMPERED,
        reason=f"chain broken at index {broken}: {reason}",
    )


def replay_persisted_trace(base_dir: str | Path, run_id: str) -> list[dict]:
    """Deterministic ordered event summary read from disk. Not proof, a view."""
    events = _load_jsonl(_events_path(base_dir, run_id))
    return [
        {
            "sequence": ev.get("sequence"),
            "event_type": ev.get("event_type"),
            "entry_hash": ev.get("entry_hash"),
            "prev_entry_hash": ev.get("prev_entry_hash"),
        }
        for ev in events
    ]


__all__ = [
    "TRACE_VERIFIED_EVIDENCE_VERSION",
    "TraceVerifiedLabel",
    "TraceVerifiedEvidenceRef",
    "verify_persisted_trace",
    "replay_persisted_trace",
]

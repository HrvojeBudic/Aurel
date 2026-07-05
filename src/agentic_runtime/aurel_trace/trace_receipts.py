"""P5-TRACE-B verification receipts, verified ranges, and checkpoint/head receipts.

A receipt is **portable verification evidence** derived from a P5-TRACE-A
:class:`~agentic_runtime.aurel_trace.trace_verify.TraceHashVerificationResult`.
It records *that* a verification was produced for a trace run, scope, and chain
head — nothing more.

Doctrine anchors enforced structurally here:

* A receipt does not re-verify, and it never upgrades a FAIL result to PASS —
  ``verified`` is true only when the source status is ``PASS``.
* A receipt is **not** ledger truth, **not** semantic/business correctness,
  **not** policy/production compliance, and **not** replay/restore state.
* Only a PASS-derived receipt may carry ``TRACE_INTEGRITY_VERIFIED``; every
  other receipt is ``TRACE_BOUND``. There is no ``TRACE_VERIFIED`` label.
* Receipt hashes are deterministic canonical JSON with sorted keys; the
  nondeterministic ``created_at`` is metadata only and excluded from hash
  material (so the same verification material always yields the same hash).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)
from .trace_refs import TraceRunRef
from .trace_verify import (
    TraceHashVerificationRequest,
    TraceHashVerificationResult,
    TraceVerificationScope,
    TraceVerificationStatus,
)


def _receipt_hash(prefix: str, material: dict[str, Any]) -> str:
    return f"{prefix}-" + trace_sha(canonical_trace_json(material))[:40]


@dataclass(frozen=True)
class VerifiedTraceRange:
    """A verified segment of a trace chain.

    Evidence of *verification scope*, never replay state, state restore, or a
    workflow fork. ``end_hash`` participates in the range identity, so tampering
    with the head changes ``range_hash``.
    """

    range_id: str
    trace_run_ref: TraceRunRef
    start_index: int
    end_index: int
    end_hash: str
    checked_count: int
    range_hash: str
    start_hash: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "range_id", "end_hash", "range_hash")
        if self.start_index < 0:
            raise AurelTraceError("start_index must not be negative")
        if self.end_index < self.start_index:
            raise AurelTraceError("range requires start_index <= end_index")
        expected = self.end_index - self.start_index + 1
        if self.checked_count != expected:
            raise AurelTraceError(
                "checked_count must equal end_index - start_index + 1"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a verified range is TRACE_BOUND evidence, not an integrity label"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "range_id": self.range_id,
            "trace_run_ref": self.trace_run_ref.to_dict(),
            "start_index": self.start_index,
            "end_index": self.end_index,
            "start_hash": self.start_hash,
            "end_hash": self.end_hash,
            "checked_count": self.checked_count,
            "range_hash": self.range_hash,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceVerificationReceipt:
    """Portable evidence that a verification result was produced for a scope."""

    receipt_id: str
    verification_result_id: str
    trace_run_ref: TraceRunRef
    verification_scope: TraceVerificationScope
    verified: bool
    status: TraceVerificationStatus
    checked_count: int
    finding_count: int
    receipt_hash: str
    chain_head_hash: str | None = None
    verified_range: VerifiedTraceRange | None = None
    created_at: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(self, "receipt_id", "verification_result_id", "receipt_hash")
        if self.checked_count < 0 or self.finding_count < 0:
            raise AurelTraceError("counts must not be negative")
        pass_status = self.status is TraceVerificationStatus.PASS
        if self.verified != pass_status:
            raise AurelTraceError(
                "verified must be true iff the source status is PASS "
                "(a receipt never upgrades a non-PASS result)"
            )
        if pass_status:
            if self.truth_label is not TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
                raise AurelTraceError(
                    "a PASS-derived receipt must carry TRACE_INTEGRITY_VERIFIED"
                )
        elif self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "only a PASS-derived receipt may carry TRACE_INTEGRITY_VERIFIED"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "verification_result_id": self.verification_result_id,
            "trace_run_ref": self.trace_run_ref.to_dict(),
            "verification_scope": self.verification_scope.value,
            "verified": self.verified,
            "status": self.status.value,
            "checked_count": self.checked_count,
            "finding_count": self.finding_count,
            "chain_head_hash": self.chain_head_hash,
            "verified_range": (
                self.verified_range.to_dict() if self.verified_range else None
            ),
            "receipt_hash": self.receipt_hash,
            "created_at": self.created_at,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceCheckpointReceipt:
    """Checkpoint-ready proof that a range/head was verified.

    A checkpoint receipt is **not** a durable replay checkpoint, snapshot
    restore, or workflow fork, and it does not by itself implement incremental
    verification. Those remain UNAVAILABLE (P5-TRACE-C and later).
    """

    checkpoint_receipt_id: str
    trace_run_ref: TraceRunRef
    verified_range: VerifiedTraceRange
    chain_head_hash: str
    source_verification_receipt_id: str
    receipt_hash: str
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    # Locked boundary markers: a checkpoint receipt never claims replay/restore.
    is_replay_checkpoint: bool = False
    is_snapshot_restore: bool = False
    enables_workflow_fork: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self,
            "checkpoint_receipt_id",
            "chain_head_hash",
            "source_verification_receipt_id",
            "receipt_hash",
        )
        for field_name in (
            "is_replay_checkpoint",
            "is_snapshot_restore",
            "enables_workflow_fork",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a checkpoint receipt is not "
                    "replay/restore/fork"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a checkpoint receipt is TRACE_BOUND; the range carries the proof"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_receipt_id": self.checkpoint_receipt_id,
            "trace_run_ref": self.trace_run_ref.to_dict(),
            "verified_range": self.verified_range.to_dict(),
            "chain_head_hash": self.chain_head_hash,
            "source_verification_receipt_id": self.source_verification_receipt_id,
            "receipt_hash": self.receipt_hash,
            "is_replay_checkpoint": self.is_replay_checkpoint,
            "is_snapshot_restore": self.is_snapshot_restore,
            "enables_workflow_fork": self.enables_workflow_fork,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceChainHeadReceipt:
    """Records the verified chain head for quick integrity status."""

    chain_head_receipt_id: str
    trace_run_ref: TraceRunRef
    event_count: int
    chain_head_hash: str
    source_verification_receipt_id: str
    receipt_hash: str
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        require_nonempty(
            self,
            "chain_head_receipt_id",
            "chain_head_hash",
            "source_verification_receipt_id",
            "receipt_hash",
        )
        if self.event_count < 0:
            raise AurelTraceError("event_count must not be negative")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a chain-head receipt is TRACE_BOUND; it does not replace the ledger"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_head_receipt_id": self.chain_head_receipt_id,
            "trace_run_ref": self.trace_run_ref.to_dict(),
            "event_count": self.event_count,
            "chain_head_hash": self.chain_head_hash,
            "source_verification_receipt_id": self.source_verification_receipt_id,
            "receipt_hash": self.receipt_hash,
            "truth_label": self.truth_label.value,
        }


# --------------------------------------------------------------------------- #
#  Deterministic builders (derivation only; no re-verification, no mutation).
# --------------------------------------------------------------------------- #
def build_verified_trace_range(
    *,
    trace_run_ref: TraceRunRef,
    start_index: int,
    end_index: int,
    end_hash: str,
    checked_count: int,
    start_hash: str | None = None,
) -> VerifiedTraceRange:
    material = {
        "trace_run_id": trace_run_ref.trace_run_id,
        "start_index": start_index,
        "end_index": end_index,
        "start_hash": start_hash,
        "end_hash": end_hash,
        "checked_count": checked_count,
    }
    return VerifiedTraceRange(
        range_id=_receipt_hash("trng", material),
        trace_run_ref=trace_run_ref,
        start_index=start_index,
        end_index=end_index,
        end_hash=end_hash,
        checked_count=checked_count,
        range_hash=trace_sha(canonical_trace_json(material)),
        start_hash=start_hash,
    )


def build_trace_verification_receipt(
    result: TraceHashVerificationResult,
    request: TraceHashVerificationRequest,
    *,
    verified_range: VerifiedTraceRange | None = None,
    created_at: str | None = None,
) -> TraceVerificationReceipt:
    """Derive a portable receipt from an actual verification result.

    The receipt preserves the source ``status``/``verified``/``finding_count``
    and never upgrades a non-PASS result. ``created_at`` is metadata only and is
    excluded from the deterministic ``receipt_hash``.
    """

    verified = result.status is TraceVerificationStatus.PASS
    truth_label = (
        TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
        if verified
        else TraceTruthLabel.TRACE_BOUND
    )
    material: dict[str, Any] = {
        "verification_result_id": result.verification_result_id,
        "trace_run_id": request.trace_run_ref.trace_run_id,
        "verification_scope": request.scope.value,
        "status": result.status.value,
        "verified": verified,
        "checked_count": result.checked_count,
        "finding_count": len(result.findings),
        "chain_head_hash": result.chain_head_hash,
        "verified_range_hash": (
            verified_range.range_hash if verified_range else None
        ),
    }
    receipt_hash = trace_sha(canonical_trace_json(material))
    return TraceVerificationReceipt(
        receipt_id=_receipt_hash("trcpt", material),
        verification_result_id=result.verification_result_id,
        trace_run_ref=request.trace_run_ref,
        verification_scope=request.scope,
        verified=verified,
        status=result.status,
        checked_count=result.checked_count,
        finding_count=len(result.findings),
        receipt_hash=receipt_hash,
        chain_head_hash=result.chain_head_hash,
        verified_range=verified_range,
        created_at=created_at,
        truth_label=truth_label,
    )


def build_trace_checkpoint_receipt(
    receipt: TraceVerificationReceipt,
    verified_range: VerifiedTraceRange,
) -> TraceCheckpointReceipt:
    """Build a checkpoint receipt from a PASS receipt and a verified range.

    Only a PASS-derived receipt is checkpoint-ready — a checkpoint proves a
    range/head was verified, which requires the source verification to have
    passed. This is not replay support.
    """

    if receipt.status is not TraceVerificationStatus.PASS or not receipt.verified:
        raise AurelTraceError(
            "a checkpoint receipt requires a PASS verification receipt"
        )
    if receipt.chain_head_hash is None:
        raise AurelTraceError("a checkpoint receipt requires a chain head hash")
    material = {
        "source_verification_receipt_id": receipt.receipt_id,
        "range_hash": verified_range.range_hash,
        "chain_head_hash": receipt.chain_head_hash,
    }
    return TraceCheckpointReceipt(
        checkpoint_receipt_id=_receipt_hash("tchk", material),
        trace_run_ref=receipt.trace_run_ref,
        verified_range=verified_range,
        chain_head_hash=receipt.chain_head_hash,
        source_verification_receipt_id=receipt.receipt_id,
        receipt_hash=trace_sha(canonical_trace_json(material)),
    )


def build_trace_chain_head_receipt(
    receipt: TraceVerificationReceipt,
    *,
    event_count: int,
) -> TraceChainHeadReceipt:
    """Build a chain-head receipt for quick integrity status.

    ``receipt_hash`` folds in both ``event_count`` and the head hash, so either
    changing yields a different receipt identity.
    """

    if receipt.chain_head_hash is None:
        raise AurelTraceError("a chain-head receipt requires a chain head hash")
    material = {
        "source_verification_receipt_id": receipt.receipt_id,
        "trace_run_id": receipt.trace_run_ref.trace_run_id,
        "event_count": event_count,
        "chain_head_hash": receipt.chain_head_hash,
    }
    return TraceChainHeadReceipt(
        chain_head_receipt_id=_receipt_hash("thead", material),
        trace_run_ref=receipt.trace_run_ref,
        event_count=event_count,
        chain_head_hash=receipt.chain_head_hash,
        source_verification_receipt_id=receipt.receipt_id,
        receipt_hash=trace_sha(canonical_trace_json(material)),
    )

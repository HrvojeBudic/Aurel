"""P5-TRACE-E replay-readiness — structural prerequisites for *future* replay.

This module describes whether trace material has enough structural data for a
future replay-analysis tool. It does **not** implement replay, fork, exact-copy,
or state restore, and it never executes or mutates anything. Actual replay is
always reported UNAVAILABLE. ``READY_FOR_ANALYSIS`` means the material is
structurally analyzable later — **not** that replay is implemented.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)
from .trace_refs import TraceRunRef

REPLAY_UNAVAILABLE_REASON = (
    "actual replay / fork / exact-copy / state restore is not implemented in P5; "
    "this assessment describes analysis prerequisites only"
)

# Closed-world replay-analysis input keys.
_KNOWN_INPUT_KEYS: frozenset[str] = frozenset(
    {
        "trace_run_ref",
        "chain_head_hash",
        "event_range",
        "canonical_event_refs",
        "evidence_refs",
        "verification_decisions",
        "schema_compatibility",
    }
)


class ReplayReadinessStatus(str, Enum):
    """Status for future replay-analysis readiness. Never means replay works."""

    READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"
    PARTIAL = "PARTIAL"
    MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"
    UNSUPPORTED = "UNSUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class TraceTimeSliceRef:
    """Reference to a trace segment/range for future replay analysis.

    A range pointer only — not replay, snapshot, state restore, or fork.
    """

    time_slice_ref_id: str
    start_ref: str
    end_ref: str
    trace_run_ref: TraceRunRef | None = None
    start_index: int | None = None
    end_index: int | None = None
    chain_head_hash: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    # Locked: a time-slice ref is a range pointer, never replay/restore/fork.
    is_replay: bool = False
    is_snapshot: bool = False
    is_state_restore: bool = False
    is_fork: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "time_slice_ref_id", "start_ref", "end_ref")
        if (
            self.start_index is not None
            and self.end_index is not None
            and self.end_index < self.start_index
        ):
            raise AurelTraceError("time slice requires start_index <= end_index")
        for field_name in ("is_replay", "is_snapshot", "is_state_restore", "is_fork"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a time-slice ref is a range pointer, "
                    "not replay/snapshot/restore/fork"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a time-slice ref is a link, not a verdict")

    def to_dict(self) -> dict[str, Any]:
        return {
            "time_slice_ref_id": self.time_slice_ref_id,
            "start_ref": self.start_ref,
            "end_ref": self.end_ref,
            "trace_run_ref": self.trace_run_ref.to_dict() if self.trace_run_ref else None,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "chain_head_hash": self.chain_head_hash,
            "is_replay": self.is_replay,
            "is_snapshot": self.is_snapshot,
            "is_state_restore": self.is_state_restore,
            "is_fork": self.is_fork,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class ReplayReadinessAssessment:
    """Whether trace material has enough structural data for future replay tooling."""

    assessment_id: str
    time_slice_ref: TraceTimeSliceRef
    status: ReplayReadinessStatus
    required_inputs: tuple[str, ...]
    present_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...] = ()
    unsupported_inputs: tuple[str, ...] = ()
    unavailable_reason: str = REPLAY_UNAVAILABLE_REASON
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: an assessment describes prerequisites; it never replays/forks/restores.
    replay_implemented: bool = False
    supports_fork: bool = False
    supports_exact_copy: bool = False
    supports_state_restore: bool = False
    executes: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "assessment_id", "unavailable_reason")
        for field_name in (
            "replay_implemented",
            "supports_fork",
            "supports_exact_copy",
            "supports_state_restore",
            "executes",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — replay-readiness is not replay; "
                    "actual replay is UNAVAILABLE"
                )
        if (
            self.status is ReplayReadinessStatus.ERROR
            and not self.unavailable_reason.strip()
        ):
            raise AurelTraceError("an ERROR assessment must include a reason")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a replay-readiness assessment is a LIVE read model")

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "time_slice_ref": self.time_slice_ref.to_dict(),
            "status": self.status.value,
            "required_inputs": list(self.required_inputs),
            "present_inputs": list(self.present_inputs),
            "missing_inputs": list(self.missing_inputs),
            "unsupported_inputs": list(self.unsupported_inputs),
            "unavailable_reason": self.unavailable_reason,
            "replay_implemented": self.replay_implemented,
            "supports_fork": self.supports_fork,
            "supports_exact_copy": self.supports_exact_copy,
            "supports_state_restore": self.supports_state_restore,
            "executes": self.executes,
            "truth_label": self.truth_label.value,
        }


def build_trace_time_slice_ref(
    *,
    start_ref: str,
    end_ref: str,
    trace_run_ref: TraceRunRef | None = None,
    start_index: int | None = None,
    end_index: int | None = None,
    chain_head_hash: str | None = None,
) -> TraceTimeSliceRef:
    """Build a deterministic time-slice ref, failing closed on an inverted range."""

    if not start_ref.strip() or not end_ref.strip():
        raise AurelTraceError("start_ref and end_ref must not be empty")
    time_slice_ref_id = "tslice-" + trace_sha(
        canonical_trace_json(
            {
                "start_ref": start_ref,
                "end_ref": end_ref,
                "start_index": start_index,
                "end_index": end_index,
                "chain_head_hash": chain_head_hash,
                "trace_run_id": trace_run_ref.trace_run_id if trace_run_ref else None,
            }
        )
    )[:40]
    return TraceTimeSliceRef(
        time_slice_ref_id=time_slice_ref_id,
        start_ref=start_ref,
        end_ref=end_ref,
        trace_run_ref=trace_run_ref,
        start_index=start_index,
        end_index=end_index,
        chain_head_hash=chain_head_hash,
    )


def assess_replay_readiness(
    *,
    time_slice_ref: TraceTimeSliceRef,
    required_inputs: Sequence[str],
    present_inputs: Sequence[str],
) -> ReplayReadinessAssessment:
    """Assess structural replay-analysis readiness. Never implements replay.

    Any input key outside the closed-world set → UNSUPPORTED; all required inputs
    present → READY_FOR_ANALYSIS; none present → MISSING_REQUIRED_DATA; some
    present → PARTIAL. Actual replay is always reported UNAVAILABLE via
    ``unavailable_reason``.
    """

    required = tuple(required_inputs)
    present = tuple(present_inputs)
    unsupported = tuple(
        k for k in set(required) | set(present) if k not in _KNOWN_INPUT_KEYS
    )
    missing = tuple(k for k in required if k not in set(present))

    if unsupported:
        status = ReplayReadinessStatus.UNSUPPORTED
    elif not required:
        status = ReplayReadinessStatus.ERROR
    elif not missing:
        status = ReplayReadinessStatus.READY_FOR_ANALYSIS
    elif not any(k in set(present) for k in required):
        status = ReplayReadinessStatus.MISSING_REQUIRED_DATA
    else:
        status = ReplayReadinessStatus.PARTIAL

    assessment_id = "rra-" + trace_sha(
        canonical_trace_json(
            {
                "time_slice_ref_id": time_slice_ref.time_slice_ref_id,
                "required": list(required),
                "present": list(present),
            }
        )
    )[:40]
    reason = REPLAY_UNAVAILABLE_REASON
    if status is ReplayReadinessStatus.ERROR:
        reason = "no required inputs supplied; " + REPLAY_UNAVAILABLE_REASON
    return ReplayReadinessAssessment(
        assessment_id=assessment_id,
        time_slice_ref=time_slice_ref,
        status=status,
        required_inputs=required,
        present_inputs=present,
        missing_inputs=missing,
        unsupported_inputs=unsupported,
        unavailable_reason=reason,
    )

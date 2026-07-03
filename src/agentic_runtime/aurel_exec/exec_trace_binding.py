"""P4-EXEC-B ExecTraceBinding — trace refs without verification claims.

If the governed runtime returned a real transition record, AurelExec binds
its refs (transition id + hash-chain entry hash) so P5 AurelTrace can later
verify them. Trace-bound is not trace-verified: ``trace_verified`` is
structurally False and ``p5_required`` is structurally True in this pack.
Nothing here writes the trace — refs are captured from the runtime result
that the existing kernel already recorded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

EXEC_TRACE_BINDING_VERSION = "exec_trace_binding.v1"


@dataclass(frozen=True)
class ExecTraceBinding(_ExecCanonicalMixin):
    """Binding to real runtime trace refs. Bound is not verified."""

    trace_binding_id: str
    attempt_id: str
    trace_bound: bool
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_TRACE_BINDING_VERSION
    runtime_trace_ref: str | None = None
    trace_event_ref: str | None = None
    trace_verified: bool = False
    p5_required: bool = True
    p5_unavailable_reason: str = TRACE_VERIFICATION_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        require_nonempty(self, "trace_binding_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "attempt_id", code=AurelExecErrorCode.EMPTY_ATTEMPT_ID)
        forbid_true(self, "trace_verified")
        forbid_false(self, "p5_required")
        if self.trace_bound != (self.runtime_trace_ref is not None):
            raise AurelExecValidationError(
                "trace_bound must reflect whether a real runtime trace ref exists",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="trace_bound",
            )
        if self.trace_bound and self.truth_label is not ExecTruthLabel.TRACE_BOUND:
            raise AurelExecValidationError(
                "a bound trace binding must carry the TRACE_BOUND label",
                code=AurelExecErrorCode.FORBIDDEN_TRUTH_LABEL,
                field="truth_label",
            )
        if not self.trace_bound and self.truth_label is ExecTruthLabel.TRACE_BOUND:
            raise AurelExecValidationError(
                "TRACE_BOUND requires an actual runtime trace ref",
                code=AurelExecErrorCode.FORBIDDEN_TRUTH_LABEL,
                field="truth_label",
            )

    @property
    def binding_hash(self) -> str:
        return stable_hash(self)


def build_exec_trace_binding(*, attempt_id: str, transition: Any) -> ExecTraceBinding:
    """Build a binding from the runtime's transition record (or its absence).

    A real transition yields TRACE_BOUND with its id/entry-hash refs; no
    transition yields an honest unbound UNAVAILABLE binding. Never verifies.
    """
    runtime_trace_ref = getattr(transition, "id", None) if transition is not None else None
    trace_event_ref = (
        getattr(transition, "entry_hash", None) if transition is not None else None
    )
    trace_bound = bool(runtime_trace_ref)
    trace_binding_id = "exec-trace-bind-" + stable_hash(
        (attempt_id, runtime_trace_ref or "unbound")
    )[:16]
    return ExecTraceBinding(
        trace_binding_id=trace_binding_id,
        attempt_id=attempt_id,
        trace_bound=trace_bound,
        truth_label=(
            ExecTruthLabel.TRACE_BOUND if trace_bound else ExecTruthLabel.UNAVAILABLE
        ),
        runtime_trace_ref=runtime_trace_ref if trace_bound else None,
        trace_event_ref=trace_event_ref if trace_bound else None,
    )

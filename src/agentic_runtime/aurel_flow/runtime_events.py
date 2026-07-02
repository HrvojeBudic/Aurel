"""P3-FLOW-B runtime event stream (P3.3.x).

Local AurelFlow behavior records. A RuntimeEvent is explicitly NOT a
TraceEvent: it is not hash-chained trace, not a global Trace write, not a
Ledger write, and it can never claim TRACE_VERIFIED. Appending an event is
an immutable in-memory record of local runtime behavior — nothing more.
Streams are immutable: appends return a new stream inside the append result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import (
    FORBIDDEN_FLOW_TRUTH_LABELS,
    LEDGER_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    FlowSourceLabel,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)

RUNTIME_EVENT_CONTRACT_VERSION = "runtime_event.v1"
RUNTIME_EVENT_STREAM_VERSION = "runtime_event_stream.v1"
RUNTIME_EVENT_SNAPSHOT_VERSION = "runtime_event_stream_snapshot.v1"
RUNTIME_EVENT_READ_MODEL_VERSION = "runtime_event_read_model.v1"


class RuntimeEventKind(str, Enum):
    RUN_CREATED = "RUN_CREATED"
    SCHEDULER_DECISION_RECORDED = "SCHEDULER_DECISION_RECORDED"
    NODE_READY_RECORDED = "NODE_READY_RECORDED"
    NODE_WAITING_RECORDED = "NODE_WAITING_RECORDED"
    NODE_BLOCKED_RECORDED = "NODE_BLOCKED_RECORDED"
    PAUSE_REQUESTED = "PAUSE_REQUESTED"
    PAUSED = "PAUSED"
    OPERATOR_DECISION_RECORDED = "OPERATOR_DECISION_RECORDED"
    RESUME_REQUESTED = "RESUME_REQUESTED"
    RESUMED_INTERNAL = "RESUMED_INTERNAL"
    STOP_REQUESTED = "STOP_REQUESTED"
    STOPPED_INTERNAL = "STOPPED_INTERNAL"
    REJECT_REQUESTED = "REJECT_REQUESTED"
    REJECTED_INTERNAL = "REJECTED_INTERNAL"
    FAILURE_RECORDED = "FAILURE_RECORDED"
    RETRY_ELIGIBILITY_RECORDED = "RETRY_ELIGIBILITY_RECORDED"
    RECOVERY_PROPOSED = "RECOVERY_PROPOSED"
    ROLLBACK_CANDIDATE_RECORDED = "ROLLBACK_CANDIDATE_RECORDED"
    STATE_COMMITMENT_PROPOSED = "STATE_COMMITMENT_PROPOSED"
    STATE_COMMITMENT_REJECTED = "STATE_COMMITMENT_REJECTED"
    STATE_COMMITTED_INTERNAL = "STATE_COMMITTED_INTERNAL"
    RESPONSIBILITY_TRANSFER_RECORDED = "RESPONSIBILITY_TRANSFER_RECORDED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RuntimeEventSeverity(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class RuntimeEventSource(_CanonicalMixin):
    """Source actor/system identity for a local runtime event."""

    source_id: str
    source_kind: str = "AUREL_FLOW"
    actor_role: str = "RUNTIME"
    source_label: FlowSourceLabel = FlowSourceLabel.LOCAL_CONSTRUCTION
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR


@dataclass(frozen=True)
class RuntimeEventRelation(_CanonicalMixin):
    """Event graph relation. A relation, not a hash-chained trace."""

    parent_event_id: str = ""
    correlation_id: str = ""
    caused_by_event_id: str = ""
    affected_node_ids: tuple[str, ...] = ()
    affected_run_ids: tuple[str, ...] = ()
    relation_kind: str = "LOCAL_BEHAVIOR"
    influence_strength_label: str = "UNSPECIFIED"


EMPTY_RUNTIME_EVENT_RELATION = RuntimeEventRelation()


@dataclass(frozen=True)
class RuntimeEventPayload(_CanonicalMixin):
    """Closed-world payload envelope: string entries only, no live objects."""

    payload_version: str = "runtime_event_payload.v1"
    payload_kind: str = "NONE"
    entries: Mapping[str, str] = field(default_factory=dict)


EMPTY_RUNTIME_EVENT_PAYLOAD = RuntimeEventPayload()


@dataclass(frozen=True)
class RuntimeEventIsNotTraceBoundary(_CanonicalMixin):
    """Explicit proof object: RuntimeEvent is not TraceEvent.

    All booleans are permanently False; constructing one with a True value
    fails closed.
    """

    is_trace_event: bool = False
    is_hash_chained_trace: bool = False
    is_global_trace_write: bool = False
    is_ledger_write: bool = False
    can_claim_trace_verified: bool = False
    trace_verification_unavailable_reason: str = TRACE_VERIFICATION_UNAVAILABLE_REASON
    ledger_unavailable_reason: str = LEDGER_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        for boundary_field in (
            "is_trace_event",
            "is_hash_chained_trace",
            "is_global_trace_write",
            "is_ledger_write",
            "can_claim_trace_verified",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeEventIsNotTraceBoundary.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


RUNTIME_EVENT_IS_NOT_TRACE_BOUNDARY = RuntimeEventIsNotTraceBoundary()


@dataclass(frozen=True)
class RuntimeEvent(_CanonicalMixin):
    """Local AurelFlow runtime behavior event. Not TraceEvent, not Ledger."""

    event_id: str
    sequence: int
    contract_version: str
    event_kind: RuntimeEventKind
    severity: RuntimeEventSeverity
    source: RuntimeEventSource
    target_run_id: str
    target_node_id: str
    relation: RuntimeEventRelation
    payload: RuntimeEventPayload
    local_state_before_ref: str
    local_state_after_ref: str
    feedback_signal: str
    predictability_label: str
    credit_unit_hint: str
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str]
    trace_verified: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("trace_verified", "ledger_written", "global_trace_written"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeEvent.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )
        if self.truth_label in FORBIDDEN_FLOW_TRUTH_LABELS:
            raise AurelFlowValidationError(
                f"RuntimeEvent may not claim truth label {self.truth_label.value!r}",
                code=AurelFlowErrorCode.FORBIDDEN_TRUTH_LABEL,
                field="truth_label",
            )


@dataclass(frozen=True)
class RuntimeEventStream(_CanonicalMixin):
    """Immutable local event stream for one workflow run."""

    stream_id: str
    run_id: str
    contract_version: str
    events: tuple[RuntimeEvent, ...]
    truth_label: FlowTruthLabel
    boundary: RuntimeEventIsNotTraceBoundary


@dataclass(frozen=True)
class RuntimeEventAppendResult(_CanonicalMixin):
    """Append result. Rejected appends leave the stream unchanged."""

    accepted: bool
    reason: str
    reject_code: str
    event: RuntimeEvent | None
    stream: RuntimeEventStream
    ledger_written: bool = False
    global_trace_written: bool = False


@dataclass(frozen=True)
class RuntimeEventStreamSnapshot(_CanonicalMixin):
    """Deterministic snapshot of a local event stream. Order-preserving."""

    snapshot_version: str
    stream_id: str
    run_id: str
    event_count: int
    event_ids: tuple[str, ...]
    kind_counts: Mapping[str, int]
    severity_counts: Mapping[str, int]
    truth_label: FlowTruthLabel
    boundary: RuntimeEventIsNotTraceBoundary
    snapshot_hash: str


@dataclass(frozen=True)
class RuntimeEventRelationView(_CanonicalMixin):
    event_id: str
    parent_event_id: str
    correlation_id: str
    caused_by_event_id: str
    affected_node_ids: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeEventReadModel(_CanonicalMixin):
    """Operator-inspectable local event read model. Not a Trace projection."""

    read_model_version: str
    stream_id: str
    run_id: str
    event_count: int
    events: tuple[RuntimeEvent, ...]
    relations: tuple[RuntimeEventRelationView, ...]
    kind_counts: Mapping[str, int]
    truth_label: FlowTruthLabel
    boundary: RuntimeEventIsNotTraceBoundary
    trace_verified: bool
    ledger_written: bool
    global_trace_written: bool
    read_model_hash: str


def create_runtime_event_stream(
    run_id: str,
    *,
    stream_key: str = "stream-0001",
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
) -> RuntimeEventStream:
    if not run_id:
        raise AurelFlowValidationError(
            "run_id must be non-empty",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="run_id",
        )
    stream_id = "rtstream-" + stable_hash({"run_id": run_id, "stream_key": stream_key})[:16]
    return RuntimeEventStream(
        stream_id=stream_id,
        run_id=run_id,
        contract_version=RUNTIME_EVENT_STREAM_VERSION,
        events=(),
        truth_label=truth_label,
        boundary=RUNTIME_EVENT_IS_NOT_TRACE_BOUNDARY,
    )


def _rejected(
    stream: RuntimeEventStream, reason: str, code: AurelFlowErrorCode
) -> RuntimeEventAppendResult:
    return RuntimeEventAppendResult(
        accepted=False,
        reason=reason,
        reject_code=code.value,
        event=None,
        stream=stream,
    )


def append_runtime_event(
    stream: RuntimeEventStream,
    *,
    event_kind: RuntimeEventKind,
    source: RuntimeEventSource,
    severity: RuntimeEventSeverity = RuntimeEventSeverity.INFO,
    target_node_id: str = "",
    target_run_id: str = "",
    relation: RuntimeEventRelation = EMPTY_RUNTIME_EVENT_RELATION,
    payload: RuntimeEventPayload = EMPTY_RUNTIME_EVENT_PAYLOAD,
    local_state_before_ref: str = "",
    local_state_after_ref: str = "",
    feedback_signal: str = "",
    predictability_label: str = "UNSPECIFIED",
    credit_unit_hint: str = "",
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
    metadata: Mapping[str, str] | None = None,
) -> RuntimeEventAppendResult:
    """Append a local behavior event. Fail-closed via rejected result.

    Appending is a local in-memory record — not a Ledger write and not a
    global Trace write. Closed-world: parent/caused-by references must point
    at events already in this stream.
    """

    if target_run_id and target_run_id != stream.run_id:
        return _rejected(
            stream,
            f"event targets run {target_run_id!r} but stream records run {stream.run_id!r}",
            AurelFlowErrorCode.RUN_MISMATCH,
        )
    if truth_label in FORBIDDEN_FLOW_TRUTH_LABELS:
        return _rejected(
            stream,
            f"runtime events may not claim truth label {truth_label.value!r}",
            AurelFlowErrorCode.FORBIDDEN_TRUTH_LABEL,
        )
    known_event_ids = {event.event_id for event in stream.events}
    for ref_field, ref in (
        ("parent_event_id", relation.parent_event_id),
        ("caused_by_event_id", relation.caused_by_event_id),
    ):
        if ref and ref not in known_event_ids:
            return _rejected(
                stream,
                f"relation.{ref_field} references unknown event {ref!r}",
                AurelFlowErrorCode.UNKNOWN_EVENT_REF,
            )

    sequence = len(stream.events)
    event_id = "rtev-" + stable_hash(
        {
            "stream_id": stream.stream_id,
            "sequence": sequence,
            "event_kind": event_kind,
            "target_node_id": target_node_id,
        }
    )[:16]
    event = RuntimeEvent(
        event_id=event_id,
        sequence=sequence,
        contract_version=RUNTIME_EVENT_CONTRACT_VERSION,
        event_kind=event_kind,
        severity=severity,
        source=source,
        target_run_id=stream.run_id,
        target_node_id=target_node_id,
        relation=relation,
        payload=payload,
        local_state_before_ref=local_state_before_ref,
        local_state_after_ref=local_state_after_ref,
        feedback_signal=feedback_signal,
        predictability_label=predictability_label,
        credit_unit_hint=credit_unit_hint,
        truth_label=truth_label,
        metadata=dict(metadata or {}),
    )
    new_stream = RuntimeEventStream(
        stream_id=stream.stream_id,
        run_id=stream.run_id,
        contract_version=stream.contract_version,
        events=stream.events + (event,),
        truth_label=stream.truth_label,
        boundary=stream.boundary,
    )
    return RuntimeEventAppendResult(
        accepted=True,
        reason="event recorded locally; not a Ledger write, not a global Trace write",
        reject_code="",
        event=event,
        stream=new_stream,
    )


def snapshot_runtime_event_stream(stream: RuntimeEventStream) -> RuntimeEventStreamSnapshot:
    kind_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for event in stream.events:
        kind_counts[event.event_kind.value] = kind_counts.get(event.event_kind.value, 0) + 1
        severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
    payload = {
        "snapshot_version": RUNTIME_EVENT_SNAPSHOT_VERSION,
        "stream_id": stream.stream_id,
        "run_id": stream.run_id,
        "event_ids": tuple(event.event_id for event in stream.events),
    }
    return RuntimeEventStreamSnapshot(
        snapshot_version=RUNTIME_EVENT_SNAPSHOT_VERSION,
        stream_id=stream.stream_id,
        run_id=stream.run_id,
        event_count=len(stream.events),
        event_ids=tuple(event.event_id for event in stream.events),
        kind_counts=kind_counts,
        severity_counts=severity_counts,
        truth_label=stream.truth_label,
        boundary=stream.boundary,
        snapshot_hash=stable_hash(payload),
    )


def build_runtime_event_read_model(stream: RuntimeEventStream) -> RuntimeEventReadModel:
    snapshot = snapshot_runtime_event_stream(stream)
    relations = tuple(
        RuntimeEventRelationView(
            event_id=event.event_id,
            parent_event_id=event.relation.parent_event_id,
            correlation_id=event.relation.correlation_id,
            caused_by_event_id=event.relation.caused_by_event_id,
            affected_node_ids=event.relation.affected_node_ids,
        )
        for event in stream.events
    )
    payload = {
        "read_model_version": RUNTIME_EVENT_READ_MODEL_VERSION,
        "snapshot_hash": snapshot.snapshot_hash,
    }
    return RuntimeEventReadModel(
        read_model_version=RUNTIME_EVENT_READ_MODEL_VERSION,
        stream_id=stream.stream_id,
        run_id=stream.run_id,
        event_count=len(stream.events),
        events=stream.events,
        relations=relations,
        kind_counts=snapshot.kind_counts,
        truth_label=stream.truth_label,
        boundary=stream.boundary,
        trace_verified=False,
        ledger_written=False,
        global_trace_written=False,
        read_model_hash=stable_hash(payload),
    )

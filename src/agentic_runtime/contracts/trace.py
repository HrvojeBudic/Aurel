"""Canonical AurelTraceLog contracts.

P1.5.10X establishes AurelTraceLog as the only canonical append-only
hash-chained event source of truth. Ledger, evidence, runtime state,
evaluation, memory, shell and reports are projections over this log.

This module is contract-first. It does not execute tools, run workflows,
schedule activities, call models, or implement the full ledger/memory stack.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


GENESIS_EVENT_HASH = "GENESIS"


class TraceEventType(str, Enum):
    RUNTIME = "runtime"
    EVALUATION = "evaluation"
    EVIDENCE = "evidence"
    MEMORY = "memory"
    LEDGER = "ledger"
    SHELL = "shell"
    REPORT = "report"
    POLICY = "policy"
    VERIFIER = "verifier"
    WORKFLOW = "workflow"
    STUB_EXECUTION_COMPLETED = "stub_execution_completed"
    UNKNOWN = "unknown"


class TraceEventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TraceEventStatus(str, Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FrozenJsonObject:
    items: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class FrozenJsonArray:
    items: tuple[Any, ...]


@dataclass(frozen=True)
class TraceEventRef:
    trace_id: str
    event_id: str
    sequence_no: int
    event_hash: str


@dataclass(frozen=True)
class TraceBindingRef:
    source_event_ref: TraceEventRef
    source_event_hash: str
    source_trace_id: str
    projection_type: str | None = None
    projection_id: str | None = None

    def __post_init__(self) -> None:
        if self.source_event_hash != self.source_event_ref.event_hash:
            raise ValueError("source_event_hash must match source_event_ref.event_hash")
        if self.source_trace_id != self.source_event_ref.trace_id:
            raise ValueError("source_trace_id must match source_event_ref.trace_id")


@dataclass(frozen=True)
class TraceIntegrityReport:
    trace_id: str
    is_valid: bool
    checked_events: int
    broken_at_event_id: str | None = None
    expected_previous_hash: str | None = None
    actual_previous_hash: str | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class TraceEvent:
    event_id: str
    trace_id: str
    sequence_no: int
    event_type: TraceEventType
    timestamp: str
    actor_type: str
    actor_id: str
    payload_json: Any
    payload_hash: str
    previous_event_hash: str
    causal_parent_event_ids: tuple[str, ...]
    causal_parent_hashes: tuple[str, ...]
    event_hash: str
    workflow_run_id: str | None = None
    activity_id: str | None = None
    session_id: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    state_before_hash: str | None = None
    state_after_hash: str | None = None
    evidence_refs: tuple[str, ...] = ()
    object_refs: tuple[str, ...] = ()
    policy_context_ref: str | None = None
    context_packet_ref: str | None = None
    verifier_result_ref: str | None = None
    severity: TraceEventSeverity = TraceEventSeverity.INFO
    status: TraceEventStatus = TraceEventStatus.CREATED


def canonical_json_dumps(value: Any) -> str:
    """Stable JSON serialization used for canonical hashing."""
    return json.dumps(
        _to_jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_json(value: Any) -> str:
    return hash_text(canonical_json_dumps(value))


def compute_payload_hash(payload_json: Any) -> str:
    _assert_json_serializable(payload_json)
    return hash_json(payload_json)


def compute_event_hash(
    *,
    trace_id: str,
    sequence_no: int,
    event_type: TraceEventType | str,
    timestamp: str,
    actor_type: str,
    actor_id: str,
    payload_hash: str,
    previous_event_hash: str,
    causal_parent_hashes: tuple[str, ...] = (),
    input_hash: str | None = None,
    output_hash: str | None = None,
    state_before_hash: str | None = None,
    state_after_hash: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    object_refs: tuple[str, ...] = (),
    policy_context_ref: str | None = None,
    context_packet_ref: str | None = None,
    verifier_result_ref: str | None = None,
    severity: TraceEventSeverity | str = TraceEventSeverity.INFO,
    status: TraceEventStatus | str = TraceEventStatus.CREATED,
) -> str:
    content = {
        "trace_id": trace_id,
        "sequence_no": sequence_no,
        "event_type": _enum_value(event_type, TraceEventType),
        "timestamp": timestamp,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "payload_hash": payload_hash,
        "previous_event_hash": previous_event_hash,
        "causal_parent_hashes": list(causal_parent_hashes),
        "input_hash": input_hash,
        "output_hash": output_hash,
        "state_before_hash": state_before_hash,
        "state_after_hash": state_after_hash,
        "evidence_refs": list(evidence_refs),
        "object_refs": list(object_refs),
        "policy_context_ref": policy_context_ref,
        "context_packet_ref": context_packet_ref,
        "verifier_result_ref": verifier_result_ref,
        "severity": _enum_value(severity, TraceEventSeverity),
        "status": _enum_value(status, TraceEventStatus),
    }
    return hash_json(content)


class AurelTraceLog:
    """Minimal in-memory append-only canonical trace log."""

    def __init__(
        self,
        trace_id: str | None = None,
        events: tuple[TraceEvent, ...] = (),
    ) -> None:
        self._trace_id = trace_id or f"trace_{uuid.uuid4().hex[:12]}"
        self._events: list[TraceEvent] = list(events)

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def head(self) -> str:
        return self._events[-1].event_hash if self._events else GENESIS_EVENT_HASH

    def append(
        self,
        *,
        event_type: TraceEventType | str,
        actor_type: str,
        actor_id: str,
        payload_json: Any,
        timestamp: str | None = None,
        causal_parent_event_ids: tuple[str, ...] = (),
        causal_parent_hashes: tuple[str, ...] = (),
        workflow_run_id: str | None = None,
        activity_id: str | None = None,
        session_id: str | None = None,
        input_hash: str | None = None,
        output_hash: str | None = None,
        state_before_hash: str | None = None,
        state_after_hash: str | None = None,
        evidence_refs: tuple[str, ...] = (),
        object_refs: tuple[str, ...] = (),
        policy_context_ref: str | None = None,
        context_packet_ref: str | None = None,
        verifier_result_ref: str | None = None,
        severity: TraceEventSeverity | str = TraceEventSeverity.INFO,
        status: TraceEventStatus | str = TraceEventStatus.CREATED,
    ) -> TraceEvent:
        sequence_no = len(self._events)
        previous_hash = self.head if self._events else GENESIS_EVENT_HASH
        parsed_event_type = _coerce_enum(event_type, TraceEventType)
        parsed_severity = _coerce_enum(severity, TraceEventSeverity)
        parsed_status = _coerce_enum(status, TraceEventStatus)
        event_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        payload_hash = compute_payload_hash(payload_json)
        frozen_payload = _freeze_json(payload_json)
        event_hash = compute_event_hash(
            trace_id=self._trace_id,
            sequence_no=sequence_no,
            event_type=parsed_event_type,
            timestamp=event_timestamp,
            actor_type=actor_type,
            actor_id=actor_id,
            payload_hash=payload_hash,
            previous_event_hash=previous_hash,
            causal_parent_hashes=causal_parent_hashes,
            input_hash=input_hash,
            output_hash=output_hash,
            state_before_hash=state_before_hash,
            state_after_hash=state_after_hash,
            evidence_refs=evidence_refs,
            object_refs=object_refs,
            policy_context_ref=policy_context_ref,
            context_packet_ref=context_packet_ref,
            verifier_result_ref=verifier_result_ref,
            severity=parsed_severity,
            status=parsed_status,
        )
        event = TraceEvent(
            event_id=f"{self._trace_id}:event:{sequence_no}",
            trace_id=self._trace_id,
            sequence_no=sequence_no,
            event_type=parsed_event_type,
            timestamp=event_timestamp,
            actor_type=actor_type,
            actor_id=actor_id,
            payload_json=frozen_payload,
            payload_hash=payload_hash,
            previous_event_hash=previous_hash,
            causal_parent_event_ids=causal_parent_event_ids,
            causal_parent_hashes=causal_parent_hashes,
            event_hash=event_hash,
            workflow_run_id=workflow_run_id,
            activity_id=activity_id,
            session_id=session_id,
            input_hash=input_hash,
            output_hash=output_hash,
            state_before_hash=state_before_hash,
            state_after_hash=state_after_hash,
            evidence_refs=evidence_refs,
            object_refs=object_refs,
            policy_context_ref=policy_context_ref,
            context_packet_ref=context_packet_ref,
            verifier_result_ref=verifier_result_ref,
            severity=parsed_severity,
            status=parsed_status,
        )
        self._events.append(event)
        return event

    def get_event(self, event_id: str) -> TraceEvent:
        for event in self._events:
            if event.event_id == event_id:
                return event
        raise KeyError(event_id)

    def get_trace(self, trace_id: str) -> list[TraceEvent]:
        return [event for event in self._events if event.trace_id == trace_id]

    def verify_chain(self, trace_id: str) -> TraceIntegrityReport:
        events = self.get_trace(trace_id)
        expected_previous = GENESIS_EVENT_HASH
        for index, event in enumerate(events):
            if event.sequence_no != index:
                return TraceIntegrityReport(
                    trace_id=trace_id,
                    is_valid=False,
                    checked_events=index + 1,
                    broken_at_event_id=event.event_id,
                    errors=(f"sequence_no mismatch at event {event.event_id}",),
                )
            if event.previous_event_hash != expected_previous:
                return TraceIntegrityReport(
                    trace_id=trace_id,
                    is_valid=False,
                    checked_events=index + 1,
                    broken_at_event_id=event.event_id,
                    expected_previous_hash=expected_previous,
                    actual_previous_hash=event.previous_event_hash,
                    errors=("previous_event_hash mismatch",),
                )
            expected_payload_hash = compute_payload_hash(event.payload_json)
            if event.payload_hash != expected_payload_hash:
                return TraceIntegrityReport(
                    trace_id=trace_id,
                    is_valid=False,
                    checked_events=index + 1,
                    broken_at_event_id=event.event_id,
                    errors=("payload_hash mismatch",),
                )
            expected_event_hash = _recompute_event_hash(event)
            if event.event_hash != expected_event_hash:
                return TraceIntegrityReport(
                    trace_id=trace_id,
                    is_valid=False,
                    checked_events=index + 1,
                    broken_at_event_id=event.event_id,
                    errors=("event_hash mismatch",),
                )
            expected_previous = event.event_hash
        return TraceIntegrityReport(
            trace_id=trace_id,
            is_valid=True,
            checked_events=len(events),
        )

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self):
        return iter(tuple(self._events))


def trace_event_ref(event: TraceEvent) -> TraceEventRef:
    return TraceEventRef(
        trace_id=event.trace_id,
        event_id=event.event_id,
        sequence_no=event.sequence_no,
        event_hash=event.event_hash,
    )


def trace_event_to_dict(event: TraceEvent) -> dict[str, Any]:
    data = asdict(event)
    data["event_type"] = event.event_type.value
    data["severity"] = event.severity.value
    data["status"] = event.status.value
    data["payload_json"] = _to_jsonable(event.payload_json)
    data["causal_parent_event_ids"] = list(event.causal_parent_event_ids)
    data["causal_parent_hashes"] = list(event.causal_parent_hashes)
    data["evidence_refs"] = list(event.evidence_refs)
    data["object_refs"] = list(event.object_refs)
    return data


def trace_integrity_report_to_dict(report: TraceIntegrityReport) -> dict[str, Any]:
    return {
        "trace_id": report.trace_id,
        "is_valid": report.is_valid,
        "checked_events": report.checked_events,
        "broken_at_event_id": report.broken_at_event_id,
        "expected_previous_hash": report.expected_previous_hash,
        "actual_previous_hash": report.actual_previous_hash,
        "errors": list(report.errors),
        "warnings": list(report.warnings),
    }


def _recompute_event_hash(event: TraceEvent) -> str:
    return compute_event_hash(
        trace_id=event.trace_id,
        sequence_no=event.sequence_no,
        event_type=event.event_type,
        timestamp=event.timestamp,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        payload_hash=event.payload_hash,
        previous_event_hash=event.previous_event_hash,
        causal_parent_hashes=event.causal_parent_hashes,
        input_hash=event.input_hash,
        output_hash=event.output_hash,
        state_before_hash=event.state_before_hash,
        state_after_hash=event.state_after_hash,
        evidence_refs=event.evidence_refs,
        object_refs=event.object_refs,
        policy_context_ref=event.policy_context_ref,
        context_packet_ref=event.context_packet_ref,
        verifier_result_ref=event.verifier_result_ref,
        severity=event.severity,
        status=event.status,
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, FrozenJsonObject):
        return {key: _to_jsonable(item) for key, item in value.items}
    if isinstance(value, FrozenJsonArray):
        return [_to_jsonable(item) for item in value.items]
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if hasattr(value, "to_dict"):
        return _to_jsonable(value.to_dict())
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _assert_json_serializable(value: Any) -> None:
    canonical_json_dumps(value)


def _coerce_enum(value: Any, enum_cls: type[Enum]) -> Any:
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


def _enum_value(value: Any, enum_cls: type[Enum]) -> str:
    return _coerce_enum(value, enum_cls).value


def _freeze_json(value: Any) -> Any:
    if isinstance(value, FrozenJsonObject | FrozenJsonArray):
        return value
    if isinstance(value, dict):
        return FrozenJsonObject(
            tuple((str(key), _freeze_json(item)) for key, item in sorted(value.items()))
        )
    if isinstance(value, list | tuple):
        return FrozenJsonArray(tuple(_freeze_json(item) for item in value))
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _freeze_json(asdict(value))
    if hasattr(value, "to_dict"):
        return _freeze_json(value.to_dict())
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, FrozenJsonObject):
        return {key: _to_jsonable(item) for key, item in value.items}
    if isinstance(value, FrozenJsonArray):
        return [_to_jsonable(item) for item in value.items]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if hasattr(value, "to_dict"):
        return _to_jsonable(value.to_dict())
    return value

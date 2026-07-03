"""P4-EXEC-C ExecutionMessage / LocalExecutionMessageLog — local causality.

Execution messages record local execution causality for operator visibility
before any distributed bus exists. A message is a local read-model log
entry, not a network event; the log is an immutable local append/list/filter
structure, not a service bus — it has no subscribers, no pub/sub, no
routing, no transport, and no async dispatch. Those claims are structurally
unconstructible.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXECUTION_MESSAGE_VERSION = "execution_message.v1"
LOCAL_EXECUTION_MESSAGE_LOG_VERSION = "local_execution_message_log.v1"
NO_TRANSPORT_BUS_PROOF_VERSION = "no_transport_bus_proof.v1"

TRANSPORT_BUS_UNAVAILABLE_REASON = (
    "no network event bus, service bus, pub/sub, or transport layer exists; "
    "execution messages are local read-model log entries only — local "
    "causality comes before any distributed bus"
)


class ExecutionMessageKind(str, Enum):
    JOB_QUEUED = "JOB_QUEUED"
    QUEUE_CLAIMED = "QUEUE_CLAIMED"
    WORKER_CLAIMED = "WORKER_CLAIMED"
    SESSION_OPENED = "SESSION_OPENED"
    ATTEMPT_READY = "ATTEMPT_READY"
    CHECKPOINT_BOUND = "CHECKPOINT_BOUND"
    ATTEMPT_SUBMITTED = "ATTEMPT_SUBMITTED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"
    ROLLBACK_REF_CREATED = "ROLLBACK_REF_CREATED"
    WORKER_RELEASED = "WORKER_RELEASED"
    ERROR_RECORDED = "ERROR_RECORDED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ExecutionMessage(_ExecCanonicalMixin):
    """One local execution causality message. Not a network event."""

    message_id: str
    message_kind: ExecutionMessageKind
    payload_summary: str
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_MESSAGE_VERSION
    exec_job_id: str | None = None
    session_id: str | None = None
    attempt_id: str | None = None
    queue_entry_id: str | None = None
    worker_slot_id: str | None = None
    causality_ref: str | None = None
    created_at_tick: int | None = None
    is_network_event: bool = False
    routes: bool = False
    executes: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "message_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "payload_summary", code=AurelExecErrorCode.EMPTY_FIELD)
        require_allowed_truth_label(self)
        forbid_true(self, "is_network_event", "routes", "executes")

    @property
    def message_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class LocalExecutionMessageLog(_ExecCanonicalMixin):
    """Immutable local message log: append returns a new log. Not a bus."""

    messages: tuple[ExecutionMessage, ...] = ()
    contract_version: str = LOCAL_EXECUTION_MESSAGE_LOG_VERSION
    is_transport_bus: bool = False
    publishes_network_events: bool = False
    pubsub_available: bool = False
    has_subscribers: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "is_transport_bus",
            "publishes_network_events",
            "pubsub_available",
            "has_subscribers",
        )


def build_execution_message(
    kind: ExecutionMessageKind,
    *,
    payload_summary: str,
    truth_label: ExecTruthLabel,
    exec_job_id: str | None = None,
    session_id: str | None = None,
    attempt_id: str | None = None,
    queue_entry_id: str | None = None,
    worker_slot_id: str | None = None,
    causality_ref: str | None = None,
    created_at_tick: int | None = None,
    sequence: int = 0,
) -> ExecutionMessage:
    """Build a local message with a deterministic id. Building routes nothing."""
    message_id = "exec-msg-" + stable_hash(
        (kind.value, exec_job_id, attempt_id, queue_entry_id, created_at_tick, sequence)
    )[:16]
    return ExecutionMessage(
        message_id=message_id,
        message_kind=kind,
        payload_summary=payload_summary,
        truth_label=truth_label,
        exec_job_id=exec_job_id,
        session_id=session_id,
        attempt_id=attempt_id,
        queue_entry_id=queue_entry_id,
        worker_slot_id=worker_slot_id,
        causality_ref=causality_ref,
        created_at_tick=created_at_tick,
    )


def append_execution_message(
    log: LocalExecutionMessageLog, message: ExecutionMessage
) -> LocalExecutionMessageLog:
    """Append locally: returns a new log. No publish, no subscribers."""
    return dataclasses.replace(log, messages=log.messages + (message,))


def list_execution_messages(log: LocalExecutionMessageLog) -> tuple[ExecutionMessage, ...]:
    return log.messages


def filter_execution_messages_by_job(
    log: LocalExecutionMessageLog, exec_job_id: str
) -> tuple[ExecutionMessage, ...]:
    return tuple(m for m in log.messages if m.exec_job_id == exec_job_id)


def filter_execution_messages_by_session(
    log: LocalExecutionMessageLog, session_id: str
) -> tuple[ExecutionMessage, ...]:
    return tuple(m for m in log.messages if m.session_id == session_id)


def filter_execution_messages_by_attempt(
    log: LocalExecutionMessageLog, attempt_id: str
) -> tuple[ExecutionMessage, ...]:
    return tuple(m for m in log.messages if m.attempt_id == attempt_id)


def filter_execution_messages_by_queue_entry(
    log: LocalExecutionMessageLog, queue_entry_id: str
) -> tuple[ExecutionMessage, ...]:
    return tuple(m for m in log.messages if m.queue_entry_id == queue_entry_id)


@dataclass(frozen=True)
class NoTransportBusProof(_ExecCanonicalMixin):
    """Evidence that no transport/event/service bus exists. Local log only."""

    reason: str
    contract_version: str = NO_TRANSPORT_BUS_PROOF_VERSION
    transport_bus_available: bool = False
    network_publish_available: bool = False
    pubsub_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "transport_bus_available",
            "network_publish_available",
            "pubsub_available",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_transport_bus_proof() -> NoTransportBusProof:
    return NoTransportBusProof(reason=TRANSPORT_BUS_UNAVAILABLE_REASON)

"""Projection boundary contracts over canonical AurelTraceLog events."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .trace import TraceEvent, TraceEventRef, trace_event_ref


class ProjectionKind(str, Enum):
    LEDGER = "ledger"
    RUNTIME = "runtime"
    EVALUATION = "evaluation"
    MEMORY = "memory"
    SHELL = "shell"
    REPORT = "report"
    EVIDENCE = "evidence"


@dataclass(frozen=True)
class ProjectionRecord:
    projection_id: str
    projection_kind: ProjectionKind
    source_event_ref: TraceEventRef
    source_event_hash: str
    is_canonical: bool = False

    def __post_init__(self) -> None:
        if self.is_canonical:
            raise ValueError("ProjectionRecord cannot claim canonical status")
        if self.source_event_hash != self.source_event_ref.event_hash:
            raise ValueError("source_event_hash must match source_event_ref.event_hash")


def validate_projection_record(record: ProjectionRecord) -> tuple[str, ...]:
    issues: list[str] = []
    if not record.projection_id or not record.projection_id.strip():
        issues.append("projection_id must not be empty")
    if record.is_canonical:
        issues.append("projection records cannot claim canonical status")
    if record.source_event_hash != record.source_event_ref.event_hash:
        issues.append("source_event_hash must match source_event_ref.event_hash")
    if not record.source_event_ref.trace_id or not record.source_event_ref.event_id:
        issues.append("projection records require a TraceEventRef")
    return tuple(issues)


def projection_record_to_dict(record: ProjectionRecord) -> dict[str, Any]:
    data = asdict(record)
    data["projection_kind"] = record.projection_kind.value
    data["source_event_ref"] = asdict(record.source_event_ref)
    return data


def projection_from_event(
    *,
    projection_id: str,
    projection_kind: ProjectionKind,
    event: TraceEvent,
) -> ProjectionRecord:
    ref = trace_event_ref(event)
    return ProjectionRecord(
        projection_id=projection_id,
        projection_kind=projection_kind,
        source_event_ref=ref,
        source_event_hash=ref.event_hash,
        is_canonical=False,
    )

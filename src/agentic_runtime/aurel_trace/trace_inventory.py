"""P5-TRACE-A existing trace inventory.

Catalogs the *existing* trace implementation so P5 adapts repo truth rather
than an imagined structure. The inventory is deterministic and serializable and
performs no side effects: importing the record/ledger classes to read their
names is pure, and no ledger is constructed, appended to, or mutated.

Two existing trace systems are catalogued:

1. ``agentic_runtime.trace`` — the operational hash-chained ledger backends
   (``InMemoryTraceLedger`` / ``PersistentTraceLedger``) over the concrete
   record types in ``agentic_runtime.core_types``. **This is the P5-A
   normalization target.**
2. ``agentic_runtime.contracts.trace`` — the contract-first canonical
   ``AurelTraceLog`` event form with its own ``TraceEventRef`` /
   ``TraceBindingRef`` / ``TraceIntegrityReport``. Catalogued as related repo
   truth; deferred as a P5-A normalization target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .. import trace as ledger_module
from ..core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    MemoryGovernanceRecord,
    PlanningFailureRecord,
    PraxisEventRecord,
    RuntimeStatusTransitionRecord,
    SandboxViolationRecord,
    StateTransitionRecord,
    ToolContractViolationRecord,
)
from .trace_hash import AurelTraceError, TraceTruthLabel, require_nonempty

EXISTING_TRACE_INVENTORY_ID = "existing-trace-inventory.p5-trace-a.v1"

# The supported normalization targets are exactly the operational ledger's
# hash-chained record types (agentic_runtime.trace.TraceEntry union members).
_SUPPORTED_RECORD_TYPES: tuple[str, ...] = (
    StateTransitionRecord.__name__,
    PlanningFailureRecord.__name__,
    RuntimeStatusTransitionRecord.__name__,
    BudgetDecisionRecord.__name__,
    MemoryGovernanceRecord.__name__,
    ToolContractViolationRecord.__name__,
    ApprovalReceiptRecord.__name__,
    PraxisEventRecord.__name__,
    SandboxViolationRecord.__name__,
)

# Related canonical event form, deferred as a P5-A normalization target.
_UNSUPPORTED_RECORD_TYPES: tuple[str, ...] = (
    "contracts.trace.TraceEvent (AurelTraceLog canonical event form)",
    "contracts.trace.AurelTraceLog (separate canonical hash scheme)",
)

_LEDGER_TYPES: tuple[str, ...] = (
    ledger_module.InMemoryTraceLedger.__name__,
    ledger_module.PersistentTraceLedger.__name__,
)

_PROJECTION_TYPES: tuple[str, ...] = (
    "contracts.projections.ProjectionRecord",
    "contracts.projections.ProjectionKind",
    "contracts.projections.projection_from_event",
)


@dataclass(frozen=True)
class ExistingTraceInventory:
    """Deterministic, serializable catalog of the existing trace system."""

    inventory_id: str
    trace_modules: tuple[str, ...]
    record_types: tuple[str, ...]
    ledger_types: tuple[str, ...]
    projection_types: tuple[str, ...]
    known_hash_fields: tuple[str, ...]
    known_previous_hash_fields: tuple[str, ...]
    known_payload_fields: tuple[str, ...]
    known_record_id_fields: tuple[str, ...]
    supported_record_types: tuple[str, ...]
    unsupported_record_types: tuple[str, ...]
    compatibility_notes: tuple[str, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "inventory_id")
        if not self.record_types:
            raise AurelTraceError("inventory must list at least one record type")
        if not self.ledger_types:
            raise AurelTraceError("inventory must list at least one ledger type")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("an inventory is a LIVE catalog, not a verified chain")

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "trace_modules": list(self.trace_modules),
            "record_types": list(self.record_types),
            "ledger_types": list(self.ledger_types),
            "projection_types": list(self.projection_types),
            "known_hash_fields": list(self.known_hash_fields),
            "known_previous_hash_fields": list(self.known_previous_hash_fields),
            "known_payload_fields": list(self.known_payload_fields),
            "known_record_id_fields": list(self.known_record_id_fields),
            "supported_record_types": list(self.supported_record_types),
            "unsupported_record_types": list(self.unsupported_record_types),
            "compatibility_notes": list(self.compatibility_notes),
            "truth_label": self.truth_label.value,
        }


def build_existing_trace_inventory() -> ExistingTraceInventory:
    """Build the deterministic inventory of the existing trace system."""

    return ExistingTraceInventory(
        inventory_id=EXISTING_TRACE_INVENTORY_ID,
        trace_modules=(
            "agentic_runtime.trace",
            "agentic_runtime.core_types",
            "agentic_runtime.contracts.trace",
            "agentic_runtime.contracts.projections",
        ),
        record_types=_SUPPORTED_RECORD_TYPES,
        ledger_types=_LEDGER_TYPES,
        projection_types=_PROJECTION_TYPES,
        known_hash_fields=("entry_hash",),
        known_previous_hash_fields=("prev_entry_hash",),
        known_payload_fields=("payload_hash() method (canonical JSON)",),
        known_record_id_fields=("id",),
        supported_record_types=_SUPPORTED_RECORD_TYPES,
        unsupported_record_types=_UNSUPPORTED_RECORD_TYPES,
        compatibility_notes=(
            "InMemoryTraceLedger chains entry_hash = sha(prev_entry_hash, "
            "payload_hash()) from GENESIS; P5-A reuses this exact scheme.",
            "PersistentTraceLedger hashes a canonical JSON event body; its "
            "record objects still expose entry_hash/prev_entry_hash/payload_hash().",
            "contracts.trace.AurelTraceLog is a separate canonical event form "
            "with its own compute_event_hash scheme and its own TraceEventRef / "
            "TraceBindingRef; P5-A reports the naming overlap and does not "
            "replace it — those refs live in contracts.trace, the P5 refs live "
            "in aurel_trace.",
            "P5-A adds no ledger and no second source of truth.",
        ),
    )

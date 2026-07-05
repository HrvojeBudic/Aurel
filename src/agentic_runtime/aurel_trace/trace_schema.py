"""P5-TRACE-B closed-world trace schema registry and compatibility decisions.

The registry describes *which* trace record/envelope schemas P5 can verify and
canonicalize. It is deliberately **closed-world**: an unknown record type never
silently passes, and there is no silent fallback to a default schema. It is a
schema *contract layer*, not a migration engine — the upcaster contract declares
*that* a migration would be required without ever rewriting historical records.

Doctrine anchors enforced structurally here:

* Unknown schema fails closed (``UNKNOWN`` decision), unsupported schema carries
  an explicit ``reason``.
* An upcaster is ``DECLARED_ONLY`` or ``UNAVAILABLE`` by default; it cannot claim
  to rewrite or migrate records.
* Descriptors/decisions/registry are ``LIVE`` contracts — they never carry
  ``TRACE_INTEGRITY_VERIFIED`` (describing compatibility is not verifying a chain).
"""

from __future__ import annotations

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
from .trace_inventory import ExistingTraceInventory, build_existing_trace_inventory

TRACE_SCHEMA_REGISTRY_ID = "trace-schema-registry.p5-trace-b.v1"
DEFAULT_TRACE_SCHEMA_VERSION = "core_types.ledger_record.v1"
AUREL_TRACE_LOG_SCHEMA_VERSION = "contracts.trace.aurel_trace_log.v1"


class TraceSchemaStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    DEPRECATED = "DEPRECATED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class TraceSchemaCompatibility(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    COMPATIBLE_WITH_WARNINGS = "COMPATIBLE_WITH_WARNINGS"
    REQUIRES_UPCASTER = "REQUIRES_UPCASTER"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class TraceUpcasterStatus(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    DECLARED_ONLY = "DECLARED_ONLY"
    SUPPORTED = "SUPPORTED"


def _stable_id(prefix: str, material: dict[str, Any]) -> str:
    return f"{prefix}-" + trace_sha(canonical_trace_json(material))[:40]


@dataclass(frozen=True)
class TraceEventUpcasterContract:
    """Declares an upcasting boundary — never a migration implementation.

    For P5-TRACE-B the status is ``DECLARED_ONLY`` or ``UNAVAILABLE``: the
    contract states that moving ``from_schema`` to ``to_schema`` *would* require
    an upcaster, but no historical record is ever rewritten here.
    """

    upcaster_id: str
    from_schema: str
    to_schema: str
    status: TraceUpcasterStatus = TraceUpcasterStatus.DECLARED_ONLY
    reason: str = ""
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: this contract never rewrites or migrates records.
    rewrites_records: bool = False
    migrates_records: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "upcaster_id", "from_schema", "to_schema")
        if self.status is TraceUpcasterStatus.SUPPORTED:
            raise AurelTraceError(
                "P5-TRACE-B declares upcasters only; SUPPORTED upcasting is not "
                "available in this pack"
            )
        for field_name in ("rewrites_records", "migrates_records"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the registry is not a migration engine"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("an upcaster contract is a LIVE declaration")

    def to_dict(self) -> dict[str, Any]:
        return {
            "upcaster_id": self.upcaster_id,
            "from_schema": self.from_schema,
            "to_schema": self.to_schema,
            "status": self.status.value,
            "reason": self.reason,
            "rewrites_records": self.rewrites_records,
            "migrates_records": self.migrates_records,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceSchemaDescriptor:
    """Describes one supported/unsupported trace or canonical-envelope schema."""

    schema_id: str
    schema_name: str
    schema_version: str
    record_type: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    hash_fields: tuple[str, ...] = ()
    previous_hash_fields: tuple[str, ...] = ()
    payload_fields: tuple[str, ...] = ()
    status: TraceSchemaStatus = TraceSchemaStatus.SUPPORTED
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(
            self, "schema_id", "schema_name", "schema_version", "record_type"
        )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a schema descriptor is a LIVE contract, not a verified chain"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "record_type": self.record_type,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "hash_fields": list(self.hash_fields),
            "previous_hash_fields": list(self.previous_hash_fields),
            "payload_fields": list(self.payload_fields),
            "status": self.status.value,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceSchemaCompatibilityDecision:
    """Whether an envelope/record schema can be verified/canonicalized.

    Every non-``COMPATIBLE`` decision must explain itself; unknown record types
    never silently pass.
    """

    decision_id: str
    record_type: str
    schema_version: str | None
    decision: TraceSchemaCompatibility
    reason: str
    required_upcaster: TraceEventUpcasterContract | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "decision_id", "record_type")
        if self.decision is not TraceSchemaCompatibility.COMPATIBLE:
            if not self.reason.strip():
                raise AurelTraceError(
                    "a non-COMPATIBLE decision must carry a non-empty reason"
                )
        if (
            self.decision is TraceSchemaCompatibility.REQUIRES_UPCASTER
            and self.required_upcaster is None
        ):
            raise AurelTraceError(
                "a REQUIRES_UPCASTER decision must reference an upcaster contract"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError(
                "a compatibility decision is a LIVE contract, not a verified chain"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "record_type": self.record_type,
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason,
            "required_upcaster": (
                self.required_upcaster.to_dict() if self.required_upcaster else None
            ),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceSchemaRegistry:
    """Closed-world registry of trace schema descriptors supported by P5."""

    registry_id: str
    schema_descriptors: tuple[TraceSchemaDescriptor, ...]
    default_schema_version: str
    supported_record_types: tuple[str, ...]
    unsupported_record_types: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a closed-world registry never silently falls back and never migrates.
    closed_world: bool = True
    silent_fallback_used: bool = False
    is_migration_engine: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "registry_id", "default_schema_version")
        if not self.schema_descriptors:
            raise AurelTraceError("registry must list at least one schema descriptor")
        if self.closed_world is not True:
            raise AurelTraceError("this registry is closed-world by construction")
        for field_name in ("silent_fallback_used", "is_migration_engine"):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — no silent fallback, no migration engine"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a registry is a LIVE contract, not a verified chain")

    def _descriptor_for(self, record_type: str) -> TraceSchemaDescriptor | None:
        for descriptor in self.schema_descriptors:
            if descriptor.record_type == record_type:
                return descriptor
        return None

    def decide(
        self,
        record_type: str,
        schema_version: str | None = None,
    ) -> TraceSchemaCompatibilityDecision:
        """Decide compatibility for a record type / schema version, fail-closed.

        * Known SUPPORTED descriptor -> COMPATIBLE (or COMPATIBLE_WITH_WARNINGS
          when the version does not match the descriptor's version).
        * Known PARTIAL descriptor -> COMPATIBLE_WITH_WARNINGS.
        * Known DEPRECATED descriptor -> REQUIRES_UPCASTER (declared-only upcaster).
        * Known UNSUPPORTED descriptor -> UNSUPPORTED with reason.
        * Unknown record type -> UNKNOWN with reason (never a silent default).
        """

        descriptor = self._descriptor_for(record_type)
        material = {"record_type": record_type, "schema_version": schema_version}
        decision_id = _stable_id("tdec", material)
        if descriptor is None:
            return TraceSchemaCompatibilityDecision(
                decision_id=decision_id,
                record_type=record_type,
                schema_version=schema_version,
                decision=TraceSchemaCompatibility.UNKNOWN,
                reason=(
                    f"record type {record_type!r} is not in the closed-world "
                    "registry; no silent fallback to the default schema is allowed"
                ),
            )
        if descriptor.status is TraceSchemaStatus.UNSUPPORTED:
            return TraceSchemaCompatibilityDecision(
                decision_id=decision_id,
                record_type=record_type,
                schema_version=schema_version,
                decision=TraceSchemaCompatibility.UNSUPPORTED,
                reason=(
                    f"record type {record_type!r} is catalogued but unsupported "
                    "for P5 verification (separate canonical scheme, deferred)"
                ),
            )
        if descriptor.status is TraceSchemaStatus.DEPRECATED:
            upcaster = TraceEventUpcasterContract(
                upcaster_id=_stable_id("tup", material),
                from_schema=descriptor.schema_version,
                to_schema=self.default_schema_version,
                status=TraceUpcasterStatus.DECLARED_ONLY,
                reason=(
                    f"schema {descriptor.schema_version!r} is deprecated; an "
                    "upcaster is declared but not implemented in P5-TRACE-B"
                ),
            )
            return TraceSchemaCompatibilityDecision(
                decision_id=decision_id,
                record_type=record_type,
                schema_version=schema_version,
                decision=TraceSchemaCompatibility.REQUIRES_UPCASTER,
                reason=f"schema {descriptor.schema_version!r} requires an upcaster",
                required_upcaster=upcaster,
            )
        version_mismatch = (
            schema_version is not None
            and schema_version != descriptor.schema_version
        )
        if descriptor.status is TraceSchemaStatus.PARTIAL or version_mismatch:
            reason = (
                f"schema {schema_version!r} does not match descriptor version "
                f"{descriptor.schema_version!r}"
                if version_mismatch
                else f"record type {record_type!r} has partial P5 support"
            )
            return TraceSchemaCompatibilityDecision(
                decision_id=decision_id,
                record_type=record_type,
                schema_version=schema_version,
                decision=TraceSchemaCompatibility.COMPATIBLE_WITH_WARNINGS,
                reason=reason,
            )
        return TraceSchemaCompatibilityDecision(
            decision_id=decision_id,
            record_type=record_type,
            schema_version=schema_version,
            decision=TraceSchemaCompatibility.COMPATIBLE,
            reason="",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "schema_descriptors": [d.to_dict() for d in self.schema_descriptors],
            "default_schema_version": self.default_schema_version,
            "supported_record_types": list(self.supported_record_types),
            "unsupported_record_types": list(self.unsupported_record_types),
            "closed_world": self.closed_world,
            "silent_fallback_used": self.silent_fallback_used,
            "is_migration_engine": self.is_migration_engine,
            "truth_label": self.truth_label.value,
        }


# The operational ledger's hash-chain field shape (shared with P5-A verification).
_LEDGER_HASH_FIELDS: tuple[str, ...] = ("entry_hash",)
_LEDGER_PREVIOUS_HASH_FIELDS: tuple[str, ...] = ("prev_entry_hash",)
_LEDGER_PAYLOAD_FIELDS: tuple[str, ...] = ("payload_hash()",)
_LEDGER_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "entry_hash",
    "prev_entry_hash",
    "payload_hash()",
)


def build_default_trace_schema_registry(
    inventory: ExistingTraceInventory | None = None,
) -> TraceSchemaRegistry:
    """Seed the closed-world registry from the P5-A existing trace inventory.

    Each of the nine operational ledger record types becomes a SUPPORTED
    descriptor; the deferred ``contracts.trace.AurelTraceLog`` canonical event
    form becomes an UNSUPPORTED descriptor — matching the inventory so the two
    layers cannot drift apart.
    """

    inv = inventory or build_existing_trace_inventory()
    descriptors: list[TraceSchemaDescriptor] = []
    for record_type in inv.supported_record_types:
        descriptors.append(
            TraceSchemaDescriptor(
                schema_id=_stable_id("tsch", {"record_type": record_type}),
                schema_name=record_type,
                schema_version=DEFAULT_TRACE_SCHEMA_VERSION,
                record_type=record_type,
                required_fields=_LEDGER_REQUIRED_FIELDS,
                hash_fields=_LEDGER_HASH_FIELDS,
                previous_hash_fields=_LEDGER_PREVIOUS_HASH_FIELDS,
                payload_fields=_LEDGER_PAYLOAD_FIELDS,
                status=TraceSchemaStatus.SUPPORTED,
            )
        )
    for record_type in inv.unsupported_record_types:
        descriptors.append(
            TraceSchemaDescriptor(
                schema_id=_stable_id("tsch", {"record_type": record_type}),
                schema_name=record_type,
                schema_version=AUREL_TRACE_LOG_SCHEMA_VERSION,
                record_type=record_type,
                required_fields=(),
                status=TraceSchemaStatus.UNSUPPORTED,
            )
        )
    return TraceSchemaRegistry(
        registry_id=TRACE_SCHEMA_REGISTRY_ID,
        schema_descriptors=tuple(descriptors),
        default_schema_version=DEFAULT_TRACE_SCHEMA_VERSION,
        supported_record_types=tuple(inv.supported_record_types),
        unsupported_record_types=tuple(inv.unsupported_record_types),
    )

"""P5-TRACE-A canonical hash material and shared trace-verification primitives.

This module is the lowest layer of the ``aurel_trace`` package. It reuses the
existing runtime hashing primitives (:func:`agentic_runtime.core_types.sha` and
:func:`agentic_runtime.core_types.canonical_json`) and the operational ledger
genesis (:data:`agentic_runtime.trace.GENESIS`) so that P5 verification is
computed with the *same* hash truth the existing ledger already writes — there
is no second hash algorithm and no second source of truth.

Doctrine anchors enforced structurally here:

* Hash material is stable canonical JSON with sorted keys — never Python
  ``repr`` of an object.
* No nondeterministic timestamp is folded into hash material.
* ``TraceTruthLabel`` deliberately has **no** ``TRACE_VERIFIED`` member. Hash
  integrity is not semantic correctness; the strongest label this domain can
  mint is ``TRACE_INTEGRITY_VERIFIED``.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from ..core_types import canonical_json as _canonical_json
from ..core_types import sha as _sha
from ..trace import GENESIS as LEDGER_GENESIS

AUREL_TRACE_CONTRACT_VERSION = "aurel_trace.v1"
CANONICAL_ENVELOPE_SCHEMA_VERSION = "canonical_trace_event_envelope.v1"

# The operational in-memory ledger chains records as
# ``entry_hash = sha(prev_entry_hash, payload_hash())`` starting from GENESIS.
# P5 verification reuses exactly this, so the genesis marker is shared.
GENESIS_ENTRY_HASH = LEDGER_GENESIS


class AurelTraceError(ValueError):
    """Raised when a P5 trace contract is constructed in an impossible state."""


class TraceTruthLabel(str, Enum):
    """Closed-world truth vocabulary for the P5 trace foundation.

    There is intentionally no ``TRACE_VERIFIED`` member: P5-TRACE-A verifies
    hash-chain integrity, not semantic/business correctness.
    """

    LIVE = "LIVE"
    TRACE_BOUND = "TRACE_BOUND"
    TRACE_INTEGRITY_VERIFIED = "TRACE_INTEGRITY_VERIFIED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class TraceIntegrityStatus(str, Enum):
    """Per-object integrity posture. Bound is not verified."""

    NOT_VERIFIED = "NOT_VERIFIED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"
    BROKEN = "BROKEN"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT = "INSUFFICIENT"


def canonical_trace_json(value: Any) -> str:
    """Stable canonical JSON (sorted keys) shared with the operational ledger."""

    return _canonical_json(_to_plain(value))


def trace_sha(*parts: str) -> str:
    """SHA-256 over the given parts, identical to the ledger's ``sha``."""

    return _sha(*parts)


def _to_plain(value: Any) -> Any:
    """Convert dataclasses/enums/tuples into plain JSON-able structures.

    Kept deliberately explicit so hash material never depends on object
    ``repr`` or dataclass field ordering surprises.
    """

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {str(k): _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class TraceHashMaterial:
    """The deterministic material from which a canonical event hash is derived.

    Every field is a stable string/int captured from an existing ledger
    record. No timestamp is included — hash material must be reproducible.
    """

    trace_run_id: str
    source_record_type: str
    event_kind: str
    sequence_index: int
    payload_hash: str
    entry_hash: str
    previous_entry_hash: str
    schema_version: str = CANONICAL_ENVELOPE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_run_id": self.trace_run_id,
            "source_record_type": self.source_record_type,
            "event_kind": self.event_kind,
            "sequence_index": self.sequence_index,
            "payload_hash": self.payload_hash,
            "entry_hash": self.entry_hash,
            "previous_entry_hash": self.previous_entry_hash,
            "schema_version": self.schema_version,
        }

    @property
    def material_hash(self) -> str:
        return trace_sha(canonical_trace_json(self.to_dict()))


def canonical_payload_hash(record: Any) -> str:
    """Return the record's own canonical payload hash.

    Supported ledger records expose a deterministic ``payload_hash()`` method
    built from stable canonical JSON. Records without it are unsupported and
    must not be silently accepted.
    """

    payload_hash = getattr(record, "payload_hash", None)
    if not callable(payload_hash):
        raise AurelTraceError(
            f"record type {type(record).__name__} exposes no payload_hash()"
        )
    return str(payload_hash())


def recompute_entry_hash(previous_entry_hash: str, payload_hash: str) -> str:
    """Recompute a ledger entry hash exactly as the in-memory ledger does."""

    return trace_sha(previous_entry_hash, payload_hash)


def canonical_event_hash_material(
    *,
    trace_run_id: str,
    source_record_type: str,
    event_kind: str,
    sequence_index: int,
    payload_hash: str,
    entry_hash: str,
    previous_entry_hash: str,
    schema_version: str = CANONICAL_ENVELOPE_SCHEMA_VERSION,
) -> TraceHashMaterial:
    return TraceHashMaterial(
        trace_run_id=trace_run_id,
        source_record_type=source_record_type,
        event_kind=event_kind,
        sequence_index=sequence_index,
        payload_hash=payload_hash,
        entry_hash=entry_hash,
        previous_entry_hash=previous_entry_hash,
        schema_version=schema_version,
    )


def canonical_event_id_from_hash_material(material: TraceHashMaterial) -> str:
    """Derive a stable canonical event id from deterministic hash material."""

    return "cev-" + material.material_hash[:40]


# --------------------------------------------------------------------------- #
#  Small structural validation helpers (mirroring the aurel_exec idiom).
# --------------------------------------------------------------------------- #
def require_nonempty(obj: Any, *field_names: str) -> None:
    for field_name in field_names:
        value = getattr(obj, field_name)
        if not isinstance(value, str) or not value.strip():
            raise AurelTraceError(f"{field_name} must be a non-empty string")


def forbid_true(obj: Any, *field_names: str) -> None:
    for field_name in field_names:
        if getattr(obj, field_name) is True:
            raise AurelTraceError(f"{field_name} must not be True in this pack")


def forbid_false(obj: Any, *field_names: str) -> None:
    for field_name in field_names:
        if getattr(obj, field_name) is False:
            raise AurelTraceError(f"{field_name} must not be False in this pack")

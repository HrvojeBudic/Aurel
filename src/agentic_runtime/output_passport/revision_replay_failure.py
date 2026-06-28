"""Output Passport revision, replay seed, and failure handling (P1.9-C).

P1.9.23 rejection/revision history, P1.9.24 replay seed, P1.9.25 failure/unavailable.

Architectural law:
  - Revision history is append-only, not destructive overwrite.
  - Replay seed is not replay execution.
  - Failure handling is not repair.
  - UNAVAILABLE requires reason.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    OutputPassportErrorCode,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportValidationError,
    stable_hash,
    to_canonical_json,
)

OUTPUT_PASSPORT_REVISION_TASK_ID = "P1.9.23"
OUTPUT_PASSPORT_REPLAY_SEED_TASK_ID = "P1.9.24"
OUTPUT_PASSPORT_FAILURE_TASK_ID = "P1.9.25"
OUTPUT_PASSPORT_REVISION_HISTORY_VERSION = (
    "output_passport_revision_history.v1"
)
OUTPUT_PASSPORT_REVISION_ENTRY_VERSION = "output_passport_revision_entry.v1"
OUTPUT_PASSPORT_REJECTION_RECORD_VERSION = (
    "output_passport_rejection_record.v1"
)
OUTPUT_PASSPORT_REPLAY_SEED_VERSION = "output_passport_replay_seed.v1"
OUTPUT_PASSPORT_FAILURE_STATE_VERSION = "output_passport_failure_state.v1"
OUTPUT_PASSPORT_UNAVAILABLE_STATE_VERSION = (
    "output_passport_unavailable_state.v1"
)


class OutputPassportFailureReason(str, Enum):
    """Closed-world failure reason taxonomy."""

    BUILD_ERROR = "build_error"
    SERIALIZATION_ERROR = "serialization_error"
    VALIDATION_ERROR = "validation_error"
    MISSING_PREREQUISITE = "missing_prerequisite"
    CONTRACT_VIOLATION = "contract_violation"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ReplaySeedUnavailableReason(str, Enum):
    """Why replay seed cannot support replay execution."""

    REPLAY_ENGINE_UNAVAILABLE = "replay_engine_unavailable"
    MISSING_INPUT_REFS = "missing_input_refs"
    MISSING_HASH_REFS = "missing_hash_refs"
    RUNTIME_UNAVAILABLE = "runtime_unavailable"
    NOT_IN_SCOPE_P1_9_C = "not_in_scope_p1_9_c"


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


@dataclass(frozen=True)
class OutputPassportRejectionRecord(_CanonicalMixin):
    """Rejection record — does not delete provenance."""

    schema_version: str
    rejection_id: str
    passport_ref: str
    rejection_reason: str
    operator_review_ref: str | None
    rejected_at_ref: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    rejection_record_hash: str


@dataclass(frozen=True)
class OutputPassportRevisionEntry(_CanonicalMixin):
    """Single revision entry — preserves previous refs."""

    schema_version: str
    revision_id: str
    previous_passport_ref: str
    revised_passport_ref: str
    revision_reason: str
    operator_review_ref: str | None
    append_only: bool
    destructive_overwrite_forbidden: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    revision_entry_hash: str


@dataclass(frozen=True)
class OutputPassportRevisionHistory(_CanonicalMixin):
    """P1.9.23 append-style revision history."""

    schema_version: str
    checkpoint_id: str
    passport_ref: str
    entries: tuple[OutputPassportRevisionEntry, ...]
    rejections: tuple[OutputPassportRejectionRecord, ...]
    append_only_contract: bool
    destructive_overwrite_forbidden: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    revision_history_hash: str


@dataclass(frozen=True)
class ReplaySeedDeterminismBoundary(_CanonicalMixin):
    """Determinism boundary for replay seed — not execution guarantee."""

    seed_only: bool
    replay_executed: bool
    output_verified: bool
    model_called: bool
    tool_called: bool
    runtime_called: bool
    invariants: tuple[str, ...]


@dataclass(frozen=True)
class OutputPassportReplaySeed(_CanonicalMixin):
    """P1.9.24 replay seed — metadata only, no replay execution."""

    schema_version: str
    checkpoint_id: str
    input_refs: tuple[str, ...]
    model_refs: tuple[str, ...]
    tool_refs: tuple[str, ...]
    hash_refs: tuple[str, ...]
    determinism_notes: str
    replay_unavailable_reason: ReplaySeedUnavailableReason | None
    determinism_boundary: ReplaySeedDeterminismBoundary
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    replay_seed_hash: str


@dataclass(frozen=True)
class OutputPassportFailureState(_CanonicalMixin):
    """P1.9.25 failure state — disclosure only, not repair."""

    schema_version: str
    checkpoint_id: str
    failure_kind: OutputPassportFailureReason
    failure_reason: str
    recoverability_hint: str | None
    operator_next_action: str | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    failure_state_hash: str


@dataclass(frozen=True)
class OutputPassportUnavailableState(_CanonicalMixin):
    """P1.9.25 unavailable state — explicit missing capability."""

    schema_version: str
    checkpoint_id: str
    unavailable_kind: str
    unavailable_reason: str
    recoverability_hint: str | None
    operator_next_action: str | None
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    unavailable_state_hash: str


REPLAY_SEED_INVARIANTS: tuple[str, ...] = (
    "replay_seed_only_not_execution",
    "seed_does_not_verify_output",
    "no_model_tool_runtime_call",
)


def build_output_passport_revision_history(
    *,
    checkpoint_id: str = "P1.9.23",
    passport_ref: str = "dev-passport-001",
    previous_passport_ref: str = "dev-passport-001-v0",
    revised_passport_ref: str = "dev-passport-001-v1",
    revision_reason: str = "operator_requested_revision",
    rejection_reason: str | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportRevisionHistory:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    revision_payload = {
        "schema_version": OUTPUT_PASSPORT_REVISION_ENTRY_VERSION,
        "revision_id": "rev-001",
        "previous_passport_ref": previous_passport_ref,
        "revised_passport_ref": revised_passport_ref,
        "revision_reason": revision_reason,
        "operator_review_ref": "dev-operator-review-ref-001",
        "append_only": True,
        "destructive_overwrite_forbidden": True,
        "truth_label": OutputPassportTruthLabel.REVISION_HISTORY_ONLY,
        "source_label": source_label,
    }
    revision_entry = OutputPassportRevisionEntry(
        **revision_payload,
        revision_entry_hash=_hash_payload(revision_payload),
    )

    rejections: tuple[OutputPassportRejectionRecord, ...] = ()
    if rejection_reason:
        rejection_payload = {
            "schema_version": OUTPUT_PASSPORT_REJECTION_RECORD_VERSION,
            "rejection_id": "rej-001",
            "passport_ref": previous_passport_ref,
            "rejection_reason": rejection_reason,
            "operator_review_ref": "dev-operator-review-ref-001",
            "rejected_at_ref": "dev-timestamp-ref-001",
            "truth_label": OutputPassportTruthLabel.REVISION_HISTORY_ONLY,
            "source_label": source_label,
        }
        rejections = (
            OutputPassportRejectionRecord(
                **rejection_payload,
                rejection_record_hash=_hash_payload(rejection_payload),
            ),
        )

    history_payload = {
        "schema_version": OUTPUT_PASSPORT_REVISION_HISTORY_VERSION,
        "checkpoint_id": checkpoint_id,
        "passport_ref": passport_ref,
        "entries": (revision_entry,),
        "rejections": rejections,
        "append_only_contract": True,
        "destructive_overwrite_forbidden": True,
        "truth_label": OutputPassportTruthLabel.REVISION_HISTORY_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportRevisionHistory(
        **history_payload,
        revision_history_hash=_hash_payload(history_payload),
    )


def build_output_passport_replay_seed(
    *,
    checkpoint_id: str = "P1.9.24",
    input_refs: Sequence[str] = ("dev-input-ref-001",),
    model_refs: Sequence[str] = ("dev-model-ref-001",),
    tool_refs: Sequence[str] = (),
    hash_refs: Sequence[str] = ("dev-hash-ref-001",),
    replay_unavailable_reason: ReplaySeedUnavailableReason | str | None = (
        ReplaySeedUnavailableReason.REPLAY_ENGINE_UNAVAILABLE
    ),
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportReplaySeed:
    if isinstance(replay_unavailable_reason, str):
        replay_unavailable_reason = ReplaySeedUnavailableReason(
            replay_unavailable_reason
        )
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    if not input_refs or not hash_refs:
        replay_unavailable_reason = ReplaySeedUnavailableReason.MISSING_INPUT_REFS

    side_effects = _all_false_side_effects()
    determinism_boundary = ReplaySeedDeterminismBoundary(
        seed_only=True,
        replay_executed=False,
        output_verified=False,
        model_called=False,
        tool_called=False,
        runtime_called=False,
        invariants=REPLAY_SEED_INVARIANTS,
    )
    seed_payload = {
        "schema_version": OUTPUT_PASSPORT_REPLAY_SEED_VERSION,
        "checkpoint_id": checkpoint_id,
        "input_refs": tuple(input_refs),
        "model_refs": tuple(model_refs),
        "tool_refs": tuple(tool_refs),
        "hash_refs": tuple(hash_refs),
        "determinism_notes": (
            "replay_seed_metadata_only; execution deferred to future runtime"
        ),
        "replay_unavailable_reason": replay_unavailable_reason,
        "determinism_boundary": determinism_boundary,
        "truth_label": OutputPassportTruthLabel.REPLAY_SEED_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportReplaySeed(
        **seed_payload,
        replay_seed_hash=_hash_payload(seed_payload),
    )


def build_output_passport_failure_unavailable_handling(
    *,
    checkpoint_id: str = "P1.9.25",
    failure_kind: OutputPassportFailureReason | str = (
        OutputPassportFailureReason.CONTRACT_VIOLATION
    ),
    failure_reason: str = "passport_contract_validation_failed",
    unavailable_kind: str = "trace_verification",
    unavailable_reason: str = "trace_verification_unavailable_in_p1_9_c",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> tuple[OutputPassportFailureState, OutputPassportUnavailableState]:
    if isinstance(failure_kind, str):
        failure_kind = OutputPassportFailureReason(failure_kind)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    if not unavailable_reason.strip():
        raise OutputPassportValidationError(
            "unavailable_reason is required and cannot be empty",
            code=OutputPassportErrorCode.VALIDATION_ERROR,
            field="unavailable_reason",
        )

    side_effects = _all_false_side_effects()
    failure_payload = {
        "schema_version": OUTPUT_PASSPORT_FAILURE_STATE_VERSION,
        "checkpoint_id": checkpoint_id,
        "failure_kind": failure_kind,
        "failure_reason": failure_reason,
        "recoverability_hint": "review_contract_and_retry_build",
        "operator_next_action": "inspect_failure_disclosure",
        "truth_label": OutputPassportTruthLabel.FAILURE_DISCLOSURE,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    failure = OutputPassportFailureState(
        **failure_payload,
        failure_state_hash=_hash_payload(failure_payload),
    )

    unavailable_payload = {
        "schema_version": OUTPUT_PASSPORT_UNAVAILABLE_STATE_VERSION,
        "checkpoint_id": checkpoint_id,
        "unavailable_kind": unavailable_kind,
        "unavailable_reason": unavailable_reason,
        "recoverability_hint": "deferred_to_p1_9_d_integration_tail",
        "operator_next_action": "acknowledge_unavailable_capability",
        "truth_label": OutputPassportTruthLabel.UNAVAILABLE,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    unavailable = OutputPassportUnavailableState(
        **unavailable_payload,
        unavailable_state_hash=_hash_payload(unavailable_payload),
    )
    return failure, unavailable


def serialize_replay_seed(seed: OutputPassportReplaySeed) -> str:
    return to_canonical_json(seed)

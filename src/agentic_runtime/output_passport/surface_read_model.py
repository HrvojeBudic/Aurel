"""Output Passport surface read model (P1.9-C / P1.9.21).

Passive read models for Aurel CRO / HQ / CORP / HUB / IDE surfaces without
UI implementation, shell routes, or P2 work.

Architectural law:
  - Surface read model is not surface implementation.
  - READ_MODEL_ONLY is not UI.
  - SURFACE_UI_UNAVAILABLE requires reason.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from .foundation import (
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    stable_hash,
    to_canonical_json,
)

OUTPUT_PASSPORT_SURFACE_READ_MODEL_TASK_ID = "P1.9.21"
OUTPUT_PASSPORT_SURFACE_READ_MODEL_VERSION = (
    "output_passport_surface_read_model.v1"
)
OUTPUT_PASSPORT_SURFACE_SUMMARY_VERSION = (
    "output_passport_surface_summary.v1"
)


class SurfacePassportConsumerKind(str, Enum):
    """Major v1 surface consumer kinds — read model only."""

    AUREL_CRO = "Aurel CRO"
    HQ = "HQ"
    CORP = "CORP"
    HUB = "HUB"
    IDE = "IDE"


SURFACE_CONSUMER_KINDS: tuple[SurfacePassportConsumerKind, ...] = (
    SurfacePassportConsumerKind.AUREL_CRO,
    SurfacePassportConsumerKind.HQ,
    SurfacePassportConsumerKind.CORP,
    SurfacePassportConsumerKind.HUB,
    SurfacePassportConsumerKind.IDE,
)


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
class SurfacePassportReadinessSummary(_CanonicalMixin):
    """Readiness summary for a surface consumer — not UI availability."""

    consumer_kind: SurfacePassportConsumerKind
    read_model_available: bool
    ui_available: bool
    shell_route_created: bool
    cli_binding_available: bool
    unavailable_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class SurfaceOutputPassportReadModel(_CanonicalMixin):
    """P1.9.21 surface passport read model — passive projection only."""

    schema_version: str
    checkpoint_id: str
    consumer_kind: SurfacePassportConsumerKind
    passport_ref: str
    readiness_summary: SurfacePassportReadinessSummary
    display_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    surface_read_model_hash: str


SURFACE_READ_MODEL_INVARIANTS: tuple[str, ...] = (
    "read_model_only_not_ui",
    "no_shell_route_created",
    "no_global_topbar",
    "surface_ui_unavailable",
    "cli_binding_unavailable_p1_9_28",
)


def _build_surface_summary(
    consumer_kind: SurfacePassportConsumerKind,
    *,
    source_label: OutputPassportSourceLabel,
) -> SurfacePassportReadinessSummary:
    return SurfacePassportReadinessSummary(
        consumer_kind=consumer_kind,
        read_model_available=True,
        ui_available=False,
        shell_route_created=False,
        cli_binding_available=False,
        unavailable_reason=(
            "surface_ui_and_cli_binding_unavailable_in_p1_9_c_read_model_only"
        ),
        truth_label=OutputPassportTruthLabel.READ_MODEL_ONLY,
        source_label=source_label,
    )


def build_surface_passport_read_model(
    *,
    consumer_kind: SurfacePassportConsumerKind | str = (
        SurfacePassportConsumerKind.AUREL_CRO
    ),
    checkpoint_id: str = "P1.9.21",
    passport_ref: str = "dev-passport-001",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> SurfaceOutputPassportReadModel:
    if isinstance(consumer_kind, str):
        consumer_kind = SurfacePassportConsumerKind(consumer_kind)
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    readiness = _build_surface_summary(consumer_kind, source_label=source_label)
    display_fields = (
        "identity",
        "attribution",
        "disclosure",
        "truth_boundary",
        "verification_state",
    )
    payload = {
        "schema_version": OUTPUT_PASSPORT_SURFACE_READ_MODEL_VERSION,
        "checkpoint_id": checkpoint_id,
        "consumer_kind": consumer_kind,
        "passport_ref": passport_ref,
        "readiness_summary": readiness,
        "display_fields": display_fields,
        "invariants": SURFACE_READ_MODEL_INVARIANTS,
        "truth_label": OutputPassportTruthLabel.READ_MODEL_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return SurfaceOutputPassportReadModel(
        **payload,
        surface_read_model_hash=_hash_payload(payload),
    )


def build_all_surface_passport_read_models(
    *,
    passport_ref: str = "dev-passport-001",
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> tuple[SurfaceOutputPassportReadModel, ...]:
    return tuple(
        build_surface_passport_read_model(
            consumer_kind=kind,
            passport_ref=passport_ref,
            source_label=source_label,
        )
        for kind in SURFACE_CONSUMER_KINDS
    )


def serialize_surface_read_model(
    read_model: SurfaceOutputPassportReadModel,
) -> str:
    return to_canonical_json(read_model)

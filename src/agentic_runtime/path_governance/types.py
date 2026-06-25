"""Path governance foundation types (P1.7.0)."""
from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .errors import PathGovernanceError, PathGovernanceErrorCode
from .labels import ProjectionSourceLabel
from .validation import validate_known_fields


PATH_GOVERNANCE_MODULE_NAME: str = "path_governance"
PATH_GOVERNANCE_MODULE_VERSION: str = "p1.7.0"
PATH_GOVERNANCE_TASK_ID: str = "P1.7.0"

CAPABILITY_STATUS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "module_name",
    "module_version",
    "task_id",
    "posture",
    "enforcement_enabled",
    "resolver_available",
    "projection_available",
    "cli_available",
    "trace_hook_available",
    "policy_bridge_available",
    "source_label",
    "unavailable_reasons",
    "notes",
})


class FoundationPosture(str, Enum):
    """Declared posture for path governance capability reporting."""

    FOUNDATION_ONLY = "FOUNDATION_ONLY"
    SHADOW_ONLY = "SHADOW_ONLY"
    NON_ENFORCING = "NON_ENFORCING"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class PathGovernanceCapabilityStatus:
    """Honest capability report for path governance foundation phase."""

    module_name: str
    module_version: str
    task_id: str
    posture: FoundationPosture
    enforcement_enabled: bool
    resolver_available: bool
    projection_available: bool
    cli_available: bool
    trace_hook_available: bool
    policy_bridge_available: bool
    source_label: ProjectionSourceLabel
    unavailable_reasons: Mapping[str, str]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.unavailable_reasons, MappingABC):
            raise PathGovernanceError(
                "unavailable_reasons must be a mapping",
                code=PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
                field="unavailable_reasons",
            )
        if not isinstance(self.notes, tuple):
            raise PathGovernanceError(
                "notes must be a tuple of strings",
                code=PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
                field="notes",
            )
        object.__setattr__(
            self,
            "unavailable_reasons",
            MappingProxyType(dict(self.unavailable_reasons)),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "cli_available": self.cli_available,
            "enforcement_enabled": self.enforcement_enabled,
            "module_name": self.module_name,
            "module_version": self.module_version,
            "notes": list(self.notes),
            "policy_bridge_available": self.policy_bridge_available,
            "posture": self.posture.value,
            "projection_available": self.projection_available,
            "resolver_available": self.resolver_available,
            "source_label": self.source_label.value,
            "task_id": self.task_id,
            "trace_hook_available": self.trace_hook_available,
            "unavailable_reasons": dict(
                sorted(self.unavailable_reasons.items(), key=lambda item: item[0])
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceCapabilityStatus:
        validate_known_fields(data, CAPABILITY_STATUS_KNOWN_FIELDS, label="capability_status")
        posture_raw = data["posture"]
        if isinstance(posture_raw, FoundationPosture):
            posture = posture_raw
        elif isinstance(posture_raw, str):
            try:
                posture = FoundationPosture(posture_raw)
            except ValueError as exc:
                raise PathGovernanceError(
                    f"invalid posture: {posture_raw!r}",
                    code=PathGovernanceErrorCode.INVALID_ENUM,
                    field="posture",
                ) from exc
        else:
            raise PathGovernanceError(
                "posture must be a string or FoundationPosture",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="posture",
            )

        source_raw = data["source_label"]
        if isinstance(source_raw, ProjectionSourceLabel):
            source_label = source_raw
        elif isinstance(source_raw, str):
            try:
                source_label = ProjectionSourceLabel(source_raw)
            except ValueError as exc:
                raise PathGovernanceError(
                    f"invalid source_label: {source_raw!r}",
                    code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                    field="source_label",
                ) from exc
        else:
            raise PathGovernanceError(
                "source_label must be a string or ProjectionSourceLabel",
                code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            )

        notes_raw = data.get("notes", ())
        if isinstance(notes_raw, str):
            notes: tuple[str, ...] = (notes_raw,)
        elif isinstance(notes_raw, (list, tuple)):
            notes = tuple(str(item) for item in notes_raw)
        else:
            raise PathGovernanceError(
                "notes must be a string, list, or tuple",
                code=PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
                field="notes",
            )

        reasons_raw = data["unavailable_reasons"]
        if not isinstance(reasons_raw, MappingABC):
            raise PathGovernanceError(
                "unavailable_reasons must be a mapping",
                code=PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
                field="unavailable_reasons",
            )

        bool_fields = (
            "enforcement_enabled",
            "resolver_available",
            "projection_available",
            "cli_available",
            "trace_hook_available",
            "policy_bridge_available",
        )
        bool_values: dict[str, bool] = {}
        for name in bool_fields:
            value = data[name]
            if not isinstance(value, bool):
                raise PathGovernanceError(
                    f"{name} must be boolean",
                    code=PathGovernanceErrorCode.PATH_GOVERNANCE_UNAVAILABLE,
                    field=name,
                )
            bool_values[name] = value

        return cls(
            module_name=str(data["module_name"]),
            module_version=str(data["module_version"]),
            task_id=str(data["task_id"]),
            posture=posture,
            source_label=source_label,
            unavailable_reasons=dict(reasons_raw),
            notes=notes,
            **bool_values,
        )

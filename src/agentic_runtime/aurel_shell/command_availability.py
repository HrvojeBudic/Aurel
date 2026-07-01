"""P2.VSLICE-A command availability projection for governed global commands.

Maps seed global commands to honest availability truth states. This module
projects read-model availability only; it does not execute commands, route
commands, or claim Shell LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)

P2_VSLICE_A_PACK_ID = "P2.VSLICE-A"
P2_VSLICE_A_CONTRACT_VERSION = "p2_vslice_a_global_command_contract.v1"
P2_VSLICE_A_REGISTRY_VERSION = "p2_vslice_a_global_command_registry.v1"
P2_VSLICE_A_AVAILABILITY_VERSION = "p2_vslice_a_command_availability_projection.v1"
P2_VSLICE_A_REPORT_PATH = (
    "agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md"
)

COMMAND_EXECUTION_UNAVAILABLE_REASON = (
    "P2.VSLICE-A provides governed command preflight only. "
    "Command execution is unavailable in this scope."
)


class CommandAvailabilityTruth(str, Enum):
    AVAILABLE_READ_ONLY = "AVAILABLE_READ_ONLY"
    AVAILABLE_PREFLIGHT_ONLY = "AVAILABLE_PREFLIGHT_ONLY"
    AVAILABLE_DEV_FIXTURE = "AVAILABLE_DEV_FIXTURE"
    UNAVAILABLE_BACKEND_MISSING = "UNAVAILABLE_BACKEND_MISSING"
    UNAVAILABLE_SAFE_SANDBOX_MISSING = "UNAVAILABLE_SAFE_SANDBOX_MISSING"
    DENIED_POLICY = "DENIED_POLICY"
    DENIED_IDENTITY = "DENIED_IDENTITY"
    DENIED_SANDBOX = "DENIED_SANDBOX"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    ERROR = "ERROR"


class GlobalCommandCategory(str, Enum):
    SHELL = "shell"
    SURFACE = "surface"
    SYSTEM = "system"
    EVIDENCE = "evidence"
    OPERATOR = "operator"
    UNAVAILABLE = "unavailable"


class GlobalCommandInteractionMode(str, Enum):
    READ_ONLY = "read_only"
    PREFLIGHT_ONLY = "preflight_only"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class GlobalCommandContract(_CanonicalMixin):
    schema_version: str
    command_id: str
    slug: str
    label: str
    description: str
    category: GlobalCommandCategory
    interaction_mode: GlobalCommandInteractionMode
    surface_relation: str
    truth_state: CommandAvailabilityTruth
    allows_execution: bool
    allows_preflight: bool
    allows_mutation: bool
    claims_live: bool
    claims_trace_verified: bool
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class GlobalCommandAvailabilityEntry(_CanonicalMixin):
    command_id: str
    truth_state: CommandAvailabilityTruth
    interaction_mode: GlobalCommandInteractionMode
    available_for_read: bool
    available_for_preflight: bool
    available_for_execution: bool
    unavailable_reason: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class CommandAvailabilityProjection(_CanonicalMixin):
    schema_version: str
    pack_id: str
    entries: tuple[GlobalCommandAvailabilityEntry, ...]
    uses_live: bool
    uses_trace_verified: bool
    projection_hash: str


@dataclass(frozen=True)
class P2VSliceACommandRegistry(_CanonicalMixin):
    schema_version: str
    pack_id: str
    commands: tuple[GlobalCommandContract, ...]
    executes_commands: bool
    truth_label: str
    registry_hash: str


def _command_id(slug: str) -> str:
    return f"global_command:{slug}"


def _build_contract(
    slug: str,
    *,
    label: str,
    description: str,
    category: GlobalCommandCategory,
    interaction_mode: GlobalCommandInteractionMode,
    surface_relation: str,
    truth_state: CommandAvailabilityTruth,
) -> GlobalCommandContract:
    allows_execution = False
    allows_preflight = interaction_mode is GlobalCommandInteractionMode.PREFLIGHT_ONLY
    allows_mutation = False
    payload: dict[str, Any] = {
        "schema_version": P2_VSLICE_A_CONTRACT_VERSION,
        "command_id": _command_id(slug),
        "slug": slug,
        "label": label,
        "description": description,
        "category": category,
        "interaction_mode": interaction_mode,
        "surface_relation": surface_relation,
        "truth_state": truth_state,
        "allows_execution": allows_execution,
        "allows_preflight": allows_preflight,
        "allows_mutation": allows_mutation,
        "claims_live": False,
        "claims_trace_verified": False,
        "limitations": (
            "no_command_execution",
            "no_command_router",
            "no_shell_live_claim",
            "no_trace_verified_claim",
        ),
    }
    return GlobalCommandContract(**payload, contract_hash=_hash_payload(payload))


def _seed_command_specs() -> tuple[dict[str, Any], ...]:
    return (
        {
            "slug": "shell.commands.list",
            "label": "List Global Commands",
            "description": "Read-only listing of governed global command contracts.",
            "category": GlobalCommandCategory.SHELL,
            "interaction_mode": GlobalCommandInteractionMode.READ_ONLY,
            "surface_relation": "global",
            "truth_state": CommandAvailabilityTruth.AVAILABLE_READ_ONLY,
        },
        {
            "slug": "shell.command.inspect",
            "label": "Inspect Global Command",
            "description": "Read-only inspection of one global command contract and availability.",
            "category": GlobalCommandCategory.SHELL,
            "interaction_mode": GlobalCommandInteractionMode.READ_ONLY,
            "surface_relation": "global",
            "truth_state": CommandAvailabilityTruth.AVAILABLE_READ_ONLY,
        },
        {
            "slug": "shell.command.preflight",
            "label": "Preflight Global Command",
            "description": "Governed preflight decision for a command intent without execution.",
            "category": GlobalCommandCategory.SHELL,
            "interaction_mode": GlobalCommandInteractionMode.PREFLIGHT_ONLY,
            "surface_relation": "global",
            "truth_state": CommandAvailabilityTruth.AVAILABLE_PREFLIGHT_ONLY,
        },
        {
            "slug": "surface.registry.list",
            "label": "List Surface Registry",
            "description": "Read-only surface registry projection from P2.1 contracts.",
            "category": GlobalCommandCategory.SURFACE,
            "interaction_mode": GlobalCommandInteractionMode.READ_ONLY,
            "surface_relation": "surface_registry",
            "truth_state": CommandAvailabilityTruth.AVAILABLE_READ_ONLY,
        },
        {
            "slug": "system.status.read",
            "label": "Read System Status",
            "description": "Read-only system status summary; DEV_FIXTURE when no live backend exists.",
            "category": GlobalCommandCategory.SYSTEM,
            "interaction_mode": GlobalCommandInteractionMode.READ_ONLY,
            "surface_relation": "system",
            "truth_state": CommandAvailabilityTruth.AVAILABLE_DEV_FIXTURE,
        },
        {
            "slug": "evidence.latest.read",
            "label": "Read Latest Evidence",
            "description": "Read-only latest evidence refs when available; contract-only otherwise.",
            "category": GlobalCommandCategory.EVIDENCE,
            "interaction_mode": GlobalCommandInteractionMode.READ_ONLY,
            "surface_relation": "evidence",
            "truth_state": CommandAvailabilityTruth.CONTRACT_ONLY,
        },
        {
            "slug": "shell.command.execute",
            "label": "Execute Global Command",
            "description": "Unavailable example: arbitrary command execution is not supported.",
            "category": GlobalCommandCategory.UNAVAILABLE,
            "interaction_mode": GlobalCommandInteractionMode.UNAVAILABLE,
            "surface_relation": "global",
            "truth_state": CommandAvailabilityTruth.UNAVAILABLE_BACKEND_MISSING,
        },
    )


def build_p2_vslice_a_command_registry() -> P2VSliceACommandRegistry:
    commands = tuple(
        _build_contract(
            str(spec["slug"]),
            label=str(spec["label"]),
            description=str(spec["description"]),
            category=spec["category"],
            interaction_mode=spec["interaction_mode"],
            surface_relation=str(spec["surface_relation"]),
            truth_state=spec["truth_state"],
        )
        for spec in _seed_command_specs()
    )
    command_ids = [command.command_id for command in commands]
    if len(command_ids) != len(set(command_ids)):
        _reject(
            "P2.VSLICE-A registry cannot contain duplicate command IDs",
            field="commands",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "schema_version": P2_VSLICE_A_REGISTRY_VERSION,
        "pack_id": P2_VSLICE_A_PACK_ID,
        "commands": commands,
        "executes_commands": False,
        "truth_label": CommandAvailabilityTruth.AVAILABLE_PREFLIGHT_ONLY.value,
    }
    registry = P2VSliceACommandRegistry(**payload, registry_hash=_hash_payload(payload))
    assert registry.executes_commands is False
    return registry


def project_command_availability(
    registry: P2VSliceACommandRegistry | None = None,
) -> CommandAvailabilityProjection:
    if registry is None:
        registry = build_p2_vslice_a_command_registry()
    entries: list[GlobalCommandAvailabilityEntry] = []
    for command in registry.commands:
        available_for_read = command.interaction_mode in (
            GlobalCommandInteractionMode.READ_ONLY,
            GlobalCommandInteractionMode.PREFLIGHT_ONLY,
        )
        available_for_preflight = command.allows_preflight or (
            command.interaction_mode is GlobalCommandInteractionMode.PREFLIGHT_ONLY
        )
        unavailable_reason = ""
        if command.interaction_mode is GlobalCommandInteractionMode.UNAVAILABLE:
            unavailable_reason = COMMAND_EXECUTION_UNAVAILABLE_REASON
        elif not available_for_execution(command):
            unavailable_reason = COMMAND_EXECUTION_UNAVAILABLE_REASON
        payload = {
            "command_id": command.command_id,
            "truth_state": command.truth_state,
            "interaction_mode": command.interaction_mode,
            "available_for_read": available_for_read,
            "available_for_preflight": available_for_preflight,
            "available_for_execution": False,
            "unavailable_reason": unavailable_reason,
            "truth_label": command.truth_state.value,
            "limitations": command.limitations,
        }
        entries.append(
            GlobalCommandAvailabilityEntry(**payload, entry_hash=_hash_payload(payload))
        )
    projection_payload = {
        "schema_version": P2_VSLICE_A_AVAILABILITY_VERSION,
        "pack_id": P2_VSLICE_A_PACK_ID,
        "entries": tuple(entries),
        "uses_live": False,
        "uses_trace_verified": False,
    }
    return CommandAvailabilityProjection(
        **projection_payload,
        projection_hash=_hash_payload(projection_payload),
    )


def available_for_execution(command: GlobalCommandContract) -> bool:
    return command.allows_execution


def lookup_command_contract(
    command_id: str,
    registry: P2VSliceACommandRegistry | None = None,
) -> GlobalCommandContract | None:
    if registry is None:
        registry = build_p2_vslice_a_command_registry()
    for command in registry.commands:
        if command.command_id == command_id or command.slug == command_id:
            return command
    return None


def list_command_contracts(
    registry: P2VSliceACommandRegistry | None = None,
) -> tuple[GlobalCommandContract, ...]:
    if registry is None:
        registry = build_p2_vslice_a_command_registry()
    return registry.commands

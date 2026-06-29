"""P2.4-A command palette / global commands foundation.

Contract-only command declarations for AurelShell. This module defines command
identity, registry, scope/surface targets, availability, and input parameter
contracts without command palette UI, command execution, routing, keyboard
shortcuts, permission enforcement, storage, memory/trace writes, product
behavior, release scope, or runtime mutation.
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
    to_canonical_json,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    SURFACE_KIND_DISPLAY_NAMES,
    SURFACE_KIND_IDS,
    AurelSurfaceKind,
    build_default_surface_registry,
)
from .workspace_window_section_projection import (
    P2_3_D_PACK_ID,
    P2_3_D_REPORT_PATH,
    P2_3_D_SECTION_SEAL_VERSION,
    build_p2_3_d_workspace_window_section_result,
)

P2_4_A_PACK_ID = "P2.4-A"
P2_4_A_SECTION_ID = "P2.4"
P2_4_A_OFFICIAL_SECTION_NAME = "Command Palette / Global Commands"
P2_4_A_DEPENDENCY_PACK = P2_3_D_PACK_ID
P2_4_A_NEXT_PACK = "P2.4-B"
P2_4_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.4.0",
    "P2.4.1",
    "P2.4.2",
    "P2.4.3",
    "P2.4.4",
    "P2.4.5",
)
P2_4_A_REPORT_FILENAME = "P2_4_A_COMMAND_PALETTE_GLOBAL_COMMANDS_FOUNDATION.md"
P2_4_A_REPORT_PATH = f"agent/reports/{P2_4_A_REPORT_FILENAME}"

P2_4_A_GATE_VERSION = "p2_4_a_command_palette_section_gate.v1"
P2_4_A_COMMAND_ID_VERSION = "p2_4_a_global_command_id.v1"
P2_4_A_IDENTITY_VERSION = "p2_4_a_global_command_identity.v1"
P2_4_A_REGISTRY_VERSION = "p2_4_a_global_command_registry.v1"
P2_4_A_SCOPE_VERSION = "p2_4_a_global_command_scope.v1"
P2_4_A_SURFACE_TARGET_VERSION = "p2_4_a_global_command_surface_target.v1"
P2_4_A_AVAILABILITY_VERSION = "p2_4_a_global_command_availability.v1"
P2_4_A_INPUT_CONTRACT_VERSION = "p2_4_a_global_command_input_contract.v1"
P2_4_A_PARAMETER_VERSION = "p2_4_a_global_command_parameter.v1"
P2_4_A_RESULT_VERSION = "p2_4_a_global_command_foundation_result.v1"

COMMAND_EXECUTION_UNAVAILABLE_REASON = (
    "P2.4-A defines command contracts only. Runtime command execution is "
    "unavailable in this scope."
)

_IDENTITY_NON_GOALS: tuple[str, ...] = (
    "no_command_execution",
    "no_command_handler",
    "no_command_router",
    "no_live_claim",
    "no_trace_verified_claim",
    "no_product_behavior",
)
_REGISTRY_NON_GOALS: tuple[str, ...] = (
    "no_command_palette_ui",
    "no_command_router",
    "no_command_execution",
    "no_runtime_mutation",
    "no_storage_write",
    "no_memory_write",
    "no_trace_write",
)
_SCOPE_NON_GOALS: tuple[str, ...] = (
    "no_authority_grant",
    "no_route_execution",
    "no_surface_runtime_switch",
)
_AVAILABILITY_NON_GOALS: tuple[str, ...] = (
    "no_permission_decision",
    "no_permission_grant",
    "no_permission_denial",
    "no_runtime_block",
    "no_custos_integration",
)
_INPUT_NON_GOALS: tuple[str, ...] = (
    "no_invocation",
    "no_handler_invocation",
    "no_command_execution",
    "no_runtime_validation",
)


class CommandPaletteSectionGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class GlobalCommandRegistryStatus(str, Enum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandAvailabilityStatus(str, Enum):
    AVAILABLE_FOR_DECLARATION = "AVAILABLE_FOR_DECLARATION"
    UNAVAILABLE_FOR_EXECUTION = "UNAVAILABLE_FOR_EXECUTION"
    DEFERRED = "DEFERRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandKind(str, Enum):
    NAVIGATION_PROPOSAL = "NAVIGATION_PROPOSAL"
    SURFACE_COMMAND = "SURFACE_COMMAND"
    WINDOW_COMMAND = "WINDOW_COMMAND"
    SYSTEM_COMMAND = "SYSTEM_COMMAND"
    SETTINGS_COMMAND = "SETTINGS_COMMAND"
    OPERATOR_COMMAND = "OPERATOR_COMMAND"
    DOCUMENTATION_COMMAND = "DOCUMENTATION_COMMAND"
    DEVELOPMENT_COMMAND = "DEVELOPMENT_COMMAND"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandScopeKind(str, Enum):
    GLOBAL = "GLOBAL"
    SURFACE = "SURFACE"
    LOCAL = "LOCAL"
    SYSTEM = "SYSTEM"
    OPERATOR = "OPERATOR"
    DEVELOPMENT = "DEVELOPMENT"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandParameterKind(str, Enum):
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    ENUM = "ENUM"
    JSON = "JSON"
    SURFACE_ID = "SURFACE_ID"
    COMMAND_ID = "COMMAND_ID"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPO_EVIDENCE_GATE = "REPO_EVIDENCE_GATE"
    OMNI_EVIDENCE_IGNORED = "OMNI_EVIDENCE_IGNORED"
    UNAVAILABLE = "UNAVAILABLE"
    UNAVAILABLE_FOR_EXECUTION = "UNAVAILABLE_FOR_EXECUTION"
    INPUT_CONTRACT_ONLY = "INPUT_CONTRACT_ONLY"
    NOT_EXECUTION = "NOT_EXECUTION"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_COMMAND_HANDLER = "NOT_COMMAND_HANDLER"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_AUTHORITY_GRANT = "NOT_AUTHORITY_GRANT"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_SURFACE_RUNTIME_SWITCH = "NOT_SURFACE_RUNTIME_SWITCH"
    NOT_COMMAND_PALETTE_UI = "NOT_COMMAND_PALETTE_UI"
    NOT_INVOCATION = "NOT_INVOCATION"
    NOT_HANDLER = "NOT_HANDLER"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class P24ASideEffectProof(_CanonicalMixin):
    command_palette_ui_created: bool = False
    frontend_ui_created: bool = False
    browser_ui_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    keyboard_listener_created: bool = False
    shortcut_handler_created: bool = False
    fuzzy_search_created: bool = False
    ranking_engine_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    approval_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    surface_runtime_switch_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    local_storage_written: bool = False
    browser_storage_written: bool = False
    memory_written: bool = False
    trace_written: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_4_b_started: bool = False
    p2_5_started: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class CommandPaletteSectionGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_contract_seal_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: CommandPaletteSectionGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class GlobalCommandId(_CanonicalMixin):
    schema_version: str
    command_id: str
    slug: str
    declared_by_pack: str
    stable: bool
    command_id_hash: str


@dataclass(frozen=True)
class GlobalCommandIdentity(_CanonicalMixin):
    command_id: GlobalCommandId
    schema_version: str
    slug: str
    label: str
    description: str
    kind: GlobalCommandKind
    family: str
    truth_boundaries: tuple[str, ...]
    declared_by_pack: str
    is_declarative: bool
    is_executable: bool
    is_command_handler: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_product_behavior: bool
    limitations: tuple[str, ...]
    identity_hash: str


@dataclass(frozen=True)
class GlobalCommandSurfaceTarget(_CanonicalMixin):
    target_id: str
    schema_version: str
    surface_id: str
    surface_display_name: str
    uses_official_surface_registry: bool
    is_authority_grant: bool
    executes_route: bool
    switches_surface_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    target_hash: str


@dataclass(frozen=True)
class GlobalCommandScope(_CanonicalMixin):
    scope_id: str
    schema_version: str
    command_id: str
    scope_kind: GlobalCommandScopeKind
    surface_target: GlobalCommandSurfaceTarget
    surface_id: str
    surface_display_name: str
    uses_official_surface_registry: bool
    is_authority_grant: bool
    executes_route: bool
    switches_surface_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    scope_hash: str


@dataclass(frozen=True)
class GlobalCommandAvailability(_CanonicalMixin):
    availability_id: str
    schema_version: str
    command_id: str
    availability_status: GlobalCommandAvailabilityStatus
    available_for_declaration: bool
    available_for_execution: bool
    unavailable_reason: str
    is_permission_decision: bool
    grants_permission: bool
    denies_permission: bool
    blocks_runtime: bool
    requires_custos: bool
    truth_label: str
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class GlobalCommandParameter(_CanonicalMixin):
    parameter_id: str
    schema_version: str
    name: str
    parameter_kind: GlobalCommandParameterKind
    required: bool
    description: str
    enum_values: tuple[str, ...]
    default_value: str
    truth_label: str
    parameter_hash: str


@dataclass(frozen=True)
class GlobalCommandInputContract(_CanonicalMixin):
    input_contract_id: str
    schema_version: str
    command_id: str
    parameters: tuple[GlobalCommandParameter, ...]
    required_parameters: tuple[str, ...]
    optional_parameters: tuple[str, ...]
    validation_mode: str
    is_invocation: bool
    invokes_handler: bool
    executes_command: bool
    truth_label: str
    limitations: tuple[str, ...]
    input_contract_hash: str


@dataclass(frozen=True)
class GlobalCommandRegistry(_CanonicalMixin):
    registry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_status: GlobalCommandRegistryStatus
    commands: tuple[GlobalCommandIdentity, ...]
    default_unavailable_reason: str
    is_command_router: bool
    executes_commands: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    creates_ui: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class P24AGlobalCommandFoundationResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    section_gate: CommandPaletteSectionGate
    command_registry: GlobalCommandRegistry
    command_records: tuple[GlobalCommandIdentity, ...]
    scope_records: tuple[GlobalCommandScope, ...]
    availability_records: tuple[GlobalCommandAvailability, ...]
    input_contract_records: tuple[GlobalCommandInputContract, ...]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    report_path: str
    report_index_expected: bool
    side_effect_proof: P24ASideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _surface_display_name(surface_id: str) -> str:
    for kind, canonical_id in SURFACE_KIND_IDS.items():
        if canonical_id == surface_id:
            return SURFACE_KIND_DISPLAY_NAMES[kind]
    _reject(
        f"surface target {surface_id!r} is not in the official P2 surface registry",
        field="surface_id",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def build_command_palette_section_gate() -> CommandPaletteSectionGate:
    p2_3_d = build_p2_3_d_workspace_window_section_result()
    payload = {
        "gate_id": "p2_4_a_command_palette_section_gate",
        "schema_version": P2_4_A_GATE_VERSION,
        "section_id": P2_4_A_SECTION_ID,
        "created_for_pack": P2_4_A_PACK_ID,
        "official_section_name": P2_4_A_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_4_A_DEPENDENCY_PACK,
        "dependency_report_ref": P2_3_D_REPORT_PATH,
        "dependency_commit_ref": "17aea2de737494d8b7b1cd29675cecf9fc5e9237",
        "dependency_validation_ref": "agent/TESTS.md#P2.3-D",
        "dependency_contract_seal_ref": (
            f"{p2_3_d.section_seal.seal_id}:{p2_3_d.section_seal.seal_hash}:"
            f"{P2_3_D_SECTION_SEAL_VERSION}"
        ),
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": CommandPaletteSectionGateStatus.READY,
        "truth_label": GlobalCommandTruthBoundary.REPO_EVIDENCE_GATE.value,
        "limitations": (
            "OMNI evidence is ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not execute commands",
        ),
    }
    return CommandPaletteSectionGate(**payload, gate_hash=_hash_payload(payload))


def build_global_command_id(slug: str) -> GlobalCommandId:
    if not slug or slug.strip() != slug or " " in slug:
        _reject(
            "command slug must be non-empty and space-free",
            field="slug",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "schema_version": P2_4_A_COMMAND_ID_VERSION,
        "command_id": f"global_command:{slug}",
        "slug": slug,
        "declared_by_pack": P2_4_A_PACK_ID,
        "stable": True,
    }
    return GlobalCommandId(**payload, command_id_hash=_hash_payload(payload))


def build_global_command_identity(
    slug: str = "open_hq_surface",
    *,
    label: str = "Open HQ Surface",
    description: str = "Declarative proposal to inspect the HQ surface target.",
    kind: GlobalCommandKind = GlobalCommandKind.NAVIGATION_PROPOSAL,
    family: str = "surface_navigation",
) -> GlobalCommandIdentity:
    command_id = build_global_command_id(slug)
    payload = {
        "command_id": command_id,
        "schema_version": P2_4_A_IDENTITY_VERSION,
        "slug": slug,
        "label": label,
        "description": description,
        "kind": kind,
        "family": family,
        "truth_boundaries": (
            GlobalCommandTruthBoundary.CONTRACT_ONLY.value,
            GlobalCommandTruthBoundary.DECLARATIVE_ONLY.value,
            GlobalCommandTruthBoundary.NOT_EXECUTABLE.value,
            GlobalCommandTruthBoundary.NOT_COMMAND_HANDLER.value,
        ),
        "declared_by_pack": P2_4_A_PACK_ID,
        "is_declarative": True,
        "is_executable": False,
        "is_command_handler": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_product_behavior": False,
        "limitations": _IDENTITY_NON_GOALS,
    }
    identity = GlobalCommandIdentity(**payload, identity_hash=_hash_payload(payload))
    assert_command_is_not_execution(identity)
    return identity


def build_global_command_surface_target(
    surface_id: str = "hq",
) -> GlobalCommandSurfaceTarget:
    registry = build_default_surface_registry()
    if surface_id not in registry.canonical_surface_ids:
        _reject(
            f"surface target {surface_id!r} is not in the official P2 surface registry",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "target_id": f"command_surface_target:{surface_id}",
        "schema_version": P2_4_A_SURFACE_TARGET_VERSION,
        "surface_id": surface_id,
        "surface_display_name": _surface_display_name(surface_id),
        "uses_official_surface_registry": True,
        "is_authority_grant": False,
        "executes_route": False,
        "switches_surface_runtime": False,
        "truth_label": GlobalCommandTruthBoundary.NOT_ROUTE_EXECUTION.value,
        "limitations": _SCOPE_NON_GOALS,
    }
    target = GlobalCommandSurfaceTarget(**payload, target_hash=_hash_payload(payload))
    assert_surface_target_is_not_route_execution(target)
    return target


def build_global_command_scope(
    command_id: str = "global_command:open_hq_surface",
    *,
    scope_kind: GlobalCommandScopeKind = GlobalCommandScopeKind.SURFACE,
    surface_id: str = "hq",
) -> GlobalCommandScope:
    target = build_global_command_surface_target(surface_id)
    payload = {
        "scope_id": f"command_scope:{command_id}:{scope_kind.value}:{surface_id}",
        "schema_version": P2_4_A_SCOPE_VERSION,
        "command_id": command_id,
        "scope_kind": scope_kind,
        "surface_target": target,
        "surface_id": surface_id,
        "surface_display_name": target.surface_display_name,
        "uses_official_surface_registry": True,
        "is_authority_grant": False,
        "executes_route": False,
        "switches_surface_runtime": False,
        "truth_label": GlobalCommandTruthBoundary.NOT_AUTHORITY_GRANT.value,
        "limitations": _SCOPE_NON_GOALS,
    }
    scope = GlobalCommandScope(**payload, scope_hash=_hash_payload(payload))
    if scope.surface_id != scope.surface_target.surface_id:
        _reject(
            "scope surface_id must match surface target",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return scope


def build_global_command_availability(
    command_id: str = "global_command:open_hq_surface",
    *,
    availability_status: GlobalCommandAvailabilityStatus = (
        GlobalCommandAvailabilityStatus.UNAVAILABLE_FOR_EXECUTION
    ),
    unavailable_reason: str = COMMAND_EXECUTION_UNAVAILABLE_REASON,
) -> GlobalCommandAvailability:
    available_for_execution = False
    if availability_status == GlobalCommandAvailabilityStatus.AVAILABLE_FOR_DECLARATION:
        available_for_execution = False
    if not available_for_execution and not unavailable_reason:
        _reject(
            "P2.4-A command execution unavailable state requires a reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "availability_id": f"command_availability:{command_id}",
        "schema_version": P2_4_A_AVAILABILITY_VERSION,
        "command_id": command_id,
        "availability_status": availability_status,
        "available_for_declaration": True,
        "available_for_execution": available_for_execution,
        "unavailable_reason": unavailable_reason,
        "is_permission_decision": False,
        "grants_permission": False,
        "denies_permission": False,
        "blocks_runtime": False,
        "requires_custos": False,
        "truth_label": GlobalCommandTruthBoundary.UNAVAILABLE_FOR_EXECUTION.value,
        "limitations": _AVAILABILITY_NON_GOALS,
    }
    availability = GlobalCommandAvailability(
        **payload,
        availability_hash=_hash_payload(payload),
    )
    assert_availability_is_not_permission(availability)
    return availability


def build_global_command_parameter(
    name: str,
    parameter_kind: GlobalCommandParameterKind,
    *,
    required: bool,
    description: str,
    enum_values: tuple[str, ...] = (),
    default_value: str = "",
) -> GlobalCommandParameter:
    if not name:
        _reject(
            "command parameter name is required",
            field="name",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "parameter_id": f"command_parameter:{name}",
        "schema_version": P2_4_A_PARAMETER_VERSION,
        "name": name,
        "parameter_kind": parameter_kind,
        "required": required,
        "description": description,
        "enum_values": enum_values,
        "default_value": default_value,
        "truth_label": GlobalCommandTruthBoundary.INPUT_CONTRACT_ONLY.value,
    }
    return GlobalCommandParameter(**payload, parameter_hash=_hash_payload(payload))


def build_global_command_input_contract(
    command_id: str = "global_command:open_hq_surface",
    *,
    parameters: tuple[GlobalCommandParameter, ...] | None = None,
) -> GlobalCommandInputContract:
    if parameters is None:
        parameters = (
            build_global_command_parameter(
                "surface_id",
                GlobalCommandParameterKind.SURFACE_ID,
                required=True,
                description="Official surface identifier to target declaratively.",
                enum_values=CANONICAL_SURFACE_ORDER,
            ),
            build_global_command_parameter(
                "reason",
                GlobalCommandParameterKind.STRING,
                required=False,
                description="Optional operator-facing reason for the command proposal.",
            ),
        )
    required = tuple(parameter.name for parameter in parameters if parameter.required)
    optional = tuple(parameter.name for parameter in parameters if not parameter.required)
    payload = {
        "input_contract_id": f"command_input_contract:{command_id}",
        "schema_version": P2_4_A_INPUT_CONTRACT_VERSION,
        "command_id": command_id,
        "parameters": parameters,
        "required_parameters": required,
        "optional_parameters": optional,
        "validation_mode": "DECLARATIVE_SCHEMA_ONLY",
        "is_invocation": False,
        "invokes_handler": False,
        "executes_command": False,
        "truth_label": GlobalCommandTruthBoundary.INPUT_CONTRACT_ONLY.value,
        "limitations": _INPUT_NON_GOALS,
    }
    contract = GlobalCommandInputContract(
        **payload,
        input_contract_hash=_hash_payload(payload),
    )
    assert_input_contract_is_not_invocation(contract)
    return contract


def _default_command_specs() -> tuple[dict[str, str | GlobalCommandKind], ...]:
    return (
        {
            "slug": "open_hq_surface",
            "label": "Open HQ Surface",
            "description": "Declarative proposal to inspect the HQ surface target.",
            "kind": GlobalCommandKind.NAVIGATION_PROPOSAL,
            "family": "surface_navigation",
            "surface_id": "hq",
        },
        {
            "slug": "inspect_workspace_window_section",
            "label": "Inspect Workspace Window Section",
            "description": "Read-model inspection of the sealed P2.3 section projection.",
            "kind": GlobalCommandKind.WINDOW_COMMAND,
            "family": "workspace_window",
            "surface_id": "system",
        },
        {
            "slug": "open_settings_contract",
            "label": "Open Settings Contract",
            "description": "Declarative settings surface target without runtime navigation.",
            "kind": GlobalCommandKind.SETTINGS_COMMAND,
            "family": "settings",
            "surface_id": "settings",
        },
    )


def build_global_command_registry(
    commands: tuple[GlobalCommandIdentity, ...] | None = None,
) -> GlobalCommandRegistry:
    if commands is None:
        built_commands: list[GlobalCommandIdentity] = []
        for spec in _default_command_specs():
            kind = spec["kind"]
            if not isinstance(kind, GlobalCommandKind):
                _reject(
                    "default command spec kind must be a GlobalCommandKind",
                    field="kind",
                    code=AurelShellErrorCode.VALIDATION_ERROR,
                )
            built_commands.append(
                build_global_command_identity(
                    str(spec["slug"]),
                    label=str(spec["label"]),
                    description=str(spec["description"]),
                    kind=kind,
                    family=str(spec["family"]),
                )
            )
        commands = tuple(built_commands)
    command_ids = [command.command_id.command_id for command in commands]
    if len(command_ids) != len(set(command_ids)):
        _reject(
            "global command registry cannot contain duplicate command IDs",
            field="commands",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "registry_id": "p2_4_a_global_command_registry",
        "schema_version": P2_4_A_REGISTRY_VERSION,
        "section_id": P2_4_A_SECTION_ID,
        "created_for_pack": P2_4_A_PACK_ID,
        "official_section_name": P2_4_A_OFFICIAL_SECTION_NAME,
        "registry_status": GlobalCommandRegistryStatus.READY,
        "commands": commands,
        "default_unavailable_reason": COMMAND_EXECUTION_UNAVAILABLE_REASON,
        "is_command_router": False,
        "executes_commands": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "writes_storage": False,
        "creates_ui": False,
        "truth_label": GlobalCommandTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": _REGISTRY_NON_GOALS,
    }
    registry = GlobalCommandRegistry(**payload, registry_hash=_hash_payload(payload))
    assert_registry_is_not_router(registry)
    return registry


def _build_scope_records(
    registry: GlobalCommandRegistry,
) -> tuple[GlobalCommandScope, ...]:
    surface_by_slug = {
        str(spec["slug"]): str(spec["surface_id"]) for spec in _default_command_specs()
    }
    return tuple(
        build_global_command_scope(
            command.command_id.command_id,
            scope_kind=(
                GlobalCommandScopeKind.SURFACE
                if surface_by_slug[command.slug] != "system"
                else GlobalCommandScopeKind.SYSTEM
            ),
            surface_id=surface_by_slug[command.slug],
        )
        for command in registry.commands
    )


def build_p2_4_a_side_effect_proof() -> P24ASideEffectProof:
    return P24ASideEffectProof()


def build_p2_4_a_global_command_foundation_result() -> (
    P24AGlobalCommandFoundationResult
):
    gate = build_command_palette_section_gate()
    registry = build_global_command_registry()
    scopes = _build_scope_records(registry)
    availability = tuple(
        build_global_command_availability(command.command_id.command_id)
        for command in registry.commands
    )
    input_contracts = tuple(
        build_global_command_input_contract(command.command_id.command_id)
        for command in registry.commands
    )
    side_effects = build_p2_4_a_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_4_A_RESULT_VERSION,
        "pack_id": P2_4_A_PACK_ID,
        "section_id": P2_4_A_SECTION_ID,
        "official_section_name": P2_4_A_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_4_A_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_4_A_DEPENDENCY_PACK,
        "dependency_report_ref": P2_3_D_REPORT_PATH,
        "dependency_commit_ref": "17aea2de737494d8b7b1cd29675cecf9fc5e9237",
        "section_gate": gate,
        "command_registry": registry,
        "command_records": registry.commands,
        "scope_records": scopes,
        "availability_records": availability,
        "input_contract_records": input_contracts,
        "truth_labels": (
            GlobalCommandTruthBoundary.CONTRACT_ONLY.value,
            GlobalCommandTruthBoundary.DECLARATIVE_ONLY.value,
            GlobalCommandTruthBoundary.READ_MODEL_ONLY.value,
            GlobalCommandTruthBoundary.DEV_FIXTURE.value,
            GlobalCommandTruthBoundary.UNAVAILABLE_FOR_EXECUTION.value,
            GlobalCommandTruthBoundary.NOT_EXECUTION.value,
            GlobalCommandTruthBoundary.NOT_COMMAND_PALETTE_UI.value,
            GlobalCommandTruthBoundary.NOT_PERMISSION_ENFORCEMENT.value,
            GlobalCommandTruthBoundary.NOT_LIVE.value,
            GlobalCommandTruthBoundary.NOT_TRACE_VERIFIED.value,
            GlobalCommandTruthBoundary.NOT_PRODUCT_BEHAVIOR.value,
            GlobalCommandTruthBoundary.NOT_RELEASE_SCOPE.value,
        ),
        "unavailable_reasons": (COMMAND_EXECUTION_UNAVAILABLE_REASON,),
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "report_path": P2_4_A_REPORT_PATH,
        "report_index_expected": True,
        "side_effect_proof": side_effects,
        "next_pack": P2_4_A_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P24AGlobalCommandFoundationResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_4_a_does_not_start_future_work(result)
    assert_p2_4_a_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_4_a_result(
    result: P24AGlobalCommandFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_a_global_command_foundation_result()
    return to_canonical_json(result.to_canonical_dict())


def render_global_command_registry_summary(
    result: P24AGlobalCommandFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_a_global_command_foundation_result()
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"registry={result.command_registry.registry_id}",
            f"commands={len(result.command_records)}",
            f"executes_commands={str(result.command_registry.executes_commands).lower()}",
            f"command_palette_ui={str(result.side_effect_proof.command_palette_ui_created).lower()}",
            f"next={result.next_pack}",
        )
    )


def assert_command_is_not_execution(command: GlobalCommandIdentity) -> None:
    if command.is_executable or command.is_command_handler:
        _reject(
            "P2.4-A command identity must not be executable or a handler",
            field="is_executable",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if command.claims_live or command.claims_trace_verified or command.claims_product_behavior:
        _reject(
            "P2.4-A command identity must not claim LIVE, TRACE_VERIFIED, or product behavior",
            field="claims_live",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_registry_is_not_router(registry: GlobalCommandRegistry) -> None:
    if registry.is_command_router or registry.executes_commands or registry.creates_ui:
        _reject(
            "P2.4-A registry must not route, execute, or create UI",
            field="is_command_router",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if registry.mutates_runtime or registry.writes_memory or registry.writes_trace or registry.writes_storage:
        _reject(
            "P2.4-A registry must not mutate runtime or write storage/memory/trace",
            field="mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_availability_is_not_permission(
    availability: GlobalCommandAvailability,
) -> None:
    if not availability.available_for_execution and not availability.unavailable_reason:
        _reject(
            "unavailable command execution requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        availability.is_permission_decision
        or availability.grants_permission
        or availability.denies_permission
        or availability.blocks_runtime
        or availability.requires_custos
    ):
        _reject(
            "P2.4-A availability is not permission enforcement",
            field="is_permission_decision",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_surface_target_is_not_route_execution(
    target: GlobalCommandSurfaceTarget,
) -> None:
    if target.surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            "surface target must use official P2 surface registry",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if target.is_authority_grant or target.executes_route or target.switches_surface_runtime:
        _reject(
            "P2.4-A surface target must not grant authority, execute routes, or switch runtime surfaces",
            field="executes_route",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_input_contract_is_not_invocation(
    input_contract: GlobalCommandInputContract,
) -> None:
    if input_contract.is_invocation or input_contract.invokes_handler or input_contract.executes_command:
        _reject(
            "P2.4-A input contract must not invoke handlers or execute commands",
            field="is_invocation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_a_does_not_start_future_work(
    result: P24AGlobalCommandFoundationResult,
) -> None:
    if result.starts_future_work or result.next_pack != P2_4_A_NEXT_PACK:
        _reject(
            "P2.4-A result must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_a_side_effects_all_false(proof: P24ASideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                f"P2.4-A side-effect field must remain false: {field}",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_p2_4_a_depends_on_p2_3_d(gate: CommandPaletteSectionGate) -> None:
    if gate.dependency_pack != P2_3_D_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.4-A must depend on passed P2.3-D repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: CommandPaletteSectionGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.4-A gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )

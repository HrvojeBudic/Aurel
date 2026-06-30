"""P2.7-A Shell / CLI / TUI binding foundation contracts.

Contract-only binding foundation over P2.6-D section seal evidence. This
module defines binding section gate, target registry, surface binding catalog,
capability descriptors, adapter/projection consumption contracts, read-only
command surface, output/render descriptors, no-command-execution boundary,
no-runtime-dispatch boundary, and binding foundation result.

Core law:
  - Binding contract is not command execution.
  - CLI descriptor is not CLI app.
  - TUI descriptor is not TUI runtime.
  - Shell binding is not Shell execution runtime.
  - Adapter contract is not runtime dispatch adapter.
  - Projection consumption is not live API/event bridge consumption.

It does not create CLI app, CLI runner, CLI entrypoint, TUI runtime, TUI app,
Shell runtime, Shell execution runtime, command parser/router/handler,
command execution, tool invocation, workflow dispatch, runtime dispatch,
runtime bridge, runtime mutation, surface switching, API server, HTTP routes,
live endpoint, event bus, trace/memory/storage writes, permission enforcement,
approval runtime, Custos/Mneme integration, product UI, product behavior,
release scope, LIVE, TRACE_VERIFIED, P2.7-B, P2.8, P2.10, or P2.13.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
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
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES
from .surface_projection_section_seal import (
    P2_6_D_PACK_ID,
    P2_6_D_REPORT_PATH,
    P2_6_D_VALIDATION_REF,
    P26DSurfaceProjectionSectionSealResult,
    build_p2_6_d_surface_projection_section_seal_result,
)
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_7_A_PACK_ID = "P2.7-A"
P2_7_A_SECTION_ID = "P2.7"
P2_7_A_OFFICIAL_SECTION_NAME = "Shell / CLI / TUI Binding"
P2_7_A_DEPENDENCY_PACK = P2_6_D_PACK_ID
P2_7_A_NEXT_PACK = "P2.7-B"
P2_7_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.7.0",
    "P2.7.1",
    "P2.7.2",
    "P2.7.3",
    "P2.7.4",
    "P2.7.5",
)
P2_7_A_REPORT_FILENAME = "P2_7_A_SHELL_CLI_TUI_BINDING_FOUNDATION.md"
P2_7_A_REPORT_PATH = f"agent/reports/{P2_7_A_REPORT_FILENAME}"

P2_6_D_COMMIT_REF = "9c74a57"

P2_7_A_GATE_VERSION = "p2_7_a_shell_binding_section_gate.v1"
P2_7_A_REGISTRY_VERSION = "p2_7_a_shell_binding_target_registry.v1"
P2_7_A_CATALOG_VERSION = "p2_7_a_shell_binding_surface_catalog.v1"
P2_7_A_CAPABILITY_VERSION = "p2_7_a_shell_binding_capability_descriptor.v1"
P2_7_A_ADAPTER_VERSION = "p2_7_a_shell_binding_adapter_contract.v1"
P2_7_A_PROJECTION_CONSUMPTION_VERSION = (
    "p2_7_a_shell_binding_projection_consumption_contract.v1"
)
P2_7_A_COMMAND_SURFACE_VERSION = "p2_7_a_shell_binding_read_only_command_surface.v1"
P2_7_A_OUTPUT_DESCRIPTOR_VERSION = "p2_7_a_shell_binding_output_descriptor.v1"
P2_7_A_RENDER_DESCRIPTOR_VERSION = "p2_7_a_shell_binding_render_descriptor.v1"
P2_7_A_NO_COMMAND_EXECUTION_VERSION = (
    "p2_7_a_shell_binding_no_command_execution_boundary.v1"
)
P2_7_A_NO_RUNTIME_DISPATCH_VERSION = (
    "p2_7_a_shell_binding_no_runtime_dispatch_boundary.v1"
)
P2_7_A_FOUNDATION_RESULT_VERSION = "p2_7_a_shell_binding_foundation_result.v1"
P2_7_A_RESULT_VERSION = "p2_7_a_shell_binding_foundation_pack_result.v1"

P2_7_A_TEST_REF = "tests/aurel_shell/test_shell_binding_foundation.py"
P2_7_A_VALIDATION_REF = "agent/TESTS.md#P2.7-A"
P2_7_A_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_7_A_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_BINDING_SURFACE_KINDS: tuple[str, ...] = ("SHELL", "CLI", "TUI")

_NO_COMMAND_EXECUTION_REASON = (
    "P2.7-A defines read-only command surface descriptors only. No command "
    "parser, router, handler, execution, invocation, tool invocation, or "
    "workflow dispatch exists in this repo scope."
)
_NO_RUNTIME_DISPATCH_REASON = (
    "P2.7-A defines binding adapter and projection consumption contracts only. "
    "No runtime dispatch, runtime bridge, runtime mutation, surface switch, or "
    "trace/memory/storage writes exist in this repo scope."
)


class ShellBindingSectionGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellBindingCapabilityMode(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_ONLY_DESCRIPTOR_ONLY = "READ_ONLY_DESCRIPTOR_ONLY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"


class ShellBindingCommandSurfaceMode(str, Enum):
    READ_ONLY_CONTRACT = "READ_ONLY_CONTRACT"
    DESCRIPTOR_ONLY = "DESCRIPTOR_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class ShellBindingCapabilityKind(str, Enum):
    SHELL_BINDING_DESCRIPTOR = "SHELL_BINDING_DESCRIPTOR"
    CLI_BINDING_DESCRIPTOR = "CLI_BINDING_DESCRIPTOR"
    TUI_BINDING_DESCRIPTOR = "TUI_BINDING_DESCRIPTOR"
    READ_ONLY_COMMAND_SURFACE_DESCRIPTOR = "READ_ONLY_COMMAND_SURFACE_DESCRIPTOR"
    OUTPUT_DESCRIPTOR = "OUTPUT_DESCRIPTOR"
    RENDER_DESCRIPTOR = "RENDER_DESCRIPTOR"
    DEV_FIXTURE_DESCRIPTOR = "DEV_FIXTURE_DESCRIPTOR"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class ShellBindingTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    BINDING_FOUNDATION_ONLY = "BINDING_FOUNDATION_ONLY"
    BINDING_GATE_ONLY = "BINDING_GATE_ONLY"
    TARGET_REGISTRY_ONLY = "TARGET_REGISTRY_ONLY"
    SURFACE_BINDING_CATALOG_ONLY = "SURFACE_BINDING_CATALOG_ONLY"
    CAPABILITY_DESCRIPTOR_ONLY = "CAPABILITY_DESCRIPTOR_ONLY"
    ADAPTER_CONTRACT_ONLY = "ADAPTER_CONTRACT_ONLY"
    PROJECTION_CONSUMPTION_CONTRACT_ONLY = "PROJECTION_CONSUMPTION_CONTRACT_ONLY"
    READ_ONLY_COMMAND_SURFACE_ONLY = "READ_ONLY_COMMAND_SURFACE_ONLY"
    OUTPUT_DESCRIPTOR_ONLY = "OUTPUT_DESCRIPTOR_ONLY"
    RENDER_DESCRIPTOR_ONLY = "RENDER_DESCRIPTOR_ONLY"
    NO_COMMAND_EXECUTION_BOUNDARY = "NO_COMMAND_EXECUTION_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CLI_APP = "NOT_CLI_APP"
    NOT_CLI_RUNNER = "NOT_CLI_RUNNER"
    NOT_CLI_ENTRYPOINT = "NOT_CLI_ENTRYPOINT"
    NOT_TUI_RUNTIME = "NOT_TUI_RUNTIME"
    NOT_TUI_APP = "NOT_TUI_APP"
    NOT_SHELL_RUNTIME = "NOT_SHELL_RUNTIME"
    NOT_SHELL_EXECUTION_RUNTIME = "NOT_SHELL_EXECUTION_RUNTIME"
    NOT_COMMAND_PARSER = "NOT_COMMAND_PARSER"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_COMMAND_HANDLER = "NOT_COMMAND_HANDLER"
    NOT_COMMAND_INVOCATION = "NOT_COMMAND_INVOCATION"
    NOT_TOOL_INVOCATION = "NOT_TOOL_INVOCATION"
    NOT_WORKFLOW_DISPATCH = "NOT_WORKFLOW_DISPATCH"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_RUNTIME_BRIDGE = "NOT_RUNTIME_BRIDGE"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_NAVIGATION_MUTATION = "NOT_NAVIGATION_MUTATION"
    NOT_API_SERVER = "NOT_API_SERVER"
    NOT_HTTP_ROUTE = "NOT_HTTP_ROUTE"
    NOT_LIVE_ENDPOINT = "NOT_LIVE_ENDPOINT"
    NOT_EVENT_BUS = "NOT_EVENT_BUS"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PRODUCT_UI = "NOT_PRODUCT_UI"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"


@dataclass(frozen=True)
class P27ASideEffectProof(_CanonicalMixin):
    cli_app_created: bool = False
    cli_runner_created: bool = False
    cli_entrypoint_created: bool = False
    tui_runtime_created: bool = False
    tui_app_created: bool = False
    shell_runtime_created: bool = False
    shell_execution_runtime_created: bool = False
    command_parser_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    runtime_dispatch_created: bool = False
    runtime_bridge_created: bool = False
    runtime_mutated: bool = False
    surface_switch_created: bool = False
    navigation_mutation_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    live_endpoint_created: bool = False
    event_bus_created: bool = False
    trace_written: bool = False
    memory_written: bool = False
    storage_written: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    authorization_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    custos_integration_created: bool = False
    mneme_integration_created: bool = False
    product_ui_created: bool = False
    product_behavior_claimed: bool = False
    release_scope_claimed: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    p2_7_b_started: bool = False
    p2_8_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellBindingSectionGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_section_seal_result_ref: str
    dependency_binding_availability_ref: str
    dependency_no_live_infrastructure_proof_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellBindingSectionGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellBindingTargetEntry(_CanonicalMixin):
    entry_id: str
    target_id: str
    target_kind: str
    surface_id: str
    binding_mode: str
    capability_descriptor_ref: str
    adapter_contract_ref: str
    available_as_contract: bool
    available_as_runtime_binding: bool
    requires_future_pack: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellBindingTargetRegistry(_CanonicalMixin):
    registry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_version: str
    target_entries: tuple[ShellBindingTargetEntry, ...]
    surface_catalog_ref: str
    source_section_ref: str
    source_section_seal_ref: str
    official_surface_set: tuple[str, ...]
    is_source_of_truth: bool
    creates_surface_switch: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class ShellBindingSurfaceCatalog(_CanonicalMixin):
    catalog_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_surface_set: tuple[str, ...]
    binding_surface_kinds: tuple[str, ...]
    target_registry_ref: str
    is_live_surface_switcher: bool
    mutates_navigation: bool
    truth_label: str
    limitations: tuple[str, ...]
    catalog_hash: str


@dataclass(frozen=True)
class ShellBindingCapabilityDescriptor(_CanonicalMixin):
    capability_descriptor_id: str
    schema_version: str
    capability_kind: ShellBindingCapabilityKind
    capability_mode: ShellBindingCapabilityMode
    target_kind: str
    surface_scope: str
    available_as_contract: bool
    available_as_cli_app: bool
    available_as_tui_runtime: bool
    available_as_shell_runtime: bool
    executable: bool
    requires_future_pack: str
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellBindingAdapterContract(_CanonicalMixin):
    adapter_contract_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    adapter_kind: str
    source_projection_ref: str
    target_binding_ref: str
    projection_consumption_ref: str
    dispatches_runtime: bool
    creates_runtime_bridge: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    adapter_hash: str


@dataclass(frozen=True)
class ShellBindingProjectionConsumptionContract(_CanonicalMixin):
    projection_consumption_id: str
    schema_version: str
    source_pack: str
    source_section: str
    source_section_seal_ref: str
    source_read_model_ref: str
    source_contract_inventory_ref: str
    consumes_live_api: bool
    consumes_live_event_bridge: bool
    reads_runtime_state: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    consumption_hash: str


@dataclass(frozen=True)
class ShellBindingReadOnlyCommandSurface(_CanonicalMixin):
    command_surface_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    command_surface_mode: ShellBindingCommandSurfaceMode
    available_commands_as_descriptors: tuple[str, ...]
    executable_commands: tuple[str, ...]
    creates_command_parser: bool
    creates_command_router: bool
    creates_command_handler: bool
    executes_commands: bool
    truth_label: str
    limitations: tuple[str, ...]
    command_surface_hash: str


@dataclass(frozen=True)
class ShellBindingOutputDescriptor(_CanonicalMixin):
    output_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    output_kind: str
    source_binding_ref: str
    render_descriptor_ref: str
    is_product_ui: bool
    writes_output: bool
    requires_tui_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    output_hash: str


@dataclass(frozen=True)
class ShellBindingRenderDescriptor(_CanonicalMixin):
    render_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    render_kind: str
    render_mode: str
    target_surface: str
    is_tui_runtime: bool
    is_product_ui: bool
    requires_frontend: bool
    truth_label: str
    limitations: tuple[str, ...]
    render_hash: str


@dataclass(frozen=True)
class ShellBindingNoCommandExecutionBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    boundary_active: bool
    read_only_command_surface_ref: str
    prevents_command_parser: bool
    prevents_command_router: bool
    prevents_command_handler: bool
    prevents_command_execution: bool
    prevents_command_invocation: bool
    prevents_tool_invocation: bool
    prevents_workflow_dispatch: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellBindingNoRuntimeDispatchBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    boundary_active: bool
    adapter_contract_ref: str
    projection_consumption_ref: str
    prevents_runtime_dispatch: bool
    prevents_runtime_bridge: bool
    prevents_runtime_mutation: bool
    prevents_surface_switch: bool
    prevents_trace_write: bool
    prevents_memory_write: bool
    prevents_storage_write: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellBindingFoundationResult(_CanonicalMixin):
    binding_foundation_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    binding_section_gate: ShellBindingSectionGate
    target_registry: ShellBindingTargetRegistry
    surface_catalog: ShellBindingSurfaceCatalog
    capability_descriptors: tuple[ShellBindingCapabilityDescriptor, ...]
    adapter_contract: ShellBindingAdapterContract
    projection_consumption_contract: ShellBindingProjectionConsumptionContract
    read_only_command_surface: ShellBindingReadOnlyCommandSurface
    output_descriptor: ShellBindingOutputDescriptor
    render_descriptor: ShellBindingRenderDescriptor
    no_command_execution_boundary: ShellBindingNoCommandExecutionBoundary
    no_runtime_dispatch_boundary: ShellBindingNoRuntimeDispatchBoundary
    creates_cli_app: bool
    creates_cli_runner: bool
    creates_tui_runtime: bool
    creates_shell_runtime: bool
    creates_command_execution: bool
    creates_command_router: bool
    creates_command_handler: bool
    creates_tool_invocation: bool
    creates_workflow_dispatch: bool
    creates_runtime_dispatch: bool
    creates_runtime_bridge: bool
    creates_runtime_mutation: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    foundation_hash: str


@dataclass(frozen=True)
class P27AShellBindingFoundationResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_6_d_evidence_ref: str
    binding_section_gate: ShellBindingSectionGate
    target_registry: ShellBindingTargetRegistry
    surface_catalog: ShellBindingSurfaceCatalog
    capability_descriptors: tuple[ShellBindingCapabilityDescriptor, ...]
    adapter_contract: ShellBindingAdapterContract
    projection_consumption_contract: ShellBindingProjectionConsumptionContract
    read_only_command_surface: ShellBindingReadOnlyCommandSurface
    output_descriptor: ShellBindingOutputDescriptor
    render_descriptor: ShellBindingRenderDescriptor
    no_command_execution_boundary: ShellBindingNoCommandExecutionBoundary
    no_runtime_dispatch_boundary: ShellBindingNoRuntimeDispatchBoundary
    binding_foundation_result: ShellBindingFoundationResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P27ASideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _section_seal_result_ref(
    seal_result: P26DSurfaceProjectionSectionSealResult,
) -> str:
    seal = seal_result.section_seal_result
    return f"{seal.section_seal_result_id}:hash={seal.seal_result_hash[:12]}"


def _binding_availability_ref(
    seal_result: P26DSurfaceProjectionSectionSealResult,
) -> str:
    binding = seal_result.binding_availability
    return (
        f"{binding.binding_availability_id}:"
        f"status={binding.availability_status.value}"
    )


def _no_live_infrastructure_proof_ref(
    seal_result: P26DSurfaceProjectionSectionSealResult,
) -> str:
    proof = seal_result.no_live_infrastructure_proof
    return f"{proof.proof_id}:hash={proof.proof_hash[:12]}"


def assert_p2_6_d_section_seal_result_available(
    seal_result: P26DSurfaceProjectionSectionSealResult,
) -> None:
    if seal_result.pack_id != P2_6_D_PACK_ID or seal_result.starts_future_work:
        _reject(
            "P2.7-A requires P2.6-D section seal result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    binding = seal_result.binding_availability
    if binding.next_required_pack != P2_7_A_PACK_ID:
        _reject(
            "P2.7-A requires P2.6-D binding availability pointing to P2.7-A",
            field="next_required_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def build_shell_binding_section_gate(
    seal_result: P26DSurfaceProjectionSectionSealResult | None = None,
) -> ShellBindingSectionGate:
    if seal_result is None:
        seal_result = build_p2_6_d_surface_projection_section_seal_result()
    assert_p2_6_d_section_seal_result_available(seal_result)
    payload: dict[str, Any] = {
        "gate_id": "p2_7_a_shell_binding_section_gate",
        "schema_version": P2_7_A_GATE_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "official_section_name": P2_7_A_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_7_A_DEPENDENCY_PACK,
        "dependency_report_ref": P2_6_D_REPORT_PATH,
        "dependency_commit_ref": P2_6_D_COMMIT_REF,
        "dependency_validation_ref": P2_6_D_VALIDATION_REF,
        "dependency_section_seal_result_ref": _section_seal_result_ref(seal_result),
        "dependency_binding_availability_ref": _binding_availability_ref(seal_result),
        "dependency_no_live_infrastructure_proof_ref": _no_live_infrastructure_proof_ref(
            seal_result
        ),
        "dependency_side_effect_proof_ref": "P26DSideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellBindingSectionGateStatus.READY,
        "truth_label": ShellBindingTruthBoundary.BINDING_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create binding runtime",
        ),
    }
    gate = ShellBindingSectionGate(**payload, gate_hash=_hash_payload(payload))
    assert_binding_section_gate_depends_on_p2_6_d(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def _build_capability_descriptor(
    capability_kind: ShellBindingCapabilityKind,
    *,
    capability_mode: ShellBindingCapabilityMode = ShellBindingCapabilityMode.CONTRACT_ONLY,
    target_kind: str = "ALL",
    surface_scope: str = "ALL_SURFACES",
    requires_future_pack: str = "",
) -> ShellBindingCapabilityDescriptor:
    if capability_kind == ShellBindingCapabilityKind.DEV_FIXTURE_DESCRIPTOR:
        capability_mode = ShellBindingCapabilityMode.DEV_FIXTURE_ONLY
    if capability_kind == ShellBindingCapabilityKind.UNKNOWN_UNAVAILABLE:
        capability_mode = ShellBindingCapabilityMode.UNAVAILABLE
    payload: dict[str, Any] = {
        "capability_descriptor_id": (
            f"p2_7_a_capability_{capability_kind.value.lower()}"
        ),
        "schema_version": P2_7_A_CAPABILITY_VERSION,
        "capability_kind": capability_kind,
        "capability_mode": capability_mode,
        "target_kind": target_kind,
        "surface_scope": surface_scope,
        "available_as_contract": capability_mode
        in {
            ShellBindingCapabilityMode.CONTRACT_ONLY,
            ShellBindingCapabilityMode.READ_ONLY_DESCRIPTOR_ONLY,
            ShellBindingCapabilityMode.DEV_FIXTURE_ONLY,
        },
        "available_as_cli_app": False,
        "available_as_tui_runtime": False,
        "available_as_shell_runtime": False,
        "executable": False,
        "requires_future_pack": requires_future_pack,
        "truth_label": ShellBindingTruthBoundary.CAPABILITY_DESCRIPTOR_ONLY.value,
        "limitations": ("descriptor is not runtime", "executable remains unavailable"),
    }
    descriptor = ShellBindingCapabilityDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_cli_descriptor_is_not_cli_app(descriptor)
    assert_tui_descriptor_is_not_tui_runtime(descriptor)
    assert_shell_descriptor_is_not_shell_runtime(descriptor)
    return descriptor


def build_shell_binding_capability_descriptors() -> tuple[
    ShellBindingCapabilityDescriptor, ...
]:
    kinds = (
        ShellBindingCapabilityKind.SHELL_BINDING_DESCRIPTOR,
        ShellBindingCapabilityKind.CLI_BINDING_DESCRIPTOR,
        ShellBindingCapabilityKind.TUI_BINDING_DESCRIPTOR,
        ShellBindingCapabilityKind.READ_ONLY_COMMAND_SURFACE_DESCRIPTOR,
        ShellBindingCapabilityKind.OUTPUT_DESCRIPTOR,
        ShellBindingCapabilityKind.RENDER_DESCRIPTOR,
        ShellBindingCapabilityKind.DEV_FIXTURE_DESCRIPTOR,
        ShellBindingCapabilityKind.UNKNOWN_UNAVAILABLE,
    )
    return tuple(_build_capability_descriptor(kind) for kind in kinds)


def build_shell_binding_capability_descriptor(
    capability_kind: ShellBindingCapabilityKind | None = None,
) -> ShellBindingCapabilityDescriptor:
    kind = capability_kind or ShellBindingCapabilityKind.CLI_BINDING_DESCRIPTOR
    return _build_capability_descriptor(kind)


def _build_target_entry(
    surface_id: str,
    *,
    adapter_contract_ref: str,
) -> ShellBindingTargetEntry:
    payload: dict[str, Any] = {
        "entry_id": f"p2_7_a_binding_target_{surface_id}",
        "target_id": f"shell_binding_target:{surface_id}",
        "target_kind": "SHELL_CLI_TUI_CONTRACT",
        "surface_id": surface_id,
        "binding_mode": ShellBindingCapabilityMode.CONTRACT_ONLY.value,
        "capability_descriptor_ref": "p2_7_a_capability_shell_binding_descriptor",
        "adapter_contract_ref": adapter_contract_ref,
        "available_as_contract": True,
        "available_as_runtime_binding": False,
        "requires_future_pack": P2_7_A_NEXT_PACK,
        "truth_label": ShellBindingTruthBoundary.TARGET_REGISTRY_ONLY.value,
        "limitations": (
            "target entry is contract metadata only",
            "runtime binding deferred to P2.7-B+",
        ),
    }
    return ShellBindingTargetEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_binding_target_registry(
    adapter_contract_ref: str = "p2_7_a_shell_binding_adapter_contract",
    surface_catalog: ShellBindingSurfaceCatalog | None = None,
) -> ShellBindingTargetRegistry:
    if surface_catalog is None:
        surface_catalog = build_shell_binding_surface_catalog(
            target_registry_ref="p2_7_a_shell_binding_target_registry"
        )
    entries = tuple(
        _build_target_entry(
            surface_id,
            adapter_contract_ref=adapter_contract_ref,
        )
        for surface_id in CANONICAL_SURFACE_ORDER
    )
    payload: dict[str, Any] = {
        "registry_id": "p2_7_a_shell_binding_target_registry",
        "schema_version": P2_7_A_REGISTRY_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "official_section_name": P2_7_A_OFFICIAL_SECTION_NAME,
        "registry_version": P2_7_A_REGISTRY_VERSION,
        "target_entries": entries,
        "surface_catalog_ref": surface_catalog.catalog_id,
        "source_section_ref": "P2.6",
        "source_section_seal_ref": "SurfaceProjectionSectionSealResult",
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "is_source_of_truth": False,
        "creates_surface_switch": False,
        "truth_label": ShellBindingTruthBoundary.TARGET_REGISTRY_ONLY.value,
        "limitations": (
            "registry is not source-of-truth",
            "does not create surface switch",
        ),
    }
    registry = ShellBindingTargetRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_binding_target_registry_is_not_source_of_truth(registry)
    return registry


def build_shell_binding_surface_catalog(
    target_registry_ref: str = "p2_7_a_shell_binding_target_registry",
) -> ShellBindingSurfaceCatalog:
    payload: dict[str, Any] = {
        "catalog_id": "p2_7_a_shell_binding_surface_catalog",
        "schema_version": P2_7_A_CATALOG_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "binding_surface_kinds": _BINDING_SURFACE_KINDS,
        "target_registry_ref": target_registry_ref,
        "is_live_surface_switcher": False,
        "mutates_navigation": False,
        "truth_label": ShellBindingTruthBoundary.SURFACE_BINDING_CATALOG_ONLY.value,
        "limitations": (
            "catalog is not live surface switcher",
            "does not mutate navigation",
        ),
    }
    catalog = ShellBindingSurfaceCatalog(
        **payload,
        catalog_hash=_hash_payload(payload),
    )
    assert_surface_binding_catalog_is_not_surface_switcher(catalog)
    return catalog


def build_shell_binding_projection_consumption_contract(
    seal_result: P26DSurfaceProjectionSectionSealResult | None = None,
) -> ShellBindingProjectionConsumptionContract:
    if seal_result is None:
        seal_result = build_p2_6_d_surface_projection_section_seal_result()
    read_model = seal_result.section_read_model
    inventory = seal_result.contract_inventory
    payload: dict[str, Any] = {
        "projection_consumption_id": "p2_7_a_shell_binding_projection_consumption_contract",
        "schema_version": P2_7_A_PROJECTION_CONSUMPTION_VERSION,
        "source_pack": P2_6_D_PACK_ID,
        "source_section": "P2.6",
        "source_section_seal_ref": _section_seal_result_ref(seal_result),
        "source_read_model_ref": read_model.read_model_id,
        "source_contract_inventory_ref": inventory.inventory_id,
        "consumes_live_api": False,
        "consumes_live_event_bridge": False,
        "reads_runtime_state": False,
        "mutates_runtime": False,
        "truth_label": (
            ShellBindingTruthBoundary.PROJECTION_CONSUMPTION_CONTRACT_ONLY.value
        ),
        "limitations": (
            "consumption is by reference only",
            "does not consume live API or event bridge",
        ),
    }
    contract = ShellBindingProjectionConsumptionContract(
        **payload,
        consumption_hash=_hash_payload(payload),
    )
    assert_projection_consumption_is_not_live_bridge_consumption(contract)
    return contract


def build_shell_binding_adapter_contract(
    projection_consumption: ShellBindingProjectionConsumptionContract | None = None,
    target_registry_ref: str = "p2_7_a_shell_binding_target_registry",
) -> ShellBindingAdapterContract:
    if projection_consumption is None:
        projection_consumption = build_shell_binding_projection_consumption_contract()
    payload: dict[str, Any] = {
        "adapter_contract_id": "p2_7_a_shell_binding_adapter_contract",
        "schema_version": P2_7_A_ADAPTER_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "adapter_kind": "PROJECTION_TO_BINDING_DESCRIPTOR",
        "source_projection_ref": projection_consumption.source_read_model_ref,
        "target_binding_ref": target_registry_ref,
        "projection_consumption_ref": projection_consumption.projection_consumption_id,
        "dispatches_runtime": False,
        "creates_runtime_bridge": False,
        "mutates_runtime": False,
        "truth_label": ShellBindingTruthBoundary.ADAPTER_CONTRACT_ONLY.value,
        "limitations": (
            "adapter contract is not runtime dispatch adapter",
            "does not dispatch runtime or create bridge",
        ),
    }
    contract = ShellBindingAdapterContract(
        **payload,
        adapter_hash=_hash_payload(payload),
    )
    assert_adapter_contract_is_not_runtime_dispatch(contract)
    return contract


def build_shell_binding_read_only_command_surface() -> ShellBindingReadOnlyCommandSurface:
    payload: dict[str, Any] = {
        "command_surface_id": "p2_7_a_shell_binding_read_only_command_surface",
        "schema_version": P2_7_A_COMMAND_SURFACE_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "command_surface_mode": ShellBindingCommandSurfaceMode.READ_ONLY_CONTRACT,
        "available_commands_as_descriptors": (
            "inspect_binding_contract",
            "describe_capability_descriptor",
            "render_binding_summary",
        ),
        "executable_commands": (),
        "creates_command_parser": False,
        "creates_command_router": False,
        "creates_command_handler": False,
        "executes_commands": False,
        "truth_label": ShellBindingTruthBoundary.READ_ONLY_COMMAND_SURFACE_ONLY.value,
        "limitations": (
            "command names are descriptors only",
            "no parser/router/handler/execution",
        ),
    }
    surface = ShellBindingReadOnlyCommandSurface(
        **payload,
        command_surface_hash=_hash_payload(payload),
    )
    assert_command_surface_is_read_only(surface)
    return surface


def build_shell_binding_render_descriptor() -> ShellBindingRenderDescriptor:
    payload: dict[str, Any] = {
        "render_descriptor_id": "p2_7_a_shell_binding_render_descriptor",
        "schema_version": P2_7_A_RENDER_DESCRIPTOR_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "render_kind": "BINDING_CONTRACT_SUMMARY",
        "render_mode": ShellBindingCapabilityMode.CONTRACT_ONLY.value,
        "target_surface": "ALL_SURFACES",
        "is_tui_runtime": False,
        "is_product_ui": False,
        "requires_frontend": False,
        "truth_label": ShellBindingTruthBoundary.RENDER_DESCRIPTOR_ONLY.value,
        "limitations": (
            "render descriptor is not TUI runtime or product UI",
            "requires no frontend",
        ),
    }
    descriptor = ShellBindingRenderDescriptor(
        **payload,
        render_hash=_hash_payload(payload),
    )
    assert_render_descriptor_is_not_tui_runtime(descriptor)
    return descriptor


def build_shell_binding_output_descriptor(
    render_descriptor: ShellBindingRenderDescriptor | None = None,
) -> ShellBindingOutputDescriptor:
    if render_descriptor is None:
        render_descriptor = build_shell_binding_render_descriptor()
    payload: dict[str, Any] = {
        "output_descriptor_id": "p2_7_a_shell_binding_output_descriptor",
        "schema_version": P2_7_A_OUTPUT_DESCRIPTOR_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "output_kind": "BINDING_CONTRACT_OUTPUT",
        "source_binding_ref": "p2_7_a_shell_binding_adapter_contract",
        "render_descriptor_ref": render_descriptor.render_descriptor_id,
        "is_product_ui": False,
        "writes_output": False,
        "requires_tui_runtime": False,
        "truth_label": ShellBindingTruthBoundary.OUTPUT_DESCRIPTOR_ONLY.value,
        "limitations": (
            "output descriptor is not product UI",
            "does not require TUI runtime",
        ),
    }
    descriptor = ShellBindingOutputDescriptor(
        **payload,
        output_hash=_hash_payload(payload),
    )
    assert_output_descriptor_is_not_product_ui(descriptor)
    return descriptor


def build_shell_binding_no_command_execution_boundary(
    command_surface: ShellBindingReadOnlyCommandSurface | None = None,
) -> ShellBindingNoCommandExecutionBoundary:
    if command_surface is None:
        command_surface = build_shell_binding_read_only_command_surface()
    payload: dict[str, Any] = {
        "boundary_id": "p2_7_a_shell_binding_no_command_execution_boundary",
        "schema_version": P2_7_A_NO_COMMAND_EXECUTION_VERSION,
        "boundary_active": True,
        "read_only_command_surface_ref": command_surface.command_surface_id,
        "prevents_command_parser": True,
        "prevents_command_router": True,
        "prevents_command_handler": True,
        "prevents_command_execution": True,
        "prevents_command_invocation": True,
        "prevents_tool_invocation": True,
        "prevents_workflow_dispatch": True,
        "reason": _NO_COMMAND_EXECUTION_REASON,
        "truth_label": ShellBindingTruthBoundary.NO_COMMAND_EXECUTION_BOUNDARY.value,
        "limitations": (
            "boundary is contract firewall only",
            "not executor implementation",
        ),
    }
    boundary = ShellBindingNoCommandExecutionBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_command_execution_boundary_is_active(boundary)
    return boundary


def build_shell_binding_no_runtime_dispatch_boundary(
    adapter_contract: ShellBindingAdapterContract | None = None,
    projection_consumption: ShellBindingProjectionConsumptionContract | None = None,
) -> ShellBindingNoRuntimeDispatchBoundary:
    if adapter_contract is None:
        adapter_contract = build_shell_binding_adapter_contract()
    if projection_consumption is None:
        projection_consumption = build_shell_binding_projection_consumption_contract()
    payload: dict[str, Any] = {
        "boundary_id": "p2_7_a_shell_binding_no_runtime_dispatch_boundary",
        "schema_version": P2_7_A_NO_RUNTIME_DISPATCH_VERSION,
        "boundary_active": True,
        "adapter_contract_ref": adapter_contract.adapter_contract_id,
        "projection_consumption_ref": projection_consumption.projection_consumption_id,
        "prevents_runtime_dispatch": True,
        "prevents_runtime_bridge": True,
        "prevents_runtime_mutation": True,
        "prevents_surface_switch": True,
        "prevents_trace_write": True,
        "prevents_memory_write": True,
        "prevents_storage_write": True,
        "reason": _NO_RUNTIME_DISPATCH_REASON,
        "truth_label": ShellBindingTruthBoundary.NO_RUNTIME_DISPATCH_BOUNDARY.value,
        "limitations": (
            "boundary is contract firewall only",
            "not dispatcher implementation",
        ),
    }
    boundary = ShellBindingNoRuntimeDispatchBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_runtime_dispatch_boundary_is_active(boundary)
    return boundary


def build_shell_binding_foundation_result(
    seal_result: P26DSurfaceProjectionSectionSealResult | None = None,
) -> ShellBindingFoundationResult:
    if seal_result is None:
        seal_result = build_p2_6_d_surface_projection_section_seal_result()
    gate = build_shell_binding_section_gate(seal_result)
    projection_consumption = build_shell_binding_projection_consumption_contract(
        seal_result
    )
    adapter_contract = build_shell_binding_adapter_contract(projection_consumption)
    target_registry = build_shell_binding_target_registry(
        adapter_contract_ref=adapter_contract.adapter_contract_id,
    )
    surface_catalog = build_shell_binding_surface_catalog(
        target_registry_ref=target_registry.registry_id,
    )
    capability_descriptors = build_shell_binding_capability_descriptors()
    read_only_command_surface = build_shell_binding_read_only_command_surface()
    render_descriptor = build_shell_binding_render_descriptor()
    output_descriptor = build_shell_binding_output_descriptor(render_descriptor)
    no_command_execution_boundary = build_shell_binding_no_command_execution_boundary(
        read_only_command_surface
    )
    no_runtime_dispatch_boundary = build_shell_binding_no_runtime_dispatch_boundary(
        adapter_contract,
        projection_consumption,
    )
    payload: dict[str, Any] = {
        "binding_foundation_result_id": "p2_7_a_shell_binding_foundation_result",
        "schema_version": P2_7_A_FOUNDATION_RESULT_VERSION,
        "section_id": P2_7_A_SECTION_ID,
        "created_for_pack": P2_7_A_PACK_ID,
        "official_section_name": P2_7_A_OFFICIAL_SECTION_NAME,
        "binding_section_gate": gate,
        "target_registry": target_registry,
        "surface_catalog": surface_catalog,
        "capability_descriptors": capability_descriptors,
        "adapter_contract": adapter_contract,
        "projection_consumption_contract": projection_consumption,
        "read_only_command_surface": read_only_command_surface,
        "output_descriptor": output_descriptor,
        "render_descriptor": render_descriptor,
        "no_command_execution_boundary": no_command_execution_boundary,
        "no_runtime_dispatch_boundary": no_runtime_dispatch_boundary,
        "creates_cli_app": False,
        "creates_cli_runner": False,
        "creates_tui_runtime": False,
        "creates_shell_runtime": False,
        "creates_command_execution": False,
        "creates_command_router": False,
        "creates_command_handler": False,
        "creates_tool_invocation": False,
        "creates_workflow_dispatch": False,
        "creates_runtime_dispatch": False,
        "creates_runtime_bridge": False,
        "creates_runtime_mutation": False,
        "creates_product_behavior": False,
        "truth_label": ShellBindingTruthBoundary.BINDING_FOUNDATION_ONLY.value,
        "limitations": (
            "binding foundation is not operator-testable product behavior",
            "runtime binding deferred to P2.7-B+",
        ),
    }
    result = ShellBindingFoundationResult(
        **payload,
        foundation_hash=_hash_payload(payload),
    )
    assert_binding_contract_is_not_command_execution(result)
    return result


def build_p2_7_a_side_effect_proof() -> P27ASideEffectProof:
    return P27ASideEffectProof()


def build_p2_7_a_shell_binding_foundation_result() -> P27AShellBindingFoundationResult:
    seal_result = build_p2_6_d_surface_projection_section_seal_result()
    foundation = build_shell_binding_foundation_result(seal_result)
    side_effects = build_p2_7_a_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_7_A_RESULT_VERSION,
        "pack_id": P2_7_A_PACK_ID,
        "section_id": P2_7_A_SECTION_ID,
        "official_section_name": P2_7_A_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_7_A_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_7_A_DEPENDENCY_PACK,
        "p2_6_d_evidence_ref": (
            f"{P2_6_D_REPORT_PATH}:{seal_result.result_hash[:12]}"
        ),
        "binding_section_gate": foundation.binding_section_gate,
        "target_registry": foundation.target_registry,
        "surface_catalog": foundation.surface_catalog,
        "capability_descriptors": foundation.capability_descriptors,
        "adapter_contract": foundation.adapter_contract,
        "projection_consumption_contract": foundation.projection_consumption_contract,
        "read_only_command_surface": foundation.read_only_command_surface,
        "output_descriptor": foundation.output_descriptor,
        "render_descriptor": foundation.render_descriptor,
        "no_command_execution_boundary": foundation.no_command_execution_boundary,
        "no_runtime_dispatch_boundary": foundation.no_runtime_dispatch_boundary,
        "binding_foundation_result": foundation,
        "truth_labels": tuple(label.value for label in ShellBindingTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_7_A_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P27AShellBindingFoundationResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_7_a_does_not_start_future_work(result)
    assert_p2_7_a_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_7_a_result(
    result: P27AShellBindingFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_a_shell_binding_foundation_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_binding_contract_summary(
    result: P27AShellBindingFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_a_shell_binding_foundation_result()
    foundation = result.binding_foundation_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.binding_section_gate.gate_status.value}",
            f"targets={len(result.target_registry.target_entries)}",
            f"capabilities={len(result.capability_descriptors)}",
            f"next={result.next_pack}",
            f"cli_app={str(foundation.creates_cli_app).lower()}",
            f"tui_runtime={str(foundation.creates_tui_runtime).lower()}",
            f"command_execution={str(foundation.creates_command_execution).lower()}",
            f"runtime_dispatch={str(foundation.creates_runtime_dispatch).lower()}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


def assert_binding_section_gate_depends_on_p2_6_d(
    gate: ShellBindingSectionGate,
) -> None:
    if gate.dependency_pack != P2_7_A_DEPENDENCY_PACK or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.7-A binding gate must depend on passed P2.6-D repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_section_seal_result_ref
        or not gate.dependency_binding_availability_ref
        or not gate.dependency_no_live_infrastructure_proof_ref
        or not gate.dependency_side_effect_proof_ref
    ):
        _reject(
            "P2.7-A binding gate must reference P2.6-D section seal evidence",
            field="dependency_section_seal_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellBindingSectionGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.7-A gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_binding_target_registry_is_not_source_of_truth(
    registry: ShellBindingTargetRegistry,
) -> None:
    if registry.is_source_of_truth or registry.creates_surface_switch:
        _reject(
            "Binding target registry must not be source-of-truth or surface switcher",
            field="is_source_of_truth",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_surface_binding_catalog_is_not_surface_switcher(
    catalog: ShellBindingSurfaceCatalog,
) -> None:
    if catalog.is_live_surface_switcher or catalog.mutates_navigation:
        _reject(
            "Surface binding catalog must not switch surfaces or mutate navigation",
            field="is_live_surface_switcher",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_binding_contract_is_not_command_execution(
    foundation: ShellBindingFoundationResult,
) -> None:
    if any(
        (
            foundation.creates_cli_app,
            foundation.creates_cli_runner,
            foundation.creates_tui_runtime,
            foundation.creates_shell_runtime,
            foundation.creates_command_execution,
            foundation.creates_command_router,
            foundation.creates_command_handler,
            foundation.creates_tool_invocation,
            foundation.creates_workflow_dispatch,
            foundation.creates_runtime_dispatch,
            foundation.creates_runtime_bridge,
            foundation.creates_runtime_mutation,
            foundation.creates_product_behavior,
        )
    ):
        _reject(
            "Binding foundation must not create executable runtime behavior",
            field="creates_command_execution",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_cli_descriptor_is_not_cli_app(
    descriptor: ShellBindingCapabilityDescriptor,
) -> None:
    if descriptor.capability_kind == ShellBindingCapabilityKind.CLI_BINDING_DESCRIPTOR:
        if descriptor.available_as_cli_app or descriptor.executable:
            _reject(
                "CLI capability descriptor must not be CLI app",
                field="available_as_cli_app",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_tui_descriptor_is_not_tui_runtime(
    descriptor: ShellBindingCapabilityDescriptor,
) -> None:
    if descriptor.capability_kind == ShellBindingCapabilityKind.TUI_BINDING_DESCRIPTOR:
        if descriptor.available_as_tui_runtime or descriptor.executable:
            _reject(
                "TUI capability descriptor must not be TUI runtime",
                field="available_as_tui_runtime",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_shell_descriptor_is_not_shell_runtime(
    descriptor: ShellBindingCapabilityDescriptor,
) -> None:
    if descriptor.capability_kind == ShellBindingCapabilityKind.SHELL_BINDING_DESCRIPTOR:
        if descriptor.available_as_shell_runtime or descriptor.executable:
            _reject(
                "Shell capability descriptor must not be Shell execution runtime",
                field="available_as_shell_runtime",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_command_surface_is_read_only(
    surface: ShellBindingReadOnlyCommandSurface,
) -> None:
    if (
        surface.executes_commands
        or surface.creates_command_parser
        or surface.creates_command_router
        or surface.creates_command_handler
        or surface.executable_commands
    ):
        _reject(
            "Read-only command surface must not execute commands",
            field="executes_commands",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_adapter_contract_is_not_runtime_dispatch(
    contract: ShellBindingAdapterContract,
) -> None:
    if (
        contract.dispatches_runtime
        or contract.creates_runtime_bridge
        or contract.mutates_runtime
    ):
        _reject(
            "Adapter contract must not dispatch runtime",
            field="dispatches_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_consumption_is_not_live_bridge_consumption(
    contract: ShellBindingProjectionConsumptionContract,
) -> None:
    if (
        contract.consumes_live_api
        or contract.consumes_live_event_bridge
        or contract.reads_runtime_state
        or contract.mutates_runtime
    ):
        _reject(
            "Projection consumption must not consume live bridge or runtime state",
            field="consumes_live_api",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_output_descriptor_is_not_product_ui(
    descriptor: ShellBindingOutputDescriptor,
) -> None:
    if descriptor.is_product_ui or descriptor.requires_tui_runtime:
        _reject(
            "Output descriptor must not be product UI or require TUI runtime",
            field="is_product_ui",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_render_descriptor_is_not_tui_runtime(
    descriptor: ShellBindingRenderDescriptor,
) -> None:
    if descriptor.is_tui_runtime or descriptor.is_product_ui or descriptor.requires_frontend:
        _reject(
            "Render descriptor must not be TUI runtime or product UI",
            field="is_tui_runtime",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_command_execution_boundary_is_active(
    boundary: ShellBindingNoCommandExecutionBoundary,
) -> None:
    if not boundary.boundary_active or not all(
        (
            boundary.prevents_command_parser,
            boundary.prevents_command_router,
            boundary.prevents_command_handler,
            boundary.prevents_command_execution,
            boundary.prevents_command_invocation,
            boundary.prevents_tool_invocation,
            boundary.prevents_workflow_dispatch,
        )
    ):
        _reject(
            "No-command-execution boundary must be active with all prevents flags",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_runtime_dispatch_boundary_is_active(
    boundary: ShellBindingNoRuntimeDispatchBoundary,
) -> None:
    if not boundary.boundary_active or not all(
        (
            boundary.prevents_runtime_dispatch,
            boundary.prevents_runtime_bridge,
            boundary.prevents_runtime_mutation,
            boundary.prevents_surface_switch,
            boundary.prevents_trace_write,
            boundary.prevents_memory_write,
            boundary.prevents_storage_write,
        )
    ):
        _reject(
            "No-runtime-dispatch boundary must be active with all prevents flags",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_7_a_does_not_start_future_work(
    result: P27AShellBindingFoundationResult,
) -> None:
    proof = result.side_effect_proof
    if result.starts_future_work or any(
        (
            proof.p2_7_b_started,
            proof.p2_8_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.7-A must not start P2.7-B, P2.8, P2.10, or P2.13",
            field="starts_future_work",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_7_a_side_effects_all_false(proof: P27ASideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name) is not False:
            _reject(
                f"P2.7-A side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )

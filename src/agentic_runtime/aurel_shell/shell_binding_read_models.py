"""P2.7-B Shell binding read models / command surface adapter contracts.

Contract-only read-model and command surface adapter expansion over P2.7-A
binding foundation evidence. This module defines the binding read model gate,
read model registry/inventory, command descriptor read model, command surface
adapter read model, output/render preview schemas, binding context descriptor,
binding availability read model, binding selection descriptor, adapter
expansion result, side-effect proof, and pack result.

Core law:
  - Command descriptor is not command parser.
  - Command surface adapter read model is not command router.
  - Command surface adapter read model is not command handler.
  - Adapter expansion is not command execution.
  - Output preview is not output writer.
  - Render preview is not TUI runtime / product UI.
  - Binding context descriptor is not runtime context mutation.
  - Binding availability read model is not permission enforcement.
  - Binding selection descriptor is not operator confirmation / approval runtime.
  - Read model registry/inventory are not source-of-truth.
  - Projection/binding consumption is not live bridge consumption.

It does not create command parser/router/handler, command execution/invocation,
CLI app/runner/entrypoint, TUI runtime/app, Shell runtime/execution runtime,
output writer runtime, render runtime, product UI, operator confirmation
runtime, approval runtime, authorization, permission enforcement, Custos/Mneme
integration, tool invocation, workflow dispatch, runtime dispatch, runtime
bridge, runtime mutation, surface switching, navigation mutation, API server,
HTTP routes, live endpoint, event bus, trace/memory/storage writes,
source-of-truth store, product behavior, release scope, LIVE, TRACE_VERIFIED,
P2.7-C, P2.8, P2.10, or P2.13.
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
from .shell_binding_foundation import (
    P2_7_A_PACK_ID,
    P2_7_A_REPORT_PATH,
    P2_7_A_VALIDATION_REF,
    P27AShellBindingFoundationResult,
    build_p2_7_a_shell_binding_foundation_result,
)
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES

P2_7_B_PACK_ID = "P2.7-B"
P2_7_B_SECTION_ID = "P2.7"
P2_7_B_OFFICIAL_SECTION_NAME = "Shell / CLI / TUI Binding"
P2_7_B_DEPENDENCY_PACK = P2_7_A_PACK_ID
P2_7_B_NEXT_PACK = "P2.7-C"
P2_7_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.7.6",
    "P2.7.7",
    "P2.7.8",
    "P2.7.9",
    "P2.7.10",
)
P2_7_B_REPORT_FILENAME = "P2_7_B_SHELL_BINDING_READ_MODELS_COMMAND_SURFACE_ADAPTER.md"
P2_7_B_REPORT_PATH = f"agent/reports/{P2_7_B_REPORT_FILENAME}"

P2_7_A_COMMIT_REF = "e6f84da"

P2_7_B_GATE_VERSION = "p2_7_b_shell_binding_read_model_gate.v1"
P2_7_B_REGISTRY_VERSION = "p2_7_b_shell_binding_read_model_registry.v1"
P2_7_B_INVENTORY_VERSION = "p2_7_b_shell_binding_read_model_inventory.v1"
P2_7_B_COMMAND_DESCRIPTOR_VERSION = "p2_7_b_shell_command_descriptor_read_model.v1"
P2_7_B_ADAPTER_READ_MODEL_VERSION = "p2_7_b_shell_command_surface_adapter_read_model.v1"
P2_7_B_OUTPUT_PREVIEW_VERSION = "p2_7_b_shell_binding_output_preview_schema.v1"
P2_7_B_RENDER_PREVIEW_VERSION = "p2_7_b_shell_binding_render_preview_schema.v1"
P2_7_B_CONTEXT_DESCRIPTOR_VERSION = "p2_7_b_shell_binding_context_descriptor.v1"
P2_7_B_AVAILABILITY_VERSION = "p2_7_b_shell_binding_availability_read_model.v1"
P2_7_B_SELECTION_VERSION = "p2_7_b_shell_binding_selection_descriptor.v1"
P2_7_B_ADAPTER_EXPANSION_VERSION = "p2_7_b_shell_binding_adapter_expansion_result.v1"
P2_7_B_RESULT_VERSION = "p2_7_b_shell_binding_read_model_pack_result.v1"

P2_7_B_TEST_REF = "tests/aurel_shell/test_shell_binding_read_models.py"
P2_7_B_VALIDATION_REF = "agent/TESTS.md#P2.7-B"
P2_7_B_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_7_B_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_GATE_ID = "p2_7_b_shell_binding_read_model_gate"
_REGISTRY_ID = "p2_7_b_shell_binding_read_model_registry"
_INVENTORY_ID = "p2_7_b_shell_binding_read_model_inventory"
_COMMAND_DESCRIPTOR_ID = "p2_7_b_shell_command_descriptor_read_model"
_ADAPTER_READ_MODEL_ID = "p2_7_b_shell_command_surface_adapter_read_model"
_OUTPUT_PREVIEW_ID = "p2_7_b_shell_binding_output_preview_schema"
_RENDER_PREVIEW_ID = "p2_7_b_shell_binding_render_preview_schema"
_CONTEXT_DESCRIPTOR_ID = "p2_7_b_shell_binding_context_descriptor"
_AVAILABILITY_ID = "p2_7_b_shell_binding_availability_read_model"
_SELECTION_ID = "p2_7_b_shell_binding_selection_descriptor"
_ADAPTER_EXPANSION_ID = "p2_7_b_shell_binding_adapter_expansion_result"

# (read_model_id, read_model_kind, requires_future_pack)
_READ_MODEL_MANIFEST: tuple[tuple[str, str, str], ...] = (
    (_GATE_ID, "BINDING_READ_MODEL_GATE", ""),
    (_REGISTRY_ID, "BINDING_READ_MODEL_REGISTRY", ""),
    (_INVENTORY_ID, "BINDING_READ_MODEL_INVENTORY", ""),
    (_COMMAND_DESCRIPTOR_ID, "COMMAND_DESCRIPTOR_READ_MODEL", ""),
    (_ADAPTER_READ_MODEL_ID, "COMMAND_SURFACE_ADAPTER_READ_MODEL", ""),
    (_OUTPUT_PREVIEW_ID, "OUTPUT_PREVIEW_SCHEMA", ""),
    (_RENDER_PREVIEW_ID, "RENDER_PREVIEW_SCHEMA", ""),
    (_CONTEXT_DESCRIPTOR_ID, "CONTEXT_DESCRIPTOR", ""),
    (_AVAILABILITY_ID, "AVAILABILITY_READ_MODEL", P2_7_B_NEXT_PACK),
    (_SELECTION_ID, "SELECTION_DESCRIPTOR", P2_7_B_NEXT_PACK),
    (_ADAPTER_EXPANSION_ID, "ADAPTER_EXPANSION_RESULT", ""),
)

_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "command_execution",
    "command_parser",
    "command_router",
    "command_handler",
    "output_writer",
    "tui_runtime",
    "operator_confirmation",
    "approval_runtime",
    "permission_enforcement",
    "runtime_dispatch",
)


class ShellBindingReadModelGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellCommandDescriptorKind(str, Enum):
    BINDING_SUMMARY_DESCRIPTOR = "BINDING_SUMMARY_DESCRIPTOR"
    SURFACE_TARGET_DESCRIPTOR = "SURFACE_TARGET_DESCRIPTOR"
    READ_ONLY_COMMAND_DESCRIPTOR = "READ_ONLY_COMMAND_DESCRIPTOR"
    OUTPUT_PREVIEW_DESCRIPTOR = "OUTPUT_PREVIEW_DESCRIPTOR"
    RENDER_PREVIEW_DESCRIPTOR = "RENDER_PREVIEW_DESCRIPTOR"
    AVAILABILITY_DESCRIPTOR = "AVAILABILITY_DESCRIPTOR"
    SELECTION_DESCRIPTOR = "SELECTION_DESCRIPTOR"
    DEV_FIXTURE_DESCRIPTOR = "DEV_FIXTURE_DESCRIPTOR"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class ShellCommandSurfaceAdapterMode(str, Enum):
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DESCRIPTOR_ONLY = "DESCRIPTOR_ONLY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class ShellBindingAvailabilityReadModelStatus(str, Enum):
    CONTRACT_AVAILABLE = "CONTRACT_AVAILABLE"
    UNAVAILABLE_COMMAND_EXECUTION_REQUIRED = "UNAVAILABLE_COMMAND_EXECUTION_REQUIRED"
    UNAVAILABLE_P2_7_C_REQUIRED = "UNAVAILABLE_P2_7_C_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellBindingReadModelTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    BINDING_READ_MODEL_ONLY = "BINDING_READ_MODEL_ONLY"
    READ_MODEL_REGISTRY_ONLY = "READ_MODEL_REGISTRY_ONLY"
    READ_MODEL_INVENTORY_ONLY = "READ_MODEL_INVENTORY_ONLY"
    COMMAND_DESCRIPTOR_ONLY = "COMMAND_DESCRIPTOR_ONLY"
    COMMAND_SURFACE_ADAPTER_READ_MODEL_ONLY = "COMMAND_SURFACE_ADAPTER_READ_MODEL_ONLY"
    OUTPUT_PREVIEW_SCHEMA_ONLY = "OUTPUT_PREVIEW_SCHEMA_ONLY"
    RENDER_PREVIEW_SCHEMA_ONLY = "RENDER_PREVIEW_SCHEMA_ONLY"
    CONTEXT_DESCRIPTOR_ONLY = "CONTEXT_DESCRIPTOR_ONLY"
    AVAILABILITY_READ_MODEL_ONLY = "AVAILABILITY_READ_MODEL_ONLY"
    SELECTION_DESCRIPTOR_ONLY = "SELECTION_DESCRIPTOR_ONLY"
    ADAPTER_EXPANSION_RESULT_ONLY = "ADAPTER_EXPANSION_RESULT_ONLY"
    NO_COMMAND_EXECUTION_BOUNDARY = "NO_COMMAND_EXECUTION_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    BINDING_READ_MODEL_GATE_ONLY = "BINDING_READ_MODEL_GATE_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_COMMAND_PARSER = "NOT_COMMAND_PARSER"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_COMMAND_HANDLER = "NOT_COMMAND_HANDLER"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_COMMAND_INVOCATION = "NOT_COMMAND_INVOCATION"
    NOT_CLI_APP = "NOT_CLI_APP"
    NOT_CLI_RUNNER = "NOT_CLI_RUNNER"
    NOT_CLI_ENTRYPOINT = "NOT_CLI_ENTRYPOINT"
    NOT_TUI_RUNTIME = "NOT_TUI_RUNTIME"
    NOT_TUI_APP = "NOT_TUI_APP"
    NOT_SHELL_RUNTIME = "NOT_SHELL_RUNTIME"
    NOT_SHELL_EXECUTION_RUNTIME = "NOT_SHELL_EXECUTION_RUNTIME"
    NOT_OUTPUT_WRITER = "NOT_OUTPUT_WRITER"
    NOT_RENDER_RUNTIME = "NOT_RENDER_RUNTIME"
    NOT_PRODUCT_UI = "NOT_PRODUCT_UI"
    NOT_OPERATOR_CONFIRMATION = "NOT_OPERATOR_CONFIRMATION"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
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
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_RUNTIME_BINDING = "NOT_RUNTIME_BINDING"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class P27BSideEffectProof(_CanonicalMixin):
    cli_app_created: bool = False
    cli_runner_created: bool = False
    cli_entrypoint_created: bool = False
    tui_runtime_created: bool = False
    tui_app_created: bool = False
    shell_runtime_created: bool = False
    shell_execution_runtime_created: bool = False
    command_parser_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_execution_created: bool = False
    command_invocation_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    runtime_dispatch_created: bool = False
    runtime_bridge_created: bool = False
    runtime_mutated: bool = False
    surface_switch_created: bool = False
    navigation_mutation_created: bool = False
    output_writer_created: bool = False
    render_runtime_created: bool = False
    operator_confirmation_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    authorization_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    custos_integration_created: bool = False
    mneme_integration_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    live_endpoint_created: bool = False
    event_bus_created: bool = False
    trace_written: bool = False
    memory_written: bool = False
    storage_written: bool = False
    source_of_truth_created: bool = False
    product_ui_created: bool = False
    product_behavior_claimed: bool = False
    release_scope_claimed: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    p2_7_c_started: bool = False
    p2_8_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellBindingReadModelGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_binding_foundation_result_ref: str
    dependency_no_command_execution_boundary_ref: str
    dependency_no_runtime_dispatch_boundary_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellBindingReadModelGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellBindingReadModelEntry(_CanonicalMixin):
    entry_id: str
    read_model_id: str
    read_model_kind: str
    source_pack: str
    source_contract_ref: str
    available_as_read_model: bool
    available_as_runtime_binding: bool
    requires_future_pack: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellBindingReadModelRegistry(_CanonicalMixin):
    registry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_version: str
    read_model_entries: tuple[ShellBindingReadModelEntry, ...]
    inventory_ref: str
    source_pack_ref: str
    source_binding_foundation_ref: str
    official_surface_set: tuple[str, ...]
    is_source_of_truth: bool
    creates_runtime_binding: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class ShellBindingReadModelInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    inventory_version: str
    entries: tuple[str, ...]
    covered_checkpoints: tuple[str, ...]
    source_pack_refs: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    duplicates_source_of_truth: bool
    is_source_of_truth: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class ShellCommandDescriptorReadModel(_CanonicalMixin):
    command_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    descriptor_kind: ShellCommandDescriptorKind
    descriptor_name: str
    descriptor_summary: str
    source_binding_ref: str
    command_surface_ref: str
    available_as_descriptor: bool
    available_as_parser: bool
    executable: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellCommandSurfaceAdapterReadModel(_CanonicalMixin):
    adapter_read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    adapter_mode: ShellCommandSurfaceAdapterMode
    source_command_descriptor_ref: str
    target_surface_ref: str
    output_preview_ref: str
    render_preview_ref: str
    is_command_router: bool
    is_command_handler: bool
    executes_commands: bool
    truth_label: str
    limitations: tuple[str, ...]
    adapter_hash: str


@dataclass(frozen=True)
class ShellBindingOutputPreviewSchema(_CanonicalMixin):
    output_preview_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    preview_kind: str
    source_descriptor_ref: str
    preview_fields: tuple[str, ...]
    writes_output: bool
    creates_output_writer: bool
    truth_label: str
    limitations: tuple[str, ...]
    output_hash: str


@dataclass(frozen=True)
class ShellBindingRenderPreviewSchema(_CanonicalMixin):
    render_preview_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    render_preview_kind: str
    render_mode: str
    target_surface: str
    requires_tui_runtime: bool
    creates_render_runtime: bool
    is_product_ui: bool
    requires_frontend: bool
    truth_label: str
    limitations: tuple[str, ...]
    render_hash: str


@dataclass(frozen=True)
class ShellBindingContextDescriptor(_CanonicalMixin):
    context_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    context_scope: str
    source_binding_ref: str
    context_fields: tuple[str, ...]
    reads_runtime_context: bool
    mutates_runtime_context: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    context_hash: str


@dataclass(frozen=True)
class ShellBindingAvailabilityReadModel(_CanonicalMixin):
    availability_read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    availability_status: ShellBindingAvailabilityReadModelStatus
    available_contracts: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    blocked_capabilities: tuple[str, ...]
    future_pack_refs: tuple[str, ...]
    grants_permission: bool
    denies_permission: bool
    enforces_permission: bool
    activates_approval: bool
    truth_label: str
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class ShellBindingSelectionDescriptor(_CanonicalMixin):
    selection_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    selection_scope: str
    selectable_descriptor_refs: tuple[str, ...]
    selection_mode: str
    creates_operator_confirmation: bool
    creates_approval_runtime: bool
    executes_selection: bool
    truth_label: str
    limitations: tuple[str, ...]
    selection_hash: str


@dataclass(frozen=True)
class ShellBindingAdapterExpansionResult(_CanonicalMixin):
    adapter_expansion_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    read_model_gate: ShellBindingReadModelGate
    read_model_registry: ShellBindingReadModelRegistry
    read_model_inventory: ShellBindingReadModelInventory
    command_descriptor_read_model: ShellCommandDescriptorReadModel
    command_surface_adapter_read_model: ShellCommandSurfaceAdapterReadModel
    output_preview_schema: ShellBindingOutputPreviewSchema
    render_preview_schema: ShellBindingRenderPreviewSchema
    context_descriptor: ShellBindingContextDescriptor
    availability_read_model: ShellBindingAvailabilityReadModel
    selection_descriptor: ShellBindingSelectionDescriptor
    creates_command_parser: bool
    creates_command_router: bool
    creates_command_handler: bool
    creates_command_execution: bool
    creates_output_writer: bool
    creates_tui_runtime: bool
    creates_operator_confirmation: bool
    creates_permission_enforcement: bool
    creates_runtime_dispatch: bool
    creates_runtime_mutation: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    expansion_hash: str


@dataclass(frozen=True)
class P27BShellBindingReadModelResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_7_a_evidence_ref: str
    read_model_gate: ShellBindingReadModelGate
    read_model_registry: ShellBindingReadModelRegistry
    read_model_inventory: ShellBindingReadModelInventory
    command_descriptor_read_model: ShellCommandDescriptorReadModel
    command_surface_adapter_read_model: ShellCommandSurfaceAdapterReadModel
    output_preview_schema: ShellBindingOutputPreviewSchema
    render_preview_schema: ShellBindingRenderPreviewSchema
    context_descriptor: ShellBindingContextDescriptor
    availability_read_model: ShellBindingAvailabilityReadModel
    selection_descriptor: ShellBindingSelectionDescriptor
    adapter_expansion_result: ShellBindingAdapterExpansionResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P27BSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


# ---------------------------------------------------------------------------
# P2.7-A evidence reuse (by reference only — no source-of-truth duplication)
# ---------------------------------------------------------------------------


def _foundation_result_ref(result: P27AShellBindingFoundationResult) -> str:
    foundation = result.binding_foundation_result
    return (
        f"{foundation.binding_foundation_result_id}:"
        f"hash={foundation.foundation_hash[:12]}"
    )


def _no_command_execution_boundary_ref(result: P27AShellBindingFoundationResult) -> str:
    boundary = result.no_command_execution_boundary
    return f"{boundary.boundary_id}:hash={boundary.boundary_hash[:12]}"


def _no_runtime_dispatch_boundary_ref(result: P27AShellBindingFoundationResult) -> str:
    boundary = result.no_runtime_dispatch_boundary
    return f"{boundary.boundary_id}:hash={boundary.boundary_hash[:12]}"


def _p2_7_a_evidence_ref(result: P27AShellBindingFoundationResult) -> str:
    return f"{P2_7_A_REPORT_PATH}:{result.result_hash[:12]}"


def assert_p2_7_a_foundation_result_available(
    result: P27AShellBindingFoundationResult,
) -> None:
    if result.pack_id != P2_7_A_PACK_ID or result.starts_future_work:
        _reject(
            "P2.7-B requires a P2.7-A foundation result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.next_pack != P2_7_B_PACK_ID:
        _reject(
            "P2.7-B requires P2.7-A foundation pointing to P2.7-B",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_shell_binding_read_model_gate(
    foundation_result: P27AShellBindingFoundationResult | None = None,
) -> ShellBindingReadModelGate:
    if foundation_result is None:
        foundation_result = build_p2_7_a_shell_binding_foundation_result()
    assert_p2_7_a_foundation_result_available(foundation_result)
    payload: dict[str, Any] = {
        "gate_id": _GATE_ID,
        "schema_version": P2_7_B_GATE_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "official_section_name": P2_7_B_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_7_B_DEPENDENCY_PACK,
        "dependency_report_ref": P2_7_A_REPORT_PATH,
        "dependency_commit_ref": P2_7_A_COMMIT_REF,
        "dependency_validation_ref": P2_7_A_VALIDATION_REF,
        "dependency_binding_foundation_result_ref": _foundation_result_ref(
            foundation_result
        ),
        "dependency_no_command_execution_boundary_ref": (
            _no_command_execution_boundary_ref(foundation_result)
        ),
        "dependency_no_runtime_dispatch_boundary_ref": (
            _no_runtime_dispatch_boundary_ref(foundation_result)
        ),
        "dependency_side_effect_proof_ref": "P27ASideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellBindingReadModelGateStatus.READY,
        "truth_label": ShellBindingReadModelTruthBoundary.BINDING_READ_MODEL_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create binding runtime or runtime binding",
        ),
    }
    gate = ShellBindingReadModelGate(**payload, gate_hash=_hash_payload(payload))
    assert_read_model_gate_depends_on_p2_7_a(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def _build_read_model_entry(
    read_model_id: str,
    read_model_kind: str,
    requires_future_pack: str,
    *,
    source_contract_ref: str,
) -> ShellBindingReadModelEntry:
    payload: dict[str, Any] = {
        "entry_id": f"p2_7_b_entry_{read_model_id}",
        "read_model_id": read_model_id,
        "read_model_kind": read_model_kind,
        "source_pack": P2_7_B_PACK_ID,
        "source_contract_ref": source_contract_ref,
        "available_as_read_model": True,
        "available_as_runtime_binding": False,
        "requires_future_pack": requires_future_pack,
        "truth_label": ShellBindingReadModelTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": (
            "entry is read-model metadata only",
            "runtime binding deferred to P2.7-C+",
        ),
    }
    return ShellBindingReadModelEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_binding_read_model_registry(
    foundation_result: P27AShellBindingFoundationResult | None = None,
) -> ShellBindingReadModelRegistry:
    if foundation_result is None:
        foundation_result = build_p2_7_a_shell_binding_foundation_result()
    source_contract_ref = _foundation_result_ref(foundation_result)
    entries = tuple(
        _build_read_model_entry(
            read_model_id,
            read_model_kind,
            requires_future_pack,
            source_contract_ref=source_contract_ref,
        )
        for read_model_id, read_model_kind, requires_future_pack in _READ_MODEL_MANIFEST
    )
    payload: dict[str, Any] = {
        "registry_id": _REGISTRY_ID,
        "schema_version": P2_7_B_REGISTRY_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "official_section_name": P2_7_B_OFFICIAL_SECTION_NAME,
        "registry_version": P2_7_B_REGISTRY_VERSION,
        "read_model_entries": entries,
        "inventory_ref": _INVENTORY_ID,
        "source_pack_ref": P2_7_A_PACK_ID,
        "source_binding_foundation_ref": source_contract_ref,
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "is_source_of_truth": False,
        "creates_runtime_binding": False,
        "truth_label": ShellBindingReadModelTruthBoundary.READ_MODEL_REGISTRY_ONLY.value,
        "limitations": (
            "registry is not source-of-truth",
            "registry does not create runtime binding",
        ),
    }
    registry = ShellBindingReadModelRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_read_model_registry_is_not_source_of_truth(registry)
    return registry


def build_shell_binding_read_model_inventory() -> ShellBindingReadModelInventory:
    entries = tuple(read_model_id for read_model_id, _kind, _pack in _READ_MODEL_MANIFEST)
    payload: dict[str, Any] = {
        "inventory_id": _INVENTORY_ID,
        "schema_version": P2_7_B_INVENTORY_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "inventory_version": P2_7_B_INVENTORY_VERSION,
        "entries": entries,
        "covered_checkpoints": P2_7_B_PACK_CHECKPOINT_IDS,
        "source_pack_refs": (P2_7_A_PACK_ID, P2_7_B_PACK_ID),
        "source_report_refs": (P2_7_A_REPORT_PATH, P2_7_B_REPORT_PATH),
        "duplicates_source_of_truth": False,
        "is_source_of_truth": False,
        "truth_label": ShellBindingReadModelTruthBoundary.READ_MODEL_INVENTORY_ONLY.value,
        "limitations": (
            "inventory does not duplicate source-of-truth",
            "inventory is a read-model manifest, not authority",
        ),
    }
    inventory = ShellBindingReadModelInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    assert_read_model_inventory_does_not_duplicate_source_of_truth(inventory)
    return inventory


def _build_command_descriptor_read_model(
    descriptor_kind: ShellCommandDescriptorKind,
) -> ShellCommandDescriptorReadModel:
    payload: dict[str, Any] = {
        "command_descriptor_id": (
            f"{_COMMAND_DESCRIPTOR_ID}_{descriptor_kind.value.lower()}"
        ),
        "schema_version": P2_7_B_COMMAND_DESCRIPTOR_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "descriptor_kind": descriptor_kind,
        "descriptor_name": descriptor_kind.value.lower(),
        "descriptor_summary": (
            f"read-only command descriptor for {descriptor_kind.value}"
        ),
        "source_binding_ref": "p2_7_a_shell_binding_read_only_command_surface",
        "command_surface_ref": "p2_7_a_shell_binding_read_only_command_surface",
        "available_as_descriptor": True,
        "available_as_parser": False,
        "executable": False,
        "truth_label": ShellBindingReadModelTruthBoundary.COMMAND_DESCRIPTOR_ONLY.value,
        "limitations": (
            "command descriptor is not a command parser",
            "descriptor is not executable",
        ),
    }
    descriptor = ShellCommandDescriptorReadModel(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_command_descriptor_is_not_command_parser(descriptor)
    return descriptor


def build_shell_command_descriptor_read_model(
    descriptor_kind: ShellCommandDescriptorKind | None = None,
) -> ShellCommandDescriptorReadModel:
    kind = descriptor_kind or ShellCommandDescriptorKind.READ_ONLY_COMMAND_DESCRIPTOR
    return _build_command_descriptor_read_model(kind)


def build_shell_command_descriptor_read_models() -> tuple[
    ShellCommandDescriptorReadModel, ...
]:
    return tuple(
        _build_command_descriptor_read_model(kind)
        for kind in ShellCommandDescriptorKind
    )


def build_shell_binding_output_preview_schema(
    source_descriptor_ref: str | None = None,
) -> ShellBindingOutputPreviewSchema:
    payload: dict[str, Any] = {
        "output_preview_id": _OUTPUT_PREVIEW_ID,
        "schema_version": P2_7_B_OUTPUT_PREVIEW_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "preview_kind": "BINDING_COMMAND_OUTPUT_PREVIEW",
        "source_descriptor_ref": (
            source_descriptor_ref
            or f"{_COMMAND_DESCRIPTOR_ID}_read_only_command_descriptor"
        ),
        "preview_fields": (
            "binding_summary",
            "surface_target",
            "read_only_command",
            "availability_status",
        ),
        "writes_output": False,
        "creates_output_writer": False,
        "truth_label": ShellBindingReadModelTruthBoundary.OUTPUT_PREVIEW_SCHEMA_ONLY.value,
        "limitations": (
            "output preview is a schema only",
            "preview does not write output or create an output writer",
        ),
    }
    preview = ShellBindingOutputPreviewSchema(
        **payload,
        output_hash=_hash_payload(payload),
    )
    assert_output_preview_is_not_output_writer(preview)
    return preview


def build_shell_binding_render_preview_schema() -> ShellBindingRenderPreviewSchema:
    payload: dict[str, Any] = {
        "render_preview_id": _RENDER_PREVIEW_ID,
        "schema_version": P2_7_B_RENDER_PREVIEW_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "render_preview_kind": "BINDING_COMMAND_RENDER_PREVIEW",
        "render_mode": ShellCommandSurfaceAdapterMode.READ_MODEL_ONLY.value,
        "target_surface": "ALL_SURFACES",
        "requires_tui_runtime": False,
        "creates_render_runtime": False,
        "is_product_ui": False,
        "requires_frontend": False,
        "truth_label": ShellBindingReadModelTruthBoundary.RENDER_PREVIEW_SCHEMA_ONLY.value,
        "limitations": (
            "render preview is a schema only",
            "preview is not TUI runtime, render runtime, or product UI",
        ),
    }
    preview = ShellBindingRenderPreviewSchema(
        **payload,
        render_hash=_hash_payload(payload),
    )
    assert_render_preview_is_not_tui_runtime(preview)
    assert_render_preview_is_not_product_ui(preview)
    return preview


def build_shell_command_surface_adapter_read_model(
    source_command_descriptor_ref: str | None = None,
    output_preview: ShellBindingOutputPreviewSchema | None = None,
    render_preview: ShellBindingRenderPreviewSchema | None = None,
) -> ShellCommandSurfaceAdapterReadModel:
    if output_preview is None:
        output_preview = build_shell_binding_output_preview_schema()
    if render_preview is None:
        render_preview = build_shell_binding_render_preview_schema()
    payload: dict[str, Any] = {
        "adapter_read_model_id": _ADAPTER_READ_MODEL_ID,
        "schema_version": P2_7_B_ADAPTER_READ_MODEL_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "adapter_mode": ShellCommandSurfaceAdapterMode.READ_MODEL_ONLY,
        "source_command_descriptor_ref": (
            source_command_descriptor_ref
            or f"{_COMMAND_DESCRIPTOR_ID}_read_only_command_descriptor"
        ),
        "target_surface_ref": "ALL_SURFACES",
        "output_preview_ref": output_preview.output_preview_id,
        "render_preview_ref": render_preview.render_preview_id,
        "is_command_router": False,
        "is_command_handler": False,
        "executes_commands": False,
        "truth_label": (
            ShellBindingReadModelTruthBoundary.COMMAND_SURFACE_ADAPTER_READ_MODEL_ONLY.value
        ),
        "limitations": (
            "adapter read model is a route shape only",
            "adapter is not a command router, handler, or executor",
        ),
    }
    adapter = ShellCommandSurfaceAdapterReadModel(
        **payload,
        adapter_hash=_hash_payload(payload),
    )
    assert_adapter_read_model_is_not_command_router(adapter)
    assert_adapter_read_model_is_not_command_handler(adapter)
    return adapter


def build_shell_binding_context_descriptor(
    foundation_result: P27AShellBindingFoundationResult | None = None,
) -> ShellBindingContextDescriptor:
    if foundation_result is None:
        foundation_result = build_p2_7_a_shell_binding_foundation_result()
    payload: dict[str, Any] = {
        "context_descriptor_id": _CONTEXT_DESCRIPTOR_ID,
        "schema_version": P2_7_B_CONTEXT_DESCRIPTOR_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "context_scope": "SHELL_BINDING_READ_MODEL",
        "source_binding_ref": _foundation_result_ref(foundation_result),
        "context_fields": (
            "section_id",
            "official_section_name",
            "dependency_pack",
            "covered_checkpoints",
        ),
        "reads_runtime_context": False,
        "mutates_runtime_context": False,
        "mutates_runtime": False,
        "truth_label": ShellBindingReadModelTruthBoundary.CONTEXT_DESCRIPTOR_ONLY.value,
        "limitations": (
            "context descriptor is descriptor-only",
            "descriptor does not read or mutate runtime context",
        ),
    }
    descriptor = ShellBindingContextDescriptor(
        **payload,
        context_hash=_hash_payload(payload),
    )
    assert_context_descriptor_does_not_mutate_runtime_context(descriptor)
    return descriptor


def build_shell_binding_availability_read_model(
    availability_status: ShellBindingAvailabilityReadModelStatus | None = None,
) -> ShellBindingAvailabilityReadModel:
    status = availability_status or ShellBindingAvailabilityReadModelStatus.CONTRACT_AVAILABLE
    available_contracts = tuple(
        read_model_id
        for read_model_id, _kind, requires_future_pack in _READ_MODEL_MANIFEST
        if not requires_future_pack
    )
    payload: dict[str, Any] = {
        "availability_read_model_id": _AVAILABILITY_ID,
        "schema_version": P2_7_B_AVAILABILITY_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "availability_status": status,
        "available_contracts": available_contracts,
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "blocked_capabilities": (),
        "future_pack_refs": (P2_7_B_NEXT_PACK,),
        "grants_permission": False,
        "denies_permission": False,
        "enforces_permission": False,
        "activates_approval": False,
        "truth_label": ShellBindingReadModelTruthBoundary.AVAILABILITY_READ_MODEL_ONLY.value,
        "limitations": (
            "availability read model reports contract availability only",
            "model does not grant, deny, enforce permission, or activate approval",
        ),
    }
    availability = ShellBindingAvailabilityReadModel(
        **payload,
        availability_hash=_hash_payload(payload),
    )
    assert_availability_read_model_is_not_permission_enforcement(availability)
    return availability


def build_shell_binding_selection_descriptor() -> ShellBindingSelectionDescriptor:
    selectable_descriptor_refs = tuple(
        read_model_id for read_model_id, _kind, _pack in _READ_MODEL_MANIFEST
    )
    payload: dict[str, Any] = {
        "selection_descriptor_id": _SELECTION_ID,
        "schema_version": P2_7_B_SELECTION_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "selection_scope": "SHELL_BINDING_READ_MODEL",
        "selectable_descriptor_refs": selectable_descriptor_refs,
        "selection_mode": ShellCommandSurfaceAdapterMode.DESCRIPTOR_ONLY.value,
        "creates_operator_confirmation": False,
        "creates_approval_runtime": False,
        "executes_selection": False,
        "truth_label": ShellBindingReadModelTruthBoundary.SELECTION_DESCRIPTOR_ONLY.value,
        "limitations": (
            "selection descriptor is an intent shape only",
            "descriptor is not operator confirmation or approval runtime",
        ),
    }
    selection = ShellBindingSelectionDescriptor(
        **payload,
        selection_hash=_hash_payload(payload),
    )
    assert_selection_descriptor_is_not_operator_confirmation(selection)
    return selection


def build_shell_binding_adapter_expansion_result(
    foundation_result: P27AShellBindingFoundationResult | None = None,
) -> ShellBindingAdapterExpansionResult:
    if foundation_result is None:
        foundation_result = build_p2_7_a_shell_binding_foundation_result()
    gate = build_shell_binding_read_model_gate(foundation_result)
    registry = build_shell_binding_read_model_registry(foundation_result)
    inventory = build_shell_binding_read_model_inventory()
    command_descriptor = build_shell_command_descriptor_read_model()
    output_preview = build_shell_binding_output_preview_schema(
        source_descriptor_ref=command_descriptor.command_descriptor_id
    )
    render_preview = build_shell_binding_render_preview_schema()
    adapter_read_model = build_shell_command_surface_adapter_read_model(
        source_command_descriptor_ref=command_descriptor.command_descriptor_id,
        output_preview=output_preview,
        render_preview=render_preview,
    )
    context_descriptor = build_shell_binding_context_descriptor(foundation_result)
    availability_read_model = build_shell_binding_availability_read_model()
    selection_descriptor = build_shell_binding_selection_descriptor()
    payload: dict[str, Any] = {
        "adapter_expansion_result_id": _ADAPTER_EXPANSION_ID,
        "schema_version": P2_7_B_ADAPTER_EXPANSION_VERSION,
        "section_id": P2_7_B_SECTION_ID,
        "created_for_pack": P2_7_B_PACK_ID,
        "official_section_name": P2_7_B_OFFICIAL_SECTION_NAME,
        "read_model_gate": gate,
        "read_model_registry": registry,
        "read_model_inventory": inventory,
        "command_descriptor_read_model": command_descriptor,
        "command_surface_adapter_read_model": adapter_read_model,
        "output_preview_schema": output_preview,
        "render_preview_schema": render_preview,
        "context_descriptor": context_descriptor,
        "availability_read_model": availability_read_model,
        "selection_descriptor": selection_descriptor,
        "creates_command_parser": False,
        "creates_command_router": False,
        "creates_command_handler": False,
        "creates_command_execution": False,
        "creates_output_writer": False,
        "creates_tui_runtime": False,
        "creates_operator_confirmation": False,
        "creates_permission_enforcement": False,
        "creates_runtime_dispatch": False,
        "creates_runtime_mutation": False,
        "creates_product_behavior": False,
        "truth_label": ShellBindingReadModelTruthBoundary.ADAPTER_EXPANSION_RESULT_ONLY.value,
        "limitations": (
            "adapter expansion result bundles read models only",
            "result creates no execution, runtime, or product behavior",
        ),
    }
    result = ShellBindingAdapterExpansionResult(
        **payload,
        expansion_hash=_hash_payload(payload),
    )
    assert_adapter_expansion_result_is_not_command_execution(result)
    return result


def build_p2_7_b_side_effect_proof() -> P27BSideEffectProof:
    return P27BSideEffectProof()


def build_p2_7_b_shell_binding_read_model_result() -> P27BShellBindingReadModelResult:
    foundation_result = build_p2_7_a_shell_binding_foundation_result()
    expansion = build_shell_binding_adapter_expansion_result(foundation_result)
    side_effects = build_p2_7_b_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_7_B_RESULT_VERSION,
        "pack_id": P2_7_B_PACK_ID,
        "section_id": P2_7_B_SECTION_ID,
        "official_section_name": P2_7_B_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_7_B_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_7_B_DEPENDENCY_PACK,
        "p2_7_a_evidence_ref": _p2_7_a_evidence_ref(foundation_result),
        "read_model_gate": expansion.read_model_gate,
        "read_model_registry": expansion.read_model_registry,
        "read_model_inventory": expansion.read_model_inventory,
        "command_descriptor_read_model": expansion.command_descriptor_read_model,
        "command_surface_adapter_read_model": expansion.command_surface_adapter_read_model,
        "output_preview_schema": expansion.output_preview_schema,
        "render_preview_schema": expansion.render_preview_schema,
        "context_descriptor": expansion.context_descriptor,
        "availability_read_model": expansion.availability_read_model,
        "selection_descriptor": expansion.selection_descriptor,
        "adapter_expansion_result": expansion,
        "truth_labels": tuple(
            label.value for label in ShellBindingReadModelTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_7_B_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P27BShellBindingReadModelResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_7_b_does_not_start_future_work(result)
    assert_p2_7_b_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_7_b_result(
    result: P27BShellBindingReadModelResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_b_shell_binding_read_model_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_binding_read_model_summary(
    result: P27BShellBindingReadModelResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_b_shell_binding_read_model_result()
    expansion = result.adapter_expansion_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.read_model_gate.gate_status.value}",
            f"read_models={len(result.read_model_registry.read_model_entries)}",
            f"checkpoints={len(result.covered_checkpoints)}",
            f"next={result.next_pack}",
            f"command_parser={str(expansion.creates_command_parser).lower()}",
            f"command_router={str(expansion.creates_command_router).lower()}",
            f"command_handler={str(expansion.creates_command_handler).lower()}",
            f"command_execution={str(expansion.creates_command_execution).lower()}",
            f"output_writer={str(expansion.creates_output_writer).lower()}",
            f"tui_runtime={str(expansion.creates_tui_runtime).lower()}",
            f"operator_confirmation={str(expansion.creates_operator_confirmation).lower()}",
            f"permission_enforcement={str(expansion.creates_permission_enforcement).lower()}",
            f"runtime_dispatch={str(expansion.creates_runtime_dispatch).lower()}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


def assert_read_model_gate_depends_on_p2_7_a(gate: ShellBindingReadModelGate) -> None:
    if gate.dependency_pack != P2_7_B_DEPENDENCY_PACK or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.7-B read model gate must depend on passed P2.7-A repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_binding_foundation_result_ref
        or not gate.dependency_no_command_execution_boundary_ref
        or not gate.dependency_no_runtime_dispatch_boundary_ref
        or not gate.dependency_side_effect_proof_ref
    ):
        _reject(
            "P2.7-B read model gate must reference P2.7-A binding foundation evidence",
            field="dependency_binding_foundation_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellBindingReadModelGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.7-B gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_read_model_registry_is_not_source_of_truth(
    registry: ShellBindingReadModelRegistry,
) -> None:
    if registry.is_source_of_truth or registry.creates_runtime_binding:
        _reject(
            "Read model registry must not be source-of-truth or create runtime binding",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_read_model_inventory_does_not_duplicate_source_of_truth(
    inventory: ShellBindingReadModelInventory,
) -> None:
    if inventory.is_source_of_truth or inventory.duplicates_source_of_truth:
        _reject(
            "Read model inventory must not be or duplicate source-of-truth",
            field="duplicates_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_command_descriptor_is_not_command_parser(
    descriptor: ShellCommandDescriptorReadModel,
) -> None:
    if descriptor.available_as_parser or descriptor.executable:
        _reject(
            "Command descriptor read model must not be a command parser",
            field="available_as_parser",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_adapter_read_model_is_not_command_router(
    adapter: ShellCommandSurfaceAdapterReadModel,
) -> None:
    if adapter.is_command_router or adapter.executes_commands:
        _reject(
            "Command surface adapter read model must not be a command router",
            field="is_command_router",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_adapter_read_model_is_not_command_handler(
    adapter: ShellCommandSurfaceAdapterReadModel,
) -> None:
    if adapter.is_command_handler or adapter.executes_commands:
        _reject(
            "Command surface adapter read model must not be a command handler",
            field="is_command_handler",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_output_preview_is_not_output_writer(
    preview: ShellBindingOutputPreviewSchema,
) -> None:
    if preview.writes_output or preview.creates_output_writer:
        _reject(
            "Output preview schema must not write output or create an output writer",
            field="writes_output",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_render_preview_is_not_tui_runtime(
    preview: ShellBindingRenderPreviewSchema,
) -> None:
    if preview.requires_tui_runtime or preview.creates_render_runtime:
        _reject(
            "Render preview schema must not be a TUI runtime or render runtime",
            field="requires_tui_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_render_preview_is_not_product_ui(
    preview: ShellBindingRenderPreviewSchema,
) -> None:
    if preview.is_product_ui or preview.requires_frontend:
        _reject(
            "Render preview schema must not be product UI or require a frontend",
            field="is_product_ui",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_context_descriptor_does_not_mutate_runtime_context(
    descriptor: ShellBindingContextDescriptor,
) -> None:
    if (
        descriptor.reads_runtime_context
        or descriptor.mutates_runtime_context
        or descriptor.mutates_runtime
    ):
        _reject(
            "Binding context descriptor must not read or mutate runtime context",
            field="mutates_runtime_context",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_availability_read_model_is_not_permission_enforcement(
    availability: ShellBindingAvailabilityReadModel,
) -> None:
    if (
        availability.grants_permission
        or availability.denies_permission
        or availability.enforces_permission
        or availability.activates_approval
    ):
        _reject(
            "Binding availability read model must not enforce permission or approval",
            field="enforces_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selection_descriptor_is_not_operator_confirmation(
    selection: ShellBindingSelectionDescriptor,
) -> None:
    if (
        selection.creates_operator_confirmation
        or selection.creates_approval_runtime
        or selection.executes_selection
    ):
        _reject(
            "Binding selection descriptor must not be operator confirmation or approval",
            field="creates_operator_confirmation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_adapter_expansion_result_is_not_command_execution(
    result: ShellBindingAdapterExpansionResult,
) -> None:
    if any(
        (
            result.creates_command_parser,
            result.creates_command_router,
            result.creates_command_handler,
            result.creates_command_execution,
            result.creates_output_writer,
            result.creates_tui_runtime,
            result.creates_operator_confirmation,
            result.creates_permission_enforcement,
            result.creates_runtime_dispatch,
            result.creates_runtime_mutation,
            result.creates_product_behavior,
        )
    ):
        _reject(
            "Adapter expansion result must not create execution or runtime behavior",
            field="creates_command_execution",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_7_b_does_not_start_future_work(
    result: P27BShellBindingReadModelResult,
) -> None:
    proof = result.side_effect_proof
    if result.starts_future_work or any(
        (
            proof.p2_7_c_started,
            proof.p2_8_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.7-B must not start P2.7-C, P2.8, P2.10, or P2.13",
            field="starts_future_work",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_7_b_side_effects_all_false(proof: P27BSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name) is not False:
            _reject(
                f"P2.7-B side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )

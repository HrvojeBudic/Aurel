"""P2.7-D Shell / CLI / TUI binding section seal contracts.

Contract-only section seal over P2.7-A/B/C evidence. This module creates the
P2.7 section seal gate, contract inventory, section read model, binding
availability rollup, runtime unavailable rollup, P2.8 handoff contract,
validation rollup, contract-scope demo, no-live-binding proof, section seal
result, side-effect proof, and pack result.

It does not create a CLI app/runner/entrypoint, TUI runtime/app, Shell runtime,
Shell execution runtime, Shell state runtime, command parser/router/handler,
command execution/invocation, output writer runtime, render runtime, operator
confirmation runtime, approval runtime, HITL approval activation, permission
enforcement, Custos decisioning, tool/workflow/runtime dispatch, runtime
bridge, runtime mutation, shell state mutation, trace/memory/storage writes,
product UI, product behavior, release scope, LIVE, TRACE_VERIFIED, P2.8,
P2.10, or P2.13.
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
from .shell_binding_preview_selection import (
    P2_7_C_PACK_ID,
    P2_7_C_REPORT_PATH,
    P2_7_C_VALIDATION_REF,
    P27CShellBindingPreviewSelectionResult,
    build_p2_7_c_shell_binding_preview_selection_result,
)
from .shell_binding_read_models import (
    P2_7_B_PACK_ID,
    P2_7_B_REPORT_PATH,
    P2_7_B_VALIDATION_REF,
    P27BShellBindingReadModelResult,
    build_p2_7_b_shell_binding_read_model_result,
)
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES

P2_7_D_PACK_ID = "P2.7-D"
P2_7_D_SECTION_ID = "P2.7"
P2_7_D_OFFICIAL_SECTION_NAME = "Shell / CLI / TUI Binding"
P2_7_D_DEPENDENCY_PACK = P2_7_C_PACK_ID
P2_7_D_NEXT_PACK = "P2.8-A"
P2_7_D_NEXT_SECTION = "P2.8 — Shell State / Reports / Docs"
P2_7_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.7.16",
    "P2.7.17",
    "P2.7.18",
    "P2.7.19",
    "P2.7.20",
)
P2_7_D_FULL_SECTION_CHECKPOINTS: tuple[str, ...] = tuple(
    f"P2.7.{index}" for index in range(21)
)
P2_7_D_REPORT_FILENAME = "P2_7_D_SHELL_CLI_TUI_BINDING_SECTION_SEAL.md"
P2_7_D_REPORT_PATH = f"agent/reports/{P2_7_D_REPORT_FILENAME}"

P2_7_A_COMMIT_REF = "e6f84da"
P2_7_B_COMMIT_REF = "c6cc7a0"
P2_7_C_COMMIT_REF = "47d69d2"

P2_7_D_GATE_VERSION = "p2_7_d_shell_binding_section_seal_gate.v1"
P2_7_D_INVENTORY_VERSION = "p2_7_d_shell_binding_section_contract_inventory.v1"
P2_7_D_ENTRY_VERSION = "p2_7_d_shell_binding_section_contract_entry.v1"
P2_7_D_READ_MODEL_VERSION = "p2_7_d_shell_binding_section_read_model.v1"
P2_7_D_READ_MODEL_VERSION_META = "p2_7_d_shell_binding_section_read_model_version.v1"
P2_7_D_AVAILABILITY_ROLLUP_VERSION = "p2_7_d_shell_binding_availability_rollup.v1"
P2_7_D_RUNTIME_UNAVAILABLE_VERSION = "p2_7_d_shell_binding_runtime_unavailable_rollup.v1"
P2_7_D_P2_8_HANDOFF_VERSION = "p2_7_d_shell_binding_p2_8_handoff_contract.v1"
P2_7_D_VALIDATION_ROLLUP_VERSION = "p2_7_d_shell_binding_section_validation_rollup.v1"
P2_7_D_DEMO_VERSION = "p2_7_d_shell_binding_contract_scope_demo.v1"
P2_7_D_NO_LIVE_BINDING_VERSION = "p2_7_d_shell_binding_no_live_binding_proof.v1"
P2_7_D_SECTION_SEAL_RESULT_VERSION = "p2_7_d_shell_binding_section_seal_result.v1"
P2_7_D_RESULT_VERSION = "p2_7_d_shell_binding_section_seal_pack_result.v1"

P2_7_A_TEST_REF = "tests/aurel_shell/test_shell_binding_foundation.py"
P2_7_B_TEST_REF = "tests/aurel_shell/test_shell_binding_read_models.py"
P2_7_C_TEST_REF = "tests/aurel_shell/test_shell_binding_preview_selection.py"
P2_7_D_TEST_REF = "tests/aurel_shell/test_shell_binding_section_seal.py"
P2_7_D_VALIDATION_REF = "agent/TESTS.md#P2.7-D"
P2_7_D_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_7_D_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_RUNTIME_UNAVAILABLE_REASON = (
    "P2.7-D seals Shell / CLI / TUI binding contracts only. Live runtime, "
    "execution, approval, permission, storage, product, and future-pack "
    "capabilities are unavailable by design."
)
_P2_8_HANDOFF_REASON = (
    "P2.7-D can hand off contract evidence to P2.8-A, but it does not start "
    "P2.8 or create Shell state runtime."
)
_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "CLI runner",
    "CLI app",
    "CLI entrypoint",
    "TUI runtime",
    "Shell runtime",
    "Shell execution runtime",
    "Shell state runtime",
    "Command parser",
    "Command router",
    "Command handler",
    "Command execution",
    "Output writer runtime",
    "Operator confirmation runtime",
    "Approval runtime",
    "HITL activation",
    "Permission enforcement",
    "Custos decisioning",
    "Runtime dispatch",
    "Runtime bridge",
    "Runtime mutation",
    "Trace write",
    "Memory write",
    "Storage write",
    "Product UI",
    "Product behavior",
    "P2.8 implementation",
    "P2.10 implementation",
    "P2.13 implementation",
)

_CHECKPOINT_SPECS: tuple[tuple[str, str, str, str, str, str, str], ...] = (
    ("P2.7.0", "Shell / CLI / TUI Binding Foundation Gate", P2_7_A_PACK_ID, P2_7_A_REPORT_PATH, P2_7_A_TEST_REF, P2_7_A_COMMIT_REF, "ShellBindingSectionGate"),
    ("P2.7.1", "Target Registry / Surface Catalog", P2_7_A_PACK_ID, P2_7_A_REPORT_PATH, P2_7_A_TEST_REF, P2_7_A_COMMIT_REF, "ShellBindingTargetRegistry"),
    ("P2.7.2", "Capability Descriptors", P2_7_A_PACK_ID, P2_7_A_REPORT_PATH, P2_7_A_TEST_REF, P2_7_A_COMMIT_REF, "ShellBindingCapabilityDescriptor"),
    ("P2.7.3", "Adapter / Projection Consumption Contracts", P2_7_A_PACK_ID, P2_7_A_REPORT_PATH, P2_7_A_TEST_REF, P2_7_A_COMMIT_REF, "ShellBindingAdapterContract"),
    ("P2.7.4", "Read-Only Command Surface / Output / Render Descriptors", P2_7_A_PACK_ID, P2_7_A_REPORT_PATH, P2_7_A_TEST_REF, P2_7_A_COMMIT_REF, "ShellBindingReadOnlyCommandSurface"),
    ("P2.7.5", "No-Command / No-Runtime-Dispatch Boundaries", P2_7_A_PACK_ID, P2_7_A_REPORT_PATH, P2_7_A_TEST_REF, P2_7_A_COMMIT_REF, "ShellBindingFoundationResult"),
    ("P2.7.6", "Binding Read Model Gate", P2_7_B_PACK_ID, P2_7_B_REPORT_PATH, P2_7_B_TEST_REF, P2_7_B_COMMIT_REF, "ShellBindingReadModelGate"),
    ("P2.7.7", "Read Model Registry / Inventory", P2_7_B_PACK_ID, P2_7_B_REPORT_PATH, P2_7_B_TEST_REF, P2_7_B_COMMIT_REF, "ShellBindingReadModelInventory"),
    ("P2.7.8", "Command Descriptor / Surface Adapter Read Model", P2_7_B_PACK_ID, P2_7_B_REPORT_PATH, P2_7_B_TEST_REF, P2_7_B_COMMIT_REF, "ShellCommandSurfaceAdapterReadModel"),
    ("P2.7.9", "Output / Render / Context / Availability Read Models", P2_7_B_PACK_ID, P2_7_B_REPORT_PATH, P2_7_B_TEST_REF, P2_7_B_COMMIT_REF, "ShellBindingAvailabilityReadModel"),
    ("P2.7.10", "Selection Descriptor / Adapter Expansion Result", P2_7_B_PACK_ID, P2_7_B_REPORT_PATH, P2_7_B_TEST_REF, P2_7_B_COMMIT_REF, "ShellBindingAdapterExpansionResult"),
    ("P2.7.11", "Binding Preview Bundle / Safe Preview Contract", P2_7_C_PACK_ID, P2_7_C_REPORT_PATH, P2_7_C_TEST_REF, P2_7_C_COMMIT_REF, "ShellBindingPreviewBundle"),
    ("P2.7.12", "Binding Selection Intent / Non-Executable Selection Contract", P2_7_C_PACK_ID, P2_7_C_REPORT_PATH, P2_7_C_TEST_REF, P2_7_C_COMMIT_REF, "ShellBindingSelectedIntent"),
    ("P2.7.13", "Operator Confirmation Requirement / Intent Boundary", P2_7_C_PACK_ID, P2_7_C_REPORT_PATH, P2_7_C_TEST_REF, P2_7_C_COMMIT_REF, "ShellBindingConfirmationRequirement"),
    ("P2.7.14", "Confirmation Outcome / Cancel / Reject / Defer Read Model", P2_7_C_PACK_ID, P2_7_C_REPORT_PATH, P2_7_C_TEST_REF, P2_7_C_COMMIT_REF, "ShellBindingConfirmationOutcomeReadModel"),
    ("P2.7.15", "Preview Selection Boundary Result / No-Execution Contract", P2_7_C_PACK_ID, P2_7_C_REPORT_PATH, P2_7_C_TEST_REF, P2_7_C_COMMIT_REF, "ShellBindingConfirmationBoundaryResult"),
    ("P2.7.16", "Shell / CLI / TUI Binding Contract Inventory Rollup", P2_7_D_PACK_ID, P2_7_D_REPORT_PATH, P2_7_D_TEST_REF, "PENDING_AT_BUILD", "ShellBindingSectionContractInventory"),
    ("P2.7.17", "Binding Section Read Model / Section Status Contract", P2_7_D_PACK_ID, P2_7_D_REPORT_PATH, P2_7_D_TEST_REF, "PENDING_AT_BUILD", "ShellBindingSectionReadModel"),
    ("P2.7.18", "Binding Availability / Runtime Unavailable / P2.8 Handoff Contract", P2_7_D_PACK_ID, P2_7_D_REPORT_PATH, P2_7_D_TEST_REF, "PENDING_AT_BUILD", "ShellBindingP28HandoffContract"),
    ("P2.7.19", "Docs / State / Reports Synchronization", P2_7_D_PACK_ID, P2_7_D_REPORT_PATH, P2_7_D_TEST_REF, "PENDING_AT_BUILD", "ShellBindingSectionValidationRollup"),
    ("P2.7.20", "Section Exit Seal / Contract-Scope Demo / No-Live-Binding Proof", P2_7_D_PACK_ID, P2_7_D_REPORT_PATH, P2_7_D_TEST_REF, "PENDING_AT_BUILD", "ShellBindingSectionSealResult"),
)


class ShellBindingSectionSealGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellBindingSectionContractEntryStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ShellBindingSectionSealStatus(str, Enum):
    SEALED_CONTRACT_ONLY = "SEALED_CONTRACT_ONLY"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellBindingP28HandoffStatus(str, Enum):
    READY_FOR_P2_8_CONTRACT_HANDOFF = "READY_FOR_P2_8_CONTRACT_HANDOFF"
    UNAVAILABLE_P2_8_REQUIRED = "UNAVAILABLE_P2_8_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellBindingSectionValidationStatus(str, Enum):
    RECORDED_IN_REPORT = "RECORDED_IN_REPORT"
    NOT_RUN_AT_BUILD = "NOT_RUN_AT_BUILD"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellBindingSectionSealTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    SECTION_SEAL_ONLY = "SECTION_SEAL_ONLY"
    BINDING_SECTION_SEAL_ONLY = "BINDING_SECTION_SEAL_ONLY"
    CONTRACT_INVENTORY_ONLY = "CONTRACT_INVENTORY_ONLY"
    SECTION_READ_MODEL_ONLY = "SECTION_READ_MODEL_ONLY"
    AVAILABILITY_ROLLUP_ONLY = "AVAILABILITY_ROLLUP_ONLY"
    RUNTIME_UNAVAILABLE_ROLLUP_ONLY = "RUNTIME_UNAVAILABLE_ROLLUP_ONLY"
    P2_8_HANDOFF_CONTRACT_ONLY = "P2_8_HANDOFF_CONTRACT_ONLY"
    VALIDATION_ROLLUP_ONLY = "VALIDATION_ROLLUP_ONLY"
    CONTRACT_SCOPE_DEMO_ONLY = "CONTRACT_SCOPE_DEMO_ONLY"
    NO_LIVE_BINDING_PROOF = "NO_LIVE_BINDING_PROOF"
    NO_COMMAND_EXECUTION_BOUNDARY = "NO_COMMAND_EXECUTION_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    NO_APPROVAL_RUNTIME_BOUNDARY = "NO_APPROVAL_RUNTIME_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_RELEASE_SEAL = "NOT_RELEASE_SEAL"
    NOT_SHELL_COMPLETE = "NOT_SHELL_COMPLETE"
    NOT_P2_COMPLETE = "NOT_P2_COMPLETE"
    NOT_CLI_APP = "NOT_CLI_APP"
    NOT_CLI_RUNNER = "NOT_CLI_RUNNER"
    NOT_CLI_ENTRYPOINT = "NOT_CLI_ENTRYPOINT"
    NOT_TUI_RUNTIME = "NOT_TUI_RUNTIME"
    NOT_TUI_APP = "NOT_TUI_APP"
    NOT_SHELL_RUNTIME = "NOT_SHELL_RUNTIME"
    NOT_SHELL_EXECUTION_RUNTIME = "NOT_SHELL_EXECUTION_RUNTIME"
    NOT_SHELL_STATE_RUNTIME = "NOT_SHELL_STATE_RUNTIME"
    NOT_COMMAND_PARSER = "NOT_COMMAND_PARSER"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_COMMAND_HANDLER = "NOT_COMMAND_HANDLER"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_COMMAND_INVOCATION = "NOT_COMMAND_INVOCATION"
    NOT_TOOL_INVOCATION = "NOT_TOOL_INVOCATION"
    NOT_WORKFLOW_DISPATCH = "NOT_WORKFLOW_DISPATCH"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_RUNTIME_BRIDGE = "NOT_RUNTIME_BRIDGE"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_NAVIGATION_MUTATION = "NOT_NAVIGATION_MUTATION"
    NOT_OUTPUT_WRITER = "NOT_OUTPUT_WRITER"
    NOT_RENDER_RUNTIME = "NOT_RENDER_RUNTIME"
    NOT_OPERATOR_CONFIRMATION_RUNTIME = "NOT_OPERATOR_CONFIRMATION_RUNTIME"
    NOT_APPROVAL_RUNTIME = "NOT_APPROVAL_RUNTIME"
    NOT_HITL_APPROVAL = "NOT_HITL_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_CUSTOS_DECISION = "NOT_CUSTOS_DECISION"
    NOT_PERMISSION_GRANT = "NOT_PERMISSION_GRANT"
    NOT_PERMISSION_DENIAL = "NOT_PERMISSION_DENIAL"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_PRODUCT_UI = "NOT_PRODUCT_UI"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_P2_8_IMPLEMENTATION = "NOT_P2_8_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_DEMO = "NOT_PRODUCT_DEMO"
    NOT_INVENTED_PASS = "NOT_INVENTED_PASS"
    STATE_MIRROR_ONLY = "STATE_MIRROR_ONLY"
    SECTION_SEAL_GATE_ONLY = "SECTION_SEAL_GATE_ONLY"


@dataclass(frozen=True)
class P27DSideEffectProof(_CanonicalMixin):
    cli_app_created: bool = False
    cli_runner_created: bool = False
    cli_entrypoint_created: bool = False
    tui_runtime_created: bool = False
    tui_app_created: bool = False
    shell_runtime_created: bool = False
    shell_execution_runtime_created: bool = False
    shell_state_runtime_created: bool = False
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
    shell_state_mutated: bool = False
    surface_switch_created: bool = False
    navigation_mutation_created: bool = False
    output_writer_created: bool = False
    render_runtime_created: bool = False
    operator_confirmation_runtime_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    hitl_approval_activated: bool = False
    authorization_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    custos_decisioning_created: bool = False
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
    shell_complete_claimed: bool = False
    p2_complete_claimed: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    p2_8_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellBindingSectionSealGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_confirmation_boundary_result_ref: str
    dependency_side_effect_proof_ref: str
    p2_7_a_evidence_ref: str
    p2_7_b_evidence_ref: str
    p2_7_c_evidence_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellBindingSectionSealGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellBindingSectionContractEntry(_CanonicalMixin):
    entry_id: str
    schema_version: str
    checkpoint_id: str
    checkpoint_capsule: str
    source_pack: str
    source_report_ref: str
    source_contract_ref: str
    source_test_ref: str
    source_commit_ref: str
    status: ShellBindingSectionContractEntryStatus
    truth_label: str
    unavailable_runtime_reason: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellBindingSectionContractInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    inventory_version: str
    covered_checkpoints: tuple[str, ...]
    contract_entries: tuple[ShellBindingSectionContractEntry, ...]
    source_pack_refs: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    source_validation_refs: tuple[str, ...]
    is_source_of_truth: bool
    duplicates_source_evidence: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class ShellBindingSectionReadModelVersion(_CanonicalMixin):
    version_id: str
    schema_version: str
    read_model_name: str
    read_model_version: str
    compatible_section: str
    compatible_pack: str
    source_contract_refs: tuple[str, ...]
    breaking_change: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_hash: str


@dataclass(frozen=True)
class ShellBindingSectionReadModel(_CanonicalMixin):
    section_read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    read_model_version: ShellBindingSectionReadModelVersion
    section_status: ShellBindingSectionSealStatus
    covered_checkpoints: tuple[str, ...]
    sealed_contract_only: bool
    is_release_seal: bool
    is_shell_complete: bool
    is_p2_complete: bool
    is_live_binding: bool
    next_pack: str
    truth_label: str
    limitations: tuple[str, ...]
    read_model_hash: str


@dataclass(frozen=True)
class ShellBindingAvailabilityRollup(_CanonicalMixin):
    availability_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    contract_binding_available: bool
    live_binding_available: bool
    cli_descriptor_available: bool
    tui_descriptor_available: bool
    shell_descriptor_available: bool
    command_surface_descriptor_available: bool
    preview_selection_available: bool
    confirmation_boundary_available: bool
    permission_enforcement_available: bool
    approval_runtime_available: bool
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellBindingRuntimeUnavailableRollup(_CanonicalMixin):
    runtime_unavailable_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    unavailable_capabilities: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    future_pack_refs: tuple[str, ...]
    creates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellBindingP28HandoffContract(_CanonicalMixin):
    handoff_contract_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    handoff_to_pack: str
    handoff_to_section: str
    handoff_status: ShellBindingP28HandoffStatus
    handoff_reason: str
    requires_p2_8: bool
    starts_p2_8: bool
    implements_p2_8: bool
    creates_shell_state_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class ShellBindingSectionValidationRollup(_CanonicalMixin):
    validation_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_validation_refs: tuple[str, ...]
    commands_recorded: tuple[str, ...]
    focused_tests_recorded: str
    nearby_tests_recorded: str
    ruff_recorded: str
    mypy_recorded: str
    invented_pass: bool
    validation_status: ShellBindingSectionValidationStatus
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellBindingContractScopeDemo(_CanonicalMixin):
    contract_scope_demo_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    demo_scope: str
    source_inventory_ref: str
    source_section_read_model_ref: str
    demo_serialization_ref: str
    is_product_demo: bool
    is_live_demo: bool
    requires_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    demo_hash: str


@dataclass(frozen=True)
class ShellBindingNoLiveBindingProof(_CanonicalMixin):
    no_live_binding_proof_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    live_cli_runner_created: bool
    live_tui_runtime_created: bool
    live_shell_runtime_created: bool
    live_command_execution_created: bool
    live_runtime_dispatch_created: bool
    live_trace_write_created: bool
    live_product_behavior_created: bool
    proof_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    proof_hash: str


@dataclass(frozen=True)
class ShellBindingSectionSealResult(_CanonicalMixin):
    section_seal_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    section_seal_gate: ShellBindingSectionSealGate
    contract_inventory: ShellBindingSectionContractInventory
    section_read_model: ShellBindingSectionReadModel
    availability_rollup: ShellBindingAvailabilityRollup
    runtime_unavailable_rollup: ShellBindingRuntimeUnavailableRollup
    p2_8_handoff_contract: ShellBindingP28HandoffContract
    validation_rollup: ShellBindingSectionValidationRollup
    contract_scope_demo: ShellBindingContractScopeDemo
    no_live_binding_proof: ShellBindingNoLiveBindingProof
    section_status: ShellBindingSectionSealStatus
    is_release_seal: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_shell_complete: bool
    claims_p2_complete: bool
    claims_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    seal_result_hash: str


@dataclass(frozen=True)
class P27DShellBindingSectionSealResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    full_section_coverage: tuple[str, ...]
    dependency_pack: str
    p2_7_a_evidence_ref: str
    p2_7_b_evidence_ref: str
    p2_7_c_evidence_ref: str
    section_seal_gate: ShellBindingSectionSealGate
    contract_inventory: ShellBindingSectionContractInventory
    section_read_model: ShellBindingSectionReadModel
    availability_rollup: ShellBindingAvailabilityRollup
    runtime_unavailable_rollup: ShellBindingRuntimeUnavailableRollup
    p2_8_handoff_contract: ShellBindingP28HandoffContract
    validation_rollup: ShellBindingSectionValidationRollup
    contract_scope_demo: ShellBindingContractScopeDemo
    no_live_binding_proof: ShellBindingNoLiveBindingProof
    section_seal_result: ShellBindingSectionSealResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P27DSideEffectProof
    official_surface_ids: tuple[str, ...]
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_shell_complete: bool
    claims_p2_complete: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _p2_7_a_evidence_ref(result: P27AShellBindingFoundationResult) -> str:
    return f"{P2_7_A_REPORT_PATH}:{result.result_hash[:12]}"


def _p2_7_b_evidence_ref(result: P27BShellBindingReadModelResult) -> str:
    return f"{P2_7_B_REPORT_PATH}:{result.result_hash[:12]}"


def _p2_7_c_evidence_ref(result: P27CShellBindingPreviewSelectionResult) -> str:
    return f"{P2_7_C_REPORT_PATH}:{result.result_hash[:12]}"


def _p2_7_c_confirmation_boundary_ref(
    result: P27CShellBindingPreviewSelectionResult,
) -> str:
    boundary = result.confirmation_boundary_result
    return (
        f"{boundary.confirmation_boundary_result_id}:"
        f"hash={boundary.boundary_hash[:12]}"
    )


def build_shell_binding_section_seal_gate(
    preview_result: P27CShellBindingPreviewSelectionResult | None = None,
) -> ShellBindingSectionSealGate:
    if preview_result is None:
        preview_result = build_p2_7_c_shell_binding_preview_selection_result()
    assert_p2_7_c_preview_result_available(preview_result)
    payload: dict[str, Any] = {
        "gate_id": "p2_7_d_shell_binding_section_seal_gate",
        "schema_version": P2_7_D_GATE_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "official_section_name": P2_7_D_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_7_D_DEPENDENCY_PACK,
        "dependency_report_ref": P2_7_C_REPORT_PATH,
        "dependency_commit_ref": P2_7_C_COMMIT_REF,
        "dependency_validation_ref": P2_7_C_VALIDATION_REF,
        "dependency_confirmation_boundary_result_ref": (
            _p2_7_c_confirmation_boundary_ref(preview_result)
        ),
        "dependency_side_effect_proof_ref": "P27CSideEffectProof:all_false",
        "p2_7_a_evidence_ref": P2_7_A_REPORT_PATH,
        "p2_7_b_evidence_ref": P2_7_B_REPORT_PATH,
        "p2_7_c_evidence_ref": P2_7_C_REPORT_PATH,
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellBindingSectionSealGateStatus.READY,
        "truth_label": ShellBindingSectionSealTruthBoundary.SECTION_SEAL_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate creates no CLI, TUI, Shell, command, approval, or permission runtime",
        ),
    }
    gate = ShellBindingSectionSealGate(**payload, gate_hash=_hash_payload(payload))
    assert_section_gate_depends_on_p2_7_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def _build_contract_entry(
    checkpoint_id: str,
    checkpoint_capsule: str,
    source_pack: str,
    source_report_ref: str,
    source_test_ref: str,
    source_commit_ref: str,
    source_contract_ref: str,
) -> ShellBindingSectionContractEntry:
    payload: dict[str, Any] = {
        "entry_id": f"p2_7_contract_entry_{checkpoint_id.replace('.', '_').lower()}",
        "schema_version": P2_7_D_ENTRY_VERSION,
        "checkpoint_id": checkpoint_id,
        "checkpoint_capsule": checkpoint_capsule,
        "source_pack": source_pack,
        "source_report_ref": source_report_ref,
        "source_contract_ref": source_contract_ref,
        "source_test_ref": source_test_ref,
        "source_commit_ref": source_commit_ref,
        "status": ShellBindingSectionContractEntryStatus.DONE,
        "truth_label": ShellBindingSectionSealTruthBoundary.REPORT_ONLY.value,
        "unavailable_runtime_reason": (
            _RUNTIME_UNAVAILABLE_REASON if source_pack == P2_7_D_PACK_ID else ""
        ),
        "limitations": (
            "entry references source evidence only",
            "entry does not duplicate source-of-truth contracts",
        ),
    }
    return ShellBindingSectionContractEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_shell_binding_section_contract_inventory() -> (
    ShellBindingSectionContractInventory
):
    entries = tuple(
        _build_contract_entry(
            checkpoint_id,
            checkpoint_capsule,
            source_pack,
            source_report_ref,
            source_test_ref,
            source_commit_ref,
            source_contract_ref,
        )
        for (
            checkpoint_id,
            checkpoint_capsule,
            source_pack,
            source_report_ref,
            source_test_ref,
            source_commit_ref,
            source_contract_ref,
        ) in _CHECKPOINT_SPECS
    )
    payload: dict[str, Any] = {
        "inventory_id": "p2_7_d_shell_binding_section_contract_inventory",
        "schema_version": P2_7_D_INVENTORY_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "official_section_name": P2_7_D_OFFICIAL_SECTION_NAME,
        "inventory_version": P2_7_D_INVENTORY_VERSION,
        "covered_checkpoints": P2_7_D_FULL_SECTION_CHECKPOINTS,
        "contract_entries": entries,
        "source_pack_refs": (
            P2_7_A_PACK_ID,
            P2_7_B_PACK_ID,
            P2_7_C_PACK_ID,
            P2_7_D_PACK_ID,
        ),
        "source_report_refs": (
            P2_7_A_REPORT_PATH,
            P2_7_B_REPORT_PATH,
            P2_7_C_REPORT_PATH,
            P2_7_D_REPORT_PATH,
        ),
        "source_validation_refs": (
            P2_7_A_VALIDATION_REF,
            P2_7_B_VALIDATION_REF,
            P2_7_C_VALIDATION_REF,
            P2_7_D_VALIDATION_REF,
        ),
        "is_source_of_truth": False,
        "duplicates_source_evidence": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.CONTRACT_INVENTORY_ONLY.value,
        "limitations": (
            "inventory references P2.7-A/B/C/D evidence by ref",
            "inventory does not duplicate source evidence or source-of-truth",
        ),
    }
    inventory = ShellBindingSectionContractInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    assert_contract_inventory_is_not_source_of_truth_duplication(inventory)
    return inventory


def build_shell_binding_section_read_model_version() -> (
    ShellBindingSectionReadModelVersion
):
    payload: dict[str, Any] = {
        "version_id": "p2_7_d_shell_binding_section_read_model_version",
        "schema_version": P2_7_D_READ_MODEL_VERSION_META,
        "read_model_name": "shell_binding_section_read_model",
        "read_model_version": P2_7_D_READ_MODEL_VERSION,
        "compatible_section": P2_7_D_SECTION_ID,
        "compatible_pack": P2_7_D_PACK_ID,
        "source_contract_refs": (
            "ShellBindingFoundationResult",
            "ShellBindingAdapterExpansionResult",
            "ShellBindingConfirmationBoundaryResult",
            "ShellBindingSectionSealResult",
        ),
        "breaking_change": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.SECTION_READ_MODEL_ONLY.value,
        "limitations": ("read model version is contract metadata only",),
    }
    return ShellBindingSectionReadModelVersion(
        **payload,
        version_hash=_hash_payload(payload),
    )


def build_shell_binding_section_read_model() -> ShellBindingSectionReadModel:
    version = build_shell_binding_section_read_model_version()
    payload: dict[str, Any] = {
        "section_read_model_id": "p2_7_d_shell_binding_section_read_model",
        "schema_version": P2_7_D_READ_MODEL_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "official_section_name": P2_7_D_OFFICIAL_SECTION_NAME,
        "read_model_version": version,
        "section_status": ShellBindingSectionSealStatus.SEALED_CONTRACT_ONLY,
        "covered_checkpoints": P2_7_D_FULL_SECTION_CHECKPOINTS,
        "sealed_contract_only": True,
        "is_release_seal": False,
        "is_shell_complete": False,
        "is_p2_complete": False,
        "is_live_binding": False,
        "next_pack": P2_7_D_NEXT_PACK,
        "truth_label": ShellBindingSectionSealTruthBoundary.SECTION_READ_MODEL_ONLY.value,
        "limitations": (
            "section read model is contract-only",
            "section seal is not release seal, Shell complete, P2 complete, or live binding",
        ),
    }
    read_model = ShellBindingSectionReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )
    assert_binding_section_complete_is_not_live_binding(read_model)
    assert_p2_7_complete_is_not_p2_complete(read_model)
    return read_model


def build_shell_binding_availability_rollup() -> ShellBindingAvailabilityRollup:
    payload: dict[str, Any] = {
        "availability_rollup_id": "p2_7_d_shell_binding_availability_rollup",
        "schema_version": P2_7_D_AVAILABILITY_ROLLUP_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "contract_binding_available": True,
        "live_binding_available": False,
        "cli_descriptor_available": True,
        "tui_descriptor_available": True,
        "shell_descriptor_available": True,
        "command_surface_descriptor_available": True,
        "preview_selection_available": True,
        "confirmation_boundary_available": True,
        "permission_enforcement_available": False,
        "approval_runtime_available": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.AVAILABILITY_ROLLUP_ONLY.value,
        "limitations": (
            "contract availability is not live binding",
            "availability rollup does not enforce permission or activate approval",
        ),
    }
    rollup = ShellBindingAvailabilityRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_availability_rollup_is_not_permission_enforcement(rollup)
    return rollup


def build_shell_binding_runtime_unavailable_rollup() -> (
    ShellBindingRuntimeUnavailableRollup
):
    payload: dict[str, Any] = {
        "runtime_unavailable_rollup_id": "p2_7_d_shell_binding_runtime_unavailable_rollup",
        "schema_version": P2_7_D_RUNTIME_UNAVAILABLE_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "unavailable_reasons": (
            _RUNTIME_UNAVAILABLE_REASON,
            _P2_8_HANDOFF_REASON,
        ),
        "future_pack_refs": ("P2.8-A", "P2.10-A", "P2.13-A"),
        "creates_runtime": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.RUNTIME_UNAVAILABLE_ROLLUP_ONLY.value,
        "limitations": (
            "runtime unavailable rollup is honesty metadata only",
            "rollup creates no runtime",
        ),
    }
    rollup = ShellBindingRuntimeUnavailableRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_runtime_unavailable_rollup_is_not_runtime_implementation(rollup)
    return rollup


def build_shell_binding_p2_8_handoff_contract() -> ShellBindingP28HandoffContract:
    payload: dict[str, Any] = {
        "handoff_contract_id": "p2_7_d_shell_binding_p2_8_handoff_contract",
        "schema_version": P2_7_D_P2_8_HANDOFF_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "handoff_to_pack": P2_7_D_NEXT_PACK,
        "handoff_to_section": P2_7_D_NEXT_SECTION,
        "handoff_status": ShellBindingP28HandoffStatus.READY_FOR_P2_8_CONTRACT_HANDOFF,
        "handoff_reason": _P2_8_HANDOFF_REASON,
        "requires_p2_8": True,
        "starts_p2_8": False,
        "implements_p2_8": False,
        "creates_shell_state_runtime": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.P2_8_HANDOFF_CONTRACT_ONLY.value,
        "limitations": (
            "P2.8 handoff is a contract boundary only",
            "handoff does not start P2.8 or create Shell state runtime",
        ),
    }
    handoff = ShellBindingP28HandoffContract(
        **payload,
        handoff_hash=_hash_payload(payload),
    )
    assert_p2_8_handoff_is_not_p2_8_implementation(handoff)
    return handoff


def build_shell_binding_section_validation_rollup() -> (
    ShellBindingSectionValidationRollup
):
    payload: dict[str, Any] = {
        "validation_rollup_id": "p2_7_d_shell_binding_section_validation_rollup",
        "schema_version": P2_7_D_VALIDATION_ROLLUP_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "source_validation_refs": (
            P2_7_A_VALIDATION_REF,
            P2_7_B_VALIDATION_REF,
            P2_7_C_VALIDATION_REF,
            P2_7_D_VALIDATION_REF,
        ),
        "commands_recorded": P2_7_D_VALIDATION_COMMANDS,
        "focused_tests_recorded": P2_7_D_TEST_REF,
        "nearby_tests_recorded": "tests/aurel_shell",
        "ruff_recorded": "NOT_RUN_AT_BUILD",
        "mypy_recorded": "NOT_RUN_AT_BUILD",
        "invented_pass": False,
        "validation_status": ShellBindingSectionValidationStatus.NOT_RUN_AT_BUILD,
        "truth_label": ShellBindingSectionSealTruthBoundary.VALIDATION_ROLLUP_ONLY.value,
        "limitations": (
            "validation results are recorded in the agent report after commands run",
            "validation rollup does not invent PASS",
        ),
    }
    rollup = ShellBindingSectionValidationRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_validation_rollup_does_not_invent_pass(rollup)
    return rollup


def build_shell_binding_contract_scope_demo(
    inventory: ShellBindingSectionContractInventory | None = None,
    read_model: ShellBindingSectionReadModel | None = None,
) -> ShellBindingContractScopeDemo:
    if inventory is None:
        inventory = build_shell_binding_section_contract_inventory()
    if read_model is None:
        read_model = build_shell_binding_section_read_model()
    payload: dict[str, Any] = {
        "contract_scope_demo_id": "p2_7_d_shell_binding_contract_scope_demo",
        "schema_version": P2_7_D_DEMO_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "demo_scope": "CONTRACT_SCOPE_ONLY",
        "source_inventory_ref": inventory.inventory_id,
        "source_section_read_model_ref": read_model.section_read_model_id,
        "demo_serialization_ref": "serialize_p2_7_d_result",
        "is_product_demo": False,
        "is_live_demo": False,
        "requires_runtime": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.CONTRACT_SCOPE_DEMO_ONLY.value,
        "limitations": (
            "contract-scope demo validates serialization and contract shape only",
            "demo is not product demo or live demo",
        ),
    }
    demo = ShellBindingContractScopeDemo(**payload, demo_hash=_hash_payload(payload))
    assert_contract_scope_demo_is_not_product_demo(demo)
    return demo


def build_shell_binding_no_live_binding_proof() -> ShellBindingNoLiveBindingProof:
    payload: dict[str, Any] = {
        "no_live_binding_proof_id": "p2_7_d_shell_binding_no_live_binding_proof",
        "schema_version": P2_7_D_NO_LIVE_BINDING_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "live_cli_runner_created": False,
        "live_tui_runtime_created": False,
        "live_shell_runtime_created": False,
        "live_command_execution_created": False,
        "live_runtime_dispatch_created": False,
        "live_trace_write_created": False,
        "live_product_behavior_created": False,
        "proof_active": True,
        "truth_label": ShellBindingSectionSealTruthBoundary.NO_LIVE_BINDING_PROOF.value,
        "limitations": (
            "proof records absence of live binding at P2.7-D scope",
            "proof is not live binding",
        ),
    }
    proof = ShellBindingNoLiveBindingProof(**payload, proof_hash=_hash_payload(payload))
    assert_no_live_binding_proof_is_active(proof)
    return proof


def build_shell_binding_section_seal_result(
    gate: ShellBindingSectionSealGate | None = None,
    inventory: ShellBindingSectionContractInventory | None = None,
    read_model: ShellBindingSectionReadModel | None = None,
    availability_rollup: ShellBindingAvailabilityRollup | None = None,
    runtime_unavailable_rollup: ShellBindingRuntimeUnavailableRollup | None = None,
    p2_8_handoff_contract: ShellBindingP28HandoffContract | None = None,
    validation_rollup: ShellBindingSectionValidationRollup | None = None,
    contract_scope_demo: ShellBindingContractScopeDemo | None = None,
    no_live_binding_proof: ShellBindingNoLiveBindingProof | None = None,
) -> ShellBindingSectionSealResult:
    if gate is None:
        gate = build_shell_binding_section_seal_gate()
    if inventory is None:
        inventory = build_shell_binding_section_contract_inventory()
    if read_model is None:
        read_model = build_shell_binding_section_read_model()
    if availability_rollup is None:
        availability_rollup = build_shell_binding_availability_rollup()
    if runtime_unavailable_rollup is None:
        runtime_unavailable_rollup = build_shell_binding_runtime_unavailable_rollup()
    if p2_8_handoff_contract is None:
        p2_8_handoff_contract = build_shell_binding_p2_8_handoff_contract()
    if validation_rollup is None:
        validation_rollup = build_shell_binding_section_validation_rollup()
    if contract_scope_demo is None:
        contract_scope_demo = build_shell_binding_contract_scope_demo(
            inventory=inventory,
            read_model=read_model,
        )
    if no_live_binding_proof is None:
        no_live_binding_proof = build_shell_binding_no_live_binding_proof()
    payload: dict[str, Any] = {
        "section_seal_result_id": "p2_7_d_shell_binding_section_seal_result",
        "schema_version": P2_7_D_SECTION_SEAL_RESULT_VERSION,
        "section_id": P2_7_D_SECTION_ID,
        "created_for_pack": P2_7_D_PACK_ID,
        "official_section_name": P2_7_D_OFFICIAL_SECTION_NAME,
        "section_seal_gate": gate,
        "contract_inventory": inventory,
        "section_read_model": read_model,
        "availability_rollup": availability_rollup,
        "runtime_unavailable_rollup": runtime_unavailable_rollup,
        "p2_8_handoff_contract": p2_8_handoff_contract,
        "validation_rollup": validation_rollup,
        "contract_scope_demo": contract_scope_demo,
        "no_live_binding_proof": no_live_binding_proof,
        "section_status": ShellBindingSectionSealStatus.SEALED_CONTRACT_ONLY,
        "is_release_seal": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_shell_complete": False,
        "claims_p2_complete": False,
        "claims_product_behavior": False,
        "truth_label": ShellBindingSectionSealTruthBoundary.SECTION_SEAL_ONLY.value,
        "limitations": (
            "section seal is not release seal",
            "P2.7 complete is not P2 complete",
            "binding section complete is not live binding",
        ),
    }
    result = ShellBindingSectionSealResult(
        **payload,
        seal_result_hash=_hash_payload(payload),
    )
    assert_section_seal_is_not_release_seal(result)
    return result


def build_p2_7_d_side_effect_proof() -> P27DSideEffectProof:
    return P27DSideEffectProof()


def build_p2_7_d_shell_binding_section_seal_result() -> (
    P27DShellBindingSectionSealResult
):
    foundation = build_p2_7_a_shell_binding_foundation_result()
    read_model_result = build_p2_7_b_shell_binding_read_model_result()
    preview_result = build_p2_7_c_shell_binding_preview_selection_result()
    gate = build_shell_binding_section_seal_gate(preview_result)
    inventory = build_shell_binding_section_contract_inventory()
    read_model = build_shell_binding_section_read_model()
    availability_rollup = build_shell_binding_availability_rollup()
    runtime_unavailable_rollup = build_shell_binding_runtime_unavailable_rollup()
    p2_8_handoff_contract = build_shell_binding_p2_8_handoff_contract()
    validation_rollup = build_shell_binding_section_validation_rollup()
    contract_scope_demo = build_shell_binding_contract_scope_demo(inventory, read_model)
    no_live_binding_proof = build_shell_binding_no_live_binding_proof()
    section_seal_result = build_shell_binding_section_seal_result(
        gate=gate,
        inventory=inventory,
        read_model=read_model,
        availability_rollup=availability_rollup,
        runtime_unavailable_rollup=runtime_unavailable_rollup,
        p2_8_handoff_contract=p2_8_handoff_contract,
        validation_rollup=validation_rollup,
        contract_scope_demo=contract_scope_demo,
        no_live_binding_proof=no_live_binding_proof,
    )
    side_effects = build_p2_7_d_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_7_D_RESULT_VERSION,
        "pack_id": P2_7_D_PACK_ID,
        "section_id": P2_7_D_SECTION_ID,
        "official_section_name": P2_7_D_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_7_D_PACK_CHECKPOINT_IDS,
        "full_section_coverage": P2_7_D_FULL_SECTION_CHECKPOINTS,
        "dependency_pack": P2_7_D_DEPENDENCY_PACK,
        "p2_7_a_evidence_ref": _p2_7_a_evidence_ref(foundation),
        "p2_7_b_evidence_ref": _p2_7_b_evidence_ref(read_model_result),
        "p2_7_c_evidence_ref": _p2_7_c_evidence_ref(preview_result),
        "section_seal_gate": gate,
        "contract_inventory": inventory,
        "section_read_model": read_model,
        "availability_rollup": availability_rollup,
        "runtime_unavailable_rollup": runtime_unavailable_rollup,
        "p2_8_handoff_contract": p2_8_handoff_contract,
        "validation_rollup": validation_rollup,
        "contract_scope_demo": contract_scope_demo,
        "no_live_binding_proof": no_live_binding_proof,
        "section_seal_result": section_seal_result,
        "truth_labels": tuple(
            label.value for label in ShellBindingSectionSealTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "official_surface_ids": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "next_pack": P2_7_D_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_shell_complete": False,
        "claims_p2_complete": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P27DShellBindingSectionSealResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_7_d_does_not_start_future_work(result)
    assert_p2_7_d_side_effects_all_false(result.side_effect_proof)
    assert_contract_inventory_is_not_source_of_truth_duplication(result.contract_inventory)
    return result


def serialize_p2_7_d_result(
    result: P27DShellBindingSectionSealResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_d_shell_binding_section_seal_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_binding_section_seal_summary(
    result: P27DShellBindingSectionSealResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_d_shell_binding_section_seal_result()
    unavailable = result.runtime_unavailable_rollup
    handoff = result.p2_8_handoff_contract
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.section_seal_gate.gate_status.value}",
            f"section_status={result.section_read_model.section_status.value}",
            f"inventory_entries={len(result.contract_inventory.contract_entries)}",
            f"unavailable_capabilities={len(unavailable.unavailable_capabilities)}",
            f"next={result.next_pack}",
            f"handoff_to={handoff.handoff_to_pack}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"shell_complete={str(result.claims_shell_complete).lower()}",
            f"p2_complete={str(result.claims_p2_complete).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
            f"creates_runtime={str(unavailable.creates_runtime).lower()}",
            f"p2_8_started={str(handoff.starts_p2_8).lower()}",
        )
    )


def assert_p2_7_c_preview_result_available(
    result: P27CShellBindingPreviewSelectionResult,
) -> None:
    if result.pack_id != P2_7_C_PACK_ID or result.starts_future_work:
        _reject(
            "P2.7-D requires P2.7-C preview result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.next_pack != P2_7_D_PACK_ID:
        _reject(
            "P2.7-D requires P2.7-C result pointing to P2.7-D",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.side_effect_proof.p2_7_d_started:
        _reject(
            "P2.7-C must not have started P2.7-D",
            field="side_effect_proof",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_gate_depends_on_p2_7_c(
    gate: ShellBindingSectionSealGate,
) -> None:
    if (
        gate.dependency_pack != P2_7_D_DEPENDENCY_PACK
        or not gate.repo_evidence_gate_passed
    ):
        _reject(
            "P2.7-D section seal gate must depend on passed P2.7-C repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_confirmation_boundary_result_ref
        or not gate.dependency_side_effect_proof_ref
    ):
        _reject(
            "P2.7-D gate must reference P2.7-C confirmation boundary and side-effect proof",
            field="dependency_confirmation_boundary_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellBindingSectionSealGate,
) -> None:
    if (
        gate.omni_evidence_required
        or not gate.omni_evidence_ignored_by_operator_instruction
    ):
        _reject(
            "OMNI evidence must be ignored as hard gate for P2.7-D dispatch",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_seal_is_not_release_seal(
    result: ShellBindingSectionSealResult,
) -> None:
    if (
        result.is_release_seal
        or result.claims_live
        or result.claims_trace_verified
        or result.claims_shell_complete
        or result.claims_p2_complete
        or result.claims_product_behavior
    ):
        _reject(
            "P2.7-D section seal must not claim release/live/Shell/P2/product behavior",
            field="is_release_seal",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_binding_section_complete_is_not_live_binding(
    read_model: ShellBindingSectionReadModel,
) -> None:
    if read_model.is_live_binding or read_model.is_release_seal:
        _reject(
            "P2.7-D read model must not claim live binding or release seal",
            field="is_live_binding",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_7_complete_is_not_p2_complete(
    read_model: ShellBindingSectionReadModel,
) -> None:
    if read_model.is_p2_complete or read_model.is_shell_complete:
        _reject(
            "P2.7 completion must not claim P2 or Shell completion",
            field="is_p2_complete",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_contract_scope_demo_is_not_product_demo(
    demo: ShellBindingContractScopeDemo,
) -> None:
    if demo.is_product_demo or demo.is_live_demo or demo.requires_runtime:
        _reject(
            "P2.7-D contract-scope demo must not be product/live/runtime demo",
            field="is_product_demo",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_handoff_is_not_p2_8_implementation(
    handoff: ShellBindingP28HandoffContract,
) -> None:
    if (
        handoff.starts_p2_8
        or handoff.implements_p2_8
        or handoff.creates_shell_state_runtime
    ):
        _reject(
            "P2.8 handoff contract must not start or implement P2.8",
            field="starts_p2_8",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_validation_rollup_does_not_invent_pass(
    rollup: ShellBindingSectionValidationRollup,
) -> None:
    if rollup.invented_pass:
        _reject(
            "P2.7-D validation rollup must not invent PASS",
            field="invented_pass",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_evidence_rollup_is_not_trace_verified(
    result: P27DShellBindingSectionSealResult,
) -> None:
    if result.claims_trace_verified:
        _reject(
            "P2.7-D evidence refs must not claim TRACE_VERIFIED",
            field="claims_trace_verified",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_availability_rollup_is_not_permission_enforcement(
    rollup: ShellBindingAvailabilityRollup,
) -> None:
    if rollup.permission_enforcement_available or rollup.approval_runtime_available:
        _reject(
            "P2.7-D availability rollup must not enforce permission or approval",
            field="permission_enforcement_available",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_runtime_unavailable_rollup_is_not_runtime_implementation(
    rollup: ShellBindingRuntimeUnavailableRollup,
) -> None:
    if rollup.creates_runtime:
        _reject(
            "P2.7-D runtime unavailable rollup must not create runtime",
            field="creates_runtime",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_live_binding_proof_is_active(
    proof: ShellBindingNoLiveBindingProof,
) -> None:
    if (
        not proof.proof_active
        or proof.live_cli_runner_created
        or proof.live_tui_runtime_created
        or proof.live_shell_runtime_created
        or proof.live_command_execution_created
        or proof.live_runtime_dispatch_created
        or proof.live_trace_write_created
        or proof.live_product_behavior_created
    ):
        _reject(
            "P2.7-D no-live-binding proof must be active and all live fields false",
            field="proof_active",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_7_d_does_not_start_future_work(
    result: P27DShellBindingSectionSealResult,
) -> None:
    if result.next_pack != P2_7_D_NEXT_PACK or result.starts_future_work:
        _reject(
            "P2.7-D must hand off to P2.8-A without starting future work",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    proof = result.side_effect_proof
    if proof.p2_8_started or proof.p2_10_started or proof.p2_13_started:
        _reject(
            "P2.7-D side-effect proof must not start P2.8/P2.10/P2.13",
            field="side_effect_proof",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_7_d_side_effects_all_false(proof: P27DSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name) is not False:
            _reject(
                "P2.7-D side-effect proof booleans must all be false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_contract_inventory_is_not_source_of_truth_duplication(
    inventory: ShellBindingSectionContractInventory,
) -> None:
    if inventory.is_source_of_truth or inventory.duplicates_source_evidence:
        _reject(
            "P2.7-D inventory must not duplicate source evidence or source-of-truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_p2_7_d_does_not_start_future_pack(
    proof: P27DSideEffectProof,
) -> None:
    if proof.p2_8_started or proof.p2_10_started or proof.p2_13_started:
        _reject(
            "P2.7-D must not start P2.8/P2.10/P2.13",
            field="p2_8_started",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )

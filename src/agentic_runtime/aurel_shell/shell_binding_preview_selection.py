"""P2.7-C Shell binding preview / selection / operator confirmation boundary.

Contract-only preview, selection and confirmation-boundary contracts over
P2.7-B binding read model / command surface adapter evidence. This module
defines the binding preview gate, preview bundle / item / risk note, selected
binding intent, selection candidate / state, operator confirmation requirement /
intent, confirmation outcome read model, cancel / reject / defer descriptors,
confirmation boundary result, side-effect proof, and pack result.

Core law:
  - Preview bundle is not UI.
  - Preview item is not rendered product UI.
  - Selection intent is not execution.
  - Selected binding is not invoked binding.
  - Selection state is not runtime state mutation.
  - Operator confirmation requirement is not approval.
  - Operator confirmation intent is not authority.
  - Confirmation outcome read model is not Custos decision.
  - Confirmed state is not permission grant.
  - Cancel / reject / defer descriptors are not runtime transitions.
  - No-approval-activation boundary is not approval runtime.

It does not create UI, product UI, CLI app/runner/entrypoint, TUI runtime/app,
Shell runtime/execution runtime, command parser/router/handler, command
execution/invocation, output writer runtime, render runtime, operator
confirmation runtime, approval runtime, HITL approval activation, authorization,
permission enforcement/grant/denial, Custos/Mneme integration, tool invocation,
workflow dispatch, runtime dispatch, runtime bridge, runtime mutation, surface
switching, navigation mutation, API server, HTTP routes, live endpoint, event
bus, trace/memory/storage writes, source-of-truth store, product behavior,
release scope, LIVE, TRACE_VERIFIED, P2.7-D, P2.8, P2.10, or P2.13.
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
from .shell_binding_read_models import (
    P2_7_B_OFFICIAL_SECTION_NAME,
    P2_7_B_PACK_ID,
    P2_7_B_REPORT_PATH,
    P2_7_B_VALIDATION_REF,
    P27BShellBindingReadModelResult,
    build_p2_7_b_shell_binding_read_model_result,
)
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES

P2_7_C_PACK_ID = "P2.7-C"
P2_7_C_SECTION_ID = "P2.7"
P2_7_C_OFFICIAL_SECTION_NAME = P2_7_B_OFFICIAL_SECTION_NAME
P2_7_C_DEPENDENCY_PACK = P2_7_B_PACK_ID
P2_7_C_NEXT_PACK = "P2.7-D"
P2_7_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.7.11",
    "P2.7.12",
    "P2.7.13",
    "P2.7.14",
    "P2.7.15",
)
P2_7_C_REPORT_FILENAME = (
    "P2_7_C_SHELL_BINDING_PREVIEW_SELECTION_CONFIRMATION_BOUNDARY.md"
)
P2_7_C_REPORT_PATH = f"agent/reports/{P2_7_C_REPORT_FILENAME}"

P2_7_B_COMMIT_REF = "c6cc7a0"
P2_7_B_COMMAND_DESCRIPTOR_SOURCE_REF = "p2_7_b_shell_command_descriptor_read_model"

P2_7_C_PREVIEW_GATE_VERSION = "p2_7_c_shell_binding_preview_gate.v1"
P2_7_C_PREVIEW_BUNDLE_VERSION = "p2_7_c_shell_binding_preview_bundle.v1"
P2_7_C_PREVIEW_ITEM_VERSION = "p2_7_c_shell_binding_preview_item.v1"
P2_7_C_RISK_NOTE_VERSION = "p2_7_c_shell_binding_preview_risk_note.v1"
P2_7_C_SELECTED_INTENT_VERSION = "p2_7_c_shell_binding_selected_intent.v1"
P2_7_C_SELECTION_CANDIDATE_VERSION = "p2_7_c_shell_binding_selection_candidate.v1"
P2_7_C_SELECTION_STATE_VERSION = "p2_7_c_shell_binding_selection_state.v1"
P2_7_C_CONFIRMATION_REQUIREMENT_VERSION = (
    "p2_7_c_shell_binding_confirmation_requirement.v1"
)
P2_7_C_CONFIRMATION_INTENT_VERSION = "p2_7_c_shell_binding_confirmation_intent.v1"
P2_7_C_CONFIRMATION_OUTCOME_VERSION = (
    "p2_7_c_shell_binding_confirmation_outcome_read_model.v1"
)
P2_7_C_CANCEL_DESCRIPTOR_VERSION = "p2_7_c_shell_binding_cancel_descriptor.v1"
P2_7_C_REJECT_DESCRIPTOR_VERSION = "p2_7_c_shell_binding_reject_descriptor.v1"
P2_7_C_DEFER_DESCRIPTOR_VERSION = "p2_7_c_shell_binding_defer_descriptor.v1"
P2_7_C_BOUNDARY_RESULT_VERSION = "p2_7_c_shell_binding_confirmation_boundary_result.v1"
P2_7_C_RESULT_VERSION = "p2_7_c_shell_binding_preview_selection_pack_result.v1"

P2_7_C_TEST_REF = "tests/aurel_shell/test_shell_binding_preview_selection.py"
P2_7_C_VALIDATION_REF = "agent/TESTS.md#P2.7-C"
P2_7_C_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_7_C_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_PREVIEW_GATE_ID = "p2_7_c_shell_binding_preview_gate"
_PREVIEW_BUNDLE_ID = "p2_7_c_shell_binding_preview_bundle"
_PREVIEW_ITEM_ID = "p2_7_c_shell_binding_preview_item"
_RISK_NOTE_ID = "p2_7_c_shell_binding_preview_risk_note"
_SELECTED_INTENT_ID = "p2_7_c_shell_binding_selected_intent"
_SELECTION_CANDIDATE_ID = "p2_7_c_shell_binding_selection_candidate"
_SELECTION_STATE_ID = "p2_7_c_shell_binding_selection_state"
_CONFIRMATION_REQUIREMENT_ID = "p2_7_c_shell_binding_confirmation_requirement"
_CONFIRMATION_INTENT_ID = "p2_7_c_shell_binding_confirmation_intent"
_CONFIRMATION_OUTCOME_ID = "p2_7_c_shell_binding_confirmation_outcome_read_model"
_CANCEL_DESCRIPTOR_ID = "p2_7_c_shell_binding_cancel_descriptor"
_REJECT_DESCRIPTOR_ID = "p2_7_c_shell_binding_reject_descriptor"
_DEFER_DESCRIPTOR_ID = "p2_7_c_shell_binding_defer_descriptor"
_BOUNDARY_RESULT_ID = "p2_7_c_shell_binding_confirmation_boundary_result"


class ShellBindingPreviewGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellBindingPreviewItemKind(str, Enum):
    BINDING_SUMMARY_PREVIEW = "BINDING_SUMMARY_PREVIEW"
    SURFACE_TARGET_PREVIEW = "SURFACE_TARGET_PREVIEW"
    COMMAND_DESCRIPTOR_PREVIEW = "COMMAND_DESCRIPTOR_PREVIEW"
    OUTPUT_PREVIEW = "OUTPUT_PREVIEW"
    RENDER_PREVIEW = "RENDER_PREVIEW"
    AVAILABILITY_PREVIEW = "AVAILABILITY_PREVIEW"
    DEV_FIXTURE_PREVIEW = "DEV_FIXTURE_PREVIEW"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class ShellBindingPreviewRiskKind(str, Enum):
    COMMAND_EXECUTION_DEFERRED = "COMMAND_EXECUTION_DEFERRED"
    APPROVAL_RUNTIME_DEFERRED = "APPROVAL_RUNTIME_DEFERRED"
    PERMISSION_ENFORCEMENT_DEFERRED = "PERMISSION_ENFORCEMENT_DEFERRED"
    RUNTIME_DISPATCH_DEFERRED = "RUNTIME_DISPATCH_DEFERRED"
    CUSTOS_DECISION_DEFERRED = "CUSTOS_DECISION_DEFERRED"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class ShellBindingSelectionMode(str, Enum):
    DESCRIPTOR_ONLY = "DESCRIPTOR_ONLY"
    INTENT_ONLY = "INTENT_ONLY"
    READ_ONLY_SELECTION = "READ_ONLY_SELECTION"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class ShellBindingConfirmationRequirementStatus(str, Enum):
    REQUIRED_CONTRACT_ONLY = "REQUIRED_CONTRACT_ONLY"
    NOT_REQUIRED_CONTRACT_ONLY = "NOT_REQUIRED_CONTRACT_ONLY"
    UNAVAILABLE_APPROVAL_RUNTIME_REQUIRED = "UNAVAILABLE_APPROVAL_RUNTIME_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellBindingConfirmationOutcomeStatus(str, Enum):
    CONFIRMATION_INTENT_RECORDED_CONTRACT_ONLY = (
        "CONFIRMATION_INTENT_RECORDED_CONTRACT_ONLY"
    )
    CANCELLED_CONTRACT_ONLY = "CANCELLED_CONTRACT_ONLY"
    REJECTED_CONTRACT_ONLY = "REJECTED_CONTRACT_ONLY"
    DEFERRED_CONTRACT_ONLY = "DEFERRED_CONTRACT_ONLY"
    UNAVAILABLE_RUNTIME_REQUIRED = "UNAVAILABLE_RUNTIME_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellBindingPreviewSelectionTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    PREVIEW_ONLY = "PREVIEW_ONLY"
    PREVIEW_BUNDLE_ONLY = "PREVIEW_BUNDLE_ONLY"
    PREVIEW_ITEM_ONLY = "PREVIEW_ITEM_ONLY"
    PREVIEW_RISK_NOTE_ONLY = "PREVIEW_RISK_NOTE_ONLY"
    SELECTION_INTENT_ONLY = "SELECTION_INTENT_ONLY"
    SELECTION_CANDIDATE_ONLY = "SELECTION_CANDIDATE_ONLY"
    SELECTION_STATE_ONLY = "SELECTION_STATE_ONLY"
    CONFIRMATION_REQUIREMENT_ONLY = "CONFIRMATION_REQUIREMENT_ONLY"
    CONFIRMATION_INTENT_ONLY = "CONFIRMATION_INTENT_ONLY"
    CONFIRMATION_OUTCOME_READ_MODEL_ONLY = "CONFIRMATION_OUTCOME_READ_MODEL_ONLY"
    CANCEL_DESCRIPTOR_ONLY = "CANCEL_DESCRIPTOR_ONLY"
    REJECT_DESCRIPTOR_ONLY = "REJECT_DESCRIPTOR_ONLY"
    DEFER_DESCRIPTOR_ONLY = "DEFER_DESCRIPTOR_ONLY"
    BOUNDARY_RESULT_ONLY = "BOUNDARY_RESULT_ONLY"
    PREVIEW_GATE_ONLY = "PREVIEW_GATE_ONLY"
    NO_COMMAND_EXECUTION_BOUNDARY = "NO_COMMAND_EXECUTION_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    NO_APPROVAL_ACTIVATION_BOUNDARY = "NO_APPROVAL_ACTIVATION_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_UI = "NOT_UI"
    NOT_PRODUCT_UI = "NOT_PRODUCT_UI"
    NOT_CLI_APP = "NOT_CLI_APP"
    NOT_CLI_RUNNER = "NOT_CLI_RUNNER"
    NOT_CLI_ENTRYPOINT = "NOT_CLI_ENTRYPOINT"
    NOT_TUI_RUNTIME = "NOT_TUI_RUNTIME"
    NOT_TUI_APP = "NOT_TUI_APP"
    NOT_SHELL_RUNTIME = "NOT_SHELL_RUNTIME"
    NOT_SHELL_EXECUTION_RUNTIME = "NOT_SHELL_EXECUTION_RUNTIME"
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
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


# (item_kind, preview_title)
_PREVIEW_ITEM_MANIFEST: tuple[tuple[ShellBindingPreviewItemKind, str], ...] = (
    (ShellBindingPreviewItemKind.BINDING_SUMMARY_PREVIEW, "Binding summary preview"),
    (ShellBindingPreviewItemKind.SURFACE_TARGET_PREVIEW, "Surface target preview"),
    (
        ShellBindingPreviewItemKind.COMMAND_DESCRIPTOR_PREVIEW,
        "Command descriptor preview",
    ),
    (ShellBindingPreviewItemKind.OUTPUT_PREVIEW, "Output preview"),
    (ShellBindingPreviewItemKind.RENDER_PREVIEW, "Render preview"),
    (ShellBindingPreviewItemKind.AVAILABILITY_PREVIEW, "Availability preview"),
)

# (risk_kind, risk_summary, requires_future_pack)
_RISK_NOTE_MANIFEST: tuple[tuple[ShellBindingPreviewRiskKind, str, str], ...] = (
    (
        ShellBindingPreviewRiskKind.COMMAND_EXECUTION_DEFERRED,
        "Command execution is deferred to a future pack",
        P2_7_C_NEXT_PACK,
    ),
    (
        ShellBindingPreviewRiskKind.APPROVAL_RUNTIME_DEFERRED,
        "Approval runtime is deferred to a future pack",
        P2_7_C_NEXT_PACK,
    ),
    (
        ShellBindingPreviewRiskKind.PERMISSION_ENFORCEMENT_DEFERRED,
        "Permission enforcement is deferred to a future pack",
        P2_7_C_NEXT_PACK,
    ),
    (
        ShellBindingPreviewRiskKind.RUNTIME_DISPATCH_DEFERRED,
        "Runtime dispatch is deferred to a future pack",
        P2_7_C_NEXT_PACK,
    ),
    (
        ShellBindingPreviewRiskKind.CUSTOS_DECISION_DEFERRED,
        "Custos decisioning is deferred to a future pack",
        P2_7_C_NEXT_PACK,
    ),
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P27CSideEffectProof(_CanonicalMixin):
    ui_created: bool = False
    product_ui_created: bool = False
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
    product_behavior_claimed: bool = False
    release_scope_claimed: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    p2_7_d_started: bool = False
    p2_8_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellBindingPreviewGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_adapter_expansion_result_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellBindingPreviewGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellBindingPreviewItem(_CanonicalMixin):
    preview_item_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    item_kind: ShellBindingPreviewItemKind
    source_descriptor_ref: str
    preview_title: str
    preview_summary: str
    preview_limitations: tuple[str, ...]
    available_as_preview: bool
    renders_ui: bool
    creates_product_ui: bool
    truth_label: str
    limitations: tuple[str, ...]
    item_hash: str


@dataclass(frozen=True)
class ShellBindingPreviewRiskNote(_CanonicalMixin):
    risk_note_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    risk_kind: ShellBindingPreviewRiskKind
    risk_summary: str
    boundary_refs: tuple[str, ...]
    requires_future_pack: str
    enforces_policy: bool
    activates_approval: bool
    truth_label: str
    limitations: tuple[str, ...]
    risk_hash: str


@dataclass(frozen=True)
class ShellBindingSelectionCandidate(_CanonicalMixin):
    selection_candidate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    candidate_kind: str
    source_preview_ref: str
    source_descriptor_ref: str
    selectable_as_contract: bool
    selectable_as_runtime_action: bool
    requires_confirmation: bool
    truth_label: str
    limitations: tuple[str, ...]
    candidate_hash: str


@dataclass(frozen=True)
class ShellBindingPreviewBundle(_CanonicalMixin):
    preview_bundle_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    source_pack_ref: str
    source_read_model_ref: str
    preview_items: tuple[ShellBindingPreviewItem, ...]
    risk_notes: tuple[ShellBindingPreviewRiskNote, ...]
    selection_candidates: tuple[ShellBindingSelectionCandidate, ...]
    confirmation_requirement_ref: str
    official_surface_set: tuple[str, ...]
    is_ui: bool
    is_product_ui: bool
    truth_label: str
    limitations: tuple[str, ...]
    bundle_hash: str


@dataclass(frozen=True)
class ShellBindingSelectionState(_CanonicalMixin):
    selection_state_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    selection_mode: ShellBindingSelectionMode
    selected_candidate_ref: str
    selected_intent_ref: str
    state_scope: str
    mutates_runtime_state: bool
    mutates_shell_state: bool
    executes_selection: bool
    truth_label: str
    limitations: tuple[str, ...]
    state_hash: str


@dataclass(frozen=True)
class ShellBindingSelectedIntent(_CanonicalMixin):
    selected_intent_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_preview_item_ref: str
    source_selection_candidate_ref: str
    selection_state_ref: str
    selected_binding_ref: str
    intent_scope: str
    invokes_binding: bool
    executes_command: bool
    dispatches_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    intent_hash: str


@dataclass(frozen=True)
class ShellBindingConfirmationRequirement(_CanonicalMixin):
    confirmation_requirement_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    requirement_status: ShellBindingConfirmationRequirementStatus
    source_selected_intent_ref: str
    confirmation_reason: str
    required_before_future_execution: bool
    requires_approval_runtime: bool
    activates_approval: bool
    activates_hitl: bool
    truth_label: str
    limitations: tuple[str, ...]
    requirement_hash: str


@dataclass(frozen=True)
class ShellBindingConfirmationIntent(_CanonicalMixin):
    confirmation_intent_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_requirement_ref: str
    source_selected_intent_ref: str
    intent_status: str
    operator_intent_recorded_as_contract: bool
    grants_authority: bool
    grants_permission: bool
    activates_approval: bool
    executes_binding: bool
    truth_label: str
    limitations: tuple[str, ...]
    intent_hash: str


@dataclass(frozen=True)
class ShellBindingConfirmationOutcomeReadModel(_CanonicalMixin):
    confirmation_outcome_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    outcome_status: ShellBindingConfirmationOutcomeStatus
    source_confirmation_intent_ref: str
    source_selected_intent_ref: str
    confirmed_state_is_contract_only: bool
    is_custos_decision: bool
    is_permission_grant: bool
    is_runtime_transition: bool
    truth_label: str
    limitations: tuple[str, ...]
    outcome_hash: str


@dataclass(frozen=True)
class ShellBindingCancelDescriptor(_CanonicalMixin):
    cancel_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_confirmation_ref: str
    cancel_reason: str
    cancels_runtime: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    cancel_hash: str


@dataclass(frozen=True)
class ShellBindingRejectDescriptor(_CanonicalMixin):
    reject_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_confirmation_ref: str
    reject_reason: str
    denies_permission: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    reject_hash: str


@dataclass(frozen=True)
class ShellBindingDeferDescriptor(_CanonicalMixin):
    defer_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_confirmation_ref: str
    defer_reason: str
    creates_schedule: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    defer_hash: str


@dataclass(frozen=True)
class ShellBindingConfirmationBoundaryResult(_CanonicalMixin):
    confirmation_boundary_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    preview_gate: ShellBindingPreviewGate
    preview_bundle: ShellBindingPreviewBundle
    selected_intent: ShellBindingSelectedIntent
    selection_state: ShellBindingSelectionState
    confirmation_requirement: ShellBindingConfirmationRequirement
    confirmation_intent: ShellBindingConfirmationIntent
    confirmation_outcome: ShellBindingConfirmationOutcomeReadModel
    cancel_descriptor: ShellBindingCancelDescriptor
    reject_descriptor: ShellBindingRejectDescriptor
    defer_descriptor: ShellBindingDeferDescriptor
    creates_ui: bool
    creates_product_ui: bool
    creates_command_execution: bool
    creates_operator_confirmation_runtime: bool
    creates_approval_runtime: bool
    activates_hitl_approval: bool
    creates_permission_enforcement: bool
    creates_custos_decision: bool
    creates_runtime_dispatch: bool
    creates_runtime_mutation: bool
    creates_trace_write: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P27CShellBindingPreviewSelectionResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_7_b_evidence_ref: str
    preview_gate: ShellBindingPreviewGate
    preview_bundle: ShellBindingPreviewBundle
    preview_items: tuple[ShellBindingPreviewItem, ...]
    preview_risk_notes: tuple[ShellBindingPreviewRiskNote, ...]
    selected_intent: ShellBindingSelectedIntent
    selection_candidates: tuple[ShellBindingSelectionCandidate, ...]
    selection_state: ShellBindingSelectionState
    confirmation_requirement: ShellBindingConfirmationRequirement
    confirmation_intent: ShellBindingConfirmationIntent
    confirmation_outcome: ShellBindingConfirmationOutcomeReadModel
    cancel_descriptor: ShellBindingCancelDescriptor
    reject_descriptor: ShellBindingRejectDescriptor
    defer_descriptor: ShellBindingDeferDescriptor
    confirmation_boundary_result: ShellBindingConfirmationBoundaryResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P27CSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


# ---------------------------------------------------------------------------
# P2.7-B evidence reuse (by reference only — no source-of-truth duplication)
# ---------------------------------------------------------------------------


def _p2_7_b_adapter_expansion_ref(result: P27BShellBindingReadModelResult) -> str:
    expansion = result.adapter_expansion_result
    return (
        f"{expansion.adapter_expansion_result_id}:"
        f"hash={expansion.expansion_hash[:12]}"
    )


def _p2_7_b_evidence_ref(result: P27BShellBindingReadModelResult) -> str:
    return f"{P2_7_B_REPORT_PATH}:{result.result_hash[:12]}"


def assert_p2_7_b_read_model_result_available(
    result: P27BShellBindingReadModelResult,
) -> None:
    if result.pack_id != P2_7_B_PACK_ID or result.starts_future_work:
        _reject(
            "P2.7-C requires a P2.7-B read model result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.next_pack != P2_7_C_PACK_ID:
        _reject(
            "P2.7-C requires P2.7-B read model result pointing to P2.7-C",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_shell_binding_preview_gate(
    read_model_result: P27BShellBindingReadModelResult | None = None,
) -> ShellBindingPreviewGate:
    if read_model_result is None:
        read_model_result = build_p2_7_b_shell_binding_read_model_result()
    assert_p2_7_b_read_model_result_available(read_model_result)
    payload: dict[str, Any] = {
        "gate_id": _PREVIEW_GATE_ID,
        "schema_version": P2_7_C_PREVIEW_GATE_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "official_section_name": P2_7_C_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_7_C_DEPENDENCY_PACK,
        "dependency_report_ref": P2_7_B_REPORT_PATH,
        "dependency_commit_ref": P2_7_B_COMMIT_REF,
        "dependency_validation_ref": P2_7_B_VALIDATION_REF,
        "dependency_adapter_expansion_result_ref": _p2_7_b_adapter_expansion_ref(
            read_model_result
        ),
        "dependency_side_effect_proof_ref": "P27BSideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellBindingPreviewGateStatus.READY,
        "truth_label": ShellBindingPreviewSelectionTruthBoundary.PREVIEW_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not preview, select, confirm, or execute any binding",
        ),
    }
    gate = ShellBindingPreviewGate(**payload, gate_hash=_hash_payload(payload))
    assert_preview_gate_depends_on_p2_7_b(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_shell_binding_preview_item(
    item_kind: ShellBindingPreviewItemKind | None = None,
    source_descriptor_ref: str | None = None,
    preview_title: str | None = None,
) -> ShellBindingPreviewItem:
    kind = item_kind or ShellBindingPreviewItemKind.BINDING_SUMMARY_PREVIEW
    title = preview_title or f"{kind.value.replace('_', ' ').title()}"
    payload: dict[str, Any] = {
        "preview_item_id": f"{_PREVIEW_ITEM_ID}_{kind.value.lower()}",
        "schema_version": P2_7_C_PREVIEW_ITEM_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "item_kind": kind,
        "source_descriptor_ref": (
            source_descriptor_ref or P2_7_B_COMMAND_DESCRIPTOR_SOURCE_REF
        ),
        "preview_title": title,
        "preview_summary": (
            f"read-only preview of {kind.value} without rendering product UI"
        ),
        "preview_limitations": (
            "preview item explains intent only",
            "preview item does not render UI or execute a binding",
        ),
        "available_as_preview": True,
        "renders_ui": False,
        "creates_product_ui": False,
        "truth_label": ShellBindingPreviewSelectionTruthBoundary.PREVIEW_ITEM_ONLY.value,
        "limitations": (
            "preview item is not product UI",
            "preview item is not a render runtime",
        ),
    }
    item = ShellBindingPreviewItem(**payload, item_hash=_hash_payload(payload))
    assert_preview_item_is_not_product_ui(item)
    return item


def build_shell_binding_preview_items() -> tuple[ShellBindingPreviewItem, ...]:
    return tuple(
        build_shell_binding_preview_item(item_kind=kind, preview_title=title)
        for kind, title in _PREVIEW_ITEM_MANIFEST
    )


def build_shell_binding_preview_risk_note(
    risk_kind: ShellBindingPreviewRiskKind | None = None,
    risk_summary: str | None = None,
    requires_future_pack: str | None = None,
) -> ShellBindingPreviewRiskNote:
    kind = risk_kind or ShellBindingPreviewRiskKind.COMMAND_EXECUTION_DEFERRED
    summary = risk_summary or f"{kind.value} is deferred to a future pack"
    payload: dict[str, Any] = {
        "risk_note_id": f"{_RISK_NOTE_ID}_{kind.value.lower()}",
        "schema_version": P2_7_C_RISK_NOTE_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "risk_kind": kind,
        "risk_summary": summary,
        "boundary_refs": (
            ShellBindingPreviewSelectionTruthBoundary.NO_COMMAND_EXECUTION_BOUNDARY.value,
            ShellBindingPreviewSelectionTruthBoundary.NO_RUNTIME_DISPATCH_BOUNDARY.value,
            ShellBindingPreviewSelectionTruthBoundary.NO_APPROVAL_ACTIVATION_BOUNDARY.value,
        ),
        "requires_future_pack": requires_future_pack or P2_7_C_NEXT_PACK,
        "enforces_policy": False,
        "activates_approval": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.PREVIEW_RISK_NOTE_ONLY.value
        ),
        "limitations": (
            "risk note is descriptive only",
            "risk note does not enforce policy or activate approval",
        ),
    }
    note = ShellBindingPreviewRiskNote(**payload, risk_hash=_hash_payload(payload))
    assert_preview_risk_note_does_not_enforce_policy(note)
    return note


def build_shell_binding_preview_risk_notes() -> tuple[
    ShellBindingPreviewRiskNote, ...
]:
    return tuple(
        build_shell_binding_preview_risk_note(
            risk_kind=kind,
            risk_summary=summary,
            requires_future_pack=future_pack,
        )
        for kind, summary, future_pack in _RISK_NOTE_MANIFEST
    )


def build_shell_binding_selection_candidate(
    source_preview_item: ShellBindingPreviewItem | None = None,
) -> ShellBindingSelectionCandidate:
    if source_preview_item is None:
        source_preview_item = build_shell_binding_preview_item()
    kind = source_preview_item.item_kind
    payload: dict[str, Any] = {
        "selection_candidate_id": f"{_SELECTION_CANDIDATE_ID}_{kind.value.lower()}",
        "schema_version": P2_7_C_SELECTION_CANDIDATE_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "candidate_kind": kind.value,
        "source_preview_ref": source_preview_item.preview_item_id,
        "source_descriptor_ref": source_preview_item.source_descriptor_ref,
        "selectable_as_contract": True,
        "selectable_as_runtime_action": False,
        "requires_confirmation": True,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.SELECTION_CANDIDATE_ONLY.value
        ),
        "limitations": (
            "candidate is selectable as a contract only",
            "candidate is not a runtime action",
        ),
    }
    candidate = ShellBindingSelectionCandidate(
        **payload,
        candidate_hash=_hash_payload(payload),
    )
    assert_selection_candidate_is_not_runtime_action(candidate)
    return candidate


def build_shell_binding_selection_candidates(
    preview_items: tuple[ShellBindingPreviewItem, ...] | None = None,
) -> tuple[ShellBindingSelectionCandidate, ...]:
    if preview_items is None:
        preview_items = build_shell_binding_preview_items()
    return tuple(
        build_shell_binding_selection_candidate(source_preview_item=item)
        for item in preview_items
    )


def build_shell_binding_preview_bundle(
    read_model_result: P27BShellBindingReadModelResult | None = None,
) -> ShellBindingPreviewBundle:
    if read_model_result is None:
        read_model_result = build_p2_7_b_shell_binding_read_model_result()
    preview_items = build_shell_binding_preview_items()
    risk_notes = build_shell_binding_preview_risk_notes()
    selection_candidates = build_shell_binding_selection_candidates(preview_items)
    source_read_model_ref = _p2_7_b_adapter_expansion_ref(read_model_result)
    payload: dict[str, Any] = {
        "preview_bundle_id": _PREVIEW_BUNDLE_ID,
        "schema_version": P2_7_C_PREVIEW_BUNDLE_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "official_section_name": P2_7_C_OFFICIAL_SECTION_NAME,
        "source_pack_ref": P2_7_B_PACK_ID,
        "source_read_model_ref": source_read_model_ref,
        "preview_items": preview_items,
        "risk_notes": risk_notes,
        "selection_candidates": selection_candidates,
        "confirmation_requirement_ref": _CONFIRMATION_REQUIREMENT_ID,
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "is_ui": False,
        "is_product_ui": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.PREVIEW_BUNDLE_ONLY.value
        ),
        "limitations": (
            "preview bundle is a contract-only intent explanation",
            "preview bundle is not UI or product UI",
        ),
    }
    bundle = ShellBindingPreviewBundle(**payload, bundle_hash=_hash_payload(payload))
    assert_preview_bundle_is_not_ui(bundle)
    return bundle


def build_shell_binding_selection_state(
    selection_mode: ShellBindingSelectionMode | None = None,
    selected_candidate_ref: str | None = None,
) -> ShellBindingSelectionState:
    mode = selection_mode or ShellBindingSelectionMode.INTENT_ONLY
    payload: dict[str, Any] = {
        "selection_state_id": _SELECTION_STATE_ID,
        "schema_version": P2_7_C_SELECTION_STATE_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "selection_mode": mode,
        "selected_candidate_ref": (
            selected_candidate_ref
            or f"{_SELECTION_CANDIDATE_ID}_binding_summary_preview"
        ),
        "selected_intent_ref": _SELECTED_INTENT_ID,
        "state_scope": "SHELL_BINDING_PREVIEW_SELECTION",
        "mutates_runtime_state": False,
        "mutates_shell_state": False,
        "executes_selection": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.SELECTION_STATE_ONLY.value
        ),
        "limitations": (
            "selection state is a contract-only intent state",
            "selection state does not mutate runtime or shell state",
        ),
    }
    state = ShellBindingSelectionState(**payload, state_hash=_hash_payload(payload))
    assert_selection_state_does_not_mutate_runtime(state)
    return state


def build_shell_binding_selected_intent(
    source_preview_item: ShellBindingPreviewItem | None = None,
    source_selection_candidate: ShellBindingSelectionCandidate | None = None,
    selection_state: ShellBindingSelectionState | None = None,
) -> ShellBindingSelectedIntent:
    if source_preview_item is None:
        source_preview_item = build_shell_binding_preview_item()
    if source_selection_candidate is None:
        source_selection_candidate = build_shell_binding_selection_candidate(
            source_preview_item=source_preview_item
        )
    if selection_state is None:
        selection_state = build_shell_binding_selection_state()
    payload: dict[str, Any] = {
        "selected_intent_id": _SELECTED_INTENT_ID,
        "schema_version": P2_7_C_SELECTED_INTENT_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "source_preview_item_ref": source_preview_item.preview_item_id,
        "source_selection_candidate_ref": (
            source_selection_candidate.selection_candidate_id
        ),
        "selection_state_ref": selection_state.selection_state_id,
        "selected_binding_ref": source_preview_item.source_descriptor_ref,
        "intent_scope": "SHELL_BINDING_PREVIEW_SELECTION",
        "invokes_binding": False,
        "executes_command": False,
        "dispatches_runtime": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.SELECTION_INTENT_ONLY.value
        ),
        "limitations": (
            "selected intent is a contract-only selection",
            "selected binding is not an invoked binding",
        ),
    }
    intent = ShellBindingSelectedIntent(**payload, intent_hash=_hash_payload(payload))
    assert_selection_intent_is_not_execution(intent)
    assert_selected_binding_is_not_invoked_binding(intent)
    return intent


def build_shell_binding_confirmation_requirement(
    requirement_status: ShellBindingConfirmationRequirementStatus | None = None,
    source_selected_intent: ShellBindingSelectedIntent | None = None,
) -> ShellBindingConfirmationRequirement:
    status = (
        requirement_status
        or ShellBindingConfirmationRequirementStatus.REQUIRED_CONTRACT_ONLY
    )
    intent_ref = (
        source_selected_intent.selected_intent_id
        if source_selected_intent is not None
        else _SELECTED_INTENT_ID
    )
    payload: dict[str, Any] = {
        "confirmation_requirement_id": _CONFIRMATION_REQUIREMENT_ID,
        "schema_version": P2_7_C_CONFIRMATION_REQUIREMENT_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "requirement_status": status,
        "source_selected_intent_ref": intent_ref,
        "confirmation_reason": (
            "future binding execution must pass operator confirmation"
        ),
        "required_before_future_execution": True,
        "requires_approval_runtime": False,
        "activates_approval": False,
        "activates_hitl": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.CONFIRMATION_REQUIREMENT_ONLY.value
        ),
        "limitations": (
            "confirmation requirement is a contract-only boundary marker",
            "confirmation requirement is not approval and activates no HITL",
        ),
    }
    requirement = ShellBindingConfirmationRequirement(
        **payload,
        requirement_hash=_hash_payload(payload),
    )
    assert_confirmation_requirement_is_not_approval(requirement)
    return requirement


def build_shell_binding_confirmation_intent(
    source_requirement: ShellBindingConfirmationRequirement | None = None,
    source_selected_intent: ShellBindingSelectedIntent | None = None,
) -> ShellBindingConfirmationIntent:
    requirement_ref = (
        source_requirement.confirmation_requirement_id
        if source_requirement is not None
        else _CONFIRMATION_REQUIREMENT_ID
    )
    intent_ref = (
        source_selected_intent.selected_intent_id
        if source_selected_intent is not None
        else _SELECTED_INTENT_ID
    )
    payload: dict[str, Any] = {
        "confirmation_intent_id": _CONFIRMATION_INTENT_ID,
        "schema_version": P2_7_C_CONFIRMATION_INTENT_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "source_requirement_ref": requirement_ref,
        "source_selected_intent_ref": intent_ref,
        "intent_status": (
            ShellBindingConfirmationOutcomeStatus
            .CONFIRMATION_INTENT_RECORDED_CONTRACT_ONLY.value
        ),
        "operator_intent_recorded_as_contract": True,
        "grants_authority": False,
        "grants_permission": False,
        "activates_approval": False,
        "executes_binding": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.CONFIRMATION_INTENT_ONLY.value
        ),
        "limitations": (
            "confirmation intent records operator intent as contract only",
            "confirmation intent grants no authority or permission",
        ),
    }
    intent = ShellBindingConfirmationIntent(
        **payload,
        intent_hash=_hash_payload(payload),
    )
    assert_confirmation_intent_is_not_authority(intent)
    return intent


def build_shell_binding_confirmation_outcome_read_model(
    outcome_status: ShellBindingConfirmationOutcomeStatus | None = None,
    source_confirmation_intent: ShellBindingConfirmationIntent | None = None,
    source_selected_intent: ShellBindingSelectedIntent | None = None,
) -> ShellBindingConfirmationOutcomeReadModel:
    status = (
        outcome_status
        or ShellBindingConfirmationOutcomeStatus
        .CONFIRMATION_INTENT_RECORDED_CONTRACT_ONLY
    )
    confirmation_intent_ref = (
        source_confirmation_intent.confirmation_intent_id
        if source_confirmation_intent is not None
        else _CONFIRMATION_INTENT_ID
    )
    selected_intent_ref = (
        source_selected_intent.selected_intent_id
        if source_selected_intent is not None
        else _SELECTED_INTENT_ID
    )
    payload: dict[str, Any] = {
        "confirmation_outcome_id": _CONFIRMATION_OUTCOME_ID,
        "schema_version": P2_7_C_CONFIRMATION_OUTCOME_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "outcome_status": status,
        "source_confirmation_intent_ref": confirmation_intent_ref,
        "source_selected_intent_ref": selected_intent_ref,
        "confirmed_state_is_contract_only": True,
        "is_custos_decision": False,
        "is_permission_grant": False,
        "is_runtime_transition": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary
            .CONFIRMATION_OUTCOME_READ_MODEL_ONLY.value
        ),
        "limitations": (
            "confirmation outcome is a read model only",
            "confirmation outcome is not a Custos decision or permission grant",
        ),
    }
    outcome = ShellBindingConfirmationOutcomeReadModel(
        **payload,
        outcome_hash=_hash_payload(payload),
    )
    assert_confirmation_outcome_is_not_custos_decision(outcome)
    assert_confirmed_state_is_not_permission_grant(outcome)
    return outcome


def build_shell_binding_cancel_descriptor(
    source_confirmation_ref: str | None = None,
) -> ShellBindingCancelDescriptor:
    payload: dict[str, Any] = {
        "cancel_descriptor_id": _CANCEL_DESCRIPTOR_ID,
        "schema_version": P2_7_C_CANCEL_DESCRIPTOR_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "source_confirmation_ref": source_confirmation_ref or _CONFIRMATION_OUTCOME_ID,
        "cancel_reason": "operator may cancel the previewed selection",
        "cancels_runtime": False,
        "mutates_runtime": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.CANCEL_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "cancel descriptor describes a possible future choice",
            "cancel descriptor cancels no runtime and mutates no runtime",
        ),
    }
    descriptor = ShellBindingCancelDescriptor(
        **payload,
        cancel_hash=_hash_payload(payload),
    )
    assert_cancel_reject_defer_are_not_runtime_transitions(
        cancel=descriptor,
        reject=None,
        defer=None,
    )
    return descriptor


def build_shell_binding_reject_descriptor(
    source_confirmation_ref: str | None = None,
) -> ShellBindingRejectDescriptor:
    payload: dict[str, Any] = {
        "reject_descriptor_id": _REJECT_DESCRIPTOR_ID,
        "schema_version": P2_7_C_REJECT_DESCRIPTOR_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "source_confirmation_ref": source_confirmation_ref or _CONFIRMATION_OUTCOME_ID,
        "reject_reason": "operator may reject the previewed selection",
        "denies_permission": False,
        "mutates_runtime": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.REJECT_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "reject descriptor describes a possible future choice",
            "reject descriptor denies no permission and mutates no runtime",
        ),
    }
    descriptor = ShellBindingRejectDescriptor(
        **payload,
        reject_hash=_hash_payload(payload),
    )
    assert_cancel_reject_defer_are_not_runtime_transitions(
        cancel=None,
        reject=descriptor,
        defer=None,
    )
    return descriptor


def build_shell_binding_defer_descriptor(
    source_confirmation_ref: str | None = None,
) -> ShellBindingDeferDescriptor:
    payload: dict[str, Any] = {
        "defer_descriptor_id": _DEFER_DESCRIPTOR_ID,
        "schema_version": P2_7_C_DEFER_DESCRIPTOR_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "source_confirmation_ref": source_confirmation_ref or _CONFIRMATION_OUTCOME_ID,
        "defer_reason": "operator may defer the previewed selection",
        "creates_schedule": False,
        "mutates_runtime": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.DEFER_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "defer descriptor describes a possible future choice",
            "defer descriptor creates no schedule and mutates no runtime",
        ),
    }
    descriptor = ShellBindingDeferDescriptor(
        **payload,
        defer_hash=_hash_payload(payload),
    )
    assert_cancel_reject_defer_are_not_runtime_transitions(
        cancel=None,
        reject=None,
        defer=descriptor,
    )
    return descriptor


def build_shell_binding_confirmation_boundary_result(
    read_model_result: P27BShellBindingReadModelResult | None = None,
) -> ShellBindingConfirmationBoundaryResult:
    if read_model_result is None:
        read_model_result = build_p2_7_b_shell_binding_read_model_result()
    preview_gate = build_shell_binding_preview_gate(read_model_result)
    preview_bundle = build_shell_binding_preview_bundle(read_model_result)
    source_item = preview_bundle.preview_items[0]
    source_candidate = preview_bundle.selection_candidates[0]
    selection_state = build_shell_binding_selection_state(
        selected_candidate_ref=source_candidate.selection_candidate_id,
    )
    selected_intent = build_shell_binding_selected_intent(
        source_preview_item=source_item,
        source_selection_candidate=source_candidate,
        selection_state=selection_state,
    )
    confirmation_requirement = build_shell_binding_confirmation_requirement(
        source_selected_intent=selected_intent,
    )
    confirmation_intent = build_shell_binding_confirmation_intent(
        source_requirement=confirmation_requirement,
        source_selected_intent=selected_intent,
    )
    confirmation_outcome = build_shell_binding_confirmation_outcome_read_model(
        source_confirmation_intent=confirmation_intent,
        source_selected_intent=selected_intent,
    )
    cancel_descriptor = build_shell_binding_cancel_descriptor(
        source_confirmation_ref=confirmation_outcome.confirmation_outcome_id,
    )
    reject_descriptor = build_shell_binding_reject_descriptor(
        source_confirmation_ref=confirmation_outcome.confirmation_outcome_id,
    )
    defer_descriptor = build_shell_binding_defer_descriptor(
        source_confirmation_ref=confirmation_outcome.confirmation_outcome_id,
    )
    payload: dict[str, Any] = {
        "confirmation_boundary_result_id": _BOUNDARY_RESULT_ID,
        "schema_version": P2_7_C_BOUNDARY_RESULT_VERSION,
        "section_id": P2_7_C_SECTION_ID,
        "created_for_pack": P2_7_C_PACK_ID,
        "official_section_name": P2_7_C_OFFICIAL_SECTION_NAME,
        "preview_gate": preview_gate,
        "preview_bundle": preview_bundle,
        "selected_intent": selected_intent,
        "selection_state": selection_state,
        "confirmation_requirement": confirmation_requirement,
        "confirmation_intent": confirmation_intent,
        "confirmation_outcome": confirmation_outcome,
        "cancel_descriptor": cancel_descriptor,
        "reject_descriptor": reject_descriptor,
        "defer_descriptor": defer_descriptor,
        "creates_ui": False,
        "creates_product_ui": False,
        "creates_command_execution": False,
        "creates_operator_confirmation_runtime": False,
        "creates_approval_runtime": False,
        "activates_hitl_approval": False,
        "creates_permission_enforcement": False,
        "creates_custos_decision": False,
        "creates_runtime_dispatch": False,
        "creates_runtime_mutation": False,
        "creates_trace_write": False,
        "creates_product_behavior": False,
        "truth_label": (
            ShellBindingPreviewSelectionTruthBoundary.BOUNDARY_RESULT_ONLY.value
        ),
        "limitations": (
            "confirmation boundary result bundles contracts only",
            "result creates no execution, approval, or runtime behavior",
        ),
    }
    result = ShellBindingConfirmationBoundaryResult(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_confirmation_boundary_result_is_not_execution(result)
    return result


def build_p2_7_c_side_effect_proof() -> P27CSideEffectProof:
    return P27CSideEffectProof()


def build_p2_7_c_shell_binding_preview_selection_result() -> (
    P27CShellBindingPreviewSelectionResult
):
    read_model_result = build_p2_7_b_shell_binding_read_model_result()
    boundary = build_shell_binding_confirmation_boundary_result(read_model_result)
    side_effects = build_p2_7_c_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_7_C_RESULT_VERSION,
        "pack_id": P2_7_C_PACK_ID,
        "section_id": P2_7_C_SECTION_ID,
        "official_section_name": P2_7_C_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_7_C_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_7_C_DEPENDENCY_PACK,
        "p2_7_b_evidence_ref": _p2_7_b_evidence_ref(read_model_result),
        "preview_gate": boundary.preview_gate,
        "preview_bundle": boundary.preview_bundle,
        "preview_items": boundary.preview_bundle.preview_items,
        "preview_risk_notes": boundary.preview_bundle.risk_notes,
        "selected_intent": boundary.selected_intent,
        "selection_candidates": boundary.preview_bundle.selection_candidates,
        "selection_state": boundary.selection_state,
        "confirmation_requirement": boundary.confirmation_requirement,
        "confirmation_intent": boundary.confirmation_intent,
        "confirmation_outcome": boundary.confirmation_outcome,
        "cancel_descriptor": boundary.cancel_descriptor,
        "reject_descriptor": boundary.reject_descriptor,
        "defer_descriptor": boundary.defer_descriptor,
        "confirmation_boundary_result": boundary,
        "truth_labels": tuple(
            label.value for label in ShellBindingPreviewSelectionTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_7_C_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P27CShellBindingPreviewSelectionResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_7_c_does_not_start_future_work(result)
    assert_p2_7_c_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_7_c_result(
    result: P27CShellBindingPreviewSelectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_c_shell_binding_preview_selection_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_binding_preview_summary(
    result: P27CShellBindingPreviewSelectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_7_c_shell_binding_preview_selection_result()
    boundary = result.confirmation_boundary_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.preview_gate.gate_status.value}",
            f"preview_items={len(result.preview_items)}",
            f"risk_notes={len(result.preview_risk_notes)}",
            f"selection_candidates={len(result.selection_candidates)}",
            f"checkpoints={len(result.covered_checkpoints)}",
            f"next={result.next_pack}",
            f"ui={str(boundary.creates_ui).lower()}",
            f"product_ui={str(boundary.creates_product_ui).lower()}",
            f"command_execution={str(boundary.creates_command_execution).lower()}",
            (
                "operator_confirmation_runtime="
                f"{str(boundary.creates_operator_confirmation_runtime).lower()}"
            ),
            f"approval_runtime={str(boundary.creates_approval_runtime).lower()}",
            f"hitl_approval={str(boundary.activates_hitl_approval).lower()}",
            (
                "permission_enforcement="
                f"{str(boundary.creates_permission_enforcement).lower()}"
            ),
            f"custos_decision={str(boundary.creates_custos_decision).lower()}",
            f"runtime_dispatch={str(boundary.creates_runtime_dispatch).lower()}",
            f"trace_write={str(boundary.creates_trace_write).lower()}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


def assert_preview_gate_depends_on_p2_7_b(gate: ShellBindingPreviewGate) -> None:
    if (
        gate.dependency_pack != P2_7_C_DEPENDENCY_PACK
        or not gate.repo_evidence_gate_passed
    ):
        _reject(
            "P2.7-C preview gate must depend on passed P2.7-B repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_adapter_expansion_result_ref
        or not gate.dependency_side_effect_proof_ref
    ):
        _reject(
            "P2.7-C preview gate must reference P2.7-B adapter expansion evidence",
            field="dependency_adapter_expansion_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellBindingPreviewGate,
) -> None:
    if (
        gate.omni_evidence_required
        or not gate.omni_evidence_ignored_by_operator_instruction
    ):
        _reject(
            "P2.7-C gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_preview_bundle_is_not_ui(bundle: ShellBindingPreviewBundle) -> None:
    if bundle.is_ui or bundle.is_product_ui:
        _reject(
            "Preview bundle must not be UI or product UI",
            field="is_ui",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_preview_item_is_not_product_ui(item: ShellBindingPreviewItem) -> None:
    if item.renders_ui or item.creates_product_ui:
        _reject(
            "Preview item must not render UI or create product UI",
            field="renders_ui",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_preview_risk_note_does_not_enforce_policy(
    note: ShellBindingPreviewRiskNote,
) -> None:
    if note.enforces_policy or note.activates_approval:
        _reject(
            "Preview risk note must not enforce policy or activate approval",
            field="enforces_policy",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selection_candidate_is_not_runtime_action(
    candidate: ShellBindingSelectionCandidate,
) -> None:
    if candidate.selectable_as_runtime_action or not candidate.selectable_as_contract:
        _reject(
            "Selection candidate must be selectable as contract only",
            field="selectable_as_runtime_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selection_intent_is_not_execution(
    intent: ShellBindingSelectedIntent,
) -> None:
    if intent.executes_command or intent.dispatches_runtime:
        _reject(
            "Selected binding intent must not execute commands or dispatch runtime",
            field="executes_command",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selected_binding_is_not_invoked_binding(
    intent: ShellBindingSelectedIntent,
) -> None:
    if intent.invokes_binding:
        _reject(
            "Selected binding must not be an invoked binding",
            field="invokes_binding",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selection_state_does_not_mutate_runtime(
    state: ShellBindingSelectionState,
) -> None:
    if (
        state.mutates_runtime_state
        or state.mutates_shell_state
        or state.executes_selection
    ):
        _reject(
            "Selection state must not mutate runtime/shell state or execute selection",
            field="mutates_runtime_state",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmation_requirement_is_not_approval(
    requirement: ShellBindingConfirmationRequirement,
) -> None:
    if (
        requirement.requires_approval_runtime
        or requirement.activates_approval
        or requirement.activates_hitl
    ):
        _reject(
            "Confirmation requirement must not be approval or activate HITL",
            field="requires_approval_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmation_intent_is_not_authority(
    intent: ShellBindingConfirmationIntent,
) -> None:
    if (
        intent.grants_authority
        or intent.grants_permission
        or intent.activates_approval
        or intent.executes_binding
    ):
        _reject(
            "Confirmation intent must not grant authority/permission or execute",
            field="grants_authority",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmation_outcome_is_not_custos_decision(
    outcome: ShellBindingConfirmationOutcomeReadModel,
) -> None:
    if outcome.is_custos_decision or outcome.is_runtime_transition:
        _reject(
            "Confirmation outcome must not be a Custos decision or runtime transition",
            field="is_custos_decision",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmed_state_is_not_permission_grant(
    outcome: ShellBindingConfirmationOutcomeReadModel,
) -> None:
    if outcome.is_permission_grant or not outcome.confirmed_state_is_contract_only:
        _reject(
            "Confirmed state must be contract-only and not a permission grant",
            field="is_permission_grant",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_cancel_reject_defer_are_not_runtime_transitions(
    cancel: ShellBindingCancelDescriptor | None,
    reject: ShellBindingRejectDescriptor | None,
    defer: ShellBindingDeferDescriptor | None,
) -> None:
    if cancel is not None and (cancel.cancels_runtime or cancel.mutates_runtime):
        _reject(
            "Cancel descriptor must not cancel or mutate runtime",
            field="cancels_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if reject is not None and (reject.denies_permission or reject.mutates_runtime):
        _reject(
            "Reject descriptor must not deny permission or mutate runtime",
            field="denies_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if defer is not None and (defer.creates_schedule or defer.mutates_runtime):
        _reject(
            "Defer descriptor must not create a schedule or mutate runtime",
            field="creates_schedule",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmation_boundary_result_is_not_execution(
    result: ShellBindingConfirmationBoundaryResult,
) -> None:
    if any(
        (
            result.creates_ui,
            result.creates_product_ui,
            result.creates_command_execution,
            result.creates_operator_confirmation_runtime,
            result.creates_approval_runtime,
            result.activates_hitl_approval,
            result.creates_permission_enforcement,
            result.creates_custos_decision,
            result.creates_runtime_dispatch,
            result.creates_runtime_mutation,
            result.creates_trace_write,
            result.creates_product_behavior,
        )
    ):
        _reject(
            "Confirmation boundary result must not create execution or runtime behavior",
            field="creates_command_execution",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_7_c_does_not_start_future_work(
    result: P27CShellBindingPreviewSelectionResult,
) -> None:
    proof = result.side_effect_proof
    if result.starts_future_work or any(
        (
            proof.p2_7_d_started,
            proof.p2_8_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.7-C must not start P2.7-D, P2.8, P2.10, or P2.13",
            field="starts_future_work",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_7_c_side_effects_all_false(proof: P27CSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name) is not False:
            _reject(
                f"P2.7-C side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )

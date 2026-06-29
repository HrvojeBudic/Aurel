"""P2.4-C command proposal / selection / preview / no-execution boundary.

Contract-only command proposal over the P2.4-B command result-set read model.
Defines selection intent, proposal, input/impact/requirement previews, and
no-execution boundary without command palette UI, preview panel UI, command
execution, approval activation, permission enforcement, storage, memory/trace
writes, product behavior, release scope, or runtime mutation.
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
from .global_command_discovery import (
    COMMAND_EXECUTION_UNAVAILABLE_REASON,
    P2_4_B_PACK_ID,
    P2_4_B_REPORT_PATH,
    P2_4_B_SECTION_ID,
    GlobalCommandResultItem,
    GlobalCommandResultSet,
    build_global_command_result_set,
)
from .global_command_registry import (
    GlobalCommandAvailabilityStatus,
    GlobalCommandInputContract,
    GlobalCommandKind,
    GlobalCommandScopeKind,
    build_p2_4_a_global_command_foundation_result,
)
from .read_model import detect_surface_taxonomy_drift

P2_4_C_PACK_ID = "P2.4-C"
P2_4_C_SECTION_ID = P2_4_B_SECTION_ID
P2_4_C_OFFICIAL_SECTION_NAME = "Command Palette / Global Commands"
P2_4_C_DEPENDENCY_PACK = P2_4_B_PACK_ID
P2_4_C_NEXT_PACK = "P2.4-D"
P2_4_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.4.11",
    "P2.4.12",
    "P2.4.13",
    "P2.4.14",
    "P2.4.15",
)
P2_4_C_REPORT_FILENAME = "P2_4_C_COMMAND_PROPOSAL_NO_EXECUTION.md"
P2_4_C_REPORT_PATH = f"agent/reports/{P2_4_C_REPORT_FILENAME}"

P2_4_C_GATE_VERSION = "p2_4_c_command_proposal_gate.v1"
P2_4_C_SELECTION_VERSION = "p2_4_c_global_command_selection_intent.v1"
P2_4_C_PROPOSAL_VERSION = "p2_4_c_global_command_proposal.v1"
P2_4_C_INPUT_PREVIEW_VERSION = "p2_4_c_global_command_input_preview.v1"
P2_4_C_IMPACT_PREVIEW_VERSION = "p2_4_c_global_command_impact_preview.v1"
P2_4_C_REQUIREMENT_PREVIEW_VERSION = "p2_4_c_global_command_requirement_preview.v1"
P2_4_C_NO_EXECUTION_VERSION = "p2_4_c_global_command_no_execution_boundary.v1"
P2_4_C_PROPOSAL_RESULT_VERSION = "p2_4_c_global_command_proposal_result.v1"
P2_4_C_RESULT_VERSION = "p2_4_c_command_proposal_result.v1"

P2_4_B_COMMIT_REF = "526c1b78f7a673ced0b2928cc67ecac409bfc4ec"

_SELECTION_NON_GOALS: tuple[str, ...] = (
    "no_execution",
    "no_invocation",
    "no_operator_consent",
    "no_approval",
)
_PROPOSAL_NON_GOALS: tuple[str, ...] = (
    "no_approval",
    "no_authorization",
    "no_command_execution",
    "no_handler_invocation",
)
_INPUT_PREVIEW_NON_GOALS: tuple[str, ...] = (
    "no_invocation",
    "no_handler_invocation",
    "no_validation_runtime",
    "no_command_execution",
)
_IMPACT_PREVIEW_NON_GOALS: tuple[str, ...] = (
    "no_runtime_simulation",
    "no_runtime_mutation",
    "no_memory_write",
    "no_trace_write",
    "no_storage_write",
)
_REQUIREMENT_PREVIEW_NON_GOALS: tuple[str, ...] = (
    "no_permission_decision",
    "no_permission_grant",
    "no_permission_denial",
    "no_approval_activation",
)
_NO_EXECUTION_NON_GOALS: tuple[str, ...] = (
    "no_command_execution",
    "no_approval_activation",
    "no_permission_enforcement",
    "no_route_execution",
    "no_handler_invocation",
    "no_tool_invocation",
    "no_workflow_dispatch",
    "no_runtime_mutation",
    "no_storage_write",
    "no_memory_write",
    "no_trace_write",
)
_PROPOSAL_RESULT_NON_GOALS: tuple[str, ...] = (
    "no_command_execution_result",
    "no_command_palette_ui",
    "no_preview_ui",
    "no_source_of_truth",
    "no_runtime_mutation",
)


class GlobalCommandProposalGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class GlobalCommandSelectionSource(str, Enum):
    RESULT_SET_ITEM = "RESULT_SET_ITEM"
    DIRECT_COMMAND_ID = "DIRECT_COMMAND_ID"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandProposalStatus(str, Enum):
    READY_FOR_PREVIEW = "READY_FOR_PREVIEW"
    UNAVAILABLE_FOR_EXECUTION = "UNAVAILABLE_FOR_EXECUTION"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class GlobalCommandInputPreviewStatus(str, Enum):
    READY = "READY"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandRequirementKind(str, Enum):
    INPUT_REQUIRED = "INPUT_REQUIRED"
    SURFACE_CONTEXT_REQUIRED = "SURFACE_CONTEXT_REQUIRED"
    OPERATOR_CONFIRMATION_REQUIRED_LATER = "OPERATOR_CONFIRMATION_REQUIRED_LATER"
    APPROVAL_REQUIRED_LATER = "APPROVAL_REQUIRED_LATER"
    POLICY_REQUIRED_LATER = "POLICY_REQUIRED_LATER"
    EXECUTION_RUNTIME_REQUIRED_LATER = "EXECUTION_RUNTIME_REQUIRED_LATER"
    TRACE_BINDING_REQUIRED_LATER = "TRACE_BINDING_REQUIRED_LATER"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandProposalResultStatus(str, Enum):
    READY = "READY"
    UNAVAILABLE_FOR_EXECUTION = "UNAVAILABLE_FOR_EXECUTION"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class GlobalCommandProposalTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_SELECTION_UI = "NOT_SELECTION_UI"
    NOT_PREVIEW_UI = "NOT_PREVIEW_UI"
    NOT_COMMAND_PALETTE_UI = "NOT_COMMAND_PALETTE_UI"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_COMMAND_HANDLER = "NOT_COMMAND_HANDLER"
    NOT_INVOCATION = "NOT_INVOCATION"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_RUNTIME_SIMULATION = "NOT_RUNTIME_SIMULATION"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    INPUT_PREVIEW_ONLY = "INPUT_PREVIEW_ONLY"
    IMPACT_PREVIEW_ONLY = "IMPACT_PREVIEW_ONLY"
    REQUIREMENT_PREVIEW_ONLY = "REQUIREMENT_PREVIEW_ONLY"
    NO_EXECUTION_BOUNDARY = "NO_EXECUTION_BOUNDARY"
    NOT_COMMAND_EXECUTION_RESULT = "NOT_COMMAND_EXECUTION_RESULT"
    NOT_EXECUTION = "NOT_EXECUTION"


@dataclass(frozen=True)
class P24CSideEffectProof(_CanonicalMixin):
    command_palette_ui_created: bool = False
    selection_ui_created: bool = False
    preview_panel_ui_created: bool = False
    confirmation_modal_created: bool = False
    frontend_ui_created: bool = False
    browser_ui_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    keyboard_listener_created: bool = False
    shortcut_handler_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    surface_runtime_switch_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
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
    p2_4_d_started: bool = False
    p2_5_started: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class GlobalCommandProposalGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_result_set_ref: str
    dependency_unavailable_reason_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: GlobalCommandProposalGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class GlobalCommandSelectionIntent(_CanonicalMixin):
    selection_id: str
    schema_version: str
    selection_source: GlobalCommandSelectionSource
    selected_command_id: str
    selected_result_item_ref: str
    query_ref: str
    result_set_ref: str
    selected_at_label: str
    is_execution: bool
    is_invocation: bool
    is_operator_consent: bool
    is_approval: bool
    truth_label: str
    limitations: tuple[str, ...]
    selection_hash: str


@dataclass(frozen=True)
class GlobalCommandProposal(_CanonicalMixin):
    proposal_id: str
    schema_version: str
    selection_intent_ref: str
    command_id: str
    command_label: str
    command_kind: GlobalCommandKind
    surface_target: str
    scope: GlobalCommandScopeKind
    availability_status: GlobalCommandAvailabilityStatus
    unavailable_reason: str
    input_preview_ref: str
    impact_preview_ref: str
    requirement_preview_refs: tuple[str, ...]
    proposal_status: GlobalCommandProposalStatus
    is_approval: bool
    is_authorization: bool
    executes_command: bool
    truth_label: str
    limitations: tuple[str, ...]
    proposal_hash: str


@dataclass(frozen=True)
class GlobalCommandInputPreview(_CanonicalMixin):
    input_preview_id: str
    schema_version: str
    command_id: str
    input_contract_ref: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    provided_inputs: tuple[str, ...]
    input_preview_status: GlobalCommandInputPreviewStatus
    is_invocation: bool
    invokes_handler: bool
    executes_validation_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    input_preview_hash: str


@dataclass(frozen=True)
class GlobalCommandImpactPreview(_CanonicalMixin):
    impact_preview_id: str
    schema_version: str
    command_id: str
    declared_intent: str
    declared_target: str
    declared_scope: str
    requirement_previews: tuple[str, ...]
    unavailable_reason: str
    is_runtime_simulation: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    impact_preview_hash: str


@dataclass(frozen=True)
class GlobalCommandRequirementPreview(_CanonicalMixin):
    requirement_id: str
    schema_version: str
    command_id: str
    requirement_kind: GlobalCommandRequirementKind
    description: str
    required_later: bool
    available_now: bool
    unavailable_reason: str
    is_permission_decision: bool
    grants_permission: bool
    denies_permission: bool
    activates_approval: bool
    truth_label: str
    limitations: tuple[str, ...]
    requirement_hash: str


@dataclass(frozen=True)
class GlobalCommandNoExecutionBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    command_id: str
    proposal_id: str
    boundary_active: bool
    execution_allowed: bool
    approval_activated: bool
    permission_enforced: bool
    route_executed: bool
    handler_invoked: bool
    tool_invoked: bool
    workflow_dispatched: bool
    runtime_mutated: bool
    memory_written: bool
    trace_written: bool
    storage_written: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class GlobalCommandProposalResult(_CanonicalMixin):
    proposal_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    selection_intent: GlobalCommandSelectionIntent
    proposal: GlobalCommandProposal
    input_preview: GlobalCommandInputPreview
    impact_preview: GlobalCommandImpactPreview
    requirement_previews: tuple[GlobalCommandRequirementPreview, ...]
    no_execution_boundary: GlobalCommandNoExecutionBoundary
    result_status: GlobalCommandProposalResultStatus
    is_command_execution_result: bool
    is_command_palette_ui: bool
    is_preview_ui: bool
    is_source_of_truth: bool
    executes_commands: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    proposal_result_hash: str


@dataclass(frozen=True)
class P24CCommandProposalResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    proposal_gate: GlobalCommandProposalGate
    selection_intent: GlobalCommandSelectionIntent
    proposal: GlobalCommandProposal
    input_preview: GlobalCommandInputPreview
    impact_preview: GlobalCommandImpactPreview
    requirement_previews: tuple[GlobalCommandRequirementPreview, ...]
    no_execution_boundary: GlobalCommandNoExecutionBoundary
    proposal_result: GlobalCommandProposalResult
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P24CSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _input_contract_for_command(command_id: str) -> GlobalCommandInputContract | None:
    foundation = build_p2_4_a_global_command_foundation_result()
    for contract in foundation.input_contract_records:
        if contract.command_id == command_id:
            return contract
    return None


def _default_requirement_kinds() -> tuple[GlobalCommandRequirementKind, ...]:
    return (
        GlobalCommandRequirementKind.INPUT_REQUIRED,
        GlobalCommandRequirementKind.SURFACE_CONTEXT_REQUIRED,
        GlobalCommandRequirementKind.OPERATOR_CONFIRMATION_REQUIRED_LATER,
        GlobalCommandRequirementKind.APPROVAL_REQUIRED_LATER,
        GlobalCommandRequirementKind.POLICY_REQUIRED_LATER,
        GlobalCommandRequirementKind.EXECUTION_RUNTIME_REQUIRED_LATER,
        GlobalCommandRequirementKind.TRACE_BINDING_REQUIRED_LATER,
    )


def _requirement_description(kind: GlobalCommandRequirementKind) -> str:
    descriptions = {
        GlobalCommandRequirementKind.INPUT_REQUIRED: (
            "Required inputs must be supplied before any future execution layer."
        ),
        GlobalCommandRequirementKind.SURFACE_CONTEXT_REQUIRED: (
            "Surface context must be established before any future execution layer."
        ),
        GlobalCommandRequirementKind.OPERATOR_CONFIRMATION_REQUIRED_LATER: (
            "Operator confirmation would be required later; not captured as consent here."
        ),
        GlobalCommandRequirementKind.APPROVAL_REQUIRED_LATER: (
            "Approval runtime would be required later; no approval is activated here."
        ),
        GlobalCommandRequirementKind.POLICY_REQUIRED_LATER: (
            "Policy evaluation would be required later; no policy decision here."
        ),
        GlobalCommandRequirementKind.EXECUTION_RUNTIME_REQUIRED_LATER: (
            "Command execution runtime is unavailable in P2.4-C scope."
        ),
        GlobalCommandRequirementKind.TRACE_BINDING_REQUIRED_LATER: (
            "Trace binding would be required later; no trace write occurs here."
        ),
        GlobalCommandRequirementKind.UNKNOWN_UNAVAILABLE: (
            "Requirement kind unavailable in P2.4-C scope."
        ),
    }
    return descriptions[kind]


def build_global_command_proposal_gate(
    result_set: GlobalCommandResultSet | None = None,
) -> GlobalCommandProposalGate:
    if result_set is None:
        result_set = build_global_command_result_set()
    payload = {
        "gate_id": "p2_4_c_command_proposal_gate",
        "schema_version": P2_4_C_GATE_VERSION,
        "section_id": P2_4_C_SECTION_ID,
        "created_for_pack": P2_4_C_PACK_ID,
        "official_section_name": P2_4_C_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_4_C_DEPENDENCY_PACK,
        "dependency_report_ref": P2_4_B_REPORT_PATH,
        "dependency_commit_ref": P2_4_B_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.4-B",
        "dependency_result_set_ref": (
            f"{result_set.result_set_id}:{result_set.result_set_hash}"
        ),
        "dependency_unavailable_reason_ref": COMMAND_EXECUTION_UNAVAILABLE_REASON,
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": GlobalCommandProposalGateStatus.READY,
        "truth_label": GlobalCommandProposalTruthBoundary.CONTRACT_ONLY.value,
        "limitations": (
            "OMNI evidence is ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not execute commands or create selection/preview UI",
        ),
    }
    return GlobalCommandProposalGate(**payload, gate_hash=_hash_payload(payload))


def build_global_command_selection_intent(
    result_item: GlobalCommandResultItem,
    result_set: GlobalCommandResultSet,
    *,
    selection_source: GlobalCommandSelectionSource = (
        GlobalCommandSelectionSource.RESULT_SET_ITEM
    ),
) -> GlobalCommandSelectionIntent:
    payload = {
        "selection_id": f"command_selection:{result_item.command_id}",
        "schema_version": P2_4_C_SELECTION_VERSION,
        "selection_source": selection_source,
        "selected_command_id": result_item.command_id,
        "selected_result_item_ref": (
            f"{result_item.result_item_id}:{result_item.result_item_hash}"
        ),
        "query_ref": f"{result_set.query.query_id}:{result_set.query.query_hash}",
        "result_set_ref": (
            f"{result_set.result_set_id}:{result_set.result_set_hash}"
        ),
        "selected_at_label": GlobalCommandProposalTruthBoundary.DEV_FIXTURE.value,
        "is_execution": False,
        "is_invocation": False,
        "is_operator_consent": False,
        "is_approval": False,
        "truth_label": GlobalCommandProposalTruthBoundary.NOT_EXECUTION.value,
        "limitations": _SELECTION_NON_GOALS,
    }
    selection = GlobalCommandSelectionIntent(
        **payload,
        selection_hash=_hash_payload(payload),
    )
    assert_selection_is_not_execution(selection)
    return selection


def build_global_command_input_preview(
    result_item: GlobalCommandResultItem,
    *,
    provided_inputs: tuple[str, ...] = (),
) -> GlobalCommandInputPreview:
    contract = _input_contract_for_command(result_item.command_id)
    if contract is None:
        payload = {
            "input_preview_id": f"command_input_preview:{result_item.command_id}",
            "schema_version": P2_4_C_INPUT_PREVIEW_VERSION,
            "command_id": result_item.command_id,
            "input_contract_ref": result_item.input_contract_ref,
            "required_inputs": (),
            "optional_inputs": (),
            "missing_inputs": (),
            "provided_inputs": provided_inputs,
            "input_preview_status": GlobalCommandInputPreviewStatus.UNAVAILABLE,
            "is_invocation": False,
            "invokes_handler": False,
            "executes_validation_runtime": False,
            "truth_label": GlobalCommandProposalTruthBoundary.INPUT_PREVIEW_ONLY.value,
            "limitations": _INPUT_PREVIEW_NON_GOALS,
        }
    else:
        missing = tuple(
            name for name in contract.required_parameters if name not in provided_inputs
        )
        if not contract.required_parameters and not contract.optional_parameters:
            status = GlobalCommandInputPreviewStatus.EMPTY
        elif missing:
            status = GlobalCommandInputPreviewStatus.PARTIAL
        else:
            status = GlobalCommandInputPreviewStatus.READY
        payload = {
            "input_preview_id": f"command_input_preview:{result_item.command_id}",
            "schema_version": P2_4_C_INPUT_PREVIEW_VERSION,
            "command_id": result_item.command_id,
            "input_contract_ref": (
                f"{contract.input_contract_id}:{contract.input_contract_hash}"
            ),
            "required_inputs": contract.required_parameters,
            "optional_inputs": contract.optional_parameters,
            "missing_inputs": missing,
            "provided_inputs": provided_inputs,
            "input_preview_status": status,
            "is_invocation": False,
            "invokes_handler": False,
            "executes_validation_runtime": False,
            "truth_label": GlobalCommandProposalTruthBoundary.INPUT_PREVIEW_ONLY.value,
            "limitations": _INPUT_PREVIEW_NON_GOALS,
        }
    preview = GlobalCommandInputPreview(**payload, input_preview_hash=_hash_payload(payload))
    assert_input_preview_is_not_invocation(preview)
    return preview


def build_global_command_requirement_preview(
    result_item: GlobalCommandResultItem,
    requirement_kind: GlobalCommandRequirementKind,
) -> GlobalCommandRequirementPreview:
    unavailable_reason = ""
    if requirement_kind in (
        GlobalCommandRequirementKind.EXECUTION_RUNTIME_REQUIRED_LATER,
        GlobalCommandRequirementKind.APPROVAL_REQUIRED_LATER,
        GlobalCommandRequirementKind.POLICY_REQUIRED_LATER,
        GlobalCommandRequirementKind.TRACE_BINDING_REQUIRED_LATER,
    ):
        unavailable_reason = COMMAND_EXECUTION_UNAVAILABLE_REASON
    payload = {
        "requirement_id": (
            f"command_requirement_preview:{result_item.command_id}:{requirement_kind.value}"
        ),
        "schema_version": P2_4_C_REQUIREMENT_PREVIEW_VERSION,
        "command_id": result_item.command_id,
        "requirement_kind": requirement_kind,
        "description": _requirement_description(requirement_kind),
        "required_later": True,
        "available_now": False,
        "unavailable_reason": unavailable_reason,
        "is_permission_decision": False,
        "grants_permission": False,
        "denies_permission": False,
        "activates_approval": False,
        "truth_label": GlobalCommandProposalTruthBoundary.REQUIREMENT_PREVIEW_ONLY.value,
        "limitations": _REQUIREMENT_PREVIEW_NON_GOALS,
    }
    preview = GlobalCommandRequirementPreview(
        **payload,
        requirement_hash=_hash_payload(payload),
    )
    assert_requirement_preview_is_not_permission_enforcement(preview)
    return preview


def build_global_command_requirement_previews(
    result_item: GlobalCommandResultItem,
) -> tuple[GlobalCommandRequirementPreview, ...]:
    return tuple(
        build_global_command_requirement_preview(result_item, kind)
        for kind in _default_requirement_kinds()
    )


def build_global_command_impact_preview(
    result_item: GlobalCommandResultItem,
    requirement_previews: tuple[GlobalCommandRequirementPreview, ...],
) -> GlobalCommandImpactPreview:
    payload = {
        "impact_preview_id": f"command_impact_preview:{result_item.command_id}",
        "schema_version": P2_4_C_IMPACT_PREVIEW_VERSION,
        "command_id": result_item.command_id,
        "declared_intent": result_item.description,
        "declared_target": result_item.surface_target,
        "declared_scope": result_item.scope.value,
        "requirement_previews": tuple(
            preview.requirement_id for preview in requirement_previews
        ),
        "unavailable_reason": result_item.unavailable_reason,
        "is_runtime_simulation": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "writes_storage": False,
        "truth_label": GlobalCommandProposalTruthBoundary.IMPACT_PREVIEW_ONLY.value,
        "limitations": _IMPACT_PREVIEW_NON_GOALS,
    }
    preview = GlobalCommandImpactPreview(**payload, impact_preview_hash=_hash_payload(payload))
    assert_impact_preview_is_not_runtime_mutation(preview)
    return preview


def build_global_command_proposal(
    selection_intent: GlobalCommandSelectionIntent,
    result_item: GlobalCommandResultItem,
    input_preview: GlobalCommandInputPreview,
    impact_preview: GlobalCommandImpactPreview,
    requirement_previews: tuple[GlobalCommandRequirementPreview, ...],
) -> GlobalCommandProposal:
    if (
        result_item.availability_status
        == GlobalCommandAvailabilityStatus.UNAVAILABLE_FOR_EXECUTION
    ):
        proposal_status = GlobalCommandProposalStatus.UNAVAILABLE_FOR_EXECUTION
    else:
        proposal_status = GlobalCommandProposalStatus.READY_FOR_PREVIEW

    payload = {
        "proposal_id": f"command_proposal:{result_item.command_id}",
        "schema_version": P2_4_C_PROPOSAL_VERSION,
        "selection_intent_ref": (
            f"{selection_intent.selection_id}:{selection_intent.selection_hash}"
        ),
        "command_id": result_item.command_id,
        "command_label": result_item.label,
        "command_kind": result_item.kind,
        "surface_target": result_item.surface_target,
        "scope": result_item.scope,
        "availability_status": result_item.availability_status,
        "unavailable_reason": result_item.unavailable_reason,
        "input_preview_ref": (
            f"{input_preview.input_preview_id}:{input_preview.input_preview_hash}"
        ),
        "impact_preview_ref": (
            f"{impact_preview.impact_preview_id}:{impact_preview.impact_preview_hash}"
        ),
        "requirement_preview_refs": tuple(
            f"{preview.requirement_id}:{preview.requirement_hash}"
            for preview in requirement_previews
        ),
        "proposal_status": proposal_status,
        "is_approval": False,
        "is_authorization": False,
        "executes_command": False,
        "truth_label": GlobalCommandProposalTruthBoundary.DECLARATIVE_ONLY.value,
        "limitations": _PROPOSAL_NON_GOALS,
    }
    proposal = GlobalCommandProposal(**payload, proposal_hash=_hash_payload(payload))
    assert_proposal_is_not_approval(proposal)
    return proposal


def build_global_command_no_execution_boundary(
    proposal: GlobalCommandProposal,
) -> GlobalCommandNoExecutionBoundary:
    payload = {
        "boundary_id": f"command_no_execution_boundary:{proposal.command_id}",
        "schema_version": P2_4_C_NO_EXECUTION_VERSION,
        "command_id": proposal.command_id,
        "proposal_id": proposal.proposal_id,
        "boundary_active": True,
        "execution_allowed": False,
        "approval_activated": False,
        "permission_enforced": False,
        "route_executed": False,
        "handler_invoked": False,
        "tool_invoked": False,
        "workflow_dispatched": False,
        "runtime_mutated": False,
        "memory_written": False,
        "trace_written": False,
        "storage_written": False,
        "reason": (
            "P2.4-C defines proposal/preview contracts only. Command execution, "
            "approval activation, permission enforcement, and runtime mutation "
            "remain unavailable in this scope."
        ),
        "truth_label": GlobalCommandProposalTruthBoundary.NO_EXECUTION_BOUNDARY.value,
        "limitations": _NO_EXECUTION_NON_GOALS,
    }
    boundary = GlobalCommandNoExecutionBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_execution_boundary_is_active(boundary)
    return boundary


def build_global_command_proposal_result(
    selection_intent: GlobalCommandSelectionIntent,
    proposal: GlobalCommandProposal,
    input_preview: GlobalCommandInputPreview,
    impact_preview: GlobalCommandImpactPreview,
    requirement_previews: tuple[GlobalCommandRequirementPreview, ...],
    no_execution_boundary: GlobalCommandNoExecutionBoundary,
) -> GlobalCommandProposalResult:
    if proposal.proposal_status == GlobalCommandProposalStatus.UNAVAILABLE_FOR_EXECUTION:
        result_status = GlobalCommandProposalResultStatus.UNAVAILABLE_FOR_EXECUTION
    elif input_preview.input_preview_status == GlobalCommandInputPreviewStatus.PARTIAL:
        result_status = GlobalCommandProposalResultStatus.PARTIAL
    else:
        result_status = GlobalCommandProposalResultStatus.READY

    payload = {
        "proposal_result_id": f"command_proposal_result:{proposal.command_id}",
        "schema_version": P2_4_C_PROPOSAL_RESULT_VERSION,
        "section_id": P2_4_C_SECTION_ID,
        "created_for_pack": P2_4_C_PACK_ID,
        "official_section_name": P2_4_C_OFFICIAL_SECTION_NAME,
        "selection_intent": selection_intent,
        "proposal": proposal,
        "input_preview": input_preview,
        "impact_preview": impact_preview,
        "requirement_previews": requirement_previews,
        "no_execution_boundary": no_execution_boundary,
        "result_status": result_status,
        "is_command_execution_result": False,
        "is_command_palette_ui": False,
        "is_preview_ui": False,
        "is_source_of_truth": False,
        "executes_commands": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "writes_storage": False,
        "truth_label": GlobalCommandProposalTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": _PROPOSAL_RESULT_NON_GOALS,
    }
    proposal_result = GlobalCommandProposalResult(
        **payload,
        proposal_result_hash=_hash_payload(payload),
    )
    assert_preview_is_not_action(proposal_result)
    return proposal_result


def build_p2_4_c_side_effect_proof() -> P24CSideEffectProof:
    return P24CSideEffectProof()


def build_p2_4_c_command_proposal_result(
    *,
    result_set: GlobalCommandResultSet | None = None,
    item_index: int = 0,
    provided_inputs: tuple[str, ...] = (),
) -> P24CCommandProposalResult:
    if result_set is None:
        result_set = build_global_command_result_set()
    if not result_set.items:
        _reject(
            "result set must contain at least one item for proposal",
            field="items",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if item_index < 0 or item_index >= len(result_set.items):
        _reject(
            "item_index out of range for result set",
            field="item_index",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )

    result_item = result_set.items[item_index]
    gate = build_global_command_proposal_gate(result_set)
    selection_intent = build_global_command_selection_intent(result_item, result_set)
    input_preview = build_global_command_input_preview(
        result_item,
        provided_inputs=provided_inputs,
    )
    requirement_previews = build_global_command_requirement_previews(result_item)
    impact_preview = build_global_command_impact_preview(
        result_item,
        requirement_previews,
    )
    proposal = build_global_command_proposal(
        selection_intent,
        result_item,
        input_preview,
        impact_preview,
        requirement_previews,
    )
    no_execution_boundary = build_global_command_no_execution_boundary(proposal)
    proposal_result = build_global_command_proposal_result(
        selection_intent,
        proposal,
        input_preview,
        impact_preview,
        requirement_previews,
        no_execution_boundary,
    )
    side_effects = build_p2_4_c_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()

    payload: dict[str, Any] = {
        "schema_version": P2_4_C_RESULT_VERSION,
        "pack_id": P2_4_C_PACK_ID,
        "section_id": P2_4_C_SECTION_ID,
        "official_section_name": P2_4_C_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_4_C_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_4_C_DEPENDENCY_PACK,
        "proposal_gate": gate,
        "selection_intent": selection_intent,
        "proposal": proposal,
        "input_preview": input_preview,
        "impact_preview": impact_preview,
        "requirement_previews": requirement_previews,
        "no_execution_boundary": no_execution_boundary,
        "proposal_result": proposal_result,
        "truth_labels": (
            GlobalCommandProposalTruthBoundary.CONTRACT_ONLY.value,
            GlobalCommandProposalTruthBoundary.READ_MODEL_ONLY.value,
            GlobalCommandProposalTruthBoundary.NOT_SELECTION_UI.value,
            GlobalCommandProposalTruthBoundary.NOT_PREVIEW_UI.value,
            GlobalCommandProposalTruthBoundary.NOT_COMMAND_PALETTE_UI.value,
            GlobalCommandProposalTruthBoundary.NOT_EXECUTABLE.value,
            GlobalCommandProposalTruthBoundary.NOT_INVOCATION.value,
            GlobalCommandProposalTruthBoundary.NOT_APPROVAL.value,
            GlobalCommandProposalTruthBoundary.NOT_AUTHORIZATION.value,
            GlobalCommandProposalTruthBoundary.NOT_PERMISSION_ENFORCEMENT.value,
            GlobalCommandProposalTruthBoundary.NOT_RUNTIME_SIMULATION.value,
            GlobalCommandProposalTruthBoundary.NO_EXECUTION_BOUNDARY.value,
            GlobalCommandProposalTruthBoundary.NOT_COMMAND_EXECUTION_RESULT.value,
            GlobalCommandProposalTruthBoundary.NOT_LIVE.value,
            GlobalCommandProposalTruthBoundary.NOT_TRACE_VERIFIED.value,
            GlobalCommandProposalTruthBoundary.NOT_PRODUCT_BEHAVIOR.value,
            GlobalCommandProposalTruthBoundary.NOT_RELEASE_SCOPE.value,
        ),
        "unavailable_reasons": (COMMAND_EXECUTION_UNAVAILABLE_REASON,),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_4_C_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P24CCommandProposalResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_4_c_does_not_start_future_work(result)
    assert_p2_4_c_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_4_c_result(
    result: P24CCommandProposalResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_c_command_proposal_result()
    return to_canonical_json(result.to_canonical_dict())


def render_global_command_proposal_summary(
    result: P24CCommandProposalResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_c_command_proposal_result()
    proposal = result.proposal
    boundary = result.no_execution_boundary
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"command_id={proposal.command_id}",
            f"proposal_status={proposal.proposal_status.value}",
            f"result_status={result.proposal_result.result_status.value}",
            f"boundary_active={str(boundary.boundary_active).lower()}",
            f"execution_allowed={str(boundary.execution_allowed).lower()}",
            f"is_command_palette_ui={str(result.proposal_result.is_command_palette_ui).lower()}",
            f"executes_commands={str(result.proposal_result.executes_commands).lower()}",
        )
    )


def assert_selection_is_not_execution(selection: GlobalCommandSelectionIntent) -> None:
    if (
        selection.is_execution
        or selection.is_invocation
        or selection.is_operator_consent
        or selection.is_approval
    ):
        _reject(
            "P2.4-C selection must not be execution, invocation, consent, or approval",
            field="is_execution",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_proposal_is_not_approval(proposal: GlobalCommandProposal) -> None:
    if proposal.is_approval or proposal.is_authorization or proposal.executes_command:
        _reject(
            "P2.4-C proposal must not approve, authorize, or execute",
            field="is_approval",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_preview_is_not_action(proposal_result: GlobalCommandProposalResult) -> None:
    if (
        proposal_result.is_command_execution_result
        or proposal_result.is_command_palette_ui
        or proposal_result.is_preview_ui
        or proposal_result.is_source_of_truth
        or proposal_result.executes_commands
        or proposal_result.mutates_runtime
        or proposal_result.writes_memory
        or proposal_result.writes_trace
        or proposal_result.writes_storage
    ):
        _reject(
            "P2.4-C proposal result must remain read-model only",
            field="is_command_execution_result",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_input_preview_is_not_invocation(preview: GlobalCommandInputPreview) -> None:
    if (
        preview.is_invocation
        or preview.invokes_handler
        or preview.executes_validation_runtime
    ):
        _reject(
            "P2.4-C input preview must not invoke handlers or validation runtime",
            field="is_invocation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_impact_preview_is_not_runtime_mutation(
    preview: GlobalCommandImpactPreview,
) -> None:
    if (
        preview.is_runtime_simulation
        or preview.mutates_runtime
        or preview.writes_memory
        or preview.writes_trace
        or preview.writes_storage
    ):
        _reject(
            "P2.4-C impact preview must not simulate or mutate runtime",
            field="is_runtime_simulation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_requirement_preview_is_not_permission_enforcement(
    preview: GlobalCommandRequirementPreview,
) -> None:
    if (
        preview.is_permission_decision
        or preview.grants_permission
        or preview.denies_permission
        or preview.activates_approval
    ):
        _reject(
            "P2.4-C requirement preview must not enforce permission or activate approval",
            field="is_permission_decision",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_execution_boundary_is_active(
    boundary: GlobalCommandNoExecutionBoundary,
) -> None:
    if not boundary.boundary_active or boundary.execution_allowed:
        _reject(
            "P2.4-C no-execution boundary must be active and disallow execution",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if any(
        (
            boundary.approval_activated,
            boundary.permission_enforced,
            boundary.route_executed,
            boundary.handler_invoked,
            boundary.tool_invoked,
            boundary.workflow_dispatched,
            boundary.runtime_mutated,
            boundary.memory_written,
            boundary.trace_written,
            boundary.storage_written,
        )
    ):
        _reject(
            "P2.4-C no-execution boundary must keep all side effects false",
            field="approval_activated",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_c_does_not_start_future_work(result: P24CCommandProposalResult) -> None:
    if result.starts_future_work or result.next_pack != P2_4_C_NEXT_PACK:
        _reject(
            "P2.4-C result must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_4_d_started,
            proof.p2_5_started,
            proof.p2_6_started,
            proof.p2_7_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.4-C must not start P2.4-D or later packs",
            field="p2_4_d_started",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_c_side_effects_all_false(proof: P24CSideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                f"P2.4-C side-effect field must remain false: {field}",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_p2_4_c_depends_on_p2_4_b(gate: GlobalCommandProposalGate) -> None:
    if gate.dependency_pack != P2_4_B_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.4-C must depend on passed P2.4-B repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not gate.dependency_result_set_ref:
        _reject(
            "P2.4-C gate must reference P2.4-B result set",
            field="dependency_result_set_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: GlobalCommandProposalGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.4-C gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )

"""P2.5-B handoff context / continuity / conflict / availability read model.

Contract-only read model over the P2.5-A cross-surface handoff foundation.
This module explains handoff context without transferring context, represents
continuity without persistence, records conflicts without resolving them, and
reports availability without permission enforcement, approval activation,
surface switching, route execution, UI, storage, memory, trace, or runtime
mutation.
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
from .cross_surface_handoff import (
    P2_5_A_PACK_ID,
    P2_5_A_REPORT_PATH,
    build_p2_5_a_fixture_handoff_pipeline,
)
from .read_model import detect_surface_taxonomy_drift

P2_5_B_PACK_ID = "P2.5-B"
P2_5_B_SECTION_ID = "P2.5"
P2_5_B_OFFICIAL_SECTION_NAME = "Cross-Surface Handoff"
P2_5_B_DEPENDENCY_PACK = P2_5_A_PACK_ID
P2_5_B_NEXT_PACK = "P2.5-C"
P2_5_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.5.6",
    "P2.5.7",
    "P2.5.8",
    "P2.5.9",
    "P2.5.10",
)
P2_5_B_REPORT_FILENAME = "P2_5_B_HANDOFF_CONTEXT_AVAILABILITY_READ_MODEL.md"
P2_5_B_REPORT_PATH = f"agent/reports/{P2_5_B_REPORT_FILENAME}"

P2_5_A_COMMIT_REF = "691acfe82536668473becce3921e834825579ab0"
P2_5_A_REPORT_HASH_COMMIT_REF = "a85174936b09e36d62aad75b47393842556f17af"

P2_5_B_GATE_VERSION = "p2_5_b_handoff_context_gate.v1"
P2_5_B_CONTEXT_ITEM_VERSION = "p2_5_b_cross_surface_context_item.v1"
P2_5_B_CONTEXT_SNAPSHOT_VERSION = "p2_5_b_handoff_context_snapshot.v1"
P2_5_B_CONTINUITY_VERSION = "p2_5_b_handoff_continuity.v1"
P2_5_B_CONFLICT_VERSION = "p2_5_b_handoff_conflict.v1"
P2_5_B_AVAILABILITY_VERSION = "p2_5_b_handoff_availability.v1"
P2_5_B_EXPLANATION_VERSION = "p2_5_b_handoff_explanation.v1"
P2_5_B_CONTEXT_RESULT_VERSION = "p2_5_b_handoff_context_result.v1"
P2_5_B_SIDE_EFFECT_VERSION = "p2_5_b_side_effect_proof.v1"
P2_5_B_PACK_RESULT_VERSION = "p2_5_b_handoff_context_pack_result.v1"


class CrossSurfaceHandoffContextGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class CrossSurfaceContextKind(str, Enum):
    COMMAND_RESULT_CONTEXT = "COMMAND_RESULT_CONTEXT"
    COMMAND_PROPOSAL_CONTEXT = "COMMAND_PROPOSAL_CONTEXT"
    SURFACE_CONTEXT_REF = "SURFACE_CONTEXT_REF"
    WINDOW_CONTEXT_REF = "WINDOW_CONTEXT_REF"
    OBJECT_CONTEXT_REF = "OBJECT_CONTEXT_REF"
    ARTIFACT_CONTEXT_REF = "ARTIFACT_CONTEXT_REF"
    SYSTEM_STATUS_CONTEXT = "SYSTEM_STATUS_CONTEXT"
    OPERATOR_ATTENTION_CONTEXT = "OPERATOR_ATTENTION_CONTEXT"
    DEV_FIXTURE_CONTEXT = "DEV_FIXTURE_CONTEXT"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfaceContinuityKind(str, Enum):
    CARRY_LABEL = "CARRY_LABEL"
    CARRY_REFERENCE = "CARRY_REFERENCE"
    CARRY_SURFACE_SOURCE = "CARRY_SURFACE_SOURCE"
    CARRY_SURFACE_TARGET = "CARRY_SURFACE_TARGET"
    CARRY_INTENT = "CARRY_INTENT"
    CARRY_LIMITATION = "CARRY_LIMITATION"
    CARRY_UNAVAILABLE_REASON = "CARRY_UNAVAILABLE_REASON"
    DEV_FIXTURE_CONTINUITY = "DEV_FIXTURE_CONTINUITY"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfaceConflictKind(str, Enum):
    SURFACE_UNAVAILABLE = "SURFACE_UNAVAILABLE"
    PAYLOAD_KIND_UNSUPPORTED = "PAYLOAD_KIND_UNSUPPORTED"
    CONTEXT_INCOMPLETE = "CONTEXT_INCOMPLETE"
    TARGET_REQUIRES_LATER_UI = "TARGET_REQUIRES_LATER_UI"
    TARGET_REQUIRES_LATER_ROUTE_RUNTIME = "TARGET_REQUIRES_LATER_ROUTE_RUNTIME"
    TARGET_REQUIRES_LATER_PERMISSION = "TARGET_REQUIRES_LATER_PERMISSION"
    TARGET_REQUIRES_LATER_APPROVAL = "TARGET_REQUIRES_LATER_APPROVAL"
    TAXONOMY_DRIFT = "TAXONOMY_DRIFT"
    DUPLICATE_CONTEXT_REF = "DUPLICATE_CONTEXT_REF"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfaceConflictSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"
    ERROR = "ERROR"


class CrossSurfaceAvailabilityStatus(str, Enum):
    AVAILABLE_READ_MODEL_ONLY = "AVAILABLE_READ_MODEL_ONLY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class CrossSurfaceExplanationKind(str, Enum):
    WHY_AVAILABLE = "WHY_AVAILABLE"
    WHY_PARTIAL = "WHY_PARTIAL"
    WHY_UNAVAILABLE = "WHY_UNAVAILABLE"
    WHY_BLOCKED = "WHY_BLOCKED"
    WHAT_CONTEXT_INCLUDED = "WHAT_CONTEXT_INCLUDED"
    WHAT_CONTINUITY_REQUIRED_LATER = "WHAT_CONTINUITY_REQUIRED_LATER"
    WHAT_CONFLICTS_EXIST = "WHAT_CONFLICTS_EXIST"
    WHAT_IS_NOT_EXECUTED = "WHAT_IS_NOT_EXECUTED"
    DEV_FIXTURE_EXPLANATION = "DEV_FIXTURE_EXPLANATION"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfaceHandoffContextTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONTEXT_TRANSFER = "NOT_CONTEXT_TRANSFER"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_PERSISTENCE = "NOT_PERSISTENCE"
    NOT_CONFLICT_RESOLUTION = "NOT_CONFLICT_RESOLUTION"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_OPERATOR_CONFIRMATION = "NOT_OPERATOR_CONFIRMATION"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_UI = "NOT_UI"
    NOT_PREVIEW_UI = "NOT_PREVIEW_UI"
    NOT_EXPLANATION_PANEL_UI = "NOT_EXPLANATION_PANEL_UI"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class CrossSurfaceHandoffContextGate(_CanonicalMixin):
    gate_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_handoff_foundation_result_ref: str
    dependency_no_route_boundary_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: CrossSurfaceHandoffContextGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_GATE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.gate_status, CrossSurfaceHandoffContextGateStatus):
            _reject(
                "gate_status must be CrossSurfaceHandoffContextGateStatus",
                field="gate_status",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


@dataclass(frozen=True)
class CrossSurfaceContextItem(_CanonicalMixin):
    context_item_id: str
    context_kind: CrossSurfaceContextKind
    context_ref: str
    context_label: str
    source_ref: str
    included_for_explanation: bool
    is_persisted: bool
    is_transferred: bool
    memory_written: bool
    storage_written: bool
    trace_written: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_CONTEXT_ITEM_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.context_kind, CrossSurfaceContextKind):
            _reject(
                "context_kind must be CrossSurfaceContextKind",
                field="context_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.is_persisted:
            _reject(
                "context item must not persist context",
                field="is_persisted",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        if self.is_transferred:
            _reject(
                "context item must not transfer context",
                field="is_transferred",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        if self.memory_written or self.storage_written or self.trace_written:
            _reject(
                "context item must not write memory/storage/trace",
                field="memory_written",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffContextSnapshot(_CanonicalMixin):
    snapshot_id: str
    handoff_foundation_result_ref: str
    source_surface_id: str
    target_surface_id: str
    context_items: tuple[CrossSurfaceContextItem, ...]
    snapshot_label: str
    is_context_transfer: bool
    memory_written: bool
    storage_written: bool
    trace_written: bool
    runtime_mutated: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_CONTEXT_SNAPSHOT_VERSION

    def __post_init__(self) -> None:
        if self.is_context_transfer:
            _reject(
                "context snapshot must not transfer context",
                field="is_context_transfer",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        if (
            self.memory_written
            or self.storage_written
            or self.trace_written
            or self.runtime_mutated
        ):
            _reject(
                "context snapshot must not write or mutate runtime",
                field="runtime_mutated",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffContinuity(_CanonicalMixin):
    continuity_id: str
    handoff_foundation_result_ref: str
    continuity_kind: CrossSurfaceContinuityKind
    carry_forward_label: str
    carry_forward_ref: str
    required_later: bool
    persisted_now: bool
    memory_mutated: bool
    object_copied: bool
    object_moved: bool
    storage_written: bool
    trace_written: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_CONTINUITY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.continuity_kind, CrossSurfaceContinuityKind):
            _reject(
                "continuity_kind must be CrossSurfaceContinuityKind",
                field="continuity_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if (
            self.persisted_now
            or self.memory_mutated
            or self.object_copied
            or self.object_moved
            or self.storage_written
            or self.trace_written
        ):
            _reject(
                "continuity is carry-forward metadata only",
                field="persisted_now",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffConflict(_CanonicalMixin):
    conflict_id: str
    conflict_kind: CrossSurfaceConflictKind
    severity: CrossSurfaceConflictSeverity
    message: str
    context_ref: str
    surface_ref: str
    payload_ref: str
    blocks_contract_read_model: bool
    resolves_conflict: bool
    runtime_blocked: bool
    runtime_mutated: bool
    required_action_later: str
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_CONFLICT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.conflict_kind, CrossSurfaceConflictKind):
            _reject(
                "conflict_kind must be CrossSurfaceConflictKind",
                field="conflict_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if not isinstance(self.severity, CrossSurfaceConflictSeverity):
            _reject(
                "severity must be CrossSurfaceConflictSeverity",
                field="severity",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.resolves_conflict or self.runtime_blocked or self.runtime_mutated:
            _reject(
                "conflict record must not resolve, block, or mutate runtime",
                field="resolves_conflict",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffAvailability(_CanonicalMixin):
    availability_id: str
    handoff_foundation_result_ref: str
    availability_status: CrossSurfaceAvailabilityStatus
    available_read_model_only: bool
    unavailable_reasons: tuple[str, ...]
    conflicts: tuple[CrossSurfaceHandoffConflict, ...]
    requires_ui_later: bool
    requires_route_runtime_later: bool
    requires_permission_later: bool
    requires_approval_later: bool
    is_permission_decision: bool
    grants_permission: bool
    denies_permission: bool
    activates_approval: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_AVAILABILITY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.availability_status, CrossSurfaceAvailabilityStatus):
            _reject(
                "availability_status must be CrossSurfaceAvailabilityStatus",
                field="availability_status",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if (
            self.is_permission_decision
            or self.grants_permission
            or self.denies_permission
            or self.activates_approval
        ):
            _reject(
                "availability must not enforce permissions or activate approval",
                field="is_permission_decision",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffExplanation(_CanonicalMixin):
    explanation_id: str
    explanation_kind: CrossSurfaceExplanationKind
    summary: str
    context_refs: tuple[str, ...]
    continuity_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    availability_ref: str
    explains_unavailable_reasons: bool
    is_approval: bool
    is_operator_confirmation: bool
    executes_handoff: bool
    executes_route: bool
    switches_surface: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_EXPLANATION_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.explanation_kind, CrossSurfaceExplanationKind):
            _reject(
                "explanation_kind must be CrossSurfaceExplanationKind",
                field="explanation_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if (
            self.is_approval
            or self.is_operator_confirmation
            or self.executes_handoff
            or self.executes_route
            or self.switches_surface
        ):
            _reject(
                "explanation must not approve, confirm, execute, route, or switch",
                field="is_approval",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffContextResult(_CanonicalMixin):
    context_result_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    handoff_foundation_result_ref: str
    context_snapshot: CrossSurfaceHandoffContextSnapshot
    continuity_items: tuple[CrossSurfaceHandoffContinuity, ...]
    conflict_items: tuple[CrossSurfaceHandoffConflict, ...]
    availability: CrossSurfaceHandoffAvailability
    explanations: tuple[CrossSurfaceHandoffExplanation, ...]
    result_status: str
    is_transition_result: bool
    is_route_result: bool
    is_live_ui: bool
    is_source_of_truth: bool
    transfers_context: bool
    persists_context: bool
    resolves_conflicts: bool
    enforces_permissions: bool
    approves_handoff: bool
    confirms_operator_action: bool
    switches_surface: bool
    executes_route: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_B_CONTEXT_RESULT_VERSION

    def __post_init__(self) -> None:
        forbidden = (
            self.is_transition_result,
            self.is_route_result,
            self.is_live_ui,
            self.is_source_of_truth,
            self.transfers_context,
            self.persists_context,
            self.resolves_conflicts,
            self.enforces_permissions,
            self.approves_handoff,
            self.confirms_operator_action,
            self.switches_surface,
            self.executes_route,
            self.mutates_runtime,
            self.writes_memory,
            self.writes_trace,
            self.writes_storage,
        )
        if any(forbidden):
            _reject(
                "context result must remain read-model only",
                field="context_result_id",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class P25BSideEffectProof(_CanonicalMixin):
    cross_surface_ui_created: bool = False
    preview_ui_created: bool = False
    explanation_panel_ui_created: bool = False
    drag_drop_created: bool = False
    handoff_animation_created: bool = False
    frontend_ui_created: bool = False
    browser_ui_created: bool = False
    tauri_app_created: bool = False
    surface_runtime_switch_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    context_transfer_created: bool = False
    context_persistence_created: bool = False
    memory_written: bool = False
    trace_written: bool = False
    storage_written: bool = False
    conflict_resolution_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    operator_confirmation_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    mneme_integration_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_5_c_started: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False
    version_tag: str = P2_5_B_SIDE_EFFECT_VERSION

    def __post_init__(self) -> None:
        _ensure_all_false(self, "P2.5-B side-effect proof")


@dataclass(frozen=True)
class P25BHandoffContextResult(_CanonicalMixin):
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    context_gate: CrossSurfaceHandoffContextGate
    handoff_foundation_result_ref: str
    context_snapshot: CrossSurfaceHandoffContextSnapshot
    context_items: tuple[CrossSurfaceContextItem, ...]
    continuity_items: tuple[CrossSurfaceHandoffContinuity, ...]
    conflict_items: tuple[CrossSurfaceHandoffConflict, ...]
    availability: CrossSurfaceHandoffAvailability
    explanations: tuple[CrossSurfaceHandoffExplanation, ...]
    context_result: CrossSurfaceHandoffContextResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    side_effect_proof: P25BSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    version_tag: str = P2_5_B_PACK_RESULT_VERSION


def _ensure_all_false(obj: object, label: str) -> None:
    for field in fields(obj):
        value = getattr(obj, field.name)
        if isinstance(value, bool) and value:
            _reject(
                f"{label}: {field.name} must be false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def _truth_labels() -> tuple[str, ...]:
    return tuple(boundary.value for boundary in CrossSurfaceHandoffContextTruthBoundary)


def build_cross_surface_handoff_context_gate(
    *,
    repo_evidence_gate_passed: bool = True,
    omni_evidence_ignored_by_operator_instruction: bool = True,
) -> CrossSurfaceHandoffContextGate:
    return CrossSurfaceHandoffContextGate(
        gate_id="p2_5_b_handoff_context_gate",
        section_id=P2_5_B_SECTION_ID,
        created_for_pack=P2_5_B_PACK_ID,
        official_section_name=P2_5_B_OFFICIAL_SECTION_NAME,
        dependency_pack=P2_5_B_DEPENDENCY_PACK,
        dependency_report_ref=P2_5_A_REPORT_PATH,
        dependency_commit_ref=P2_5_A_COMMIT_REF,
        dependency_validation_ref="P2.5-A validation: compileall, focused, aurel_shell, ruff, mypy",
        dependency_handoff_foundation_result_ref="p2_5_a_foundation_result",
        dependency_no_route_boundary_ref="p2_5_a_no_route_boundary",
        repo_evidence_gate_passed=repo_evidence_gate_passed,
        omni_evidence_required=False,
        omni_evidence_ignored_by_operator_instruction=(
            omni_evidence_ignored_by_operator_instruction
        ),
        gate_status=(
            CrossSurfaceHandoffContextGateStatus.READY
            if repo_evidence_gate_passed
            else CrossSurfaceHandoffContextGateStatus.BLOCKED
        ),
        truth_label="CONTRACT_ONLY / READ_MODEL_ONLY / REPORT_ONLY / NOT_LIVE / NOT_TRACE_VERIFIED",
        limitations=(
            "P2.5-B depends on P2.5-A foundation result and active no-route boundary",
            "context gate is not route execution or runtime transition",
        ),
    )


def build_cross_surface_context_item(
    *,
    context_kind: CrossSurfaceContextKind,
    context_ref: str,
    context_label: str,
    source_ref: str,
    included_for_explanation: bool = True,
) -> CrossSurfaceContextItem:
    return CrossSurfaceContextItem(
        context_item_id="p2_5_b_context_item::" + _hash_payload(
            {
                "context_kind": context_kind.value,
                "context_ref": context_ref,
                "source_ref": source_ref,
            }
        ),
        context_kind=context_kind,
        context_ref=context_ref,
        context_label=context_label,
        source_ref=source_ref,
        included_for_explanation=included_for_explanation,
        is_persisted=False,
        is_transferred=False,
        memory_written=False,
        storage_written=False,
        trace_written=False,
        truth_label="READ_MODEL_ONLY / NOT_CONTEXT_TRANSFER / NOT_PERSISTENCE / NOT_MEMORY_WRITE / NOT_STORAGE_WRITE / NOT_TRACE_WRITE",
        limitations=(
            "context item is a read-only reference",
            "context item is not copied, moved, persisted, transferred, or written",
        ),
    )


def build_cross_surface_context_snapshot(
    *,
    handoff_foundation_result_ref: str,
    source_surface_id: str = "hq",
    target_surface_id: str = "corp",
    context_items: tuple[CrossSurfaceContextItem, ...] = (),
    snapshot_label: str = "P2.5-B DEV_FIXTURE context snapshot",
) -> CrossSurfaceHandoffContextSnapshot:
    items = context_items or (
        build_cross_surface_context_item(
            context_kind=CrossSurfaceContextKind.DEV_FIXTURE_CONTEXT,
            context_ref="dev_fixture::handoff_context",
            context_label="DEV_FIXTURE handoff context",
            source_ref=handoff_foundation_result_ref,
        ),
        build_cross_surface_context_item(
            context_kind=CrossSurfaceContextKind.SURFACE_CONTEXT_REF,
            context_ref=f"surface::{source_surface_id}",
            context_label="Source surface reference",
            source_ref=handoff_foundation_result_ref,
        ),
        build_cross_surface_context_item(
            context_kind=CrossSurfaceContextKind.OBJECT_CONTEXT_REF,
            context_ref="dev_fixture::payload_object_ref",
            context_label="Payload object reference",
            source_ref=handoff_foundation_result_ref,
        ),
    )
    return CrossSurfaceHandoffContextSnapshot(
        snapshot_id="p2_5_b_context_snapshot::" + _hash_payload(
            {
                "handoff_foundation_result_ref": handoff_foundation_result_ref,
                "source_surface_id": source_surface_id,
                "target_surface_id": target_surface_id,
                "context_item_ids": [item.context_item_id for item in items],
            }
        ),
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
        context_items=items,
        snapshot_label=snapshot_label,
        is_context_transfer=False,
        memory_written=False,
        storage_written=False,
        trace_written=False,
        runtime_mutated=False,
        truth_label="CONTRACT_ONLY / READ_MODEL_ONLY / NOT_CONTEXT_TRANSFER / NOT_MEMORY_WRITE / NOT_STORAGE_WRITE / NOT_TRACE_WRITE / NOT_RUNTIME_MUTATION",
        limitations=(
            "context snapshot captures read-only refs only",
            "context snapshot does not transfer, persist, write, or mutate runtime",
        ),
    )


def build_cross_surface_handoff_continuity(
    *,
    handoff_foundation_result_ref: str,
    continuity_kind: CrossSurfaceContinuityKind,
    carry_forward_label: str,
    carry_forward_ref: str,
    required_later: bool = True,
) -> CrossSurfaceHandoffContinuity:
    return CrossSurfaceHandoffContinuity(
        continuity_id="p2_5_b_continuity::" + _hash_payload(
            {
                "handoff_foundation_result_ref": handoff_foundation_result_ref,
                "continuity_kind": continuity_kind.value,
                "carry_forward_ref": carry_forward_ref,
            }
        ),
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        continuity_kind=continuity_kind,
        carry_forward_label=carry_forward_label,
        carry_forward_ref=carry_forward_ref,
        required_later=required_later,
        persisted_now=False,
        memory_mutated=False,
        object_copied=False,
        object_moved=False,
        storage_written=False,
        trace_written=False,
        truth_label="CONTRACT_ONLY / CARRY_FORWARD_METADATA_ONLY / NOT_PERSISTENCE / NOT_MEMORY_WRITE / NOT_OBJECT_TRANSFER / NOT_STORAGE_WRITE / NOT_TRACE_WRITE",
        limitations=(
            "continuity is carry-forward metadata for later layers",
            "continuity does not persist, copy, move, or write anything now",
        ),
    )


def build_cross_surface_handoff_conflict(
    *,
    conflict_kind: CrossSurfaceConflictKind,
    severity: CrossSurfaceConflictSeverity,
    message: str,
    context_ref: str = "",
    surface_ref: str = "",
    payload_ref: str = "",
    blocks_contract_read_model: bool = False,
    required_action_later: str = "",
) -> CrossSurfaceHandoffConflict:
    return CrossSurfaceHandoffConflict(
        conflict_id="p2_5_b_conflict::" + _hash_payload(
            {
                "conflict_kind": conflict_kind.value,
                "context_ref": context_ref,
                "surface_ref": surface_ref,
                "payload_ref": payload_ref,
                "message": message,
            }
        ),
        conflict_kind=conflict_kind,
        severity=severity,
        message=message,
        context_ref=context_ref,
        surface_ref=surface_ref,
        payload_ref=payload_ref,
        blocks_contract_read_model=blocks_contract_read_model,
        resolves_conflict=False,
        runtime_blocked=False,
        runtime_mutated=False,
        required_action_later=required_action_later,
        truth_label="CONFLICT_RECORD_ONLY / NOT_CONFLICT_RESOLUTION / NOT_RUNTIME_BLOCKING / NOT_RUNTIME_MUTATION / NOT_AUTHORIZATION",
        limitations=(
            "conflict is diagnostic only",
            "conflict record does not resolve, block runtime, enforce, or create action",
        ),
    )


def build_cross_surface_handoff_availability(
    *,
    handoff_foundation_result_ref: str,
    conflicts: tuple[CrossSurfaceHandoffConflict, ...] = (),
    unavailable_reasons: tuple[str, ...] = (),
) -> CrossSurfaceHandoffAvailability:
    reasons = unavailable_reasons or (
        "context transfer unavailable in P2.5-B",
        "route runtime unavailable in P2.5-B",
        "permission enforcement unavailable in P2.5-B",
        "approval activation unavailable in P2.5-B",
        "memory/storage/trace writes unavailable in P2.5-B",
    )
    return CrossSurfaceHandoffAvailability(
        availability_id="p2_5_b_availability::" + _hash_payload(
            {
                "handoff_foundation_result_ref": handoff_foundation_result_ref,
                "conflict_ids": [conflict.conflict_id for conflict in conflicts],
                "unavailable_reasons": list(reasons),
            }
        ),
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        availability_status=CrossSurfaceAvailabilityStatus.AVAILABLE_READ_MODEL_ONLY,
        available_read_model_only=True,
        unavailable_reasons=reasons,
        conflicts=conflicts,
        requires_ui_later=True,
        requires_route_runtime_later=True,
        requires_permission_later=True,
        requires_approval_later=True,
        is_permission_decision=False,
        grants_permission=False,
        denies_permission=False,
        activates_approval=False,
        truth_label="READ_MODEL_ONLY / AVAILABILITY_EXPLANATION_ONLY / NOT_PERMISSION_ENFORCEMENT / NOT_APPROVAL / NOT_AUTHORIZATION / NOT_RUNTIME_BLOCKING",
        limitations=(
            "availability is explanatory read model only",
            "availability grants no permission, denies no permission, and activates no approval",
        ),
    )


def build_cross_surface_handoff_explanation(
    *,
    explanation_kind: CrossSurfaceExplanationKind,
    summary: str,
    context_refs: tuple[str, ...],
    continuity_refs: tuple[str, ...],
    conflict_refs: tuple[str, ...],
    availability_ref: str,
    explains_unavailable_reasons: bool = True,
) -> CrossSurfaceHandoffExplanation:
    return CrossSurfaceHandoffExplanation(
        explanation_id="p2_5_b_explanation::" + _hash_payload(
            {
                "explanation_kind": explanation_kind.value,
                "summary": summary,
                "availability_ref": availability_ref,
            }
        ),
        explanation_kind=explanation_kind,
        summary=summary,
        context_refs=context_refs,
        continuity_refs=continuity_refs,
        conflict_refs=conflict_refs,
        availability_ref=availability_ref,
        explains_unavailable_reasons=explains_unavailable_reasons,
        is_approval=False,
        is_operator_confirmation=False,
        executes_handoff=False,
        executes_route=False,
        switches_surface=False,
        truth_label="EXPLANATION_CONTRACT_ONLY / READ_MODEL_ONLY / NOT_APPROVAL / NOT_OPERATOR_CONFIRMATION / NOT_ROUTE_EXECUTION / NOT_UI / NOT_RUNTIME_MUTATION",
        limitations=(
            "explanation is not approval or operator confirmation",
            "explanation does not execute handoff, execute route, or switch surfaces",
        ),
    )


def build_cross_surface_handoff_context_result(
    *,
    handoff_foundation_result_ref: str,
    context_snapshot: CrossSurfaceHandoffContextSnapshot,
    continuity_items: tuple[CrossSurfaceHandoffContinuity, ...],
    conflict_items: tuple[CrossSurfaceHandoffConflict, ...],
    availability: CrossSurfaceHandoffAvailability,
    explanations: tuple[CrossSurfaceHandoffExplanation, ...],
) -> CrossSurfaceHandoffContextResult:
    return CrossSurfaceHandoffContextResult(
        context_result_id="p2_5_b_context_result::" + _hash_payload(
            {
                "handoff_foundation_result_ref": handoff_foundation_result_ref,
                "snapshot_id": context_snapshot.snapshot_id,
                "availability_id": availability.availability_id,
            }
        ),
        section_id=P2_5_B_SECTION_ID,
        created_for_pack=P2_5_B_PACK_ID,
        official_section_name=P2_5_B_OFFICIAL_SECTION_NAME,
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        context_snapshot=context_snapshot,
        continuity_items=continuity_items,
        conflict_items=conflict_items,
        availability=availability,
        explanations=explanations,
        result_status="READ_MODEL_ONLY",
        is_transition_result=False,
        is_route_result=False,
        is_live_ui=False,
        is_source_of_truth=False,
        transfers_context=False,
        persists_context=False,
        resolves_conflicts=False,
        enforces_permissions=False,
        approves_handoff=False,
        confirms_operator_action=False,
        switches_surface=False,
        executes_route=False,
        mutates_runtime=False,
        writes_memory=False,
        writes_trace=False,
        writes_storage=False,
        truth_label="READ_MODEL_ONLY / EXPLANATION_CONTRACT_ONLY / NOT_TRANSITION_RESULT / NOT_ROUTE_RESULT / NOT_UI / NOT_RUNTIME_MUTATION",
        limitations=(
            "context result is not handoff completion, transition result, or route result",
            "context result is not source of truth and writes no memory/storage/trace",
        ),
    )


def build_p2_5_b_side_effect_proof() -> P25BSideEffectProof:
    return P25BSideEffectProof()


def build_p2_5_b_handoff_context_result(
    *,
    source_surface_id: str = "hq",
    target_surface_id: str = "corp",
) -> P25BHandoffContextResult:
    foundation = build_p2_5_a_fixture_handoff_pipeline(
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
    )
    handoff_foundation_result_ref = foundation.foundation_result
    gate = build_cross_surface_handoff_context_gate(repo_evidence_gate_passed=True)
    snapshot = build_cross_surface_context_snapshot(
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
    )
    continuity_items = (
        build_cross_surface_handoff_continuity(
            handoff_foundation_result_ref=handoff_foundation_result_ref,
            continuity_kind=CrossSurfaceContinuityKind.CARRY_REFERENCE,
            carry_forward_label="Carry P2.5-A handoff foundation result reference",
            carry_forward_ref=handoff_foundation_result_ref,
        ),
        build_cross_surface_handoff_continuity(
            handoff_foundation_result_ref=handoff_foundation_result_ref,
            continuity_kind=CrossSurfaceContinuityKind.CARRY_LIMITATION,
            carry_forward_label="Carry no-route/no-runtime limitation",
            carry_forward_ref="p2_5_a_no_route_boundary",
        ),
    )
    drift, _details = detect_surface_taxonomy_drift()
    conflicts = (
        build_cross_surface_handoff_conflict(
            conflict_kind=CrossSurfaceConflictKind.TARGET_REQUIRES_LATER_ROUTE_RUNTIME,
            severity=CrossSurfaceConflictSeverity.INFO,
            message="Route runtime is unavailable in P2.5-B; availability remains read-model only.",
            context_ref=snapshot.snapshot_id,
            surface_ref=target_surface_id,
            payload_ref=foundation.payload_envelope,
            required_action_later="P2.5-C/P2.6 or later may define preview/route behavior under a separate gate",
        ),
        build_cross_surface_handoff_conflict(
            conflict_kind=CrossSurfaceConflictKind.TARGET_REQUIRES_LATER_PERMISSION,
            severity=CrossSurfaceConflictSeverity.INFO,
            message="Permission enforcement is unavailable in P2.5-B; no grant or denial occurs.",
            context_ref=snapshot.snapshot_id,
            surface_ref=target_surface_id,
            payload_ref=foundation.payload_envelope,
            required_action_later="P2.13 or later may integrate permission/Custos under a separate gate",
        ),
    )
    if drift:
        conflicts = conflicts + (
            build_cross_surface_handoff_conflict(
                conflict_kind=CrossSurfaceConflictKind.TAXONOMY_DRIFT,
                severity=CrossSurfaceConflictSeverity.WARNING,
                message="Legacy surface taxonomy appears in local docs; official P2 surface IDs remain active.",
                context_ref=snapshot.snapshot_id,
                surface_ref="legacy_surface_taxonomy",
                payload_ref=foundation.payload_envelope,
                required_action_later="Keep legacy taxonomy as drift/future refs only",
            ),
        )
    availability = build_cross_surface_handoff_availability(
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        conflicts=conflicts,
    )
    explanations = (
        build_cross_surface_handoff_explanation(
            explanation_kind=CrossSurfaceExplanationKind.WHAT_CONTEXT_INCLUDED,
            summary="P2.5-B includes read-only handoff context references only.",
            context_refs=tuple(item.context_item_id for item in snapshot.context_items),
            continuity_refs=tuple(item.continuity_id for item in continuity_items),
            conflict_refs=tuple(item.conflict_id for item in conflicts),
            availability_ref=availability.availability_id,
        ),
        build_cross_surface_handoff_explanation(
            explanation_kind=CrossSurfaceExplanationKind.WHAT_IS_NOT_EXECUTED,
            summary="P2.5-B executes no handoff, route, surface switch, approval, permission decision, memory write, storage write, or trace write.",
            context_refs=tuple(item.context_item_id for item in snapshot.context_items),
            continuity_refs=tuple(item.continuity_id for item in continuity_items),
            conflict_refs=tuple(item.conflict_id for item in conflicts),
            availability_ref=availability.availability_id,
        ),
    )
    context_result = build_cross_surface_handoff_context_result(
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        context_snapshot=snapshot,
        continuity_items=continuity_items,
        conflict_items=conflicts,
        availability=availability,
        explanations=explanations,
    )
    proof = build_p2_5_b_side_effect_proof()
    return P25BHandoffContextResult(
        pack_id=P2_5_B_PACK_ID,
        section_id=P2_5_B_SECTION_ID,
        official_section_name=P2_5_B_OFFICIAL_SECTION_NAME,
        covered_checkpoints=P2_5_B_PACK_CHECKPOINT_IDS,
        dependency_pack=P2_5_B_DEPENDENCY_PACK,
        context_gate=gate,
        handoff_foundation_result_ref=handoff_foundation_result_ref,
        context_snapshot=snapshot,
        context_items=snapshot.context_items,
        continuity_items=continuity_items,
        conflict_items=conflicts,
        availability=availability,
        explanations=explanations,
        context_result=context_result,
        truth_labels=_truth_labels(),
        surface_taxonomy_drift=drift,
        side_effect_proof=proof,
        next_pack=P2_5_B_NEXT_PACK,
        claims_live=False,
        claims_trace_verified=False,
        claims_release_scope=False,
        claims_product_behavior=False,
        starts_future_work=False,
    )


def serialize_p2_5_b_result(result: P25BHandoffContextResult) -> str:
    return to_canonical_json(result)


def render_cross_surface_handoff_context_summary(
    result: P25BHandoffContextResult,
) -> str:
    """Read-only text summary; not UI, preview UI, route execution, or confirmation."""
    lines = [
        f"P2.5-B {result.official_section_name} — Handoff Context Read Model",
        f"  Pack: {result.pack_id}",
        f"  Section: {result.section_id}",
        f"  Dependency: {result.dependency_pack}",
        f"  Next: {result.next_pack}",
        f"  Context items: {len(result.context_items)}",
        f"  Continuity items: {len(result.continuity_items)}",
        f"  Conflicts: {len(result.conflict_items)}",
        f"  Availability: {result.availability.availability_status.value}",
        f"  Claims LIVE: {result.claims_live}",
        f"  Claims TRACE_VERIFIED: {result.claims_trace_verified}",
        f"  Claims RELEASE_SCOPE: {result.claims_release_scope}",
        f"  Claims product behavior: {result.claims_product_behavior}",
        f"  Starts future work: {result.starts_future_work}",
    ]
    return "\n".join(lines)


def assert_context_snapshot_is_not_memory_write(
    snapshot: CrossSurfaceHandoffContextSnapshot,
) -> None:
    if (
        snapshot.is_context_transfer
        or snapshot.memory_written
        or snapshot.storage_written
        or snapshot.trace_written
        or snapshot.runtime_mutated
    ):
        _reject(
            "context snapshot must not transfer context or write memory/storage/trace",
            field="is_context_transfer",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_snapshot_is_not_context_transfer(
    snapshot: CrossSurfaceHandoffContextSnapshot,
) -> None:
    if snapshot.is_context_transfer:
        _reject(
            "context snapshot is not context transfer",
            field="is_context_transfer",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_continuity_is_not_persistence(
    continuity: CrossSurfaceHandoffContinuity,
) -> None:
    if (
        continuity.persisted_now
        or continuity.memory_mutated
        or continuity.object_copied
        or continuity.object_moved
        or continuity.storage_written
        or continuity.trace_written
    ):
        _reject(
            "continuity must not persist or move/copy objects",
            field="persisted_now",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_conflict_is_not_resolution(conflict: CrossSurfaceHandoffConflict) -> None:
    if conflict.resolves_conflict or conflict.runtime_blocked or conflict.runtime_mutated:
        _reject(
            "conflict record must not resolve conflicts or block runtime",
            field="resolves_conflict",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_availability_is_not_permission_enforcement(
    availability: CrossSurfaceHandoffAvailability,
) -> None:
    if (
        availability.is_permission_decision
        or availability.grants_permission
        or availability.denies_permission
        or availability.activates_approval
    ):
        _reject(
            "availability must not enforce permission or activate approval",
            field="is_permission_decision",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_explanation_is_not_approval(
    explanation: CrossSurfaceHandoffExplanation,
) -> None:
    if explanation.is_approval:
        _reject(
            "explanation is not approval",
            field="is_approval",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_explanation_is_not_operator_confirmation(
    explanation: CrossSurfaceHandoffExplanation,
) -> None:
    if explanation.is_operator_confirmation:
        _reject(
            "explanation is not operator confirmation",
            field="is_operator_confirmation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_5_b_does_not_start_future_work(
    result: P25BHandoffContextResult,
) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or result.next_pack != P2_5_B_NEXT_PACK
        or proof.p2_5_c_started
        or proof.p2_6_started
        or proof.p2_7_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.5-B must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )

"""P2.5-C handoff preview / explanation / operator confirmation boundary.

Contract-only handoff preview over the P2.5-B handoff context result/read model.
Defines preview request, preview content, explanation bundle, confirmation
requirement, confirmation intent boundary, and preview result without preview UI,
explanation panel UI, confirmation modal, real operator consent, approval
runtime, authorization, permission enforcement, handoff execution, surface
switching, route execution, storage, memory/trace writes, product behavior,
release scope, or runtime mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .cross_surface_handoff_context import (
    P2_5_B_PACK_ID,
    P2_5_B_REPORT_PATH,
    CrossSurfaceHandoffContextResult,
    CrossSurfaceHandoffExplanation,
    P25BHandoffContextResult,
    build_p2_5_b_handoff_context_result,
)
from .read_model import detect_surface_taxonomy_drift

P2_5_C_PACK_ID = "P2.5-C"
P2_5_C_SECTION_ID = "P2.5"
P2_5_C_OFFICIAL_SECTION_NAME = "Cross-Surface Handoff"
P2_5_C_DEPENDENCY_PACK = P2_5_B_PACK_ID
P2_5_C_NEXT_PACK = "P2.5-D"
P2_5_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.5.11",
    "P2.5.12",
    "P2.5.13",
    "P2.5.14",
    "P2.5.15",
)
P2_5_C_REPORT_FILENAME = "P2_5_C_HANDOFF_PREVIEW_CONFIRMATION_BOUNDARY.md"
P2_5_C_REPORT_PATH = f"agent/reports/{P2_5_C_REPORT_FILENAME}"

P2_5_B_COMMIT_REF = "196c3ba7967291f1a860456929ff25b39bdc54e6"
P2_5_B_REPORT_HASH_COMMIT_REF = "19e2e7e"

P2_5_C_GATE_VERSION = "p2_5_c_handoff_preview_gate.v1"
P2_5_C_PREVIEW_REQUEST_VERSION = "p2_5_c_handoff_preview_request.v1"
P2_5_C_PREVIEW_CONTENT_VERSION = "p2_5_c_handoff_preview_content.v1"
P2_5_C_EXPLANATION_BUNDLE_VERSION = "p2_5_c_handoff_explanation_bundle.v1"
P2_5_C_CONFIRMATION_REQUIREMENT_VERSION = (
    "p2_5_c_operator_confirmation_requirement.v1"
)
P2_5_C_CONFIRMATION_BOUNDARY_VERSION = (
    "p2_5_c_operator_confirmation_intent_boundary.v1"
)
P2_5_C_PREVIEW_RESULT_VERSION = "p2_5_c_handoff_preview_result.v1"
P2_5_C_SIDE_EFFECT_VERSION = "p2_5_c_side_effect_proof.v1"
P2_5_C_PACK_RESULT_VERSION = "p2_5_c_handoff_preview_pack_result.v1"


class CrossSurfaceHandoffPreviewGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class CrossSurfacePreviewRequestKind(str, Enum):
    INSPECT_HANDOFF = "INSPECT_HANDOFF"
    REVIEW_CONTEXT = "REVIEW_CONTEXT"
    REVIEW_CONFLICTS = "REVIEW_CONFLICTS"
    REVIEW_AVAILABILITY = "REVIEW_AVAILABILITY"
    REVIEW_EXPLANATION = "REVIEW_EXPLANATION"
    CONFIRMATION_REQUIRED_LATER = "CONFIRMATION_REQUIRED_LATER"
    DEV_FIXTURE_PREVIEW = "DEV_FIXTURE_PREVIEW"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfacePreviewContentKind(str, Enum):
    SOURCE_TARGET_SUMMARY = "SOURCE_TARGET_SUMMARY"
    PAYLOAD_SUMMARY = "PAYLOAD_SUMMARY"
    CONTEXT_SUMMARY = "CONTEXT_SUMMARY"
    CONTINUITY_SUMMARY = "CONTINUITY_SUMMARY"
    CONFLICT_SUMMARY = "CONFLICT_SUMMARY"
    AVAILABILITY_SUMMARY = "AVAILABILITY_SUMMARY"
    EXPLANATION_SUMMARY = "EXPLANATION_SUMMARY"
    NO_EXECUTION_WARNING = "NO_EXECUTION_WARNING"
    DEV_FIXTURE_CONTENT = "DEV_FIXTURE_CONTENT"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfaceConfirmationRequirementKind(str, Enum):
    OPERATOR_REVIEW_REQUIRED_LATER = "OPERATOR_REVIEW_REQUIRED_LATER"
    OPERATOR_CONFIRMATION_REQUIRED_LATER = "OPERATOR_CONFIRMATION_REQUIRED_LATER"
    APPROVAL_REQUIRED_LATER = "APPROVAL_REQUIRED_LATER"
    PERMISSION_REQUIRED_LATER = "PERMISSION_REQUIRED_LATER"
    ROUTE_RUNTIME_REQUIRED_LATER = "ROUTE_RUNTIME_REQUIRED_LATER"
    UI_REQUIRED_LATER = "UI_REQUIRED_LATER"
    DEV_FIXTURE_REQUIREMENT = "DEV_FIXTURE_REQUIREMENT"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class CrossSurfacePreviewResultStatus(str, Enum):
    PREVIEW_READY_CONTRACT_ONLY = "PREVIEW_READY_CONTRACT_ONLY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class CrossSurfaceHandoffPreviewTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_UI = "NOT_UI"
    NOT_PREVIEW_UI = "NOT_PREVIEW_UI"
    NOT_EXPLANATION_PANEL_UI = "NOT_EXPLANATION_PANEL_UI"
    NOT_CONFIRMATION_MODAL = "NOT_CONFIRMATION_MODAL"
    NOT_REAL_OPERATOR_CONSENT = "NOT_REAL_OPERATOR_CONSENT"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_HANDOFF_EXECUTION = "NOT_HANDOFF_EXECUTION"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    PREVIEW_REQUEST_ONLY = "PREVIEW_REQUEST_ONLY"
    PREVIEW_CONTENT_ONLY = "PREVIEW_CONTENT_ONLY"
    EXPLANATION_BUNDLE_ONLY = "EXPLANATION_BUNDLE_ONLY"
    CONFIRMATION_REQUIREMENT_ONLY = "CONFIRMATION_REQUIREMENT_ONLY"
    FUTURE_REQUIREMENT_ONLY = "FUTURE_REQUIREMENT_ONLY"
    CONFIRMATION_BOUNDARY_ONLY = "CONFIRMATION_BOUNDARY_ONLY"
    PREVIEW_RESULT_ONLY = "PREVIEW_RESULT_ONLY"
    NO_CONFIRMATION_BOUNDARY = "NO_CONFIRMATION_BOUNDARY"
    NO_EXECUTION_BOUNDARY = "NO_EXECUTION_BOUNDARY"
    NOT_TRANSITION_RESULT = "NOT_TRANSITION_RESULT"
    NOT_ROUTE_RESULT = "NOT_ROUTE_RESULT"


@dataclass(frozen=True)
class CrossSurfaceHandoffPreviewGate(_CanonicalMixin):
    gate_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_context_result_ref: str
    dependency_availability_ref: str
    dependency_explanation_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: CrossSurfaceHandoffPreviewGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_GATE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.gate_status, CrossSurfaceHandoffPreviewGateStatus):
            _reject(
                "gate_status must be CrossSurfaceHandoffPreviewGateStatus",
                field="gate_status",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffPreviewRequest(_CanonicalMixin):
    preview_request_id: str
    handoff_context_result_ref: str
    request_kind: CrossSurfacePreviewRequestKind
    requested_summary: str
    source_surface_id: str
    target_surface_id: str
    renders_ui: bool
    asks_real_operator: bool
    records_consent: bool
    executes_handoff: bool
    executes_route: bool
    switches_surface: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_PREVIEW_REQUEST_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.request_kind, CrossSurfacePreviewRequestKind):
            _reject(
                "request_kind must be CrossSurfacePreviewRequestKind",
                field="request_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        forbidden = (
            self.renders_ui,
            self.asks_real_operator,
            self.records_consent,
            self.executes_handoff,
            self.executes_route,
            self.switches_surface,
        )
        if any(forbidden):
            _reject(
                "preview request must not render UI, ask operator, record consent, or execute",
                field="renders_ui",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffPreviewContent(_CanonicalMixin):
    preview_content_id: str
    content_kind: CrossSurfacePreviewContentKind
    content_label: str
    source_ref: str
    context_refs: tuple[str, ...]
    availability_ref: str
    explanation_refs: tuple[str, ...]
    is_rendered_ui: bool
    creates_panel: bool
    creates_modal: bool
    executes_action: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_PREVIEW_CONTENT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.content_kind, CrossSurfacePreviewContentKind):
            _reject(
                "content_kind must be CrossSurfacePreviewContentKind",
                field="content_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if (
            self.is_rendered_ui
            or self.creates_panel
            or self.creates_modal
            or self.executes_action
        ):
            _reject(
                "preview content must not render UI, create panel/modal, or execute",
                field="is_rendered_ui",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffExplanationBundle(_CanonicalMixin):
    bundle_id: str
    handoff_context_result_ref: str
    explanation_refs: tuple[str, ...]
    content_refs: tuple[str, ...]
    summary: str
    is_approval: bool
    is_authorization: bool
    is_operator_confirmation: bool
    executes_handoff: bool
    executes_route: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_EXPLANATION_BUNDLE_VERSION

    def __post_init__(self) -> None:
        if (
            self.is_approval
            or self.is_authorization
            or self.is_operator_confirmation
            or self.executes_handoff
            or self.executes_route
        ):
            _reject(
                "explanation bundle must not approve, authorize, confirm, or execute",
                field="is_approval",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceOperatorConfirmationRequirement(_CanonicalMixin):
    requirement_id: str
    requirement_kind: CrossSurfaceConfirmationRequirementKind
    required_later: bool
    reason: str
    future_pack_or_section: str
    records_real_consent: bool
    creates_confirmation_ui: bool
    activates_approval: bool
    enforces_permission: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_CONFIRMATION_REQUIREMENT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.requirement_kind, CrossSurfaceConfirmationRequirementKind):
            _reject(
                "requirement_kind must be CrossSurfaceConfirmationRequirementKind",
                field="requirement_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if (
            self.records_real_consent
            or self.creates_confirmation_ui
            or self.activates_approval
            or self.enforces_permission
        ):
            _reject(
                "confirmation requirement must not record consent, create UI, approve, or enforce",
                field="records_real_consent",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceOperatorConfirmationIntentBoundary(_CanonicalMixin):
    boundary_id: str
    boundary_active: bool
    confirmation_requirement_ref: str
    prevents_authorization: bool
    prevents_permission_decision: bool
    prevents_approval_activation: bool
    prevents_consent_recording: bool
    prevents_operator_prompt: bool
    prevents_execution: bool
    prevents_route_execution: bool
    prevents_surface_switch: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_CONFIRMATION_BOUNDARY_VERSION

    def __post_init__(self) -> None:
        if not self.boundary_active:
            _reject(
                "confirmation intent boundary must be active",
                field="boundary_active",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        required = (
            self.prevents_authorization,
            self.prevents_permission_decision,
            self.prevents_approval_activation,
            self.prevents_consent_recording,
            self.prevents_operator_prompt,
            self.prevents_execution,
            self.prevents_route_execution,
            self.prevents_surface_switch,
        )
        if not all(required):
            _reject(
                "confirmation intent boundary must prevent authorization, permission, approval, consent, prompt, and execution",
                field="prevents_authorization",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class CrossSurfaceHandoffPreviewResult(_CanonicalMixin):
    preview_result_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    handoff_context_result_ref: str
    preview_request: CrossSurfaceHandoffPreviewRequest
    preview_content_items: tuple[CrossSurfaceHandoffPreviewContent, ...]
    explanation_bundle: CrossSurfaceHandoffExplanationBundle
    confirmation_requirement: CrossSurfaceOperatorConfirmationRequirement
    confirmation_intent_boundary: CrossSurfaceOperatorConfirmationIntentBoundary
    result_status: CrossSurfacePreviewResultStatus
    no_confirmation_boundary_active: bool
    no_execution_boundary_active: bool
    is_transition_result: bool
    is_route_result: bool
    is_live_ui: bool
    is_source_of_truth: bool
    renders_preview_ui: bool
    creates_explanation_panel: bool
    creates_confirmation_modal: bool
    records_real_consent: bool
    activates_approval: bool
    authorizes_action: bool
    enforces_permission: bool
    executes_handoff: bool
    switches_surface: bool
    executes_route: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_tag: str = P2_5_C_PREVIEW_RESULT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.result_status, CrossSurfacePreviewResultStatus):
            _reject(
                "result_status must be CrossSurfacePreviewResultStatus",
                field="result_status",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if not self.no_confirmation_boundary_active or not self.no_execution_boundary_active:
            _reject(
                "preview result must keep no-confirmation and no-execution boundaries active",
                field="no_confirmation_boundary_active",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
        forbidden = (
            self.is_transition_result,
            self.is_route_result,
            self.is_live_ui,
            self.is_source_of_truth,
            self.renders_preview_ui,
            self.creates_explanation_panel,
            self.creates_confirmation_modal,
            self.records_real_consent,
            self.activates_approval,
            self.authorizes_action,
            self.enforces_permission,
            self.executes_handoff,
            self.switches_surface,
            self.executes_route,
            self.mutates_runtime,
            self.writes_memory,
            self.writes_trace,
            self.writes_storage,
        )
        if any(forbidden):
            _reject(
                "preview result must remain read-model only",
                field="preview_result_id",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


@dataclass(frozen=True)
class P25CSideEffectProof(_CanonicalMixin):
    cross_surface_ui_created: bool = False
    preview_ui_created: bool = False
    explanation_panel_ui_created: bool = False
    confirmation_modal_created: bool = False
    operator_confirmation_ui_created: bool = False
    real_operator_consent_recorded: bool = False
    consent_state_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    authorization_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    mneme_integration_created: bool = False
    handoff_execution_created: bool = False
    surface_runtime_switch_created: bool = False
    active_navigation_mutation_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    memory_written: bool = False
    trace_written: bool = False
    storage_written: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_5_d_started: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False
    version_tag: str = P2_5_C_SIDE_EFFECT_VERSION

    def __post_init__(self) -> None:
        _ensure_all_false(self, "P2.5-C side-effect proof")


@dataclass(frozen=True)
class P25CHandoffPreviewResult(_CanonicalMixin):
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    preview_gate: CrossSurfaceHandoffPreviewGate
    handoff_context_result_ref: str
    preview_request: CrossSurfaceHandoffPreviewRequest
    preview_content_items: tuple[CrossSurfaceHandoffPreviewContent, ...]
    explanation_bundle: CrossSurfaceHandoffExplanationBundle
    confirmation_requirement: CrossSurfaceOperatorConfirmationRequirement
    confirmation_intent_boundary: CrossSurfaceOperatorConfirmationIntentBoundary
    preview_result: CrossSurfaceHandoffPreviewResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    side_effect_proof: P25CSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    version_tag: str = P2_5_C_PACK_RESULT_VERSION


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
    return tuple(boundary.value for boundary in CrossSurfaceHandoffPreviewTruthBoundary)


def build_cross_surface_handoff_preview_gate(
    *,
    repo_evidence_gate_passed: bool = True,
    omni_evidence_ignored_by_operator_instruction: bool = True,
    handoff_context_result_ref: str = "p2_5_b_context_result",
) -> CrossSurfaceHandoffPreviewGate:
    return CrossSurfaceHandoffPreviewGate(
        gate_id="p2_5_c_handoff_preview_gate",
        section_id=P2_5_C_SECTION_ID,
        created_for_pack=P2_5_C_PACK_ID,
        official_section_name=P2_5_C_OFFICIAL_SECTION_NAME,
        dependency_pack=P2_5_C_DEPENDENCY_PACK,
        dependency_report_ref=P2_5_B_REPORT_PATH,
        dependency_commit_ref=P2_5_B_COMMIT_REF,
        dependency_validation_ref="P2.5-B validation: compileall, focused, aurel_shell, ruff, mypy",
        dependency_context_result_ref=handoff_context_result_ref,
        dependency_availability_ref=f"{handoff_context_result_ref}::availability",
        dependency_explanation_ref=f"{handoff_context_result_ref}::explanations",
        repo_evidence_gate_passed=repo_evidence_gate_passed,
        omni_evidence_required=False,
        omni_evidence_ignored_by_operator_instruction=(
            omni_evidence_ignored_by_operator_instruction
        ),
        gate_status=(
            CrossSurfaceHandoffPreviewGateStatus.READY
            if repo_evidence_gate_passed
            else CrossSurfaceHandoffPreviewGateStatus.BLOCKED
        ),
        truth_label="CONTRACT_ONLY / READ_MODEL_ONLY / REPORT_ONLY / NOT_LIVE / NOT_TRACE_VERIFIED",
        limitations=(
            "P2.5-C depends on P2.5-B handoff context result and availability/explanation contracts",
            "preview gate is not preview UI, confirmation modal, or handoff execution",
        ),
    )


def build_cross_surface_handoff_preview_request(
    *,
    handoff_context_result_ref: str,
    request_kind: CrossSurfacePreviewRequestKind = CrossSurfacePreviewRequestKind.DEV_FIXTURE_PREVIEW,
    requested_summary: str = "P2.5-C DEV_FIXTURE handoff preview request",
    source_surface_id: str = "hq",
    target_surface_id: str = "corp",
) -> CrossSurfaceHandoffPreviewRequest:
    return CrossSurfaceHandoffPreviewRequest(
        preview_request_id="p2_5_c_preview_request::" + _hash_payload(
            {
                "handoff_context_result_ref": handoff_context_result_ref,
                "request_kind": request_kind.value,
                "source_surface_id": source_surface_id,
                "target_surface_id": target_surface_id,
            }
        ),
        handoff_context_result_ref=handoff_context_result_ref,
        request_kind=request_kind,
        requested_summary=requested_summary,
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
        renders_ui=False,
        asks_real_operator=False,
        records_consent=False,
        executes_handoff=False,
        executes_route=False,
        switches_surface=False,
        truth_label="CONTRACT_ONLY / PREVIEW_REQUEST_ONLY / NOT_UI / NOT_REAL_OPERATOR_CONSENT / NOT_HANDOFF_EXECUTION / NOT_ROUTE_EXECUTION / NOT_SURFACE_SWITCH",
        limitations=(
            "preview request is data only",
            "preview request does not render UI, ask operator, record consent, or execute",
        ),
    )


def build_cross_surface_handoff_preview_content(
    *,
    content_kind: CrossSurfacePreviewContentKind,
    content_label: str,
    source_ref: str,
    context_refs: tuple[str, ...] = (),
    availability_ref: str = "",
    explanation_refs: tuple[str, ...] = (),
) -> CrossSurfaceHandoffPreviewContent:
    return CrossSurfaceHandoffPreviewContent(
        preview_content_id="p2_5_c_preview_content::" + _hash_payload(
            {
                "content_kind": content_kind.value,
                "content_label": content_label,
                "source_ref": source_ref,
            }
        ),
        content_kind=content_kind,
        content_label=content_label,
        source_ref=source_ref,
        context_refs=context_refs,
        availability_ref=availability_ref,
        explanation_refs=explanation_refs,
        is_rendered_ui=False,
        creates_panel=False,
        creates_modal=False,
        executes_action=False,
        truth_label="PREVIEW_CONTENT_ONLY / NOT_UI / NOT_EXPLANATION_PANEL_UI / NOT_HANDOFF_EXECUTION",
        limitations=(
            "preview content is structured content only",
            "preview content does not render UI, create panel/modal, or execute",
        ),
    )


def build_cross_surface_handoff_explanation_bundle(
    *,
    handoff_context_result_ref: str,
    explanation_refs: tuple[str, ...],
    content_refs: tuple[str, ...],
    summary: str,
) -> CrossSurfaceHandoffExplanationBundle:
    return CrossSurfaceHandoffExplanationBundle(
        bundle_id="p2_5_c_explanation_bundle::" + _hash_payload(
            {
                "handoff_context_result_ref": handoff_context_result_ref,
                "explanation_refs": list(explanation_refs),
                "summary": summary,
            }
        ),
        handoff_context_result_ref=handoff_context_result_ref,
        explanation_refs=explanation_refs,
        content_refs=content_refs,
        summary=summary,
        is_approval=False,
        is_authorization=False,
        is_operator_confirmation=False,
        executes_handoff=False,
        executes_route=False,
        truth_label="EXPLANATION_BUNDLE_ONLY / NOT_APPROVAL / NOT_AUTHORIZATION / NOT_OPERATOR_CONFIRMATION / NOT_HANDOFF_EXECUTION",
        limitations=(
            "explanation bundle groups evidence for operator understanding",
            "explanation bundle is not approval, authorization, or confirmation",
        ),
    )


def build_cross_surface_operator_confirmation_requirement(
    *,
    requirement_kind: CrossSurfaceConfirmationRequirementKind = (
        CrossSurfaceConfirmationRequirementKind.OPERATOR_CONFIRMATION_REQUIRED_LATER
    ),
    required_later: bool = True,
    reason: str = "Real operator confirmation will be required in a future pack with explicit UI and consent recording gates.",
    future_pack_or_section: str = "P2.5-D or later",
) -> CrossSurfaceOperatorConfirmationRequirement:
    return CrossSurfaceOperatorConfirmationRequirement(
        requirement_id="p2_5_c_confirmation_requirement::" + _hash_payload(
            {
                "requirement_kind": requirement_kind.value,
                "reason": reason,
                "future_pack_or_section": future_pack_or_section,
            }
        ),
        requirement_kind=requirement_kind,
        required_later=required_later,
        reason=reason,
        future_pack_or_section=future_pack_or_section,
        records_real_consent=False,
        creates_confirmation_ui=False,
        activates_approval=False,
        enforces_permission=False,
        truth_label="CONFIRMATION_REQUIREMENT_ONLY / FUTURE_REQUIREMENT_ONLY / NOT_REAL_OPERATOR_CONSENT / NOT_CONFIRMATION_MODAL / NOT_APPROVAL / NOT_PERMISSION_ENFORCEMENT",
        limitations=(
            "confirmation requirement states future obligation only",
            "requirement does not record consent, create UI, activate approval, or enforce permission",
        ),
    )


def build_cross_surface_operator_confirmation_intent_boundary(
    *,
    confirmation_requirement_ref: str,
    reason: str = "P2.5-C preview/requirement objects must not become authorization, permission, approval, consent, prompt, or execution.",
) -> CrossSurfaceOperatorConfirmationIntentBoundary:
    return CrossSurfaceOperatorConfirmationIntentBoundary(
        boundary_id="p2_5_c_confirmation_intent_boundary::" + _hash_payload(
            {
                "confirmation_requirement_ref": confirmation_requirement_ref,
                "reason": reason,
            }
        ),
        boundary_active=True,
        confirmation_requirement_ref=confirmation_requirement_ref,
        prevents_authorization=True,
        prevents_permission_decision=True,
        prevents_approval_activation=True,
        prevents_consent_recording=True,
        prevents_operator_prompt=True,
        prevents_execution=True,
        prevents_route_execution=True,
        prevents_surface_switch=True,
        reason=reason,
        truth_label="CONFIRMATION_BOUNDARY_ONLY / NOT_AUTHORIZATION / NOT_PERMISSION_ENFORCEMENT / NOT_APPROVAL / NOT_REAL_OPERATOR_CONSENT / NOT_HANDOFF_EXECUTION / NOT_ROUTE_EXECUTION / NOT_SURFACE_SWITCH",
        limitations=(
            "confirmation intent boundary is an authority firewall",
            "boundary blocks preview/requirement from becoming consent, approval, or execution",
        ),
    )


def build_cross_surface_handoff_preview_result(
    *,
    handoff_context_result_ref: str,
    preview_request: CrossSurfaceHandoffPreviewRequest,
    preview_content_items: tuple[CrossSurfaceHandoffPreviewContent, ...],
    explanation_bundle: CrossSurfaceHandoffExplanationBundle,
    confirmation_requirement: CrossSurfaceOperatorConfirmationRequirement,
    confirmation_intent_boundary: CrossSurfaceOperatorConfirmationIntentBoundary,
) -> CrossSurfaceHandoffPreviewResult:
    return CrossSurfaceHandoffPreviewResult(
        preview_result_id="p2_5_c_preview_result::" + _hash_payload(
            {
                "handoff_context_result_ref": handoff_context_result_ref,
                "preview_request_id": preview_request.preview_request_id,
                "confirmation_requirement_id": confirmation_requirement.requirement_id,
            }
        ),
        section_id=P2_5_C_SECTION_ID,
        created_for_pack=P2_5_C_PACK_ID,
        official_section_name=P2_5_C_OFFICIAL_SECTION_NAME,
        handoff_context_result_ref=handoff_context_result_ref,
        preview_request=preview_request,
        preview_content_items=preview_content_items,
        explanation_bundle=explanation_bundle,
        confirmation_requirement=confirmation_requirement,
        confirmation_intent_boundary=confirmation_intent_boundary,
        result_status=CrossSurfacePreviewResultStatus.PREVIEW_READY_CONTRACT_ONLY,
        no_confirmation_boundary_active=True,
        no_execution_boundary_active=True,
        is_transition_result=False,
        is_route_result=False,
        is_live_ui=False,
        is_source_of_truth=False,
        renders_preview_ui=False,
        creates_explanation_panel=False,
        creates_confirmation_modal=False,
        records_real_consent=False,
        activates_approval=False,
        authorizes_action=False,
        enforces_permission=False,
        executes_handoff=False,
        switches_surface=False,
        executes_route=False,
        mutates_runtime=False,
        writes_memory=False,
        writes_trace=False,
        writes_storage=False,
        truth_label="PREVIEW_RESULT_ONLY / READ_MODEL_ONLY / NO_CONFIRMATION_BOUNDARY / NO_EXECUTION_BOUNDARY / NOT_TRANSITION_RESULT / NOT_ROUTE_RESULT / NOT_UI / NOT_RUNTIME_MUTATION",
        limitations=(
            "preview result is read model only",
            "preview result is not handoff execution, transition result, route result, or live UI",
        ),
    )


def build_p2_5_c_side_effect_proof() -> P25CSideEffectProof:
    return P25CSideEffectProof()


def _build_preview_content_items_from_context(
    context_pack: P25BHandoffContextResult,
    handoff_context_result_ref: str,
) -> tuple[CrossSurfaceHandoffPreviewContent, ...]:
    snapshot = context_pack.context_snapshot
    availability_ref = context_pack.availability.availability_id
    explanation_refs = tuple(
        explanation.explanation_id for explanation in context_pack.explanations
    )
    context_refs = tuple(item.context_item_id for item in context_pack.context_items)
    return (
        build_cross_surface_handoff_preview_content(
            content_kind=CrossSurfacePreviewContentKind.SOURCE_TARGET_SUMMARY,
            content_label=f"Source {snapshot.source_surface_id} to target {snapshot.target_surface_id}",
            source_ref=handoff_context_result_ref,
            context_refs=context_refs,
        ),
        build_cross_surface_handoff_preview_content(
            content_kind=CrossSurfacePreviewContentKind.CONTEXT_SUMMARY,
            content_label="Handoff context snapshot summary",
            source_ref=snapshot.snapshot_id,
            context_refs=context_refs,
        ),
        build_cross_surface_handoff_preview_content(
            content_kind=CrossSurfacePreviewContentKind.AVAILABILITY_SUMMARY,
            content_label="Availability/readiness summary",
            source_ref=availability_ref,
            availability_ref=availability_ref,
            explanation_refs=explanation_refs,
        ),
        build_cross_surface_handoff_preview_content(
            content_kind=CrossSurfacePreviewContentKind.NO_EXECUTION_WARNING,
            content_label="No handoff execution, route execution, or surface switch in P2.5-C",
            source_ref=handoff_context_result_ref,
        ),
    )


def build_p2_5_c_handoff_preview_result(
    *,
    source_surface_id: str = "hq",
    target_surface_id: str = "corp",
) -> P25CHandoffPreviewResult:
    context_pack = build_p2_5_b_handoff_context_result(
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
    )
    handoff_context_result_ref = context_pack.context_result.context_result_id
    gate = build_cross_surface_handoff_preview_gate(
        repo_evidence_gate_passed=True,
        handoff_context_result_ref=handoff_context_result_ref,
    )
    preview_request = build_cross_surface_handoff_preview_request(
        handoff_context_result_ref=handoff_context_result_ref,
        request_kind=CrossSurfacePreviewRequestKind.REVIEW_CONTEXT,
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
    )
    preview_content_items = _build_preview_content_items_from_context(
        context_pack,
        handoff_context_result_ref,
    )
    explanation_refs = tuple(
        explanation.explanation_id for explanation in context_pack.explanations
    )
    content_refs = tuple(item.preview_content_id for item in preview_content_items)
    explanation_bundle = build_cross_surface_handoff_explanation_bundle(
        handoff_context_result_ref=handoff_context_result_ref,
        explanation_refs=explanation_refs,
        content_refs=content_refs,
        summary="P2.5-C bundles P2.5-B explanations and preview content for operator understanding without approval or execution.",
    )
    confirmation_requirement = build_cross_surface_operator_confirmation_requirement()
    confirmation_intent_boundary = build_cross_surface_operator_confirmation_intent_boundary(
        confirmation_requirement_ref=confirmation_requirement.requirement_id,
    )
    preview_result = build_cross_surface_handoff_preview_result(
        handoff_context_result_ref=handoff_context_result_ref,
        preview_request=preview_request,
        preview_content_items=preview_content_items,
        explanation_bundle=explanation_bundle,
        confirmation_requirement=confirmation_requirement,
        confirmation_intent_boundary=confirmation_intent_boundary,
    )
    drift, _details = detect_surface_taxonomy_drift()
    proof = build_p2_5_c_side_effect_proof()
    result = P25CHandoffPreviewResult(
        pack_id=P2_5_C_PACK_ID,
        section_id=P2_5_C_SECTION_ID,
        official_section_name=P2_5_C_OFFICIAL_SECTION_NAME,
        covered_checkpoints=P2_5_C_PACK_CHECKPOINT_IDS,
        dependency_pack=P2_5_C_DEPENDENCY_PACK,
        preview_gate=gate,
        handoff_context_result_ref=handoff_context_result_ref,
        preview_request=preview_request,
        preview_content_items=preview_content_items,
        explanation_bundle=explanation_bundle,
        confirmation_requirement=confirmation_requirement,
        confirmation_intent_boundary=confirmation_intent_boundary,
        preview_result=preview_result,
        truth_labels=_truth_labels(),
        surface_taxonomy_drift=drift,
        side_effect_proof=proof,
        next_pack=P2_5_C_NEXT_PACK,
        claims_live=False,
        claims_trace_verified=False,
        claims_release_scope=False,
        claims_product_behavior=False,
        starts_future_work=False,
    )
    assert_p2_5_c_does_not_start_future_work(result)
    return result


def serialize_p2_5_c_result(result: P25CHandoffPreviewResult) -> str:
    return to_canonical_json(result)


def render_cross_surface_handoff_preview_summary(
    result: P25CHandoffPreviewResult,
) -> str:
    """Read-only text summary; not preview UI, explanation panel, confirmation modal, or execution."""
    lines = [
        f"P2.5-C {result.official_section_name} — Handoff Preview Boundary",
        f"  Pack: {result.pack_id}",
        f"  Section: {result.section_id}",
        f"  Dependency: {result.dependency_pack}",
        f"  Next: {result.next_pack}",
        f"  Context result ref: {result.handoff_context_result_ref}",
        f"  Preview request: {result.preview_request.request_kind.value}",
        f"  Preview content items: {len(result.preview_content_items)}",
        f"  Confirmation required later: {result.confirmation_requirement.required_later}",
        f"  No-confirmation boundary: {result.preview_result.no_confirmation_boundary_active}",
        f"  No-execution boundary: {result.preview_result.no_execution_boundary_active}",
        f"  Claims LIVE: {result.claims_live}",
        f"  Claims TRACE_VERIFIED: {result.claims_trace_verified}",
        f"  Starts future work: {result.starts_future_work}",
    ]
    return "\n".join(lines)


def assert_preview_is_not_ui(request: CrossSurfaceHandoffPreviewRequest) -> None:
    if request.renders_ui:
        _reject(
            "preview request must not render UI",
            field="renders_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_preview_request_is_not_operator_prompt(
    request: CrossSurfaceHandoffPreviewRequest,
) -> None:
    if request.asks_real_operator or request.records_consent:
        _reject(
            "preview request must not ask real operator or record consent",
            field="asks_real_operator",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_explanation_bundle_is_not_approval(
    bundle: CrossSurfaceHandoffExplanationBundle,
) -> None:
    if bundle.is_approval or bundle.is_authorization or bundle.is_operator_confirmation:
        _reject(
            "explanation bundle must not be approval, authorization, or confirmation",
            field="is_approval",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmation_requirement_is_not_consent(
    requirement: CrossSurfaceOperatorConfirmationRequirement,
) -> None:
    if requirement.records_real_consent or requirement.creates_confirmation_ui:
        _reject(
            "confirmation requirement must not record consent or create confirmation UI",
            field="records_real_consent",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_confirmation_intent_is_not_authorization(
    boundary: CrossSurfaceOperatorConfirmationIntentBoundary,
) -> None:
    if not boundary.prevents_authorization or not boundary.prevents_permission_decision:
        _reject(
            "confirmation intent boundary must prevent authorization and permission decision",
            field="prevents_authorization",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_preview_result_is_not_execution(
    preview_result: CrossSurfaceHandoffPreviewResult,
) -> None:
    if (
        preview_result.executes_handoff
        or preview_result.executes_route
        or preview_result.switches_surface
        or preview_result.mutates_runtime
    ):
        _reject(
            "preview result must not execute handoff, route, surface switch, or mutate runtime",
            field="executes_handoff",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_confirmation_boundary_is_active(
    preview_result: CrossSurfaceHandoffPreviewResult,
) -> None:
    if not preview_result.no_confirmation_boundary_active:
        _reject(
            "no-confirmation boundary must be active",
            field="no_confirmation_boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_execution_boundary_is_active(
    preview_result: CrossSurfaceHandoffPreviewResult,
) -> None:
    if not preview_result.no_execution_boundary_active:
        _reject(
            "no-execution boundary must be active",
            field="no_execution_boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_5_c_does_not_start_future_work(result: P25CHandoffPreviewResult) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or result.next_pack != P2_5_C_NEXT_PACK
        or proof.p2_5_d_started
        or proof.p2_6_started
        or proof.p2_7_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.5-C result must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )

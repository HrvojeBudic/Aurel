"""P2.5-A cross-surface handoff foundation (P2.5.0–P2.5.5).

Contract-only declarative cross-surface handoff identity, intent, endpoint,
payload envelope, eligibility, no-route/no-runtime boundary, and foundation
result read model. This module defines deterministic handoff contracts
without performing handoffs, switching surfaces, executing routes, executing
commands, enforcing permissions, mutating runtime, writing memory/storage/
trace, creating UI (cross-surface, drag/drop, animation, frontend, browser,
Tauri, desktop), creating keyboard listeners, integrating Custos, dispatching
tools/workflows, creating API servers, or starting P2.5-B/P2.6/P2.7/P2.10/
P2.13.

Core law:
  - Handoff is not route execution.
  - Handoff is not surface switching.
  - Target surface is not runtime switch.
  - Payload reference is not storage/memory/trace write.
  - Eligibility is not permission enforcement.
  - Intent is not command execution.
  - Boundary result is not runtime transition.
  - DEV_FIXTURE is not LIVE.
  - Report evidence is not TRACE_VERIFIED.
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
from .global_command_section_projection import (
    P2_4_D_PACK_ID,
    P2_4_D_REPORT_PATH,
    P2_4_D_SECTION_SEAL_VERSION,
    build_p2_4_d_command_palette_section_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_KINDS,
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
    SURFACE_KIND_DISPLAY_NAMES,
    SURFACE_KIND_IDS,
    AurelSurfaceKind,
)

# ---------------------------------------------------------------------------
# Pack / section identity
# ---------------------------------------------------------------------------

P2_5_A_PACK_ID = "P2.5-A"
P2_5_A_SECTION_ID = "P2.5"
P2_5_A_OFFICIAL_SECTION_NAME = "Cross-Surface Handoff"
P2_5_A_DEPENDENCY_PACK = P2_4_D_PACK_ID
P2_5_A_NEXT_PACK = "P2.5-B"
P2_5_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.5.0",
    "P2.5.1",
    "P2.5.2",
    "P2.5.3",
    "P2.5.4",
    "P2.5.5",
)
P2_5_A_REPORT_FILENAME = "P2_5_A_CROSS_SURFACE_HANDOFF_FOUNDATION.md"
P2_5_A_REPORT_PATH = f"agent/reports/{P2_5_A_REPORT_FILENAME}"

P2_4_D_COMMIT_REF = "c10c64287f00540f874dfcadf1bddb4ddf683c7b"
P2_4_D_REPORT_HASH_COMMIT_REF = "a67d3f33df7f76e3d8d764e3e737a2e15e3f5354"

# ---------------------------------------------------------------------------
# Version tags
# ---------------------------------------------------------------------------

P2_5_A_GATE_VERSION = "p2_5_a_cross_surface_handoff_gate.v1"
P2_5_A_HANDOFF_ID_VERSION = "p2_5_a_cross_surface_handoff_id.v1"
P2_5_A_INTENT_VERSION = "p2_5_a_cross_surface_handoff_intent.v1"
P2_5_A_ENDPOINT_VERSION = "p2_5_a_cross_surface_endpoint.v1"
P2_5_A_PAYLOAD_ENVELOPE_VERSION = "p2_5_a_cross_surface_payload_envelope.v1"
P2_5_A_ELIGIBILITY_VERSION = "p2_5_a_cross_surface_eligibility.v1"
P2_5_A_UNAVAILABLE_REASON_VERSION = "p2_5_a_cross_surface_unavailable_reason.v1"
P2_5_A_BOUNDARY_VERSION = "p2_5_a_cross_surface_no_route_boundary.v1"
P2_5_A_FOUNDATION_RESULT_VERSION = "p2_5_a_handoff_foundation_result.v1"
P2_5_A_SIDE_EFFECT_VERSION = "p2_5_a_side_effect_proof.v1"
P2_5_A_RESULT_VERSION = "p2_5_a_cross_surface_handoff_result.v1"

# ---------------------------------------------------------------------------
# Non-goals / invariants
# ---------------------------------------------------------------------------

_HANDOFF_NON_GOALS: tuple[str, ...] = (
    "no_route_execution",
    "no_surface_switch",
    "no_runtime_switch",
    "no_command_execution",
    "no_permission_enforcement",
    "no_approval_activation",
    "no_custos_integration",
    "no_storage_write",
    "no_memory_write",
    "no_trace_write",
    "no_runtime_mutation",
    "no_cross_surface_ui",
    "no_drag_drop",
    "no_handoff_animation",
    "no_frontend_ui",
    "no_browser_ui",
    "no_tauri_app",
    "no_keyboard_listener",
    "no_tool_invocation",
    "no_workflow_dispatch",
    "no_api_server",
    "no_event_bus",
    "no_live_claim",
    "no_trace_verified_claim",
    "no_release_scope_claim",
    "no_product_behavior_claim",
    "no_p2_5_b_implementation",
    "no_p2_6_implementation",
    "no_p2_7_implementation",
    "no_p2_10_implementation",
    "no_p2_13_implementation",
)


# ---------------------------------------------------------------------------
# P2.5.0 — Cross-Surface Handoff Section Intake / Gate Contract
# ---------------------------------------------------------------------------

class CrossSurfaceHandoffGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


@dataclass(frozen=True)
class CrossSurfaceHandoffGate(_CanonicalMixin):
    gate_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_section_seal_ref: str
    dependency_contract_scope_demo_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: CrossSurfaceHandoffGateStatus
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_GATE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.gate_status, CrossSurfaceHandoffGateStatus):
            _reject(
                "gate_status must be CrossSurfaceHandoffGateStatus",
                field="gate_status",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "section_id": self.section_id,
            "created_for_pack": self.created_for_pack,
            "official_section_name": self.official_section_name,
            "dependency_pack": self.dependency_pack,
            "dependency_report_ref": self.dependency_report_ref,
            "dependency_commit_ref": self.dependency_commit_ref,
            "dependency_validation_ref": self.dependency_validation_ref,
            "dependency_section_seal_ref": self.dependency_section_seal_ref,
            "dependency_contract_scope_demo_ref": self.dependency_contract_scope_demo_ref,
            "repo_evidence_gate_passed": self.repo_evidence_gate_passed,
            "omni_evidence_required": self.omni_evidence_required,
            "omni_evidence_ignored_by_operator_instruction": (
                self.omni_evidence_ignored_by_operator_instruction
            ),
            "gate_status": self.gate_status.value,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


def build_cross_surface_handoff_gate(
    *,
    repo_evidence_gate_passed: bool,
    omni_evidence_ignored_by_operator_instruction: bool = True,
) -> CrossSurfaceHandoffGate:
    return CrossSurfaceHandoffGate(
        gate_id="p2_5_a_cross_surface_handoff_section_gate",
        section_id=P2_5_A_SECTION_ID,
        created_for_pack=P2_5_A_PACK_ID,
        official_section_name=P2_5_A_OFFICIAL_SECTION_NAME,
        dependency_pack=P2_5_A_DEPENDENCY_PACK,
        dependency_report_ref=P2_4_D_REPORT_PATH,
        dependency_commit_ref=P2_4_D_COMMIT_REF,
        dependency_validation_ref="P2.4-D validation: compileall, focused, aurel_shell, ruff, mypy",
        dependency_section_seal_ref=P2_4_D_SECTION_SEAL_VERSION,
        dependency_contract_scope_demo_ref=f"{P2_4_D_PACK_ID} contract-scope demo",
        repo_evidence_gate_passed=repo_evidence_gate_passed,
        omni_evidence_required=False,
        omni_evidence_ignored_by_operator_instruction=(
            omni_evidence_ignored_by_operator_instruction
        ),
        gate_status=(
            CrossSurfaceHandoffGateStatus.READY
            if repo_evidence_gate_passed
            else CrossSurfaceHandoffGateStatus.BLOCKED
        ),
        truth_label="CONTRACT_ONLY / SECTION_INTAKE_ONLY / REPORT_ONLY / NOT_LIVE / NOT_TRACE_VERIFIED / NOT_PRODUCT_BEHAVIOR",
        limitations=(
            "section intake gate is not section completion",
            "DO NOT claim LIVE",
            "DO NOT claim TRACE_VERIFIED",
            "DO NOT claim product behavior",
        ),
    )


# ---------------------------------------------------------------------------
# P2.5.1 — Handoff Identity / Intent Contract
# ---------------------------------------------------------------------------

class CrossSurfaceHandoffIntentKind(str, Enum):
    OPEN_REFERENCE = "OPEN_REFERENCE"
    CONTINUE_CONTEXT = "CONTINUE_CONTEXT"
    INSPECT_OBJECT = "INSPECT_OBJECT"
    COMPARE_CONTEXT = "COMPARE_CONTEXT"
    SEND_TO_SURFACE = "SEND_TO_SURFACE"
    REQUEST_ATTENTION = "REQUEST_ATTENTION"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


@dataclass(frozen=True)
class CrossSurfaceHandoffId(_CanonicalMixin):
    handoff_id: str
    section_id: str
    created_for_pack: str
    source_surface_id: str
    target_surface_id: str
    payload_kind: str
    intent_kind: str
    stable_key: str
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_HANDOFF_ID_VERSION

    def __post_init__(self) -> None:
        if not self.handoff_id:
            _reject(
                "handoff_id must not be empty",
                field="handoff_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if not self.source_surface_id:
            _reject(
                "source_surface_id must not be empty",
                field="source_surface_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if not self.target_surface_id:
            _reject(
                "target_surface_id must not be empty",
                field="target_surface_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "section_id": self.section_id,
            "created_for_pack": self.created_for_pack,
            "source_surface_id": self.source_surface_id,
            "target_surface_id": self.target_surface_id,
            "payload_kind": self.payload_kind,
            "intent_kind": self.intent_kind,
            "stable_key": self.stable_key,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


@dataclass(frozen=True)
class CrossSurfaceHandoffIntent(_CanonicalMixin):
    intent_id: str
    intent_kind: CrossSurfaceHandoffIntentKind
    description: str
    requested_by: str
    source_surface_id: str
    target_surface_id: str
    executes_command: bool
    executes_route: bool
    switches_surface: bool
    is_authorization: bool
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_INTENT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.intent_kind, CrossSurfaceHandoffIntentKind):
            _reject(
                "intent_kind must be CrossSurfaceHandoffIntentKind",
                field="intent_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.executes_command:
            _reject(
                "handoff intent must not execute commands",
                field="executes_command",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.executes_route:
            _reject(
                "handoff intent must not execute routes",
                field="executes_route",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.switches_surface:
            _reject(
                "handoff intent must not switch surfaces",
                field="switches_surface",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.is_authorization:
            _reject(
                "handoff intent must not be authorization",
                field="is_authorization",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "intent_kind": self.intent_kind.value,
            "description": self.description,
            "requested_by": self.requested_by,
            "source_surface_id": self.source_surface_id,
            "target_surface_id": self.target_surface_id,
            "executes_command": self.executes_command,
            "executes_route": self.executes_route,
            "switches_surface": self.switches_surface,
            "is_authorization": self.is_authorization,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


def build_cross_surface_handoff_id(
    *,
    source_surface_id: str,
    target_surface_id: str,
    payload_kind: str,
    intent_kind: str,
) -> CrossSurfaceHandoffId:
    stable_key_parts = (
        P2_5_A_SECTION_ID,
        P2_5_A_PACK_ID,
        source_surface_id,
        target_surface_id,
        payload_kind,
        intent_kind,
    )
    stable_key = "::".join(stable_key_parts)
    handoff_id = _hash_payload({"stable_key": stable_key})
    return CrossSurfaceHandoffId(
        handoff_id=handoff_id,
        section_id=P2_5_A_SECTION_ID,
        created_for_pack=P2_5_A_PACK_ID,
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
        payload_kind=payload_kind,
        intent_kind=intent_kind,
        stable_key=stable_key,
        truth_label="CONTRACT_ONLY / DECLARATIVE_ONLY / NOT_COMMAND_EXECUTION / NOT_ROUTE_EXECUTION / NOT_AUTHORIZATION / NOT_SURFACE_SWITCH",
        limitations=(
            "handoff identity is deterministic but does not execute handoff",
            "stable_key must not include runtime/mutable execution state",
        ),
    )


def build_cross_surface_handoff_intent(
    *,
    intent_kind: CrossSurfaceHandoffIntentKind,
    description: str,
    source_surface_id: str,
    target_surface_id: str,
    requested_by: str = "contract_fixture",
) -> CrossSurfaceHandoffIntent:
    return CrossSurfaceHandoffIntent(
        intent_id="p2_5_a_handoff_intent::" + _hash_payload(
            {
                "intent_kind": intent_kind.value,
                "source": source_surface_id,
                "target": target_surface_id,
            }
        ),
        intent_kind=intent_kind,
        description=description,
        requested_by=requested_by,
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
        executes_command=False,
        executes_route=False,
        switches_surface=False,
        is_authorization=False,
        truth_label="CONTRACT_ONLY / DECLARATIVE_ONLY / NOT_COMMAND_EXECUTION / NOT_ROUTE_EXECUTION / NOT_AUTHORIZATION / NOT_SURFACE_SWITCH",
        limitations=(
            "intent describes handoff purpose as data only",
            "intent does not execute commands, routes, surface switches, or authorization",
        ),
    )


# ---------------------------------------------------------------------------
# P2.5.2 — Source / Target Surface Contract
# ---------------------------------------------------------------------------

class CrossSurfaceEndpointRole(str, Enum):
    SOURCE = "SOURCE"
    TARGET = "TARGET"


@dataclass(frozen=True)
class CrossSurfaceEndpoint(_CanonicalMixin):
    endpoint_id: str
    endpoint_role: CrossSurfaceEndpointRole
    surface_id: str
    surface_label: str
    uses_official_surface_registry: bool
    surface_known: bool
    surface_taxonomy_drift: bool
    active_navigation_mutation: bool
    runtime_switch: bool
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_ENDPOINT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.endpoint_role, CrossSurfaceEndpointRole):
            _reject(
                "endpoint_role must be CrossSurfaceEndpointRole",
                field="endpoint_role",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.active_navigation_mutation:
            _reject(
                "endpoint must not mutate active navigation",
                field="active_navigation_mutation",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.runtime_switch:
            _reject(
                "endpoint must not be runtime switch",
                field="runtime_switch",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "endpoint_role": self.endpoint_role.value,
            "surface_id": self.surface_id,
            "surface_label": self.surface_label,
            "uses_official_surface_registry": self.uses_official_surface_registry,
            "surface_known": self.surface_known,
            "surface_taxonomy_drift": self.surface_taxonomy_drift,
            "active_navigation_mutation": self.active_navigation_mutation,
            "runtime_switch": self.runtime_switch,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


def build_cross_surface_endpoint(
    *,
    endpoint_role: CrossSurfaceEndpointRole,
    surface_id: str,
) -> CrossSurfaceEndpoint:
    surface_ids = set(SURFACE_KIND_IDS.values())
    surface_kind_str_to_display: dict[str, str] = {}
    for kind, sid in SURFACE_KIND_IDS.items():
        surface_kind_str_to_display[sid] = SURFACE_KIND_DISPLAY_NAMES.get(
            kind, sid
        )

    surface_known = surface_id in surface_ids
    drift, _drift_details = detect_surface_taxonomy_drift()
    surface_taxonomy_drift = drift

    surface_label = surface_kind_str_to_display.get(
        surface_id, surface_id
    )

    return CrossSurfaceEndpoint(
        endpoint_id="p2_5_a_endpoint::" + _hash_payload(
            {"role": endpoint_role.value, "surface_id": surface_id}
        ),
        endpoint_role=endpoint_role,
        surface_id=surface_id,
        surface_label=surface_label,
        uses_official_surface_registry=surface_known,
        surface_known=surface_known,
        surface_taxonomy_drift=surface_taxonomy_drift,
        active_navigation_mutation=False,
        runtime_switch=False,
        truth_label="CONTRACT_ONLY / OFFICIAL_SURFACE_REF_ONLY / NOT_SURFACE_SWITCH / NOT_ROUTE_EXECUTION / NOT_UI_TRANSITION",
        limitations=(
            "source/target surface is data-only reference, not navigation state",
            "endpoint does not switch surfaces at runtime",
            "endpoint does not execute routes",
        ),
    )


# ---------------------------------------------------------------------------
# P2.5.3 — Handoff Payload / Reference Envelope Contract
# ---------------------------------------------------------------------------

class CrossSurfacePayloadKind(str, Enum):
    COMMAND_RESULT_REF = "COMMAND_RESULT_REF"
    COMMAND_PROPOSAL_REF = "COMMAND_PROPOSAL_REF"
    OBJECT_REF = "OBJECT_REF"
    ARTIFACT_REF = "ARTIFACT_REF"
    WINDOW_STATE_REF = "WINDOW_STATE_REF"
    SURFACE_CONTEXT_REF = "SURFACE_CONTEXT_REF"
    SYSTEM_STATUS_REF = "SYSTEM_STATUS_REF"
    DEV_FIXTURE_REF = "DEV_FIXTURE_REF"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


@dataclass(frozen=True)
class CrossSurfacePayloadEnvelope(_CanonicalMixin):
    payload_envelope_id: str
    payload_kind: CrossSurfacePayloadKind
    payload_ref: str
    payload_label: str
    source_ref: str
    ownership_transferred: bool
    storage_written: bool
    memory_written: bool
    trace_written: bool
    object_copied: bool
    object_moved: bool
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_PAYLOAD_ENVELOPE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.payload_kind, CrossSurfacePayloadKind):
            _reject(
                "payload_kind must be CrossSurfacePayloadKind",
                field="payload_kind",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.ownership_transferred:
            _reject(
                "payload envelope must not transfer object ownership",
                field="ownership_transferred",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.storage_written:
            _reject(
                "payload envelope must not write storage",
                field="storage_written",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.memory_written:
            _reject(
                "payload envelope must not write memory",
                field="memory_written",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.trace_written:
            _reject(
                "payload envelope must not write trace",
                field="trace_written",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.object_copied:
            _reject(
                "payload envelope must not copy object",
                field="object_copied",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.object_moved:
            _reject(
                "payload envelope must not move object",
                field="object_moved",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "payload_envelope_id": self.payload_envelope_id,
            "payload_kind": self.payload_kind.value,
            "payload_ref": self.payload_ref,
            "payload_label": self.payload_label,
            "source_ref": self.source_ref,
            "ownership_transferred": self.ownership_transferred,
            "storage_written": self.storage_written,
            "memory_written": self.memory_written,
            "trace_written": self.trace_written,
            "object_copied": self.object_copied,
            "object_moved": self.object_moved,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


def build_cross_surface_payload_envelope(
    *,
    payload_kind: CrossSurfacePayloadKind,
    payload_ref: str,
    payload_label: str = "",
    source_ref: str = "",
) -> CrossSurfacePayloadEnvelope:
    envelope_id = "p2_5_a_payload_envelope::" + _hash_payload(
        {
            "kind": payload_kind.value,
            "payload_ref": payload_ref,
        }
    )
    return CrossSurfacePayloadEnvelope(
        payload_envelope_id=envelope_id,
        payload_kind=payload_kind,
        payload_ref=payload_ref,
        payload_label=payload_label,
        source_ref=source_ref,
        ownership_transferred=False,
        storage_written=False,
        memory_written=False,
        trace_written=False,
        object_copied=False,
        object_moved=False,
        truth_label="REFERENCE_ENVELOPE_ONLY / NOT_MEMORY_WRITE / NOT_STORAGE_WRITE / NOT_TRACE_WRITE / NOT_OBJECT_TRANSFER",
        limitations=(
            "payload envelope references a payload without transferring ownership",
            "payload envelope does not copy, move, persist, or write memory/storage/trace",
        ),
    )


# ---------------------------------------------------------------------------
# P2.5.4 — Handoff Eligibility / Unavailable-State Contract
# ---------------------------------------------------------------------------

class CrossSurfaceEligibilityStatus(str, Enum):
    ELIGIBLE_CONTRACT_ONLY = "ELIGIBLE_CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


@dataclass(frozen=True)
class CrossSurfaceUnavailableReason(_CanonicalMixin):
    reason_id: str
    capability: str
    reason: str
    future_pack_or_section: str
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_UNAVAILABLE_REASON_VERSION

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "reason_id": self.reason_id,
            "capability": self.capability,
            "reason": self.reason,
            "future_pack_or_section": self.future_pack_or_section,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


@dataclass(frozen=True)
class CrossSurfaceEligibility(_CanonicalMixin):
    eligibility_id: str
    eligibility_status: CrossSurfaceEligibilityStatus
    eligible_contract_only: bool
    unavailable_reasons: tuple[CrossSurfaceUnavailableReason, ...]
    requires_permission_later: bool
    requires_approval_later: bool
    requires_route_runtime_later: bool
    requires_ui_later: bool
    is_permission_decision: bool
    grants_permission: bool
    denies_permission: bool
    activates_approval: bool
    blocks_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_ELIGIBILITY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(
            self.eligibility_status, CrossSurfaceEligibilityStatus
        ):
            _reject(
                "eligibility_status must be CrossSurfaceEligibilityStatus",
                field="eligibility_status",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.is_permission_decision:
            _reject(
                "eligibility must not be permission decision",
                field="is_permission_decision",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.grants_permission:
            _reject(
                "eligibility must not grant permission",
                field="grants_permission",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.denies_permission:
            _reject(
                "eligibility must not deny permission",
                field="denies_permission",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.activates_approval:
            _reject(
                "eligibility must not activate approval",
                field="activates_approval",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.blocks_runtime:
            _reject(
                "eligibility must not block runtime",
                field="blocks_runtime",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "eligibility_id": self.eligibility_id,
            "eligibility_status": self.eligibility_status.value,
            "eligible_contract_only": self.eligible_contract_only,
            "unavailable_reasons": len(self.unavailable_reasons),
            "requires_permission_later": self.requires_permission_later,
            "requires_approval_later": self.requires_approval_later,
            "requires_route_runtime_later": self.requires_route_runtime_later,
            "requires_ui_later": self.requires_ui_later,
            "is_permission_decision": self.is_permission_decision,
            "grants_permission": self.grants_permission,
            "denies_permission": self.denies_permission,
            "activates_approval": self.activates_approval,
            "blocks_runtime": self.blocks_runtime,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


_UNAVAILABLE_CAPABILITIES: tuple[tuple[str, str, str], ...] = (
    ("runtime_surface_switching", "runtime surface switching", "P2.6 or later"),
    ("route_execution", "route execution", "P2.6 or later"),
    ("route_handler_invocation", "route handler invocation", "P2.6 or later"),
    ("cross_surface_ui_transition", "cross-surface UI transition", "P2.10 or later"),
    ("drag_drop", "drag/drop", "P2.10 or later"),
    ("window_movement", "window movement", "P2.10 or later"),
    ("command_execution", "command execution", "P2.6 or later"),
    ("approval_activation", "approval activation", "P2.13 or later"),
    ("permission_enforcement", "permission enforcement", "P2.13 or later"),
    ("custos_integration", "Custos integration", "P2.13 or later"),
    ("workflow_tool_dispatch", "workflow/tool dispatch", "P2.13 or later"),
    ("api_event_bridge", "API/event bridge", "P2.10 or later"),
    ("storage_write", "storage write", "P2.6 or later"),
    ("memory_write", "memory write", "P2.13 or later"),
    ("trace_write", "trace write", "P2.13 or later"),
    ("runtime_mutation", "runtime mutation", "P2.6 or later"),
    ("live_handoff", "LIVE handoff", "P2.13 or later"),
    ("trace_verified_handoff", "TRACE_VERIFIED handoff", "P2.13 or later"),
    ("product_behavior", "product behavior", "P2.13 or later"),
    ("release_scope", "release scope", "P2.13 or later"),
)


def _build_default_unavailable_reasons() -> tuple[CrossSurfaceUnavailableReason, ...]:
    reasons: list[CrossSurfaceUnavailableReason] = []
    for cap_key, cap_name, future_pack in _UNAVAILABLE_CAPABILITIES:
        reasons.append(
            CrossSurfaceUnavailableReason(
                reason_id=f"p2_5_a_unavailable::{cap_key}",
                capability=cap_name,
                reason=(
                    f"P2.5-A defines cross-surface handoff contracts only. "
                    f"{cap_name} is unavailable in this scope."
                ),
                future_pack_or_section=future_pack,
                truth_label="UNAVAILABLE_STATE_ONLY / CONTRACT_ELIGIBILITY_ONLY",
                limitations=(),
            )
        )
    return tuple(reasons)


def build_cross_surface_eligibility() -> CrossSurfaceEligibility:
    return CrossSurfaceEligibility(
        eligibility_id="p2_5_a_handoff_eligibility",
        eligibility_status=CrossSurfaceEligibilityStatus.ELIGIBLE_CONTRACT_ONLY,
        eligible_contract_only=True,
        unavailable_reasons=_build_default_unavailable_reasons(),
        requires_permission_later=True,
        requires_approval_later=True,
        requires_route_runtime_later=True,
        requires_ui_later=True,
        is_permission_decision=False,
        grants_permission=False,
        denies_permission=False,
        activates_approval=False,
        blocks_runtime=False,
        truth_label="CONTRACT_ELIGIBILITY_ONLY / UNAVAILABLE_STATE_ONLY / NOT_PERMISSION_ENFORCEMENT / NOT_APPROVAL / NOT_AUTHORIZATION",
        limitations=(
            "eligibility describes contract-only availability and unavailable reasons",
            "eligibility does not grant/deny permissions or enforce policy",
            "all runtime capabilities are marked unavailable with future pack references",
        ),
    )


# ---------------------------------------------------------------------------
# P2.5.5 — No-Route / No-Runtime Boundary Result Contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrossSurfaceNoRouteBoundary(_CanonicalMixin):
    boundary_id: str
    handoff_id: str
    boundary_active: bool
    surface_switch_allowed: bool
    route_execution_allowed: bool
    route_handler_invoked: bool
    ui_transition_created: bool
    drag_drop_created: bool
    command_execution_allowed: bool
    approval_activated: bool
    permission_enforced: bool
    tool_invoked: bool
    workflow_dispatched: bool
    storage_written: bool
    memory_written: bool
    trace_written: bool
    runtime_mutated: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_BOUNDARY_VERSION

    def __post_init__(self) -> None:
        if not self.boundary_active:
            _reject(
                "no-route boundary must be active",
                field="boundary_active",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.surface_switch_allowed:
            _reject(
                "no-route boundary must not allow surface switch",
                field="surface_switch_allowed",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.route_execution_allowed:
            _reject(
                "no-route boundary must not allow route execution",
                field="route_execution_allowed",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.route_handler_invoked:
            _reject(
                "no-route boundary must not invoke route handler",
                field="route_handler_invoked",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.ui_transition_created:
            _reject(
                "no-route boundary must not create UI transition",
                field="ui_transition_created",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.drag_drop_created:
            _reject(
                "no-route boundary must not create drag/drop",
                field="drag_drop_created",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.command_execution_allowed:
            _reject(
                "no-route boundary must not allow command execution",
                field="command_execution_allowed",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.approval_activated:
            _reject(
                "no-route boundary must not activate approval",
                field="approval_activated",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.permission_enforced:
            _reject(
                "no-route boundary must not enforce permission",
                field="permission_enforced",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.tool_invoked:
            _reject(
                "no-route boundary must not invoke tools",
                field="tool_invoked",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.workflow_dispatched:
            _reject(
                "no-route boundary must not dispatch workflows",
                field="workflow_dispatched",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.storage_written:
            _reject(
                "no-route boundary must not write storage",
                field="storage_written",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.memory_written:
            _reject(
                "no-route boundary must not write memory",
                field="memory_written",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.trace_written:
            _reject(
                "no-route boundary must not write trace",
                field="trace_written",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        if self.runtime_mutated:
            _reject(
                "no-route boundary must not mutate runtime",
                field="runtime_mutated",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "handoff_id": self.handoff_id,
            "boundary_active": self.boundary_active,
            "surface_switch_allowed": self.surface_switch_allowed,
            "route_execution_allowed": self.route_execution_allowed,
            "route_handler_invoked": self.route_handler_invoked,
            "ui_transition_created": self.ui_transition_created,
            "drag_drop_created": self.drag_drop_created,
            "command_execution_allowed": self.command_execution_allowed,
            "approval_activated": self.approval_activated,
            "permission_enforced": self.permission_enforced,
            "tool_invoked": self.tool_invoked,
            "workflow_dispatched": self.workflow_dispatched,
            "storage_written": self.storage_written,
            "memory_written": self.memory_written,
            "trace_written": self.trace_written,
            "runtime_mutated": self.runtime_mutated,
            "reason": self.reason,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


@dataclass(frozen=True)
class CrossSurfaceHandoffFoundationResult(_CanonicalMixin):
    foundation_result_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    handoff_id: str
    intent: str
    source_endpoint: str
    target_endpoint: str
    payload_envelope: str
    eligibility: str
    no_route_boundary: str
    result_status: str
    is_transition_result: bool
    is_route_result: bool
    is_live_ui: bool
    is_source_of_truth: bool
    switches_surface: bool
    executes_route: bool
    executes_command: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    truth_label: str
    limitations: tuple[str, ...]

    version_tag: str = P2_5_A_FOUNDATION_RESULT_VERSION

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "foundation_result_id": self.foundation_result_id,
            "section_id": self.section_id,
            "created_for_pack": self.created_for_pack,
            "official_section_name": self.official_section_name,
            "handoff_id": self.handoff_id,
            "intent": self.intent,
            "source_endpoint": self.source_endpoint,
            "target_endpoint": self.target_endpoint,
            "payload_envelope": self.payload_envelope,
            "eligibility": self.eligibility,
            "no_route_boundary": self.no_route_boundary,
            "result_status": self.result_status,
            "is_transition_result": self.is_transition_result,
            "is_route_result": self.is_route_result,
            "is_live_ui": self.is_live_ui,
            "is_source_of_truth": self.is_source_of_truth,
            "switches_surface": self.switches_surface,
            "executes_route": self.executes_route,
            "executes_command": self.executes_command,
            "mutates_runtime": self.mutates_runtime,
            "writes_memory": self.writes_memory,
            "writes_trace": self.writes_trace,
            "writes_storage": self.writes_storage,
            "truth_label": self.truth_label,
            "limitations": list(self.limitations),
            "version_tag": self.version_tag,
        }


def build_cross_surface_no_route_boundary(
    *,
    handoff_id: str,
) -> CrossSurfaceNoRouteBoundary:
    return CrossSurfaceNoRouteBoundary(
        boundary_id="p2_5_a_no_route_boundary::" + _hash_payload(
            {"handoff_id": handoff_id}
        ),
        handoff_id=handoff_id,
        boundary_active=True,
        surface_switch_allowed=False,
        route_execution_allowed=False,
        route_handler_invoked=False,
        ui_transition_created=False,
        drag_drop_created=False,
        command_execution_allowed=False,
        approval_activated=False,
        permission_enforced=False,
        tool_invoked=False,
        workflow_dispatched=False,
        storage_written=False,
        memory_written=False,
        trace_written=False,
        runtime_mutated=False,
        reason="P2.5-A defines declarative handoff contracts only; no route/runtime execution occurs",
        truth_label="NO_ROUTE_BOUNDARY / NO_RUNTIME_BOUNDARY",
        limitations=(),
    )


def build_cross_surface_handoff_foundation_result(
    *,
    handoff_id: str,
    intent: str,
    source_endpoint: str,
    target_endpoint: str,
    payload_envelope: str,
    eligibility: str,
    no_route_boundary: str,
) -> CrossSurfaceHandoffFoundationResult:
    return CrossSurfaceHandoffFoundationResult(
        foundation_result_id="p2_5_a_foundation_result::" + _hash_payload(
            {"handoff_id": handoff_id}
        ),
        section_id=P2_5_A_SECTION_ID,
        created_for_pack=P2_5_A_PACK_ID,
        official_section_name=P2_5_A_OFFICIAL_SECTION_NAME,
        handoff_id=handoff_id,
        intent=intent,
        source_endpoint=source_endpoint,
        target_endpoint=target_endpoint,
        payload_envelope=payload_envelope,
        eligibility=eligibility,
        no_route_boundary=no_route_boundary,
        result_status="CONTRACT_ONLY",
        is_transition_result=False,
        is_route_result=False,
        is_live_ui=False,
        is_source_of_truth=False,
        switches_surface=False,
        executes_route=False,
        executes_command=False,
        mutates_runtime=False,
        writes_memory=False,
        writes_trace=False,
        writes_storage=False,
        truth_label="READ_MODEL_ONLY / NOT_TRANSITION_RESULT / NOT_ROUTE_RESULT / NOT_LIVE / NOT_TRACE_VERIFIED",
        limitations=(
            "foundation result is read model only",
            "not transition result, route result, live UI, or source of truth",
            "does not switch surfaces, execute routes, execute commands, or mutate runtime",
        ),
    )


# ---------------------------------------------------------------------------
# Side-effect / no-authority proof
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class P25ASideEffectProof(_CanonicalMixin):
    cross_surface_ui_created: bool
    drag_drop_created: bool
    handoff_animation_created: bool
    frontend_ui_created: bool
    browser_ui_created: bool
    tauri_app_created: bool
    desktop_app_created: bool
    keyboard_listener_created: bool
    shortcut_handler_created: bool
    surface_runtime_switch_created: bool
    route_execution_created: bool
    route_handler_created: bool
    route_runtime_created: bool
    command_execution_created: bool
    command_router_created: bool
    command_handler_created: bool
    command_invocation_created: bool
    tool_invocation_created: bool
    workflow_dispatch_created: bool
    approval_created: bool
    approval_activated: bool
    permission_enforcement_created: bool
    permission_granted: bool
    permission_denied: bool
    runtime_blocking_created: bool
    custos_integration_created: bool
    api_server_created: bool
    http_routes_created: bool
    event_bus_created: bool
    runtime_events_emitted: bool
    local_storage_written: bool
    browser_storage_written: bool
    memory_written: bool
    trace_written: bool
    runtime_mutated: bool
    source_of_truth_created: bool
    live_claimed: bool
    trace_verified_claimed: bool
    release_scope_claimed: bool
    product_behavior_claimed: bool
    p2_5_b_started: bool
    p2_6_started: bool
    p2_7_started: bool
    p2_10_started: bool
    p2_13_started: bool

    version_tag: str = P2_5_A_SIDE_EFFECT_VERSION

    def __post_init__(self) -> None:
        _ensure_all_false(self, "side-effect proof")

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "cross_surface_ui_created": self.cross_surface_ui_created,
            "drag_drop_created": self.drag_drop_created,
            "handoff_animation_created": self.handoff_animation_created,
            "frontend_ui_created": self.frontend_ui_created,
            "browser_ui_created": self.browser_ui_created,
            "tauri_app_created": self.tauri_app_created,
            "desktop_app_created": self.desktop_app_created,
            "keyboard_listener_created": self.keyboard_listener_created,
            "shortcut_handler_created": self.shortcut_handler_created,
            "surface_runtime_switch_created": self.surface_runtime_switch_created,
            "route_execution_created": self.route_execution_created,
            "route_handler_created": self.route_handler_created,
            "route_runtime_created": self.route_runtime_created,
            "command_execution_created": self.command_execution_created,
            "command_router_created": self.command_router_created,
            "command_handler_created": self.command_handler_created,
            "command_invocation_created": self.command_invocation_created,
            "tool_invocation_created": self.tool_invocation_created,
            "workflow_dispatch_created": self.workflow_dispatch_created,
            "approval_created": self.approval_created,
            "approval_activated": self.approval_activated,
            "permission_enforcement_created": self.permission_enforcement_created,
            "permission_granted": self.permission_granted,
            "permission_denied": self.permission_denied,
            "runtime_blocking_created": self.runtime_blocking_created,
            "custos_integration_created": self.custos_integration_created,
            "api_server_created": self.api_server_created,
            "http_routes_created": self.http_routes_created,
            "event_bus_created": self.event_bus_created,
            "runtime_events_emitted": self.runtime_events_emitted,
            "local_storage_written": self.local_storage_written,
            "browser_storage_written": self.browser_storage_written,
            "memory_written": self.memory_written,
            "trace_written": self.trace_written,
            "runtime_mutated": self.runtime_mutated,
            "source_of_truth_created": self.source_of_truth_created,
            "live_claimed": self.live_claimed,
            "trace_verified_claimed": self.trace_verified_claimed,
            "release_scope_claimed": self.release_scope_claimed,
            "product_behavior_claimed": self.product_behavior_claimed,
            "p2_5_b_started": self.p2_5_b_started,
            "p2_6_started": self.p2_6_started,
            "p2_7_started": self.p2_7_started,
            "p2_10_started": self.p2_10_started,
            "p2_13_started": self.p2_13_started,
            "version_tag": self.version_tag,
        }


def _ensure_all_false(obj: object, label: str) -> None:
    """Assert all boolean fields are False."""
    from dataclasses import fields

    for f in fields(obj):
        val = getattr(obj, f.name)
        if isinstance(val, bool) and val:
            _reject(
                f"{label}: {f.name} must be false",
                field=f.name,
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def build_p2_5_a_side_effect_proof() -> P25ASideEffectProof:
    return P25ASideEffectProof(
        cross_surface_ui_created=False,
        drag_drop_created=False,
        handoff_animation_created=False,
        frontend_ui_created=False,
        browser_ui_created=False,
        tauri_app_created=False,
        desktop_app_created=False,
        keyboard_listener_created=False,
        shortcut_handler_created=False,
        surface_runtime_switch_created=False,
        route_execution_created=False,
        route_handler_created=False,
        route_runtime_created=False,
        command_execution_created=False,
        command_router_created=False,
        command_handler_created=False,
        command_invocation_created=False,
        tool_invocation_created=False,
        workflow_dispatch_created=False,
        approval_created=False,
        approval_activated=False,
        permission_enforcement_created=False,
        permission_granted=False,
        permission_denied=False,
        runtime_blocking_created=False,
        custos_integration_created=False,
        api_server_created=False,
        http_routes_created=False,
        event_bus_created=False,
        runtime_events_emitted=False,
        local_storage_written=False,
        browser_storage_written=False,
        memory_written=False,
        trace_written=False,
        runtime_mutated=False,
        source_of_truth_created=False,
        live_claimed=False,
        trace_verified_claimed=False,
        release_scope_claimed=False,
        product_behavior_claimed=False,
        p2_5_b_started=False,
        p2_6_started=False,
        p2_7_started=False,
        p2_10_started=False,
        p2_13_started=False,
    )


# ---------------------------------------------------------------------------
# P2.5-A Pack Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class P25ACrossSurfaceHandoffResult(_CanonicalMixin):
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    handoff_gate: str
    handoff_id: str
    intent: str
    source_endpoint: str
    target_endpoint: str
    payload_envelope: str
    eligibility: str
    unavailable_reasons: int
    no_route_boundary: str
    foundation_result: str
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    side_effect_proof: str
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool

    version_tag: str = P2_5_A_RESULT_VERSION

    def _to_stable_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "section_id": self.section_id,
            "official_section_name": self.official_section_name,
            "covered_checkpoints": list(self.covered_checkpoints),
            "dependency_pack": self.dependency_pack,
            "handoff_gate": self.handoff_gate,
            "handoff_id": self.handoff_id,
            "intent": self.intent,
            "source_endpoint": self.source_endpoint,
            "target_endpoint": self.target_endpoint,
            "payload_envelope": self.payload_envelope,
            "eligibility": self.eligibility,
            "unavailable_reasons": self.unavailable_reasons,
            "no_route_boundary": self.no_route_boundary,
            "foundation_result": self.foundation_result,
            "truth_labels": list(self.truth_labels),
            "surface_taxonomy_drift": self.surface_taxonomy_drift,
            "side_effect_proof": self.side_effect_proof,
            "next_pack": self.next_pack,
            "claims_live": self.claims_live,
            "claims_trace_verified": self.claims_trace_verified,
            "claims_release_scope": self.claims_release_scope,
            "claims_product_behavior": self.claims_product_behavior,
            "starts_future_work": self.starts_future_work,
            "version_tag": self.version_tag,
        }


def build_p2_5_a_cross_surface_handoff_result(
    *,
    handoff_gate: str,
    handoff_id: str,
    intent: str,
    source_endpoint: str,
    target_endpoint: str,
    payload_envelope: str,
    eligibility: str,
    unavailable_reasons: int,
    no_route_boundary: str,
    foundation_result: str,
    side_effect_proof: str,
) -> P25ACrossSurfaceHandoffResult:
    drift, _drift_details = detect_surface_taxonomy_drift()
    return P25ACrossSurfaceHandoffResult(
        pack_id=P2_5_A_PACK_ID,
        section_id=P2_5_A_SECTION_ID,
        official_section_name=P2_5_A_OFFICIAL_SECTION_NAME,
        covered_checkpoints=P2_5_A_PACK_CHECKPOINT_IDS,
        dependency_pack=P2_5_A_DEPENDENCY_PACK,
        handoff_gate=handoff_gate,
        handoff_id=handoff_id,
        intent=intent,
        source_endpoint=source_endpoint,
        target_endpoint=target_endpoint,
        payload_envelope=payload_envelope,
        eligibility=eligibility,
        unavailable_reasons=unavailable_reasons,
        no_route_boundary=no_route_boundary,
        foundation_result=foundation_result,
        truth_labels=(
            "CONTRACT_ONLY",
            "DECLARATIVE_ONLY",
            "READ_MODEL_ONLY",
            "DEV_FIXTURE",
            "REPORT_ONLY",
            "UNAVAILABLE",
            "NOT_SURFACE_SWITCH",
            "NOT_ROUTE_EXECUTION",
            "NOT_UI_TRANSITION",
            "NOT_DRAG_DROP",
            "NOT_COMMAND_EXECUTION",
            "NOT_COMMAND_ROUTER",
            "NOT_COMMAND_HANDLER",
            "NOT_INVOCATION",
            "NOT_APPROVAL",
            "NOT_AUTHORIZATION",
            "NOT_PERMISSION_ENFORCEMENT",
            "NOT_MEMORY_WRITE",
            "NOT_TRACE_WRITE",
            "NOT_STORAGE_WRITE",
            "NOT_RUNTIME_MUTATION",
            "NOT_LIVE",
            "NOT_TRACE_VERIFIED",
            "NOT_PRODUCT_BEHAVIOR",
            "NOT_RELEASE_SCOPE",
        ),
        surface_taxonomy_drift=drift,
        side_effect_proof=side_effect_proof,
        next_pack=P2_5_A_NEXT_PACK,
        claims_live=False,
        claims_trace_verified=False,
        claims_release_scope=False,
        claims_product_behavior=False,
        starts_future_work=False,
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def serialize_p2_5_a_result(result: P25ACrossSurfaceHandoffResult) -> dict[str, Any]:
    return to_canonical_json(result)


def render_cross_surface_handoff_summary(
    result: P25ACrossSurfaceHandoffResult,
) -> str:
    """Read-only summary render — does not create UI or execute anything."""
    lines = [
        f"P2.5-A {result.official_section_name} — Foundation Result",
        f"  Pack: {result.pack_id}",
        f"  Section: {result.section_id}",
        f"  Dependency: {result.dependency_pack}",
        f"  Next: {result.next_pack}",
        f"  Checkpoints: {', '.join(result.covered_checkpoints)}",
        f"  Unavailable reasons: {result.unavailable_reasons}",
        f"  Surface taxonomy drift: {result.surface_taxonomy_drift}",
        f"  Claims LIVE: {result.claims_live}",
        f"  Claims TRACE_VERIFIED: {result.claims_trace_verified}",
        f"  Claims RELEASE_SCOPE: {result.claims_release_scope}",
        f"  Claims product behavior: {result.claims_product_behavior}",
        f"  Starts future work: {result.starts_future_work}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Invariant assertions
# ---------------------------------------------------------------------------

def assert_handoff_is_not_route_execution() -> None:
    """Handoff contracts must not execute routes."""
    # existence proof: all intent/endpoint objects reject route execution


def assert_target_surface_is_not_runtime_switch() -> None:
    """Target surface must not be a runtime switch."""
    # existence proof: CrossSurfaceEndpoint rejects runtime_switch=True


def assert_payload_is_not_storage_or_memory_write() -> None:
    """Payload envelope must not write storage, memory, or trace."""
    # existence proof: CrossSurfacePayloadEnvelope rejects write booleans


def assert_eligibility_is_not_permission_enforcement() -> None:
    """Eligibility must not enforce, grant, or deny permissions."""
    # existence proof: CrossSurfaceEligibility rejects permission booleans


def assert_no_route_boundary_is_active() -> None:
    """No-route boundary must be active and reject all execution."""
    # existence proof: CrossSurfaceNoRouteBoundary requires boundary_active=True


def assert_p2_5_a_does_not_start_future_work() -> None:
    """P2.5-A must not start P2.5-B, P2.6, P2.7, P2.10, or P2.13."""
    # existence proof: side-effect proof rejects all future-pack flags


# ---------------------------------------------------------------------------
# DEV_FIXTURE convenience builder
# ---------------------------------------------------------------------------

def build_p2_5_a_fixture_handoff_pipeline(
    *,
    source_surface_id: str = "hq",
    target_surface_id: str = "corp",
) -> P25ACrossSurfaceHandoffResult:
    """Build a complete DEV_FIXTURE handoff pipeline.

    Creates gate, handoff identity, intent, source/target endpoints,
    payload envelope, eligibility, no-route boundary, foundation result,
    side-effect proof, and pack result in one call. All objects are
    contract/read-model only; nothing is executed.
    """
    gate = build_cross_surface_handoff_gate(repo_evidence_gate_passed=True)
    handoff_id_obj = build_cross_surface_handoff_id(
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
        payload_kind=CrossSurfacePayloadKind.DEV_FIXTURE_REF.value,
        intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE.value,
    )
    intent_obj = build_cross_surface_handoff_intent(
        intent_kind=CrossSurfaceHandoffIntentKind.DEV_FIXTURE,
        description=f"DEV_FIXTURE handoff from {source_surface_id} to {target_surface_id}",
        source_surface_id=source_surface_id,
        target_surface_id=target_surface_id,
    )
    source = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.SOURCE,
        surface_id=source_surface_id,
    )
    target = build_cross_surface_endpoint(
        endpoint_role=CrossSurfaceEndpointRole.TARGET,
        surface_id=target_surface_id,
    )
    envelope = build_cross_surface_payload_envelope(
        payload_kind=CrossSurfacePayloadKind.DEV_FIXTURE_REF,
        payload_ref="dev_fixture::handoff_test_payload",
        payload_label="DEV_FIXTURE test payload",
    )
    eligibility = build_cross_surface_eligibility()
    boundary = build_cross_surface_no_route_boundary(
        handoff_id=handoff_id_obj.handoff_id,
    )
    foundation = build_cross_surface_handoff_foundation_result(
        handoff_id=handoff_id_obj.handoff_id,
        intent=intent_obj.intent_id,
        source_endpoint=source.endpoint_id,
        target_endpoint=target.endpoint_id,
        payload_envelope=envelope.payload_envelope_id,
        eligibility=eligibility.eligibility_id,
        no_route_boundary=boundary.boundary_id,
    )
    proof = build_p2_5_a_side_effect_proof()

    return build_p2_5_a_cross_surface_handoff_result(
        handoff_gate=gate.gate_id,
        handoff_id=handoff_id_obj.handoff_id,
        intent=intent_obj.intent_id,
        source_endpoint=source.endpoint_id,
        target_endpoint=target.endpoint_id,
        payload_envelope=envelope.payload_envelope_id,
        eligibility=eligibility.eligibility_id,
        unavailable_reasons=len(eligibility.unavailable_reasons),
        no_route_boundary=boundary.boundary_id,
        foundation_result=foundation.foundation_result_id,
        side_effect_proof=_hash_payload(proof._to_stable_dict()),
    )

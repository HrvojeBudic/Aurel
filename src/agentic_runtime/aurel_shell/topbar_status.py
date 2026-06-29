"""AurelShell topbar status slot contracts (P2.1-B / P2.1.6-P2.1.10).

Contract-only status projection over the P2.1-A global topbar registry/read
model. Status slots are bounded projections: they do not authenticate, grant
authority, perform runtime probes, emit events, create notifications, enforce
security, mutate runtime, write memory, or write trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .topbar import (
    P2_1_A_NEXT_PACK,
    P2_1_A_PACK_ID,
    P2_1_SECTION_ID,
    P2_1_SECTION_NAME,
    P21CheckpointRead,
    P21CheckpointStatus,
    SurfaceRegistry,
    TopbarReadModel,
    build_default_topbar_surface_registry,
    build_global_topbar_read_model,
)

P2_1_B_PACK_ID = "P2.1-B"
P2_1_B_PACK_NAME = "Topbar Status Slots / Availability / Operator Context"
P2_1_B_NEXT_PACK = "P2.1-C"
P2_1_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.1.6",
    "P2.1.7",
    "P2.1.8",
    "P2.1.9",
    "P2.1.10",
)
P2_1_B_DEPENDENCY_PACKS: tuple[str, ...] = (
    "P2.0-A",
    "P2.0-B",
    "P2.0-C",
    "P2.0-D",
    "P2.0-E",
    "P2.0-F",
    "P2.1-A",
)
P2_1_A_REPORT_FILENAME = "P2_1_A_GLOBAL_TOPBAR_SURFACE_REGISTRY.md"
TOPBAR_STATUS_PROJECTION_VERSION = "topbar_status_projection.v1"
P2_1_B_PACK_RESULT_VERSION = "p2_1_b_topbar_status_slots_result.v1"

_EnumT = TypeVar("_EnumT", bound=Enum)

_OPERATOR_CONTEXT_NON_GOALS: tuple[str, ...] = (
    "no_auth_backend",
    "no_login_runtime",
    "no_session_runtime",
    "no_identity_mutation",
    "no_authority_lease",
    "no_permission_grant",
)
_AVAILABILITY_NON_GOALS: tuple[str, ...] = (
    "no_backend_health_check",
    "no_live_runtime_probe",
    "no_api_server_status_check",
    "no_event_stream_status",
)
_PROTECTED_BOUNDARY_NON_GOALS: tuple[str, ...] = (
    "no_system_enforcement_runtime",
    "no_custos_integration",
    "no_permission_grants",
    "no_security_engine",
    "no_policy_runtime",
)
_ATTENTION_NON_GOALS: tuple[str, ...] = (
    "no_notification_engine",
    "no_approval_queue",
    "no_runtime_event_stream",
    "no_hq_decision_board",
    "no_workflow_start",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_visual_topbar",
    "no_live_notifications",
    "no_route_runtime",
    "no_command_palette",
    "no_local_nav",
    "no_p2_1_c_implementation",
    "no_p2_2_implementation",
)


class TopbarOperatorContextTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_AUTHORITY = "NOT_AUTHORITY"
    NOT_AUTH_SESSION = "NOT_AUTH_SESSION"
    NOT_IDENTITY_MUTATION = "NOT_IDENTITY_MUTATION"


class TopbarOperatorContextAvailability(str, Enum):
    OPERATOR_CONTEXT_VISIBLE = "OPERATOR_CONTEXT_VISIBLE"
    UNAVAILABLE = "UNAVAILABLE"


class TopbarSurfaceAvailabilityStatus(str, Enum):
    AVAILABLE_CONTRACT = "AVAILABLE_CONTRACT"
    DEV_FIXTURE_AVAILABLE = "DEV_FIXTURE_AVAILABLE"
    UNAVAILABLE_NOT_IMPLEMENTED = "UNAVAILABLE_NOT_IMPLEMENTED"
    UNAVAILABLE_BACKEND_MISSING = "UNAVAILABLE_BACKEND_MISSING"
    UNAVAILABLE_P2_SCOPE = "UNAVAILABLE_P2_SCOPE"
    UNAVAILABLE_P2_1_SCOPE = "UNAVAILABLE_P2_1_SCOPE"
    ERROR = "ERROR"


class TopbarSurfaceAvailabilityTruthBoundary(str, Enum):
    CONTRACT_AVAILABLE = "CONTRACT_AVAILABLE"
    NOT_LIVE = "NOT_LIVE"
    UNAVAILABLE_WITH_REASON = "UNAVAILABLE_WITH_REASON"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_RUNTIME_PROBE = "NOT_RUNTIME_PROBE"


class TopbarProtectedBoundaryReason(str, Enum):
    SYSTEM_PROTECTED = "SYSTEM_PROTECTED"
    SETTINGS_NON_ROOT_CONFIGURATION = "SETTINGS_NON_ROOT_CONFIGURATION"


class TopbarProtectedBoundaryTruthBoundary(str, Enum):
    PROTECTED_BOUNDARY_DISPLAY_ONLY = "PROTECTED_BOUNDARY_DISPLAY_ONLY"
    NOT_ENFORCEMENT = "NOT_ENFORCEMENT"
    NOT_AUTHORITY = "NOT_AUTHORITY"
    NOT_CUSTOS_CALL = "NOT_CUSTOS_CALL"


class TopbarAttentionKind(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    PROTECTED = "PROTECTED"
    FIXTURE = "FIXTURE"


class TopbarAttentionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKING = "BLOCKING"


class TopbarAttentionTruthBoundary(str, Enum):
    STATUS_INDICATOR_ONLY = "STATUS_INDICATOR_ONLY"
    NOT_RUNTIME_EVENT = "NOT_RUNTIME_EVENT"
    NOT_NOTIFICATION_ENGINE = "NOT_NOTIFICATION_ENGINE"
    NOT_APPROVAL_QUEUE = "NOT_APPROVAL_QUEUE"


class TopbarStatusProjectionTruthBoundary(str, Enum):
    PROJECTION_ONLY = "PROJECTION_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_LIVE_UI = "NOT_LIVE_UI"
    NOT_NOTIFICATION_ENGINE = "NOT_NOTIFICATION_ENGINE"
    NOT_RUNTIME_EVENT = "NOT_RUNTIME_EVENT"


@dataclass(frozen=True)
class TopbarOperatorContextSlot(_CanonicalMixin):
    operator_context_id: str
    operator_display_label: str
    session_scope: str
    authority_context_label: str
    is_authenticated_context: bool
    is_authority_grant: bool
    authority_granted: bool
    auth_session_created: bool
    identity_mutated: bool
    truth_label: str
    availability: TopbarOperatorContextAvailability
    unavailable_reason: str
    source: str
    non_goals: tuple[str, ...]
    slot_hash: str


@dataclass(frozen=True)
class TopbarSurfaceAvailabilitySlot(_CanonicalMixin):
    surface_id: str
    display_name: str
    availability_status: TopbarSurfaceAvailabilityStatus
    truth_label: str
    is_live: bool
    is_dev_fixture: bool
    is_contract_available: bool
    is_unavailable: bool
    unavailable_reason: str
    required_backend: str
    required_future_pack: str
    requires_runtime_probe: bool
    runtime_probe_performed: bool
    source: str
    non_goals: tuple[str, ...]
    slot_hash: str


@dataclass(frozen=True)
class TopbarProtectedBoundarySlot(_CanonicalMixin):
    surface_id: str
    display_name: str
    protected_reason: TopbarProtectedBoundaryReason
    operator_only: bool
    agent_access_allowed: bool
    requires_explicit_operator_action: bool
    is_system_root: bool
    is_settings_non_root: bool
    enforces_security: bool
    grants_access: bool
    custos_called: bool
    policy_enforced: bool
    truth_label: str
    source: str
    non_goals: tuple[str, ...]
    slot_hash: str


@dataclass(frozen=True)
class TopbarAttentionStatusSlot(_CanonicalMixin):
    attention_id: str
    attention_kind: TopbarAttentionKind
    surface_id: str
    severity: TopbarAttentionSeverity
    message: str
    source: str
    truth_label: str
    is_runtime_event: bool
    is_notification_engine: bool
    approval_queue_created: bool
    workflow_started: bool
    requires_operator_review: bool
    unavailable_reason: str
    non_goals: tuple[str, ...]
    slot_hash: str


@dataclass(frozen=True)
class TopbarStatusUnavailableBinding(_CanonicalMixin):
    binding_id: str
    slot_group: str
    status: str
    unavailable_reason: str
    truth_label: str


@dataclass(frozen=True)
class P21BSideEffectProof(_CanonicalMixin):
    ui_created: bool = False
    frontend_component_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    cli_live_binding_created: bool = False
    tui_live_binding_created: bool = False
    route_runtime_created: bool = False
    browser_tests_created: bool = False
    live_shell_created: bool = False
    notification_engine_created: bool = False
    approval_queue_created: bool = False
    runtime_event_stream_created: bool = False
    auth_session_backend_created: bool = False
    source_of_truth_created: bool = False
    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    event_bus_created: bool = False
    api_server_created: bool = False
    http_route_created: bool = False
    p2_1_c_started: bool = False
    p2_2_started: bool = False


@dataclass(frozen=True)
class TopbarStatusProjection(_CanonicalMixin):
    projection_id: str
    created_for_pack: str
    topbar_read_model_ref: str
    registry_ref: str
    operator_context_slot: TopbarOperatorContextSlot
    surface_availability_slots: tuple[TopbarSurfaceAvailabilitySlot, ...]
    protected_boundary_slots: tuple[TopbarProtectedBoundarySlot, ...]
    attention_status_slots: tuple[TopbarAttentionStatusSlot, ...]
    truth_boundary: tuple[TopbarStatusProjectionTruthBoundary, ...]
    unavailable_bindings: tuple[TopbarStatusUnavailableBinding, ...]
    side_effect_proof: P21BSideEffectProof
    is_live_ui: bool
    creates_ui: bool
    creates_notification_engine: bool
    emits_runtime_event: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    starts_p2_1_c: bool
    starts_p2_2: bool
    next_pack: str
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P21BTopbarStatusSlotsPackResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    depends_on_pack: str
    depends_on_report: str
    topbar_read_model_ref: str
    registry_ref: str
    checkpoint_reads: tuple[P21CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    projection: TopbarStatusProjection
    side_effect_proof: P21BSideEffectProof
    truth_labels: tuple[str, ...]
    next_pack: str
    result_hash: str


def _coerce_enum(enum_cls: type[_EnumT], value: _EnumT | str, field: str) -> _EnumT:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            try:
                return enum_cls[value]
            except KeyError:
                pass
    _reject(
        f"invalid {field}: {value!r}",
        field=field,
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def _require_reason(reason: str, *, field: str) -> None:
    if not reason:
        _reject(
            "unavailable or error state requires unavailable_reason",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def build_topbar_operator_context_slot(
    *,
    operator_context_id: str = "operator_context_default",
    operator_display_label: str = "Operator",
    session_scope: str = "read_model_session_scope",
    authority_context_label: str = "visible_operator_context_not_authority",
    availability: TopbarOperatorContextAvailability | str = (
        TopbarOperatorContextAvailability.OPERATOR_CONTEXT_VISIBLE
    ),
    unavailable_reason: str = "",
    source: str = "P2.1-B contract projection",
) -> TopbarOperatorContextSlot:
    availability_value = _coerce_enum(
        TopbarOperatorContextAvailability,
        availability,
        "availability",
    )
    if availability_value == TopbarOperatorContextAvailability.UNAVAILABLE:
        _require_reason(unavailable_reason, field="unavailable_reason")
    payload = {
        "operator_context_id": operator_context_id,
        "operator_display_label": operator_display_label,
        "session_scope": session_scope,
        "authority_context_label": authority_context_label,
        "is_authenticated_context": False,
        "is_authority_grant": False,
        "authority_granted": False,
        "auth_session_created": False,
        "identity_mutated": False,
        "truth_label": TopbarOperatorContextTruthBoundary.READ_MODEL_ONLY.value,
        "availability": availability_value,
        "unavailable_reason": unavailable_reason,
        "source": source,
        "non_goals": _OPERATOR_CONTEXT_NON_GOALS,
    }
    slot = TopbarOperatorContextSlot(**payload, slot_hash=_hash_payload(payload))
    assert_operator_context_is_not_authority(slot)
    assert_operator_context_does_not_authenticate(slot)
    return slot


def build_surface_availability_slot(
    surface_id: str,
    *,
    registry: SurfaceRegistry | None = None,
    availability_status: TopbarSurfaceAvailabilityStatus | str = (
        TopbarSurfaceAvailabilityStatus.AVAILABLE_CONTRACT
    ),
    unavailable_reason: str = "",
    required_backend: str = "",
    required_future_pack: str = "",
    source: str = "P2.1-A SurfaceRegistry",
) -> TopbarSurfaceAvailabilitySlot:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    status = _coerce_enum(
        TopbarSurfaceAvailabilityStatus,
        availability_status,
        "availability_status",
    )
    entry = next((item for item in registry.entries if item.surface_id == surface_id), None)
    if entry is None:
        _reject(
            f"unknown surface id: {surface_id!r}",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    assert entry is not None
    is_unavailable = status.value.startswith("UNAVAILABLE") or status == (
        TopbarSurfaceAvailabilityStatus.ERROR
    )
    if is_unavailable:
        _require_reason(unavailable_reason, field="unavailable_reason")
    is_contract_available = status == TopbarSurfaceAvailabilityStatus.AVAILABLE_CONTRACT
    payload = {
        "surface_id": entry.surface_id,
        "display_name": entry.display_name,
        "availability_status": status,
        "truth_label": (
            TopbarSurfaceAvailabilityTruthBoundary.UNAVAILABLE_WITH_REASON.value
            if is_unavailable
            else TopbarSurfaceAvailabilityTruthBoundary.CONTRACT_AVAILABLE.value
        ),
        "is_live": False,
        "is_dev_fixture": status == TopbarSurfaceAvailabilityStatus.DEV_FIXTURE_AVAILABLE,
        "is_contract_available": is_contract_available,
        "is_unavailable": is_unavailable,
        "unavailable_reason": unavailable_reason,
        "required_backend": required_backend,
        "required_future_pack": required_future_pack,
        "requires_runtime_probe": False,
        "runtime_probe_performed": False,
        "source": source,
        "non_goals": _AVAILABILITY_NON_GOALS,
    }
    slot = TopbarSurfaceAvailabilitySlot(**payload, slot_hash=_hash_payload(payload))
    assert_availability_is_not_live(slot)
    assert_unavailable_state_has_reason(slot)
    return slot


def build_surface_availability_slots(
    *,
    registry: SurfaceRegistry | None = None,
) -> tuple[TopbarSurfaceAvailabilitySlot, ...]:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    return tuple(
        build_surface_availability_slot(entry.surface_id, registry=registry)
        for entry in registry.entries
        if entry.global_topbar_visible
    )


def build_protected_boundary_slot(
    surface_id: str,
    *,
    registry: SurfaceRegistry | None = None,
) -> TopbarProtectedBoundarySlot:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    entry = next((item for item in registry.entries if item.surface_id == surface_id), None)
    if entry is None:
        _reject(
            f"unknown surface id: {surface_id!r}",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    assert entry is not None
    if surface_id == "system":
        reason = TopbarProtectedBoundaryReason.SYSTEM_PROTECTED
    elif surface_id == "settings":
        reason = TopbarProtectedBoundaryReason.SETTINGS_NON_ROOT_CONFIGURATION
    else:
        _reject(
            "protected boundary slot is only defined for SYSTEM or Settings in P2.1-B",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "surface_id": entry.surface_id,
        "display_name": entry.display_name,
        "protected_reason": reason,
        "operator_only": surface_id == "system",
        "agent_access_allowed": entry.agent_access_allowed if surface_id != "system" else False,
        "requires_explicit_operator_action": surface_id == "system",
        "is_system_root": surface_id == "system",
        "is_settings_non_root": surface_id == "settings",
        "enforces_security": False,
        "grants_access": False,
        "custos_called": False,
        "policy_enforced": False,
        "truth_label": (
            TopbarProtectedBoundaryTruthBoundary.PROTECTED_BOUNDARY_DISPLAY_ONLY.value
        ),
        "source": "P2.1-A registry protected/settings boundary",
        "non_goals": _PROTECTED_BOUNDARY_NON_GOALS,
    }
    slot = TopbarProtectedBoundarySlot(**payload, slot_hash=_hash_payload(payload))
    assert_system_guard_is_display_not_enforcement(slot)
    if surface_id == "settings":
        assert_settings_remains_non_root(slot)
    return slot


def build_protected_boundary_slots(
    *,
    registry: SurfaceRegistry | None = None,
) -> tuple[TopbarProtectedBoundarySlot, ...]:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    return (
        build_protected_boundary_slot("system", registry=registry),
        build_protected_boundary_slot("settings", registry=registry),
    )


def build_topbar_attention_status_slot(
    attention_id: str = "attention_contract_available",
    *,
    attention_kind: TopbarAttentionKind | str = TopbarAttentionKind.INFO,
    surface_id: str = "aurel_cro",
    severity: TopbarAttentionSeverity | str = TopbarAttentionSeverity.LOW,
    message: str = "Topbar status projection available at contract scope",
    source: str = "P2.1-B read-model status",
    requires_operator_review: bool = False,
    unavailable_reason: str = "",
) -> TopbarAttentionStatusSlot:
    kind = _coerce_enum(TopbarAttentionKind, attention_kind, "attention_kind")
    severity_value = _coerce_enum(TopbarAttentionSeverity, severity, "severity")
    if kind == TopbarAttentionKind.UNAVAILABLE:
        _require_reason(unavailable_reason, field="unavailable_reason")
    payload = {
        "attention_id": attention_id,
        "attention_kind": kind,
        "surface_id": surface_id,
        "severity": severity_value,
        "message": message,
        "source": source,
        "truth_label": TopbarAttentionTruthBoundary.STATUS_INDICATOR_ONLY.value,
        "is_runtime_event": False,
        "is_notification_engine": False,
        "approval_queue_created": False,
        "workflow_started": False,
        "requires_operator_review": requires_operator_review,
        "unavailable_reason": unavailable_reason,
        "non_goals": _ATTENTION_NON_GOALS,
    }
    slot = TopbarAttentionStatusSlot(**payload, slot_hash=_hash_payload(payload))
    assert_attention_is_not_runtime_event(slot)
    assert_attention_is_not_notification_engine(slot)
    return slot


def build_topbar_attention_status_slots(
    *,
    registry: SurfaceRegistry | None = None,
) -> tuple[TopbarAttentionStatusSlot, ...]:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    default_surface = registry.topbar_visible_surface_ids[0]
    return (
        build_topbar_attention_status_slot(surface_id=default_surface),
        build_topbar_attention_status_slot(
            attention_id="attention_system_protected",
            attention_kind=TopbarAttentionKind.PROTECTED,
            surface_id="system",
            severity=TopbarAttentionSeverity.MEDIUM,
            message="SYSTEM is operator-only and protected in the topbar projection",
            requires_operator_review=True,
        ),
        build_topbar_attention_status_slot(
            attention_id="attention_topbar_ui_unavailable",
            attention_kind=TopbarAttentionKind.UNAVAILABLE,
            surface_id=default_surface,
            severity=TopbarAttentionSeverity.LOW,
            message="Live visual topbar remains unavailable in P2.1-B",
            unavailable_reason="UNAVAILABLE_UI: P2.1-B is contract/read-model only",
        ),
    )


def _unavailable_bindings_from_slots(
    operator_context_slot: TopbarOperatorContextSlot,
    availability_slots: tuple[TopbarSurfaceAvailabilitySlot, ...],
    attention_slots: tuple[TopbarAttentionStatusSlot, ...],
) -> tuple[TopbarStatusUnavailableBinding, ...]:
    bindings: list[TopbarStatusUnavailableBinding] = []
    if operator_context_slot.availability == TopbarOperatorContextAvailability.UNAVAILABLE:
        bindings.append(
            TopbarStatusUnavailableBinding(
                binding_id=f"{operator_context_slot.operator_context_id}_unavailable",
                slot_group="operator_context",
                status=operator_context_slot.availability.value,
                unavailable_reason=operator_context_slot.unavailable_reason,
                truth_label=TopbarOperatorContextTruthBoundary.READ_MODEL_ONLY.value,
            )
        )
    for availability_slot in availability_slots:
        if availability_slot.is_unavailable:
            bindings.append(
                TopbarStatusUnavailableBinding(
                    binding_id=f"{availability_slot.surface_id}_availability_unavailable",
                    slot_group="surface_availability",
                    status=availability_slot.availability_status.value,
                    unavailable_reason=availability_slot.unavailable_reason,
                    truth_label=availability_slot.truth_label,
                )
            )
    for attention_slot in attention_slots:
        if attention_slot.unavailable_reason:
            bindings.append(
                TopbarStatusUnavailableBinding(
                    binding_id=f"{attention_slot.attention_id}_unavailable",
                    slot_group="attention_status",
                    status=attention_slot.attention_kind.value,
                    unavailable_reason=attention_slot.unavailable_reason,
                    truth_label=attention_slot.truth_label,
                )
            )
    return tuple(bindings)


def build_p2_1_b_side_effect_proof() -> P21BSideEffectProof:
    return P21BSideEffectProof()


def build_topbar_status_projection(
    *,
    registry: SurfaceRegistry | None = None,
    topbar_read_model: TopbarReadModel | None = None,
    operator_context_slot: TopbarOperatorContextSlot | None = None,
    surface_availability_slots: tuple[TopbarSurfaceAvailabilitySlot, ...] | None = None,
    protected_boundary_slots: tuple[TopbarProtectedBoundarySlot, ...] | None = None,
    attention_status_slots: tuple[TopbarAttentionStatusSlot, ...] | None = None,
) -> TopbarStatusProjection:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if topbar_read_model is None:
        topbar_read_model = build_global_topbar_read_model(registry=registry)
    if operator_context_slot is None:
        operator_context_slot = build_topbar_operator_context_slot()
    if surface_availability_slots is None:
        surface_availability_slots = build_surface_availability_slots(registry=registry)
    if protected_boundary_slots is None:
        protected_boundary_slots = build_protected_boundary_slots(registry=registry)
    if attention_status_slots is None:
        attention_status_slots = build_topbar_attention_status_slots(registry=registry)

    assert_topbar_status_extends_p2_1_a_read_model(topbar_read_model, registry)
    side_effects = build_p2_1_b_side_effect_proof()
    unavailable_bindings = _unavailable_bindings_from_slots(
        operator_context_slot,
        surface_availability_slots,
        attention_status_slots,
    )
    payload = {
        "projection_id": "topbar_status_projection_p2_1_b",
        "created_for_pack": P2_1_B_PACK_ID,
        "topbar_read_model_ref": topbar_read_model.read_model_id,
        "registry_ref": registry.registry_id,
        "operator_context_slot": operator_context_slot,
        "surface_availability_slots": surface_availability_slots,
        "protected_boundary_slots": protected_boundary_slots,
        "attention_status_slots": attention_status_slots,
        "truth_boundary": (
            TopbarStatusProjectionTruthBoundary.PROJECTION_ONLY,
            TopbarStatusProjectionTruthBoundary.READ_MODEL_ONLY,
            TopbarStatusProjectionTruthBoundary.NOT_LIVE_UI,
            TopbarStatusProjectionTruthBoundary.NOT_NOTIFICATION_ENGINE,
            TopbarStatusProjectionTruthBoundary.NOT_RUNTIME_EVENT,
        ),
        "unavailable_bindings": unavailable_bindings,
        "side_effect_proof": side_effects,
        "is_live_ui": False,
        "creates_ui": False,
        "creates_notification_engine": False,
        "emits_runtime_event": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "starts_p2_1_c": False,
        "starts_p2_2": False,
        "next_pack": P2_1_B_NEXT_PACK,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = TopbarStatusProjection(**payload, projection_hash=_hash_payload(payload))
    assert_status_projection_is_not_live_ui(projection)
    assert_status_projection_does_not_create_notification_engine(projection)
    assert_status_projection_does_not_mutate_runtime(projection)
    assert_p2_1_b_does_not_start_p2_1_c(projection)
    assert_p2_1_b_does_not_start_p2_2(projection)
    return projection


def _checkpoint_reads() -> tuple[P21CheckpointRead, ...]:
    rows = {
        "P2.1.6": (
            "Topbar Operator Context Slot Contract",
            "TopbarOperatorContextSlot, build_topbar_operator_context_slot()",
            "test_operator_context_slot_*",
            "CONTRACT_ONLY / READ_MODEL_ONLY / NOT_AUTHORITY",
        ),
        "P2.1.7": (
            "Surface Availability Status Slot Contract",
            "TopbarSurfaceAvailabilitySlot, build_surface_availability_slots()",
            "test_surface_availability_*",
            "CONTRACT_AVAILABLE / NOT_LIVE / READ_MODEL_ONLY",
        ),
        "P2.1.8": (
            "Protected Boundary / SYSTEM Guard Slot Contract",
            "TopbarProtectedBoundarySlot, build_protected_boundary_slots()",
            "test_protected_boundary_*",
            "PROTECTED_BOUNDARY_DISPLAY_ONLY / NOT_ENFORCEMENT",
        ),
        "P2.1.9": (
            "Topbar Attention / Status Indicator Contract",
            "TopbarAttentionStatusSlot, build_topbar_attention_status_slots()",
            "test_attention_status_*",
            "STATUS_INDICATOR_ONLY / NOT_RUNTIME_EVENT",
        ),
        "P2.1.10": (
            "Topbar Status Projection / Readiness Result",
            "TopbarStatusProjection, P21BTopbarStatusSlotsPackResult",
            "test_status_projection_*",
            "PROJECTION_ONLY / READ_MODEL_ONLY / NOT_LIVE_UI",
        ),
    }
    return tuple(
        P21CheckpointRead(
            checkpoint_id=checkpoint_id,
            canonical_name=rows[checkpoint_id][0],
            status=P21CheckpointStatus.DONE,
            evidence=rows[checkpoint_id][1],
            tests=rows[checkpoint_id][2],
            truth_label=rows[checkpoint_id][3],
            unavailable_reason="n/a - contract/read-model status slot only",
            limitations="No UI, runtime, notification engine, authority, P2.1-C, or P2.2",
        )
        for checkpoint_id in P2_1_B_PACK_CHECKPOINT_IDS
    )


def build_p2_1_b_topbar_status_slots_result() -> P21BTopbarStatusSlotsPackResult:
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    projection = build_topbar_status_projection(
        registry=registry,
        topbar_read_model=read_model,
    )
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        checkpoint.checkpoint_id: checkpoint.status.value
        for checkpoint in checkpoint_reads
    }
    side_effects = build_p2_1_b_side_effect_proof()
    payload = {
        "schema_version": P2_1_B_PACK_RESULT_VERSION,
        "pack_id": P2_1_B_PACK_ID,
        "section_id": P2_1_SECTION_ID,
        "section_name": P2_1_SECTION_NAME,
        "covered_checkpoints": P2_1_B_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_1_B_DEPENDENCY_PACKS,
        "depends_on_pack": P2_1_A_PACK_ID,
        "depends_on_report": P2_1_A_REPORT_FILENAME,
        "topbar_read_model_ref": read_model.read_model_id,
        "registry_ref": registry.registry_id,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "projection": projection,
        "side_effect_proof": side_effects,
        "truth_labels": (
            TopbarStatusProjectionTruthBoundary.PROJECTION_ONLY.value,
            TopbarStatusProjectionTruthBoundary.READ_MODEL_ONLY.value,
            TopbarStatusProjectionTruthBoundary.NOT_LIVE_UI.value,
            TopbarSurfaceAvailabilityTruthBoundary.NOT_LIVE.value,
            TopbarOperatorContextTruthBoundary.NOT_AUTHORITY.value,
            TopbarProtectedBoundaryTruthBoundary.NOT_ENFORCEMENT.value,
            TopbarAttentionTruthBoundary.NOT_RUNTIME_EVENT.value,
        ),
        "next_pack": P2_1_B_NEXT_PACK,
    }
    return P21BTopbarStatusSlotsPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_p2_1_b_result(result: P21BTopbarStatusSlotsPackResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_1_b_depends_on_p2_1_a(result: P21BTopbarStatusSlotsPackResult) -> None:
    if result.depends_on_pack != P2_1_A_PACK_ID:
        _reject(
            "P2.1-B must depend on P2.1-A",
            field="depends_on_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_topbar_status_extends_p2_1_a_read_model(
    read_model: TopbarReadModel,
    registry: SurfaceRegistry,
) -> None:
    if read_model.created_for_pack != P2_1_A_PACK_ID:
        _reject(
            "status projection must extend P2.1-A read model",
            field="topbar_read_model_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    visible_ids = tuple(entry.surface_id for entry in read_model.visible_surfaces)
    if visible_ids != registry.topbar_visible_surface_ids:
        _reject(
            "status projection must reuse P2.1-A visible surface ordering",
            field="topbar_read_model_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_operator_context_is_not_authority(slot: TopbarOperatorContextSlot) -> None:
    if slot.is_authority_grant or slot.authority_granted:
        _reject(
            "operator context slot must not grant authority",
            field="authority_granted",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_operator_context_does_not_authenticate(slot: TopbarOperatorContextSlot) -> None:
    if slot.is_authenticated_context or slot.auth_session_created or slot.identity_mutated:
        _reject(
            "operator context slot must not authenticate or mutate identity",
            field="is_authenticated_context",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_availability_is_not_live(slot: TopbarSurfaceAvailabilitySlot) -> None:
    if slot.is_live:
        _reject(
            "topbar availability slot must not claim LIVE",
            field="is_live",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if slot.requires_runtime_probe or slot.runtime_probe_performed:
        _reject(
            "topbar availability slot must not perform runtime probe",
            field="runtime_probe_performed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_unavailable_state_has_reason(slot: TopbarSurfaceAvailabilitySlot) -> None:
    if slot.is_unavailable and not slot.unavailable_reason:
        _reject(
            "unavailable availability slot requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_system_guard_is_display_not_enforcement(
    slot: TopbarProtectedBoundarySlot,
) -> None:
    if slot.enforces_security or slot.grants_access or slot.custos_called or slot.policy_enforced:
        _reject(
            "protected boundary slot is display-only, not enforcement",
            field="enforces_security",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if slot.surface_id == "system" and (slot.agent_access_allowed or not slot.operator_only):
        _reject(
            "SYSTEM must remain operator-only and agent-blocked",
            field="agent_access_allowed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_settings_remains_non_root(slot: TopbarProtectedBoundarySlot) -> None:
    if slot.surface_id != "settings" or not slot.is_settings_non_root or slot.is_system_root:
        _reject(
            "Settings must remain non-root configuration",
            field="is_settings_non_root",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_attention_is_not_runtime_event(slot: TopbarAttentionStatusSlot) -> None:
    if slot.is_runtime_event:
        _reject(
            "attention slot must not be a runtime event",
            field="is_runtime_event",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_attention_is_not_notification_engine(slot: TopbarAttentionStatusSlot) -> None:
    if slot.is_notification_engine or slot.approval_queue_created or slot.workflow_started:
        _reject(
            "attention slot must not create notifications, approvals, or workflows",
            field="is_notification_engine",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_status_projection_is_not_live_ui(projection: TopbarStatusProjection) -> None:
    if projection.is_live_ui or projection.creates_ui:
        _reject(
            "topbar status projection must not claim live UI",
            field="is_live_ui",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_status_projection_does_not_create_notification_engine(
    projection: TopbarStatusProjection,
) -> None:
    if projection.creates_notification_engine or projection.emits_runtime_event:
        _reject(
            "topbar status projection must not create notification engine or event",
            field="creates_notification_engine",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_status_projection_does_not_mutate_runtime(
    projection: TopbarStatusProjection,
) -> None:
    if projection.mutates_runtime or projection.writes_memory or projection.writes_trace:
        _reject(
            "topbar status projection must not mutate runtime, memory, or trace",
            field="mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_1_b_does_not_start_p2_1_c(projection: TopbarStatusProjection) -> None:
    if projection.starts_p2_1_c:
        _reject(
            "P2.1-B must not start P2.1-C",
            field="starts_p2_1_c",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_1_b_does_not_start_p2_2(projection: TopbarStatusProjection) -> None:
    if projection.starts_p2_2:
        _reject(
            "P2.1-B must not start P2.2",
            field="starts_p2_2",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )

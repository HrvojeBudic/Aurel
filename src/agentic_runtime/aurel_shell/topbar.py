"""AurelShell global topbar / surface registry foundation (P2.1-A / P2.1.0–P2.1.5).

Contract-only topbar read model over the P2.0 seven-surface registry. The global
topbar inspects registered surfaces, active surface state, switch intents, and
protected boundaries without claiming live UI or route execution.

Architectural law:
  - Global topbar reads the Surface Registry.
  - Surface Registry is not source of truth.
  - Topbar read model is not live UI.
  - Surface switch intent is not route execution.
  - No universal left nav; local navigation belongs to P2.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    AurelShellValidationError,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .exit_seal import P20ExitSealDecision
from .navigation_boundary import (
    AurelLogoRouteBinding,
    build_aurel_logo_route_binding,
    build_no_universal_left_nav_contract,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
    AurelSurfaceAgentAccess,
    AurelSurfaceContract,
    AurelSurfaceKind,
    AurelSurfaceRegistry,
    SURFACE_KIND_DISPLAY_NAMES,
    SURFACE_KIND_IDS,
    build_default_surface_registry,
)

P2_1_A_PACK_ID = "P2.1-A"
P2_1_SECTION_ID = "P2.1"
P2_1_SECTION_NAME = "Global Topbar / Surface Registry"
P2_1_A_PACK_NAME = "Global Topbar / Surface Registry Foundation"
P2_1_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.1.0",
    "P2.1.1",
    "P2.1.2",
    "P2.1.3",
    "P2.1.4",
    "P2.1.5",
)
P2_1_A_NEXT_PACK = "P2.1-B"
P2_1_A_DEPENDENCY_PACKS: tuple[str, ...] = (
    "P2.0-A",
    "P2.0-B",
    "P2.0-C",
    "P2.0-D",
    "P2.0-E",
    "P2.0-F",
)
P2_0_F_REPORT_FILENAME = "P2_0_F_PROJECTION_CLI_EXIT_SEAL.md"
P2_0_CONTRACT_SCOPE_SEAL = P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE.value

TOPBAR_REGISTRY_VERSION = "topbar_surface_registry.v1"
TOPBAR_ENTRY_VERSION = "topbar_surface_registry_entry.v1"
TOPBAR_READ_MODEL_VERSION = "topbar_read_model.v1"
P2_1_A_PACK_RESULT_VERSION = "p2_1_a_global_topbar_surface_registry_result.v1"

DEFAULT_ACTIVE_SURFACE_ID = "aurel_cro"
LOGO_ROUTE_SURFACE_ID = "aurel_cro"
SETTINGS_SURFACE_ID = "settings"
SYSTEM_SURFACE_ID = "system"

UI_UNAVAILABLE_REASON = (
    "UNAVAILABLE_UI: global topbar product UI is not implemented in P2.1-A"
)
CLI_LIVE_UNAVAILABLE_REASON = (
    "UNAVAILABLE_CLI_LIVE: live CLI topbar binding is not implemented in P2.1-A"
)
TUI_LIVE_UNAVAILABLE_REASON = (
    "UNAVAILABLE_TUI_LIVE: live TUI topbar binding is not implemented in P2.1-A"
)

_FUTURE_SURFACE_REFS: tuple[str, ...] = tuple(sorted(OLD_SURFACE_TAXONOMY))

_ENTRY_NON_GOALS: tuple[str, ...] = (
    "no_authority_grant",
    "no_route_execution",
    "no_runtime_mutation",
    "no_memory_write",
    "no_trace_write",
    "no_ui_mount",
)

_REGISTRY_NON_GOALS: tuple[str, ...] = (
    "no_source_of_truth",
    "no_route_runtime",
    "no_permission_enforcement",
    "no_second_canonical_surface_list",
)

_TOPBAR_NON_GOALS: tuple[str, ...] = (
    "no_product_ui",
    "no_global_left_nav",
    "no_route_runtime",
    "no_command_palette",
    "no_local_nav_implementation",
    "no_p2_1_b",
    "no_p2_2",
)


class P21CheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class SurfaceRegistryTruthLabel(str, Enum):
    CONTRACT_SCOPE = "CONTRACT_SCOPE"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    REGISTRY_ONLY = "REGISTRY_ONLY"
    NOT_AUTHORITY = "NOT_AUTHORITY"
    NOT_EXECUTION = "NOT_EXECUTION"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    FUTURE_REF_UNAVAILABLE = "FUTURE_REF_UNAVAILABLE"
    TAXONOMY_DRIFT_REPORTED = "TAXONOMY_DRIFT_REPORTED"


class SurfaceRegistryAvailabilityState(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    FUTURE_REF = "FUTURE_REF"


class ActiveSurfaceActivationSource(str, Enum):
    DEFAULT = "default"
    OPERATOR = "operator"
    AGENT = "agent"
    SYSTEM = "system"


class TopbarSurfaceSwitchDisposition(str, Enum):
    PROPOSED = "proposed"
    BLOCKED = "blocked"
    PROTECTED_PROPOSAL = "protected_proposal"


class TopbarSwitchTruthLabel(str, Enum):
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    NOT_PERMISSION = "NOT_PERMISSION"
    NOT_EXECUTION = "NOT_EXECUTION"
    NOT_PROOF = "NOT_PROOF"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    OPERATOR_PROTECTED = "OPERATOR_PROTECTED"


class TopbarReadModelTruthLabel(str, Enum):
    PROJECTION_ONLY = "PROJECTION_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_LIVE_UI = "NOT_LIVE_UI"
    NOT_AUTHORITY = "NOT_AUTHORITY"
    NOT_EXECUTION = "NOT_EXECUTION"
    UNAVAILABLE_CLI_OR_UI = "UNAVAILABLE_CLI_OR_UI_IF_NOT_IMPLEMENTED"


_CHECKPOINT_CANONICAL_NAMES: dict[str, str] = {
    "P2.1.0": "P2.1 Section Intake + P2.0 Handoff Gate",
    "P2.1.1": "Surface Registry Entry Model",
    "P2.1.2": "Canonical Surface Registry Builder",
    "P2.1.3": "Active Surface State Contract",
    "P2.1.4": "Topbar Surface Switch Intent Contract",
    "P2.1.5": "Global Topbar Read Model / Projection Seed",
}


@dataclass(frozen=True)
class P21ASideEffectProof(_CanonicalMixin):
    """P2.1-A side-effect / no-authority proof. Every field is false."""

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
    p2_1_b_started: bool = False
    p2_2_started: bool = False


def build_p2_1_a_side_effect_proof() -> P21ASideEffectProof:
    return P21ASideEffectProof()


@dataclass(frozen=True)
class P21SectionIntake(_CanonicalMixin):
    section_id: str
    section_name: str
    pack_id: str
    pack_name: str
    covered_checkpoints: tuple[str, ...]
    depends_on_pack: str
    depends_on_seal: str
    contract_scope_required: bool
    p2_0_contract_scope_sealed: bool
    production_live_scope_required: bool
    trace_verified_scope_required: bool
    release_scope_required: bool
    truth_label: str
    starts_p2_1: bool
    starts_p2_2: bool
    non_goals: tuple[str, ...]
    intake_hash: str


@dataclass(frozen=True)
class P21AHandoffGate(_CanonicalMixin):
    """P2.1.0 handoff gate — opens P2.1 after P2.0-F contract-scope seal."""

    schema_version: str
    pack_id: str
    depends_on_pack: str
    requires_seal: str
    p2_0_f_report: str
    p2_0_contract_scope_sealed: bool
    production_live_scope_required: bool
    trace_verified_scope_required: bool
    release_scope_required: bool
    starts_p2_1: bool
    starts_p2_2: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfaceRegistryTruthBoundary(_CanonicalMixin):
    is_read_model: bool
    is_source_of_truth: bool
    grants_authority: bool
    executes_route: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str


@dataclass(frozen=True)
class SurfaceRegistryEntry(_CanonicalMixin):
    """P2.1.1 topbar-oriented surface registry entry."""

    schema_version: str
    surface_id: str
    display_name: str
    surface_kind: AurelSurfaceKind
    route: str
    global_topbar_visible: bool
    logo_route_target: bool
    local_navigation_owner: str
    root_protected: bool
    operator_only: bool
    agent_access_allowed: bool
    settings_scope: bool
    source_of_truth_boundary: str
    availability_status: SurfaceRegistryAvailabilityState
    truth_label: SurfaceRegistryTruthLabel
    unavailable_reason: str
    aliases: tuple[str, ...]
    future_refs: tuple[str, ...]
    creates_surface: bool
    grants_authority: bool
    executes_route: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class SurfaceTaxonomyDriftSignal(_CanonicalMixin):
    drift_id: str
    detected: bool
    legacy_terms: tuple[str, ...]
    evolved_terms: tuple[str, ...]
    official_terms: tuple[str, ...]
    handling: str
    activated_as_registry_truth: bool
    unavailable_reason: str
    truth_label: str
    non_goals: tuple[str, ...]
    signal_hash: str


@dataclass(frozen=True)
class SurfaceRegistry(_CanonicalMixin):
    """P2.1.2 topbar surface registry — read model over P2.0 official surfaces."""

    schema_version: str
    registry_id: str
    created_for_pack: str
    canonical_surface_order: tuple[str, ...]
    entries: tuple[SurfaceRegistryEntry, ...]
    official_surface_ids: tuple[str, ...]
    topbar_visible_surface_ids: tuple[str, ...]
    protected_surface_ids: tuple[str, ...]
    settings_surface_id: str
    logo_route_surface_id: str
    future_surface_refs: tuple[str, ...]
    taxonomy_drift_signals: tuple[SurfaceTaxonomyDriftSignal, ...]
    truth_label: SurfaceRegistryTruthLabel
    is_source_of_truth: bool
    is_read_model: bool
    grants_authority: bool
    executes_routes: bool
    mutates_runtime: bool
    non_goals: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class SurfaceRegistryResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    registry: SurfaceRegistry
    p2_0_registry_ref: str
    side_effects: P21ASideEffectProof
    result_hash: str


@dataclass(frozen=True)
class ActiveSurfaceTruthBoundary(_CanonicalMixin):
    is_shell_state: bool
    is_source_of_truth: bool
    authority_granted: bool
    runtime_mutated: bool
    route_executed: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str


@dataclass(frozen=True)
class ActiveSurfaceState(_CanonicalMixin):
    """P2.1.3 shell-level active surface state."""

    schema_version: str
    state_id: str
    active_surface_id: str
    previous_surface_id: str | None
    activation_source: ActiveSurfaceActivationSource
    route: str
    can_switch: bool
    blocked_reason: str
    truth_label: str
    is_shell_state: bool
    is_source_of_truth: bool
    authority_granted: bool
    runtime_mutated: bool
    route_executed: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    state_hash: str


@dataclass(frozen=True)
class TopbarSwitchTruthBoundary(_CanonicalMixin):
    is_proposal: bool
    authority_granted: bool
    permission_granted: bool
    route_executed: bool
    runtime_mutated: bool
    proof_created: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str


@dataclass(frozen=True)
class TopbarSurfaceSwitchIntent(_CanonicalMixin):
    """P2.1.4 proposal-only surface switch intent."""

    schema_version: str
    intent_id: str
    from_surface_id: str
    to_surface_id: str
    requested_by: str
    request_source: str
    disposition: TopbarSurfaceSwitchDisposition
    requires_operator: bool
    blocked_reason: str
    truth_label: str
    is_proposal: bool
    authority_granted: bool
    permission_granted: bool
    route_executed: bool
    runtime_mutated: bool
    proof_created: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    intent_hash: str


@dataclass(frozen=True)
class TopbarVisibleSurfaceEntry(_CanonicalMixin):
    surface_id: str
    display_name: str
    route: str
    global_topbar_visible: bool
    truth_label: str


@dataclass(frozen=True)
class TopbarProtectedSurfaceEntry(_CanonicalMixin):
    surface_id: str
    display_name: str
    operator_only: bool
    agent_access_allowed: bool
    root_protected: bool
    truth_label: str


@dataclass(frozen=True)
class TopbarGlobalNavigationPolicy(_CanonicalMixin):
    global_left_nav_allowed: bool
    logo_route_surface_id: str
    local_navigation_deferred_to: str
    navigation_grants_permission: bool
    executes_routes: bool
    truth_label: str
    non_goals: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True)
class TopbarUnavailableBinding(_CanonicalMixin):
    binding_kind: str
    status: str
    unavailable_reason: str
    truth_label: str


@dataclass(frozen=True)
class TopbarReadModelTruthBoundary(_CanonicalMixin):
    is_read_model: bool
    is_live_ui: bool
    is_source_of_truth: bool
    creates_ui: bool
    creates_global_left_nav: bool
    executes_routes: bool
    grants_authority: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str


@dataclass(frozen=True)
class TopbarReadModel(_CanonicalMixin):
    """P2.1.5 global topbar projection seed."""

    schema_version: str
    read_model_id: str
    created_for_pack: str
    active_surface: ActiveSurfaceState
    visible_surfaces: tuple[TopbarVisibleSurfaceEntry, ...]
    protected_surfaces: tuple[TopbarProtectedSurfaceEntry, ...]
    settings_entry: SurfaceRegistryEntry
    logo_route: AurelLogoRouteBinding
    global_navigation_policy: TopbarGlobalNavigationPolicy
    local_navigation_boundary: str
    taxonomy_drift_signals: tuple[SurfaceTaxonomyDriftSignal, ...]
    truth_boundary: TopbarReadModelTruthBoundary
    unavailable_bindings: tuple[TopbarUnavailableBinding, ...]
    truth_label: str
    is_read_model: bool
    is_live_ui: bool
    is_source_of_truth: bool
    creates_ui: bool
    creates_global_left_nav: bool
    executes_routes: bool
    grants_authority: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    read_model_hash: str


@dataclass(frozen=True)
class P21CheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P21CheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class P21AGlobalTopbarSurfaceRegistryPackResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    p2_0_contract_scope_seal: str
    section_intake: P21SectionIntake
    handoff_gate: P21AHandoffGate
    official_surface_ids: tuple[str, ...]
    topbar_visible_surface_ids: tuple[str, ...]
    protected_surface_ids: tuple[str, ...]
    active_surface_state_summary: dict[str, str]
    switch_intent_summary: dict[str, str]
    topbar_read_model_summary: dict[str, str]
    taxonomy_drift_signals: tuple[SurfaceTaxonomyDriftSignal, ...]
    checkpoint_reads: tuple[P21CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    side_effect_proof: P21ASideEffectProof
    registry: SurfaceRegistry
    active_surface_state: ActiveSurfaceState
    topbar_read_model: TopbarReadModel
    next_pack: str
    result_hash: str


def assert_p2_1_a_depends_on_p2_0_contract_scope_seal(
    handoff_gate: P21AHandoffGate,
) -> None:
    if handoff_gate.requires_seal != P2_0_CONTRACT_SCOPE_SEAL:
        _reject(
            f"expected seal {P2_0_CONTRACT_SCOPE_SEAL!r}, got {handoff_gate.requires_seal!r}",
            field="requires_seal",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not handoff_gate.p2_0_contract_scope_sealed:
        _reject(
            "P2.0 contract scope must be sealed before P2.1-A",
            field="p2_0_contract_scope_sealed",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_registry_preserves_official_p2_0_surfaces(registry: SurfaceRegistry) -> None:
    if registry.official_surface_ids != CANONICAL_SURFACE_ORDER:
        _reject(
            f"official surface ids must match P2.0 lock: {registry.official_surface_ids!r}",
            field="official_surface_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_registry_does_not_activate_future_refs(registry: SurfaceRegistry) -> None:
    active_ids = {entry.surface_id for entry in registry.entries}
    for ref in registry.future_surface_refs:
        normalized = ref.lower().replace("-", "_").replace(" ", "_")
        if normalized in active_ids or ref in active_ids:
            _reject(
                f"future ref activated as registry truth: {ref!r}",
                field="future_surface_refs",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_registry_has_no_duplicate_surface_ids(registry: SurfaceRegistry) -> None:
    ids = [entry.surface_id for entry in registry.entries]
    if len(ids) != len(set(ids)):
        _reject(
            "duplicate surface ids in registry",
            field="entries",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_registry_entry_is_not_authority(entry: SurfaceRegistryEntry) -> None:
    if entry.grants_authority or entry.executes_route or entry.mutates_runtime:
        _reject(
            "registry entry must not grant authority or execute routes",
            field="grants_authority",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if entry.writes_memory or entry.writes_trace:
        _reject(
            "registry entry must not write memory or trace",
            field="writes_memory",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_system_is_operator_only_and_agent_blocked(entry: SurfaceRegistryEntry) -> None:
    if entry.surface_id != SYSTEM_SURFACE_ID:
        _reject("expected SYSTEM entry", field="surface_id", code=AurelShellErrorCode.VALIDATION_ERROR)
    if not entry.operator_only or not entry.root_protected:
        _reject(
            "SYSTEM must be operator-only and root protected",
            field="operator_only",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if entry.agent_access_allowed:
        _reject(
            "SYSTEM must block agent access",
            field="agent_access_allowed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_settings_is_non_root_configuration(entry: SurfaceRegistryEntry) -> None:
    if entry.surface_id != SETTINGS_SURFACE_ID:
        _reject("expected Settings entry", field="surface_id", code=AurelShellErrorCode.VALIDATION_ERROR)
    if not entry.settings_scope or entry.root_protected:
        _reject(
            "Settings must be non-root configuration scope",
            field="settings_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_active_surface_exists_in_registry(
    state: ActiveSurfaceState,
    registry: SurfaceRegistry,
) -> None:
    if state.active_surface_id not in registry.official_surface_ids:
        _reject(
            f"active surface {state.active_surface_id!r} not in registry",
            field="active_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_unknown_active_surface_is_blocked(
    surface_id: str,
    registry: SurfaceRegistry,
) -> None:
    if surface_id in registry.official_surface_ids:
        _reject(
            f"surface {surface_id!r} is known — use build_active_surface_state",
            field="active_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_switch_intent_is_proposal_only(intent: TopbarSurfaceSwitchIntent) -> None:
    if not intent.is_proposal:
        _reject(
            "switch intent must be proposal-only",
            field="is_proposal",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if intent.route_executed or intent.runtime_mutated:
        _reject(
            "switch intent must not execute route or mutate runtime",
            field="route_executed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_switch_intent_does_not_execute_route(intent: TopbarSurfaceSwitchIntent) -> None:
    if intent.route_executed:
        _reject(
            "switch intent must not execute route",
            field="route_executed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_switch_intent_does_not_grant_permission(intent: TopbarSurfaceSwitchIntent) -> None:
    if intent.permission_granted or intent.authority_granted:
        _reject(
            "switch intent must not grant permission or authority",
            field="permission_granted",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_agent_cannot_switch_to_system(intent: TopbarSurfaceSwitchIntent) -> None:
    if (
        intent.to_surface_id == SYSTEM_SURFACE_ID
        and intent.requested_by == "agent"
        and intent.disposition != TopbarSurfaceSwitchDisposition.BLOCKED
    ):
        _reject(
            "agent-originated SYSTEM switch must be blocked",
            field="disposition",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_topbar_read_model_derives_from_registry(
    read_model: TopbarReadModel,
    registry: SurfaceRegistry,
) -> None:
    visible_ids = {entry.surface_id for entry in read_model.visible_surfaces}
    expected_visible = set(registry.topbar_visible_surface_ids)
    if visible_ids != expected_visible:
        _reject(
            f"visible surfaces {visible_ids!r} != registry {expected_visible!r}",
            field="visible_surfaces",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_topbar_does_not_create_global_left_nav(read_model: TopbarReadModel) -> None:
    if read_model.creates_global_left_nav:
        _reject(
            "topbar read model must not create global left nav",
            field="creates_global_left_nav",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if read_model.global_navigation_policy.global_left_nav_allowed:
        _reject(
            "global navigation policy must forbid universal left nav",
            field="global_left_nav_allowed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_local_navigation_is_deferred_to_p2_2(read_model: TopbarReadModel) -> None:
    if read_model.global_navigation_policy.local_navigation_deferred_to != "P2.2":
        _reject(
            "local navigation must be deferred to P2.2",
            field="local_navigation_deferred_to",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_topbar_read_model_is_not_live_ui(read_model: TopbarReadModel) -> None:
    if read_model.is_live_ui or read_model.creates_ui:
        _reject(
            "topbar read model must not claim live UI",
            field="is_live_ui",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def _validate_surface_id(surface_id: str) -> None:
    if surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            f"invalid surface id: {surface_id!r}",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _entry_from_p2_0_contract(contract: AurelSurfaceContract) -> SurfaceRegistryEntry:
    surface_id = contract.surface_id
    kind = contract.surface_kind
    is_system = surface_id == SYSTEM_SURFACE_ID
    is_settings = surface_id == SETTINGS_SURFACE_ID
    is_logo_target = surface_id == LOGO_ROUTE_SURFACE_ID
    agent_allowed = contract.agent_access_boundary != AurelSurfaceAgentAccess.FORBIDDEN
    payload = {
        "schema_version": TOPBAR_ENTRY_VERSION,
        "surface_id": surface_id,
        "display_name": contract.display_name,
        "surface_kind": kind,
        "route": f"/{surface_id}",
        "global_topbar_visible": True,
        "logo_route_target": is_logo_target,
        "local_navigation_owner": f"P2.2:{surface_id}",
        "root_protected": is_system,
        "operator_only": is_system,
        "agent_access_allowed": agent_allowed and not is_system,
        "settings_scope": is_settings,
        "source_of_truth_boundary": "projection_read_model_only_not_source_of_truth",
        "availability_status": SurfaceRegistryAvailabilityState.CONTRACT_ONLY,
        "truth_label": SurfaceRegistryTruthLabel.READ_MODEL_ONLY,
        "unavailable_reason": contract.unavailable_reason,
        "aliases": (),
        "future_refs": (),
        "creates_surface": False,
        "grants_authority": False,
        "executes_route": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": _ENTRY_NON_GOALS,
    }
    entry = SurfaceRegistryEntry(**payload, entry_hash=_hash_payload(payload))
    assert_registry_entry_is_not_authority(entry)
    return entry


def build_surface_registry_entry(
    surface_id: str,
    *,
    p2_0_registry: AurelSurfaceRegistry | None = None,
) -> SurfaceRegistryEntry:
    _validate_surface_id(surface_id)
    if p2_0_registry is None:
        p2_0_registry = build_default_surface_registry()
    for contract in p2_0_registry.surfaces:
        if contract.surface_id == surface_id:
            return _entry_from_p2_0_contract(contract)
    _reject(
        f"surface {surface_id!r} not found in P2.0 registry",
        field="surface_id",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def build_surface_taxonomy_drift_signal() -> SurfaceTaxonomyDriftSignal:
    detected, details = detect_surface_taxonomy_drift()
    legacy = tuple(sorted(OLD_SURFACE_TAXONOMY))
    payload = {
        "drift_id": "p2_1_a_surface_taxonomy_drift",
        "detected": detected,
        "legacy_terms": legacy,
        "evolved_terms": ("Forum", "Archivium"),
        "official_terms": CANONICAL_SURFACE_ORDER,
        "handling": (
            "Report SURFACE_TAXONOMY_DRIFT; legacy/evolved terms remain future refs "
            "or drift metadata — not active P2.1-A registry truth"
        ),
        "activated_as_registry_truth": False,
        "unavailable_reason": (
            "FUTURE_REF_UNAVAILABLE: legacy taxonomy terms are not active registry entries"
        ),
        "truth_label": (
            SurfaceRegistryTruthLabel.TAXONOMY_DRIFT_REPORTED.value
            if detected
            else SurfaceRegistryTruthLabel.FUTURE_REF_UNAVAILABLE.value
        ),
        "non_goals": ("no_roadmap_rewrite", "no_fake_active_surfaces"),
    }
    if detected and details:
        payload = dict(payload)
        payload["handling"] = f"{payload['handling']}; details: {'; '.join(details[:2])}"
    return SurfaceTaxonomyDriftSignal(**payload, signal_hash=_hash_payload(payload))


def build_default_topbar_surface_registry(
    *,
    p2_0_registry: AurelSurfaceRegistry | None = None,
) -> SurfaceRegistry:
    if p2_0_registry is None:
        p2_0_registry = build_default_surface_registry()
    entries = tuple(_entry_from_p2_0_contract(c) for c in p2_0_registry.surfaces)
    topbar_visible = tuple(e.surface_id for e in entries if e.global_topbar_visible)
    protected = tuple(e.surface_id for e in entries if e.root_protected or e.operator_only)
    drift_signal = build_surface_taxonomy_drift_signal()
    payload = {
        "schema_version": TOPBAR_REGISTRY_VERSION,
        "registry_id": "topbar_surface_registry_default",
        "created_for_pack": P2_1_A_PACK_ID,
        "canonical_surface_order": CANONICAL_SURFACE_ORDER,
        "entries": entries,
        "official_surface_ids": CANONICAL_SURFACE_ORDER,
        "topbar_visible_surface_ids": topbar_visible,
        "protected_surface_ids": protected,
        "settings_surface_id": SETTINGS_SURFACE_ID,
        "logo_route_surface_id": LOGO_ROUTE_SURFACE_ID,
        "future_surface_refs": _FUTURE_SURFACE_REFS,
        "taxonomy_drift_signals": (drift_signal,),
        "truth_label": SurfaceRegistryTruthLabel.CONTRACT_SCOPE,
        "is_source_of_truth": False,
        "is_read_model": True,
        "grants_authority": False,
        "executes_routes": False,
        "mutates_runtime": False,
        "non_goals": _REGISTRY_NON_GOALS,
    }
    registry = SurfaceRegistry(**payload, registry_hash=_hash_payload(payload))
    assert_registry_preserves_official_p2_0_surfaces(registry)
    assert_registry_has_no_duplicate_surface_ids(registry)
    assert_registry_does_not_activate_future_refs(registry)
    return registry


def build_p2_1_section_intake(
    *,
    p2_0_contract_scope_sealed: bool = True,
) -> P21SectionIntake:
    payload = {
        "section_id": P2_1_SECTION_ID,
        "section_name": P2_1_SECTION_NAME,
        "pack_id": P2_1_A_PACK_ID,
        "pack_name": P2_1_A_PACK_NAME,
        "covered_checkpoints": P2_1_A_PACK_CHECKPOINT_IDS,
        "depends_on_pack": "P2.0-F",
        "depends_on_seal": P2_0_CONTRACT_SCOPE_SEAL,
        "contract_scope_required": True,
        "p2_0_contract_scope_sealed": p2_0_contract_scope_sealed,
        "production_live_scope_required": False,
        "trace_verified_scope_required": False,
        "release_scope_required": False,
        "truth_label": SurfaceRegistryTruthLabel.CONTRACT_SCOPE.value,
        "starts_p2_1": True,
        "starts_p2_2": False,
        "non_goals": _TOPBAR_NON_GOALS,
    }
    return P21SectionIntake(**payload, intake_hash=_hash_payload(payload))


def build_p2_1_a_handoff_gate(
    *,
    p2_0_contract_scope_sealed: bool = True,
) -> P21AHandoffGate:
    payload = {
        "schema_version": "p2_1_a_handoff_gate.v1",
        "pack_id": P2_1_A_PACK_ID,
        "depends_on_pack": "P2.0-F",
        "requires_seal": P2_0_CONTRACT_SCOPE_SEAL,
        "p2_0_f_report": P2_0_F_REPORT_FILENAME,
        "p2_0_contract_scope_sealed": p2_0_contract_scope_sealed,
        "production_live_scope_required": False,
        "trace_verified_scope_required": False,
        "release_scope_required": False,
        "starts_p2_1": True,
        "starts_p2_2": False,
        "truth_labels": (
            SurfaceRegistryTruthLabel.CONTRACT_SCOPE.value,
            "REPORT_EVIDENCE",
            "NOT_LIVE",
            "NOT_TRACE_VERIFIED",
        ),
        "non_goals": _TOPBAR_NON_GOALS,
    }
    gate = P21AHandoffGate(**payload, gate_hash=_hash_payload(payload))
    assert_p2_1_a_depends_on_p2_0_contract_scope_seal(gate)
    return gate


def build_active_surface_state(
    active_surface_id: str | None = None,
    *,
    registry: SurfaceRegistry | None = None,
    activation_source: ActiveSurfaceActivationSource = ActiveSurfaceActivationSource.DEFAULT,
    previous_surface_id: str | None = None,
) -> ActiveSurfaceState:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if active_surface_id is None:
        active_surface_id = DEFAULT_ACTIVE_SURFACE_ID
    _validate_surface_id(active_surface_id)
    if active_surface_id not in registry.official_surface_ids:
        _reject(
            f"active surface {active_surface_id!r} not in registry",
            field="active_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    is_system = active_surface_id == SYSTEM_SURFACE_ID
    can_switch = not (
        is_system and activation_source == ActiveSurfaceActivationSource.AGENT
    )
    blocked_reason = ""
    if is_system and activation_source == ActiveSurfaceActivationSource.AGENT:
        blocked_reason = "agent_access_to_system_blocked"
    payload = {
        "schema_version": "active_surface_state.v1",
        "state_id": f"active_surface_{active_surface_id}",
        "active_surface_id": active_surface_id,
        "previous_surface_id": previous_surface_id,
        "activation_source": activation_source,
        "route": f"/{active_surface_id}",
        "can_switch": can_switch,
        "blocked_reason": blocked_reason,
        "truth_label": "SHELL_STATE_ONLY",
        "is_shell_state": True,
        "is_source_of_truth": False,
        "authority_granted": False,
        "runtime_mutated": False,
        "route_executed": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": ("no_persistent_store", "no_route_runtime", "no_live_topbar_ui"),
    }
    return ActiveSurfaceState(**payload, state_hash=_hash_payload(payload))


def propose_topbar_surface_switch(
    from_surface_id: str,
    to_surface_id: str,
    *,
    requested_by: str = "operator",
    request_source: str = "topbar",
    registry: SurfaceRegistry | None = None,
) -> TopbarSurfaceSwitchIntent:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    _validate_surface_id(from_surface_id)
    intent_id = f"switch_{from_surface_id}_to_{to_surface_id}_{requested_by}"
    disposition = TopbarSurfaceSwitchDisposition.PROPOSED
    blocked_reason = ""
    requires_operator = False
    truth_label = TopbarSwitchTruthLabel.PROPOSAL_ONLY.value

    if to_surface_id not in registry.official_surface_ids:
        disposition = TopbarSurfaceSwitchDisposition.BLOCKED
        blocked_reason = f"unknown_target_surface:{to_surface_id}"
        truth_label = TopbarSwitchTruthLabel.NOT_EXECUTION.value
    elif to_surface_id == SYSTEM_SURFACE_ID and requested_by == "agent":
        disposition = TopbarSurfaceSwitchDisposition.BLOCKED
        blocked_reason = "agent_cannot_switch_to_system"
        truth_label = TopbarSwitchTruthLabel.NOT_PERMISSION.value
    elif to_surface_id == SYSTEM_SURFACE_ID and requested_by == "operator":
        disposition = TopbarSurfaceSwitchDisposition.PROTECTED_PROPOSAL
        requires_operator = True
        blocked_reason = "system_switch_protected_not_executed"
        truth_label = TopbarSwitchTruthLabel.OPERATOR_PROTECTED.value

    payload = {
        "schema_version": "topbar_surface_switch_intent.v1",
        "intent_id": intent_id,
        "from_surface_id": from_surface_id,
        "to_surface_id": to_surface_id,
        "requested_by": requested_by,
        "request_source": request_source,
        "disposition": disposition,
        "requires_operator": requires_operator,
        "blocked_reason": blocked_reason,
        "truth_label": truth_label,
        "is_proposal": True,
        "authority_granted": False,
        "permission_granted": False,
        "route_executed": False,
        "runtime_mutated": False,
        "proof_created": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": ("no_route_runtime", "no_permission_engine", "no_navigation_engine"),
    }
    intent = TopbarSurfaceSwitchIntent(**payload, intent_hash=_hash_payload(payload))
    assert_switch_intent_is_proposal_only(intent)
    assert_switch_intent_does_not_grant_permission(intent)
    assert_agent_cannot_switch_to_system(intent)
    return intent


def _build_global_navigation_policy() -> TopbarGlobalNavigationPolicy:
    no_universal = build_no_universal_left_nav_contract()
    payload = {
        "global_left_nav_allowed": no_universal.global_left_nav_allowed,
        "logo_route_surface_id": LOGO_ROUTE_SURFACE_ID,
        "local_navigation_deferred_to": "P2.2",
        "navigation_grants_permission": False,
        "executes_routes": False,
        "truth_label": TopbarReadModelTruthLabel.PROJECTION_ONLY.value,
        "non_goals": ("no_universal_left_nav", "no_route_runtime"),
    }
    return TopbarGlobalNavigationPolicy(**payload, policy_hash=_hash_payload(payload))


def _default_unavailable_bindings() -> tuple[TopbarUnavailableBinding, ...]:
    return (
        TopbarUnavailableBinding(
            binding_kind="ui",
            status="UNAVAILABLE",
            unavailable_reason=UI_UNAVAILABLE_REASON,
            truth_label=TopbarReadModelTruthLabel.UNAVAILABLE_CLI_OR_UI.value,
        ),
        TopbarUnavailableBinding(
            binding_kind="cli_live",
            status="UNAVAILABLE",
            unavailable_reason=CLI_LIVE_UNAVAILABLE_REASON,
            truth_label=TopbarReadModelTruthLabel.UNAVAILABLE_CLI_OR_UI.value,
        ),
        TopbarUnavailableBinding(
            binding_kind="tui_live",
            status="UNAVAILABLE",
            unavailable_reason=TUI_LIVE_UNAVAILABLE_REASON,
            truth_label=TopbarReadModelTruthLabel.UNAVAILABLE_CLI_OR_UI.value,
        ),
    )


def build_global_topbar_read_model(
    *,
    registry: SurfaceRegistry | None = None,
    active_state: ActiveSurfaceState | None = None,
) -> TopbarReadModel:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if active_state is None:
        active_state = build_active_surface_state(registry=registry)
    assert_active_surface_exists_in_registry(active_state, registry)

    visible = tuple(
        TopbarVisibleSurfaceEntry(
            surface_id=e.surface_id,
            display_name=e.display_name,
            route=e.route,
            global_topbar_visible=e.global_topbar_visible,
            truth_label=SurfaceRegistryTruthLabel.READ_MODEL_ONLY.value,
        )
        for e in registry.entries
        if e.global_topbar_visible
    )
    protected = tuple(
        TopbarProtectedSurfaceEntry(
            surface_id=e.surface_id,
            display_name=e.display_name,
            operator_only=e.operator_only,
            agent_access_allowed=e.agent_access_allowed,
            root_protected=e.root_protected,
            truth_label=(
                "OPERATOR_ONLY_CONTRACT"
                if e.operator_only
                else SurfaceRegistryTruthLabel.READ_MODEL_ONLY.value
            ),
        )
        for e in registry.entries
        if e.root_protected or e.operator_only
    )
    settings_entry = next(
        e for e in registry.entries if e.surface_id == SETTINGS_SURFACE_ID
    )
    logo_route = build_aurel_logo_route_binding()
    nav_policy = _build_global_navigation_policy()
    truth_boundary = TopbarReadModelTruthBoundary(
        is_read_model=True,
        is_live_ui=False,
        is_source_of_truth=False,
        creates_ui=False,
        creates_global_left_nav=False,
        executes_routes=False,
        grants_authority=False,
        mutates_runtime=False,
        writes_memory=False,
        writes_trace=False,
        truth_label=TopbarReadModelTruthLabel.NOT_LIVE_UI.value,
    )
    payload = {
        "schema_version": TOPBAR_READ_MODEL_VERSION,
        "read_model_id": "global_topbar_read_model_default",
        "created_for_pack": P2_1_A_PACK_ID,
        "active_surface": active_state,
        "visible_surfaces": visible,
        "protected_surfaces": protected,
        "settings_entry": settings_entry,
        "logo_route": logo_route,
        "global_navigation_policy": nav_policy,
        "local_navigation_boundary": "deferred_to_p2_2_per_surface_local_nav",
        "taxonomy_drift_signals": registry.taxonomy_drift_signals,
        "truth_boundary": truth_boundary,
        "unavailable_bindings": _default_unavailable_bindings(),
        "truth_label": TopbarReadModelTruthLabel.PROJECTION_ONLY.value,
        "is_read_model": True,
        "is_live_ui": False,
        "is_source_of_truth": False,
        "creates_ui": False,
        "creates_global_left_nav": False,
        "executes_routes": False,
        "grants_authority": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": _TOPBAR_NON_GOALS,
    }
    read_model = TopbarReadModel(**payload, read_model_hash=_hash_payload(payload))
    assert_topbar_read_model_derives_from_registry(read_model, registry)
    assert_topbar_does_not_create_global_left_nav(read_model)
    assert_local_navigation_is_deferred_to_p2_2(read_model)
    assert_topbar_read_model_is_not_live_ui(read_model)
    return read_model


def _default_checkpoint_reads() -> tuple[P21CheckpointRead, ...]:
    evidence_map = {
        "P2.1.0": "P21SectionIntake, P21AHandoffGate",
        "P2.1.1": "SurfaceRegistryEntry, SurfaceRegistryTruthBoundary",
        "P2.1.2": "SurfaceRegistry, build_default_topbar_surface_registry()",
        "P2.1.3": "ActiveSurfaceState, build_active_surface_state()",
        "P2.1.4": "TopbarSurfaceSwitchIntent, propose_topbar_surface_switch()",
        "P2.1.5": "TopbarReadModel, build_global_topbar_read_model()",
    }
    tests_map = {
        "P2.1.0": "test_p2_1_0_section_intake_and_handoff_gate",
        "P2.1.1": "test_p2_1_1_surface_registry_entry_*",
        "P2.1.2": "test_p2_1_2_default_topbar_surface_registry_*",
        "P2.1.3": "test_p2_1_3_active_surface_state_*",
        "P2.1.4": "test_p2_1_4_topbar_switch_intent_*",
        "P2.1.5": "test_p2_1_5_topbar_read_model_*",
    }
    truth_map = {
        "P2.1.0": "CONTRACT_SCOPE / REPORT_EVIDENCE / NOT_LIVE",
        "P2.1.1": "CONTRACT_ONLY / READ_MODEL_ONLY / NOT_AUTHORITY",
        "P2.1.2": "CONTRACT_SCOPE / REGISTRY_ONLY / READ_MODEL_ONLY",
        "P2.1.3": "SHELL_STATE_ONLY / READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH",
        "P2.1.4": "PROPOSAL_ONLY / NOT_PERMISSION / NOT_EXECUTION",
        "P2.1.5": "PROJECTION_ONLY / READ_MODEL_ONLY / NOT_LIVE_UI",
    }
    reads: list[P21CheckpointRead] = []
    for checkpoint_id in P2_1_A_PACK_CHECKPOINT_IDS:
        reads.append(
            P21CheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=_CHECKPOINT_CANONICAL_NAMES[checkpoint_id],
                status=P21CheckpointStatus.DONE,
                evidence=evidence_map[checkpoint_id],
                tests=tests_map[checkpoint_id],
                truth_label=truth_map[checkpoint_id],
                unavailable_reason="n/a — contract/read-model foundation only",
                limitations="No product UI, route runtime, local nav, or P2.1-B+",
            )
        )
    return tuple(reads)


def build_p2_1_a_global_topbar_surface_registry_result() -> (
    P21AGlobalTopbarSurfaceRegistryPackResult
):
    section_intake = build_p2_1_section_intake()
    handoff_gate = build_p2_1_a_handoff_gate()
    registry = build_default_topbar_surface_registry()
    active_state = build_active_surface_state(registry=registry)
    read_model = build_global_topbar_read_model(registry=registry, active_state=active_state)
    sample_intent = propose_topbar_surface_switch("hq", "corp", registry=registry)
    side_effects = build_p2_1_a_side_effect_proof()
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    truth_labels = (
        SurfaceRegistryTruthLabel.CONTRACT_SCOPE.value,
        SurfaceRegistryTruthLabel.READ_MODEL_ONLY.value,
        TopbarReadModelTruthLabel.PROJECTION_ONLY.value,
        TopbarReadModelTruthLabel.NOT_LIVE_UI.value,
        TopbarSwitchTruthLabel.PROPOSAL_ONLY.value,
        "NOT_LIVE",
        "NOT_TRACE_VERIFIED",
    )
    payload: dict[str, Any] = {
        "schema_version": P2_1_A_PACK_RESULT_VERSION,
        "pack_id": P2_1_A_PACK_ID,
        "section_id": P2_1_SECTION_ID,
        "covered_checkpoints": P2_1_A_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_1_A_DEPENDENCY_PACKS,
        "p2_0_contract_scope_seal": P2_0_CONTRACT_SCOPE_SEAL,
        "section_intake": section_intake,
        "handoff_gate": handoff_gate,
        "official_surface_ids": registry.official_surface_ids,
        "topbar_visible_surface_ids": registry.topbar_visible_surface_ids,
        "protected_surface_ids": registry.protected_surface_ids,
        "active_surface_state_summary": {
            "active_surface_id": active_state.active_surface_id,
            "activation_source": active_state.activation_source.value,
            "is_source_of_truth": str(active_state.is_source_of_truth).lower(),
            "route_executed": str(active_state.route_executed).lower(),
        },
        "switch_intent_summary": {
            "disposition": sample_intent.disposition.value,
            "is_proposal": str(sample_intent.is_proposal).lower(),
            "route_executed": str(sample_intent.route_executed).lower(),
        },
        "topbar_read_model_summary": {
            "visible_count": str(len(read_model.visible_surfaces)),
            "protected_count": str(len(read_model.protected_surfaces)),
            "is_live_ui": str(read_model.is_live_ui).lower(),
            "logo_route_surface_id": registry.logo_route_surface_id,
        },
        "taxonomy_drift_signals": registry.taxonomy_drift_signals,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "side_effect_proof": side_effects,
        "registry": registry,
        "active_surface_state": active_state,
        "topbar_read_model": read_model,
        "next_pack": P2_1_A_NEXT_PACK,
    }
    return P21AGlobalTopbarSurfaceRegistryPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_p2_1_a_result(result: P21AGlobalTopbarSurfaceRegistryPackResult) -> str:
    return to_canonical_json(result.to_canonical_dict())

"""P2.4-B command search / ranking / context / result read model foundation.

Contract-only command discovery over the P2.4-A global command registry.
Defines query, match/filter, discovery context, ranking, and result-set read
models without command palette UI, search UI, command execution, routing,
permission enforcement, storage, memory/trace writes, product behavior, release
scope, or runtime mutation.
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
from .global_command_registry import (
    COMMAND_EXECUTION_UNAVAILABLE_REASON,
    P2_4_A_PACK_ID,
    P2_4_A_REPORT_PATH,
    P2_4_A_SECTION_ID,
    GlobalCommandAvailability,
    GlobalCommandAvailabilityStatus,
    GlobalCommandIdentity,
    GlobalCommandKind,
    GlobalCommandRegistry,
    GlobalCommandScope,
    GlobalCommandScopeKind,
    build_global_command_registry,
    build_p2_4_a_global_command_foundation_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    SURFACE_KIND_DISPLAY_NAMES,
    SURFACE_KIND_IDS,
    build_default_surface_registry,
)

P2_4_B_PACK_ID = "P2.4-B"
P2_4_B_SECTION_ID = P2_4_A_SECTION_ID
P2_4_B_OFFICIAL_SECTION_NAME = "Command Palette / Global Commands"
P2_4_B_DEPENDENCY_PACK = P2_4_A_PACK_ID
P2_4_B_NEXT_PACK = "P2.4-C"
P2_4_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.4.6",
    "P2.4.7",
    "P2.4.8",
    "P2.4.9",
    "P2.4.10",
)
P2_4_B_REPORT_FILENAME = "P2_4_B_COMMAND_DISCOVERY_READ_MODEL.md"
P2_4_B_REPORT_PATH = f"agent/reports/{P2_4_B_REPORT_FILENAME}"

P2_4_B_GATE_VERSION = "p2_4_b_command_discovery_gate.v1"
P2_4_B_QUERY_VERSION = "p2_4_b_global_command_query.v1"
P2_4_B_FILTER_VERSION = "p2_4_b_global_command_filter.v1"
P2_4_B_MATCH_VERSION = "p2_4_b_global_command_match.v1"
P2_4_B_CONTEXT_VERSION = "p2_4_b_global_command_discovery_context.v1"
P2_4_B_RANKING_VERSION = "p2_4_b_global_command_ranking.v1"
P2_4_B_RESULT_ITEM_VERSION = "p2_4_b_global_command_result_item.v1"
P2_4_B_RESULT_SET_VERSION = "p2_4_b_global_command_result_set.v1"
P2_4_B_RESULT_VERSION = "p2_4_b_command_discovery_result.v1"

P2_4_A_COMMIT_REF = "f54d626d86cea2451c86e0c53770e3d2a0e5f441"

_QUERY_NON_GOALS: tuple[str, ...] = (
    "no_search_ui",
    "no_live_search_box",
    "no_command_execution",
    "no_command_router",
)
_FILTER_NON_GOALS: tuple[str, ...] = (
    "no_permission_decision",
    "no_permission_grant",
    "no_permission_denial",
    "no_command_execution",
)
_CONTEXT_NON_GOALS: tuple[str, ...] = (
    "no_authority_grant",
    "no_permission_decision",
    "no_surface_runtime_switch",
    "no_route_execution",
)
_RANKING_NON_GOALS: tuple[str, ...] = (
    "no_authorization",
    "no_recommendation_policy",
    "no_execution_decision",
    "no_ml_ranking",
    "no_recommendation_engine",
)
_RESULT_SET_NON_GOALS: tuple[str, ...] = (
    "no_command_palette_ui",
    "no_command_execution",
    "no_runtime_mutation",
    "no_storage_write",
    "no_memory_write",
    "no_trace_write",
)


class GlobalCommandDiscoveryGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class GlobalCommandQueryMode(str, Enum):
    EXACT = "EXACT"
    PREFIX = "PREFIX"
    SUBSTRING = "SUBSTRING"
    TOKEN = "TOKEN"
    EMPTY_QUERY = "EMPTY_QUERY"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandFilterStatus(str, Enum):
    APPLIED = "APPLIED"
    NOT_APPLIED = "NOT_APPLIED"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandMatchReason(str, Enum):
    EXACT_SLUG = "EXACT_SLUG"
    EXACT_LABEL = "EXACT_LABEL"
    PREFIX_SLUG = "PREFIX_SLUG"
    PREFIX_LABEL = "PREFIX_LABEL"
    SUBSTRING_LABEL = "SUBSTRING_LABEL"
    SUBSTRING_DESCRIPTION = "SUBSTRING_DESCRIPTION"
    TOKEN_ALL = "TOKEN_ALL"
    EMPTY_QUERY = "EMPTY_QUERY"
    FILTER_KIND = "FILTER_KIND"
    FILTER_SURFACE = "FILTER_SURFACE"
    FILTER_SCOPE = "FILTER_SCOPE"
    FILTER_AVAILABILITY = "FILTER_AVAILABILITY"
    CONTEXT_SURFACE = "CONTEXT_SURFACE"
    UNAVAILABLE_INCLUDED = "UNAVAILABLE_INCLUDED"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandContextScope(str, Enum):
    GLOBAL = "GLOBAL"
    SURFACE = "SURFACE"
    LOCAL_NAVIGATION = "LOCAL_NAVIGATION"
    WINDOW_STATE = "WINDOW_STATE"
    SYSTEM = "SYSTEM"
    OPERATOR = "OPERATOR"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandRankReason(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    PREFIX_MATCH = "PREFIX_MATCH"
    SUBSTRING_MATCH = "SUBSTRING_MATCH"
    TOKEN_MATCH = "TOKEN_MATCH"
    EMPTY_QUERY_ORDER = "EMPTY_QUERY_ORDER"
    SURFACE_CONTEXT_BOOST = "SURFACE_CONTEXT_BOOST"
    ALPHABETICAL_SLUG = "ALPHABETICAL_SLUG"
    UNAVAILABLE_PRESERVED = "UNAVAILABLE_PRESERVED"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class GlobalCommandResultSetStatus(str, Enum):
    READY = "READY"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandDiscoveryTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_SEARCH_UI = "NOT_SEARCH_UI"
    NOT_COMMAND_PALETTE_UI = "NOT_COMMAND_PALETTE_UI"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_INVOCATION = "NOT_INVOCATION"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    DETERMINISTIC_ORDERING = "DETERMINISTIC_ORDERING"
    NOT_EXECUTION_DECISION = "NOT_EXECUTION_DECISION"
    NOT_RECOMMENDATION_ENGINE = "NOT_RECOMMENDATION_ENGINE"


@dataclass(frozen=True)
class P24BSideEffectProof(_CanonicalMixin):
    command_palette_ui_created: bool = False
    search_ui_created: bool = False
    frontend_ui_created: bool = False
    browser_ui_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    keyboard_listener_created: bool = False
    shortcut_handler_created: bool = False
    fuzzy_search_ui_created: bool = False
    live_search_box_created: bool = False
    ml_ranking_created: bool = False
    recommendation_engine_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    approval_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    surface_runtime_switch_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
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
    p2_4_c_started: bool = False
    p2_5_started: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class GlobalCommandDiscoveryGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_registry_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: GlobalCommandDiscoveryGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class GlobalCommandQuery(_CanonicalMixin):
    query_id: str
    schema_version: str
    query_text: str
    query_mode: GlobalCommandQueryMode
    normalized_query: str
    tokens: tuple[str, ...]
    requested_limit: int
    include_unavailable: bool
    is_ui_query: bool
    executes_command: bool
    truth_label: str
    limitations: tuple[str, ...]
    query_hash: str


@dataclass(frozen=True)
class GlobalCommandFilter(_CanonicalMixin):
    filter_id: str
    schema_version: str
    command_kinds: tuple[GlobalCommandKind, ...]
    surface_targets: tuple[str, ...]
    scope_kinds: tuple[GlobalCommandScopeKind, ...]
    availability_statuses: tuple[GlobalCommandAvailabilityStatus, ...]
    include_unavailable: bool
    filter_status: GlobalCommandFilterStatus
    is_permission_decision: bool
    grants_permission: bool
    denies_permission: bool
    truth_label: str
    limitations: tuple[str, ...]
    filter_hash: str


@dataclass(frozen=True)
class GlobalCommandMatch(_CanonicalMixin):
    match_id: str
    schema_version: str
    command_id: str
    matched_fields: tuple[str, ...]
    match_reasons: tuple[GlobalCommandMatchReason, ...]
    match_score: int
    unavailable_reason: str
    is_execution: bool
    is_invocation: bool
    truth_label: str
    limitations: tuple[str, ...]
    match_hash: str


@dataclass(frozen=True)
class GlobalCommandDiscoveryContext(_CanonicalMixin):
    context_id: str
    schema_version: str
    context_scope: GlobalCommandContextScope
    surface_id: str
    surface_display_name: str
    local_navigation_ref: str
    window_state_ref: str
    uses_official_surface_registry: bool
    is_authority_grant: bool
    is_permission_decision: bool
    switches_surface_runtime: bool
    executes_route: bool
    truth_label: str
    limitations: tuple[str, ...]
    context_hash: str


@dataclass(frozen=True)
class GlobalCommandRanking(_CanonicalMixin):
    ranking_id: str
    schema_version: str
    ranking_strategy: str
    ranked_command_ids: tuple[str, ...]
    rank_reasons: tuple[tuple[str, GlobalCommandRankReason], ...]
    deterministic: bool
    is_authorization: bool
    is_recommendation_policy: bool
    makes_execution_decision: bool
    truth_label: str
    limitations: tuple[str, ...]
    ranking_hash: str


@dataclass(frozen=True)
class GlobalCommandResultItem(_CanonicalMixin):
    result_item_id: str
    schema_version: str
    command_id: str
    label: str
    description: str
    kind: GlobalCommandKind
    scope: GlobalCommandScopeKind
    surface_target: str
    availability_status: GlobalCommandAvailabilityStatus
    unavailable_reason: str
    match_reasons: tuple[GlobalCommandMatchReason, ...]
    rank_reasons: tuple[GlobalCommandRankReason, ...]
    input_contract_ref: str
    is_invocation: bool
    executes_command: bool
    truth_label: str
    limitations: tuple[str, ...]
    result_item_hash: str


@dataclass(frozen=True)
class GlobalCommandResultSet(_CanonicalMixin):
    result_set_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    query: GlobalCommandQuery
    filter: GlobalCommandFilter
    context: GlobalCommandDiscoveryContext
    ranking: GlobalCommandRanking
    items: tuple[GlobalCommandResultItem, ...]
    result_count: int
    result_status: GlobalCommandResultSetStatus
    is_command_palette_ui: bool
    is_source_of_truth: bool
    executes_commands: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    result_set_hash: str


@dataclass(frozen=True)
class P24BCommandDiscoveryResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    discovery_gate: GlobalCommandDiscoveryGate
    query: GlobalCommandQuery
    filter: GlobalCommandFilter
    context: GlobalCommandDiscoveryContext
    ranking: GlobalCommandRanking
    result_set: GlobalCommandResultSet
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P24BSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _normalize_query_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _tokenize(text: str) -> tuple[str, ...]:
    normalized = _normalize_query_text(text)
    if not normalized:
        return ()
    return tuple(normalized.split())


def _infer_query_mode(query_text: str) -> GlobalCommandQueryMode:
    normalized = _normalize_query_text(query_text)
    if not normalized:
        return GlobalCommandQueryMode.EMPTY_QUERY
    if " " in normalized:
        return GlobalCommandQueryMode.TOKEN
    return GlobalCommandQueryMode.PREFIX


def _surface_display_name(surface_id: str) -> str:
    for kind, canonical_id in SURFACE_KIND_IDS.items():
        if canonical_id == surface_id:
            return SURFACE_KIND_DISPLAY_NAMES[kind]
    _reject(
        f"surface id {surface_id!r} is not in the official P2 surface registry",
        field="surface_id",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def build_global_command_discovery_gate() -> GlobalCommandDiscoveryGate:
    p2_4_a = build_p2_4_a_global_command_foundation_result()
    payload = {
        "gate_id": "p2_4_b_command_discovery_gate",
        "schema_version": P2_4_B_GATE_VERSION,
        "section_id": P2_4_B_SECTION_ID,
        "created_for_pack": P2_4_B_PACK_ID,
        "official_section_name": P2_4_B_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_4_B_DEPENDENCY_PACK,
        "dependency_report_ref": P2_4_A_REPORT_PATH,
        "dependency_commit_ref": P2_4_A_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.4-A",
        "dependency_registry_ref": (
            f"{p2_4_a.command_registry.registry_id}:"
            f"{p2_4_a.command_registry.registry_hash}"
        ),
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": GlobalCommandDiscoveryGateStatus.READY,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": (
            "OMNI evidence is ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not execute commands or create search UI",
        ),
    }
    return GlobalCommandDiscoveryGate(**payload, gate_hash=_hash_payload(payload))


def build_global_command_query(
    query_text: str = "",
    *,
    query_mode: GlobalCommandQueryMode | None = None,
    requested_limit: int = 50,
    include_unavailable: bool = True,
) -> GlobalCommandQuery:
    if requested_limit < 1:
        _reject(
            "requested_limit must be positive",
            field="requested_limit",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    mode = query_mode if query_mode is not None else _infer_query_mode(query_text)
    normalized = _normalize_query_text(query_text)
    tokens = _tokenize(query_text)
    payload = {
        "query_id": f"command_query:{mode.value}:{normalized or 'empty'}",
        "schema_version": P2_4_B_QUERY_VERSION,
        "query_text": query_text,
        "query_mode": mode,
        "normalized_query": normalized,
        "tokens": tokens,
        "requested_limit": requested_limit,
        "include_unavailable": include_unavailable,
        "is_ui_query": False,
        "executes_command": False,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.NOT_SEARCH_UI.value,
        "limitations": _QUERY_NON_GOALS,
    }
    query = GlobalCommandQuery(**payload, query_hash=_hash_payload(payload))
    assert_query_is_not_ui(query)
    return query


def build_global_command_filter(
    *,
    command_kinds: tuple[GlobalCommandKind, ...] = (),
    surface_targets: tuple[str, ...] = (),
    scope_kinds: tuple[GlobalCommandScopeKind, ...] = (),
    availability_statuses: tuple[GlobalCommandAvailabilityStatus, ...] = (),
    include_unavailable: bool = True,
) -> GlobalCommandFilter:
    registry = build_default_surface_registry()
    for surface_id in surface_targets:
        if surface_id not in registry.canonical_surface_ids:
            _reject(
                f"surface target {surface_id!r} is not in the official P2 surface registry",
                field="surface_targets",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    has_constraints = any(
        (
            command_kinds,
            surface_targets,
            scope_kinds,
            availability_statuses,
        )
    )
    filter_status = (
        GlobalCommandFilterStatus.APPLIED
        if has_constraints
        else GlobalCommandFilterStatus.NOT_APPLIED
    )
    payload = {
        "filter_id": "command_filter:p2_4_b",
        "schema_version": P2_4_B_FILTER_VERSION,
        "command_kinds": command_kinds,
        "surface_targets": surface_targets,
        "scope_kinds": scope_kinds,
        "availability_statuses": availability_statuses,
        "include_unavailable": include_unavailable,
        "filter_status": filter_status,
        "is_permission_decision": False,
        "grants_permission": False,
        "denies_permission": False,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.NOT_PERMISSION_ENFORCEMENT.value,
        "limitations": _FILTER_NON_GOALS,
    }
    command_filter = GlobalCommandFilter(**payload, filter_hash=_hash_payload(payload))
    assert_filter_is_not_permission(command_filter)
    return command_filter


def build_global_command_discovery_context(
    *,
    context_scope: GlobalCommandContextScope = GlobalCommandContextScope.GLOBAL,
    surface_id: str = "",
    local_navigation_ref: str = "",
    window_state_ref: str = "",
) -> GlobalCommandDiscoveryContext:
    uses_registry = False
    display_name = ""
    if surface_id:
        registry = build_default_surface_registry()
        if surface_id not in registry.canonical_surface_ids:
            _reject(
                f"surface id {surface_id!r} is not in the official P2 surface registry",
                field="surface_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
        uses_registry = True
        display_name = _surface_display_name(surface_id)
    payload = {
        "context_id": f"command_discovery_context:{context_scope.value}:{surface_id or 'global'}",
        "schema_version": P2_4_B_CONTEXT_VERSION,
        "context_scope": context_scope,
        "surface_id": surface_id,
        "surface_display_name": display_name,
        "local_navigation_ref": local_navigation_ref,
        "window_state_ref": window_state_ref,
        "uses_official_surface_registry": uses_registry,
        "is_authority_grant": False,
        "is_permission_decision": False,
        "switches_surface_runtime": False,
        "executes_route": False,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.NOT_AUTHORIZATION.value,
        "limitations": _CONTEXT_NON_GOALS,
    }
    context = GlobalCommandDiscoveryContext(
        **payload,
        context_hash=_hash_payload(payload),
    )
    assert_context_is_not_authority(context)
    return context


def _availability_by_command_id(
    availability_records: tuple[GlobalCommandAvailability, ...],
) -> dict[str, GlobalCommandAvailability]:
    return {record.command_id: record for record in availability_records}


def _scope_by_command_id(
    scope_records: tuple[GlobalCommandScope, ...],
) -> dict[str, GlobalCommandScope]:
    return {record.command_id: record for record in scope_records}


def _query_matches_command(
    command: GlobalCommandIdentity,
    query: GlobalCommandQuery,
) -> tuple[bool, tuple[str, ...], tuple[GlobalCommandMatchReason, ...], int]:
    slug = command.slug.lower()
    label = command.label.lower()
    description = command.description.lower()
    normalized = query.normalized_query

    if query.query_mode == GlobalCommandQueryMode.EMPTY_QUERY:
        return (
            True,
            ("slug",),
            (GlobalCommandMatchReason.EMPTY_QUERY,),
            0,
        )

    if query.query_mode == GlobalCommandQueryMode.EXACT:
        if slug == normalized:
            return True, ("slug",), (GlobalCommandMatchReason.EXACT_SLUG,), 100
        if label == normalized:
            return True, ("label",), (GlobalCommandMatchReason.EXACT_LABEL,), 95
        return False, (), (), 0

    if query.query_mode == GlobalCommandQueryMode.PREFIX:
        if slug.startswith(normalized):
            return True, ("slug",), (GlobalCommandMatchReason.PREFIX_SLUG,), 80
        if label.startswith(normalized):
            return True, ("label",), (GlobalCommandMatchReason.PREFIX_LABEL,), 75
        return False, (), (), 0

    if query.query_mode == GlobalCommandQueryMode.SUBSTRING:
        if normalized in label:
            return (
                True,
                ("label",),
                (GlobalCommandMatchReason.SUBSTRING_LABEL,),
                60,
            )
        if normalized in description:
            return (
                True,
                ("description",),
                (GlobalCommandMatchReason.SUBSTRING_DESCRIPTION,),
                55,
            )
        if normalized in slug:
            return True, ("slug",), (GlobalCommandMatchReason.PREFIX_SLUG,), 50
        return False, (), (), 0

    if query.query_mode == GlobalCommandQueryMode.TOKEN:
        searchable = f"{slug} {label} {description}"
        if all(token in searchable for token in query.tokens):
            return True, ("label", "description", "slug"), (GlobalCommandMatchReason.TOKEN_ALL,), 40
        return False, (), (), 0

    return False, (), (GlobalCommandMatchReason.UNKNOWN_UNAVAILABLE,), 0


def _filter_matches_command(
    command: GlobalCommandIdentity,
    command_filter: GlobalCommandFilter,
    scope: GlobalCommandScope | None,
    availability: GlobalCommandAvailability | None,
) -> tuple[bool, tuple[GlobalCommandMatchReason, ...]]:
    reasons: list[GlobalCommandMatchReason] = []
    if command_filter.command_kinds and command.kind not in command_filter.command_kinds:
        return False, ()
    if command_filter.command_kinds:
        reasons.append(GlobalCommandMatchReason.FILTER_KIND)
    if command_filter.surface_targets:
        if scope is None or scope.surface_id not in command_filter.surface_targets:
            return False, ()
        reasons.append(GlobalCommandMatchReason.FILTER_SURFACE)
    if command_filter.scope_kinds:
        if scope is None or scope.scope_kind not in command_filter.scope_kinds:
            return False, ()
        reasons.append(GlobalCommandMatchReason.FILTER_SCOPE)
    if command_filter.availability_statuses:
        if (
            availability is None
            or availability.availability_status not in command_filter.availability_statuses
        ):
            return False, ()
        reasons.append(GlobalCommandMatchReason.FILTER_AVAILABILITY)
    return True, tuple(reasons)


def match_global_commands(
    registry: GlobalCommandRegistry,
    query: GlobalCommandQuery,
    command_filter: GlobalCommandFilter,
    *,
    availability_records: tuple[GlobalCommandAvailability, ...] | None = None,
    scope_records: tuple[GlobalCommandScope, ...] | None = None,
    context: GlobalCommandDiscoveryContext | None = None,
) -> tuple[GlobalCommandMatch, ...]:
    foundation = build_p2_4_a_global_command_foundation_result()
    if availability_records is None:
        availability_records = foundation.availability_records
    if scope_records is None:
        scope_records = foundation.scope_records
    availability_map = _availability_by_command_id(availability_records)
    scope_map = _scope_by_command_id(scope_records)

    matches: list[GlobalCommandMatch] = []
    for command in registry.commands:
        command_id = command.command_id.command_id
        availability = availability_map.get(command_id)
        scope = scope_map.get(command_id)

        include_unavailable = query.include_unavailable and command_filter.include_unavailable
        if (
            availability is not None
            and availability.availability_status
            == GlobalCommandAvailabilityStatus.UNAVAILABLE_FOR_EXECUTION
            and not include_unavailable
        ):
            continue

        matched, fields, query_reasons, score = _query_matches_command(command, query)
        if not matched:
            continue

        filter_ok, filter_reasons = _filter_matches_command(
            command,
            command_filter,
            scope,
            availability,
        )
        if not filter_ok:
            continue

        reasons = list(query_reasons) + list(filter_reasons)
        if (
            context is not None
            and context.context_scope == GlobalCommandContextScope.SURFACE
            and context.surface_id
            and scope is not None
            and scope.surface_id == context.surface_id
        ):
            reasons.append(GlobalCommandMatchReason.CONTEXT_SURFACE)
            score += 5

        unavailable_reason = ""
        if availability is not None and not availability.available_for_execution:
            unavailable_reason = availability.unavailable_reason
            if include_unavailable:
                reasons.append(GlobalCommandMatchReason.UNAVAILABLE_INCLUDED)

        payload = {
            "match_id": f"command_match:{command_id}:{query.query_hash[:12]}",
            "schema_version": P2_4_B_MATCH_VERSION,
            "command_id": command_id,
            "matched_fields": fields,
            "match_reasons": tuple(reasons),
            "match_score": score,
            "unavailable_reason": unavailable_reason,
            "is_execution": False,
            "is_invocation": False,
            "truth_label": GlobalCommandDiscoveryTruthBoundary.NOT_EXECUTABLE.value,
            "limitations": ("match is not execution", "match is not invocation"),
        }
        match = GlobalCommandMatch(**payload, match_hash=_hash_payload(payload))
        assert_match_is_not_execution(match)
        matches.append(match)

    return tuple(matches)


def rank_global_command_matches(
    matches: tuple[GlobalCommandMatch, ...],
    registry: GlobalCommandRegistry,
    *,
    context: GlobalCommandDiscoveryContext | None = None,
) -> GlobalCommandRanking:
    command_by_id = {
        command.command_id.command_id: command for command in registry.commands
    }
    foundation = build_p2_4_a_global_command_foundation_result()
    scope_map = _scope_by_command_id(foundation.scope_records)

    def sort_key(match: GlobalCommandMatch) -> tuple[int, int, str]:
        context_boost = 0
        if (
            context is not None
            and context.context_scope == GlobalCommandContextScope.SURFACE
            and context.surface_id
        ):
            scope = scope_map.get(match.command_id)
            if scope is not None and scope.surface_id == context.surface_id:
                context_boost = -1
        command = command_by_id.get(match.command_id)
        slug = command.slug if command is not None else match.command_id
        return (-match.match_score, context_boost, slug)

    sorted_matches = sorted(matches, key=sort_key)
    rank_reasons: list[tuple[str, GlobalCommandRankReason]] = []
    ranked_ids: list[str] = []
    for match in sorted_matches:
        ranked_ids.append(match.command_id)
        if GlobalCommandMatchReason.EXACT_SLUG in match.match_reasons:
            rank_reasons.append((match.command_id, GlobalCommandRankReason.EXACT_MATCH))
        elif GlobalCommandMatchReason.EXACT_LABEL in match.match_reasons:
            rank_reasons.append((match.command_id, GlobalCommandRankReason.EXACT_MATCH))
        elif any(
            reason in match.match_reasons
            for reason in (
                GlobalCommandMatchReason.PREFIX_SLUG,
                GlobalCommandMatchReason.PREFIX_LABEL,
            )
        ):
            rank_reasons.append((match.command_id, GlobalCommandRankReason.PREFIX_MATCH))
        elif any(
            reason in match.match_reasons
            for reason in (
                GlobalCommandMatchReason.SUBSTRING_LABEL,
                GlobalCommandMatchReason.SUBSTRING_DESCRIPTION,
            )
        ):
            rank_reasons.append((match.command_id, GlobalCommandRankReason.SUBSTRING_MATCH))
        elif GlobalCommandMatchReason.TOKEN_ALL in match.match_reasons:
            rank_reasons.append((match.command_id, GlobalCommandRankReason.TOKEN_MATCH))
        elif GlobalCommandMatchReason.EMPTY_QUERY in match.match_reasons:
            rank_reasons.append((match.command_id, GlobalCommandRankReason.EMPTY_QUERY_ORDER))
        else:
            rank_reasons.append((match.command_id, GlobalCommandRankReason.ALPHABETICAL_SLUG))
        if GlobalCommandMatchReason.CONTEXT_SURFACE in match.match_reasons:
            rank_reasons.append(
                (match.command_id, GlobalCommandRankReason.SURFACE_CONTEXT_BOOST)
            )
        if match.unavailable_reason:
            rank_reasons.append(
                (match.command_id, GlobalCommandRankReason.UNAVAILABLE_PRESERVED)
            )

    payload = {
        "ranking_id": "command_ranking:p2_4_b_deterministic",
        "schema_version": P2_4_B_RANKING_VERSION,
        "ranking_strategy": "DETERMINISTIC_SCORE_THEN_SLUG",
        "ranked_command_ids": tuple(ranked_ids),
        "rank_reasons": tuple(rank_reasons),
        "deterministic": True,
        "is_authorization": False,
        "is_recommendation_policy": False,
        "makes_execution_decision": False,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.DETERMINISTIC_ORDERING.value,
        "limitations": _RANKING_NON_GOALS,
    }
    ranking = GlobalCommandRanking(**payload, ranking_hash=_hash_payload(payload))
    assert_ranking_is_not_authorization(ranking)
    return ranking


def _build_result_item(
    match: GlobalCommandMatch,
    ranking: GlobalCommandRanking,
    registry: GlobalCommandRegistry,
    availability_records: tuple[GlobalCommandAvailability, ...],
    scope_records: tuple[GlobalCommandScope, ...],
) -> GlobalCommandResultItem:
    command_by_id = {
        command.command_id.command_id: command for command in registry.commands
    }
    availability_map = _availability_by_command_id(availability_records)
    scope_map = _scope_by_command_id(scope_records)

    command = command_by_id[match.command_id]
    availability = availability_map[match.command_id]
    scope = scope_map[match.command_id]

    rank_reasons = tuple(
        reason for command_id, reason in ranking.rank_reasons if command_id == match.command_id
    )

    payload = {
        "result_item_id": f"command_result_item:{match.command_id}",
        "schema_version": P2_4_B_RESULT_ITEM_VERSION,
        "command_id": match.command_id,
        "label": command.label,
        "description": command.description,
        "kind": command.kind,
        "scope": scope.scope_kind,
        "surface_target": scope.surface_id,
        "availability_status": availability.availability_status,
        "unavailable_reason": match.unavailable_reason,
        "match_reasons": match.match_reasons,
        "rank_reasons": rank_reasons,
        "input_contract_ref": f"command_input_contract:{match.command_id}",
        "is_invocation": False,
        "executes_command": False,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.NOT_INVOCATION.value,
        "limitations": ("result item is not invocation", "result item is not execution"),
    }
    item = GlobalCommandResultItem(**payload, result_item_hash=_hash_payload(payload))
    assert_result_item_is_not_invocation(item)
    return item


def build_global_command_result_set(
    query: GlobalCommandQuery | None = None,
    command_filter: GlobalCommandFilter | None = None,
    context: GlobalCommandDiscoveryContext | None = None,
    *,
    registry: GlobalCommandRegistry | None = None,
) -> GlobalCommandResultSet:
    if query is None:
        query = build_global_command_query()
    if command_filter is None:
        command_filter = build_global_command_filter()
    if context is None:
        context = build_global_command_discovery_context()
    if registry is None:
        registry = build_global_command_registry()

    foundation = build_p2_4_a_global_command_foundation_result()
    matches = match_global_commands(
        registry,
        query,
        command_filter,
        availability_records=foundation.availability_records,
        scope_records=foundation.scope_records,
        context=context,
    )
    ranking = rank_global_command_matches(matches, registry, context=context)

    match_by_id = {match.command_id: match for match in matches}
    ordered_matches = tuple(
        match_by_id[command_id]
        for command_id in ranking.ranked_command_ids
        if command_id in match_by_id
    )[: query.requested_limit]

    items = tuple(
        _build_result_item(
            match,
            ranking,
            registry,
            foundation.availability_records,
            foundation.scope_records,
        )
        for match in ordered_matches
    )

    if not items:
        result_status = GlobalCommandResultSetStatus.EMPTY
    elif len(matches) > len(items):
        result_status = GlobalCommandResultSetStatus.PARTIAL
    else:
        result_status = GlobalCommandResultSetStatus.READY

    payload = {
        "result_set_id": "p2_4_b_global_command_result_set",
        "schema_version": P2_4_B_RESULT_SET_VERSION,
        "section_id": P2_4_B_SECTION_ID,
        "created_for_pack": P2_4_B_PACK_ID,
        "official_section_name": P2_4_B_OFFICIAL_SECTION_NAME,
        "query": query,
        "filter": command_filter,
        "context": context,
        "ranking": ranking,
        "items": items,
        "result_count": len(items),
        "result_status": result_status,
        "is_command_palette_ui": False,
        "is_source_of_truth": False,
        "executes_commands": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "writes_storage": False,
        "truth_label": GlobalCommandDiscoveryTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": _RESULT_SET_NON_GOALS,
    }
    result_set = GlobalCommandResultSet(**payload, result_set_hash=_hash_payload(payload))
    assert_result_set_is_not_invocation(result_set)
    return result_set


def build_p2_4_b_side_effect_proof() -> P24BSideEffectProof:
    return P24BSideEffectProof()


def build_p2_4_b_command_discovery_result(
    query_text: str = "",
    *,
    context_surface_id: str = "hq",
) -> P24BCommandDiscoveryResult:
    gate = build_global_command_discovery_gate()
    query = build_global_command_query(query_text)
    command_filter = build_global_command_filter()
    context = build_global_command_discovery_context(
        context_scope=(
            GlobalCommandContextScope.SURFACE
            if context_surface_id
            else GlobalCommandContextScope.GLOBAL
        ),
        surface_id=context_surface_id,
    )
    result_set = build_global_command_result_set(query, command_filter, context)
    side_effects = build_p2_4_b_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_4_B_RESULT_VERSION,
        "pack_id": P2_4_B_PACK_ID,
        "section_id": P2_4_B_SECTION_ID,
        "official_section_name": P2_4_B_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_4_B_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_4_B_DEPENDENCY_PACK,
        "discovery_gate": gate,
        "query": query,
        "filter": command_filter,
        "context": context,
        "ranking": result_set.ranking,
        "result_set": result_set,
        "truth_labels": (
            GlobalCommandDiscoveryTruthBoundary.CONTRACT_ONLY.value,
            GlobalCommandDiscoveryTruthBoundary.READ_MODEL_ONLY.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_SEARCH_UI.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_COMMAND_PALETTE_UI.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_EXECUTABLE.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_INVOCATION.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_AUTHORIZATION.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_PERMISSION_ENFORCEMENT.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_LIVE.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_TRACE_VERIFIED.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_PRODUCT_BEHAVIOR.value,
            GlobalCommandDiscoveryTruthBoundary.NOT_RELEASE_SCOPE.value,
        ),
        "unavailable_reasons": (COMMAND_EXECUTION_UNAVAILABLE_REASON,),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_4_B_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P24BCommandDiscoveryResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_4_b_does_not_start_future_work(result)
    assert_p2_4_b_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_4_b_result(
    result: P24BCommandDiscoveryResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_b_command_discovery_result()
    return to_canonical_json(result.to_canonical_dict())


def render_global_command_result_set_summary(
    result_set: GlobalCommandResultSet | None = None,
) -> str:
    if result_set is None:
        result_set = build_global_command_result_set()
    return "\n".join(
        (
            f"{result_set.section_id} {result_set.official_section_name}",
            f"pack={result_set.created_for_pack}",
            f"result_set={result_set.result_set_id}",
            f"query_mode={result_set.query.query_mode.value}",
            f"result_count={result_set.result_count}",
            f"result_status={result_set.result_status.value}",
            f"is_command_palette_ui={str(result_set.is_command_palette_ui).lower()}",
            f"executes_commands={str(result_set.executes_commands).lower()}",
        )
    )


def assert_query_is_not_ui(query: GlobalCommandQuery) -> None:
    if query.is_ui_query or query.executes_command:
        _reject(
            "P2.4-B query must not be UI or execute commands",
            field="is_ui_query",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_filter_is_not_permission(command_filter: GlobalCommandFilter) -> None:
    if (
        command_filter.is_permission_decision
        or command_filter.grants_permission
        or command_filter.denies_permission
    ):
        _reject(
            "P2.4-B filter must not be permission decision",
            field="is_permission_decision",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_match_is_not_execution(match: GlobalCommandMatch) -> None:
    if match.is_execution or match.is_invocation:
        _reject(
            "P2.4-B match must not be execution or invocation",
            field="is_execution",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_is_not_authority(context: GlobalCommandDiscoveryContext) -> None:
    if (
        context.is_authority_grant
        or context.is_permission_decision
        or context.switches_surface_runtime
        or context.executes_route
    ):
        _reject(
            "P2.4-B context must not grant authority, switch surfaces, or execute routes",
            field="is_authority_grant",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_ranking_is_not_authorization(ranking: GlobalCommandRanking) -> None:
    if (
        ranking.is_authorization
        or ranking.is_recommendation_policy
        or ranking.makes_execution_decision
        or not ranking.deterministic
    ):
        _reject(
            "P2.4-B ranking must be deterministic and not authorize or recommend execution",
            field="is_authorization",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_result_item_is_not_invocation(item: GlobalCommandResultItem) -> None:
    if item.is_invocation or item.executes_command:
        _reject(
            "P2.4-B result item must not invoke or execute commands",
            field="is_invocation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_result_set_is_not_invocation(result_set: GlobalCommandResultSet) -> None:
    if (
        result_set.is_command_palette_ui
        or result_set.is_source_of_truth
        or result_set.executes_commands
        or result_set.mutates_runtime
        or result_set.writes_memory
        or result_set.writes_trace
        or result_set.writes_storage
    ):
        _reject(
            "P2.4-B result set must remain read-model only",
            field="is_command_palette_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_b_does_not_start_future_work(result: P24BCommandDiscoveryResult) -> None:
    if result.starts_future_work or result.next_pack != P2_4_B_NEXT_PACK:
        _reject(
            "P2.4-B result must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_4_c_started,
            proof.p2_5_started,
            proof.p2_6_started,
            proof.p2_7_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.4-B must not start P2.4-C or later packs",
            field="p2_4_c_started",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_b_side_effects_all_false(proof: P24BSideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                f"P2.4-B side-effect field must remain false: {field}",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_p2_4_b_depends_on_p2_4_a(gate: GlobalCommandDiscoveryGate) -> None:
    if gate.dependency_pack != P2_4_A_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.4-B must depend on passed P2.4-A repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: GlobalCommandDiscoveryGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.4-B gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )

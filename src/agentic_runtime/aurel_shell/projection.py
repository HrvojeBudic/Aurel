"""AurelShell projection read model + contract (P2.0-F / P2.0.27).

Projection exposes the P2.0-A/B/C/D/E shell contract stack as a bounded read
model. It does not own truth, mutate runtime, write memory, or write trace.

Architectural law:
  - Projection is not runtime.
  - Projection is a read model; it is not source of truth.
  - API contract is not API server.
  - Event contract is not emitted event stream.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .readiness import build_p2_0_cognitive_os_lock_readiness
from .regression_harness import run_surface_regression_route_contract_harness
from .shell_snapshot import ShellStateSnapshot, build_shell_state_snapshot
from .surface_registry import CANONICAL_SURFACE_ORDER

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids runtime import cycle
    from .api_contract import ShellAPIContract
    from .event_contract import ShellEventContract

P2_0_F_PACK_ID = "P2.0-F"
P2_0_F_SECTION_ID = "P2.0"
P2_0_F_DEPENDENCY_PACKS: tuple[str, ...] = (
    "P2.0-A",
    "P2.0-B",
    "P2.0-C",
    "P2.0-D",
    "P2.0-E",
)
P2_0_F_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.0.27",
    "P2.0.28",
    "P2.0.29",
    "P2.0.30",
)
P2_0_F_NEXT_STEP = "OMNI review of P2.0 exit seal and P2.1 readiness boundary"

SHELL_PROJECTION_READ_MODEL_VERSION = "aurel_shell_projection_read_model.v1"
SHELL_PROJECTION_PAYLOAD_VERSION = "aurel_shell_projection_payload.v1"
SHELL_PROJECTION_CONTRACT_VERSION = "aurel_shell_projection_contract.v1"

SHELL_PROJECTION_ID = "p2_0_f_shell_projection"

API_RUNTIME_UNAVAILABLE_REASON = (
    "UNAVAILABLE_API_RUNTIME: HTTP API server is not implemented in P2.0-F; "
    "contract-only payload envelope"
)
EVENT_RUNTIME_UNAVAILABLE_REASON = (
    "UNAVAILABLE_EVENT_RUNTIME: event bus dispatch is not implemented in "
    "P2.0-F; contract-only payload shape; no runtime event is emitted"
)


class P20FTruthLabel(str, Enum):
    """Truth labels for the P2.0-F contract tail."""

    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    API_CONTRACT_ONLY = "API_CONTRACT_ONLY"
    EVENT_CONTRACT_ONLY = "EVENT_CONTRACT_ONLY"
    CLI_INSPECT_CONTRACT_ONLY = "CLI_INSPECT_CONTRACT_ONLY"
    TUI_UNAVAILABLE = "TUI_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    DOCS_SYNC_ONLY = "DOCS_SYNC_ONLY"
    REPORT_EVIDENCE = "REPORT_EVIDENCE"
    READINESS_REVIEW_ONLY = "READINESS_REVIEW_ONLY"
    P2_CONTRACT_SCOPE = "P2_CONTRACT_SCOPE"
    SEALED_FOR_P2_CONTRACT_SCOPE = "SEALED_FOR_P2_CONTRACT_SCOPE"
    READY_FOR_P2_1_REVIEW = "READY_FOR_P2_1_REVIEW"
    NOT_READY_FOR_P2_1 = "NOT_READY_FOR_P2_1"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_SEALED = "NOT_SEALED"


# Stronger operational labels that P2.0-F must never claim by default.
FORBIDDEN_P2_0_F_TRUTH_LABELS: frozenset[str] = frozenset(
    {
        "LIVE",
        "TRACE_VERIFIED",
        "API_SERVER_LIVE",
        "HTTP_ROUTE_CREATED",
        "EVENT_EMITTED",
        "EVENT_BUS_CREATED",
        "CLI_PRODUCT_LIVE",
        "TUI_PRODUCT_LIVE",
        "PRODUCTION_LIVE_SEALED",
        "TRACE_VERIFIED_SEALED",
        "RELEASE_SEALED",
        "P2_1_STARTED",
        "P2_1_AUTHORIZED_FOR_CODING",
        "MEMORY_WRITTEN",
        "TRACE_WRITTEN",
        "RUNTIME_MUTATED",
        "PERMISSION_GRANTED",
    }
)


class ShellProjectionStatus(str, Enum):
    """Projection layer status — read model only, not execution."""

    PROJECTION_ONLY = "PROJECTION_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_runtime",
    "no_source_of_truth_store",
    "no_runtime_mutation",
    "no_memory_write",
    "no_trace_write",
    "no_api_server",
    "no_http_routes",
    "no_event_bus",
    "no_emitted_runtime_events",
)


@dataclass(frozen=True)
class P20FSideEffectProof(_CanonicalMixin):
    """P2.0-F side-effect / no-authority proof. Every field is false."""

    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    ui_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    live_cli_product_created: bool = False
    live_tui_product_created: bool = False
    shell_runtime_mutated: bool = False
    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    trace_verification_created: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    p2_1_started: bool = False


def all_false_p2_0_f_side_effects() -> P20FSideEffectProof:
    return P20FSideEffectProof()


@dataclass(frozen=True)
class ShellProjectionTruthBoundary(_CanonicalMixin):
    """Truth boundary for the shell projection read model."""

    is_read_model: bool
    is_source_of_truth: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    live_not_claimed: bool
    trace_verified_not_claimed: bool
    truth_label: str


@dataclass(frozen=True)
class ShellProjectionReadModel(_CanonicalMixin):
    """Bounded read model over P2.0-A/B/C/D/E contract evidence."""

    schema_version: str
    projection_id: str
    projection_version: str
    source_snapshot_ref: str
    surface_registry_summary: dict[str, str]
    navigation_boundary_summary: dict[str, str]
    continuity_summary: dict[str, str]
    truth_label_summary: dict[str, str]
    permission_matrix_summary: dict[str, str]
    unavailable_state_summary: dict[str, str]
    fixture_disclosure_summary: dict[str, str]
    operator_demo_summary: dict[str, str]
    client_consistency_summary: dict[str, str]
    regression_harness_summary: dict[str, str]
    readiness_summary: dict[str, str]
    canonical_surface_ids: tuple[str, ...]
    truth_label: str
    is_read_model: bool
    is_source_of_truth: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    read_model_hash: str


@dataclass(frozen=True)
class ShellProjectionPayload(_CanonicalMixin):
    """Projection payload — read model plus projection metadata."""

    schema_version: str
    projection_id: str
    projection_version: str
    source_snapshot_ref: str
    read_model: ShellProjectionReadModel
    truth_boundary: ShellProjectionTruthBoundary
    projection_status: ShellProjectionStatus
    truth_label: str
    is_read_model: bool
    is_source_of_truth: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    projection_payload_hash: str


@dataclass(frozen=True)
class ShellProjectionContract(_CanonicalMixin):
    """Projection/API/event contract bundle for P2.0.27."""

    schema_version: str
    projection_payload: ShellProjectionPayload
    api_contract: "ShellAPIContract"
    event_contract: "ShellEventContract"
    projection_status: ShellProjectionStatus
    truth_labels: tuple[str, ...]
    truth_label: str
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    contract_hash: str


def _regression_summary(result: Any) -> dict[str, str]:
    return {
        "passed": str(result.passed).lower(),
        "case_count": str(len(result.case_results)),
        "failed_case_count": str(result.failed_case_count),
        "creates_route_runtime": "false",
        "runs_frontend": "false",
        "runs_browser": "false",
        "result_hash": result.result_hash,
    }


def _readiness_summary(readiness: Any) -> dict[str, str]:
    return {
        "decision": readiness.readiness_decision.value,
        "blocker_count": str(len(readiness.blockers)),
        "is_exit_seal": "false",
        "is_live_claim": "false",
        "starts_next_pack": "false",
        "authorizes_p2_1": "false",
        "readiness_hash": readiness.readiness_hash,
    }


def _build_complete_shell_snapshot() -> ShellStateSnapshot:
    """Build a snapshot whose regression/readiness summaries are populated."""
    regression = run_surface_regression_route_contract_harness()
    readiness = build_p2_0_cognitive_os_lock_readiness()
    return build_shell_state_snapshot(
        regression_harness_summary=_regression_summary(regression),
        readiness_summary=_readiness_summary(readiness),
    )


def build_shell_projection_read_model(
    snapshot: ShellStateSnapshot | None = None,
) -> ShellProjectionReadModel:
    """Build the read-model projection over the shell state snapshot."""
    resolved = snapshot or _build_complete_shell_snapshot()
    payload = {
        "schema_version": SHELL_PROJECTION_READ_MODEL_VERSION,
        "projection_id": SHELL_PROJECTION_ID,
        "projection_version": "v1",
        "source_snapshot_ref": resolved.snapshot_hash,
        "surface_registry_summary": resolved.surface_registry_summary,
        "navigation_boundary_summary": resolved.navigation_boundary_summary,
        "continuity_summary": resolved.continuity_summary,
        "truth_label_summary": resolved.truth_label_summary,
        "permission_matrix_summary": resolved.permission_matrix_summary,
        "unavailable_state_summary": resolved.unavailable_state_summary,
        "fixture_disclosure_summary": resolved.fixture_disclosure_summary,
        "operator_demo_summary": resolved.operator_demo_summary,
        "client_consistency_summary": resolved.client_consistency_summary,
        "regression_harness_summary": resolved.regression_harness_summary,
        "readiness_summary": resolved.readiness_summary,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "truth_label": P20FTruthLabel.READ_MODEL_ONLY.value,
        "is_read_model": True,
        "is_source_of_truth": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
    }
    return ShellProjectionReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )


def build_shell_projection_payload(
    snapshot: ShellStateSnapshot | None = None,
) -> ShellProjectionPayload:
    """Build the projection payload around the read model."""
    read_model = build_shell_projection_read_model(snapshot)
    truth_boundary = ShellProjectionTruthBoundary(
        is_read_model=True,
        is_source_of_truth=False,
        mutates_runtime=False,
        writes_memory=False,
        writes_trace=False,
        live_not_claimed=True,
        trace_verified_not_claimed=True,
        truth_label=P20FTruthLabel.PROJECTION_ONLY.value,
    )
    side_effects = all_false_p2_0_f_side_effects()
    payload = {
        "schema_version": SHELL_PROJECTION_PAYLOAD_VERSION,
        "projection_id": SHELL_PROJECTION_ID,
        "projection_version": "v1",
        "source_snapshot_ref": read_model.source_snapshot_ref,
        "read_model": read_model,
        "truth_boundary": truth_boundary,
        "projection_status": ShellProjectionStatus.PROJECTION_ONLY,
        "truth_label": P20FTruthLabel.PROJECTION_ONLY.value,
        "is_read_model": True,
        "is_source_of_truth": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": _PROJECTION_NON_GOALS,
        "side_effects": side_effects,
    }
    projection_payload = ShellProjectionPayload(
        **payload,
        projection_payload_hash=_hash_payload(payload),
    )
    assert_projection_is_read_model_only(projection_payload)
    assert_projection_is_not_source_of_truth(projection_payload)
    assert_projection_does_not_mutate_runtime(projection_payload)
    return projection_payload


def build_shell_projection_contract(
    snapshot: ShellStateSnapshot | None = None,
) -> ShellProjectionContract:
    """Bundle projection payload + API contract + event contract (P2.0.27)."""
    # Lazy imports keep the API/event contract modules importing this module
    # without a runtime cycle.
    from .api_contract import build_shell_api_contract
    from .event_contract import build_shell_event_contract

    projection_payload = build_shell_projection_payload(snapshot)
    api_contract = build_shell_api_contract(
        projection_ref=projection_payload.projection_payload_hash,
    )
    event_contract = build_shell_event_contract(
        projection_ref=projection_payload.projection_payload_hash,
    )
    side_effects = all_false_p2_0_f_side_effects()
    truth_labels = (
        P20FTruthLabel.PROJECTION_ONLY.value,
        P20FTruthLabel.READ_MODEL_ONLY.value,
        P20FTruthLabel.API_CONTRACT_ONLY.value,
        P20FTruthLabel.EVENT_CONTRACT_ONLY.value,
        P20FTruthLabel.NOT_LIVE.value,
        P20FTruthLabel.NOT_TRACE_VERIFIED.value,
    )
    payload = {
        "schema_version": SHELL_PROJECTION_CONTRACT_VERSION,
        "projection_payload": projection_payload,
        "api_contract": api_contract,
        "event_contract": event_contract,
        "projection_status": ShellProjectionStatus.PROJECTION_ONLY,
        "truth_labels": truth_labels,
        "truth_label": P20FTruthLabel.PROJECTION_ONLY.value,
        "non_goals": _PROJECTION_NON_GOALS,
        "side_effects": side_effects,
    }
    return ShellProjectionContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def serialize_shell_projection_payload(
    payload: ShellProjectionPayload | ShellProjectionReadModel | ShellProjectionContract,
) -> str:
    return to_canonical_json(payload.to_canonical_dict())


def assert_projection_is_read_model_only(payload: ShellProjectionPayload) -> None:
    if not payload.is_read_model or not payload.read_model.is_read_model:
        _reject(
            "shell projection must be a read model only",
            field="is_read_model",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_projection_is_not_source_of_truth(payload: ShellProjectionPayload) -> None:
    if payload.is_source_of_truth or payload.read_model.is_source_of_truth:
        _reject(
            "shell projection must not be source of truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_projection_does_not_mutate_runtime(payload: ShellProjectionPayload) -> None:
    if payload.mutates_runtime or payload.writes_memory or payload.writes_trace:
        _reject(
            "shell projection must not mutate runtime, write memory, or write trace",
            field="mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )

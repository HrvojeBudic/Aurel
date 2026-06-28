"""P2.0-E shell state snapshot contract.

The snapshot is a bounded read model over A/B/C/D/E contract evidence. It is
serializable and inspectable, but it is not source of truth and mutates nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from .client_consistency import (
    MultiClientConsistencyContract,
    build_multi_client_consistency_contract,
)
from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .continuity_read_model import build_p2_0_c_floating_window_handoff_context_result
from .navigation_read_model import build_p2_0_b_navigation_boundary_pack_result
from .operator_demo import (
    OperatorTestableSurfaceDemoState,
    build_operator_testable_surface_demo_state,
)
from .read_model import (
    build_p2_0_a_shell_foundation_surface_registry_result,
)
from .surface_registry import AurelSurfaceRegistry, build_default_surface_registry
from .truth_permission_fixture_read_model import (
    build_p2_0_d_truth_permission_fixture_result,
)

SHELL_STATE_SNAPSHOT_CONTRACT_VERSION = "shell_state_snapshot_contract.v1"
SHELL_STATE_SNAPSHOT_VERSION = "shell_state_snapshot.v1"
SHELL_STATE_SNAPSHOT_ID = "p2_0_e_shell_state_snapshot"

_SNAPSHOT_NON_GOALS: tuple[str, ...] = (
    "no_source_of_truth_store",
    "no_runtime_state_mutation",
    "no_memory_write",
    "no_trace_write",
    "no_live_shell_state",
)


@dataclass(frozen=True)
class ShellStateSnapshotTruthBoundary(_CanonicalMixin):
    """Truth boundary for shell snapshots."""

    carries_truth_labels: bool
    snapshot_truth_label_is_not_proof: bool
    live_not_claimed: bool
    trace_verified_not_claimed: bool
    truth_label: str


@dataclass(frozen=True)
class ShellStateSnapshotSourceBoundary(_CanonicalMixin):
    """Source boundary for shell snapshots."""

    is_read_model: bool
    is_source_of_truth: bool
    owns_truth: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool


@dataclass(frozen=True)
class ShellStateSnapshotContract(_CanonicalMixin):
    """P2.0.24 snapshot contract."""

    schema_version: str
    snapshot_serializes: bool
    snapshot_is_read_model: bool
    snapshot_is_not_source_of_truth: bool
    snapshot_does_not_mutate_runtime: bool
    snapshot_carries_truth_labels: bool
    truth_boundary: ShellStateSnapshotTruthBoundary
    source_boundary: ShellStateSnapshotSourceBoundary
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class ShellStateSnapshot(_CanonicalMixin):
    """Serializable shell state read model over P2.0-A/B/C/D/E contracts."""

    schema_version: str
    snapshot_id: str
    created_for_pack: str
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
    truth_label: str
    is_read_model: bool
    is_source_of_truth: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    carries_truth_labels: bool
    contract: ShellStateSnapshotContract
    non_goals: tuple[str, ...]
    snapshot_hash: str


def build_shell_state_snapshot_contract() -> ShellStateSnapshotContract:
    truth_boundary = ShellStateSnapshotTruthBoundary(
        carries_truth_labels=True,
        snapshot_truth_label_is_not_proof=True,
        live_not_claimed=True,
        trace_verified_not_claimed=True,
        truth_label="SHELL_SNAPSHOT_CONTRACT_ONLY",
    )
    source_boundary = ShellStateSnapshotSourceBoundary(
        is_read_model=True,
        is_source_of_truth=False,
        owns_truth=False,
        mutates_runtime=False,
        writes_memory=False,
        writes_trace=False,
    )
    payload = {
        "schema_version": SHELL_STATE_SNAPSHOT_CONTRACT_VERSION,
        "snapshot_serializes": True,
        "snapshot_is_read_model": True,
        "snapshot_is_not_source_of_truth": True,
        "snapshot_does_not_mutate_runtime": True,
        "snapshot_carries_truth_labels": True,
        "truth_boundary": truth_boundary,
        "source_boundary": source_boundary,
        "truth_label": "SHELL_SNAPSHOT_CONTRACT_ONLY",
        "non_goals": _SNAPSHOT_NON_GOALS,
    }
    return ShellStateSnapshotContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def _surface_registry_summary(registry: AurelSurfaceRegistry) -> dict[str, str]:
    return {
        "surface_count": str(registry.surface_count),
        "canonical_surface_ids": ",".join(registry.canonical_surface_ids),
        "registry_hash": registry.registry_hash,
        "truth_label": "SURFACE_CONTRACT_ONLY",
    }


def _operator_demo_summary(
    demo_state: OperatorTestableSurfaceDemoState,
) -> dict[str, str]:
    return {
        "demo_id": demo_state.demo_id,
        "surface_count": str(demo_state.surface_count),
        "operator_testable": str(demo_state.demo_state_is_operator_testable).lower(),
        "dev_fixture": str(demo_state.demo_state_is_dev_fixture).lower(),
        "live": "false",
        "state_hash": demo_state.state_hash,
    }


def _client_consistency_summary(
    contract: MultiClientConsistencyContract,
) -> dict[str, str]:
    return {
        "client_kinds": ",".join(kind.value for kind in contract.client_kinds),
        "same_surface_registry": "true",
        "same_truth_labels": "true",
        "same_permission_meanings": "true",
        "same_unavailable_states": "true",
        "same_fixture_disclosures": "true",
        "creates_clients": "false",
        "contract_hash": contract.contract_hash,
    }


def build_shell_state_snapshot(
    *,
    regression_harness_summary: dict[str, str] | None = None,
    readiness_summary: dict[str, str] | None = None,
) -> ShellStateSnapshot:
    registry = build_default_surface_registry()
    p2_0_a = build_p2_0_a_shell_foundation_surface_registry_result()
    p2_0_b = build_p2_0_b_navigation_boundary_pack_result()
    p2_0_c = build_p2_0_c_floating_window_handoff_context_result()
    p2_0_d = build_p2_0_d_truth_permission_fixture_result()
    operator_demo = build_operator_testable_surface_demo_state(registry)
    client_contract = build_multi_client_consistency_contract(registry)
    contract = build_shell_state_snapshot_contract()
    payload = {
        "schema_version": SHELL_STATE_SNAPSHOT_VERSION,
        "snapshot_id": SHELL_STATE_SNAPSHOT_ID,
        "created_for_pack": "P2.0-E",
        "surface_registry_summary": _surface_registry_summary(registry),
        "navigation_boundary_summary": {
            "no_universal_left_nav": "true",
            "logo_routes_to": p2_0_b.logo_route_binding.target.surface_id,
            "system_default_route_allowed": "false",
            "result_hash": p2_0_b.result_hash,
        },
        "continuity_summary": {
            "floating_window_contract": p2_0_c.floating_window_contract.truth_label.value,
            "handoff_contract": p2_0_c.handoff_contract.truth_label.value,
            "context_carryover_contract": (
                p2_0_c.context_carryover_contract.truth_label.value
            ),
            "result_hash": p2_0_c.result_hash,
        },
        "truth_label_summary": {
            "truth_contract": p2_0_d.truth_label_contract.contract_hash,
            "truth_claim_count": str(len(p2_0_d.truth_snapshot)),
            "live_claimed": "false",
            "trace_verified_claimed": "false",
        },
        "permission_matrix_summary": p2_0_d.permission_matrix_summary,
        "unavailable_state_summary": {
            "state_count": str(len(p2_0_d.unavailable_states)),
            "reasoned": "true",
            "operator_visible": "true",
            "live": "false",
        },
        "fixture_disclosure_summary": p2_0_d.fixture_discipline_summary,
        "operator_demo_summary": _operator_demo_summary(operator_demo),
        "client_consistency_summary": _client_consistency_summary(client_contract),
        "regression_harness_summary": regression_harness_summary
        or {"status": "pending_contract_summary", "creates_route_runtime": "false"},
        "readiness_summary": readiness_summary
        or {"status": "pending_readiness_summary", "is_exit_seal": "false"},
        "truth_label": "SHELL_SNAPSHOT_CONTRACT_ONLY",
        "is_read_model": True,
        "is_source_of_truth": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "carries_truth_labels": True,
        "contract": contract,
        "non_goals": _SNAPSHOT_NON_GOALS,
    }
    snapshot = ShellStateSnapshot(**payload, snapshot_hash=_hash_payload(payload))
    assert_shell_snapshot_is_read_model_only(snapshot)
    assert_shell_snapshot_is_not_source_of_truth(snapshot)
    assert_shell_snapshot_does_not_mutate_runtime(snapshot)
    assert p2_0_a.result_hash
    return snapshot


def serialize_shell_state_snapshot(snapshot: ShellStateSnapshot) -> str:
    return to_canonical_json(snapshot.to_canonical_dict())


def assert_shell_snapshot_serializes(snapshot: ShellStateSnapshot) -> None:
    payload = serialize_shell_state_snapshot(snapshot)
    if not payload:
        _reject(
            "shell snapshot must serialize",
            field="snapshot",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_shell_snapshot_is_read_model_only(snapshot: ShellStateSnapshot) -> None:
    if not snapshot.is_read_model or snapshot.contract.source_boundary.owns_truth:
        _reject(
            "shell snapshot must be read-model only",
            field="is_read_model",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_shell_snapshot_is_not_source_of_truth(snapshot: ShellStateSnapshot) -> None:
    if snapshot.is_source_of_truth or snapshot.contract.source_boundary.is_source_of_truth:
        _reject(
            "shell snapshot must not be source of truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_shell_snapshot_does_not_mutate_runtime(snapshot: ShellStateSnapshot) -> None:
    if snapshot.mutates_runtime or snapshot.writes_memory or snapshot.writes_trace:
        _reject(
            "shell snapshot must not mutate runtime, memory, or trace",
            field="mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )

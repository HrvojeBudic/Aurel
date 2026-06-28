"""P2.0-D truth, permission, unavailable, and fixture pack result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import _CanonicalMixin, _hash_payload, to_canonical_json
from .continuity_read_model import (
    build_p2_0_c_floating_window_handoff_context_result,
)
from .fixture_discipline import (
    SurfaceDevFixtureDisclosure,
    SurfaceFixtureDisciplineContract,
    SurfaceFixtureDisclosure,
    SurfaceMockDisclosure,
    SurfaceSimulatedDisclosure,
    build_surface_dev_fixture_disclosure,
    build_surface_fixture_discipline_contract,
    build_surface_mock_disclosure,
    build_surface_simulated_disclosure,
)
from .permission_matrix import (
    SurfacePermissionMatrixContract,
    SurfacePermissionMatrixSnapshot,
    build_default_surface_permission_matrix,
    build_surface_permission_matrix_contract,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)
from .truth_labels import (
    SurfaceTruthClaim,
    SurfaceTruthLabel,
    SurfaceTruthLabelContract,
    build_surface_truth_label_contract,
    build_surface_truth_snapshot,
)
from .unavailable_state import (
    SurfaceUnavailableReason,
    SurfaceUnavailableState,
    SurfaceUnavailableStateContract,
    build_surface_unavailable_state,
    build_surface_unavailable_state_contract,
)

P2_0_D_PACK_ID = "P2.0-D"
P2_0_D_SECTION_ID = "P2.0"
P2_0_D_DEPENDENCY_PACKS: tuple[str, ...] = ("P2.0-A", "P2.0-B", "P2.0-C")
P2_0_D_NEXT_PACK = "P2.0-E"
P2_0_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.0.18",
    "P2.0.19",
    "P2.0.20",
    "P2.0.21",
)
P2_0_D_PACK_RESULT_VERSION = "p2_0_d_truth_permission_fixture_result.v1"


class P20DCheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


_CHECKPOINT_CANONICAL_NAMES: dict[str, str] = {
    "P2.0.18": "Surface Truth Label Contract",
    "P2.0.19": "Surface Permission Matrix Contract",
    "P2.0.20": "Surface Unavailable-State Contract",
    "P2.0.21": "Surface Fixture / DEV_FIXTURE / MOCK Contract",
}


@dataclass(frozen=True)
class P20DTruthPermissionFixtureSideEffectProof(_CanonicalMixin):
    """Proof that P2.0-D creates no authority/runtime side effects."""

    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    authorization_granted: bool = False
    root_authority_granted: bool = False
    agent_system_access_granted: bool = False
    tool_permission_granted: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    live_surface_created: bool = False
    trace_verification_created: bool = False
    ui_created: bool = False
    demo_harness_created: bool = False
    production_data_created: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    p2_0_e_started: bool = False
    p2_1_started: bool = False


@dataclass(frozen=True)
class P20DCheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P20DCheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class P20DTruthPermissionFixturePackResult(_CanonicalMixin):
    """P2.0-D pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    checkpoint_reads: tuple[P20DCheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    permission_matrix_summary: dict[str, str]
    unavailable_reason_catalog: tuple[str, ...]
    fixture_discipline_summary: dict[str, str]
    side_effect_proof: P20DTruthPermissionFixtureSideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    truth_label_contract: SurfaceTruthLabelContract
    truth_snapshot: tuple[SurfaceTruthClaim, ...]
    permission_matrix_contract: SurfacePermissionMatrixContract
    permission_matrix: SurfacePermissionMatrixSnapshot
    unavailable_state_contract: SurfaceUnavailableStateContract
    unavailable_states: tuple[SurfaceUnavailableState, ...]
    fixture_discipline_contract: SurfaceFixtureDisciplineContract
    fixture_disclosures: tuple[SurfaceFixtureDisclosure, ...]
    registry: AurelSurfaceRegistry
    p2_0_c_dependency_hash: str
    next_pack: str
    result_hash: str


def _all_false_p2_0_d_side_effects() -> P20DTruthPermissionFixtureSideEffectProof:
    return P20DTruthPermissionFixtureSideEffectProof()


def _default_checkpoint_reads() -> tuple[P20DCheckpointRead, ...]:
    evidence_map = {
        "P2.0.18": "SurfaceTruthLabelContract, SurfaceTruthClaim",
        "P2.0.19": "SurfacePermissionMatrixContract, SurfacePermissionEntry",
        "P2.0.20": "SurfaceUnavailableStateContract, SurfaceUnavailableState",
        "P2.0.21": "SurfaceFixtureDisciplineContract, fixture disclosures",
    }
    tests_map = {
        "P2.0.18": "test_p2_0_18_truth_*",
        "P2.0.19": "test_p2_0_19_permission_*",
        "P2.0.20": "test_p2_0_20_unavailable_*",
        "P2.0.21": "test_p2_0_21_fixture_*",
    }
    truth_map = {
        "P2.0.18": "CONTRACT_ONLY / NOT_LIVE",
        "P2.0.19": "PERMISSION_MATRIX_CONTRACT_ONLY / CONTRACT_ONLY",
        "P2.0.20": "UNAVAILABLE_STATE_CONTRACT_ONLY / UNAVAILABLE / NOT_LIVE",
        "P2.0.21": "FIXTURE_DISCLOSURE_ONLY / DEV_FIXTURE / MOCK / SIMULATED / NOT_LIVE",
    }
    unavailable_map = {
        "P2.0.18": "n/a — truth label contract only",
        "P2.0.19": "n/a — permission meaning contract only",
        "P2.0.20": "MISSING_LIVE_PATH / NOT_IMPLEMENTED_YET",
        "P2.0.21": "n/a — fixture disclosure contract only",
    }
    limitations_map = {
        "P2.0.18": "No live shell path or trace verification implementation",
        "P2.0.19": "No permission enforcement, Custos integration, or auth middleware",
        "P2.0.20": "No runtime probing, automatic repair, or UI error rendering",
        "P2.0.21": "No demo UI, production data, or fake product fixture data",
    }
    return tuple(
        P20DCheckpointRead(
            checkpoint_id=checkpoint_id,
            canonical_name=_CHECKPOINT_CANONICAL_NAMES[checkpoint_id],
            status=P20DCheckpointStatus.DONE,
            evidence=evidence_map[checkpoint_id],
            tests=tests_map[checkpoint_id],
            truth_label=truth_map[checkpoint_id],
            unavailable_reason=unavailable_map[checkpoint_id],
            limitations=limitations_map[checkpoint_id],
        )
        for checkpoint_id in P2_0_D_PACK_CHECKPOINT_IDS
    )


def _build_unavailable_states(
    registry: AurelSurfaceRegistry,
) -> tuple[SurfaceUnavailableState, ...]:
    return tuple(
        build_surface_unavailable_state(
            surface_kind=surface.surface_kind,
            unavailable_reason=SurfaceUnavailableReason.MISSING_LIVE_PATH,
            operator_message=(
                f"{surface.display_name} has no live surface path in P2.0-D."
            ),
            dependency="live_surface_runtime",
        )
        for surface in registry.surfaces
    )


def _build_fixture_disclosures() -> tuple[
    SurfaceDevFixtureDisclosure | SurfaceMockDisclosure | SurfaceSimulatedDisclosure,
    ...,
]:
    return (
        build_surface_dev_fixture_disclosure(),
        build_surface_mock_disclosure(),
        build_surface_simulated_disclosure(),
    )


def build_p2_0_d_truth_permission_fixture_result() -> (
    P20DTruthPermissionFixturePackResult
):
    registry = build_default_surface_registry()
    p2_0_c_result = build_p2_0_c_floating_window_handoff_context_result()
    truth_contract = build_surface_truth_label_contract()
    truth_snapshot = build_surface_truth_snapshot(registry)
    permission_contract = build_surface_permission_matrix_contract()
    permission_matrix = build_default_surface_permission_matrix(registry)
    unavailable_contract = build_surface_unavailable_state_contract()
    unavailable_states = _build_unavailable_states(registry)
    fixture_contract = build_surface_fixture_discipline_contract()
    fixture_disclosures = _build_fixture_disclosures()
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    drift, drift_details = detect_surface_taxonomy_drift()
    truth_labels = tuple(label.value for label in SurfaceTruthLabel)
    unavailable_reason_catalog = tuple(reason.value for reason in SurfaceUnavailableReason)
    permission_matrix_summary = {
        "entry_count": str(permission_matrix.entry_count),
        "contract_only": str(
            permission_contract.permission_matrix_is_contract_only
        ).lower(),
        "authorizes_action": "false",
        "executes_action": "false",
        "replaces_custos": "false",
        "grants_permission": "false",
    }
    fixture_discipline_summary = {
        "disclosure_count": str(len(fixture_disclosures)),
        "requires_visible_label": "true",
        "requires_source": "true",
        "requires_scope_or_expiry": "true",
        "is_live": "false",
        "is_production_data": "false",
    }
    payload: dict[str, Any] = {
        "schema_version": P2_0_D_PACK_RESULT_VERSION,
        "pack_id": P2_0_D_PACK_ID,
        "section_id": P2_0_D_SECTION_ID,
        "covered_checkpoints": P2_0_D_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_0_D_DEPENDENCY_PACKS,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "permission_matrix_summary": permission_matrix_summary,
        "unavailable_reason_catalog": unavailable_reason_catalog,
        "fixture_discipline_summary": fixture_discipline_summary,
        "side_effect_proof": _all_false_p2_0_d_side_effects(),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "truth_label_contract": truth_contract,
        "truth_snapshot": truth_snapshot,
        "permission_matrix_contract": permission_contract,
        "permission_matrix": permission_matrix,
        "unavailable_state_contract": unavailable_contract,
        "unavailable_states": unavailable_states,
        "fixture_discipline_contract": fixture_contract,
        "fixture_disclosures": fixture_disclosures,
        "registry": registry,
        "p2_0_c_dependency_hash": p2_0_c_result.result_hash,
        "next_pack": P2_0_D_NEXT_PACK,
    }
    return P20DTruthPermissionFixturePackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_truth_permission_fixture_result(
    result: P20DTruthPermissionFixturePackResult,
) -> str:
    return to_canonical_json(result.to_canonical_dict())

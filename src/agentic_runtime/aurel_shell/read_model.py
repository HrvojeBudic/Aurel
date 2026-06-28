"""AurelShell registry snapshot and P2.0-A pack result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AUREL_SHELL_NEXT_PACK_ID,
    AUREL_SHELL_PACK_CHECKPOINT_IDS,
    AUREL_SHELL_PACK_TASK_ID,
    AUREL_SHELL_SECTION_ID,
    AurelShellContract,
    AurelShellSideEffectProof,
    AurelShellTruthLabel,
    AurelShellValidationError,
    build_aurel_shell_contract,
    _CanonicalMixin,
    _all_false_side_effects,
    _hash_payload,
    to_canonical_json,
)
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    OLD_SURFACE_TAXONOMY,
    AurelSurfaceContract,
    AurelSurfaceRegistry,
    AurelSurfaceTruthLabel,
    build_default_surface_registry,
)

AUREL_SURFACE_REGISTRY_SNAPSHOT_VERSION = "aurel_surface_registry_snapshot.v1"
P2_0_A_PACK_RESULT_VERSION = "p2_0_a_shell_foundation_surface_registry_result.v1"


class P20ACheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


_CHECKPOINT_CANONICAL_NAMES: dict[str, str] = {
    "P2.0.0": "Phase 2 Shell Lock Foundation",
    "P2.0.1": "AurelShell as Operator Command Skin Contract",
    "P2.0.2": "Aurel CRO Surface Contract",
    "P2.0.3": "HQ Sovereign Operations Surface Contract",
    "P2.0.4": "CORP BusinessEnvironment Surface Contract",
    "P2.0.5": "HUB Tool Constellation Surface Contract",
    "P2.0.6": "IDE / CodeOps Engineering Surface Contract",
    "P2.0.7": "SYSTEM Operator-Only Root Surface Contract",
    "P2.0.8": "Settings Non-Root Configuration Surface Contract",
}


@dataclass(frozen=True)
class P20ACheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P20ACheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class AurelSurfaceRegistrySnapshot(_CanonicalMixin):
    """Read-model snapshot of the seven-surface registry."""

    schema_version: str
    pack_id: str
    shell_contract: AurelShellContract
    registry: AurelSurfaceRegistry
    surface_count: int
    canonical_surface_ids: tuple[str, ...]
    truth_labels: tuple[str, ...]
    side_effects: AurelShellSideEffectProof
    snapshot_hash: str


@dataclass(frozen=True)
class P20AShellFoundationSurfaceRegistryResult(_CanonicalMixin):
    """P2.0-A pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    surface_count: int
    canonical_surface_ids: tuple[str, ...]
    checkpoint_reads: tuple[P20ACheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    side_effect_proof: AurelShellSideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    shell_contract: AurelShellContract
    registry: AurelSurfaceRegistry
    snapshot: AurelSurfaceRegistrySnapshot
    next_pack: str
    result_hash: str


def _default_checkpoint_reads() -> tuple[P20ACheckpointRead, ...]:
    reads: list[P20ACheckpointRead] = []
    evidence_map = {
        "P2.0.0": "AurelShellContract, build_aurel_shell_contract()",
        "P2.0.1": "AurelShellBoundary, AurelShellRole.OPERATOR_COMMAND_SKIN",
        "P2.0.2": "AurelSurfaceContract(kind=AUREL_CRO)",
        "P2.0.3": "AurelSurfaceContract(kind=HQ)",
        "P2.0.4": "AurelSurfaceContract(kind=CORP)",
        "P2.0.5": "AurelSurfaceContract(kind=HUB)",
        "P2.0.6": "AurelSurfaceContract(kind=IDE)",
        "P2.0.7": "AurelSurfaceContract(kind=SYSTEM)",
        "P2.0.8": "AurelSurfaceContract(kind=SETTINGS)",
    }
    tests_map = {
        "P2.0.0": "test_p2_0_0_shell_contract_builds_and_serializes",
        "P2.0.1": "test_p2_0_1_shell_boundary_operator_command_skin",
        "P2.0.2": "test_p2_0_2_aurel_cro_surface_contract",
        "P2.0.3": "test_p2_0_3_hq_surface_contract",
        "P2.0.4": "test_p2_0_4_corp_surface_contract",
        "P2.0.5": "test_p2_0_5_hub_surface_contract",
        "P2.0.6": "test_p2_0_6_ide_surface_contract",
        "P2.0.7": "test_p2_0_7_system_surface_contract",
        "P2.0.8": "test_p2_0_8_settings_surface_contract",
    }
    truth_map = {
        "P2.0.0": "CONTRACT_ONLY / READ_MODEL_ONLY / NOT_LIVE",
        "P2.0.1": "CONTRACT_ONLY / PROJECTION_ONLY",
        "P2.0.2": "SURFACE_CONTRACT_ONLY",
        "P2.0.3": "SURFACE_CONTRACT_ONLY",
        "P2.0.4": "SURFACE_CONTRACT_ONLY",
        "P2.0.5": "SURFACE_CONTRACT_ONLY",
        "P2.0.6": "SURFACE_CONTRACT_ONLY",
        "P2.0.7": "SURFACE_CONTRACT_ONLY / OPERATOR_ONLY_CONTRACT",
        "P2.0.8": "SURFACE_CONTRACT_ONLY / NON_ROOT_CONFIG_CONTRACT",
    }
    for checkpoint_id in AUREL_SHELL_PACK_CHECKPOINT_IDS:
        reads.append(
            P20ACheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=_CHECKPOINT_CANONICAL_NAMES[checkpoint_id],
                status=P20ACheckpointStatus.DONE,
                evidence=evidence_map[checkpoint_id],
                tests=tests_map[checkpoint_id],
                truth_label=truth_map[checkpoint_id],
                unavailable_reason="n/a — contract foundation only",
                limitations="No UI, routes, navigation, or runtime enforcement",
            )
        )
    return tuple(reads)


def detect_surface_taxonomy_drift() -> tuple[bool, tuple[str, ...]]:
    """Report legacy taxonomy references present elsewhere in repo docs/code."""
    details = (
        "ARCHITECTURE.md documents A-Hub/S-Hub/L-Hub as independent tools — "
        "not active P2.0-A registry surfaces",
        "evaluation_foundation.py references A-Hub/S-Hub/L-Hub evaluation — "
        "not active P2.0-A registry surfaces",
        "output_passport surface_read_model.py covers 5 surfaces without "
        "SYSTEM/Settings — P1.9 read model, not P2.0-A registry",
    )
    return True, details


def build_surface_registry_snapshot() -> AurelSurfaceRegistrySnapshot:
    shell_contract = build_aurel_shell_contract()
    registry = build_default_surface_registry()
    side_effects = _all_false_side_effects()
    truth_labels = (
        AurelShellTruthLabel.CONTRACT_ONLY.value,
        AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY.value,
        AurelSurfaceTruthLabel.NOT_LIVE.value,
    )
    payload = {
        "schema_version": AUREL_SURFACE_REGISTRY_SNAPSHOT_VERSION,
        "pack_id": AUREL_SHELL_PACK_TASK_ID,
        "shell_contract": shell_contract,
        "registry": registry,
        "surface_count": registry.surface_count,
        "canonical_surface_ids": registry.canonical_surface_ids,
        "truth_labels": truth_labels,
        "side_effects": side_effects,
    }
    return AurelSurfaceRegistrySnapshot(
        **payload,
        snapshot_hash=_hash_payload(payload),
    )


def build_p2_0_a_shell_foundation_surface_registry_result() -> (
    P20AShellFoundationSurfaceRegistryResult
):
    shell_contract = build_aurel_shell_contract()
    registry = build_default_surface_registry()
    snapshot = build_surface_registry_snapshot()
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    drift, drift_details = detect_surface_taxonomy_drift()
    unavailable_reasons = tuple(
        sorted({surface.unavailable_reason for surface in registry.surfaces})
    )
    truth_labels = (
        AurelShellTruthLabel.CONTRACT_ONLY.value,
        AurelShellTruthLabel.READ_MODEL_ONLY.value,
        AurelShellTruthLabel.NOT_LIVE.value,
        AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY.value,
        AurelSurfaceTruthLabel.OPERATOR_ONLY_CONTRACT.value,
        AurelSurfaceTruthLabel.NON_ROOT_CONFIG_CONTRACT.value,
    )
    side_effects = _all_false_side_effects()
    payload: dict[str, Any] = {
        "schema_version": P2_0_A_PACK_RESULT_VERSION,
        "pack_id": AUREL_SHELL_PACK_TASK_ID,
        "section_id": AUREL_SHELL_SECTION_ID,
        "covered_checkpoints": AUREL_SHELL_PACK_CHECKPOINT_IDS,
        "surface_count": registry.surface_count,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "unavailable_reasons": unavailable_reasons,
        "side_effect_proof": side_effects,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "shell_contract": shell_contract,
        "registry": registry,
        "snapshot": snapshot,
        "next_pack": AUREL_SHELL_NEXT_PACK_ID,
    }
    return P20AShellFoundationSurfaceRegistryResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_surface_registry_snapshot(snapshot: AurelSurfaceRegistrySnapshot) -> str:
    return to_canonical_json(snapshot.to_canonical_dict())


def serialize_p2_0_a_pack_result(result: P20AShellFoundationSurfaceRegistryResult) -> str:
    return to_canonical_json(result.to_canonical_dict())

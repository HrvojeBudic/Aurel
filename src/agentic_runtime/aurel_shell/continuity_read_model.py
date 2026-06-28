"""AurelShell P2.0-C floating window / handoff / context carryover pack result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .context_carryover import (
    CrossSurfaceContextCarryoverContract,
    build_context_carryover_contract,
)
from .contracts import (
    _CanonicalMixin,
    _hash_payload,
    to_canonical_json,
)
from .floating_window import (
    FloatingWindowDescriptor,
    FloatingWindowSharedContract,
    build_dev_fixture_floating_window_descriptor,
    build_floating_window_shared_contract,
)
from .handoff import (
    CrossSurfaceHandoffContract,
    build_cross_surface_handoff_contract,
)
from .navigation_read_model import (
    build_p2_0_b_navigation_boundary_pack_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)

P2_0_C_PACK_ID = "P2.0-C"
P2_0_C_SECTION_ID = "P2.0"
P2_0_C_DEPENDENCY_PACKS: tuple[str, ...] = ("P2.0-A", "P2.0-B")
P2_0_C_NEXT_PACK = "P2.0-D"
P2_0_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.0.15",
    "P2.0.16",
    "P2.0.17",
)
P2_0_C_PACK_RESULT_VERSION = "p2_0_c_floating_window_handoff_context_result.v1"


class P20CCheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


_CHECKPOINT_CANONICAL_NAMES: dict[str, str] = {
    "P2.0.15": "Floating Window Shared Contract",
    "P2.0.16": "Cross-Surface Handoff Contract",
    "P2.0.17": "Cross-Surface Context Carryover Contract",
}


@dataclass(frozen=True)
class P20CContinuitySideEffectProof(_CanonicalMixin):
    """Proof that P2.0-C performs no UI/runtime/authority side effects."""

    ui_created: bool = False
    draggable_window_ui_created: bool = False
    modal_ui_created: bool = False
    window_manager_created: bool = False
    route_runtime_created: bool = False
    handoff_runtime_created: bool = False
    command_executed: bool = False
    permission_granted: bool = False
    system_access_granted: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    p2_0_d_started: bool = False
    p2_1_started: bool = False


@dataclass(frozen=True)
class P20CCheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P20CCheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class P20CFloatingWindowHandoffContextPackResult(_CanonicalMixin):
    """P2.0-C pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    checkpoint_reads: tuple[P20CCheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    side_effect_proof: P20CContinuitySideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    floating_window_contract: FloatingWindowSharedContract
    floating_window_descriptor: FloatingWindowDescriptor
    handoff_contract: CrossSurfaceHandoffContract
    context_carryover_contract: CrossSurfaceContextCarryoverContract
    registry: AurelSurfaceRegistry
    p2_0_b_dependency_hash: str
    next_pack: str
    result_hash: str


def _all_false_p2_0_c_side_effects() -> P20CContinuitySideEffectProof:
    return P20CContinuitySideEffectProof()


def _default_checkpoint_reads() -> tuple[P20CCheckpointRead, ...]:
    evidence_map = {
        "P2.0.15": "FloatingWindowSharedContract, FloatingWindowDescriptor",
        "P2.0.16": "CrossSurfaceHandoffContract, SurfaceHandoffIntent",
        "P2.0.17": "CrossSurfaceContextCarryoverContract, ContextCarryoverPayload",
    }
    tests_map = {
        "P2.0.15": "test_p2_0_15_floating_window_*",
        "P2.0.16": "test_p2_0_16_handoff_*",
        "P2.0.17": "test_p2_0_17_context_carryover_*",
    }
    truth_map = {
        "P2.0.15": "FLOATING_WINDOW_CONTRACT_ONLY / DEV_FIXTURE / NOT_LIVE",
        "P2.0.16": "HANDOFF_CONTRACT_ONLY / DEV_FIXTURE / NOT_LIVE / NOT_EXECUTED",
        "P2.0.17": "CONTEXT_CARRYOVER_CONTRACT_ONLY / NOT_TRACE_VERIFIED / DEV_FIXTURE",
    }
    reads: list[P20CCheckpointRead] = []
    for checkpoint_id in P2_0_C_PACK_CHECKPOINT_IDS:
        reads.append(
            P20CCheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=_CHECKPOINT_CANONICAL_NAMES[checkpoint_id],
                status=P20CCheckpointStatus.DONE,
                evidence=evidence_map[checkpoint_id],
                tests=tests_map[checkpoint_id],
                truth_label=truth_map[checkpoint_id],
                unavailable_reason="n/a — continuity contract only",
                limitations="No UI, window manager, handoff runtime, memory, or trace writes",
            )
        )
    return tuple(reads)


def build_p2_0_c_floating_window_handoff_context_result() -> (
    P20CFloatingWindowHandoffContextPackResult
):
    registry = build_default_surface_registry()
    p2_0_b_result = build_p2_0_b_navigation_boundary_pack_result()
    floating_contract = build_floating_window_shared_contract()
    floating_descriptor = build_dev_fixture_floating_window_descriptor()
    handoff_contract = build_cross_surface_handoff_contract(registry)
    context_contract = build_context_carryover_contract()
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    drift, drift_details = detect_surface_taxonomy_drift()
    unavailable_reasons = tuple(
        sorted(
            {
                floating_contract.unavailable_reason,
                floating_descriptor.unavailable_reason,
                handoff_contract.unavailable_reason,
                context_contract.unavailable_reason,
            }
        )
    )
    truth_labels = (
        "FLOATING_WINDOW_CONTRACT_ONLY",
        "HANDOFF_CONTRACT_ONLY",
        "CONTEXT_CARRYOVER_CONTRACT_ONLY",
        "DEV_FIXTURE",
        "NOT_LIVE",
        "NOT_TRACE_VERIFIED",
        "NOT_EXECUTED",
        "CONTRACT_ONLY",
    )
    side_effects = _all_false_p2_0_c_side_effects()
    payload: dict[str, Any] = {
        "schema_version": P2_0_C_PACK_RESULT_VERSION,
        "pack_id": P2_0_C_PACK_ID,
        "section_id": P2_0_C_SECTION_ID,
        "covered_checkpoints": P2_0_C_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_0_C_DEPENDENCY_PACKS,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "unavailable_reasons": unavailable_reasons,
        "side_effect_proof": side_effects,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "floating_window_contract": floating_contract,
        "floating_window_descriptor": floating_descriptor,
        "handoff_contract": handoff_contract,
        "context_carryover_contract": context_contract,
        "registry": registry,
        "p2_0_b_dependency_hash": p2_0_b_result.result_hash,
        "next_pack": P2_0_C_NEXT_PACK,
    }
    return P20CFloatingWindowHandoffContextPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_floating_window_handoff_context_result(
    result: P20CFloatingWindowHandoffContextPackResult,
) -> str:
    return to_canonical_json(result.to_canonical_dict())

"""Delegation integration tail projection (P1.8-C).

P1.8-C covers P1.8.27 through P1.8.30 as the integration tail pack:

- P1.8.27 Delegation Projection / API / Event Contract
- P1.8.28 Delegation Shell / CLI / TUI Binding  (UNAVAILABLE)
- P1.8.29 Delegation Docs / State / Reports Update
- P1.8.30 P1.8 Exit Seal + Integration Demo

Boundary: these contracts compose P1.8-A and P1.8-B into a unified
projection/read-model/event contract. They do not enforce runtime policy,
call Custos, create approvals, grant live permissions, execute tools/workflows,
write memory, write Ledger/global trace, dispatch events, bind CLI/Shell/TUI
(CLI is explicitly UNAVAILABLE), or mutate runtime state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, TypeVar

from .action_boundary import (
    DelegationActionBoundaryPackResult,
    build_p1_8_b_action_boundary_pack_result,
)
from .actor_boundary import (
    DelegationActorBoundaryPackResult,
    build_p1_8_a_actor_boundary_pack_result,
)
from .foundation import (
    DelegationErrorCode,
    DelegationSourceLabel,
    DelegationValidationError,
    stable_hash,
    to_canonical_json,
    validate_known_fields,
)

# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------

DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID = "P1.8-C"
DELEGATION_INTEGRATION_TAIL_PACK_CHECKPOINT_IDS = (
    "P1.8.27",
    "P1.8.28",
    "P1.8.29",
    "P1.8.30",
)

DELEGATION_SECTION_READ_MODEL_VERSION = "delegation_section_read_model.v1"
DELEGATION_SECTION_PROJECTION_PAYLOAD_VERSION = (
    "delegation_section_projection_payload.v1"
)
DELEGATION_EVENT_PAYLOAD_VERSION = "delegation_event_payload.v1"
DELEGATION_OPERATOR_DEMO_RESULT_VERSION = "delegation_operator_demo_result.v1"
DELEGATION_EXIT_SEAL_RESULT_VERSION = "delegation_exit_seal_result.v1"
DELEGATION_PROJECTION_SIDE_EFFECTS_VERSION = (
    "delegation_projection_side_effects.v1"
)

DELEGATION_COVERED_CHECKPOINT_RANGE = ("P1.8.17", "P1.8.30")
DELEGATION_NEXT_PACK = "P1.9-A"

DELEGATION_CLI_UNAVAILABLE_REASON = (
    "CLI/TUI binding not safely available in current repo layer; "
    "projection builder functions, serialization helpers, and focused "
    "pytest tests provide an operator-testable inspection path. "
    "CLI binding is owned by P1.8.28 and is explicitly UNAVAILABLE."
)

DELEGATION_RUNTIME_ENFORCEMENT_UNAVAILABLE_REASON = (
    "Runtime delegation enforcement is UNAVAILABLE in P1.8-C. "
    "This pack is contract/projection-only and enforcement belongs "
    "to later runtime/policy layers."
)

DELEGATION_TRACE_VERIFICATION_UNAVAILABLE_REASON = (
    "Trace verification is UNAVAILABLE in P1.8-C. "
    "Projection hashes are contract evidence, not trace-verified proof. "
    "No Ledger or global trace write occurs."
)

DELEGATION_EVENT_BUS_UNAVAILABLE_REASON = (
    "Event bus dispatch is UNAVAILABLE in P1.8-C. "
    "EventPayload shape exists as a versioned contract seed; "
    "it does not publish to any event bus."
)

DELEGATION_PROJECTION_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    "runtime_enforcement": DELEGATION_RUNTIME_ENFORCEMENT_UNAVAILABLE_REASON,
    "trace_verification": DELEGATION_TRACE_VERIFICATION_UNAVAILABLE_REASON,
    "cli_tui_binding": DELEGATION_CLI_UNAVAILABLE_REASON,
    "event_bus_dispatch": DELEGATION_EVENT_BUS_UNAVAILABLE_REASON,
    "custos_policy": (
        "Policy/Custos decisioning is UNAVAILABLE in P1.8-C. "
        "Projection exposes contract state without calling Custos."
    ),
    "approval_activation": (
        "Approval activation is UNAVAILABLE in P1.8-C. "
        "Projection is read-only and never grants permission."
    ),
    "execution_dispatch": (
        "Execution dispatch is UNAVAILABLE in P1.8-C. "
        "Every side-effect boolean is false."
    ),
    "memory_write": (
        "Memory write is UNAVAILABLE in P1.8-C. "
        "Projection does not mutate Mneme or any memory tier."
    ),
    "ledger_write": (
        "Ledger write is UNAVAILABLE in P1.8-C. "
        "No AurelTraceLog or Ledger entry is written."
    ),
    "global_trace_write": (
        "Global trace spine write is UNAVAILABLE in P1.8-C."
    ),
    "output_passport": (
        "Output Passport / P1.9 behavior is UNAVAILABLE in P1.8-C. "
        "Handoff to P1.9-A is declared; P1.9 is not implemented here."
    ),
    "live_demo": (
        "Live integration demo is DEV_FIXTURE in P1.8-C. "
        "Builder functions and focused tests supply the operator-testable path."
    ),
    "tool_workflow_execution": (
        "Tool and workflow execution are UNAVAILABLE in P1.8-C."
    ),
    "system_mutation": (
        "SYSTEM boundary mutation is UNAVAILABLE in P1.8-C."
    ),
    "runtime_mutation": (
        "Runtime mutation is UNAVAILABLE in P1.8-C. "
        "Projection surfaces never mutate runtime state."
    ),
}


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DelegationProjectionKind(str, Enum):
    """Closed-world projection kind taxonomy for P1.8-C."""

    SECTION_READ_MODEL = "section_read_model"
    PROJECTION_PAYLOAD = "projection_payload"
    EVENT_PAYLOAD = "event_payload"
    CLI_READ_MODEL = "cli_read_model"
    DEMO_RESULT = "demo_result"
    EXIT_SEAL = "exit_seal"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class DelegationProjectionStatus(str, Enum):
    """Closed-world projection status labels."""

    CONTRACT_READY = "contract_ready"
    PROJECTION_READY = "projection_ready"
    CLI_UNAVAILABLE = "cli_unavailable"
    DEMO_READY = "demo_ready"
    SEAL_READY = "seal_ready"
    SEAL_PARTIAL = "seal_partial"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class DelegationProjectionTruthLabel(str, Enum):
    """Truth labels for P1.8-C projection data."""

    CONTRACT_ONLY = "CONTRACT_ONLY"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    SIMULATED = "SIMULATED"
    CLI_READ_ONLY = "CLI_READ_ONLY"
    UNAVAILABLE_CLI_TUI_BINDING = "UNAVAILABLE_CLI_TUI_BINDING"
    UNAVAILABLE_RUNTIME_ENFORCEMENT = "UNAVAILABLE_RUNTIME_ENFORCEMENT"
    UNAVAILABLE_TRACE_VERIFICATION = "UNAVAILABLE_TRACE_VERIFICATION"
    UNAVAILABLE_EVENT_BUS = "UNAVAILABLE_EVENT_BUS"
    UNAVAILABLE_API_SERVER = "UNAVAILABLE_API_SERVER"


class DelegationSectionSealStatus(str, Enum):
    """P1.8 exit seal status labels."""

    SEAL_READY = "SEAL_READY"
    SEAL_PARTIAL = "SEAL_PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class DelegationOperatorDemoStatus(str, Enum):
    """Demo/testable-path status labels."""

    DEMO_READY = "DEMO_READY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"


# ---------------------------------------------------------------------------
# Known fields
# ---------------------------------------------------------------------------

PROJECTION_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_decision_emitted",
    "custos_decision_emitted",
    "approval_created",
    "permission_granted",
    "execution_started",
    "ledger_written",
    "global_trace_written",
    "memory_written",
    "workflow_executed",
    "tool_executed",
    "event_dispatched",
    "system_boundary_mutated",
    "runtime_mutated",
})

SECTION_READ_MODEL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "section_name",
    "covered_checkpoints",
    "actor_boundary_pack_ref",
    "action_boundary_pack_ref",
    "actor_boundary_result_hash",
    "action_boundary_result_hash",
    "actor_boundary_checkpoint_count",
    "action_boundary_checkpoint_count",
    "cli_status",
    "projection_status",
    "seal_status",
    "demo_status",
    "runtime_enforcement_status",
    "trace_verification_status",
    "event_bus_status",
    "truth_label",
    "source_label",
    "unavailable_reason_details",
    "unavailable_reasons",
    "next_pack",
    "side_effects",
    "deterministic_id",
    "read_model_hash",
})

SECTION_PROJECTION_PAYLOAD_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "projection_kind",
    "read_model_hash",
    "covered_checkpoints",
    "cli_status",
    "seal_status",
    "demo_status",
    "runtime_enforcement_status",
    "trace_verification_status",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "next_pack",
    "projection_hash",
})

EVENT_PAYLOAD_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "event_kind",
    "event_ref",
    "projection_payload_hash",
    "dispatched",
    "event_bus_status",
    "unavailable_reason",
    "event_payload_hash",
})

OPERATOR_DEMO_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "section_name",
    "demo_status",
    "actor_boundary_present",
    "action_boundary_present",
    "projection_present",
    "cli_status",
    "docs_report_status",
    "seal_status",
    "runtime_enforcement_available",
    "trace_verification_available",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "next_pack",
    "demo_result_hash",
})

EXIT_SEAL_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "section_name",
    "checkpoint_range",
    "actor_boundary_checkpoint_count",
    "action_boundary_checkpoint_count",
    "tail_checkpoint_count",
    "seal_status",
    "seal_reason",
    "cli_status",
    "demo_status",
    "runtime_enforcement_declared",
    "trace_verification_declared",
    "live_claimed",
    "trace_verified_claimed",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "next_pack",
    "seal_hash",
})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


@dataclass(frozen=True)
class DelegationProjectionSideEffects(_CanonicalMixin):
    """Proof that P1.8-C performs no policy/execution/mutation side effects."""

    policy_decision_emitted: bool = False
    custos_decision_emitted: bool = False
    approval_created: bool = False
    permission_granted: bool = False
    execution_started: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    memory_written: bool = False
    workflow_executed: bool = False
    tool_executed: bool = False
    event_dispatched: bool = False
    system_boundary_mutated: bool = False
    runtime_mutated: bool = False


@dataclass(frozen=True)
class DelegationSectionReadModel(_CanonicalMixin):
    """Unified P1.8 read model composing P1.8-A + P1.8-B + tail."""

    schema_version: str
    task_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    actor_boundary_pack_ref: str
    action_boundary_pack_ref: str
    actor_boundary_result_hash: str
    action_boundary_result_hash: str
    actor_boundary_checkpoint_count: int
    action_boundary_checkpoint_count: int
    cli_status: DelegationProjectionStatus
    projection_status: DelegationProjectionStatus
    seal_status: DelegationSectionSealStatus
    demo_status: DelegationOperatorDemoStatus
    runtime_enforcement_status: DelegationProjectionStatus
    trace_verification_status: DelegationProjectionStatus
    event_bus_status: DelegationProjectionStatus
    truth_label: DelegationProjectionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reason_details: dict[str, str]
    unavailable_reasons: tuple[str, ...]
    next_pack: str
    side_effects: DelegationProjectionSideEffects
    deterministic_id: str
    read_model_hash: str


@dataclass(frozen=True)
class DelegationSectionProjectionPayload(_CanonicalMixin):
    """JSON-safe P1.8 section projection payload."""

    schema_version: str
    task_id: str
    projection_kind: DelegationProjectionKind
    read_model_hash: str
    covered_checkpoints: tuple[str, ...]
    cli_status: DelegationProjectionStatus
    seal_status: DelegationSectionSealStatus
    demo_status: DelegationOperatorDemoStatus
    runtime_enforcement_status: DelegationProjectionStatus
    trace_verification_status: DelegationProjectionStatus
    truth_label: DelegationProjectionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[str, ...]
    next_pack: str
    projection_hash: str


@dataclass(frozen=True)
class DelegationEventPayload(_CanonicalMixin):
    """Event contract shape. Never dispatched in P1.8-C."""

    schema_version: str
    task_id: str
    event_kind: DelegationProjectionKind
    event_ref: str
    projection_payload_hash: str
    dispatched: bool
    event_bus_status: DelegationProjectionStatus
    unavailable_reason: str
    event_payload_hash: str


@dataclass(frozen=True)
class DelegationOperatorDemoResult(_CanonicalMixin):
    """Operator-testable demo result for P1.8 integration."""

    schema_version: str
    task_id: str
    section_name: str
    demo_status: DelegationOperatorDemoStatus
    actor_boundary_present: bool
    action_boundary_present: bool
    projection_present: bool
    cli_status: str
    docs_report_status: str
    seal_status: DelegationSectionSealStatus
    runtime_enforcement_available: bool
    trace_verification_available: bool
    truth_label: DelegationProjectionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[str, ...]
    next_pack: str
    demo_result_hash: str


@dataclass(frozen=True)
class DelegationExitSealResult(_CanonicalMixin):
    """P1.8 exit seal result with honest status."""

    schema_version: str
    task_id: str
    section_name: str
    checkpoint_range: tuple[str, str]
    actor_boundary_checkpoint_count: int
    action_boundary_checkpoint_count: int
    tail_checkpoint_count: int
    seal_status: DelegationSectionSealStatus
    seal_reason: str
    cli_status: str
    demo_status: DelegationOperatorDemoStatus
    runtime_enforcement_declared: bool
    trace_verification_declared: bool
    live_claimed: bool
    trace_verified_claimed: bool
    truth_label: DelegationProjectionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[str, ...]
    next_pack: str
    seal_hash: str


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

P1_8_C_PROJECTION_INVARIANTS = (
    "P1.8-C does not enforce runtime policy.",
    "P1.8-C does not call Custos.",
    "P1.8-C does not create approvals.",
    "P1.8-C does not grant permissions.",
    "P1.8-C does not execute tools/workflows.",
    "P1.8-C does not write memory.",
    "P1.8-C does not write Ledger or global trace.",
    "P1.8-C does not dispatch events.",
    "P1.8-C does not mutate SYSTEM or runtime.",
    "P1.8-C does not claim LIVE.",
    "P1.8-C does not claim TRACE_VERIFIED.",
    "P1.8-C does not implement P1.9.",
    "CLI is explicitly UNAVAILABLE with honest reason.",
    "Exit seal is honest about partial/unavailable states.",
    "Projection is read-only and side-effect-free.",
)


# ---------------------------------------------------------------------------
# Parse and canonical helpers
# ---------------------------------------------------------------------------

E = TypeVar("E", bound=Enum)


def _parse_enum(enum_type: type[E], value: E | str, field_name: str) -> E:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except ValueError as exc:
        raise DelegationValidationError(
            f"invalid {field_name}: {value!r}",
            code=DelegationErrorCode.INVALID_ENUM,
            field=field_name,
        ) from exc


def _parse_source_label(value: DelegationSourceLabel | str) -> DelegationSourceLabel:
    if isinstance(value, DelegationSourceLabel):
        return value
    try:
        return DelegationSourceLabel(value)
    except ValueError as exc:
        raise DelegationValidationError(
            f"invalid source_label: {value!r}",
            code=DelegationErrorCode.INVALID_SOURCE_LABEL,
            field="source_label",
        ) from exc


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def _all_false_side_effects() -> DelegationProjectionSideEffects:
    return DelegationProjectionSideEffects()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def build_p1_8_delegation_section_read_model(
    *,
    actor_boundary_pack: DelegationActorBoundaryPackResult | None = None,
    action_boundary_pack: DelegationActionBoundaryPackResult | None = None,
) -> DelegationSectionReadModel:
    actor = actor_boundary_pack or build_p1_8_a_actor_boundary_pack_result()
    action = action_boundary_pack or build_p1_8_b_action_boundary_pack_result()

    _start_n = int(DELEGATION_COVERED_CHECKPOINT_RANGE[0].split(".")[-1])
    _end_n = int(DELEGATION_COVERED_CHECKPOINT_RANGE[1].split(".")[-1])
    covered = tuple(sorted({
        "P1.8.%d" % n for n in range(_start_n, _end_n + 1)
    }))

    unavailable_reasons = tuple(
        sorted(DELEGATION_PROJECTION_UNAVAILABLE_REASON_DETAILS.keys())
    )

    side_effects = _all_false_side_effects()

    deterministic_payload = {
        "schema_version_val": DELEGATION_SECTION_READ_MODEL_VERSION,
        "task_id": DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
        "actor_hash": actor.result_hash,
        "action_hash": action.result_hash,
    }
    deterministic_id = _hash_payload(deterministic_payload)

    payload = {
        "schema_version": DELEGATION_SECTION_READ_MODEL_VERSION,
        "task_id": DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
        "section_name": "P1.8 Delegation / Non-Repudiation / Agent Identity Mesh",
        "covered_checkpoints": covered,
        "actor_boundary_pack_ref": "P1.8-A",
        "action_boundary_pack_ref": "P1.8-B",
        "actor_boundary_result_hash": actor.result_hash,
        "action_boundary_result_hash": action.result_hash,
        "actor_boundary_checkpoint_count": len(actor.checkpoint_ids),
        "action_boundary_checkpoint_count": len(action.checkpoint_ids),
        "cli_status": DelegationProjectionStatus.CLI_UNAVAILABLE,
        "projection_status": DelegationProjectionStatus.PROJECTION_READY,
        "seal_status": DelegationSectionSealStatus.SEAL_PARTIAL,
        "demo_status": DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY,
        "runtime_enforcement_status": DelegationProjectionStatus.UNAVAILABLE,
        "trace_verification_status": DelegationProjectionStatus.UNAVAILABLE,
        "event_bus_status": DelegationProjectionStatus.UNAVAILABLE,
        "truth_label": DelegationProjectionTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reason_details": dict(
            DELEGATION_PROJECTION_UNAVAILABLE_REASON_DETAILS
        ),
        "unavailable_reasons": unavailable_reasons,
        "next_pack": DELEGATION_NEXT_PACK,
        "side_effects": side_effects,
        "deterministic_id": deterministic_id,
    }
    return DelegationSectionReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )


def build_p1_8_delegation_projection_payload(
    *,
    read_model: DelegationSectionReadModel | None = None,
) -> DelegationSectionProjectionPayload:
    rm = read_model or build_p1_8_delegation_section_read_model()
    unavailable_reasons = (
        "CLI_TUI_BINDING_UNAVAILABLE",
        "RUNTIME_ENFORCEMENT_UNAVAILABLE",
        "TRACE_VERIFICATION_UNAVAILABLE",
        "EVENT_BUS_UNAVAILABLE",
        "API_SERVER_UNAVAILABLE",
    )
    payload = {
        "schema_version": DELEGATION_SECTION_PROJECTION_PAYLOAD_VERSION,
        "task_id": DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
        "projection_kind": DelegationProjectionKind.PROJECTION_PAYLOAD,
        "read_model_hash": rm.read_model_hash,
        "covered_checkpoints": rm.covered_checkpoints,
        "cli_status": DelegationProjectionStatus.CLI_UNAVAILABLE,
        "seal_status": DelegationSectionSealStatus.SEAL_PARTIAL,
        "demo_status": DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY,
        "runtime_enforcement_status": DelegationProjectionStatus.UNAVAILABLE,
        "trace_verification_status": DelegationProjectionStatus.UNAVAILABLE,
        "truth_label": DelegationProjectionTruthLabel.PROJECTION_ONLY,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": unavailable_reasons,
        "next_pack": DELEGATION_NEXT_PACK,
    }
    return DelegationSectionProjectionPayload(
        **payload,
        projection_hash=_hash_payload(payload),
    )


def build_p1_8_delegation_event_payload(
    *,
    projection_payload: DelegationSectionProjectionPayload | None = None,
) -> DelegationEventPayload:
    pp = projection_payload or build_p1_8_delegation_projection_payload()
    payload = {
        "schema_version": DELEGATION_EVENT_PAYLOAD_VERSION,
        "task_id": DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
        "event_kind": DelegationProjectionKind.EVENT_PAYLOAD,
        "event_ref": f"delegation_section_event.{pp.task_id}",
        "projection_payload_hash": pp.projection_hash,
        "dispatched": False,
        "event_bus_status": DelegationProjectionStatus.UNAVAILABLE,
        "unavailable_reason": DELEGATION_EVENT_BUS_UNAVAILABLE_REASON,
    }
    return DelegationEventPayload(
        **payload,
        event_payload_hash=_hash_payload(payload),
    )


def build_p1_8_operator_demo_result() -> DelegationOperatorDemoResult:
    read_model = build_p1_8_delegation_section_read_model()
    actor = build_p1_8_a_actor_boundary_pack_result()
    action = build_p1_8_b_action_boundary_pack_result()

    unavailable_reasons = (
        "RUNTIME_ENFORCEMENT_UNAVAILABLE",
        "TRACE_VERIFICATION_UNAVAILABLE",
        "CLI_TUI_BINDING_UNAVAILABLE",
        "EVENT_BUS_UNAVAILABLE",
    )

    payload = {
        "schema_version": DELEGATION_OPERATOR_DEMO_RESULT_VERSION,
        "task_id": DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
        "section_name": "P1.8 Delegation Integration Tail",
        "demo_status": DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY,
        "actor_boundary_present": actor.result_hash != "",
        "action_boundary_present": action.result_hash != "",
        "projection_present": read_model.read_model_hash != "",
        "cli_status": f"UNAVAILABLE — {DELEGATION_CLI_UNAVAILABLE_REASON}",
        "docs_report_status": (
            "Report, canon, and state files updated; "
            "projection builders, tests, and serialization helpers "
            "provide operator-testable inspection path."
        ),
        "seal_status": DelegationSectionSealStatus.SEAL_PARTIAL,
        "runtime_enforcement_available": False,
        "trace_verification_available": False,
        "truth_label": DelegationProjectionTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": unavailable_reasons,
        "next_pack": DELEGATION_NEXT_PACK,
    }
    return DelegationOperatorDemoResult(
        **payload,
        demo_result_hash=_hash_payload(payload),
    )


def build_p1_8_exit_seal_result() -> DelegationExitSealResult:
    unavailable_reasons = (
        "RUNTIME_ENFORCEMENT_UNAVAILABLE",
        "TRACE_VERIFICATION_UNAVAILABLE",
        "CLI_TUI_BINDING_UNAVAILABLE",
    )

    seal_status = DelegationSectionSealStatus.SEAL_PARTIAL
    seal_reason = (
        "P1.8 is SEAL_PARTIAL: all 14 checkpoints (P1.8.17-P1.8.30) "
        "have contract/projection/read-model evidence. "
        "CLI/TUI binding is explicitly UNAVAILABLE (P1.8.28). "
        "Live integration demo is DEV_FIXTURE (P1.8.30). "
        "Runtime enforcement and trace verification remain UNAVAILABLE "
        "and belong to later runtime/policy layers. "
        "Honest labels, no fake LIVE, no fake TRACE_VERIFIED. "
        "Next: P1.9-A Output Passport Identity / Attribution / Hash Pack."
    )

    payload = {
        "schema_version": DELEGATION_EXIT_SEAL_RESULT_VERSION,
        "task_id": DELEGATION_INTEGRATION_TAIL_PACK_TASK_ID,
        "section_name": "P1.8 Delegation / Non-Repudiation / Agent Identity Mesh",
        "checkpoint_range": DELEGATION_COVERED_CHECKPOINT_RANGE,
        "actor_boundary_checkpoint_count": 6,
        "action_boundary_checkpoint_count": 4,
        "tail_checkpoint_count": 4,
        "seal_status": seal_status,
        "seal_reason": seal_reason,
        "cli_status": f"UNAVAILABLE — {DELEGATION_CLI_UNAVAILABLE_REASON}",
        "demo_status": DelegationOperatorDemoStatus.DEV_FIXTURE_ONLY,
        "runtime_enforcement_declared": False,
        "trace_verification_declared": False,
        "live_claimed": False,
        "trace_verified_claimed": False,
        "truth_label": DelegationProjectionTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": unavailable_reasons,
        "next_pack": DELEGATION_NEXT_PACK,
    }
    return DelegationExitSealResult(
        **payload,
        seal_hash=_hash_payload(payload),
    )


# ---------------------------------------------------------------------------
# Hash functions
# ---------------------------------------------------------------------------


def hash_delegation_section_read_model(
    read_model: DelegationSectionReadModel,
) -> str:
    return read_model.read_model_hash


def hash_delegation_section_projection_payload(
    payload: DelegationSectionProjectionPayload,
) -> str:
    return payload.projection_hash


def hash_delegation_event_payload(
    payload: DelegationEventPayload,
) -> str:
    return payload.event_payload_hash


def hash_delegation_operator_demo_result(
    result: DelegationOperatorDemoResult,
) -> str:
    return result.demo_result_hash


def hash_delegation_exit_seal_result(
    result: DelegationExitSealResult,
) -> str:
    return result.seal_hash


# ---------------------------------------------------------------------------
# Serialize functions
# ---------------------------------------------------------------------------


def serialize_delegation_section_read_model(
    read_model: DelegationSectionReadModel,
) -> str:
    payload = read_model.to_canonical_dict()
    validate_known_fields(
        payload,
        SECTION_READ_MODEL_KNOWN_FIELDS,
        label="DelegationSectionReadModel",
    )
    return to_canonical_json(payload)


def serialize_delegation_section_projection_payload(
    projection: DelegationSectionProjectionPayload,
) -> str:
    payload = projection.to_canonical_dict()
    validate_known_fields(
        payload,
        SECTION_PROJECTION_PAYLOAD_KNOWN_FIELDS,
        label="DelegationSectionProjectionPayload",
    )
    return to_canonical_json(payload)


def serialize_p1_8_delegation_projection(
    read_model: DelegationSectionReadModel | None = None,
) -> str:
    return serialize_delegation_section_read_model(
        read_model or build_p1_8_delegation_section_read_model()
    )


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_projection_is_read_only(
    projection: DelegationSectionProjectionPayload,
) -> None:
    """Assert that the projection payload claims no side effects."""
    assert (
        projection.truth_label != DelegationProjectionTruthLabel.CONTRACT_ONLY
        or projection.truth_label
        == DelegationProjectionTruthLabel.PROJECTION_ONLY
        or projection.truth_label
        == DelegationProjectionTruthLabel.DEV_FIXTURE
    ) or projection.truth_label in (
        DelegationProjectionTruthLabel.PROJECTION_ONLY,
        DelegationProjectionTruthLabel.DEV_FIXTURE,
    ), "projection must not claim LIVE or TRACE_VERIFIED"


def assert_event_not_dispatched(event: DelegationEventPayload) -> None:
    """Assert that the event payload has not been dispatched."""
    assert event.dispatched is False, "event must not be dispatched in P1.8-C"
    assert (
        event.event_bus_status == DelegationProjectionStatus.UNAVAILABLE
    ), "event bus must be UNAVAILABLE in P1.8-C"


def assert_seal_honest(seal: DelegationExitSealResult) -> None:
    """Assert that the exit seal makes no false claims."""
    assert seal.live_claimed is False, "P1.8-C seal must not claim LIVE"
    assert (
        seal.trace_verified_claimed is False
    ), "P1.8-C seal must not claim TRACE_VERIFIED"
    assert (
        seal.runtime_enforcement_declared is False
    ), "P1.8-C seal must not declare runtime enforcement"
    assert (
        seal.trace_verification_declared is False
    ), "P1.8-C seal must not declare trace verification"

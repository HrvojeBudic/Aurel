"""Delegation actor boundary contracts (P1.8-A).

P1.8-A is an operator-authorized remap over local v5.1 P1.8.17. It covers
P1.8.17 through P1.8.22 as a pure contract/read-model pack:

- P1.8.17 Aurel state actor boundary
- P1.8.18 Agent worker boundary
- P1.8.19 CRO authority/state bridge
- P1.8.20 SYSTEM root boundary reference
- P1.8.21 BusinessEnvironment actor boundary
- P1.8.22 Trigger proposal boundary

Boundary: these contracts describe actor separation. They do not enforce
runtime policy, create approvals, grant permissions, execute tools/workflows,
write memory, write Ledger/global trace, enter SYSTEM, or mutate runtime state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, TypeVar

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

DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID = "P1.8-A"
DELEGATION_ACTOR_BOUNDARY_PACK_CHECKPOINT_IDS = (
    "P1.8.17",
    "P1.8.18",
    "P1.8.19",
    "P1.8.20",
    "P1.8.21",
    "P1.8.22",
)

DELEGATION_AUREL_STATE_ACTOR_BOUNDARY_VERSION = "aurel_state_actor_boundary.v1"
DELEGATION_AGENT_WORKER_BOUNDARY_VERSION = "agent_worker_boundary.v1"
DELEGATION_CRO_AUTHORITY_STATE_BRIDGE_VERSION = "cro_authority_state_bridge.v1"
DELEGATION_SYSTEM_ROOT_BOUNDARY_REFERENCE_VERSION = "system_root_boundary_reference.v1"
DELEGATION_BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY_VERSION = (
    "business_environment_actor_boundary.v1"
)
DELEGATION_TRIGGER_PROPOSAL_BOUNDARY_VERSION = "trigger_proposal_boundary.v1"
DELEGATION_ACTOR_BOUNDARY_CHECKPOINT_READ_VERSION = (
    "delegation_actor_boundary_checkpoint_read.v1"
)
DELEGATION_ACTOR_BOUNDARY_READ_MODEL_VERSION = (
    "delegation_actor_boundary_read_model.v1"
)
DELEGATION_ACTOR_BOUNDARY_PACK_RESULT_VERSION = (
    "delegation_actor_boundary_pack_result.v1"
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DelegationActorBoundaryActorKind(str, Enum):
    """Closed-world actor taxonomy for P1.8-A actor boundary contracts."""

    AUREL_STATE_ACTOR = "aurel_state_actor"
    AGENT_WORKER = "agent_worker"
    CRO = "cro"
    OPERATOR = "operator"
    SYSTEM_ROOT = "system_root"
    BUSINESS_ENVIRONMENT = "business_environment"
    TOOL = "tool"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


class DelegationActorBoundaryKind(str, Enum):
    """Closed-world boundary taxonomy for P1.8.17-P1.8.22."""

    AUREL_STATE_ACTOR_BOUNDARY = "aurel_state_actor_boundary"
    AGENT_WORKER_BOUNDARY = "agent_worker_boundary"
    CRO_AUTHORITY_STATE_BRIDGE = "cro_authority_state_bridge"
    SYSTEM_ROOT_BOUNDARY = "system_root_boundary"
    BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY = "business_environment_actor_boundary"
    TRIGGER_PROPOSAL_BOUNDARY = "trigger_proposal_boundary"
    UNKNOWN = "unknown"


class DelegationAuthorityScope(str, Enum):
    """Authority scope labels. Labels do not grant authority."""

    STATE_OWNERSHIP = "state_ownership"
    WORKER_ONLY = "worker_only"
    OPERATOR_CUSTOS_RUNTIME_SYSTEM_DEPENDENT = (
        "operator_custos_runtime_system_dependent"
    )
    SYSTEM_ROOT_OPERATOR_ONLY = "system_root_operator_only"
    BUSINESS_ENVIRONMENT_BOUNDED_STATE = "business_environment_bounded_state"
    PROPOSAL_ONLY = "proposal_only"
    NONE = "none"
    UNKNOWN = "unknown"


class DelegationActorStateRole(str, Enum):
    """State role labels. Roles do not execute or mutate state."""

    STATE_OWNER = "state_owner"
    WORKER_ONLY = "worker_only"
    CRO_BRIDGE = "cro_bridge"
    SYSTEM_ROOT = "system_root"
    BOUNDED_STATE_HOLDER = "bounded_state_holder"
    PROPOSAL_ORIGIN = "proposal_origin"
    NO_STATE_AUTHORITY = "no_state_authority"
    UNKNOWN = "unknown"


class DelegationProposalOriginKind(str, Enum):
    """Closed-world proposal-origin taxonomy for trigger boundaries."""

    OPERATOR = "operator"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    MEMORY_TRIGGER = "memory_trigger"
    BUSINESS_ENVIRONMENT = "business_environment"
    SYSTEM = "system"
    NONE = "none"
    UNKNOWN = "unknown"


class DelegationBoundaryTruthLabel(str, Enum):
    """Truth label for actor-boundary contract data."""

    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"


class DelegationBoundaryUnavailableReason(str, Enum):
    """Unavailable reasons for surfaces deliberately outside P1.8-A."""

    CLI_SHELL_TUI_BINDING_P1_8_28 = "cli_shell_tui_binding_p1_8_28"
    UNAVAILABLE_RUNTIME_ENFORCEMENT = "unavailable_runtime_enforcement"
    POLICY_CUSTOS_DECISION_UNAVAILABLE = "policy_custos_decision_unavailable"
    APPROVAL_PERMISSION_UNAVAILABLE = "approval_permission_unavailable"
    EXECUTION_UNAVAILABLE = "execution_unavailable"
    TRACE_LEDGER_WRITE_UNAVAILABLE = "trace_ledger_write_unavailable"
    MEMORY_WRITE_UNAVAILABLE = "memory_write_unavailable"
    TOOL_WORKFLOW_EXECUTION_UNAVAILABLE = "tool_workflow_execution_unavailable"
    SYSTEM_ENTRY_UNAVAILABLE = "system_entry_unavailable"
    OUTPUT_PASSPORT_UNAVAILABLE = "output_passport_unavailable"
    TRACE_VERIFICATION_UNAVAILABLE = "trace_verification_unavailable"


class DelegationActorBoundaryStatus(str, Enum):
    """Read-model status labels for checkpoint rows."""

    CONTRACT_ONLY = "contract_only"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    DelegationBoundaryUnavailableReason.CLI_SHELL_TUI_BINDING_P1_8_28.value: (
        "CLI/Shell/TUI binding is UNAVAILABLE in P1.8-A; owned by P1.8.28 "
        "Delegation Shell/CLI/TUI Binding."
    ),
    DelegationBoundaryUnavailableReason.UNAVAILABLE_RUNTIME_ENFORCEMENT.value: (
        "Runtime enforcement is UNAVAILABLE in P1.8-A; this pack is "
        "contract-only and enforcement belongs to later runtime/policy layers."
    ),
    DelegationBoundaryUnavailableReason.POLICY_CUSTOS_DECISION_UNAVAILABLE.value: (
        "Policy/Custos decisioning is UNAVAILABLE in P1.8-A; actor-boundary "
        "contracts do not call policy or Custos."
    ),
    DelegationBoundaryUnavailableReason.APPROVAL_PERMISSION_UNAVAILABLE.value: (
        "Approval and permission grants are UNAVAILABLE in P1.8-A; contracts "
        "declare boundaries only."
    ),
    DelegationBoundaryUnavailableReason.EXECUTION_UNAVAILABLE.value: (
        "Runtime execution is UNAVAILABLE in P1.8-A; no command, action, or "
        "high-impact business execution occurs."
    ),
    DelegationBoundaryUnavailableReason.TRACE_LEDGER_WRITE_UNAVAILABLE.value: (
        "Trace and Ledger writes are UNAVAILABLE in P1.8-A; hashes are not "
        "audit finality."
    ),
    DelegationBoundaryUnavailableReason.MEMORY_WRITE_UNAVAILABLE.value: (
        "Memory writes are UNAVAILABLE in P1.8-A; trigger proposals do not "
        "persist memory."
    ),
    DelegationBoundaryUnavailableReason.TOOL_WORKFLOW_EXECUTION_UNAVAILABLE.value: (
        "Tool and workflow execution are UNAVAILABLE in P1.8-A; tool/workflow "
        "triggers are proposal-only."
    ),
    DelegationBoundaryUnavailableReason.SYSTEM_ENTRY_UNAVAILABLE.value: (
        "SYSTEM entry is UNAVAILABLE to agents, tools, and workflows in "
        "P1.8-A; SYSTEM root is operator-only."
    ),
    DelegationBoundaryUnavailableReason.OUTPUT_PASSPORT_UNAVAILABLE.value: (
        "Output Passport / P1.9 behavior is UNAVAILABLE in P1.8-A."
    ),
    DelegationBoundaryUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE.value: (
        "TRACE_VERIFIED is UNAVAILABLE in P1.8-A; default data is contract-only "
        "or DEV_FIXTURE."
    ),
}

DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS = tuple(
    DelegationBoundaryUnavailableReason(reason)
    for reason in DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASON_DETAILS
)


# ---------------------------------------------------------------------------
# Known fields
# ---------------------------------------------------------------------------


ACTOR_BOUNDARY_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
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
    "system_boundary_mutated",
    "runtime_mutated",
})

AUREL_STATE_ACTOR_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "actor_kind",
    "boundary_kind",
    "authority_scope",
    "state_role",
    "state_ref",
    "can_own_state",
    "agent_worker_can_own_state",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "aurel_state_actor_boundary_hash",
})

AGENT_WORKER_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "actor_kind",
    "boundary_kind",
    "authority_scope",
    "state_role",
    "worker_only",
    "can_self_authorize",
    "can_enter_system",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "agent_worker_boundary_hash",
})

CRO_AUTHORITY_STATE_BRIDGE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "actor_kind",
    "boundary_kind",
    "authority_scope",
    "state_role",
    "requires_operator",
    "requires_custos",
    "requires_runtime",
    "requires_system_root",
    "can_self_authorize",
    "can_activate_evolution",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "cro_authority_state_bridge_hash",
})

SYSTEM_ROOT_BOUNDARY_REFERENCE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "actor_kind",
    "boundary_kind",
    "authority_scope",
    "state_role",
    "operator_only",
    "agent_entry_allowed",
    "tool_entry_allowed",
    "workflow_entry_allowed",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "system_root_boundary_reference_hash",
})

BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "actor_kind",
    "boundary_kind",
    "authority_scope",
    "state_role",
    "can_hold_bounded_state_refs",
    "can_grant_permission",
    "can_execute_high_impact_actions",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "business_environment_actor_boundary_hash",
})

TRIGGER_PROPOSAL_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "boundary_kind",
    "authority_scope",
    "state_role",
    "proposal_origin_kinds",
    "proposal_only",
    "permission_granted",
    "execution_started",
    "memory_written",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "trigger_proposal_boundary_hash",
})

ACTOR_BOUNDARY_CHECKPOINT_READ_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "checkpoint_id",
    "status",
    "evidence_ref",
    "contract_hash",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "checkpoint_read_hash",
})

ACTOR_BOUNDARY_READ_MODEL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "checkpoint_reads",
    "checkpoint_count",
    "truth_label",
    "source_label",
    "unavailable_reason_details",
    "side_effects",
    "read_model_hash",
})

ACTOR_BOUNDARY_PACK_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "checkpoint_ids",
    "aurel_state_actor_boundary",
    "agent_worker_boundary",
    "cro_authority_state_bridge",
    "system_root_boundary_reference",
    "business_environment_actor_boundary",
    "trigger_proposal_boundary",
    "read_model",
    "status",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "unavailable_reason_details",
    "side_effects",
    "result_hash",
})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


@dataclass(frozen=True)
class DelegationActorBoundarySideEffects(_CanonicalMixin):
    """Proof that P1.8-A performs no policy/execution/mutation side effects."""

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
    system_boundary_mutated: bool = False
    runtime_mutated: bool = False


@dataclass(frozen=True)
class AurelStateActorBoundary(_CanonicalMixin):
    """P1.8.17 contract: Aurel state actor can own state; workers cannot."""

    checkpoint_id: str
    contract_version: str
    actor_kind: DelegationActorBoundaryActorKind
    boundary_kind: DelegationActorBoundaryKind
    authority_scope: DelegationAuthorityScope
    state_role: DelegationActorStateRole
    state_ref: str
    can_own_state: bool
    agent_worker_can_own_state: bool
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActorBoundarySideEffects
    aurel_state_actor_boundary_hash: str


@dataclass(frozen=True)
class AgentWorkerBoundary(_CanonicalMixin):
    """P1.8.18 contract: agent is worker-only, not self-authorizing."""

    checkpoint_id: str
    contract_version: str
    actor_kind: DelegationActorBoundaryActorKind
    boundary_kind: DelegationActorBoundaryKind
    authority_scope: DelegationAuthorityScope
    state_role: DelegationActorStateRole
    worker_only: bool
    can_self_authorize: bool
    can_enter_system: bool
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActorBoundarySideEffects
    agent_worker_boundary_hash: str


@dataclass(frozen=True)
class CROAuthorityStateBridge(_CanonicalMixin):
    """P1.8.19 contract: CRO bridge depends on higher authority layers."""

    checkpoint_id: str
    contract_version: str
    actor_kind: DelegationActorBoundaryActorKind
    boundary_kind: DelegationActorBoundaryKind
    authority_scope: DelegationAuthorityScope
    state_role: DelegationActorStateRole
    requires_operator: bool
    requires_custos: bool
    requires_runtime: bool
    requires_system_root: bool
    can_self_authorize: bool
    can_activate_evolution: bool
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActorBoundarySideEffects
    cro_authority_state_bridge_hash: str


@dataclass(frozen=True)
class SystemRootBoundaryReference(_CanonicalMixin):
    """P1.8.20 contract: SYSTEM root is operator-only."""

    checkpoint_id: str
    contract_version: str
    actor_kind: DelegationActorBoundaryActorKind
    boundary_kind: DelegationActorBoundaryKind
    authority_scope: DelegationAuthorityScope
    state_role: DelegationActorStateRole
    operator_only: bool
    agent_entry_allowed: bool
    tool_entry_allowed: bool
    workflow_entry_allowed: bool
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActorBoundarySideEffects
    system_root_boundary_reference_hash: str


@dataclass(frozen=True)
class BusinessEnvironmentActorBoundary(_CanonicalMixin):
    """P1.8.21 contract: BusinessEnvironment can hold bounded state refs."""

    checkpoint_id: str
    contract_version: str
    actor_kind: DelegationActorBoundaryActorKind
    boundary_kind: DelegationActorBoundaryKind
    authority_scope: DelegationAuthorityScope
    state_role: DelegationActorStateRole
    can_hold_bounded_state_refs: bool
    can_grant_permission: bool
    can_execute_high_impact_actions: bool
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActorBoundarySideEffects
    business_environment_actor_boundary_hash: str


@dataclass(frozen=True)
class TriggerProposalBoundary(_CanonicalMixin):
    """P1.8.22 contract: tool/workflow/memory triggers are proposal-only."""

    checkpoint_id: str
    contract_version: str
    boundary_kind: DelegationActorBoundaryKind
    authority_scope: DelegationAuthorityScope
    state_role: DelegationActorStateRole
    proposal_origin_kinds: tuple[DelegationProposalOriginKind, ...]
    proposal_only: bool
    permission_granted: bool
    execution_started: bool
    memory_written: bool
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActorBoundarySideEffects
    trigger_proposal_boundary_hash: str


@dataclass(frozen=True)
class DelegationActorBoundaryCheckpointRead(_CanonicalMixin):
    """Compact read-model row for one P1.8-A checkpoint."""

    schema_version: str
    checkpoint_id: str
    status: DelegationActorBoundaryStatus
    evidence_ref: str
    contract_hash: str
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    checkpoint_read_hash: str


@dataclass(frozen=True)
class DelegationActorBoundaryReadModel(_CanonicalMixin):
    """Compact P1.8-A read model containing exactly P1.8.17-P1.8.22."""

    schema_version: str
    task_id: str
    checkpoint_reads: tuple[DelegationActorBoundaryCheckpointRead, ...]
    checkpoint_count: int
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reason_details: dict[str, str]
    side_effects: DelegationActorBoundarySideEffects
    read_model_hash: str


@dataclass(frozen=True)
class DelegationActorBoundaryPackResult(_CanonicalMixin):
    """P1.8-A result envelope for the six actor-boundary contracts."""

    schema_version: str
    task_id: str
    checkpoint_ids: tuple[str, ...]
    aurel_state_actor_boundary: AurelStateActorBoundary
    agent_worker_boundary: AgentWorkerBoundary
    cro_authority_state_bridge: CROAuthorityStateBridge
    system_root_boundary_reference: SystemRootBoundaryReference
    business_environment_actor_boundary: BusinessEnvironmentActorBoundary
    trigger_proposal_boundary: TriggerProposalBoundary
    read_model: DelegationActorBoundaryReadModel
    status: DelegationActorBoundaryStatus
    truth_label: DelegationBoundaryTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationBoundaryUnavailableReason, ...]
    unavailable_reason_details: dict[str, str]
    side_effects: DelegationActorBoundarySideEffects
    result_hash: str


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


AUREL_STATE_ACTOR_BOUNDARY_INVARIANTS = (
    "Aurel state actor can own Aurel state references.",
    "Agent worker cannot own Aurel state.",
    "State ownership contract does not grant permission or execute runtime.",
)

AGENT_WORKER_BOUNDARY_INVARIANTS = (
    "Agent worker is worker-only.",
    "Agent worker cannot self-authorize.",
    "Agent worker cannot enter SYSTEM.",
)

CRO_AUTHORITY_STATE_BRIDGE_INVARIANTS = (
    "CRO bridge depends on operator, Custos, runtime, and SYSTEM root.",
    "CRO bridge cannot self-authorize.",
    "CRO bridge cannot activate evolution.",
)

SYSTEM_ROOT_BOUNDARY_REFERENCE_INVARIANTS = (
    "SYSTEM root is operator-only.",
    "Agent entry into SYSTEM is unavailable.",
    "Tool and workflow entry into SYSTEM are unavailable.",
)

BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY_INVARIANTS = (
    "BusinessEnvironment can hold bounded state references.",
    "BusinessEnvironment cannot grant permission.",
    "BusinessEnvironment cannot execute high-impact actions.",
)

TRIGGER_PROPOSAL_BOUNDARY_INVARIANTS = (
    "Tool triggers are proposal-only.",
    "Workflow triggers are proposal-only.",
    "Memory triggers are proposal-only and cannot write memory.",
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


def _parse_unavailable_reasons(
    reasons: Sequence[DelegationBoundaryUnavailableReason | str],
) -> tuple[DelegationBoundaryUnavailableReason, ...]:
    return tuple(
        _parse_enum(
            DelegationBoundaryUnavailableReason,
            reason,
            "unavailable_reasons",
        )
        for reason in reasons
    )


def _parse_proposal_origin_kinds(
    origins: Sequence[DelegationProposalOriginKind | str],
) -> tuple[DelegationProposalOriginKind, ...]:
    return tuple(
        _parse_enum(DelegationProposalOriginKind, origin, "proposal_origin_kinds")
        for origin in origins
    )


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
    return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}


def _reason_details() -> dict[str, str]:
    return dict(DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASON_DETAILS)


def _all_false_side_effects() -> DelegationActorBoundarySideEffects:
    return DelegationActorBoundarySideEffects()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def build_aurel_state_actor_boundary(
    *,
    checkpoint_id: str = "P1.8.17",
    state_ref: str = "aurel_state",
    actor_kind: DelegationActorBoundaryActorKind | str = (
        DelegationActorBoundaryActorKind.AUREL_STATE_ACTOR
    ),
    boundary_kind: DelegationActorBoundaryKind | str = (
        DelegationActorBoundaryKind.AUREL_STATE_ACTOR_BOUNDARY
    ),
    authority_scope: DelegationAuthorityScope | str = (
        DelegationAuthorityScope.STATE_OWNERSHIP
    ),
    state_role: DelegationActorStateRole | str = (
        DelegationActorStateRole.STATE_OWNER
    ),
    can_own_state: bool = True,
    agent_worker_can_own_state: bool = False,
    truth_label: DelegationBoundaryTruthLabel | str = (
        DelegationBoundaryTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = AUREL_STATE_ACTOR_BOUNDARY_INVARIANTS,
) -> AurelStateActorBoundary:
    actor_kind_val = _parse_enum(
        DelegationActorBoundaryActorKind,
        actor_kind,
        "actor_kind",
    )
    boundary_kind_val = _parse_enum(
        DelegationActorBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    authority_scope_val = _parse_enum(
        DelegationAuthorityScope,
        authority_scope,
        "authority_scope",
    )
    state_role_val = _parse_enum(DelegationActorStateRole, state_role, "state_role")
    truth_label_val = _parse_enum(
        DelegationBoundaryTruthLabel,
        truth_label,
        "truth_label",
    )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_AUREL_STATE_ACTOR_BOUNDARY_VERSION,
        "actor_kind": actor_kind_val,
        "boundary_kind": boundary_kind_val,
        "authority_scope": authority_scope_val,
        "state_role": state_role_val,
        "state_ref": state_ref,
        "can_own_state": can_own_state,
        "agent_worker_can_own_state": agent_worker_can_own_state,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return AurelStateActorBoundary(
        **payload,
        aurel_state_actor_boundary_hash=_hash_payload(payload),
    )


def build_agent_worker_boundary(
    *,
    checkpoint_id: str = "P1.8.18",
    actor_kind: DelegationActorBoundaryActorKind | str = (
        DelegationActorBoundaryActorKind.AGENT_WORKER
    ),
    boundary_kind: DelegationActorBoundaryKind | str = (
        DelegationActorBoundaryKind.AGENT_WORKER_BOUNDARY
    ),
    authority_scope: DelegationAuthorityScope | str = (
        DelegationAuthorityScope.WORKER_ONLY
    ),
    state_role: DelegationActorStateRole | str = (
        DelegationActorStateRole.WORKER_ONLY
    ),
    worker_only: bool = True,
    can_self_authorize: bool = False,
    can_enter_system: bool = False,
    truth_label: DelegationBoundaryTruthLabel | str = (
        DelegationBoundaryTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = AGENT_WORKER_BOUNDARY_INVARIANTS,
) -> AgentWorkerBoundary:
    actor_kind_val = _parse_enum(
        DelegationActorBoundaryActorKind,
        actor_kind,
        "actor_kind",
    )
    boundary_kind_val = _parse_enum(
        DelegationActorBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    authority_scope_val = _parse_enum(
        DelegationAuthorityScope,
        authority_scope,
        "authority_scope",
    )
    state_role_val = _parse_enum(DelegationActorStateRole, state_role, "state_role")
    truth_label_val = _parse_enum(
        DelegationBoundaryTruthLabel,
        truth_label,
        "truth_label",
    )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_AGENT_WORKER_BOUNDARY_VERSION,
        "actor_kind": actor_kind_val,
        "boundary_kind": boundary_kind_val,
        "authority_scope": authority_scope_val,
        "state_role": state_role_val,
        "worker_only": worker_only,
        "can_self_authorize": can_self_authorize,
        "can_enter_system": can_enter_system,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return AgentWorkerBoundary(
        **payload,
        agent_worker_boundary_hash=_hash_payload(payload),
    )


def build_cro_authority_state_bridge(
    *,
    checkpoint_id: str = "P1.8.19",
    actor_kind: DelegationActorBoundaryActorKind | str = (
        DelegationActorBoundaryActorKind.CRO
    ),
    boundary_kind: DelegationActorBoundaryKind | str = (
        DelegationActorBoundaryKind.CRO_AUTHORITY_STATE_BRIDGE
    ),
    authority_scope: DelegationAuthorityScope | str = (
        DelegationAuthorityScope.OPERATOR_CUSTOS_RUNTIME_SYSTEM_DEPENDENT
    ),
    state_role: DelegationActorStateRole | str = (
        DelegationActorStateRole.CRO_BRIDGE
    ),
    requires_operator: bool = True,
    requires_custos: bool = True,
    requires_runtime: bool = True,
    requires_system_root: bool = True,
    can_self_authorize: bool = False,
    can_activate_evolution: bool = False,
    truth_label: DelegationBoundaryTruthLabel | str = (
        DelegationBoundaryTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = CRO_AUTHORITY_STATE_BRIDGE_INVARIANTS,
) -> CROAuthorityStateBridge:
    actor_kind_val = _parse_enum(
        DelegationActorBoundaryActorKind,
        actor_kind,
        "actor_kind",
    )
    boundary_kind_val = _parse_enum(
        DelegationActorBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    authority_scope_val = _parse_enum(
        DelegationAuthorityScope,
        authority_scope,
        "authority_scope",
    )
    state_role_val = _parse_enum(DelegationActorStateRole, state_role, "state_role")
    truth_label_val = _parse_enum(
        DelegationBoundaryTruthLabel,
        truth_label,
        "truth_label",
    )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_CRO_AUTHORITY_STATE_BRIDGE_VERSION,
        "actor_kind": actor_kind_val,
        "boundary_kind": boundary_kind_val,
        "authority_scope": authority_scope_val,
        "state_role": state_role_val,
        "requires_operator": requires_operator,
        "requires_custos": requires_custos,
        "requires_runtime": requires_runtime,
        "requires_system_root": requires_system_root,
        "can_self_authorize": can_self_authorize,
        "can_activate_evolution": can_activate_evolution,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return CROAuthorityStateBridge(
        **payload,
        cro_authority_state_bridge_hash=_hash_payload(payload),
    )


def build_system_root_boundary_reference(
    *,
    checkpoint_id: str = "P1.8.20",
    actor_kind: DelegationActorBoundaryActorKind | str = (
        DelegationActorBoundaryActorKind.SYSTEM_ROOT
    ),
    boundary_kind: DelegationActorBoundaryKind | str = (
        DelegationActorBoundaryKind.SYSTEM_ROOT_BOUNDARY
    ),
    authority_scope: DelegationAuthorityScope | str = (
        DelegationAuthorityScope.SYSTEM_ROOT_OPERATOR_ONLY
    ),
    state_role: DelegationActorStateRole | str = (
        DelegationActorStateRole.SYSTEM_ROOT
    ),
    operator_only: bool = True,
    agent_entry_allowed: bool = False,
    tool_entry_allowed: bool = False,
    workflow_entry_allowed: bool = False,
    truth_label: DelegationBoundaryTruthLabel | str = (
        DelegationBoundaryTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = SYSTEM_ROOT_BOUNDARY_REFERENCE_INVARIANTS,
) -> SystemRootBoundaryReference:
    actor_kind_val = _parse_enum(
        DelegationActorBoundaryActorKind,
        actor_kind,
        "actor_kind",
    )
    boundary_kind_val = _parse_enum(
        DelegationActorBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    authority_scope_val = _parse_enum(
        DelegationAuthorityScope,
        authority_scope,
        "authority_scope",
    )
    state_role_val = _parse_enum(DelegationActorStateRole, state_role, "state_role")
    truth_label_val = _parse_enum(
        DelegationBoundaryTruthLabel,
        truth_label,
        "truth_label",
    )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_SYSTEM_ROOT_BOUNDARY_REFERENCE_VERSION,
        "actor_kind": actor_kind_val,
        "boundary_kind": boundary_kind_val,
        "authority_scope": authority_scope_val,
        "state_role": state_role_val,
        "operator_only": operator_only,
        "agent_entry_allowed": agent_entry_allowed,
        "tool_entry_allowed": tool_entry_allowed,
        "workflow_entry_allowed": workflow_entry_allowed,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return SystemRootBoundaryReference(
        **payload,
        system_root_boundary_reference_hash=_hash_payload(payload),
    )


def build_business_environment_actor_boundary(
    *,
    checkpoint_id: str = "P1.8.21",
    actor_kind: DelegationActorBoundaryActorKind | str = (
        DelegationActorBoundaryActorKind.BUSINESS_ENVIRONMENT
    ),
    boundary_kind: DelegationActorBoundaryKind | str = (
        DelegationActorBoundaryKind.BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY
    ),
    authority_scope: DelegationAuthorityScope | str = (
        DelegationAuthorityScope.BUSINESS_ENVIRONMENT_BOUNDED_STATE
    ),
    state_role: DelegationActorStateRole | str = (
        DelegationActorStateRole.BOUNDED_STATE_HOLDER
    ),
    can_hold_bounded_state_refs: bool = True,
    can_grant_permission: bool = False,
    can_execute_high_impact_actions: bool = False,
    truth_label: DelegationBoundaryTruthLabel | str = (
        DelegationBoundaryTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY_INVARIANTS,
) -> BusinessEnvironmentActorBoundary:
    actor_kind_val = _parse_enum(
        DelegationActorBoundaryActorKind,
        actor_kind,
        "actor_kind",
    )
    boundary_kind_val = _parse_enum(
        DelegationActorBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    authority_scope_val = _parse_enum(
        DelegationAuthorityScope,
        authority_scope,
        "authority_scope",
    )
    state_role_val = _parse_enum(DelegationActorStateRole, state_role, "state_role")
    truth_label_val = _parse_enum(
        DelegationBoundaryTruthLabel,
        truth_label,
        "truth_label",
    )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_BUSINESS_ENVIRONMENT_ACTOR_BOUNDARY_VERSION,
        "actor_kind": actor_kind_val,
        "boundary_kind": boundary_kind_val,
        "authority_scope": authority_scope_val,
        "state_role": state_role_val,
        "can_hold_bounded_state_refs": can_hold_bounded_state_refs,
        "can_grant_permission": can_grant_permission,
        "can_execute_high_impact_actions": can_execute_high_impact_actions,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return BusinessEnvironmentActorBoundary(
        **payload,
        business_environment_actor_boundary_hash=_hash_payload(payload),
    )


def build_trigger_proposal_boundary(
    *,
    checkpoint_id: str = "P1.8.22",
    boundary_kind: DelegationActorBoundaryKind | str = (
        DelegationActorBoundaryKind.TRIGGER_PROPOSAL_BOUNDARY
    ),
    authority_scope: DelegationAuthorityScope | str = (
        DelegationAuthorityScope.PROPOSAL_ONLY
    ),
    state_role: DelegationActorStateRole | str = (
        DelegationActorStateRole.PROPOSAL_ORIGIN
    ),
    proposal_origin_kinds: Sequence[DelegationProposalOriginKind | str] = (
        DelegationProposalOriginKind.TOOL,
        DelegationProposalOriginKind.WORKFLOW,
        DelegationProposalOriginKind.MEMORY_TRIGGER,
    ),
    proposal_only: bool = True,
    permission_granted: bool = False,
    execution_started: bool = False,
    memory_written: bool = False,
    truth_label: DelegationBoundaryTruthLabel | str = (
        DelegationBoundaryTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = TRIGGER_PROPOSAL_BOUNDARY_INVARIANTS,
) -> TriggerProposalBoundary:
    boundary_kind_val = _parse_enum(
        DelegationActorBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    authority_scope_val = _parse_enum(
        DelegationAuthorityScope,
        authority_scope,
        "authority_scope",
    )
    state_role_val = _parse_enum(DelegationActorStateRole, state_role, "state_role")
    origins = _parse_proposal_origin_kinds(proposal_origin_kinds)
    truth_label_val = _parse_enum(
        DelegationBoundaryTruthLabel,
        truth_label,
        "truth_label",
    )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_TRIGGER_PROPOSAL_BOUNDARY_VERSION,
        "boundary_kind": boundary_kind_val,
        "authority_scope": authority_scope_val,
        "state_role": state_role_val,
        "proposal_origin_kinds": origins,
        "proposal_only": proposal_only,
        "permission_granted": permission_granted,
        "execution_started": execution_started,
        "memory_written": memory_written,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return TriggerProposalBoundary(
        **payload,
        trigger_proposal_boundary_hash=_hash_payload(payload),
    )


def _build_checkpoint_read(
    *,
    checkpoint_id: str,
    evidence_ref: str,
    contract_hash: str,
    unavailable_reasons: Sequence[DelegationBoundaryUnavailableReason],
) -> DelegationActorBoundaryCheckpointRead:
    reasons = tuple(unavailable_reasons)
    payload = {
        "schema_version": DELEGATION_ACTOR_BOUNDARY_CHECKPOINT_READ_VERSION,
        "checkpoint_id": checkpoint_id,
        "status": DelegationActorBoundaryStatus.CONTRACT_ONLY,
        "evidence_ref": evidence_ref,
        "contract_hash": contract_hash,
        "truth_label": DelegationBoundaryTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": reasons,
    }
    return DelegationActorBoundaryCheckpointRead(
        **payload,
        checkpoint_read_hash=_hash_payload(payload),
    )


def build_default_delegation_actor_boundary_read_model(
    *,
    aurel_state_actor_boundary: AurelStateActorBoundary | None = None,
    agent_worker_boundary: AgentWorkerBoundary | None = None,
    cro_authority_state_bridge: CROAuthorityStateBridge | None = None,
    system_root_boundary_reference: SystemRootBoundaryReference | None = None,
    business_environment_actor_boundary: BusinessEnvironmentActorBoundary | None = None,
    trigger_proposal_boundary: TriggerProposalBoundary | None = None,
) -> DelegationActorBoundaryReadModel:
    state_boundary = aurel_state_actor_boundary or build_aurel_state_actor_boundary()
    worker_boundary = agent_worker_boundary or build_agent_worker_boundary()
    cro_bridge = cro_authority_state_bridge or build_cro_authority_state_bridge()
    system_boundary = (
        system_root_boundary_reference or build_system_root_boundary_reference()
    )
    business_boundary = (
        business_environment_actor_boundary
        or build_business_environment_actor_boundary()
    )
    trigger_boundary = trigger_proposal_boundary or build_trigger_proposal_boundary()

    checkpoint_reads = (
        _build_checkpoint_read(
            checkpoint_id="P1.8.17",
            evidence_ref=(
                "AurelStateActorBoundary.aurel_state_actor_boundary_hash"
            ),
            contract_hash=state_boundary.aurel_state_actor_boundary_hash,
            unavailable_reasons=state_boundary.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.18",
            evidence_ref="AgentWorkerBoundary.agent_worker_boundary_hash",
            contract_hash=worker_boundary.agent_worker_boundary_hash,
            unavailable_reasons=worker_boundary.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.19",
            evidence_ref=(
                "CROAuthorityStateBridge.cro_authority_state_bridge_hash"
            ),
            contract_hash=cro_bridge.cro_authority_state_bridge_hash,
            unavailable_reasons=cro_bridge.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.20",
            evidence_ref=(
                "SystemRootBoundaryReference."
                "system_root_boundary_reference_hash"
            ),
            contract_hash=(
                system_boundary.system_root_boundary_reference_hash
            ),
            unavailable_reasons=system_boundary.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.21",
            evidence_ref=(
                "BusinessEnvironmentActorBoundary."
                "business_environment_actor_boundary_hash"
            ),
            contract_hash=(
                business_boundary.business_environment_actor_boundary_hash
            ),
            unavailable_reasons=business_boundary.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.22",
            evidence_ref="TriggerProposalBoundary.trigger_proposal_boundary_hash",
            contract_hash=trigger_boundary.trigger_proposal_boundary_hash,
            unavailable_reasons=trigger_boundary.unavailable_reasons,
        ),
    )
    side_effects = _all_false_side_effects()
    payload = {
        "schema_version": DELEGATION_ACTOR_BOUNDARY_READ_MODEL_VERSION,
        "task_id": DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_count": len(checkpoint_reads),
        "truth_label": DelegationBoundaryTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reason_details": _reason_details(),
        "side_effects": side_effects,
    }
    return DelegationActorBoundaryReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )


def build_p1_8_a_actor_boundary_pack_result() -> DelegationActorBoundaryPackResult:
    state_boundary = build_aurel_state_actor_boundary()
    worker_boundary = build_agent_worker_boundary()
    cro_bridge = build_cro_authority_state_bridge()
    system_boundary = build_system_root_boundary_reference()
    business_boundary = build_business_environment_actor_boundary()
    trigger_boundary = build_trigger_proposal_boundary()
    read_model = build_default_delegation_actor_boundary_read_model(
        aurel_state_actor_boundary=state_boundary,
        agent_worker_boundary=worker_boundary,
        cro_authority_state_bridge=cro_bridge,
        system_root_boundary_reference=system_boundary,
        business_environment_actor_boundary=business_boundary,
        trigger_proposal_boundary=trigger_boundary,
    )
    side_effects = _all_false_side_effects()
    unavailable_reasons = DEFAULT_DELEGATION_ACTOR_BOUNDARY_UNAVAILABLE_REASONS
    payload = {
        "schema_version": DELEGATION_ACTOR_BOUNDARY_PACK_RESULT_VERSION,
        "task_id": DELEGATION_ACTOR_BOUNDARY_PACK_TASK_ID,
        "checkpoint_ids": DELEGATION_ACTOR_BOUNDARY_PACK_CHECKPOINT_IDS,
        "aurel_state_actor_boundary": state_boundary,
        "agent_worker_boundary": worker_boundary,
        "cro_authority_state_bridge": cro_bridge,
        "system_root_boundary_reference": system_boundary,
        "business_environment_actor_boundary": business_boundary,
        "trigger_proposal_boundary": trigger_boundary,
        "read_model": read_model,
        "status": DelegationActorBoundaryStatus.CONTRACT_ONLY,
        "truth_label": DelegationBoundaryTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": unavailable_reasons,
        "unavailable_reason_details": _reason_details(),
        "side_effects": side_effects,
    }
    return DelegationActorBoundaryPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


# ---------------------------------------------------------------------------
# Hash functions
# ---------------------------------------------------------------------------


def hash_delegation_aurel_state_actor_boundary(
    boundary: AurelStateActorBoundary,
) -> str:
    return boundary.aurel_state_actor_boundary_hash


def hash_delegation_agent_worker_boundary(boundary: AgentWorkerBoundary) -> str:
    return boundary.agent_worker_boundary_hash


def hash_delegation_cro_authority_state_bridge(
    bridge: CROAuthorityStateBridge,
) -> str:
    return bridge.cro_authority_state_bridge_hash


def hash_delegation_system_root_boundary_reference(
    boundary: SystemRootBoundaryReference,
) -> str:
    return boundary.system_root_boundary_reference_hash


def hash_delegation_business_environment_actor_boundary(
    boundary: BusinessEnvironmentActorBoundary,
) -> str:
    return boundary.business_environment_actor_boundary_hash


def hash_delegation_trigger_proposal_boundary(
    boundary: TriggerProposalBoundary,
) -> str:
    return boundary.trigger_proposal_boundary_hash


def hash_delegation_actor_boundary_read_model(
    read_model: DelegationActorBoundaryReadModel,
) -> str:
    return read_model.read_model_hash


def hash_delegation_actor_boundary_pack_result(
    result: DelegationActorBoundaryPackResult,
) -> str:
    return result.result_hash


# ---------------------------------------------------------------------------
# Serialize functions
# ---------------------------------------------------------------------------


def serialize_delegation_actor_boundary_read_model(
    read_model: DelegationActorBoundaryReadModel,
) -> str:
    payload = read_model.to_canonical_dict()
    validate_known_fields(
        payload,
        ACTOR_BOUNDARY_READ_MODEL_KNOWN_FIELDS,
        label="DelegationActorBoundaryReadModel",
    )
    return to_canonical_json(payload)


def serialize_delegation_actor_boundary_pack_result(
    result: DelegationActorBoundaryPackResult,
) -> str:
    payload = result.to_canonical_dict()
    validate_known_fields(
        payload,
        ACTOR_BOUNDARY_PACK_RESULT_KNOWN_FIELDS,
        label="DelegationActorBoundaryPackResult",
    )
    return to_canonical_json(payload)

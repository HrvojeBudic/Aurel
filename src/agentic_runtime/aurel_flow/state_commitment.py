"""P3-FLOW-B mediated internal state commitment (P3.4.x, mediation half).

Actor/runtime outputs can never mutate shared workflow state directly: they
become MediatedActorOutput objects, and any internal state change must pass
through a RuntimeStateCommitment. COMMITTED_INTERNAL means internal AurelFlow
state only — it is not a Ledger commit, grants no authority, and produces no
external side effect. Constructing any of these objects with an authority /
mutation / side-effect boolean set True fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

MEDIATED_ACTOR_OUTPUT_VERSION = "mediated_actor_output.v1"
RUNTIME_STATE_COMMITMENT_VERSION = "runtime_state_commitment.v1"
MUTATION_SCOPE_INTERNAL = "INTERNAL_AUREL_FLOW"


class RuntimeSymbolState(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    COMMITTED_INTERNAL = "COMMITTED_INTERNAL"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class MediatedActorOutput(_CanonicalMixin):
    """Actor/runtime output wrapper. Direct shared-state mutation is forbidden."""

    output_id: str
    contract_version: str
    actor_id: str
    target_run_id: str
    target_node_id: str
    output_kind: str
    proposed_symbol_or_state_ref: str
    validation_status: RuntimeSymbolState
    truth_label: FlowTruthLabel
    reason: str
    metadata: Mapping[str, str] = field(default_factory=dict)
    direct_state_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        if self.direct_state_mutation_allowed:
            raise AurelFlowValidationError(
                "MediatedActorOutput.direct_state_mutation_allowed must remain False; "
                "actor outputs cannot mutate shared workflow state directly",
                code=AurelFlowErrorCode.DIRECT_STATE_MUTATION_FORBIDDEN,
                field="direct_state_mutation_allowed",
            )


@dataclass(frozen=True)
class RuntimeStateCommitment(_CanonicalMixin):
    """Mediated internal runtime state commitment. Not a Ledger commit."""

    commitment_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    source_event_id: str
    source_actor_id: str
    mediated_output_id: str
    symbol_or_state_ref: str
    previous_state_ref: str
    proposed_state_ref: str
    commit_status: RuntimeSymbolState
    validation_status: RuntimeSymbolState
    state_mutated: bool
    mutation_scope: str
    truth_label: FlowTruthLabel
    reason: str
    metadata: Mapping[str, str] = field(default_factory=dict)
    authority_granted: bool = False
    ledger_written: bool = False
    external_side_effect: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("authority_granted", "ledger_written", "external_side_effect"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RuntimeStateCommitment.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )
        if self.mutation_scope != MUTATION_SCOPE_INTERNAL:
            raise AurelFlowValidationError(
                f"mutation_scope must be {MUTATION_SCOPE_INTERNAL!r}; external scopes are "
                "forbidden in P3-FLOW-B",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="mutation_scope",
            )


@dataclass(frozen=True)
class RuntimeStateCommitmentResult(_CanonicalMixin):
    """Accepted/rejected commitment result. Internal-only, never Ledger."""

    result_id: str
    accepted: bool
    commitment: RuntimeStateCommitment
    reason: str
    internal_only: bool = True
    ledger_written: bool = False
    external_side_effect: bool = False


def create_mediated_actor_output(
    *,
    actor_id: str,
    target_run_id: str,
    proposed_symbol_or_state_ref: str,
    target_node_id: str = "",
    output_kind: str = "STATE_PROPOSAL",
    validation_status: RuntimeSymbolState = RuntimeSymbolState.PROPOSED,
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
    reason: str = "",
    metadata: Mapping[str, str] | None = None,
) -> MediatedActorOutput:
    if not actor_id:
        raise AurelFlowValidationError(
            "actor_id must be non-empty",
            code=AurelFlowErrorCode.EMPTY_ACTOR_ID,
            field="actor_id",
        )
    output_id = "maout-" + stable_hash(
        {
            "actor_id": actor_id,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "output_kind": output_kind,
            "ref": proposed_symbol_or_state_ref,
        }
    )[:16]
    return MediatedActorOutput(
        output_id=output_id,
        contract_version=MEDIATED_ACTOR_OUTPUT_VERSION,
        actor_id=actor_id,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        output_kind=output_kind,
        proposed_symbol_or_state_ref=proposed_symbol_or_state_ref,
        validation_status=validation_status,
        truth_label=truth_label,
        reason=reason,
        metadata=dict(metadata or {}),
    )


def create_runtime_state_commitment(
    output: MediatedActorOutput,
    *,
    previous_state_ref: str,
    proposed_state_ref: str,
    source_event_id: str = "",
    reason: str = "",
    metadata: Mapping[str, str] | None = None,
) -> RuntimeStateCommitment:
    """Create a PROPOSED commitment from a mediated output. Nothing commits yet."""

    commitment_id = "rtsc-" + stable_hash(
        {
            "mediated_output_id": output.output_id,
            "previous_state_ref": previous_state_ref,
            "proposed_state_ref": proposed_state_ref,
        }
    )[:16]
    return RuntimeStateCommitment(
        commitment_id=commitment_id,
        contract_version=RUNTIME_STATE_COMMITMENT_VERSION,
        target_run_id=output.target_run_id,
        target_node_id=output.target_node_id,
        source_event_id=source_event_id,
        source_actor_id=output.actor_id,
        mediated_output_id=output.output_id,
        symbol_or_state_ref=output.proposed_symbol_or_state_ref,
        previous_state_ref=previous_state_ref,
        proposed_state_ref=proposed_state_ref,
        commit_status=RuntimeSymbolState.PROPOSED,
        validation_status=output.validation_status,
        state_mutated=False,
        mutation_scope=MUTATION_SCOPE_INTERNAL,
        truth_label=output.truth_label,
        reason=reason or output.reason,
        metadata=dict(metadata or {}),
    )


_COMMITTABLE_STATUSES = (RuntimeSymbolState.PROPOSED, RuntimeSymbolState.VALIDATED)
_COMMITTABLE_VALIDATION = (
    RuntimeSymbolState.PROPOSED,
    RuntimeSymbolState.VALIDATED,
)


def commit_internal_runtime_state(
    commitment: RuntimeStateCommitment,
) -> RuntimeStateCommitmentResult:
    """Commit internal AurelFlow state only. No Ledger, no external effect.

    Only PROPOSED/VALIDATED commitments with non-rejected validation commit;
    everything else is rejected with an explicit reason.
    """

    result_id = "rtscr-" + stable_hash({"commitment_id": commitment.commitment_id})[:16]
    if commitment.commit_status not in _COMMITTABLE_STATUSES:
        return RuntimeStateCommitmentResult(
            result_id=result_id,
            accepted=False,
            commitment=replace(commitment, commit_status=RuntimeSymbolState.REJECTED),
            reason=(
                f"commit_status {commitment.commit_status.value!r} is not committable; "
                "only PROPOSED or VALIDATED commitments can commit internally"
            ),
        )
    if commitment.validation_status not in _COMMITTABLE_VALIDATION:
        return RuntimeStateCommitmentResult(
            result_id=result_id,
            accepted=False,
            commitment=replace(commitment, commit_status=RuntimeSymbolState.REJECTED),
            reason=(
                f"validation_status {commitment.validation_status.value!r} blocks internal "
                "commit; mediated output was not validated"
            ),
        )
    committed = replace(
        commitment,
        commit_status=RuntimeSymbolState.COMMITTED_INTERNAL,
        state_mutated=True,
        mutation_scope=MUTATION_SCOPE_INTERNAL,
    )
    return RuntimeStateCommitmentResult(
        result_id=result_id,
        accepted=True,
        commitment=committed,
        reason=(
            "COMMITTED_INTERNAL: internal AurelFlow state only — not a Ledger commit, "
            "no authority granted, no external side effect"
        ),
    )

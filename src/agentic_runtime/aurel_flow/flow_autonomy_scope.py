"""P3-FLOW-H autonomy scope envelopes (P3.16).

A scope envelope limits what an autonomy mode may cover; it never
authorizes, never permits, and never executes. Every external-side-effect
capability boolean is structurally False: memory, policy, identity, tool,
network, and sandbox actions stay unavailable in P3.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_autonomy import (
    AUTONOMY_AUTHORITY_UNAVAILABLE_REASON,
    GovernedAutonomyLevel,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUTONOMY_SCOPE_ENVELOPE_VERSION = "autonomy_scope_envelope.v1"
AUTONOMY_SCOPE_LIMIT_VERSION = "autonomy_scope_limit.v1"


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


class AutonomyScopeDimension(str, Enum):
    """Closed-world dimensions a scope envelope may bound."""

    RUN_SCOPE = "RUN_SCOPE"
    WORKFLOW_SCOPE = "WORKFLOW_SCOPE"
    NODE_SCOPE = "NODE_SCOPE"
    TOOL_SCOPE = "TOOL_SCOPE"
    DATA_SCOPE = "DATA_SCOPE"
    MEMORY_SCOPE = "MEMORY_SCOPE"
    NETWORK_SCOPE = "NETWORK_SCOPE"
    SANDBOX_SCOPE = "SANDBOX_SCOPE"
    TIME_SCOPE = "TIME_SCOPE"
    COST_SCOPE = "COST_SCOPE"
    LATENCY_SCOPE = "LATENCY_SCOPE"
    REVERSIBILITY_SCOPE = "REVERSIBILITY_SCOPE"
    RISK_SCOPE = "RISK_SCOPE"
    TENANT_SCOPE = "TENANT_SCOPE"
    OPERATOR_SCOPE = "OPERATOR_SCOPE"
    TRACE_SCOPE = "TRACE_SCOPE"


@dataclass(frozen=True)
class AutonomyScopeLimit(_CanonicalMixin):
    """One bounded dimension. A limit restricts; it never authorizes."""

    limit_id: str
    limit_version: str
    dimension: AutonomyScopeDimension
    limit_description: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    limit_authorizes_action: bool = False
    limit_executes_action: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "limit_authorizes_action", "limit_executes_action")


def create_autonomy_scope_limit(
    *, dimension: AutonomyScopeDimension, limit_description: str
) -> AutonomyScopeLimit:
    payload = {
        "limit_version": AUTONOMY_SCOPE_LIMIT_VERSION,
        "dimension": dimension.value,
        "limit_description": limit_description,
    }
    return AutonomyScopeLimit(
        limit_id="flasl-" + stable_hash(payload)[:16],
        limit_version=AUTONOMY_SCOPE_LIMIT_VERSION,
        dimension=dimension,
        limit_description=limit_description,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class AutonomyScopeEnvelope(_CanonicalMixin):
    """The bounded coverage of an autonomy mode. Scope is not permission."""

    envelope_id: str
    contract_version: str
    run_id: str
    level: GovernedAutonomyLevel
    limits: tuple[AutonomyScopeLimit, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    scope_authorizes_action: bool = False
    scope_executes_action: bool = False
    external_side_effects_allowed: bool = False
    memory_write_allowed: bool = False
    policy_change_allowed: bool = False
    identity_change_allowed: bool = False
    network_call_allowed: bool = False
    tool_execution_allowed: bool = False
    sandbox_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "scope_authorizes_action",
            "scope_executes_action",
            "external_side_effects_allowed",
            "memory_write_allowed",
            "policy_change_allowed",
            "identity_change_allowed",
            "network_call_allowed",
            "tool_execution_allowed",
            "sandbox_execution_allowed",
        )
        dimensions = [limit.dimension for limit in self.limits]
        if len(dimensions) != len(set(dimensions)):
            raise AurelFlowValidationError(
                "a scope envelope must bound each dimension at most once",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="limits",
            )

    def covers(self, dimension: AutonomyScopeDimension) -> bool:
        """True when the envelope explicitly bounds the dimension."""

        return any(limit.dimension is dimension for limit in self.limits)


def build_autonomy_scope_envelope(
    *,
    run_id: str,
    level: GovernedAutonomyLevel,
    limits: tuple[AutonomyScopeLimit, ...],
) -> AutonomyScopeEnvelope:
    payload = {
        "contract_version": AUTONOMY_SCOPE_ENVELOPE_VERSION,
        "run_id": run_id,
        "level": level.value,
        "limit_ids": tuple(limit.limit_id for limit in limits),
    }
    return AutonomyScopeEnvelope(
        envelope_id="flase-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_SCOPE_ENVELOPE_VERSION,
        run_id=run_id,
        level=level,
        limits=limits,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )

"""P3-FLOW-H governed autonomy projection (P3.16).

Read-only projection of autonomy mode, scope, resolver posture, gate
decisions, and violations for a future React/AurelShell surface. React is
projection only: no UI autonomy toggle, override, or execution authority
exists or can be represented as granted, and no API server or frontend is
implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_autonomy import (
    AutonomyDecisionClass,
    OperatorSelectedAutonomyMode,
    resolve_permission_state,
)
from .flow_autonomy_gates import AutonomyGateResult, AutonomyViolationSignal
from .flow_autonomy_scope import AutonomyScopeEnvelope
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

GOVERNED_AUTONOMY_PROJECTION_VERSION = "governed_autonomy_projection.v1"

AUTONOMY_PROJECTION_UNAVAILABLE_REASON = (
    "no React component, frontend route, frontend state, API server, REST, "
    "or WebSocket exists in P3-FLOW-H; this projection is a read-only view "
    "contract, and no UI can toggle autonomy, override modes, or execute "
    "anything through it"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


@dataclass(frozen=True)
class GovernedAutonomyProjection(_CanonicalMixin):
    """Everything a future surface may render about governed autonomy."""

    projection_id: str
    projection_version: str
    run_id: str
    level_value: str
    mode_source_value: str
    scope_dimension_count: int
    resolver_permission_state_counts: Mapping[str, int]
    gate_decision_values: tuple[str, ...]
    violation_count: int
    attempted_self_upgrade_present: bool
    escalation_or_review_needed: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = AUTONOMY_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_autonomy_toggle_authority: bool = False
    ui_override_authority: bool = False
    ui_execution_allowed: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(
            self,
            "frontend_mutation_allowed",
            "ui_autonomy_toggle_authority",
            "ui_override_authority",
            "ui_execution_allowed",
            "api_server_implemented",
            "frontend_implemented",
        )


def build_governed_autonomy_projection(
    mode: OperatorSelectedAutonomyMode,
    *,
    scope: AutonomyScopeEnvelope | None = None,
    gate_results: tuple[AutonomyGateResult, ...] = (),
    violations: tuple[AutonomyViolationSignal, ...] = (),
) -> GovernedAutonomyProjection:
    """Project mode/scope/resolver/gate/violation state, read-only.

    The resolver summary is computed live by resolving every known decision
    class at the mode's level — the projection shows resolver truth, it
    never re-derives its own permission rules.
    """

    for source_name, source_run_id in (
        ("scope", scope.run_id if scope else None),
        *(("gate_results", result.run_id) for result in gate_results),
        *(("violations", violation.run_id) for violation in violations),
    ):
        if source_run_id is not None and source_run_id != mode.run_id:
            raise AurelFlowValidationError(
                f"{source_name} run {source_run_id!r} does not match mode "
                f"run {mode.run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field=source_name,
            )
    permission_state_counts: dict[str, int] = {}
    for decision_class in AutonomyDecisionClass:
        resolution = resolve_permission_state(mode.level, decision_class)
        state_value = resolution.permission_state.value
        permission_state_counts[state_value] = (
            permission_state_counts.get(state_value, 0) + 1
        )
    payload = {
        "projection_version": GOVERNED_AUTONOMY_PROJECTION_VERSION,
        "mode_id": mode.mode_id,
        "scope_envelope_id": scope.envelope_id if scope else "",
        "gate_ids": tuple(result.gate_id for result in gate_results),
        "violation_ids": tuple(
            violation.violation_id for violation in violations
        ),
    }
    return GovernedAutonomyProjection(
        projection_id="flapj-" + stable_hash(payload)[:16],
        projection_version=GOVERNED_AUTONOMY_PROJECTION_VERSION,
        run_id=mode.run_id,
        level_value=mode.level.value,
        mode_source_value=mode.mode_source.value,
        scope_dimension_count=len(scope.limits) if scope else 0,
        resolver_permission_state_counts=permission_state_counts,
        gate_decision_values=tuple(
            result.decision.value for result in gate_results
        ),
        violation_count=len(violations),
        attempted_self_upgrade_present=any(
            violation.attempted_self_upgrade for violation in violations
        ),
        escalation_or_review_needed=bool(violations)
        or any(result.requires_operator_review for result in gate_results),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )

"""P3-FLOW-H governed autonomy levels / total decision resolver (P3.16).

Autonomy is a governed boundary, not autonomous hands. The closed-world
GovernedAutonomyLevel vocabulary is operator-selected (never self-selected,
never self-upgraded), A9 heretic live mode is locked unavailable in P3, and
``resolve_permission_state`` is a total deterministic resolver over every
(level, decision class) pair — rules and hard safety overrides, not a manual
Cartesian table. Nothing here grants authority, permission, execution, or
proof: P4 executes, P5 proves, P9 authorizes. This vocabulary is distinct
from the P3-FLOW-C visibility projection ``FlowAutonomyLevel`` in
``flow_wiring.py``, which only displays autonomy posture.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUREL_FLOW_H_PACK_ID = "P3-FLOW-H"
AUREL_FLOW_H_PACK_TITLE = "Governed Autonomy Levels / Scope Envelopes Pack"
AUREL_FLOW_H_REPORT_PATH = (
    "agent/reports/P3_FLOW_H_GOVERNED_AUTONOMY_SCOPE_PACK.md"
)

OPERATOR_SELECTED_AUTONOMY_MODE_VERSION = "operator_selected_autonomy_mode.v1"
AUTONOMY_RESOLUTION_VERSION = "autonomy_resolution.v1"
AUTONOMY_ACTION_BOUNDARY_VERSION = "autonomy_action_boundary.v1"

AUTONOMY_AUTHORITY_UNAVAILABLE_REASON = (
    "an autonomy level bounds what AurelFlow may represent; it grants no "
    "authority, permission, execution, or proof — P4 executes, P5 proves, "
    "P9 authorizes"
)
HERETIC_LIVE_LOCKED_REASON = (
    "A9 heretic live mode is locked unavailable in P3; no autonomy level "
    "unlocks live execution before P4/P5/P9 exist"
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


class GovernedAutonomyLevel(str, Enum):
    """Closed-world governed autonomy vocabulary. A level is not authority."""

    A0_OBSERVE_ONLY = "A0_OBSERVE_ONLY"
    A1_SUGGEST_ONLY = "A1_SUGGEST_ONLY"
    A2_PREPARE_CANDIDATES = "A2_PREPARE_CANDIDATES"
    A3_INTERNAL_LOW_RISK_AUTO = "A3_INTERNAL_LOW_RISK_AUTO"
    A4_INTERNAL_BOUNDED_AUTO = "A4_INTERNAL_BOUNDED_AUTO"
    A5_OPERATOR_REVIEWED_EXTERNAL = "A5_OPERATOR_REVIEWED_EXTERNAL"
    A6_POLICY_GATED_EXTERNAL = "A6_POLICY_GATED_EXTERNAL"
    A7_HIGH_AUTONOMY_BOUNDED = "A7_HIGH_AUTONOMY_BOUNDED"
    A8_HERETIC_MODE_SIMULATED = "A8_HERETIC_MODE_SIMULATED"
    A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE = (
        "A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE"
    )
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


GOVERNED_AUTONOMY_TIER_ORDER: Mapping[GovernedAutonomyLevel, int] = {
    GovernedAutonomyLevel.A0_OBSERVE_ONLY: 0,
    GovernedAutonomyLevel.A1_SUGGEST_ONLY: 1,
    GovernedAutonomyLevel.A2_PREPARE_CANDIDATES: 2,
    GovernedAutonomyLevel.A3_INTERNAL_LOW_RISK_AUTO: 3,
    GovernedAutonomyLevel.A4_INTERNAL_BOUNDED_AUTO: 4,
    GovernedAutonomyLevel.A5_OPERATOR_REVIEWED_EXTERNAL: 5,
    GovernedAutonomyLevel.A6_POLICY_GATED_EXTERNAL: 6,
    GovernedAutonomyLevel.A7_HIGH_AUTONOMY_BOUNDED: 7,
    GovernedAutonomyLevel.A8_HERETIC_MODE_SIMULATED: 8,
}
# A9 is deliberately absent: it is locked, not the top of the ladder.
# UNAVAILABLE/ERROR are deliberately absent: they are hard-override inputs.


class AutonomyModeSource(str, Enum):
    """Where an autonomy mode came from. Aurel never self-selects."""

    OPERATOR_SELECTED = "OPERATOR_SELECTED"
    POLICY_DEFAULT = "POLICY_DEFAULT"
    TENANT_DEFAULT = "TENANT_DEFAULT"
    WORKFLOW_DEFAULT = "WORKFLOW_DEFAULT"
    SAFETY_DOWNGRADE = "SAFETY_DOWNGRADE"
    FAILURE_DRIVEN_DOWNGRADE = "FAILURE_DRIVEN_DOWNGRADE"
    BUDGET_DRIVEN_DOWNGRADE = "BUDGET_DRIVEN_DOWNGRADE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class OperatorSelectedAutonomyMode(_CanonicalMixin):
    """The current autonomy mode with an explicit source. Not self-selected."""

    mode_id: str
    contract_version: str
    run_id: str
    level: GovernedAutonomyLevel
    mode_source: AutonomyModeSource
    selected_by: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    self_selected: bool = False
    self_upgrade_allowed: bool = False
    authority_granted: bool = False
    permission_granted: bool = False
    execution_available: bool = False
    live_execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "self_selected",
            "self_upgrade_allowed",
            "authority_granted",
            "permission_granted",
            "execution_available",
            "live_execution_available",
        )
        if (
            self.mode_source is AutonomyModeSource.OPERATOR_SELECTED
            and not self.selected_by
        ):
            raise AurelFlowValidationError(
                "an operator-selected mode must name the selecting operator",
                code=AurelFlowErrorCode.EMPTY_ACTOR_ID,
                field="selected_by",
            )


def select_autonomy_mode(
    *,
    run_id: str,
    level: GovernedAutonomyLevel,
    mode_source: AutonomyModeSource,
    selected_by: str = "",
) -> OperatorSelectedAutonomyMode:
    payload = {
        "contract_version": OPERATOR_SELECTED_AUTONOMY_MODE_VERSION,
        "run_id": run_id,
        "level": level.value,
        "mode_source": mode_source.value,
        "selected_by": selected_by,
    }
    return OperatorSelectedAutonomyMode(
        mode_id="flaum-" + stable_hash(payload)[:16],
        contract_version=OPERATOR_SELECTED_AUTONOMY_MODE_VERSION,
        run_id=run_id,
        level=level,
        mode_source=mode_source,
        selected_by=selected_by,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


class AutonomyDecisionClass(str, Enum):
    """Closed-world decision/action classes the resolver understands."""

    OBSERVE_STATE = "OBSERVE_STATE"
    SUMMARIZE_STATE = "SUMMARIZE_STATE"
    SUGGEST_NEXT_STEP = "SUGGEST_NEXT_STEP"
    PREPARE_PLAN = "PREPARE_PLAN"
    PREPARE_RECOVERY_CANDIDATE = "PREPARE_RECOVERY_CANDIDATE"
    PREPARE_REPLAY_PLAN = "PREPARE_REPLAY_PLAN"
    PREPARE_GRAPH_REVISION = "PREPARE_GRAPH_REVISION"
    PREPARE_OPERATOR_REVIEW = "PREPARE_OPERATOR_REVIEW"
    MARK_INTERNAL_READ_MODEL = "MARK_INTERNAL_READ_MODEL"
    ADVANCE_INTERNAL_STATE_CANDIDATE = "ADVANCE_INTERNAL_STATE_CANDIDATE"
    AUTO_INTERNAL_STATE_TRANSITION_CANDIDATE = (
        "AUTO_INTERNAL_STATE_TRANSITION_CANDIDATE"
    )
    REQUEST_PERMISSION = "REQUEST_PERMISSION"
    REQUEST_EXECUTION = "REQUEST_EXECUTION"
    REQUEST_PROOF = "REQUEST_PROOF"
    REQUEST_AUTHORITY = "REQUEST_AUTHORITY"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"
    MEMORY_WRITE = "MEMORY_WRITE"
    POLICY_CHANGE = "POLICY_CHANGE"
    IDENTITY_CHANGE = "IDENTITY_CHANGE"
    NETWORK_CALL = "NETWORK_CALL"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    SANDBOX_EXECUTION = "SANDBOX_EXECUTION"
    ROLLBACK_EXECUTION = "ROLLBACK_EXECUTION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class AutonomyPermissionState(str, Enum):
    """What a (level, decision class) pair resolves to. Never live authority."""

    ALLOWED_READ_ONLY = "ALLOWED_READ_ONLY"
    ALLOWED_CANDIDATE_ONLY = "ALLOWED_CANDIDATE_ONLY"
    ALLOWED_INTERNAL_PROJECTION_ONLY = "ALLOWED_INTERNAL_PROJECTION_ONLY"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_P4_EXECUTION = "REQUIRES_P4_EXECUTION"
    REQUIRES_P5_PROOF = "REQUIRES_P5_PROOF"
    REQUIRES_P9_AUTHORITY = "REQUIRES_P9_AUTHORITY"
    FORBIDDEN_IN_P3 = "FORBIDDEN_IN_P3"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


ALLOWED_AUTONOMY_PERMISSION_STATES: frozenset[AutonomyPermissionState] = frozenset(
    {
        AutonomyPermissionState.ALLOWED_READ_ONLY,
        AutonomyPermissionState.ALLOWED_CANDIDATE_ONLY,
        AutonomyPermissionState.ALLOWED_INTERNAL_PROJECTION_ONLY,
    }
)

READ_ONLY_DECISION_CLASSES: frozenset[AutonomyDecisionClass] = frozenset(
    {
        AutonomyDecisionClass.OBSERVE_STATE,
        AutonomyDecisionClass.SUMMARIZE_STATE,
    }
)

SIDE_EFFECT_DECISION_CLASSES: frozenset[AutonomyDecisionClass] = frozenset(
    {
        AutonomyDecisionClass.EXTERNAL_SIDE_EFFECT,
        AutonomyDecisionClass.MEMORY_WRITE,
        AutonomyDecisionClass.POLICY_CHANGE,
        AutonomyDecisionClass.IDENTITY_CHANGE,
        AutonomyDecisionClass.NETWORK_CALL,
        AutonomyDecisionClass.TOOL_EXECUTION,
        AutonomyDecisionClass.SANDBOX_EXECUTION,
        AutonomyDecisionClass.ROLLBACK_EXECUTION,
    }
)

# Minimum tier at which a candidate-producing class becomes candidate-only
# allowed. Below the tier the class requires operator review instead.
_CANDIDATE_CLASS_MINIMUM_TIER: Mapping[AutonomyDecisionClass, int] = {
    AutonomyDecisionClass.SUGGEST_NEXT_STEP: 1,
    AutonomyDecisionClass.PREPARE_PLAN: 2,
    AutonomyDecisionClass.PREPARE_RECOVERY_CANDIDATE: 2,
    AutonomyDecisionClass.PREPARE_REPLAY_PLAN: 2,
    AutonomyDecisionClass.PREPARE_GRAPH_REVISION: 2,
    AutonomyDecisionClass.PREPARE_OPERATOR_REVIEW: 2,
    AutonomyDecisionClass.ADVANCE_INTERNAL_STATE_CANDIDATE: 3,
    AutonomyDecisionClass.AUTO_INTERNAL_STATE_TRANSITION_CANDIDATE: 4,
}


@dataclass(frozen=True)
class AutonomyResolution(_CanonicalMixin):
    """One total-resolver output. A resolution is never authority."""

    resolution_id: str
    contract_version: str
    level_value: str
    decision_class_value: str
    permission_state: AutonomyPermissionState
    reason: str
    truth_label: FlowTruthLabel
    requires_operator_review: bool = False
    future_p4_required: bool = False
    future_p5_required: bool = False
    future_p9_required: bool = False
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    authority_granted: bool = False
    permission_granted: bool = False
    execution_available: bool = False
    proof_available: bool = False
    trace_verified: bool = False
    runtime_submit_wired: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "permission_granted",
            "execution_available",
            "proof_available",
            "trace_verified",
            "runtime_submit_wired",
        )


def _resolution(
    level_value: str,
    decision_class_value: str,
    permission_state: AutonomyPermissionState,
    reason: str,
    *,
    requires_operator_review: bool = False,
    future_p4_required: bool = False,
    future_p5_required: bool = False,
    future_p9_required: bool = False,
) -> AutonomyResolution:
    payload = {
        "contract_version": AUTONOMY_RESOLUTION_VERSION,
        "level_value": level_value,
        "decision_class_value": decision_class_value,
        "permission_state": permission_state.value,
    }
    return AutonomyResolution(
        resolution_id="flars-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_RESOLUTION_VERSION,
        level_value=level_value,
        decision_class_value=decision_class_value,
        permission_state=permission_state,
        reason=reason,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        requires_operator_review=requires_operator_review,
        future_p4_required=future_p4_required,
        future_p5_required=future_p5_required,
        future_p9_required=future_p9_required,
    )


def resolve_permission_state(
    level: GovernedAutonomyLevel | str,
    decision_class: AutonomyDecisionClass | str,
) -> AutonomyResolution:
    """Total deterministic resolver: every input pair returns a resolution.

    Rules + hard safety overrides, not a manual Cartesian table. Unknown raw
    inputs fail closed to FORBIDDEN_IN_P3 and can never resolve ALLOWED_*.
    """

    level_value = level.value if isinstance(level, GovernedAutonomyLevel) else level
    class_value = (
        decision_class.value
        if isinstance(decision_class, AutonomyDecisionClass)
        else decision_class
    )
    try:
        known_level = GovernedAutonomyLevel(level_value)
    except ValueError:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
            f"unknown autonomy level {level_value!r} fails closed",
            requires_operator_review=True,
        )
    try:
        known_class = AutonomyDecisionClass(class_value)
    except ValueError:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
            f"unknown decision class {class_value!r} fails closed",
            requires_operator_review=True,
        )

    # Hard overrides, in precedence order.
    if (
        known_level is GovernedAutonomyLevel.ERROR
        or known_class is AutonomyDecisionClass.ERROR
    ):
        return _resolution(
            level_value, class_value, AutonomyPermissionState.ERROR, "ERROR input"
        )
    if (
        known_level is GovernedAutonomyLevel.UNAVAILABLE
        or known_class is AutonomyDecisionClass.UNAVAILABLE
    ):
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.UNAVAILABLE,
            "UNAVAILABLE input",
        )
    if known_class in SIDE_EFFECT_DECISION_CLASSES:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.FORBIDDEN_IN_P3,
            "side-effect classes are forbidden in P3 and future-bound to "
            "P4 execution and P9 authority at every autonomy level",
            requires_operator_review=True,
            future_p4_required=True,
            future_p9_required=True,
        )
    if known_class is AutonomyDecisionClass.REQUEST_PROOF:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.REQUIRES_P5_PROOF,
            "proof requires P5 AurelTrace at every autonomy level",
            future_p5_required=True,
        )
    if known_class is AutonomyDecisionClass.REQUEST_AUTHORITY:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.REQUIRES_P9_AUTHORITY,
            "authority requires P9 Custos at every autonomy level",
            future_p9_required=True,
        )
    if known_level is (
        GovernedAutonomyLevel.A9_HERETIC_MODE_LIVE_LOCKED_UNAVAILABLE
    ):
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.UNAVAILABLE,
            HERETIC_LIVE_LOCKED_REASON,
        )
    if known_class is AutonomyDecisionClass.REQUEST_EXECUTION:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.REQUIRES_P4_EXECUTION,
            "execution requires operator review and future P4 AurelExec",
            requires_operator_review=True,
            future_p4_required=True,
        )
    if known_class is AutonomyDecisionClass.REQUEST_PERMISSION:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.REQUIRES_OPERATOR_REVIEW,
            "a permission request surfaces to the operator and remains "
            "future-bound to P9 authority",
            requires_operator_review=True,
            future_p9_required=True,
        )

    # Tiered ladder for read/projection/candidate classes (A0..A8 only).
    tier = GOVERNED_AUTONOMY_TIER_ORDER[known_level]
    if known_class in READ_ONLY_DECISION_CLASSES:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.ALLOWED_READ_ONLY,
            "read-only observation is allowed at every tiered level",
        )
    if known_class is AutonomyDecisionClass.MARK_INTERNAL_READ_MODEL:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.ALLOWED_INTERNAL_PROJECTION_ONLY,
            "internal read-model marking is projection-only bookkeeping",
        )
    minimum_tier = _CANDIDATE_CLASS_MINIMUM_TIER[known_class]
    if tier >= minimum_tier:
        return _resolution(
            level_value,
            class_value,
            AutonomyPermissionState.ALLOWED_CANDIDATE_ONLY,
            f"candidate-only at tier {tier} >= minimum tier {minimum_tier}; "
            "a candidate never executes",
        )
    return _resolution(
        level_value,
        class_value,
        AutonomyPermissionState.REQUIRES_OPERATOR_REVIEW,
        f"tier {tier} is below minimum tier {minimum_tier}; the operator "
        "must review",
        requires_operator_review=True,
    )


@dataclass(frozen=True)
class AutonomyActionBoundary(_CanonicalMixin):
    """Thin action-boundary wrapper over the resolver. Never authority."""

    boundary_id: str
    contract_version: str
    resolution: AutonomyResolution
    read_only_allowed: bool
    candidate_only_allowed: bool
    requires_operator_review: bool
    future_p4_required: bool
    future_p5_required: bool
    future_p9_required: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    execution_available: bool = False
    authority_granted: bool = False
    runtime_submit_wired: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "execution_available",
            "authority_granted",
            "runtime_submit_wired",
        )


def resolve_action_boundary(
    level: GovernedAutonomyLevel | str,
    decision_class: AutonomyDecisionClass | str,
) -> AutonomyActionBoundary:
    resolution = resolve_permission_state(level, decision_class)
    payload = {
        "contract_version": AUTONOMY_ACTION_BOUNDARY_VERSION,
        "resolution_id": resolution.resolution_id,
    }
    return AutonomyActionBoundary(
        boundary_id="flabd-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_ACTION_BOUNDARY_VERSION,
        resolution=resolution,
        read_only_allowed=resolution.permission_state
        in (
            AutonomyPermissionState.ALLOWED_READ_ONLY,
            AutonomyPermissionState.ALLOWED_INTERNAL_PROJECTION_ONLY,
        ),
        candidate_only_allowed=resolution.permission_state
        is AutonomyPermissionState.ALLOWED_CANDIDATE_ONLY,
        requires_operator_review=resolution.requires_operator_review,
        future_p4_required=resolution.future_p4_required,
        future_p5_required=resolution.future_p5_required,
        future_p9_required=resolution.future_p9_required,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )

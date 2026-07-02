"""P3-FLOW-G recovery budget / loop guard / escalation layer (P3.15.20-P3.15.30).

Self-healing must be bounded: attempt, latency, cost, and depth budgets cap
repair; retry-storm and no-progress guards block auto-recovery candidates;
exhaustion and blocked loops surface degradation and human escalation frames.
Budget availability is not permission, a guard never executes a stop, a
degradation frame never hides failure, and an escalation is not approval.
Enforcement/execution belongs to P4 AurelExec and authority to P9 Custos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

RECOVERY_BUDGET_VERSION = "recovery_budget.v1"
RECOVERY_ATTEMPT_BUDGET_VERSION = "recovery_attempt_budget.v1"
RECOVERY_LATENCY_BUDGET_VERSION = "recovery_latency_budget.v1"
RECOVERY_COST_BUDGET_VERSION = "recovery_cost_budget.v1"
RECOVERY_DEPTH_BUDGET_VERSION = "recovery_depth_budget.v1"
RECOVERY_BUDGET_STATE_VERSION = "recovery_budget_state.v1"
RECOVERY_BUDGET_EXHAUSTED_SIGNAL_VERSION = "recovery_budget_exhausted_signal.v1"
RECOVERY_BUDGET_READ_MODEL_VERSION = "recovery_budget_read_model.v1"
RETRY_STORM_GUARD_VERSION = "retry_storm_guard.v1"
NO_PROGRESS_GUARD_VERSION = "no_progress_guard.v1"
CONTROL_LOOP_COLLAPSE_SIGNAL_VERSION = "control_loop_collapse_signal.v1"
LOOP_HEALTH_SIGNAL_VERSION = "loop_health_signal.v1"
LOOP_SAFETY_READ_MODEL_VERSION = "loop_safety_read_model.v1"
GRACEFUL_DEGRADATION_FRAME_VERSION = "graceful_degradation_frame.v1"
HUMAN_ESCALATION_FRAME_VERSION = "human_escalation_frame.v1"
ESCALATION_READ_MODEL_VERSION = "escalation_read_model.v1"

BUDGET_PERMISSION_UNAVAILABLE_REASON = (
    "a recovery budget bounds future self-healing; budget availability is "
    "not permission and budget state enforces nothing — enforcement belongs "
    "to P4 AurelExec and authority to P9 Custos"
)
GUARD_STOP_UNAVAILABLE_REASON = (
    "a loop guard blocks auto-recovery candidates as recorded state only; it "
    "never executes a stop, kill, or termination — execution belongs to P4 "
    "AurelExec"
)
ESCALATION_APPROVAL_UNAVAILABLE_REASON = (
    "a human escalation frame surfaces state to an operator; it grants no "
    "approval and no authority — approval flows only from a real operator "
    "decision and authority from P9 Custos"
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


def _forbid_negative(obj: object, *count_fields: str) -> None:
    for count_field in count_fields:
        if getattr(obj, count_field) < 0:
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{count_field} must be non-negative",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=count_field,
            )


@dataclass(frozen=True)
class RecoveryAttemptBudget(_CanonicalMixin):
    """Attempt bound for future recovery. A bound is not enforcement."""

    budget_id: str
    contract_version: str
    attempt_limit: int
    attempts_used: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    budget_enforced: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "budget_enforced", "permission_granted")
        _forbid_negative(self, "attempt_limit", "attempts_used")

    @property
    def exhausted(self) -> bool:
        return self.attempts_used >= self.attempt_limit


@dataclass(frozen=True)
class RecoveryLatencyBudget(_CanonicalMixin):
    """Logical latency bound (in logical steps, never wall clock)."""

    budget_id: str
    contract_version: str
    latency_step_limit: int
    latency_steps_used: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    budget_enforced: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "budget_enforced", "permission_granted")
        _forbid_negative(self, "latency_step_limit", "latency_steps_used")

    @property
    def exhausted(self) -> bool:
        return self.latency_steps_used >= self.latency_step_limit


@dataclass(frozen=True)
class RecoveryCostBudget(_CanonicalMixin):
    """Abstract cost-unit bound. Units are declared, never billed here."""

    budget_id: str
    contract_version: str
    cost_unit_limit: int
    cost_units_used: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    budget_enforced: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "budget_enforced", "permission_granted")
        _forbid_negative(self, "cost_unit_limit", "cost_units_used")

    @property
    def exhausted(self) -> bool:
        return self.cost_units_used >= self.cost_unit_limit


@dataclass(frozen=True)
class RecoveryDepthBudget(_CanonicalMixin):
    """Nested-recovery depth bound: no infinite repair-of-repair loops."""

    budget_id: str
    contract_version: str
    depth_limit: int
    depth_used: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    budget_enforced: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "budget_enforced", "permission_granted")
        _forbid_negative(self, "depth_limit", "depth_used")

    @property
    def exhausted(self) -> bool:
        return self.depth_used >= self.depth_limit


def _sub_budget_id(prefix: str, version: str, run_id: str, limit: int, used: int) -> str:
    return prefix + stable_hash(
        {
            "contract_version": version,
            "run_id": run_id,
            "limit": limit,
            "used": used,
        }
    )[:16]


@dataclass(frozen=True)
class RecoveryBudget(_CanonicalMixin):
    """Aggregate recovery budget for one run. A budget is not permission."""

    budget_id: str
    contract_version: str
    run_id: str
    attempt_budget: RecoveryAttemptBudget
    latency_budget: RecoveryLatencyBudget
    cost_budget: RecoveryCostBudget
    depth_budget: RecoveryDepthBudget
    truth_label: FlowTruthLabel
    retry_storm_limit: int = 3
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    requires_operator_review_above_limit: bool = True
    budget_enforced: bool = False
    permission_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_operator_review_above_limit")
        _forbid_true(
            self, "budget_enforced", "permission_granted", "execution_available"
        )
        _forbid_negative(self, "retry_storm_limit")


def create_recovery_budget(
    *,
    run_id: str,
    attempt_limit: int = 3,
    attempts_used: int = 0,
    latency_step_limit: int = 50,
    latency_steps_used: int = 0,
    cost_unit_limit: int = 100,
    cost_units_used: int = 0,
    depth_limit: int = 2,
    depth_used: int = 0,
    retry_storm_limit: int = 3,
) -> RecoveryBudget:
    attempt_budget = RecoveryAttemptBudget(
        budget_id=_sub_budget_id(
            "flrba-", RECOVERY_ATTEMPT_BUDGET_VERSION, run_id, attempt_limit,
            attempts_used,
        ),
        contract_version=RECOVERY_ATTEMPT_BUDGET_VERSION,
        attempt_limit=attempt_limit,
        attempts_used=attempts_used,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
    latency_budget = RecoveryLatencyBudget(
        budget_id=_sub_budget_id(
            "flrbl-", RECOVERY_LATENCY_BUDGET_VERSION, run_id, latency_step_limit,
            latency_steps_used,
        ),
        contract_version=RECOVERY_LATENCY_BUDGET_VERSION,
        latency_step_limit=latency_step_limit,
        latency_steps_used=latency_steps_used,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
    cost_budget = RecoveryCostBudget(
        budget_id=_sub_budget_id(
            "flrbc-", RECOVERY_COST_BUDGET_VERSION, run_id, cost_unit_limit,
            cost_units_used,
        ),
        contract_version=RECOVERY_COST_BUDGET_VERSION,
        cost_unit_limit=cost_unit_limit,
        cost_units_used=cost_units_used,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
    depth_budget = RecoveryDepthBudget(
        budget_id=_sub_budget_id(
            "flrbd-", RECOVERY_DEPTH_BUDGET_VERSION, run_id, depth_limit, depth_used
        ),
        contract_version=RECOVERY_DEPTH_BUDGET_VERSION,
        depth_limit=depth_limit,
        depth_used=depth_used,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
    payload = {
        "contract_version": RECOVERY_BUDGET_VERSION,
        "run_id": run_id,
        "attempt_budget_id": attempt_budget.budget_id,
        "latency_budget_id": latency_budget.budget_id,
        "cost_budget_id": cost_budget.budget_id,
        "depth_budget_id": depth_budget.budget_id,
        "retry_storm_limit": retry_storm_limit,
    }
    return RecoveryBudget(
        budget_id="flrbg-" + stable_hash(payload)[:16],
        contract_version=RECOVERY_BUDGET_VERSION,
        run_id=run_id,
        attempt_budget=attempt_budget,
        latency_budget=latency_budget,
        cost_budget=cost_budget,
        depth_budget=depth_budget,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        retry_storm_limit=retry_storm_limit,
    )


@dataclass(frozen=True)
class RecoveryBudgetState(_CanonicalMixin):
    """Deterministic budget posture. Availability is not permission."""

    state_id: str
    contract_version: str
    budget_id: str
    run_id: str
    budget_available: bool
    budget_exhausted: bool
    exhausted_dimensions: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    budget_availability_is_not_permission: bool = True
    requires_operator_review_above_limit: bool = True
    permission_granted: bool = False
    execution_available: bool = False
    degradation_auto_authorized: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "budget_availability_is_not_permission",
            "requires_operator_review_above_limit",
        )
        _forbid_true(
            self,
            "permission_granted",
            "execution_available",
            "degradation_auto_authorized",
        )
        if self.budget_available and self.budget_exhausted:
            raise AurelFlowValidationError(
                "budget cannot be both available and exhausted",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="budget_exhausted",
            )


def build_recovery_budget_state(budget: RecoveryBudget) -> RecoveryBudgetState:
    """Derive budget posture with plain arithmetic over declared limits."""

    exhausted_dimensions: list[str] = []
    if budget.attempt_budget.exhausted:
        exhausted_dimensions.append("ATTEMPTS")
    if budget.latency_budget.exhausted:
        exhausted_dimensions.append("LATENCY_STEPS")
    if budget.cost_budget.exhausted:
        exhausted_dimensions.append("COST_UNITS")
    if budget.depth_budget.exhausted:
        exhausted_dimensions.append("DEPTH")
    budget_exhausted = bool(exhausted_dimensions)
    payload = {
        "contract_version": RECOVERY_BUDGET_STATE_VERSION,
        "budget_id": budget.budget_id,
        "exhausted_dimensions": tuple(exhausted_dimensions),
    }
    return RecoveryBudgetState(
        state_id="flrbs-" + stable_hash(payload)[:16],
        contract_version=RECOVERY_BUDGET_STATE_VERSION,
        budget_id=budget.budget_id,
        run_id=budget.run_id,
        budget_available=not budget_exhausted,
        budget_exhausted=budget_exhausted,
        exhausted_dimensions=tuple(exhausted_dimensions),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RecoveryBudgetExhaustedSignal(_CanonicalMixin):
    """Visible exhaustion. Exhaustion does not auto-authorize anything."""

    signal_id: str
    contract_version: str
    budget_id: str
    run_id: str
    exhausted_dimensions: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_PERMISSION_UNAVAILABLE_REASON
    requires_operator_review: bool = True
    requires_human_escalation: bool = True
    degradation_auto_authorized: bool = False
    permission_granted: bool = False
    stop_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_operator_review", "requires_human_escalation")
        _forbid_true(
            self, "degradation_auto_authorized", "permission_granted", "stop_executed"
        )
        if not self.exhausted_dimensions:
            raise AurelFlowValidationError(
                "an exhausted signal must name at least one exhausted dimension",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="exhausted_dimensions",
            )


def build_recovery_budget_exhausted_signal(
    state: RecoveryBudgetState,
) -> RecoveryBudgetExhaustedSignal:
    if not state.budget_exhausted:
        raise AurelFlowValidationError(
            "cannot build an exhausted signal from a non-exhausted budget state",
            code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
            field="state",
        )
    payload = {
        "contract_version": RECOVERY_BUDGET_EXHAUSTED_SIGNAL_VERSION,
        "state_id": state.state_id,
        "exhausted_dimensions": state.exhausted_dimensions,
    }
    return RecoveryBudgetExhaustedSignal(
        signal_id="flrbx-" + stable_hash(payload)[:16],
        contract_version=RECOVERY_BUDGET_EXHAUSTED_SIGNAL_VERSION,
        budget_id=state.budget_id,
        run_id=state.run_id,
        exhausted_dimensions=state.exhausted_dimensions,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RecoveryBudgetReadModel(_CanonicalMixin):
    """Deterministic budget projection."""

    read_model_version: str
    budget_id: str
    run_id: str
    budget_available: bool
    budget_exhausted: bool
    exhausted_dimensions: tuple[str, ...]
    attempt_limit: int
    attempts_used: int
    depth_limit: int
    depth_used: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    budget_availability_is_not_permission: bool = True
    permission_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "budget_availability_is_not_permission")
        _forbid_true(self, "permission_granted", "execution_available")


def build_recovery_budget_read_model(
    budget: RecoveryBudget, state: RecoveryBudgetState
) -> RecoveryBudgetReadModel:
    if state.budget_id != budget.budget_id:
        raise AurelFlowValidationError(
            f"budget state budget {state.budget_id!r} does not match budget "
            f"{budget.budget_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="state",
        )
    payload = {
        "read_model_version": RECOVERY_BUDGET_READ_MODEL_VERSION,
        "state_id": state.state_id,
    }
    return RecoveryBudgetReadModel(
        read_model_version=RECOVERY_BUDGET_READ_MODEL_VERSION,
        budget_id=budget.budget_id,
        run_id=budget.run_id,
        budget_available=state.budget_available,
        budget_exhausted=state.budget_exhausted,
        exhausted_dimensions=state.exhausted_dimensions,
        attempt_limit=budget.attempt_budget.attempt_limit,
        attempts_used=budget.attempt_budget.attempts_used,
        depth_limit=budget.depth_budget.depth_limit,
        depth_used=budget.depth_budget.depth_used,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


class LoopHealth(str, Enum):
    """Closed-world loop health vocabulary."""

    HEALTHY = "HEALTHY"
    DEGRADING = "DEGRADING"
    STORMING = "STORMING"
    STALLED = "STALLED"
    COLLAPSED = "COLLAPSED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RetryStormGuard(_CanonicalMixin):
    """Blocks auto-recovery on repeated same-failure loops. Never executes stop."""

    guard_id: str
    contract_version: str
    run_id: str
    retry_count: int
    same_failure_count: int
    retry_storm_limit: int
    auto_recovery_blocked: bool
    requires_human_escalation: bool
    truth_label: FlowTruthLabel
    failure_signal_id: str = ""
    unavailable_reason: str = GUARD_STOP_UNAVAILABLE_REASON
    execution_available: bool = False
    stop_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "execution_available", "stop_executed")
        _forbid_negative(
            self, "retry_count", "same_failure_count", "retry_storm_limit"
        )
        if self.same_failure_count >= self.retry_storm_limit and not (
            self.auto_recovery_blocked
        ):
            raise AurelFlowValidationError(
                "retry storm guard at or above limit must block auto-recovery",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="auto_recovery_blocked",
            )


def build_retry_storm_guard(
    *,
    run_id: str,
    retry_count: int,
    same_failure_count: int,
    retry_storm_limit: int = 3,
    failure_signal_id: str = "",
) -> RetryStormGuard:
    blocked = same_failure_count >= retry_storm_limit
    payload = {
        "contract_version": RETRY_STORM_GUARD_VERSION,
        "run_id": run_id,
        "retry_count": retry_count,
        "same_failure_count": same_failure_count,
        "retry_storm_limit": retry_storm_limit,
        "failure_signal_id": failure_signal_id,
    }
    return RetryStormGuard(
        guard_id="flrsg-" + stable_hash(payload)[:16],
        contract_version=RETRY_STORM_GUARD_VERSION,
        run_id=run_id,
        retry_count=retry_count,
        same_failure_count=same_failure_count,
        retry_storm_limit=retry_storm_limit,
        auto_recovery_blocked=blocked,
        requires_human_escalation=blocked,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        failure_signal_id=failure_signal_id,
    )


@dataclass(frozen=True)
class NoProgressGuard(_CanonicalMixin):
    """Blocks auto-recovery when the loop makes no progress. Never executes stop."""

    guard_id: str
    contract_version: str
    run_id: str
    no_progress_count: int
    no_progress_limit: int
    auto_recovery_blocked: bool
    requires_human_escalation: bool
    truth_label: FlowTruthLabel
    failure_signal_id: str = ""
    unavailable_reason: str = GUARD_STOP_UNAVAILABLE_REASON
    execution_available: bool = False
    stop_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "execution_available", "stop_executed")
        _forbid_negative(self, "no_progress_count", "no_progress_limit")
        if self.no_progress_count >= self.no_progress_limit and not (
            self.auto_recovery_blocked and self.requires_human_escalation
        ):
            raise AurelFlowValidationError(
                "no-progress guard at or above limit must block auto-recovery "
                "and require human escalation",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="auto_recovery_blocked",
            )


def build_no_progress_guard(
    *,
    run_id: str,
    no_progress_count: int,
    no_progress_limit: int = 2,
    failure_signal_id: str = "",
) -> NoProgressGuard:
    blocked = no_progress_count >= no_progress_limit
    payload = {
        "contract_version": NO_PROGRESS_GUARD_VERSION,
        "run_id": run_id,
        "no_progress_count": no_progress_count,
        "no_progress_limit": no_progress_limit,
        "failure_signal_id": failure_signal_id,
    }
    return NoProgressGuard(
        guard_id="flnpg-" + stable_hash(payload)[:16],
        contract_version=NO_PROGRESS_GUARD_VERSION,
        run_id=run_id,
        no_progress_count=no_progress_count,
        no_progress_limit=no_progress_limit,
        auto_recovery_blocked=blocked,
        requires_human_escalation=blocked,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        failure_signal_id=failure_signal_id,
    )


@dataclass(frozen=True)
class ControlLoopCollapseSignal(_CanonicalMixin):
    """The control loop itself has collapsed. Naming collapse executes nothing."""

    signal_id: str
    contract_version: str
    run_id: str
    detail: str
    truth_label: FlowTruthLabel
    failure_signal_id: str = ""
    unavailable_reason: str = GUARD_STOP_UNAVAILABLE_REASON
    auto_recovery_blocked: bool = True
    requires_human_escalation: bool = True
    stop_executed: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "auto_recovery_blocked", "requires_human_escalation")
        _forbid_true(self, "stop_executed", "execution_available")


def build_control_loop_collapse_signal(
    *, run_id: str, detail: str, failure_signal_id: str = ""
) -> ControlLoopCollapseSignal:
    payload = {
        "contract_version": CONTROL_LOOP_COLLAPSE_SIGNAL_VERSION,
        "run_id": run_id,
        "detail": detail,
        "failure_signal_id": failure_signal_id,
    }
    return ControlLoopCollapseSignal(
        signal_id="flcls-" + stable_hash(payload)[:16],
        contract_version=CONTROL_LOOP_COLLAPSE_SIGNAL_VERSION,
        run_id=run_id,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        failure_signal_id=failure_signal_id,
    )


@dataclass(frozen=True)
class LoopHealthSignal(_CanonicalMixin):
    """Deterministic loop-health summary derived from guards."""

    signal_id: str
    contract_version: str
    run_id: str
    loop_health: LoopHealth
    truth_label: FlowTruthLabel
    unavailable_reason: str = GUARD_STOP_UNAVAILABLE_REASON
    execution_available: bool = False
    stop_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "execution_available", "stop_executed")


def build_loop_health_signal(
    *,
    run_id: str,
    retry_storm_guard: RetryStormGuard | None = None,
    no_progress_guard: NoProgressGuard | None = None,
    collapse_signal: ControlLoopCollapseSignal | None = None,
) -> LoopHealthSignal:
    """Derive loop health deterministically: collapse > storm > stall > healthy."""

    if collapse_signal is not None:
        loop_health = LoopHealth.COLLAPSED
    elif retry_storm_guard is not None and retry_storm_guard.auto_recovery_blocked:
        loop_health = LoopHealth.STORMING
    elif no_progress_guard is not None and no_progress_guard.auto_recovery_blocked:
        loop_health = LoopHealth.STALLED
    elif (
        retry_storm_guard is not None and retry_storm_guard.same_failure_count > 0
    ) or (no_progress_guard is not None and no_progress_guard.no_progress_count > 0):
        loop_health = LoopHealth.DEGRADING
    elif retry_storm_guard is None and no_progress_guard is None:
        loop_health = LoopHealth.UNKNOWN
    else:
        loop_health = LoopHealth.HEALTHY
    payload = {
        "contract_version": LOOP_HEALTH_SIGNAL_VERSION,
        "run_id": run_id,
        "loop_health": loop_health.value,
        "retry_storm_guard_id": (
            retry_storm_guard.guard_id if retry_storm_guard else ""
        ),
        "no_progress_guard_id": (
            no_progress_guard.guard_id if no_progress_guard else ""
        ),
        "collapse_signal_id": collapse_signal.signal_id if collapse_signal else "",
    }
    return LoopHealthSignal(
        signal_id="fllhs-" + stable_hash(payload)[:16],
        contract_version=LOOP_HEALTH_SIGNAL_VERSION,
        run_id=run_id,
        loop_health=loop_health,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class LoopSafetyReadModel(_CanonicalMixin):
    """Deterministic guard/health projection."""

    read_model_version: str
    run_id: str
    loop_health: LoopHealth
    any_auto_recovery_blocked: bool
    any_requires_human_escalation: bool
    retry_storm_guard_present: bool
    no_progress_guard_present: bool
    collapse_signal_present: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    guard_executes_stop: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "guard_executes_stop", "execution_available")


def build_loop_safety_read_model(
    *,
    run_id: str,
    loop_health_signal: LoopHealthSignal,
    retry_storm_guard: RetryStormGuard | None = None,
    no_progress_guard: NoProgressGuard | None = None,
    collapse_signal: ControlLoopCollapseSignal | None = None,
) -> LoopSafetyReadModel:
    any_blocked = (
        (retry_storm_guard is not None and retry_storm_guard.auto_recovery_blocked)
        or (no_progress_guard is not None and no_progress_guard.auto_recovery_blocked)
        or collapse_signal is not None
    )
    any_escalation = (
        (
            retry_storm_guard is not None
            and retry_storm_guard.requires_human_escalation
        )
        or (
            no_progress_guard is not None
            and no_progress_guard.requires_human_escalation
        )
        or collapse_signal is not None
    )
    payload = {
        "read_model_version": LOOP_SAFETY_READ_MODEL_VERSION,
        "loop_health_signal_id": loop_health_signal.signal_id,
        "retry_storm_guard_id": (
            retry_storm_guard.guard_id if retry_storm_guard else ""
        ),
        "no_progress_guard_id": (
            no_progress_guard.guard_id if no_progress_guard else ""
        ),
        "collapse_signal_id": collapse_signal.signal_id if collapse_signal else "",
    }
    return LoopSafetyReadModel(
        read_model_version=LOOP_SAFETY_READ_MODEL_VERSION,
        run_id=run_id,
        loop_health=loop_health_signal.loop_health,
        any_auto_recovery_blocked=any_blocked,
        any_requires_human_escalation=any_escalation,
        retry_storm_guard_present=retry_storm_guard is not None,
        no_progress_guard_present=no_progress_guard is not None,
        collapse_signal_present=collapse_signal is not None,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


class EscalationReason(str, Enum):
    """Why a human must look. Escalating grants nothing."""

    RECOVERY_BUDGET_EXHAUSTED = "RECOVERY_BUDGET_EXHAUSTED"
    RETRY_STORM = "RETRY_STORM"
    NO_PROGRESS = "NO_PROGRESS"
    CONTROL_LOOP_COLLAPSE = "CONTROL_LOOP_COLLAPSE"
    LOW_DIAGNOSIS_CONFIDENCE = "LOW_DIAGNOSIS_CONFIDENCE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    HIGH_RISK_RECOVERY = "HIGH_RISK_RECOVERY"
    IRREVERSIBLE_ACTION_REQUIRED = "IRREVERSIBLE_ACTION_REQUIRED"
    DIVERSITY_CORRELATION_RISK = "DIVERSITY_CORRELATION_RISK"
    OPERATOR_REQUESTED = "OPERATOR_REQUESTED"
    POLICY_REQUIRED = "POLICY_REQUIRED"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class DegradationMode(str, Enum):
    """How a workflow can degrade safely. Degrading hides nothing."""

    PARTIAL_RESULT = "PARTIAL_RESULT"
    REDUCED_SCOPE = "REDUCED_SCOPE"
    SAFE_HOLD = "SAFE_HOLD"
    READ_ONLY_MODE = "READ_ONLY_MODE"
    GRACEFUL_TERMINATION = "GRACEFUL_TERMINATION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class GracefulDegradationFrame(_CanonicalMixin):
    """Represents safe degradation. Degradation is visible, never hidden failure."""

    degradation_frame_id: str
    contract_version: str
    run_id: str
    failure_signal_id: str
    degradation_mode: DegradationMode
    degradation_reason: str
    truth_label: FlowTruthLabel
    recovery_candidate_id: str = ""
    unavailable_reason: str = ESCALATION_APPROVAL_UNAVAILABLE_REASON
    degradation_is_visible: bool = True
    requires_operator_review: bool = True
    failure_hidden: bool = False
    approval_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "degradation_is_visible", "requires_operator_review")
        _forbid_true(
            self, "failure_hidden", "approval_granted", "execution_available"
        )


def build_graceful_degradation_frame(
    *,
    run_id: str,
    failure_signal_id: str,
    degradation_mode: DegradationMode,
    degradation_reason: str,
    recovery_candidate_id: str = "",
) -> GracefulDegradationFrame:
    payload = {
        "contract_version": GRACEFUL_DEGRADATION_FRAME_VERSION,
        "run_id": run_id,
        "failure_signal_id": failure_signal_id,
        "degradation_mode": degradation_mode.value,
        "degradation_reason": degradation_reason,
        "recovery_candidate_id": recovery_candidate_id,
    }
    return GracefulDegradationFrame(
        degradation_frame_id="flgdf-" + stable_hash(payload)[:16],
        contract_version=GRACEFUL_DEGRADATION_FRAME_VERSION,
        run_id=run_id,
        failure_signal_id=failure_signal_id,
        degradation_mode=degradation_mode,
        degradation_reason=degradation_reason,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        recovery_candidate_id=recovery_candidate_id,
    )


@dataclass(frozen=True)
class HumanEscalationFrame(_CanonicalMixin):
    """Surfaces state to a human/operator. Escalation is not approval."""

    escalation_frame_id: str
    contract_version: str
    run_id: str
    failure_signal_id: str
    escalation_reason: EscalationReason
    detail: str
    truth_label: FlowTruthLabel
    recovery_candidate_id: str = ""
    unavailable_reason: str = ESCALATION_APPROVAL_UNAVAILABLE_REASON
    escalation_is_not_approval: bool = True
    requires_operator_review: bool = True
    approval_granted: bool = False
    authority_granted: bool = False
    execution_available: bool = False
    failure_hidden: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "escalation_is_not_approval", "requires_operator_review")
        _forbid_true(
            self,
            "approval_granted",
            "authority_granted",
            "execution_available",
            "failure_hidden",
        )


def build_human_escalation_frame(
    *,
    run_id: str,
    failure_signal_id: str,
    escalation_reason: EscalationReason,
    detail: str,
    recovery_candidate_id: str = "",
) -> HumanEscalationFrame:
    payload = {
        "contract_version": HUMAN_ESCALATION_FRAME_VERSION,
        "run_id": run_id,
        "failure_signal_id": failure_signal_id,
        "escalation_reason": escalation_reason.value,
        "detail": detail,
        "recovery_candidate_id": recovery_candidate_id,
    }
    return HumanEscalationFrame(
        escalation_frame_id="flhef-" + stable_hash(payload)[:16],
        contract_version=HUMAN_ESCALATION_FRAME_VERSION,
        run_id=run_id,
        failure_signal_id=failure_signal_id,
        escalation_reason=escalation_reason,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        recovery_candidate_id=recovery_candidate_id,
    )


@dataclass(frozen=True)
class EscalationReadModel(_CanonicalMixin):
    """Deterministic degradation/escalation projection."""

    read_model_version: str
    run_id: str
    escalation_count: int
    degradation_count: int
    escalation_reasons: tuple[str, ...]
    degradation_modes: tuple[str, ...]
    any_requires_operator_review: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    escalation_is_not_approval: bool = True
    any_approval_granted: bool = False
    any_failure_hidden: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "escalation_is_not_approval")
        _forbid_true(self, "any_approval_granted", "any_failure_hidden")


def build_escalation_read_model(
    run_id: str,
    *,
    escalation_frames: tuple[HumanEscalationFrame, ...] = (),
    degradation_frames: tuple[GracefulDegradationFrame, ...] = (),
) -> EscalationReadModel:
    for frame_run_id in tuple(frame.run_id for frame in escalation_frames) + tuple(
        frame.run_id for frame in degradation_frames
    ):
        if frame_run_id != run_id:
            raise AurelFlowValidationError(
                f"escalation/degradation frame run {frame_run_id!r} does not "
                f"match read model run {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="frames",
            )
    payload = {
        "read_model_version": ESCALATION_READ_MODEL_VERSION,
        "run_id": run_id,
        "escalation_ids": tuple(
            frame.escalation_frame_id for frame in escalation_frames
        ),
        "degradation_ids": tuple(
            frame.degradation_frame_id for frame in degradation_frames
        ),
    }
    return EscalationReadModel(
        read_model_version=ESCALATION_READ_MODEL_VERSION,
        run_id=run_id,
        escalation_count=len(escalation_frames),
        degradation_count=len(degradation_frames),
        escalation_reasons=tuple(
            sorted({frame.escalation_reason.value for frame in escalation_frames})
        ),
        degradation_modes=tuple(
            sorted({frame.degradation_mode.value for frame in degradation_frames})
        ),
        any_requires_operator_review=bool(escalation_frames or degradation_frames),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )

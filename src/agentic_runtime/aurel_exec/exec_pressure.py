"""P4-EXEC-F concurrency window / pressure / backpressure — control before
concurrency.

A ``ConcurrencyWindow`` is local bounded capacity arithmetic — it spawns no
threads, tasks, or workers. A ``ConcurrencyLimitDecision`` and a
``BackpressureDecision`` decide ALLOW/HOLD/DELAY/BLOCK/ESCALATE
deterministically; deciding is not executing, and backpressure is safety
feedback, never recovery — no retry, no rollback, no authority mutation.
Pressure derives deterministically from queue depth, in-flight count,
available slots, recent failure classifications, algedonic signals, and
declared resource pressure; a snapshot whose level contradicts the
derivation is unconstructible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_nonempty,
    stable_hash,
)

CONCURRENCY_WINDOW_VERSION = "concurrency_window.v1"
CONCURRENCY_LIMIT_DECISION_VERSION = "concurrency_limit_decision.v1"
EXECUTION_PRESSURE_SNAPSHOT_VERSION = "execution_pressure_snapshot.v1"
BACKPRESSURE_SIGNAL_VERSION = "backpressure_signal.v1"
BACKPRESSURE_DECISION_VERSION = "backpressure_decision.v1"

BACKPRESSURE_AUTHORITY_BOUNDARY_REASON = (
    "backpressure is safety feedback on the local control plane; it slows, "
    "holds, delays, blocks, or escalates admission of new work — it never "
    "retries, recovers, rolls back, grants authority, or bypasses Custos"
)


class ExecutionPressureLevel(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"


class ConcurrencyLimitDecisionKind(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    DELAY = "DELAY"
    BLOCK = "BLOCK"
    ERROR = "ERROR"


class BackpressureSignalKind(str, Enum):
    QUEUE_DEPTH_HIGH = "QUEUE_DEPTH_HIGH"
    NO_AVAILABLE_SLOTS = "NO_AVAILABLE_SLOTS"
    FAILURE_RATE_HIGH = "FAILURE_RATE_HIGH"
    ALGEDONIC_ACTIVE = "ALGEDONIC_ACTIVE"
    RESOURCE_PRESSURE_HIGH = "RESOURCE_PRESSURE_HIGH"
    UNSAFE_TO_ADMIT = "UNSAFE_TO_ADMIT"
    UNKNOWN_PRESSURE = "UNKNOWN_PRESSURE"


class BackpressureDecisionKind(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    DELAY = "DELAY"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    ERROR = "ERROR"


def derive_pressure_level(
    *,
    queue_depth: int,
    current_in_flight: int,
    max_in_flight: int,
    recent_failures: int = 0,
    recent_algedonic_signals: int = 0,
    resource_pressure: int = 0,
) -> ExecutionPressureLevel:
    """Deterministic local pressure derivation. Pure arithmetic, no I/O.

    ``resource_pressure`` is a declared 0–3 scale (0 none … 3 severe).
    """
    if min(queue_depth, current_in_flight, max_in_flight) < 0 or max_in_flight == 0:
        return ExecutionPressureLevel.ERROR
    if resource_pressure < 0 or recent_failures < 0 or recent_algedonic_signals < 0:
        return ExecutionPressureLevel.ERROR
    available_slots = max(max_in_flight - current_in_flight, 0)
    score = 0
    if available_slots == 0:
        score += 2
    if queue_depth > max_in_flight * 2:
        score += 2
    elif queue_depth > max_in_flight:
        score += 1
    if recent_failures >= 3:
        score += 2
    elif recent_failures >= 1:
        score += 1
    if recent_algedonic_signals >= 1:
        score += 3
    if resource_pressure >= 2:
        score += 2
    elif resource_pressure == 1:
        score += 1
    if score >= 5:
        return ExecutionPressureLevel.CRITICAL
    if score >= 3:
        return ExecutionPressureLevel.HIGH
    if score >= 1:
        return ExecutionPressureLevel.ELEVATED
    if current_in_flight == 0 and queue_depth == 0:
        return ExecutionPressureLevel.LOW
    return ExecutionPressureLevel.NORMAL


@dataclass(frozen=True)
class ConcurrencyWindow(_ExecCanonicalMixin):
    """Local bounded capacity arithmetic. Not a worker pool."""

    concurrency_window_id: str
    max_in_flight: int
    current_in_flight: int
    available_slots: int
    queue_depth: int
    pressure_level: ExecutionPressureLevel
    truth_label: ExecTruthLabel
    contract_version: str = CONCURRENCY_WINDOW_VERSION
    created_at_tick: int | None = None
    spawns_workers: bool = False
    is_worker_pool: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "concurrency_window_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        forbid_true(self, "spawns_workers", "is_worker_pool")
        if min(self.max_in_flight, self.current_in_flight, self.queue_depth) < 0:
            raise AurelExecValidationError(
                "negative capacity inputs are invalid",
                code=AurelExecErrorCode.ERROR,
                field="max_in_flight",
            )
        if self.available_slots != max(self.max_in_flight - self.current_in_flight, 0):
            raise AurelExecValidationError(
                "available_slots must equal max(max_in_flight - current_in_flight, 0)",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="available_slots",
            )

    @property
    def window_hash(self) -> str:
        return stable_hash(self)


def build_concurrency_window(
    *,
    max_in_flight: int,
    current_in_flight: int,
    queue_depth: int,
    created_at_tick: int | None = None,
    truth_label: ExecTruthLabel = ExecTruthLabel.LIVE,
) -> ConcurrencyWindow:
    """Deterministic window with computed slots and derived pressure."""
    pressure = derive_pressure_level(
        queue_depth=queue_depth,
        current_in_flight=current_in_flight,
        max_in_flight=max_in_flight,
    )
    return ConcurrencyWindow(
        concurrency_window_id="exec-window-"
        + stable_hash((max_in_flight, current_in_flight, queue_depth, created_at_tick))[:16],
        max_in_flight=max_in_flight,
        current_in_flight=current_in_flight,
        available_slots=max(max_in_flight - current_in_flight, 0),
        queue_depth=queue_depth,
        pressure_level=pressure,
        truth_label=truth_label,
        created_at_tick=created_at_tick,
    )


@dataclass(frozen=True)
class ConcurrencyLimitDecision(_ExecCanonicalMixin):
    """ALLOW/HOLD/DELAY/BLOCK/ERROR under the local window. Not execution."""

    decision_id: str
    concurrency_window_id: str
    decision: ConcurrencyLimitDecisionKind
    allowed: bool
    held: bool
    blocked: bool
    reason: str
    truth_label: ExecTruthLabel
    contract_version: str = CONCURRENCY_LIMIT_DECISION_VERSION
    exec_job_id: str | None = None
    queue_entry_id: str | None = None
    recommended_delay_ms: int | None = None
    requires_backpressure_signal: bool = False
    executes: bool = False
    spawns_workers: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "decision_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "executes", "spawns_workers")
        expected = {
            ConcurrencyLimitDecisionKind.ALLOW: (True, False, False),
            ConcurrencyLimitDecisionKind.HOLD: (False, True, False),
            ConcurrencyLimitDecisionKind.DELAY: (False, True, False),
            ConcurrencyLimitDecisionKind.BLOCK: (False, False, True),
            ConcurrencyLimitDecisionKind.ERROR: (False, False, True),
        }[self.decision]
        if (self.allowed, self.held, self.blocked) != expected:
            raise AurelExecValidationError(
                "allowed/held/blocked flags must agree with the decision kind",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="decision",
            )

    @property
    def decision_hash(self) -> str:
        return stable_hash(self)


def decide_concurrency_limit(
    window: ConcurrencyWindow,
    *,
    exec_job_id: str | None = None,
    queue_entry_id: str | None = None,
) -> ConcurrencyLimitDecision:
    """Deterministic local admission verdict. Decides; never executes."""
    def _make(kind, reason, *, delay=None, signal=False):
        flags = {
            ConcurrencyLimitDecisionKind.ALLOW: (True, False, False),
            ConcurrencyLimitDecisionKind.HOLD: (False, True, False),
            ConcurrencyLimitDecisionKind.DELAY: (False, True, False),
            ConcurrencyLimitDecisionKind.BLOCK: (False, False, True),
            ConcurrencyLimitDecisionKind.ERROR: (False, False, True),
        }[kind]
        return ConcurrencyLimitDecision(
            decision_id="exec-climit-"
            + stable_hash((window.concurrency_window_id, kind.value, exec_job_id))[:16],
            concurrency_window_id=window.concurrency_window_id,
            decision=kind,
            allowed=flags[0],
            held=flags[1],
            blocked=flags[2],
            reason=reason,
            truth_label=ExecTruthLabel.LIVE,
            exec_job_id=exec_job_id,
            queue_entry_id=queue_entry_id,
            recommended_delay_ms=delay,
            requires_backpressure_signal=signal,
        )

    if window.pressure_level is ExecutionPressureLevel.ERROR:
        return _make(
            ConcurrencyLimitDecisionKind.ERROR,
            "invalid window inputs; nothing may be admitted",
            signal=True,
        )
    if window.pressure_level is ExecutionPressureLevel.CRITICAL:
        return _make(
            ConcurrencyLimitDecisionKind.BLOCK,
            "critical local pressure: new execution is blocked",
            signal=True,
        )
    if window.available_slots == 0:
        return _make(
            ConcurrencyLimitDecisionKind.HOLD,
            "no available local slots: new execution is held until the "
            "single local slot releases",
            signal=window.queue_depth > 0,
        )
    if window.pressure_level is ExecutionPressureLevel.HIGH:
        return _make(
            ConcurrencyLimitDecisionKind.DELAY,
            "high local pressure: new execution should be delayed",
            delay=250,
            signal=True,
        )
    return _make(
        ConcurrencyLimitDecisionKind.ALLOW,
        "local slot available under acceptable pressure; allowing admission "
        "is not execution — every lease/session/claim/bridge guard still applies",
    )


@dataclass(frozen=True)
class ExecutionPressureSnapshot(_ExecCanonicalMixin):
    """Deterministic local pressure view. A level contradicting the
    derivation is unconstructible."""

    pressure_snapshot_id: str
    queue_depth: int
    current_in_flight: int
    max_in_flight: int
    available_slots: int
    recent_failures: int
    recent_algedonic_signals: int
    resource_pressure: int
    pressure_level: ExecutionPressureLevel
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_PRESSURE_SNAPSHOT_VERSION
    created_at_tick: int | None = None
    executes: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "pressure_snapshot_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        forbid_true(self, "executes")
        derived = derive_pressure_level(
            queue_depth=self.queue_depth,
            current_in_flight=self.current_in_flight,
            max_in_flight=self.max_in_flight,
            recent_failures=self.recent_failures,
            recent_algedonic_signals=self.recent_algedonic_signals,
            resource_pressure=self.resource_pressure,
        )
        if self.pressure_level is not derived:
            raise AurelExecValidationError(
                f"pressure_level must match the deterministic derivation "
                f"({derived.value})",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="pressure_level",
            )

    @property
    def snapshot_hash(self) -> str:
        return stable_hash(self)


def build_execution_pressure_snapshot(
    *,
    queue_depth: int,
    current_in_flight: int,
    max_in_flight: int,
    resource_pressure: int = 0,
    failure_classifications: tuple[Any, ...] = (),
    algedonic_signals: tuple[Any, ...] = (),
    created_at_tick: int | None = None,
    truth_label: ExecTruthLabel = ExecTruthLabel.LIVE,
) -> ExecutionPressureSnapshot:
    """Build a snapshot from local shape counts plus real P4-E judgment
    objects: failures counted from classifications whose class is not NONE,
    urgency counted from provided algedonic signals."""
    recent_failures = sum(
        1
        for classification in failure_classifications
        if getattr(classification.failure_class, "value", "NONE") != "NONE"
    )
    recent_algedonic = len(algedonic_signals)
    level = derive_pressure_level(
        queue_depth=queue_depth,
        current_in_flight=current_in_flight,
        max_in_flight=max_in_flight,
        recent_failures=recent_failures,
        recent_algedonic_signals=recent_algedonic,
        resource_pressure=resource_pressure,
    )
    return ExecutionPressureSnapshot(
        pressure_snapshot_id="exec-pressure-"
        + stable_hash(
            (queue_depth, current_in_flight, max_in_flight, recent_failures,
             recent_algedonic, resource_pressure, created_at_tick)
        )[:16],
        queue_depth=queue_depth,
        current_in_flight=current_in_flight,
        max_in_flight=max_in_flight,
        available_slots=max(max_in_flight - current_in_flight, 0),
        recent_failures=recent_failures,
        recent_algedonic_signals=recent_algedonic,
        resource_pressure=resource_pressure,
        pressure_level=level,
        truth_label=truth_label,
        created_at_tick=created_at_tick,
    )


@dataclass(frozen=True)
class BackpressureSignal(_ExecCanonicalMixin):
    """Explains local pressure. Feedback only — never authority."""

    backpressure_signal_id: str
    pressure_snapshot_id: str
    signal_kind: BackpressureSignalKind
    severity: ExecutionPressureLevel
    message: str
    operator_attention_required: bool
    truth_label: ExecTruthLabel
    contract_version: str = BACKPRESSURE_SIGNAL_VERSION
    created_at_tick: int | None = None
    grants_authority: bool = False
    bypasses_custos: bool = False
    executes_recovery: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "backpressure_signal_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(self, "message", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "grants_authority", "bypasses_custos", "executes_recovery")

    @property
    def signal_hash(self) -> str:
        return stable_hash(self)


def build_backpressure_signal_if_needed(
    snapshot: ExecutionPressureSnapshot,
) -> BackpressureSignal | None:
    """Emit a signal for HIGH/CRITICAL/ERROR pressure; otherwise None.
    Deterministic kind priority; emitting explains, never acts."""
    if snapshot.pressure_level not in (
        ExecutionPressureLevel.HIGH,
        ExecutionPressureLevel.CRITICAL,
        ExecutionPressureLevel.ERROR,
    ):
        return None
    if snapshot.pressure_level is ExecutionPressureLevel.ERROR:
        kind = BackpressureSignalKind.UNKNOWN_PRESSURE
    elif snapshot.recent_algedonic_signals >= 1:
        kind = BackpressureSignalKind.ALGEDONIC_ACTIVE
    elif snapshot.available_slots == 0:
        kind = BackpressureSignalKind.NO_AVAILABLE_SLOTS
    elif snapshot.recent_failures >= 3:
        kind = BackpressureSignalKind.FAILURE_RATE_HIGH
    elif snapshot.queue_depth > snapshot.max_in_flight * 2:
        kind = BackpressureSignalKind.QUEUE_DEPTH_HIGH
    elif snapshot.resource_pressure >= 2:
        kind = BackpressureSignalKind.RESOURCE_PRESSURE_HIGH
    else:
        kind = BackpressureSignalKind.UNSAFE_TO_ADMIT
    return BackpressureSignal(
        backpressure_signal_id="exec-bpsig-"
        + stable_hash((snapshot.pressure_snapshot_id, kind.value))[:16],
        pressure_snapshot_id=snapshot.pressure_snapshot_id,
        signal_kind=kind,
        severity=snapshot.pressure_level,
        message=(
            f"{snapshot.pressure_level.value} local pressure ({kind.value}): "
            f"queue_depth={snapshot.queue_depth}, "
            f"in_flight={snapshot.current_in_flight}/{snapshot.max_in_flight}, "
            f"failures={snapshot.recent_failures}, "
            f"algedonic={snapshot.recent_algedonic_signals} — "
            + BACKPRESSURE_AUTHORITY_BOUNDARY_REASON
        ),
        operator_attention_required=snapshot.pressure_level
        is not ExecutionPressureLevel.HIGH
        or snapshot.recent_algedonic_signals >= 1,
        truth_label=ExecTruthLabel.LIVE,
        created_at_tick=snapshot.created_at_tick,
    )


@dataclass(frozen=True)
class BackpressureDecision(_ExecCanonicalMixin):
    """ALLOW/HOLD/DELAY/BLOCK/ESCALATE/ERROR from pressure. Not recovery."""

    backpressure_decision_id: str
    pressure_snapshot_id: str
    decision: BackpressureDecisionKind
    reason: str
    hold_new_work: bool
    delay_new_work: bool
    block_new_work: bool
    requires_operator_attention: bool
    truth_label: ExecTruthLabel
    contract_version: str = BACKPRESSURE_DECISION_VERSION
    signal_id: str | None = None
    recommended_delay_ms: int | None = None
    executes_retry: bool = False
    executes_recovery: bool = False
    executes_rollback: bool = False
    grants_authority: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "backpressure_decision_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(
            self,
            "executes_retry",
            "executes_recovery",
            "executes_rollback",
            "grants_authority",
        )
        expected = {
            BackpressureDecisionKind.ALLOW: (False, False, False),
            BackpressureDecisionKind.HOLD: (True, False, False),
            BackpressureDecisionKind.DELAY: (False, True, False),
            BackpressureDecisionKind.BLOCK: (False, False, True),
            BackpressureDecisionKind.ESCALATE: (False, False, True),
            BackpressureDecisionKind.ERROR: (False, False, True),
        }[self.decision]
        if (self.hold_new_work, self.delay_new_work, self.block_new_work) != expected:
            raise AurelExecValidationError(
                "hold/delay/block flags must agree with the decision kind",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="decision",
            )

    @property
    def decision_hash(self) -> str:
        return stable_hash(self)


def decide_backpressure(
    snapshot: ExecutionPressureSnapshot,
    *,
    signal: BackpressureSignal | None = None,
) -> BackpressureDecision:
    """Deterministic backpressure verdict. Shapes admission; repairs nothing."""
    def _make(kind, reason, *, delay=None, attention=False):
        flags = {
            BackpressureDecisionKind.ALLOW: (False, False, False),
            BackpressureDecisionKind.HOLD: (True, False, False),
            BackpressureDecisionKind.DELAY: (False, True, False),
            BackpressureDecisionKind.BLOCK: (False, False, True),
            BackpressureDecisionKind.ESCALATE: (False, False, True),
            BackpressureDecisionKind.ERROR: (False, False, True),
        }[kind]
        return BackpressureDecision(
            backpressure_decision_id="exec-bpdec-"
            + stable_hash((snapshot.pressure_snapshot_id, kind.value))[:16],
            pressure_snapshot_id=snapshot.pressure_snapshot_id,
            decision=kind,
            reason=reason,
            hold_new_work=flags[0],
            delay_new_work=flags[1],
            block_new_work=flags[2],
            requires_operator_attention=attention,
            truth_label=ExecTruthLabel.LIVE,
            signal_id=signal.backpressure_signal_id if signal is not None else None,
            recommended_delay_ms=delay,
        )

    level = snapshot.pressure_level
    if level is ExecutionPressureLevel.ERROR:
        return _make(
            BackpressureDecisionKind.ERROR,
            "invalid pressure inputs; admission blocked fail-closed",
            attention=True,
        )
    if level is ExecutionPressureLevel.CRITICAL:
        return _make(
            BackpressureDecisionKind.ESCALATE,
            "critical local pressure: block new work and escalate to the "
            "operator — escalation is visibility, not authority",
            attention=True,
        )
    if level is ExecutionPressureLevel.HIGH:
        if snapshot.available_slots == 0:
            return _make(
                BackpressureDecisionKind.BLOCK,
                "high pressure with no available slots: new work blocked",
                attention=True,
            )
        return _make(
            BackpressureDecisionKind.DELAY,
            "high local pressure: delay new work",
            delay=300,
            attention=snapshot.recent_algedonic_signals >= 1,
        )
    if level is ExecutionPressureLevel.ELEVATED and snapshot.available_slots == 0:
        return _make(
            BackpressureDecisionKind.HOLD,
            "elevated pressure with no available slots: hold new work",
        )
    return _make(
        BackpressureDecisionKind.ALLOW,
        "pressure acceptable: new work may proceed to the existing "
        "admission/lease/claim/bridge guard chain",
    )

"""P4-EXEC-A AurelExec contract types, truth labels, and doctrine constants.

P4 doctrine / kernel boundary lock:

    P4-EXEC-A creates the execution gate and the execution key.
    It does not turn the key.

    A P3 candidate is not admission.
    An admission decision is not authorization.
    A lease is not execution.
    A job is not runtime execution.
    An attempt skeleton is not runtime.submit.
    Runtime success is not semantic success.
    Trace-bound is not trace-verified.
    Policy shadow is not policy enforcement.
    A projection is not execution.

Nothing in this package calls AgenticRuntime.submit, dispatches a tool,
invokes a model or verifier, executes code or a sandbox, opens a network
or subprocess side effect, writes Trace/Ledger, or mutates memory, policy,
or identity state. runtime.submit belongs to P4-EXEC-B; trace verification
belongs to P5 AurelTrace; authorization and enforcement belong to P9 Custos.

The truth-label vocabulary here is deliberately narrower than P3's
``FlowTruthLabel``: ``ExecTruthLabel`` has no TRACE_VERIFIED member, so a
trace-verified claim is structurally unconstructible in P4-EXEC-A.
Canonical serialization helpers are reused from ``aurel_flow.types`` so the
existing canon does not fragment.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from ..aurel_flow.types import (
    canonical_dataclass_dict,
    stable_hash,
    to_canonical_json,
)
from .exec_errors import AurelExecErrorCode, AurelExecValidationError

AUREL_EXEC_CONTRACT_VERSION = "aurel_exec.v1"
AUREL_EXEC_PACK_ID = "P4-EXEC-A"
AUREL_EXEC_PACK_TITLE = "AurelExec Doctrine / Contracts / Admission / Lease Foundation"
AUREL_EXEC_REPORT_PATH = "agent/reports/P4_EXEC_A_ADMISSION_LEASE_FOUNDATION.md"

RUNTIME_SUBMIT_UNAVAILABLE_REASON = (
    "runtime.submit is never called at admission/lease time; execution is "
    "available only through the P4-EXEC-B ExecRuntimeBridge with a valid "
    "lease and session on the supported read-only path"
)
RAW_EXECUTION_UNAVAILABLE_REASON = (
    "no tool, model, verifier, terminal, code, sandbox, subprocess, or network "
    "action is executed in P4-EXEC-A; admission and lease are eligibility only"
)
TRACE_VERIFICATION_UNAVAILABLE_REASON = (
    "trace verification is not implemented in P4-EXEC-A; the evidence spine "
    "belongs to P5 AurelTrace — trace-bound is not trace-verified"
)
CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON = (
    "Custos/P9 enforcement is not implemented in P4-EXEC-A; admission is a "
    "structural gate, not authorization — authority belongs to P9 Custos"
)
POLICY_SHADOW_ONLY_REASON = (
    "policy context is referenced shadow-only in P4-EXEC-A (Custos v0 shadow "
    "resolver exists in repo canon); nothing here enforces policy"
)
SHELL_PROJECTION_UNAVAILABLE_REASON = (
    "no Shell UI, React frontend, or API server projects AurelExec state in "
    "P4-EXEC-A; ExecProjection is a Python read model only"
)
PERSISTENCE_UNAVAILABLE_REASON = (
    "all AurelExec state is in-memory only in P4-EXEC-A; no database, file, "
    "event store, or external persistence exists"
)

P3_READY_MARKER = "READY_BUT_NO_P4"
"""The P3-FLOW-I dispatchability reason marking a fully ready candidate.

P3 readiness is not P4 admission: carrying this marker only lets a request
enter the gate chain; every later gate can still hold or reject it.
"""


class ExecTruthLabel(str, Enum):
    """Honest truth labels for AurelExec objects.

    LIVE is assignable only to P4-EXEC-B bridge results/outcomes produced by
    an actual ``AgenticRuntime.submit()`` call; admission/lease/job/attempt
    eligibility objects still reject it fail-closed at construction.
    TRACE_BOUND (added by P4-EXEC-B) is assignable only when an actual
    runtime trace/transition ref was captured. There is deliberately no
    TRACE_VERIFIED member — that claim is structurally unconstructible
    until P5 AurelTrace performs real verification.
    """

    LIVE = "LIVE"
    TRACE_BOUND = "TRACE_BOUND"
    DEV_FIXTURE = "DEV_FIXTURE"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    RUNTIME_SUBMIT_UNAVAILABLE = "RUNTIME_SUBMIT_UNAVAILABLE"
    TRACE_BOUND_UNAVAILABLE = "TRACE_BOUND_UNAVAILABLE"
    TRACE_VERIFIED_UNAVAILABLE = "TRACE_VERIFIED_UNAVAILABLE"
    POLICY_SHADOW = "POLICY_SHADOW"
    POLICY_ENFORCED_UNAVAILABLE = "POLICY_ENFORCED_UNAVAILABLE"


FORBIDDEN_EXEC_TRUTH_LABELS: tuple[ExecTruthLabel, ...] = (ExecTruthLabel.LIVE,)


class ExecAdmissionState(str, Enum):
    ADMIT = "ADMIT"
    HOLD = "HOLD"
    REJECT = "REJECT"
    REQUIRE_OPERATOR = "REQUIRE_OPERATOR"
    REQUIRE_POLICY = "REQUIRE_POLICY"
    REQUIRE_VERIFIER = "REQUIRE_VERIFIER"
    REQUIRE_CONTEXT_REFRESH = "REQUIRE_CONTEXT_REFRESH"
    ERROR = "ERROR"


class ExecLifecycleState(str, Enum):
    """Closed-world job/attempt lifecycle.

    P4-EXEC-A shipped the eligibility states only; P4-EXEC-B adds the
    submit-aware states (SESSION_BOUND, READY_TO_SUBMIT, RUNNING, SUBMITTED,
    SUCCEEDED, FAILED) because a real governed submit bridge now exists.
    ATTEMPT_PENDING doubles as the attempt's PENDING state. There is still
    no EXECUTED/COMPLETED/VERIFIED member: SUCCEEDED means runtime submit
    success only — runtime success is not semantic success and not proof.
    """

    CANDIDATE = "CANDIDATE"
    ADMITTED = "ADMITTED"
    LEASED = "LEASED"
    SESSION_BOUND = "SESSION_BOUND"
    ATTEMPT_PENDING = "ATTEMPT_PENDING"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    RUNNING = "RUNNING"
    SUBMITTED = "SUBMITTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


JOB_LIFECYCLE_TRANSITIONS: dict[ExecLifecycleState, tuple[ExecLifecycleState, ...]] = {
    ExecLifecycleState.CANDIDATE: (
        ExecLifecycleState.ADMITTED,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.ADMITTED: (
        ExecLifecycleState.LEASED,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.LEASED: (
        ExecLifecycleState.SESSION_BOUND,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.SESSION_BOUND: (
        ExecLifecycleState.ATTEMPT_PENDING,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.ATTEMPT_PENDING: (
        ExecLifecycleState.RUNNING,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.RUNNING: (
        ExecLifecycleState.SUCCEEDED,
        ExecLifecycleState.FAILED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.READY_TO_SUBMIT: (),
    ExecLifecycleState.SUBMITTED: (),
    ExecLifecycleState.SUCCEEDED: (),
    ExecLifecycleState.FAILED: (),
    ExecLifecycleState.BLOCKED: (),
    ExecLifecycleState.ERROR: (),
}
"""Deterministic ExecJob transition map. READY_TO_SUBMIT/SUBMITTED are
attempt-only states and are unreachable for jobs."""

ATTEMPT_LIFECYCLE_TRANSITIONS: dict[ExecLifecycleState, tuple[ExecLifecycleState, ...]] = {
    ExecLifecycleState.ATTEMPT_PENDING: (
        ExecLifecycleState.READY_TO_SUBMIT,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.READY_TO_SUBMIT: (
        ExecLifecycleState.RUNNING,
        ExecLifecycleState.BLOCKED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.RUNNING: (
        ExecLifecycleState.SUBMITTED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.SUBMITTED: (
        ExecLifecycleState.SUCCEEDED,
        ExecLifecycleState.FAILED,
        ExecLifecycleState.ERROR,
    ),
    ExecLifecycleState.CANDIDATE: (),
    ExecLifecycleState.ADMITTED: (),
    ExecLifecycleState.LEASED: (),
    ExecLifecycleState.SESSION_BOUND: (),
    ExecLifecycleState.SUCCEEDED: (),
    ExecLifecycleState.FAILED: (),
    ExecLifecycleState.BLOCKED: (),
    ExecLifecycleState.ERROR: (),
}
"""Deterministic ExecutionAttempt transition map. ATTEMPT_PENDING is the
attempt's PENDING state; job-only states are unreachable for attempts."""

SUBMIT_AWARE_ATTEMPT_STATES: tuple[ExecLifecycleState, ...] = (
    ExecLifecycleState.SUBMITTED,
    ExecLifecycleState.SUCCEEDED,
    ExecLifecycleState.FAILED,
)
"""The only attempt states in which runtime_submit_called=True is
constructible. An attempt claiming a submit before submitting is impossible."""


class ExecutionMode(str, Enum):
    TOOL = "TOOL"
    MODEL = "MODEL"
    TERMINAL = "TERMINAL"
    CODE = "CODE"
    CONVERSATION = "CONVERSATION"
    COMPOSITE = "COMPOSITE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


SANDBOX_REQUIRED_MODES: tuple[ExecutionMode, ...] = (
    ExecutionMode.TOOL,
    ExecutionMode.TERMINAL,
    ExecutionMode.CODE,
    ExecutionMode.COMPOSITE,
)
VERIFIER_REQUIRED_MODES: tuple[ExecutionMode, ...] = (
    ExecutionMode.TERMINAL,
    ExecutionMode.CODE,
    ExecutionMode.COMPOSITE,
)


class ExecutionTopologyKind(str, Enum):
    SINGLE_IN_PROCESS = "SINGLE_IN_PROCESS"
    LINEAR = "LINEAR"
    CASCADE = "CASCADE"
    PARALLEL_FANOUT = "PARALLEL_FANOUT"
    SUPERVISOR = "SUPERVISOR"
    FILTER_CHAIN = "FILTER_CHAIN"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ExecutionPlasticityLevel(str, Enum):
    STATIC_TEMPLATE = "STATIC_TEMPLATE"
    DYNAMIC_SELECTION = "DYNAMIC_SELECTION"
    PRE_EXECUTION_GENERATION = "PRE_EXECUTION_GENERATION"
    IN_EXECUTION_EDITING_UNAVAILABLE = "IN_EXECUTION_EDITING_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ExecutionFailureClass(str, Enum):
    NONE = "NONE"
    INVALID_SOURCE = "INVALID_SOURCE"
    MISSING_REQUIREMENT = "MISSING_REQUIREMENT"
    POLICY_REQUIRED = "POLICY_REQUIRED"
    OPERATOR_REQUIRED = "OPERATOR_REQUIRED"
    VERIFIER_REQUIRED = "VERIFIER_REQUIRED"
    CONTEXT_REFRESH_REQUIRED = "CONTEXT_REFRESH_REQUIRED"
    LEASE_INVALID = "LEASE_INVALID"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    LEASE_REVOKED = "LEASE_REVOKED"
    RUNTIME_SUBMIT_UNAVAILABLE = "RUNTIME_SUBMIT_UNAVAILABLE"
    ERROR = "ERROR"


class RecoveryActionKind(str, Enum):
    NONE = "NONE"
    HOLD = "HOLD"
    REJECT = "REJECT"
    REQUIRE_OPERATOR = "REQUIRE_OPERATOR"
    REQUIRE_POLICY = "REQUIRE_POLICY"
    REQUIRE_VERIFIER = "REQUIRE_VERIFIER"
    REQUIRE_CONTEXT_REFRESH = "REQUIRE_CONTEXT_REFRESH"
    ESCALATE = "ESCALATE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class AlgedonicSignalKind(str, Enum):
    NONE = "NONE"
    BUDGET_EXHAUSTION = "BUDGET_EXHAUSTION"
    RETRY_STORM = "RETRY_STORM"
    SEMANTIC_SILENT_FAILURE = "SEMANTIC_SILENT_FAILURE"
    SANDBOX_ANOMALY = "SANDBOX_ANOMALY"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    TRACE_BINDING_FAILURE = "TRACE_BINDING_FAILURE"
    OPERATOR_ESCALATION = "OPERATOR_ESCALATION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class TraceBindingStatus(str, Enum):
    """Closed-world trace binding posture. There is no BOUND or VERIFIED
    member: binding belongs to P4-EXEC-B/P5 and verification to P5 only."""

    UNAVAILABLE = "UNAVAILABLE"
    TRACE_BOUND_UNAVAILABLE = "TRACE_BOUND_UNAVAILABLE"
    TRACE_VERIFIED_UNAVAILABLE = "TRACE_VERIFIED_UNAVAILABLE"
    ERROR = "ERROR"


class ExecPolicyStatus(str, Enum):
    """No ENFORCED member: policy enforcement is unconstructible in P4."""

    SHADOW_ONLY = "SHADOW_ONLY"
    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    ERROR = "ERROR"


class ExecCustosStatus(str, Enum):
    """No ENFORCED/AUTHORIZED member: Custos authority is unconstructible
    in P4 — authorization belongs to P9."""

    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    SHADOW_ONLY = "SHADOW_ONLY"
    ERROR = "ERROR"


class ExecTraceStatus(str, Enum):
    """No VERIFIED member: trace verification is unconstructible in P4."""

    TRACE_BINDING_UNAVAILABLE = "TRACE_BINDING_UNAVAILABLE"
    TRACE_VERIFICATION_UNAVAILABLE = "TRACE_VERIFICATION_UNAVAILABLE"
    ERROR = "ERROR"


class ExecUnavailableSystem(str, Enum):
    RUNTIME_SUBMIT = "RUNTIME_SUBMIT"
    RAW_EXECUTION = "RAW_EXECUTION"
    TRACE_VERIFICATION = "TRACE_VERIFICATION"
    CUSTOS_ENFORCEMENT = "CUSTOS_ENFORCEMENT"
    POLICY_ENFORCEMENT = "POLICY_ENFORCEMENT"
    SHELL_PROJECTION = "SHELL_PROJECTION"
    PERSISTENCE = "PERSISTENCE"


class ExecMissingRequirementKind(str, Enum):
    SOURCE_REF = "SOURCE_REF"
    SOURCE_READINESS_MARKER = "SOURCE_READINESS_MARKER"
    AUTHORITY_REF = "AUTHORITY_REF"
    SANDBOX_PROFILE = "SANDBOX_PROFILE"
    BUDGET_REF = "BUDGET_REF"
    VERIFIER_REF = "VERIFIER_REF"
    POLICY_CONTEXT_REF = "POLICY_CONTEXT_REF"
    VALID_LEASE = "VALID_LEASE"


class ExecAdmissionGateKind(str, Enum):
    """Closed-world NCF-style gate chain order for deterministic admission."""

    SOURCE_VALIDITY = "SOURCE_VALIDITY"
    P3_READINESS_MARKER = "P3_READINESS_MARKER"
    AUTHORITY_REF = "AUTHORITY_REF"
    SANDBOX_PROFILE = "SANDBOX_PROFILE"
    BUDGET_REF = "BUDGET_REF"
    VERIFIER_REQUIREMENT = "VERIFIER_REQUIREMENT"
    TRACE_BINDING_AVAILABILITY = "TRACE_BINDING_AVAILABILITY"
    POLICY_CUSTOS_AVAILABILITY = "POLICY_CUSTOS_AVAILABILITY"


ADMISSION_GATE_ORDER: tuple[ExecAdmissionGateKind, ...] = (
    ExecAdmissionGateKind.SOURCE_VALIDITY,
    ExecAdmissionGateKind.P3_READINESS_MARKER,
    ExecAdmissionGateKind.AUTHORITY_REF,
    ExecAdmissionGateKind.SANDBOX_PROFILE,
    ExecAdmissionGateKind.BUDGET_REF,
    ExecAdmissionGateKind.VERIFIER_REQUIREMENT,
    ExecAdmissionGateKind.TRACE_BINDING_AVAILABILITY,
    ExecAdmissionGateKind.POLICY_CUSTOS_AVAILABILITY,
)


class _ExecCanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return canonical_dataclass_dict(self)

    def stable_hash(self) -> str:
        return stable_hash(self)


def require_nonempty(obj: object, field_name: str, *, code: AurelExecErrorCode) -> None:
    value = getattr(obj, field_name)
    if not isinstance(value, str) or not value.strip():
        raise AurelExecValidationError(
            f"{type(obj).__name__}.{field_name} must be a non-empty string",
            code=code,
            field=field_name,
        )


def require_allowed_truth_label(obj: object, field_name: str = "truth_label") -> None:
    label = getattr(obj, field_name)
    if label in FORBIDDEN_EXEC_TRUTH_LABELS:
        raise AurelExecValidationError(
            f"{type(obj).__name__}.{field_name} may not claim {label.value} in P4-EXEC-A",
            code=AurelExecErrorCode.FORBIDDEN_TRUTH_LABEL,
            field=field_name,
        )


def forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelExecValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False in P4-EXEC-A",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelExecValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True in P4-EXEC-A",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )

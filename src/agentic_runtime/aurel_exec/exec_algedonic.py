"""P4-EXEC-E algedonic signals + runtime substrate boundary proofs.

An ``AlgedonicSignal`` is urgent local visibility for critical/severe
failure — the pain channel that must not be lost in ordinary reporting. It
executes nothing, grants no authority, and does not bypass Custos; those
claims are structurally unconstructible. The escalation-kind vocabulary is
E-local (``AlgedonicEscalationKind``) because the A-pack already exports an
`AlgedonicSignalKind` vocabulary with different future-facing members.

This module also carries the runtime substrate boundary proofs: Python
AurelExec v1 is the governance/control/reference layer, not the final
deterministic durable execution substrate. Deterministic replay, durable
event logs, exact workflow copy/fork, and any Rust/WASM implementation are
explicitly not implemented here and remain a future extraction boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode
from .exec_failure import FailureClass, FailureClassification, FailureSeverity
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

ALGEDONIC_SIGNAL_VERSION = "algedonic_signal.v1"
NO_FINAL_PYTHON_KERNEL_CLAIM_PROOF_VERSION = "no_final_python_kernel_claim_proof.v1"
NO_RUST_REWRITE_PROOF_VERSION = "no_rust_rewrite_proof.v1"

ALGEDONIC_AUTHORITY_BOUNDARY_REASON = (
    "an algedonic signal is urgent operator visibility only; it executes no "
    "action, grants no authority, and does not bypass Custos — escalated "
    "authorization belongs to P9"
)
RUNTIME_SUBSTRATE_BOUNDARY_REASON = (
    "Python AurelExec v1 is the governance/control/reference layer and "
    "contract authority; it is not the final deterministic durable "
    "execution substrate — deterministic replay, durable event logs, exact "
    "workflow copy/fork, and worker-lease kernels remain a future "
    "extraction boundary that a later substrate may implement against "
    "these serializable contracts"
)


class AlgedonicSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class AlgedonicEscalationKind(str, Enum):
    RUNTIME_FAILURE = "RUNTIME_FAILURE"
    POLICY_CONFLICT = "POLICY_CONFLICT"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    REPEATED_FAILURE = "REPEATED_FAILURE"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    UNSAFE_MODE_REQUEST = "UNSAFE_MODE_REQUEST"
    UNKNOWN_CRITICAL = "UNKNOWN_CRITICAL"


_SIGNAL_WORTHY_SEVERITIES = (FailureSeverity.URGENT, FailureSeverity.CRITICAL)

_KIND_BY_FAILURE_CLASS: dict[FailureClass, AlgedonicEscalationKind] = {
    FailureClass.POLICY_BLOCKED: AlgedonicEscalationKind.POLICY_CONFLICT,
    FailureClass.VERIFICATION_FAILED: AlgedonicEscalationKind.VERIFICATION_FAILURE,
    FailureClass.OUTPUT_CONTRACT_FAILED: AlgedonicEscalationKind.VERIFICATION_FAILURE,
    FailureClass.RESOURCE_EXHAUSTED: AlgedonicEscalationKind.RESOURCE_EXHAUSTION,
    FailureClass.MODE_UNAVAILABLE: AlgedonicEscalationKind.UNSAFE_MODE_REQUEST,
    FailureClass.UNKNOWN_ERROR: AlgedonicEscalationKind.UNKNOWN_CRITICAL,
}


@dataclass(frozen=True)
class AlgedonicSignal(_ExecCanonicalMixin):
    """Urgent local visibility. Not authority, not action, not a bypass."""

    algedonic_signal_id: str
    exec_job_id: str
    severity: AlgedonicSeverity
    signal_kind: AlgedonicEscalationKind
    message: str
    operator_attention_required: bool
    truth_label: ExecTruthLabel
    contract_version: str = ALGEDONIC_SIGNAL_VERSION
    attempt_id: str | None = None
    failure_classification_id: str | None = None
    created_at_tick: int | None = None
    grants_authority: bool = False
    bypasses_custos: bool = False
    executes_action: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "algedonic_signal_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "message", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "grants_authority", "bypasses_custos", "executes_action")

    @property
    def signal_hash(self) -> str:
        return stable_hash(self)


def create_algedonic_signal_if_needed(
    classification: FailureClassification,
    *,
    created_at_tick: int | None = None,
    repeated_failure: bool = False,
) -> AlgedonicSignal | None:
    """Emit an urgent signal for URGENT/CRITICAL failure; otherwise None.

    Deterministic over its inputs. ``repeated_failure`` is caller-supplied
    local evidence (no failure history store exists in this pack).
    """
    if classification.severity not in _SIGNAL_WORTHY_SEVERITIES:
        return None
    kind = (
        AlgedonicEscalationKind.REPEATED_FAILURE
        if repeated_failure
        else _KIND_BY_FAILURE_CLASS.get(
            classification.failure_class, AlgedonicEscalationKind.RUNTIME_FAILURE
        )
    )
    severity = (
        AlgedonicSeverity.CRITICAL
        if classification.severity is FailureSeverity.CRITICAL
        else AlgedonicSeverity.URGENT
    )
    return AlgedonicSignal(
        algedonic_signal_id="exec-algedonic-"
        + stable_hash(
            (classification.failure_classification_id, kind.value, repeated_failure)
        )[:16],
        exec_job_id=classification.exec_job_id,
        severity=severity,
        signal_kind=kind,
        message=(
            f"{severity.value} {kind.value}: {classification.reason[:200]} — "
            "urgent visibility only; authority remains with the operator and P9"
        ),
        operator_attention_required=True,
        truth_label=ExecTruthLabel.LIVE,
        attempt_id=classification.attempt_id,
        failure_classification_id=classification.failure_classification_id,
        created_at_tick=created_at_tick,
    )


@dataclass(frozen=True)
class NoFinalPythonKernelClaimProof(_ExecCanonicalMixin):
    """Evidence that Python v1 is not claimed as the final durable kernel."""

    reason: str
    contract_version: str = NO_FINAL_PYTHON_KERNEL_CLAIM_PROOF_VERSION
    python_final_kernel_claim: bool = False
    python_is_v1_reference_and_control_layer: bool = True
    deterministic_replay_engine_available: bool = False
    durable_event_log_available: bool = False
    workflow_exact_copy_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "python_final_kernel_claim",
            "deterministic_replay_engine_available",
            "durable_event_log_available",
            "workflow_exact_copy_available",
        )
        forbid_false(self, "python_is_v1_reference_and_control_layer")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_final_python_kernel_claim_proof() -> NoFinalPythonKernelClaimProof:
    return NoFinalPythonKernelClaimProof(reason=RUNTIME_SUBSTRATE_BOUNDARY_REASON)


@dataclass(frozen=True)
class NoRustRewriteProof(_ExecCanonicalMixin):
    """Evidence that no Rust/WASM substrate work was started in this pack."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_RUST_REWRITE_PROOF_VERSION
    rust_wasm_substrate_available: bool = False
    rust_code_added: bool = False
    wasm_runtime_added: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self, "rust_wasm_substrate_available", "rust_code_added", "wasm_runtime_added"
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_rust_rewrite_proof() -> NoRustRewriteProof:
    return NoRustRewriteProof(
        reason=RUNTIME_SUBSTRATE_BOUNDARY_REASON,
        future_pack_owner=(
            "future runtime substrate extraction (operator-decided; e.g. "
            "P4-EXEC-RUST-BRIDGE-DOCTRINE)"
        ),
    )

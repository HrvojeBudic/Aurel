"""P4-EXEC-E execution verification — runtime success is not semantic success.

An ``ExecutionVerificationRequest`` asks for judgment over one
``ExecutionOutcome``; an ``ExecutionVerificationDecision`` answers honestly:
PASSED only with actual verifier evidence, FAILED when the outcome or
evidence contradicts the claim, UNAVAILABLE/INCONCLUSIVE with reasons when
no verifier can speak, REQUIRES_OPERATOR_REVIEW when a human must decide.
``verified=True`` without evidence is unconstructible.

A ``VerifierHook`` is a side-effect-free judgment interface description: it
calls no model, no tool, no terminal, no code, mutates no runtime state,
and writes no trace/ledger proof — those claims are structurally
unconstructible. A verification decision is P4-local judgment, never P5
trace verification: ``requires_p5_proof`` is structurally True.

Contracts here are kept primitive/serializable (str/bool/int/tuple fields,
stable hashes) so a future non-Python substrate can implement them without
redefining governance semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

EXECUTION_VERIFICATION_REQUEST_VERSION = "execution_verification_request.v1"
EXECUTION_VERIFICATION_DECISION_VERSION = "execution_verification_decision.v1"
VERIFIER_HOOK_VERSION = "verifier_hook.v1"
NO_MODEL_VERIFIER_CALL_PROOF_VERSION = "no_model_verifier_call_proof.v1"
NO_P5_PROOF_PROOF_VERSION = "no_p5_proof_proof.v1"
NO_P9_AUTHORITY_PROOF_VERSION = "no_p9_authority_proof.v1"

VERIFIER_UNAVAILABLE_REASON = (
    "no concrete verifier evidence source exists in P4-EXEC-E; the hook "
    "interface is profile-only and P5 AurelTrace proof remains required"
)
MODEL_VERIFIER_CALL_UNAVAILABLE_REASON = (
    "no model API is called for verification; a model-judge verifier "
    "requires router/budget/contract canon in a future pack"
)
P5_PROOF_UNAVAILABLE_REASON = (
    "a P4 verification decision is local judgment, never P5 trace "
    "verification; the evidence spine belongs to P5 AurelTrace"
)
P9_AUTHORITY_UNAVAILABLE_REASON = (
    "no judgment object grants or enforces authority; high-risk recovery, "
    "retry, rollback, and escalation authorization belong to P9 Custos"
)


class VerificationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    ERROR = "ERROR"


class VerifierHookAvailability(str, Enum):
    """No AVAILABLE member: a concrete evidence-producing verifier does not
    exist in this pack — hooks are profile-only or unavailable."""

    PROFILE_ONLY = "PROFILE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ExecutionVerificationRequest(_ExecCanonicalMixin):
    """A request for judgment over one outcome. Requesting verifies nothing."""

    verification_request_id: str
    exec_job_id: str
    session_id: str
    attempt_id: str
    outcome_id: str
    requested_execution_mode: str
    verification_scope: str
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_VERIFICATION_REQUEST_VERSION
    mode_profile_id: str | None = None
    expected_contract_ref: str | None = None
    semantic_guard_ref: str | None = None
    created_at_tick: int | None = None
    executes: bool = False
    writes_p5_proof: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "verification_request_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "outcome_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "verification_scope", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "executes", "writes_p5_proof")

    @property
    def request_hash(self) -> str:
        return stable_hash(self)


def build_execution_verification_request(
    outcome: Any,
    *,
    requested_execution_mode: ExecutionMode,
    verification_scope: str = "runtime outcome semantic acceptability",
    mode_profile_id: str | None = None,
    expected_contract_ref: str | None = None,
    semantic_guard_ref: str | None = None,
    created_at_tick: int | None = None,
) -> ExecutionVerificationRequest:
    """Build a verification request from an ExecutionOutcome-shaped object."""
    request_id = "exec-verify-req-" + stable_hash(
        (outcome.outcome_id, verification_scope)
    )[:16]
    return ExecutionVerificationRequest(
        verification_request_id=request_id,
        exec_job_id=outcome.exec_job_id,
        session_id=outcome.session_id,
        attempt_id=outcome.attempt_id,
        outcome_id=outcome.outcome_id,
        requested_execution_mode=requested_execution_mode.value,
        verification_scope=verification_scope,
        truth_label=ExecTruthLabel.LIVE,
        mode_profile_id=mode_profile_id,
        expected_contract_ref=expected_contract_ref,
        semantic_guard_ref=semantic_guard_ref,
        created_at_tick=created_at_tick,
    )


@dataclass(frozen=True)
class VerifierHook(_ExecCanonicalMixin):
    """Side-effect-free verifier / semantic guard interface description.

    A hook that calls models/tools, executes, mutates runtime state, or
    writes proof is unconstructible.
    """

    verifier_hook_id: str
    hook_name: str
    supported_modes: tuple[str, ...]
    availability_status: VerifierHookAvailability
    truth_label: ExecTruthLabel
    contract_version: str = VERIFIER_HOOK_VERSION
    side_effect_free: bool = True
    requires_contract: bool = True
    unavailable_reason: str | None = None
    calls_model: bool = False
    calls_tools: bool = False
    executes_terminal_or_code: bool = False
    mutates_runtime_state: bool = False
    writes_trace_proof: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "verifier_hook_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "hook_name", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_false(self, "side_effect_free")
        forbid_true(
            self,
            "calls_model",
            "calls_tools",
            "executes_terminal_or_code",
            "mutates_runtime_state",
            "writes_trace_proof",
        )
        if (
            self.availability_status is VerifierHookAvailability.UNAVAILABLE
            and not self.unavailable_reason
        ):
            raise AurelExecValidationError(
                "an unavailable hook must explain itself",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="unavailable_reason",
            )


def build_profile_only_verifier_hook(
    *, hook_name: str = "semantic-guard-profile", supported_modes: tuple[str, ...] = ("TOOL",)
) -> VerifierHook:
    return VerifierHook(
        verifier_hook_id="exec-verifier-hook-" + stable_hash(hook_name)[:16],
        hook_name=hook_name,
        supported_modes=supported_modes,
        availability_status=VerifierHookAvailability.PROFILE_ONLY,
        # PROFILE_ONLY posture is carried by the availability status per
        # DEC-P4EXECD-02; the truth label stays honestly UNAVAILABLE.
        truth_label=ExecTruthLabel.UNAVAILABLE,
        unavailable_reason=VERIFIER_UNAVAILABLE_REASON,
    )


@dataclass(frozen=True)
class ExecutionVerificationDecision(_ExecCanonicalMixin):
    """P4-local verification decision. Never P5 trace verification.

    ``verified=True`` requires PASSED status, availability, and actual
    evidence refs; anything else is unconstructible. UNAVAILABLE requires a
    reason. ``requires_p5_proof`` and ``trace_verified=False`` are structural.
    """

    verification_decision_id: str
    verification_request_id: str
    outcome_id: str
    verified: bool
    verification_available: bool
    verification_status: VerificationStatus
    reason: str
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_VERIFICATION_DECISION_VERSION
    missing_evidence: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    requires_p5_proof: bool = True
    requires_operator_review: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "verification_decision_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_false(self, "requires_p5_proof")
        forbid_true(self, "trace_verified")
        if self.verified:
            if self.verification_status is not VerificationStatus.PASSED:
                raise AurelExecValidationError(
                    "verified=True requires PASSED status",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="verified",
                )
            if not self.evidence_refs:
                raise AurelExecValidationError(
                    "verified=True requires actual verifier evidence refs",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="evidence_refs",
                )
            if not self.verification_available:
                raise AurelExecValidationError(
                    "verified=True requires verification to be available",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="verification_available",
                )
        if self.verification_status is VerificationStatus.PASSED and not self.verified:
            raise AurelExecValidationError(
                "PASSED status requires verified=True",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="verification_status",
            )
        if self.verification_status is VerificationStatus.UNAVAILABLE and (
            self.verification_available
        ):
            raise AurelExecValidationError(
                "UNAVAILABLE status contradicts verification_available=True",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="verification_available",
            )

    @property
    def decision_hash(self) -> str:
        return stable_hash(self)


def _decision(
    request: ExecutionVerificationRequest,
    *,
    status: VerificationStatus,
    reason: str,
    verified: bool = False,
    available: bool = True,
    missing_evidence: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    requires_operator_review: bool = False,
) -> ExecutionVerificationDecision:
    return ExecutionVerificationDecision(
        verification_decision_id="exec-verify-dec-"
        + stable_hash((request.verification_request_id, status.value))[:16],
        verification_request_id=request.verification_request_id,
        outcome_id=request.outcome_id,
        verified=verified,
        verification_available=available,
        verification_status=status,
        reason=reason,
        truth_label=ExecTruthLabel.LIVE,
        missing_evidence=missing_evidence,
        evidence_refs=evidence_refs,
        requires_operator_review=requires_operator_review,
    )


def decide_verification(
    request: ExecutionVerificationRequest,
    outcome: Any,
    *,
    hook: VerifierHook | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> ExecutionVerificationDecision:
    """Deterministically decide verification status. No side effects.

    Runtime success is not automatically semantic success: a successful
    outcome without a hook and evidence is UNAVAILABLE/INCONCLUSIVE, never
    PASSED. A failed runtime outcome is FAILED. Evidence with no hook is
    unattributable and INCONCLUSIVE.
    """
    if request.outcome_id != outcome.outcome_id:
        return _decision(
            request,
            status=VerificationStatus.ERROR,
            reason="verification request does not match the outcome",
        )
    if not outcome.success:
        return _decision(
            request,
            status=VerificationStatus.FAILED,
            reason=(
                "runtime outcome failed; failure preserved: "
                + (outcome.error_message or "runtime failure")[:200]
            ),
            requires_operator_review=True,
        )
    if hook is None:
        return _decision(
            request,
            status=VerificationStatus.UNAVAILABLE,
            reason=VERIFIER_UNAVAILABLE_REASON,
            available=False,
            missing_evidence=("verifier_hook",),
        )
    if hook.availability_status is VerifierHookAvailability.UNAVAILABLE:
        return _decision(
            request,
            status=VerificationStatus.UNAVAILABLE,
            reason=hook.unavailable_reason or VERIFIER_UNAVAILABLE_REASON,
            available=False,
            missing_evidence=("available_verifier_hook",),
        )
    if request.requested_execution_mode not in hook.supported_modes:
        return _decision(
            request,
            status=VerificationStatus.UNAVAILABLE,
            reason=(
                f"hook {hook.hook_name!r} does not support mode "
                f"{request.requested_execution_mode}"
            ),
            available=False,
            missing_evidence=("mode_supported_verifier_hook",),
        )
    if not evidence_refs:
        return _decision(
            request,
            status=VerificationStatus.INCONCLUSIVE,
            reason=(
                "verifier hook is profile-only and produced no evidence; "
                "runtime success is not semantic success — operator review "
                "or P5 proof required"
            ),
            missing_evidence=("verifier_evidence",),
            requires_operator_review=True,
        )
    return _decision(
        request,
        status=VerificationStatus.PASSED,
        reason=(
            "verifier evidence present for the requested scope; this is "
            "P4-local judgment, not P5 trace verification"
        ),
        verified=True,
        evidence_refs=evidence_refs,
    )


@dataclass(frozen=True)
class NoModelVerifierCallProof(_ExecCanonicalMixin):
    """Evidence that no model API is called for verification."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_MODEL_VERIFIER_CALL_PROOF_VERSION
    model_verifier_call_allowed: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "model_verifier_call_allowed")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_model_verifier_call_proof() -> NoModelVerifierCallProof:
    return NoModelVerifierCallProof(
        reason=MODEL_VERIFIER_CALL_UNAVAILABLE_REASON,
        future_pack_owner="future model-judge pack under router/budget/contract canon",
    )


@dataclass(frozen=True)
class NoP5ProofProof(_ExecCanonicalMixin):
    """Evidence that no P4 judgment object is or writes P5 proof."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_P5_PROOF_PROOF_VERSION
    p5_trace_verification_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "p5_trace_verification_available", "trace_verified")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_p5_proof_proof() -> NoP5ProofProof:
    return NoP5ProofProof(
        reason=P5_PROOF_UNAVAILABLE_REASON, future_pack_owner="P5 AurelTrace"
    )


@dataclass(frozen=True)
class NoP9AuthorityProof(_ExecCanonicalMixin):
    """Evidence that no judgment object grants or enforces authority."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_P9_AUTHORITY_PROOF_VERSION
    p9_full_enforcement_available: bool = False
    authority_granted: bool = False
    custos_bypassed: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self, "p9_full_enforcement_available", "authority_granted", "custos_bypassed"
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_p9_authority_proof() -> NoP9AuthorityProof:
    return NoP9AuthorityProof(
        reason=P9_AUTHORITY_UNAVAILABLE_REASON, future_pack_owner="P9 Custos"
    )

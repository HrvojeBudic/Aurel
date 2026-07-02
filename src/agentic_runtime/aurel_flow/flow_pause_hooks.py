"""P3-FLOW-D deliberation / reasoning pause runtime hooks.

A pause hook is a represented waiting state, nothing more. Reasoning pause is
runtime state, not hidden chain-of-thought capture. Verifier expectation is
not verification. Operator pause requests review but does not authorize.
Evidence pause expects evidence but does not produce proof.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

RUNTIME_PAUSE_HOOK_VERSION = "runtime_pause_hook.v1"
PAUSE_HOOK_READ_MODEL_VERSION = "pause_hook_read_model.v1"

HIDDEN_COT_BOUNDARY_REASON = (
    "reasoning pause hooks store a safe reasoning category and summary only; "
    "hidden chain-of-thought capture is structurally forbidden"
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


class PauseHookReason(str, Enum):
    """Closed-world waiting reasons for runtime pause hooks."""

    WAITING_REASONING = "WAITING_REASONING"
    WAITING_VERIFIER = "WAITING_VERIFIER"
    WAITING_OPERATOR = "WAITING_OPERATOR"
    WAITING_MEDIATION = "WAITING_MEDIATION"
    WAITING_COUNTERARGUMENT = "WAITING_COUNTERARGUMENT"
    WAITING_EVIDENCE = "WAITING_EVIDENCE"
    WAITING_PERMISSION = "WAITING_PERMISSION"
    WAITING_EXECUTOR = "WAITING_EXECUTOR"
    WAITING_PROOF = "WAITING_PROOF"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class PauseHookKind(str, Enum):
    """Which layer the pause hook represents."""

    RUNTIME = "RUNTIME"
    REASONING = "REASONING"
    VERIFIER = "VERIFIER"
    OPERATOR = "OPERATOR"
    EVIDENCE = "EVIDENCE"


@dataclass(frozen=True)
class RuntimePauseHook(_CanonicalMixin):
    """A represented waiting state. Waiting is not executing or authorizing."""

    hook_id: str
    contract_version: str
    hook_kind: PauseHookKind
    reason: PauseHookReason
    target_run_id: str
    target_node_id: str
    waiting_for: str
    safe_state_summary: str
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    resumable: bool = True
    authority_granted: bool = False
    execution_available: bool = False
    verification_performed: bool = False
    evidence_produced: bool = False
    stores_hidden_chain_of_thought: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "execution_available",
            "verification_performed",
            "evidence_produced",
            "stores_hidden_chain_of_thought",
        )


def create_runtime_pause_hook(
    *,
    hook_kind: PauseHookKind,
    reason: PauseHookReason,
    target_run_id: str,
    target_node_id: str,
    waiting_for: str,
    safe_state_summary: str,
    resumable: bool = True,
    metadata: Mapping[str, str] | None = None,
) -> RuntimePauseHook:
    hook_id = "flhook-" + stable_hash(
        {
            "contract_version": RUNTIME_PAUSE_HOOK_VERSION,
            "hook_kind": hook_kind.value,
            "reason": reason.value,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "waiting_for": waiting_for,
        }
    )[:16]
    return RuntimePauseHook(
        hook_id=hook_id,
        contract_version=RUNTIME_PAUSE_HOOK_VERSION,
        hook_kind=hook_kind,
        reason=reason,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        waiting_for=waiting_for,
        safe_state_summary=safe_state_summary,
        truth_label=FlowTruthLabel.INTERNAL_ONLY,
        metadata=dict(metadata or {}),
        resumable=resumable,
    )


@dataclass(frozen=True)
class ReasoningPauseHook(_CanonicalMixin):
    """Waiting on reasoning. Stores a safe category, never hidden chain-of-thought."""

    hook: RuntimePauseHook
    safe_reasoning_category: str
    cot_boundary_reason: str = HIDDEN_COT_BOUNDARY_REASON
    stores_hidden_chain_of_thought: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "stores_hidden_chain_of_thought")
        if self.hook.hook_kind is not PauseHookKind.REASONING:
            raise AurelFlowValidationError(
                "ReasoningPauseHook requires a REASONING hook",
                code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
                field="hook",
            )


def create_reasoning_pause_hook(
    *,
    target_run_id: str,
    target_node_id: str,
    safe_reasoning_category: str,
    safe_state_summary: str,
    reason: PauseHookReason = PauseHookReason.WAITING_REASONING,
) -> ReasoningPauseHook:
    return ReasoningPauseHook(
        hook=create_runtime_pause_hook(
            hook_kind=PauseHookKind.REASONING,
            reason=reason,
            target_run_id=target_run_id,
            target_node_id=target_node_id,
            waiting_for="deliberation to complete",
            safe_state_summary=safe_state_summary,
        ),
        safe_reasoning_category=safe_reasoning_category,
    )


@dataclass(frozen=True)
class VerifierPauseHook(_CanonicalMixin):
    """Waiting on a verifier. Expecting verification is not verifying."""

    hook: RuntimePauseHook
    expected_verifier: str
    verification_expectation: str
    future_p5_required: bool = True
    verification_performed: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "verification_performed", "proof_available", "trace_verified"
        )
        _forbid_false(self, "future_p5_required")
        if self.hook.hook_kind is not PauseHookKind.VERIFIER:
            raise AurelFlowValidationError(
                "VerifierPauseHook requires a VERIFIER hook",
                code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
                field="hook",
            )


def create_verifier_pause_hook(
    *,
    target_run_id: str,
    target_node_id: str,
    expected_verifier: str,
    verification_expectation: str,
) -> VerifierPauseHook:
    return VerifierPauseHook(
        hook=create_runtime_pause_hook(
            hook_kind=PauseHookKind.VERIFIER,
            reason=PauseHookReason.WAITING_VERIFIER,
            target_run_id=target_run_id,
            target_node_id=target_node_id,
            waiting_for=f"verifier {expected_verifier}",
            safe_state_summary=verification_expectation,
        ),
        expected_verifier=expected_verifier,
        verification_expectation=verification_expectation,
    )


@dataclass(frozen=True)
class OperatorPauseHook(_CanonicalMixin):
    """Waiting on operator review. Requesting review is not authorizing."""

    hook: RuntimePauseHook
    review_frame_ref: str
    requested_review: str
    authority_granted: bool = False
    approval_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "authority_granted", "approval_granted", "execution_available")
        if self.hook.hook_kind is not PauseHookKind.OPERATOR:
            raise AurelFlowValidationError(
                "OperatorPauseHook requires an OPERATOR hook",
                code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
                field="hook",
            )


def create_operator_pause_hook(
    *,
    target_run_id: str,
    target_node_id: str,
    review_frame_ref: str,
    requested_review: str,
) -> OperatorPauseHook:
    return OperatorPauseHook(
        hook=create_runtime_pause_hook(
            hook_kind=PauseHookKind.OPERATOR,
            reason=PauseHookReason.WAITING_OPERATOR,
            target_run_id=target_run_id,
            target_node_id=target_node_id,
            waiting_for="operator review",
            safe_state_summary=requested_review,
        ),
        review_frame_ref=review_frame_ref,
        requested_review=requested_review,
    )


@dataclass(frozen=True)
class EvidencePauseHook(_CanonicalMixin):
    """Waiting on evidence. Missing evidence is a failure candidate, not a warning."""

    hook: RuntimePauseHook
    evidence_requirement_ref: str
    missing_evidence_is_failure_candidate: bool = True
    evidence_produced: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "evidence_produced", "proof_available")
        _forbid_false(self, "missing_evidence_is_failure_candidate")
        if self.hook.hook_kind is not PauseHookKind.EVIDENCE:
            raise AurelFlowValidationError(
                "EvidencePauseHook requires an EVIDENCE hook",
                code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
                field="hook",
            )


def create_evidence_pause_hook(
    *,
    target_run_id: str,
    target_node_id: str,
    evidence_requirement_ref: str,
    safe_state_summary: str,
) -> EvidencePauseHook:
    return EvidencePauseHook(
        hook=create_runtime_pause_hook(
            hook_kind=PauseHookKind.EVIDENCE,
            reason=PauseHookReason.WAITING_EVIDENCE,
            target_run_id=target_run_id,
            target_node_id=target_node_id,
            waiting_for="required evidence",
            safe_state_summary=safe_state_summary,
        ),
        evidence_requirement_ref=evidence_requirement_ref,
    )


@dataclass(frozen=True)
class PauseHookReadModel(_CanonicalMixin):
    """Deterministic view over pause hooks. Visibility is not resumption."""

    read_model_version: str
    hook_count: int
    reason_counts: Mapping[str, int]
    kind_counts: Mapping[str, int]
    resumable_count: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    stores_hidden_chain_of_thought: bool = False
    verification_performed_any: bool = False
    authority_granted_any: bool = False
    evidence_produced_any: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "stores_hidden_chain_of_thought",
            "verification_performed_any",
            "authority_granted_any",
            "evidence_produced_any",
            "execution_available",
        )


def build_pause_hook_read_model(
    *, hooks: tuple[RuntimePauseHook, ...]
) -> PauseHookReadModel:
    reason_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for hook in hooks:
        reason_counts[hook.reason.value] = reason_counts.get(hook.reason.value, 0) + 1
        kind_counts[hook.hook_kind.value] = kind_counts.get(hook.hook_kind.value, 0) + 1
    payload = {
        "read_model_version": PAUSE_HOOK_READ_MODEL_VERSION,
        "hook_ids": tuple(hook.hook_id for hook in hooks),
    }
    return PauseHookReadModel(
        read_model_version=PAUSE_HOOK_READ_MODEL_VERSION,
        hook_count=len(hooks),
        reason_counts=reason_counts,
        kind_counts=kind_counts,
        resumable_count=sum(1 for hook in hooks if hook.resumable),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )

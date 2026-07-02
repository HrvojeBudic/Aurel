"""P3-FLOW-G targeted recovery policy / candidate envelope layer (P3.15.15-P3.15.19).

Recovery must be targeted to failure type — no blind retry. The default
policy deterministically maps every closed-world failure kind to a recovery
candidate kind. A recovery candidate is a contract only: it does not
execute, it is not authorized, and it fail-closes into the P3-FLOW-F
checkpoint discipline (pre-recovery checkpoint required, post-recovery
comparison required). Recovery execution belongs to P4 AurelExec, proof to
P5 AurelTrace, and authority over irreversible recovery to P9 Custos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_diagnosis import (
    RootCauseDiagnosis,
    RuntimeFailureKind,
    RuntimeFailureSignal,
)
from .flow_reversible_state import (
    RecoveryCheckpointRequirement,
    create_recovery_checkpoint_requirement,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

TARGETED_RECOVERY_POLICY_VERSION = "targeted_recovery_policy.v1"
RECOVERY_POLICY_RULE_VERSION = "recovery_policy_rule.v1"
RECOVERY_CANDIDATE_SELECTION_VERSION = "recovery_candidate_selection.v1"
RECOVERY_POLICY_READ_MODEL_VERSION = "recovery_policy_read_model.v1"
RECOVERY_CANDIDATE_ENVELOPE_VERSION = "recovery_candidate_envelope.v1"
RECOVERY_CANDIDATE_BOUNDARY_VERSION = "recovery_candidate_boundary.v1"
RECOVERY_CANDIDATE_READ_MODEL_VERSION = "recovery_candidate_read_model.v1"
RECOVERY_EXECUTION_REQUIREMENT_VERSION = "recovery_execution_requirement.v1"
RECOVERY_VERIFICATION_REQUIREMENT_VERSION = "recovery_verification_requirement.v1"

RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON = (
    "a recovery candidate is a targeted contract only; no retry, repair, "
    "refresh, cross-check, verifier insertion, or termination executes in "
    "P3-FLOW-G — execution belongs to P4 AurelExec, proof to P5 AurelTrace, "
    "and authority over irreversible recovery to P9 Custos"
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


class RecoveryCandidateKind(str, Enum):
    """Closed-world targeted recovery candidate vocabulary.

    Every member names a candidate; there is deliberately no EXECUTED,
    APPLIED, or COMPLETED member, so a candidate structurally cannot claim
    it ran.
    """

    BACKOFF_RETRY_CANDIDATE = "BACKOFF_RETRY_CANDIDATE"
    DELAYED_RETRY_CANDIDATE = "DELAYED_RETRY_CANDIDATE"
    ARGUMENT_REPAIR_CANDIDATE = "ARGUMENT_REPAIR_CANDIDATE"
    STRUCTURE_REPAIR_CANDIDATE = "STRUCTURE_REPAIR_CANDIDATE"
    FIELD_COMPLETION_CANDIDATE = "FIELD_COMPLETION_CANDIDATE"
    REFRESH_CONTEXT_CANDIDATE = "REFRESH_CONTEXT_CANDIDATE"
    CROSS_CHECK_SOURCES_CANDIDATE = "CROSS_CHECK_SOURCES_CANDIDATE"
    EVIDENCE_VERIFICATION_CANDIDATE = "EVIDENCE_VERIFICATION_CANDIDATE"
    INSERT_VERIFIER_CANDIDATE = "INSERT_VERIFIER_CANDIDATE"
    PRUNE_RISKY_EDGE_CANDIDATE = "PRUNE_RISKY_EDGE_CANDIDATE"
    USE_FALLBACK_EDGE_CANDIDATE = "USE_FALLBACK_EDGE_CANDIDATE"
    GRACEFUL_TERMINATION_CANDIDATE = "GRACEFUL_TERMINATION_CANDIDATE"
    GRACEFUL_DEGRADATION_CANDIDATE = "GRACEFUL_DEGRADATION_CANDIDATE"
    HUMAN_ESCALATION_CANDIDATE = "HUMAN_ESCALATION_CANDIDATE"
    HOLD_CANDIDATE = "HOLD_CANDIDATE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class RecoveryPolicyRule(_CanonicalMixin):
    """One deterministic failure-kind -> candidate-kind mapping rule."""

    rule_id: str
    rule_version: str
    failure_kind: RuntimeFailureKind
    primary_candidate_kind: RecoveryCandidateKind
    truth_label: FlowTruthLabel
    alternative_candidate_kinds: tuple[RecoveryCandidateKind, ...] = ()
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    rule_executes: bool = False
    rule_grants_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "rule_executes", "rule_grants_authority")


def _make_rule(
    failure_kind: RuntimeFailureKind,
    primary: RecoveryCandidateKind,
    alternatives: tuple[RecoveryCandidateKind, ...] = (),
) -> RecoveryPolicyRule:
    payload = {
        "rule_version": RECOVERY_POLICY_RULE_VERSION,
        "failure_kind": failure_kind.value,
        "primary_candidate_kind": primary.value,
        "alternative_candidate_kinds": tuple(kind.value for kind in alternatives),
    }
    return RecoveryPolicyRule(
        rule_id="flrpr-" + stable_hash(payload)[:16],
        rule_version=RECOVERY_POLICY_RULE_VERSION,
        failure_kind=failure_kind,
        primary_candidate_kind=primary,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        alternative_candidate_kinds=alternatives,
    )


_DEFAULT_RULES: tuple[RecoveryPolicyRule, ...] = (
    _make_rule(
        RuntimeFailureKind.TOOL_TIMEOUT,
        RecoveryCandidateKind.BACKOFF_RETRY_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.TOOL_RATE_LIMITED,
        RecoveryCandidateKind.DELAYED_RETRY_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.TOOL_UNAVAILABLE,
        RecoveryCandidateKind.USE_FALLBACK_EDGE_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.SCHEMA_MISMATCH,
        RecoveryCandidateKind.ARGUMENT_REPAIR_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.MALFORMED_JSON,
        RecoveryCandidateKind.STRUCTURE_REPAIR_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.MISSING_FIELD,
        RecoveryCandidateKind.FIELD_COMPLETION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.TYPE_ERROR,
        RecoveryCandidateKind.ARGUMENT_REPAIR_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.CONTEXT_DECAY,
        RecoveryCandidateKind.REFRESH_CONTEXT_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.STALE_RETRIEVAL,
        RecoveryCandidateKind.REFRESH_CONTEXT_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.CONTRADICTORY_EVIDENCE,
        RecoveryCandidateKind.CROSS_CHECK_SOURCES_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.CONTROL_LOOP_COLLAPSE,
        RecoveryCandidateKind.GRACEFUL_TERMINATION_CANDIDATE,
        (RecoveryCandidateKind.HUMAN_ESCALATION_CANDIDATE,),
    ),
    _make_rule(
        RuntimeFailureKind.RETRY_STORM,
        RecoveryCandidateKind.GRACEFUL_TERMINATION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.NO_PROGRESS,
        RecoveryCandidateKind.HUMAN_ESCALATION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.SEMANTIC_SILENT_FAILURE,
        RecoveryCandidateKind.EVIDENCE_VERIFICATION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.UNSUPPORTED_OUTPUT,
        RecoveryCandidateKind.EVIDENCE_VERIFICATION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.EVIDENCE_MISSING,
        RecoveryCandidateKind.EVIDENCE_VERIFICATION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.TOPOLOGY_AMPLIFICATION_RISK,
        RecoveryCandidateKind.INSERT_VERIFIER_CANDIDATE,
        (RecoveryCandidateKind.PRUNE_RISKY_EDGE_CANDIDATE,),
    ),
    _make_rule(
        RuntimeFailureKind.DIVERSITY_CORRELATION_RISK,
        RecoveryCandidateKind.HUMAN_ESCALATION_CANDIDATE,
        (RecoveryCandidateKind.INSERT_VERIFIER_CANDIDATE,),
    ),
    _make_rule(
        RuntimeFailureKind.CHECKPOINT_REQUIRED_MISSING,
        RecoveryCandidateKind.HOLD_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.UNKNOWN,
        RecoveryCandidateKind.HUMAN_ESCALATION_CANDIDATE,
    ),
    _make_rule(
        RuntimeFailureKind.UNAVAILABLE,
        RecoveryCandidateKind.UNAVAILABLE,
    ),
    _make_rule(
        RuntimeFailureKind.ERROR,
        RecoveryCandidateKind.ERROR,
    ),
)


@dataclass(frozen=True)
class TargetedRecoveryPolicy(_CanonicalMixin):
    """Deterministic total mapping from failure kinds to recovery candidates.

    The policy selects; it never executes and never authorizes. Construction
    fail-closes unless every closed-world failure kind is covered by exactly
    one rule.
    """

    policy_id: str
    contract_version: str
    rules: tuple[RecoveryPolicyRule, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    policy_executes: bool = False
    policy_grants_authority: bool = False
    blind_retry_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "policy_executes", "policy_grants_authority", "blind_retry_allowed"
        )
        covered = [rule.failure_kind for rule in self.rules]
        if len(covered) != len(set(covered)):
            raise AurelFlowValidationError(
                "targeted recovery policy has duplicate rules for a failure kind",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="rules",
            )
        missing = set(RuntimeFailureKind) - set(covered)
        if missing:
            missing_names = ", ".join(sorted(kind.value for kind in missing))
            raise AurelFlowValidationError(
                f"targeted recovery policy does not cover failure kinds: "
                f"{missing_names}",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="rules",
            )

    def rule_for(self, failure_kind: RuntimeFailureKind) -> RecoveryPolicyRule:
        for rule in self.rules:
            if rule.failure_kind is failure_kind:
                return rule
        raise AurelFlowValidationError(  # pragma: no cover - totality enforced above
            f"no rule for failure kind {failure_kind.value}",
            code=AurelFlowErrorCode.ERROR,
            field="failure_kind",
        )


def build_targeted_recovery_policy(
    rules: tuple[RecoveryPolicyRule, ...] = _DEFAULT_RULES,
) -> TargetedRecoveryPolicy:
    payload = {
        "contract_version": TARGETED_RECOVERY_POLICY_VERSION,
        "rule_ids": tuple(rule.rule_id for rule in rules),
    }
    return TargetedRecoveryPolicy(
        policy_id="fltrp-" + stable_hash(payload)[:16],
        contract_version=TARGETED_RECOVERY_POLICY_VERSION,
        rules=rules,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


DEFAULT_TARGETED_RECOVERY_POLICY = build_targeted_recovery_policy()


@dataclass(frozen=True)
class RecoveryCandidateSelection(_CanonicalMixin):
    """The deterministic selection of a candidate for one failure signal."""

    selection_id: str
    contract_version: str
    policy_id: str
    rule_id: str
    failure_signal_id: str
    run_id: str
    failure_kind: RuntimeFailureKind
    selected_candidate_kind: RecoveryCandidateKind
    truth_label: FlowTruthLabel
    alternative_candidate_kinds: tuple[RecoveryCandidateKind, ...] = ()
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    selection_is_not_execution: bool = True
    recovery_executed: bool = False
    execution_available: bool = False
    authority_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "selection_is_not_execution")
        _forbid_true(
            self, "recovery_executed", "execution_available", "authority_granted"
        )


def select_recovery_candidate(
    policy: TargetedRecoveryPolicy, failure_signal: RuntimeFailureSignal
) -> RecoveryCandidateSelection:
    """Deterministically select a targeted candidate. Selection executes nothing."""

    rule = policy.rule_for(failure_signal.failure_kind)
    payload = {
        "contract_version": RECOVERY_CANDIDATE_SELECTION_VERSION,
        "policy_id": policy.policy_id,
        "rule_id": rule.rule_id,
        "failure_signal_id": failure_signal.failure_signal_id,
    }
    return RecoveryCandidateSelection(
        selection_id="flrcs-" + stable_hash(payload)[:16],
        contract_version=RECOVERY_CANDIDATE_SELECTION_VERSION,
        policy_id=policy.policy_id,
        rule_id=rule.rule_id,
        failure_signal_id=failure_signal.failure_signal_id,
        run_id=failure_signal.run_id,
        failure_kind=failure_signal.failure_kind,
        selected_candidate_kind=rule.primary_candidate_kind,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        alternative_candidate_kinds=rule.alternative_candidate_kinds,
    )


@dataclass(frozen=True)
class RecoveryPolicyReadModel(_CanonicalMixin):
    """Deterministic policy projection: coverage without execution."""

    read_model_version: str
    policy_id: str
    rule_count: int
    covered_failure_kind_count: int
    covers_all_failure_kinds: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    policy_executes: bool = False
    blind_retry_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "policy_executes", "blind_retry_allowed")
        _forbid_false(self, "covers_all_failure_kinds")


def build_recovery_policy_read_model(
    policy: TargetedRecoveryPolicy,
) -> RecoveryPolicyReadModel:
    covered = {rule.failure_kind for rule in policy.rules}
    payload = {
        "read_model_version": RECOVERY_POLICY_READ_MODEL_VERSION,
        "policy_id": policy.policy_id,
    }
    return RecoveryPolicyReadModel(
        read_model_version=RECOVERY_POLICY_READ_MODEL_VERSION,
        policy_id=policy.policy_id,
        rule_count=len(policy.rules),
        covered_failure_kind_count=len(covered),
        covers_all_failure_kinds=covered == set(RuntimeFailureKind),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class RecoveryExecutionRequirement(_CanonicalMixin):
    """What future execution of a candidate would require. Not authority."""

    requirement_id: str
    contract_version: str
    recovery_candidate_id: str
    run_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    requires_pre_recovery_checkpoint: bool = True
    requires_budget_check: bool = True
    requires_operator_review: bool = True
    requires_p4_execution: bool = True
    requires_p9_authority_if_irreversible: bool = True
    execution_available: bool = False
    recovery_executed: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_pre_recovery_checkpoint",
            "requires_budget_check",
            "requires_operator_review",
            "requires_p4_execution",
            "requires_p9_authority_if_irreversible",
        )
        _forbid_true(
            self, "execution_available", "recovery_executed", "permission_granted"
        )


@dataclass(frozen=True)
class RecoveryVerificationRequirement(_CanonicalMixin):
    """What future verification of a candidate would require. Not verification."""

    requirement_id: str
    contract_version: str
    recovery_candidate_id: str
    run_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    requires_post_recovery_comparison: bool = True
    requires_p5_proof: bool = True
    verification_required: bool = True
    verification_available: bool = False
    verification_executed: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_post_recovery_comparison",
            "requires_p5_proof",
            "verification_required",
        )
        _forbid_true(
            self,
            "verification_available",
            "verification_executed",
            "proof_available",
            "trace_verified",
        )


@dataclass(frozen=True)
class RecoveryCandidateEnvelope(_CanonicalMixin):
    """A fully-bound targeted recovery candidate. A candidate is not execution."""

    recovery_candidate_id: str
    contract_version: str
    failure_signal_id: str
    run_id: str
    candidate_kind: RecoveryCandidateKind
    execution_requirement: RecoveryExecutionRequirement
    verification_requirement: RecoveryVerificationRequirement
    truth_label: FlowTruthLabel
    diagnosis_id: str = ""
    selection_id: str = ""
    recovery_checkpoint_requirement_id: str = ""
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    requires_pre_recovery_checkpoint: bool = True
    requires_post_recovery_comparison: bool = True
    requires_operator_review: bool = True
    requires_p4_execution: bool = True
    requires_p5_proof: bool = True
    requires_p9_authority_if_irreversible: bool = True
    execution_available: bool = False
    recovery_executed: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_pre_recovery_checkpoint",
            "requires_post_recovery_comparison",
            "requires_operator_review",
            "requires_p4_execution",
            "requires_p5_proof",
            "requires_p9_authority_if_irreversible",
        )
        _forbid_true(
            self,
            "execution_available",
            "recovery_executed",
            "proof_available",
            "trace_verified",
        )


def create_recovery_candidate_envelope(
    selection: RecoveryCandidateSelection,
    *,
    diagnosis: RootCauseDiagnosis | None = None,
    checkpoint_requirement: RecoveryCheckpointRequirement | None = None,
) -> RecoveryCandidateEnvelope:
    """Bind a selection into a candidate envelope with the P3-FLOW-F checkpoint
    discipline. When no requirement is passed, one is derived so a candidate
    can never exist without a pre-recovery checkpoint requirement."""

    if diagnosis is not None and diagnosis.failure_signal_id != (
        selection.failure_signal_id
    ):
        raise AurelFlowValidationError(
            f"diagnosis failure signal {diagnosis.failure_signal_id!r} does "
            f"not match selection failure signal "
            f"{selection.failure_signal_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="diagnosis",
        )
    if checkpoint_requirement is None:
        checkpoint_requirement = create_recovery_checkpoint_requirement(
            run_id=selection.run_id,
            failure_or_recovery_candidate_id=selection.failure_signal_id,
        )
    elif checkpoint_requirement.run_id != selection.run_id:
        raise AurelFlowValidationError(
            f"checkpoint requirement run {checkpoint_requirement.run_id!r} "
            f"does not match selection run {selection.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="checkpoint_requirement",
        )
    payload = {
        "contract_version": RECOVERY_CANDIDATE_ENVELOPE_VERSION,
        "selection_id": selection.selection_id,
        "failure_signal_id": selection.failure_signal_id,
        "candidate_kind": selection.selected_candidate_kind.value,
        "diagnosis_id": diagnosis.diagnosis_id if diagnosis else "",
        "recovery_checkpoint_requirement_id": (
            checkpoint_requirement.requirement_id
        ),
    }
    recovery_candidate_id = "flrce-" + stable_hash(payload)[:16]
    execution_requirement = RecoveryExecutionRequirement(
        requirement_id="flrer-" + stable_hash(
            {
                "contract_version": RECOVERY_EXECUTION_REQUIREMENT_VERSION,
                "recovery_candidate_id": recovery_candidate_id,
            }
        )[:16],
        contract_version=RECOVERY_EXECUTION_REQUIREMENT_VERSION,
        recovery_candidate_id=recovery_candidate_id,
        run_id=selection.run_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
    verification_requirement = RecoveryVerificationRequirement(
        requirement_id="flrvr-" + stable_hash(
            {
                "contract_version": RECOVERY_VERIFICATION_REQUIREMENT_VERSION,
                "recovery_candidate_id": recovery_candidate_id,
            }
        )[:16],
        contract_version=RECOVERY_VERIFICATION_REQUIREMENT_VERSION,
        recovery_candidate_id=recovery_candidate_id,
        run_id=selection.run_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
    return RecoveryCandidateEnvelope(
        recovery_candidate_id=recovery_candidate_id,
        contract_version=RECOVERY_CANDIDATE_ENVELOPE_VERSION,
        failure_signal_id=selection.failure_signal_id,
        run_id=selection.run_id,
        candidate_kind=selection.selected_candidate_kind,
        execution_requirement=execution_requirement,
        verification_requirement=verification_requirement,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        diagnosis_id=diagnosis.diagnosis_id if diagnosis else "",
        selection_id=selection.selection_id,
        recovery_checkpoint_requirement_id=checkpoint_requirement.requirement_id,
    )


@dataclass(frozen=True)
class RecoveryCandidateBoundary(_CanonicalMixin):
    """The recovery-candidate law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = RECOVERY_CANDIDATE_EXECUTION_UNAVAILABLE_REASON
    candidate_is_not_execution: bool = True
    candidate_is_not_authority: bool = True
    candidate_requires_checkpoint: bool = True
    candidate_requires_verification_expectation: bool = True
    candidate_executes: bool = False
    candidate_grants_permission: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "candidate_is_not_execution",
            "candidate_is_not_authority",
            "candidate_requires_checkpoint",
            "candidate_requires_verification_expectation",
        )
        _forbid_true(self, "candidate_executes", "candidate_grants_permission")


def build_recovery_candidate_boundary() -> RecoveryCandidateBoundary:
    payload = {"boundary_version": RECOVERY_CANDIDATE_BOUNDARY_VERSION}
    return RecoveryCandidateBoundary(
        boundary_version=RECOVERY_CANDIDATE_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class RecoveryCandidateReadModel(_CanonicalMixin):
    """Deterministic aggregate over candidate envelopes."""

    read_model_version: str
    run_id: str
    candidate_count: int
    candidate_kind_counts: Mapping[str, int]
    all_require_pre_recovery_checkpoint: bool
    all_require_post_recovery_comparison: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    any_execution_available: bool = False
    any_recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "all_require_pre_recovery_checkpoint",
            "all_require_post_recovery_comparison",
        )
        _forbid_true(self, "any_execution_available", "any_recovery_executed")


def build_recovery_candidate_read_model(
    run_id: str, envelopes: tuple[RecoveryCandidateEnvelope, ...]
) -> RecoveryCandidateReadModel:
    for envelope in envelopes:
        if envelope.run_id != run_id:
            raise AurelFlowValidationError(
                f"candidate envelope run {envelope.run_id!r} does not match "
                f"read model run {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="envelopes",
            )
    kind_counts: dict[str, int] = {}
    for envelope in envelopes:
        kind_counts[envelope.candidate_kind.value] = (
            kind_counts.get(envelope.candidate_kind.value, 0) + 1
        )
    payload = {
        "read_model_version": RECOVERY_CANDIDATE_READ_MODEL_VERSION,
        "run_id": run_id,
        "candidate_ids": tuple(
            envelope.recovery_candidate_id for envelope in envelopes
        ),
    }
    return RecoveryCandidateReadModel(
        read_model_version=RECOVERY_CANDIDATE_READ_MODEL_VERSION,
        run_id=run_id,
        candidate_count=len(envelopes),
        candidate_kind_counts=kind_counts,
        all_require_pre_recovery_checkpoint=all(
            envelope.requires_pre_recovery_checkpoint for envelope in envelopes
        ),
        all_require_post_recovery_comparison=all(
            envelope.requires_post_recovery_comparison for envelope in envelopes
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )

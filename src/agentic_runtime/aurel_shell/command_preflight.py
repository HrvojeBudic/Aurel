"""P2.VSLICE-A governed command preflight decision layer.

Preflight evaluates policy, identity, and sandbox gate summaries for a command
intent. Preflight never executes commands, routes commands, or claims Shell LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from agentic_runtime.governance_enforcement import (
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
)
from agentic_runtime.identity_invariant_enforcement import (
    IdentityInvariantCheckInput,
    IdentityInvariantDecision,
    evaluate_identity_invariant_enforcement,
)
from agentic_runtime.policy_submit_influence import (
    PolicyResolverSubmitInfluenceStatus,
    evaluate_policy_resolver_submit_influence,
)
from agentic_runtime.sandbox import SandboxBackend, UnsafeLocalSandbox
from agentic_runtime.sandbox_backend_gate import (
    SandboxBackendDecision,
    SandboxBackendGateMode,
    SandboxBackendRequirement,
    evaluate_sandbox_backend_gate,
)

from .command_availability import (
    COMMAND_EXECUTION_UNAVAILABLE_REASON,
    CommandAvailabilityTruth,
    GlobalCommandContract,
    GlobalCommandInteractionMode,
    P2_VSLICE_A_PACK_ID,
    lookup_command_contract,
)
from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)

P2_VSLICE_A_INTENT_VERSION = "p2_vslice_a_command_intent.v1"
P2_VSLICE_A_PREFLIGHT_VERSION = "p2_vslice_a_command_preflight_decision.v1"
P2_VSLICE_A_GATE_SUMMARY_VERSION = "p2_vslice_a_command_preflight_gate_summary.v1"


class CommandIntentSource(str, Enum):
    OPERATOR = "operator"
    TEST_HARNESS = "test_harness"
    READ_MODEL = "read_model"
    UNAVAILABLE = "unavailable"


class CommandPreflightOutcome(str, Enum):
    ALLOWED_READ_ONLY = "allowed_read_only"
    ALLOWED_PREFLIGHT_ONLY = "allowed_preflight_only"
    DENIED_POLICY = "denied_policy"
    DENIED_IDENTITY = "denied_identity"
    DENIED_SANDBOX = "denied_sandbox"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class CommandIntent(_CanonicalMixin):
    schema_version: str
    intent_id: str
    source: CommandIntentSource
    requested_command_id: str
    arguments: Mapping[str, str]
    operator_context: str
    test_context: str
    intent_hash: str


@dataclass(frozen=True)
class CommandPreflightEvidenceRef(_CanonicalMixin):
    ref_id: str
    ref_kind: str
    ref_path: str
    truth_label: str
    ref_hash: str


@dataclass(frozen=True)
class CommandPreflightGateSummary(_CanonicalMixin):
    schema_version: str
    gate_name: str
    decision: str
    truth_label: str
    blocked: bool
    enforced: bool
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class CommandPreflightDecision(_CanonicalMixin):
    schema_version: str
    pack_id: str
    intent: CommandIntent
    command: GlobalCommandContract | None
    outcome: CommandPreflightOutcome
    truth_label: str
    preflight_allowed: bool
    execution_allowed: bool
    executes_command: bool
    policy_decision_summary: CommandPreflightGateSummary
    identity_invariant_summary: CommandPreflightGateSummary
    sandbox_backend_gate_summary: CommandPreflightGateSummary
    evidence_refs: tuple[CommandPreflightEvidenceRef, ...]
    evidence_gaps: tuple[str, ...]
    unavailable_reason: str
    decision_hash: str


@dataclass(frozen=True)
class P2VSliceAPreflightSideEffectProof(_CanonicalMixin):
    command_executed: bool = False
    command_router_created: bool = False
    shell_live_claimed: bool = False
    trace_verified_claimed: bool = False
    p2_9_b_implemented: bool = False
    runtime_mutated: bool = False


def build_command_intent(
    requested_command_id: str,
    *,
    source: CommandIntentSource = CommandIntentSource.OPERATOR,
    arguments: Mapping[str, str] | None = None,
    operator_context: str = "",
    test_context: str = "",
) -> CommandIntent:
    if not requested_command_id:
        _reject(
            "command intent requires requested_command_id",
            field="requested_command_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "schema_version": P2_VSLICE_A_INTENT_VERSION,
        "intent_id": f"command_intent:{requested_command_id}",
        "source": source,
        "requested_command_id": requested_command_id,
        "arguments": dict(arguments or {}),
        "operator_context": operator_context,
        "test_context": test_context,
    }
    return CommandIntent(**payload, intent_hash=_hash_payload(payload))


def _gate_summary(
    *,
    gate_name: str,
    decision: str,
    truth_label: str,
    blocked: bool,
    enforced: bool,
    reason_codes: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    evidence_gaps: tuple[str, ...] = (),
) -> CommandPreflightGateSummary:
    payload = {
        "schema_version": P2_VSLICE_A_GATE_SUMMARY_VERSION,
        "gate_name": gate_name,
        "decision": decision,
        "truth_label": truth_label,
        "blocked": blocked,
        "enforced": enforced,
        "reason_codes": reason_codes,
        "evidence_refs": evidence_refs,
        "evidence_gaps": evidence_gaps,
    }
    return CommandPreflightGateSummary(**payload, summary_hash=_hash_payload(payload))


def _policy_summary(
    *,
    mode: GovernanceEnforcementMode,
    require_policy_context: bool,
    registry: Any | None,
    context: Any | None,
    simulate_policy_deny: bool = False,
) -> CommandPreflightGateSummary:
    if simulate_policy_deny and mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED:
        return _gate_summary(
            gate_name="policy",
            decision=PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_DENY.value,
            truth_label=CommandAvailabilityTruth.DENIED_POLICY.value,
            blocked=True,
            enforced=True,
            reason_codes=("SIMULATED_POLICY_DENY",),
            evidence_refs=("src/agentic_runtime/policy_submit_influence.py",),
        )
    if registry is None or context is None:
        gaps = ("policy_registry_or_context_unavailable",)
        if require_policy_context and mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED:
            return _gate_summary(
                gate_name="policy",
                decision=PolicyResolverSubmitInfluenceStatus.BLOCKED_MISSING_REQUIRED_CONTEXT.value,
                truth_label=CommandAvailabilityTruth.DENIED_POLICY.value,
                blocked=True,
                enforced=True,
                reason_codes=("POLICY_CONTEXT_REQUIRED",),
                evidence_refs=("src/agentic_runtime/policy_submit_influence.py",),
                evidence_gaps=gaps,
            )
        return _gate_summary(
            gate_name="policy",
            decision=PolicyResolverSubmitInfluenceStatus.UNAVAILABLE.value,
            truth_label=CommandAvailabilityTruth.CONTRACT_ONLY.value,
            blocked=False,
            enforced=False,
            reason_codes=("POLICY_CONTEXT_UNAVAILABLE",),
            evidence_refs=("src/agentic_runtime/policy_submit_influence.py",),
            evidence_gaps=gaps,
        )
    result = evaluate_policy_resolver_submit_influence(
        mode=mode,
        require_policy_context=require_policy_context,
        registry=registry,
        context=context,
    )
    truth = CommandAvailabilityTruth.CONTRACT_ONLY.value
    if result.should_block:
        truth = CommandAvailabilityTruth.DENIED_POLICY.value
    return _gate_summary(
        gate_name="policy",
        decision=result.status.value,
        truth_label=truth,
        blocked=result.should_block,
        enforced=result.artifact.enforced,
        reason_codes=result.artifact.reason_codes,
        evidence_refs=(
            "src/agentic_runtime/policy_submit_influence.py",
            "agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md",
        ),
    )


def _identity_summary(
    *,
    mode: GovernanceEnforcementMode,
    require_identity_context: bool,
    check_input: IdentityInvariantCheckInput | None = None,
    simulate_identity_deny: bool = False,
) -> CommandPreflightGateSummary:
    if simulate_identity_deny and mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED:
        return _gate_summary(
            gate_name="identity",
            decision=IdentityInvariantDecision.DENY.value,
            truth_label=CommandAvailabilityTruth.DENIED_IDENTITY.value,
            blocked=True,
            enforced=True,
            reason_codes=("SIMULATED_IDENTITY_DENY",),
            evidence_refs=("src/agentic_runtime/identity_invariant_enforcement.py",),
        )
    if check_input is None:
        check_input = IdentityInvariantCheckInput(
            require_identity_context=require_identity_context,
        )
    result = evaluate_identity_invariant_enforcement(
        mode=mode,
        check_input=check_input,
    )
    truth = CommandAvailabilityTruth.CONTRACT_ONLY.value
    if result.should_block:
        truth = CommandAvailabilityTruth.DENIED_IDENTITY.value
    elif result.decision is IdentityInvariantDecision.UNAVAILABLE:
        truth = CommandAvailabilityTruth.CONTRACT_ONLY.value
    return _gate_summary(
        gate_name="identity",
        decision=result.decision.value,
        truth_label=truth,
        blocked=result.should_block,
        enforced=result.artifact.enforced,
        reason_codes=result.artifact.reason_codes,
        evidence_refs=(
            "src/agentic_runtime/identity_invariant_enforcement.py",
            "config/aurel/identity_kernel.yaml",
            "agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md",
        ),
        evidence_gaps=result.artifact.unavailable_reasons,
    )


def _sandbox_summary(
    *,
    mode: GovernanceEnforcementMode,
    backend: SandboxBackend | None = None,
    require_safe_verified: bool = False,
    simulate_sandbox_deny: bool = False,
) -> CommandPreflightGateSummary:
    if backend is None:
        backend = UnsafeLocalSandbox()
    requirement = SandboxBackendRequirement(
        gate_mode=(
            SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED
            if require_safe_verified
            else SandboxBackendGateMode.DEV_ALLOW_UNSAFE
        ),
        require_safe_verified=require_safe_verified,
        allow_unsafe_dev=True,
        dev_fixture_backend=True,
        claims_live_execution=False,
        claims_trace_verified=False,
        claims_safe_sandbox=require_safe_verified,
    )
    if simulate_sandbox_deny:
        requirement = SandboxBackendRequirement(
            gate_mode=SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED,
            require_safe_verified=True,
            allow_unsafe_dev=False,
            claims_safe_sandbox=True,
        )
    result = evaluate_sandbox_backend_gate(
        mode=mode,
        backend=backend,
        requirement=requirement,
    )
    truth = CommandAvailabilityTruth.CONTRACT_ONLY.value
    if result.should_block:
        truth = CommandAvailabilityTruth.DENIED_SANDBOX.value
    elif result.decision is SandboxBackendDecision.UNAVAILABLE:
        truth = CommandAvailabilityTruth.UNAVAILABLE_SAFE_SANDBOX_MISSING.value
    return _gate_summary(
        gate_name="sandbox",
        decision=result.decision.value,
        truth_label=truth,
        blocked=result.should_block,
        enforced=result.artifact.enforced,
        reason_codes=result.artifact.reason_codes,
        evidence_refs=tuple(result.artifact.evidence_refs),
        evidence_gaps=tuple(result.artifact.unavailable_reasons),
    )


def _evidence_ref(ref_id: str, ref_kind: str, ref_path: str, truth_label: str) -> CommandPreflightEvidenceRef:
    payload = {
        "ref_id": ref_id,
        "ref_kind": ref_kind,
        "ref_path": ref_path,
        "truth_label": truth_label,
    }
    return CommandPreflightEvidenceRef(**payload, ref_hash=_hash_payload(payload))


def run_command_preflight(
    intent: CommandIntent,
    *,
    governance_config: GovernanceEnforcementConfig | None = None,
    policy_registry: Any | None = None,
    policy_context: Any | None = None,
    identity_check_input: IdentityInvariantCheckInput | None = None,
    sandbox_backend: SandboxBackend | None = None,
    simulate_policy_deny: bool = False,
    simulate_identity_deny: bool = False,
    simulate_sandbox_deny: bool = False,
) -> CommandPreflightDecision:
    """Evaluate governed preflight for a command intent without executing it."""
    config = governance_config or GovernanceEnforcementConfig()
    command = lookup_command_contract(intent.requested_command_id)

    if command is None:
        policy_summary = _policy_summary(
            mode=config.mode,
            require_policy_context=config.require_policy_context,
            registry=policy_registry,
            context=policy_context,
            simulate_policy_deny=simulate_policy_deny,
        )
        identity_summary = _identity_summary(
            mode=config.mode,
            require_identity_context=config.require_identity_context,
            check_input=identity_check_input,
            simulate_identity_deny=simulate_identity_deny,
        )
        sandbox_summary = _sandbox_summary(
            mode=config.mode,
            backend=sandbox_backend,
            require_safe_verified=config.require_safe_sandbox_backend,
            simulate_sandbox_deny=simulate_sandbox_deny,
        )
        payload = {
            "schema_version": P2_VSLICE_A_PREFLIGHT_VERSION,
            "pack_id": P2_VSLICE_A_PACK_ID,
            "intent": intent,
            "command": None,
            "outcome": CommandPreflightOutcome.UNAVAILABLE,
            "truth_label": CommandAvailabilityTruth.ERROR.value,
            "preflight_allowed": False,
            "execution_allowed": False,
            "executes_command": False,
            "policy_decision_summary": policy_summary,
            "identity_invariant_summary": identity_summary,
            "sandbox_backend_gate_summary": sandbox_summary,
            "evidence_refs": (
                _evidence_ref(
                    "p2_vslice_a_report",
                    "report",
                    "agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md",
                    CommandAvailabilityTruth.CONTRACT_ONLY.value,
                ),
            ),
            "evidence_gaps": ("unknown_command_id",),
            "unavailable_reason": f"Unknown command: {intent.requested_command_id}",
        }
        return CommandPreflightDecision(**payload, decision_hash=_hash_payload(payload))

    if command.interaction_mode is GlobalCommandInteractionMode.UNAVAILABLE:
        outcome = CommandPreflightOutcome.UNAVAILABLE
        truth_label = command.truth_state.value
        preflight_allowed = False
    elif command.interaction_mode is GlobalCommandInteractionMode.READ_ONLY:
        outcome = CommandPreflightOutcome.ALLOWED_READ_ONLY
        truth_label = command.truth_state.value
        preflight_allowed = True
    else:
        outcome = CommandPreflightOutcome.ALLOWED_PREFLIGHT_ONLY
        truth_label = command.truth_state.value
        preflight_allowed = True

    policy_summary = _policy_summary(
        mode=config.mode,
        require_policy_context=config.require_policy_context,
        registry=policy_registry,
        context=policy_context,
        simulate_policy_deny=simulate_policy_deny,
    )
    identity_summary = _identity_summary(
        mode=config.mode,
        require_identity_context=config.require_identity_context,
        check_input=identity_check_input,
        simulate_identity_deny=simulate_identity_deny,
    )
    sandbox_summary = _sandbox_summary(
        mode=config.mode,
        backend=sandbox_backend,
        require_safe_verified=config.require_safe_sandbox_backend,
        simulate_sandbox_deny=simulate_sandbox_deny,
    )

    if policy_summary.blocked:
        outcome = CommandPreflightOutcome.DENIED_POLICY
        truth_label = CommandAvailabilityTruth.DENIED_POLICY.value
        preflight_allowed = False
    elif identity_summary.blocked:
        outcome = CommandPreflightOutcome.DENIED_IDENTITY
        truth_label = CommandAvailabilityTruth.DENIED_IDENTITY.value
        preflight_allowed = False
    elif sandbox_summary.blocked:
        outcome = CommandPreflightOutcome.DENIED_SANDBOX
        truth_label = CommandAvailabilityTruth.DENIED_SANDBOX.value
        preflight_allowed = False
    elif sandbox_summary.truth_label == CommandAvailabilityTruth.UNAVAILABLE_SAFE_SANDBOX_MISSING.value:
        if config.require_safe_sandbox_backend and config.mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED:
            outcome = CommandPreflightOutcome.DENIED_SANDBOX
            truth_label = CommandAvailabilityTruth.DENIED_SANDBOX.value
            preflight_allowed = False

    evidence_gaps: list[str] = []
    for summary in (policy_summary, identity_summary, sandbox_summary):
        evidence_gaps.extend(summary.evidence_gaps)
    if command.truth_state is CommandAvailabilityTruth.CONTRACT_ONLY:
        evidence_gaps.append("command_contract_only_no_live_backend")

    payload = {
        "schema_version": P2_VSLICE_A_PREFLIGHT_VERSION,
        "pack_id": P2_VSLICE_A_PACK_ID,
        "intent": intent,
        "command": command,
        "outcome": outcome,
        "truth_label": truth_label,
        "preflight_allowed": preflight_allowed,
        "execution_allowed": False,
        "executes_command": False,
        "policy_decision_summary": policy_summary,
        "identity_invariant_summary": identity_summary,
        "sandbox_backend_gate_summary": sandbox_summary,
        "evidence_refs": (
            _evidence_ref(
                "p2_vslice_a_report",
                "report",
                "agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md",
                CommandAvailabilityTruth.CONTRACT_ONLY.value,
            ),
            _evidence_ref(
                "p2_review_a_report",
                "report",
                "agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md",
                CommandAvailabilityTruth.CONTRACT_ONLY.value,
            ),
            _evidence_ref(
                "command_contract",
                "contract",
                f"global_command:{command.slug}",
                command.truth_state.value,
            ),
        ),
        "evidence_gaps": tuple(sorted(set(evidence_gaps))),
        "unavailable_reason": (
            COMMAND_EXECUTION_UNAVAILABLE_REASON
            if not preflight_allowed
            else ""
        ),
    }
    decision = CommandPreflightDecision(**payload, decision_hash=_hash_payload(payload))
    assert_preflight_does_not_execute(decision)
    return decision


def assert_preflight_does_not_execute(decision: CommandPreflightDecision) -> None:
    if decision.executes_command or decision.execution_allowed:
        _reject(
            "P2.VSLICE-A preflight must not execute commands or allow execution",
            field="executes_command",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def build_p2_vslice_a_preflight_side_effect_proof() -> P2VSliceAPreflightSideEffectProof:
    return P2VSliceAPreflightSideEffectProof()

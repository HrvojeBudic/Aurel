"""P2.VSLICE-A governed command preflight tests."""

from __future__ import annotations

from agentic_runtime.aurel_shell.command_availability import CommandAvailabilityTruth
from agentic_runtime.aurel_shell.command_preflight import (
    CommandIntentSource,
    CommandPreflightOutcome,
    build_command_intent,
    run_command_preflight,
)
from agentic_runtime.aurel_shell.command_projection import preflight_global_command
from agentic_runtime.governance_enforcement import (
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
)
from agentic_runtime.identity_invariant_enforcement import IdentityInvariantCheckInput


def test_command_intent_can_be_preflighted_without_execution() -> None:
    intent = build_command_intent(
        "shell.command.preflight",
        source=CommandIntentSource.TEST_HARNESS,
        test_context="pytest",
    )
    decision = run_command_preflight(intent)
    assert decision.executes_command is False
    assert decision.execution_allowed is False
    assert decision.outcome is CommandPreflightOutcome.ALLOWED_PREFLIGHT_ONLY


def test_command_preflight_includes_policy_identity_sandbox_summaries() -> None:
    decision = preflight_global_command("shell.command.preflight")
    assert decision.policy_decision_summary.gate_name == "policy"
    assert decision.identity_invariant_summary.gate_name == "identity"
    assert decision.sandbox_backend_gate_summary.gate_name == "sandbox"
    assert decision.policy_decision_summary.decision
    assert decision.identity_invariant_summary.decision
    assert decision.sandbox_backend_gate_summary.decision


def test_command_preflight_denied_policy_is_honest() -> None:
    config = GovernanceEnforcementConfig(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        require_policy_context=True,
    )
    intent = build_command_intent("shell.command.preflight")
    decision = run_command_preflight(
        intent,
        governance_config=config,
        simulate_policy_deny=True,
    )
    assert decision.outcome is CommandPreflightOutcome.DENIED_POLICY
    assert decision.truth_label == CommandAvailabilityTruth.DENIED_POLICY.value
    assert decision.policy_decision_summary.blocked is True
    assert decision.executes_command is False


def test_command_preflight_denied_identity_is_honest() -> None:
    config = GovernanceEnforcementConfig(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        require_identity_context=True,
    )
    check_input = IdentityInvariantCheckInput(
        require_identity_context=True,
        identity_context_present=False,
        policy_bypass_self_grant=True,
    )
    intent = build_command_intent("shell.command.preflight")
    decision = run_command_preflight(
        intent,
        governance_config=config,
        identity_check_input=check_input,
    )
    assert decision.outcome is CommandPreflightOutcome.DENIED_IDENTITY
    assert decision.identity_invariant_summary.blocked is True
    assert decision.executes_command is False


def test_command_preflight_unavailable_safe_sandbox_is_honest() -> None:
    config = GovernanceEnforcementConfig(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        require_safe_sandbox_backend=True,
    )
    intent = build_command_intent("shell.command.preflight")
    decision = run_command_preflight(
        intent,
        governance_config=config,
        simulate_sandbox_deny=True,
    )
    assert decision.outcome is CommandPreflightOutcome.DENIED_SANDBOX
    assert decision.sandbox_backend_gate_summary.blocked is True
    assert (
        decision.sandbox_backend_gate_summary.truth_label
        in {
            CommandAvailabilityTruth.DENIED_SANDBOX.value,
            CommandAvailabilityTruth.UNAVAILABLE_SAFE_SANDBOX_MISSING.value,
        }
    )
    assert decision.executes_command is False


def test_preflight_only_command_does_not_claim_execution() -> None:
    decision = preflight_global_command("shell.command.preflight")
    assert decision.preflight_allowed is True
    assert decision.execution_allowed is False
    assert decision.executes_command is False
    assert decision.truth_label in {
        CommandAvailabilityTruth.AVAILABLE_PREFLIGHT_ONLY.value,
        CommandAvailabilityTruth.DENIED_POLICY.value,
        CommandAvailabilityTruth.DENIED_IDENTITY.value,
        CommandAvailabilityTruth.DENIED_SANDBOX.value,
    }

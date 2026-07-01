"""P1.ENF-A entrypoint bypass guard tests."""
from __future__ import annotations

from agentic_runtime import (
    EntrypointGovernanceClassification,
    EntrypointGovernanceGuard,
    GovernedDelegationRequirement,
    classify_entrypoint_governance,
)


def test_runtime_submit_is_governed_entrypoint():
    result = classify_entrypoint_governance(
        "agentic_runtime.runtime.AgenticRuntime.submit"
    )
    assert (
        result.classification
        is EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT
    )
    assert result.delegation_requirement is GovernedDelegationRequirement.NOT_REQUIRED
    assert "RUNTIME_SUBMIT_IS_GOVERNED_DISPOSAL_PATH" in result.reason_codes


def test_aurel_shell_contract_modules_are_non_executing():
    result = classify_entrypoint_governance(
        "agentic_runtime.aurel_shell.shell_exit_seal_foundation"
    )
    assert (
        result.classification
        is EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY
    )
    assert result.non_executing_proof is not None
    assert result.non_executing_proof.contract_only is True
    assert result.non_executing_proof.command_router_created is False
    assert result.non_executing_proof.product_execution_created is False


def test_repo_agent_execution_like_paths_require_governed_delegation():
    result = classify_entrypoint_governance(
        "agentic_runtime.repo_agent.PatchExecutor.apply"
    )
    assert result.classification in {
        EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED,
    }
    assert result.metadata.get("known_runtime_submit_delegation") is True


def test_unknown_execution_like_entrypoint_is_blocked_unknown_risk():
    result = classify_entrypoint_governance("external.plugin.execute_command")
    assert (
        result.classification
        is EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK
    )
    assert "UNKNOWN_EXECUTION_LIKE_ENTRYPOINT_BLOCKED" in result.reason_codes


def test_entrypoint_guard_does_not_create_command_router():
    guard = EntrypointGovernanceGuard()
    assert not hasattr(guard, "route")
    assert not hasattr(guard, "dispatch")
    assert not hasattr(guard, "execute")
    assert not hasattr(guard, "submit")


def test_entrypoint_guard_result_hash_is_deterministic():
    first = classify_entrypoint_governance(
        "agentic_runtime.aurel_shell.global_command_registry"
    )
    second = classify_entrypoint_governance(
        "agentic_runtime.aurel_shell.global_command_registry"
    )
    assert first.result_hash == second.result_hash
    assert len(first.result_hash) == 64

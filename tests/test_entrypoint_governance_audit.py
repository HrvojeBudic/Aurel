"""P1.ENF-B entrypoint governance audit tests."""
from __future__ import annotations

from agentic_runtime.entrypoint_governance_audit import (
    EntrypointGovernanceAudit,
    EntrypointSurface,
    EntrypointTruthLabel,
    P1ENFBSideEffectProof,
    classify_entrypoint_with_audit_symbol,
)
from agentic_runtime.entrypoint_governance_guard import (
    EntrypointGovernanceClassification,
    classify_entrypoint_governance,
)


def test_runtime_submit_is_governed_runtime_submit():
    record = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.runtime.AgenticRuntime.submit"
    )
    assert (
        record.classification
        is EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT
    )
    assert record.side_effect_vectors.calls_tool_bus is True
    assert record.truth_label is EntrypointTruthLabel.NO_BYPASS_EVIDENCE
    guard = classify_entrypoint_governance("agentic_runtime.runtime.AgenticRuntime.submit")
    assert guard.classification is EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT


def test_aurel_shell_modules_are_non_executing_contract_only():
    records = [
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.surface is EntrypointSurface.AUREL_SHELL
    ]
    assert records
    for record in records:
        assert record.classification in {
            EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY,
            EntrypointGovernanceClassification.UNAVAILABLE,
        }
        assert not record.side_effect_vectors.calls_runtime_submit
    shell = classify_entrypoint_governance(
        "agentic_runtime.aurel_shell.shell_exit_seal_foundation"
    )
    assert (
        shell.classification
        is EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY
    )


def test_repo_agent_execution_like_paths_are_governed_or_delegation_required():
    audit = EntrypointGovernanceAudit()
    repo_records = [r for r in audit.build_discovery_map() if r.surface is EntrypointSurface.REPO_AGENT]
    assert repo_records
    for record in repo_records:
        assert record.classification in {
            EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED,
            EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
            EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY,
        }
    patch = classify_entrypoint_with_audit_symbol(
        "agentic_runtime.repo_agent.PatchExecutor.apply"
    )
    assert patch is EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED


def test_unknown_execution_like_path_is_blocked_unknown_risk():
    result = classify_entrypoint_governance("external.plugin.execute_command")
    assert (
        result.classification
        is EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK
    )
    audit = EntrypointGovernanceAudit().build_result()
    assert audit.unknown_risk_count >= 1
    assert audit.blocked_risk_count >= 1


def test_cli_status_like_paths_are_read_only_if_applicable():
    status = classify_entrypoint_governance("agentic_runtime.cli.cmd_status")
    assert (
        status.classification
        is EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY
    )
    verify = classify_entrypoint_governance("agentic_runtime.cli.cmd_verify")
    assert (
        verify.classification
        is EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK
    )


def test_shell_or_run_command_paths_require_runtime_submit_or_sandbox_guard():
    repo_task = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.cli.cmd_repo_task"
    )
    assert repo_task.classification is EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED
    sandbox = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.sandbox.UnsafeLocalSandbox.run_shell"
    )
    assert sandbox.classification is EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED
    assert sandbox.metadata.get("reachable_only_via")


def test_test_only_execution_fixtures_are_not_product_entrypoints():
    result = classify_entrypoint_governance("tests.conftest")
    assert (
        result.classification
        is EntrypointGovernanceClassification.TEST_ONLY_EXECUTION_FIXTURE
    )


def test_p1_enf_b_does_not_create_shell_command_router():
    audit = EntrypointGovernanceAudit()
    assert not hasattr(audit, "route")
    assert not hasattr(audit, "dispatch")
    assert not hasattr(audit, "execute")


def test_p1_enf_b_does_not_implement_p2_9_b():
    proof = P1ENFBSideEffectProof()
    assert proof.p2_9_b_implemented is False
    assert proof.allows_no_product_scope is True


def test_p1_enf_b_side_effect_proof_allows_no_product_scope():
    result = EntrypointGovernanceAudit().build_result()
    assert result.side_effect_proof.allows_no_product_scope is True
    assert len(result.discovery_records) >= 10
    assert result.result_hash
    assert len(result.result_hash) == 64

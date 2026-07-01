"""P1.ENF-B repo_agent entrypoint enforcement audit tests."""
from __future__ import annotations

from agentic_runtime.entrypoint_governance_audit import (
    EntrypointGovernanceAudit,
    EntrypointSurface,
)
from agentic_runtime.entrypoint_governance_guard import (
    EntrypointGovernanceClassification,
    classify_entrypoint_governance,
)


def test_patch_executor_delegates_to_runtime_submit():
    record = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.repo_agent.PatchExecutor.apply"
    )
    assert record.side_effect_vectors.calls_runtime_submit is True
    assert record.side_effect_vectors.writes_files is True
    assert (
        record.classification
        is EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED
    )
    assert "repo_agent.py:647" in record.evidence_refs


def test_test_runner_delegates_to_runtime_submit():
    record = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.repo_agent.TestRunnerAdapter.run"
    )
    assert record.side_effect_vectors.calls_runtime_submit is True
    assert (
        record.classification
        is EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED
    )


def test_repository_agent_loop_is_delegation_required():
    record = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.repo_agent.RepositoryAgentLoop.run"
    )
    assert (
        record.classification
        is EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED
    )
    assert record.side_effect_vectors.calls_sandbox is True


def test_repo_context_builder_is_read_model_only():
    record = next(
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.symbol == "agentic_runtime.repo_agent.RepoContextBuilder.build"
    )
    assert (
        record.classification
        is EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY
    )
    assert not any(record.side_effect_vectors.to_canonical_dict().values())


def test_repo_agent_prefix_fallback_is_delegation_required():
    result = classify_entrypoint_governance(
        "agentic_runtime.repo_agent.CodeTaskPlanner.create_plan"
    )
    assert (
        result.classification
        is EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED
    )


def test_repo_agent_audit_matrix_covers_all_repo_surfaces():
    repo_records = [
        r
        for r in EntrypointGovernanceAudit().build_discovery_map()
        if r.surface is EntrypointSurface.REPO_AGENT
    ]
    symbols = {r.symbol for r in repo_records}
    assert "agentic_runtime.repo_agent.PatchExecutor.apply" in symbols
    assert "agentic_runtime.repo_agent.RepositoryAgentLoop.run" in symbols
    assert len(repo_records) >= 4

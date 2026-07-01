"""Focused tests for P1.ENF-F-A validation truth gates."""
from __future__ import annotations

from agentic_runtime.validation_truth_gates import (
    CORE_STRICT_PROBE_ERROR_CODES,
    CoreStrictProbeGate,
    CoreStrictProbeGateInput,
    DeterminismGate,
    DeterminismGateInput,
    DeterminismGateStatus,
    DirtyWorktreeGate,
    DirtyWorktreeGateInput,
    ToolingTruthGate,
    ToolingTruthGateInput,
    ToolingTruthGateStatus,
    ValidationClaimStrength,
    evaluate_core_strict_probe_gate,
    evaluate_dirty_worktree_gate,
    evaluate_tooling_truth_gate,
)


def test_dirty_worktree_gate_detects_fixture_mutation():
    gate_input = DirtyWorktreeGateInput(
        tracked_fixture_paths=("tests/fixtures/consent/consent_request.json",),
        tracked_fixture_hashes_before={
            "tests/fixtures/consent/consent_request.json": "abc123",
        },
        tracked_fixture_hashes_after={
            "tests/fixtures/consent/consent_request.json": "def456",
        },
    )
    result = evaluate_dirty_worktree_gate(gate_input)
    assert result.status is DeterminismGateStatus.FAIL_FIXTURE_MUTATION
    assert len(result.determinism.fixture_mutations) == 1


def test_dirty_worktree_gate_passes_clean_fixture_hashes():
    path = "tests/fixtures/consent/consent_request.json"
    stable_hash = "abc123"
    gate_input = DirtyWorktreeGateInput(
        tracked_fixture_paths=(path,),
        tracked_fixture_hashes_before={path: stable_hash},
        tracked_fixture_hashes_after={path: stable_hash},
    )
    result = DirtyWorktreeGate().evaluate(gate_input)
    assert result.status is DeterminismGateStatus.PASS


def test_dirty_worktree_gate_blocks_unrelated_dirty_files():
    gate_input = DeterminismGateInput(
        unrelated_dirty_paths=("agent/STATE.md",),
    )
    result = DeterminismGate().evaluate(gate_input)
    assert result.status is DeterminismGateStatus.BLOCKED_UNRELATED_DIRTY_FILES


def test_core_strict_probe_gate_requires_arg_type_call_arg_union_attr():
    missing_codes = evaluate_core_strict_probe_gate(
        CoreStrictProbeGateInput(
            probe_command_present=True,
            probe_passed=True,
            enabled_error_codes=("arg-type",),
            probe_targets_core_files=True,
        )
    )
    assert (
        missing_codes.status
        is ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_MISSING
    )
    assert set(missing_codes.missing_error_codes) == {
        "call-arg",
        "union-attr",
    }

    complete = CoreStrictProbeGate().evaluate(
        CoreStrictProbeGateInput(
            probe_command_present=True,
            probe_passed=True,
            enabled_error_codes=tuple(sorted(CORE_STRICT_PROBE_ERROR_CODES)),
            probe_targets_core_files=True,
        )
    )
    assert complete.status is ToolingTruthGateStatus.PASS


def test_tooling_truth_gate_detects_baseline_only_overclaim():
    result = evaluate_tooling_truth_gate(
        ToolingTruthGateInput(
            baseline_mypy_documented=True,
            cited_strength=ValidationClaimStrength.BASELINE_ONLY,
            core_strict_probe_present=False,
        )
    )
    assert result.status is ToolingTruthGateStatus.WARN_BASELINE_ONLY


def test_tooling_truth_gate_accepts_core_strict_probe_with_required_codes():
    result = ToolingTruthGate().evaluate(
        ToolingTruthGateInput(
            baseline_mypy_documented=True,
            core_strict_probe_documented=True,
            ruff_documented=True,
            cited_strength=ValidationClaimStrength.CORE_STRICT_PROBE,
            core_strict_probe_present=True,
            core_strict_probe_passed=True,
            core_strict_probe_error_codes=tuple(sorted(CORE_STRICT_PROBE_ERROR_CODES)),
        )
    )
    assert result.status is ToolingTruthGateStatus.PASS

"""P1.7.15 — Path Governance Test Harness tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    PathGovernanceHarnessExpectation,
    PathGovernanceHarnessRunInput,
    PathGovernanceHarnessRunResult,
    PathGovernanceHarnessScenario,
    PathGovernanceHarnessScenarioKind,
    PathGovernanceHarnessStatus,
    PathGovernanceHarnessStepResult,
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    build_default_path_governance_harness_suite,
    build_path_governance_harness_scenario,
    run_path_governance_harness_scenario,
    run_path_governance_harness_suite,
)

_REQUIRED_SCENARIO_KINDS = {
    "TRUSTED_PATH_ALLOWED_SHADOW",
    "UNTRUSTED_SOURCE_REVIEW_SHADOW",
    "PATH_ESCAPE_RESTRICT_SHADOW",
    "SOURCE_DISTRUST_CONFLICT_SHADOW",
    "CRITICAL_RISK_QUARANTINE_RECOMMENDED",
    "MISSING_PROVENANCE_REVIEW_SHADOW",
    "UNTRUSTED_BOUNDARY_COMMAND_SURFACE",
    "TRACE_PAYLOAD_ONLY",
    "VIOLATION_DRIFT_PAYLOAD_ONLY",
    "UNKNOWN",
}

_REQUIRED_EXPECTATIONS = {
    "EXPECT_WOULD_ALLOW",
    "EXPECT_WOULD_REVIEW",
    "EXPECT_WOULD_RESTRICT",
    "EXPECT_WOULD_DENY",
    "EXPECT_WOULD_DISTRUST",
    "EXPECT_WOULD_QUARANTINE",
    "EXPECT_CONFLICT_SIGNAL",
    "EXPECT_TRACE_PAYLOAD",
    "EXPECT_VIOLATION_PAYLOAD",
    "EXPECT_NO_ENFORCEMENT",
    "EXPECT_NO_LEDGER",
    "EXPECT_NO_RUNTIME_MUTATION",
    "EXPECT_NO_POLICY_CALL",
    "EXPECT_NO_APPROVAL_ACTIVATION",
    "EXPECT_NO_SOURCE_MUTATION",
    "UNKNOWN",
}

_REQUIRED_STATUSES = {
    "PASS",
    "FAIL",
    "SKIPPED",
    "UNAVAILABLE",
    "ERROR",
    "UNKNOWN",
}

_P1_7_REGRESSION_FILES = (
    "tests/path_governance/test_p1_7_0_foundation.py",
    "tests/path_governance/test_p1_7_1_path_identity.py",
    "tests/path_governance/test_p1_7_2_source_identity.py",
    "tests/path_governance/test_p1_7_3_source_trust_taxonomy.py",
    "tests/path_governance/test_p1_7_4_trusted_roots.py",
    "tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py",
    "tests/path_governance/test_p1_7_6_path_authority_scope.py",
    "tests/path_governance/test_p1_7_7_untrusted_content_boundary.py",
    "tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py",
    "tests/path_governance/test_p1_7_9_path_source_risk_classification.py",
    "tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py",
    "tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py",
    "tests/path_governance/test_p1_7_12_conflict_precedence.py",
    "tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py",
    "tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py",
)


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.test_harness"),
    )


def _scenario(kind: PathGovernanceHarnessScenarioKind) -> PathGovernanceHarnessScenario:
    return build_path_governance_harness_scenario(kind)


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathGovernanceHarnessScenarioKind",
        "PathGovernanceHarnessExpectation",
        "PathGovernanceHarnessStatus",
        "PathGovernanceHarnessScenario",
        "PathGovernanceHarnessRunInput",
        "PathGovernanceHarnessStepResult",
        "PathGovernanceHarnessRunResult",
        "build_path_governance_harness_scenario",
        "run_path_governance_harness_scenario",
        "run_path_governance_harness_suite",
        "build_default_path_governance_harness_suite",
    ):
        assert hasattr(pg, name)


def test_scenario_kind_has_required_values() -> None:
    assert {item.value for item in PathGovernanceHarnessScenarioKind} == (
        _REQUIRED_SCENARIO_KINDS
    )


def test_expectation_has_required_values() -> None:
    assert {item.value for item in PathGovernanceHarnessExpectation} == (
        _REQUIRED_EXPECTATIONS
    )


def test_status_has_required_values() -> None:
    assert {item.value for item in PathGovernanceHarnessStatus} == _REQUIRED_STATUSES


def test_harness_scenario_builds_deterministically() -> None:
    first = build_path_governance_harness_scenario(
        PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW,
    )
    second = build_path_governance_harness_scenario(
        PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW,
    )
    assert first.scenario_id == second.scenario_id


def test_harness_run_input_builds_deterministically() -> None:
    scenarios = build_default_path_governance_harness_suite()
    first = PathGovernanceHarnessRunInput(scenarios=scenarios)
    second = PathGovernanceHarnessRunInput(scenarios=scenarios)
    assert first.run_id == second.run_id
    assert first.input_hash == second.input_hash


def test_harness_step_result_builds_deterministically() -> None:
    scenario = _scenario(PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY)
    first = run_path_governance_harness_scenario(scenario)
    second = run_path_governance_harness_scenario(scenario)
    assert first.step_id == second.step_id
    assert first.step_hash == second.step_hash


def test_harness_run_result_builds_deterministically() -> None:
    first = run_path_governance_harness_suite()
    second = run_path_governance_harness_suite()
    assert first.result_id == second.result_id
    assert first.result_hash == second.result_hash


def test_default_suite_exists_and_uses_dev_fixture() -> None:
    suite = build_default_path_governance_harness_suite()
    assert len(suite) == 9
    for scenario in suite:
        assert scenario.source_label is ProjectionSourceLabel.DEV_FIXTURE
        assert scenario.fixtures_label is ProjectionSourceLabel.DEV_FIXTURE


@pytest.mark.parametrize(
    "kind",
    [
        PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW,
        PathGovernanceHarnessScenarioKind.UNTRUSTED_SOURCE_REVIEW_SHADOW,
        PathGovernanceHarnessScenarioKind.PATH_ESCAPE_RESTRICT_SHADOW,
        PathGovernanceHarnessScenarioKind.SOURCE_DISTRUST_CONFLICT_SHADOW,
        PathGovernanceHarnessScenarioKind.CRITICAL_RISK_QUARANTINE_RECOMMENDED,
        PathGovernanceHarnessScenarioKind.MISSING_PROVENANCE_REVIEW_SHADOW,
        PathGovernanceHarnessScenarioKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE,
        PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY,
        PathGovernanceHarnessScenarioKind.VIOLATION_DRIFT_PAYLOAD_ONLY,
    ],
)
def test_default_scenario_runs_deterministically(
    kind: PathGovernanceHarnessScenarioKind,
) -> None:
    first = run_path_governance_harness_scenario(_scenario(kind))
    second = run_path_governance_harness_scenario(_scenario(kind))
    assert first.status == second.status
    assert first.step_hash == second.step_hash
    assert first.status is not PathGovernanceHarnessStatus.ERROR


def test_trusted_path_allowed_shadow_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW),
    )
    assert result.status in {
        PathGovernanceHarnessStatus.PASS,
        PathGovernanceHarnessStatus.SKIPPED,
        PathGovernanceHarnessStatus.UNAVAILABLE,
    }
    assert result.observed_refs.get("harness_enforcement") == "false"


def test_untrusted_source_review_shadow_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.UNTRUSTED_SOURCE_REVIEW_SHADOW),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert "source_shadow_decision" in result.observed_refs
    assert result.observed_refs.get("harness_source_mutation") == "false"


def test_path_escape_restrict_shadow_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.PATH_ESCAPE_RESTRICT_SHADOW),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert result.observed_refs.get("path_shadow_decision") in {
        "WOULD_RESTRICT",
        "WOULD_DENY",
    }


def test_source_distrust_conflict_shadow_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.SOURCE_DISTRUST_CONFLICT_SHADOW),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert int(result.observed_refs.get("conflict_signal_count", "0")) > 0


def test_critical_risk_quarantine_recommended_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.CRITICAL_RISK_QUARANTINE_RECOMMENDED),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert result.observed_refs.get("path_shadow_decision") in {
        "WOULD_QUARANTINE",
        "WOULD_DENY",
    }


def test_missing_provenance_review_shadow_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.MISSING_PROVENANCE_REVIEW_SHADOW),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert result.observed_refs.get("provenance_binding_present") == "false"


def test_untrusted_boundary_command_surface_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert int(result.observed_refs.get("conflict_signal_count", "0")) >= 0


def test_trace_payload_only_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert result.observed_refs.get("trace_payload_id")
    assert result.observed_refs.get("trace_written") == "false"
    assert result.observed_refs.get("ledger_written") == "false"


def test_violation_drift_payload_only_scenario_runs() -> None:
    result = run_path_governance_harness_scenario(
        _scenario(PathGovernanceHarnessScenarioKind.VIOLATION_DRIFT_PAYLOAD_ONLY),
    )
    assert result.status is PathGovernanceHarnessStatus.PASS
    assert result.observed_refs.get("violation_payload_id")
    assert result.observed_refs.get("runtime_mutated") == "false"
    assert result.observed_refs.get("enforcement_triggered") == "false"


def test_suite_result_hash_is_deterministic() -> None:
    first = run_path_governance_harness_suite()
    second = run_path_governance_harness_suite()
    assert first.result_hash == second.result_hash


def test_changed_scenario_changes_result_hash() -> None:
    baseline = run_path_governance_harness_suite()
    suite = build_default_path_governance_harness_suite()
    changed_scenario = build_path_governance_harness_scenario(
        PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW,
        metadata={"fixture": "DEV_FIXTURE", "mutation": "changed"},
    )
    mutated = tuple(
        changed_scenario
        if item.scenario_kind is PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW
        else item
        for item in suite
    )
    changed = run_path_governance_harness_suite(scenarios=mutated)
    assert changed.result_hash != baseline.result_hash


def test_harness_preserves_source_labels() -> None:
    scenario = build_path_governance_harness_scenario(
        PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        fixtures_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    step = run_path_governance_harness_scenario(scenario)
    run_input = PathGovernanceHarnessRunInput(scenarios=(scenario,))
    run_result = run_path_governance_harness_suite(run_input=run_input)
    assert scenario.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert step.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert run_input.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert run_result.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    suite = build_default_path_governance_harness_suite()
    for scenario in suite:
        assert scenario.source_label is ProjectionSourceLabel.DEV_FIXTURE
        assert scenario.source_label is not ProjectionSourceLabel.LIVE
        assert scenario.fixtures_label is ProjectionSourceLabel.DEV_FIXTURE


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc_info:
        PathGovernanceHarnessScenario.from_dict({
            "scenario_kind": "TRUSTED_PATH_ALLOWED_SHADOW",
            "description": "DEV_FIXTURE",
            "expected_outcomes": [],
            "shadow_authority_grant": True,
        })
    assert "UNKNOWN_FIELD" in str(exc_info.value.code)


def test_no_policy_engine_call_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
    ):
        assert snippet not in source


def test_no_approval_activation_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.approval",
        "approval_queue",
        "activate_approval",
    ):
        assert snippet not in source


def test_no_ledger_write_exists() -> None:
    source = _module_source()
    for snippet in (
        "write_ledger",
        "ledger_writer",
        "from agentic_runtime.ledger",
    ):
        assert snippet not in source


def test_no_global_trace_write_exists() -> None:
    source = _module_source()
    for snippet in (
        "trace_writer",
        "emit_trace",
        "from agentic_runtime.trace",
    ):
        assert snippet not in source


def test_no_source_trust_mutation() -> None:
    source = _module_source()
    for snippet in (
        "mutate_source",
        "promote_source",
        "demote_source",
        "SourceTrustTaxonomy(",
    ):
        assert snippet not in source


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = _module_source()
    for snippet in (
        "def filter",
        "def rewrite",
        "def sanitize",
        "prompt_compiler",
        "prompt_assembly",
        "injection_firewall",
    ):
        assert snippet not in source


def test_no_memory_or_tool_gating_occurs() -> None:
    source = _module_source()
    for snippet in (
        "memory_writer",
        "write_memory",
        "block_tool",
        "tool_gate",
    ):
        assert snippet not in source


def test_no_runtime_sandbox_approval_imports() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.runtime",
        "AgenticRuntime",
        "from agentic_runtime.sandbox",
        "from agentic_runtime.approval",
        "from agentic_runtime.tools",
        "from agentic_runtime.cli",
        "from agentic_runtime.trace",
        "from agentic_runtime.ledger",
    ):
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = _module_source()
    for snippet in (
        "Path.resolve",
        "Path.exists",
        "Path.stat",
        "open(",
        "read_text",
        "read_bytes",
        "urllib",
        "requests",
        "httpx",
    ):
        assert snippet not in source


def test_p1_7_0_to_p1_7_14_regression_still_pass() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *_P1_7_REGRESSION_FILES,
            "-k",
            "not regression_still_pass",
            "-q",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

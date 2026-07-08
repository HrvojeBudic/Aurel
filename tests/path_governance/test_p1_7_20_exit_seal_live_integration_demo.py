"""P1.7.20 — Path Governance Exit Seal + Live Integration Demo tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    P17_UNAVAILABLE_INTEGRATIONS,
    PathGovernanceExitSealCheckKind,
    PathGovernanceExitSealCheckResult,
    PathGovernanceExitSealDemoInput,
    PathGovernanceExitSealResult,
    PathGovernanceExitSealSideEffects,
    PathGovernanceExitSealStatus,
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    build_default_path_governance_exit_seal_checks,
    build_path_governance_exit_seal_demo_input,
    build_path_governance_exit_seal_side_effects,
    render_path_governance_exit_seal_summary,
    run_path_governance_exit_seal,
)

_REQUIRED_CHECK_KINDS = {
    "PACKAGE_IMPORTS",
    "REPORT_INVENTORY",
    "FOUNDATION_CAPABILITY",
    "PATH_IDENTITY_CAPABILITY",
    "SOURCE_IDENTITY_CAPABILITY",
    "SOURCE_TRUST_TAXONOMY_CAPABILITY",
    "TRUSTED_ROOT_CAPABILITY",
    "PATH_NORMALIZATION_CAPABILITY",
    "AUTHORITY_SCOPE_CAPABILITY",
    "UNTRUSTED_BOUNDARY_CAPABILITY",
    "PROVENANCE_BINDING_CAPABILITY",
    "RISK_CLASSIFICATION_CAPABILITY",
    "PATH_RESOLVER_SHADOW",
    "SOURCE_TRUST_RESOLVER_SHADOW",
    "CONFLICT_PRECEDENCE_SHADOW",
    "PATH_RESOLUTION_TRACE_HOOK",
    "VIOLATION_DRIFT_TRACE_HOOK",
    "TEST_HARNESS_DEMO",
    "POLICY_CONTEXT_BRIDGE_DEMO",
    "PROJECTION_CONTRACT_DEMO",
    "CLI_TUI_BINDING_DEMO",
    "UNAVAILABLE_STATES_PROOF",
    "NO_ENFORCEMENT_PROOF",
    "DOCS_STATE_REPORTS_PROOF",
    "EXIT_SEAL_RESULT",
    "UNKNOWN",
}

_REQUIRED_STATUSES = {"PASS", "FAIL", "SKIPPED", "UNAVAILABLE", "ERROR", "UNKNOWN"}

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
    "tests/path_governance/test_p1_7_15_path_governance_test_harness.py",
    "tests/path_governance/test_p1_7_16_policy_context_bridge.py",
    "tests/path_governance/test_p1_7_17_projection_api_event_contract.py",
    "tests/path_governance/test_p1_7_18_path_governance_cli_tui_binding.py",
)

_FIXTURE_LABEL = ProjectionSourceLabel.DEV_FIXTURE


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.exit_seal"),
    )


def _checks_by_kind(result: PathGovernanceExitSealResult) -> dict[str, PathGovernanceExitSealCheckResult]:
    return {check.check_kind.value: check for check in result.checks}


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathGovernanceExitSealCheckKind",
        "PathGovernanceExitSealStatus",
        "PathGovernanceExitSealSideEffects",
        "PathGovernanceExitSealCheckResult",
        "PathGovernanceExitSealDemoInput",
        "PathGovernanceExitSealResult",
        "build_path_governance_exit_seal_demo_input",
        "build_default_path_governance_exit_seal_checks",
        "run_path_governance_exit_seal",
        "render_path_governance_exit_seal_summary",
    ):
        assert hasattr(pg, name)


def test_exit_seal_check_kind_has_required_values() -> None:
    assert {item.value for item in PathGovernanceExitSealCheckKind} == _REQUIRED_CHECK_KINDS


def test_exit_seal_status_has_required_values() -> None:
    assert {item.value for item in PathGovernanceExitSealStatus} == _REQUIRED_STATUSES


def test_side_effects_default_false() -> None:
    effects = build_path_governance_exit_seal_side_effects()
    assert effects.policy_called is False
    assert effects.approval_created is False
    assert effects.ledger_written is False
    assert effects.global_trace_written is False
    assert effects.runtime_mutated is False
    assert effects.enforcement_triggered is False
    assert effects.source_mutated is False
    assert effects.prompt_filtered is False
    assert effects.memory_written is False
    assert effects.tool_blocked is False


def test_demo_input_builds_deterministically() -> None:
    first = build_path_governance_exit_seal_demo_input()
    second = build_path_governance_exit_seal_demo_input()
    assert first.demo_id == second.demo_id
    assert first.demo_hash == second.demo_hash


def test_check_result_builds_deterministically() -> None:
    payload = {
        "check_id": "",
        "check_kind": PathGovernanceExitSealCheckKind.PACKAGE_IMPORTS.value,
        "status": PathGovernanceExitSealStatus.PASS.value,
        "summary": "package imports",
        "evidence_refs": ["agentic_runtime.path_governance"],
        "source_label": _FIXTURE_LABEL.value,
        "unavailable_reason": "",
        "check_hash": "",
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    first = PathGovernanceExitSealCheckResult.from_dict(payload)
    second = PathGovernanceExitSealCheckResult.from_dict(payload)
    assert first.check_id == second.check_id
    assert first.check_hash == second.check_hash


def test_exit_seal_result_builds_deterministically() -> None:
    first = run_path_governance_exit_seal()
    second = run_path_governance_exit_seal()
    assert first.seal_id == second.seal_id
    assert first.seal_hash == second.seal_hash


def test_default_seal_checks_include_p1_7_0_to_p1_7_19_coverage() -> None:
    checks = build_default_path_governance_exit_seal_checks()
    kinds = {check.check_kind for check in checks}
    for kind in (
        PathGovernanceExitSealCheckKind.FOUNDATION_CAPABILITY,
        PathGovernanceExitSealCheckKind.PATH_IDENTITY_CAPABILITY,
        PathGovernanceExitSealCheckKind.SOURCE_IDENTITY_CAPABILITY,
        PathGovernanceExitSealCheckKind.SOURCE_TRUST_TAXONOMY_CAPABILITY,
        PathGovernanceExitSealCheckKind.TRUSTED_ROOT_CAPABILITY,
        PathGovernanceExitSealCheckKind.PATH_NORMALIZATION_CAPABILITY,
        PathGovernanceExitSealCheckKind.AUTHORITY_SCOPE_CAPABILITY,
        PathGovernanceExitSealCheckKind.UNTRUSTED_BOUNDARY_CAPABILITY,
        PathGovernanceExitSealCheckKind.PROVENANCE_BINDING_CAPABILITY,
        PathGovernanceExitSealCheckKind.RISK_CLASSIFICATION_CAPABILITY,
        PathGovernanceExitSealCheckKind.PATH_RESOLVER_SHADOW,
        PathGovernanceExitSealCheckKind.SOURCE_TRUST_RESOLVER_SHADOW,
        PathGovernanceExitSealCheckKind.CONFLICT_PRECEDENCE_SHADOW,
        PathGovernanceExitSealCheckKind.PATH_RESOLUTION_TRACE_HOOK,
        PathGovernanceExitSealCheckKind.VIOLATION_DRIFT_TRACE_HOOK,
        PathGovernanceExitSealCheckKind.TEST_HARNESS_DEMO,
        PathGovernanceExitSealCheckKind.POLICY_CONTEXT_BRIDGE_DEMO,
        PathGovernanceExitSealCheckKind.PROJECTION_CONTRACT_DEMO,
        PathGovernanceExitSealCheckKind.CLI_TUI_BINDING_DEMO,
        PathGovernanceExitSealCheckKind.DOCS_STATE_REPORTS_PROOF,
    ):
        assert kind in kinds


def test_harness_demo_runs_and_is_dev_fixture_labeled() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[PathGovernanceExitSealCheckKind.TEST_HARNESS_DEMO.value]
    assert check.status is PathGovernanceExitSealStatus.PASS
    assert check.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_policy_context_demo_runs_and_policy_called_false() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[
        PathGovernanceExitSealCheckKind.POLICY_CONTEXT_BRIDGE_DEMO.value
    ]
    assert check.status is PathGovernanceExitSealStatus.PASS
    assert "policy_called=false" in check.evidence_refs
    assert result.side_effects.policy_called is False


def test_projection_demo_builds_api_envelope() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[
        PathGovernanceExitSealCheckKind.PROJECTION_CONTRACT_DEMO.value
    ]
    assert check.status is PathGovernanceExitSealStatus.PASS
    assert len(check.evidence_refs) == 1
    assert len(check.evidence_refs[0]) == 64


def test_cli_demo_renders_read_only_response() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[PathGovernanceExitSealCheckKind.CLI_TUI_BINDING_DEMO.value]
    assert check.status is PathGovernanceExitSealStatus.PASS
    assert len(check.evidence_refs) >= 3


def test_trace_hook_demo_produces_payload_only_no_ledger() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[
        PathGovernanceExitSealCheckKind.PATH_RESOLUTION_TRACE_HOOK.value
    ]
    assert check.status is PathGovernanceExitSealStatus.PASS
    assert "ledger_written=false" in check.evidence_refs
    assert result.side_effects.ledger_written is False
    assert result.side_effects.global_trace_written is False


def test_violation_drift_demo_produces_evidence_only_no_correction() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[
        PathGovernanceExitSealCheckKind.VIOLATION_DRIFT_TRACE_HOOK.value
    ]
    assert check.status is PathGovernanceExitSealStatus.PASS
    assert "runtime_mutated=false" in check.evidence_refs
    assert "enforcement_triggered=false" in check.evidence_refs
    assert result.side_effects.runtime_mutated is False
    assert result.side_effects.enforcement_triggered is False


def test_unavailable_states_are_represented_with_reasons() -> None:
    result = run_path_governance_exit_seal()
    check = _checks_by_kind(result)[PathGovernanceExitSealCheckKind.UNAVAILABLE_STATES_PROOF.value]
    assert check.status is PathGovernanceExitSealStatus.PASS
    joined = " ".join(check.evidence_refs)
    for reason in P17_UNAVAILABLE_INTEGRATIONS.values():
        assert reason in joined


def test_no_enforcement_proof_side_effects_all_false() -> None:
    result = run_path_governance_exit_seal()
    effects = result.side_effects
    assert effects.policy_called is False
    assert effects.approval_created is False
    assert effects.ledger_written is False
    assert effects.global_trace_written is False
    assert effects.runtime_mutated is False
    assert effects.enforcement_triggered is False
    assert effects.source_mutated is False
    assert effects.prompt_filtered is False
    assert effects.memory_written is False
    assert effects.tool_blocked is False


def test_no_fake_live_for_dev_fixture_demo() -> None:
    result = run_path_governance_exit_seal()
    demo_kinds = {
        PathGovernanceExitSealCheckKind.TEST_HARNESS_DEMO,
        PathGovernanceExitSealCheckKind.POLICY_CONTEXT_BRIDGE_DEMO,
        PathGovernanceExitSealCheckKind.PROJECTION_CONTRACT_DEMO,
        PathGovernanceExitSealCheckKind.CLI_TUI_BINDING_DEMO,
        PathGovernanceExitSealCheckKind.PATH_RESOLUTION_TRACE_HOOK,
        PathGovernanceExitSealCheckKind.VIOLATION_DRIFT_TRACE_HOOK,
    }
    for check in result.checks:
        if check.check_kind in demo_kinds:
            assert check.source_label is not ProjectionSourceLabel.LIVE


def test_no_fake_trace_verified() -> None:
    result = run_path_governance_exit_seal()
    for check in result.checks:
        assert check.source_label is not ProjectionSourceLabel.TRACE_VERIFIED


def test_seal_result_hash_is_deterministic() -> None:
    first = run_path_governance_exit_seal()
    second = run_path_governance_exit_seal()
    assert first.seal_hash == second.seal_hash


def test_changed_check_changes_seal_hash() -> None:
    baseline = run_path_governance_exit_seal()
    mutated_checks = []
    for check in baseline.checks:
        if check.check_kind is PathGovernanceExitSealCheckKind.PACKAGE_IMPORTS:
            mutated_checks.append(
                PathGovernanceExitSealCheckResult.from_dict({
                    **check.to_canonical_dict(include_hash=True),
                    "summary": "mutated summary for hash test",
                }),
            )
        else:
            mutated_checks.append(check)
    mutated = PathGovernanceExitSealResult.from_dict({
        **baseline.to_canonical_dict(include_hash=True),
        "checks": [check.to_canonical_dict(include_hash=True) for check in mutated_checks],
    })
    assert mutated.seal_hash != baseline.seal_hash


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc:
        PathGovernanceExitSealDemoInput.from_dict({
            "demo_id": "x",
            "source_label": _FIXTURE_LABEL.value,
            "include_harness_demo": True,
            "include_policy_context_demo": True,
            "include_projection_demo": True,
            "include_cli_demo": True,
            "include_trace_demo": True,
            "include_violation_demo": True,
            "include_unavailable_proof": True,
            "demo_hash": "",
            "metadata": {},
            "shadow_authority_grant": True,
        })
    assert "unknown field" in str(exc.value).lower()


def test_summary_render_is_deterministic() -> None:
    result = run_path_governance_exit_seal()
    first = render_path_governance_exit_seal_summary(result)
    second = render_path_governance_exit_seal_summary(result)
    assert first == second


def test_summary_contains_unavailable_states() -> None:
    result = run_path_governance_exit_seal()
    summary = render_path_governance_exit_seal_summary(result)
    assert "Shell UI not implemented" in summary
    assert "HTTP API server not implemented" in summary


def test_summary_contains_side_effect_truth() -> None:
    result = run_path_governance_exit_seal()
    summary = render_path_governance_exit_seal_summary(result)
    assert "policy_called=False" in summary
    assert "ledger_written=False" in summary


def test_no_policy_engine_call_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
        "import Custos",
        "from agentic_runtime.custos",
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
        "from agentic_runtime.ledger",
        "write_ledger",
        "LedgerWriter",
    ):
        assert snippet not in source


def test_no_global_trace_write_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.trace",
        "emit_trace",
        "write_global_trace",
    ):
        assert snippet not in source


def test_no_source_trust_mutation() -> None:
    source = _module_source()
    for snippet in (
        "mutate_source",
        "promote_source",
        "demote_source",
        "quarantine_source",
    ):
        assert snippet not in source


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = _module_source()
    for snippet in (
        "prompt_compiler",
        "prompt_assembly",
        "def filter",
        "def rewrite",
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
        "from agentic_runtime.memory",
        "from agentic_runtime.prompts",
    ):
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = _module_source()
    for snippet in (
        "Path.exists",
        "Path.resolve",
        "Path.stat",
        "open(",
        "read_text",
        "read_bytes",
        "requests.",
        "urllib",
        "httpx",
    ):
        assert snippet not in source


def test_no_subprocess_or_environment_secret_access() -> None:
    source = _module_source()
    for snippet in (
        "subprocess",
        "os.environ",
    ):
        assert snippet not in source


def test_p1_7_0_to_p1_7_19_regression_still_pass() -> None:
    proc = subprocess.run(
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
    assert proc.returncode == 0, proc.stdout + proc.stderr

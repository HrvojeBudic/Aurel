"""P1.6.18 — Policy CLI harness binding tests."""
from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

from agentic_runtime.cli_modules import policy_commands as policy_cli_mod
from agentic_runtime.policy_cards import PolicyHarnessVerdict
from agentic_runtime.policy_cards.test_harness import PolicyHarnessActual, PolicyHarnessResult
from tests.cli_helpers import run_cli


class TestPolicyHarnessCliList:
    def test_policy_harness_list_works(self):
        proc = run_cli("policy", "harness", "list")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "all_allow_no_conflict" in proc.stdout

    def test_policy_harness_list_json(self):
        proc = run_cli("policy", "harness", "list", "--json")
        assert proc.returncode == 0
        rows = json.loads(proc.stdout)
        case_ids = {row["case_id"] for row in rows}
        assert "deny_beats_allow" in case_ids


class TestPolicyHarnessCliRun:
    def test_policy_harness_run_works(self):
        proc = run_cli("policy", "harness", "run")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "suite_id: custos-v0-default" in proc.stdout

    def test_policy_harness_run_exposes_report_hash(self):
        proc = run_cli("policy", "harness", "run")
        assert "report_hash:" in proc.stdout
        hash_value = proc.stdout.split("report_hash:")[1].strip().split()[0]
        assert len(hash_value) == 64

    def test_policy_harness_run_summary_fields(self):
        proc = run_cli("policy", "harness", "run")
        for field in (
            "case_count:",
            "passed:",
            "failed:",
            "warned:",
            "errored:",
            "skipped:",
            "shadow_only_status:",
            "enforced: false",
        ):
            assert field in proc.stdout

    def test_policy_harness_run_case_works(self):
        proc = run_cli("policy", "harness", "run", "--case", "all_allow_no_conflict")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "verdict: PASS" in proc.stdout

    def test_policy_harness_run_missing_case_returns_unavailable(self):
        proc = run_cli("policy", "harness", "run", "--case", "no_such_case")
        assert proc.returncode == 4
        assert "Unknown case_id: no_such_case" in proc.stdout

    def test_failing_harness_result_returns_non_zero_exit_code(self):
        failing = PolicyHarnessResult(
            case_id="fail_case",
            verdict=PolicyHarnessVerdict.FAIL,
            actual=PolicyHarnessActual(shadow_only=True, enforced=False),
        ).with_canonical_hash()

        def _fake_evaluate(_case):
            return failing

        original = policy_cli_mod.evaluate_policy_harness_case
        policy_cli_mod.evaluate_policy_harness_case = _fake_evaluate
        try:
            code = policy_cli_mod.cmd_policy_harness_run(
                SimpleNamespace(case="all_allow_no_conflict", json=False),
            )
        finally:
            policy_cli_mod.evaluate_policy_harness_case = original
        assert code == 1


class TestPolicyHarnessCliBoundary:
    def test_cli_does_not_duplicate_comparator_logic(self):
        src = inspect.getsource(policy_cli_mod)
        assert "compare_policy_harness_expected_actual" not in src
        assert "PolicyHarnessFailureType" not in src

    def test_cli_imports_registry_not_inline_cases(self):
        src = inspect.getsource(policy_cli_mod)
        assert "list_policy_harness_cases" in src
        assert "default_policy_harness_suite" in src

"""P1.6.20 — Policy exit seal CLI proof tests."""
from __future__ import annotations

import inspect
import json

from agentic_runtime.cli_modules import policy_commands as policy_cli_mod
from agentic_runtime.policy_cards.exit_seal import (
    PolicyExitSealVerdict,
    policy_exit_seal_checks,
    run_policy_exit_seal_check,
)
from tests.cli_helpers import run_cli


class TestCliSealChecks:
    def test_policy_status_command(self):
        proc = run_cli("policy", "status")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "policy_projection.v1" in proc.stdout

    def test_policy_projection_json(self):
        proc = run_cli("policy", "projection", "--json")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        payload = json.loads(proc.stdout)
        assert payload["contract_version"] == "policy_projection.v1"
        assert payload["projection_hash"]

    def test_policy_unavailable_command(self):
        proc = run_cli("policy", "unavailable")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "shell_binding" in proc.stdout

    def test_cli_json_contains_source_labels(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert payload["sections"]["cli_binding"]["source"] == "LIVE"
        assert payload["sections"]["shell_binding"]["source"] == "UNAVAILABLE"

    def test_cli_does_not_invent_live_shell(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert payload["sections"]["shell_binding"]["source"] == "UNAVAILABLE"

    def test_cli_seal_checks_pass(self):
        cli_ids = {
            "cli_status_available_or_honest",
            "cli_projection_json_available_or_honest",
            "cli_unavailable_available_or_honest",
        }
        checks = {c.check_id: c for c in policy_exit_seal_checks()}
        for cid in cli_ids:
            result = run_policy_exit_seal_check(checks[cid])
            assert result.verdict is PolicyExitSealVerdict.PASS, f"{cid}: {result.summary}"


class TestHarnessCliSeal:
    def test_policy_harness_list(self):
        proc = run_cli("policy", "harness", "list")
        assert proc.returncode == 0, proc.stderr + proc.stdout

    def test_policy_harness_run(self):
        proc = run_cli("policy", "harness", "run")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "enforced: false" in proc.stdout

    def test_harness_seal_check_pass(self):
        check = next(
            c for c in policy_exit_seal_checks()
            if c.check_id == "harness_available_or_honestly_unavailable"
        )
        result = run_policy_exit_seal_check(check)
        assert result.verdict is PolicyExitSealVerdict.PASS


class TestCliNonEnforcementBoundary:
    def test_module_does_not_import_runtime(self):
        src = inspect.getsource(policy_cli_mod)
        assert "agentic_runtime.runtime" not in src
        assert "AgenticRuntime(" not in src
        assert ".submit(" not in src.replace("AgenticRuntime.submit()", "")

    def test_module_does_not_import_approval(self):
        src = inspect.getsource(policy_cli_mod)
        assert "approval" not in src.lower()

    def test_module_does_not_import_ledger(self):
        src = inspect.getsource(policy_cli_mod)
        assert "ledger" not in src.lower()

    def test_module_does_not_import_sandbox(self):
        src = inspect.getsource(policy_cli_mod)
        assert "sandbox" not in src.lower()

    def test_module_does_not_enforce_policy(self):
        src = inspect.getsource(policy_cli_mod)
        assert "enforce_policy" not in src.lower()
        assert "block_command" not in src.lower()

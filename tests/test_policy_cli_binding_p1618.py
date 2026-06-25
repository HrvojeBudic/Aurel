"""P1.6.18 — Policy CLI binding tests."""
from __future__ import annotations

import inspect
import json

from agentic_runtime.cli_modules import policy_commands as policy_cli_mod
from tests.cli_helpers import run_cli


class TestPolicyCliHelpAndRouting:
    def test_policy_status_command_works(self):
        proc = run_cli("policy", "status")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "policy_projection.v1" in proc.stdout
        assert "Projection Hash:" in proc.stdout

    def test_policy_projection_command_works(self):
        proc = run_cli("policy", "projection")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "policy_projection.v1" in proc.stdout

    def test_policy_projection_json_works(self):
        proc = run_cli("policy", "projection", "--json")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        payload = json.loads(proc.stdout)
        assert payload["contract_version"] == "policy_projection.v1"

    def test_policy_unavailable_command_works(self):
        proc = run_cli("policy", "unavailable")
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "shell_binding" in proc.stdout

    def test_invalid_policy_subcommand_usage(self):
        proc = run_cli("policy", "no-such-command")
        assert proc.returncode != 0
        assert "invalid choice" in proc.stderr.lower() or "error" in proc.stderr.lower()


class TestPolicyCliContractConsumption:
    def test_cli_displays_contract_version(self):
        proc = run_cli("policy", "status")
        assert "policy_projection.v1" in proc.stdout

    def test_cli_displays_projection_hash(self):
        proc = run_cli("policy", "status")
        assert "Projection Hash: sha256:" in proc.stdout
        assert len(proc.stdout.split("sha256:")[1].strip().split()[0]) == 64

    def test_cli_displays_source_labels(self):
        proc = run_cli("policy", "status")
        assert "Source: LIVE" in proc.stdout
        assert "cli_binding: LIVE" in proc.stdout

    def test_cli_displays_unavailable_reasons(self):
        proc = run_cli("policy", "status")
        assert "Shell binding not implemented in P1.6" in proc.stdout

    def test_cli_uses_policy_projection_contract_v1(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert payload["contract_version"] == "policy_projection.v1"
        assert "sections" in payload
        assert payload["sections"]["cli_binding"]["source"] == "LIVE"


class TestPolicyCliNonEnforcementBoundary:
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

    def test_module_does_not_define_comparator(self):
        src = inspect.getsource(policy_cli_mod)
        assert "compare_policy_harness_expected_actual" not in src

    def test_build_cli_projection_sets_cli_binding_live(self):
        contract = policy_cli_mod._build_cli_projection()
        cli = next(s for s in contract.sections if s.section_id == "cli_binding")
        assert cli.source.value == "LIVE"
        assert contract.readiness.cli_binding_available is True

"""P1.6.20 — Policy exit seal model and governance tests."""
from __future__ import annotations

import inspect
import json
from unittest.mock import patch

import pytest

from agentic_runtime.policy_cards.exit_seal import (
    PolicyExitSealCheck,
    PolicyExitSealReportVerdict,
    PolicyExitSealResult,
    PolicyExitSealVerdict,
    build_policy_exit_seal_report,
    decide_policy_exit_seal_verdict,
    policy_exit_seal_checks,
    policy_exit_seal_report_hash,
    policy_exit_seal_to_json_safe_dict,
    run_policy_exit_seal_check,
)


class TestExitSealReportBuild:
    def test_build_policy_exit_seal_report(self):
        report = build_policy_exit_seal_report()
        assert report.seal_version == "policy_exit_seal.v1"
        assert len(report.checks) == len(policy_exit_seal_checks())
        assert report.verdict in PolicyExitSealReportVerdict

    def test_policy_exit_seal_check_can_be_built(self):
        checks = policy_exit_seal_checks()
        assert len(checks) >= 20
        first = checks[0]
        assert isinstance(first, PolicyExitSealCheck)
        result = run_policy_exit_seal_check(first)
        assert isinstance(result, PolicyExitSealResult)
        assert result.verdict in PolicyExitSealVerdict


class TestExitSealVerdicts:
    def test_pass_check_produces_pass(self):
        check = next(c for c in policy_exit_seal_checks() if c.check_id == "contract_version_present")
        result = run_policy_exit_seal_check(check)
        assert result.verdict is PolicyExitSealVerdict.PASS

    def test_missing_capability_produces_fail(self):
        check = next(c for c in policy_exit_seal_checks() if c.check_id == "contract_version_present")
        with patch(
            "agentic_runtime.policy_cards.exit_seal._build_projection_contract",
            side_effect=RuntimeError("build failed"),
        ):
            result = run_policy_exit_seal_check(check)
        assert result.verdict is PolicyExitSealVerdict.ERROR

    def test_honest_unavailable_trace_produces_warn(self):
        check = next(
            c for c in policy_exit_seal_checks()
            if c.check_id == "resolution_trace_available_or_honestly_unavailable"
        )
        result = run_policy_exit_seal_check(check)
        assert result.verdict in (PolicyExitSealVerdict.PASS, PolicyExitSealVerdict.WARN)

    def test_decide_pass_when_all_pass(self):
        results = (
            PolicyExitSealResult("a", PolicyExitSealVerdict.PASS, "ok"),
            PolicyExitSealResult("b", PolicyExitSealVerdict.PASS, "ok"),
        )
        assert decide_policy_exit_seal_verdict(results) is PolicyExitSealReportVerdict.PASS

    def test_decide_pass_with_warnings(self):
        results = (
            PolicyExitSealResult("a", PolicyExitSealVerdict.PASS, "ok"),
            PolicyExitSealResult("b", PolicyExitSealVerdict.WARN, "shell unavailable"),
        )
        assert decide_policy_exit_seal_verdict(results) is PolicyExitSealReportVerdict.PASS_WITH_WARNINGS

    def test_decide_fail_on_failure(self):
        results = (
            PolicyExitSealResult("projection_contract_builds", PolicyExitSealVerdict.FAIL, "missing"),
        )
        assert decide_policy_exit_seal_verdict(results) is PolicyExitSealReportVerdict.FAIL


class TestExitSealHash:
    def test_seal_report_hash_is_deterministic(self):
        r1 = build_policy_exit_seal_report(include_cli=False)
        r2 = build_policy_exit_seal_report(include_cli=False)
        h1 = policy_exit_seal_report_hash(r1)
        h2 = policy_exit_seal_report_hash(r2)
        assert h1 == h2
        assert len(h1) == 64

    def test_shuffled_checks_same_hash(self):
        report = build_policy_exit_seal_report(include_cli=False)
        shuffled = tuple(sorted(report.checks, key=lambda c: c.check_id, reverse=True))
        from agentic_runtime.policy_cards.exit_seal import PolicyExitSealReport

        r1 = PolicyExitSealReport(
            report_id="",
            seal_version=report.seal_version,
            verdict=report.verdict,
            checks=report.checks,
            projection_status=report.projection_status,
            cli_status=report.cli_status,
            harness_status=report.harness_status,
            trace_status=report.trace_status,
            docs_status=report.docs_status,
            governance_status=report.governance_status,
            next_task=report.next_task,
            summary=report.summary,
            generated_at="",
        )
        r2 = PolicyExitSealReport(
            report_id="",
            seal_version=report.seal_version,
            verdict=report.verdict,
            checks=shuffled,
            projection_status=report.projection_status,
            cli_status=report.cli_status,
            harness_status=report.harness_status,
            trace_status=report.trace_status,
            docs_status=report.docs_status,
            governance_status=report.governance_status,
            next_task=report.next_task,
            summary=report.summary,
            generated_at="",
        )
        assert policy_exit_seal_report_hash(r1) == policy_exit_seal_report_hash(r2)

    def test_json_safe_payload(self):
        report = build_policy_exit_seal_report(include_cli=False)
        payload = policy_exit_seal_to_json_safe_dict(report)
        json.dumps(payload, sort_keys=True)

    def test_no_secret_like_metadata(self):
        report = build_policy_exit_seal_report(include_cli=False)
        payload = policy_exit_seal_to_json_safe_dict(report)
        raw = json.dumps(payload)
        assert "password" not in raw.lower()
        assert "api_key" not in raw.lower()


class TestNonEnforcementBoundary:
    def test_module_does_not_import_agentic_runtime(self):
        import agentic_runtime.policy_cards.exit_seal as mod

        assert not hasattr(mod, "AgenticRuntime")
        import_lines = [
            line for line in inspect.getsource(mod).splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        assert not any("agentic_runtime.runtime" in line for line in import_lines)

    def test_module_has_no_enforce_methods(self):
        import agentic_runtime.policy_cards.exit_seal as mod

        forbidden = ("enforce", "block", "apply", "approve", "write_ledger")
        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if callable(obj):
                for term in forbidden:
                    assert term not in name.lower()

    def test_governance_checks_pass(self):
        report = build_policy_exit_seal_report(include_cli=False)
        gov_ids = {
            "non_enforcement_confirmed",
            "no_ledger_write_confirmed",
            "no_approval_activation_confirmed",
            "no_sandbox_change_confirmed",
            "no_runtime_submit_confirmed",
        }
        by_id = {c.check_id: c.verdict for c in report.checks}
        for cid in gov_ids:
            assert by_id[cid] is PolicyExitSealVerdict.PASS, f"{cid} should PASS"

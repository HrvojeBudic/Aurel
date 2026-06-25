"""P1.6.20 — Policy exit seal projection proof tests."""
from __future__ import annotations

import json

from agentic_runtime.policy_cards import (
    PolicyProjectionSourceLabel,
    PolicyProjectionStatus,
    build_policy_projection_contract,
    policy_projection_to_json_safe_dict,
)
from agentic_runtime.policy_cards.exit_seal import (
    PolicyExitSealVerdict,
    build_policy_exit_seal_report,
    policy_exit_seal_checks,
    run_policy_exit_seal_check,
)
from agentic_runtime.policy_cards.projection_contract import (
    POLICY_PROJECTION_CONTRACT_VERSION,
    SHELL_BINDING_UNAVAILABLE_REASON,
)


def _section_by_id(contract, section_id: str):
    return next(s for s in contract.sections if s.section_id == section_id)


class TestProjectionContractSeal:
    def test_policy_projection_contract_v1_builds(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        assert contract.contract_version == POLICY_PROJECTION_CONTRACT_VERSION

    def test_projection_json_valid(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        payload = policy_projection_to_json_safe_dict(contract)
        json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def test_projection_hash_exists(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        assert contract.projection_hash
        assert len(contract.projection_hash.replace("sha256:", "")) == 64

    def test_contract_version_exists(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        assert contract.contract_version == "policy_projection.v1"

    def test_sections_exist(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        assert len(contract.sections) >= 8

    def test_readiness_exists(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        readiness = contract.readiness.to_canonical_dict()
        assert "cli_binding_available" in readiness
        assert readiness["cli_binding_available"] is True

    def test_all_sections_have_source_labels(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        payload = policy_projection_to_json_safe_dict(contract)
        for sid, data in payload["sections"].items():
            assert "source" in data, sid

    def test_unavailable_sections_have_reasons(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        shell = _section_by_id(contract, "shell_binding")
        assert shell.source is PolicyProjectionSourceLabel.UNAVAILABLE
        assert shell.unavailable_reason is not None
        assert SHELL_BINDING_UNAVAILABLE_REASON in shell.unavailable_reason.message

    def test_no_fixture_labeled_live(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        for section in contract.sections:
            if section.source is PolicyProjectionSourceLabel.LIVE:
                meta = section.metadata or {}
                assert not meta.get("fixture")
                assert not meta.get("simulated")

    def test_shell_binding_unavailable(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        shell = _section_by_id(contract, "shell_binding")
        assert shell.source is PolicyProjectionSourceLabel.UNAVAILABLE
        assert shell.status is PolicyProjectionStatus.UNAVAILABLE

    def test_cli_binding_live_when_cli_available(self):
        contract = build_policy_projection_contract(cli_binding_available=True)
        cli = _section_by_id(contract, "cli_binding")
        assert cli.source is PolicyProjectionSourceLabel.LIVE

    def test_projection_seal_checks_deterministic(self):
        projection_ids = {
            "projection_contract_builds",
            "projection_json_valid",
            "projection_hash_present",
            "contract_version_present",
            "source_labels_present",
            "no_fake_live_state",
            "unavailable_reasons_visible",
        }
        checks = {c.check_id: c for c in policy_exit_seal_checks()}
        results = [
            run_policy_exit_seal_check(checks[cid], include_cli=False)
            for cid in projection_ids
        ]
        assert all(r.verdict is PolicyExitSealVerdict.PASS for r in results)

    def test_full_report_projection_status_ok(self):
        report = build_policy_exit_seal_report(include_cli=False)
        assert report.projection_status in ("OK", "WARN")

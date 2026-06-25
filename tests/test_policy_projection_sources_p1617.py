"""P1.6.17 Policy Projection — source label honesty tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from agentic_runtime.policy_cards import (
    PolicyCardRegistry,
    PolicyProjectionSourceLabel,
    PolicyProjectionStatus,
    build_policy_projection_contract,
    policy_projection_to_json_safe_dict,
)
from agentic_runtime.policy_cards.projection_contract import (
    CLI_BINDING_UNAVAILABLE_REASON,
    SHELL_BINDING_UNAVAILABLE_REASON,
    build_policy_registry_projection,
    build_policy_resolver_projection,
)


def _section_by_id(contract, section_id: str):
    return next(s for s in contract.sections if s.section_id == section_id)


class TestBackendSectionsLive:
    def test_registry_section_is_live_if_backend_exists(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_registry")
        assert section.source is PolicyProjectionSourceLabel.LIVE
        assert section.status is PolicyProjectionStatus.AVAILABLE

    def test_resolver_section_is_live_if_backend_exists(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_resolver")
        assert section.source is PolicyProjectionSourceLabel.LIVE

    def test_conflict_algebra_section_is_live_if_backend_exists(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "conflict_algebra")
        assert section.source is PolicyProjectionSourceLabel.LIVE

    def test_resolution_trace_section_is_live_if_backend_exists(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "resolution_trace")
        assert section.source is PolicyProjectionSourceLabel.LIVE

    def test_violation_trace_section_is_live_if_backend_exists(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "violation_trace")
        assert section.source is PolicyProjectionSourceLabel.LIVE

    def test_policy_harness_section_is_live_if_backend_exists(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_harness")
        assert section.source is PolicyProjectionSourceLabel.LIVE


class TestCliShellUnavailable:
    def test_cli_binding_unavailable_in_p1617(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "cli_binding")
        assert section.source is PolicyProjectionSourceLabel.UNAVAILABLE
        assert section.status is PolicyProjectionStatus.UNAVAILABLE

    def test_cli_binding_reason(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "cli_binding")
        assert section.unavailable_reason is not None
        assert section.unavailable_reason.message == CLI_BINDING_UNAVAILABLE_REASON

    def test_shell_binding_unavailable_in_p1617(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "shell_binding")
        assert section.source is PolicyProjectionSourceLabel.UNAVAILABLE

    def test_shell_binding_honest_reason(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "shell_binding")
        assert section.unavailable_reason is not None
        assert section.unavailable_reason.message == SHELL_BINDING_UNAVAILABLE_REASON


class TestTraceVerifiedUpgrade:
    def test_resolution_trace_trace_verified_when_hash_present(self):
        trace_hash = "a" * 64
        contract = build_policy_projection_contract(resolution_trace_hash=trace_hash)
        section = _section_by_id(contract, "resolution_trace")
        assert section.source is PolicyProjectionSourceLabel.TRACE_VERIFIED
        assert section.hashes.get("resolution_trace_hash") == trace_hash

    def test_violation_trace_trace_verified_when_hash_present(self):
        trace_hash = "b" * 64
        contract = build_policy_projection_contract(violation_trace_hash=trace_hash)
        section = _section_by_id(contract, "violation_trace")
        assert section.source is PolicyProjectionSourceLabel.TRACE_VERIFIED
        assert section.hashes.get("violation_trace_hash") == trace_hash


class TestSimulatedAndFixtureLabels:
    def test_simulated_state_when_source_simulated(self):
        contract = build_policy_projection_contract(
            source=PolicyProjectionSourceLabel.SIMULATED,
        )
        assert contract.source is PolicyProjectionSourceLabel.SIMULATED
        resolver = _section_by_id(contract, "policy_resolver")
        assert resolver.source is PolicyProjectionSourceLabel.SIMULATED

    def test_dev_fixture_when_explicit(self):
        projection = build_policy_registry_projection(
            source=PolicyProjectionSourceLabel.DEV_FIXTURE,
        )
        assert projection.section.source is PolicyProjectionSourceLabel.DEV_FIXTURE


class TestErrorNotFakeLive:
    def test_projection_errors_become_error_not_live(self):
        with patch(
            "agentic_runtime.policy_cards.projection_contract.build_policy_resolver_projection",
            side_effect=RuntimeError("probe failure"),
        ):
            contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_resolver")
        assert section.source is PolicyProjectionSourceLabel.ERROR
        assert section.status is PolicyProjectionStatus.ERROR
        assert section.error is not None


class TestNoUnlabelledMockState:
    def test_no_section_lacks_source_in_projection(self):
        contract = build_policy_projection_contract(
            registry=PolicyCardRegistry(),
        )
        payload = policy_projection_to_json_safe_dict(contract)
        for section_id, section_payload in payload["sections"].items():
            assert "source" in section_payload, f"missing source for {section_id}"
            assert section_payload["source"] in {
                label.value for label in PolicyProjectionSourceLabel
            }

    def test_registry_with_cards_stays_live(self):
        registry = PolicyCardRegistry()
        contract = build_policy_projection_contract(registry=registry)
        section = _section_by_id(contract, "policy_registry")
        assert section.source is PolicyProjectionSourceLabel.LIVE
        assert section.capabilities.get("card_count") == "0"

    def test_resolver_builder_live_by_default(self):
        projection = build_policy_resolver_projection()
        assert projection.section.source is PolicyProjectionSourceLabel.LIVE

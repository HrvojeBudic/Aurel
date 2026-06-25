"""P1.6.17 Policy Projection — integration and boundary tests."""
from __future__ import annotations

import inspect
import json

from agentic_runtime.policy_cards import (
    PolicyCardRegistry,
    PolicyProjectionContract,
    PolicyProjectionEvent,
    PolicyProjectionReadiness,
    PolicyProjectionSection,
    PolicyProjectionSnapshot,
    build_policy_projection_contract,
    build_policy_projection_snapshot,
    policy_projection_to_json_safe_dict,
)
from agentic_runtime.policy_cards import projection_contract as projection_mod


def _section_by_id(contract: PolicyProjectionContract, section_id: str) -> PolicyProjectionSection:
    return next(s for s in contract.sections if s.section_id == section_id)


class TestProjectionIntegration:
    def test_detects_policy_registry_capability(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_registry")
        assert section.capabilities.get("registry_class") == "PolicyCardRegistry"

    def test_detects_policy_resolver_capability(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_resolver")
        assert section.capabilities.get("resolve_fn") == "resolve_policy_cards"

    def test_detects_conflict_algebra_capability(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "conflict_algebra")
        assert section.capabilities.get("strategy") == "strictest_wins"

    def test_detects_resolution_trace_capability(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "resolution_trace")
        assert "resolution_trace" in section.capabilities.get("module", "")

    def test_detects_violation_trace_capability(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "violation_trace")
        assert "violation_trace" in section.capabilities.get("module", "")

    def test_detects_policy_harness_capability(self):
        contract = build_policy_projection_contract()
        section = _section_by_id(contract, "policy_harness")
        assert section.capabilities.get("harness_version", "").startswith("custos-v0")

    def test_includes_readiness_object(self):
        contract = build_policy_projection_contract()
        assert isinstance(contract.readiness, PolicyProjectionReadiness)
        assert contract.readiness.registry_available is True
        assert contract.readiness.cli_binding_available is False
        assert contract.readiness.shell_binding_available is False

    def test_includes_unavailable_reasons_for_cli_shell(self):
        contract = build_policy_projection_contract()
        codes = {reason.code for reason in contract.unavailable_reasons}
        assert "CLI_BINDING_DEFERRED" in codes
        assert "SHELL_BINDING_UNAVAILABLE" in codes

    def test_includes_contract_version(self):
        contract = build_policy_projection_contract()
        assert contract.contract_version == "policy_projection.v1"

    def test_includes_projection_hash(self):
        contract = build_policy_projection_contract()
        assert len(contract.projection_hash) == 64
        assert contract.projection_id.startswith("policy-projection-")

    def test_returns_cli_readable_json_safe_dict(self):
        contract = build_policy_projection_contract()
        payload = policy_projection_to_json_safe_dict(contract)
        serialized = json.dumps(payload, indent=2)
        assert "policy_registry" in serialized
        assert "cli_binding" in serialized

    def test_snapshot_wraps_contract(self):
        snapshot = build_policy_projection_snapshot()
        assert isinstance(snapshot, PolicyProjectionSnapshot)
        assert snapshot.generated_at
        assert snapshot.contract.projection_hash


class TestNonEnforcementBoundary:
    def test_module_does_not_import_runtime(self):
        src = inspect.getsource(projection_mod)
        assert "agentic_runtime.runtime" not in src
        assert "AgenticRuntime(" not in src
        assert ".submit(" not in src.replace("AgenticRuntime.submit()", "")

    def test_contract_objects_have_no_enforcement_methods(self):
        forbidden = {"enforce", "block", "apply", "approve", "write_ledger"}
        for cls in (
            PolicyProjectionContract,
            PolicyProjectionSection,
            PolicyProjectionSnapshot,
            PolicyProjectionEvent,
        ):
            methods = {name for name, _ in inspect.getmembers(cls) if not name.startswith("_")}
            assert not forbidden & methods

    def test_does_not_mutate_registry(self):
        registry = PolicyCardRegistry()
        before_ids = registry.list_card_ids()
        build_policy_projection_contract(registry=registry)
        after_ids = registry.list_card_ids()
        assert before_ids == after_ids

    def test_projection_is_side_effect_free_on_repeat(self):
        c1 = build_policy_projection_contract()
        c2 = build_policy_projection_contract()
        assert c1.projection_hash == c2.projection_hash
        assert len(c1.sections) == len(c2.sections) == 8

    def test_eight_sections_present(self):
        contract = build_policy_projection_contract()
        section_ids = {section.section_id for section in contract.sections}
        assert section_ids == {
            "policy_registry",
            "policy_resolver",
            "conflict_algebra",
            "resolution_trace",
            "violation_trace",
            "policy_harness",
            "cli_binding",
            "shell_binding",
        }

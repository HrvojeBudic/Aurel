"""P1.6.17 Policy Projection Contract — unit tests."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.policy_cards.projection_contract import (
    CLI_BINDING_UNAVAILABLE_REASON,
    POLICY_PROJECTION_CONTRACT_VERSION,
    SHELL_BINDING_UNAVAILABLE_REASON,
    PolicyProjectionContract,
    PolicyProjectionError,
    PolicyProjectionEvent,
    PolicyProjectionEventType,
    PolicyProjectionReadiness,
    PolicyProjectionSection,
    PolicyProjectionSourceLabel,
    PolicyProjectionStatus,
    PolicyProjectionUnavailableReason,
    build_policy_cli_binding_projection,
    build_policy_projection_contract,
    build_policy_projection_event,
    build_policy_shell_binding_projection,
    policy_projection_event_hash,
    policy_projection_event_to_json_safe_dict,
    policy_projection_hash,
    policy_projection_to_json_safe_dict,
)


def _section(
    section_id: str,
    *,
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
    status: PolicyProjectionStatus = PolicyProjectionStatus.AVAILABLE,
    capabilities: dict[str, str] | None = None,
    unavailable_reason: PolicyProjectionUnavailableReason | None = None,
    error: PolicyProjectionError | None = None,
) -> PolicyProjectionSection:
    return PolicyProjectionSection(
        section_id=section_id,
        title=section_id,
        status=status,
        source=source,
        capabilities=capabilities or {},
        unavailable_reason=unavailable_reason,
        error=error,
    )


class TestSourceLabelEnum:
    def test_includes_all_required_labels(self):
        values = {label.value for label in PolicyProjectionSourceLabel}
        assert values == {
            "LIVE",
            "TRACE_VERIFIED",
            "SIMULATED",
            "DEV_FIXTURE",
            "UNAVAILABLE",
            "ERROR",
        }


class TestContractConstruction:
    def test_policy_projection_contract_defaults(self):
        contract = PolicyProjectionContract()
        assert contract.contract_version == POLICY_PROJECTION_CONTRACT_VERSION
        assert contract.contract_version == "policy_projection.v1"

    def test_policy_projection_section_construction(self):
        section = _section("policy_registry")
        assert section.source is PolicyProjectionSourceLabel.LIVE

    def test_policy_projection_readiness_construction(self):
        readiness = PolicyProjectionReadiness(registry_available=True)
        assert readiness.registry_available is True
        assert readiness.cli_binding_available is False

    def test_policy_projection_event_construction(self):
        event = PolicyProjectionEvent(
            event_type=PolicyProjectionEventType.POLICY_PROJECTION_BUILT,
        )
        assert event.event_type is PolicyProjectionEventType.POLICY_PROJECTION_BUILT


class TestCanonicalizationAndHash:
    def test_projection_payload_is_json_safe(self):
        contract = build_policy_projection_contract()
        payload = policy_projection_to_json_safe_dict(contract)
        json.dumps(payload)

    def test_same_input_gives_same_hash(self):
        c1 = build_policy_projection_contract()
        c2 = build_policy_projection_contract()
        assert policy_projection_hash(c1) == policy_projection_hash(c2)
        assert c1.projection_hash == c2.projection_hash

    def test_shuffled_sections_do_not_change_hash(self):
        base = build_policy_projection_contract()
        shuffled = PolicyProjectionContract(
            source=base.source,
            sections=tuple(reversed(base.sections)),
            readiness=base.readiness,
            unavailable_reasons=base.unavailable_reasons,
            errors=base.errors,
            metadata=base.metadata,
        ).with_projection_hash()
        assert shuffled.projection_hash == base.projection_hash

    def test_shuffled_capabilities_do_not_change_hash(self):
        s1 = _section("x", capabilities={"b": "2", "a": "1"})
        s2 = _section("x", capabilities={"a": "1", "b": "2"})
        c1 = PolicyProjectionContract(sections=(s1,)).with_projection_hash()
        c2 = PolicyProjectionContract(sections=(s2,)).with_projection_hash()
        assert c1.projection_hash == c2.projection_hash

    def test_shuffled_unavailable_reasons_do_not_change_hash(self):
        r1 = PolicyProjectionUnavailableReason(code="B", message="b")
        r2 = PolicyProjectionUnavailableReason(code="A", message="a")
        c1 = PolicyProjectionContract(unavailable_reasons=(r1, r2)).with_projection_hash()
        c2 = PolicyProjectionContract(unavailable_reasons=(r2, r1)).with_projection_hash()
        assert c1.projection_hash == c2.projection_hash

    def test_shuffled_errors_do_not_change_hash(self):
        e1 = PolicyProjectionError(code="B", message="b")
        e2 = PolicyProjectionError(code="A", message="a")
        c1 = PolicyProjectionContract(errors=(e1, e2)).with_projection_hash()
        c2 = PolicyProjectionContract(errors=(e2, e1)).with_projection_hash()
        assert c1.projection_hash == c2.projection_hash

    def test_event_payload_is_json_safe(self):
        contract = build_policy_projection_contract()
        event = build_policy_projection_event(
            event_type=PolicyProjectionEventType.POLICY_PROJECTION_BUILT,
            contract=contract,
        )
        json.dumps(policy_projection_event_to_json_safe_dict(event))

    def test_event_hash_is_deterministic(self):
        contract = build_policy_projection_contract()
        event = build_policy_projection_event(
            event_type=PolicyProjectionEventType.POLICY_PROJECTION_BUILT,
            contract=contract,
        )
        assert policy_projection_event_hash(event) == policy_projection_event_hash(event)


class TestInvariants:
    def test_unavailable_section_requires_reason(self):
        with pytest.raises(ValueError, match="unavailable_reason"):
            PolicyProjectionSection(
                section_id="cli_binding",
                title="CLI",
                status=PolicyProjectionStatus.UNAVAILABLE,
                source=PolicyProjectionSourceLabel.UNAVAILABLE,
            )

    def test_error_section_requires_safe_error(self):
        with pytest.raises(ValueError, match="error"):
            PolicyProjectionSection(
                section_id="broken",
                title="Broken",
                status=PolicyProjectionStatus.ERROR,
                source=PolicyProjectionSourceLabel.ERROR,
            )

    def test_cli_binding_section_unavailable_by_default(self):
        cli = build_policy_cli_binding_projection()
        assert cli.section.source is PolicyProjectionSourceLabel.UNAVAILABLE
        assert cli.section.status is PolicyProjectionStatus.UNAVAILABLE

    def test_shell_binding_section_unavailable_by_default(self):
        shell = build_policy_shell_binding_projection()
        assert shell.section.source is PolicyProjectionSourceLabel.UNAVAILABLE
        assert shell.section.status is PolicyProjectionStatus.UNAVAILABLE

    def test_cli_binding_has_scheduled_reason(self):
        cli = build_policy_cli_binding_projection()
        assert cli.section.unavailable_reason is not None
        assert cli.section.unavailable_reason.message == CLI_BINDING_UNAVAILABLE_REASON

    def test_shell_binding_has_honest_reason(self):
        shell = build_policy_shell_binding_projection()
        assert shell.section.unavailable_reason is not None
        assert shell.section.unavailable_reason.message == SHELL_BINDING_UNAVAILABLE_REASON

    def test_every_built_section_has_source(self):
        contract = build_policy_projection_contract()
        for section in contract.sections:
            assert section.source is not None
            payload = policy_projection_to_json_safe_dict(contract)
            for section_payload in payload["sections"].values():
                assert "source" in section_payload

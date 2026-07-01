"""P1.ENF-A identity submit context tests."""
from __future__ import annotations

from copy import deepcopy

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
    IdentitySubmitContext,
    RiskLevel,
    build_identity_submit_context,
    build_runtime,
    evaluate_identity_submit_preflight,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import bounded_test_approver


def _hash(seed: str) -> str:
    return (seed * 64)[:64]


def _identity_payload() -> dict:
    return {
        "canonical_hashes": {
            "identity_kernel": _hash("1"),
            "persona_manifest": _hash("2"),
            "operator_contract": _hash("3"),
            "communication_modes": _hash("4"),
        },
        "raw_hashes": {
            "identity_kernel": _hash("a"),
            "persona_manifest": _hash("b"),
            "operator_contract": _hash("c"),
            "communication_modes": _hash("d"),
        },
        "source_paths": {
            "identity_kernel": "config/aurel/identity_kernel.yaml",
            "persona_manifest": "config/aurel/persona_manifest.yaml",
            "operator_contract": "config/aurel/operator_contract.yaml",
            "communication_modes": "config/aurel/communication_modes.yaml",
        },
    }


def _card() -> AgentCard:
    return AgentCard.make(
        name="P1 ENF-A Identity Agent",
        agent_class=AgentClass.EXECUTION,
        mission="exercise identity submit context",
        authority=AuthorityScope(
            read_paths=["*"],
            write_paths=["*"],
            max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=["read_file"],
    )


def _cmd(card: AgentCard):
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool="read_file",
        args={"path": "src/a.txt"},
        rationale="identity submit context test",
        declared_risk=RiskLevel.LOW,
        expected_effect="read identity-bound fixture",
    )


def test_identity_submit_context_hash_is_stable():
    first = build_identity_submit_context(_identity_payload())
    second = build_identity_submit_context(_identity_payload())
    assert first.context_hash.value == second.context_hash.value
    assert len(first.context_hash.value) == 64


def test_identity_submit_context_is_bound_to_submit_artifacts(tmp_path):
    card = _card()
    context = build_identity_submit_context(_identity_payload())
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=GovernanceEnforcementMode.ADVISORY,
        ),
        identity_context_loader=lambda: context,
    )
    kernel.sandbox.write_file("src/a.txt", "hello")

    result = kernel.runtime.submit(_cmd(card), card)

    assert result.ok
    artifact = result.observation.artifacts["governance_enforcement"][
        "identity_submit_context"
    ]
    assert artifact["status"] == "bound"
    assert artifact["artifact"]["context_hash"] == context.context_hash.value
    assert artifact["artifact"]["identity_kernel_hash"] == context.identity_kernel_hash


def test_missing_identity_context_is_advisory_in_shadow_mode():
    result = evaluate_identity_submit_preflight(
        mode=GovernanceEnforcementMode.SHADOW_ONLY,
        require_identity_context=False,
        loader=None,
    )
    assert result.should_block is False
    assert result.status.value == "advisory_missing"
    assert result.artifact.missing_behavior.value == "record_advisory"


def test_missing_required_identity_fails_closed_in_enforce_mode(tmp_path):
    card = _card()
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
            require_identity_context=True,
        ),
        identity_context_loader=None,
    )
    kernel.sandbox.write_file("src/a.txt", "hello")

    result = kernel.runtime.submit(_cmd(card), card)

    assert not result.ok
    artifact = result.observation.artifacts["governance_enforcement"][
        "identity_submit_context"
    ]
    assert artifact["status"] == "blocked_missing_required_context"
    assert artifact["should_block"] is True


def test_identity_submit_context_does_not_mutate_identity_state():
    payload = _identity_payload()
    before = deepcopy(payload)
    context = build_identity_submit_context(payload)
    result = evaluate_identity_submit_preflight(
        mode=GovernanceEnforcementMode.ADVISORY,
        require_identity_context=False,
        loader=lambda: context,
    )
    assert result.status.value == "bound"
    assert payload == before


def test_identity_submit_context_rejects_invalid_hashes():
    payload = _identity_payload()
    payload["canonical_hashes"]["identity_kernel"] = "not-a-hash"
    try:
        build_identity_submit_context(payload)
    except ValueError as exc:
        assert "identity_kernel_hash" in str(exc)
    else:
        raise AssertionError("invalid identity hash was accepted")


def test_identity_submit_context_object_serializes_deterministically():
    context = IdentitySubmitContext(
        identity_kernel_hash=_hash("1"),
        persona_manifest_hash=_hash("2"),
        operator_contract_hash=_hash("3"),
        canonical_hashes={"operator_contract": _hash("3"), "identity_kernel": _hash("1")},
        raw_hashes={"operator_contract": _hash("c"), "identity_kernel": _hash("a")},
    )
    assert context.to_canonical_dict()["canonical_hashes"] == {
        "identity_kernel": _hash("1"),
        "operator_contract": _hash("3"),
    }

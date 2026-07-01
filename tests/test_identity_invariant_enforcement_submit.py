"""P1.ENF-D1 Identity invariant enforcement submit tests."""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
    IdentityInvariantCheckInput,
    IdentityInvariantDecision,
    RiskLevel,
    build_identity_submit_context,
    build_runtime,
    evaluate_identity_invariant_enforcement,
    evaluate_identity_submit_with_invariants,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.identity_invariant_enforcement import IDENTITY_INVARIANT_SIGNALS_KEY
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
        name="P1 ENF-D1 Identity Agent",
        agent_class=AgentClass.EXECUTION,
        mission="exercise identity invariant enforcement",
        authority=AuthorityScope(
            read_paths=["*"],
            write_paths=["*"],
            max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=["read_file"],
    )


def _cmd(card: AgentCard, signals: dict | None = None):
    args = {"path": "src/a.txt"}
    if signals is not None:
        args[IDENTITY_INVARIANT_SIGNALS_KEY] = signals
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool="read_file",
        args=args,
        rationale="identity invariant enforcement test",
        declared_risk=RiskLevel.LOW,
        expected_effect="exercise identity invariant enforcement",
    )


def _check_input(**overrides) -> IdentityInvariantCheckInput:
    base = IdentityInvariantCheckInput()
    return IdentityInvariantCheckInput(
        **{**base.to_canonical_dict(), **overrides}
    )


def test_missing_identity_context_blocks_in_enforce_fail_closed(tmp_path):
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
        "identity_invariant_enforcement"
    ]
    assert artifact["should_block"] is True
    assert artifact["artifact"]["decision"] == "deny"


def test_missing_identity_context_warns_in_advisory():
    result = evaluate_identity_submit_with_invariants(
        mode=GovernanceEnforcementMode.ADVISORY,
        require_identity_context=True,
        loader=None,
    )
    assert result.should_block is False
    assert result.preflight.status.value == "advisory_missing"
    assert result.invariant_enforcement.decision is IdentityInvariantDecision.WARN


def test_shadow_only_records_without_blocking():
    context = build_identity_submit_context(_identity_payload())
    result = evaluate_identity_submit_with_invariants(
        mode=GovernanceEnforcementMode.SHADOW_ONLY,
        require_identity_context=False,
        loader=lambda: context,
        submit_metadata={
            "args": {
                IDENTITY_INVARIANT_SIGNALS_KEY: {
                    "self_authority_escalation": True,
                }
            }
        },
    )
    assert result.should_block is False
    assert result.invariant_enforcement.artifact.violations
    assert result.invariant_enforcement.decision is IdentityInvariantDecision.ALLOW


def test_disabled_identity_enforcement_returns_unavailable():
    result = evaluate_identity_invariant_enforcement(
        mode=GovernanceEnforcementMode.DISABLED_UNAVAILABLE,
        check_input=_check_input(),
    )
    assert result.decision is IdentityInvariantDecision.UNAVAILABLE
    assert result.should_block is False
    assert result.artifact.truth_label == "IDENTITY_INVARIANT_UNAVAILABLE"


def test_operator_authority_invariant_blocks_impersonation_attempt():
    result = evaluate_identity_invariant_enforcement(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        check_input=_check_input(
            claims_operator_authority=True,
            operator_authority_present=False,
        ),
    )
    assert result.should_block is True
    assert any(item.invariant_id == "IK-007" for item in result.artifact.violations)


def test_canon_authority_invariant_blocks_silent_override_attempt():
    result = evaluate_identity_invariant_enforcement(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        check_input=_check_input(
            claims_canon_override=True,
            canon_authority_present=False,
        ),
    )
    assert result.should_block is True
    assert any(
        item.truth_label == "CANON_AUTHORITY_REQUIRED"
        for item in result.artifact.violations
    )


def test_identity_mutation_invariant_blocks_silent_mutation_attempt():
    result = evaluate_identity_invariant_enforcement(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        check_input=_check_input(silent_identity_mutation=True),
    )
    assert result.should_block is True
    assert any(item.invariant_id == "IK-006" for item in result.artifact.violations)


def test_identity_invariant_decision_contains_evidence_refs():
    result = evaluate_identity_invariant_enforcement(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        check_input=_check_input(policy_bypass_self_grant=True),
    )
    assert result.artifact.evidence_refs
    assert "config/aurel/identity_kernel.yaml" in result.artifact.evidence_refs
    assert result.artifact.violations[0].evidence_refs


def test_runtime_submit_binds_identity_invariant_result(tmp_path):
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
    governance = result.observation.artifacts["governance_enforcement"]
    assert "identity_invariant_enforcement" in governance
    assert governance["identity_submit_context"]["status"] == "bound"
    assert governance["identity_invariant_enforcement"]["artifact"]["decision"] == "allow"

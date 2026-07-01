"""P1.ENF-E runtime submit sandbox backend gate integration tests."""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
    RiskLevel,
    SANDBOX_BACKEND_SIGNALS_KEY,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import bounded_test_approver


def _card() -> AgentCard:
    return AgentCard.make(
        name="P1 ENF-E Sandbox Agent",
        agent_class=AgentClass.EXECUTION,
        mission="exercise sandbox backend gate",
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
        args[SANDBOX_BACKEND_SIGNALS_KEY] = signals
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool="read_file",
        args=args,
        rationale="sandbox backend gate submit test",
        declared_risk=RiskLevel.LOW,
        expected_effect="exercise sandbox backend gate",
    )


def test_runtime_submit_binds_sandbox_backend_decision(tmp_path):
    card = _card()
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=GovernanceEnforcementMode.SHADOW_ONLY,
        ),
    )
    kernel.sandbox.write_file("src/a.txt", "hello")

    result = kernel.runtime.submit(_cmd(card), card)

    assert result.ok
    artifact = result.observation.artifacts["governance_enforcement"][
        "sandbox_backend_gate"
    ]
    assert artifact["artifact"]["sandbox_safety_class"] == "UNSAFE_LOCAL"
    assert artifact["artifact"]["sandbox_backend_kind"] == "UnsafeLocalSandbox"
    assert artifact["artifact"]["sandbox_gate_decision"] in {"allow", "warn"}


def test_runtime_submit_blocks_unsafe_backend_when_safe_required(tmp_path):
    card = _card()
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
            require_safe_sandbox_backend=True,
        ),
    )
    kernel.sandbox.write_file("src/a.txt", "hello")

    result = kernel.runtime.submit(_cmd(card), card)

    assert not result.ok
    artifact = result.observation.artifacts["governance_enforcement"][
        "sandbox_backend_gate"
    ]
    assert artifact["should_block"] is True
    assert artifact["decision"] == "deny"
    assert artifact["artifact"]["sandbox_safety_class"] == "UNSAFE_LOCAL"


def test_runtime_submit_preserves_dev_fixture_default_when_explicit(tmp_path):
    card = _card()
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=GovernanceEnforcementMode.ADVISORY,
            require_safe_sandbox_backend=False,
        ),
    )
    kernel.sandbox.write_file("src/a.txt", "hello")

    result = kernel.runtime.submit(_cmd(card), card)

    assert result.ok
    artifact = result.observation.artifacts["governance_enforcement"][
        "sandbox_backend_gate"
    ]
    assert artifact["should_block"] is False
    assert artifact["artifact"]["unsafe_backend_allowed_reason"] == (
        "explicit_dev_allow_unsafe_gate"
    )


def test_runtime_submit_blocks_live_claim_on_unsafe_backend(tmp_path):
    card = _card()
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        ),
    )
    kernel.sandbox.write_file("src/a.txt", "hello")

    result = kernel.runtime.submit(
        _cmd(card, signals={"claims_live_execution": True}),
        card,
    )

    assert not result.ok
    artifact = result.observation.artifacts["governance_enforcement"][
        "sandbox_backend_gate"
    ]
    assert artifact["should_block"] is True
    assert any(
        v["key"] == "live_claim_denied"
        for v in artifact["artifact"]["violations"]
    )

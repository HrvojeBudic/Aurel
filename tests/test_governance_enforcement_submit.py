"""P1.ENF-A governance enforcement submit bridge tests."""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
    P1ENFASideEffectProof,
    P1ENFAResult,
    RiskLevel,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.policy_cards import PolicyCardRegistry
from agentic_runtime.policy_cards.models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from agentic_runtime.policy_cards.tool_permissions import (
    ToolIdentityMatcher,
    ToolMatchMode,
    ToolPermissionDecision,
    ToolPermissionPolicyCard,
    ToolPermissionRule,
    ToolPermissionType,
)
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import bounded_test_approver


def _card() -> AgentCard:
    return AgentCard.make(
        name="P1 ENF-A Submit Agent",
        agent_class=AgentClass.EXECUTION,
        mission="exercise governance enforcement bridge",
        authority=AuthorityScope(
            read_paths=["*"],
            write_paths=["*"],
            max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=["read_file", "write_file"],
    )


def _cmd(card: AgentCard, tool: str = "read_file", args: dict | None = None):
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args or {"path": "src/a.txt"},
        rationale="P1.ENF-A submit bridge test",
        declared_risk=RiskLevel.LOW,
        expected_effect="exercise submit bridge",
    )


def _policy_card(kind: PolicyCardKind, cid: str) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=cid,
            slug=cid,
            name=cid,
            version="1.0",
            namespace="p1-enf-a-test",
        ),
        kind=kind,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description="P1.ENF-A test card",
    )


def _tool_registry(decision: ToolPermissionDecision) -> PolicyCardRegistry:
    return PolicyCardRegistry.from_cards(
        [
            ToolPermissionPolicyCard(
                policy_card=_policy_card(PolicyCardKind.TOOL_PERMISSION, "p1-enf-tool"),
                schema_version="1.0",
                permission_rules=(
                    ToolPermissionRule(
                        matcher=ToolIdentityMatcher(
                            match_mode=ToolMatchMode.EXACT,
                            tool_name="read_file",
                        ),
                        permission_type=ToolPermissionType.EXECUTE,
                        decision=decision,
                    ),
                ),
                default_decision=ToolPermissionDecision.DENY,
            )
        ]
    )


def _kernel(tmp_path, *, mode: GovernanceEnforcementMode, registry=None, **config):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(lambda r: True),
        policy_card_registry=registry,
        governance_enforcement_config=GovernanceEnforcementConfig(
            mode=mode,
            **config,
        ),
    )
    kernel.sandbox.write_file("src/a.txt", "hello")
    return kernel


def _governance_artifact(result):
    return result.observation.artifacts["governance_enforcement"]


def test_shadow_mode_preserves_existing_submit_behavior(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        mode=GovernanceEnforcementMode.SHADOW_ONLY,
        registry=_tool_registry(ToolPermissionDecision.DENY),
    )

    result = kernel.runtime.submit(_cmd(card), card)

    assert result.ok
    policy_artifact = _governance_artifact(result)["policy_submit_influence"]
    assert policy_artifact["should_block"] is False
    assert policy_artifact["status"] == "shadow_only"
    assert policy_artifact["artifact"]["overall_decision"] == "deny"


def test_advisory_mode_records_policy_influence_without_blocking(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        mode=GovernanceEnforcementMode.ADVISORY,
        registry=_tool_registry(ToolPermissionDecision.DENY),
    )

    result = kernel.runtime.submit(_cmd(card), card)

    assert result.ok
    policy_artifact = _governance_artifact(result)["policy_submit_influence"]
    assert policy_artifact["should_block"] is False
    assert policy_artifact["status"] == "advisory_recorded"
    assert policy_artifact["artifact"]["enforced"] is False


def test_enforce_fail_closed_blocks_on_policy_deny(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        registry=_tool_registry(ToolPermissionDecision.DENY),
    )

    result = kernel.runtime.submit(_cmd(card), card)

    assert not result.ok
    assert result.decision.verdict.value == "deny"
    assert result.verifier.code == "GOVERNANCE_ENFORCEMENT_DENIED"
    policy_artifact = _governance_artifact(result)["policy_submit_influence"]
    assert policy_artifact["should_block"] is True
    assert policy_artifact["status"] == "blocked_policy_deny"


def test_enforce_fail_closed_blocks_on_missing_required_policy_context(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        registry=None,
        require_policy_context=True,
    )

    result = kernel.runtime.submit(_cmd(card), card)

    assert not result.ok
    policy_artifact = _governance_artifact(result)["policy_submit_influence"]
    assert policy_artifact["status"] == "blocked_missing_required_context"
    assert policy_artifact["should_block"] is True


def test_policy_submit_influence_emits_audit_artifact(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        mode=GovernanceEnforcementMode.ADVISORY,
        registry=_tool_registry(ToolPermissionDecision.ALLOW),
    )

    result = kernel.runtime.submit(_cmd(card), card)

    artifact = _governance_artifact(result)
    policy_artifact = artifact["policy_submit_influence"]
    assert artifact["truth_label"] == "ENFORCEMENT_BRIDGE"
    assert len(policy_artifact["artifact"]["context_hash"]) == 64
    assert len(policy_artifact["artifact"]["registry_hash"]) == 64
    assert len(policy_artifact["artifact_hash"]) == 64


def test_p1_enf_a_does_not_implement_p2_9_b():
    proof = P1ENFASideEffectProof()
    assert proof.p2_9_b_implemented is False
    assert proof.p2_9_c_started is False
    assert proof.p2_9_d_started is False
    assert proof.p2_10_plus_started is False


def test_p1_enf_a_does_not_create_product_ui():
    proof = P1ENFASideEffectProof()
    assert proof.product_ui_created is False
    assert proof.shell_command_router_created is False


def test_p1_enf_a_does_not_claim_trace_verified():
    proof = P1ENFASideEffectProof()
    assert proof.fake_trace_verified_claimed is False
    assert proof.fake_live_shell_claimed is False


def test_p1_enf_a_does_not_claim_full_custos_runtime():
    proof = P1ENFASideEffectProof()
    assert proof.full_custos_runtime_created is False


def test_p1_enf_a_does_not_create_permission_matrix():
    proof = P1ENFASideEffectProof()
    assert proof.permission_matrix_created is False


def test_p1_enf_a_vertical_result_side_effect_proof_is_hashable():
    result = P1ENFAResult(
        mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        policy_influence_result={"status": "blocked_policy_deny"},
        identity_submit_context_result={"status": "bound"},
        entrypoint_guard_result={"classification": "governed_runtime_submit"},
    )
    assert len(result.result_hash) == 64
    assert result.side_effect_proof.trace_ledger_rewritten is False

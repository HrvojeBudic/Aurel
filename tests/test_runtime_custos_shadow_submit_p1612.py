"""P1.6.12 submit-time Custos shadow projection tests."""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import DenyAllApprover
from agentic_runtime.policy_cards import (
    PolicyCardRegistry,
    create_default_sandbox_policy_card,
)
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


def _card(*, max_risk: RiskLevel = RiskLevel.HIGH, denied_tools: list[str] | None = None):
    return AgentCard.make(
        name="Shadow Submit Agent",
        agent_class=AgentClass.EXECUTION,
        mission="test shadow projection",
        authority=AuthorityScope(
            write_paths=["*"],
            read_paths=["*"],
            max_risk=max_risk,
            allow_network=True,
        ),
        allowed_tools=[
            "list_dir",
            "read_file",
            "write_file",
            "run_shell",
        ],
        denied_tools=denied_tools or [],
    )


def _cmd(card: AgentCard, tool: str = "read_file", args: dict | None = None) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args or {"path": "src/a.txt"},
        rationale="projection test",
        declared_risk=RiskLevel.LOW,
        expected_effect="read test fixture",
    )


def _policy_card(kind: PolicyCardKind, cid: str) -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=cid,
            slug=cid,
            name=cid,
            version="1.0",
            namespace="test",
        ),
        kind=kind,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.GLOBAL),
        description="test card",
    )


def _tool_card(
    decision: ToolPermissionDecision,
    *,
    tool: str = "read_file",
    cid: str = "tool-shadow",
) -> ToolPermissionPolicyCard:
    return ToolPermissionPolicyCard(
        policy_card=_policy_card(PolicyCardKind.TOOL_PERMISSION, cid),
        schema_version="1.0",
        permission_rules=(
            ToolPermissionRule(
                matcher=ToolIdentityMatcher(
                    match_mode=ToolMatchMode.EXACT,
                    tool_name=tool,
                ),
                permission_type=ToolPermissionType.EXECUTE,
                decision=decision,
            ),
        ),
        default_decision=ToolPermissionDecision.DENY,
    )


def _registry_for(decision: ToolPermissionDecision, *, tool: str = "read_file") -> PolicyCardRegistry:
    return PolicyCardRegistry.from_cards([_tool_card(decision, tool=tool)])


def _kernel(tmp_path, *, registry=None, enabled=False, approval_gate=None):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=approval_gate or bounded_test_approver(lambda r: True),
        policy_card_registry=registry,
        enable_policy_shadow_projection=enabled,
    )
    kernel.sandbox.write_file("src/a.txt", "hello")
    return kernel


def _projection(result):
    return result.observation.artifacts.get("policy_shadow_projection")


def test_flag_false_and_no_registry_preserve_result_without_projection(tmp_path):
    card = _card()
    kernel = _kernel(tmp_path, registry=None, enabled=False)
    result = kernel.runtime.submit(_cmd(card), card)
    assert result.ok
    assert _projection(result) is None


def test_registry_flag_false_preserves_result_without_projection(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        registry=_registry_for(ToolPermissionDecision.DENY),
        enabled=False,
    )
    result = kernel.runtime.submit(_cmd(card), card)
    assert result.ok
    assert _projection(result) is None


def test_flag_true_without_registry_does_not_crash_or_attach_projection(tmp_path):
    card = _card()
    kernel = _kernel(tmp_path, registry=None, enabled=True)
    result = kernel.runtime.submit(_cmd(card), card)
    assert result.ok
    assert _projection(result) is None


def test_registry_enabled_attaches_projection_metadata(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        registry=_registry_for(ToolPermissionDecision.DENY),
        enabled=True,
    )
    result = kernel.runtime.submit(_cmd(card), card)
    payload = _projection(result)
    assert result.ok
    assert payload["enabled"] is True
    assert payload["mode"] == "shadow_only"
    assert payload["enforced"] is False
    assert payload["runtime_effective_action"] == "RUNTIME_ALLOW"
    assert payload["custos_effective_action"] == "WOULD_DENY"
    assert payload["alignment_status"] == "CUSTOS_STRICTER"
    assert "RUNTIME_ALLOWED_CUSTOS_WOULD_DENY" in payload["mismatch_codes"]


def test_custos_require_approval_and_warn_do_not_alter_runtime_result(tmp_path):
    card = _card()
    for decision, expected in (
        (ToolPermissionDecision.APPROVAL_REQUIRED, "WOULD_REQUIRE_APPROVAL"),
        (ToolPermissionDecision.SANDBOX_REQUIRED, "WOULD_WARN"),
    ):
        kernel = _kernel(tmp_path, registry=_registry_for(decision), enabled=True)
        result = kernel.runtime.submit(_cmd(card), card)
        assert result.ok
        assert _projection(result)["custos_effective_action"] == expected
        assert _projection(result)["alignment_status"] == "CUSTOS_STRICTER"


def test_runtime_stricter_case_visible_without_changing_p0_denial(tmp_path):
    card = _card(denied_tools=["read_file"])
    kernel = _kernel(
        tmp_path,
        registry=_registry_for(ToolPermissionDecision.ALLOW),
        enabled=True,
    )
    result = kernel.runtime.submit(_cmd(card), card)
    payload = _projection(result)
    assert not result.ok
    assert result.decision.verdict.value == "deny"
    assert payload["runtime_effective_action"] == "RUNTIME_DENY"
    assert payload["custos_effective_action"] == "WOULD_ALLOW"
    assert payload["alignment_status"] == "RUNTIME_STRICTER"
    assert "RUNTIME_POLICY_STRICTER_THAN_CUSTOS" in payload["mismatch_codes"]


def test_sandbox_policy_card_mismatch_visible_not_enforced(tmp_path):
    card = _card()
    registry = PolicyCardRegistry.from_cards([create_default_sandbox_policy_card()])
    kernel = _kernel(tmp_path, registry=registry, enabled=True)
    result = kernel.runtime.submit(_cmd(card), card)
    payload = _projection(result)
    assert result.ok
    assert payload["alignment_status"] == "CUSTOS_STRICTER"
    assert "SANDBOX_POLICY_CARD_STRICTER_THAN_RUNTIME" in payload["mismatch_codes"]


def test_shadow_failure_records_error_and_submit_still_returns(tmp_path):
    class BrokenRegistry:
        def canonical_hash(self):
            return "c" * 64

        def get_applicable(self, context):
            raise RuntimeError("resolver unavailable")

    card = _card()
    kernel = _kernel(tmp_path, registry=BrokenRegistry(), enabled=True)
    result = kernel.runtime.submit(_cmd(card), card)
    payload = _projection(result)
    assert result.ok
    assert payload["alignment_status"] == "SHADOW_ERROR"
    assert payload["custos_effective_action"] == "WOULD_ERROR"
    assert payload["enforced"] is False
    assert "CUSTOS_SHADOW_RESOLUTION_ERROR" in payload["mismatch_codes"]


def test_p0_approval_path_still_determines_result(tmp_path):
    card = _card(max_risk=RiskLevel.LOW)
    kernel = _kernel(
        tmp_path,
        registry=_registry_for(ToolPermissionDecision.ALLOW, tool="run_shell"),
        enabled=True,
        approval_gate=DenyAllApprover(),
    )
    result = kernel.runtime.submit(
        _cmd(card, tool="run_shell", args={"cmd": ["echo", "hello"]}),
        card,
    )
    payload = _projection(result)
    assert not result.ok
    assert result.decision.verdict.value == "require_approval"
    assert result.approval_decision is not None
    assert result.approval_decision.approved is False
    assert payload["runtime_effective_action"] == "RUNTIME_DENY"
    assert payload["custos_effective_action"] == "WOULD_ALLOW"


def test_p0_verifier_and_write_result_remain_authoritative(tmp_path):
    card = _card()
    kernel = _kernel(
        tmp_path,
        registry=_registry_for(ToolPermissionDecision.DENY, tool="write_file"),
        enabled=True,
    )
    result = kernel.runtime.submit(
        _cmd(
            card,
            tool="write_file",
            args={"path": "src/new.txt", "content": "written", "create_dirs": True},
        ),
        card,
    )
    assert result.ok
    assert result.verifier.passed is True
    assert result.rolled_back is False
    assert kernel.sandbox.read_file("src/new.txt") == "written"
    assert _projection(result)["custos_effective_action"] == "WOULD_DENY"

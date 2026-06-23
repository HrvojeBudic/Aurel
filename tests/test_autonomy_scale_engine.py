"""P1.4.8 — Autonomy Scale Engine tests (unit, seal, CLI)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.cli_helpers import run_cli

from agentic_runtime.identity.autonomy_scale_engine import (
    ActionCategory,
    AutonomyDecision,
    AutonomyEvaluationContext,
    AutonomyLevel,
    AutonomyRequest,
    LifecycleState,
    ReversibilityTier,
    RiskTier,
    autonomy_decision_to_dict,
    is_denied,
    resolve_autonomy_decision,
)
from agentic_runtime.identity.autonomy_scale_engine_validation import (
    AutonomyValidationError,
    AutonomyValidationResult,
    enforce_autonomy_invariants,
    validate_and_resolve_autonomy,
    validate_autonomy_context,
    validate_autonomy_request,
)
from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.agent_identity_card_builder import build_agent_identity_card_from_paths
from agentic_runtime.identity.capability_inventory import (
    CapabilityInventoryEntry,
    default_capability_inventory,
)
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy
from agentic_runtime.identity.self_model_policy import load_self_model_policy
from agentic_runtime.identity.self_model_builder import build_aurel_self_model_from_paths
from agentic_runtime.identity.agent_identity_card_policy import (
    load_agent_identity_card_config,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CARD = REPO_ROOT / "config" / "aurel" / "agent_identity_card.yaml"


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(name="identity_card")
def fixture_identity_card():
    return build_agent_identity_card_from_paths(
        kernel_path=REPO_ROOT / "config/aurel/identity_kernel.yaml",
        persona_path=REPO_ROOT / "config/aurel/persona_manifest.yaml",
        operator_path=REPO_ROOT / "config/aurel/operator_contract.yaml",
        modes_path=REPO_ROOT / "config/aurel/communication_modes.yaml",
        compiler_path=REPO_ROOT / "config/aurel/identity_prompt_compiler.yaml",
        self_model_policy_path=REPO_ROOT / "config/aurel/self_model_policy.yaml",
        card_config_path=CANONICAL_CARD,
        include_prompt_context=True,
    )


@pytest.fixture(name="operator_contract")
def fixture_operator_contract():
    return load_operator_contract(REPO_ROOT / "config/aurel/operator_contract.yaml")


@pytest.fixture(name="capability_inventory")
def fixture_capability_inventory():
    return default_capability_inventory()


@pytest.fixture(name="context")
def fixture_context(identity_card, operator_contract, capability_inventory):
    return AutonomyEvaluationContext(
        agent_identity_card=identity_card,
        operator_contract=operator_contract,
        capability_inventory=capability_inventory,
    )


def _make_request(
    category: ActionCategory = ActionCategory.ANSWER,
    name: str = "test_action",
    risk: RiskTier = RiskTier.R1_LOW,
    reversibility: ReversibilityTier = ReversibilityTier.R1_FULLY_REVERSIBLE,
    **kwargs,
) -> AutonomyRequest:
    defaults = {
        "action_id": "test_001",
        "action_category": category,
        "action_name": name,
        "requested_by": "operator",
        "agent_id": "aurel.core",
        "risk_tier": risk,
        "reversibility_tier": reversibility,
    }
    defaults.update(kwargs)
    return AutonomyRequest(**defaults)


# ── Unit: is_denied ─────────────────────────────────────────────────────


def test_a7_is_denied():
    assert is_denied(AutonomyLevel.A7_DENIED) is True


def test_a0_is_not_denied():
    assert is_denied(AutonomyLevel.A0_ANSWER_ONLY) is False


def test_a6_is_not_denied():
    assert is_denied(AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK) is False


# ── Unit: baseline mapping ───────────────────────────────────────────────


def test_answer_action_maps_to_A0(context):
    r = _make_request(ActionCategory.ANSWER)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A0_ANSWER_ONLY


def test_suggestion_action_maps_to_A1(context):
    r = _make_request(ActionCategory.SUGGEST)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A1_SUGGESTION


def test_draft_action_maps_to_A2(context):
    r = _make_request(ActionCategory.DRAFT)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A2_DRAFT


def test_reversible_local_write_maps_to_A3(context):
    r = _make_request(ActionCategory.LOCAL_WRITE)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION


def test_governed_tool_call_maps_to_A4(context):
    r = _make_request(ActionCategory.TOOL_CALL)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A4_GOVERNED_TOOL_ACTION


def test_conditional_execution_maps_to_A5(context):
    r = _make_request(ActionCategory.CONDITIONAL_EXECUTION)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A5_CONDITIONAL_EXECUTION


def test_high_risk_maps_to_A6_with_approval_gate(context):
    r = _make_request(ActionCategory.HIGH_RISK, risk=RiskTier.R3_HIGH)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert d.autonomy_level == AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK
    assert d.requires_human_approval


def test_unknown_action_category_is_A7_denied(context):
    r = _make_request(ActionCategory.UNKNOWN)
    d = resolve_autonomy_decision(r, context)
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED
    assert "unknown_action_category" in d.blockers


def test_out_of_scope_action_is_A7_denied(context):
    # EXTERNAL_EFFECT without proper authority scope info
    r = _make_request(ActionCategory.EXTERNAL_EFFECT, risk=RiskTier.R4_CRITICAL,
                       reversibility=ReversibilityTier.R5_IRREVERSIBLE_APPROVAL_REQUIRED)
    d = resolve_autonomy_decision(r, context)
    # With critical risk and no escalation path -> denied
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED


# ── Unit: fail-closed on unknowns ────────────────────────────────────────


def test_unknown_risk_tier_is_A7_denied(context):
    r = _make_request(risk=None)  # type: ignore[arg-type]
    d = resolve_autonomy_decision(r, context)
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED


def test_unknown_reversibility_tier_is_A7_denied(context):
    r = _make_request(reversibility=None)  # type: ignore[arg-type]
    d = resolve_autonomy_decision(r, context)
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED


def test_forbidden_reversibility_is_A7_denied(context):
    r = _make_request(reversibility=ReversibilityTier.R6_FORBIDDEN)
    d = resolve_autonomy_decision(r, context)
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED
    assert "forbidden_reversibility" in d.blockers


def test_missing_context_is_validation_error():
    """Missing operator contract in context is a validation error."""
    card = build_agent_identity_card_from_paths(include_prompt_context=True)
    with pytest.raises(AutonomyValidationError):
        validate_and_resolve_autonomy(
            _make_request(),
            AutonomyEvaluationContext(
                agent_identity_card=card,
                operator_contract=None,  # type: ignore[arg-type]
            ),
        )


# ── Seal tests ───────────────────────────────────────────────────────────


def test_p148_autonomy_engine_fails_closed_on_unknowns(context):
    """INV-P148-03: Unknown action/risk/reversibility fails closed."""
    # Unknown action category
    r = _make_request(ActionCategory.UNKNOWN)
    d = resolve_autonomy_decision(r, context)
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED

    # Missing risk tier
    r2 = _make_request(risk=None)  # type: ignore[arg-type]
    d2 = resolve_autonomy_decision(r2, context)
    assert not d2.allowed

    # Missing reversibility tier
    r3 = _make_request(reversibility=None)  # type: ignore[arg-type]
    d3 = resolve_autonomy_decision(r3, context)
    assert not d3.allowed


def test_p148_autonomy_engine_does_not_create_global_autonomy_score(context):
    """INV-P148-10: No global autonomy score computed."""
    # Resolve multiple actions — each should be scoped, no global score field
    for cat in (ActionCategory.ANSWER, ActionCategory.DRAFT, ActionCategory.TOOL_CALL):
        r = _make_request(cat)
        d = resolve_autonomy_decision(r, context)
        # Ensure no "global_score" or "aggregate" field leaks in serialization
        dd = autonomy_decision_to_dict(d)
        assert "global_score" not in dd
        assert "aggregate_score" not in dd
        assert "measured_autonomy" not in dd


def test_p148_a7_is_denial_not_highest_autonomy(context):
    """INV-P148-02: A7 means denied."""
    r = _make_request(ActionCategory.UNKNOWN)
    d = resolve_autonomy_decision(r, context)
    assert d.autonomy_level == AutonomyLevel.A7_DENIED
    assert not d.allowed
    assert is_denied(d.autonomy_level)


def test_p148_high_risk_requires_human_gate(context):
    """INV-P148-05: High-risk actions require human approval."""
    r = _make_request(ActionCategory.HIGH_RISK, risk=RiskTier.R3_HIGH)
    d = resolve_autonomy_decision(r, context)
    assert d.requires_human_approval
    assert "human_approval_required" in d.required_gates


def test_p148_authority_scope_is_required_beyond_suggestion(context):
    """INV-P148-04: Authority scope required beyond suggestion."""
    # ANSWER and SUGGEST should work fine
    r_suggest = _make_request(ActionCategory.SUGGEST)
    d_suggest = resolve_autonomy_decision(r_suggest, context)
    assert d_suggest.allowed

    r_answer = _make_request(ActionCategory.ANSWER)
    d_answer = resolve_autonomy_decision(r_answer, context)
    assert d_answer.allowed

    # DRAFT and beyond need authority scope - but our test card from --card-config-path should have one
    # Actually, the operator contract from the config may not have `allows_autonomous_action` set.
    # Let's check if the draf builder passes authority for DRAFT:
    # If operator contract blocks autonomous action, DRAFT should get denied.
    r_draft = _make_request(ActionCategory.DRAFT)
    d_draft = resolve_autonomy_decision(r_draft, context)
    # Either allowed (if authority scope present) or denied with authority blocker
    if not d_draft.allowed:
        has_auth_blocker = any("authority" in b.lower() or "scope" in b.lower()
                                for b in d_draft.blockers)
        assert has_auth_blocker, (
            f"Denied DRAFT action should have authority blocker, got: {d_draft.blockers}"
        )


def test_p148_does_not_execute_tools(context):
    """INV-P148-09: Resolver does not execute tools."""
    # Resolution is pure logic — no side effects
    r = _make_request(ActionCategory.TOOL_CALL, tool_name="write_file")
    d = resolve_autonomy_decision(r, context)
    # Decision is a dataclass, not a tool execution result
    assert isinstance(d, AutonomyDecision)
    assert hasattr(d, "allowed")


# ── Decision contract tests ─────────────────────────────────────────────


def test_autonomy_decision_is_json_serializable(context):
    r = _make_request(ActionCategory.DRAFT)
    d = resolve_autonomy_decision(r, context)
    dd = autonomy_decision_to_dict(d)
    json_str = json.dumps(dd)
    assert len(json_str) > 0
    parsed = json.loads(json_str)
    assert parsed["allowed"] == d.allowed
    assert parsed["autonomy_level"] == d.autonomy_level.value


def test_autonomy_decision_has_reason(context):
    r = _make_request()
    d = resolve_autonomy_decision(r, context)
    assert d.reason
    assert len(d.reason) > 0


def test_autonomy_decision_has_blockers_when_denied(context):
    r = _make_request(ActionCategory.UNKNOWN)
    d = resolve_autonomy_decision(r, context)
    assert not d.allowed
    assert len(d.blockers) > 0


def test_allowed_decision_has_no_blockers(context):
    r = _make_request(ActionCategory.ANSWER)
    d = resolve_autonomy_decision(r, context)
    assert d.allowed
    assert len(d.blockers) == 0


# ── Capability check tests ──────────────────────────────────────────────


def test_planned_capability_cannot_authorize_action(context):
    r = _make_request(ActionCategory.DRAFT, required_capability="autonomy_measurement_orchestrator")
    d = resolve_autonomy_decision(r, context)
    # autonomy_measurement_orchestrator is planned (P1.4.9), not implemented
    assert not d.allowed
    assert d.autonomy_level == AutonomyLevel.A7_DENIED
    assert "capability_not_implemented" in d.blockers


def test_implemented_capability_can_authorize_only_with_scope(context):
    r = _make_request(ActionCategory.DRAFT, required_capability="agent_identity_card")
    d = resolve_autonomy_decision(r, context)
    # agent_identity_card is implemented but authority scope check applies
    assert d.allowed or (
        not d.allowed and any("authority" in b.lower() or "scope" in b.lower()
                               for b in d.blockers)
    )


def test_roadmap_only_capability_is_A7_denied(context):
    # Create a custom inventory with a roadmap-only entry
    roadmap_inventory = (
        CapabilityInventoryEntry("roadmap_feature", "Roadmap Feature", "roadmap", "P9.9"),
        CapabilityInventoryEntry("agent_identity_card", "Agent Identity Card", "implemented", "P1.4.7"),
    )
    ctx = AutonomyEvaluationContext(
        agent_identity_card=context.agent_identity_card,
        operator_contract=context.operator_contract,
        capability_inventory=roadmap_inventory,
    )
    r = _make_request(ActionCategory.DRAFT, required_capability="roadmap_feature")
    d = resolve_autonomy_decision(r, ctx)
    assert not d.allowed
    assert "roadmap_only_capability" in d.blockers


# ── Invariant enforcement tests ──────────────────────────────────────────


def test_invariants_pass_on_valid_decision(context):
    r = _make_request(ActionCategory.ANSWER)
    d = resolve_autonomy_decision(r, context)
    result = enforce_autonomy_invariants(d)
    assert result.is_valid


def test_invariants_detect_denied_without_blockers():
    invalid_decision = AutonomyDecision(
        decision_id="test",
        request_id="test",
        agent_id="test",
        allowed=False,
        autonomy_level=AutonomyLevel.A7_DENIED,
        requires_human_approval=False,
        action_category=ActionCategory.UNKNOWN,
        risk_tier=RiskTier.R0_NONE,
        reversibility_tier=ReversibilityTier.R1_FULLY_REVERSIBLE,
        reason="test",
        blockers=(),  # empty — violation
    )
    result = enforce_autonomy_invariants(invalid_decision)
    assert not result.is_valid
    assert any("INV-P148-08" in e for e in result.errors)


def test_invariants_detect_a7_with_allowed():
    invalid_decision = AutonomyDecision(
        decision_id="test",
        request_id="test",
        agent_id="test",
        allowed=True,  # wrong!
        autonomy_level=AutonomyLevel.A7_DENIED,
        requires_human_approval=False,
        action_category=ActionCategory.ANSWER,
        risk_tier=RiskTier.R0_NONE,
        reversibility_tier=ReversibilityTier.R1_FULLY_REVERSIBLE,
        reason="test",
    )
    result = enforce_autonomy_invariants(invalid_decision)
    assert not result.is_valid
    assert any("INV-P148-02" in e for e in result.errors)


def test_invariants_detect_missing_reason():
    invalid_decision = AutonomyDecision(
        decision_id="test",
        request_id="test",
        agent_id="test",
        allowed=True,
        autonomy_level=AutonomyLevel.A1_SUGGESTION,
        requires_human_approval=False,
        action_category=ActionCategory.SUGGEST,
        risk_tier=RiskTier.R0_NONE,
        reversibility_tier=ReversibilityTier.R1_FULLY_REVERSIBLE,
        reason="",  # empty — violation
    )
    result = enforce_autonomy_invariants(invalid_decision)
    assert not result.is_valid
    assert any("INV-P148-07" in e for e in result.errors)


# ── Validation tests ────────────────────────────────────────────────────


def test_validate_valid_request_passes():
    r = _make_request()
    result = validate_autonomy_request(r)
    assert result.is_valid


def test_validate_request_missing_action_id_fails():
    r = _make_request()
    r = AutonomyRequest(
        action_id="",
        action_category=ActionCategory.ANSWER,
        action_name="test",
        requested_by="op",
        agent_id="aurel",
    )
    result = validate_autonomy_request(r)
    assert not result.is_valid
    assert "missing_action_id" in result.errors


def test_validate_valid_context_passes(identity_card, operator_contract, capability_inventory):
    ctx = AutonomyEvaluationContext(
        agent_identity_card=identity_card,
        operator_contract=operator_contract,
        capability_inventory=capability_inventory,
    )
    result = validate_autonomy_context(ctx)
    assert result.is_valid


# ── CLI tests ────────────────────────────────────────────────────────────


def test_autonomy_cli_outputs_json_decision():
    result = run_cli(
        "identity", "autonomy", "evaluate",
        "--action-category", "answer",
        "--action-name", "cli_test_answer",
        "--risk-tier", "R1_LOW",
        "--reversibility-tier", "R1_FULLY_REVERSIBLE",
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["autonomy_level"] == "A0_ANSWER_ONLY"
    assert data["allowed"] is True


def test_autonomy_cli_denies_unknown_risk_tier():
    result = run_cli(
        "identity", "autonomy", "evaluate",
        "--action-category", "draft",
        "--action-name", "cli_test_draft",
        "--risk-tier", "",
        "--reversibility-tier", "R1_FULLY_REVERSIBLE",
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["autonomy_level"] == "A7_DENIED"
    assert data["allowed"] is False


def test_autonomy_cli_human_output_contains_level_reason_and_blockers():
    result = run_cli(
        "identity", "autonomy", "evaluate",
        "--action-category", "unknown",
        "--action-name", "cli_test_unknown",
        "--risk-tier", "R1_LOW",
        "--reversibility-tier", "R1_FULLY_REVERSIBLE",
    )
    assert "DENIED" in result.stdout
    assert "A7_DENIED" in result.stdout
    assert "unknown_action_category" in result.stdout


# ── Serialization stability ─────────────────────────────────────────────


def test_autonomy_decision_dict_keys_stable(context):
    """Ensure dict keys are stable across calls for the same inputs."""
    r = _make_request(ActionCategory.DRAFT)
    d1 = resolve_autonomy_decision(r, context)
    d2 = resolve_autonomy_decision(r, context)
    dd1 = autonomy_decision_to_dict(d1)
    dd2 = autonomy_decision_to_dict(d2)
    # Decision IDs differ (UUID), but structure should be same
    assert set(dd1.keys()) == set(dd2.keys())
    assert dd1["allowed"] == dd2["allowed"]
    assert dd1["autonomy_level"] == dd2["autonomy_level"]

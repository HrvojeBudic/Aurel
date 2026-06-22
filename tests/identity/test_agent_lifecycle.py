"""Core state machine tests for P1.4.17 Agent Lifecycle."""
from __future__ import annotations

import json

from agentic_runtime.identity.agent_lifecycle import (
    AgentLifecyclePolicy,
    AgentLifecycleState,
    AgentLifecycleTransitionDecision,
    AgentLifecycleTransitionEvent,
    AgentLifecycleTransitionRequest,
    LifecycleLane,
    LifecycleReasonCode,
    agent_lifecycle_eligibility_profile_to_dict,
    agent_lifecycle_policy_to_dict,
    agent_lifecycle_transition_decision_to_dict,
    agent_lifecycle_transition_event_to_dict,
    agent_lifecycle_transition_request_to_dict,
    build_agent_lifecycle_eligibility_profile,
    create_lifecycle_transition_event,
    default_agent_lifecycle_policy,
    format_lifecycle_decision_human,
    format_lifecycle_profile_human,
    recommend_lifecycle_state,
    validate_agent_lifecycle_transition,
)


# ---------------------------------------------------------------------------
# Enum existence
# ---------------------------------------------------------------------------

def test_lifecycle_states_are_closed_world():
    states = list(AgentLifecycleState)
    assert len(states) == 8
    expected = {"DRAFT", "CANDIDATE", "ACTIVE", "RESTRICTED", "SUSPENDED", "DEPRECATED", "RETIRED", "REVOKED"}
    assert {s.value for s in states} == expected


def test_lifecycle_lanes_exist():
    lanes = list(LifecycleLane)
    assert len(lanes) == 9


def test_lifecycle_reason_codes_exist():
    codes = list(LifecycleReasonCode)
    assert len(codes) >= 20


# ---------------------------------------------------------------------------
# Default policy
# ---------------------------------------------------------------------------

def test_default_lifecycle_policy_exists():
    policy = default_agent_lifecycle_policy()
    assert isinstance(policy, AgentLifecyclePolicy)
    assert len(policy.allowed_transitions) == 8
    assert len(policy.terminal_states) == 1
    assert policy.terminal_states[0] == AgentLifecycleState.REVOKED
    assert policy.active_requires_evidence is True
    assert policy.active_requires_test_battery is True
    assert policy.revoked_is_terminal is True


# ---------------------------------------------------------------------------
# Transition: DRAFT
# ---------------------------------------------------------------------------

def test_draft_to_candidate_allowed():
    request = AgentLifecycleTransitionRequest(
        request_id="r1", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.CANDIDATE,
        reason_code=LifecycleReasonCode.READY_FOR_EVALUATION,
        reason_text="Ready for evaluation",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is True
    assert decision.resulting_state == AgentLifecycleState.CANDIDATE


def test_draft_to_active_denied():
    request = AgentLifecycleTransitionRequest(
        request_id="r2", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="Direct activation",
        evidence_refs=("ref1",),
        test_battery_refs=("ref1",),
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert "forbidden_transition" in decision.blockers[0]


# ---------------------------------------------------------------------------
# Transition: CANDIDATE
# ---------------------------------------------------------------------------

def test_candidate_to_active_requires_evidence():
    request = AgentLifecycleTransitionRequest(
        request_id="r3", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="battery passed",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert any("evidence" in b.lower() for b in decision.blockers)


def test_candidate_to_active_requires_test_battery():
    request = AgentLifecycleTransitionRequest(
        request_id="r4", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="battery passed",
        evidence_refs=("ref1",),
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert any("test_battery" in b.lower() or "battery" in b for b in decision.blockers)


def test_candidate_to_active_with_refs_allowed():
    request = AgentLifecycleTransitionRequest(
        request_id="r5", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="battery passed",
        evidence_refs=("report.md",),
        test_battery_refs=("report.md",),
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is True
    assert decision.requires_evidence is True
    assert decision.requires_test_battery is True


# ---------------------------------------------------------------------------
# Transition: ACTIVE
# ---------------------------------------------------------------------------

def test_active_to_suspended_allowed():
    request = AgentLifecycleTransitionRequest(
        request_id="r6", agent_id="a1",
        old_state=AgentLifecycleState.ACTIVE,
        requested_state=AgentLifecycleState.SUSPENDED,
        reason_code=LifecycleReasonCode.SECURITY_INCIDENT,
        reason_text="Security incident detected",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is True
    assert decision.resulting_state == AgentLifecycleState.SUSPENDED


# ---------------------------------------------------------------------------
# Transition: SUSPENDED
# ---------------------------------------------------------------------------

def test_suspended_to_active_denied_directly():
    request = AgentLifecycleTransitionRequest(
        request_id="r7", agent_id="a1",
        old_state=AgentLifecycleState.SUSPENDED,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="reactivate directly",
        evidence_refs=("ref1",),
        test_battery_refs=("ref1",),
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert "forbidden_transition" in decision.blockers[0]


def test_suspended_to_restricted_allowed():
    request = AgentLifecycleTransitionRequest(
        request_id="r8", agent_id="a1",
        old_state=AgentLifecycleState.SUSPENDED,
        requested_state=AgentLifecycleState.RESTRICTED,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="Repair evidence provided",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is True


# ---------------------------------------------------------------------------
# Transition: RESTRICTED
# ---------------------------------------------------------------------------

def test_restricted_to_active_requires_repair_evidence():
    request = AgentLifecycleTransitionRequest(
        request_id="r9", agent_id="a1",
        old_state=AgentLifecycleState.RESTRICTED,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.CONSENT_GRANTED,
        reason_text="consent repaired",
        test_battery_refs=("ref1",),
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert any("evidence" in b.lower() or "repair" in b.lower() for b in decision.blockers)


# ---------------------------------------------------------------------------
# Terminal states
# ---------------------------------------------------------------------------

def test_deprecated_to_active_denied():
    request = AgentLifecycleTransitionRequest(
        request_id="r10", agent_id="a1",
        old_state=AgentLifecycleState.DEPRECATED,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="reactivate deprecated",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False


def test_retired_to_active_denied():
    request = AgentLifecycleTransitionRequest(
        request_id="r11", agent_id="a1",
        old_state=AgentLifecycleState.RETIRED,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="reactivate retired",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False


def test_revoked_is_terminal():
    request = AgentLifecycleTransitionRequest(
        request_id="r12", agent_id="a1",
        old_state=AgentLifecycleState.REVOKED,
        requested_state=AgentLifecycleState.CANDIDATE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="reactivate revoked",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert "revoked_is_terminal" in decision.blockers


# ---------------------------------------------------------------------------
# REVOKED from ACTIVE
# ---------------------------------------------------------------------------

def test_active_to_revoked_requires_valid_reason():
    request = AgentLifecycleTransitionRequest(
        request_id="r13", agent_id="a1",
        old_state=AgentLifecycleState.ACTIVE,
        requested_state=AgentLifecycleState.REVOKED,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="revoked",
    )
    decision = validate_agent_lifecycle_transition(request)
    assert decision.allowed is False
    assert any("valid_reason_code" in b for b in decision.blockers)


# ---------------------------------------------------------------------------
# Eligibility profiles
# ---------------------------------------------------------------------------

def test_draft_profile_allows_sandbox_not_production():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.DRAFT,
    )
    assert LifecycleLane.SANDBOX in profile.eligible_lanes
    assert LifecycleLane.PRODUCTION not in profile.eligible_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes


def test_candidate_profile_allows_evaluation_not_production():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.CANDIDATE,
    )
    assert LifecycleLane.EVALUATION in profile.eligible_lanes
    assert LifecycleLane.PRODUCTION not in profile.eligible_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes
    assert not profile.hard_blocked


def test_active_profile_has_required_gates():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.ACTIVE,
    )
    assert LifecycleLane.PRODUCTION in profile.eligible_lanes
    assert LifecycleLane.EXTERNAL_EFFECT in profile.eligible_lanes
    assert len(profile.required_gates) > 0
    assert "authority_scope" in profile.required_gates
    assert not profile.hard_blocked


def test_restricted_consent_expired_blocks_external_and_delegation():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1",
        lifecycle_state=AgentLifecycleState.RESTRICTED,
        restriction_reasons=(LifecycleReasonCode.CONSENT_EXPIRED,),
    )
    assert LifecycleLane.EXTERNAL_EFFECT in profile.blocked_lanes
    assert LifecycleLane.DELEGATION in profile.blocked_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes
    assert LifecycleLane.SANDBOX in profile.eligible_lanes
    assert not profile.audit_only


def test_restricted_security_incident_becomes_audit_only():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1",
        lifecycle_state=AgentLifecycleState.RESTRICTED,
        restriction_reasons=(LifecycleReasonCode.SECURITY_INCIDENT,),
    )
    assert profile.audit_only is True
    assert LifecycleLane.AUDIT_ONLY in profile.eligible_lanes
    assert LifecycleLane.GOVERNED_RUNTIME in profile.blocked_lanes
    assert LifecycleLane.EXTERNAL_EFFECT in profile.blocked_lanes
    assert profile.hard_blocked is True


def test_suspended_profile_is_audit_only():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.SUSPENDED,
    )
    assert profile.audit_only is True
    assert LifecycleLane.AUDIT_ONLY in profile.eligible_lanes
    assert LifecycleLane.GOVERNED_RUNTIME in profile.blocked_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes


def test_deprecated_profile_blocks_new_operations():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.DEPRECATED,
    )
    assert LifecycleLane.GOVERNED_RUNTIME in profile.blocked_lanes
    assert LifecycleLane.AUDIT_ONLY in profile.eligible_lanes
    assert LifecycleLane.LOCAL_READ_ONLY in profile.eligible_lanes


def test_retired_profile_is_audit_only():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.RETIRED,
    )
    assert profile.audit_only is True
    assert profile.hard_blocked is True
    assert LifecycleLane.SANDBOX in profile.blocked_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes


def test_revoked_profile_is_hard_blocked():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.REVOKED,
    )
    assert profile.audit_only is True
    assert profile.hard_blocked is True
    assert LifecycleLane.AUDIT_ONLY in profile.eligible_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes
    assert LifecycleLane.SANDBOX in profile.blocked_lanes


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------

def test_failed_critical_battery_recommends_suspended():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        battery_status="FAILED",
        highest_failed_severity="CRITICAL",
    )
    assert decision.resulting_state == AgentLifecycleState.SUSPENDED


def test_degraded_battery_recommends_restricted():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        battery_status="DEGRADED",
    )
    assert decision.resulting_state == AgentLifecycleState.RESTRICTED


def test_invalid_source_attestation_recommends_suspended():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        source_attestation_valid=False,
    )
    assert decision.resulting_state == AgentLifecycleState.SUSPENDED


def test_invalid_consent_recommends_restricted():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        consent_valid=False,
    )
    assert decision.resulting_state == AgentLifecycleState.RESTRICTED


def test_claim_boundary_violation_recommends_restricted():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        claim_boundary_valid=False,
    )
    assert decision.resulting_state == AgentLifecycleState.RESTRICTED


def test_candidate_with_passed_battery_recommends_active():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.CANDIDATE,
        battery_status="PASSED",
        source_attestation_valid=True,
        consent_valid=True,
        claim_boundary_valid=True,
    )
    assert decision.resulting_state == AgentLifecycleState.ACTIVE


def test_recommendation_does_not_apply_transition():
    decision = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        battery_status="FAILED",
        highest_failed_severity="CRITICAL",
    )
    assert decision.allowed is False
    assert decision.resulting_state == AgentLifecycleState.SUSPENDED


# ---------------------------------------------------------------------------
# Transition event creation
# ---------------------------------------------------------------------------

def test_create_event_when_allowed():
    request = AgentLifecycleTransitionRequest(
        request_id="r_e1", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="ready",
    )
    decision = AgentLifecycleTransitionDecision(
        decision_id="d1", request_id="r_e1", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        allowed=True,
        resulting_state=AgentLifecycleState.ACTIVE,
        reason="ok",
    )
    event = create_lifecycle_transition_event(request, decision)
    assert event is not None
    assert event.old_state == AgentLifecycleState.CANDIDATE
    assert event.new_state == AgentLifecycleState.ACTIVE


def test_create_event_when_denied_returns_none():
    request = AgentLifecycleTransitionRequest(
        request_id="r_e2", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="no",
    )
    decision = AgentLifecycleTransitionDecision(
        decision_id="d2", request_id="r_e2", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.ACTIVE,
        allowed=False,
        reason="blocked",
    )
    event = create_lifecycle_transition_event(request, decision)
    assert event is None


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_request_serialization_json():
    request = AgentLifecycleTransitionRequest(
        request_id="r1", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.CANDIDATE,
        reason_code=LifecycleReasonCode.READY_FOR_EVALUATION,
        reason_text="ready",
    )
    d = agent_lifecycle_transition_request_to_dict(request)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["old_state"] == "DRAFT"
    assert parsed["requested_state"] == "CANDIDATE"


def test_decision_serialization_json():
    decision = AgentLifecycleTransitionDecision(
        decision_id="d1", request_id="r1", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        allowed=True,
        resulting_state=AgentLifecycleState.ACTIVE,
        requires_evidence=True,
        blockers=("test",),
        reason="ok",
    )
    d = agent_lifecycle_transition_decision_to_dict(decision)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["allowed"] is True
    assert parsed["resulting_state"] == "ACTIVE"


def test_event_serialization_json():
    event = AgentLifecycleTransitionEvent(
        event_id="e1", request_id="r1", decision_id="d1",
        agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        new_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="done",
    )
    d = agent_lifecycle_transition_event_to_dict(event)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["old_state"] == "CANDIDATE"
    assert parsed["new_state"] == "ACTIVE"


def test_profile_serialization_json():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.CANDIDATE,
    )
    d = agent_lifecycle_eligibility_profile_to_dict(profile)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["lifecycle_state"] == "CANDIDATE"
    assert isinstance(parsed["eligible_lanes"], list)


def test_policy_serialization_json():
    policy = default_agent_lifecycle_policy()
    d = agent_lifecycle_policy_to_dict(policy)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert "DRAFT" in parsed["allowed_transitions"]
    assert "REVOKED" in parsed["terminal_states"]


# ---------------------------------------------------------------------------
# Human formatters
# ---------------------------------------------------------------------------

def test_decision_human_contains_blockers():
    decision = AgentLifecycleTransitionDecision(
        decision_id="d1", request_id="r1", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.ACTIVE,
        allowed=False,
        blockers=("forbidden",),
        reason="not allowed",
    )
    text = format_lifecycle_decision_human(decision)
    assert "BLOCKED" in text
    assert "forbidden" in text


def test_profile_human_contains_lanes():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.CANDIDATE,
    )
    text = format_lifecycle_profile_human(profile)
    assert "CANDIDATE" in text
    assert "SANDBOX" in text
    assert "PRODUCTION" in text

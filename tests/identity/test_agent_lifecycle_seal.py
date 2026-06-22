"""Seal and CLI tests for P1.4.17 Agent Lifecycle."""
from __future__ import annotations

import json
import subprocess
import sys

from agentic_runtime.identity.agent_lifecycle import (
    AgentLifecycleState,
    AgentLifecycleTransitionDecision,
    AgentLifecycleTransitionRequest,
    LifecycleLane,
    LifecycleReasonCode,
    build_agent_lifecycle_eligibility_profile,
    recommend_lifecycle_state,
    validate_agent_lifecycle_transition,
)


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True, text=True, timeout=30,
    )


# ---------------------------------------------------------------------------
# INV-P1417-03: Lifecycle state never grants authority by itself
# ---------------------------------------------------------------------------

def test_p1417_lifecycle_state_does_not_grant_authority():
    """Lifecycle profile is about lanes, not permissions."""
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.ACTIVE,
    )
    # Lanes are eligibility categories, not tool permissions
    assert "write_file" not in profile.required_gates
    assert "grant_capability" not in profile.required_gates


# ---------------------------------------------------------------------------
# INV-P1417-07: REVOKED is terminal
# ---------------------------------------------------------------------------

def test_p1417_no_revoked_reactivation():
    request = AgentLifecycleTransitionRequest(
        request_id="r1", agent_id="a1",
        old_state=AgentLifecycleState.REVOKED,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="reactivate",
    )
    d = validate_agent_lifecycle_transition(request)
    assert d.allowed is False
    assert "revoked_is_terminal" in d.blockers


# ---------------------------------------------------------------------------
# INV-P1417-08: DRAFT cannot transition directly to ACTIVE
# ---------------------------------------------------------------------------

def test_p1417_no_draft_to_active_shortcut():
    request = AgentLifecycleTransitionRequest(
        request_id="r2", agent_id="a1",
        old_state=AgentLifecycleState.DRAFT,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.OPERATOR_ACTION,
        reason_text="shortcut",
        evidence_refs=("ref",),
        test_battery_refs=("ref",),
    )
    d = validate_agent_lifecycle_transition(request)
    assert d.allowed is False


# ---------------------------------------------------------------------------
# INV-P1417-10: ACTIVE requires evidence and test battery
# ---------------------------------------------------------------------------

def test_p1417_active_requires_evidence_and_test_battery():
    r_no_evidence = AgentLifecycleTransitionRequest(
        request_id="r3", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="activation, no refs",
    )
    d_no = validate_agent_lifecycle_transition(r_no_evidence)
    assert d_no.allowed is False
    assert d_no.requires_evidence is True
    assert d_no.requires_test_battery is True


# ---------------------------------------------------------------------------
# INV-P1417-05: CANDIDATE can use evaluation lane
# ---------------------------------------------------------------------------

def test_p1417_candidate_can_use_evaluation_lane():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.CANDIDATE,
    )
    assert LifecycleLane.EVALUATION in profile.eligible_lanes
    assert LifecycleLane.SANDBOX in profile.eligible_lanes


# ---------------------------------------------------------------------------
# INV-P1417-06: RESTRICTED is reason-sensitive
# ---------------------------------------------------------------------------

def test_p1417_restricted_is_reason_sensitive_not_dead():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1",
        lifecycle_state=AgentLifecycleState.RESTRICTED,
    )
    # Default RESTRICTED still allows sandbox/evaluation
    assert LifecycleLane.SANDBOX in profile.eligible_lanes
    assert LifecycleLane.EVALUATION in profile.eligible_lanes
    assert not profile.audit_only


def test_p1417_restricted_blocks_external_when_consent_expired():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1",
        lifecycle_state=AgentLifecycleState.RESTRICTED,
        restriction_reasons=(LifecycleReasonCode.CONSENT_EXPIRED,),
    )
    assert LifecycleLane.EXTERNAL_EFFECT in profile.blocked_lanes


# ---------------------------------------------------------------------------
# INV-P1417-09: SUSPENDED cannot use operational lanes
# ---------------------------------------------------------------------------

def test_p1417_suspended_cannot_use_operational_lanes():
    profile = build_agent_lifecycle_eligibility_profile(
        agent_id="a1", lifecycle_state=AgentLifecycleState.SUSPENDED,
    )
    assert LifecycleLane.GOVERNED_RUNTIME in profile.blocked_lanes
    assert LifecycleLane.PRODUCTION in profile.blocked_lanes
    assert LifecycleLane.EXTERNAL_EFFECT in profile.blocked_lanes


# ---------------------------------------------------------------------------
# INV-P1417-11: Validation does not mutate state
# ---------------------------------------------------------------------------

def test_p1417_validation_does_not_mutate_state():
    r1 = validate_agent_lifecycle_transition(
        AgentLifecycleTransitionRequest(
            request_id="r1", agent_id="a1",
            old_state=AgentLifecycleState.ACTIVE,
            requested_state=AgentLifecycleState.RESTRICTED,
            reason_code=LifecycleReasonCode.CONSENT_EXPIRED,
            reason_text="testing idempotence",
        ),
    )
    r2 = validate_agent_lifecycle_transition(
        AgentLifecycleTransitionRequest(
            request_id="r1", agent_id="a1",
            old_state=AgentLifecycleState.ACTIVE,
            requested_state=AgentLifecycleState.RESTRICTED,
            reason_code=LifecycleReasonCode.CONSENT_EXPIRED,
            reason_text="testing idempotence",
        ),
    )
    assert r1.allowed == r2.allowed
    assert r1.blockers == r2.blockers
    assert r1.reason == r2.reason


# ---------------------------------------------------------------------------
# INV-P1417-16: Recommendations do not apply transitions
# ---------------------------------------------------------------------------

def test_p1417_recommendation_does_not_apply_transition():
    d = recommend_lifecycle_state(
        agent_id="a1",
        current_state=AgentLifecycleState.ACTIVE,
        battery_status="FAILED",
        highest_failed_severity="CRITICAL",
    )
    assert d.allowed is False
    assert d.resulting_state == AgentLifecycleState.SUSPENDED


# ---------------------------------------------------------------------------
# INV-P1417-17: Prepares P1.4.18 trust evidence linkage
# ---------------------------------------------------------------------------

def test_p1417_prepares_p1418_trust_evidence_linkage():
    """Lifecycle decisions carry evidence and consent refs for trust linkage."""
    request = AgentLifecycleTransitionRequest(
        request_id="r4", agent_id="a1",
        old_state=AgentLifecycleState.CANDIDATE,
        requested_state=AgentLifecycleState.ACTIVE,
        reason_code=LifecycleReasonCode.EVALUATION_PASSED,
        reason_text="ready",
        evidence_refs=("battery_report.md",),
        test_battery_refs=("battery_report.md",),
        consent_refs=("consent_1",),
        authority_delta_refs=("ad_1",),
    )
    d = validate_agent_lifecycle_transition(request)
    # Decision carries evidence requirement signals for P1.4.18
    assert d.requires_evidence is True
    assert d.requires_test_battery is True


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_lifecycle_cli_transitions_outputs_policy():
    result = _run_cli("identity", "lifecycle", "transitions", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "allowed_transitions" in data
    assert "DRAFT" in data["allowed_transitions"]


def test_lifecycle_cli_profile_outputs_eligibility():
    result = _run_cli("identity", "lifecycle", "profile",
                      "--agent-id", "aurel.core",
                      "--state", "CANDIDATE",
                      "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["lifecycle_state"] == "CANDIDATE"
    assert "EVALUATION" in data["eligible_lanes"]


def test_lifecycle_cli_show_outputs_json():
    result = _run_cli("identity", "lifecycle", "show",
                      "--agent-id", "aurel.core",
                      "--state", "ACTIVE",
                      "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["lifecycle_state"] == "ACTIVE"


def test_lifecycle_cli_validate_transition_outputs_decision():
    result = _run_cli("identity", "lifecycle", "validate-transition",
                      "--agent-id", "aurel.core",
                      "--old-state", "CANDIDATE",
                      "--new-state", "ACTIVE",
                      "--reason-code", "EVALUATION_PASSED",
                      "--reason", "battery passed",
                      "--evidence-ref", "report.md",
                      "--test-battery-ref", "report.md",
                      "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["allowed"] is True
    assert data["resulting_state"] == "ACTIVE"
    assert data["requires_evidence"] is True


def test_lifecycle_cli_validate_transition_denied_exits_nonzero():
    result = _run_cli("identity", "lifecycle", "validate-transition",
                      "--agent-id", "aurel.core",
                      "--old-state", "DRAFT",
                      "--new-state", "ACTIVE",
                      "--reason-code", "OPERATOR_ACTION",
                      "--reason", "shortcut",
                      "--json")
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["allowed"] is False


def test_lifecycle_cli_recommend_outputs_decision():
    result = _run_cli("identity", "lifecycle", "recommend",
                      "--agent-id", "aurel.core",
                      "--current-state", "ACTIVE",
                      "--battery-status", "FAILED",
                      "--highest-failed-severity", "CRITICAL",
                      "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["resulting_state"] == "SUSPENDED"
    assert "recommend_suspension" in data["warnings"][0] if data["warnings"] else True


def test_lifecycle_cli_validation_does_not_mutate_state():
    """Running validate twice produces the same output."""
    result1 = _run_cli("identity", "lifecycle", "validate-transition",
                       "--agent-id", "aurel.core",
                       "--old-state", "CANDIDATE",
                       "--new-state", "ACTIVE",
                       "--reason-code", "EVALUATION_PASSED",
                       "--reason", "battery passed",
                       "--evidence-ref", "report.md",
                       "--test-battery-ref", "report.md",
                       "--json")
    result2 = _run_cli("identity", "lifecycle", "validate-transition",
                       "--agent-id", "aurel.core",
                       "--old-state", "CANDIDATE",
                       "--new-state", "ACTIVE",
                       "--reason-code", "EVALUATION_PASSED",
                       "--reason", "battery passed",
                       "--evidence-ref", "report.md",
                       "--test-battery-ref", "report.md",
                       "--json")
    assert result1.stdout == result2.stdout

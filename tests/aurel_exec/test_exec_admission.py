"""P4-EXEC-A admission request / deterministic gate chain tests."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecAdmissionGateKind,
    ExecAdmissionState,
    ExecCustosStatus,
    ExecMissingRequirementKind,
    ExecPolicyStatus,
    ExecTraceStatus,
    ExecTruthLabel,
    ExecUnavailableSystem,
    ExecutionMode,
    build_dev_fixture_admission_request,
    decide_admission,
)


def test_dev_fixture_candidate_becomes_valid_admission_request():
    request = build_dev_fixture_admission_request()
    assert request.truth_label is ExecTruthLabel.DEV_FIXTURE
    assert request.source_p3_candidate_ref
    assert request.request_hash


def test_empty_request_id_is_rejected():
    with pytest.raises(AurelExecValidationError):
        build_dev_fixture_admission_request(request_id="  ")


def test_fully_prepared_fixture_is_admitted():
    decision = decide_admission(build_dev_fixture_admission_request())
    assert decision.state is ExecAdmissionState.ADMIT
    assert decision.admitted
    assert len(decision.gate_results) == 8
    assert not decision.missing_requirements


def test_admission_is_deterministic_and_closed_world():
    request = build_dev_fixture_admission_request()
    first = decide_admission(request)
    second = decide_admission(request)
    assert first == second
    assert first.decision_id == second.decision_id
    assert first.decision_hash == second.decision_hash


def test_missing_source_ref_rejects_deterministically():
    request = build_dev_fixture_admission_request(source_p3_candidate_ref="")
    decision = decide_admission(request)
    assert decision.state is ExecAdmissionState.REJECT
    assert decision.missing_requirements[0].kind is ExecMissingRequirementKind.SOURCE_REF
    # the first blocking gate locks the outcome: no later gates were evaluated
    assert len(decision.gate_results) == 1
    assert decision.gate_results[0].gate is ExecAdmissionGateKind.SOURCE_VALIDITY


def test_non_admittable_execution_mode_is_rejected():
    for mode in (ExecutionMode.UNAVAILABLE, ExecutionMode.ERROR):
        decision = decide_admission(
            build_dev_fixture_admission_request(requested_execution_mode=mode)
        )
        assert decision.state is ExecAdmissionState.REJECT


def test_p3_readiness_marker_gate_holds_non_ready_candidates():
    request = build_dev_fixture_admission_request(
        source_dispatchability_reason="BLOCKED_BY_DEPENDENCY"
    )
    decision = decide_admission(request)
    assert decision.state is ExecAdmissionState.HOLD
    assert (
        decision.missing_requirements[0].kind
        is ExecMissingRequirementKind.SOURCE_READINESS_MARKER
    )


def test_p3_readiness_does_not_imply_p4_admission():
    # A fully P3-ready candidate (READY_BUT_NO_P4) is still held by later gates.
    request = build_dev_fixture_admission_request(requested_sandbox_profile=None)
    assert request.source_dispatchability_reason == "READY_BUT_NO_P4"
    decision = decide_admission(request)
    assert decision.state is not ExecAdmissionState.ADMIT


def test_missing_authority_ref_requires_operator():
    decision = decide_admission(
        build_dev_fixture_admission_request(requested_authority_ref=None)
    )
    assert decision.state is ExecAdmissionState.REQUIRE_OPERATOR
    assert decision.missing_requirements[0].kind is ExecMissingRequirementKind.AUTHORITY_REF


def test_missing_sandbox_profile_holds_sandbox_required_mode():
    decision = decide_admission(
        build_dev_fixture_admission_request(requested_sandbox_profile=None)
    )
    assert decision.state is ExecAdmissionState.HOLD
    assert decision.missing_requirements[0].kind is ExecMissingRequirementKind.SANDBOX_PROFILE


def test_conversation_mode_does_not_require_sandbox_profile():
    decision = decide_admission(
        build_dev_fixture_admission_request(
            requested_execution_mode=ExecutionMode.CONVERSATION,
            requested_sandbox_profile=None,
        )
    )
    assert decision.state is ExecAdmissionState.ADMIT


def test_missing_budget_ref_holds():
    decision = decide_admission(
        build_dev_fixture_admission_request(requested_budget_ref=None)
    )
    assert decision.state is ExecAdmissionState.HOLD
    assert decision.missing_requirements[0].kind is ExecMissingRequirementKind.BUDGET_REF


def test_risky_mode_without_verifier_requires_verifier():
    decision = decide_admission(
        build_dev_fixture_admission_request(
            requested_execution_mode=ExecutionMode.TERMINAL,
            requested_verifier_ref=None,
        )
    )
    assert decision.state is ExecAdmissionState.REQUIRE_VERIFIER
    assert decision.missing_requirements[0].kind is ExecMissingRequirementKind.VERIFIER_REF


def test_missing_policy_context_requires_policy():
    decision = decide_admission(
        build_dev_fixture_admission_request(requested_policy_context_ref=None)
    )
    assert decision.state is ExecAdmissionState.REQUIRE_POLICY
    assert decision.policy_status is ExecPolicyStatus.ENFORCEMENT_UNAVAILABLE


def test_admission_does_not_claim_authorization_or_proof():
    decision = decide_admission(build_dev_fixture_admission_request())
    assert decision.state is ExecAdmissionState.ADMIT
    assert decision.custos_status is ExecCustosStatus.ENFORCEMENT_UNAVAILABLE
    assert decision.policy_status is ExecPolicyStatus.SHADOW_ONLY
    assert decision.trace_status is ExecTraceStatus.TRACE_VERIFICATION_UNAVAILABLE
    assert not hasattr(decision, "authorized")
    assert not hasattr(decision, "executed")


def test_admitted_decision_names_unavailable_systems_and_future_owners():
    decision = decide_admission(build_dev_fixture_admission_request())
    systems = {reason.system for reason in decision.unavailable_reasons}
    assert ExecUnavailableSystem.RUNTIME_SUBMIT in systems
    assert ExecUnavailableSystem.TRACE_VERIFICATION in systems
    assert ExecUnavailableSystem.CUSTOS_ENFORCEMENT in systems
    owners = {reason.future_pack_owner for reason in decision.unavailable_reasons}
    assert "P4-EXEC-B" in owners
    assert "P5 AurelTrace" in owners
    assert "P9 Custos" in owners


def test_non_admit_decisions_always_explain_themselves():
    for overrides in (
        {"source_p3_candidate_ref": ""},
        {"requested_authority_ref": None},
        {"requested_sandbox_profile": None},
        {"requested_budget_ref": None},
        {"requested_policy_context_ref": None},
    ):
        decision = decide_admission(build_dev_fixture_admission_request(**overrides))
        assert decision.state is not ExecAdmissionState.ADMIT
        assert decision.reason.strip()
        assert decision.missing_requirements


def test_gate_chain_has_no_side_effect_surface():
    decision = decide_admission(build_dev_fixture_admission_request())
    for name in ("submit", "dispatch", "execute", "enforce", "invoke"):
        assert not hasattr(decision, name)

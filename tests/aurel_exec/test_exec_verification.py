"""P4-EXEC-E verification tests — runtime success is not semantic success."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecutionMode,
    ExecutionVerificationDecision,
    ExecTruthLabel,
    VerificationStatus,
    VerifierHook,
    VerifierHookAvailability,
    build_execution_verification_request,
    build_no_model_verifier_call_proof,
    build_no_p5_proof_proof,
    build_no_p9_authority_proof,
    build_profile_only_verifier_hook,
    decide_verification,
    normalize_runtime_result,
)
from tests.aurel_exec._bridge_helpers import RecordingFakeRuntime, _FakeCard


class _Cmd:
    id = "cmd_x"


def _outcome(*, succeed=True):
    return normalize_runtime_result(
        RecordingFakeRuntime(succeed=succeed).submit(_Cmd(), _FakeCard()),
        attempt_id="exec-attempt-a",
        exec_job_id="exec-job-a",
        session_id="exec-session-a",
        tool_name="read_file",
        command_id="cmd_x",
    )


def _request(outcome):
    return build_execution_verification_request(
        outcome, requested_execution_mode=ExecutionMode.TOOL
    )


def test_runtime_success_is_not_automatically_verified_success():
    outcome = _outcome(succeed=True)
    assert outcome.success is True  # runtime succeeded...
    decision = decide_verification(_request(outcome), outcome)
    assert decision.verified is False  # ...but nothing is verified
    assert decision.verification_status is not VerificationStatus.PASSED


def test_verifier_unavailable_returns_honest_unavailable_decision():
    outcome = _outcome()
    request = _request(outcome)
    no_hook = decide_verification(request, outcome)
    assert no_hook.verification_status is VerificationStatus.UNAVAILABLE
    assert no_hook.verification_available is False
    assert no_hook.reason
    assert "verifier_hook" in no_hook.missing_evidence
    # hook exists but produced no evidence -> INCONCLUSIVE with operator review
    inconclusive = decide_verification(
        request, outcome, hook=build_profile_only_verifier_hook()
    )
    assert inconclusive.verification_status is VerificationStatus.INCONCLUSIVE
    assert inconclusive.verified is False
    assert inconclusive.requires_operator_review is True


def test_verified_true_requires_verifier_evidence():
    outcome = _outcome()
    request = _request(outcome)
    passed = decide_verification(
        request, outcome,
        hook=build_profile_only_verifier_hook(),
        evidence_refs=("evidence:contract-check-1",),
    )
    assert passed.verification_status is VerificationStatus.PASSED
    assert passed.verified is True
    assert passed.evidence_refs == ("evidence:contract-check-1",)
    # verified without evidence is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(passed, evidence_refs=())
    # PASSED without verified is unconstructible; verified requires PASSED
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(passed, verified=False)
    with pytest.raises(AurelExecValidationError):
        ExecutionVerificationDecision(
            verification_decision_id="exec-verify-dec-x",
            verification_request_id=request.verification_request_id,
            outcome_id=outcome.outcome_id,
            verified=True,
            verification_available=True,
            verification_status=VerificationStatus.INCONCLUSIVE,
            reason="verified without PASSED",
            truth_label=ExecTruthLabel.LIVE,
            evidence_refs=("evidence:x",),
        )


def test_failed_runtime_outcome_verifies_failed():
    outcome = _outcome(succeed=False)
    decision = decide_verification(
        _request(outcome), outcome, hook=build_profile_only_verifier_hook()
    )
    assert decision.verification_status is VerificationStatus.FAILED
    assert decision.verified is False
    assert "FileNotFoundError" in decision.reason
    assert decision.requires_operator_review is True


def test_decision_never_claims_p5_trace_verification():
    outcome = _outcome()
    decision = decide_verification(_request(outcome), outcome)
    assert decision.requires_p5_proof is True
    assert decision.trace_verified is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(decision, requires_p5_proof=False)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(decision, trace_verified=True)


def test_verifier_hook_is_structurally_side_effect_free():
    hook = build_profile_only_verifier_hook()
    assert hook.side_effect_free is True
    assert hook.availability_status is VerifierHookAvailability.PROFILE_ONLY
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(hook, side_effect_free=False)
    for boundary_field in (
        "calls_model",
        "calls_tools",
        "executes_terminal_or_code",
        "mutates_runtime_state",
        "writes_trace_proof",
    ):
        assert getattr(hook, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(hook, **{boundary_field: True})
    # no AVAILABLE member: a concrete evidence-producing verifier cannot be claimed
    assert "AVAILABLE" not in VerifierHookAvailability.__members__
    # unsupported mode -> honest UNAVAILABLE
    outcome = _outcome()
    request = _request(outcome)
    narrow_hook = dataclasses.replace(hook, supported_modes=("MODEL",))
    decision = decide_verification(request, outcome, hook=narrow_hook)
    assert decision.verification_status is VerificationStatus.UNAVAILABLE


def test_verification_boundary_proofs_are_fail_closed():
    for proof, boundary_field in (
        (build_no_model_verifier_call_proof(), "model_verifier_call_allowed"),
        (build_no_p5_proof_proof(), "p5_trace_verification_available"),
        (build_no_p9_authority_proof(), "p9_full_enforcement_available"),
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})

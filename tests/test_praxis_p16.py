"""P0.16 — Praxis Memory Seed tests."""

from __future__ import annotations

import pytest

from agentic_runtime import (
    MemoryFabric,
    MemoryTruthState,
    MemoryWriteRequest,
    PraxisCandidateGenerator,
    PraxisExperienceBuilder,
    PraxisMetabolism,
    PraxisMemoryCandidate,
    PraxisOutcomeStatus,
    PraxisProcedureCandidate,
    PraxisPromotionDecision,
    PraxisSkillCandidate,
    PromotionEvaluator,
    PromotionGate,
    ReflexEligibilityCheck,
    build_runtime,
    submit_memory_candidate_to_governance,
    bridge_skill_candidate_to_library,
)
from agentic_runtime.core_types import (
    ObservationEnvelope,
    PolicyVerdict,
    RiskLevel,
    VerifierResult,
)
from agentic_runtime.policy import PolicyDecision
from agentic_runtime.praxis import (
    MemoryCandidate,
    PraxisCandidateType,
    PraxisEvidence as PraxisEvidenceObj,
    PraxisEvidenceType as EvidenceKind,
    PraxisExperience,
    PraxisPromotionStatus,
    PraxisTrustLevel,
    PromotionDecision,
    PromotionDecisionType,
    PromotionSubjectType,
    ProcedureCandidate,
    SkillCandidate,
)
from agentic_runtime.repo_agent import CodeTaskReport, TestRunResult
from agentic_runtime.runtime import CommandResult
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_praxis"


def _fabric():
    trace = InMemoryTraceLedger(run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(trace)
    return fab, trace


def _success_result() -> CommandResult:
    return CommandResult(
        observation=ObservationEnvelope.make("cmd1", True, stdout="ok"),
        verifier=VerifierResult(passed=True, verifier="test", evidence={}, reason="ok", code="OK"),
        decision=PolicyDecision(verdict=PolicyVerdict.ALLOW, risk=RiskLevel.LOW, reasons=["ok"]),
        transition=None,
    )


def _failure_result() -> CommandResult:
    return CommandResult(
        observation=ObservationEnvelope.make("cmd2", False, stderr="error fail"),
        verifier=VerifierResult(passed=False, verifier="test", evidence={}, reason="fail", code="FAIL"),
        decision=PolicyDecision(verdict=PolicyVerdict.DENY, risk=RiskLevel.HIGH, reasons=["fail"]),
        transition=None,
    )


# --------------------------------------------------------------------------- #
# Contracts
# --------------------------------------------------------------------------- #
def test_praxis_contracts_construct():
    evidence = PraxisEvidenceObj.make(EvidenceKind.TRACE, "t1", "trace ref")
    exp = PraxisExperience(
        experience_id="e1",
        source_trace_id="t1",
        objective="obj",
        action_summary="act",
        outcome_status=PraxisOutcomeStatus.SUCCESS,
        evidence=[evidence],
    )
    mem = MemoryCandidate(
        candidate_id="m1",
        source_experience_id="e1",
        candidate_type=PraxisCandidateType.EPISODIC,
        content_summary="summary",
        evidence_refs=["t1"],
        trust_level=PraxisTrustLevel.MEDIUM,
        promotion_status=PraxisPromotionStatus.CANDIDATE,
    )
    proc = ProcedureCandidate(
        procedure_id="p1",
        source_candidate_ids=["m1"],
        trigger_pattern="when x",
        steps_summary="do y",
        expected_outcome="ok",
        required_tools=["read_file"],
        required_risk_level="low",
        evidence_refs=["t1"],
        status=PraxisPromotionStatus.PROPOSED,
    )
    skill = SkillCandidate(
        skill_id="s1",
        source_procedure_id="p1",
        name="skill",
        description="desc",
        preconditions=["pre"],
        bounded_steps=["step1"],
        required_capabilities=["read_file"],
        risk_class="low",
        evidence_refs=["t1"],
        status=PraxisPromotionStatus.PROPOSED,
    )
    decision = PromotionDecision(
        decision_id="d1",
        subject_id="m1",
        subject_type=PromotionSubjectType.MEMORY_CANDIDATE,
        decision=PromotionDecisionType.ACCEPT_CANDIDATE,
        reason="ok",
        evidence_refs=["t1"],
        decided_by="test",
    )
    reflex = ReflexEligibilityCheck(skill_id="s1", eligible=True, reason="bounded")
    assert exp.experience_id == "e1"
    assert mem.candidate_id == "m1"
    assert proc.procedure_id == "p1"
    assert skill.skill_id == "s1"
    assert decision.decision_id == "d1"
    assert reflex.must_still_pass_policy is True


# --------------------------------------------------------------------------- #
# Experience builder
# --------------------------------------------------------------------------- #
def test_success_run_creates_success_experience():
    exp = PraxisExperienceBuilder.from_command_result(
        trace_id=RUN, run_id=RUN, objective="read", action_summary="read file",
        result=_success_result(), tools_used=["read_file"],
    )
    assert exp.outcome_status == PraxisOutcomeStatus.SUCCESS


def test_failed_run_creates_failure_experience():
    exp = PraxisExperienceBuilder.from_command_result(
        trace_id=RUN, run_id=RUN, objective="read", action_summary="read file",
        result=_failure_result(),
    )
    assert exp.outcome_status == PraxisOutcomeStatus.FAILURE


def test_denied_repo_run_creates_deferred_experience():
    report = CodeTaskReport(task_id="t1", objective="plan only", plan_summary="p", final_status="planned")
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    assert exp.outcome_status == PraxisOutcomeStatus.DEFERRED


def test_secrets_redacted_in_summary():
    report = CodeTaskReport(
        task_id="t1", objective="api_key=sk-abcdefghijklmnopqrstuvwxyz12345",
        plan_summary="token: Bearer abc.def.ghi", final_status="failed",
        test_result=TestRunResult(command=["pytest"], exit_code=1),
    )
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    blob = exp.objective + " " + " ".join(e.summary for e in exp.evidence)
    assert "sk-" not in blob
    assert "[REDACTED]" in exp.objective or "[REDACTED]" in blob


def test_huge_output_summarized():
    report = CodeTaskReport(
        task_id="t1", objective="x", plan_summary="y", final_status="succeeded",
        test_result=TestRunResult(command=["pytest"], exit_code=0, stdout="a" * 2000),
    )
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    for e in exp.evidence:
        assert len(e.summary) <= 503


# --------------------------------------------------------------------------- #
# Candidate generation
# --------------------------------------------------------------------------- #
def test_successful_experience_creates_episodic_candidate():
    report = CodeTaskReport(
        task_id="t1", objective="fix bug", plan_summary="p", final_status="succeeded",
        test_result=TestRunResult(command=["pytest"], exit_code=0),
    )
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    cands, _ = PraxisCandidateGenerator.generate(exp)
    types = {c.candidate_type for c in cands}
    assert PraxisCandidateType.EPISODIC in types


def test_failed_experience_creates_diagnostic_candidate():
    report = CodeTaskReport(task_id="t1", objective="fix", plan_summary="p", final_status="failed")
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    cands, _ = PraxisCandidateGenerator.generate(exp)
    assert all(c.candidate_type == PraxisCandidateType.DIAGNOSTIC for c in cands)


def test_failed_execution_cannot_create_success_memory_candidate():
    report = CodeTaskReport(task_id="t1", objective="fix", plan_summary="p", final_status="failed")
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    cands, _ = PraxisCandidateGenerator.generate(exp)
    assert not any(c.candidate_type == PraxisCandidateType.EPISODIC for c in cands)


def test_candidate_without_trace_rejected():
    exp = PraxisExperience(
        experience_id="e1", source_trace_id="", objective="x", action_summary="y",
        outcome_status=PraxisOutcomeStatus.SUCCESS, evidence=[],
    )
    cands, decisions = PraxisCandidateGenerator.generate(exp)
    assert cands == []
    assert any(d.decision == PromotionDecisionType.REJECT_CANDIDATE for d in decisions)


def test_untrusted_stays_candidate_level():
    fab, _ = _fabric()
    report = CodeTaskReport(task_id="t1", objective="x", plan_summary="p", final_status="succeeded")
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=RUN)
    cands, _ = PraxisCandidateGenerator.generate(exp)
    for c in cands:
        dec = submit_memory_candidate_to_governance(fab, c, exp, run_id=RUN)
        assert dec.effective_truth_state == MemoryTruthState.CANDIDATE


# --------------------------------------------------------------------------- #
# Promotion gates
# --------------------------------------------------------------------------- #
def test_unverified_memory_cannot_become_procedure_without_evidence():
    mem = MemoryCandidate(
        candidate_id="m1", source_experience_id="e1",
        candidate_type=PraxisCandidateType.DIAGNOSTIC,
        content_summary="diag", evidence_refs=[], trust_level=PraxisTrustLevel.LOW,
        promotion_status=PraxisPromotionStatus.CANDIDATE,
    )
    proc, dec = PromotionEvaluator.evaluate_procedure([mem])
    assert proc is None
    assert dec.decision in {PromotionDecisionType.NEEDS_MORE_EVIDENCE, PromotionDecisionType.REJECT_CANDIDATE}


def test_procedure_candidate_requires_evidence_refs():
    proc = ProcedureCandidate(
        procedure_id="p1", source_candidate_ids=["m1"], trigger_pattern="t",
        steps_summary="s", expected_outcome="o", required_tools=[], required_risk_level="low",
        evidence_refs=[], status=PraxisPromotionStatus.PROPOSED,
    )
    skill, dec = PromotionEvaluator.evaluate_skill(proc)
    assert skill is None
    assert dec.decision == PromotionDecisionType.NEEDS_MORE_EVIDENCE


def test_skill_candidate_requires_bounded_steps():
    proc = ProcedureCandidate(
        procedure_id="p1", source_candidate_ids=["m1"], trigger_pattern="",
        steps_summary="", expected_outcome="o", required_tools=[], required_risk_level="low",
        evidence_refs=["t1"], status=PraxisPromotionStatus.PROPOSED,
    )
    skill, dec = PromotionEvaluator.evaluate_skill(proc)
    assert skill is not None
    assert skill.bounded_steps


def test_reflex_eligibility_does_not_bypass_governance():
    skill = SkillCandidate(
        skill_id="s1", source_procedure_id="p1", name="n", description="d",
        preconditions=["when"], bounded_steps=["step"], required_capabilities=["read"],
        risk_class="low", evidence_refs=["t1"], status=PraxisPromotionStatus.PROPOSED,
    )
    check = PromotionEvaluator.check_reflex_eligibility(skill)
    assert check.must_still_pass_policy is True
    assert check.must_still_pass_sandbox is True
    assert check.must_still_pass_verifier is True
    assert check.must_still_trace is True


def test_high_risk_skill_not_reflex_eligible():
    skill = SkillCandidate(
        skill_id="s1", source_procedure_id="p1", name="n", description="d",
        preconditions=["when"], bounded_steps=["step"], required_capabilities=["run_shell"],
        risk_class="high", evidence_refs=["t1"], status=PraxisPromotionStatus.PROPOSED,
    )
    check = PromotionEvaluator.check_reflex_eligibility(skill)
    assert not check.eligible


def test_promotion_gate_alias():
    assert PromotionGate is PromotionEvaluator


# --------------------------------------------------------------------------- #
# Repo agent integration
# --------------------------------------------------------------------------- #
def test_completed_repo_task_produces_praxis_report():
    metabolism = PraxisMetabolism()
    report = CodeTaskReport(
        task_id="t1", objective="task", plan_summary="p", final_status="succeeded",
        test_result=TestRunResult(command=["pytest"], exit_code=0),
        files_changed=["a.py"],
    )
    pr = metabolism.process_repo_report(report, run_id=RUN)
    assert pr.experience_id
    assert pr.memory_candidates_created


def test_failed_repo_task_produces_diagnostic():
    metabolism = PraxisMetabolism()
    report = CodeTaskReport(task_id="t1", objective="task", plan_summary="p", final_status="failed")
    pr = metabolism.process_repo_report(report, run_id=RUN)
    diag = [c for c in metabolism.memory_candidates if c.candidate_type == PraxisCandidateType.DIAGNOSTIC]
    assert diag
    assert not pr.skill_candidates_created


# --------------------------------------------------------------------------- #
# Memory governance integration
# --------------------------------------------------------------------------- #
def test_candidates_submit_through_governance():
    fab, trace = _fabric()
    metabolism = PraxisMetabolism()
    report = CodeTaskReport(
        task_id="t1", objective="task", plan_summary="p", final_status="succeeded",
        test_result=TestRunResult(command=["pytest"], exit_code=0),
    )
    metabolism.process_repo_report(report, trace=trace, run_id=RUN, memory_fabric=fab)
    assert fab.stats()["L3"] >= 1 or len(list(trace.replay())) > 0


def test_direct_verified_write_rejected():
    fab, _ = _fabric()
    dec = fab.request_write(MemoryWriteRequest(
        content="canon fact",
        proposed_truth_state=MemoryTruthState.VERIFIED,
        writer_kind="agent",
        source_run_id=RUN,
    ))
    assert not dec.allowed


def test_failed_candidate_cannot_submit_success_memory():
    fab, _ = _fabric()
    exp = PraxisExperience(
        experience_id="e1", source_trace_id=RUN, objective="x", action_summary="y",
        outcome_status=PraxisOutcomeStatus.FAILURE,
        evidence=[PraxisEvidenceObj.make(EvidenceKind.TRACE, RUN, "trace")],
    )
    cand = MemoryCandidate(
        candidate_id="m1", source_experience_id="e1",
        candidate_type=PraxisCandidateType.EPISODIC,
        content_summary="should fail", evidence_refs=[RUN],
        trust_level=PraxisTrustLevel.LOW, promotion_status=PraxisPromotionStatus.CANDIDATE,
    )
    with pytest.raises(ValueError):
        submit_memory_candidate_to_governance(fab, cand, exp, run_id=RUN)


def test_bridge_skill_does_not_register():
    skill = SkillCandidate(
        skill_id="s1", source_procedure_id="p1", name="n", description="d",
        preconditions=["p"], bounded_steps=["s"], required_capabilities=["read"],
        risk_class="low", evidence_refs=["t1"], status=PraxisPromotionStatus.PROPOSED,
    )
    proposal = bridge_skill_candidate_to_library(skill)
    assert proposal["proposal_only"] is True
    assert proposal["status"] == "candidate_not_registered"


def test_trace_records_praxis_events():
    trace = InMemoryTraceLedger(run_id=RUN)
    metabolism = PraxisMetabolism()
    report = CodeTaskReport(task_id="t1", objective="t", plan_summary="p", final_status="succeeded",
                            test_result=TestRunResult(command=["pytest"], exit_code=0))
    metabolism.process_repo_report(report, trace=trace, run_id=RUN)
    kinds = [r.get("kind") for r in trace.replay()]
    assert "praxis_event" in kinds

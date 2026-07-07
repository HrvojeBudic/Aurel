"""
Praxis memory metabolism seed (P0.16).

Captures execution experience, links trace/evidence/approval/test outcomes, and
produces governed memory/procedure/skill *candidates* — never auto-promoted truth.

Core distinctions:
- Trace is not memory.
- Memory candidate is not verified truth.
- Procedure candidate is not a skill.
- Skill is not a reflex.
- Reflex must never bypass runtime governance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from .core_types import (
    MemoryTruthState,
    new_id,
    now,
    PraxisEventRecord,
)
from .memory_governance import MemoryWriteRequest

if TYPE_CHECKING:
    from .memory import MemoryFabric
    from .repo_agent import CodeTaskReport
    from .runtime import CommandResult
    from .trace import TraceLedger

_SECRET_PATTERNS = [
  re.compile(r"(?i)(api[_-]?key|secret|token|password|credential)\s*[:=]\s*\S+"),
  re.compile(r"sk-[a-zA-Z0-9]{20,}"),
  re.compile(r"Bearer\s+[A-Za-z0-9._\-]+"),
]
_MAX_SUMMARY = 500


def _redact(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out[:_MAX_SUMMARY]


def _summarize(text: str, limit: int = _MAX_SUMMARY) -> str:
    cleaned = _redact(str(text or ""))
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


class PraxisOutcomeStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"
    DEFERRED = "deferred"


class PraxisCandidateType(str, Enum):
    EPISODIC = "episodic"
    DIAGNOSTIC = "diagnostic"
    PROCEDURAL_HINT = "procedural_hint"
    PREFERENCE = "preference"
    OPERATIONAL_PATTERN = "operational_pattern"


class PraxisTrustLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PraxisPromotionStatus(str, Enum):
    CANDIDATE = "candidate"
    PROPOSED = "proposed"
    REJECTED = "rejected"
    NEEDS_EVIDENCE = "needs_more_evidence"


class PraxisEvidenceType(str, Enum):
    TRACE = "trace"
    TEST_RESULT = "test_result"
    VERIFIER_RESULT = "verifier_result"
    APPROVAL_RECEIPT = "approval_receipt"
    REPORT = "report"
    DIFF_SUMMARY = "diff_summary"


class PromotionSubjectType(str, Enum):
    MEMORY_CANDIDATE = "memory_candidate"
    PROCEDURE_CANDIDATE = "procedure_candidate"
    SKILL_CANDIDATE = "skill_candidate"


class PromotionDecisionType(str, Enum):
    ACCEPT_CANDIDATE = "accept_candidate"
    REJECT_CANDIDATE = "reject_candidate"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    PROMOTE_TO_PROCEDURE = "promote_to_procedure_candidate"
    PROMOTE_TO_SKILL = "promote_to_skill_candidate"


@dataclass
class PraxisEvidence:
    evidence_id: str
    evidence_type: PraxisEvidenceType
    reference_id: str
    summary: str
    confidence: float
    created_at: float = field(default_factory=now)

    @staticmethod
    def make(
        evidence_type: PraxisEvidenceType,
        reference_id: str,
        summary: str,
        confidence: float = 0.5,
    ) -> "PraxisEvidence":
        return PraxisEvidence(
            evidence_id=new_id("evidence"),
            evidence_type=evidence_type,
            reference_id=reference_id,
            summary=_summarize(summary),
            confidence=max(0.0, min(1.0, confidence)),
        )


@dataclass
class PraxisExperience:
    experience_id: str
    source_trace_id: str
    objective: str
    action_summary: str
    outcome_status: PraxisOutcomeStatus
    tools_used: list[str] = field(default_factory=list)
    task_id: str = ""
    command_id: str = ""
    files_changed: list[str] = field(default_factory=list)
    tests_run: list[str] = field(default_factory=list)
    approval_receipts: list[str] = field(default_factory=list)
    verifier_results: list[str] = field(default_factory=list)
    sandbox_profile: str = ""
    evidence: list[PraxisEvidence] = field(default_factory=list)
    created_at: float = field(default_factory=now)


@dataclass
class MemoryCandidate:
    candidate_id: str
    source_experience_id: str
    candidate_type: PraxisCandidateType
    content_summary: str
    evidence_refs: list[str]
    trust_level: PraxisTrustLevel
    promotion_status: PraxisPromotionStatus
    created_at: float = field(default_factory=now)


@dataclass
class ProcedureCandidate:
    procedure_id: str
    source_candidate_ids: list[str]
    trigger_pattern: str
    steps_summary: str
    expected_outcome: str
    required_tools: list[str]
    required_risk_level: str
    evidence_refs: list[str]
    status: PraxisPromotionStatus
    created_at: float = field(default_factory=now)


@dataclass
class SkillCandidate:
    """Praxis skill candidate — not an active runtime skill or reflex."""
    skill_id: str
    source_procedure_id: str
    name: str
    description: str
    preconditions: list[str]
    bounded_steps: list[str]
    required_capabilities: list[str]
    risk_class: str
    evidence_refs: list[str]
    status: PraxisPromotionStatus
    created_at: float = field(default_factory=now)


@dataclass
class PromotionDecision:
    decision_id: str
    subject_id: str
    subject_type: PromotionSubjectType
    decision: PromotionDecisionType
    reason: str
    evidence_refs: list[str]
    decided_by: str
    created_at: float = field(default_factory=now)


@dataclass
class ReflexEligibilityCheck:
    skill_id: str
    eligible: bool
    reason: str
    must_still_pass_policy: bool = True
    must_still_pass_sandbox: bool = True
    must_still_pass_verifier: bool = True
    must_still_trace: bool = True


@dataclass
class PromotionReport:
    decisions: list[PromotionDecision] = field(default_factory=list)
    procedure_candidates: list[ProcedureCandidate] = field(default_factory=list)
    skill_candidates: list[SkillCandidate] = field(default_factory=list)
    reflex_checks: list[ReflexEligibilityCheck] = field(default_factory=list)


@dataclass
class PraxisReport:
    experience_id: str
    memory_candidates_created: list[str] = field(default_factory=list)
    procedure_candidates_created: list[str] = field(default_factory=list)
    skill_candidates_created: list[str] = field(default_factory=list)
    promotion_decisions: list[str] = field(default_factory=list)
    reflex_eligibility_checks: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class PraxisExperienceBuilder:
    """Build PraxisExperience from runtime/repo/approval/test/verifier sources."""

    @staticmethod
    def from_command_result(
        *,
        trace_id: str,
        run_id: str,
        objective: str,
        action_summary: str,
        result: "CommandResult",
        tools_used: Optional[list[str]] = None,
        command_id: str = "",
    ) -> PraxisExperience:
        outcome = PraxisExperienceBuilder._outcome_from_command(result)
        evidence: list[PraxisEvidence] = [
            PraxisEvidence.make(PraxisEvidenceType.TRACE, trace_id or run_id, f"trace:{run_id}")
        ]
        if result.approval_receipt:
            rid = getattr(result.approval_receipt, "receipt_id", "") or new_id("approval")
            evidence.append(
                PraxisEvidence.make(
                    PraxisEvidenceType.APPROVAL_RECEIPT,
                    rid,
                    _summarize(getattr(result.approval_receipt, "reason", "approval")),
                    0.8,
                )
            )
        if result.verifier and getattr(result.verifier, "passed", None) is not None:
            evidence.append(
                PraxisEvidence.make(
                    PraxisEvidenceType.VERIFIER_RESULT,
                    run_id,
                    _summarize(str(result.verifier)),
                    0.9 if result.verifier.passed else 0.3,
                )
            )
        approval_ids = []
        if result.approval_receipt:
            approval_ids.append(getattr(result.approval_receipt, "receipt_id", rid))
        verifier_ids = [run_id] if result.verifier else []
        return PraxisExperience(
            experience_id=new_id("experience"),
            source_trace_id=trace_id or run_id,
            command_id=command_id,
            objective=_summarize(objective),
            action_summary=_summarize(action_summary),
            outcome_status=outcome,
            tools_used=list(tools_used or []),
            approval_receipts=approval_ids,
            verifier_results=verifier_ids,
            evidence=evidence,
        )

    @staticmethod
    def from_repo_report(
        report: "CodeTaskReport",
        *,
        trace_run_id: str = "",
    ) -> PraxisExperience:
        trace_id = trace_run_id or report.task_id
        outcome = PraxisExperienceBuilder._outcome_from_repo_status(report.final_status)
        evidence: list[PraxisEvidence] = [
            PraxisEvidence.make(PraxisEvidenceType.TRACE, trace_id, f"repo task trace:{trace_id}")
        ]
        if report.test_result:
            tr = report.test_result
            evidence.append(
                PraxisEvidence.make(
                    PraxisEvidenceType.TEST_RESULT,
                    report.task_id,
                    _summarize(f"exit={tr.exit_code} passed={tr.passed}"),
                    0.85 if tr.passed else 0.4,
                )
            )
        if report.files_changed:
            evidence.append(
                PraxisEvidence.make(
                    PraxisEvidenceType.DIFF_SUMMARY,
                    report.task_id,
                    _summarize(", ".join(report.files_changed[:10])),
                    0.7,
                )
            )
        evidence.append(
            PraxisEvidence.make(
                PraxisEvidenceType.REPORT,
                report.task_id,
                _summarize(f"{report.final_status}: {report.objective}"),
                0.75,
            )
        )
        approval_ids = [s.get("receipt_id", "") for s in (report.approval_summaries or []) if s.get("receipt_id")]
        tests: list[str] = []
        if report.test_result:
            tr = report.test_result
            tests = [f"{' '.join(tr.command)}: {'passed' if tr.passed else 'failed'}"]
        return PraxisExperience(
            experience_id=new_id("experience"),
            source_trace_id=trace_id,
            task_id=report.task_id,
            objective=_summarize(report.objective),
            action_summary=_summarize(
                f"files={len(report.files_changed)} repairs={report.repair_attempts} status={report.final_status}"
            ),
            outcome_status=outcome,
            files_changed=list(report.files_changed or []),
            tests_run=tests,
            approval_receipts=[a for a in approval_ids if a],
            evidence=evidence,
            sandbox_profile=report.sandbox_profile or "",
        )

    @staticmethod
    def _outcome_from_command(result: "CommandResult") -> PraxisOutcomeStatus:
        if result.approval_decision and getattr(result.approval_decision, "outcome", None):
            ao = str(result.approval_decision.outcome).lower()
            if "deny" in ao or ao == "rejected":
                return PraxisOutcomeStatus.DENIED
            if "defer" in ao:
                return PraxisOutcomeStatus.DEFERRED
        if not result.ok:
            return PraxisOutcomeStatus.FAILURE
        if result.verifier and result.verifier.passed:
            return PraxisOutcomeStatus.SUCCESS
        obs = str(getattr(result, "observation", "") or "")
        if "error" in obs.lower() or "fail" in obs.lower():
            return PraxisOutcomeStatus.FAILURE
        return PraxisOutcomeStatus.PARTIAL

    @staticmethod
    def _outcome_from_repo_status(status: str) -> PraxisOutcomeStatus:
        s = (status or "").lower()
        if s in ("succeeded", "success"):
            return PraxisOutcomeStatus.SUCCESS
        if s in ("failed", "patch_failed", "failure"):
            return PraxisOutcomeStatus.FAILURE
        if s in ("dry_run", "planned"):
            return PraxisOutcomeStatus.DEFERRED
        if "denied" in s:
            return PraxisOutcomeStatus.DENIED
        return PraxisOutcomeStatus.PARTIAL


class PraxisCandidateGenerator:
    """Generate memory candidates from experiences — conservative, evidence-backed."""

    @staticmethod
    def generate(experience: PraxisExperience) -> tuple[list[MemoryCandidate], list[PromotionDecision]]:
        decisions: list[PromotionDecision] = []
        if not experience.source_trace_id and not experience.evidence:
            decisions.append(
                PromotionDecision(
                    decision_id=new_id("promo"),
                    subject_id=experience.experience_id,
                    subject_type=PromotionSubjectType.MEMORY_CANDIDATE,
                    decision=PromotionDecisionType.REJECT_CANDIDATE,
                    reason="no trace or evidence references",
                    evidence_refs=[],
                    decided_by="praxis_generator",
                )
            )
            return [], decisions

        evidence_refs = [e.evidence_id for e in experience.evidence]
        if experience.source_trace_id and experience.source_trace_id not in evidence_refs:
            evidence_refs.insert(0, experience.source_trace_id)

        trust = PraxisCandidateGenerator._trust_level(experience)
        candidates: list[MemoryCandidate] = []

        if experience.outcome_status == PraxisOutcomeStatus.SUCCESS:
            candidates.append(
                MemoryCandidate(
                    candidate_id=new_id("mem_cand"),
                    source_experience_id=experience.experience_id,
                    candidate_type=PraxisCandidateType.EPISODIC,
                    content_summary=_summarize(
                        f"Success: {experience.objective} — {experience.action_summary}"
                    ),
                    evidence_refs=evidence_refs,
                    trust_level=trust,
                    promotion_status=PraxisPromotionStatus.CANDIDATE,
                )
            )
            if PraxisCandidateGenerator._has_structured_evidence(experience):
                candidates.append(
                    MemoryCandidate(
                        candidate_id=new_id("mem_cand"),
                        source_experience_id=experience.experience_id,
                        candidate_type=PraxisCandidateType.PROCEDURAL_HINT,
                        content_summary=_summarize(
                            f"Procedural hint from success: {experience.objective}"
                        ),
                        evidence_refs=evidence_refs,
                        trust_level=trust,
                        promotion_status=PraxisPromotionStatus.CANDIDATE,
                    )
                )
        elif experience.outcome_status in (
            PraxisOutcomeStatus.FAILURE,
            PraxisOutcomeStatus.DENIED,
            PraxisOutcomeStatus.DEFERRED,
        ):
            candidates.append(
                MemoryCandidate(
                    candidate_id=new_id("mem_cand"),
                    source_experience_id=experience.experience_id,
                    candidate_type=PraxisCandidateType.DIAGNOSTIC,
                    content_summary=_summarize(
                        f"Diagnostic ({experience.outcome_status.value}): {experience.objective}"
                    ),
                    evidence_refs=evidence_refs,
                    trust_level=PraxisTrustLevel.LOW if trust == PraxisTrustLevel.LOW else PraxisTrustLevel.MEDIUM,
                    promotion_status=PraxisPromotionStatus.CANDIDATE,
                )
            )
        elif experience.outcome_status == PraxisOutcomeStatus.PARTIAL:
            candidates.append(
                MemoryCandidate(
                    candidate_id=new_id("mem_cand"),
                    source_experience_id=experience.experience_id,
                    candidate_type=PraxisCandidateType.DIAGNOSTIC,
                    content_summary=_summarize(f"Partial: {experience.objective}"),
                    evidence_refs=evidence_refs,
                    trust_level=PraxisTrustLevel.MEDIUM,
                    promotion_status=PraxisPromotionStatus.CANDIDATE,
                )
            )

        for c in candidates:
            if not c.evidence_refs:
                decisions.append(
                    PromotionDecision(
                        decision_id=new_id("promo"),
                        subject_id=c.candidate_id,
                        subject_type=PromotionSubjectType.MEMORY_CANDIDATE,
                        decision=PromotionDecisionType.REJECT_CANDIDATE,
                        reason="candidate lacks evidence refs",
                        evidence_refs=[],
                        decided_by="praxis_generator",
                    )
                )
            else:
                decisions.append(
                    PromotionDecision(
                        decision_id=new_id("promo"),
                        subject_id=c.candidate_id,
                        subject_type=PromotionSubjectType.MEMORY_CANDIDATE,
                        decision=PromotionDecisionType.ACCEPT_CANDIDATE,
                        reason="trace-backed candidate",
                        evidence_refs=c.evidence_refs,
                        decided_by="praxis_generator",
                    )
                )

        # Filter rejected
        rejected_ids = {
            d.subject_id
            for d in decisions
            if d.decision == PromotionDecisionType.REJECT_CANDIDATE
        }
        candidates = [c for c in candidates if c.candidate_id not in rejected_ids]
        return candidates, decisions

    @staticmethod
    def _trust_level(experience: PraxisExperience) -> PraxisTrustLevel:
        if not experience.evidence:
            return PraxisTrustLevel.LOW
        if len(experience.evidence) >= 3:
            return PraxisTrustLevel.MEDIUM
        has_test = any(e.evidence_type == PraxisEvidenceType.TEST_RESULT for e in experience.evidence)
        has_verifier = any(e.evidence_type == PraxisEvidenceType.VERIFIER_RESULT for e in experience.evidence)
        if has_test and has_verifier:
            return PraxisTrustLevel.HIGH
        if has_test or has_verifier:
            return PraxisTrustLevel.MEDIUM
        return PraxisTrustLevel.LOW

    @staticmethod
    def _has_structured_evidence(experience: PraxisExperience) -> bool:
        types = {e.evidence_type for e in experience.evidence}
        return bool(
            types & {
                PraxisEvidenceType.TEST_RESULT,
                PraxisEvidenceType.VERIFIER_RESULT,
                PraxisEvidenceType.REPORT,
            }
        )


class PromotionEvaluator:
    """Conservative promotion gates — no auto canon/verified promotion."""

    @staticmethod
    def evaluate_procedure(
        memory_candidates: list[MemoryCandidate],
        experience: Optional[PraxisExperience] = None,
    ) -> tuple[Optional[ProcedureCandidate], PromotionDecision]:
        accepted = [
            c
            for c in memory_candidates
            if c.promotion_status != PraxisPromotionStatus.REJECTED and c.evidence_refs
        ]
        if not accepted:
            return None, PromotionDecision(
                decision_id=new_id("promo"),
                subject_id="procedure",
                subject_type=PromotionSubjectType.PROCEDURE_CANDIDATE,
                decision=PromotionDecisionType.NEEDS_MORE_EVIDENCE,
                reason="no memory candidates with evidence",
                evidence_refs=[],
                decided_by="promotion_gate",
            )
        hint = next(
            (c for c in accepted if c.candidate_type == PraxisCandidateType.PROCEDURAL_HINT),
            None,
        )
        episodic = next(
            (c for c in accepted if c.candidate_type == PraxisCandidateType.EPISODIC),
            accepted[0],
        )
        if not hint and episodic.candidate_type == PraxisCandidateType.DIAGNOSTIC:
            return None, PromotionDecision(
                decision_id=new_id("promo"),
                subject_id=episodic.candidate_id,
                subject_type=PromotionSubjectType.PROCEDURE_CANDIDATE,
                decision=PromotionDecisionType.REJECT_CANDIDATE,
                reason="diagnostic-only memory cannot become procedure",
                evidence_refs=episodic.evidence_refs,
                decided_by="promotion_gate",
            )
        source_ids = [c.candidate_id for c in accepted[:3]]
        evidence_refs: list[str] = []
        for c in accepted:
            evidence_refs.extend(c.evidence_refs)
        evidence_refs = list(dict.fromkeys(evidence_refs))
        if not evidence_refs:
            return None, PromotionDecision(
                decision_id=new_id("promo"),
                subject_id="procedure",
                subject_type=PromotionSubjectType.PROCEDURE_CANDIDATE,
                decision=PromotionDecisionType.NEEDS_MORE_EVIDENCE,
                reason="procedure requires evidence refs",
                evidence_refs=[],
                decided_by="promotion_gate",
            )
        obj = experience.objective if experience else episodic.content_summary
        proc = ProcedureCandidate(
            procedure_id=new_id("proc_cand"),
            source_candidate_ids=source_ids,
            trigger_pattern=_summarize(obj, 120),
            steps_summary=_summarize(episodic.content_summary),
            expected_outcome="successful completion with tests passing",
            required_tools=experience.tools_used if experience else [],
            required_risk_level="medium",
            evidence_refs=evidence_refs,
            status=PraxisPromotionStatus.PROPOSED,
        )
        return proc, PromotionDecision(
            decision_id=new_id("promo"),
            subject_id=proc.procedure_id,
            subject_type=PromotionSubjectType.PROCEDURE_CANDIDATE,
            decision=PromotionDecisionType.PROMOTE_TO_PROCEDURE,
            reason="memory candidates with evidence support procedure proposal",
            evidence_refs=evidence_refs,
            decided_by="promotion_gate",
        )

    @staticmethod
    def evaluate_skill(procedure: ProcedureCandidate) -> tuple[Optional[SkillCandidate], PromotionDecision]:
        if not procedure.evidence_refs:
            return None, PromotionDecision(
                decision_id=new_id("promo"),
                subject_id=procedure.procedure_id,
                subject_type=PromotionSubjectType.SKILL_CANDIDATE,
                decision=PromotionDecisionType.NEEDS_MORE_EVIDENCE,
                reason="procedure lacks evidence refs",
                evidence_refs=[],
                decided_by="promotion_gate",
            )
        steps = [_summarize(procedure.steps_summary)]
        if procedure.trigger_pattern:
            steps.insert(0, f"When: {procedure.trigger_pattern}")
        if len(steps) < 1:
            return None, PromotionDecision(
                decision_id=new_id("promo"),
                subject_id=procedure.procedure_id,
                subject_type=PromotionSubjectType.SKILL_CANDIDATE,
                decision=PromotionDecisionType.REJECT_CANDIDATE,
                reason="unbounded procedure cannot become skill",
                evidence_refs=procedure.evidence_refs,
                decided_by="promotion_gate",
            )
        skill = SkillCandidate(
            skill_id=new_id("skill_cand"),
            source_procedure_id=procedure.procedure_id,
            name=_summarize(procedure.trigger_pattern, 80) or "praxis_skill",
            description=_summarize(procedure.steps_summary),
            preconditions=[f"trigger:{procedure.trigger_pattern}"] if procedure.trigger_pattern else [],
            bounded_steps=steps,
            required_capabilities=list(procedure.required_tools),
            risk_class=procedure.required_risk_level,
            evidence_refs=procedure.evidence_refs,
            status=PraxisPromotionStatus.PROPOSED,
        )
        return skill, PromotionDecision(
            decision_id=new_id("promo"),
            subject_id=skill.skill_id,
            subject_type=PromotionSubjectType.SKILL_CANDIDATE,
            decision=PromotionDecisionType.PROMOTE_TO_SKILL,
            reason="bounded procedure with evidence",
            evidence_refs=procedure.evidence_refs,
            decided_by="promotion_gate",
        )

    @staticmethod
    def check_reflex_eligibility(skill: SkillCandidate) -> ReflexEligibilityCheck:
        if not skill.bounded_steps or not skill.preconditions:
            return ReflexEligibilityCheck(
                skill_id=skill.skill_id,
                eligible=False,
                reason="skill lacks bounded steps or explicit preconditions",
            )
        risk = (skill.risk_class or "").lower()
        if risk in ("high", "critical", "r0", "r1"):
            return ReflexEligibilityCheck(
                skill_id=skill.skill_id,
                eligible=False,
                reason="high-risk skill requires explicit approval path; not reflex-eligible",
            )
        if not skill.evidence_refs:
            return ReflexEligibilityCheck(
                skill_id=skill.skill_id,
                eligible=False,
                reason="no evidence refs",
            )
        return ReflexEligibilityCheck(
            skill_id=skill.skill_id,
            eligible=True,
            reason="bounded low/medium risk skill; runtime governance still required",
        )


def submit_memory_candidate_to_governance(
    fabric: "MemoryFabric",
    candidate: MemoryCandidate,
    experience: PraxisExperience,
    *,
    run_id: str,
) -> Any:
    """Adapter: submit Praxis memory candidate through existing memory governance."""
    run_succeeded = experience.outcome_status == PraxisOutcomeStatus.SUCCESS
    if candidate.candidate_type == PraxisCandidateType.DIAGNOSTIC:
        run_succeeded = False
    if candidate.candidate_type in (
        PraxisCandidateType.EPISODIC,
        PraxisCandidateType.OPERATIONAL_PATTERN,
        PraxisCandidateType.PROCEDURAL_HINT,
    ) and experience.outcome_status not in (
        PraxisOutcomeStatus.SUCCESS,
        PraxisOutcomeStatus.PARTIAL,
    ):
        raise ValueError("failed execution cannot create success memory via governance")
    trust = "untrusted" if candidate.trust_level == PraxisTrustLevel.LOW else "trusted"
    req = MemoryWriteRequest(
        content=candidate.content_summary,
        proposed_truth_state=MemoryTruthState.CANDIDATE,
        writer_kind="runtime",
        source_run_id=run_id,
        source_trace_ids=candidate.evidence_refs,
        evidence_refs=candidate.evidence_refs,
        run_succeeded=run_succeeded,
        trust=trust,
    )
    return fabric.request_write(req)


def submit_consolidation_to_governance(
    fabric: "MemoryFabric",
    records: list[Any],
    *,
    run_id: str,
    threshold: float = 0.5,
    min_size: int = 2,
) -> Any:
    """Adapter: deterministically consolidate related memories into governed
    CANDIDATE summaries (+ SUMMARIZES edges). Mirrors
    ``submit_memory_candidate_to_governance`` — the runtime proposes, memory
    governance disposes. Never elevates trust (summary is always CANDIDATE);
    fail-closed on degenerate clusters; sources are never destroyed or altered."""
    from .memory_consolidation import consolidate

    return consolidate(
        fabric, records,
        writer_kind="runtime",
        source_run_id=run_id,
        threshold=threshold,
        min_size=min_size,
    )


def bridge_skill_candidate_to_library(skill: SkillCandidate) -> dict[str, Any]:
    """
    Conservative bridge to skills.SkillLibrary — returns a proposal dict only.
    Does NOT auto-register active skills or reflexes.
    """
    return {
        "proposal_only": True,
        "name": skill.name,
        "description": skill.description,
        "preconditions": skill.preconditions,
        "bounded_steps": skill.bounded_steps,
        "capabilities": skill.required_capabilities,
        "risk_class": skill.risk_class,
        "status": "candidate_not_registered",
        "governance_note": "Reflex activation requires runtime policy/sandbox/verifier/trace",
    }


# Alias for task terminology
PromotionGate = PromotionEvaluator


class PraxisMetabolism:
    """Orchestrates experience capture, candidate generation, and promotion evaluation."""

    def __init__(self) -> None:
        self.experiences: list[PraxisExperience] = []
        self.memory_candidates: list[MemoryCandidate] = []
        self.procedure_candidates: list[ProcedureCandidate] = []
        self.skill_candidates: list[SkillCandidate] = []
        self.promotion_decisions: list[PromotionDecision] = []
        self.reflex_checks: list[ReflexEligibilityCheck] = []
        self.reports: list[PraxisReport] = []

    def process_experience(
        self,
        experience: PraxisExperience,
        *,
        trace: Optional["TraceLedger"] = None,
        run_id: str = "",
        agent_id: str = "runtime",
        evaluate_promotion: bool = True,
    ) -> PraxisReport:
        self.experiences.append(experience)
        self._trace_event(trace, run_id, agent_id, "experience", experience.experience_id,
                          f"{experience.outcome_status.value}: {experience.objective[:80]}")

        mem_cands, gen_decisions = PraxisCandidateGenerator.generate(experience)
        self.memory_candidates.extend(mem_cands)
        self.promotion_decisions.extend(gen_decisions)

        for c in mem_cands:
            self._trace_event(
                trace, run_id, agent_id, "memory_candidate", c.candidate_id,
                f"{c.candidate_type.value}: {c.content_summary[:80]}",
            )
        for d in gen_decisions:
            self._trace_event(
                trace, run_id, agent_id, "promotion_decision", d.decision_id,
                f"{d.decision.value}: {d.reason[:80]}",
            )

        proc_ids: list[str] = []
        skill_ids: list[str] = []
        reflex_ids: list[str] = []
        limitations = [
            "Candidates are not verified truth",
            "No auto-promotion to canon or verified memory",
            "Reflexes still require full runtime governance",
        ]

        if evaluate_promotion and mem_cands:
            accepted = [
                c for c in mem_cands
                if any(
                    d.subject_id == c.candidate_id
                    and d.decision == PromotionDecisionType.ACCEPT_CANDIDATE
                    for d in gen_decisions
                )
            ]
            if accepted and experience.outcome_status == PraxisOutcomeStatus.SUCCESS:
                proc, proc_dec = PromotionEvaluator.evaluate_procedure(accepted, experience)
                self.promotion_decisions.append(proc_dec)
                self._trace_event(
                    trace, run_id, agent_id, "promotion_decision", proc_dec.decision_id,
                    proc_dec.reason[:80],
                )
                if proc:
                    self.procedure_candidates.append(proc)
                    proc_ids.append(proc.procedure_id)
                    skill, skill_dec = PromotionEvaluator.evaluate_skill(proc)
                    self.promotion_decisions.append(skill_dec)
                    self._trace_event(
                        trace, run_id, agent_id, "promotion_decision", skill_dec.decision_id,
                        skill_dec.reason[:80],
                    )
                    if skill:
                        self.skill_candidates.append(skill)
                        skill_ids.append(skill.skill_id)
                        check = PromotionEvaluator.check_reflex_eligibility(skill)
                        self.reflex_checks.append(check)
                        reflex_ids.append(skill.skill_id)
                        self._trace_event(
                            trace, run_id, agent_id, "reflex_check", skill.skill_id,
                            f"eligible={check.eligible}: {check.reason[:60]}",
                        )

        report = PraxisReport(
            experience_id=experience.experience_id,
            memory_candidates_created=[c.candidate_id for c in mem_cands],
            procedure_candidates_created=proc_ids,
            skill_candidates_created=skill_ids,
            promotion_decisions=[d.decision_id for d in gen_decisions],
            reflex_eligibility_checks=reflex_ids,
            limitations=limitations,
        )
        self.reports.append(report)
        return report

    def process_repo_report(
        self,
        report: "CodeTaskReport",
        *,
        trace: Optional["TraceLedger"] = None,
        run_id: str = "",
        agent_id: str = "repo_agent",
        memory_fabric: Optional["MemoryFabric"] = None,
    ) -> PraxisReport:
        experience = PraxisExperienceBuilder.from_repo_report(report, trace_run_id=run_id or report.task_id)
        praxis_report = self.process_experience(
            experience,
            trace=trace,
            run_id=run_id or report.task_id,
            agent_id=agent_id,
            evaluate_promotion=(report.final_status == "succeeded"),
        )
        if memory_fabric:
            for cand in self.memory_candidates:
                if cand.source_experience_id != experience.experience_id:
                    continue
                try:
                    submit_memory_candidate_to_governance(
                        memory_fabric, cand, experience, run_id=run_id or report.task_id,
                    )
                except (ValueError, Exception):
                    praxis_report.limitations.append(
                        f"governance submit skipped for {cand.candidate_id}"
                    )
        return praxis_report

    def _trace_event(
        self,
        trace: Optional["TraceLedger"],
        run_id: str,
        agent_id: str,
        event_type: str,
        subject_id: str,
        summary: str,
    ) -> None:
        if trace is None or not run_id:
            return
        append = getattr(trace, "append_praxis_event", None)
        if append:
            append(
                PraxisEventRecord.make(
                    run_id=run_id,
                    agent_id=agent_id,
                    event_type=event_type,
                    subject_id=subject_id,
                    summary=summary,
                )
            )

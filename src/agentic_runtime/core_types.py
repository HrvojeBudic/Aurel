"""
core_types.py — The vocabulary of the Agentic Runtime.

Every object that crosses a subsystem boundary is defined here. These are the
"7 objects" of the spec, expanded to production shape, plus the supporting
enums and the AgentCard.

Design law (Hrvoje §3): the entity NEVER acts. It only emits a CommandEnvelope.
The runtime decides whether/how it executes. So CommandEnvelope is a *proposal*,
never an execution. ObservationEnvelope is the only way results re-enter the mind.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  Canonical hashing — the substrate of the whole trace/verify system.
#  "Ako nema traga, nije se dogodilo." Hash must be deterministic & stable.
# --------------------------------------------------------------------------- #
def canonical_json(obj: Any) -> str:
    """Stable JSON: sorted keys, no whitespace drift, enums -> value."""
    def default(o):
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, "to_dict"):
            return o.to_dict()
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=default)


def sha(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def now() -> float:
    return time.time()


# --------------------------------------------------------------------------- #
#  Enums
# --------------------------------------------------------------------------- #
class RiskLevel(str, Enum):
    TRIVIAL = "trivial"      # read-only, no side effects
    LOW = "low"              # bounded writes inside authority
    MEDIUM = "medium"        # writes touching shared/canonical state
    HIGH = "high"            # destructive / irreversible / network / secrets
    CRITICAL = "critical"    # outside authority entirely -> hard stop


class AgentClass(str, Enum):
    """Classes are AgentCard *configurations*, not separate codebases."""
    CORE = "core"            # canonical decision-maker; the only writer
    EXECUTION = "execution"  # writes inside an assigned scope (sandbox)
    RESEARCH = "research"    # read-only; no write authority
    CRITIC = "critic"        # verifies; no execution authority
    MEMORY = "memory"        # background consolidation; writes only to memory
    POLICY = "policy"        # guards boundaries; cannot execute tools


class PolicyVerdict(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class ExecutionStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    PLANNED = "planned"
    RUNNING = "running"
    REJECTED = "rejected"
    NEEDS_HUMAN = "needs_human"
    INVALID_PLAN = "invalid_plan"
    HALTED = "halted"
    FAILED = "failed"
    VERIFICATION_FAILED = "verification_failed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED_WITH_PARTIAL_EXECUTION = "failed_with_partial_execution"
    COMPLETED = "completed"


class TruthStatus(str, Enum):
    ASSERTED = "asserted"        # claimed, not yet verified
    VERIFIED = "verified"        # confirmed by a verifier against real state
    CONTRADICTED = "contradicted"
    DEPRECATED = "deprecated"    # superseded; kept for audit


class CapabilityState(str, Enum):
    OBSERVED = "observed"
    REPEATED = "repeated"
    CANDIDATE = "candidate"
    TESTED = "tested"
    APPROVED = "approved"
    ACTIVE = "active"
    OPTIMIZED = "optimized"
    REFLEX = "reflex"           # cached verified plan; skips planning LLM call


class MemoryTier(str, Enum):
    EPHEMERAL = "L1_ephemeral"   # last relevant steps (ring buffer)
    EPISODIC = "L2_episodic"     # what happened (trace-linked)
    SEMANTIC = "L3_semantic"     # what it means (vector RAG)
    PROCEDURAL = "L4_procedural" # what it can now do (skills)
    CANON = "L5_canon"           # what it must never forget (policy/identity)


class MemoryTruthState(str, Enum):
    """Governed lifecycle of a memory record (P0.9).

    Distinct from ``TruthStatus`` (verification verdict): this is the promotion
    pipeline state that decides whether a memory may be operated on as fact.
    """
    RAW = "raw"                  # ephemeral observation; not durable knowledge
    EPISODIC = "episodic"        # what happened, trace-linked
    CANDIDATE = "candidate"      # proposed semantic fact; needs evidence
    VERIFIED = "verified"        # candidate confirmed by evidence
    PROCEDURAL = "procedural"    # repeated, reusable know-how
    CANON = "canon"              # never-forget identity/policy; approval-gated
    REJECTED = "rejected"        # denied by governance; kept for audit, inactive
    EXPIRED = "expired"          # past its expiry policy; inactive


# --------------------------------------------------------------------------- #
#  AgentCard — the identity + authority of an entity. NOT a persona.
# --------------------------------------------------------------------------- #
@dataclass
class AuthorityScope:
    """What the entity may *change*. Distinct from which tools it can call."""
    write_paths: list[str] = field(default_factory=list)   # path prefixes it may write
    read_paths: list[str] = field(default_factory=list)    # path prefixes it may read
    protected_test_paths: list[str] = field(default_factory=list)
    allow_test_modification: bool = False                  # deprecated; use allow_protected_mutation
    allow_protected_mutation: bool = False                 # dedicated pathway + HITL only
    allow_network: bool = False
    allow_secrets: bool = False
    git_branches: list[str] = field(default_factory=list)  # branches it may touch
    max_risk: RiskLevel = RiskLevel.LOW                    # ceiling without HITL

    def to_dict(self) -> dict:
        d = asdict(self)
        d["max_risk"] = self.max_risk.value
        return d


@dataclass
class AgentCard:
    id: str
    name: str
    agent_class: AgentClass
    mission: str
    authority: AuthorityScope
    allowed_tools: list[str] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)
    memory_scope: str = "project-local"
    skill_scope: list[str] = field(default_factory=list)
    model_profile: str = "balanced"            # router selects, not hardcoded model
    escalation_policy: list[str] = field(default_factory=list)
    runtime_limits: dict[str, float] = field(default_factory=dict)  # budgets

    @staticmethod
    def make(name: str, agent_class: AgentClass, mission: str,
             authority: AuthorityScope, **kw) -> "AgentCard":
        return AgentCard(id=new_id("card"), name=name, agent_class=agent_class,
                         mission=mission, authority=authority, **kw)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["agent_class"] = self.agent_class.value
        d["authority"] = self.authority.to_dict()
        return d


# --------------------------------------------------------------------------- #
#  Intent — a user/parent goal entering the system.
# --------------------------------------------------------------------------- #
@dataclass
class Intent:
    id: str
    text: str
    origin: str = "operator"          # operator | parent_agent | schedule
    constraints: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=now)

    @staticmethod
    def make(text: str, origin: str = "operator", constraints=None) -> "Intent":
        return Intent(id=new_id("intent"), text=text, origin=origin,
                      constraints=constraints or [])


# --------------------------------------------------------------------------- #
#  CommandEnvelope — a PROPOSAL to act. The runtime, not the entity, executes.
# --------------------------------------------------------------------------- #
@dataclass
class CommandEnvelope:
    id: str
    issuer_card_id: str
    tool: str
    args: dict[str, Any]
    rationale: str                      # why the entity wants this (for trace)
    declared_risk: RiskLevel            # entity's self-assessment (policy re-scores)
    expected_effect: str                # what the entity claims will change
    parent_intent_id: Optional[str] = None
    created_at: float = field(default_factory=now)

    @staticmethod
    def make(issuer_card_id: str, tool: str, args: dict, rationale: str,
             declared_risk: RiskLevel, expected_effect: str,
             parent_intent_id: Optional[str] = None) -> "CommandEnvelope":
        return CommandEnvelope(
            id=new_id("cmd"), issuer_card_id=issuer_card_id, tool=tool, args=args,
            rationale=rationale, declared_risk=declared_risk,
            expected_effect=expected_effect, parent_intent_id=parent_intent_id)

    def command_hash(self) -> str:
        return sha(canonical_json({
            "issuer": self.issuer_card_id, "tool": self.tool,
            "args": self.args, "expected_effect": self.expected_effect}))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["declared_risk"] = self.declared_risk.value
        return d


# --------------------------------------------------------------------------- #
#  ObservationEnvelope — the ONLY way results re-enter cognition.
# --------------------------------------------------------------------------- #
@dataclass
class ObservationEnvelope:
    id: str
    command_id: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    artifacts: dict[str, Any] = field(default_factory=dict)  # diffs, parsed data
    duration_s: float = 0.0
    created_at: float = field(default_factory=now)

    @staticmethod
    def make(command_id: str, success: bool, **kw) -> "ObservationEnvelope":
        return ObservationEnvelope(id=new_id("obs"), command_id=command_id,
                                   success=success, **kw)

    def observation_hash(self) -> str:
        return sha(canonical_json({
            "command_id": self.command_id, "success": self.success,
            "exit_code": self.exit_code, "stdout": self.stdout,
            "stderr": self.stderr, "artifacts": self.artifacts}))

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
#  VerifierResult — did the world actually change as claimed?
# --------------------------------------------------------------------------- #
@dataclass
class VerifierResult:
    passed: bool
    verifier: str
    evidence: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    code: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
#  PlanningFailureRecord — hash-chained trace of rejected planner output (P0.5).
# --------------------------------------------------------------------------- #
@dataclass
class PlanningFailureRecord:
    id: str
    intent_id: str
    issuer_card_id: str
    status: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(intent_id: str, issuer_card_id: str, status: str,
             reason: str, details: Optional[dict] = None) -> "PlanningFailureRecord":
        return PlanningFailureRecord(
            id=new_id("plan_fail"),
            intent_id=intent_id,
            issuer_card_id=issuer_card_id,
            status=status,
            reason=reason,
            details=details or {},
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "planning_failure",
            "intent_id": self.intent_id,
            "issuer": self.issuer_card_id,
            "status": self.status,
            "reason": self.reason,
            "details": self.details,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RuntimeStatusTransitionRecord:
    id: str
    run_id: str
    intent_id: str
    issuer_card_id: str
    from_status: str
    to_status: str
    reason_code: str
    message: str
    evidence_refs: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    command_hash: Optional[str] = None
    observation_hash: Optional[str] = None
    verifier_hash: Optional[str] = None
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        intent_id: str,
        issuer_card_id: str,
        from_status: str,
        to_status: str,
        reason_code: str,
        message: str,
        evidence_refs: Optional[list[str]] = None,
        details: Optional[dict[str, Any]] = None,
        command_hash: Optional[str] = None,
        observation_hash: Optional[str] = None,
        verifier_hash: Optional[str] = None,
    ) -> "RuntimeStatusTransitionRecord":
        return RuntimeStatusTransitionRecord(
            id=new_id("run_state"),
            run_id=run_id,
            intent_id=intent_id,
            issuer_card_id=issuer_card_id,
            from_status=from_status,
            to_status=to_status,
            reason_code=reason_code,
            message=message,
            evidence_refs=evidence_refs or [],
            details=details or {},
            command_hash=command_hash,
            observation_hash=observation_hash,
            verifier_hash=verifier_hash,
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "runtime_status_transition",
            "run_id": self.run_id,
            "intent_id": self.intent_id,
            "issuer": self.issuer_card_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reason_code": self.reason_code,
            "message": self.message,
            "evidence_refs": self.evidence_refs,
            "details": self.details,
            "command_hash": self.command_hash,
            "observation_hash": self.observation_hash,
            "verifier_hash": self.verifier_hash,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BudgetDecisionRecord:
    id: str
    run_id: str
    intent_id: str
    issuer_card_id: str
    metric: str
    verdict: str  # allow | deny
    used: float
    limit: float
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        intent_id: str,
        issuer_card_id: str,
        metric: str,
        verdict: str,
        used: float,
        limit: float,
        reason: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> "BudgetDecisionRecord":
        return BudgetDecisionRecord(
            id=new_id("budget"),
            run_id=run_id,
            intent_id=intent_id,
            issuer_card_id=issuer_card_id,
            metric=metric,
            verdict=verdict,
            used=used,
            limit=limit,
            reason=reason,
            details=details or {},
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "budget_decision",
            "run_id": self.run_id,
            "intent_id": self.intent_id,
            "issuer": self.issuer_card_id,
            "metric": self.metric,
            "verdict": self.verdict,
            "used": self.used,
            "limit": self.limit,
            "reason": self.reason,
            "details": self.details,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MemoryGovernanceRecord:
    """Hash-chained trace of a memory write/promotion decision (P0.9)."""
    id: str
    run_id: str
    agent_id: str
    action: str       # write | promote
    verdict: str      # allow | deny
    memory_id: str
    from_state: str
    to_state: str
    reason_code: str
    message: str
    evidence_refs: list[str] = field(default_factory=list)
    source_trace_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        agent_id: str,
        action: str,
        verdict: str,
        memory_id: str,
        from_state: str,
        to_state: str,
        reason_code: str,
        message: str,
        evidence_refs: Optional[list[str]] = None,
        source_trace_ids: Optional[list[str]] = None,
        confidence: float = 0.0,
        details: Optional[dict[str, Any]] = None,
    ) -> "MemoryGovernanceRecord":
        return MemoryGovernanceRecord(
            id=new_id("mem_gov"),
            run_id=run_id,
            agent_id=agent_id,
            action=action,
            verdict=verdict,
            memory_id=memory_id,
            from_state=from_state,
            to_state=to_state,
            reason_code=reason_code,
            message=message,
            evidence_refs=evidence_refs or [],
            source_trace_ids=source_trace_ids or [],
            confidence=confidence,
            details=details or {},
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "memory_governance",
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "verdict": self.verdict,
            "memory_id": self.memory_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason_code": self.reason_code,
            "message": self.message,
            "evidence_refs": self.evidence_refs,
            "source_trace_ids": self.source_trace_ids,
            "confidence": self.confidence,
            "details": self.details,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApprovalReceiptRecord:
    """Hash-chained trace of an approval decision (P0.15)."""
    id: str
    run_id: str
    issuer_card_id: str
    request_id: str
    receipt_id: str
    tool: str
    risk_class: str
    outcome: str
    reason: str
    decided_by: str
    preview_summary: str = ""
    approved_scope: list[str] = field(default_factory=list)
    trace_id: str = ""
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        issuer_card_id: str,
        request_id: str,
        receipt_id: str,
        tool: str,
        risk_class: str,
        outcome: str,
        reason: str,
        decided_by: str,
        preview_summary: str = "",
        approved_scope: Optional[list[str]] = None,
        trace_id: str = "",
    ) -> "ApprovalReceiptRecord":
        return ApprovalReceiptRecord(
            id=new_id("approval_trace"),
            run_id=run_id,
            issuer_card_id=issuer_card_id,
            request_id=request_id,
            receipt_id=receipt_id,
            tool=tool,
            risk_class=risk_class,
            outcome=outcome,
            reason=reason,
            decided_by=decided_by,
            preview_summary=preview_summary,
            approved_scope=approved_scope or [],
            trace_id=trace_id,
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "approval_receipt",
            "run_id": self.run_id,
            "issuer_card_id": self.issuer_card_id,
            "request_id": self.request_id,
            "receipt_id": self.receipt_id,
            "tool": self.tool,
            "risk_class": self.risk_class,
            "outcome": self.outcome,
            "reason": self.reason,
            "decided_by": self.decided_by,
            "preview_summary": self.preview_summary,
            "approved_scope": self.approved_scope,
            "trace_id": self.trace_id,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PraxisEventRecord:
    """Hash-chained trace of a Praxis metabolism event (P0.16)."""
    id: str
    run_id: str
    agent_id: str
    event_type: str
    subject_id: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        agent_id: str,
        event_type: str,
        subject_id: str,
        summary: str,
        details: Optional[dict[str, Any]] = None,
    ) -> "PraxisEventRecord":
        return PraxisEventRecord(
            id=new_id("praxis"),
            run_id=run_id,
            agent_id=agent_id,
            event_type=event_type,
            subject_id=subject_id,
            summary=summary[:500],
            details=details or {},
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "praxis_event",
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "subject_id": self.subject_id,
            "summary": self.summary,
            "details": self.details,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SandboxViolationRecord:
    """Hash-chained trace of a sandbox policy violation (P0.17)."""
    id: str
    run_id: str
    issuer_card_id: str
    profile_name: str
    tool: str
    attempted_action: str
    reason: str
    attempted_path: str = ""
    severity: str = "deny"
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        issuer_card_id: str,
        profile_name: str,
        tool: str,
        attempted_action: str,
        reason: str,
        *,
        attempted_path: str = "",
        severity: str = "deny",
        details: Optional[dict[str, Any]] = None,
    ) -> "SandboxViolationRecord":
        return SandboxViolationRecord(
            id=new_id("sandbox"),
            run_id=run_id,
            issuer_card_id=issuer_card_id,
            profile_name=profile_name,
            tool=tool,
            attempted_action=attempted_action,
            reason=reason[:500],
            attempted_path=attempted_path,
            severity=severity,
            details=details or {},
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "sandbox_violation",
            "run_id": self.run_id,
            "issuer": self.issuer_card_id,
            "profile_name": self.profile_name,
            "tool": self.tool,
            "attempted_action": self.attempted_action,
            "reason": self.reason,
            "attempted_path": self.attempted_path,
            "severity": self.severity,
            "details": self.details,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SandboxAttestationRecord:
    """Hash-chained proof of the isolation a host could actually provide (M0).

    Written at runtime construction from a *functional* probe (a real sandboxed
    execution), not a version/info check — so the trace records the true
    isolation posture a run executed under, closing the "probe says OK, runtime
    fails" gap.
    """
    id: str
    run_id: str
    backend: str            # sandbox mode value
    available: bool
    hard_isolated: bool
    reason: str
    probe: str
    host: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(run_id: str, attestation: dict[str, Any]) -> "SandboxAttestationRecord":
        return SandboxAttestationRecord(
            id=new_id("sbxattest"),
            run_id=run_id,
            backend=str(attestation.get("backend", "")),
            available=bool(attestation.get("available", False)),
            hard_isolated=bool(attestation.get("hard_isolated", False)),
            reason=str(attestation.get("reason", ""))[:500],
            probe=str(attestation.get("probe", "")),
            host=dict(attestation.get("host", {})),
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "sandbox_attestation",
            "run_id": self.run_id,
            "backend": self.backend,
            "available": self.available,
            "hard_isolated": self.hard_isolated,
            "reason": self.reason,
            "probe": self.probe,
            "host": self.host,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ToolContractViolationRecord:
    """Hash-chained trace of a tool contract (input/output) violation (P0.10)."""
    id: str
    run_id: str
    issuer_card_id: str
    tool: str
    phase: str          # input | output | registry
    code: str
    reason: str
    arg: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    prev_entry_hash: str = ""
    entry_hash: str = ""

    @staticmethod
    def make(
        run_id: str,
        issuer_card_id: str,
        tool: str,
        phase: str,
        code: str,
        reason: str,
        arg: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> "ToolContractViolationRecord":
        return ToolContractViolationRecord(
            id=new_id("contract"),
            run_id=run_id,
            issuer_card_id=issuer_card_id,
            tool=tool,
            phase=phase,
            code=code,
            reason=reason,
            arg=arg,
            details=details or {},
        )

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "kind": "tool_contract_violation",
            "run_id": self.run_id,
            "issuer": self.issuer_card_id,
            "tool": self.tool,
            "phase": self.phase,
            "code": self.code,
            "reason": self.reason,
            "arg": self.arg,
            "details": self.details,
        }))

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
#  StateTransitionRecord — the atom of the trace ledger.
#  before -> command -> observation -> after, each hashed.
# --------------------------------------------------------------------------- #
@dataclass
class StateTransitionRecord:
    id: str
    before_state_hash: str
    command_hash: str
    observation_hash: str
    after_state_hash: str
    verifier_result: VerifierResult
    policy_verdict: PolicyVerdict
    issuer_card_id: str
    parent_intent_id: Optional[str]
    created_at: float = field(default_factory=now)
    # filled by the ledger:
    prev_entry_hash: str = ""
    entry_hash: str = ""

    def payload_hash(self) -> str:
        return sha(canonical_json({
            "before": self.before_state_hash, "command": self.command_hash,
            "observation": self.observation_hash, "after": self.after_state_hash,
            "verifier": self.verifier_result.to_dict(),
            "verdict": self.policy_verdict.value, "issuer": self.issuer_card_id}))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verifier_result"] = self.verifier_result.to_dict()
        d["policy_verdict"] = self.policy_verdict.value
        return d


# --------------------------------------------------------------------------- #
#  MemoryRecord — NOT chat history. Every memory carries provenance & truth.
# --------------------------------------------------------------------------- #
@dataclass
class MemoryRecord:
    id: str
    tier: MemoryTier
    content: str
    source: str
    truth_status: TruthStatus = TruthStatus.ASSERTED
    confidence: float = 0.5
    importance: float = 0.5                # self-assessed salience (0..1)
    created_at: float = field(default_factory=now)
    last_used: float = field(default_factory=now)
    usage_count: int = 0
    decay: float = 0.0                     # accumulated forgetting pressure
    embedding: Optional[list[float]] = None
    links: list[str] = field(default_factory=list)  # ids of related records
    # ---- P0.9 provenance & governance ---------------------------------- #
    memory_id: str = ""
    created_by: str = ""
    source_run_id: str = ""
    source_command_id: Optional[str] = None
    source_trace_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    truth_state: MemoryTruthState = MemoryTruthState.RAW
    promotion_state: str = "none"
    expiry_policy: dict[str, Any] = field(default_factory=lambda: {"kind": "none"})
    # ---- A0 bi-temporal stamps (additive, default-open) ---------------- #
    # Valid time = when the fact is true in the world; transaction time = when
    # the system believed it. ``None`` on any endpoint means an OPEN interval:
    # a ``valid_to``/``transaction_to`` of None ⇒ still-current. These fields
    # are descriptive metadata only — they are NOT written by A0 (no writer
    # exists yet; supersession/revision arrive in A2/A4) and they never enter a
    # hashed trace payload (the memory-governance funnel serializes a fixed
    # scalar set, not the record dict), so default records stay byte-identical.
    superseded_by: Optional[str] = None   # id of the version that replaced this
    revises: Optional[str] = None         # id of the version this one revises
    valid_from: Optional[float] = None    # None ⇒ open (since inception)
    valid_to: Optional[float] = None      # None ⇒ open (still valid in-world)
    transaction_from: Optional[float] = None  # None ⇒ open (since first belief)
    transaction_to: Optional[float] = None    # None ⇒ open (current belief)

    @staticmethod
    def make(tier: MemoryTier, content: str, source: str, **kw) -> "MemoryRecord":
        rec = MemoryRecord(id=new_id("mem"), tier=tier, content=content,
                           source=source, **kw)
        if not rec.memory_id:
            rec.memory_id = rec.id
        return rec

    def is_expired(self, at: Optional[float] = None) -> bool:
        if self.truth_state is MemoryTruthState.EXPIRED:
            return True
        pol = self.expiry_policy or {}
        kind = pol.get("kind", "none")
        if kind == "ttl":
            ttl = float(pol.get("ttl_s", 0))
            return (at if at is not None else now()) >= self.created_at + ttl
        return False

    def is_active(self, at: Optional[float] = None) -> bool:
        if self.truth_state in (MemoryTruthState.REJECTED, MemoryTruthState.EXPIRED):
            return False
        return not self.is_expired(at)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["truth_status"] = self.truth_status.value
        d["truth_state"] = self.truth_state.value
        return d


# --------------------------------------------------------------------------- #
#  SkillCandidate — a successful trajectory proposed for promotion.
# --------------------------------------------------------------------------- #
@dataclass
class SkillCandidate:
    id: str
    name: str
    description: str
    action_sequence: list[dict]            # the compiled command templates
    required_tools: list[str]
    required_permissions: list[str]
    input_schema: dict
    output_schema: dict
    environment_signature: str             # for reflex drift-detection
    success_count: int = 1
    failure_count: int = 0
    state: CapabilityState = CapabilityState.OBSERVED
    last_verified: float = field(default_factory=now)
    cost_profile: dict[str, float] = field(default_factory=dict)
    known_failures: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value
        return d


@dataclass
class ExecutionOutcome:
    status: ExecutionStatus
    reason_code: str
    message: str
    run_id: str
    trace_refs: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    goal: str = ""
    confidence: float = 0.0
    actions_executed: int = 0
    errors: list[str] = field(default_factory=list)
    planning_status: str = ""
    planning_details: dict[str, Any] = field(default_factory=dict)
    trace_len: int = 0
    trace_intact: bool = False
    trace_merkle_root: str = ""
    budget: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    skills: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out = asdict(self)
        out["status"] = self.status.value
        out["reason"] = self.message  # backward-compatible alias used in old tests/demo
        return out

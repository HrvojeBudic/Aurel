"""
entity.py — The Agentic Entity (Hrvoje §2, §6.1).

Planning failures are validated by PlanValidator and traced before any tool runs.
``run()`` never reports ``completed`` unless at least one action was verified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .budget import BudgetExceeded
from .core_types import (
    AgentCard,
    CommandEnvelope,
    ExecutionOutcome,
    ExecutionStatus,
    Intent,
    MemoryRecord,
    MemoryTier,
    PlanningFailureRecord,
    PraxisEventRecord,
    RiskLevel,
    canonical_json,
    sha,
)
from .reasoning import reasoning_scheduler
from .model_router import ModelRouter
from .plan_validator import PlanValidationResult, PlanValidator, PlanStatus
from .runtime import AgenticRuntime, CommandResult
from .skills import SkillLibrary, environment_signature
from .state_machine import RuntimeStateMachine


@dataclass
class AgentRuntimeState:
    current_goal: str = ""
    active_plan: list[dict] = field(default_factory=list)
    step_index: int = 0
    confidence: float = 0.6
    risk_level: RiskLevel = RiskLevel.LOW
    open_errors: list[str] = field(default_factory=list)
    last_verified_state: str = ""
    attempts_on_step: int = 0
    done: bool = False
    escalated: bool = False
    planning_status: str = ""
    budget_exceeded: bool = False

    def snapshot(self) -> dict:
        d = dict(self.__dict__)
        d["risk_level"] = self.risk_level.value
        return d


_PLANNER_SYSTEM = (
    "You are the planning core of a governed agentic runtime. You do NOT act; "
    "you emit a JSON plan. Each step must include: tool, args, reason. "
    "Optional: step_id, expected_effect, risk_level. "
    "Tools: list_dir, read_file, edit_file, write_file, run_tests. "
    "Prefer the smallest safe change. Output ONLY JSON: {\"plan\": [ ... ]}")

MAX_ATTEMPTS_PER_STEP = 3


class AgenticEntity:
    def __init__(self, card: AgentCard, runtime: AgenticRuntime,
                 router: ModelRouter, skills: SkillLibrary,
                 plan_validator: Optional[PlanValidator] = None) -> None:
        self.card = card
        self.runtime = runtime
        self.router = router
        self.skills = skills
        self.plan_validator = plan_validator or PlanValidator(
            registered_tools=runtime.tools.registered,
            allowed_tools=card.allowed_tools or None,
        )
        self.state = AgentRuntimeState()
        self._executed_commands: list[CommandEnvelope] = []

    def _current_env_sig(self) -> str:
        return environment_signature(
            {"fs_diff": {f: "" for f in _safe_list(self.runtime)}})

    def plan(self, intent: Intent) -> PlanValidationResult:
        self.state.current_goal = intent.text

        env_sig = self._current_env_sig()
        reflex = self.skills.find_reflex(intent.text, env_sig)
        if reflex:
            self._remember(MemoryRecord.make(
                MemoryTier.EPHEMERAL,
                f"REFLEX hit: reusing skill '{reflex.name}' (no LLM call)",
                source=self.card.id))
            steps = [{"tool": s["tool"], "args": s["args_template"],
                      "rationale": f"reflex:{reflex.name}",
                      "reason": f"reflex:{reflex.name}",
                      "expected_effect": s["expected_effect"], "risk": "low"}
                     for s in reflex.action_sequence]
            return self.plan_validator.validate_steps(steps)

        context = self.runtime.memory.assemble_context(intent.text, k=5)
        user = (f"GOAL: {intent.text}\nCONSTRAINTS: {intent.constraints}\n"
                f"MEMORY CONTEXT:\n{context}\n")
        profile = self.card.model_profile
        if reasoning_scheduler.enabled():
            profile = self._allocate_reasoning(intent, context)
        self.runtime.budget.precheck_llm()
        raw, model_name, usage = self.router.complete_with_usage(
            profile, _PLANNER_SYSTEM, user)
        self.runtime.budget.charge_llm(usage=usage)
        result = self.plan_validator.parse_and_validate(raw)
        if result.valid:
            self._remember(MemoryRecord.make(
                MemoryTier.EPISODIC,
                f"planned {len(result.steps)} steps for goal via {model_name}",
                source=self.card.id))
        return result

    def _allocate_reasoning(self, intent: Intent, context: str) -> str:
        """B3/B4 — adaptive effort allocation: charge one reasoning pass, record a
        hash-chained reasoning_allocation trace event (safe summaries, no raw CoT),
        and return the chosen model profile. Proposal-only; allocation ≠ authority."""
        alloc = reasoning_scheduler.allocate(
            intent=intent, card=self.card, memory_context=context, router=self.router)
        self.runtime.budget.charge_reasoning(passes=1)
        self.runtime.trace.append_praxis_event(PraxisEventRecord.make(
            run_id=self.runtime.trace.run_id,
            agent_id=self.card.id,
            event_type="reasoning_allocation",
            subject_id=intent.id,
            summary=(f"difficulty={alloc.difficulty.value} effort={alloc.effort.value} "
                     f"profile={alloc.chosen_profile} passes={alloc.passes}"),
            details={
                "difficulty": alloc.difficulty.value,
                "requested_effort": alloc.requested_effort.value,
                "effort": alloc.effort.value,
                "profile": alloc.chosen_profile,
                "passes": alloc.passes,
                "reasons": list(alloc.reasons),
            }))
        return alloc.chosen_profile

    def run(self, intent: Intent) -> dict:
        self.runtime.budget.begin_run(
            run_id=self.runtime.trace.run_id,
            agent_id=self.card.id,
            intent_id=intent.id,
        )
        sm = RuntimeStateMachine(
            trace=self.runtime.trace,
            run_id=self.runtime.trace.run_id,
            intent_id=intent.id,
            agent_id=self.card.id,
        )
        sm.transition(
            ExecutionStatus.PLANNING,
            "planning_started",
            "planning started",
        )

        try:
            plan_result = self.plan(intent)
        except BudgetExceeded as e:
            self.state.budget_exceeded = True
            sm.transition(
                ExecutionStatus.HALTED,
                "budget_exceeded",
                f"budget exceeded during planning: {e}",
            )
            return self._outcome(sm, reason_code="budget_exceeded", message=str(e))

        if not plan_result.valid:
            return self._halt_planning_failure(intent, plan_result, sm)

        sm.transition(
            ExecutionStatus.PLANNED,
            "plan_valid",
            f"plan accepted with {len(plan_result.steps)} step(s)",
        )
        self.state.active_plan = plan_result.steps
        sm.transition(
            ExecutionStatus.RUNNING,
            "execution_started",
            "executing validated plan",
        )

        for i, step in enumerate(self.state.active_plan):
            self.state.step_index = i
            self.state.attempts_on_step = 0
            ok, res = self._execute_step(intent, step)
            if ok:
                continue
            if not self.state.escalated:
                retried = self._replan_and_retry(intent, step)
                if retried:
                    continue
            outcome_status, reason_code, message = self._failure_semantics(step, res)
            sm.transition(
                outcome_status,
                reason_code,
                message,
                evidence_refs=_evidence_refs(self._executed_commands),
                details={
                    "step_index": i,
                    "tool": step["tool"],
                    "actions_executed": len(self._executed_commands),
                },
                command_hash=res.transition.command_hash if res and res.transition else None,
                observation_hash=(
                    res.transition.observation_hash if res and res.transition else None
                ),
                verifier_hash=(
                    _verifier_hash(res) if res and res.transition else None
                ),
            )
            return self._outcome(sm, reason_code=reason_code, message=message)

        if not self._executed_commands:
            sm.transition(
                ExecutionStatus.HALTED,
                "no_actions_executed",
                "no valid actions executed; cannot report completed",
            )
            return self._outcome(
                sm,
                reason_code="no_actions_executed",
                message="no valid actions executed; cannot report completed",
            )

        self._promote_skill(intent)
        self.state.done = True
        self.state.confidence = min(1.0, self.state.confidence + 0.2)
        sm.transition(
            ExecutionStatus.COMPLETED,
            "run_completed",
            "run completed after verified execution",
            evidence_refs=_evidence_refs(self._executed_commands),
            details={"actions_executed": len(self._executed_commands)},
        )
        return self._outcome(sm, reason_code="run_completed", message="completed")

    def _execute_step(self, intent: Intent, step: dict) -> tuple[bool, Optional[CommandResult]]:
        self.state.attempts_on_step += 1
        cmd = CommandEnvelope.make(
            issuer_card_id=self.card.id, tool=step["tool"], args=step["args"],
            rationale=step.get("rationale") or step.get("reason", ""),
            declared_risk=_risk(step.get("risk") or step.get("risk_level", "low")),
            expected_effect=step.get("expected_effect", ""),
            parent_intent_id=intent.id)
        try:
            res: CommandResult = self.runtime.submit(cmd, self.card)
        except BudgetExceeded as e:
            self.state.open_errors.append(str(e))
            self.state.budget_exceeded = True
            return False, None

        if (res.decision.verdict.value == "require_approval"
                or (res.verifier and res.verifier.code == "HITL_DENIED")) and not res.ok:
            self.state.escalated = True
            return False, res

        if res.ok:
            self._executed_commands.append(cmd)
            self.state.last_verified_state = (res.transition.after_state_hash
                                              if res.transition else "")
            self.state.confidence = min(1.0, self.state.confidence + 0.05)
            return True, res

        self.state.open_errors.append(
            f"{step['tool']}: {res.verifier.reason or res.observation.stderr[:80]}")
        self.state.confidence = max(0.0, self.state.confidence - 0.15)
        return False, res

    def _replan_and_retry(self, intent: Intent, failed_step: dict) -> bool:
        if self.state.attempts_on_step >= self.runtime.budget.policy.max_retries_per_step:
            self.state.budget_exceeded = True
            return False
        step_key = f"{intent.id}:{self.state.step_index}"
        try:
            self.runtime.budget.charge_retry(step_key)
        except BudgetExceeded as e:
            self.state.open_errors.append(str(e))
            self.state.budget_exceeded = True
            return False
        try:
            self._remember(MemoryRecord.make(
                MemoryTier.EPISODIC,
                f"FAILURE on {failed_step['tool']}: {self.state.open_errors[-1]}; "
                f"retrying step", source=self.card.id,
                confidence=0.4))
        except BudgetExceeded as e:
            self.state.open_errors.append(str(e))
            self.state.budget_exceeded = True
            return False
        ok, _ = self._execute_step(intent, failed_step)
        return ok

    def _promote_skill(self, intent: Intent) -> None:
        if not self._executed_commands:
            return
        env_sig = self._current_env_sig()
        cost = self.runtime.budget.snapshot()
        self.skills.observe_success(
            name=_skill_name(intent.text), description=intent.text,
            commands=self._executed_commands, env_sig=env_sig, cost=cost)

    def _halt_planning_failure(
        self,
        intent: Intent,
        result: PlanValidationResult,
        sm: RuntimeStateMachine,
    ) -> dict:
        self.state.planning_status = result.status.value
        self.runtime.trace.append_planning_failure(PlanningFailureRecord.make(
            intent_id=intent.id,
            issuer_card_id=self.card.id,
            status=result.status.value,
            reason=result.reason,
            details=result.details,
        ))
        try:
            self._remember(MemoryRecord.make(
                MemoryTier.EPISODIC,
                f"PLANNING HALT [{result.status.value}]: {result.reason}",
                source=self.card.id, confidence=0.4))
        except BudgetExceeded:
            self.state.budget_exceeded = True
        final = (
            ExecutionStatus.INVALID_PLAN
            if result.status in {
                PlanStatus.INVALID_JSON,
                PlanStatus.INVALID_SCHEMA,
            }
            else ExecutionStatus.HALTED
        )
        sm.transition(
            final,
            result.status.value,
            result.reason,
            details=result.details,
        )
        return self._outcome(
            sm,
            reason_code=result.status.value,
            message=f"{result.status.value}: {result.reason}",
            planning_status=result.status.value,
            planning_details=result.details,
        )

    def _remember(self, rec: MemoryRecord) -> None:
        self.runtime.budget.charge_memory_write()
        self.runtime.memory.remember(
            rec, writer_kind="agent", source_run_id=self.runtime.trace.run_id)

    def _outcome(
        self,
        sm: RuntimeStateMachine,
        *,
        reason_code: str,
        message: str,
        planning_status: str = "",
        planning_details: Optional[dict[str, Any]] = None,
    ) -> dict:
        ok, broken = self.runtime.trace.verify_chain()
        verification_summary = {"ok": ok, "broken_index": broken}
        self.runtime.trace.seal_run(
            sm.status.value, verification_summary=verification_summary
        )
        outcome = ExecutionOutcome(
            status=sm.status,
            reason_code=reason_code,
            message=message,
            run_id=self.runtime.trace.run_id,
            trace_refs={
                "run_id": self.runtime.trace.run_id,
                "trace_len": len(self.runtime.trace),
                "last_transition_id": sm.last_transition_id,
                "chain_head": self.runtime.trace.head,
            },
            evidence_refs=_evidence_refs(self._executed_commands),
            goal=self.state.current_goal,
            confidence=round(self.state.confidence, 2),
            actions_executed=len(self._executed_commands),
            errors=self.state.open_errors,
            planning_status=planning_status or self.state.planning_status,
            planning_details=planning_details or {},
            trace_len=len(self.runtime.trace),
            trace_intact=ok,
            trace_merkle_root=self.runtime.trace.merkle_root()[:16],
            budget=self.runtime.budget.snapshot(),
            memory=self.runtime.memory.stats(),
            skills=self.skills.stats(),
        )
        return outcome.to_dict()

    def _failure_semantics(
        self,
        step: dict,
        res: Optional[CommandResult],
    ) -> tuple[ExecutionStatus, str, str]:
        if self.state.budget_exceeded:
            return (
                ExecutionStatus.HALTED,
                "budget_exceeded",
                f"budget exceeded while executing '{step['tool']}'",
            )
        if self.state.escalated:
            if self._executed_commands:
                return (
                    ExecutionStatus.PARTIALLY_COMPLETED,
                    "needs_human_after_partial_execution",
                    "escalated to human after partial execution",
                )
            return (
                ExecutionStatus.NEEDS_HUMAN,
                "needs_human_approval",
                "escalated to human; awaiting decision",
            )
        if res is None:
            return (
                ExecutionStatus.HALTED,
                "budget_exceeded",
                "budget exceeded while executing step",
            )
        if res.verifier.code == "INPUT_CONTRACT_VIOLATION":
            status = (
                ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION
                if self._executed_commands else ExecutionStatus.REJECTED
            )
            return (
                status,
                "tool_contract_violation",
                f"tool input contract violation on '{step['tool']}': "
                f"{res.verifier.reason}",
            )
        if res.verifier.code == "OUTPUT_CONTRACT_VIOLATION":
            status = (
                ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION
                if self._executed_commands else ExecutionStatus.VERIFICATION_FAILED
            )
            return (
                status,
                "tool_contract_violation",
                f"tool output contract violation on '{step['tool']}': "
                f"{res.verifier.reason}",
            )
        if res.decision.verdict.value == "deny":
            if self._executed_commands:
                return (
                    ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION,
                    "policy_denied_after_partial_execution",
                    f"policy denied command '{step['tool']}' after partial execution",
                )
            return (
                ExecutionStatus.REJECTED,
                "policy_denied",
                f"policy denied command '{step['tool']}'",
            )
        if _is_sandbox_failure(res):
            status = (
                ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION
                if self._executed_commands else ExecutionStatus.FAILED
            )
            return (
                status,
                "sandbox_failure",
                f"sandbox execution failed on '{step['tool']}'",
            )
        if not res.verifier.passed:
            return (
                ExecutionStatus.VERIFICATION_FAILED,
                "verification_failed",
                f"verification failed on '{step['tool']}'",
            )
        status = (
            ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION
            if self._executed_commands else ExecutionStatus.FAILED
        )
        return status, "step_failed", f"step '{step['tool']}' failed"


def _risk(label: str) -> RiskLevel:
    try:
        return RiskLevel(label)
    except ValueError:
        return RiskLevel.LOW


def _skill_name(goal: str) -> str:
    return "_".join(goal.lower().split()[:4])


def _safe_list(runtime) -> list[str]:
    try:
        return runtime.tools.sandbox.list_dir(".")
    except Exception:
        return []


def _evidence_refs(commands: list[CommandEnvelope]) -> list[str]:
    return [c.id for c in commands]


def _is_sandbox_failure(res: CommandResult) -> bool:
    kind = (res.observation.artifacts or {}).get("error_kind", "")
    if kind == "sandbox_error":
        return True
    return "sandbox error" in (res.observation.stderr or "").lower()


def _verifier_hash(res: CommandResult) -> str:
    return sha(canonical_json(res.verifier.to_dict()))

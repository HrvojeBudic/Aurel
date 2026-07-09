"""
entity_loom_loop.py — F4.3 interactive ReAct loop over the ContextLoom.

An additive observe→think→act loop that drives actions through the real
``runtime.submit`` kernel while assembling its context each turn through the
ContextLoom (F4.0–4.2): every turn's context is provenance-labelled, taint-aware
(external items data-only), budget-fit, and trace-bound by a ``context_ref``.

It does NOT modify ``AgenticEntity`` — the existing single-shot planner path is
byte-identical. The loop is opt-in by construction (flag ``AUREL_ENTITY_LOOP``,
defined-not-gating) and takes an injectable ``Planner`` so it stays deterministic
under a cassette/stub and can be driven by a real router in production
(``RouterPlanner``).

  - **observe** — assemble operator intent + memory recall + prior tool
    observations into a governed ``ContextBundle``, bind its ``context_ref`` to
    the trace.
  - **think** — hand the bundle to the planner; it returns steps or ``done``.
  - **act** — submit each step through the governed kernel; fold each observation
    back in as an INTERNAL (trusted, governed-result) context item.

Termination is always bounded: ``done`` / no steps / no progress / budget /
``max_turns``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .budget import BudgetExceeded
from .context_loom import (
    ContextBundle,
    assemble,
    bind_context_to_trace,
    make_context_item,
)
from .core_types import AgentCard, CommandEnvelope, Intent, RiskLevel
from .external_ingress import SourceKind

_FLAG = "AUREL_ENTITY_LOOP"

_RISK = {
    "trivial": RiskLevel.TRIVIAL,
    "low": RiskLevel.LOW,
    "medium": RiskLevel.MEDIUM,
    "high": RiskLevel.HIGH,
    "critical": RiskLevel.CRITICAL,
}


def flag_enabled() -> bool:
    """True iff the interactive-loop flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class PlanTurn:
    """One planner decision: steps to act on, or ``done``."""

    steps: tuple[dict, ...] = ()
    done: bool = False


# A planner maps the assembled context + card to a decision.
Planner = Callable[[ContextBundle, AgentCard], PlanTurn]


@dataclass(frozen=True)
class LoopTurn:
    index: int
    context_ref: str
    steps_planned: int
    steps_executed: int
    observations: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "context_ref": self.context_ref,
            "steps_planned": self.steps_planned,
            "steps_executed": self.steps_executed,
            "observations": list(self.observations),
        }


@dataclass
class LoopResult:
    turns: tuple[LoopTurn, ...]
    context_refs: tuple[str, ...]
    executed: int
    terminated: str  # done | no_steps | no_progress | budget_exceeded | max_turns

    def to_dict(self) -> dict:
        return {
            "turns": [t.to_dict() for t in self.turns],
            "context_refs": list(self.context_refs),
            "executed": self.executed,
            "terminated": self.terminated,
        }


class EntityLoomLoop:
    """A ContextLoom-driven ReAct loop over one runtime + card + planner."""

    def __init__(
        self,
        runtime: Any,
        card: AgentCard,
        planner: Planner,
        *,
        max_context_tokens: Optional[int] = None,
        memory_k: int = 5,
    ) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self.card = card
        self.planner = planner
        self.max_context_tokens = max_context_tokens
        self.memory_k = memory_k
        self._observations: list = []  # accumulated INTERNAL context items

    # ----------------------------------------------------------------- #
    def _observe(self, intent: Intent) -> ContextBundle:
        items = [make_context_item(intent.text, SourceKind.OPERATOR, intent.id)]
        try:
            for rec in self._inner.memory.retrieve(intent.text, self.memory_k):
                items.append(
                    make_context_item(rec.content, SourceKind.INTERNAL, "memory")
                )
        except (AttributeError, TypeError):
            pass  # no memory retrieval available ⇒ intent-only context
        items.extend(self._observations)
        bundle = assemble(items, max_tokens=self.max_context_tokens, compress=True)
        bind_context_to_trace(
            self._inner.trace,
            run_id=self._inner.trace.run_id,
            agent_id=self.card.id,
            subject_id=intent.id,
            bundle=bundle,
        )
        return bundle

    def _act(self, intent: Intent, steps: tuple[dict, ...]) -> tuple[int, list[str], bool]:
        executed = 0
        summaries: list[str] = []
        for step in steps:
            cmd = CommandEnvelope.make(
                issuer_card_id=self.card.id,
                tool=step["tool"],
                args=dict(step.get("args", {}) or {}),
                rationale=step.get("rationale") or step.get("reason", "loop step"),
                declared_risk=_RISK.get(str(step.get("risk", "low")), RiskLevel.LOW),
                expected_effect=step.get("expected_effect", ""),
                parent_intent_id=intent.id,
            )
            try:
                res = self._inner.submit(cmd, self.card)
            except BudgetExceeded:
                return executed, summaries, True
            if res.ok:
                executed += 1
                summary = f"{step['tool']}: ok"
            else:
                reason = (res.verifier.reason if res.verifier else "") or "failed"
                summary = f"{step['tool']}: {reason}"[:120]
            summaries.append(summary)
            # Governed tool results are trusted-internal; fold back into context.
            self._observations.append(
                make_context_item(summary, SourceKind.INTERNAL, "tool_result")
            )
        return executed, summaries, False

    def run(self, intent: Intent, *, max_turns: int = 6) -> LoopResult:
        """Drive the loop, bounded by ``max_turns`` and always terminating."""
        turns: list[LoopTurn] = []
        refs: list[str] = []
        total = 0
        terminated = "max_turns"
        for i in range(max(1, max_turns)):
            bundle = self._observe(intent)
            refs.append(bundle.context_ref)
            decision = self.planner(bundle, self.card)
            if decision.done:
                turns.append(LoopTurn(i, bundle.context_ref, 0, 0, ()))
                terminated = "done"
                break
            if not decision.steps:
                turns.append(LoopTurn(i, bundle.context_ref, 0, 0, ()))
                terminated = "no_steps"
                break
            executed, summaries, budget_hit = self._act(intent, decision.steps)
            total += executed
            turns.append(
                LoopTurn(
                    i, bundle.context_ref, len(decision.steps), executed,
                    tuple(summaries),
                )
            )
            if budget_hit:
                terminated = "budget_exceeded"
                break
            if executed == 0:
                terminated = "no_progress"
                break
        return LoopResult(
            turns=tuple(turns),
            context_refs=tuple(refs),
            executed=total,
            terminated=terminated,
        )


@dataclass
class RouterPlanner:
    """Production planner: assemble → LLM (cassette by default) → validated steps.

    Reuses the router + PlanValidator exactly as ``AgenticEntity.plan`` does, but
    is fed the ContextLoom prompt (external items already fenced as data). Charges
    the budget when one is supplied, so LLM planning stays accounted.
    """

    router: Any
    plan_validator: Any
    system_prompt: str
    profile: str = "balanced"
    budget: Any = None
    _last_model: str = field(default="", init=False)

    def __call__(self, bundle: ContextBundle, card: AgentCard) -> PlanTurn:
        if self.budget is not None:
            self.budget.precheck_llm()
        raw, model, usage = self.router.complete_with_usage(
            self.profile, self.system_prompt, bundle.to_prompt()
        )
        self._last_model = model
        if self.budget is not None:
            self.budget.charge_llm(usage=usage)
        result = self.plan_validator.parse_and_validate(raw)
        if not result.valid or not result.steps:
            return PlanTurn(steps=(), done=True)
        return PlanTurn(steps=tuple(result.steps), done=False)

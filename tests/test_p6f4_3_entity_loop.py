"""F4.3 seal — interactive ReAct loop over the ContextLoom.

  1. Each turn assembles context via the ContextLoom and binds a context_ref to
     the trace; the loop's refs match a pure trace replay.
  2. Actions run through the governed runtime.submit; a successful step folds its
     observation back into the next turn's context as an INTERNAL item.
  3. Termination is always bounded: done / no_progress / max_turns.
  4. RouterPlanner wires router + PlanValidator (stub router → validated steps).
  5. Flag default OFF. entity.py is untouched (byte-identical single-shot path).
"""
from __future__ import annotations

import json

from agentic_runtime import build_runtime
from agentic_runtime.context_loom import context_refs_from_replay
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    Intent,
    RiskLevel,
)
from agentic_runtime.entity_loom_loop import (
    EntityLoomLoop,
    PlanTurn,
    RouterPlanner,
    flag_enabled,
)
from agentic_runtime.plan_validator import PlanValidator

LIST_STEP = {"tool": "list_dir", "args": {"path": "."}, "risk": "low"}


def _card():
    return AgentCard.make(
        name="loop-agent",
        agent_class=AgentClass.EXECUTION,
        mission="F4.3 loop seal",
        authority=AuthorityScope(read_paths=["."], max_risk=RiskLevel.MEDIUM),
        allowed_tools=["list_dir"],
    )


def _scripted(script):
    state = {"n": 0, "bundles": []}

    def planner(bundle, card):
        state["bundles"].append(bundle)
        i = state["n"]
        state["n"] += 1
        return script[i] if i < len(script) else PlanTurn(done=True)

    return planner, state


# --------------------------------------------------------------------------- #
# 1 + 2. Assemble → trace-bound refs; observation folds back.
# --------------------------------------------------------------------------- #
def test_loop_assembles_binds_and_folds_observation():
    rt = build_runtime()
    planner, state = _scripted([PlanTurn(steps=(LIST_STEP,)), PlanTurn(done=True)])
    loop = EntityLoomLoop(rt, _card(), planner)
    result = loop.run(Intent.make("list the workspace"), max_turns=5)

    assert result.terminated == "done"
    assert result.executed == 1
    assert len(result.context_refs) == 2
    # Refs are trace-bound and reconstructable from a pure replay.
    assert context_refs_from_replay(rt.runtime.trace.replay()) == list(result.context_refs)
    # Turn 0 context leads with the operator intent (instruction-eligible).
    assert state["bundles"][0].items[0].instruction_eligible is True
    # Turn 1 context folded in the tool observation as an INTERNAL item.
    assert any(i.origin_ref == "tool_result" for i in state["bundles"][1].items)


# --------------------------------------------------------------------------- #
# 3. Bounded termination.
# --------------------------------------------------------------------------- #
def test_terminates_done_immediately():
    rt = build_runtime()
    planner, _ = _scripted([PlanTurn(done=True)])
    result = EntityLoomLoop(rt, _card(), planner).run(Intent.make("x"), max_turns=4)
    assert result.terminated == "done"
    assert result.executed == 0
    assert len(result.context_refs) == 1


def test_no_progress_on_failing_step():
    rt = build_runtime()
    # An unregistered tool is contract-blocked (res.ok False) ⇒ executed 0.
    bad = {"tool": "frobnicate", "args": {}, "risk": "low"}
    planner, _ = _scripted([PlanTurn(steps=(bad,))])
    result = EntityLoomLoop(rt, _card(), planner).run(Intent.make("x"), max_turns=4)
    assert result.terminated == "no_progress"
    assert result.executed == 0


def test_max_turns_bound():
    rt = build_runtime()
    # Planner always returns an executing step ⇒ loop runs to max_turns.
    planner = lambda bundle, card: PlanTurn(steps=(LIST_STEP,))  # noqa: E731
    result = EntityLoomLoop(rt, _card(), planner).run(Intent.make("x"), max_turns=3)
    assert result.terminated == "max_turns"
    assert result.executed == 3
    assert len(result.context_refs) == 3


# --------------------------------------------------------------------------- #
# 4. RouterPlanner wiring.
# --------------------------------------------------------------------------- #
class _StubRouter:
    def __init__(self, raw):
        self._raw = raw

    def complete_with_usage(self, profile, system, user):
        return self._raw, "stub-model", None


def test_router_planner_validates_and_returns_steps():
    rt = build_runtime()
    validator = PlanValidator(registered_tools=rt.runtime.tools.registered)
    raw = json.dumps({"plan": [{"tool": "list_dir", "args": {"path": "."},
                                "reason": "look"}]})
    planner = RouterPlanner(_StubRouter(raw), validator, system_prompt="plan.")
    from agentic_runtime.context_loom import assemble, make_context_item
    from agentic_runtime.external_ingress import SourceKind

    bundle = assemble([make_context_item("goal", SourceKind.OPERATOR, "op")])
    turn = planner(bundle, _card())
    assert turn.done is False
    assert turn.steps and turn.steps[0]["tool"] == "list_dir"


def test_router_planner_done_on_invalid_plan():
    rt = build_runtime()
    validator = PlanValidator(registered_tools=rt.runtime.tools.registered)
    planner = RouterPlanner(_StubRouter("not json"), validator, system_prompt="p")
    from agentic_runtime.context_loom import assemble, make_context_item
    from agentic_runtime.external_ingress import SourceKind

    bundle = assemble([make_context_item("g", SourceKind.OPERATOR, "op")])
    assert planner(bundle, _card()).done is True


# --------------------------------------------------------------------------- #
# 5. Flag default OFF.
# --------------------------------------------------------------------------- #
def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_ENTITY_LOOP", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_ENTITY_LOOP", "1")
    assert flag_enabled() is True

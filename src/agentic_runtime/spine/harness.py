"""SPINE-LIVE-5 — end-to-end spine slice harness + honest seal.

Drives one real task through the whole living thread and aggregates the
evidence flags from every phase:

    cognition (S0)  -> model_call_available   (a real model call happened)
    flow     (S2)  -> execution_available    (every node really dispatched)
    exec     (S1)  -> (through the flow's submits, hard-isolation gated)
    trace    (S3)  -> trace_verified         (chain recomputed from disk)
    shell    (S4)  -> shell_binding_live      (operator view reads the trace)

``spine_live`` is True only when all four are True and the run completed. There
is no fake-hard sandbox here: if no real isolation boundary (Bubblewrap/Docker)
is available, the slice reports an honest UNAVAILABLE result — a valid governed
outcome, not a failure. Tests inject a hard sandbox to exercise the green path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core_types import AgentCard, AgentClass, AuthorityScope, RiskLevel, new_id
from ..governance.profile import GovernanceLevel, governed_approver, profile_for
from ..hitl import AutoApprover
from ..model_router import MockModelClient, ModelRouter
from .flow_dispatch import (
    FlowDispatcher,
    build_patch_test_graph,
    create_workflow_run,
)
from .live_evidence import ModelCallEvidenceRef
from .shell_run_view import build_shell_run_view
from .tool_exec import SpineExecutionBlocked, SpineToolExecSession
from .trace_verify import verify_persisted_trace

SPINE_SLICE_RESULT_VERSION = "spine_slice_result.v1"

_BUGGY_CALC = "VALUE = 1\n"
_FIXED_CALC = "VALUE = 2\n"
_CALC_TEST = "import calc, sys\nsys.exit(0 if calc.VALUE == 2 else 1)\n"

_PLANNER_SYSTEM = (
    "You are the planning core of a governed runtime. You do NOT act; you emit "
    "a JSON plan. To fix a bug, write the corrected file with write_file, then "
    "verify with run_tests. Each step needs: step_id, tool, args, risk, reason. "
    "Prefer the smallest safe change."
)
_DEFAULT_GOAL = (
    "Fix calc.py so that its test (test_calc.py) passes. calc.py currently "
    "defines VALUE = 1 but the test expects VALUE == 2. Use write_file to set "
    "calc.py to 'VALUE = 2\\n', then run_tests with test_file test_calc.py."
)


def _planner_user(goal: str) -> str:
    return f"GOAL: {goal}\n\nRespond with a single JSON plan object."

_NO_HARD_SANDBOX_REASON = (
    "no hard-isolated sandbox (Bubblewrap/Docker) available; mutating spine "
    "execution is fail-closed UNAVAILABLE — this is a valid governed outcome"
)

# A deterministic, validated plan for the fixed spine calc goal, aligned to the
# spine card's tool allowlist (write_file, run_tests). Emitted by the offline
# planner below so plan-driven mode has an honest, supported plan when no live
# model is attached — the alternative (the generic mock ``list_dir`` plan) is not
# in the spine card allowlist and fails the plan closed as ``unsupported_command``.
_SPINE_PLAN_JSON = json.dumps(
    {
        "intent_summary": "fix calc.py so its test passes",
        "plan": [
            {
                "step_id": "patch",
                "tool": "write_file",
                "args": {"path": "calc.py", "content": _FIXED_CALC},
                "risk": "medium",
                "reason": "set VALUE to 2",
                "expected_effect": "calc.py fixed",
            },
            {
                "step_id": "verify",
                "tool": "run_tests",
                "args": {"test_file": "test_calc.py"},
                "risk": "low",
                "reason": "confirm the fix",
                "expected_effect": "test passes",
            },
        ],
        "confidence": 0.9,
        "requires_approval": True,
        "assumptions": [],
        "refusal_reason": None,
    }
)


class _SpineOfflinePlanner:
    """Deterministic offline planner for the fixed spine calc goal.

    Stands in for a live model when plan-driven mode runs without one. It emits
    the validated ``write_file`` + ``run_tests`` plan that fixes calc.py, aligned
    to the spine card's tool allowlist. Honest: this is a local deterministic
    fixture (``DEV_FIXTURE`` cognition), not an external model call — the model
    evidence records it as such.
    """

    name = "spine-offline-planner"

    def complete(self, system: str, user: str) -> str:
        return _SPINE_PLAN_JSON


@dataclass(frozen=True)
class SpineSliceResult:
    """Aggregate outcome of the full spine thread. Evidence, not vibes."""

    contract_version: str
    scenario: str
    run_id: str
    trace_dir: str
    model_call_available: bool
    execution_available: bool
    trace_verified: bool
    shell_binding_live: bool
    dispatch_success: bool
    spine_live: bool
    unavailable_reason: str
    model_evidence: dict
    dispatch: dict | None
    trace_evidence: dict | None
    shell_view: dict | None
    goal: str = ""
    plan_driven: bool = False
    plan: dict | None = None

    def to_dict(self) -> dict:
        return {
            "contract_version": self.contract_version,
            "scenario": self.scenario,
            "run_id": self.run_id,
            "trace_dir": self.trace_dir,
            "goal": self.goal,
            "plan_driven": self.plan_driven,
            "model_call_available": self.model_call_available,
            "execution_available": self.execution_available,
            "trace_verified": self.trace_verified,
            "shell_binding_live": self.shell_binding_live,
            "dispatch_success": self.dispatch_success,
            "spine_live": self.spine_live,
            "unavailable_reason": self.unavailable_reason,
            "plan": self.plan,
            "model_evidence": self.model_evidence,
            "dispatch": self.dispatch,
            "trace_evidence": self.trace_evidence,
            "shell_view": self.shell_view,
        }


def _spine_card() -> AgentCard:
    return AgentCard.make(
        name="Spine Surgeon",
        agent_class=AgentClass.EXECUTION,
        mission="SPINE-LIVE end-to-end thread",
        authority=AuthorityScope(
            write_paths=["calc.py"], read_paths=["*"], max_risk=RiskLevel.HIGH
        ),
        allowed_tools=["read_file", "write_file", "run_tests"],
        model_profile="balanced",
    )


def _try_backend(backend: Any) -> Any | None:
    # ``is_available`` is now a functional probe (real sandboxed exec), so a
    # host where isolation is only nominally present no longer yields a backend.
    try:
        if backend.is_available():
            return backend.create()
    except Exception:
        return None
    return None


def _auto_hard_sandbox() -> Any | None:
    """Return a real hard-isolated backend if one is functionally available, else None.

    bwrap is preferred (cheap), docker is the fallback; both are gated on a
    functional probe so this returns None on a host that cannot actually
    isolate — an honest UNAVAILABLE rather than a backend that fails at dispatch.
    """
    from ..sandbox import BubblewrapSandbox, DockerSandbox

    return _try_backend(BubblewrapSandbox) or _try_backend(DockerSandbox)


def _sandbox_posture(sbx: Any) -> dict:
    """Honest, operator-visible posture of the sandbox actually in use."""
    mode = getattr(sbx, "mode", None)
    backend = getattr(mode, "value", None) or (
        str(mode) if mode is not None else type(sbx).__name__
    )
    return {
        "backend": backend,
        "hard_isolated": bool(getattr(sbx, "is_hard_isolated", False)),
        "security_boundary": bool(getattr(sbx, "is_security_boundary", False)),
    }


def resolve_replay_sandbox(*, allow_unsafe: bool = False) -> tuple[Any | None, dict]:
    """Resolve a replay sandbox factory *without* silent unsafe fallback.

    Returns ``(factory, posture)``:

    * A hard-isolated backend is functionally available → a factory for it and a
      ``LIVE`` posture.
    * None available and ``allow_unsafe`` is False → ``(None, posture)`` with
      ``truth_label='UNAVAILABLE'`` and a reason. The caller MUST fail closed and
      must not claim a live/verified/deterministic result.
    * None available and ``allow_unsafe`` is True → an explicit, dev-only opt-in:
      an ``UnsafeLocalSandbox`` factory with ``truth_label='UNSAFE'`` and
      ``security_boundary=False`` so the downgrade is visible, never silent.
    """
    hard = _auto_hard_sandbox()
    if hard is not None:
        posture = _sandbox_posture(hard)
        posture.update(truth_label="LIVE", reason="")
        return (lambda: _auto_hard_sandbox()), posture
    if allow_unsafe:
        from ..sandbox import UnsafeLocalSandbox

        posture = _sandbox_posture(UnsafeLocalSandbox())
        posture.update(
            truth_label="UNSAFE",
            reason=(
                "no hard-isolated sandbox available; replay ran on the UNSAFE "
                "local backend (explicit dev opt-in) — determinism is shown but "
                "this is NOT a security boundary"
            ),
        )
        return (lambda: UnsafeLocalSandbox()), posture
    return None, {
        "backend": "",
        "hard_isolated": False,
        "security_boundary": False,
        "truth_label": "UNAVAILABLE",
        "reason": _NO_HARD_SANDBOX_REASON,
    }


def unavailable_replay_report(posture: dict) -> dict:
    """Honest fail-closed replay report — makes no false determinism claim.

    No ``TRACE_VERIFIED``, no ``LIVE``, no deterministic success shape: the
    operator sees exactly why replay could not run.
    """
    return {
        "available": False,
        "deterministic": False,
        "outcomes_match": False,
        "cassette_size": 0,
        "original_state_hashes": [],
        "replay_state_hashes": [],
        "replay_used_network": False,
        "sandbox": posture,
        "truth_label": posture.get("truth_label", "UNAVAILABLE"),
        "unavailable_reason": posture.get("reason", _NO_HARD_SANDBOX_REASON),
    }


_DEEPSEEK_MODELS = {
    "pro": "deepseek-v4-pro",
    "flash": "deepseek-v4-flash",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek-v4-flash": "deepseek-v4-flash",
}


def build_deepseek_client(model: str = "deepseek-v4-pro") -> Any:
    """Build a live DeepSeek model client for the spine cognition leg.

    ``model`` accepts ``pro``/``flash`` shorthands or full ids. The provider
    reads ``DEEPSEEK_API_KEY`` from the environment; without it the call fails
    closed to a refusal (non-available evidence), never a fake plan.
    """
    from ..model_providers.base import ModelProviderConfig
    from ..model_providers.deepseek_provider import (
        DEEPSEEK_API_KEY_ENV,
        DEEPSEEK_DEFAULT_BASE_URL,
        DeepSeekProvider,
    )
    from ..model_router import ProviderModelClient

    model_id = _DEEPSEEK_MODELS.get(model, model)
    provider = DeepSeekProvider(
        ModelProviderConfig(
            provider_name="deepseek",
            model_name=model_id,
            api_key_env=DEEPSEEK_API_KEY_ENV,
            base_url=DEEPSEEK_DEFAULT_BASE_URL,
        )
    )
    return ProviderModelClient(provider)


def _model_leg(model_client: Any | None, goal: str) -> tuple[ModelCallEvidenceRef, str]:
    router = ModelRouter()
    router.register("balanced", [model_client or MockModelClient()])
    raw, _name, evidence = router.complete_with_evidence(
        "balanced", _PLANNER_SYSTEM, _planner_user(goal)
    )
    return evidence, raw


def run_spine_slice(
    *,
    trace_dir: str | Path,
    run_id: str | None = None,
    sandbox: Any | None = None,
    model_client: Any | None = None,
    scenario: str = "spine_buggy_calculator",
    goal: str = _DEFAULT_GOAL,
    plan_driven: bool = False,
    retry: bool = False,
) -> SpineSliceResult:
    """Run the full thread and aggregate every phase's evidence flag.

    With ``plan_driven=True`` the model's own validated plan is realized as the
    flow graph (the entity proposes the steps); otherwise a fixed patch/test
    graph is used and the model call is evidence-only.
    """
    from .. import build_runtime

    run_id = run_id or new_id("spine")
    # Plan-driven mode needs a plan whose tools are in the spine card allowlist.
    # With no live model attached, use the deterministic offline planner rather
    # than the generic mock (whose ``list_dir`` plan is unsupported here).
    planner = model_client
    if planner is None and plan_driven:
        planner = _SpineOfflinePlanner()
    model_evidence, model_raw = _model_leg(planner, goal)
    plan_dict: dict | None = None

    def _unavailable(reason: str) -> SpineSliceResult:
        return SpineSliceResult(
            contract_version=SPINE_SLICE_RESULT_VERSION,
            scenario=scenario,
            run_id=run_id,
            trace_dir=str(trace_dir),
            model_call_available=model_evidence.available,
            execution_available=False,
            trace_verified=False,
            shell_binding_live=False,
            dispatch_success=False,
            spine_live=False,
            unavailable_reason=reason,
            model_evidence=model_evidence.to_dict(),
            dispatch=None,
            trace_evidence=None,
            shell_view=None,
            goal=goal,
            plan_driven=plan_driven,
            plan=plan_dict,
        )

    sandbox = sandbox if sandbox is not None else _auto_hard_sandbox()
    if sandbox is None:
        return _unavailable(_NO_HARD_SANDBOX_REASON)

    kernel = build_runtime(
        sandbox=sandbox,
        trace_backend="persistent",
        trace_dir=str(trace_dir),
        trace_run_id=run_id,
        # M6 — the approver is materialized from a declared governance level, not
        # hand-rolled as fully-permissive. G4 (frontier) auto-approves the slice's
        # reversible writes and test runs while keeping the level auditable.
        approval_gate=governed_approver(profile_for(GovernanceLevel.G4)),
    )
    kernel.sandbox.write_file("calc.py", _BUGGY_CALC)
    kernel.sandbox.write_file("test_calc.py", _CALC_TEST)

    card = _spine_card()
    session = SpineToolExecSession(kernel.runtime, card)

    if plan_driven:
        from ..plan_validator import PlanValidator
        from .plan_flow import DEFAULT_PLAN_TOOL_ALLOWLIST, PlanRealizationError, plan_to_flow

        validator = PlanValidator(
            set(kernel.tools.registered), allowed_tools=list(card.allowed_tools)
        )
        parsed = validator.parse_and_validate(model_raw)
        if not parsed.valid or not parsed.steps:
            return _unavailable(
                f"model plan invalid or empty: {parsed.status.value}"
            )
        plan_dict = {"steps": parsed.steps, "status": parsed.status.value}
        allow = tuple(t for t in DEFAULT_PLAN_TOOL_ALLOWLIST if t in set(card.allowed_tools))
        try:
            graph, tasks = plan_to_flow(parsed.steps, allowed_tools=allow)
        except PlanRealizationError as e:
            return _unavailable(f"plan not realizable: {e}")
        ordered_steps = list(tasks.values())
    else:
        graph = build_patch_test_graph()
        tasks = {
            "patch": ("write_file", {"path": "calc.py", "content": _FIXED_CALC}),
            "test": ("run_tests", {"test_file": "test_calc.py"}),
        }
        ordered_steps = [tasks["patch"], tasks["test"]]

    run = create_workflow_run(graph)
    lease = session.issue_lease(ordered_steps)

    try:
        retry_policy = None
        if retry:
            from ..aurel_flow.recovery import DEFAULT_RETRY_POLICY
            retry_policy = DEFAULT_RETRY_POLICY
        dispatch = FlowDispatcher(session).dispatch(
            graph, run, tasks, lease, retry_policy=retry_policy
        )
    except SpineExecutionBlocked as e:
        return _unavailable(f"execution blocked: {e}")

    if hasattr(kernel.trace, "seal_run"):
        kernel.trace.seal_run("completed" if dispatch.success else "failed")

    trace_ev = verify_persisted_trace(trace_dir, run_id)
    shell_view = build_shell_run_view(trace_dir, run_id)

    spine_live = (
        model_evidence.available
        and dispatch.execution_available
        and trace_ev.trace_verified
        and shell_view.shell_binding_live
        and dispatch.success
    )
    return SpineSliceResult(
        contract_version=SPINE_SLICE_RESULT_VERSION,
        scenario=scenario,
        run_id=run_id,
        trace_dir=str(trace_dir),
        model_call_available=model_evidence.available,
        execution_available=dispatch.execution_available,
        trace_verified=trace_ev.trace_verified,
        shell_binding_live=shell_view.shell_binding_live,
        dispatch_success=dispatch.success,
        spine_live=spine_live,
        unavailable_reason="",
        model_evidence=model_evidence.to_dict(),
        dispatch=dispatch.to_dict(),
        trace_evidence=trace_ev.to_dict(),
        shell_view=shell_view.to_dict(),
        goal=goal,
        plan_driven=plan_driven,
        plan=plan_dict,
    )


# Tools whose post-state is a governed, reproducible mutation. Verification/exec
# tools (run_tests/run_shell) leave incidental, non-deterministic artifacts
# (e.g. __pycache__ with embedded temp paths), so their post-state is compared
# for outcome but not for byte-identical world-state — see docs/DEPLOYMENT.md.
_MUTATION_TOOLS = frozenset({"write_file", "patch_file", "edit_file", "delete_file"})


def _mutation_state_hashes(result: "SpineSliceResult") -> list[str]:
    """Ordered post-state hashes of governed *mutation* nodes only."""
    out: list[str] = []
    dispatch = result.to_dict().get("dispatch") or {}
    for step in dispatch.get("step_results", []):
        ev = step.get("exec_evidence") or {}
        if ev.get("tool") in _MUTATION_TOOLS:
            out.append(ev.get("after_state_hash", ""))
    return out


def _node_outcomes(result: "SpineSliceResult") -> list[bool]:
    dispatch = result.to_dict().get("dispatch") or {}
    return [bool(s.get("success")) for s in dispatch.get("step_results", [])]


def replay_spine_run(
    *,
    trace_dir: str | Path,
    sandbox_factory: Any,
    model_client: Any | None = None,
    goal: str = _DEFAULT_GOAL,
    plan_driven: bool = False,
) -> dict:
    """Record a run's model I/O, then replay it from the cassette — no network.

    Runs the slice once wrapping the model in a recording cassette, then a second
    time in a fresh trace dir with a fail-closed ``ReplayModelClient`` fed only by
    that cassette (no provider is contacted on replay). Determinism is asserted at
    the world-state-hash level: the ordered per-node ``after_state_hash`` list
    must match. ``sandbox_factory`` supplies a fresh sandbox per run.
    """
    from ..model_cassette import ModelCassette, RecordingModelClient, ReplayModelClient

    base = Path(trace_dir)
    cassette = ModelCassette(base / "cassette.jsonl")

    # Plan-driven replay needs a supported plan; use the offline planner when no
    # live model is attached (mirrors run_spine_slice's plan-driven default).
    inner = model_client
    if inner is None and plan_driven:
        inner = _SpineOfflinePlanner()
    record_client = RecordingModelClient(
        inner or MockModelClient(), cassette, model_id="spine-model"
    )
    # Introspect the real sandbox posture so the report never hides which backend
    # actually ran the replay.
    sbx_record = sandbox_factory()
    posture = _sandbox_posture(sbx_record)
    original = run_spine_slice(
        trace_dir=base / "record", run_id="replay-record", sandbox=sbx_record,
        model_client=record_client, goal=goal, plan_driven=plan_driven,
    )

    replay_client = ReplayModelClient(cassette, model_id="spine-model")
    replay = run_spine_slice(
        trace_dir=base / "replay", run_id="replay-run", sandbox=sandbox_factory(),
        model_client=replay_client, goal=goal, plan_driven=plan_driven,
    )

    original_hashes = _mutation_state_hashes(original)
    replay_hashes = _mutation_state_hashes(replay)
    outcomes_match = _node_outcomes(original) == _node_outcomes(replay)
    truth_label = posture.get("truth_label") or (
        "LIVE" if posture["security_boundary"] else "UNSAFE"
    )
    return {
        "available": True,
        # Deterministic = every governed mutation reproduced the same world-state
        # AND every node reached the same outcome, driving the model from the
        # cassette alone (no provider contacted on replay).
        "deterministic": (
            original_hashes == replay_hashes
            and bool(original_hashes)
            and outcomes_match
        ),
        "outcomes_match": outcomes_match,
        "cassette_size": len(cassette),
        "original_state_hashes": original_hashes,
        "replay_state_hashes": replay_hashes,
        "replay_used_network": False,
        "sandbox": posture,
        "truth_label": truth_label,
        "original_unavailable_reason": original.unavailable_reason,
        "replay_unavailable_reason": replay.unavailable_reason,
    }


__all__ = [
    "SPINE_SLICE_RESULT_VERSION",
    "SpineSliceResult",
    "run_spine_slice",
    "replay_spine_run",
    "resolve_replay_sandbox",
    "unavailable_replay_report",
    "build_deepseek_client",
]

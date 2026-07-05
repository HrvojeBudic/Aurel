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

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core_types import AgentCard, AgentClass, AuthorityScope, RiskLevel, new_id
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
    "You are the planning core of a governed runtime. Emit a JSON plan; you do "
    "not act."
)
_PLANNER_USER = "GOAL: fix buggy_calculator so its test passes\n"

_NO_HARD_SANDBOX_REASON = (
    "no hard-isolated sandbox (Bubblewrap/Docker) available; mutating spine "
    "execution is fail-closed UNAVAILABLE — this is a valid governed outcome"
)


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

    def to_dict(self) -> dict:
        return {
            "contract_version": self.contract_version,
            "scenario": self.scenario,
            "run_id": self.run_id,
            "trace_dir": self.trace_dir,
            "model_call_available": self.model_call_available,
            "execution_available": self.execution_available,
            "trace_verified": self.trace_verified,
            "shell_binding_live": self.shell_binding_live,
            "dispatch_success": self.dispatch_success,
            "spine_live": self.spine_live,
            "unavailable_reason": self.unavailable_reason,
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
    try:
        if backend.is_available():
            return backend.create()
    except Exception:
        return None
    return None


def _auto_hard_sandbox() -> Any | None:
    """Return a real hard-isolated backend if one is available, else None."""
    from ..sandbox import BubblewrapSandbox, DockerSandbox

    return _try_backend(BubblewrapSandbox) or _try_backend(DockerSandbox)


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


def _model_leg(model_client: Any | None) -> ModelCallEvidenceRef:
    router = ModelRouter()
    router.register("balanced", [model_client or MockModelClient()])
    _raw, _name, evidence = router.complete_with_evidence(
        "balanced", _PLANNER_SYSTEM, _PLANNER_USER
    )
    return evidence


def run_spine_slice(
    *,
    trace_dir: str | Path,
    run_id: str | None = None,
    sandbox: Any | None = None,
    model_client: Any | None = None,
    scenario: str = "spine_buggy_calculator",
) -> SpineSliceResult:
    """Run the full thread and aggregate every phase's evidence flag."""
    from .. import build_runtime

    run_id = run_id or new_id("spine")
    model_evidence = _model_leg(model_client)

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
        )

    sandbox = sandbox if sandbox is not None else _auto_hard_sandbox()
    if sandbox is None:
        return _unavailable(_NO_HARD_SANDBOX_REASON)

    kernel = build_runtime(
        sandbox=sandbox,
        trace_backend="persistent",
        trace_dir=str(trace_dir),
        trace_run_id=run_id,
        approval_gate=AutoApprover(
            lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
        ),
    )
    kernel.sandbox.write_file("calc.py", _BUGGY_CALC)
    kernel.sandbox.write_file("test_calc.py", _CALC_TEST)

    session = SpineToolExecSession(kernel.runtime, _spine_card())
    graph = build_patch_test_graph()
    run = create_workflow_run(graph)
    tasks = {
        "patch": ("write_file", {"path": "calc.py", "content": _FIXED_CALC}),
        "test": ("run_tests", {"test_file": "test_calc.py"}),
    }
    lease = session.issue_lease([tasks["patch"], tasks["test"]])

    try:
        dispatch = FlowDispatcher(session).dispatch(graph, run, tasks, lease)
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
    )


__all__ = [
    "SPINE_SLICE_RESULT_VERSION",
    "SpineSliceResult",
    "run_spine_slice",
    "build_deepseek_client",
]

"""SPINE-LIVE-4 tests — Shell live run view read model + CLI binding."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from agentic_runtime import AutoApprover, UnsafeLocalSandbox, build_runtime
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
)
from agentic_runtime.spine import (
    FlowDispatcher,
    SpineToolExecSession,
    build_patch_test_graph,
    build_shell_run_view,
    create_workflow_run,
)

_ORIGINAL = "VALUE = 1\n"
_PATCHED = "VALUE = 2\n"
_PASS = {"command": ["python3", "-c", "import sys; sys.exit(0)"]}
_RUN_ID = "spine-s4-run"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src"


class _FakeHardSandbox(UnsafeLocalSandbox):
    def __init__(self, root: str | None = None) -> None:
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


def _card() -> AgentCard:
    return AgentCard.make(
        name="Spine Shell",
        agent_class=AgentClass.EXECUTION,
        mission="SPINE-LIVE shell run view",
        authority=AuthorityScope(
            write_paths=["calc.py"], read_paths=["*"], max_risk=RiskLevel.HIGH
        ),
        allowed_tools=["read_file", "write_file", "run_tests"],
        model_profile="balanced",
    )


def _run_persistent_slice(trace_dir: Path):
    kernel = build_runtime(
        sandbox=_FakeHardSandbox(),
        trace_backend="persistent",
        trace_dir=str(trace_dir),
        trace_run_id=_RUN_ID,
        approval_gate=AutoApprover(
            lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
        ),
    )
    kernel.sandbox.write_file("calc.py", _ORIGINAL)
    session = SpineToolExecSession(kernel.runtime, _card())
    graph = build_patch_test_graph()
    run = create_workflow_run(graph)
    tasks = {
        "patch": ("write_file", {"path": "calc.py", "content": _PATCHED}),
        "test": ("run_tests", _PASS),
    }
    lease = session.issue_lease([tasks["patch"], tasks["test"]])
    FlowDispatcher(session).dispatch(graph, run, tasks, lease)


def test_run_view_is_live_after_a_run(tmp_path):
    _run_persistent_slice(tmp_path)
    view = build_shell_run_view(tmp_path, _RUN_ID)
    assert view.shell_binding_live is True
    assert view.truth_label == "LIVE"
    assert view.trace_verified is True
    assert view.event_count > 0
    assert view.head_hash
    assert len(view.transitions) == view.event_count
    assert any(t["event_type"] == "state_transition" for t in view.transitions)


def test_run_view_unavailable_without_a_run(tmp_path):
    view = build_shell_run_view(tmp_path, "no-such-run")
    assert view.shell_binding_live is False
    assert view.truth_label == "UNAVAILABLE"
    assert view.trace_verified is False
    assert view.event_count == 0
    assert view.unavailable_reason


def test_cli_shell_run_view_binding(tmp_path):
    _run_persistent_slice(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(_SRC), str(_REPO_ROOT)])
    proc = subprocess.run(
        [
            sys.executable, "-m", "agentic_runtime.cli", "shell", "run-view",
            _RUN_ID, "--trace-dir", str(tmp_path), "--json",
        ],
        capture_output=True, text=True, env=env, cwd=str(_REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["run_id"] == _RUN_ID
    assert payload["shell_binding_live"] is True
    assert payload["trace_verified"] is True
    assert payload["truth_label"] == "LIVE"


def test_cli_shell_run_view_unavailable_exit_code(tmp_path):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(_SRC), str(_REPO_ROOT)])
    proc = subprocess.run(
        [
            sys.executable, "-m", "agentic_runtime.cli", "shell", "run-view",
            "no-such-run", "--trace-dir", str(tmp_path), "--json",
        ],
        capture_output=True, text=True, env=env, cwd=str(_REPO_ROOT),
    )
    # honest UNAVAILABLE → non-zero exit, still valid JSON
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["shell_binding_live"] is False
    assert payload["truth_label"] == "UNAVAILABLE"

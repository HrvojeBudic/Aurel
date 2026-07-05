"""SPINE-LIVE-5 tests — the whole living thread, proven live like P0."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from agentic_runtime import UnsafeLocalSandbox
from agentic_runtime.spine import run_spine_slice

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src"


class _FakeHardSandbox(UnsafeLocalSandbox):
    """Stands in for a real Bubblewrap/Docker boundary in CI."""

    def __init__(self, root: str | None = None) -> None:
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


def test_full_thread_is_live_with_mock_model(tmp_path):
    result = run_spine_slice(
        trace_dir=tmp_path,
        run_id="spine-e2e",
        sandbox=_FakeHardSandbox(),
    )
    # every phase's evidence flag is True → the thread is live
    assert result.model_call_available is True
    assert result.execution_available is True
    assert result.trace_verified is True
    assert result.shell_binding_live is True
    assert result.dispatch_success is True
    assert result.spine_live is True
    assert result.unavailable_reason == ""
    # each flag is backed by a concrete ref
    assert result.model_evidence["available"] is True
    assert result.trace_evidence["trace_verified"] is True
    assert result.shell_view["shell_binding_live"] is True
    # the governed patch really landed and the test really passed
    assert any(
        s["node_id"] == "test" and s["success"] for s in result.dispatch["step_results"]
    )


def test_no_hard_sandbox_is_honest_unavailable(tmp_path):
    # unsafe sandbox → the S1 gate fail-closes; the slice reports UNAVAILABLE,
    # a valid governed outcome, not a crash
    result = run_spine_slice(
        trace_dir=tmp_path,
        run_id="spine-e2e-unsafe",
        sandbox=UnsafeLocalSandbox(),
    )
    assert result.spine_live is False
    assert result.execution_available is False
    assert result.unavailable_reason
    # cognition still happened honestly even though execution was blocked
    assert result.model_call_available is True


def test_result_is_deterministic_shape(tmp_path):
    a = run_spine_slice(trace_dir=tmp_path / "a", run_id="r1", sandbox=_FakeHardSandbox())
    b = run_spine_slice(trace_dir=tmp_path / "b", run_id="r2", sandbox=_FakeHardSandbox())
    assert set(a.to_dict().keys()) == set(b.to_dict().keys())
    assert a.spine_live is True and b.spine_live is True


def test_cli_spine_run_is_honest_end_to_end(tmp_path):
    # The CLI drives the real slice with whatever sandbox this host provides.
    # Its verdict is environment-honest: green only with a real isolation
    # boundary that can also run the test; otherwise a truthful non-live result.
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(_SRC), str(_REPO_ROOT)])
    proc = subprocess.run(
        [
            sys.executable, "-m", "agentic_runtime.cli", "spine", "run",
            "--trace-dir", str(tmp_path), "--run-id", "cli-spine", "--json",
        ],
        capture_output=True, text=True, env=env, cwd=str(_REPO_ROOT),
    )
    payload = json.loads(proc.stdout)
    assert payload["scenario"] == "spine_buggy_calculator"
    # cognition always happens; the model call is evidenced regardless of sandbox
    assert payload["model_call_available"] is True
    # exit code faithfully mirrors the live verdict
    assert proc.returncode == (0 if payload["spine_live"] else 1)
    if payload["spine_live"]:
        assert payload["trace_verified"] is True
        assert payload["shell_binding_live"] is True
    else:
        # a non-live result is honest: either blocked (no isolation) or a
        # governed node failed inside the sandbox
        assert payload["unavailable_reason"] or payload["dispatch_success"] is False

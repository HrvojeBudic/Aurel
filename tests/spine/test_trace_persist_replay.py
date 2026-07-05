"""SPINE-LIVE-3 tests — persistent trace + independent replay verifier."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_runtime import AutoApprover, UnsafeLocalSandbox, build_runtime
from agentic_runtime.aurel_flow.workflow_state import WorkflowLifecycleStatus
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
)
from agentic_runtime.spine import (
    FlowDispatcher,
    SpineToolExecSession,
    TraceVerifiedLabel,
    build_patch_test_graph,
    create_workflow_run,
    replay_persisted_trace,
    verify_persisted_trace,
)

_ORIGINAL = "VALUE = 1\n"
_PATCHED = "VALUE = 2\n"
_PASS = {"command": ["python3", "-c", "import sys; sys.exit(0)"]}
_RUN_ID = "spine-s3-run"


class _FakeHardSandbox(UnsafeLocalSandbox):
    def __init__(self, root: str | None = None) -> None:
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


def _card() -> AgentCard:
    return AgentCard.make(
        name="Spine Trace",
        agent_class=AgentClass.EXECUTION,
        mission="SPINE-LIVE trace persistence",
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
    result = FlowDispatcher(session).dispatch(graph, run, tasks, lease)
    return kernel, result


def test_persisted_trace_verifies_from_disk(tmp_path):
    kernel, result = _run_persistent_slice(tmp_path)
    assert result.lifecycle_status is WorkflowLifecycleStatus.COMPLETED

    # events actually landed on disk
    events_file = tmp_path / "runs" / _RUN_ID / "events.jsonl"
    assert events_file.exists()
    assert events_file.read_text(encoding="utf-8").strip()

    # independent verifier recomputes the chain from disk bytes
    ev = verify_persisted_trace(tmp_path, _RUN_ID)
    assert ev.label is TraceVerifiedLabel.VERIFIED
    assert ev.trace_verified is True
    assert ev.event_count > 0
    assert ev.recomputed_head_hash == ev.persisted_head_hash
    assert ev.recomputed_head_hash == kernel.trace.head


def test_tampered_event_fails_closed(tmp_path):
    _run_persistent_slice(tmp_path)
    events_file = tmp_path / "runs" / _RUN_ID / "events.jsonl"
    lines = events_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2

    # tamper the first event's payload without fixing its stored entry_hash
    first = json.loads(lines[0])
    first["x_tamper"] = "injected"
    lines[0] = json.dumps(first)
    events_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ev = verify_persisted_trace(tmp_path, _RUN_ID)
    assert ev.label is TraceVerifiedLabel.TAMPERED
    assert ev.trace_verified is False
    assert "index 0" in ev.reason


def test_verify_unavailable_when_no_trace(tmp_path):
    ev = verify_persisted_trace(tmp_path, "no-such-run")
    assert ev.label is TraceVerifiedLabel.UNAVAILABLE
    assert ev.trace_verified is False


def test_replay_is_deterministic_and_nonempty(tmp_path):
    _run_persistent_slice(tmp_path)
    a = replay_persisted_trace(tmp_path, _RUN_ID)
    b = replay_persisted_trace(tmp_path, _RUN_ID)
    assert a == b
    assert len(a) > 0
    # sequence numbers are contiguous from 1
    assert [row["sequence"] for row in a] == list(range(1, len(a) + 1))
    # a real state transition (the governed write) is present
    assert any(row["event_type"] == "state_transition" for row in a)


def test_trace_verified_grants_no_authority(tmp_path):
    _run_persistent_slice(tmp_path)
    ev = verify_persisted_trace(tmp_path, _RUN_ID)
    assert ev.authority_granted is False
    assert ev.permission_granted is False

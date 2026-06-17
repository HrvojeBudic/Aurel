"""P0.6 persistent trace ledger tests."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    Intent,
    PersistentTraceLedger,
    RiskLevel,
    build_runtime,
)
from tests.conftest import bounded_test_approver
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import make_cmd


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _last_event(events: list[dict], event_type: str) -> dict:
    return next(e for e in reversed(events) if e.get("event_type") == event_type)


def _card(**kw):
    defaults = dict(
        name="Persistent Trace Agent",
        agent_class=AgentClass.EXECUTION,
        mission="persist trace evidence",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "edit_file", "run_tests", "run_shell", "list_dir"],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def _persistent_kernel(tmp_path, *, scripted=None):
    model_clients = None
    if scripted is not None:
        model_clients = {"balanced": [MockModelClient(scripted=scripted)]}
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "workspace")),
        model_clients=model_clients,
        approval_gate=bounded_test_approver(
            lambda r: r.command.tool in ("run_tests", "run_shell", "write_file", "edit_file"),
            allow_r4=True,
        ),
        trace_backend="persistent",
        trace_dir=str(tmp_path / ".traces"),
        trace_checkpoint_every=2,
    )


def test_persistent_trace_writes_jsonl(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card()
    cmd = make_cmd(card, "write_file", {"path": "src/a.py", "content": "print('ok')\n"})
    res = kernel.runtime.submit(cmd, card)
    assert res.transition is not None

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    assert (run_dir / "events.jsonl").exists()
    assert (run_dir / "checkpoints.jsonl").exists()
    assert (run_dir / "metadata.json").exists()

    events = _read_jsonl(run_dir / "events.jsonl")
    event = next(e for e in events if e["event_type"] == "state_transition")
    assert event["event_id"]
    assert event["run_id"] == kernel.trace.run_id
    assert event["event_type"] == "state_transition"
    assert "prev_entry_hash" in event
    assert "entry_hash" in event


def test_trace_survives_reload(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card()
    kernel.runtime.submit(make_cmd(card, "write_file", {"path": "src/a.py", "content": "x\n"}), card)
    kernel.runtime.submit(make_cmd(card, "edit_file", {"path": "src/a.py", "find": "x", "replace": "y"}), card)

    run_id = kernel.trace.run_id
    reloaded = PersistentTraceLedger(
        base_dir=str(tmp_path / ".traces"),
        run_id=run_id,
        checkpoint_every=2,
    )
    assert len(reloaded) == len(kernel.trace)
    assert reloaded.verify_chain()[0]


def test_valid_trace_verifies(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card()
    kernel.runtime.submit(make_cmd(card, "write_file", {"path": "src/a.py", "content": "x\n"}), card)
    kernel.runtime.submit(make_cmd(card, "edit_file", {"path": "src/a.py", "find": "x", "replace": "z"}), card)
    kernel.trace.seal_run("completed")

    ok, _ = kernel.trace.verify_chain()
    assert ok
    summary = kernel.trace.verify_persisted()
    assert summary["ok"]


def test_modified_event_fails_verification(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card()
    kernel.runtime.submit(make_cmd(card, "write_file", {"path": "src/a.py", "content": "x\n"}), card)
    kernel.trace.seal_run("completed")

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    events_path = run_dir / "events.jsonl"
    events = _read_jsonl(events_path)
    idx = next(i for i, e in enumerate(events) if e.get("event_type") == "state_transition")
    events[idx]["payload"]["after_state_hash"] = "forged_after_hash"
    events_path.write_text("\n".join(json.dumps(e, sort_keys=True) for e in events) + "\n", encoding="utf-8")

    ok, _ = kernel.trace.verify_chain()
    assert not ok


def test_deleted_event_fails_verification(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card()
    kernel.runtime.submit(make_cmd(card, "write_file", {"path": "src/a.py", "content": "x\n"}), card)
    kernel.runtime.submit(make_cmd(card, "edit_file", {"path": "src/a.py", "find": "x", "replace": "y"}), card)
    kernel.trace.seal_run("completed")

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    events_path = run_dir / "events.jsonl"
    events = _read_jsonl(events_path)
    events_path.write_text(json.dumps(events[1], sort_keys=True) + "\n", encoding="utf-8")

    ok, _ = kernel.trace.verify_chain()
    assert not ok


def test_reordered_event_fails_verification(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card()
    kernel.runtime.submit(make_cmd(card, "write_file", {"path": "src/a.py", "content": "x\n"}), card)
    kernel.runtime.submit(make_cmd(card, "edit_file", {"path": "src/a.py", "find": "x", "replace": "y"}), card)
    kernel.trace.seal_run("completed")

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    events_path = run_dir / "events.jsonl"
    events = _read_jsonl(events_path)
    a = events[0]
    b = events[1]
    events_path.write_text(
        "\n".join(json.dumps(e, sort_keys=True) for e in [b, a]) + "\n",
        encoding="utf-8",
    )

    ok, _ = kernel.trace.verify_chain()
    assert not ok


def test_receipt_final_hash_matches_chain_hash(tmp_path):
    goal = "persist trace receipt"
    plan = {
        "plan": [
            {
                "tool": "write_file",
                "args": {"path": "src/a.py", "content": "x\n"},
                "reason": "create source file",
            }
        ]
    }
    kernel = _persistent_kernel(tmp_path, scripted={goal: json.dumps(plan)})
    card = _card()
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == "completed"

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["final_chain_hash"] == kernel.trace.head
    assert receipt["event_count"] == len(kernel.trace)
    assert receipt["final_status"] == "completed"


def test_planning_failure_is_persisted(tmp_path):
    goal = "empty plan"
    kernel = _persistent_kernel(tmp_path, scripted={goal: json.dumps({"plan": []})})
    card = _card(allowed_tools=["read_file", "list_dir"])
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == "halted"
    assert report["planning_status"] == "empty_plan"

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    events = _read_jsonl(run_dir / "events.jsonl")
    assert any(e["event_type"] == "planning_failure" for e in events)


def test_policy_denial_is_persisted(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card(authority=AuthorityScope(write_paths=["src/"], max_risk=RiskLevel.HIGH))
    cmd = make_cmd(card, "edit_file", {"path": "/etc/passwd", "find": "a", "replace": "b"})
    res = kernel.runtime.submit(cmd, card)
    assert res.decision.verdict.value == "deny"
    assert res.transition is not None

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    last = _last_event(_read_jsonl(run_dir / "events.jsonl"), "state_transition")
    assert last["event_type"] == "state_transition"
    assert last["payload"]["policy_verdict"] == "deny"


def test_verifier_failure_is_persisted(tmp_path):
    kernel = _persistent_kernel(tmp_path)
    card = _card(authority=AuthorityScope(write_paths=["."], max_risk=RiskLevel.HIGH))
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "run_shell", {"cmd": ["python3", "-c", "open('test_x.py','w').write('x')"]})
    res = kernel.runtime.submit(cmd, card)
    assert not res.verifier.passed
    assert res.transition is not None

    run_dir = Path(tmp_path / ".traces" / "runs" / kernel.trace.run_id)
    last = _last_event(_read_jsonl(run_dir / "events.jsonl"), "state_transition")
    assert last["event_type"] == "state_transition"
    assert not last["payload"]["verifier_result"]["passed"]

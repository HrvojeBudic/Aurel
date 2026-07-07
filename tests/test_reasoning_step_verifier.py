"""Track B, B5 — deterministic PRM step verifier (advisory, never truth)."""
from __future__ import annotations

from agentic_runtime.reasoning import model_judge_available, score_steps


def _step(tool="write_file", args=None, reason="do it"):
    return {"tool": tool,
            "args": args if args is not None else {"path": "src/a.py", "content": "a\n"},
            "reason": reason}


def test_clean_single_step_does_not_escalate():
    ps = score_steps([_step()])
    assert ps.min_score == 1.0
    assert ps.should_escalate is False


def test_missing_tool_scores_low_and_escalates():
    ps = score_steps([{"args": {"path": "x"}, "reason": "r"}])
    assert ps.min_score < 0.5
    assert ps.should_escalate is True
    assert "missing_tool" in ps.scores[0].issues


def test_duplicate_steps_escalate():
    s = _step()
    assert score_steps([s, dict(s)]).should_escalate is True


def test_too_many_steps_escalate():
    ps = score_steps([_step(args={"path": f"src/f{i}.py", "content": "x"}) for i in range(9)])
    assert ps.should_escalate is True


def test_empty_plan_does_not_escalate():
    ps = score_steps([])
    assert ps.should_escalate is False
    assert ps.mean_score == 1.0


def test_vague_reason_penalized_but_not_escalating_alone():
    ps = score_steps([_step(reason="")])
    assert ps.scores[0].score < 1.0
    assert ps.should_escalate is False   # 0.9 ≥ threshold


def test_model_judge_is_structurally_unavailable():
    assert model_judge_available() is False
    ps = score_steps([_step()])
    summary = ps.to_summary()
    assert summary["advisory"] is True
    assert summary["model_judge_available"] is False
    # the PRM output is advisory only — it is not a truth verdict
    assert not hasattr(ps, "verified")
    assert not hasattr(ps, "truth")


def test_is_deterministic():
    steps = [_step(), _step(args={"path": "src/b.py", "content": "b"})]
    a, b = score_steps(steps), score_steps(steps)
    assert a.min_score == b.min_score and a.mean_score == b.mean_score

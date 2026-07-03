"""P4-EXEC-D ModeCompatibilityDecision tests — deterministic, no fallback."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecQueueState,
    ExecutionMode,
    build_default_execution_mode_registry,
    build_default_tool_execution_profile,
    create_queue_entry,
    decide_mode_compatibility,
    enforce_mode_compatibility_before_claim,
    require_mode_compatibility,
)
from tests.aurel_exec._bridge_helpers import build_bound_slice

_REGISTRY = build_default_execution_mode_registry()
_TOOL_PROFILE = build_default_tool_execution_profile()


def _tool_decision(**overrides):
    _, _, job, lease, _, _ = build_bound_slice()
    values = dict(
        exec_job_id=job.exec_job_id,
        tool_profile=_TOOL_PROFILE,
        requested_tool_name="read_file",
        lease=lease,
    )
    values.update(overrides)
    return decide_mode_compatibility(_REGISTRY, ExecutionMode.TOOL, **values), job, lease


def test_tool_mode_allowed_only_with_matching_context():
    decision, job, lease = _tool_decision()
    assert decision.allowed is True
    assert decision.blocked is False
    assert "allowed is not runtime success" in decision.reason
    # same inputs, same decision
    again, _, _ = _tool_decision(exec_job_id=job.exec_job_id, lease=lease)
    assert again.decision_id == decision.decision_id


def test_tool_mode_blocked_on_tool_or_scope_mismatch():
    wrong_tool, _, _ = _tool_decision(requested_tool_name="write_file")
    assert wrong_tool.blocked is True
    assert any("write_file" in miss for miss in wrong_tool.missing_requirements)
    missing_profile, _, _ = _tool_decision(tool_profile=None)
    assert missing_profile.blocked is True
    assert "tool_profile" in missing_profile.missing_requirements


def test_mode_compatibility_blocks_unsupported_modes():
    for mode in (
        ExecutionMode.MODEL,
        ExecutionMode.TERMINAL,
        ExecutionMode.CODE,
        ExecutionMode.CONVERSATION,
        ExecutionMode.COMPOSITE,
        ExecutionMode.UNAVAILABLE,
        ExecutionMode.ERROR,
    ):
        decision = decide_mode_compatibility(_REGISTRY, mode)
        assert decision.allowed is False
        assert decision.blocked is True
        assert decision.reason.strip()


def test_mode_compatibility_has_no_silent_fallback():
    decision = decide_mode_compatibility(_REGISTRY, ExecutionMode.TERMINAL)
    assert decision.blocked is True
    assert decision.fallback_mode is None
    assert decision.silent_fallback_used is False
    # a decision carrying a fallback is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(decision, fallback_mode="TOOL")
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(decision, silent_fallback_used=True)
    # allowed/blocked are exclusive and exhaustive
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(decision, allowed=True)


def test_unknown_mode_string_is_blocked():
    decision = decide_mode_compatibility(_REGISTRY, "quantum_mind_meld")
    assert decision.blocked is True
    assert "closed-world" in decision.reason


def test_enforce_hook_blocks_queue_entry_without_rewriting_c():
    _, _, job, lease, _, _ = build_bound_slice()
    entry = create_queue_entry(job, lease, current_tick=4)
    blocked_decision = decide_mode_compatibility(_REGISTRY, ExecutionMode.TERMINAL,
                                                 exec_job_id=job.exec_job_id)
    blocked_entry = enforce_mode_compatibility_before_claim(blocked_decision, entry)
    assert blocked_entry.queue_state is ExecQueueState.BLOCKED
    allowed_decision, _, _ = _tool_decision()
    entry2 = create_queue_entry(job, lease, current_tick=5)
    untouched = enforce_mode_compatibility_before_claim(allowed_decision, entry2)
    assert untouched is entry2  # allowed decision changes nothing


def test_require_mode_compatibility_raises_fail_closed():
    blocked = decide_mode_compatibility(_REGISTRY, ExecutionMode.CODE)
    with pytest.raises(AurelExecValidationError) as excinfo:
        require_mode_compatibility(blocked)
    assert excinfo.value.code is AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE
    allowed, _, _ = _tool_decision()
    require_mode_compatibility(allowed)  # does not raise

"""P4-EXEC-D ModeProjection tests — honest mode visibility, no control."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecutionMode,
    build_default_execution_mode_registry,
    build_default_tool_execution_profile,
    build_mode_projection,
    decide_mode_compatibility,
)
from tests.aurel_exec._bridge_helpers import build_bound_slice

_REGISTRY = build_default_execution_mode_registry()


def test_mode_projection_reports_available_profile_only_unavailable_and_blocked_modes():
    projection = build_mode_projection(_REGISTRY)
    assert projection.supported_modes == ("TOOL",)
    assert projection.profile_only_modes == ("MODEL",)
    assert set(projection.unavailable_modes) == {
        "TERMINAL",
        "CODE",
        "CONVERSATION",
        "COMPOSITE",
    }
    assert set(projection.blocked_modes) == {"UNAVAILABLE", "ERROR"}
    assert projection.tool_profile_status == "AVAILABLE_FOR_EXISTING_BRIDGE"
    assert projection.model_profile_status == "PROFILE_ONLY"
    assert projection.terminal_profile_status == "UNAVAILABLE"
    assert projection.code_profile_status == "UNAVAILABLE"


def test_projection_shows_allowed_tool_decision():
    _, _, job, lease, _, _ = build_bound_slice()
    decision = decide_mode_compatibility(
        _REGISTRY,
        ExecutionMode.TOOL,
        exec_job_id=job.exec_job_id,
        tool_profile=build_default_tool_execution_profile(),
        requested_tool_name="read_file",
        lease=lease,
    )
    projection = build_mode_projection(_REGISTRY, decision=decision)
    assert projection.requested_execution_mode == "TOOL"
    assert projection.mode_available is True
    assert projection.mode_blocked_reason is None


def test_projection_shows_blocked_decision_with_reason():
    decision = decide_mode_compatibility(_REGISTRY, ExecutionMode.TERMINAL)
    projection = build_mode_projection(_REGISTRY, decision=decision)
    assert projection.requested_execution_mode == "TERMINAL"
    assert projection.mode_available is False
    assert projection.mode_blocked_reason
    assert "UNAVAILABLE" in projection.mode_blocked_reason


def test_projection_risky_claims_are_unconstructible():
    projection = build_mode_projection(_REGISTRY)
    for boundary_field in (
        "silent_fallback_allowed",
        "direct_dispatch_allowed",
        "model_call_allowed",
        "terminal_execution_available",
        "shell_allowed",
        "subprocess_allowed",
        "code_execution_available",
        "eval_allowed",
        "script_execution_allowed",
        "new_sandbox_execution_available",
        "network_execution_available",
        "p5_trace_verification_available",
        "p9_full_enforcement_available",
        "shell_ui_available",
        "react_frontend_available",
        "api_server_available",
    ):
        assert getattr(projection, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, read_only=False)


def test_projection_cannot_claim_availability_for_unsupported_mode():
    decision = decide_mode_compatibility(_REGISTRY, ExecutionMode.MODEL)
    projection = build_mode_projection(_REGISTRY, decision=decision)
    assert projection.mode_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, mode_available=True)  # MODEL not supported


def test_projection_is_read_only_and_frozen():
    projection = build_mode_projection(_REGISTRY)
    assert projection.read_only is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        projection.mode_available = True  # type: ignore[misc]

"""P4-EXEC-D ToolExecutionProfile tests — existing safe bridge path only."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    SUPPORTED_BRIDGE_TOOLS,
    ToolExecutionProfile,
    ExecTruthLabel,
    build_default_tool_execution_profile,
    build_no_direct_dispatch_proof,
)


def test_tool_profile_allows_existing_safe_bridge_path():
    profile = build_default_tool_execution_profile()
    assert profile.allowed_tool_names == SUPPORTED_BRIDGE_TOOLS == ("read_file",)
    assert profile.read_only_tools == ("read_file",)
    assert profile.runtime_bridge_required is True
    assert profile.requires_lease_scope_match is True
    assert profile.truth_label is ExecTruthLabel.LIVE


def test_tool_profile_forbids_direct_dispatch():
    profile = build_default_tool_execution_profile()
    assert profile.direct_dispatch_allowed is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(profile, direct_dispatch_allowed=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(profile, runtime_bridge_required=False)
    for verb in ("dispatch", "execute", "run", "submit"):
        assert not hasattr(profile, verb)
    # the B-era proof still holds
    proof = build_no_direct_dispatch_proof()
    assert proof.direct_tool_runtime_dispatch_called is False


def test_mutating_tools_remain_unavailable_by_default():
    profile = build_default_tool_execution_profile()
    assert profile.mutating_tools_unavailable is True
    assert profile.mutating_tools_unavailable_reason
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(profile, mutating_tools_unavailable=False)
    # a mutating tool cannot be smuggled into the allowed set:
    # (1) not declared read-only
    with pytest.raises(AurelExecValidationError) as not_read_only:
        dataclasses.replace(profile, allowed_tool_names=("read_file", "write_file"))
    assert not_read_only.value.code is AurelExecErrorCode.UNSUPPORTED_TOOL
    # (2) even if declared read-only, it must not exceed the bridge's path
    with pytest.raises(AurelExecValidationError) as exceeds_bridge:
        dataclasses.replace(
            profile,
            allowed_tool_names=("read_file", "list_dir"),
            read_only_tools=("read_file", "list_dir"),
        )
    assert exceeds_bridge.value.code is AurelExecErrorCode.UNSUPPORTED_TOOL


def test_tool_profile_must_name_its_tools():
    profile = build_default_tool_execution_profile()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(profile, allowed_tool_names=())


def test_tool_profile_requires_sandbox_and_policy_context():
    profile = build_default_tool_execution_profile()
    assert profile.requires_sandbox_profile is True
    assert profile.requires_policy_context is True

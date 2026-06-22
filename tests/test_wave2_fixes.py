"""Regression tests for wave-2 hardening fixes."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.approval import ApprovalPolicy
from agentic_runtime.budget import BudgetLedger, BudgetPolicy
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.hitl import DenyAllApprover
from agentic_runtime.sandbox_policy import SandboxProfileName
from tests.conftest import bounded_test_approver, make_cmd, write_kernel


def test_build_runtime_defaults_to_restricted_local(tmp_path):
    kernel = build_runtime(workspace_root=str(tmp_path))
    assert kernel.sandbox_policy is not None
    assert kernel.sandbox_policy.profile.profile_name == SandboxProfileName.RESTRICTED_LOCAL.value
    assert kernel.sandbox_policy.profile.unsafe is False


def test_build_runtime_allow_unsafe_uses_demo_profile(tmp_path):
    kernel = build_runtime(workspace_root=str(tmp_path), allow_unsafe=True)
    assert kernel.sandbox_policy.profile.profile_name == SandboxProfileName.UNSAFE_LOCAL_DEMO.value
    assert kernel.sandbox_policy.profile.unsafe is True


def test_delete_file_is_registered_and_deletes(card, tmp_path):
    from agentic_runtime.sandbox import UnsafeLocalSandbox

    runtime = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=bounded_test_approver(
            lambda r: r.command.tool == "delete_file",
            allow_r4=True,
            allow_r5=True,
        ),
        approval_policy=ApprovalPolicy(deny_r5_by_default=False),
    )
    card.authority.write_paths = ["src/"]
    card.allowed_tools = ["delete_file", "read_file", "write_file"]
    runtime.sandbox.write_file("src/remove_me.txt", "bye\n")
    cmd = make_cmd(card, "delete_file", {"path": "src/remove_me.txt"}, risk=RiskLevel.HIGH)
    res = runtime.runtime.submit(cmd, card)
    assert res.ok
    with pytest.raises(OSError):
        runtime.sandbox.read_file("src/remove_me.txt")


def test_edit_file_verifier_rejects_ambiguous_find(write_kernel, card):
    card.authority.write_paths = ["src/"]
    write_kernel.sandbox.write_file("src/dup.py", "foo\nfoo\n")
    cmd = make_cmd(card, "edit_file", {
        "path": "src/dup.py", "find": "foo", "replace": "bar"})
    res = write_kernel.runtime.submit(cmd, card)
    assert not res.ok
    assert "ambiguous" in res.verifier.reason.lower()


def test_hitl_blocks_medium_write_without_explicit_approval(card):
    from agentic_runtime.sandbox import UnsafeLocalSandbox

    strict = build_runtime(
        sandbox=UnsafeLocalSandbox(),
        approval_gate=bounded_test_approver(allow_r2=False, allow_r3=False),
    )
    strict.sandbox.write_file("src/a.py", "old\n")
    cmd = make_cmd(card, "write_file", {
        "path": "src/a.py", "content": "new\n"}, risk=RiskLevel.MEDIUM)
    res = strict.runtime.submit(cmd, card)
    assert not res.ok
    assert res.verifier.code in {"HITL_DENIED", "APPROVAL_DENIED"} or (
        res.decision.verdict.value == "require_approval"
    )


def test_post_execution_memory_budget_returns_command_result(write_kernel, card):
    card.authority.write_paths = ["src/"]
    cmd = make_cmd(card, "write_file", {"path": "src/mem.py", "content": "x\n"})
    tight = BudgetLedger(BudgetPolicy(max_memory_writes=0))
    write_kernel.runtime.budget = tight

    res = write_kernel.runtime.submit(cmd, card)
    assert res.verifier.code == "BUDGET_EXCEEDED"
    assert res.transition is not None
    assert len(write_kernel.trace) >= 1

"""Regression tests for wave-3 hardening fixes."""

from __future__ import annotations

import os

import pytest

from agentic_runtime import AgentCard, AgentClass, AuthorityScope, RiskLevel, build_runtime
from agentic_runtime.approval import ApprovalPolicy
from agentic_runtime.core_types import PolicyVerdict
from agentic_runtime.sandbox import UnsafeLocalSandbox, max_snapshots_limit
from tests.conftest import make_cmd


def test_empty_read_and_write_paths_denies_read(kernel):
    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=[], read_paths=[], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file"],
    )
    cmd = make_cmd(card, "read_file", {"path": "secret.txt"})
    decision = kernel.policy.evaluate(cmd, card)
    assert decision.verdict is PolicyVerdict.DENY
    assert any("no read authority" in r for r in decision.reasons)


def test_read_authority_falls_back_to_write_paths(kernel):
    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=["src/"], read_paths=[], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file"],
    )
    allowed = make_cmd(card, "read_file", {"path": "src/app.py"})
    denied = make_cmd(card, "read_file", {"path": "outside.txt"})
    assert kernel.policy.evaluate(allowed, card).verdict is PolicyVerdict.ALLOW
    assert kernel.policy.evaluate(denied, card).verdict is PolicyVerdict.DENY


def test_build_runtime_accepts_approval_policy(tmp_path):
    policy = ApprovalPolicy(deny_r5_by_default=False)
    kernel = build_runtime(
        workspace_root=str(tmp_path),
        approval_policy=policy,
    )
    assert kernel.runtime.approval_policy is policy
    assert kernel.runtime.approval_policy.deny_r5_by_default is False


def test_snapshot_eviction_honors_env_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTIC_MAX_SNAPSHOTS", "2")
    assert max_snapshots_limit() == 2

    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    sbx.write_file("a.txt", "1")
    ids = [sbx.snapshot() for _ in range(4)]

    assert sbx.active_snapshot_count() == 2
    assert ids[0] not in sbx._snapshots
    assert ids[1] not in sbx._snapshots
    assert ids[2] in sbx._snapshots
    assert ids[3] in sbx._snapshots

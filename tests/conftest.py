"""Shared fixtures for agentic_runtime tests."""

from __future__ import annotations

import sys

import pytest

from agentic_runtime import (
    AgentCard, AgentClass, AuthorityScope, RiskLevel, build_runtime,
)
from agentic_runtime.approval import ApprovalRiskClass
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.sandbox import UnsafeLocalSandbox


def subprocess_spawn_available() -> bool:
    """True when sandbox subprocess timeout enforcement works in this environment."""
    import tempfile

    from agentic_runtime.sandbox import UnsafeLocalSandbox

    try:
        with tempfile.TemporaryDirectory() as td:
            sbx = UnsafeLocalSandbox(root=td)
            res = sbx.run_shell(
                [sys.executable, "-c", "import time; time.sleep(2)"],
                timeout=0.5,
            )
            if "Permission denied" in res.stderr or res.error_kind == "sandbox_error":
                return False
            return res.timed_out
    except OSError:
        return False


requires_subprocess = pytest.mark.skipif(
    not subprocess_spawn_available(),
    reason="nested subprocess execution unavailable in this environment",
)


def bounded_test_approver(predicate=None, **kwargs):
    """Test helper: R0–R3 allowed by default; predicate may narrow, never widen."""
    defaults = {
        "allow_r0": True,
        "allow_r1": True,
        "allow_r2": True,
        "allow_r3": True,
        "allow_r4": False,
        "allow_r5": False,
    }
    defaults.update(kwargs)
    return AutoApprover(predicate, **defaults)


def _unsafe_runtime(approval_gate):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(),
        approval_gate=approval_gate,
    )


@pytest.fixture
def kernel():
    """Narrow approver: only R0/R1 auto-approved (HITL paths stay realistic)."""
    return _unsafe_runtime(bounded_test_approver())


@pytest.fixture
def write_kernel():
    """Unsafe sandbox with explicit approval for common write/exec test tools."""
    return _unsafe_runtime(
        bounded_test_approver(
            lambda r: (
                r.command.tool in {
                    "run_tests", "edit_file", "write_file", "patch_file", "delete_file",
                }
                or r.risk_class in {ApprovalRiskClass.R0, ApprovalRiskClass.R1}
            ),
        ),
    )


@pytest.fixture
def card():
    return AgentCard.make(
        name="Test Agent", agent_class=AgentClass.EXECUTION,
        mission="test workspace",
        authority=AuthorityScope(
            write_paths=["src/"], read_paths=["*"],
            max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "edit_file", "write_file", "run_tests", "list_dir"],
    )


def make_cmd(card, tool, args, **kw):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale=kw.get("rationale", "test"),
        declared_risk=kw.get("risk", RiskLevel.LOW),
        expected_effect=kw.get("expected_effect", "test"))

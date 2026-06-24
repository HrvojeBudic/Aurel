"""P0.3 sandbox reality patch tests."""

from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.sandbox import (
    BubblewrapSandbox,
    DEFAULT_MAX_OUTPUT_BYTES,
    SandboxMode,
    SandboxUnavailableError,
    UnsafeLocalSandbox,
    _run_subprocess,
    create_sandbox,
)
from tests.conftest import make_cmd, requires_subprocess


def test_unsafe_local_sandbox_is_explicitly_marked_unsafe():
    sbx = UnsafeLocalSandbox()
    assert sbx.is_hard_isolated is False
    assert sbx.is_security_boundary is False
    assert sbx.mode is SandboxMode.UNSAFE_LOCAL
    assert "NOT a security boundary" in UnsafeLocalSandbox.UNSAFE_WARNING


def test_create_sandbox_unsafe_requires_allow_unsafe():
    with pytest.raises(ValueError, match="allow_unsafe"):
        create_sandbox(SandboxMode.UNSAFE_LOCAL)


def test_create_sandbox_unsafe_with_flag():
    sbx = create_sandbox(SandboxMode.UNSAFE_LOCAL, allow_unsafe=True)
    assert isinstance(sbx, UnsafeLocalSandbox)


def test_no_silent_downgrade_from_bubblewrap():
    if BubblewrapSandbox.is_available():
        sbx = create_sandbox(SandboxMode.BUBBLEWRAP, allow_unsafe=True)
        assert isinstance(sbx, BubblewrapSandbox)
        assert not isinstance(sbx, UnsafeLocalSandbox)
    else:
        with pytest.raises(SandboxUnavailableError) as exc:
            create_sandbox(SandboxMode.BUBBLEWRAP, allow_unsafe=True)
        assert exc.value.mode is SandboxMode.BUBBLEWRAP
        # Must not return UnsafeLocalSandbox
        with pytest.raises(SandboxUnavailableError):
            create_sandbox(SandboxMode.BUBBLEWRAP, allow_unsafe=True)


def test_run_tests_high_risk_without_hard_sandbox(tmp_path):
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope

    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(lambda r: r.command.tool == "run_tests"),
    )
    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=["."], max_risk=RiskLevel.HIGH))
    cmd = make_cmd(card, "run_tests", {"test_file": "t.py"})
    decision = kernel.policy.evaluate(cmd, card)
    assert decision.risk is RiskLevel.HIGH


def test_sandbox_blocks_write_outside_root_via_api(tmp_path):
    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    with pytest.raises(PermissionError):
        sbx.write_file("/etc/passwd", "nope")


@pytest.mark.skipif(not BubblewrapSandbox.is_available(), reason="bwrap not installed")
def test_bubblewrap_blocks_write_outside_workspace(tmp_path):
    sbx = BubblewrapSandbox.create(root=str(tmp_path))
    res = sbx.run_shell(
        ["python3", "-c", "open('/etc/passwd','a').write('x')"],
        timeout=5,
    )
    assert not res.success or "Permission denied" in res.stderr or res.exit_code != 0


@pytest.mark.skipif(not BubblewrapSandbox.is_available(), reason="bwrap not installed")
def test_bubblewrap_blocks_network_by_default(tmp_path):
    sbx = BubblewrapSandbox.create(root=str(tmp_path))
    script = (
        "import socket\n"
        "s = socket.socket()\n"
        "s.settimeout(2)\n"
        "s.connect(('1.1.1.1', 53))\n"
    )
    sbx.write_file("net_probe.py", script)
    res = sbx.run_shell(["python3", "net_probe.py"], timeout=5)
    assert not res.success


@requires_subprocess
def test_timeout_kills_long_running_command(tmp_path):
    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    res = sbx.run_shell(["python3", "-c", "import time; time.sleep(30)"], timeout=0.2)
    assert res.timed_out
    assert res.error_kind == "timeout"
    assert res.exit_code == 124


def test_stdout_stderr_are_capped(tmp_path):
    limit = 4096
    sbx = UnsafeLocalSandbox(root=str(tmp_path), max_output_bytes=limit)
    res = sbx.run_shell(["python3", "-c", "print('x' * 20000)"], timeout=5)
    assert res.truncated
    assert len(res.stdout) <= limit + 128
    assert "truncated" in res.stdout


def test_structured_observation_on_sandbox_failure(tmp_path):
    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    res = sbx.run_shell(["/nonexistent/binary"], timeout=1)
    assert res.error_kind == "unavailable"
    assert res.sandbox_mode == SandboxMode.UNSAFE_LOCAL.value
    assert res.stderr


def test_run_subprocess_rejects_empty_argv(tmp_path):
    with pytest.raises(ValueError, match="must not be empty"):
        _run_subprocess(
            [],
            cwd=str(tmp_path),
            env={},
            timeout=1,
            sandbox_mode=SandboxMode.UNSAFE_LOCAL,
        )


def test_run_subprocess_rejects_non_string_argv_entries(tmp_path):
    with pytest.raises(TypeError, match="cmd\\[1\\] must be str"):
        _run_subprocess(
            ["python3", 1],  # type: ignore[list-item]
            cwd=str(tmp_path),
            env={},
            timeout=1,
            sandbox_mode=SandboxMode.UNSAFE_LOCAL,
        )


def test_run_subprocess_rejects_nul_byte_argv(tmp_path):
    with pytest.raises(ValueError, match="NUL"):
        _run_subprocess(
            ["python3", "-c", "print('bad')\x00"],
            cwd=str(tmp_path),
            env={},
            timeout=1,
            sandbox_mode=SandboxMode.UNSAFE_LOCAL,
        )


@pytest.mark.skipif(not BubblewrapSandbox.is_available(), reason="bwrap not installed")
def test_run_tests_escape_fails_in_hard_sandbox(tmp_path):
    from agentic_runtime import AgentCard, AgentClass, AuthorityScope

    sbx = BubblewrapSandbox.create(root=str(tmp_path))
    kernel = build_runtime(
        sandbox=sbx,
        approval_gate=AutoApprover(lambda r: r.command.tool == "run_tests"),
    )
    card = AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=["."], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["run_tests", "read_file", "write_file"],
    )
    sbx.write_file("test_evil.py", "open('/etc/passwd','a').write('p')\n")
    kernel.verifier.test_integrity.snapshot()
    cmd = make_cmd(card, "run_tests", {"test_file": "test_evil.py"})
    decision = kernel.policy.evaluate(cmd, card)
    assert decision.risk is RiskLevel.MEDIUM
    res = kernel.runtime.submit(cmd, card)
    assert not res.ok

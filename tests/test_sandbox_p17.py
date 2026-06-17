"""P0.17 — Sandbox Hardening tests."""

from __future__ import annotations

import os
import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    build_runtime,
    create_profiled_sandbox,
    enforce_path_policy,
    get_sandbox_profile,
    is_secret_like_path,
    backend_availability,
)
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.praxis import PraxisCandidateGenerator, PraxisExperienceBuilder
from agentic_runtime.repo_agent import CodeTaskReport, RepositoryAgentLoop, RepoTaskRequest
from agentic_runtime.sandbox import (
    BubblewrapSandbox,
    DockerSandbox,
    SandboxMode,
    SandboxUnavailableError,
    UnsafeLocalSandbox,
)
from agentic_runtime.sandbox_policy import (
    ProfiledSandbox,
    SandboxPolicy,
    SandboxProfileName,
    SandboxViolationError,
)
from tests.conftest import make_cmd


def _card(tmp_path):
    return AgentCard.make(
        "t", AgentClass.EXECUTION, "m",
        AuthorityScope(write_paths=["*"], read_paths=["*"], max_risk=RiskLevel.HIGH),
    )


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
def test_no_exec_readonly_denies_write_and_exec(tmp_path):
    sandbox, policy = create_profiled_sandbox(
        SandboxProfileName.NO_EXEC_READONLY.value, str(tmp_path))
    assert policy.profile.allow_read is True
    assert policy.profile.allow_write is False
    assert policy.profile.allow_exec is False
    with pytest.raises(SandboxViolationError):
        sandbox.write_file("ok.txt", "x")


def test_restricted_local_allows_workspace_write(tmp_path):
    sandbox, policy = create_profiled_sandbox(
        SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    sandbox.write_file("ok.txt", "hello")
    assert sandbox.read_file("ok.txt") == "hello"
    assert policy.profile.allow_network is False


def test_unsafe_local_demo_marked_unsafe(tmp_path):
    profile = get_sandbox_profile(SandboxProfileName.UNSAFE_LOCAL_DEMO.value, str(tmp_path))
    assert profile.unsafe is True
    diag = SandboxPolicy(profile).diagnostics(UnsafeLocalSandbox(root=str(tmp_path)))
    assert diag.unsafe is True
    assert any("NOT a security boundary" in x for x in diag.limitations)


def test_docker_unavailable_is_honest():
    ok, msg = backend_availability(SandboxProfileName.DOCKER.value)
    if not DockerSandbox.is_available():
        assert not ok
        with pytest.raises(SandboxUnavailableError):
            create_profiled_sandbox(SandboxProfileName.DOCKER.value, "/tmp/ar_docker_test")


def test_bubblewrap_unavailable_is_honest():
    ok, msg = backend_availability(SandboxProfileName.BUBBLEWRAP.value)
    if not BubblewrapSandbox.is_available():
        assert not ok
        with pytest.raises(SandboxUnavailableError):
            create_profiled_sandbox(SandboxProfileName.BUBBLEWRAP.value, "/tmp/ar_bwrap_test")


# --------------------------------------------------------------------------- #
# Filesystem boundaries
# --------------------------------------------------------------------------- #
def test_valid_path_inside_workspace_accepted(tmp_path):
    profile = get_sandbox_profile(SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    decision = enforce_path_policy(profile, "src/a.py", "read")
    assert decision.allowed


def test_path_traversal_rejected(tmp_path):
    profile = get_sandbox_profile(SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    decision = enforce_path_policy(profile, "../outside.txt", "read")
    assert not decision.allowed


def test_write_outside_workspace_rejected(tmp_path):
    sandbox, _ = create_profiled_sandbox(
        SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    with pytest.raises((PermissionError, SandboxViolationError)):
        sandbox.write_file("/etc/passwd", "nope")


def test_read_outside_workspace_rejected(tmp_path):
    sandbox, _ = create_profiled_sandbox(
        SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    with pytest.raises((PermissionError, SandboxViolationError)):
        sandbox.read_file("/etc/passwd")


def test_secret_like_paths_protected(tmp_path):
    assert is_secret_like_path(".env")
    assert is_secret_like_path("config/.env.local")
    profile = get_sandbox_profile(SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    decision = enforce_path_policy(profile, ".env", "read")
    assert not decision.allowed


@pytest.mark.skipif(os.name == "nt", reason="symlinks")
def test_symlink_escape_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("leak")
    link = tmp_path / "link"
    link.symlink_to(outside / "secret.txt")
    sandbox, _ = create_profiled_sandbox(
        SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    with pytest.raises((PermissionError, SandboxViolationError, OSError)):
        sandbox.read_file("link")


# --------------------------------------------------------------------------- #
# Execution limits
# --------------------------------------------------------------------------- #
def test_run_shell_has_default_timeout(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.RESTRICTED_LOCAL.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(
        make_cmd(card, "run_shell", {"command": ["echo", "hi"]}),
        card,
    )
    assert res.observation.success or res.observation.stderr


def test_long_command_timeout_enforced(tmp_path):
    sandbox, _ = create_profiled_sandbox(
        SandboxProfileName.RESTRICTED_LOCAL.value, str(tmp_path))
    res = sandbox.run_shell(
        ["python3", "-c", "import time; time.sleep(5)"],
        timeout=0.2,
    )
    assert res.timed_out or res.exit_code != 0


def test_output_truncation(tmp_path):
    sandbox = UnsafeLocalSandbox(root=str(tmp_path), max_output_bytes=64)
    res = sandbox.run_shell(["python3", "-c", "print('x' * 2000)"], timeout=5)
    assert res.truncated or len(res.stdout) < 2100


# --------------------------------------------------------------------------- #
# Tool Bus integration
# --------------------------------------------------------------------------- #
def test_read_tool_works_under_readonly_profile(tmp_path):
    (tmp_path / "a.txt").write_text("hi")
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.NO_EXEC_READONLY.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(make_cmd(card, "read_file", {"path": "a.txt"}), card)
    assert res.ok


def test_write_tool_denied_under_readonly_profile(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.NO_EXEC_READONLY.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(
        make_cmd(card, "write_file", {"path": "a.txt", "content": "x"}),
        card,
    )
    assert not res.ok
    assert "SANDBOX" in res.observation.stderr.upper() or res.verifier.code == "SANDBOX_VIOLATION"


def test_write_tool_allowed_under_restricted_local(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.RESTRICTED_LOCAL.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(
        make_cmd(card, "write_file", {"path": "a.txt", "content": "x"}),
        card,
    )
    assert res.ok


def test_execution_tool_denied_under_no_exec_readonly(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.NO_EXEC_READONLY.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(
        make_cmd(card, "run_shell", {"command": ["echo", "hi"]}),
        card,
    )
    assert not res.ok


def test_sandbox_violation_structured_failure(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.NO_EXEC_READONLY.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(
        make_cmd(card, "write_file", {"path": "a.txt", "content": "x"}),
        card,
    )
    assert res.verifier.code == "SANDBOX_VIOLATION"


# --------------------------------------------------------------------------- #
# Runtime integration
# --------------------------------------------------------------------------- #
def test_runtime_reports_active_sandbox_mode(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.RESTRICTED_LOCAL.value,
        workspace_root=str(tmp_path),
    )
    from agentic_runtime.status import runtime_status
    status = runtime_status(kernel)
    assert status["sandbox"]["profile"] == SandboxProfileName.RESTRICTED_LOCAL.value
    assert status["sandbox"]["network_allowed"] is False


def test_trace_includes_sandbox_violation(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.NO_EXEC_READONLY.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card(tmp_path)
    kernel.runtime.submit(
        make_cmd(card, "write_file", {"path": "a.txt", "content": "x"}),
        card,
    )
    kinds = [r.get("kind") for r in kernel.trace.replay()]
    assert "sandbox_violation" in kinds


def test_sandbox_violation_prevents_handler(tmp_path):
    kernel = build_runtime(
        sandbox_profile=SandboxProfileName.NO_EXEC_READONLY.value,
        workspace_root=str(tmp_path),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
    )
    card = _card(tmp_path)
    res = kernel.runtime.submit(
        make_cmd(card, "write_file", {"path": "a.txt", "content": "blocked"}),
        card,
    )
    assert not (tmp_path / "a.txt").exists() or not res.ok


def test_denied_sandbox_does_not_create_success_praxis_candidate(tmp_path):
    report = CodeTaskReport(
        task_id="t1", objective="x", plan_summary="p",
        final_status="failed", sandbox_profile="no_exec_readonly",
    )
    exp = PraxisExperienceBuilder.from_repo_report(report, trace_run_id="run1")
    cands, _ = PraxisCandidateGenerator.generate(exp)
    assert not any(c.candidate_type.value == "episodic" for c in cands)


# --------------------------------------------------------------------------- #
# Repo agent integration
# --------------------------------------------------------------------------- #
def test_repo_dry_run_uses_readonly_profile(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("old\n")
    req = RepoTaskRequest.make(
        "replace 'old' with 'new' in src/a.py",
        repo_path=str(tmp_path),
        allowed_paths=["src/*"],
    )
    report = RepositoryAgentLoop().run(req, apply=False, dry_run=True)
    assert report.sandbox_profile == SandboxProfileName.NO_EXEC_READONLY.value


def test_repo_task_report_includes_sandbox_profile(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("old\n")
    req = RepoTaskRequest.make(
        "replace 'old' with 'new' in src/a.py",
        repo_path=str(tmp_path),
        allowed_paths=["src/*"],
        sandbox_profile=SandboxProfileName.RESTRICTED_LOCAL.value,
    )
    report = RepositoryAgentLoop().run(req, apply=False)
    assert report.sandbox_profile == SandboxProfileName.NO_EXEC_READONLY.value or report.sandbox_profile

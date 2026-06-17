"""P1.0 — apply sandbox resolution tests."""

from __future__ import annotations

from agentic_runtime.sandbox import BubblewrapSandbox, DockerSandbox
from agentic_runtime.sandbox_policy import (
    SandboxProfileName,
    backend_availability,
    get_sandbox_profile,
    resolve_apply_sandbox_profile,
)


def test_backend_availability_reports_honestly():
    ok, msg = backend_availability(SandboxProfileName.BUBBLEWRAP.value)
    assert ok == BubblewrapSandbox.is_available()
    assert msg


def test_get_sandbox_profile_bubblewrap():
    profile = get_sandbox_profile(SandboxProfileName.BUBBLEWRAP.value, "/tmp/ws")
    assert profile.profile_name == "bubblewrap"
    assert profile.allow_exec is True
    assert profile.unsafe is False


def test_resolve_apply_prefers_bubblewrap_over_docker():
    explicit, _ = resolve_apply_sandbox_profile("docker")
    assert explicit == "docker"
    profile, _ = resolve_apply_sandbox_profile()
    if BubblewrapSandbox.is_available():
        assert profile == SandboxProfileName.BUBBLEWRAP.value
    elif DockerSandbox.is_available():
        assert profile == SandboxProfileName.DOCKER.value
    else:
        assert profile == SandboxProfileName.RESTRICTED_LOCAL.value

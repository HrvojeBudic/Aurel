"""Tests for P2.10-C desktop capability boundary."""

from __future__ import annotations

from agentic_runtime.aurel_shell.desktop_shell_contract import (
    DesktopShellCapability,
    DesktopShellCapabilityStatus,
    build_desktop_shell_capability_boundary,
    build_p2_10_c_desktop_shell_result,
)


def test_p210c_allowed_minimal_capabilities() -> None:
    boundary = build_desktop_shell_capability_boundary()
    allowed = {e.capability for e in boundary.allowed_capabilities}
    assert allowed == {
        DesktopShellCapability.LOAD_LOCAL_WEB_SHELL,
        DesktopShellCapability.DISPLAY_CONTRACT_STATE,
        DesktopShellCapability.DISPLAY_TRUTH_LABELS,
        DesktopShellCapability.DISPLAY_EVIDENCE_REFS,
        DesktopShellCapability.DISPLAY_LIMITATIONS,
    }
    for entry in boundary.allowed_capabilities:
        assert entry.status is DesktopShellCapabilityStatus.ALLOWED_MINIMAL


def test_p210c_disabled_native_capabilities() -> None:
    boundary = build_desktop_shell_capability_boundary()
    disabled = {e.capability: e.status for e in boundary.disabled_capabilities}
    assert disabled[DesktopShellCapability.NATIVE_FILE_READ] is (
        DesktopShellCapabilityStatus.DISABLED
    )
    assert disabled[DesktopShellCapability.NATIVE_FILE_WRITE] is (
        DesktopShellCapabilityStatus.DISABLED
    )
    assert disabled[DesktopShellCapability.NATIVE_SECRET_ACCESS] is (
        DesktopShellCapabilityStatus.DISABLED
    )
    assert disabled[DesktopShellCapability.NATIVE_SHELL_EXEC] is (
        DesktopShellCapabilityStatus.DISABLED
    )


def test_p210c_future_gated_native_capabilities() -> None:
    boundary = build_desktop_shell_capability_boundary()
    future = {e.capability: e.status for e in boundary.future_gated_capabilities}
    assert future[DesktopShellCapability.NATIVE_NETWORK_BRIDGE] is (
        DesktopShellCapabilityStatus.FUTURE_GATED
    )
    assert future[DesktopShellCapability.NATIVE_APPROVAL_BRIDGE] is (
        DesktopShellCapabilityStatus.FUTURE_GATED
    )
    assert future[DesktopShellCapability.NATIVE_RUNTIME_CONTROL] is (
        DesktopShellCapabilityStatus.FUTURE_GATED
    )
    assert future[DesktopShellCapability.NATIVE_SANDBOX_CONTROL] is (
        DesktopShellCapabilityStatus.FUTURE_GATED
    )


def test_p210c_capability_boundary_in_read_model() -> None:
    result = build_p2_10_c_desktop_shell_result()
    boundary = result.desktop_read_model.capability_boundary
    assert boundary.boundary_hash == result.desktop_capability_boundary.boundary_hash
    assert "NO_SHELL_LIVE_CLAIM" in boundary.no_overclaim_boundaries

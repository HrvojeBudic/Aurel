"""P4-EXEC-D execution mode registry tests — closed world, no fallback."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecTruthLabel,
    ExecutionMode,
    ExecutionModeAvailability,
    ExecutionModeProfile,
    ExecutionModeRegistry,
    build_default_execution_mode_registry,
    build_no_silent_fallback_proof,
    decide_mode_compatibility,
)


def test_execution_mode_registry_is_closed_world():
    registry = build_default_execution_mode_registry()
    covered = {profile.execution_mode for profile in registry.profiles}
    assert covered == set(ExecutionMode)  # total over the enum
    assert registry.registry_is_closed_world is True
    assert registry.unknown_mode_blocked is True
    # a registry missing a mode is unconstructible
    with pytest.raises(AurelExecValidationError) as excinfo:
        dataclasses.replace(registry, profiles=registry.profiles[:-1])
    assert "must be total" in str(excinfo.value)
    # duplicate mode profiles are unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(
            registry, profiles=registry.profiles + (registry.profiles[0],)
        )


def test_default_registry_classifies_every_mode_honestly():
    registry = build_default_execution_mode_registry()
    assert registry.supported_modes == ("TOOL",)
    assert registry.profile_only_modes == ("MODEL",)
    assert set(registry.unavailable_modes) == {
        "TERMINAL",
        "CODE",
        "CONVERSATION",
        "COMPOSITE",
    }
    assert set(registry.blocked_modes) == {"UNAVAILABLE", "ERROR"}
    assert registry.default_mode is ExecutionMode.TOOL


def test_unknown_execution_mode_is_blocked():
    registry = build_default_execution_mode_registry()
    decision = decide_mode_compatibility(registry, "warp_drive")
    assert decision.blocked is True
    assert decision.allowed is False
    assert "closed-world" in decision.reason
    assert "no silent fallback" in decision.reason


def test_registry_cannot_execute_grant_authority_or_fallback():
    registry = build_default_execution_mode_registry()
    for boundary_field in ("silent_fallback_allowed", "grants_authority", "executes"):
        assert getattr(registry, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(registry, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(registry, registry_is_closed_world=False)
    for verb in ("execute", "run", "submit", "dispatch", "authorize"):
        assert not hasattr(registry, verb)


def test_only_bridge_modes_can_be_available():
    # a profile claiming availability for a risky mode is unconstructible
    with pytest.raises(AurelExecValidationError) as excinfo:
        ExecutionModeProfile(
            profile_id="exec-mode-profile-x",
            execution_mode=ExecutionMode.TERMINAL,
            profile_name="illegally available terminal",
            availability_status=ExecutionModeAvailability.AVAILABLE_FOR_EXISTING_BRIDGE,
            truth_label=ExecTruthLabel.LIVE,
        )
    assert excinfo.value.code is AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE


def test_unavailable_and_blocked_profiles_must_explain_themselves():
    with pytest.raises(AurelExecValidationError):
        ExecutionModeProfile(
            profile_id="exec-mode-profile-x",
            execution_mode=ExecutionMode.TERMINAL,
            profile_name="unexplained unavailable",
            availability_status=ExecutionModeAvailability.UNAVAILABLE,
            truth_label=ExecTruthLabel.UNAVAILABLE,
            unavailable_reason=None,
        )


def test_default_mode_must_be_available():
    registry = build_default_execution_mode_registry()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(registry, default_mode=ExecutionMode.TERMINAL)


def test_no_silent_fallback_proof_is_fail_closed():
    proof = build_no_silent_fallback_proof()
    assert proof.silent_fallback_allowed is False
    assert proof.unknown_mode_blocked is True
    assert proof.registry_is_closed_world is True
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, silent_fallback_allowed=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, unknown_mode_blocked=False)

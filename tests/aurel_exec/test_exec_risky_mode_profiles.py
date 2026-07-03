"""P4-EXEC-D risky mode profile tests — modeled, never executable."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import agentic_runtime.aurel_exec as aurel_exec
from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTruthLabel,
    build_default_code_execution_profile,
    build_default_model_execution_profile,
    build_default_terminal_execution_profile,
    build_no_code_execution_proof,
    build_no_model_call_proof,
    build_no_terminal_execution_proof,
)


def test_model_profile_exists_but_model_calls_are_unavailable():
    profile = build_default_model_execution_profile()
    assert profile.model_execution_available is False
    assert profile.model_call_allowed is False
    assert profile.truth_label is ExecTruthLabel.UNAVAILABLE
    assert profile.unavailable_reason
    for boundary_field in ("model_execution_available", "model_call_allowed"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(profile, **{boundary_field: True})
    # the future requirements are mandatory, not optional
    for requirement in (
        "requires_router_ref",
        "requires_budget_ref",
        "requires_policy_context",
        "requires_prompt_contract",
        "requires_output_contract",
        "requires_verifier",
    ):
        assert getattr(profile, requirement) is True
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(profile, **{requirement: False})
    proof = build_no_model_call_proof()
    assert proof.model_call_allowed is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, model_call_allowed=True)


def test_terminal_profile_exists_but_shell_and_subprocess_are_unavailable():
    profile = build_default_terminal_execution_profile()
    assert profile.terminal_execution_available is False
    assert profile.subprocess_allowed is False
    assert profile.shell_allowed is False
    assert profile.network_allowed is False
    for boundary_field in (
        "terminal_execution_available",
        "subprocess_allowed",
        "shell_allowed",
        "network_allowed",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(profile, **{boundary_field: True})
    for requirement in (
        "requires_sandbox_profile",
        "requires_operator_approval",
        "requires_p9_authority",
    ):
        assert getattr(profile, requirement) is True
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(profile, **{requirement: False})
    proof = build_no_terminal_execution_proof()
    assert proof.subprocess_allowed is False
    assert proof.shell_allowed is False


def test_code_profile_exists_but_eval_and_script_execution_are_unavailable():
    profile = build_default_code_execution_profile()
    assert profile.code_execution_available is False
    assert profile.eval_allowed is False
    assert profile.script_execution_allowed is False
    assert profile.filesystem_mutation_allowed is False
    assert profile.network_allowed is False
    for boundary_field in (
        "code_execution_available",
        "eval_allowed",
        "script_execution_allowed",
        "filesystem_mutation_allowed",
        "network_allowed",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(profile, **{boundary_field: True})
    proof = build_no_code_execution_proof()
    assert proof.eval_allowed is False
    assert proof.script_execution_allowed is False


def test_risky_profiles_have_no_execution_surface():
    for profile in (
        build_default_model_execution_profile(),
        build_default_terminal_execution_profile(),
        build_default_code_execution_profile(),
    ):
        for verb in ("execute", "run", "call", "invoke", "submit", "dispatch"):
            assert not hasattr(profile, verb), f"{type(profile).__name__}.{verb}"


def test_d_modules_contain_no_risky_execution_primitives():
    package_dir = Path(aurel_exec.__file__).parent
    for module_name in ("exec_modes.py", "exec_mode_profiles.py"):
        source = (package_dir / module_name).read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "import socket",
            "import requests",
            "import httpx",
            "import urllib",
            "import asyncio",
            "os.system",
            "eval(",
            "exec(",
            "open(",
            ".dispatch(",
            "from ..runtime import",
            "from agentic_runtime.runtime import",
            "from ..tools import",
            "from ..sandbox",
            "from ..model_router",
            "from ..model_providers",
        ):
            assert forbidden not in source, f"{module_name} contains {forbidden!r}"

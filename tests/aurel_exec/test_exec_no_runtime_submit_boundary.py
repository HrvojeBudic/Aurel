"""P4-EXEC-A no-runtime-submit / no-raw-execution boundary tests.

Proves runtime.submit is unavailable, unwired, and uncalled in this pack,
and that the aurel_exec package has no execution side-effect surface.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import agentic_runtime.aurel_exec as aurel_exec
from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    build_dev_fixture_admission_request,
    build_no_raw_execution_proof,
    build_no_runtime_submit_proof,
    create_exec_job,
    create_execution_attempt,
    decide_admission,
    issue_execution_lease,
)

_PACKAGE_DIR = Path(aurel_exec.__file__).parent
_FORBIDDEN_IMPORTS = (
    "import subprocess",
    "import socket",
    "import requests",
    "import httpx",
    "import urllib",
    "from subprocess",
    "from socket",
    "from ..runtime import",
    "from agentic_runtime.runtime import",
    "from ..tool_runtime import",
    "from agentic_runtime.tool_runtime import",
    "from ..entity import",
    "ToolRuntime",
    "AgenticEntity",
)


def test_package_source_has_no_runtime_or_side_effect_imports():
    for module_path in sorted(_PACKAGE_DIR.glob("*.py")):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in _FORBIDDEN_IMPORTS:
            assert forbidden not in source, f"{module_path.name} contains {forbidden!r}"


def test_no_runtime_submit_proof_is_fail_closed():
    proof = build_no_runtime_submit_proof()
    assert proof.runtime_submit_available is False
    assert proof.runtime_submit_called is False
    assert proof.runtime_submit_wired is False
    assert proof.future_pack_owner == "P4-EXEC-B"
    for boundary_field in (
        "runtime_submit_available",
        "runtime_submit_called",
        "runtime_submit_wired",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_no_raw_execution_proof_is_fail_closed():
    proof = build_no_raw_execution_proof()
    for boundary_field in (
        "execution_performed",
        "tool_dispatched",
        "model_invoked",
        "verifier_executed",
        "sandbox_executed",
        "environment_executed",
        "subprocess_called",
        "network_called",
        "filesystem_mutated",
        "memory_written",
        "identity_mutated",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_runtime_submit_called_stays_false_across_the_full_slice():
    request = build_dev_fixture_admission_request()
    decision = decide_admission(request)
    job = create_exec_job(decision, source_p3_candidate_ref=request.source_p3_candidate_ref)
    lease = issue_execution_lease(
        decision, request, exec_job_id=job.exec_job_id, issued_at_tick=1
    )
    attempt, _ = create_execution_attempt(job, lease, current_tick=2)
    assert attempt.runtime_submit_called is False


def test_no_pack_object_exposes_a_submit_or_dispatch_callable():
    request = build_dev_fixture_admission_request()
    decision = decide_admission(request)
    job = create_exec_job(decision, source_p3_candidate_ref=request.source_p3_candidate_ref)
    lease = issue_execution_lease(
        decision, request, exec_job_id=job.exec_job_id, issued_at_tick=1
    )
    attempt, _ = create_execution_attempt(job, lease, current_tick=2)
    for obj in (request, decision, job, lease, attempt):
        for name in ("submit", "dispatch", "execute", "run", "invoke", "spawn"):
            assert not hasattr(obj, name), f"{type(obj).__name__}.{name} must not exist"


def test_public_api_has_no_submit_or_dispatch_verb():
    for name in dir(aurel_exec):
        lowered = name.lower()
        assert "submit_execution" not in lowered
        assert not lowered.startswith("submit")
        assert not lowered.startswith("dispatch")

"""P4-EXEC-E judgment projection tests — honest visibility, no control,
and the runtime substrate boundary held structurally."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import agentic_runtime.aurel_exec as aurel_exec
from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecutionMode,
    build_execution_verification_request,
    build_judgment_projection,
    build_no_final_python_kernel_claim_proof,
    build_no_rust_rewrite_proof,
    build_profile_only_verifier_hook,
    classify_execution_failure,
    create_algedonic_signal_if_needed,
    create_bounded_recovery_plan,
    decide_verification,
    normalize_runtime_result,
)
from tests.aurel_exec._bridge_helpers import RecordingFakeRuntime, _FakeCard


class _Cmd:
    id = "cmd_x"


def _judgment_chain(*, succeed=False):
    outcome = normalize_runtime_result(
        RecordingFakeRuntime(succeed=succeed).submit(_Cmd(), _FakeCard()),
        attempt_id="exec-attempt-a",
        exec_job_id="exec-job-a",
        session_id="exec-session-a",
        tool_name="read_file",
        command_id="cmd_x",
    )
    request = build_execution_verification_request(
        outcome, requested_execution_mode=ExecutionMode.TOOL
    )
    decision = decide_verification(
        request, outcome, hook=build_profile_only_verifier_hook()
    )
    classification = classify_execution_failure(outcome, decision)
    plan = create_bounded_recovery_plan(classification, max_attempts=1)
    signal = create_algedonic_signal_if_needed(classification)
    return decision, classification, plan, signal


def test_judgment_projection_reports_verification_failure_recovery_and_algedonic_state():
    decision, classification, plan, signal = _judgment_chain(succeed=False)
    projection = build_judgment_projection(
        verification_decision=decision,
        failure_classification=classification,
        recovery_plan=plan,
        algedonic_signal=signal,
    )
    assert projection.verification_status == "FAILED"
    assert projection.verified is False
    assert projection.failure_class == "TOOL_ERROR"
    assert projection.failure_severity == "ERROR"
    assert projection.retryable is True
    assert projection.recovery_plan_available is True
    assert projection.recommended_recovery_action == "RETRY_SAME_INPUT"
    assert projection.recovery_executed is False
    assert projection.algedonic_signal_present is (signal is not None)
    assert projection.operator_action_required is True
    assert projection.p5_proof_required is True
    assert projection.read_only is True


def test_projection_boundary_claims_are_unconstructible():
    decision, classification, plan, signal = _judgment_chain()
    projection = build_judgment_projection(
        verification_decision=decision,
        failure_classification=classification,
        recovery_plan=plan,
        algedonic_signal=signal,
    )
    for boundary_field in (
        "recovery_executed",
        "automatic_retry_available",
        "rollback_execution_available",
        "recovery_execution_available",
        "self_healing_available",
        "p5_trace_verification_available",
        "p9_full_enforcement_available",
        "shell_ui_available",
        "react_frontend_available",
        "api_server_available",
    ):
        assert getattr(projection, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, p5_proof_required=False)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, read_only=False)
    # claiming verified without a PASSED status is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, verified=True)


def test_projection_does_not_claim_final_python_kernel_or_rust_substrate():
    decision, classification, plan, signal = _judgment_chain()
    projection = build_judgment_projection(
        verification_decision=decision,
        failure_classification=classification,
    )
    for boundary_field in (
        "deterministic_replay_engine_available",
        "durable_event_log_available",
        "workflow_exact_copy_available",
        "rust_wasm_substrate_available",
        "python_final_kernel_claim",
    ):
        assert getattr(projection, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})
    kernel_proof = build_no_final_python_kernel_claim_proof()
    assert kernel_proof.python_final_kernel_claim is False
    assert kernel_proof.python_is_v1_reference_and_control_layer is True
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(kernel_proof, python_final_kernel_claim=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(kernel_proof, python_is_v1_reference_and_control_layer=False)
    rust_proof = build_no_rust_rewrite_proof()
    assert rust_proof.rust_wasm_substrate_available is False
    assert rust_proof.rust_code_added is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(rust_proof, rust_code_added=True)


def test_no_rust_wasm_or_substrate_files_exist():
    repo_root = Path(aurel_exec.__file__).parents[3]
    for forbidden in ("Cargo.toml", "crates", "rust", "wasm"):
        assert not (repo_root / forbidden).exists(), forbidden
    package_dir = Path(aurel_exec.__file__).parent
    filenames = {path.name for path in package_dir.glob("*.py")}
    for forbidden in ("exec_replay.py", "exec_event_log.py", "exec_self_healing.py"):
        assert forbidden not in filenames


def test_e_modules_contain_no_execution_primitives():
    package_dir = Path(aurel_exec.__file__).parent
    for module_name in (
        "exec_verification.py",
        "exec_failure.py",
        "exec_recovery.py",
        "exec_algedonic.py",
    ):
        source = (package_dir / module_name).read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "import socket",
            "import asyncio",
            "import threading",
            "os.system",
            "eval(",
            "exec(",
            "open(",
            ".dispatch(",
            ".submit(",
            "from ..runtime import",
            "from agentic_runtime.runtime import",
            "from ..tools import",
            "from ..sandbox",
            "from ..model_router",
            "from ..model_providers",
            "from ..trace import",
        ):
            assert forbidden not in source, f"{module_name} contains {forbidden!r}"


def test_success_chain_projects_honestly_without_overclaim():
    decision, classification, plan, signal = _judgment_chain(succeed=True)
    projection = build_judgment_projection(
        verification_decision=decision,
        failure_classification=classification,
        recovery_plan=plan,
        algedonic_signal=signal,
    )
    # runtime succeeded but verification is inconclusive -> not verified
    assert projection.verification_status == "INCONCLUSIVE"
    assert projection.verified is False
    assert projection.failure_class == "VERIFIER_UNAVAILABLE"
    assert projection.algedonic_signal_present is False

"""P4-EXEC-B unsupported execution modes boundary tests.

Only the safe read-only TOOL path crosses the bridge. Terminal/code/model/
conversation/composite execution remains structurally UNAVAILABLE with a
named future owner, and no P5/P9/Shell/UI surface exists.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import agentic_runtime.aurel_exec as aurel_exec
from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecutionMode,
    SUPPORTED_BRIDGE_EXECUTION_MODES,
    SUPPORTED_BRIDGE_TOOLS,
    UnsupportedExecutionModeProof,
    build_dev_fixture_admission_request,
    build_exec_projection,
    build_unsupported_execution_mode_proofs,
    decide_admission,
    describe_unavailable_mode,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def test_only_the_read_only_tool_path_is_supported():
    assert SUPPORTED_BRIDGE_EXECUTION_MODES == (ExecutionMode.TOOL,)
    assert SUPPORTED_BRIDGE_TOOLS == ("read_file",)


def test_unsupported_execution_modes_remain_unavailable():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    for mode in (
        ExecutionMode.MODEL,
        ExecutionMode.TERMINAL,
        ExecutionMode.CODE,
        ExecutionMode.CONVERSATION,
        ExecutionMode.COMPOSITE,
        ExecutionMode.UNAVAILABLE,
        ExecutionMode.ERROR,
    ):
        request = build_bridge_request(
            job, lease, session, attempt, requested_execution_mode=mode
        )
        with pytest.raises(AurelExecValidationError) as excinfo:
            bridge.submit_once(
                request, job=job, lease=lease, session=session, attempt=attempt,
                card=card, current_tick=5,
            )
        assert excinfo.value.code is AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE
    assert fake.submit_calls == []


def test_unsupported_tools_are_refused_even_in_tool_mode():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    for tool in ("write_file", "run_shell", "run_python", "edit_file", "delete_file"):
        request = build_bridge_request(
            job, lease, session, attempt, requested_tool_name=tool
        )
        with pytest.raises(AurelExecValidationError) as excinfo:
            bridge.submit_once(
                request, job=job, lease=lease, session=session, attempt=attempt,
                card=card, current_tick=5,
            )
        assert excinfo.value.code is AurelExecErrorCode.UNSUPPORTED_TOOL
    assert fake.submit_calls == []


def test_unsupported_mode_proofs_cover_every_non_tool_mode():
    proofs = build_unsupported_execution_mode_proofs()
    covered = {proof.mode for proof in proofs}
    assert covered == set(ExecutionMode) - set(SUPPORTED_BRIDGE_EXECUTION_MODES)
    for proof in proofs:
        assert proof.unavailable is True
        assert proof.reason
        assert proof.future_pack_owner
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, unavailable=False)


def test_supported_mode_cannot_carry_an_unsupported_proof():
    with pytest.raises(AurelExecValidationError):
        UnsupportedExecutionModeProof(
            mode=ExecutionMode.TOOL,
            reason="impossible",
            future_pack_owner="nobody",
        )
    with pytest.raises(AurelExecValidationError):
        describe_unavailable_mode(ExecutionMode.TOOL)


def test_projection_lists_unsupported_modes_unavailable():
    projection = build_exec_projection(
        decide_admission(build_dev_fixture_admission_request())
    )
    assert set(projection.unsupported_modes_unavailable) == {
        "MODEL",
        "TERMINAL",
        "CODE",
        "CONVERSATION",
        "COMPOSITE",
        "UNAVAILABLE",
        "ERROR",
    }


def test_no_p5_p9_shell_ui_surface_exists():
    package_dir = Path(aurel_exec.__file__).parent
    filenames = {path.name for path in package_dir.glob("*.py")}
    for forbidden in (
        "exec_trace_verifier.py",
        "exec_custos.py",
        "exec_shell.py",
        "exec_api.py",
        "exec_worker.py",
        "exec_queue.py",
        "exec_bus.py",
        "exec_checkpoint.py",
        "exec_recovery.py",
    ):
        assert forbidden not in filenames
    public_names = {name.lower() for name in dir(aurel_exec) if not name.startswith("_")}
    for fragment in ("react", "frontend", "apiserver", "websocket", "shellui"):
        assert not any(fragment in name for name in public_names), fragment

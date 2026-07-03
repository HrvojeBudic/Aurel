"""P4-EXEC-B no-direct-dispatch / no-second-executor boundary tests.

Proves AurelExec crosses into execution only through the injected kernel's
submit surface: no direct tool dispatch, no subprocess/network/raw
filesystem/sandbox/model/verifier invocation, no manual trace/ledger write,
no manual policy/Custos enforcement.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import agentic_runtime.aurel_exec as aurel_exec
from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    DIRECT_DISPATCH_FORBIDDEN_REASON,
    build_no_direct_dispatch_proof,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)

_PACKAGE_DIR = Path(aurel_exec.__file__).parent


def test_bridge_uses_only_the_kernel_submit_surface():
    """The fake kernel exposes ONLY submit(); the bridge completes a full
    pass against it — proof it needs no dispatch/sandbox/trace surface."""
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    assert len(fake.submit_calls) == 1
    assert execution.result.direct_tool_dispatch_called is False
    # the fake has no dispatch attribute at all — nothing could have bypassed
    assert not hasattr(fake, "dispatch")
    assert not hasattr(fake, "tools")


def test_runtime_bridge_does_not_call_tool_runtime_directly():
    """Source-level: no aurel_exec module references the tool-dispatch layer,
    subprocess, sockets, HTTP clients, or the sandbox/trace/policy modules."""
    for module_path in sorted(_PACKAGE_DIR.glob("*.py")):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in (
            "from ..tools import",
            "from agentic_runtime.tools import",
            ".dispatch(",
            "import subprocess",
            "import socket",
            "import requests",
            "import httpx",
            "import urllib",
            "from ..sandbox",
            "from agentic_runtime.sandbox",
            "from ..trace import",
            "from agentic_runtime.trace import",
            "from ..policy import",
            "from ..custos",
            "from ..memory import",
            "open(",
            "os.system",
            "eval(",
            "exec(",
        ):
            assert forbidden not in source, f"{module_path.name} contains {forbidden!r}"


def test_no_direct_dispatch_proof_is_fail_closed():
    proof = build_no_direct_dispatch_proof()
    assert proof.reason == DIRECT_DISPATCH_FORBIDDEN_REASON
    for boundary_field in (
        "direct_tool_runtime_dispatch_called",
        "direct_subprocess_called",
        "direct_network_called",
        "direct_raw_filesystem_execution_called",
        "direct_sandbox_execution_called",
        "direct_model_invoked",
        "direct_verifier_executed",
        "manual_trace_write",
        "manual_ledger_write",
        "manual_policy_enforced",
        "manual_custos_enforced",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_blocked_submits_perform_nothing():
    """Every validation failure raises BEFORE the kernel is touched."""
    _, _, job, lease, session, attempt = build_bound_slice(expires_at_tick=4)
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    with pytest.raises(AurelExecValidationError):
        bridge.submit_once(
            request, job=job, lease=lease, session=session, attempt=attempt,
            card=card, current_tick=99,  # expired
        )
    assert fake.submit_calls == []


def test_worker_queue_checkpoint_recovery_remain_unavailable():
    """No worker/queue/bus/checkpoint/recovery surface exists in the package."""
    public_names = {name.lower() for name in dir(aurel_exec) if not name.startswith("_")}
    # Updated by P4-EXEC-E: WorkerSlot/QueueClaim became sealed C-pack canon
    # (single local slot, deterministic claim — proven not a platform), so
    # those name fragments moved out of the guard; the platform-shaped
    # fragments remain forbidden. Boundary-proof objects (NoWorkerPoolProof
    # etc.) legitimately contain the fragment they negate and are excluded.
    public_names = {name for name in public_names if "proof" not in name}
    for forbidden_fragment in (
        "workerpool",
        "executionbus",
        "checkpointmanager",
        "recoveryengine",
        "selfhealing",
        "replayengine",
        "eventlog",
    ):
        assert not any(forbidden_fragment in name for name in public_names), (
            forbidden_fragment
        )
    from agentic_runtime.aurel_exec import build_dev_fixture_admission_request, decide_admission
    from agentic_runtime.aurel_exec import build_exec_projection

    projection = build_exec_projection(
        decide_admission(build_dev_fixture_admission_request())
    )
    assert projection.worker_queue_available is False
    assert projection.execution_bus_available is False
    assert projection.checkpoint_available is False
    assert projection.recovery_available is False
    for boundary_field in (
        "worker_queue_available",
        "execution_bus_available",
        "checkpoint_available",
        "recovery_available",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})

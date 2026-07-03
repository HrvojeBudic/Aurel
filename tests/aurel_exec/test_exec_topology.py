"""P4-EXEC-F topology profile tests — control-plane model, not runtime."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import agentic_runtime.aurel_exec as aurel_exec
from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecutionTopologyProfile,
    ExecTruthLabel,
    TopologyProfileKind,
    build_local_topology_profile,
    build_no_async_dispatcher_proof,
    build_no_remote_worker_proof,
    build_no_rust_rewrite_proof,
    build_no_worker_pool_proof,
)


def test_topology_profile_defaults_to_local_control_plane_shape():
    topology = build_local_topology_profile()
    # repo truth: P4-EXEC-C proved exactly one local slot
    assert topology.topology_kind is TopologyProfileKind.LOCAL_SINGLE_SLOT
    assert topology.max_local_slots == 1
    assert "P4-EXEC-C" in topology.worker_model
    bounded = build_local_topology_profile(max_local_slots=3)
    assert bounded.topology_kind is TopologyProfileKind.LOCAL_BOUNDED_WINDOW
    # deterministic ids
    assert build_local_topology_profile().topology_profile_id == topology.topology_profile_id


def test_remote_distributed_workers_and_worker_pool_are_unavailable():
    topology = build_local_topology_profile()
    for boundary_field in (
        "supports_remote_workers",
        "supports_distributed_workers",
        "supports_worker_pool",
        "supports_rust_wasm_substrate",
        "spawns_workers",
        "distributes_work",
    ):
        assert getattr(topology, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(topology, **{boundary_field: True})
    # non-local kinds are not constructible as active profiles
    for kind in (
        TopologyProfileKind.REMOTE_UNAVAILABLE,
        TopologyProfileKind.DISTRIBUTED_UNAVAILABLE,
        TopologyProfileKind.FUTURE_RUST_WASM_SUBSTRATE,
        TopologyProfileKind.ERROR,
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(topology, topology_kind=kind)
    # C-era proofs still hold and cover the F claims
    assert build_no_worker_pool_proof().worker_pool_available is False
    remote_proof = build_no_remote_worker_proof()
    assert remote_proof.remote_worker_available is False
    assert remote_proof.distributed_worker_available is False


def test_async_dispatcher_is_unavailable():
    topology = build_local_topology_profile()
    assert topology.supports_async_dispatch is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(topology, supports_async_dispatch=True)
    proof = build_no_async_dispatcher_proof()
    assert proof.async_dispatcher_available is False
    assert proof.thread_pool_available is False
    assert proof.task_scheduler_available is False
    for boundary_field in (
        "async_dispatcher_available",
        "thread_pool_available",
        "task_scheduler_available",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
    # source truth: no F module imports asyncio/threading/multiprocessing
    package_dir = Path(aurel_exec.__file__).parent
    for module_name in ("exec_topology.py", "exec_pressure.py", "exec_bench.py"):
        source = (package_dir / module_name).read_text(encoding="utf-8")
        for forbidden in (
            "import asyncio",
            "import threading",
            "import multiprocessing",
            "import concurrent",
            "import subprocess",
            "import socket",
            ".dispatch(",
            ".submit(",
            "from ..runtime import",
        ):
            assert forbidden not in source, f"{module_name} contains {forbidden!r}"


def test_rust_wasm_substrate_remains_future_unavailable():
    rust_proof = build_no_rust_rewrite_proof()  # E-era proof re-asserted
    assert rust_proof.rust_wasm_substrate_available is False
    repo_root = Path(aurel_exec.__file__).parents[3]
    for forbidden in ("Cargo.toml", "crates", "rust", "wasm"):
        assert not (repo_root / forbidden).exists(), forbidden
    topology = build_local_topology_profile()
    assert any("Rust/WASM" in reason for reason in topology.unavailable_reasons)


def test_topology_profile_validation_is_fail_closed():
    with pytest.raises(AurelExecValidationError):
        build_local_topology_profile(max_local_slots=0)
    topology = build_local_topology_profile()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(topology, max_local_slots=2)  # SINGLE_SLOT means one
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(topology, unavailable_reasons=())
    for verb in ("spawn", "execute", "run", "distribute", "route", "dispatch"):
        assert not hasattr(topology, verb)

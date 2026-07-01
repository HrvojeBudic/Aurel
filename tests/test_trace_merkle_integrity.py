"""Trace Merkle integrity semantics for InMemoryTraceLedger."""

from __future__ import annotations

from agentic_runtime.core_types import VerifierResult
from tests.conftest import make_cmd


def test_verify_chain_detects_live_record_mutation(write_kernel, card):
    write_kernel.sandbox.write_file("src/a.py", "a")
    cmd = make_cmd(card, "write_file", {"path": "src/a.py", "content": "b"})
    write_kernel.runtime.submit(cmd, card)
    assert len(write_kernel.trace) >= 1
    ok, _ = write_kernel.trace.verify_chain()
    assert ok
    entries = list(write_kernel.trace)
    idx_target = next(i for i, r in enumerate(entries) if hasattr(r, "verifier_result"))
    entries[idx_target].verifier_result = VerifierResult(True, "forged", reason="tampered")
    ok2, idx = write_kernel.trace.verify_chain()
    assert not ok2
    assert idx == idx_target


def test_merkle_root_changes_after_live_payload_mutation_when_recomputed(write_kernel, card):
    write_kernel.sandbox.write_file("src/a.py", "a")
    cmd = make_cmd(card, "write_file", {"path": "src/a.py", "content": "b"})
    write_kernel.runtime.submit(cmd, card)
    root_before = write_kernel.trace.merkle_root()
    entries = list(write_kernel.trace)
    idx_target = next(i for i, r in enumerate(entries) if hasattr(r, "verifier_result"))
    entries[idx_target].verifier_result = VerifierResult(True, "forged", reason="tampered")
    assert write_kernel.trace.merkle_root() != root_before

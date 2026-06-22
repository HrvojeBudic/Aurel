"""Trace ledger integrity tests."""

from agentic_runtime.core_types import VerifierResult
from tests.conftest import make_cmd


def test_trace_tampering_detected(write_kernel, card):
    write_kernel.sandbox.write_file("src/a.py", "a")
    cmd = make_cmd(card, "write_file", {"path": "src/a.py", "content": "b"})
    write_kernel.runtime.submit(cmd, card)
    assert len(write_kernel.trace) >= 1
    ok, _ = write_kernel.trace.verify_chain()
    assert ok
    entries = list(write_kernel.trace)
    idx_target = next(i for i, r in enumerate(entries) if hasattr(r, "verifier_result"))
    rec = entries[idx_target]
    rec.verifier_result = VerifierResult(True, "forged", reason="tampered")
    ok2, idx = write_kernel.trace.verify_chain()
    assert not ok2
    assert idx == idx_target

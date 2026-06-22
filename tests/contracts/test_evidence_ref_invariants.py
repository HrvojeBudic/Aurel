"""P1.5.11A EvidenceRef invariant tests."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.evidence import (
    EvidenceRef,
    build_evidence_ref,
    compute_evidence_content_hash,
)
from agentic_runtime.contracts.trace import AurelTraceLog, TraceEventType, trace_event_ref


def _trace_ref():
    log = AurelTraceLog(trace_id="trace_evidence_contract_test")
    event = log.append(
        event_type=TraceEventType.EVIDENCE,
        actor_type="test",
        actor_id="tester",
        payload_json={"ok": True},
        timestamp="2026-06-22T00:00:00+00:00",
    )
    return trace_event_ref(event)


def test_evidence_ref_requires_trace_event_ref():
    with pytest.raises(ValueError, match="source_trace_event_ref"):
        EvidenceRef(
            evidence_id="evidence_001",
            source_trace_event_ref=None,  # type: ignore[arg-type]
            evidence_type="stub",
            content_hash="hash",
            summary="missing trace ref",
        )


def test_evidence_hash_is_deterministic():
    first = compute_evidence_content_hash({"b": 2, "a": 1})
    second = compute_evidence_content_hash({"a": 1, "b": 2})
    assert first == second

    ref = _trace_ref()
    evidence = build_evidence_ref(
        evidence_id="evidence_001",
        source_trace_event_ref=ref,
        evidence_type="stub_execution",
        content={"b": 2, "a": 1},
        summary="deterministic evidence",
    )
    assert evidence.content_hash == first
    assert evidence.source_trace_event_ref == ref


def test_evidence_ref_cannot_claim_canonical_status():
    with pytest.raises(ValueError, match="cannot claim canonical"):
        EvidenceRef(
            evidence_id="evidence_001",
            source_trace_event_ref=_trace_ref(),
            evidence_type="stub",
            content_hash="hash",
            summary="bad canonical claim",
            is_canonical=True,
        )

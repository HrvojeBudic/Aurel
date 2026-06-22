"""P1.5.2 anti-scope-creep tests."""
from __future__ import annotations

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceStatus,
    P152_INVARIANTS,
    capability_evidence_from_evaluation_result,
    example_usable_evidence_from_result,
)
from agentic_runtime.evaluation.evaluation_objects import example_supported_evaluation_result


def test_p152_does_not_verify_capability():
    rec = example_usable_evidence_from_result()
    assert rec.status != CapabilityEvidenceStatus.USABLE or rec.status.value != "VERIFIED"
    assert "VERIFIED" not in {v.value for v in CapabilityEvidenceStatus}
    assert not hasattr(rec, "verified")
    assert not hasattr(rec, "capability_verified")


def test_p152_does_not_modify_capability_claim_decision():
    # Evidence record is read-only container — no claim mutation API
    rec = example_usable_evidence_from_result()
    assert not hasattr(rec, "mutate_claim")
    assert not hasattr(rec, "claim_status")


def test_p152_does_not_introduce_numeric_capability_score():
    rec = example_usable_evidence_from_result()
    for name in rec.__dataclass_fields__:
        assert "score" not in name.lower() or rec.__dataclass_fields__[name].type not in (int, float)


def test_p152_does_not_run_benchmarks():
    text = " ".join(P152_INVARIANTS).lower()
    assert "benchmark runner" not in text


def test_p152_prepares_p157_evidence_to_claim_binding():
    text = " ".join(P152_INVARIANTS)
    assert "P1.5.7" in text or "P1.5.3" in text

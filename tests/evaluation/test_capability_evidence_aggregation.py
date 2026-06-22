"""P1.5.2 capability evidence aggregation tests."""
from __future__ import annotations

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
    aggregate_capability_evidence_records,
    capability_evidence_from_evaluation_result,
    example_usable_evidence_from_result,
)


def _rec(eid, status, strength, refs=("r1",)):
    return CapabilityEvidenceRecord(
        evidence_id=eid, kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=status, strength=strength,
        source_result_ids=refs, summary="",
    )


def test_aggregate_empty_records_insufficient_or_invalid():
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=())
    assert rs.aggregate_status == CapabilityEvidenceStatus.INSUFFICIENT
    assert rs.blockers


def test_aggregate_usable_records_to_usable():
    rec = example_usable_evidence_from_result()
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(rec,))
    assert rs.aggregate_status == CapabilityEvidenceStatus.USABLE


def test_aggregate_conflicted_blocks_usable():
    usable = example_usable_evidence_from_result()
    conflicted = _rec("ev2", CapabilityEvidenceStatus.CONFLICTED, CapabilityEvidenceStrength.CONFLICTED)
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(usable, conflicted))
    assert rs.aggregate_status != CapabilityEvidenceStatus.USABLE


def test_aggregate_revoked_blocks_usable():
    usable = example_usable_evidence_from_result()
    revoked = _rec("ev2", CapabilityEvidenceStatus.REVOKED, CapabilityEvidenceStrength.NONE)
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(usable, revoked))
    assert rs.aggregate_status != CapabilityEvidenceStatus.USABLE


def test_aggregate_invalid_blocks_usable():
    usable = example_usable_evidence_from_result()
    invalid = _rec("ev2", CapabilityEvidenceStatus.INVALID, CapabilityEvidenceStrength.NONE)
    invalid = CapabilityEvidenceRecord(
        evidence_id="ev2", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.INVALID, strength=CapabilityEvidenceStrength.NONE,
        blockers=("invalid",), summary="",
    )
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(usable, invalid))
    assert rs.aggregate_status == CapabilityEvidenceStatus.INVALID


def test_aggregate_expired_degrades():
    stale = _rec("ev1", CapabilityEvidenceStatus.STALE, CapabilityEvidenceStrength.WEAK)
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(stale,))
    assert rs.aggregate_status == CapabilityEvidenceStatus.STALE


def test_aggregate_stale_degrades():
    stale = _rec("ev1", CapabilityEvidenceStatus.STALE, CapabilityEvidenceStrength.WEAK)
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(stale,))
    assert rs.aggregate_strength == CapabilityEvidenceStrength.WEAK


def test_aggregate_insufficient_when_no_usable_records():
    ins = _rec("ev1", CapabilityEvidenceStatus.INSUFFICIENT, CapabilityEvidenceStrength.NONE)
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(ins,))
    assert rs.aggregate_status == CapabilityEvidenceStatus.INSUFFICIENT


def test_aggregate_strong_when_strong_usable_exists():
    strong = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE, strength=CapabilityEvidenceStrength.STRONG,
        source_result_ids=("r1",), evidence_refs=("ref1",), summary="",
    )
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(strong,))
    assert rs.aggregate_strength == CapabilityEvidenceStrength.STRONG


def test_aggregate_no_numeric_score():
    rec = example_usable_evidence_from_result()
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(rec,))
    assert not hasattr(rs, "score")
    assert not hasattr(rs, "numeric_score")

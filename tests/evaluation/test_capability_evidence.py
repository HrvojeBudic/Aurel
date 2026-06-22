"""P1.5.2 core capability evidence tests."""
from __future__ import annotations

import pytest

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
    validate_capability_evidence_record,
)


def test_capability_evidence_kind_closed_world():
    assert CapabilityEvidenceKind.EVALUATION_RESULT.value == "EVALUATION_RESULT"
    assert len(CapabilityEvidenceKind) >= 10


def test_capability_evidence_status_closed_world():
    assert CapabilityEvidenceStatus.USABLE.value == "USABLE"
    assert "VERIFIED" not in {v.value for v in CapabilityEvidenceStatus}
    assert len(CapabilityEvidenceStatus) >= 10


def test_capability_evidence_strength_closed_world():
    assert CapabilityEvidenceStrength.ADEQUATE.value == "ADEQUATE"
    assert len(CapabilityEvidenceStrength) >= 6


def test_build_capability_evidence_record():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.ADEQUATE,
        source_result_ids=("r1",), evidence_refs=("ref1",),
        summary="test",
    )
    assert rec.evidence_id == "ev1"
    assert validate_capability_evidence_record(rec) == ()


def test_validate_record_rejects_empty_id():
    rec = CapabilityEvidenceRecord(
        evidence_id="", kind=CapabilityEvidenceKind.UNKNOWN,
        status=CapabilityEvidenceStatus.DRAFT,
        strength=CapabilityEvidenceStrength.NONE, summary="",
    )
    assert any("evidence_id" in e for e in validate_capability_evidence_record(rec))


def test_validate_usable_requires_adequate_or_strong_strength():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.WEAK,
        source_result_ids=("r1",), summary="",
    )
    assert any("ADEQUATE" in e for e in validate_capability_evidence_record(rec))


def test_validate_usable_requires_source_or_evidence_refs():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.ADEQUATE,
        summary="",
    )
    assert any("source" in e.lower() or "evidence_refs" in e for e in validate_capability_evidence_record(rec))


def test_validate_conflicted_requires_warning_or_blocker():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.CONFLICTED,
        strength=CapabilityEvidenceStrength.CONFLICTED,
        summary="",
    )
    assert any("CONFLICTED" in e for e in validate_capability_evidence_record(rec))


def test_validate_invalid_requires_blocker():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.INVALID,
        strength=CapabilityEvidenceStrength.NONE,
        summary="",
    )
    assert any("blocker" in e for e in validate_capability_evidence_record(rec))


def test_validate_revoked_cannot_be_usable():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.REVOKED,
        strength=CapabilityEvidenceStrength.NONE,
        summary="",
    )
    assert rec.status != CapabilityEvidenceStatus.USABLE


def test_validate_expired_cannot_be_usable():
    rec = CapabilityEvidenceRecord(
        evidence_id="ev1", kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.EXPIRED,
        strength=CapabilityEvidenceStrength.WEAK,
        summary="",
    )
    assert rec.status != CapabilityEvidenceStatus.USABLE

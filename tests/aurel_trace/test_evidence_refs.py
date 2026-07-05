"""P5.10 — EvidenceRef / Proof object model."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    EvidenceKind,
    EvidenceRef,
    EvidenceStatus,
    TraceTruthLabel,
    evidence_ref_has_no_authority,
    make_evidence_ref,
    make_missing_evidence_ref,
)


def test_evidence_ref_id_is_deterministic():
    a = make_evidence_ref(
        evidence_kind=EvidenceKind.COMMAND_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="cmd-1",
    )
    b = make_evidence_ref(
        evidence_kind=EvidenceKind.COMMAND_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="cmd-1",
    )
    assert a.evidence_ref_id == b.evidence_ref_id


def test_different_source_yields_different_id():
    a = make_evidence_ref(
        evidence_kind=EvidenceKind.COMMAND_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="cmd-1",
    )
    b = make_evidence_ref(
        evidence_kind=EvidenceKind.COMMAND_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="cmd-2",
    )
    assert a.evidence_ref_id != b.evidence_ref_id


def test_missing_evidence_carries_reason():
    ref = make_missing_evidence_ref(
        evidence_kind=EvidenceKind.MEMORY_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="MEMORY_WRITE_RECORDED",
        missing_reason="no discrete memory-write record on the observed path",
    )
    assert ref.status is EvidenceStatus.MISSING
    assert ref.missing_reason
    assert ref.is_present is False


def test_missing_status_without_reason_fails_closed():
    with pytest.raises(AurelTraceError):
        EvidenceRef(
            evidence_ref_id="e",
            evidence_kind=EvidenceKind.MEMORY_EVIDENCE,
            source_domain="d",
            source_object_id="o",
            status=EvidenceStatus.MISSING,
        )


def test_unknown_evidence_kind_fails_closed():
    with pytest.raises(AurelTraceError):
        make_evidence_ref(
            evidence_kind="NOT_A_KIND",  # type: ignore[arg-type]
            source_domain="d",
            source_object_id="o",
        )


def test_evidence_ref_without_receipt_is_not_integrity_verified():
    ref = make_evidence_ref(
        evidence_kind=EvidenceKind.VERIFIER_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="VERIFIER_RESULT_RECORDED",
    )
    assert ref.truth_label is TraceTruthLabel.TRACE_BOUND
    # A hand-built ref cannot claim the integrity label without a receipt id.
    with pytest.raises(AurelTraceError):
        EvidenceRef(
            evidence_ref_id="e",
            evidence_kind=EvidenceKind.VERIFIER_EVIDENCE,
            source_domain="d",
            source_object_id="o",
            status=EvidenceStatus.TRACE_INTEGRITY_VERIFIED,
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )


def test_receipt_backed_ref_may_be_integrity_verified():
    ref = make_evidence_ref(
        evidence_kind=EvidenceKind.SANDBOX_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="SANDBOX_BEFORE_HASH_RECORDED",
        verification_receipt_id="trcpt-abc123",
    )
    assert ref.status is EvidenceStatus.TRACE_INTEGRITY_VERIFIED
    assert ref.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED


def test_no_trace_verified_label_exists():
    assert not hasattr(TraceTruthLabel, "TRACE_VERIFIED")


def test_evidence_ref_grants_no_authority():
    ref = make_evidence_ref(
        evidence_kind=EvidenceKind.APPROVAL_EVIDENCE,
        source_domain="runtime.submit",
        source_object_id="HITL_DECISION_RECORDED",
    )
    assert evidence_ref_has_no_authority(ref) is True

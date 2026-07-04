"""P5.4 — Hash Chain Verification Kernel v1."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    HashChainVerificationSummary,
    TraceHashFinding,
    TraceHashFindingKind,
    TraceHashVerificationRequest,
    TraceHashVerificationResult,
    TraceTruthLabel,
    TraceVerificationScope,
    TraceVerificationStatus,
    verify_canonical_trace_hash_chain,
    verify_trace_records,
)


def _request(run_ref, scope=TraceVerificationScope.FULL_CHAIN, **kw):
    return TraceHashVerificationRequest(
        verification_request_id="vr-test",
        trace_run_ref=run_ref,
        scope=scope,
        **kw,
    )


def test_valid_full_chain_passes(demo_run_ref, demo_envelopes):
    result = verify_canonical_trace_hash_chain(_request(demo_run_ref), demo_envelopes)
    assert result.status is TraceVerificationStatus.PASS
    assert result.verified is True
    assert result.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
    assert result.invalid_count == 0
    assert result.valid_count == len(demo_envelopes)
    assert result.findings == ()


def test_broken_previous_hash_fails_with_finding(demo_run_ref, demo_envelopes):
    tampered = dataclasses.replace(
        demo_envelopes[2], previous_entry_hash="0" * 64
    )
    envelopes = demo_envelopes[:2] + (tampered,) + demo_envelopes[3:]
    result = verify_canonical_trace_hash_chain(_request(demo_run_ref), envelopes)
    assert result.status is TraceVerificationStatus.FAIL
    assert result.verified is False
    assert result.first_invalid_index == 2
    kinds = {f.finding_kind for f in result.findings}
    assert TraceHashFindingKind.BROKEN_PREVIOUS_HASH in kinds


def test_payload_tamper_fails_with_entry_hash_mismatch(demo_run_ref, demo_envelopes):
    tampered = dataclasses.replace(demo_envelopes[1], payload_hash="deadbeef" * 8)
    envelopes = (demo_envelopes[0], tampered) + demo_envelopes[2:]
    result = verify_canonical_trace_hash_chain(_request(demo_run_ref), envelopes)
    assert result.status is TraceVerificationStatus.FAIL
    kinds = {f.finding_kind for f in result.findings}
    assert TraceHashFindingKind.ENTRY_HASH_MISMATCH in kinds


def test_chain_head_scope_matches_and_mismatches(demo_run_ref, demo_envelopes):
    head = demo_envelopes[-1].entry_hash
    ok = verify_canonical_trace_hash_chain(
        _request(demo_run_ref, TraceVerificationScope.CHAIN_HEAD, expected_chain_head=head),
        demo_envelopes,
    )
    assert ok.status is TraceVerificationStatus.PASS
    assert ok.chain_head_hash == head

    bad = verify_canonical_trace_hash_chain(
        _request(
            demo_run_ref,
            TraceVerificationScope.CHAIN_HEAD,
            expected_chain_head="not-the-head",
        ),
        demo_envelopes,
    )
    assert bad.status is TraceVerificationStatus.FAIL
    assert TraceHashFindingKind.CHAIN_HEAD_MISMATCH in {
        f.finding_kind for f in bad.findings
    }


def test_single_entry_and_segment_scopes(demo_run_ref, demo_envelopes):
    single = verify_canonical_trace_hash_chain(
        _request(demo_run_ref, TraceVerificationScope.SINGLE_ENTRY, start_index=1),
        demo_envelopes,
    )
    assert single.status is TraceVerificationStatus.PASS
    assert single.checked_count == 1

    segment = verify_canonical_trace_hash_chain(
        _request(
            demo_run_ref,
            TraceVerificationScope.SEGMENT,
            start_index=1,
            end_index=2,
        ),
        demo_envelopes,
    )
    assert segment.status is TraceVerificationStatus.PASS
    assert segment.checked_count == 2


def test_empty_envelopes_is_unavailable(demo_run_ref):
    result = verify_canonical_trace_hash_chain(_request(demo_run_ref), ())
    assert result.status is TraceVerificationStatus.UNAVAILABLE
    assert TraceHashFindingKind.INSUFFICIENT_DATA in {
        f.finding_kind for f in result.findings
    }


def test_unsupported_record_yields_partial_not_pass(demo_run_ref, demo_ledger):
    records = list(demo_ledger) + [{"totally": "unsupported"}]
    result = verify_trace_records(_request(demo_run_ref), records)
    assert result.status is TraceVerificationStatus.PARTIAL
    assert result.status is not TraceVerificationStatus.PASS
    assert TraceHashFindingKind.UNSUPPORTED_RECORD_TYPE in {
        f.finding_kind for f in result.findings
    }


def test_verify_trace_records_full_valid_chain_passes(demo_run_ref, demo_ledger):
    result = verify_trace_records(_request(demo_run_ref), list(demo_ledger))
    assert result.status is TraceVerificationStatus.PASS
    assert result.verified is True


def test_pass_result_is_unconstructible_when_invalid():
    # a PASS status with invalid entries cannot be constructed
    with pytest.raises(AurelTraceError):
        TraceHashVerificationResult(
            verification_result_id="r",
            request_id="vr",
            status=TraceVerificationStatus.PASS,
            verified=True,
            checked_count=1,
            valid_count=0,
            invalid_count=1,
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )
    # a non-PASS status may not carry the integrity-verified label
    with pytest.raises(AurelTraceError):
        TraceHashVerificationResult(
            verification_result_id="r",
            request_id="vr",
            status=TraceVerificationStatus.FAIL,
            verified=False,
            checked_count=1,
            valid_count=0,
            invalid_count=1,
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )


def test_no_auto_repair_findings_are_evidence_only(demo_run_ref, demo_envelopes):
    tampered = dataclasses.replace(demo_envelopes[1], payload_hash="beefbeef" * 8)
    envelopes = (demo_envelopes[0], tampered) + demo_envelopes[2:]
    result = verify_canonical_trace_hash_chain(_request(demo_run_ref), envelopes)
    # verification does not mutate the input envelopes (no repair)
    assert envelopes[1].payload_hash == "beefbeef" * 8
    assert result.status is TraceVerificationStatus.FAIL
    for finding in result.findings:
        assert isinstance(finding, TraceHashFinding)


def test_summary_aggregates_results(demo_run_ref, demo_envelopes):
    good = verify_canonical_trace_hash_chain(_request(demo_run_ref), demo_envelopes)
    tampered = dataclasses.replace(demo_envelopes[1], payload_hash="cafe" * 16)
    bad = verify_canonical_trace_hash_chain(
        _request(demo_run_ref), (demo_envelopes[0], tampered) + demo_envelopes[2:]
    )
    summary = HashChainVerificationSummary(summary_id="s1", results=(good, bad))
    assert summary.total_results == 2
    assert summary.pass_count == 1
    assert summary.fail_count == 1
    assert summary.all_passed is False


def test_request_scope_validation():
    from agentic_runtime.aurel_trace import build_trace_run_ref

    run_ref = build_trace_run_ref(trace_run_id="r", ledger_backend="mem")
    with pytest.raises(AurelTraceError):
        TraceHashVerificationRequest(
            verification_request_id="vr",
            trace_run_ref=run_ref,
            scope=TraceVerificationScope.SEGMENT,
        )
    with pytest.raises(AurelTraceError):
        TraceHashVerificationRequest(
            verification_request_id="vr",
            trace_run_ref=run_ref,
            scope=TraceVerificationScope.CHAIN_HEAD,
        )

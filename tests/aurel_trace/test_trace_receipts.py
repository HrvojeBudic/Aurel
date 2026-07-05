"""P5.5 — Verification receipts / verified ranges / checkpoint & head receipts."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceHashVerificationRequest,
    TraceTruthLabel,
    TraceVerificationScope,
    TraceVerificationStatus,
    build_trace_chain_head_receipt,
    build_trace_checkpoint_receipt,
    build_trace_verification_receipt,
    build_verified_trace_range,
    verify_canonical_trace_hash_chain,
)


def _request(run_ref, scope=TraceVerificationScope.FULL_CHAIN, **kw):
    return TraceHashVerificationRequest(
        verification_request_id="vr-receipt",
        trace_run_ref=run_ref,
        scope=scope,
        **kw,
    )


def _pass_result(run_ref, envelopes):
    request = _request(run_ref)
    return request, verify_canonical_trace_hash_chain(request, envelopes)


def test_pass_result_yields_integrity_verified_receipt(demo_run_ref, demo_envelopes):
    request, result = _pass_result(demo_run_ref, demo_envelopes)
    assert result.status is TraceVerificationStatus.PASS
    receipt = build_trace_verification_receipt(result, request)
    assert receipt.verified is True
    assert receipt.status is TraceVerificationStatus.PASS
    assert receipt.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
    assert receipt.checked_count == result.checked_count
    assert receipt.finding_count == 0


def test_fail_result_receipt_does_not_upgrade(demo_run_ref, demo_envelopes):
    tampered = dataclasses.replace(demo_envelopes[1], payload_hash="dead" * 16)
    envelopes = (demo_envelopes[0], tampered) + demo_envelopes[2:]
    request = _request(demo_run_ref)
    result = verify_canonical_trace_hash_chain(request, envelopes)
    assert result.status is TraceVerificationStatus.FAIL
    receipt = build_trace_verification_receipt(result, request)
    assert receipt.verified is False
    assert receipt.status is TraceVerificationStatus.FAIL
    assert receipt.truth_label is TraceTruthLabel.TRACE_BOUND
    assert receipt.finding_count == len(result.findings)


def test_receipt_cannot_claim_pass_without_pass_status():
    # A hand-built receipt cannot mark verified=True for a non-PASS status.
    from agentic_runtime.aurel_trace import TraceRunRef, TraceVerificationReceipt

    run = TraceRunRef(trace_run_id="r", ledger_backend="mem")
    with pytest.raises(AurelTraceError):
        TraceVerificationReceipt(
            receipt_id="x",
            verification_result_id="v",
            trace_run_ref=run,
            verification_scope=TraceVerificationScope.FULL_CHAIN,
            verified=True,
            status=TraceVerificationStatus.FAIL,
            checked_count=1,
            finding_count=1,
            receipt_hash="h",
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )
    # And a non-PASS receipt cannot carry the integrity-verified label.
    with pytest.raises(AurelTraceError):
        TraceVerificationReceipt(
            receipt_id="x",
            verification_result_id="v",
            trace_run_ref=run,
            verification_scope=TraceVerificationScope.FULL_CHAIN,
            verified=False,
            status=TraceVerificationStatus.FAIL,
            checked_count=1,
            finding_count=1,
            receipt_hash="h",
            truth_label=TraceTruthLabel.TRACE_INTEGRITY_VERIFIED,
        )


def test_receipt_hash_is_deterministic(demo_run_ref, demo_envelopes):
    request, result = _pass_result(demo_run_ref, demo_envelopes)
    a = build_trace_verification_receipt(result, request)
    b = build_trace_verification_receipt(result, request)
    assert a.receipt_hash == b.receipt_hash
    assert a.receipt_id == b.receipt_id


def test_created_at_is_metadata_only(demo_run_ref, demo_envelopes):
    request, result = _pass_result(demo_run_ref, demo_envelopes)
    a = build_trace_verification_receipt(result, request, created_at="2026-01-01T00:00:00Z")
    b = build_trace_verification_receipt(result, request, created_at="2099-12-31T23:59:59Z")
    assert a.receipt_hash == b.receipt_hash
    assert a.created_at != b.created_at


def test_changing_chain_head_changes_receipt_hash(demo_run_ref, demo_envelopes):
    request, result = _pass_result(demo_run_ref, demo_envelopes)
    base = build_trace_verification_receipt(result, request)
    shifted = dataclasses.replace(result, chain_head_hash="different-head")
    other = build_trace_verification_receipt(shifted, request)
    assert base.receipt_hash != other.receipt_hash


def test_verified_range_rejects_inverted_bounds(demo_run_ref):
    with pytest.raises(AurelTraceError):
        build_verified_trace_range(
            trace_run_ref=demo_run_ref,
            start_index=5,
            end_index=2,
            end_hash="h",
            checked_count=1,
        )


def test_verified_range_checked_count_must_match(demo_run_ref):
    with pytest.raises(AurelTraceError):
        build_verified_trace_range(
            trace_run_ref=demo_run_ref,
            start_index=0,
            end_index=3,
            end_hash="h",
            checked_count=99,
        )


def test_checkpoint_receipt_is_not_replay(demo_run_ref, demo_envelopes):
    request, result = _pass_result(demo_run_ref, demo_envelopes)
    receipt = build_trace_verification_receipt(result, request)
    rng = build_verified_trace_range(
        trace_run_ref=demo_run_ref,
        start_index=0,
        end_index=len(demo_envelopes) - 1,
        end_hash=result.chain_head_hash,
        checked_count=len(demo_envelopes),
    )
    checkpoint = build_trace_checkpoint_receipt(receipt, rng)
    assert checkpoint.is_replay_checkpoint is False
    assert checkpoint.is_snapshot_restore is False
    assert checkpoint.enables_workflow_fork is False
    assert checkpoint.source_verification_receipt_id == receipt.receipt_id


def test_checkpoint_requires_pass_receipt(demo_run_ref, demo_envelopes):
    tampered = dataclasses.replace(demo_envelopes[1], payload_hash="beef" * 16)
    envelopes = (demo_envelopes[0], tampered) + demo_envelopes[2:]
    request = _request(demo_run_ref)
    fail_result = verify_canonical_trace_hash_chain(request, envelopes)
    fail_receipt = build_trace_verification_receipt(fail_result, request)
    rng = build_verified_trace_range(
        trace_run_ref=demo_run_ref,
        start_index=0,
        end_index=len(envelopes) - 1,
        end_hash=fail_result.chain_head_hash,
        checked_count=len(envelopes),
    )
    with pytest.raises(AurelTraceError):
        build_trace_checkpoint_receipt(fail_receipt, rng)


def test_chain_head_receipt_identity_tracks_count_and_head(demo_run_ref, demo_envelopes):
    request, result = _pass_result(demo_run_ref, demo_envelopes)
    receipt = build_trace_verification_receipt(result, request)
    base = build_trace_chain_head_receipt(receipt, event_count=len(demo_envelopes))
    more = build_trace_chain_head_receipt(receipt, event_count=len(demo_envelopes) + 1)
    assert base.chain_head_hash == result.chain_head_hash
    assert base.receipt_hash != more.receipt_hash

    shifted = dataclasses.replace(result, chain_head_hash="other-head")
    shifted_receipt = build_trace_verification_receipt(shifted, request)
    shifted_head = build_trace_chain_head_receipt(
        shifted_receipt, event_count=len(demo_envelopes)
    )
    assert shifted_head.receipt_hash != base.receipt_hash

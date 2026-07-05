"""P5.19 — Persistent trace backend integrity posture (assessment only)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    PersistentTraceBackendKind,
    PersistentTraceBackendProfile,
    PersistentTraceBackendStatus,
    assess_persistent_trace_backend,
    profile_persistent_trace_backend,
)
from agentic_runtime.aurel_trace.persistent_integrity import LOCAL_DURABLE_LIMITATION


def test_in_memory_is_dev_only_durability_unsupported():
    profile = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.IN_MEMORY
    )
    assert profile.backend_status is PersistentTraceBackendStatus.DEV_ONLY
    assessment = assess_persistent_trace_backend(profile)
    assert "append_only" in assessment.checks_unsupported
    assert "fsync_durability" in assessment.checks_unsupported


def test_jsonl_local_durable_only_with_integrity_checks():
    durable = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.JSONL,
        append_only_claim=True,
        hash_chain_supported=True,
        fsync_claim=True,
    )
    assert durable.backend_status is PersistentTraceBackendStatus.LOCAL_DURABLE
    assert LOCAL_DURABLE_LIMITATION in durable.limitations
    partial = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.JSONL
    )
    assert partial.backend_status is PersistentTraceBackendStatus.PARTIAL


def test_file_system_partial_without_checks():
    partial = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.FILE_SYSTEM, hash_chain_supported=True
    )
    assert partial.backend_status is PersistentTraceBackendStatus.PARTIAL


def test_external_db_unavailable_unless_profiled():
    unprofiled = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.EXTERNAL_DB
    )
    assert unprofiled.backend_status is PersistentTraceBackendStatus.UNAVAILABLE


def test_unknown_backend_unsupported():
    unknown = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.UNKNOWN
    )
    assert unknown.backend_status is PersistentTraceBackendStatus.UNSUPPORTED


def test_local_durable_is_not_a_production_ledger():
    # The profile records the limitation; and the profile cannot be a ledger.
    durable = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.JSONL,
        append_only_claim=True,
        hash_chain_supported=True,
        fsync_claim=True,
    )
    assert durable.is_distributed_ledger is False
    assert durable.certifies_durability is False
    assert any("not" in lim.lower() and "ledger" in lim.lower() for lim in durable.limitations)


def test_assessment_lists_missing_guarantees():
    profile = profile_persistent_trace_backend(
        backend_kind=PersistentTraceBackendKind.JSONL, hash_chain_supported=True
    )
    assessment = assess_persistent_trace_backend(profile)
    assert "hash_chain" in assessment.checks_passed
    assert assessment.checks_missing  # some guarantees missing
    assert assessment.limitations


def test_profile_cannot_migrate_or_certify():
    with pytest.raises(AurelTraceError):
        PersistentTraceBackendProfile(
            profile_id="p",
            backend_kind=PersistentTraceBackendKind.JSONL,
            backend_status=PersistentTraceBackendStatus.PARTIAL,
            migrates_storage=True,
        )
    with pytest.raises(AurelTraceError):
        PersistentTraceBackendProfile(
            profile_id="p",
            backend_kind=PersistentTraceBackendKind.JSONL,
            backend_status=PersistentTraceBackendStatus.PARTIAL,
            is_distributed_ledger=True,
        )

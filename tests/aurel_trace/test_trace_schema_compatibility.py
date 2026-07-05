"""P5.6 — Trace schema compatibility decisions and declared-only upcaster."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceEventUpcasterContract,
    TraceSchemaCompatibility,
    TraceSchemaCompatibilityDecision,
    TraceSchemaDescriptor,
    TraceSchemaRegistry,
    TraceSchemaStatus,
    TraceUpcasterStatus,
    build_default_trace_schema_registry,
)


def test_compatible_decision_is_deterministic():
    registry = build_default_trace_schema_registry()
    a = registry.decide("StateTransitionRecord")
    b = registry.decide("StateTransitionRecord")
    assert a.decision is TraceSchemaCompatibility.COMPATIBLE
    assert a.decision_id == b.decision_id


def test_unsupported_decision_includes_reason():
    registry = build_default_trace_schema_registry()
    unsupported_type = registry.unsupported_record_types[0]
    decision = registry.decide(unsupported_type)
    assert decision.decision is TraceSchemaCompatibility.UNSUPPORTED
    assert decision.reason.strip()


def test_version_mismatch_yields_compatible_with_warnings():
    registry = build_default_trace_schema_registry()
    decision = registry.decide("StateTransitionRecord", schema_version="some.other.v9")
    assert decision.decision is TraceSchemaCompatibility.COMPATIBLE_WITH_WARNINGS
    assert decision.reason.strip()


def test_deprecated_schema_requires_declared_only_upcaster():
    # Build a registry with one DEPRECATED descriptor to exercise the path.
    descriptor = TraceSchemaDescriptor(
        schema_id="s-dep",
        schema_name="LegacyRecord",
        schema_version="legacy.v0",
        record_type="LegacyRecord",
        required_fields=("id",),
        status=TraceSchemaStatus.DEPRECATED,
    )
    registry = TraceSchemaRegistry(
        registry_id="reg-test",
        schema_descriptors=(descriptor,),
        default_schema_version="core.v1",
        supported_record_types=(),
    )
    decision = registry.decide("LegacyRecord")
    assert decision.decision is TraceSchemaCompatibility.REQUIRES_UPCASTER
    assert decision.required_upcaster is not None
    assert decision.required_upcaster.status in (
        TraceUpcasterStatus.DECLARED_ONLY,
        TraceUpcasterStatus.UNAVAILABLE,
    )


def test_upcaster_contract_is_declared_only_by_default():
    upcaster = TraceEventUpcasterContract(
        upcaster_id="up-1",
        from_schema="a.v0",
        to_schema="a.v1",
    )
    assert upcaster.status is TraceUpcasterStatus.DECLARED_ONLY
    assert upcaster.rewrites_records is False
    assert upcaster.migrates_records is False


def test_upcaster_cannot_be_supported_in_p5b():
    with pytest.raises(AurelTraceError):
        TraceEventUpcasterContract(
            upcaster_id="up-1",
            from_schema="a.v0",
            to_schema="a.v1",
            status=TraceUpcasterStatus.SUPPORTED,
        )


def test_upcaster_cannot_claim_record_migration():
    with pytest.raises(AurelTraceError):
        TraceEventUpcasterContract(
            upcaster_id="up-1",
            from_schema="a.v0",
            to_schema="a.v1",
            migrates_records=True,
        )


def test_non_compatible_decision_requires_reason():
    with pytest.raises(AurelTraceError):
        TraceSchemaCompatibilityDecision(
            decision_id="d1",
            record_type="X",
            schema_version=None,
            decision=TraceSchemaCompatibility.UNSUPPORTED,
            reason="",
        )

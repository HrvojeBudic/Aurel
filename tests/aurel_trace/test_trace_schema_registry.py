"""P5.6 — Trace schema registry (closed-world, no silent fallback)."""

from __future__ import annotations

from agentic_runtime.aurel_trace import (
    TraceSchemaCompatibility,
    TraceSchemaStatus,
    TraceTruthLabel,
    build_default_trace_schema_registry,
    build_existing_trace_inventory,
)


def test_known_record_type_resolves_to_descriptor():
    registry = build_default_trace_schema_registry()
    descriptors = {d.record_type: d for d in registry.schema_descriptors}
    assert "StateTransitionRecord" in descriptors
    assert descriptors["StateTransitionRecord"].status is TraceSchemaStatus.SUPPORTED


def test_supported_types_align_with_inventory():
    inventory = build_existing_trace_inventory()
    registry = build_default_trace_schema_registry(inventory)
    assert set(registry.supported_record_types) == set(inventory.supported_record_types)
    supported = {
        d.record_type
        for d in registry.schema_descriptors
        if d.status is TraceSchemaStatus.SUPPORTED
    }
    assert supported == set(inventory.supported_record_types)


def test_unsupported_types_are_catalogued_from_inventory():
    inventory = build_existing_trace_inventory()
    registry = build_default_trace_schema_registry(inventory)
    unsupported = {
        d.record_type
        for d in registry.schema_descriptors
        if d.status is TraceSchemaStatus.UNSUPPORTED
    }
    assert unsupported == set(inventory.unsupported_record_types)


def test_unknown_record_type_does_not_pass():
    registry = build_default_trace_schema_registry()
    decision = registry.decide("NoSuchRecordType")
    assert decision.decision is TraceSchemaCompatibility.UNKNOWN
    assert decision.reason  # explicit reason, never silent


def test_no_silent_fallback_to_default_schema():
    registry = build_default_trace_schema_registry()
    decision = registry.decide("NoSuchRecordType", schema_version=registry.default_schema_version)
    # Even when the caller passes the default version, an unknown record type is
    # not silently accepted.
    assert decision.decision is TraceSchemaCompatibility.UNKNOWN
    assert registry.silent_fallback_used is False


def test_registry_is_closed_world_and_not_migration_engine():
    registry = build_default_trace_schema_registry()
    assert registry.closed_world is True
    assert registry.is_migration_engine is False
    assert registry.truth_label is TraceTruthLabel.LIVE


def test_registry_serializes_deterministically():
    a = build_default_trace_schema_registry().to_dict()
    b = build_default_trace_schema_registry().to_dict()
    assert a == b

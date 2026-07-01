"""P1.ENF-D1 Identity Kernel invariant discovery tests."""
from __future__ import annotations

from agentic_runtime.identity_kernel_invariants import (
    CANONICAL_IDENTITY_KERNEL_SOURCE,
    SELECTED_INVARIANT_IDS,
    discover_identity_kernel_invariants,
    selected_invariants_by_id,
)


def test_identity_kernel_invariants_discovered():
    discovery = discover_identity_kernel_invariants()
    assert discovery.source.path == CANONICAL_IDENTITY_KERNEL_SOURCE
    assert discovery.source.format == "yaml"
    assert len(discovery.invariants) >= 8
    assert discovery.ik_ids_found
    assert not discovery.unavailable_invariants


def test_selected_identity_invariants_are_known():
    discovery = discover_identity_kernel_invariants()
    selected = selected_invariants_by_id(discovery)
    assert tuple(sorted(selected)) == SELECTED_INVARIANT_IDS
    for invariant_id in SELECTED_INVARIANT_IDS:
        record = selected[invariant_id]
        assert record.source_path == CANONICAL_IDENTITY_KERNEL_SOURCE
        assert record.selected_for_enforcement is True
        assert record.severity == "critical"
        assert record.statement

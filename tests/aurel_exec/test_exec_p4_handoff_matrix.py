"""P4-EXEC-G handoff matrix + coverage matrix + unavailable audit tests."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    CapabilityStatus,
    P4_CAPABILITY_ROWS,
    REQUIRED_UNAVAILABLE_OWNERS,
    build_p4_capability_coverage_matrix,
    build_p4_handoff_matrix,
    build_unavailable_state_audit,
)


def test_p4_capability_coverage_matrix_covers_p4_0_through_p4_20():
    matrix = build_p4_capability_coverage_matrix()
    assert len(matrix.items) == 21
    assert [item.capability for item in matrix.items] == list(P4_CAPABILITY_ROWS)
    # every row explains itself
    for item in matrix.items:
        assert item.evidence.strip()
    # honest statuses from repo truth
    assert matrix.status_of("P4.6 runtime submit bridge") is CapabilityStatus.LIVE
    assert (
        matrix.status_of("P4.12 model execution profile")
        is CapabilityStatus.PROFILE_ONLY
    )
    assert (
        matrix.status_of("P4.13 terminal / code execution profile")
        is CapabilityStatus.UNAVAILABLE
    )
    assert (
        matrix.status_of("P4.14 verifier hook / semantic guard")
        is CapabilityStatus.PROFILE_ONLY
    )
    # a truncated or reordered matrix is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(matrix, items=matrix.items[:-1])
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(matrix, items=tuple(reversed(matrix.items)))


def test_p4_handoff_matrix_assigns_p5_p8_p9_p2_and_rust_wasm_owners():
    matrix = build_p4_handoff_matrix()
    owners = {row.owner: row.owns for row in matrix.rows}
    assert "trace verification" in owners["P5 AurelTrace"]
    assert "TRACE_VERIFIED truth" in owners["P5 AurelTrace"]
    assert "routing / model-worker coordination" in owners["P8 Atlas / coordination"]
    assert "authority / enforcement" in owners["P9 Custos"]
    assert "backpressure override authority" in owners["P9 Custos"]
    assert "operator UI projection" in owners["P2 AurelShell"]
    assert "real worker pool" in owners["Future Rust/WASM substrate"]
    assert "deterministic replay" in owners["Future Rust/WASM substrate"]
    # handoff is future ownership, never present capability
    assert matrix.handoff_is_implementation is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(matrix, handoff_is_implementation=True)
    # a matrix missing an owner is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(matrix, rows=matrix.rows[:-1])


def test_unavailable_state_audit_names_reasons_and_owners():
    audit = build_unavailable_state_audit()
    covered = {entry.system: entry for entry in audit.entries}
    assert set(covered) == set(REQUIRED_UNAVAILABLE_OWNERS)
    for system, entry in covered.items():
        assert entry.reason.strip()
        assert entry.future_owner == REQUIRED_UNAVAILABLE_OWNERS[system]
    # a truncated audit is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(audit, entries=audit.entries[:-1])
    # a wrong owner is unconstructible
    tampered = dataclasses.replace(
        audit.entries[0], future_owner="somebody else"
    )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(audit, entries=(tampered,) + audit.entries[1:])


def test_matrices_are_deterministic():
    assert (
        build_p4_capability_coverage_matrix().matrix_hash
        == build_p4_capability_coverage_matrix().matrix_hash
    )
    assert (
        build_p4_handoff_matrix().matrix_hash == build_p4_handoff_matrix().matrix_hash
    )

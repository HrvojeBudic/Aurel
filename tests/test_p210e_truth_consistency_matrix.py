from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_demo_seal import (
    MultiClientTruthDimension,
    build_multi_client_truth_consistency_matrix,
    build_p2_10_surface_coverage_matrix,
)
from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind


def test_p210e_truth_matrix_compares_required_clients_and_surfaces() -> None:
    matrix = build_multi_client_truth_consistency_matrix()

    assert matrix.clients == (
        ShellClientKind.WEB,
        ShellClientKind.DESKTOP_TAURI,
        ShellClientKind.CLI,
        ShellClientKind.TUI,
        ShellClientKind.MOBILE_FOUNDATION,
    )
    assert matrix.surfaces == (
        "Aurel CRO",
        "HQ",
        "CORP",
        "HUB",
        "IDE",
        "SYSTEM",
        "Settings",
    )
    assert matrix.consistent is True
    assert matrix.inconsistencies == ()


def test_p210e_truth_matrix_contains_all_required_dimensions() -> None:
    matrix = build_multi_client_truth_consistency_matrix()

    assert set(matrix.dimensions) == set(MultiClientTruthDimension)
    for client in matrix.clients:
        client_dimensions = {
            entry.dimension for entry in matrix.entries if entry.client_kind == client
        }
        assert client_dimensions == set(MultiClientTruthDimension)


def test_p210e_surface_coverage_matrix_is_seven_by_five() -> None:
    coverage = build_p2_10_surface_coverage_matrix()

    assert len(coverage) == 35
    assert {entry.surface for entry in coverage} == {
        "Aurel CRO",
        "HQ",
        "CORP",
        "HUB",
        "IDE",
        "SYSTEM",
        "Settings",
    }
    assert {entry.client_kind for entry in coverage} == set(ShellClientKind)


def test_p210e_surface_coverage_labels_mobile_not_started() -> None:
    coverage = build_p2_10_surface_coverage_matrix()
    mobile_entries = [
        entry for entry in coverage if entry.client_kind == ShellClientKind.MOBILE_FOUNDATION
    ]

    assert len(mobile_entries) == 7
    assert all(entry.availability is False for entry in mobile_entries)
    assert all(entry.claim_level.value == "NOT_STARTED" for entry in mobile_entries)

"""Tests for P2.10-A Shell client parity matrix."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell.multi_client_foundation import (
    ShellClientKind,
    ShellClientParityDimension,
    ShellClientTruthLabel,
    build_p2_10_a_multi_client_foundation_result,
    build_shell_client_parity_matrix,
)


def _roundtrip(obj) -> dict:
    return json.loads(json.dumps(obj.to_canonical_dict(), sort_keys=True))


def test_parity_matrix_has_all_clients_and_dimensions() -> None:
    matrix = build_shell_client_parity_matrix()
    assert len(matrix.clients) == 5
    assert len(matrix.dimensions) == 10
    assert len(matrix.entries) == 50
    assert set(matrix.clients) == set(ShellClientKind)
    assert set(matrix.dimensions) == set(ShellClientParityDimension)


def test_parity_matrix_json_serializable() -> None:
    matrix = build_shell_client_parity_matrix()
    data = _roundtrip(matrix)
    assert data["matrix_hash"] == matrix.matrix_hash
    assert "not identical ui" in data["parity_summary"].lower()


def test_parity_preserves_truth_labels_not_live() -> None:
    matrix = build_shell_client_parity_matrix()
    for entry in matrix.entries:
        if entry.supported:
            assert entry.truth_label is not ShellClientTruthLabel.LIVE
            assert entry.truth_label is not ShellClientTruthLabel.TRACE_VERIFIED


def test_parity_command_preflight_is_preflight_only() -> None:
    matrix = build_shell_client_parity_matrix()
    preflight_entries = [
        e
        for e in matrix.entries
        if e.dimension is ShellClientParityDimension.COMMAND_PREFLIGHT_VISIBLE and e.supported
    ]
    assert preflight_entries
    for entry in preflight_entries:
        assert entry.truth_label is ShellClientTruthLabel.PREFLIGHT_ONLY


def test_parity_does_not_require_identical_ui() -> None:
    result = build_p2_10_a_multi_client_foundation_result()
    summary = result.parity_matrix.parity_summary.lower()
    assert "not identical ui" in summary or "not identical ui" in summary.replace("—", "-")
    assert "same truth" in summary or "truth labels" in summary


def test_web_and_cli_both_support_surface_truth_parity() -> None:
    matrix = build_shell_client_parity_matrix()
    for client in (ShellClientKind.WEB, ShellClientKind.CLI):
        truth_entry = next(
            e
            for e in matrix.entries
            if e.client_kind is client
            and e.dimension is ShellClientParityDimension.TRUTH_LABELS_VISIBLE
        )
        surfaces_entry = next(
            e
            for e in matrix.entries
            if e.client_kind is client
            and e.dimension is ShellClientParityDimension.SURFACE_AVAILABILITY_VISIBLE
        )
        assert truth_entry.supported is True
        assert surfaces_entry.supported is True


def test_tui_has_limited_parity_with_unavailable_truth() -> None:
    matrix = build_shell_client_parity_matrix()
    tui_entries = [e for e in matrix.entries if e.client_kind is ShellClientKind.TUI]
    supported = [e for e in tui_entries if e.supported]
    assert len(supported) < len(tui_entries)
    for entry in tui_entries:
        if not entry.supported:
            assert entry.truth_label is ShellClientTruthLabel.UNAVAILABLE

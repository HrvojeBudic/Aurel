"""Read-only Shell terminal commands for P2.10-D CLI/TUI parity binding."""

from __future__ import annotations

import argparse
import json

from ..aurel_shell.terminal_shell_client import (
    OPERATOR_CANON_LAST_COMPLETED_PACK,
    OPERATOR_CANON_NEXT_NOT_STARTED,
    OPERATOR_CANON_NEXT_PACK,
    TerminalShellParityDimension,
    build_terminal_shell_parity_matrix,
    build_terminal_shell_read_model,
    serialize_terminal_shell_read_model,
    terminal_shell_read_model_to_json_safe_dict,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def format_shell_status_text() -> str:
    rm = build_terminal_shell_read_model()
    lines = [
        "Aurel Shell Terminal Client",
        f"status: {rm.terminal_client_status}",
        f"execution_disabled: {str(rm.execution_disabled).lower()}",
        f"p2_vslice_status: {rm.p2_vslice_status.value}",
        f"json_export_available: {str(rm.json_export_available).lower()}",
        f"last_completed_pack: {OPERATOR_CANON_LAST_COMPLETED_PACK}",
        f"next_pack: {rm.next_pack_pointer}",
        f"next_pack_not_started: {str(OPERATOR_CANON_NEXT_NOT_STARTED).lower()}",
        "truth_labels:",
    ]
    for label in rm.truth_label_summary:
        lines.append(f"  - {label.value}")
    lines.append("limitations:")
    for limitation in rm.limitations:
        lines.append(f"  - {limitation}")
    return "\n".join(lines)


def format_shell_clients_text() -> str:
    rm = build_terminal_shell_read_model()
    lines = ["Shell clients:"]
    for client in rm.available_clients:
        lines.append(f"  - {client.value}")
    return "\n".join(lines)


def format_shell_surfaces_text() -> str:
    rm = build_terminal_shell_read_model()
    lines = ["Shell surfaces:"]
    for surface in rm.surface_availability:
        lines.append(
            f"  - {surface.surface_id}: {surface.surface_label} "
            f"[{surface.truth_label.value}] available={str(surface.available).lower()}"
        )
    return "\n".join(lines)


def format_shell_parity_text() -> str:
    matrix = build_terminal_shell_parity_matrix()
    lines = ["CLI/TUI parity matrix:", matrix.terminal_parity_summary]
    for client in matrix.clients:
        supported = [
            entry.dimension.value
            for entry in matrix.entries
            if entry.client_kind is client and entry.supported
        ]
        lines.append(f"  - {client.value}: {', '.join(supported)}")
    if matrix.missing_parity:
        lines.append("missing parity:")
        for gap in matrix.missing_parity:
            lines.append(f"  - {gap}")
    lines.append("execution disabled:")
    for cap in matrix.execution_disabled_proof:
        lines.append(f"  - {cap}")
    return "\n".join(lines)


def format_shell_evidence_text() -> str:
    rm = build_terminal_shell_read_model()
    lines = ["Evidence refs:"]
    for ref in rm.evidence_refs:
        lines.append(f"  - {ref}")
    return "\n".join(lines)


def format_shell_run_modes_text() -> str:
    rm = build_terminal_shell_read_model()
    lines = ["Terminal local run modes:"]
    for mode in rm.local_run_modes:
        lines.append(f"  - {mode.value}")
    lines.extend(
        [
            "command_execution_exposed: false",
            "shell_live_claimed: false",
            "full_terminal_automation_claimed: false",
        ]
    )
    return "\n".join(lines)


def cmd_shell_status(args: argparse.Namespace) -> int:
    if args.json:
        rm = build_terminal_shell_read_model()
        _print_json(
            {
                "covered_pack": "P2.10-D",
                "status": rm.terminal_client_status,
                "execution_disabled": rm.execution_disabled,
                "p2_vslice_status": rm.p2_vslice_status.value,
                "last_completed_pack": OPERATOR_CANON_LAST_COMPLETED_PACK,
                "next_pack": rm.next_pack_pointer,
                "next_pack_not_started": OPERATOR_CANON_NEXT_NOT_STARTED,
                "read_model_hash": rm.read_model_hash,
            }
        )
    else:
        print(format_shell_status_text())
    return 0


def cmd_shell_clients(args: argparse.Namespace) -> int:
    rm = build_terminal_shell_read_model()
    if args.json:
        _print_json([client.value for client in rm.available_clients])
    else:
        print(format_shell_clients_text())
    return 0


def cmd_shell_surfaces(args: argparse.Namespace) -> int:
    rm = build_terminal_shell_read_model()
    if args.json:
        _print_json([surface.to_canonical_dict() for surface in rm.surface_availability])
    else:
        print(format_shell_surfaces_text())
    return 0


def cmd_shell_parity(args: argparse.Namespace) -> int:
    matrix = build_terminal_shell_parity_matrix()
    if args.json:
        _print_json(matrix.to_canonical_dict())
    else:
        print(format_shell_parity_text())
    return 0


def cmd_shell_evidence(args: argparse.Namespace) -> int:
    rm = build_terminal_shell_read_model()
    if args.json:
        _print_json({"evidence_refs": rm.evidence_refs})
    else:
        print(format_shell_evidence_text())
    return 0


def cmd_shell_run_modes(args: argparse.Namespace) -> int:
    rm = build_terminal_shell_read_model()
    if args.json:
        _print_json(
            {
                "local_run_modes": [mode.value for mode in rm.local_run_modes],
                "command_execution_exposed": False,
                "shell_live_claimed": False,
                "full_terminal_automation_claimed": False,
            }
        )
    else:
        print(format_shell_run_modes_text())
    return 0


def cmd_shell_export_json(_args: argparse.Namespace) -> int:
    print(serialize_terminal_shell_read_model(build_terminal_shell_read_model()))
    return 0


def cmd_shell_read_model(args: argparse.Namespace) -> int:
    if args.json:
        _print_json(terminal_shell_read_model_to_json_safe_dict())
    else:
        print(format_shell_status_text())
    return 0


def terminal_parity_dimension_names() -> list[str]:
    return [dimension.value for dimension in TerminalShellParityDimension]


def next_pack_pointer() -> str:
    return OPERATOR_CANON_NEXT_PACK

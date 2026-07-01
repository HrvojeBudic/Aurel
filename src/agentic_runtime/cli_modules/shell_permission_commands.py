"""Read-only Shell permission inspection CLI commands for P2.11-C."""

from __future__ import annotations

import argparse
import json

from ..aurel_shell.multi_client_foundation import ShellClientKind
from ..aurel_shell.surface_permission_inspection import (
    P2_11_C_PACK_ID,
    SurfacePermissionInspectionQuery,
    SurfacePermissionInspectionViewKind,
    build_p2_11_c_surface_permission_inspection_result,
    export_surface_permission_inspection,
    inspect_surface_permissions,
    render_surface_permission_inspection,
)
from ..aurel_shell.surface_permission_matrix import (
    SurfacePermissionAction,
    SurfacePermissionLevel,
    SurfacePermissionReason,
)
from ..aurel_shell.surface_permission_projection import build_surface_permission_read_model


def _print_json(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _parse_client(value: str | None) -> ShellClientKind | None:
    if value is None:
        return None
    return ShellClientKind(value.upper())


def _parse_action(value: str | None) -> SurfacePermissionAction | None:
    if value is None:
        return None
    return SurfacePermissionAction(value.upper())


def _parse_level(value: str | None) -> SurfacePermissionLevel | None:
    if value is None:
        return None
    return SurfacePermissionLevel(value.upper())


def _parse_reason(value: str | None) -> SurfacePermissionReason | None:
    if value is None:
        return None
    return SurfacePermissionReason(value.upper())


def _query_from_args(args: argparse.Namespace) -> SurfacePermissionInspectionQuery:
    return SurfacePermissionInspectionQuery(
        client_kind=_parse_client(getattr(args, "client", None)),
        surface_id=getattr(args, "surface", None),
        permission_action=_parse_action(getattr(args, "action", None)),
        permission_level=_parse_level(getattr(args, "level", None)),
        reason=_parse_reason(getattr(args, "reason", None)),
        evidence_status=(
            "NO_EVIDENCE" if getattr(args, "no_evidence", False) else None
        ),
        sensitive_only=getattr(args, "sensitive", False),
        no_evidence_only=getattr(args, "no_evidence", False),
        denied_only=getattr(args, "denied", False),
        future_gated_only=getattr(args, "future_gated", False),
        contract_only_only=getattr(args, "contract_only", False),
        unavailable_only=getattr(args, "unavailable", False),
        preflight_only_only=getattr(args, "preflight_only", False),
    )


def format_permissions_summary_text() -> str:
    result = build_p2_11_c_surface_permission_inspection_result()
    read_model = build_surface_permission_read_model()
    lines = [
        "Aurel Shell Permission Inspection",
        f"covered_pack: {P2_11_C_PACK_ID}",
        f"source_read_model: {read_model.read_model_hash}",
        f"next_pack: {result.handoff.next_pack}",
        f"p211d_not_done: {str(result.p211d_not_done).lower()}",
        "inspection_is_enforcement: false",
        "shell_live_claimed: false",
        "summary:",
    ]
    for item in result.handoff.inspection_summary:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def cmd_shell_permissions_summary(args: argparse.Namespace) -> int:
    if args.json:
        result = build_p2_11_c_surface_permission_inspection_result()
        _print_json(
            {
                "covered_pack": result.covered_pack,
                "source_read_model": build_surface_permission_read_model().read_model_hash,
                "next_pack": result.handoff.next_pack,
                "p211d_not_done": result.p211d_not_done,
                "inspection_is_enforcement": False,
                "shell_live_claimed": False,
                "summary": result.handoff.inspection_summary,
                "result_hash": result.result_hash,
            }
        )
    else:
        print(format_permissions_summary_text())
    return 0


def cmd_shell_permissions_clients(args: argparse.Namespace) -> int:
    read_model = build_surface_permission_read_model()
    if args.json:
        _print_json([view.to_canonical_dict() for view in read_model.client_views])
    else:
        for view in read_model.client_views:
            print(
                f"{view.client_kind.value} run_mode={view.run_mode} "
                f"visible={len(view.surfaces_visible)}"
            )
    return 0


def cmd_shell_permissions_surfaces(args: argparse.Namespace) -> int:
    read_model = build_surface_permission_read_model()
    if args.json:
        _print_json([view.to_canonical_dict() for view in read_model.surface_views])
    else:
        for view in read_model.surface_views:
            print(
                f"{view.surface_id} sensitive={str(view.sensitive_surface_flag).lower()} "
                f"visible_clients={len(view.clients_with_visibility)}"
            )
    return 0


def cmd_shell_permissions_actions(args: argparse.Namespace) -> int:
    read_model = build_surface_permission_read_model()
    if args.json:
        _print_json([view.to_canonical_dict() for view in read_model.action_views])
    else:
        for view in read_model.action_views:
            print(
                f"{view.permission_action.value} "
                f"allowed={len(view.allowed_clients_surfaces)} "
                f"denied={len(view.denied_clients_surfaces)}"
            )
    return 0


def cmd_shell_permissions_show(args: argparse.Namespace) -> int:
    query = _query_from_args(args)
    result = inspect_surface_permissions(query)
    view = render_surface_permission_inspection(result)
    if args.json:
        _print_json(
            {
                "summary": result.summary,
                "matched_entry_count": len(result.matched_entries),
                "matched_entries": [
                    entry.to_canonical_dict() for entry in result.matched_entries
                ],
                "evidence_refs": result.evidence_refs,
                "limitations": result.limitations,
            }
        )
    else:
        print(view.title)
        for row in view.rows:
            print(row)
    return 0


def cmd_shell_permissions_evidence(args: argparse.Namespace) -> int:
    query = SurfacePermissionInspectionQuery(no_evidence_only=args.no_evidence)
    result = inspect_surface_permissions(query)
    if args.json:
        _print_json(
            {
                "evidence_views": [
                    view.to_canonical_dict()
                    for view in result.matched_evidence_views
                ],
                "evidence_refs": result.evidence_refs,
            }
        )
    else:
        for view in result.matched_evidence_views:
            print(
                f"{view.source_pack} supported={len(view.entries_supported)} "
                f"no_evidence={len(view.entries_with_no_evidence)}"
            )
    return 0


def cmd_shell_permissions_sensitive(args: argparse.Namespace) -> int:
    query = SurfacePermissionInspectionQuery(sensitive_only=True)
    result = inspect_surface_permissions(query)
    if args.json:
        _print_json(
            {
                "matched_entry_count": len(result.matched_entries),
                "surface_views": [
                    view.to_canonical_dict()
                    for view in result.matched_surface_views
                ],
                "limitations": result.limitations,
            }
        )
    else:
        for view in result.matched_surface_views:
            print(f"{view.surface_id} limitations={view.limitations}")
    return 0


def cmd_shell_permissions_export(args: argparse.Namespace) -> int:
    query = _query_from_args(args)
    result = inspect_surface_permissions(query)
    export = export_surface_permission_inspection(result)
    print(export.export_payload)
    return 0

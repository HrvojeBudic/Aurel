from __future__ import annotations

from agentic_runtime.aurel_shell.multi_client_foundation import ShellClientKind
from agentic_runtime.aurel_shell.surface_permission_inspection import (
    SurfacePermissionInspectionFilter,
    SurfacePermissionInspectionQuery,
    build_surface_permission_inspection_filter,
    filter_surface_permission_read_model,
    inspect_surface_permissions,
)
from agentic_runtime.aurel_shell.surface_permission_matrix import (
    SurfacePermissionAction,
    SurfacePermissionLevel,
    SurfacePermissionReason,
)
from agentic_runtime.aurel_shell.surface_permission_projection import (
    build_surface_permission_read_model,
)


def test_p211c_filter_by_client_kind() -> None:
    read_model = build_surface_permission_read_model()
    query = SurfacePermissionInspectionQuery(client_kind=ShellClientKind.WEB)
    filter_model = build_surface_permission_inspection_filter(query)
    matched = filter_surface_permission_read_model(read_model, filter_model)

    assert matched
    assert all(entry.client_kind is ShellClientKind.WEB for entry in matched)
    assert len(matched) == 140


def test_p211c_filter_by_surface_and_action() -> None:
    read_model = build_surface_permission_read_model()
    query = SurfacePermissionInspectionQuery(
        surface_id="system",
        permission_action=SurfacePermissionAction.READ_SURFACE_STATE,
    )
    matched = filter_surface_permission_read_model(
        read_model,
        build_surface_permission_inspection_filter(query),
    )

    assert len(matched) == 5
    assert all(entry.surface_id == "system" for entry in matched)
    assert all(
        entry.permission_action is SurfacePermissionAction.READ_SURFACE_STATE
        for entry in matched
    )


def test_p211c_filter_by_permission_level_and_reason() -> None:
    read_model = build_surface_permission_read_model()
    query = SurfacePermissionInspectionQuery(
        permission_level=SurfacePermissionLevel.DENIED,
        reason=SurfacePermissionReason.EXECUTION_NOT_IMPLEMENTED,
    )
    matched = filter_surface_permission_read_model(
        read_model,
        build_surface_permission_inspection_filter(query),
    )

    assert matched
    assert all(
        entry.permission_level is SurfacePermissionLevel.DENIED for entry in matched
    )
    assert all(
        entry.reason is SurfacePermissionReason.EXECUTION_NOT_IMPLEMENTED
        for entry in matched
    )


def test_p211c_boolean_filters_reduce_result_sets() -> None:
    read_model = build_surface_permission_read_model()
    sensitive = filter_surface_permission_read_model(
        read_model,
        SurfacePermissionInspectionFilter(sensitive_only=True),
    )
    denied = filter_surface_permission_read_model(
        read_model,
        SurfacePermissionInspectionFilter(denied_only=True),
    )
    preflight = filter_surface_permission_read_model(
        read_model,
        SurfacePermissionInspectionFilter(preflight_only_only=True),
    )

    assert len(sensitive) < 700
    assert all(entry.surface_id in {"system", "settings", "ide"} for entry in sensitive)
    assert len(denied) == read_model.denied_summary.__len__()
    assert all(
        entry.permission_level is SurfacePermissionLevel.DENIED for entry in denied
    )
    assert all(
        entry.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY
        for entry in preflight
    )


def test_p211c_filters_preserve_permission_levels_and_evidence_refs() -> None:
    read_model = build_surface_permission_read_model()
    before = {entry.entry_hash: entry for entry in read_model.entries}
    matched = filter_surface_permission_read_model(
        read_model,
        SurfacePermissionInspectionFilter(clients=(ShellClientKind.CLI,)),
    )

    for entry in matched:
        source = before[entry.entry_hash]
        assert entry.permission_level is source.permission_level
        assert entry.evidence_refs == source.evidence_refs


def test_p211c_filters_do_not_mutate_source_read_model() -> None:
    read_model = build_surface_permission_read_model()
    original_hash = read_model.read_model_hash
    inspect_surface_permissions(
        SurfacePermissionInspectionQuery(
            client_kind=ShellClientKind.WEB,
            denied_only=True,
        ),
        read_model=read_model,
    )

    assert read_model.read_model_hash == original_hash
    assert len(read_model.entries) == 700

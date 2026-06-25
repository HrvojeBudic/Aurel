"""P1.7.5 — Path Normalization & Escape Detection Contract tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    EscapeDetectionContract,
    PathBoundaryCheckResult,
    PathBoundaryStatus,
    PathEscapeSignal,
    PathGovernanceUnknownFieldError,
    PathGovernanceValidationError,
    PathKind,
    PathNormalizationResult,
    PathNormalizationStatus,
    PathScopeAction,
    PathScopeReason,
    ProjectionSourceLabel,
    TrustedRoot,
    TrustedRootKind,
    TrustedRootRegistry,
    build_path_identity,
    build_trusted_root_registry,
    detect_path_escape_candidates,
    normalize_path_for_governance,
    to_canonical_json,
)


_REQUIRED_NORMALIZATION_STATUSES = {
    "NORMALIZED",
    "ERROR",
    "UNKNOWN",
}

_REQUIRED_ESCAPE_SIGNALS = {
    "TRAVERSAL_CANDIDATE",
    "ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT",
    "ROOT_MISMATCH",
    "WINDOWS_DRIVE_PREFIX",
    "UNC_PATH",
    "HOME_EXPANSION",
    "MIXED_SEPARATORS",
    "EMPTY_PATH",
    "UNKNOWN",
}

_REQUIRED_BOUNDARY_STATUSES = {
    "PATH_OK",
    "PATH_OUTSIDE_TRUSTED_ROOT",
    "PATH_TRAVERSAL_CANDIDATE",
    "PATH_UNRESOLVED",
    "UNKNOWN",
}

_AUTHORITY_METHOD_NAMES = {
    "allow",
    "deny_runtime",
    "block",
    "enforce",
    "apply",
    "authorize",
    "can_read",
    "can_write",
    "can_execute",
    "is_allowed",
    "is_denied",
    "resolve_root_authority",
    "resolve_path",
    "write_ledger",
    "approve",
    "submit",
}

_FORBIDDEN_IMPORT_SNIPPETS = (
    "from agentic_runtime.runtime",
    "from agentic_runtime.trace",
    "from agentic_runtime.sandbox",
    "from agentic_runtime.sandbox_policy",
    "from agentic_runtime.approval",
    "from agentic_runtime.policy",
    "from agentic_runtime.tools",
    "from agentic_runtime.cli",
)


def _path_identity(raw_path: str, path_kind: PathKind = PathKind.REPO_RELATIVE):
    return build_path_identity(
        raw_path,
        path_kind=path_kind,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _root(raw_path: str) -> TrustedRoot:
    return TrustedRoot(
        path_identity=_path_identity(raw_path),
        root_kind=TrustedRootKind.REPO_ROOT,
        display_name="repo",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        allowed_actions=(PathScopeAction.READ, PathScopeAction.LIST),
        reason=PathScopeReason.REPO_CONTEXT,
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert PathNormalizationStatus is pg.PathNormalizationStatus
    assert PathEscapeSignal is pg.PathEscapeSignal
    assert PathNormalizationResult is pg.PathNormalizationResult
    assert PathBoundaryStatus is pg.PathBoundaryStatus
    assert PathBoundaryCheckResult is pg.PathBoundaryCheckResult
    assert EscapeDetectionContract is pg.EscapeDetectionContract
    assert normalize_path_for_governance is pg.normalize_path_for_governance
    assert detect_path_escape_candidates is pg.detect_path_escape_candidates


def test_normalization_status_has_required_values() -> None:
    assert {
        item.value for item in PathNormalizationStatus
    } == _REQUIRED_NORMALIZATION_STATUSES


def test_escape_signal_has_required_values() -> None:
    assert {item.value for item in PathEscapeSignal} == _REQUIRED_ESCAPE_SIGNALS


def test_boundary_status_has_required_values() -> None:
    assert {item.value for item in PathBoundaryStatus} == _REQUIRED_BOUNDARY_STATUSES


def test_raw_path_is_preserved_exactly() -> None:
    raw = " ./src//agentic_runtime/../runtime.py "
    result = normalize_path_for_governance(
        raw,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.raw_path == raw
    assert result.normalized_path == "src/agentic_runtime/../runtime.py"
    assert result.display_path == "src/agentic_runtime/../runtime.py"


def test_harmless_dot_segment_normalization() -> None:
    result = normalize_path_for_governance(
        r".\\src//agentic_runtime/./path_governance",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.status is PathNormalizationStatus.NORMALIZED
    assert result.normalized_path == "src/agentic_runtime/path_governance"
    assert result.display_path == "src/agentic_runtime/path_governance"


def test_normalization_is_deterministic() -> None:
    first = normalize_path_for_governance(
        "src/agentic_runtime/path_governance/path_normalization.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = normalize_path_for_governance(
        "src/agentic_runtime/path_governance/path_normalization.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.result_hash == second.result_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_changed_path_changes_normalization_hash() -> None:
    first = normalize_path_for_governance(
        "src/a.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = normalize_path_for_governance(
        "src/b.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.result_hash != second.result_hash


def test_traversal_signal_is_non_enforcement() -> None:
    result = normalize_path_for_governance(
        "src/../etc/passwd",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathEscapeSignal.TRAVERSAL_CANDIDATE in result.escape_signals
    assert result.status is PathNormalizationStatus.NORMALIZED
    assert "not enforcement" in result.warnings[0]


def test_empty_path_produces_empty_path_signal() -> None:
    result = normalize_path_for_governance(
        "   ",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.status is PathNormalizationStatus.ERROR
    assert PathEscapeSignal.EMPTY_PATH in result.escape_signals
    assert result.normalized_path == ""
    assert result.display_path == ""


def test_windows_drive_signal() -> None:
    result = normalize_path_for_governance(
        r"C:\Users\repo\src\main.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathEscapeSignal.WINDOWS_DRIVE_PREFIX in result.escape_signals


def test_unc_path_signal() -> None:
    result = normalize_path_for_governance(
        r"\\server\share\repo\src\main.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathEscapeSignal.UNC_PATH in result.escape_signals


def test_home_expansion_signal() -> None:
    result = normalize_path_for_governance(
        "~/repo/src/main.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathEscapeSignal.HOME_EXPANSION in result.escape_signals


def test_mixed_separator_signal() -> None:
    result = normalize_path_for_governance(
        r"src\agentic_runtime/path_governance",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathEscapeSignal.MIXED_SEPARATORS in result.escape_signals


def test_absolute_path_without_root_context_is_unresolved_not_block() -> None:
    contract = detect_path_escape_candidates(
        raw_path="/etc/passwd",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.status is PathBoundaryStatus.PATH_UNRESOLVED
    assert contract.boundary_result.enforced is False
    assert contract.boundary_result.shadow_only is True
    assert (
        PathEscapeSignal.ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT
        in contract.boundary_result.escape_signals
    )


def test_trusted_root_string_comparison_produces_path_ok() -> None:
    root = _root("src")
    contract = detect_path_escape_candidates(
        raw_path="src/agentic_runtime/path_governance",
        trusted_root=root,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.status is PathBoundaryStatus.PATH_OK
    assert contract.boundary_result.matched_root_id == root.root_id
    assert contract.boundary_result.enforced is False


def test_root_mismatch_produces_outside_trusted_root_without_enforcement() -> None:
    root = _root("src/agentic_runtime")
    contract = detect_path_escape_candidates(
        raw_path="tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py",
        trusted_root=root,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.status is PathBoundaryStatus.PATH_OUTSIDE_TRUSTED_ROOT
    assert contract.boundary_result.matched_root_id is None
    assert PathEscapeSignal.ROOT_MISMATCH in contract.boundary_result.escape_signals
    assert contract.boundary_result.enforced is False
    assert contract.boundary_result.shadow_only is True


def test_traversal_prioritized_over_root_mismatch() -> None:
    root = _root("src")
    contract = detect_path_escape_candidates(
        raw_path="src/../etc/passwd",
        trusted_root=root,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.status is PathBoundaryStatus.PATH_TRAVERSAL_CANDIDATE
    assert PathEscapeSignal.TRAVERSAL_CANDIDATE in contract.boundary_result.escape_signals


def test_registry_selects_first_matching_root_deterministically() -> None:
    first_root = _root("src")
    second_root = _root("tests")
    registry = build_trusted_root_registry(
        trusted_roots=(second_root, first_root),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    contract = detect_path_escape_candidates(
        raw_path="src/agentic_runtime/path_governance",
        trusted_root_registry=registry,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.status is PathBoundaryStatus.PATH_OK
    assert contract.boundary_result.matched_root_id == first_root.root_id


def test_registry_mismatch_uses_first_root_as_comparison_context() -> None:
    first_root = _root("src")
    second_root = _root("tests")
    registry = build_trusted_root_registry(
        trusted_roots=(second_root, first_root),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    contract = detect_path_escape_candidates(
        raw_path="agent/reports/P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md",
        trusted_root_registry=registry,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.status is PathBoundaryStatus.PATH_OUTSIDE_TRUSTED_ROOT
    assert contract.boundary_result.comparison_root_id == first_root.root_id


def test_path_identity_input_avoids_conflicting_raw_path() -> None:
    identity = _path_identity("src/agentic_runtime")
    with pytest.raises(PathGovernanceValidationError):
        detect_path_escape_candidates(
            path_identity=identity,
            raw_path="tests/path_governance",
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        )


def test_boundary_and_contract_hashes_change_with_inputs() -> None:
    root = _root("src")
    first = detect_path_escape_candidates(
        raw_path="src/a.py",
        trusted_root=root,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = detect_path_escape_candidates(
        raw_path="src/b.py",
        trusted_root=root,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.boundary_result.result_hash != second.boundary_result.result_hash
    assert first.contract_hash != second.contract_hash


def test_escape_detection_contract_metadata() -> None:
    contract = detect_path_escape_candidates(
        raw_path="src/agentic_runtime",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.contract_version == "path_escape_detection_contract.v1"
    assert contract.created_by_task == "P1.7.5"
    assert contract.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert len(contract.contract_hash) == 64


def test_unknown_fields_are_rejected() -> None:
    normalization = normalize_path_for_governance(
        "src/agentic_runtime",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    normalization_payload = normalization.to_canonical_dict()
    normalization_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as normalization_error:
        PathNormalizationResult.from_dict(normalization_payload)
    assert normalization_error.value.code.value == "UNKNOWN_FIELD"

    contract = detect_path_escape_candidates(
        raw_path="src/agentic_runtime",
        trusted_root=_root("src"),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    boundary_payload = contract.boundary_result.to_canonical_dict()
    boundary_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as boundary_error:
        PathBoundaryCheckResult.from_dict(boundary_payload)
    assert boundary_error.value.code.value == "UNKNOWN_FIELD"

    contract_payload = contract.to_canonical_dict()
    contract_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as contract_error:
        EscapeDetectionContract.from_dict(contract_payload)
    assert contract_error.value.code.value == "UNKNOWN_FIELD"


def test_no_filesystem_reads_or_resolves_occur() -> None:
    for module_name in (
        "agentic_runtime.path_governance.path_normalization",
        "agentic_runtime.path_governance.escape_detection",
    ):
        source = inspect.getsource(importlib.import_module(module_name))
        forbidden_snippets = (
            "Path(",
            "pathlib",
            "exists(",
            ".exists(",
            "resolve(",
            ".resolve(",
            "stat(",
            ".stat(",
            "open(",
            "read_text(",
            "read_bytes(",
            "realpath",
            "symlink",
        )
        for snippet in forbidden_snippets:
            assert snippet not in source


def test_no_resolver_or_enforcement_claims_exist() -> None:
    for module_name in (
        "agentic_runtime.path_governance.path_normalization",
        "agentic_runtime.path_governance.escape_detection",
    ):
        source = inspect.getsource(importlib.import_module(module_name))
        assert "AgenticRuntime.submit" not in source
        for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
            assert snippet not in source

    for cls in (
        PathNormalizationResult,
        PathBoundaryCheckResult,
        EscapeDetectionContract,
    ):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _AUTHORITY_METHOD_NAMES & methods


def test_boundary_results_remain_shadow_only() -> None:
    contract = detect_path_escape_candidates(
        raw_path="src/../etc/passwd",
        trusted_root=_root("src"),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert contract.boundary_result.shadow_only is True
    assert contract.boundary_result.enforced is False

    with pytest.raises(PathGovernanceValidationError):
        PathBoundaryCheckResult(
            raw_path="src/a.py",
            normalized_path="src/a.py",
            status=PathBoundaryStatus.PATH_OK,
            enforced=True,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        )

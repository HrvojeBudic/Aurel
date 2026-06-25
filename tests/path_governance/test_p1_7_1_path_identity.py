"""P1.7.1 — Path Identity & Canonical Path Schema tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    CanonicalPathRef,
    CanonicalizationStatus,
    PathGovernanceUnknownFieldError,
    PathIdentity,
    PathKind,
    PathRef,
    PathSensitivity,
    ProjectionSourceLabel,
    TRAVERSAL_WARNING,
    build_path_identity,
    to_canonical_json,
)


_REQUIRED_PATH_KINDS = {
    "REPO_RELATIVE",
    "LOCAL_ABSOLUTE",
    "LOCAL_RELATIVE",
    "WORKSPACE_RELATIVE",
    "UPLOAD_REF",
    "VIRTUAL",
    "UNKNOWN",
}

_REQUIRED_SENSITIVITIES = {
    "PUBLIC",
    "INTERNAL",
    "PRIVATE",
    "SECRET_CANDIDATE",
    "UNKNOWN",
}

_REQUIRED_CANONICALIZATION_STATUSES = {
    "CANONICAL",
    "NORMALIZED_ONLY",
    "UNRESOLVED",
    "UNSUPPORTED",
    "ERROR",
}

_AUTHORITY_METHOD_NAMES = {
    "allow",
    "deny",
    "enforce",
    "permission",
    "resolve_path",
    "resolve_paths",
    "trusted_root",
    "trusted_root_id",
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


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert PathKind is pg.PathKind
    assert PathSensitivity is pg.PathSensitivity
    assert CanonicalizationStatus is pg.CanonicalizationStatus
    assert PathRef is pg.PathRef
    assert CanonicalPathRef is pg.CanonicalPathRef
    assert PathIdentity is pg.PathIdentity
    assert build_path_identity is pg.build_path_identity


def test_path_kind_has_required_values() -> None:
    assert {item.value for item in PathKind} == _REQUIRED_PATH_KINDS


def test_path_sensitivity_has_required_values() -> None:
    assert {item.value for item in PathSensitivity} == _REQUIRED_SENSITIVITIES


def test_canonicalization_status_has_required_values() -> None:
    assert {
        item.value for item in CanonicalizationStatus
    } == _REQUIRED_CANONICALIZATION_STATUSES


def test_path_ref_preserves_raw_path() -> None:
    raw = " ./src//agentic_runtime/../runtime.py "
    identity = build_path_identity(
        raw,
        path_kind=PathKind.LOCAL_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert identity.path_ref.raw_path == raw
    assert identity.canonical_ref.raw_path == raw
    assert identity.canonical_ref.normalized_path != raw


def test_canonical_path_ref_separates_raw_normalized_display() -> None:
    identity = build_path_identity(
        r".\\src//agentic_runtime/./path_governance",
        path_kind=PathKind.REPO_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert identity.canonical_ref.raw_path == r".\\src//agentic_runtime/./path_governance"
    assert identity.canonical_ref.normalized_path == "src/agentic_runtime/path_governance"
    assert identity.canonical_ref.display_path == "src/agentic_runtime/path_governance"
    assert identity.canonical_ref.canonicalization_status is (
        CanonicalizationStatus.NORMALIZED_ONLY
    )


def test_build_path_identity_is_deterministic() -> None:
    first = build_path_identity(
        "src/agentic_runtime/path_governance/path_identity.py",
        path_kind=PathKind.REPO_RELATIVE,
        declared_sensitivity=PathSensitivity.INTERNAL,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_path_identity(
        "src/agentic_runtime/path_governance/path_identity.py",
        path_kind=PathKind.REPO_RELATIVE,
        declared_sensitivity=PathSensitivity.INTERNAL,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.canonical_ref.path_hash == second.canonical_ref.path_hash
    assert first.canonical_ref.canonical_hash == second.canonical_ref.canonical_hash
    assert first.identity_hash == second.identity_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_different_raw_path_changes_identity_hash() -> None:
    first = build_path_identity(
        "src/agentic_runtime/path_governance/path_identity.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_path_identity(
        "src/agentic_runtime/path_governance/canonical_path.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.identity_hash != second.identity_hash


def test_same_path_with_different_kind_changes_identity_hash() -> None:
    repo_relative = build_path_identity(
        "src/agentic_runtime/path_governance/path_identity.py",
        path_kind=PathKind.REPO_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    workspace_relative = build_path_identity(
        "src/agentic_runtime/path_governance/path_identity.py",
        path_kind=PathKind.WORKSPACE_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert repo_relative.canonical_ref.path_hash != workspace_relative.canonical_ref.path_hash
    assert repo_relative.identity_hash != workspace_relative.identity_hash


def test_unknown_fields_are_rejected() -> None:
    identity = build_path_identity(
        "src/agentic_runtime/path_governance/path_identity.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    path_payload = identity.path_ref.to_canonical_dict()
    path_payload["shadow_authority_grant"] = True

    with pytest.raises(PathGovernanceUnknownFieldError) as path_error:
        PathRef.from_dict(path_payload)
    assert path_error.value.code.value == "UNKNOWN_FIELD"

    canonical_payload = identity.canonical_ref.to_canonical_dict()
    canonical_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as canonical_error:
        CanonicalPathRef.from_dict(canonical_payload)
    assert canonical_error.value.code.value == "UNKNOWN_FIELD"

    identity_payload = identity.to_canonical_dict()
    identity_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as identity_error:
        PathIdentity.from_dict(identity_payload)
    assert identity_error.value.code.value == "UNKNOWN_FIELD"


def test_raw_path_does_not_grant_authority() -> None:
    for cls in (PathRef, PathIdentity):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _AUTHORITY_METHOD_NAMES & methods


def test_canonical_path_does_not_imply_trusted_root() -> None:
    identity = build_path_identity(
        "/tmp/project/../private",
        path_kind=PathKind.LOCAL_ABSOLUTE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    canonical = identity.canonical_ref.to_canonical_dict()

    assert "trusted_root_id" not in canonical
    assert "trusted_root" not in canonical
    assert not hasattr(identity.canonical_ref, "trusted_root_id")


def test_traversal_like_segments_are_not_enforced() -> None:
    identity = build_path_identity(
        "../secrets.txt",
        path_kind=PathKind.LOCAL_RELATIVE,
        declared_sensitivity=PathSensitivity.SECRET_CANDIDATE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert identity.path_ref.raw_path == "../secrets.txt"
    assert identity.canonical_ref.normalized_path == "../secrets.txt"
    assert identity.canonical_ref.warnings == (TRAVERSAL_WARNING,)
    assert not hasattr(identity, "allowed")
    assert not hasattr(identity, "denied")


def test_no_resolver_or_enforcement_claims_exist() -> None:
    import agentic_runtime.path_governance as pg

    assert "resolve_path_identity" not in pg.__all__
    assert "path_resolver" not in pg.__all__
    assert "trusted_root_registry" not in pg.__all__

    for cls in (PathRef, CanonicalPathRef, PathIdentity):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _AUTHORITY_METHOD_NAMES & methods

    for module_name in (
        "agentic_runtime.path_governance.canonical_path",
        "agentic_runtime.path_governance.path_identity",
    ):
        source = inspect.getsource(importlib.import_module(module_name))
        assert "AgenticRuntime.submit" not in source
        assert "realpath" not in source
        assert ".resolve(" not in source
        assert "trusted_root_id" not in source
        for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
            assert snippet not in source

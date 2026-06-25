"""P1.7.4 — Trusted Root & Scope Registry Seed tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    PathGovernanceUnknownFieldError,
    PathKind,
    PathScopeAction,
    PathScopeDeny,
    PathScopeGrant,
    PathScopeReason,
    ProjectionSourceLabel,
    SourceTrustLabel,
    TrustedRoot,
    TrustedRootKind,
    TrustedRootRegistry,
    build_path_identity,
    build_trusted_root_registry,
    to_canonical_json,
)


_REQUIRED_ROOT_KINDS = {
    "REPO_ROOT",
    "WORKSPACE_ROOT",
    "OPERATOR_APPROVED",
    "AGENT_REPORTS",
    "ARTIFACTS",
    "UPLOADS",
    "DENIED_ROOT",
    "UNKNOWN",
}

_REQUIRED_SCOPE_ACTIONS = {
    "READ",
    "WRITE",
    "CREATE",
    "DELETE",
    "EXECUTE",
    "IMPORT",
    "LIST",
    "MEMORY_USE",
    "PROMPT_CONTEXT_USE",
    "TOOL_INPUT_USE",
    "UNKNOWN",
}

_REQUIRED_SCOPE_REASONS = {
    "REPO_CONTEXT",
    "WORKSPACE_CONTEXT",
    "OPERATOR_APPROVAL",
    "REPORT_OUTPUT",
    "ARTIFACT_OUTPUT",
    "UPLOAD_BOUNDARY",
    "DENIED_BY_DEFAULT",
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


def _root(
    raw_path: str,
    *,
    root_kind: TrustedRootKind = TrustedRootKind.REPO_ROOT,
    reason: PathScopeReason = PathScopeReason.REPO_CONTEXT,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
    trust_label: SourceTrustLabel = SourceTrustLabel.INTERNAL_REPO,
    allowed_actions: tuple[PathScopeAction, ...] = (
        PathScopeAction.READ,
        PathScopeAction.LIST,
    ),
    denied_actions: tuple[PathScopeAction, ...] = (),
) -> TrustedRoot:
    return TrustedRoot(
        path_identity=_path_identity(raw_path),
        root_kind=root_kind,
        display_name=root_kind.value.lower(),
        source_label=source_label,
        trust_label=trust_label,
        allowed_actions=allowed_actions,
        denied_actions=denied_actions,
        reason=reason,
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert TrustedRootKind is pg.TrustedRootKind
    assert PathScopeAction is pg.PathScopeAction
    assert PathScopeReason is pg.PathScopeReason
    assert TrustedRoot is pg.TrustedRoot
    assert PathScopeGrant is pg.PathScopeGrant
    assert PathScopeDeny is pg.PathScopeDeny
    assert TrustedRootRegistry is pg.TrustedRootRegistry
    assert build_trusted_root_registry is pg.build_trusted_root_registry


def test_trusted_root_kind_has_required_values() -> None:
    assert {item.value for item in TrustedRootKind} == _REQUIRED_ROOT_KINDS


def test_path_scope_action_has_required_values() -> None:
    assert {item.value for item in PathScopeAction} == _REQUIRED_SCOPE_ACTIONS


def test_path_scope_reason_has_required_values() -> None:
    assert {item.value for item in PathScopeReason} == _REQUIRED_SCOPE_REASONS


def test_trusted_root_can_be_built_from_path_identity() -> None:
    identity = _path_identity("src/agentic_runtime")
    root = TrustedRoot(
        path_identity=identity,
        root_kind=TrustedRootKind.REPO_ROOT,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.INTERNAL_REPO,
        allowed_actions=(PathScopeAction.READ, PathScopeAction.LIST),
        reason=PathScopeReason.REPO_CONTEXT,
    )

    assert root.root_id
    assert len(root.root_id) == 64
    assert root.path_identity is identity
    assert root.path_identity.identity_hash == identity.identity_hash


def test_trusted_root_preserves_source_label() -> None:
    live_root = _root(
        "src",
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_root = _root(
        "tests/fixtures",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert live_root.source_label is ProjectionSourceLabel.LIVE
    assert fixture_root.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    fixture_root = _root("tests/fixtures")
    registry = build_trusted_root_registry(
        trusted_roots=(fixture_root,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert fixture_root.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert registry.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert "DEV_FIXTURE" in to_canonical_json(registry)


def test_trusted_root_does_not_imply_permission() -> None:
    root = _root("src")
    methods = {
        name for name, _ in inspect.getmembers(TrustedRoot, predicate=inspect.isfunction)
    }

    assert root.allowed_actions == (PathScopeAction.LIST, PathScopeAction.READ)
    assert not _AUTHORITY_METHOD_NAMES & methods
    assert not hasattr(root, "permission")
    assert not hasattr(root, "sandbox_policy")


def test_path_scope_grant_does_not_enforce() -> None:
    root = _root("src")
    grant = PathScopeGrant(
        root_id=root.root_id,
        actions=(PathScopeAction.READ,),
        reason=PathScopeReason.REPO_CONTEXT,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    methods = {
        name for name, _ in inspect.getmembers(PathScopeGrant, predicate=inspect.isfunction)
    }

    assert grant.grant_id
    assert not _AUTHORITY_METHOD_NAMES & methods
    assert not hasattr(grant, "runtime_authority")


def test_path_scope_deny_does_not_enforce() -> None:
    root = _root("uploads", root_kind=TrustedRootKind.UPLOADS)
    deny = PathScopeDeny(
        root_id=root.root_id,
        actions=(PathScopeAction.EXECUTE,),
        reason=PathScopeReason.UPLOAD_BOUNDARY,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    methods = {
        name for name, _ in inspect.getmembers(PathScopeDeny, predicate=inspect.isfunction)
    }

    assert deny.deny_id
    assert not _AUTHORITY_METHOD_NAMES & methods
    assert not hasattr(deny, "runtime_blocking")


def test_trusted_root_registry_builds_deterministically() -> None:
    root = _root("src")
    grant = PathScopeGrant(
        root_id=root.root_id,
        actions=(PathScopeAction.READ, PathScopeAction.LIST),
        reason=PathScopeReason.REPO_CONTEXT,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    first = build_trusted_root_registry(
        trusted_roots=(root,),
        scope_grants=(grant,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_trusted_root_registry(
        trusted_roots=(root,),
        scope_grants=(grant,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.registry_hash == second.registry_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_registry_hash_changes_when_root_changes() -> None:
    first_root = _root("src", root_kind=TrustedRootKind.REPO_ROOT)
    second_root = _root("src", root_kind=TrustedRootKind.WORKSPACE_ROOT)

    first = build_trusted_root_registry(
        trusted_roots=(first_root,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_trusted_root_registry(
        trusted_roots=(second_root,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first_root.root_id != second_root.root_id
    assert first.registry_hash != second.registry_hash


def test_registry_hash_changes_when_grant_or_deny_changes() -> None:
    root = _root("src")
    grant = PathScopeGrant(
        root_id=root.root_id,
        actions=(PathScopeAction.READ,),
        reason=PathScopeReason.REPO_CONTEXT,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_grant = PathScopeGrant(
        root_id=root.root_id,
        actions=(PathScopeAction.READ, PathScopeAction.LIST),
        reason=PathScopeReason.REPO_CONTEXT,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    deny = PathScopeDeny(
        root_id=root.root_id,
        actions=(PathScopeAction.EXECUTE,),
        reason=PathScopeReason.DENIED_BY_DEFAULT,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    grant_registry = build_trusted_root_registry(
        trusted_roots=(root,),
        scope_grants=(grant,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_grant_registry = build_trusted_root_registry(
        trusted_roots=(root,),
        scope_grants=(changed_grant,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    deny_registry = build_trusted_root_registry(
        trusted_roots=(root,),
        scope_grants=(grant,),
        scope_denies=(deny,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert grant_registry.registry_hash != changed_grant_registry.registry_hash
    assert grant_registry.registry_hash != deny_registry.registry_hash


def test_registry_hash_is_order_insensitive_where_possible() -> None:
    root_a = _root("src/a")
    root_b = _root("src/b")
    grant_a = PathScopeGrant(
        root_id=root_a.root_id,
        actions=(PathScopeAction.READ,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    grant_b = PathScopeGrant(
        root_id=root_b.root_id,
        actions=(PathScopeAction.LIST,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    deny_a = PathScopeDeny(
        root_id=root_a.root_id,
        actions=(PathScopeAction.EXECUTE,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    deny_b = PathScopeDeny(
        root_id=root_b.root_id,
        actions=(PathScopeAction.DELETE,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    first = build_trusted_root_registry(
        trusted_roots=(root_a, root_b),
        scope_grants=(grant_a, grant_b),
        scope_denies=(deny_a, deny_b),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_trusted_root_registry(
        trusted_roots=(root_b, root_a),
        scope_grants=(grant_b, grant_a),
        scope_denies=(deny_b, deny_a),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.registry_hash == second.registry_hash


def test_registry_can_represent_repo_root() -> None:
    root = _root("src", root_kind=TrustedRootKind.REPO_ROOT)
    registry = build_trusted_root_registry(
        trusted_roots=(root,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert registry.trusted_roots[0].root_kind is TrustedRootKind.REPO_ROOT
    assert not hasattr(registry.trusted_roots[0], "runtime_permission")


def test_registry_can_represent_workspace_root() -> None:
    root = _root(
        ".",
        root_kind=TrustedRootKind.WORKSPACE_ROOT,
        reason=PathScopeReason.WORKSPACE_CONTEXT,
    )
    registry = build_trusted_root_registry(
        trusted_roots=(root,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert registry.trusted_roots[0].root_kind is TrustedRootKind.WORKSPACE_ROOT
    assert not hasattr(registry.trusted_roots[0], "sandbox_permission")


def test_registry_can_represent_operator_approved_root() -> None:
    root = _root(
        "/operator/approved",
        root_kind=TrustedRootKind.OPERATOR_APPROVED,
        reason=PathScopeReason.OPERATOR_APPROVAL,
        trust_label=SourceTrustLabel.OPERATOR_PROVIDED,
    )
    registry = build_trusted_root_registry(
        trusted_roots=(root,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert registry.trusted_roots[0].reason is PathScopeReason.OPERATOR_APPROVAL
    assert not hasattr(registry.trusted_roots[0], "override_policy")


def test_registry_can_represent_agent_reports_artifacts_uploads() -> None:
    reports = _root(
        "agent/reports",
        root_kind=TrustedRootKind.AGENT_REPORTS,
        reason=PathScopeReason.REPORT_OUTPUT,
        allowed_actions=(PathScopeAction.READ, PathScopeAction.LIST, PathScopeAction.WRITE),
    )
    artifacts = _root(
        "artifacts",
        root_kind=TrustedRootKind.ARTIFACTS,
        reason=PathScopeReason.ARTIFACT_OUTPUT,
        allowed_actions=(PathScopeAction.CREATE, PathScopeAction.WRITE),
    )
    uploads = _root(
        "uploads",
        root_kind=TrustedRootKind.UPLOADS,
        reason=PathScopeReason.UPLOAD_BOUNDARY,
        trust_label=SourceTrustLabel.UNKNOWN,
        allowed_actions=(PathScopeAction.READ, PathScopeAction.LIST),
        denied_actions=(PathScopeAction.EXECUTE,),
    )
    registry = build_trusted_root_registry(
        trusted_roots=(reports, artifacts, uploads),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {root.root_kind for root in registry.trusted_roots}

    assert {
        TrustedRootKind.AGENT_REPORTS,
        TrustedRootKind.ARTIFACTS,
        TrustedRootKind.UPLOADS,
    } <= kinds
    assert uploads.trust_label is SourceTrustLabel.UNKNOWN
    assert PathScopeAction.EXECUTE in uploads.denied_actions
    assert not hasattr(uploads, "trusted_content")


def test_registry_can_represent_denied_unknown_scope() -> None:
    denied = _root(
        "/restricted",
        root_kind=TrustedRootKind.DENIED_ROOT,
        reason=PathScopeReason.DENIED_BY_DEFAULT,
        allowed_actions=(),
        denied_actions=(PathScopeAction.READ, PathScopeAction.WRITE, PathScopeAction.EXECUTE),
        trust_label=SourceTrustLabel.UNTRUSTED,
    )
    unknown = _root(
        "unknown://root",
        root_kind=TrustedRootKind.UNKNOWN,
        reason=PathScopeReason.UNKNOWN,
        allowed_actions=(PathScopeAction.UNKNOWN,),
        trust_label=SourceTrustLabel.UNKNOWN,
    )
    registry = build_trusted_root_registry(
        trusted_roots=(denied, unknown),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert {root.root_kind for root in registry.trusted_roots} == {
        TrustedRootKind.DENIED_ROOT,
        TrustedRootKind.UNKNOWN,
    }
    assert not hasattr(denied, "block_runtime")


def test_unknown_fields_are_rejected() -> None:
    root = _root("src")
    grant = PathScopeGrant(
        root_id=root.root_id,
        actions=(PathScopeAction.READ,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    deny = PathScopeDeny(
        root_id=root.root_id,
        actions=(PathScopeAction.EXECUTE,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    registry = build_trusted_root_registry(
        trusted_roots=(root,),
        scope_grants=(grant,),
        scope_denies=(deny,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    root_payload = root.to_canonical_dict()
    root_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as root_error:
        TrustedRoot.from_dict(root_payload)
    assert root_error.value.code.value == "UNKNOWN_FIELD"

    grant_payload = grant.to_canonical_dict()
    grant_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as grant_error:
        PathScopeGrant.from_dict(grant_payload)
    assert grant_error.value.code.value == "UNKNOWN_FIELD"

    deny_payload = deny.to_canonical_dict()
    deny_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as deny_error:
        PathScopeDeny.from_dict(deny_payload)
    assert deny_error.value.code.value == "UNKNOWN_FIELD"

    registry_payload = registry.to_canonical_dict()
    registry_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as registry_error:
        TrustedRootRegistry.from_dict(registry_payload)
    assert registry_error.value.code.value == "UNKNOWN_FIELD"


def test_no_filesystem_reads_or_resolves_occur() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.trusted_roots",
    ))
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
        ".read(",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_trusted_root_authority_resolver_exists() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "resolve_root_authority",
        "can_read",
        "can_write",
        "can_execute",
        "is_allowed",
        "is_denied",
    ):
        assert name not in pg.__all__


def test_no_path_escape_detection_exists() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.trusted_roots",
    ))
    forbidden_snippets = (
        "PATH_ESCAPE",
        "outside_root",
        "path_escape",
        "escape_detection",
        "symlink",
        "realpath",
        "traversal denial",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_resolver_or_enforcement_claims_exist() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.trusted_roots",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source
    for cls in (TrustedRoot, PathScopeGrant, PathScopeDeny, TrustedRootRegistry):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _AUTHORITY_METHOD_NAMES & methods

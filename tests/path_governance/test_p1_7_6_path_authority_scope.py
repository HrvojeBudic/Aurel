"""P1.7.6 — Path Authority Scope Model tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    PathAuthorityBasis,
    PathAuthorityConstraint,
    PathAuthorityConstraintKind,
    PathAuthorityScope,
    PathAuthorityScopeRegistry,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathGovernanceUnknownFieldError,
    PathKind,
    PathScopeAction,
    PathScopeReason,
    ProjectionSourceLabel,
    SourceTrustLabel,
    TrustedRoot,
    TrustedRootKind,
    build_path_authority_scope,
    build_path_authority_scope_registry,
    build_path_identity,
    build_trusted_root_registry,
    to_canonical_json,
)


_REQUIRED_SUBJECT_KINDS = {
    "OPERATOR",
    "AGENT",
    "TOOL",
    "WORKFLOW",
    "MODEL",
    "RUNTIME",
    "SYSTEM",
    "UNKNOWN",
}

_REQUIRED_BASIS_VALUES = {
    "OPERATOR_DECLARATION",
    "POLICY_DECLARATION",
    "TRUSTED_ROOT_REGISTRY",
    "SYSTEM_DEFAULT",
    "TASK_CONTEXT",
    "TEST_FIXTURE",
    "UNKNOWN",
}

_REQUIRED_CONSTRAINT_KINDS = {
    "REQUIRES_OPERATOR_REVIEW",
    "REQUIRES_POLICY_REVIEW",
    "REQUIRES_TRACE",
    "REQUIRES_LOCAL_ONLY",
    "REQUIRES_SANDBOX_LATER",
    "REQUIRES_NO_NETWORK_LATER",
    "RESTRICTS_EXECUTE",
    "RESTRICTS_WRITE",
    "RESTRICTS_MEMORY_USE",
    "RESTRICTS_PROMPT_CONTEXT_USE",
    "UNKNOWN",
}

_AUTHORITY_METHOD_NAMES = {
    "allow",
    "deny_runtime",
    "block",
    "enforce",
    "apply",
    "approve",
    "authorize",
    "can_read",
    "can_write",
    "can_execute",
    "is_allowed",
    "is_denied",
    "resolve_path_authority",
    "resolve_scope",
    "resolve_root_authority",
    "resolve_path",
    "write_ledger",
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

_RESOLVER_API_NAMES = (
    "resolve_path_authority",
    "resolve_scope",
    "authorize_path",
    "is_allowed",
    "is_denied",
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


def _subject(
    *,
    subject_kind: PathAuthoritySubjectKind = PathAuthoritySubjectKind.OPERATOR,
    display_name: str = "operator",
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
) -> PathAuthoritySubject:
    return PathAuthoritySubject(
        subject_kind=subject_kind,
        display_name=display_name,
        source_label=source_label,
    )


def _constraint(
    *,
    constraint_kind: PathAuthorityConstraintKind = PathAuthorityConstraintKind.REQUIRES_TRACE,
    reason: str = "fixture trace requirement",
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
) -> PathAuthorityConstraint:
    return PathAuthorityConstraint(
        constraint_kind=constraint_kind,
        reason=reason,
        source_label=source_label,
    )


def _scope(
    *,
    subject: PathAuthoritySubject | None = None,
    actions: tuple[PathScopeAction, ...] = (PathScopeAction.READ, PathScopeAction.LIST),
    basis: PathAuthorityBasis = PathAuthorityBasis.OPERATOR_DECLARATION,
    root_id: str | None = None,
    path_identity=None,
    constraints: tuple[PathAuthorityConstraint, ...] = (),
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
):
    return build_path_authority_scope(
        subject=subject or _subject(),
        actions=actions,
        basis=basis,
        root_id=root_id,
        path_identity=path_identity,
        constraints=constraints,
        source_label=source_label,
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathAuthoritySubjectKind",
        "PathAuthorityBasis",
        "PathAuthorityConstraintKind",
        "PathAuthoritySubject",
        "PathAuthorityConstraint",
        "PathAuthorityScope",
        "PathAuthorityScopeRegistry",
        "build_path_authority_scope",
        "build_path_authority_scope_registry",
    ):
        assert hasattr(pg, name)


def test_path_authority_subject_kind_has_required_values() -> None:
    assert {item.value for item in PathAuthoritySubjectKind} == _REQUIRED_SUBJECT_KINDS


def test_path_authority_basis_has_required_values() -> None:
    assert {item.value for item in PathAuthorityBasis} == _REQUIRED_BASIS_VALUES


def test_path_authority_constraint_kind_has_required_values() -> None:
    assert {item.value for item in PathAuthorityConstraintKind} == _REQUIRED_CONSTRAINT_KINDS


def test_path_authority_subject_builds_deterministically() -> None:
    first = _subject(display_name="fixture-operator")
    second = _subject(display_name="fixture-operator")

    assert first.subject_id == second.subject_id
    assert first.subject_id
    assert to_canonical_json(first) == to_canonical_json(second)


def test_path_authority_constraint_builds_deterministically() -> None:
    first = _constraint(reason="requires trace for read scope")
    second = _constraint(reason="requires trace for read scope")

    assert first.constraint_id == second.constraint_id
    assert first.constraint_id
    assert to_canonical_json(first) == to_canonical_json(second)


def test_path_authority_scope_can_reference_trusted_root() -> None:
    root = _root("src")
    scope = _scope(
        root_id=root.root_id,
        basis=PathAuthorityBasis.TRUSTED_ROOT_REGISTRY,
    )

    assert scope.root_id == root.root_id
    assert not hasattr(scope, "allow")
    assert not hasattr(scope, "can_read")


def test_path_authority_scope_can_use_path_scope_actions() -> None:
    scope = _scope(
        actions=(
            PathScopeAction.READ,
            PathScopeAction.WRITE,
            PathScopeAction.PROMPT_CONTEXT_USE,
            PathScopeAction.TOOL_INPUT_USE,
        ),
    )

    assert PathScopeAction.READ in scope.actions
    assert PathScopeAction.WRITE in scope.actions
    assert PathScopeAction.PROMPT_CONTEXT_USE in scope.actions
    assert PathScopeAction.TOOL_INPUT_USE in scope.actions
    assert not hasattr(scope, "authorize")


def test_path_authority_scope_can_carry_constraints() -> None:
    constraints = (
        _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_OPERATOR_REVIEW),
        _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_TRACE),
    )
    scope = _scope(constraints=constraints)

    assert len(scope.constraints) == 2
    assert scope.constraints[0].constraint_kind is PathAuthorityConstraintKind.REQUIRES_OPERATOR_REVIEW
    assert scope.constraints[1].constraint_kind is PathAuthorityConstraintKind.REQUIRES_TRACE
    assert not hasattr(scope.constraints[0], "enforce")


def test_path_authority_scope_registry_builds_deterministically() -> None:
    scope = _scope()
    first = build_path_authority_scope_registry(
        scopes=(scope,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_path_authority_scope_registry(
        scopes=(scope,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.registry_hash == second.registry_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_scope_hash_is_deterministic() -> None:
    first = _scope()
    second = _scope()

    assert first.scope_hash == second.scope_hash
    assert first.scope_id == second.scope_id


def test_changed_action_changes_scope_hash() -> None:
    read_scope = _scope(actions=(PathScopeAction.READ,))
    write_scope = _scope(actions=(PathScopeAction.WRITE,))

    assert read_scope.scope_hash != write_scope.scope_hash


def test_changed_constraint_changes_scope_hash() -> None:
    first = _scope(
        constraints=(
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_TRACE),
        ),
    )
    second = _scope(
        constraints=(
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_OPERATOR_REVIEW),
        ),
    )

    assert first.scope_hash != second.scope_hash


def test_changed_subject_changes_scope_hash() -> None:
    operator_scope = _scope(subject=_subject(subject_kind=PathAuthoritySubjectKind.OPERATOR))
    agent_scope = _scope(subject=_subject(subject_kind=PathAuthoritySubjectKind.AGENT))

    assert operator_scope.scope_hash != agent_scope.scope_hash


def test_source_labels_are_preserved() -> None:
    live_scope = build_path_authority_scope(
        subject=_subject(source_label=ProjectionSourceLabel.LIVE),
        actions=(PathScopeAction.READ,),
        basis=PathAuthorityBasis.SYSTEM_DEFAULT,
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_scope = _scope(source_label=ProjectionSourceLabel.DEV_FIXTURE)

    assert live_scope.source_label is ProjectionSourceLabel.LIVE
    assert live_scope.subject.source_label is ProjectionSourceLabel.LIVE
    assert fixture_scope.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    scope = _scope(source_label=ProjectionSourceLabel.DEV_FIXTURE)
    registry = build_path_authority_scope_registry(
        scopes=(scope,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert scope.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert registry.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_unknown_fields_are_rejected() -> None:
    subject = _subject()
    constraint = _constraint()
    scope = _scope(constraints=(constraint,))
    registry = build_path_authority_scope_registry(
        scopes=(scope,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    subject_payload = subject.to_canonical_dict()
    subject_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as subject_error:
        PathAuthoritySubject.from_dict(subject_payload)
    assert subject_error.value.code.value == "UNKNOWN_FIELD"

    constraint_payload = constraint.to_canonical_dict()
    constraint_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as constraint_error:
        PathAuthorityConstraint.from_dict(constraint_payload)
    assert constraint_error.value.code.value == "UNKNOWN_FIELD"

    scope_payload = scope.to_canonical_dict()
    scope_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as scope_error:
        PathAuthorityScope.from_dict(scope_payload)
    assert scope_error.value.code.value == "UNKNOWN_FIELD"

    registry_payload = registry.to_canonical_dict()
    registry_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as registry_error:
        PathAuthorityScopeRegistry.from_dict(registry_payload)
    assert registry_error.value.code.value == "UNKNOWN_FIELD"


def test_scope_does_not_expose_allow_deny_can_api() -> None:
    scope = _scope()
    methods = {
        name for name, _ in inspect.getmembers(PathAuthorityScope, predicate=inspect.isfunction)
    }
    assert not _AUTHORITY_METHOD_NAMES & methods
    assert not hasattr(scope, "allow")
    assert not hasattr(scope, "can_read")


def test_constraints_do_not_enforce() -> None:
    constraint = _constraint()
    methods = {
        name
        for name, _ in inspect.getmembers(PathAuthorityConstraint, predicate=inspect.isfunction)
    }
    assert not _AUTHORITY_METHOD_NAMES & methods
    assert not hasattr(constraint, "enforce")
    assert not hasattr(constraint, "apply")


def test_no_resolver_api_exists() -> None:
    import agentic_runtime.path_governance as pg

    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.path_authority_scope",
    ))
    for name in _RESOLVER_API_NAMES:
        assert name not in pg.__all__
        assert f"def {name}" not in source


def test_no_runtime_sandbox_approval_imports() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.path_authority_scope",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source


def test_no_filesystem_reads_stat_or_resolves_occur() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.path_authority_scope",
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
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_declaration_patterns_operator_read_list() -> None:
    root = _root("src")
    scope = build_path_authority_scope(
        subject=_subject(
            subject_kind=PathAuthoritySubjectKind.OPERATOR,
            display_name="operator-read-list",
        ),
        actions=(PathScopeAction.READ, PathScopeAction.LIST),
        basis=PathAuthorityBasis.OPERATOR_DECLARATION,
        root_id=root.root_id,
        constraints=(_constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_TRACE),),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert scope.subject.subject_kind is PathAuthoritySubjectKind.OPERATOR
    assert PathScopeAction.READ in scope.actions
    assert not hasattr(scope, "can_read")


def test_declaration_patterns_agent_write_create() -> None:
    scope = build_path_authority_scope(
        subject=_subject(
            subject_kind=PathAuthoritySubjectKind.AGENT,
            display_name="agent-write-create",
        ),
        actions=(PathScopeAction.WRITE, PathScopeAction.CREATE),
        basis=PathAuthorityBasis.TASK_CONTEXT,
        constraints=(
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_OPERATOR_REVIEW),
            _constraint(constraint_kind=PathAuthorityConstraintKind.RESTRICTS_WRITE),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert scope.subject.subject_kind is PathAuthoritySubjectKind.AGENT
    assert PathScopeAction.WRITE in scope.actions
    assert not hasattr(scope, "can_write")


def test_declaration_patterns_tool_input_use() -> None:
    scope = build_path_authority_scope(
        subject=_subject(
            subject_kind=PathAuthoritySubjectKind.TOOL,
            display_name="tool-input-use",
        ),
        actions=(PathScopeAction.TOOL_INPUT_USE,),
        basis=PathAuthorityBasis.POLICY_DECLARATION,
        constraints=(
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_POLICY_REVIEW),
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_TRACE),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert scope.subject.subject_kind is PathAuthoritySubjectKind.TOOL
    assert PathScopeAction.TOOL_INPUT_USE in scope.actions
    assert not hasattr(scope, "invoke")


def test_declaration_patterns_model_prompt_context_use() -> None:
    scope = build_path_authority_scope(
        subject=_subject(
            subject_kind=PathAuthoritySubjectKind.MODEL,
            display_name="model-prompt-context",
        ),
        actions=(PathScopeAction.PROMPT_CONTEXT_USE,),
        basis=PathAuthorityBasis.POLICY_DECLARATION,
        constraints=(
            _constraint(
                constraint_kind=PathAuthorityConstraintKind.RESTRICTS_PROMPT_CONTEXT_USE,
            ),
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_POLICY_REVIEW),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert scope.subject.subject_kind is PathAuthoritySubjectKind.MODEL
    assert PathScopeAction.PROMPT_CONTEXT_USE in scope.actions
    assert not hasattr(scope, "trust_content")


def test_declaration_patterns_runtime_execute() -> None:
    scope = build_path_authority_scope(
        subject=_subject(
            subject_kind=PathAuthoritySubjectKind.RUNTIME,
            display_name="runtime-execute",
        ),
        actions=(PathScopeAction.EXECUTE,),
        basis=PathAuthorityBasis.SYSTEM_DEFAULT,
        constraints=(
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_SANDBOX_LATER),
            _constraint(constraint_kind=PathAuthorityConstraintKind.REQUIRES_OPERATOR_REVIEW),
            _constraint(constraint_kind=PathAuthorityConstraintKind.RESTRICTS_EXECUTE),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert scope.subject.subject_kind is PathAuthoritySubjectKind.RUNTIME
    assert PathScopeAction.EXECUTE in scope.actions
    assert not hasattr(scope, "can_execute")


def test_registry_hash_is_order_insensitive_where_possible() -> None:
    scope_a = _scope(
        subject=_subject(display_name="scope-a"),
        actions=(PathScopeAction.READ,),
    )
    scope_b = _scope(
        subject=_subject(display_name="scope-b"),
        actions=(PathScopeAction.LIST,),
    )

    first = build_path_authority_scope_registry(
        scopes=(scope_a, scope_b),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_path_authority_scope_registry(
        scopes=(scope_b, scope_a),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.registry_hash == second.registry_hash


def test_p1_7_0_to_p1_7_5_regression_still_pass() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/path_governance/test_p1_7_0_foundation.py",
            "tests/path_governance/test_p1_7_1_path_identity.py",
            "tests/path_governance/test_p1_7_2_source_identity.py",
            "tests/path_governance/test_p1_7_3_source_trust_taxonomy.py",
            "tests/path_governance/test_p1_7_4_trusted_roots.py",
            "tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py",
            "-k",
            "not regression_still_pass",
            "-q",
        ],
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr

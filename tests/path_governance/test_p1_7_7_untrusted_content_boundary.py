"""P1.7.7 — Untrusted Content Boundary Model tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    BoundaryRestriction,
    BoundaryRestrictionKind,
    ContentInfluenceSurface,
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    SourceKind,
    SourceOrigin,
    SourceTrustLabel,
    UntrustedBoundaryPosture,
    UntrustedContentBoundary,
    UntrustedContentBoundaryRegistry,
    UntrustedContentKind,
    build_source_identity,
    build_untrusted_content_boundary,
    build_untrusted_content_boundary_registry,
    default_posture_for_trust_label,
    default_restrictions_for_trust_label,
    to_canonical_json,
)


_REQUIRED_CONTENT_KINDS = {
    "EXTERNAL_TEXT",
    "UPLOADED_FILE_CONTENT",
    "WEB_CONTENT",
    "TOOL_OUTPUT",
    "MODEL_OUTPUT",
    "AGENT_OUTPUT",
    "MEMORY_RECALL",
    "PATH_REFERENCED_CONTENT",
    "UNKNOWN",
}

_REQUIRED_INFLUENCE_SURFACES = {
    "INFORMATIONAL_CONTEXT",
    "CITATION",
    "SUMMARY",
    "PROMPT_INSTRUCTION",
    "TOOL_ARGUMENT",
    "MEMORY_WRITE",
    "POLICY_DEFINITION",
    "AUTHORITY_EXPANSION",
    "EXECUTION_REQUEST",
    "SOURCE_CANONIZATION",
    "UNKNOWN",
}

_REQUIRED_RESTRICTION_KINDS = {
    "REQUIRES_SOURCE_LABEL",
    "REQUIRES_TRUST_REVIEW",
    "REQUIRES_OPERATOR_REVIEW",
    "REQUIRES_POLICY_REVIEW",
    "REQUIRES_QUARANTINE_LATER",
    "RESTRICTS_PROMPT_INSTRUCTION",
    "RESTRICTS_TOOL_ARGUMENT",
    "RESTRICTS_MEMORY_WRITE",
    "RESTRICTS_POLICY_DEFINITION",
    "RESTRICTS_AUTHORITY_EXPANSION",
    "RESTRICTS_EXECUTION_REQUEST",
    "UNKNOWN",
}

_REQUIRED_POSTURES = {
    "INFORM_ONLY",
    "QUOTABLE",
    "SUMMARIZABLE",
    "REVIEW_REQUIRED",
    "QUARANTINED",
    "UNKNOWN",
}

_FORBIDDEN_METHOD_NAMES = {
    "allow",
    "deny",
    "block",
    "enforce",
    "apply",
    "approve",
    "authorize",
    "can_command",
    "can_write_memory",
    "can_use_as_tool_argument",
    "filter",
    "rewrite",
    "sanitize",
    "quarantine_runtime",
    "delete_content",
    "write_memory",
    "block_tool",
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
    "from agentic_runtime.prompts",
    "from agentic_runtime.memory",
)


def _source_identity(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.EXTERNAL,
    source_kind: SourceKind = SourceKind.EXTERNAL_WEB,
    source_origin: SourceOrigin = SourceOrigin.EXTERNAL_NETWORK,
):
    return build_source_identity(
        source_kind=source_kind,
        source_origin=source_origin,
        uri_or_path="https://example.invalid/source",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=trust_label,
    )


def _restriction(
    *,
    restriction_kind: BoundaryRestrictionKind = BoundaryRestrictionKind.RESTRICTS_PROMPT_INSTRUCTION,
    surface: ContentInfluenceSurface = ContentInfluenceSurface.PROMPT_INSTRUCTION,
    reason: str = "fixture prompt instruction restriction",
):
    return BoundaryRestriction(
        restriction_kind=restriction_kind,
        surface=surface,
        reason=reason,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _boundary(
    *,
    content_kind: UntrustedContentKind = UntrustedContentKind.EXTERNAL_TEXT,
    trust_label: SourceTrustLabel = SourceTrustLabel.EXTERNAL,
    source_identity=None,
    influence_surfaces: tuple[ContentInfluenceSurface, ...] | None = None,
    restrictions=None,
    posture: UntrustedBoundaryPosture | None = None,
):
    return build_untrusted_content_boundary(
        content_kind=content_kind,
        source_identity=source_identity or _source_identity(trust_label=trust_label),
        trust_label=trust_label,
        influence_surfaces=influence_surfaces,
        restrictions=restrictions,
        posture=posture,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "UntrustedContentKind",
        "ContentInfluenceSurface",
        "BoundaryRestrictionKind",
        "UntrustedBoundaryPosture",
        "BoundaryRestriction",
        "UntrustedContentBoundary",
        "UntrustedContentBoundaryRegistry",
        "build_untrusted_content_boundary",
        "build_untrusted_content_boundary_registry",
    ):
        assert hasattr(pg, name)


def test_untrusted_content_kind_has_required_values() -> None:
    assert {item.value for item in UntrustedContentKind} == _REQUIRED_CONTENT_KINDS


def test_content_influence_surface_has_required_values() -> None:
    assert {item.value for item in ContentInfluenceSurface} == _REQUIRED_INFLUENCE_SURFACES


def test_boundary_restriction_kind_has_required_values() -> None:
    assert {item.value for item in BoundaryRestrictionKind} == _REQUIRED_RESTRICTION_KINDS


def test_untrusted_boundary_posture_has_required_values() -> None:
    assert {item.value for item in UntrustedBoundaryPosture} == _REQUIRED_POSTURES


def test_boundary_restriction_builds_deterministically() -> None:
    first = _restriction()
    second = _restriction()

    assert first.restriction_id == second.restriction_id
    assert to_canonical_json(first) == to_canonical_json(second)


def test_untrusted_content_boundary_builds_from_source_identity() -> None:
    identity = _source_identity()
    boundary = _boundary(source_identity=identity)

    assert boundary.source_identity.identity_hash == identity.identity_hash
    assert boundary.boundary_hash
    assert boundary.boundary_id


def test_boundary_can_represent_external_as_inform_only() -> None:
    boundary = _boundary(
        trust_label=SourceTrustLabel.EXTERNAL,
        posture=UntrustedBoundaryPosture.INFORM_ONLY,
        influence_surfaces=(
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.CITATION,
        ),
        restrictions=default_restrictions_for_trust_label(
            SourceTrustLabel.EXTERNAL,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
    )

    assert boundary.posture is UntrustedBoundaryPosture.INFORM_ONLY
    assert ContentInfluenceSurface.INFORMATIONAL_CONTEXT in boundary.influence_surfaces
    assert not hasattr(boundary, "can_command")


def test_boundary_can_restrict_prompt_instruction() -> None:
    boundary = _boundary(
        influence_surfaces=(ContentInfluenceSurface.PROMPT_INSTRUCTION,),
        restrictions=(_restriction(),),
    )

    assert ContentInfluenceSurface.PROMPT_INSTRUCTION in boundary.influence_surfaces
    assert any(
        item.restriction_kind is BoundaryRestrictionKind.RESTRICTS_PROMPT_INSTRUCTION
        for item in boundary.restrictions
    )
    assert not hasattr(boundary, "rewrite_prompt")
    assert not hasattr(boundary, "filter_prompt")


def test_boundary_can_restrict_tool_argument() -> None:
    boundary = _boundary(
        influence_surfaces=(ContentInfluenceSurface.TOOL_ARGUMENT,),
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_TOOL_ARGUMENT,
                surface=ContentInfluenceSurface.TOOL_ARGUMENT,
            ),
        ),
    )

    assert ContentInfluenceSurface.TOOL_ARGUMENT in boundary.influence_surfaces
    assert not hasattr(boundary, "block_tool")


def test_boundary_can_restrict_memory_write() -> None:
    boundary = _boundary(
        influence_surfaces=(ContentInfluenceSurface.MEMORY_WRITE,),
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_MEMORY_WRITE,
                surface=ContentInfluenceSurface.MEMORY_WRITE,
            ),
        ),
    )

    assert ContentInfluenceSurface.MEMORY_WRITE in boundary.influence_surfaces
    assert not hasattr(boundary, "write_memory")
    assert not hasattr(boundary, "gate_memory")


def test_boundary_can_restrict_policy_definition() -> None:
    boundary = _boundary(
        influence_surfaces=(ContentInfluenceSurface.POLICY_DEFINITION,),
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_POLICY_DEFINITION,
                surface=ContentInfluenceSurface.POLICY_DEFINITION,
            ),
        ),
    )

    assert ContentInfluenceSurface.POLICY_DEFINITION in boundary.influence_surfaces
    assert not hasattr(boundary, "mutate_policy")


def test_boundary_can_restrict_authority_expansion() -> None:
    boundary = _boundary(
        influence_surfaces=(ContentInfluenceSurface.AUTHORITY_EXPANSION,),
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_AUTHORITY_EXPANSION,
                surface=ContentInfluenceSurface.AUTHORITY_EXPANSION,
            ),
        ),
    )

    assert ContentInfluenceSurface.AUTHORITY_EXPANSION in boundary.influence_surfaces
    assert not hasattr(boundary, "resolve_authority")


def test_boundary_can_restrict_execution_request() -> None:
    boundary = _boundary(
        influence_surfaces=(ContentInfluenceSurface.EXECUTION_REQUEST,),
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_EXECUTION_REQUEST,
                surface=ContentInfluenceSurface.EXECUTION_REQUEST,
            ),
        ),
    )

    assert ContentInfluenceSurface.EXECUTION_REQUEST in boundary.influence_surfaces
    assert not hasattr(boundary, "execute")
    assert not hasattr(boundary, "submit")


def test_trusted_still_does_not_imply_command_authority() -> None:
    boundary = _boundary(
        trust_label=SourceTrustLabel.TRUSTED,
        posture=UntrustedBoundaryPosture.SUMMARIZABLE,
    )

    assert boundary.trust_label is SourceTrustLabel.TRUSTED
    assert not hasattr(boundary, "can_command")
    assert not hasattr(boundary, "command_authority")


def test_operator_provided_still_does_not_override_policy() -> None:
    boundary = _boundary(
        trust_label=SourceTrustLabel.OPERATOR_PROVIDED,
        posture=UntrustedBoundaryPosture.REVIEW_REQUIRED,
    )

    assert boundary.trust_label is SourceTrustLabel.OPERATOR_PROVIDED
    assert not hasattr(boundary, "override_policy")
    assert not hasattr(boundary, "policy_override")


def test_tool_generated_still_does_not_imply_truth() -> None:
    boundary = _boundary(
        content_kind=UntrustedContentKind.TOOL_OUTPUT,
        trust_label=SourceTrustLabel.TOOL_GENERATED,
        source_identity=_source_identity(
            trust_label=SourceTrustLabel.TOOL_GENERATED,
            source_kind=SourceKind.TOOL_OUTPUT,
            source_origin=SourceOrigin.GOVERNED_TOOL,
        ),
    )

    assert boundary.trust_label is SourceTrustLabel.TOOL_GENERATED
    assert not hasattr(boundary, "assert_truth")
    assert not hasattr(boundary, "verifier_bypass")


def test_untrusted_can_inform_but_cannot_command() -> None:
    boundary = _boundary(
        trust_label=SourceTrustLabel.UNTRUSTED,
        posture=UntrustedBoundaryPosture.INFORM_ONLY,
        influence_surfaces=(
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.CITATION,
        ),
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_PROMPT_INSTRUCTION,
                surface=ContentInfluenceSurface.PROMPT_INSTRUCTION,
            ),
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_TOOL_ARGUMENT,
                surface=ContentInfluenceSurface.TOOL_ARGUMENT,
            ),
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_AUTHORITY_EXPANSION,
                surface=ContentInfluenceSurface.AUTHORITY_EXPANSION,
            ),
        ),
    )

    assert ContentInfluenceSurface.INFORMATIONAL_CONTEXT in boundary.influence_surfaces
    restricted_surfaces = {item.surface for item in boundary.restrictions}
    assert ContentInfluenceSurface.PROMPT_INSTRUCTION in restricted_surfaces
    assert not hasattr(boundary, "can_command")


def test_unknown_requires_review_or_uncertainty_posture() -> None:
    boundary = _boundary(
        trust_label=SourceTrustLabel.UNKNOWN,
        posture=None,
    )

    assert boundary.posture in {
        UntrustedBoundaryPosture.REVIEW_REQUIRED,
        UntrustedBoundaryPosture.UNKNOWN,
    }
    assert boundary.trust_label is SourceTrustLabel.UNKNOWN
    assert default_posture_for_trust_label(SourceTrustLabel.UNKNOWN) is (
        UntrustedBoundaryPosture.REVIEW_REQUIRED
    )


def test_quarantined_stays_restricted_not_deleted() -> None:
    boundary = _boundary(
        trust_label=SourceTrustLabel.QUARANTINED,
        posture=UntrustedBoundaryPosture.QUARANTINED,
        influence_surfaces=(),
        restrictions=default_restrictions_for_trust_label(
            SourceTrustLabel.QUARANTINED,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
    )

    assert boundary.posture is UntrustedBoundaryPosture.QUARANTINED
    assert not hasattr(boundary, "delete")
    assert not hasattr(boundary, "quarantine_runtime")


def test_boundary_hash_is_deterministic() -> None:
    first = _boundary()
    second = _boundary()

    assert first.boundary_hash == second.boundary_hash
    assert first.boundary_id == second.boundary_id


def test_changed_restriction_changes_boundary_hash() -> None:
    first = _boundary(
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_PROMPT_INSTRUCTION,
                surface=ContentInfluenceSurface.PROMPT_INSTRUCTION,
            ),
        ),
    )
    second = _boundary(
        restrictions=(
            _restriction(
                restriction_kind=BoundaryRestrictionKind.RESTRICTS_TOOL_ARGUMENT,
                surface=ContentInfluenceSurface.TOOL_ARGUMENT,
            ),
        ),
    )

    assert first.boundary_hash != second.boundary_hash


def test_changed_surface_changes_boundary_hash() -> None:
    first = _boundary(
        influence_surfaces=(ContentInfluenceSurface.INFORMATIONAL_CONTEXT,),
        restrictions=(),
        posture=UntrustedBoundaryPosture.INFORM_ONLY,
    )
    second = _boundary(
        influence_surfaces=(ContentInfluenceSurface.CITATION,),
        restrictions=(),
        posture=UntrustedBoundaryPosture.INFORM_ONLY,
    )

    assert first.boundary_hash != second.boundary_hash


def test_registry_hash_is_deterministic() -> None:
    boundary = _boundary()
    first = build_untrusted_content_boundary_registry(
        boundaries=(boundary,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_untrusted_content_boundary_registry(
        boundaries=(boundary,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.registry_hash == second.registry_hash


def test_source_labels_are_preserved() -> None:
    live_boundary = build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_source_identity(),
        trust_label=SourceTrustLabel.EXTERNAL,
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_boundary = _boundary()

    assert live_boundary.source_label is ProjectionSourceLabel.LIVE
    assert fixture_boundary.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    boundary = _boundary()
    registry = build_untrusted_content_boundary_registry(
        boundaries=(boundary,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert boundary.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert registry.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_unknown_fields_are_rejected() -> None:
    restriction = _restriction()
    boundary = _boundary(restrictions=(restriction,))
    registry = build_untrusted_content_boundary_registry(
        boundaries=(boundary,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    restriction_payload = restriction.to_canonical_dict()
    restriction_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as restriction_error:
        BoundaryRestriction.from_dict(restriction_payload)
    assert restriction_error.value.code.value == "UNKNOWN_FIELD"

    boundary_payload = boundary.to_canonical_dict()
    boundary_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as boundary_error:
        UntrustedContentBoundary.from_dict(boundary_payload)
    assert boundary_error.value.code.value == "UNKNOWN_FIELD"

    registry_payload = registry.to_canonical_dict()
    registry_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as registry_error:
        UntrustedContentBoundaryRegistry.from_dict(registry_payload)
    assert registry_error.value.code.value == "UNKNOWN_FIELD"


def test_no_allow_deny_block_enforce_api_exists() -> None:
    import agentic_runtime.path_governance as pg

    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.untrusted_content_boundary",
    ))
    for name in (
        "can_command",
        "can_write_memory",
        "can_use_as_tool_argument",
        "authorize",
        "is_allowed",
        "is_denied",
    ):
        assert name not in pg.__all__
        assert f"def {name}" not in source

    for cls in (
        BoundaryRestriction,
        UntrustedContentBoundary,
        UntrustedContentBoundaryRegistry,
    ):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _FORBIDDEN_METHOD_NAMES & methods


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.untrusted_content_boundary",
    ))
    forbidden_snippets = (
        "def filter",
        "def rewrite",
        "def sanitize",
        "prompt_compiler",
        "prompt_assembly",
        "injection_firewall",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_memory_write_occurs() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.untrusted_content_boundary",
    ))
    forbidden_snippets = (
        "write_memory",
        "canonize_memory",
        "memory_writer",
        "from agentic_runtime.memory",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_runtime_sandbox_approval_imports() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.untrusted_content_boundary",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.untrusted_content_boundary",
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
        "requests",
        "urllib",
        "httpx",
        "fetch(",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_p1_7_0_to_p1_7_6_regression_still_pass() -> None:
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
            "tests/path_governance/test_p1_7_6_path_authority_scope.py",
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

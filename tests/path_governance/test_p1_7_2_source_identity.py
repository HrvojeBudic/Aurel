"""P1.7.2 — Source Identity & SourceRef Schema tests."""
from __future__ import annotations

import builtins
import importlib
import inspect
from pathlib import Path

import pytest

from agentic_runtime.path_governance import (
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    SourceIdentity,
    SourceKind,
    SourceLineageRef,
    SourceLineageRelationship,
    SourceOrigin,
    SourceRef,
    SourceTrustLabel,
    build_source_identity,
)


_REQUIRED_SOURCE_KINDS = {
    "OPERATOR_INPUT",
    "REPO_FILE",
    "LOCAL_FILE",
    "UPLOADED_FILE",
    "EXTERNAL_WEB",
    "TOOL_OUTPUT",
    "MODEL_OUTPUT",
    "AGENT_OUTPUT",
    "MEMORY_ENTRY",
    "PATH_REF",
    "UNKNOWN",
}

_REQUIRED_SOURCE_ORIGINS = {
    "OPERATOR",
    "INTERNAL_REPO",
    "LOCAL_MACHINE",
    "UPLOAD",
    "EXTERNAL_NETWORK",
    "GOVERNED_TOOL",
    "MODEL",
    "AGENT",
    "MEMORY",
    "UNKNOWN",
}

_REQUIRED_LINEAGE_RELATIONSHIPS = {
    "DERIVED_FROM",
    "EXTRACTED_FROM",
    "SUMMARIZED_FROM",
    "UPLOADED_AS",
    "GENERATED_BY",
    "QUOTED_FROM",
    "REFERENCES",
    "UNKNOWN",
}

_AUTHORITY_METHOD_NAMES = {
    "allow",
    "deny",
    "enforce",
    "permission",
    "command_authority",
    "prompt_authority",
    "memory_write_authority",
    "resolve_source",
    "resolve_trust",
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
    "requests",
    "httpx",
    "urllib",
)


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert SourceKind is pg.SourceKind
    assert SourceOrigin is pg.SourceOrigin
    assert SourceLineageRelationship is pg.SourceLineageRelationship
    assert SourceRef is pg.SourceRef
    assert SourceLineageRef is pg.SourceLineageRef
    assert SourceIdentity is pg.SourceIdentity
    assert build_source_identity is pg.build_source_identity


def test_source_kind_has_required_values() -> None:
    assert {item.value for item in SourceKind} == _REQUIRED_SOURCE_KINDS


def test_source_origin_has_required_values() -> None:
    assert {item.value for item in SourceOrigin} == _REQUIRED_SOURCE_ORIGINS


def test_source_lineage_relationship_has_required_values() -> None:
    assert {
        item.value for item in SourceLineageRelationship
    } == _REQUIRED_LINEAGE_RELATIONSHIPS


def test_source_ref_represents_operator_input() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        display_name="operator prompt",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.OPERATOR_PROVIDED,
    )

    assert identity.source_ref.source_kind is SourceKind.OPERATOR_INPUT
    assert identity.source_ref.source_origin is SourceOrigin.OPERATOR
    assert identity.source_ref.trust_label is SourceTrustLabel.OPERATOR_PROVIDED
    assert not hasattr(identity.source_ref, "command_authority")


def test_source_ref_represents_repo_file_without_reading_file(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("P1.7.2 must not read files")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "read_text", fail_open)
    first = build_source_identity(
        source_kind=SourceKind.REPO_FILE,
        source_origin=SourceOrigin.INTERNAL_REPO,
        uri_or_path="src/agentic_runtime/path_governance/source_identity.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.INTERNAL_REPO,
    )
    second = build_source_identity(
        source_kind=SourceKind.REPO_FILE,
        source_origin=SourceOrigin.INTERNAL_REPO,
        uri_or_path="src/agentic_runtime/path_governance/source_identity.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.INTERNAL_REPO,
    )

    assert first.source_ref.source_id == second.source_ref.source_id


def test_source_ref_represents_local_file_without_reading_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_fs(*args: object, **kwargs: object) -> None:
        raise AssertionError("P1.7.2 must not inspect local filesystem")

    monkeypatch.setattr(Path, "read_text", fail_fs)
    monkeypatch.setattr(Path, "stat", fail_fs)
    monkeypatch.setattr(Path, "resolve", fail_fs)
    identity = build_source_identity(
        source_kind=SourceKind.LOCAL_FILE,
        source_origin=SourceOrigin.LOCAL_MACHINE,
        uri_or_path="/private/operator/file.txt",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.LOCAL_PRIVATE,
    )

    assert identity.source_ref.uri_or_path == "/private/operator/file.txt"
    assert not hasattr(identity.source_ref, "allowed")
    assert not hasattr(identity.source_ref, "denied")


def test_source_ref_represents_uploaded_file() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.UPLOADED_FILE,
        source_origin=SourceOrigin.UPLOAD,
        display_name="operator-upload.txt",
        uri_or_path="upload://operator-upload.txt",
        content_hash="sha256:explicit-upload-hash",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    repeat = build_source_identity(
        source_kind=SourceKind.UPLOADED_FILE,
        source_origin=SourceOrigin.UPLOAD,
        display_name="operator-upload.txt",
        uri_or_path="upload://operator-upload.txt",
        content_hash="sha256:explicit-upload-hash",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert identity.source_ref.source_id == repeat.source_ref.source_id


def test_source_ref_represents_external_web_without_fetching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("P1.7.2 must not fetch external web sources")

    monkeypatch.setattr("urllib.request.urlopen", fail_network)
    identity = build_source_identity(
        source_kind=SourceKind.EXTERNAL_WEB,
        source_origin=SourceOrigin.EXTERNAL_NETWORK,
        uri_or_path="https://example.invalid/source",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.EXTERNAL,
    )

    assert identity.source_ref.source_kind is SourceKind.EXTERNAL_WEB
    assert identity.source_ref.source_origin is SourceOrigin.EXTERNAL_NETWORK
    assert identity.source_ref.trust_label is SourceTrustLabel.EXTERNAL
    assert not hasattr(identity, "trusted")


def test_source_ref_represents_tool_model_agent_output() -> None:
    cases = (
        (SourceKind.TOOL_OUTPUT, SourceOrigin.GOVERNED_TOOL, "tool:lint"),
        (SourceKind.MODEL_OUTPUT, SourceOrigin.MODEL, "model:summary"),
        (SourceKind.AGENT_OUTPUT, SourceOrigin.AGENT, "agent:review"),
    )

    for source_kind, source_origin, display_name in cases:
        first = build_source_identity(
            source_kind=source_kind,
            source_origin=source_origin,
            display_name=display_name,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        )
        second = build_source_identity(
            source_kind=source_kind,
            source_origin=source_origin,
            display_name=display_name,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        )
        assert first.identity_hash == second.identity_hash


def test_source_ref_represents_memory_entry() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.MEMORY_ENTRY,
        source_origin=SourceOrigin.MEMORY,
        uri_or_path="memory://entry/abc123",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.UNKNOWN,
    )

    assert identity.source_ref.uri_or_path == "memory://entry/abc123"
    assert not hasattr(identity.source_ref, "memory_write_authority")


def test_source_ref_represents_path_ref_without_resolving_path() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.PATH_REF,
        source_origin=SourceOrigin.INTERNAL_REPO,
        uri_or_path="src/agentic_runtime/path_governance/path_identity.py",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"path_identity_hash": "abc123"},
    )

    assert identity.source_ref.source_kind is SourceKind.PATH_REF
    assert identity.source_ref.metadata["path_identity_hash"] == "abc123"
    assert not hasattr(identity.source_ref, "trusted_root_id")


def test_source_identity_hash_is_deterministic() -> None:
    first = build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        display_name="operator input",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        display_name="operator input",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.source_ref.source_id == second.source_ref.source_id
    assert first.identity_hash == second.identity_hash


def test_different_source_kind_or_origin_changes_identity_hash() -> None:
    operator_source = build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        display_name="same display",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    model_source = build_source_identity(
        source_kind=SourceKind.MODEL_OUTPUT,
        source_origin=SourceOrigin.MODEL,
        display_name="same display",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert operator_source.source_ref.source_id != model_source.source_ref.source_id
    assert operator_source.identity_hash != model_source.identity_hash


def test_source_lineage_hash_is_deterministic() -> None:
    first = build_source_identity(
        source_kind=SourceKind.MODEL_OUTPUT,
        source_origin=SourceOrigin.MODEL,
        display_name="summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        lineage_refs=({
            "parent_source_id": "parent-1",
            "relationship": SourceLineageRelationship.SUMMARIZED_FROM,
            "notes": ("summary seed",),
        },),
    )
    second = build_source_identity(
        source_kind=SourceKind.MODEL_OUTPUT,
        source_origin=SourceOrigin.MODEL,
        display_name="summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        lineage_refs=({
            "parent_source_id": "parent-1",
            "relationship": SourceLineageRelationship.SUMMARIZED_FROM,
            "notes": ("summary seed",),
        },),
    )
    different = build_source_identity(
        source_kind=SourceKind.MODEL_OUTPUT,
        source_origin=SourceOrigin.MODEL,
        display_name="summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        lineage_refs=({
            "parent_source_id": "parent-1",
            "relationship": SourceLineageRelationship.QUOTED_FROM,
            "notes": ("summary seed",),
        },),
    )

    assert first.lineage_refs[0].lineage_hash == second.lineage_refs[0].lineage_hash
    assert first.lineage_refs[0].lineage_hash != different.lineage_refs[0].lineage_hash


def test_unknown_fields_are_rejected() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        lineage_refs=({
            "parent_source_id": "parent-1",
            "relationship": SourceLineageRelationship.DERIVED_FROM,
        },),
    )
    source_payload = identity.source_ref.to_canonical_dict()
    source_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as source_error:
        SourceRef.from_dict(source_payload)
    assert source_error.value.code.value == "UNKNOWN_FIELD"

    lineage_payload = identity.lineage_refs[0].to_canonical_dict()
    lineage_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as lineage_error:
        SourceLineageRef.from_dict(lineage_payload)
    assert lineage_error.value.code.value == "UNKNOWN_FIELD"

    identity_payload = identity.to_canonical_dict()
    identity_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as identity_error:
        SourceIdentity.from_dict(identity_payload)
    assert identity_error.value.code.value == "UNKNOWN_FIELD"


def test_source_identity_does_not_imply_trust() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.EXTERNAL_WEB,
        source_origin=SourceOrigin.EXTERNAL_NETWORK,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.EXTERNAL,
    )

    assert identity.source_ref.trust_label is SourceTrustLabel.EXTERNAL
    for cls in (SourceRef, SourceIdentity):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _AUTHORITY_METHOD_NAMES & methods


def test_source_origin_does_not_imply_authority() -> None:
    operator_source = build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    external_source = build_source_identity(
        source_kind=SourceKind.EXTERNAL_WEB,
        source_origin=SourceOrigin.EXTERNAL_NETWORK,
        uri_or_path="https://example.invalid/source",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    for identity in (operator_source, external_source):
        canonical = identity.source_ref.to_canonical_dict()
        assert "authority" not in canonical
        assert "allow" not in canonical
        assert "deny" not in canonical


def test_external_source_may_be_identified_but_not_command_authoritative() -> None:
    identity = build_source_identity(
        source_kind=SourceKind.EXTERNAL_WEB,
        source_origin=SourceOrigin.EXTERNAL_NETWORK,
        uri_or_path="https://example.invalid/source",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=SourceTrustLabel.EXTERNAL,
    )

    assert identity.source_ref.source_kind is SourceKind.EXTERNAL_WEB
    assert not hasattr(identity.source_ref, "prompt_authority")
    assert not hasattr(identity.source_ref, "command_authority")
    assert not hasattr(identity.source_ref, "memory_write_authority")


def test_no_network_or_filesystem_reads_occur() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_identity",
    ))
    forbidden_snippets = (
        "urlopen(",
        "requests.",
        "httpx.",
        "read_text(",
        ".read(",
        ".stat(",
        ".resolve(",
        "open(",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_resolver_or_enforcement_claims_exist() -> None:
    import agentic_runtime.path_governance as pg

    assert "resolve_source_identity" not in pg.__all__
    assert "source_trust_resolver" not in pg.__all__
    assert "source_authority_resolver" not in pg.__all__

    for cls in (SourceRef, SourceLineageRef, SourceIdentity):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _AUTHORITY_METHOD_NAMES & methods

    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_identity",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source

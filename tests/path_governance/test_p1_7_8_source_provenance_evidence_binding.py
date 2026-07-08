"""P1.7.8 — Source Provenance & Evidence Binding Seed tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    EvidenceBindingKind,
    EvidenceConfidence,
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathGovernanceUnknownFieldError,
    PathKind,
    PathScopeAction,
    ProvenanceBinding,
    ProvenanceBindingRegistry,
    ProjectionSourceLabel,
    SourceClaimKind,
    SourceClaimRef,
    SourceEvidenceRef,
    SourceKind,
    SourceOrigin,
    SourceProvenanceKind,
    SourceProvenanceRef,
    SourceTrustLabel,
    UntrustedContentKind,
    build_path_authority_scope,
    build_path_identity,
    build_provenance_binding,
    build_provenance_binding_registry,
    build_source_claim_ref,
    build_source_evidence_ref,
    build_source_identity,
    build_source_provenance_ref,
    build_untrusted_content_boundary,
    to_canonical_json,
)


_REQUIRED_PROVENANCE_KINDS = {
    "DIRECT_SOURCE",
    "DERIVED_SOURCE",
    "TRANSFORMED_SOURCE",
    "TOOL_PRODUCED",
    "MODEL_PRODUCED",
    "AGENT_PRODUCED",
    "MEMORY_RECALLED",
    "OPERATOR_PROVIDED",
    "UNKNOWN",
}

_REQUIRED_EVIDENCE_KINDS = {
    "SOURCE_IDENTITY",
    "SOURCE_TRUST_LABEL",
    "PATH_IDENTITY",
    "TRUSTED_ROOT_DECLARATION",
    "ESCAPE_DETECTION_RESULT",
    "AUTHORITY_SCOPE_DECLARATION",
    "UNTRUSTED_BOUNDARY_DECLARATION",
    "CLAIM_REFERENCE",
    "OUTPUT_REFERENCE",
    "UNKNOWN",
}

_REQUIRED_CONFIDENCE_VALUES = {
    "HIGH",
    "MEDIUM",
    "LOW",
    "UNKNOWN",
    "CONFLICTED",
    "UNVERIFIED",
}

_REQUIRED_CLAIM_KINDS = {
    "FACTUAL_CLAIM",
    "INSTRUCTION_CLAIM",
    "POLICY_CLAIM",
    "AUTHORITY_CLAIM",
    "MEMORY_CLAIM",
    "TOOL_RESULT_CLAIM",
    "MODEL_OUTPUT_CLAIM",
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
    "resolve_trust",
    "resolve_path",
    "resolve_provenance",
    "classify_risk",
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


def _path_identity(raw_path: str = "src/example.py"):
    return build_path_identity(
        raw_path,
        path_kind=PathKind.REPO_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _scope():
    subject = PathAuthoritySubject(
        subject_kind=PathAuthoritySubjectKind.OPERATOR,
        display_name="fixture-operator",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    return build_path_authority_scope(
        subject=subject,
        actions=(PathScopeAction.READ, PathScopeAction.LIST),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _boundary():
    return build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_source_identity(),
        trust_label=SourceTrustLabel.EXTERNAL,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _binding(**kwargs):
    defaults = {
        "source_identity": _source_identity(),
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
    }
    defaults.update(kwargs)
    return build_provenance_binding(**defaults)


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "SourceProvenanceKind",
        "EvidenceBindingKind",
        "EvidenceConfidence",
        "SourceClaimKind",
        "SourceEvidenceRef",
        "SourceClaimRef",
        "SourceProvenanceRef",
        "ProvenanceBinding",
        "ProvenanceBindingRegistry",
        "build_source_evidence_ref",
        "build_source_claim_ref",
        "build_source_provenance_ref",
        "build_provenance_binding",
        "build_provenance_binding_registry",
    ):
        assert hasattr(pg, name)


def test_source_provenance_kind_has_required_values() -> None:
    assert {item.value for item in SourceProvenanceKind} == _REQUIRED_PROVENANCE_KINDS


def test_evidence_binding_kind_has_required_values() -> None:
    assert {item.value for item in EvidenceBindingKind} == _REQUIRED_EVIDENCE_KINDS


def test_evidence_confidence_has_required_values() -> None:
    assert {item.value for item in EvidenceConfidence} == _REQUIRED_CONFIDENCE_VALUES


def test_source_claim_kind_has_required_values() -> None:
    assert {item.value for item in SourceClaimKind} == _REQUIRED_CLAIM_KINDS


def test_source_evidence_ref_builds_deterministically() -> None:
    source = _source_identity()
    first = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_IDENTITY,
        source,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_IDENTITY,
        source,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.evidence_id == second.evidence_id
    assert first.evidence_hash == second.evidence_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_source_claim_ref_builds_deterministically() -> None:
    source = _source_identity()
    first = build_source_claim_ref(
        SourceClaimKind.FACTUAL_CLAIM,
        source,
        "fixture factual claim summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_source_claim_ref(
        SourceClaimKind.FACTUAL_CLAIM,
        source,
        "fixture factual claim summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.claim_id == second.claim_id
    assert first.claim_hash == second.claim_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_source_provenance_ref_builds_deterministically() -> None:
    source = _source_identity()
    first = build_source_provenance_ref(
        SourceProvenanceKind.DIRECT_SOURCE,
        source,
        derived_from=("parent-source-a", "parent-source-b"),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_source_provenance_ref(
        SourceProvenanceKind.DIRECT_SOURCE,
        source,
        derived_from=("parent-source-b", "parent-source-a"),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.provenance_id == second.provenance_id
    assert first.provenance_hash == second.provenance_hash
    assert first.derived_from == ("parent-source-a", "parent-source-b")


def test_provenance_binding_can_reference_source_identity() -> None:
    source = _source_identity()
    binding = _binding(source_identity=source)

    assert binding.source_identity.identity_hash == source.identity_hash
    assert binding.binding_hash
    assert binding.binding_id


def test_provenance_binding_can_reference_boundary_ref_id() -> None:
    boundary = _boundary()
    binding = _binding(boundary_ref_id=boundary.boundary_id)

    assert binding.boundary_ref_id == boundary.boundary_id
    assert not hasattr(binding, "filter")
    assert not hasattr(binding, "block")


def test_provenance_binding_can_reference_authority_scope_id() -> None:
    scope = _scope()
    binding = _binding(authority_scope_id=scope.scope_id)

    assert binding.authority_scope_id == scope.scope_id
    assert not hasattr(binding, "authorize")
    assert not hasattr(binding, "allow")


def test_provenance_binding_can_reference_path_identity_hash() -> None:
    path_identity = _path_identity()
    binding = _binding(path_identity_hash=path_identity.identity_hash)

    assert binding.path_identity_hash == path_identity.identity_hash


def test_binding_can_include_source_trust_label_evidence() -> None:
    source = _source_identity()
    evidence = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_TRUST_LABEL,
        source,
        metadata={"trust_label": SourceTrustLabel.EXTERNAL.value},
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    binding = _binding(evidence_refs=(evidence,))

    assert binding.evidence_refs[0].evidence_kind is EvidenceBindingKind.SOURCE_TRUST_LABEL
    assert not hasattr(binding, "resolve_trust")


def test_binding_can_include_escape_detection_evidence() -> None:
    source = _source_identity()
    evidence = build_source_evidence_ref(
        EvidenceBindingKind.ESCAPE_DETECTION_RESULT,
        source,
        metadata={"escape_result_hash": "fixture-escape-hash"},
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    binding = _binding(evidence_refs=(evidence,))

    assert (
        binding.evidence_refs[0].evidence_kind
        is EvidenceBindingKind.ESCAPE_DETECTION_RESULT
    )
    assert not hasattr(binding, "block")


def test_binding_can_include_untrusted_boundary_evidence() -> None:
    source = _source_identity()
    boundary = _boundary()
    evidence = build_source_evidence_ref(
        EvidenceBindingKind.UNTRUSTED_BOUNDARY_DECLARATION,
        source,
        metadata={"boundary_ref_id": boundary.boundary_id},
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    binding = _binding(evidence_refs=(evidence,))

    assert (
        binding.evidence_refs[0].evidence_kind
        is EvidenceBindingKind.UNTRUSTED_BOUNDARY_DECLARATION
    )
    assert not hasattr(binding, "filter")


def test_claim_ref_does_not_assert_truth() -> None:
    claim = build_source_claim_ref(
        SourceClaimKind.INSTRUCTION_CLAIM,
        _source_identity(),
        "fixture instruction claim",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    forbidden_fields = {
        "is_true",
        "verified_true",
        "accept",
        "reject",
        "execute",
        "verified",
    }
    assert not forbidden_fields & set(claim.to_canonical_dict().keys())
    assert claim.claim_kind is SourceClaimKind.INSTRUCTION_CLAIM


def test_evidence_confidence_does_not_assert_truth() -> None:
    evidence = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_IDENTITY,
        _source_identity(),
        confidence=EvidenceConfidence.HIGH,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert evidence.confidence is EvidenceConfidence.HIGH
    assert not hasattr(EvidenceConfidence.HIGH, "is_true")
    assert not hasattr(evidence, "resolve")


def test_provenance_ref_does_not_write_trace() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
    ))
    assert "trace" not in source.lower() or "does not" in source
    assert "emit_trace" not in source
    assert "trace_writer" not in source
    build_source_provenance_ref(
        SourceProvenanceKind.DERIVED_SOURCE,
        _source_identity(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def test_binding_does_not_write_ledger() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
    ))
    forbidden_snippets = ("write_ledger", "ledger_writer", "from agentic_runtime.ledger")
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_resolver_api_exists() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
    ))
    for name in (
        "resolve_trust",
        "resolve_path",
        "resolve_provenance",
        "classify_risk",
        "authorize",
    ):
        assert f"def {name}" not in source


def test_no_allow_deny_block_enforce_api_exists() -> None:
    import agentic_runtime.path_governance as pg

    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
    ))
    for name in ("allow", "deny", "block", "enforce", "can_command"):
        assert name not in pg.__all__
        assert f"def {name}" not in source

    for cls in (
        SourceEvidenceRef,
        SourceClaimRef,
        SourceProvenanceRef,
        ProvenanceBinding,
        ProvenanceBindingRegistry,
    ):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _FORBIDDEN_METHOD_NAMES & methods


def test_no_memory_write_occurs() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
    ))
    forbidden_snippets = (
        "write_memory",
        "canonize_memory",
        "memory_writer",
        "from agentic_runtime.memory",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
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


def test_no_runtime_sandbox_approval_imports() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_provenance",
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


def test_hashes_are_deterministic() -> None:
    source = _source_identity()
    claim = build_source_claim_ref(
        SourceClaimKind.FACTUAL_CLAIM,
        source,
        "fixture claim",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    binding = _binding(claim_refs=(claim,))
    registry = build_provenance_binding_registry(
        bindings=(binding,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    binding_repeat = _binding(claim_refs=(claim,))
    registry_repeat = build_provenance_binding_registry(
        bindings=(binding_repeat,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert binding.binding_hash == binding_repeat.binding_hash
    assert registry.registry_hash == registry_repeat.registry_hash


def test_changed_claim_changes_binding_hash() -> None:
    source = _source_identity()
    first_claim = build_source_claim_ref(
        SourceClaimKind.FACTUAL_CLAIM,
        source,
        "first claim summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second_claim = build_source_claim_ref(
        SourceClaimKind.INSTRUCTION_CLAIM,
        source,
        "second claim summary",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    first_binding = _binding(claim_refs=(first_claim,))
    second_binding = _binding(claim_refs=(second_claim,))

    assert first_binding.binding_hash != second_binding.binding_hash


def test_changed_evidence_changes_binding_hash() -> None:
    source = _source_identity()
    first_evidence = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_IDENTITY,
        source,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second_evidence = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_TRUST_LABEL,
        source,
        metadata={"trust_label": SourceTrustLabel.EXTERNAL.value},
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    first_binding = _binding(evidence_refs=(first_evidence,))
    second_binding = _binding(evidence_refs=(second_evidence,))

    assert first_binding.binding_hash != second_binding.binding_hash


def test_changed_source_changes_binding_hash() -> None:
    first_source = _source_identity(trust_label=SourceTrustLabel.EXTERNAL)
    second_source = _source_identity(trust_label=SourceTrustLabel.UNTRUSTED)

    first_binding = _binding(source_identity=first_source)
    second_binding = _binding(source_identity=second_source)

    assert first_binding.binding_hash != second_binding.binding_hash


def test_unknown_fields_are_rejected() -> None:
    evidence = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_IDENTITY,
        _source_identity(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    claim = build_source_claim_ref(
        SourceClaimKind.FACTUAL_CLAIM,
        _source_identity(),
        "fixture claim",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    provenance = build_source_provenance_ref(
        SourceProvenanceKind.DIRECT_SOURCE,
        _source_identity(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    binding = _binding(
        evidence_refs=(evidence,),
        claim_refs=(claim,),
        provenance_refs=(provenance,),
    )
    registry = build_provenance_binding_registry(
        bindings=(binding,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    evidence_payload = evidence.to_canonical_dict()
    evidence_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as evidence_error:
        SourceEvidenceRef.from_dict(evidence_payload)
    assert evidence_error.value.code.value == "UNKNOWN_FIELD"

    claim_payload = claim.to_canonical_dict()
    claim_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as claim_error:
        SourceClaimRef.from_dict(claim_payload)
    assert claim_error.value.code.value == "UNKNOWN_FIELD"

    provenance_payload = provenance.to_canonical_dict()
    provenance_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as provenance_error:
        SourceProvenanceRef.from_dict(provenance_payload)
    assert provenance_error.value.code.value == "UNKNOWN_FIELD"

    binding_payload = binding.to_canonical_dict()
    binding_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as binding_error:
        ProvenanceBinding.from_dict(binding_payload)
    assert binding_error.value.code.value == "UNKNOWN_FIELD"

    registry_payload = registry.to_canonical_dict()
    registry_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as registry_error:
        ProvenanceBindingRegistry.from_dict(registry_payload)
    assert registry_error.value.code.value == "UNKNOWN_FIELD"


def test_source_labels_are_preserved() -> None:
    live_evidence = build_source_evidence_ref(
        EvidenceBindingKind.SOURCE_IDENTITY,
        _source_identity(),
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_binding = _binding(source_label=ProjectionSourceLabel.DEV_FIXTURE)

    assert live_evidence.source_label is ProjectionSourceLabel.LIVE
    assert fixture_binding.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    source = _source_identity()
    binding = _binding(source_identity=source)

    assert source.source_ref.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert binding.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_p1_7_0_to_p1_7_7_regression_still_pass() -> None:
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
            "tests/path_governance/test_p1_7_7_untrusted_content_boundary.py",
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

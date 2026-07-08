"""P1.7.9 — Path/Source Risk Classification Model tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathGovernanceUnknownFieldError,
    PathKind,
    PathScopeAction,
    PathSourceRiskClassification,
    PathSourceRiskLevel,
    PathSourceRiskRegistry,
    PathSourceRiskSignal,
    PathSourceRiskSignalKind,
    ProjectionSourceLabel,
    RiskClassificationBasis,
    RiskClassificationPosture,
    SourceKind,
    SourceOrigin,
    SourceTrustLabel,
    UntrustedContentKind,
    build_path_authority_scope,
    build_path_identity,
    build_path_source_risk_classification,
    build_path_source_risk_registry,
    build_path_source_risk_signal,
    build_provenance_binding,
    build_source_identity,
    build_untrusted_content_boundary,
    derive_path_source_risk_classification,
    to_canonical_json,
)


_REQUIRED_RISK_LEVELS = {
    "NONE",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "UNKNOWN",
}

_REQUIRED_SIGNAL_KINDS = {
    "UNKNOWN_SOURCE",
    "UNTRUSTED_SOURCE",
    "QUARANTINED_SOURCE",
    "EXTERNAL_SOURCE",
    "TOOL_GENERATED_SOURCE",
    "MODEL_GENERATED_SOURCE",
    "PATH_TRAVERSAL_SIGNAL",
    "OUTSIDE_TRUSTED_ROOT_SIGNAL",
    "ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT",
    "AUTHORITY_EXPANSION_SURFACE",
    "PROMPT_INSTRUCTION_SURFACE",
    "TOOL_ARGUMENT_SURFACE",
    "MEMORY_WRITE_SURFACE",
    "POLICY_DEFINITION_SURFACE",
    "EXECUTION_REQUEST_SURFACE",
    "LOW_CONFIDENCE_EVIDENCE",
    "CONFLICTED_EVIDENCE",
    "UNVERIFIED_CLAIM",
    "MISSING_PROVENANCE",
    "UNKNOWN",
}

_REQUIRED_BASIS_VALUES = {
    "SOURCE_TRUST",
    "PATH_BOUNDARY",
    "TRUSTED_ROOT",
    "AUTHORITY_SCOPE",
    "UNTRUSTED_CONTENT_BOUNDARY",
    "PROVENANCE_EVIDENCE",
    "CLAIM_REFERENCE",
    "SYSTEM_DEFAULT",
    "TEST_FIXTURE",
    "UNKNOWN",
}

_REQUIRED_POSTURES = {
    "INFORMATIONAL",
    "REVIEW_RECOMMENDED",
    "REVIEW_REQUIRED_LATER",
    "RESTRICTED_LATER",
    "QUARANTINE_RECOMMENDED",
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
    "resolve_path_risk",
    "resolve_source_risk",
    "should_block",
    "is_allowed",
    "is_denied",
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


def _provenance_binding():
    source = _source_identity()
    return build_provenance_binding(
        source_identity=source,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _signal(
    *,
    signal_kind: PathSourceRiskSignalKind,
    basis: RiskClassificationBasis,
    risk_level: PathSourceRiskLevel,
    reason: str = "fixture risk signal",
):
    return build_path_source_risk_signal(
        signal_kind,
        basis,
        risk_level,
        reason,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _classification(**kwargs):
    defaults = {"source_label": ProjectionSourceLabel.DEV_FIXTURE}
    defaults.update(kwargs)
    return build_path_source_risk_classification(**defaults)


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathSourceRiskLevel",
        "PathSourceRiskSignalKind",
        "RiskClassificationBasis",
        "RiskClassificationPosture",
        "PathSourceRiskSignal",
        "PathSourceRiskClassification",
        "PathSourceRiskRegistry",
        "build_path_source_risk_signal",
        "build_path_source_risk_classification",
        "build_path_source_risk_registry",
        "derive_path_source_risk_classification",
    ):
        assert hasattr(pg, name)


def test_path_source_risk_level_has_required_values() -> None:
    assert {item.value for item in PathSourceRiskLevel} == _REQUIRED_RISK_LEVELS


def test_path_source_risk_signal_kind_has_required_values() -> None:
    assert {item.value for item in PathSourceRiskSignalKind} == _REQUIRED_SIGNAL_KINDS


def test_risk_classification_basis_has_required_values() -> None:
    assert {item.value for item in RiskClassificationBasis} == _REQUIRED_BASIS_VALUES


def test_risk_classification_posture_has_required_values() -> None:
    assert {item.value for item in RiskClassificationPosture} == _REQUIRED_POSTURES


def test_risk_signal_builds_deterministically() -> None:
    first = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    second = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )

    assert first.signal_id == second.signal_id
    assert to_canonical_json(first) == to_canonical_json(second)


def test_risk_classification_builds_deterministically() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    first = _classification(signals=(signal,))
    second = _classification(signals=(signal,))

    assert first.classification_id == second.classification_id
    assert first.classification_hash == second.classification_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_risk_registry_builds_deterministically() -> None:
    classification = _classification(
        signals=(
            _signal(
                signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
                basis=RiskClassificationBasis.SOURCE_TRUST,
                risk_level=PathSourceRiskLevel.MEDIUM,
            ),
        ),
    )
    first = build_path_source_risk_registry(
        classifications=(classification,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = build_path_source_risk_registry(
        classifications=(classification,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.registry_hash == second.registry_hash


def test_classification_can_reference_source_identity() -> None:
    source = _source_identity()
    classification = _classification(
        source_identity=source,
        signals=(
            _signal(
                signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
                basis=RiskClassificationBasis.SOURCE_TRUST,
                risk_level=PathSourceRiskLevel.MEDIUM,
            ),
        ),
    )

    assert classification.source_identity is not None
    assert classification.source_identity.identity_hash == source.identity_hash
    assert not hasattr(classification, "resolve_trust")


def test_classification_can_reference_path_identity_hash() -> None:
    path_identity = _path_identity()
    classification = _classification(path_identity_hash=path_identity.identity_hash)

    assert classification.path_identity_hash == path_identity.identity_hash


def test_classification_can_reference_boundary_ref_id() -> None:
    boundary = _boundary()
    classification = _classification(boundary_ref_id=boundary.boundary_id)

    assert classification.boundary_ref_id == boundary.boundary_id
    assert not hasattr(classification, "filter")
    assert not hasattr(classification, "block")


def test_classification_can_reference_authority_scope_id() -> None:
    scope = _scope()
    classification = _classification(authority_scope_id=scope.scope_id)

    assert classification.authority_scope_id == scope.scope_id
    assert not hasattr(classification, "authorize")
    assert not hasattr(classification, "allow")


def test_classification_can_reference_provenance_binding_id() -> None:
    binding = _provenance_binding()
    classification = _classification(provenance_binding_id=binding.binding_id)

    assert classification.provenance_binding_id == binding.binding_id


def test_external_untrusted_source_can_produce_risk_signal() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.UNTRUSTED_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    classification = _classification(signals=(signal,))

    assert classification.signals[0].signal_kind is PathSourceRiskSignalKind.UNTRUSTED_SOURCE
    assert not hasattr(classification, "deny")
    assert not hasattr(classification, "block")


def test_traversal_signal_can_produce_high_risk_classification() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.PATH_TRAVERSAL_SIGNAL,
        basis=RiskClassificationBasis.PATH_BOUNDARY,
        risk_level=PathSourceRiskLevel.HIGH,
    )
    classification = derive_path_source_risk_classification(
        signals=(signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.risk_level is PathSourceRiskLevel.HIGH
    assert not hasattr(classification, "enforce")


def test_outside_root_signal_can_produce_high_risk_classification() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.OUTSIDE_TRUSTED_ROOT_SIGNAL,
        basis=RiskClassificationBasis.PATH_BOUNDARY,
        risk_level=PathSourceRiskLevel.HIGH,
    )
    classification = derive_path_source_risk_classification(
        signals=(signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.risk_level is PathSourceRiskLevel.HIGH


def test_authority_expansion_surface_can_produce_critical_risk_classification() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.AUTHORITY_EXPANSION_SURFACE,
        basis=RiskClassificationBasis.UNTRUSTED_CONTENT_BOUNDARY,
        risk_level=PathSourceRiskLevel.CRITICAL,
    )
    classification = derive_path_source_risk_classification(
        signals=(signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.risk_level is PathSourceRiskLevel.CRITICAL
    assert not hasattr(classification, "resolve")


def test_memory_write_surface_can_produce_high_or_critical_classification() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.MEMORY_WRITE_SURFACE,
        basis=RiskClassificationBasis.UNTRUSTED_CONTENT_BOUNDARY,
        risk_level=PathSourceRiskLevel.HIGH,
    )
    classification = derive_path_source_risk_classification(
        signals=(signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.risk_level in {
        PathSourceRiskLevel.HIGH,
        PathSourceRiskLevel.CRITICAL,
    }
    assert not hasattr(classification, "write_memory")


def test_policy_definition_surface_can_produce_critical_classification() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.POLICY_DEFINITION_SURFACE,
        basis=RiskClassificationBasis.UNTRUSTED_CONTENT_BOUNDARY,
        risk_level=PathSourceRiskLevel.CRITICAL,
    )
    classification = derive_path_source_risk_classification(
        signals=(signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.risk_level is PathSourceRiskLevel.CRITICAL
    assert not hasattr(classification, "mutate_policy")


def test_execution_request_surface_can_produce_critical_classification() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXECUTION_REQUEST_SURFACE,
        basis=RiskClassificationBasis.UNTRUSTED_CONTENT_BOUNDARY,
        risk_level=PathSourceRiskLevel.CRITICAL,
    )
    classification = derive_path_source_risk_classification(
        signals=(signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.risk_level is PathSourceRiskLevel.CRITICAL
    assert not hasattr(classification, "execute")


def test_conflicted_evidence_can_produce_risk_signal() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.CONFLICTED_EVIDENCE,
        basis=RiskClassificationBasis.PROVENANCE_EVIDENCE,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    classification = _classification(signals=(signal,))

    assert classification.signals[0].signal_kind is PathSourceRiskSignalKind.CONFLICTED_EVIDENCE
    assert not hasattr(classification, "verify_truth")


def test_unverified_claim_can_produce_risk_signal() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.UNVERIFIED_CLAIM,
        basis=RiskClassificationBasis.CLAIM_REFERENCE,
        risk_level=PathSourceRiskLevel.LOW,
    )
    classification = _classification(signals=(signal,))

    assert classification.signals[0].signal_kind is PathSourceRiskSignalKind.UNVERIFIED_CLAIM
    assert not hasattr(classification, "accept")
    assert not hasattr(classification, "reject")


def test_missing_provenance_can_produce_risk_signal() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.MISSING_PROVENANCE,
        basis=RiskClassificationBasis.PROVENANCE_EVIDENCE,
        risk_level=PathSourceRiskLevel.UNKNOWN,
    )
    classification = _classification(signals=(signal,))

    assert classification.signals[0].signal_kind is PathSourceRiskSignalKind.MISSING_PROVENANCE
    assert not hasattr(classification, "lookup_graph")


def test_risk_level_does_not_expose_allow_deny_block() -> None:
    forbidden = {"allow", "deny", "block", "enforce", "authorize"}
    assert not forbidden & {item.name for item in PathSourceRiskLevel}
    classification = _classification(
        risk_level=PathSourceRiskLevel.CRITICAL,
        posture=RiskClassificationPosture.QUARANTINE_RECOMMENDED,
    )
    assert not forbidden & set(classification.to_canonical_dict().keys())


def test_posture_does_not_enforce() -> None:
    forbidden = {"enforce", "restrict", "quarantine", "apply", "block"}
    assert not forbidden & {item.name for item in RiskClassificationPosture}
    posture = RiskClassificationPosture.QUARANTINE_RECOMMENDED
    assert not hasattr(posture, "enforce")


def test_no_resolver_api_exists() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
    ))
    for name in (
        "resolve_path_risk",
        "resolve_source_risk",
        "authorize",
        "is_allowed",
        "is_denied",
        "should_block",
    ):
        assert f"def {name}" not in source


def test_no_policy_engine_call_exists() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
    ))
    forbidden_snippets = (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
        "evaluate_policy",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_approval_activation_exists() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
    ))
    forbidden_snippets = (
        "from agentic_runtime.approval",
        "approval_queue",
        "activate_approval",
        "request_approval",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_trace_or_ledger_write_exists() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
    ))
    forbidden_snippets = (
        "write_ledger",
        "ledger_writer",
        "from agentic_runtime.ledger",
        "trace_writer",
        "emit_trace",
        "from agentic_runtime.trace",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
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


def test_no_memory_or_tool_gating_occurs() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
    ))
    forbidden_snippets = (
        "write_memory",
        "canonize_memory",
        "memory_writer",
        "block_tool",
        "gate_tool",
        "from agentic_runtime.memory",
        "from agentic_runtime.tools",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def test_no_runtime_sandbox_approval_imports() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.risk_classification",
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
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    classification = _classification(signals=(signal,))
    registry = build_path_source_risk_registry(
        classifications=(classification,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    classification_repeat = _classification(signals=(signal,))
    registry_repeat = build_path_source_risk_registry(
        classifications=(classification_repeat,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert classification.classification_hash == classification_repeat.classification_hash
    assert registry.registry_hash == registry_repeat.registry_hash


def test_changed_signal_changes_classification_hash() -> None:
    first_signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
        reason="first signal reason",
    )
    second_signal = _signal(
        signal_kind=PathSourceRiskSignalKind.PATH_TRAVERSAL_SIGNAL,
        basis=RiskClassificationBasis.PATH_BOUNDARY,
        risk_level=PathSourceRiskLevel.HIGH,
        reason="second signal reason",
    )

    first = _classification(signals=(first_signal,))
    second = _classification(signals=(second_signal,))

    assert first.classification_hash != second.classification_hash


def test_changed_source_changes_classification_hash() -> None:
    first_source = _source_identity(trust_label=SourceTrustLabel.EXTERNAL)
    second_source = _source_identity(trust_label=SourceTrustLabel.UNTRUSTED)
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )

    first = _classification(source_identity=first_source, signals=(signal,))
    second = _classification(source_identity=second_source, signals=(signal,))

    assert first.classification_hash != second.classification_hash


def test_changed_boundary_or_authority_or_provenance_reference_changes_hash() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    base = _classification(signals=(signal,))
    with_boundary = _classification(
        signals=(signal,),
        boundary_ref_id=_boundary().boundary_id,
    )
    with_scope = _classification(
        signals=(signal,),
        authority_scope_id=_scope().scope_id,
    )
    with_binding = _classification(
        signals=(signal,),
        provenance_binding_id=_provenance_binding().binding_id,
    )

    assert base.classification_hash != with_boundary.classification_hash
    assert base.classification_hash != with_scope.classification_hash
    assert base.classification_hash != with_binding.classification_hash


def test_unknown_fields_are_rejected() -> None:
    signal = _signal(
        signal_kind=PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        basis=RiskClassificationBasis.SOURCE_TRUST,
        risk_level=PathSourceRiskLevel.MEDIUM,
    )
    classification = _classification(signals=(signal,))
    registry = build_path_source_risk_registry(
        classifications=(classification,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    signal_payload = signal.to_canonical_dict()
    signal_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as signal_error:
        PathSourceRiskSignal.from_dict(signal_payload)
    assert signal_error.value.code.value == "UNKNOWN_FIELD"

    classification_payload = classification.to_canonical_dict()
    classification_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as classification_error:
        PathSourceRiskClassification.from_dict(classification_payload)
    assert classification_error.value.code.value == "UNKNOWN_FIELD"

    registry_payload = registry.to_canonical_dict()
    registry_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as registry_error:
        PathSourceRiskRegistry.from_dict(registry_payload)
    assert registry_error.value.code.value == "UNKNOWN_FIELD"


def test_source_labels_are_preserved() -> None:
    live_signal = build_path_source_risk_signal(
        PathSourceRiskSignalKind.EXTERNAL_SOURCE,
        RiskClassificationBasis.SOURCE_TRUST,
        PathSourceRiskLevel.MEDIUM,
        "live fixture signal",
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_classification = _classification(
        signals=(live_signal,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert live_signal.source_label is ProjectionSourceLabel.LIVE
    assert fixture_classification.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    source = _source_identity()
    classification = _classification(source_identity=source)

    assert source.source_ref.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert classification.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_p1_7_0_to_p1_7_8_regression_still_pass() -> None:
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
            "tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py",
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

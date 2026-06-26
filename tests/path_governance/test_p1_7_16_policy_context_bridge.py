"""P1.7.16 — Policy Context Bridge tests."""
from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    ContentInfluenceSurface,
    EvidenceBindingKind,
    EvidenceConfidence,
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathBoundaryCheckResult,
    PathBoundaryStatus,
    PathGovernanceDecisionReason,
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
    PathGovernanceUnknownFieldError,
    PathKind,
    PathPolicyBridgeDisposition,
    PathPolicyBridgeMode,
    PathPolicyContextBridgeResult,
    PathPolicyContextInput,
    PathPolicyContextPacket,
    PathPolicyContextSubjectKind,
    PathPolicyDecisionSurface,
    PathPolicyRequirementKind,
    PathScopeAction,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    ProjectionSourceLabel,
    RiskClassificationBasis,
    SourceClaimKind,
    SourceKind,
    SourceOrigin,
    SourceTrustDecisionReason,
    SourceTrustLabel,
    SourceTrustResolverResult,
    SourceTrustShadowDecision,
    UntrustedBoundaryPosture,
    UntrustedContentKind,
    bridge_path_governance_to_policy_context,
    build_default_path_governance_harness_suite,
    build_path_authority_scope,
    build_path_governance_harness_scenario,
    build_path_identity,
    build_path_policy_context_packet,
    build_path_policy_context_subject_ref,
    build_path_resolution_trace_payload,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
    build_path_violation_trace_payload,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
    build_source_identity,
    build_trusted_root_registry,
    build_untrusted_content_boundary,
    derive_path_policy_requirements,
    resolve_path_source_conflicts_shadow,
    run_path_governance_harness_suite,
)

_REQUIRED_SUBJECT_KINDS = {
    "PATH_IDENTITY",
    "SOURCE_IDENTITY",
    "SOURCE_TRUST_LABEL",
    "TRUSTED_ROOT_SCOPE",
    "PATH_BOUNDARY_RESULT",
    "AUTHORITY_SCOPE",
    "UNTRUSTED_CONTENT_BOUNDARY",
    "PROVENANCE_BINDING",
    "RISK_CLASSIFICATION",
    "PATH_RESOLVER_RESULT",
    "SOURCE_TRUST_RESULT",
    "CONFLICT_PRECEDENCE_RESULT",
    "PATH_RESOLUTION_TRACE_PAYLOAD",
    "VIOLATION_DRIFT_TRACE_PAYLOAD",
    "HARNESS_RESULT",
    "UNKNOWN",
}

_REQUIRED_DECISION_SURFACES = {
    "MEMORY_WRITE",
    "TOOL_INVOCATION",
    "PROMPT_ASSEMBLY",
    "FILE_ACCESS",
    "COMMAND_EXECUTION",
    "MODEL_ROUTING",
    "OUTPUT_PROVENANCE",
    "AGENT_DELEGATION",
    "WORKFLOW_EXECUTION",
    "SOURCE_TRUST_UPDATE",
    "UNKNOWN",
}

_REQUIRED_REQUIREMENTS = {
    "REQUIRES_POLICY_REVIEW",
    "REQUIRES_OPERATOR_REVIEW",
    "REQUIRES_SOURCE_TRUST_REVIEW",
    "REQUIRES_PROVENANCE_REVIEW",
    "REQUIRES_AUTHORITY_REVIEW",
    "REQUIRES_TRACE_BINDING",
    "REQUIRES_CONFLICT_REVIEW",
    "REQUIRES_RISK_REVIEW",
    "WOULD_REQUIRE_RUNTIME_POLICY_LATER",
    "UNKNOWN",
}

_REQUIRED_BRIDGE_MODES = {
    "CONTEXT_ONLY",
    "SIMULATION_CONTEXT",
    "POLICY_RUNTIME_UNAVAILABLE",
    "ERROR",
    "UNKNOWN",
}

_REQUIRED_DISPOSITIONS = {
    "CONTEXT_CREATED",
    "WOULD_SUBMIT_TO_POLICY_LATER",
    "POLICY_RUNTIME_UNAVAILABLE",
    "SKIPPED",
    "ERROR",
    "UNKNOWN",
}

_FORBIDDEN_SUMMARY_TOKENS = {
    "ALLOW",
    "DENY",
    "BLOCK",
    "APPROVE",
    "ENFORCE",
    "AUTHORIZED",
    "QUARANTINED",
}

_P1_7_REGRESSION_FILES = (
    "tests/path_governance/test_p1_7_0_foundation.py",
    "tests/path_governance/test_p1_7_1_path_identity.py",
    "tests/path_governance/test_p1_7_2_source_identity.py",
    "tests/path_governance/test_p1_7_3_source_trust_taxonomy.py",
    "tests/path_governance/test_p1_7_4_trusted_roots.py",
    "tests/path_governance/test_p1_7_5_path_normalization_escape_contract.py",
    "tests/path_governance/test_p1_7_6_path_authority_scope.py",
    "tests/path_governance/test_p1_7_7_untrusted_content_boundary.py",
    "tests/path_governance/test_p1_7_8_source_provenance_evidence_binding.py",
    "tests/path_governance/test_p1_7_9_path_source_risk_classification.py",
    "tests/path_governance/test_p1_7_10_path_governance_resolver_shadow.py",
    "tests/path_governance/test_p1_7_11_source_trust_resolver_shadow.py",
    "tests/path_governance/test_p1_7_12_conflict_precedence.py",
    "tests/path_governance/test_p1_7_13_path_resolution_trace_hook.py",
    "tests/path_governance/test_p1_7_14_path_violation_drift_trace_hook.py",
    "tests/path_governance/test_p1_7_15_path_governance_test_harness.py",
)

_FIXTURE_LABEL = ProjectionSourceLabel.DEV_FIXTURE
_FIXTURE_META = {"fixture": "DEV_FIXTURE"}


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.policy_context_bridge"),
    )


def _source_identity(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.TRUSTED,
) -> object:
    return build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        uri_or_path=f"DEV_FIXTURE:source/{trust_label.value}",
        source_label=_FIXTURE_LABEL,
        trust_label=trust_label,
        metadata=_FIXTURE_META,
    )


def _path_identity(raw_path: str = "src/example.py") -> object:
    return build_path_identity(
        raw_path,
        path_kind=PathKind.REPO_RELATIVE,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _trusted_roots() -> object:
    return build_trusted_root_registry(source_label=_FIXTURE_LABEL)


def _boundary_result() -> PathBoundaryCheckResult:
    return PathBoundaryCheckResult(
        normalized_path="src/example.py",
        boundary_status=PathBoundaryStatus.PATH_OK,
        path_identity=_path_identity(),
        trusted_root_id="DEV_FIXTURE:root",
        trusted_root_normalized_path="src",
        reason="DEV_FIXTURE boundary context",
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _authority_scope() -> object:
    return build_path_authority_scope(
        subject=PathAuthoritySubject(
            subject_kind=PathAuthoritySubjectKind.OPERATOR,
            display_name="DEV_FIXTURE",
            source_label=_FIXTURE_LABEL,
        ),
        actions=(PathScopeAction.READ,),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _untrusted_boundary() -> object:
    return build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
        trust_label=SourceTrustLabel.UNTRUSTED,
        posture=UntrustedBoundaryPosture.REVIEW_REQUIRED,
        influence_surfaces=(ContentInfluenceSurface.PROMPT_INSTRUCTION,),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _provenance_binding() -> object:
    source_identity = _source_identity(trust_label=SourceTrustLabel.TRUSTED)
    return build_provenance_binding(
        source_identity=source_identity,
        evidence_refs=(
            build_source_evidence_ref(
                EvidenceBindingKind.SOURCE_TRUST_LABEL,
                source_identity,
                confidence=EvidenceConfidence.HIGH,
                source_label=_FIXTURE_LABEL,
                metadata=_FIXTURE_META,
            ),
        ),
        claim_refs=(
            build_source_claim_ref(
                SourceClaimKind.FACTUAL_CLAIM,
                source_identity,
                "DEV_FIXTURE claim",
                confidence=EvidenceConfidence.HIGH,
                source_label=_FIXTURE_LABEL,
                metadata=_FIXTURE_META,
            ),
        ),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _risk(
    risk_level: PathSourceRiskLevel,
    *,
    signals: tuple[object, ...] | None = None,
) -> object:
    if signals is None:
        signals = (
            build_path_source_risk_signal(
                PathSourceRiskSignalKind.UNKNOWN_SOURCE,
                RiskClassificationBasis.SOURCE_TRUST,
                risk_level,
                "DEV_FIXTURE risk",
                source_label=_FIXTURE_LABEL,
                metadata=_FIXTURE_META,
            ),
        )
    return build_path_source_risk_classification(
        signals=signals,
        risk_level=risk_level,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _path_result(
    decision: PathGovernanceShadowDecision = PathGovernanceShadowDecision.WOULD_ALLOW,
) -> PathGovernanceResolverResult:
    return PathGovernanceResolverResult(
        input_id="DEV_FIXTURE:path-input",
        shadow_decision=decision,
        decision_reasons=(PathGovernanceDecisionReason.SHADOW_MODE_ONLY,),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _source_result(
    decision: SourceTrustShadowDecision = SourceTrustShadowDecision.WOULD_REVIEW,
) -> SourceTrustResolverResult:
    return SourceTrustResolverResult(
        input_id="DEV_FIXTURE:source-input",
        shadow_decision=decision,
        decision_reasons=(SourceTrustDecisionReason.SHADOW_MODE_ONLY,),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _conflict_result() -> object:
    return resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=_FIXTURE_LABEL,
    )


def _resolution_trace_payload() -> object:
    return build_path_resolution_trace_payload(
        path_resolver_result=_path_result(),
        source_trust_resolver_result=_source_result(),
        conflict_precedence_result=_conflict_result(),
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        provenance_binding=_provenance_binding(),
        authority_scope=_authority_scope(),
        untrusted_boundary=_untrusted_boundary(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _violation_trace_payload() -> object:
    trace = _resolution_trace_payload()
    return build_path_violation_trace_payload(
        expected_path_resolver_result=_path_result(),
        current_path_resolver_result=_path_result(),
        expected_source_trust_result=_source_result(),
        current_source_trust_result=_source_result(),
        expected_conflict_precedence_result=_conflict_result(),
        current_conflict_precedence_result=_conflict_result(),
        expected_trace_payload=trace,
        current_trace_payload=trace,
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        provenance_binding=_provenance_binding(),
        authority_scope=_authority_scope(),
        untrusted_boundary=_untrusted_boundary(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _harness_result() -> object:
    suite = build_default_path_governance_harness_suite()
    return run_path_governance_harness_suite(
        scenarios=suite,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _full_packet(**overrides) -> PathPolicyContextPacket:
    base = {
        "path_identity": _path_identity(),
        "source_identity": _source_identity(),
        "source_trust_label": SourceTrustLabel.TRUSTED,
        "trusted_root_registry": _trusted_roots(),
        "path_boundary_result": _boundary_result(),
        "authority_scope": _authority_scope(),
        "untrusted_boundary": _untrusted_boundary(),
        "provenance_binding": _provenance_binding(),
        "risk_classification": _risk(PathSourceRiskLevel.LOW),
        "path_resolver_result": _path_result(),
        "source_trust_result": _source_result(),
        "conflict_precedence_result": _conflict_result(),
        "path_resolution_trace_payload": _resolution_trace_payload(),
        "violation_drift_trace_payload": _violation_trace_payload(),
        "harness_result": _harness_result(),
        "decision_surfaces": (
            PathPolicyDecisionSurface.FILE_ACCESS,
            PathPolicyDecisionSurface.TOOL_INVOCATION,
        ),
        "source_label": _FIXTURE_LABEL,
        "metadata": _FIXTURE_META,
    }
    base.update(overrides)
    return build_path_policy_context_packet(**base)


def _subject_kinds(packet: PathPolicyContextPacket) -> set[str]:
    return {item.subject_kind.value for item in packet.subjects}


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathPolicyContextSubjectKind",
        "PathPolicyDecisionSurface",
        "PathPolicyRequirementKind",
        "PathPolicyBridgeMode",
        "PathPolicyBridgeDisposition",
        "PathPolicyContextInput",
        "PathPolicyContextSubjectRef",
        "PathPolicyContextPacket",
        "PathPolicyContextBridgeResult",
        "build_path_policy_context_subject_ref",
        "derive_path_policy_requirements",
        "build_path_policy_context_packet",
        "bridge_path_governance_to_policy_context",
    ):
        assert hasattr(pg, name)


def test_subject_kind_has_required_values() -> None:
    assert {item.value for item in PathPolicyContextSubjectKind} == _REQUIRED_SUBJECT_KINDS


def test_decision_surface_has_required_values() -> None:
    assert {item.value for item in PathPolicyDecisionSurface} == _REQUIRED_DECISION_SURFACES


def test_requirement_kind_has_required_values() -> None:
    assert {item.value for item in PathPolicyRequirementKind} == _REQUIRED_REQUIREMENTS


def test_bridge_mode_has_required_values() -> None:
    assert {item.value for item in PathPolicyBridgeMode} == _REQUIRED_BRIDGE_MODES


def test_bridge_disposition_has_required_values() -> None:
    assert {item.value for item in PathPolicyBridgeDisposition} == _REQUIRED_DISPOSITIONS


def test_policy_context_input_builds_deterministically() -> None:
    first = PathPolicyContextInput(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    second = PathPolicyContextInput(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert first.input_id == second.input_id
    assert first.input_hash == second.input_hash


def test_subject_ref_builds_deterministically() -> None:
    first = build_path_policy_context_subject_ref(
        PathPolicyContextSubjectKind.PATH_IDENTITY,
        subject=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    second = build_path_policy_context_subject_ref(
        PathPolicyContextSubjectKind.PATH_IDENTITY,
        subject=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert first.subject_ref_id == second.subject_ref_id


def test_policy_context_packet_builds_deterministically() -> None:
    first = _full_packet()
    second = _full_packet()
    assert first.packet_id == second.packet_id
    assert first.packet_hash == second.packet_hash


def test_bridge_result_builds_deterministically() -> None:
    first = bridge_path_governance_to_policy_context(
        context_packet=_full_packet(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    second = bridge_path_governance_to_policy_context(
        context_packet=_full_packet(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert first.bridge_id == second.bridge_id
    assert first.bridge_hash == second.bridge_hash


def test_packet_can_reference_path_identity() -> None:
    packet = build_path_policy_context_packet(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.PATH_IDENTITY.value in _subject_kinds(packet)


def test_packet_can_reference_source_identity() -> None:
    packet = build_path_policy_context_packet(
        source_identity=_source_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.SOURCE_IDENTITY.value in _subject_kinds(packet)


def test_packet_can_reference_source_trust_label() -> None:
    before = SourceTrustLabel.UNTRUSTED
    packet = build_path_policy_context_packet(
        source_trust_label=before,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.SOURCE_TRUST_LABEL.value in _subject_kinds(packet)
    assert before is SourceTrustLabel.UNTRUSTED


def test_packet_can_reference_trusted_root_scope() -> None:
    packet = build_path_policy_context_packet(
        trusted_root_registry=_trusted_roots(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.TRUSTED_ROOT_SCOPE.value in _subject_kinds(packet)


def test_packet_can_reference_path_boundary_result() -> None:
    packet = build_path_policy_context_packet(
        path_boundary_result=_boundary_result(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.PATH_BOUNDARY_RESULT.value in _subject_kinds(packet)


def test_packet_can_reference_authority_scope() -> None:
    packet = build_path_policy_context_packet(
        authority_scope=_authority_scope(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.AUTHORITY_SCOPE.value in _subject_kinds(packet)


def test_packet_can_reference_untrusted_boundary() -> None:
    packet = build_path_policy_context_packet(
        untrusted_boundary=_untrusted_boundary(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.UNTRUSTED_CONTENT_BOUNDARY.value in _subject_kinds(packet)


def test_packet_can_reference_provenance_binding() -> None:
    packet = build_path_policy_context_packet(
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.PROVENANCE_BINDING.value in _subject_kinds(packet)


def test_packet_can_reference_risk_classification() -> None:
    packet = build_path_policy_context_packet(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.RISK_CLASSIFICATION.value in _subject_kinds(packet)


def test_packet_can_reference_path_resolver_result() -> None:
    packet = build_path_policy_context_packet(
        path_resolver_result=_path_result(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.PATH_RESOLVER_RESULT.value in _subject_kinds(packet)


def test_packet_can_reference_source_trust_result() -> None:
    packet = build_path_policy_context_packet(
        source_trust_result=_source_result(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.SOURCE_TRUST_RESULT.value in _subject_kinds(packet)


def test_packet_can_reference_conflict_precedence_result() -> None:
    packet = build_path_policy_context_packet(
        conflict_precedence_result=_conflict_result(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.CONFLICT_PRECEDENCE_RESULT.value in _subject_kinds(packet)


def test_packet_can_reference_trace_payload() -> None:
    packet = build_path_policy_context_packet(
        path_resolution_trace_payload=_resolution_trace_payload(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.PATH_RESOLUTION_TRACE_PAYLOAD.value in _subject_kinds(packet)


def test_packet_can_reference_violation_drift_payload() -> None:
    packet = build_path_policy_context_packet(
        violation_drift_trace_payload=_violation_trace_payload(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.VIOLATION_DRIFT_TRACE_PAYLOAD.value in _subject_kinds(packet)


def test_packet_can_reference_harness_result() -> None:
    packet = build_path_policy_context_packet(
        harness_result=_harness_result(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert PathPolicyContextSubjectKind.HARNESS_RESULT.value in _subject_kinds(packet)


def test_high_risk_derives_advisory_risk_operator_requirements() -> None:
    requirements = derive_path_policy_requirements(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        authority_scope=_authority_scope(),
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert PathPolicyRequirementKind.REQUIRES_RISK_REVIEW in requirements
    assert PathPolicyRequirementKind.REQUIRES_OPERATOR_REVIEW in requirements
    assert PathPolicyRequirementKind.WOULD_REQUIRE_RUNTIME_POLICY_LATER in requirements
    bridge = bridge_path_governance_to_policy_context(
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        authority_scope=_authority_scope(),
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert bridge.approval_created is False


def test_missing_provenance_derives_provenance_review_requirement() -> None:
    requirements = derive_path_policy_requirements(
        provenance_binding=None,
        authority_scope=_authority_scope(),
        source_label=_FIXTURE_LABEL,
    )
    assert PathPolicyRequirementKind.REQUIRES_PROVENANCE_REVIEW in requirements


def test_source_distrust_derives_source_trust_policy_review_requirement() -> None:
    before = _source_result(SourceTrustShadowDecision.WOULD_DISTRUST)
    requirements = derive_path_policy_requirements(
        source_trust_result=before,
        authority_scope=_authority_scope(),
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert PathPolicyRequirementKind.REQUIRES_SOURCE_TRUST_REVIEW in requirements
    assert PathPolicyRequirementKind.REQUIRES_POLICY_REVIEW in requirements
    assert before.shadow_decision is SourceTrustShadowDecision.WOULD_DISTRUST


def test_conflict_result_derives_conflict_review_requirement() -> None:
    requirements = derive_path_policy_requirements(
        conflict_precedence_result=_conflict_result(),
        authority_scope=_authority_scope(),
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert PathPolicyRequirementKind.REQUIRES_CONFLICT_REVIEW in requirements


def test_authority_missing_derives_authority_review_requirement() -> None:
    requirements = derive_path_policy_requirements(
        authority_scope=None,
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert PathPolicyRequirementKind.REQUIRES_AUTHORITY_REVIEW in requirements


def test_trace_payload_derives_trace_binding_requirement() -> None:
    requirements = derive_path_policy_requirements(
        path_resolution_trace_payload=_resolution_trace_payload(),
        authority_scope=_authority_scope(),
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert PathPolicyRequirementKind.REQUIRES_TRACE_BINDING in requirements
    bridge = bridge_path_governance_to_policy_context(
        path_resolution_trace_payload=_resolution_trace_payload(),
        authority_scope=_authority_scope(),
        provenance_binding=_provenance_binding(),
        source_label=_FIXTURE_LABEL,
    )
    assert bridge.ledger_written is False


def test_bridge_mode_defaults_to_context_only() -> None:
    bridge = bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    )
    assert bridge.bridge_mode is PathPolicyBridgeMode.CONTEXT_ONLY


def test_bridge_result_policy_called_false() -> None:
    assert bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    ).policy_called is False


def test_bridge_result_policy_decision_made_false() -> None:
    assert bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    ).policy_decision_made is False


def test_bridge_result_approval_created_false() -> None:
    assert bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    ).approval_created is False


def test_bridge_result_ledger_written_false() -> None:
    assert bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    ).ledger_written is False


def test_bridge_result_runtime_mutated_false() -> None:
    assert bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    ).runtime_mutated is False


def test_bridge_result_enforcement_triggered_false() -> None:
    assert bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    ).enforcement_triggered is False


def test_advisory_summary_contains_no_real_decision_words() -> None:
    packet = _full_packet()
    upper = packet.advisory_summary.upper()
    for token in _FORBIDDEN_SUMMARY_TOKENS:
        assert token not in upper.split()
        assert f" {token} " not in f" {upper} "


def test_packet_hash_changes_when_upstream_refs_change() -> None:
    first = build_path_policy_context_packet(
        path_identity=_path_identity("src/a.py"),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    second = build_path_policy_context_packet(
        path_identity=_path_identity("src/b.py"),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert first.packet_hash != second.packet_hash


def test_bridge_hash_changes_when_packet_or_mode_changes() -> None:
    packet = _full_packet()
    first = bridge_path_governance_to_policy_context(
        context_packet=packet,
        source_label=_FIXTURE_LABEL,
    )
    second = bridge_path_governance_to_policy_context(
        context_packet=packet,
        bridge_mode=PathPolicyBridgeMode.POLICY_RUNTIME_UNAVAILABLE,
        source_label=_FIXTURE_LABEL,
    )
    assert first.bridge_hash != second.bridge_hash


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc_info:
        PathPolicyContextInput.from_dict({
            "source_label": _FIXTURE_LABEL.value,
            "shadow_authority_grant": True,
        })
    assert "UNKNOWN_FIELD" in str(exc_info.value.code)


def test_source_labels_are_preserved() -> None:
    fixture_bridge = bridge_path_governance_to_policy_context(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
    )
    assert fixture_bridge.source_label is _FIXTURE_LABEL
    assert fixture_bridge.context_packet.source_label is _FIXTURE_LABEL


def test_no_fake_live_fixture_state() -> None:
    packet = build_path_policy_context_packet(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    assert packet.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_policy_engine_call_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
        "Custos",
    ):
        assert snippet not in source


def test_no_approval_activation_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.approval",
        "approval_queue",
        "activate_approval",
    ):
        assert snippet not in source


def test_no_ledger_write_exists() -> None:
    source = _module_source()
    for snippet in (
        "write_ledger",
        "ledger_writer",
        "from agentic_runtime.ledger",
    ):
        assert snippet not in source


def test_no_global_trace_write_exists() -> None:
    source = _module_source()
    for snippet in (
        "trace_writer",
        "emit_trace",
        "from agentic_runtime.trace",
    ):
        assert snippet not in source


def test_no_source_trust_mutation() -> None:
    source = _module_source()
    for snippet in (
        "mutate_source",
        "promote_source",
        "demote_source",
        "SourceTrustTaxonomy(",
    ):
        assert snippet not in source


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = _module_source()
    for snippet in (
        "def filter",
        "def rewrite",
        "def sanitize",
        "prompt_compiler",
        "prompt_assembly",
        "injection_firewall",
    ):
        assert snippet not in source


def test_no_memory_or_tool_gating_occurs() -> None:
    source = _module_source()
    for snippet in (
        "memory_writer",
        "write_memory",
        "block_tool",
        "tool_gate",
    ):
        assert snippet not in source


def test_no_runtime_sandbox_approval_imports() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.runtime",
        "AgenticRuntime",
        "from agentic_runtime.sandbox",
        "from agentic_runtime.approval",
        "from agentic_runtime.tools",
        "from agentic_runtime.cli",
        "from agentic_runtime.trace",
        "from agentic_runtime.ledger",
    ):
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = _module_source()
    for snippet in (
        "Path.exists",
        "Path.resolve",
        "Path.stat",
        "open(",
        "read_text",
        "read_bytes",
        "requests.",
        "urllib",
        "httpx",
    ):
        assert snippet not in source


def test_p1_7_0_to_p1_7_15_regression_still_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *_P1_7_REGRESSION_FILES, "-q"],
        cwd="/home/hrvojeb/Desktop/GG",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

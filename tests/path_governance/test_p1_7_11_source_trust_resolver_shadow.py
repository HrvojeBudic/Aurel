"""P1.7.11 — Source Trust Resolver v0 / Shadow Mode tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    ContentInfluenceSurface,
    EvidenceBindingKind,
    EvidenceConfidence,
    PathGovernanceResolverInput,
    PathGovernanceShadowDecision,
    PathGovernanceUnknownFieldError,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    ProjectionSourceLabel,
    RiskClassificationBasis,
    SourceClaimKind,
    SourceKind,
    SourceOrigin,
    SourceTrustDecisionReason,
    SourceTrustLabel,
    SourceTrustResolverInput,
    SourceTrustResolverResult,
    SourceTrustShadowDecision,
    UntrustedBoundaryPosture,
    UntrustedContentKind,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
    build_source_identity,
    build_source_trust_taxonomy,
    build_untrusted_content_boundary,
    resolve_path_governance_shadow,
    resolve_source_trust_shadow,
)


_REQUIRED_SHADOW_DECISIONS = {
    "WOULD_TRUST",
    "WOULD_REVIEW",
    "WOULD_DISTRUST",
    "WOULD_QUARANTINE",
    "WOULD_REQUIRE_OPERATOR_REVIEW",
    "WOULD_REQUIRE_POLICY_REVIEW",
    "UNKNOWN",
}

_REQUIRED_DECISION_REASONS = {
    "SOURCE_IDENTITY_PRESENT",
    "SOURCE_IDENTITY_MISSING",
    "SOURCE_LABEL_TRUSTED",
    "SOURCE_LABEL_UNTRUSTED",
    "SOURCE_LABEL_EXTERNAL",
    "SOURCE_LABEL_UNKNOWN",
    "SOURCE_LABEL_QUARANTINED",
    "BOUNDARY_INFORM_ONLY",
    "BOUNDARY_RESTRICTS_COMMAND",
    "PROVENANCE_PRESENT",
    "PROVENANCE_MISSING",
    "EVIDENCE_UNVERIFIED",
    "EVIDENCE_CONFLICTED",
    "RISK_CLASSIFICATION_LOW",
    "RISK_CLASSIFICATION_MEDIUM",
    "RISK_CLASSIFICATION_HIGH",
    "RISK_CLASSIFICATION_CRITICAL",
    "PATH_RESOLVER_WOULD_ALLOW",
    "PATH_RESOLVER_WOULD_REVIEW",
    "PATH_RESOLVER_WOULD_RESTRICT",
    "PATH_RESOLVER_WOULD_DENY",
    "POLICY_BRIDGE_UNAVAILABLE",
    "SHADOW_MODE_ONLY",
    "UNKNOWN",
}


def _source_identity(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.TRUSTED,
    source_kind: SourceKind = SourceKind.OPERATOR_INPUT,
    source_origin: SourceOrigin = SourceOrigin.OPERATOR,
):
    return build_source_identity(
        source_kind=source_kind,
        source_origin=source_origin,
        uri_or_path=f"DEV_FIXTURE:source/{trust_label.value}",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=trust_label,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _risk(
    risk_level: PathSourceRiskLevel,
    *,
    signals=(),
    trust_label: SourceTrustLabel | None = None,
    provenance_binding_id: str | None = None,
):
    return build_path_source_risk_classification(
        signals=signals,
        risk_level=risk_level,
        trust_label=trust_label,
        provenance_binding_id=provenance_binding_id,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _signal(
    signal_kind: PathSourceRiskSignalKind,
    basis: RiskClassificationBasis,
    risk_level: PathSourceRiskLevel,
):
    return build_path_source_risk_signal(
        signal_kind,
        basis,
        risk_level,
        "DEV_FIXTURE source trust resolver risk signal",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _provenance(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.TRUSTED,
    confidence: EvidenceConfidence = EvidenceConfidence.HIGH,
    conflicted: bool = False,
):
    source_identity = _source_identity(trust_label=trust_label)
    evidence_confidence = EvidenceConfidence.CONFLICTED if conflicted else confidence
    return build_provenance_binding(
        source_identity=source_identity,
        evidence_refs=(
            build_source_evidence_ref(
                EvidenceBindingKind.SOURCE_TRUST_LABEL,
                source_identity,
                confidence=evidence_confidence,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata={"fixture": "DEV_FIXTURE"},
            ),
        ),
        claim_refs=(
            build_source_claim_ref(
                SourceClaimKind.FACTUAL_CLAIM,
                source_identity,
                "DEV_FIXTURE trust claim",
                confidence=evidence_confidence,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata={"fixture": "DEV_FIXTURE"},
            ),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _boundary(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.UNTRUSTED,
    posture: UntrustedBoundaryPosture = UntrustedBoundaryPosture.REVIEW_REQUIRED,
):
    return build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_source_identity(
            trust_label=trust_label,
            source_kind=SourceKind.EXTERNAL_WEB,
            source_origin=SourceOrigin.EXTERNAL_NETWORK,
        ),
        trust_label=trust_label,
        posture=posture,
        influence_surfaces=(ContentInfluenceSurface.PROMPT_INSTRUCTION,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _source() -> str:
    return inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_trust_resolver",
    ))


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "SourceTrustShadowDecision",
        "SourceTrustDecisionReason",
        "SourceTrustResolverInput",
        "SourceTrustResolverResult",
        "resolve_source_trust_shadow",
    ):
        assert hasattr(pg, name)


def test_source_trust_shadow_decision_has_required_values() -> None:
    assert {item.value for item in SourceTrustShadowDecision} == (
        _REQUIRED_SHADOW_DECISIONS
    )


def test_source_trust_decision_reason_has_required_values() -> None:
    assert {item.value for item in SourceTrustDecisionReason} == (
        _REQUIRED_DECISION_REASONS
    )


def test_resolver_input_builds_deterministically() -> None:
    kwargs = {
        "source_identity": _source_identity(),
        "source_trust_label": SourceTrustLabel.TRUSTED,
        "source_trust_taxonomy": build_source_trust_taxonomy(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        "untrusted_boundary": _boundary(trust_label=SourceTrustLabel.EXTERNAL),
        "provenance_binding": _provenance(),
        "risk_classification": _risk(PathSourceRiskLevel.LOW),
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    first = SourceTrustResolverInput(**kwargs)
    second = SourceTrustResolverInput(**kwargs)

    assert first.input_id == second.input_id
    assert first.input_hash == second.input_hash


def test_resolver_result_builds_deterministically() -> None:
    first = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        provenance_binding=_provenance(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )
    second = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        provenance_binding=_provenance(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )

    assert first.result_id == second.result_id
    assert first.result_hash == second.result_hash


def test_resolver_result_is_shadow_only() -> None:
    result = resolve_source_trust_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_only is True


def test_resolver_result_is_never_enforced() -> None:
    result = resolve_source_trust_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.enforced is False


def test_trusted_source_low_risk_with_provenance_can_produce_would_trust() -> None:
    source_identity = _source_identity(trust_label=SourceTrustLabel.TRUSTED)
    before = source_identity.source_ref.trust_label
    result = resolve_source_trust_shadow(
        source_identity=source_identity,
        provenance_binding=_provenance(trust_label=SourceTrustLabel.TRUSTED),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision is SourceTrustShadowDecision.WOULD_TRUST
    assert result.recommended_trust_label is SourceTrustLabel.TRUSTED
    assert source_identity.source_ref.trust_label is before


def test_external_source_can_produce_would_review_or_distrust() -> None:
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(
            trust_label=SourceTrustLabel.EXTERNAL,
            source_kind=SourceKind.EXTERNAL_WEB,
            source_origin=SourceOrigin.EXTERNAL_NETWORK,
        ),
        source_trust_label=SourceTrustLabel.EXTERNAL,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision in {
        SourceTrustShadowDecision.WOULD_REVIEW,
        SourceTrustShadowDecision.WOULD_DISTRUST,
    }
    assert not hasattr(result, "block_source")


def test_untrusted_source_can_produce_would_distrust_or_review() -> None:
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
        source_trust_label=SourceTrustLabel.UNTRUSTED,
        untrusted_boundary=_boundary(trust_label=SourceTrustLabel.UNTRUSTED),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision in {
        SourceTrustShadowDecision.WOULD_DISTRUST,
        SourceTrustShadowDecision.WOULD_REVIEW,
    }
    assert SourceTrustDecisionReason.SOURCE_LABEL_UNTRUSTED in (
        result.decision_reasons
    )


def test_quarantined_source_can_produce_would_quarantine() -> None:
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(trust_label=SourceTrustLabel.QUARANTINED),
        source_trust_label=SourceTrustLabel.QUARANTINED,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision is SourceTrustShadowDecision.WOULD_QUARANTINE
    assert result.enforced is False
    assert not hasattr(result, "delete_source")


def test_critical_risk_can_produce_would_distrust_or_quarantine() -> None:
    distrust = resolve_source_trust_shadow(
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    quarantine = resolve_source_trust_shadow(
        source_trust_label=SourceTrustLabel.QUARANTINED,
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert distrust.shadow_decision is SourceTrustShadowDecision.WOULD_DISTRUST
    assert quarantine.shadow_decision is SourceTrustShadowDecision.WOULD_QUARANTINE
    assert distrust.enforced is False
    assert quarantine.enforced is False


def test_high_risk_can_require_operator_review_or_distrust() -> None:
    result = resolve_source_trust_shadow(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision in {
        SourceTrustShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW,
        SourceTrustShadowDecision.WOULD_DISTRUST,
    }
    assert not hasattr(result, "activate_approval")


def test_medium_risk_can_produce_would_review() -> None:
    result = resolve_source_trust_shadow(
        risk_classification=_risk(PathSourceRiskLevel.MEDIUM),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision is SourceTrustShadowDecision.WOULD_REVIEW


def test_missing_provenance_produces_reason() -> None:
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert SourceTrustDecisionReason.PROVENANCE_MISSING in result.decision_reasons
    assert "write_ledger" not in _source()


def test_unverified_evidence_produces_reason() -> None:
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        provenance_binding=_provenance(confidence=EvidenceConfidence.UNVERIFIED),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert SourceTrustDecisionReason.EVIDENCE_UNVERIFIED in result.decision_reasons
    assert result.shadow_decision is SourceTrustShadowDecision.WOULD_REVIEW


def test_conflicted_evidence_produces_policy_review_reason() -> None:
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        provenance_binding=_provenance(conflicted=True),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert SourceTrustDecisionReason.EVIDENCE_CONFLICTED in result.decision_reasons
    assert SourceTrustDecisionReason.POLICY_BRIDGE_UNAVAILABLE in (
        result.decision_reasons
    )
    assert result.shadow_decision is (
        SourceTrustShadowDecision.WOULD_REQUIRE_POLICY_REVIEW
    )
    assert "PolicyEngine" not in _source()


def test_path_resolver_would_deny_influences_shadow_reason() -> None:
    path_result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        path_resolver_result=path_result,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert SourceTrustDecisionReason.PATH_RESOLVER_WOULD_DENY in (
        result.decision_reasons
    )
    assert result.shadow_decision is SourceTrustShadowDecision.WOULD_DISTRUST


def test_path_resolver_would_restrict_influences_shadow_reason() -> None:
    path_input = PathGovernanceResolverInput(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    path_result = resolve_path_governance_shadow(
        path_input,
    )
    path_result = type(path_result)(
        input_id=path_result.input_id,
        shadow_decision=PathGovernanceShadowDecision.WOULD_RESTRICT,
        decision_reasons=path_result.decision_reasons,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    result = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        path_resolver_result=path_result,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert SourceTrustDecisionReason.PATH_RESOLVER_WOULD_RESTRICT in (
        result.decision_reasons
    )
    assert result.enforced is False


def test_recommended_trust_label_is_advisory_only() -> None:
    taxonomy = build_source_trust_taxonomy(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    source_identity = _source_identity(trust_label=SourceTrustLabel.EXTERNAL)
    original_hash = taxonomy.taxonomy_hash
    original_label = source_identity.source_ref.trust_label
    result = resolve_source_trust_shadow(
        source_identity=source_identity,
        source_trust_taxonomy=taxonomy,
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.recommended_trust_label is SourceTrustLabel.UNTRUSTED
    assert taxonomy.taxonomy_hash == original_hash
    assert source_identity.source_ref.trust_label is original_label
    assert not hasattr(result, "mutate_trust_label")


def test_shadow_mode_reason_always_present() -> None:
    for risk_level in PathSourceRiskLevel:
        result = resolve_source_trust_shadow(
            risk_classification=_risk(risk_level),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        )
        assert SourceTrustDecisionReason.SHADOW_MODE_ONLY in result.decision_reasons


def test_result_hash_is_deterministic() -> None:
    first = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        provenance_binding=_provenance(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = resolve_source_trust_shadow(
        source_identity=_source_identity(),
        provenance_binding=_provenance(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.result_hash == second.result_hash


def test_changed_source_changes_result_hash() -> None:
    base = resolve_source_trust_shadow(
        source_identity=_source_identity(trust_label=SourceTrustLabel.TRUSTED),
        provenance_binding=_provenance(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_identity = resolve_source_trust_shadow(
        source_identity=_source_identity(trust_label=SourceTrustLabel.INTERNAL_REPO),
        provenance_binding=_provenance(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_label = resolve_source_trust_shadow(
        source_identity=_source_identity(trust_label=SourceTrustLabel.TRUSTED),
        source_trust_label=SourceTrustLabel.EXTERNAL,
        provenance_binding=_provenance(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert base.result_hash != changed_identity.result_hash
    assert base.result_hash != changed_label.result_hash


def test_changed_risk_changes_result_hash() -> None:
    low = resolve_source_trust_shadow(
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    high = resolve_source_trust_shadow(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert low.result_hash != high.result_hash


def test_changed_provenance_changes_result_hash() -> None:
    high_confidence = resolve_source_trust_shadow(
        provenance_binding=_provenance(confidence=EvidenceConfidence.HIGH),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    low_confidence = resolve_source_trust_shadow(
        provenance_binding=_provenance(confidence=EvidenceConfidence.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert high_confidence.result_hash != low_confidence.result_hash


def test_changed_path_resolver_result_changes_result_hash() -> None:
    allowed_path = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.NONE),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    denied_path = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    allowed = resolve_source_trust_shadow(
        path_resolver_result=allowed_path,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    denied = resolve_source_trust_shadow(
        path_resolver_result=denied_path,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert allowed.result_hash != denied.result_hash


def test_changed_boundary_changes_result_hash() -> None:
    base = resolve_source_trust_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    with_boundary = resolve_source_trust_shadow(
        untrusted_boundary=_boundary(trust_label=SourceTrustLabel.UNTRUSTED),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert base.result_hash != with_boundary.result_hash


def test_unknown_fields_are_rejected() -> None:
    resolver_input = SourceTrustResolverInput(
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    result = resolve_source_trust_shadow(resolver_input)

    input_payload = resolver_input.to_canonical_dict()
    input_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as input_error:
        SourceTrustResolverInput.from_dict(input_payload)
    assert input_error.value.code.value == "UNKNOWN_FIELD"

    result_payload = result.to_canonical_dict()
    result_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as result_error:
        SourceTrustResolverResult.from_dict(result_payload)
    assert result_error.value.code.value == "UNKNOWN_FIELD"


def test_source_labels_are_preserved() -> None:
    live_input = SourceTrustResolverInput(source_label=ProjectionSourceLabel.LIVE)
    fixture_result = resolve_source_trust_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert live_input.source_label is ProjectionSourceLabel.LIVE
    assert fixture_result.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    resolver_input = SourceTrustResolverInput(
        source_identity=_source_identity(),
        provenance_binding=_provenance(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )

    assert resolver_input.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert resolver_input.source_identity is not None
    assert resolver_input.source_identity.source_ref.source_label is (
        ProjectionSourceLabel.DEV_FIXTURE
    )
    assert resolver_input.provenance_binding is not None
    assert resolver_input.provenance_binding.source_label is (
        ProjectionSourceLabel.DEV_FIXTURE
    )


def test_no_real_trust_distrust_block_quarantine_api_exists() -> None:
    pg = importlib.import_module(
        "agentic_runtime.path_governance.source_trust_resolver",
    )
    forbidden_exports = {
        "trust_source",
        "distrust_source",
        "block_source",
        "quarantine_source",
        "enforce",
        "authorize",
        "can_command",
        "can_write_memory",
        "can_use_as_tool_argument",
    }
    assert not forbidden_exports & {name.lower() for name in dir(pg)}
    forbidden_values = {"TRUST", "DISTRUST", "BLOCK", "QUARANTINE_NOW"}
    assert not forbidden_values & {item.value for item in SourceTrustShadowDecision}
    for item in SourceTrustShadowDecision:
        assert item.value.startswith("WOULD_") or item.value == "UNKNOWN"


def test_would_vocabulary_does_not_mutate() -> None:
    result = SourceTrustResolverResult(
        input_id=SourceTrustResolverInput(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ).input_id,
        shadow_decision=SourceTrustShadowDecision.WOULD_DISTRUST,
        decision_reasons=(SourceTrustDecisionReason.SHADOW_MODE_ONLY,),
        recommended_trust_label=SourceTrustLabel.UNTRUSTED,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    for name in (
        "trust_source",
        "distrust_source",
        "block_source",
        "quarantine_source",
        "promote",
        "demote",
        "enforce",
        "authorize",
    ):
        assert not hasattr(result, name)
    assert result.enforced is False


def test_no_source_taxonomy_mutation() -> None:
    source = _source()
    for snippet in (
        ".definitions.append",
        ".definitions[",
        "object.__setattr__(source_trust_taxonomy",
        "object.__setattr__(source_identity",
        "TrustLabelDefinition(",
    ):
        assert snippet not in source


def test_no_policy_engine_call_exists() -> None:
    source = _source()
    for snippet in (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
        "evaluate_policy",
    ):
        assert snippet not in source


def test_no_approval_activation_exists() -> None:
    source = _source()
    for snippet in (
        "from agentic_runtime.approval",
        "approval_queue",
        "activate_approval",
        "request_approval",
        "create_approval",
    ):
        assert snippet not in source


def test_no_trace_or_ledger_write_exists() -> None:
    source = _source()
    for snippet in (
        "write_ledger",
        "ledger_writer",
        "from agentic_runtime.ledger",
        "trace_writer",
        "emit_trace",
        "from agentic_runtime.trace",
    ):
        assert snippet not in source


def test_no_prompt_filtering_or_rewriting_occurs() -> None:
    source = _source()
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
    source = _source()
    for snippet in (
        "write_memory",
        "canonize_memory",
        "memory_writer",
        "block_tool",
        "gate_tool",
        "from agentic_runtime.memory",
        "from agentic_runtime.tools",
    ):
        assert snippet not in source


def test_no_runtime_sandbox_approval_imports() -> None:
    source = _source()
    assert "AgenticRuntime.submit" not in source
    for snippet in (
        "from agentic_runtime.runtime",
        "from agentic_runtime.sandbox",
        "from agentic_runtime.sandbox_policy",
        "from agentic_runtime.approval",
        "from agentic_runtime.tools",
        "from agentic_runtime.cli",
        "from agentic_runtime.prompts",
        "from agentic_runtime.memory",
    ):
        assert snippet not in source


def test_no_filesystem_or_network_access() -> None:
    source = _source()
    for snippet in (
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
    ):
        assert snippet not in source

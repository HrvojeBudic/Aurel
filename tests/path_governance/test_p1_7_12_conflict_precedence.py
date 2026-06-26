"""P1.7.12 — Path/Source Conflict & Precedence Rules tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    ConflictPrecedenceInput,
    ConflictPrecedencePosture,
    ConflictSeverity,
    ContentInfluenceSurface,
    EvidenceBindingKind,
    EvidenceConfidence,
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathGovernanceDecisionReason,
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
    PathGovernanceUnknownFieldError,
    PathScopeAction,
    PathSourceConflictKind,
    PathSourceConflictSignal,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    PrecedenceRule,
    PrecedenceRuleKind,
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
    build_path_authority_scope,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
    build_source_identity,
    build_untrusted_content_boundary,
    resolve_path_source_conflicts_shadow,
)


_REQUIRED_CONFLICT_KINDS = {
    "PATH_SOURCE_DECISION_MISMATCH",
    "PATH_WOULD_ALLOW_SOURCE_WOULD_DISTRUST",
    "PATH_WOULD_ALLOW_SOURCE_WOULD_QUARANTINE",
    "PATH_WOULD_ALLOW_RISK_HIGH",
    "PATH_WOULD_ALLOW_RISK_CRITICAL",
    "SOURCE_WOULD_TRUST_PATH_WOULD_DENY",
    "SOURCE_WOULD_TRUST_PATH_WOULD_RESTRICT",
    "AUTHORITY_SCOPE_MISSING",
    "PROVENANCE_MISSING",
    "EVIDENCE_CONFLICTED",
    "UNTRUSTED_BOUNDARY_COMMAND_SURFACE",
    "UNKNOWN",
}

_REQUIRED_RULE_KINDS = {
    "STRICTEST_WINS_SHADOW",
    "REVIEW_ON_CONFLICT",
    "POLICY_REVIEW_ON_UNKNOWN",
    "OPERATOR_REVIEW_ON_HIGH_RISK",
    "QUARANTINE_RECOMMENDED_ON_CRITICAL",
    "SOURCE_DISTRUST_OVERRIDES_PATH_ALLOW",
    "PATH_DENY_OVERRIDES_SOURCE_TRUST",
    "MISSING_PROVENANCE_REQUIRES_REVIEW",
    "CONFLICTED_EVIDENCE_REQUIRES_POLICY_REVIEW",
    "UNKNOWN",
}

_REQUIRED_SEVERITIES = {
    "NONE",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "UNKNOWN",
}

_REQUIRED_POSTURES = {
    "NO_CONFLICT",
    "INFORMATIONAL",
    "REVIEW_RECOMMENDED",
    "OPERATOR_REVIEW_RECOMMENDED",
    "POLICY_REVIEW_RECOMMENDED",
    "RESTRICT_RECOMMENDED",
    "QUARANTINE_RECOMMENDED",
    "UNKNOWN",
}


def _source_identity(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.TRUSTED,
):
    return build_source_identity(
        source_kind=SourceKind.OPERATOR_INPUT,
        source_origin=SourceOrigin.OPERATOR,
        uri_or_path=f"DEV_FIXTURE:source/{trust_label.value}",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=trust_label,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _risk(risk_level: PathSourceRiskLevel):
    return build_path_source_risk_classification(
        signals=(
            build_path_source_risk_signal(
                PathSourceRiskSignalKind.UNKNOWN_SOURCE,
                RiskClassificationBasis.SOURCE_TRUST,
                risk_level,
                "DEV_FIXTURE risk",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata={"fixture": "DEV_FIXTURE"},
            ),
        ),
        risk_level=risk_level,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _provenance_with_confidence(
    evidence_confidence: EvidenceConfidence = EvidenceConfidence.HIGH,
):
    source_identity = _source_identity(trust_label=SourceTrustLabel.TRUSTED)
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
                "DEV_FIXTURE claim",
                confidence=evidence_confidence,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata={"fixture": "DEV_FIXTURE"},
            ),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _boundary():
    return build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
        trust_label=SourceTrustLabel.UNTRUSTED,
        posture=UntrustedBoundaryPosture.REVIEW_REQUIRED,
        influence_surfaces=(ContentInfluenceSurface.PROMPT_INSTRUCTION,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _path_result(decision: PathGovernanceShadowDecision) -> PathGovernanceResolverResult:
    return PathGovernanceResolverResult(
        input_id="DEV_FIXTURE:path-input",
        shadow_decision=decision,
        decision_reasons=(PathGovernanceDecisionReason.SHADOW_MODE_ONLY,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _source_result(decision: SourceTrustShadowDecision) -> SourceTrustResolverResult:
    return SourceTrustResolverResult(
        input_id="DEV_FIXTURE:source-input",
        shadow_decision=decision,
        decision_reasons=(SourceTrustDecisionReason.SHADOW_MODE_ONLY,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.conflict_precedence"),
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathSourceConflictKind",
        "PrecedenceRuleKind",
        "ConflictSeverity",
        "ConflictPrecedencePosture",
        "PathSourceConflictSignal",
        "PrecedenceRule",
        "ConflictPrecedenceInput",
        "ConflictPrecedenceResult",
        "resolve_path_source_conflicts_shadow",
    ):
        assert hasattr(pg, name)


def test_path_source_conflict_kind_has_required_values() -> None:
    assert {item.value for item in PathSourceConflictKind} == _REQUIRED_CONFLICT_KINDS


def test_precedence_rule_kind_has_required_values() -> None:
    assert {item.value for item in PrecedenceRuleKind} == _REQUIRED_RULE_KINDS


def test_conflict_severity_has_required_values() -> None:
    assert {item.value for item in ConflictSeverity} == _REQUIRED_SEVERITIES


def test_conflict_precedence_posture_has_required_values() -> None:
    assert {item.value for item in ConflictPrecedencePosture} == _REQUIRED_POSTURES


def test_conflict_signal_builds_deterministically() -> None:
    kwargs = {
        "conflict_kind": PathSourceConflictKind.PROVENANCE_MISSING,
        "severity": ConflictSeverity.MEDIUM,
        "reason": "DEV_FIXTURE missing provenance",
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    first = PathSourceConflictSignal(**kwargs)
    second = PathSourceConflictSignal(**kwargs)
    assert first.signal_id == second.signal_id


def test_precedence_rule_builds_deterministically() -> None:
    kwargs = {
        "rule_kind": PrecedenceRuleKind.STRICTEST_WINS_SHADOW,
        "applies_to": ("PATH_SOURCE_DECISION_MISMATCH",),
        "severity": ConflictSeverity.MEDIUM,
        "recommended_posture": ConflictPrecedencePosture.REVIEW_RECOMMENDED,
        "reason": "DEV_FIXTURE strictest wins",
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    first = PrecedenceRule(**kwargs)
    second = PrecedenceRule(**kwargs)
    assert first.rule_id == second.rule_id


def test_conflict_precedence_input_builds_deterministically() -> None:
    kwargs = {
        "path_resolver_result": _path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        "source_trust_resolver_result": _source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    first = ConflictPrecedenceInput(**kwargs)
    second = ConflictPrecedenceInput(**kwargs)
    assert first.input_id == second.input_id
    assert first.input_hash == second.input_hash


def test_conflict_precedence_result_builds_deterministically() -> None:
    first = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert first.result_id == second.result_id
    assert first.result_hash == second.result_hash


def test_result_is_shadow_only() -> None:
    result = resolve_path_source_conflicts_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert result.shadow_only is True


def test_result_is_never_enforced() -> None:
    result = resolve_path_source_conflicts_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert result.enforced is False


def test_path_allow_source_distrust_creates_conflict() -> None:
    source_identity = _source_identity()
    before = source_identity.source_ref.trust_label
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    rule_kinds = {item.rule_kind for item in result.precedence_rules}
    assert PathSourceConflictKind.PATH_WOULD_ALLOW_SOURCE_WOULD_DISTRUST in kinds
    assert PrecedenceRuleKind.SOURCE_DISTRUST_OVERRIDES_PATH_ALLOW in rule_kinds
    assert source_identity.source_ref.trust_label is before


def test_path_allow_source_quarantine_creates_conflict() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_QUARANTINE,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    assert PathSourceConflictKind.PATH_WOULD_ALLOW_SOURCE_WOULD_QUARANTINE in kinds
    assert result.final_shadow_posture is ConflictPrecedencePosture.QUARANTINE_RECOMMENDED
    assert not hasattr(result, "quarantine_source")


def test_source_trust_path_deny_creates_conflict() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    rule_kinds = {item.rule_kind for item in result.precedence_rules}
    assert PathSourceConflictKind.SOURCE_WOULD_TRUST_PATH_WOULD_DENY in kinds
    assert PrecedenceRuleKind.PATH_DENY_OVERRIDES_SOURCE_TRUST in rule_kinds
    assert result.enforced is False


def test_source_trust_path_restrict_creates_conflict() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_RESTRICT),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    assert PathSourceConflictKind.SOURCE_WOULD_TRUST_PATH_WOULD_RESTRICT in kinds
    assert result.enforced is False


def _authority_scope():
    return build_path_authority_scope(
        subject=PathAuthoritySubject(
            subject_kind=PathAuthoritySubjectKind.OPERATOR,
            display_name="DEV_FIXTURE",
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        actions=(PathScopeAction.READ,),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def test_permissive_path_source_high_risk_creates_conflict() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        provenance_binding=_provenance_with_confidence(),
        authority_scope=_authority_scope(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    rule_kinds = {item.rule_kind for item in result.precedence_rules}
    assert PathSourceConflictKind.PATH_WOULD_ALLOW_RISK_HIGH in kinds
    assert PrecedenceRuleKind.OPERATOR_REVIEW_ON_HIGH_RISK in rule_kinds
    assert result.would_require_operator_review is True


def test_permissive_path_source_critical_risk_creates_conflict() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        provenance_binding=_provenance_with_confidence(),
        authority_scope=_authority_scope(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    rule_kinds = {item.rule_kind for item in result.precedence_rules}
    assert PathSourceConflictKind.PATH_WOULD_ALLOW_RISK_CRITICAL in kinds
    assert PrecedenceRuleKind.QUARANTINE_RECOMMENDED_ON_CRITICAL in rule_kinds
    assert result.enforced is False


def test_missing_provenance_creates_review_precedence() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    rule_kinds = {item.rule_kind for item in result.precedence_rules}
    assert PathSourceConflictKind.PROVENANCE_MISSING in kinds
    assert PrecedenceRuleKind.MISSING_PROVENANCE_REQUIRES_REVIEW in rule_kinds


def test_conflicted_evidence_creates_policy_review_precedence() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        provenance_binding=_provenance_with_confidence(
            evidence_confidence=EvidenceConfidence.CONFLICTED,
        ),
        authority_scope=_authority_scope(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    rule_kinds = {item.rule_kind for item in result.precedence_rules}
    assert PathSourceConflictKind.EVIDENCE_CONFLICTED in kinds
    assert PrecedenceRuleKind.CONFLICTED_EVIDENCE_REQUIRES_POLICY_REVIEW in rule_kinds
    assert result.would_require_policy_review is True


def test_untrusted_boundary_command_surface_creates_conflict_signal() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        untrusted_boundary=_boundary(),
        provenance_binding=_provenance_with_confidence(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    kinds = {item.conflict_kind for item in result.conflict_signals}
    assert PathSourceConflictKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE in kinds
    assert result.enforced is False


def test_strictest_shadow_precedence_is_deterministic() -> None:
    first = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert first.recommended_shadow_decision == second.recommended_shadow_decision
    assert (
        first.recommended_shadow_decision == "WOULD_DISTRUST"
    )
    rule_kinds = {item.rule_kind for item in first.precedence_rules}
    assert PrecedenceRuleKind.STRICTEST_WINS_SHADOW in rule_kinds


def test_recommended_decision_remains_advisory() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert result.recommended_shadow_decision.startswith("WOULD_")
    forbidden = {"ALLOW", "DENY", "BLOCK", "TRUST", "DISTRUST", "QUARANTINE_NOW"}
    assert result.recommended_shadow_decision not in forbidden


def test_no_real_allow_deny_block_enforce_api_exists() -> None:
    module = importlib.import_module(
        "agentic_runtime.path_governance.conflict_precedence",
    )
    forbidden_exports = {
        "allow",
        "deny",
        "block",
        "enforce",
        "authorize",
        "can_command",
        "can_write_memory",
        "can_use_as_tool_argument",
    }
    assert not forbidden_exports & {name.lower() for name in dir(module)}


def test_no_source_trust_mutation() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.policy",
        "SourceTrustTaxonomy(",
        ".trust_label =",
    ):
        assert snippet not in source


def test_no_policy_engine_call_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
        "evaluate_policy",
    ):
        assert snippet not in source


def test_no_approval_activation_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.approval",
        "approval_queue",
        "activate_approval",
        "request_approval",
        "create_approval",
    ):
        assert snippet not in source


def test_no_trace_or_ledger_write_exists() -> None:
    source = _module_source()
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
        "Path.resolve",
        "Path.exists",
        "Path.stat",
        "open(",
        "read_text",
        "read_bytes",
        "requests.",
        "urllib",
        "httpx",
    ):
        assert snippet not in source


def test_result_hash_is_deterministic() -> None:
    first = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert first.result_hash == second.result_hash


def test_changed_path_source_risk_or_provenance_changes_result_hash() -> None:
    base = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        provenance_binding=_provenance_with_confidence(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_path = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        provenance_binding=_provenance_with_confidence(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_source = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        provenance_binding=_provenance_with_confidence(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_risk = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        provenance_binding=_provenance_with_confidence(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_provenance = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        provenance_binding=_provenance_with_confidence(
            evidence_confidence=EvidenceConfidence.CONFLICTED,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_boundary = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(
            SourceTrustShadowDecision.WOULD_TRUST,
        ),
        provenance_binding=_provenance_with_confidence(),
        untrusted_boundary=_boundary(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    hashes = {
        base.result_hash,
        changed_path.result_hash,
        changed_source.result_hash,
        changed_risk.result_hash,
        changed_provenance.result_hash,
        changed_boundary.result_hash,
    }
    assert len(hashes) == 6


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc_info:
        ConflictPrecedenceInput.from_dict({"shadow_authority_grant": True})
    assert "UNKNOWN_FIELD" in str(exc_info.value.code)


def test_source_labels_are_preserved() -> None:
    live = resolve_path_source_conflicts_shadow(
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture = resolve_path_source_conflicts_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert live.source_label is ProjectionSourceLabel.LIVE
    assert fixture.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    result = resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )
    assert result.source_label is ProjectionSourceLabel.DEV_FIXTURE

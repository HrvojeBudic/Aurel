"""P1.7.10 — Path Governance Resolver v0 / Shadow Mode tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    ContentInfluenceSurface,
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathBoundaryCheckResult,
    PathBoundaryStatus,
    PathGovernanceDecisionReason,
    PathGovernanceResolverInput,
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
    PathGovernanceUnknownFieldError,
    PathKind,
    PathScopeAction,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    ProjectionSourceLabel,
    RiskClassificationBasis,
    SourceKind,
    SourceOrigin,
    SourceTrustLabel,
    UntrustedBoundaryPosture,
    UntrustedContentKind,
    build_path_authority_scope,
    build_path_identity,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
    build_provenance_binding,
    build_source_identity,
    build_trusted_root_registry,
    build_untrusted_content_boundary,
    resolve_path_governance_shadow,
)


_REQUIRED_SHADOW_DECISIONS = {
    "WOULD_ALLOW",
    "WOULD_REVIEW",
    "WOULD_RESTRICT",
    "WOULD_DENY",
    "WOULD_QUARANTINE",
    "WOULD_REQUIRE_OPERATOR_REVIEW",
    "WOULD_REQUIRE_POLICY_REVIEW",
    "UNKNOWN",
}

_REQUIRED_DECISION_REASONS = {
    "SOURCE_TRUST_ACCEPTABLE",
    "SOURCE_TRUST_UNTRUSTED",
    "SOURCE_TRUST_UNKNOWN",
    "PATH_WITHIN_DECLARED_ROOT",
    "PATH_OUTSIDE_DECLARED_ROOT",
    "PATH_TRAVERSAL_CANDIDATE",
    "AUTHORITY_SCOPE_DECLARED",
    "AUTHORITY_SCOPE_MISSING",
    "UNTRUSTED_CONTENT_BOUNDARY",
    "RISK_CLASSIFICATION_HIGH",
    "RISK_CLASSIFICATION_CRITICAL",
    "PROVENANCE_MISSING",
    "EVIDENCE_UNVERIFIED",
    "POLICY_BRIDGE_UNAVAILABLE",
    "SHADOW_MODE_ONLY",
    "UNKNOWN",
}


def _source_identity(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.OPERATOR_PROVIDED,
    source_kind: SourceKind = SourceKind.OPERATOR_INPUT,
    source_origin: SourceOrigin = SourceOrigin.OPERATOR,
):
    return build_source_identity(
        source_kind=source_kind,
        source_origin=source_origin,
        uri_or_path="DEV_FIXTURE:resolver/source",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=trust_label,
    )


def _path_identity(raw_path: str = "src/example.py"):
    return build_path_identity(
        raw_path,
        path_kind=PathKind.REPO_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _boundary_result(
    status: PathBoundaryStatus = PathBoundaryStatus.PATH_OK,
    raw_path: str = "src/example.py",
):
    return PathBoundaryCheckResult(
        normalized_path=raw_path,
        boundary_status=status,
        path_identity=_path_identity(raw_path),
        trusted_root_id="DEV_FIXTURE:root",
        trusted_root_normalized_path="src",
        reason="DEV_FIXTURE boundary context",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _scope():
    subject = PathAuthoritySubject(
        subject_kind=PathAuthoritySubjectKind.OPERATOR,
        display_name="DEV_FIXTURE operator",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )
    return build_path_authority_scope(
        subject=subject,
        actions=(PathScopeAction.READ, PathScopeAction.LIST),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _untrusted_boundary(
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


def _provenance_binding():
    return build_provenance_binding(
        source_identity=_source_identity(),
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
        "DEV_FIXTURE resolver risk signal",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
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


def _source() -> str:
    return inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.path_resolver",
    ))


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathGovernanceShadowDecision",
        "PathGovernanceDecisionReason",
        "PathGovernanceResolverInput",
        "PathGovernanceResolverResult",
        "resolve_path_governance_shadow",
    ):
        assert hasattr(pg, name)


def test_path_governance_shadow_decision_has_required_values() -> None:
    assert {item.value for item in PathGovernanceShadowDecision} == (
        _REQUIRED_SHADOW_DECISIONS
    )


def test_path_governance_decision_reason_has_required_values() -> None:
    assert {item.value for item in PathGovernanceDecisionReason} == (
        _REQUIRED_DECISION_REASONS
    )


def test_resolver_input_builds_deterministically() -> None:
    kwargs = {
        "path_identity": _path_identity(),
        "source_identity": _source_identity(),
        "trusted_root_registry": build_trusted_root_registry(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        "boundary_check_result": _boundary_result(),
        "authority_scope": _scope(),
        "untrusted_boundary": _untrusted_boundary(),
        "provenance_binding": _provenance_binding(),
        "risk_classification": _risk(PathSourceRiskLevel.LOW),
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    first = PathGovernanceResolverInput(**kwargs)
    second = PathGovernanceResolverInput(**kwargs)

    assert first.input_id == second.input_id
    assert first.input_hash == second.input_hash


def test_resolver_result_builds_deterministically() -> None:
    risk = _risk(PathSourceRiskLevel.MEDIUM)
    first = resolve_path_governance_shadow(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )
    second = resolve_path_governance_shadow(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )

    assert first.result_id == second.result_id
    assert first.result_hash == second.result_hash


def test_resolver_result_is_shadow_only() -> None:
    result = resolve_path_governance_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_only is True


def test_resolver_result_is_never_enforced() -> None:
    result = resolve_path_governance_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.enforced is False


def test_critical_risk_can_produce_would_deny_or_quarantine() -> None:
    deny_result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    quarantine_result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
        untrusted_boundary=_untrusted_boundary(
            trust_label=SourceTrustLabel.QUARANTINED,
            posture=UntrustedBoundaryPosture.QUARANTINED,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert deny_result.shadow_decision is PathGovernanceShadowDecision.WOULD_DENY
    assert quarantine_result.shadow_decision is (
        PathGovernanceShadowDecision.WOULD_QUARANTINE
    )
    assert deny_result.enforced is False
    assert quarantine_result.enforced is False


def test_high_risk_can_produce_would_restrict_or_operator_review() -> None:
    restrict_result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        boundary_check_result=_boundary_result(
            PathBoundaryStatus.PATH_OUTSIDE_TRUSTED_ROOT,
            "../outside.py",
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    review_result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert restrict_result.shadow_decision is (
        PathGovernanceShadowDecision.WOULD_RESTRICT
    )
    assert review_result.shadow_decision is (
        PathGovernanceShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW
    )
    assert not hasattr(review_result, "activate_approval")


def test_medium_risk_can_produce_would_review() -> None:
    result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.MEDIUM),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision is PathGovernanceShadowDecision.WOULD_REVIEW
    assert "PolicyEngine" not in _source()


def test_none_risk_can_produce_would_allow() -> None:
    result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.NONE),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision is PathGovernanceShadowDecision.WOULD_ALLOW
    assert not hasattr(result, "allow")


def test_unknown_risk_can_produce_review_or_unknown() -> None:
    result = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.UNKNOWN),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert result.shadow_decision in {
        PathGovernanceShadowDecision.WOULD_REVIEW,
        PathGovernanceShadowDecision.UNKNOWN,
    }


def test_traversal_candidate_produces_shadow_restriction_reason() -> None:
    result = resolve_path_governance_shadow(
        boundary_check_result=_boundary_result(
            PathBoundaryStatus.PATH_TRAVERSAL_CANDIDATE,
            "../secret.txt",
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathGovernanceDecisionReason.PATH_TRAVERSAL_CANDIDATE in (
        result.decision_reasons
    )
    assert result.shadow_decision is PathGovernanceShadowDecision.WOULD_RESTRICT
    assert result.enforced is False


def test_outside_root_candidate_produces_shadow_restriction_reason() -> None:
    result = resolve_path_governance_shadow(
        boundary_check_result=_boundary_result(
            PathBoundaryStatus.PATH_OUTSIDE_TRUSTED_ROOT,
            "other/example.py",
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathGovernanceDecisionReason.PATH_OUTSIDE_DECLARED_ROOT in (
        result.decision_reasons
    )
    assert result.enforced is False


def test_untrusted_prompt_instruction_produces_shadow_deny_or_review_reason() -> None:
    result = resolve_path_governance_shadow(
        untrusted_boundary=_untrusted_boundary(),
        risk_classification=_risk(
            PathSourceRiskLevel.CRITICAL,
            trust_label=SourceTrustLabel.UNTRUSTED,
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathGovernanceDecisionReason.SOURCE_TRUST_UNTRUSTED in (
        result.decision_reasons
    )
    assert PathGovernanceDecisionReason.UNTRUSTED_CONTENT_BOUNDARY in (
        result.decision_reasons
    )
    assert result.shadow_decision is PathGovernanceShadowDecision.WOULD_DENY
    assert "def filter" not in _source()


def test_missing_provenance_produces_review_reason() -> None:
    risk = _risk(
        PathSourceRiskLevel.UNKNOWN,
        signals=(
            _signal(
                PathSourceRiskSignalKind.MISSING_PROVENANCE,
                RiskClassificationBasis.PROVENANCE_EVIDENCE,
                PathSourceRiskLevel.UNKNOWN,
            ),
        ),
    )
    result = resolve_path_governance_shadow(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathGovernanceDecisionReason.PROVENANCE_MISSING in result.decision_reasons
    assert result.shadow_decision is PathGovernanceShadowDecision.WOULD_REVIEW
    assert "write_ledger" not in _source()


def test_unverified_evidence_produces_review_reason() -> None:
    risk = _risk(
        PathSourceRiskLevel.LOW,
        signals=(
            _signal(
                PathSourceRiskSignalKind.UNVERIFIED_CLAIM,
                RiskClassificationBasis.CLAIM_REFERENCE,
                PathSourceRiskLevel.LOW,
            ),
        ),
    )
    result = resolve_path_governance_shadow(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathGovernanceDecisionReason.EVIDENCE_UNVERIFIED in result.decision_reasons
    assert result.shadow_decision is PathGovernanceShadowDecision.WOULD_REVIEW


def test_missing_authority_scope_produces_policy_review_reason() -> None:
    risk = _risk(
        PathSourceRiskLevel.MEDIUM,
        signals=(
            _signal(
                PathSourceRiskSignalKind.UNKNOWN,
                RiskClassificationBasis.AUTHORITY_SCOPE,
                PathSourceRiskLevel.MEDIUM,
            ),
        ),
    )
    result = resolve_path_governance_shadow(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert PathGovernanceDecisionReason.AUTHORITY_SCOPE_MISSING in (
        result.decision_reasons
    )
    assert PathGovernanceDecisionReason.POLICY_BRIDGE_UNAVAILABLE in (
        result.decision_reasons
    )
    assert result.shadow_decision is (
        PathGovernanceShadowDecision.WOULD_REQUIRE_POLICY_REVIEW
    )
    assert "PolicyEngine" not in _source()


def test_shadow_mode_reason_always_present() -> None:
    for risk_level in PathSourceRiskLevel:
        result = resolve_path_governance_shadow(
            risk_classification=_risk(risk_level),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        )
        assert PathGovernanceDecisionReason.SHADOW_MODE_ONLY in (
            result.decision_reasons
        )


def test_result_hash_is_deterministic() -> None:
    first = resolve_path_governance_shadow(
        path_identity=_path_identity(),
        source_identity=_source_identity(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    second = resolve_path_governance_shadow(
        path_identity=_path_identity(),
        source_identity=_source_identity(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert first.result_hash == second.result_hash


def test_changed_risk_changes_result_hash() -> None:
    low = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    high = resolve_path_governance_shadow(
        risk_classification=_risk(PathSourceRiskLevel.HIGH),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert low.result_hash != high.result_hash


def test_changed_path_or_source_changes_result_hash() -> None:
    base = resolve_path_governance_shadow(
        path_identity=_path_identity("src/example.py"),
        source_identity=_source_identity(
            trust_label=SourceTrustLabel.OPERATOR_PROVIDED,
        ),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_path = resolve_path_governance_shadow(
        path_identity=_path_identity("src/other.py"),
        source_identity=_source_identity(
            trust_label=SourceTrustLabel.OPERATOR_PROVIDED,
        ),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    changed_source = resolve_path_governance_shadow(
        path_identity=_path_identity("src/example.py"),
        source_identity=_source_identity(trust_label=SourceTrustLabel.INTERNAL_REPO),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert base.result_hash != changed_path.result_hash
    assert base.result_hash != changed_source.result_hash


def test_changed_boundary_or_authority_or_provenance_changes_result_hash() -> None:
    risk = _risk(PathSourceRiskLevel.LOW)
    base = resolve_path_governance_shadow(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    with_boundary = resolve_path_governance_shadow(
        risk_classification=risk,
        boundary_check_result=_boundary_result(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    with_authority = resolve_path_governance_shadow(
        risk_classification=risk,
        authority_scope=_scope(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    with_provenance = resolve_path_governance_shadow(
        risk_classification=risk,
        provenance_binding=_provenance_binding(),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert base.result_hash != with_boundary.result_hash
    assert base.result_hash != with_authority.result_hash
    assert base.result_hash != with_provenance.result_hash


def test_unknown_fields_are_rejected() -> None:
    resolver_input = PathGovernanceResolverInput(
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    result = resolve_path_governance_shadow(resolver_input)

    input_payload = resolver_input.to_canonical_dict()
    input_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as input_error:
        PathGovernanceResolverInput.from_dict(input_payload)
    assert input_error.value.code.value == "UNKNOWN_FIELD"

    result_payload = result.to_canonical_dict()
    result_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as result_error:
        PathGovernanceResolverResult.from_dict(result_payload)
    assert result_error.value.code.value == "UNKNOWN_FIELD"


def test_source_labels_are_preserved() -> None:
    live_input = PathGovernanceResolverInput(source_label=ProjectionSourceLabel.LIVE)
    fixture_result = resolve_path_governance_shadow(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert live_input.source_label is ProjectionSourceLabel.LIVE
    assert fixture_result.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_fixture_state() -> None:
    resolver_input = PathGovernanceResolverInput(
        path_identity=_path_identity(),
        source_identity=_source_identity(),
        risk_classification=_risk(PathSourceRiskLevel.LOW),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )

    assert resolver_input.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert resolver_input.path_identity is not None
    assert resolver_input.path_identity.path_ref.source_label is (
        ProjectionSourceLabel.DEV_FIXTURE
    )
    assert resolver_input.source_identity is not None
    assert resolver_input.source_identity.source_ref.source_label is (
        ProjectionSourceLabel.DEV_FIXTURE
    )


def test_no_real_allow_deny_block_api_exists() -> None:
    pg = importlib.import_module("agentic_runtime.path_governance.path_resolver")
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
    assert not forbidden_exports & {name.lower() for name in dir(pg)}
    for item in PathGovernanceShadowDecision:
        assert item.value.startswith("WOULD_") or item.value == "UNKNOWN"


def test_would_vocabulary_does_not_enforce() -> None:
    result = PathGovernanceResolverResult(
        input_id=PathGovernanceResolverInput(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ).input_id,
        shadow_decision=PathGovernanceShadowDecision.WOULD_DENY,
        decision_reasons=(PathGovernanceDecisionReason.SHADOW_MODE_ONLY,),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    for name in ("allow", "deny", "restrict", "quarantine", "enforce", "authorize"):
        assert not hasattr(result, name)
    assert result.enforced is False


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

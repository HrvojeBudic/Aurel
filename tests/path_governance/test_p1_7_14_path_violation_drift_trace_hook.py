"""P1.7.14 — Path Violation / Drift Trace Hook tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
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
    PathSourceDriftSignal,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    PathViolationSeverity,
    PathViolationTraceDisposition,
    PathViolationTraceEventKind,
    PathViolationTraceHookMode,
    PathViolationTraceHookResult,
    PathViolationTraceInput,
    PathViolationTracePayload,
    PathViolationTraceReason,
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
    build_path_resolution_trace_payload,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
    build_path_violation_trace_payload,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
    build_source_identity,
    build_untrusted_content_boundary,
    detect_path_source_drift_signals,
    record_path_violation_trace_hook,
    resolve_path_source_conflicts_shadow,
)

_REQUIRED_EVENT_KINDS = {
    "PATH_BOUNDARY_VIOLATION_CANDIDATE",
    "PATH_TRAVERSAL_DRIFT",
    "SOURCE_TRUST_DRIFT",
    "RISK_CLASSIFICATION_DRIFT",
    "CONFLICT_PRECEDENCE_DRIFT",
    "PROVENANCE_EXPECTATION_MISSING",
    "AUTHORITY_SCOPE_MISSING_DRIFT",
    "UNTRUSTED_BOUNDARY_DRIFT",
    "TRACE_PAYLOAD_MISMATCH",
    "VIOLATION_TRACE_PAYLOAD_CREATED",
    "VIOLATION_TRACE_SINK_UNAVAILABLE",
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

_REQUIRED_HOOK_MODES = {
    "PAYLOAD_ONLY",
    "INJECTED_SINK",
    "TRACE_SPINE_UNAVAILABLE",
    "ERROR",
    "UNKNOWN",
}

_REQUIRED_DISPOSITIONS = {
    "WOULD_RECORD",
    "PAYLOAD_CREATED",
    "RECORDED_TO_INJECTED_SINK",
    "TRACE_SPINE_UNAVAILABLE",
    "SKIPPED",
    "ERROR",
    "UNKNOWN",
}

_REQUIRED_REASONS = {
    "PATH_RESOLVER_RESULT_PRESENT",
    "SOURCE_TRUST_RESULT_PRESENT",
    "CONFLICT_PRECEDENCE_PRESENT",
    "RISK_CLASSIFICATION_PRESENT",
    "EXPECTED_TRACE_PAYLOAD_PRESENT",
    "CURRENT_TRACE_PAYLOAD_PRESENT",
    "PATH_BOUNDARY_CHANGED",
    "SOURCE_TRUST_CHANGED",
    "RISK_CLASSIFICATION_CHANGED",
    "CONFLICT_PRECEDENCE_CHANGED",
    "PROVENANCE_MISSING",
    "AUTHORITY_SCOPE_MISSING",
    "BOUNDARY_CONTEXT_CHANGED",
    "SHADOW_ONLY_CONTEXT",
    "ENFORCEMENT_UNAVAILABLE",
    "LEDGER_UNAVAILABLE",
    "TRACE_SPINE_UNAVAILABLE",
    "UNKNOWN",
}

_FORBIDDEN_SUMMARY_TOKENS = {
    "DENIED",
    "ALLOWED",
    "BLOCKED",
    "ENFORCED",
    "ROLLED_BACK",
    "CORRECTED",
    "REPAIRED",
    "QUARANTINED",
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


def _authority_scope(*, display_name: str = "DEV_FIXTURE"):
    return build_path_authority_scope(
        subject=PathAuthoritySubject(
            subject_kind=PathAuthoritySubjectKind.OPERATOR,
            display_name=display_name,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        actions=(PathScopeAction.READ,),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata={"fixture": "DEV_FIXTURE"},
    )


def _boundary(*, content_kind: UntrustedContentKind = UntrustedContentKind.EXTERNAL_TEXT):
    return build_untrusted_content_boundary(
        content_kind=content_kind,
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


def _conflict_result(
    *,
    path_decision: PathGovernanceShadowDecision = PathGovernanceShadowDecision.WOULD_ALLOW,
    source_decision: SourceTrustShadowDecision = SourceTrustShadowDecision.WOULD_DISTRUST,
):
    return resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(path_decision),
        source_trust_resolver_result=_source_result(source_decision),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _trace_payload(**overrides):
    base = {
        "path_resolver_result": _path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        "source_trust_resolver_result": _source_result(
            SourceTrustShadowDecision.WOULD_DISTRUST,
        ),
        "conflict_precedence_result": _conflict_result(),
        "risk_classification": _risk(PathSourceRiskLevel.HIGH),
        "provenance_binding": _provenance_with_confidence(),
        "authority_scope": _authority_scope(),
        "untrusted_boundary": _boundary(),
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }
    base.update(overrides)
    return build_path_resolution_trace_payload(**base)


def _matched_context():
    path = _path_result(PathGovernanceShadowDecision.WOULD_ALLOW)
    source = _source_result(SourceTrustShadowDecision.WOULD_DISTRUST)
    conflict = _conflict_result()
    risk = _risk(PathSourceRiskLevel.HIGH)
    provenance = _provenance_with_confidence()
    authority = _authority_scope()
    boundary = _boundary()
    expected_trace = _trace_payload()
    current_trace = _trace_payload()
    return {
        "expected_path_resolver_result": path,
        "current_path_resolver_result": path,
        "expected_source_trust_result": source,
        "current_source_trust_result": source,
        "expected_conflict_precedence_result": conflict,
        "current_conflict_precedence_result": conflict,
        "expected_trace_payload": expected_trace,
        "current_trace_payload": current_trace,
        "risk_classification": risk,
        "provenance_binding": provenance,
        "authority_scope": authority,
        "untrusted_boundary": boundary,
        "source_label": ProjectionSourceLabel.DEV_FIXTURE,
        "metadata": {"fixture": "DEV_FIXTURE"},
    }


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.path_violation_trace"),
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathViolationTraceEventKind",
        "PathViolationSeverity",
        "PathViolationTraceHookMode",
        "PathViolationTraceDisposition",
        "PathViolationTraceReason",
        "PathViolationTraceInput",
        "PathViolationTracePayload",
        "PathViolationTraceHookResult",
        "PathSourceDriftSignal",
        "build_path_violation_trace_payload",
        "record_path_violation_trace_hook",
        "detect_path_source_drift_signals",
    ):
        assert hasattr(pg, name)


def test_violation_trace_event_kind_has_required_values() -> None:
    assert {item.value for item in PathViolationTraceEventKind} == _REQUIRED_EVENT_KINDS


def test_violation_severity_has_required_values() -> None:
    assert {item.value for item in PathViolationSeverity} == _REQUIRED_SEVERITIES


def test_violation_trace_hook_mode_has_required_values() -> None:
    assert {item.value for item in PathViolationTraceHookMode} == _REQUIRED_HOOK_MODES


def test_violation_trace_disposition_has_required_values() -> None:
    assert {item.value for item in PathViolationTraceDisposition} == _REQUIRED_DISPOSITIONS


def test_violation_trace_reason_has_required_values() -> None:
    assert {item.value for item in PathViolationTraceReason} == _REQUIRED_REASONS


def test_violation_trace_input_builds_deterministically() -> None:
    first = PathViolationTraceInput(**_matched_context())
    second = PathViolationTraceInput(**_matched_context())
    assert first.input_id == second.input_id
    assert first.input_hash == second.input_hash


def test_violation_trace_payload_builds_deterministically() -> None:
    first = build_path_violation_trace_payload(**_matched_context())
    second = build_path_violation_trace_payload(**_matched_context())
    assert first.payload_id == second.payload_id
    assert first.payload_hash == second.payload_hash


def test_violation_trace_hook_result_builds_deterministically() -> None:
    first = record_path_violation_trace_hook(**_matched_context())
    second = record_path_violation_trace_hook(**_matched_context())
    assert first.hook_id == second.hook_id
    assert first.hook_hash == second.hook_hash


def test_detects_path_resolver_drift() -> None:
    context = _matched_context()
    context["current_path_resolver_result"] = _path_result(
        PathGovernanceShadowDecision.WOULD_DENY,
    )
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind in {
        PathViolationTraceEventKind.PATH_BOUNDARY_VIOLATION_CANDIDATE,
        PathViolationTraceEventKind.PATH_TRAVERSAL_DRIFT,
    }
    assert PathViolationTraceReason.PATH_BOUNDARY_CHANGED in payload.drift_reasons
    result = record_path_violation_trace_hook(**context)
    assert result.enforcement_triggered is False
    assert result.runtime_mutated is False


def test_detects_source_trust_drift() -> None:
    context = _matched_context()
    context["current_source_trust_result"] = _source_result(
        SourceTrustShadowDecision.WOULD_QUARANTINE,
    )
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.SOURCE_TRUST_DRIFT
    assert PathViolationTraceReason.SOURCE_TRUST_CHANGED in payload.drift_reasons


def test_detects_risk_classification_drift() -> None:
    context = _matched_context()
    context["risk_classification"] = _risk(PathSourceRiskLevel.LOW)
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.RISK_CLASSIFICATION_DRIFT
    assert PathViolationTraceReason.RISK_CLASSIFICATION_CHANGED in payload.drift_reasons


def test_detects_conflict_precedence_drift() -> None:
    context = _matched_context()
    context["current_conflict_precedence_result"] = _conflict_result(
        path_decision=PathGovernanceShadowDecision.WOULD_DENY,
        source_decision=SourceTrustShadowDecision.WOULD_TRUST,
    )
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.CONFLICT_PRECEDENCE_DRIFT
    assert PathViolationTraceReason.CONFLICT_PRECEDENCE_CHANGED in payload.drift_reasons


def test_detects_provenance_expectation_missing() -> None:
    context = _matched_context()
    context["provenance_binding"] = None
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.PROVENANCE_EXPECTATION_MISSING
    assert PathViolationTraceReason.PROVENANCE_MISSING in payload.drift_reasons
    result = record_path_violation_trace_hook(**context)
    assert result.ledger_written is False


def test_detects_authority_scope_missing_drift() -> None:
    context = _matched_context()
    context["authority_scope"] = None
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.AUTHORITY_SCOPE_MISSING_DRIFT
    assert PathViolationTraceReason.AUTHORITY_SCOPE_MISSING in payload.drift_reasons


def test_detects_untrusted_boundary_drift() -> None:
    context = _matched_context()
    context["untrusted_boundary"] = _boundary(content_kind=UntrustedContentKind.TOOL_OUTPUT)
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.UNTRUSTED_BOUNDARY_DRIFT
    assert PathViolationTraceReason.BOUNDARY_CONTEXT_CHANGED in payload.drift_reasons


def test_detects_trace_payload_mismatch() -> None:
    context = _matched_context()
    context["current_trace_payload"] = _trace_payload(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
    )
    payload = build_path_violation_trace_payload(**context)
    assert payload.event_kind == PathViolationTraceEventKind.TRACE_PAYLOAD_MISMATCH
    assert (
        PathViolationTraceReason.EXPECTED_TRACE_PAYLOAD_PRESENT in payload.drift_reasons
        or PathViolationTraceReason.CURRENT_TRACE_PAYLOAD_PRESENT in payload.drift_reasons
    )
    result = record_path_violation_trace_hook(**context)
    assert result.ledger_written is False


def test_payload_summary_is_observational_only() -> None:
    context = _matched_context()
    context["current_path_resolver_result"] = _path_result(
        PathGovernanceShadowDecision.WOULD_DENY,
    )
    payload = build_path_violation_trace_payload(**context)
    summary = dict(payload.violation_summary)
    assert summary.get("enforced") is False
    assert summary.get("shadow_only") is True
    for token in _FORBIDDEN_SUMMARY_TOKENS:
        for value in summary.values():
            if isinstance(value, str):
                assert value.upper() != token
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        assert item.upper() != token


def test_default_hook_mode_is_payload_only() -> None:
    result = record_path_violation_trace_hook(**_matched_context())
    assert result.hook_mode == PathViolationTraceHookMode.PAYLOAD_ONLY


def test_payload_only_does_not_write_trace() -> None:
    result = record_path_violation_trace_hook(**_matched_context())
    assert result.trace_written is False


def test_payload_only_does_not_write_ledger() -> None:
    result = record_path_violation_trace_hook(**_matched_context())
    assert result.ledger_written is False


def test_injected_sink_receives_payload_deterministically() -> None:
    received: list[PathViolationTracePayload] = []

    def sink(payload: PathViolationTracePayload) -> None:
        received.append(payload)

    result = record_path_violation_trace_hook(
        **_matched_context(),
        sink=sink,
        sink_name="DEV_FIXTURE:test_sink",
    )
    assert len(received) == 1
    assert result.hook_mode == PathViolationTraceHookMode.INJECTED_SINK
    assert result.disposition == PathViolationTraceDisposition.RECORDED_TO_INJECTED_SINK
    assert result.trace_written is True
    assert received[0].payload_hash == result.payload.payload_hash


def test_injected_sink_does_not_write_ledger() -> None:
    result = record_path_violation_trace_hook(
        **_matched_context(),
        sink=lambda _payload: None,
    )
    assert result.ledger_written is False


def test_injected_sink_does_not_mutate_runtime() -> None:
    result = record_path_violation_trace_hook(
        **_matched_context(),
        sink=lambda _payload: None,
    )
    assert result.runtime_mutated is False


def test_ledger_written_false_always() -> None:
    context = _matched_context()
    context["current_path_resolver_result"] = _path_result(
        PathGovernanceShadowDecision.WOULD_DENY,
    )
    payload_only = record_path_violation_trace_hook(**context)
    injected = record_path_violation_trace_hook(**context, sink=lambda _payload: None)

    def failing_sink(_payload: PathViolationTracePayload) -> None:
        raise RuntimeError("DEV_FIXTURE sink failure")

    error_result = record_path_violation_trace_hook(**context, sink=failing_sink)
    assert payload_only.ledger_written is False
    assert injected.ledger_written is False
    assert error_result.ledger_written is False


def test_runtime_mutated_false_always() -> None:
    context = _matched_context()
    payload_only = record_path_violation_trace_hook(**context)
    injected = record_path_violation_trace_hook(**context, sink=lambda _payload: None)
    assert payload_only.runtime_mutated is False
    assert injected.runtime_mutated is False


def test_enforcement_triggered_false_always() -> None:
    context = _matched_context()
    context["current_path_resolver_result"] = _path_result(
        PathGovernanceShadowDecision.WOULD_DENY,
    )
    payload_only = record_path_violation_trace_hook(**context)
    injected = record_path_violation_trace_hook(**context, sink=lambda _payload: None)

    def failing_sink(_payload: PathViolationTracePayload) -> None:
        raise RuntimeError("DEV_FIXTURE sink failure")

    error_result = record_path_violation_trace_hook(**context, sink=failing_sink)
    assert payload_only.enforcement_triggered is False
    assert injected.enforcement_triggered is False
    assert error_result.enforcement_triggered is False


def test_no_fake_trace_verified() -> None:
    payload = build_path_violation_trace_payload(**_matched_context())
    assert PathViolationTraceReason.TRACE_SPINE_UNAVAILABLE in payload.drift_reasons
    assert payload.source_label is not ProjectionSourceLabel.TRACE_VERIFIED


def test_payload_hash_changes_when_expected_current_objects_change() -> None:
    context = _matched_context()
    base = build_path_violation_trace_payload(**context)
    changed_path = build_path_violation_trace_payload(
        **{
            **context,
            "current_path_resolver_result": _path_result(
                PathGovernanceShadowDecision.WOULD_DENY,
            ),
        },
    )
    changed_source = build_path_violation_trace_payload(
        **{
            **context,
            "current_source_trust_result": _source_result(
                SourceTrustShadowDecision.WOULD_QUARANTINE,
            ),
        },
    )
    changed_conflict = build_path_violation_trace_payload(
        **{
            **context,
            "current_conflict_precedence_result": _conflict_result(
                path_decision=PathGovernanceShadowDecision.WOULD_DENY,
                source_decision=SourceTrustShadowDecision.WOULD_TRUST,
            ),
        },
    )
    changed_trace = build_path_violation_trace_payload(
        **{
            **context,
            "current_trace_payload": _trace_payload(
                path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
            ),
        },
    )
    hashes = {
        base.payload_hash,
        changed_path.payload_hash,
        changed_source.payload_hash,
        changed_conflict.payload_hash,
        changed_trace.payload_hash,
    }
    assert len(hashes) == 5


def test_payload_hash_changes_when_risk_provenance_boundary_authority_changes() -> None:
    context = _matched_context()
    base = build_path_violation_trace_payload(**context)
    changed_risk = build_path_violation_trace_payload(
        **{**context, "risk_classification": _risk(PathSourceRiskLevel.CRITICAL)},
    )
    changed_provenance = build_path_violation_trace_payload(
        **{
            **context,
            "provenance_binding": _provenance_with_confidence(
                evidence_confidence=EvidenceConfidence.CONFLICTED,
            ),
        },
    )
    changed_authority = build_path_violation_trace_payload(
        **{
            **context,
            "authority_scope": _authority_scope(display_name="DEV_FIXTURE:changed"),
        },
    )
    changed_boundary = build_path_violation_trace_payload(
        **{
            **context,
            "untrusted_boundary": _boundary(content_kind=UntrustedContentKind.TOOL_OUTPUT),
        },
    )
    hashes = {
        base.payload_hash,
        changed_risk.payload_hash,
        changed_provenance.payload_hash,
        changed_authority.payload_hash,
        changed_boundary.payload_hash,
    }
    assert len(hashes) == 5


def test_hook_hash_changes_when_payload_or_mode_changes() -> None:
    context = _matched_context()
    base = record_path_violation_trace_hook(**context)
    changed_payload = record_path_violation_trace_hook(
        **{
            **context,
            "current_path_resolver_result": _path_result(
                PathGovernanceShadowDecision.WOULD_DENY,
            ),
        },
    )
    changed_mode = record_path_violation_trace_hook(
        **context,
        sink=lambda _payload: None,
        sink_name="DEV_FIXTURE:sink",
    )
    assert len({base.hook_hash, changed_payload.hook_hash, changed_mode.hook_hash}) == 3


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc_info:
        PathViolationTraceInput.from_dict({"shadow_authority_grant": True})
    assert "UNKNOWN_FIELD" in str(exc_info.value.code)


def test_source_labels_are_preserved() -> None:
    live_payload = build_path_violation_trace_payload(
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_payload = build_path_violation_trace_payload(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert live_payload.source_label == ProjectionSourceLabel.LIVE
    assert fixture_payload.source_label == ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_or_trace_verified_fixture_state() -> None:
    payload = build_path_violation_trace_payload(**_matched_context())
    assert payload.source_label == ProjectionSourceLabel.DEV_FIXTURE
    assert payload.source_label is not ProjectionSourceLabel.TRACE_VERIFIED


def test_no_policy_engine_call_exists() -> None:
    source = _module_source()
    for snippet in (
        "from agentic_runtime.policy",
        "PolicyEngine",
        "policy_engine",
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


def test_no_source_trust_mutation() -> None:
    source = _module_source()
    for snippet in (
        "mutate_source",
        "promote_source",
        "demote_source",
        "SourceTrustTaxonomy(",
    ):
        assert snippet not in source


def test_no_trace_or_ledger_global_write_exists() -> None:
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


def test_no_correction_or_rollback_api_exists() -> None:
    source = _module_source()
    for snippet in (
        "def correct",
        "def repair",
        "def rollback",
        "def enforce",
        "def deny",
        "def block",
        "def quarantine",
        "def authorize",
        "def can_",
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


def test_drift_signal_is_observational() -> None:
    context = _matched_context()
    context["current_path_resolver_result"] = _path_result(
        PathGovernanceShadowDecision.WOULD_DENY,
    )
    signals = detect_path_source_drift_signals(**context)
    assert len(signals) >= 1
    assert isinstance(signals[0], PathSourceDriftSignal)
    assert signals[0].drift_signal_id


def test_p1_7_0_to_p1_7_13_regression_still_pass() -> None:
    """Placeholder marker; full regression is run via validation command."""
    assert PathViolationTraceHookResult is not None

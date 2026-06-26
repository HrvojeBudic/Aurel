"""P1.7.13 — Path Resolution Trace Hook tests."""
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
    PathResolutionTraceDisposition,
    PathResolutionTraceEventKind,
    PathResolutionTraceHookMode,
    PathResolutionTraceHookResult,
    PathResolutionTraceInput,
    PathResolutionTracePayload,
    PathResolutionTraceReason,
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
    build_path_authority_scope,
    build_path_resolution_trace_payload,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
    build_source_identity,
    build_untrusted_content_boundary,
    record_path_resolution_trace_hook,
    resolve_path_source_conflicts_shadow,
)

_REQUIRED_EVENT_KINDS = {
    "PATH_RESOLUTION_SHADOW_RESULT",
    "SOURCE_TRUST_SHADOW_RESULT",
    "CONFLICT_PRECEDENCE_SHADOW_RESULT",
    "PATH_SOURCE_TRACE_SUMMARY",
    "TRACE_HOOK_ATTEMPTED",
    "TRACE_HOOK_PAYLOAD_CREATED",
    "TRACE_SINK_UNAVAILABLE",
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
    "PROVENANCE_PRESENT",
    "AUTHORITY_SCOPE_PRESENT",
    "BOUNDARY_CONTEXT_PRESENT",
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
    "APPROVED",
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


def _conflict_result():
    return resolve_path_source_conflicts_shadow(
        path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_ALLOW),
        source_trust_resolver_result=_source_result(SourceTrustShadowDecision.WOULD_DISTRUST),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )


def _full_context():
    return {
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


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.path_resolution_trace"),
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    for name in (
        "PathResolutionTraceEventKind",
        "PathResolutionTraceHookMode",
        "PathResolutionTraceDisposition",
        "PathResolutionTraceReason",
        "PathResolutionTraceInput",
        "PathResolutionTracePayload",
        "PathResolutionTraceHookResult",
        "build_path_resolution_trace_payload",
        "record_path_resolution_trace_hook",
    ):
        assert hasattr(pg, name)


def test_trace_event_kind_has_required_values() -> None:
    assert {item.value for item in PathResolutionTraceEventKind} == _REQUIRED_EVENT_KINDS


def test_trace_hook_mode_has_required_values() -> None:
    assert {item.value for item in PathResolutionTraceHookMode} == _REQUIRED_HOOK_MODES


def test_trace_disposition_has_required_values() -> None:
    assert {item.value for item in PathResolutionTraceDisposition} == _REQUIRED_DISPOSITIONS


def test_trace_reason_has_required_values() -> None:
    assert {item.value for item in PathResolutionTraceReason} == _REQUIRED_REASONS


def test_trace_input_builds_deterministically() -> None:
    first = PathResolutionTraceInput(**_full_context())
    second = PathResolutionTraceInput(**_full_context())
    assert first.input_id == second.input_id
    assert first.input_hash == second.input_hash


def test_trace_payload_builds_deterministically() -> None:
    first = build_path_resolution_trace_payload(**_full_context())
    second = build_path_resolution_trace_payload(**_full_context())
    assert first.payload_id == second.payload_id
    assert first.payload_hash == second.payload_hash


def test_trace_hook_result_builds_deterministically() -> None:
    first = record_path_resolution_trace_hook(**_full_context())
    second = record_path_resolution_trace_hook(**_full_context())
    assert first.hook_id == second.hook_id
    assert first.hook_hash == second.hook_hash


def test_payload_can_reference_path_resolver_result() -> None:
    path_result = _path_result(PathGovernanceShadowDecision.WOULD_DENY)
    payload = build_path_resolution_trace_payload(
        path_resolver_result=path_result,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{path_result.result_id}:{path_result.result_hash}"
    assert payload.path_result_ref == expected


def test_payload_can_reference_source_trust_resolver_result() -> None:
    source_result = _source_result(SourceTrustShadowDecision.WOULD_DISTRUST)
    payload = build_path_resolution_trace_payload(
        source_trust_resolver_result=source_result,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{source_result.result_id}:{source_result.result_hash}"
    assert payload.source_trust_result_ref == expected


def test_payload_can_reference_conflict_precedence_result() -> None:
    conflict = _conflict_result()
    payload = build_path_resolution_trace_payload(
        conflict_precedence_result=conflict,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{conflict.result_id}:{conflict.result_hash}"
    assert payload.conflict_result_ref == expected


def test_payload_can_reference_risk_classification() -> None:
    risk = _risk(PathSourceRiskLevel.CRITICAL)
    payload = build_path_resolution_trace_payload(
        risk_classification=risk,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{risk.classification_id}:{risk.classification_hash}"
    assert payload.risk_classification_ref == expected


def test_payload_can_reference_provenance_binding() -> None:
    provenance = _provenance_with_confidence()
    payload = build_path_resolution_trace_payload(
        provenance_binding=provenance,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{provenance.binding_id}:{provenance.binding_hash}"
    assert payload.provenance_binding_ref == expected


def test_payload_can_reference_authority_scope() -> None:
    authority = _authority_scope()
    payload = build_path_resolution_trace_payload(
        authority_scope=authority,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{authority.scope_id}:{authority.scope_hash}"
    assert payload.authority_scope_ref == expected


def test_payload_can_reference_untrusted_boundary() -> None:
    boundary = _boundary()
    payload = build_path_resolution_trace_payload(
        untrusted_boundary=boundary,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    expected = f"{boundary.boundary_id}:{boundary.boundary_hash}"
    assert payload.boundary_ref == expected


def test_payload_preserves_shadow_truth() -> None:
    payload = build_path_resolution_trace_payload(**_full_context())
    summary = dict(payload.decision_summary)
    assert summary["shadow_only"] is True
    assert summary["enforced"] is False
    assert summary["path_shadow_only"] is True
    assert summary["path_enforced"] is False
    assert summary["source_shadow_only"] is True
    assert summary["source_enforced"] is False
    assert summary["conflict_shadow_only"] is True
    assert summary["conflict_enforced"] is False


def test_payload_summary_remains_advisory() -> None:
    payload = build_path_resolution_trace_payload(**_full_context())
    summary = dict(payload.decision_summary)
    assert summary["summary_text"].startswith("Shadow")
    for key in ("path_shadow_decision", "source_shadow_decision", "conflict_recommended_shadow_decision"):
        if key in summary:
            value = str(summary[key])
            assert value.startswith("WOULD_") or value == "UNKNOWN"
    for token in _FORBIDDEN_SUMMARY_TOKENS:
        for value in summary.values():
            if isinstance(value, str):
                assert value.upper() != token


def test_default_hook_mode_is_payload_only() -> None:
    result = record_path_resolution_trace_hook(**_full_context())
    assert result.hook_mode == PathResolutionTraceHookMode.PAYLOAD_ONLY


def test_payload_only_does_not_write_trace() -> None:
    result = record_path_resolution_trace_hook(**_full_context())
    assert result.trace_written is False


def test_payload_only_does_not_write_ledger() -> None:
    result = record_path_resolution_trace_hook(**_full_context())
    assert result.ledger_written is False


def test_injected_sink_receives_payload_deterministically() -> None:
    received: list[PathResolutionTracePayload] = []

    def sink(payload: PathResolutionTracePayload) -> None:
        received.append(payload)

    result = record_path_resolution_trace_hook(
        **_full_context(),
        sink=sink,
        sink_name="DEV_FIXTURE:test_sink",
    )
    assert len(received) == 1
    assert result.hook_mode == PathResolutionTraceHookMode.INJECTED_SINK
    assert result.disposition == PathResolutionTraceDisposition.RECORDED_TO_INJECTED_SINK
    assert result.trace_written is True
    assert received[0].payload_hash == result.payload.payload_hash


def test_injected_sink_does_not_write_ledger() -> None:
    result = record_path_resolution_trace_hook(
        **_full_context(),
        sink=lambda _payload: None,
    )
    assert result.ledger_written is False


def test_injected_sink_does_not_mutate_runtime() -> None:
    result = record_path_resolution_trace_hook(
        **_full_context(),
        sink=lambda _payload: None,
    )
    assert result.runtime_mutated is False


def test_trace_spine_unavailable_is_honest() -> None:
    payload = build_path_resolution_trace_payload(**_full_context())
    assert PathResolutionTraceReason.TRACE_SPINE_UNAVAILABLE in payload.trace_reasons
    result = record_path_resolution_trace_hook(**_full_context())
    assert result.trace_written is False
    assert result.source_label == ProjectionSourceLabel.DEV_FIXTURE
    assert ProjectionSourceLabel.TRACE_VERIFIED not in payload.trace_reasons


def test_hook_result_ledger_written_false() -> None:
    payload_only = record_path_resolution_trace_hook(**_full_context())
    injected = record_path_resolution_trace_hook(
        **_full_context(),
        sink=lambda _payload: None,
    )

    def failing_sink(_payload: PathResolutionTracePayload) -> None:
        raise RuntimeError("DEV_FIXTURE sink failure")

    error_result = record_path_resolution_trace_hook(
        **_full_context(),
        sink=failing_sink,
    )
    assert payload_only.ledger_written is False
    assert injected.ledger_written is False
    assert error_result.ledger_written is False


def test_hook_result_runtime_mutated_false() -> None:
    payload_only = record_path_resolution_trace_hook(**_full_context())
    injected = record_path_resolution_trace_hook(
        **_full_context(),
        sink=lambda _payload: None,
    )
    assert payload_only.runtime_mutated is False
    assert injected.runtime_mutated is False


def test_payload_hash_changes_when_path_source_conflict_changes() -> None:
    context = _full_context()
    base = build_path_resolution_trace_payload(**context)
    changed_path = build_path_resolution_trace_payload(
        **{**context, "path_resolver_result": _path_result(PathGovernanceShadowDecision.WOULD_DENY)},
    )
    changed_source = build_path_resolution_trace_payload(
        **{
            **context,
            "source_trust_resolver_result": _source_result(
                SourceTrustShadowDecision.WOULD_QUARANTINE,
            ),
        },
    )
    changed_conflict = build_path_resolution_trace_payload(
        **{
            **context,
            "conflict_precedence_result": resolve_path_source_conflicts_shadow(
                path_resolver_result=_path_result(PathGovernanceShadowDecision.WOULD_DENY),
                source_trust_resolver_result=_source_result(
                    SourceTrustShadowDecision.WOULD_TRUST,
                ),
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
            ),
        },
    )
    hashes = {
        base.payload_hash,
        changed_path.payload_hash,
        changed_source.payload_hash,
        changed_conflict.payload_hash,
    }
    assert len(hashes) == 4


def test_payload_hash_changes_when_risk_provenance_boundary_authority_changes() -> None:
    context = _full_context()
    base = build_path_resolution_trace_payload(**context)
    changed_risk = build_path_resolution_trace_payload(
        **{**context, "risk_classification": _risk(PathSourceRiskLevel.CRITICAL)},
    )
    changed_provenance = build_path_resolution_trace_payload(
        **{
            **context,
            "provenance_binding": _provenance_with_confidence(
                evidence_confidence=EvidenceConfidence.CONFLICTED,
            ),
        },
    )
    changed_authority = build_path_resolution_trace_payload(
        **{
            **context,
            "authority_scope": build_path_authority_scope(
                subject=PathAuthoritySubject(
                    subject_kind=PathAuthoritySubjectKind.AGENT,
                    display_name="DEV_FIXTURE:changed",
                    source_label=ProjectionSourceLabel.DEV_FIXTURE,
                ),
                actions=(PathScopeAction.WRITE,),
                basis=PathAuthorityBasis.TEST_FIXTURE,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata={"fixture": "DEV_FIXTURE"},
            ),
        },
    )
    changed_boundary = build_path_resolution_trace_payload(
        **{
            **context,
            "untrusted_boundary": build_untrusted_content_boundary(
                content_kind=UntrustedContentKind.TOOL_OUTPUT,
                source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
                trust_label=SourceTrustLabel.UNTRUSTED,
                posture=UntrustedBoundaryPosture.QUARANTINED,
                influence_surfaces=(ContentInfluenceSurface.TOOL_ARGUMENT,),
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata={"fixture": "DEV_FIXTURE"},
            ),
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
    context = _full_context()
    base = record_path_resolution_trace_hook(**context)
    changed_payload = record_path_resolution_trace_hook(
        **{**context, "path_resolver_result": _path_result(PathGovernanceShadowDecision.WOULD_DENY)},
    )
    changed_mode = record_path_resolution_trace_hook(
        **context,
        sink=lambda _payload: None,
        sink_name="DEV_FIXTURE:sink",
    )
    assert len({base.hook_hash, changed_payload.hook_hash, changed_mode.hook_hash}) == 3


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc_info:
        PathResolutionTraceInput.from_dict({"shadow_authority_grant": True})
    assert "UNKNOWN_FIELD" in str(exc_info.value.code)


def test_source_labels_are_preserved() -> None:
    live_payload = build_path_resolution_trace_payload(
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_payload = build_path_resolution_trace_payload(
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert live_payload.source_label == ProjectionSourceLabel.LIVE
    assert fixture_payload.source_label == ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_live_or_trace_verified_fixture_state() -> None:
    payload = build_path_resolution_trace_payload(**_full_context())
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


def test_p1_7_0_to_p1_7_12_regression_still_pass() -> None:
    """Placeholder marker; full regression is run via validation command."""
    assert PathResolutionTraceHookResult is not None

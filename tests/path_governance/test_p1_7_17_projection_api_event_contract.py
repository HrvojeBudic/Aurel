"""P1.7.17 — Path Governance Projection/API/Event Contract tests."""
from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys

import pytest

from tests.repo_root import REPO_ROOT
from agentic_runtime.path_governance import (
    PathGovernanceApiEnvelope,
    PathGovernanceCapabilityKind,
    PathGovernanceProjectionEvent,
    PathGovernanceProjectionEventKind,
    PathGovernanceProjectionRecord,
    PathGovernanceReadModel,
    PathGovernanceUnknownFieldError,
    PathKind,
    PathPolicyContextPacket,
    ProjectionSourceLabel,
    SourceKind,
    SourceOrigin,
    SourceTrustLabel,
    build_default_path_governance_capability_projection,
    build_path_governance_api_envelope,
    build_path_governance_projection_event,
    build_path_governance_projection_record,
    build_path_governance_read_model,
    build_path_identity,
    build_path_policy_context_packet,
    build_path_resolution_trace_payload,
    build_path_violation_trace_payload,
    build_source_identity,
    run_path_governance_harness_suite,
)
from agentic_runtime.path_governance.projection_contract import (
    CLI_TUI_BINDING_UNAVAILABLE_REASON,
    HTTP_SERVER_UNAVAILABLE_REASON,
    SHELL_BINDING_UNAVAILABLE_REASON,
)

_REQUIRED_CAPABILITY_KINDS = {
    "PATH_GOVERNANCE_FOUNDATION",
    "PATH_IDENTITY",
    "SOURCE_IDENTITY",
    "SOURCE_TRUST_TAXONOMY",
    "TRUSTED_ROOT_REGISTRY",
    "PATH_NORMALIZATION_ESCAPE_DETECTION",
    "PATH_AUTHORITY_SCOPE",
    "UNTRUSTED_CONTENT_BOUNDARY",
    "SOURCE_PROVENANCE_EVIDENCE_BINDING",
    "PATH_SOURCE_RISK_CLASSIFICATION",
    "PATH_GOVERNANCE_RESOLVER_SHADOW",
    "SOURCE_TRUST_RESOLVER_SHADOW",
    "CONFLICT_PRECEDENCE_SHADOW",
    "PATH_RESOLUTION_TRACE_HOOK",
    "PATH_VIOLATION_DRIFT_TRACE_HOOK",
    "PATH_GOVERNANCE_TEST_HARNESS",
    "POLICY_CONTEXT_BRIDGE",
    "PROJECTION_API_EVENT_CONTRACT",
    "CLI_TUI_BINDING",
    "UNKNOWN",
}

_REQUIRED_EVENT_KINDS = {
    "CAPABILITY_PROJECTED",
    "READ_MODEL_CREATED",
    "POLICY_CONTEXT_PROJECTED",
    "TRACE_HOOK_PROJECTED",
    "VIOLATION_DRIFT_PROJECTED",
    "HARNESS_RESULT_PROJECTED",
    "CLI_BINDING_UNAVAILABLE",
    "SHELL_BINDING_UNAVAILABLE",
    "POLICY_RUNTIME_UNAVAILABLE",
    "LEDGER_WRITE_UNAVAILABLE",
    "UNKNOWN",
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
    "tests/path_governance/test_p1_7_16_policy_context_bridge.py",
)

_FIXTURE_LABEL = ProjectionSourceLabel.DEV_FIXTURE
_FIXTURE_META = {"fixture": "DEV_FIXTURE"}


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.projection_contract"),
    )


def _path_identity():
    return build_path_identity(
        "src/example.py",
        path_kind=PathKind.REPO_RELATIVE,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _source_identity():
    return build_source_identity(
        source_kind=SourceKind.LOCAL_FILE,
        origin=SourceOrigin.OPERATOR,
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )


def _sample_record(**overrides) -> PathGovernanceProjectionRecord:
    base = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "path identity backend available",
        subject_refs=[{"module": "agentic_runtime.path_governance.path_identity"}],
        source_label=ProjectionSourceLabel.LIVE,
    )
    if not overrides:
        return base
    data = base.to_canonical_dict()
    data.update(overrides)
    return PathGovernanceProjectionRecord.from_dict(data)


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert pg.PathGovernanceCapabilityKind is PathGovernanceCapabilityKind
    assert pg.PathGovernanceProjectionEventKind is PathGovernanceProjectionEventKind
    assert pg.PathGovernanceProjectionRecord is PathGovernanceProjectionRecord
    assert pg.PathGovernanceReadModel is PathGovernanceReadModel
    assert pg.PathGovernanceProjectionEvent is PathGovernanceProjectionEvent
    assert pg.PathGovernanceApiEnvelope is PathGovernanceApiEnvelope
    assert pg.build_path_governance_projection_record is build_path_governance_projection_record
    assert pg.build_path_governance_read_model is build_path_governance_read_model
    assert pg.build_path_governance_projection_event is build_path_governance_projection_event
    assert pg.build_path_governance_api_envelope is build_path_governance_api_envelope
    assert pg.build_default_path_governance_capability_projection is (
        build_default_path_governance_capability_projection
    )


def test_capability_kind_has_required_values() -> None:
    values = {kind.value for kind in PathGovernanceCapabilityKind}
    assert values == _REQUIRED_CAPABILITY_KINDS


def test_projection_event_kind_has_required_values() -> None:
    values = {kind.value for kind in PathGovernanceProjectionEventKind}
    assert values == _REQUIRED_EVENT_KINDS


def test_projection_record_builds_deterministically() -> None:
    record_a = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "path identity available",
        subject_refs=[{"module": "agentic_runtime.path_governance.path_identity"}],
    )
    record_b = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "path identity available",
        subject_refs=[{"module": "agentic_runtime.path_governance.path_identity"}],
    )
    assert record_a.record_id == record_b.record_id
    assert record_a.record_hash == record_b.record_hash


def test_read_model_builds_deterministically() -> None:
    records = [
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.PATH_IDENTITY,
            ProjectionSourceLabel.LIVE,
            "path identity available",
        ),
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.SOURCE_IDENTITY,
            ProjectionSourceLabel.LIVE,
            "source identity available",
        ),
    ]
    model_a = build_path_governance_read_model(records)
    model_b = build_path_governance_read_model(list(reversed(records)))
    assert model_a.read_model_id == model_b.read_model_id
    assert model_a.read_model_hash == model_b.read_model_hash


def test_projection_event_builds_deterministically() -> None:
    record = _sample_record()
    read_model = build_path_governance_read_model([record])
    event_a = build_path_governance_projection_event(
        PathGovernanceProjectionEventKind.CAPABILITY_PROJECTED,
        records=[record],
        read_model=read_model,
        summary="capability projected",
    )
    event_b = build_path_governance_projection_event(
        PathGovernanceProjectionEventKind.CAPABILITY_PROJECTED,
        records=[record],
        read_model=read_model,
        summary="capability projected",
    )
    assert event_a.event_id == event_b.event_id
    assert event_a.event_hash == event_b.event_hash


def test_api_envelope_builds_deterministically() -> None:
    envelope_a = build_default_path_governance_capability_projection()
    envelope_b = build_default_path_governance_capability_projection()
    assert envelope_a.envelope_id == envelope_b.envelope_id
    assert envelope_a.envelope_hash == envelope_b.envelope_hash


def test_default_capability_projection_includes_p1_7_0_to_p1_7_17() -> None:
    envelope = build_default_path_governance_capability_projection()
    assert envelope.read_model is not None
    kinds = {record.capability_kind for record in envelope.read_model.records}
    expected = {
        PathGovernanceCapabilityKind.PATH_GOVERNANCE_FOUNDATION,
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        PathGovernanceCapabilityKind.SOURCE_IDENTITY,
        PathGovernanceCapabilityKind.SOURCE_TRUST_TAXONOMY,
        PathGovernanceCapabilityKind.TRUSTED_ROOT_REGISTRY,
        PathGovernanceCapabilityKind.PATH_NORMALIZATION_ESCAPE_DETECTION,
        PathGovernanceCapabilityKind.PATH_AUTHORITY_SCOPE,
        PathGovernanceCapabilityKind.UNTRUSTED_CONTENT_BOUNDARY,
        PathGovernanceCapabilityKind.SOURCE_PROVENANCE_EVIDENCE_BINDING,
        PathGovernanceCapabilityKind.PATH_SOURCE_RISK_CLASSIFICATION,
        PathGovernanceCapabilityKind.PATH_GOVERNANCE_RESOLVER_SHADOW,
        PathGovernanceCapabilityKind.SOURCE_TRUST_RESOLVER_SHADOW,
        PathGovernanceCapabilityKind.CONFLICT_PRECEDENCE_SHADOW,
        PathGovernanceCapabilityKind.PATH_RESOLUTION_TRACE_HOOK,
        PathGovernanceCapabilityKind.PATH_VIOLATION_DRIFT_TRACE_HOOK,
        PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS,
        PathGovernanceCapabilityKind.POLICY_CONTEXT_BRIDGE,
        PathGovernanceCapabilityKind.PROJECTION_API_EVENT_CONTRACT,
    }
    assert expected.issubset(kinds)


def test_cli_tui_binding_is_unavailable() -> None:
    envelope = build_default_path_governance_capability_projection()
    assert envelope.read_model is not None
    cli_records = [
        record
        for record in envelope.read_model.records
        if record.capability_kind is PathGovernanceCapabilityKind.CLI_TUI_BINDING
    ]
    assert len(cli_records) == 1
    cli_record = cli_records[0]
    assert cli_record.state_label is ProjectionSourceLabel.UNAVAILABLE
    assert cli_record.unavailable_reason is not None
    assert "P1.7.18" in cli_record.unavailable_reason


def test_shell_binding_is_unavailable_or_honestly_not_implemented() -> None:
    envelope = build_default_path_governance_capability_projection()
    shell = envelope.unavailable_bindings.get("shell", {})
    assert shell.get("status") == ProjectionSourceLabel.UNAVAILABLE.value
    assert "P1.7.17" in shell.get("reason", "")


def test_http_server_is_unavailable_or_honestly_not_implemented() -> None:
    envelope = build_default_path_governance_capability_projection()
    http = envelope.unavailable_bindings.get("http_server", {})
    assert http.get("status") == ProjectionSourceLabel.UNAVAILABLE.value
    assert "P1.7.17" in http.get("reason", "")


def test_no_fake_live_for_dev_fixture_scenarios() -> None:
    record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS,
        ProjectionSourceLabel.DEV_FIXTURE,
        "harness fixture scenario",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_FIXTURE_META,
    )
    assert record.state_label is ProjectionSourceLabel.DEV_FIXTURE
    assert record.source_label is ProjectionSourceLabel.DEV_FIXTURE
    assert record.state_label is not ProjectionSourceLabel.LIVE


def test_no_fake_trace_verified() -> None:
    envelope = build_default_path_governance_capability_projection()
    assert envelope.read_model is not None
    for record in envelope.read_model.records:
        assert record.state_label is not ProjectionSourceLabel.TRACE_VERIFIED
    assert envelope.read_model.trace_verified_count == 0


def test_unavailable_records_require_unavailable_reason() -> None:
    with pytest.raises(Exception) as exc_info:
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.CLI_TUI_BINDING,
            ProjectionSourceLabel.UNAVAILABLE,
            "cli unavailable",
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        )
    assert "unavailable_reason" in str(exc_info.value).lower()


def test_read_model_count_fields_are_correct() -> None:
    records = [
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.PATH_IDENTITY,
            ProjectionSourceLabel.LIVE,
            "live capability",
        ),
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS,
            ProjectionSourceLabel.DEV_FIXTURE,
            "fixture harness",
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.CLI_TUI_BINDING,
            ProjectionSourceLabel.UNAVAILABLE,
            "cli unavailable",
            unavailable_reason=CLI_TUI_BINDING_UNAVAILABLE_REASON,
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        ),
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.UNKNOWN,
            ProjectionSourceLabel.ERROR,
            "error capability",
            source_label=ProjectionSourceLabel.ERROR,
        ),
    ]
    read_model = build_path_governance_read_model(records)
    assert read_model.capability_count == 4
    assert read_model.live_count == 1
    assert read_model.dev_fixture_count == 1
    assert read_model.unavailable_count == 1
    assert read_model.error_count == 1
    assert read_model.trace_verified_count == 0
    assert read_model.simulated_count == 0


def test_overall_state_is_deterministic() -> None:
    records = [
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.PATH_IDENTITY,
            ProjectionSourceLabel.LIVE,
            "live",
        ),
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.CLI_TUI_BINDING,
            ProjectionSourceLabel.UNAVAILABLE,
            "unavailable",
            unavailable_reason=CLI_TUI_BINDING_UNAVAILABLE_REASON,
            source_label=ProjectionSourceLabel.UNAVAILABLE,
        ),
    ]
    model_a = build_path_governance_read_model(records)
    model_b = build_path_governance_read_model(list(reversed(records)))
    assert model_a.overall_state == model_b.overall_state
    assert model_a.overall_state is ProjectionSourceLabel.LIVE

    error_records = records + [
        build_path_governance_projection_record(
            PathGovernanceCapabilityKind.UNKNOWN,
            ProjectionSourceLabel.ERROR,
            "error",
            source_label=ProjectionSourceLabel.ERROR,
        ),
    ]
    error_model = build_path_governance_read_model(error_records)
    assert error_model.overall_state is ProjectionSourceLabel.ERROR


def test_projection_event_does_not_emit_global_trace() -> None:
    source = _module_source()
    for snippet in (
        "trace_writer",
        "emit_trace",
        "from agentic_runtime.trace",
        "write_trace",
    ):
        assert snippet not in source


def test_api_envelope_does_not_start_server() -> None:
    source = _module_source()
    for snippet in (
        "FastAPI",
        "Flask",
        "uvicorn",
        "http.server",
        "aiohttp",
        "starlette",
    ):
        assert snippet not in source


def test_api_envelope_does_not_register_route() -> None:
    source = _module_source()
    for snippet in (
        "@app.route",
        "@router.",
        "add_api_route",
        "register_route",
        "APIRouter",
    ):
        assert snippet not in source


def test_projection_can_reference_policy_context_bridge() -> None:
    packet = build_path_policy_context_packet(
        path_identity=_path_identity(),
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.POLICY_CONTEXT_BRIDGE,
        ProjectionSourceLabel.LIVE,
        "policy context bridge projected",
        subject_refs=[{
            "ref_id": packet.packet_id,
            "ref_hash": packet.packet_hash,
            "kind": "PathPolicyContextPacket",
        }],
        source_label=ProjectionSourceLabel.LIVE,
    )
    assert record.subject_refs[0]["kind"] == "PathPolicyContextPacket"
    assert isinstance(packet, PathPolicyContextPacket)


def test_projection_can_reference_harness_result() -> None:
    result = run_path_governance_harness_suite()
    record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS,
        ProjectionSourceLabel.DEV_FIXTURE,
        "harness result projected",
        subject_refs=[{
            "ref_id": result.result_id,
            "ref_hash": result.result_hash,
            "kind": "PathGovernanceHarnessRunResult",
        }],
        source_label=_FIXTURE_LABEL,
    )
    assert record.subject_refs[0]["kind"] == "PathGovernanceHarnessRunResult"


def test_projection_can_reference_trace_payload() -> None:
    payload = build_path_resolution_trace_payload(
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_RESOLUTION_TRACE_HOOK,
        ProjectionSourceLabel.LIVE,
        "trace payload projected",
        subject_refs=[{
            "ref_id": payload.payload_id,
            "ref_hash": payload.payload_hash,
            "kind": "PathResolutionTracePayload",
        }],
    )
    assert record.subject_refs[0]["kind"] == "PathResolutionTracePayload"


def test_projection_can_reference_violation_drift_payload() -> None:
    payload = build_path_violation_trace_payload(
        source_label=_FIXTURE_LABEL,
        metadata=_FIXTURE_META,
    )
    record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_VIOLATION_DRIFT_TRACE_HOOK,
        ProjectionSourceLabel.LIVE,
        "violation payload projected",
        subject_refs=[{
            "ref_id": payload.payload_id,
            "ref_hash": payload.payload_hash,
            "kind": "PathViolationTracePayload",
        }],
    )
    assert record.subject_refs[0]["kind"] == "PathViolationTracePayload"


def test_changed_record_changes_read_model_hash() -> None:
    record_a = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "summary a",
    )
    record_b = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "summary b",
    )
    model_a = build_path_governance_read_model([record_a])
    model_b = build_path_governance_read_model([record_b])
    assert model_a.read_model_hash != model_b.read_model_hash


def test_changed_read_model_changes_envelope_hash() -> None:
    record_a = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "summary a",
    )
    record_b = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "summary b",
    )
    envelope_a = build_path_governance_api_envelope(records=[record_a], events=())
    envelope_b = build_path_governance_api_envelope(records=[record_b], events=())
    assert envelope_a.envelope_hash != envelope_b.envelope_hash


def test_unknown_fields_are_rejected() -> None:
    record = _sample_record()
    payload = record.to_canonical_dict()
    payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as exc_info:
        PathGovernanceProjectionRecord.from_dict(payload)
    assert exc_info.value.code.value == "UNKNOWN_FIELD"


def test_source_labels_are_preserved() -> None:
    live_record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.LIVE,
        "live capability",
        source_label=ProjectionSourceLabel.LIVE,
    )
    fixture_record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_GOVERNANCE_TEST_HARNESS,
        ProjectionSourceLabel.DEV_FIXTURE,
        "fixture capability",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    assert live_record.source_label is ProjectionSourceLabel.LIVE
    assert fixture_record.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_api_envelope_is_json_safe() -> None:
    envelope = build_default_path_governance_capability_projection()
    payload = envelope.to_canonical_dict()
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["contract_name"] == envelope.contract_name
    assert decoded["envelope_hash"] == envelope.envelope_hash


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


def test_p1_7_0_to_p1_7_16_regression_still_pass() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *_P1_7_REGRESSION_FILES,
            "-k",
            "not regression_still_pass",
            "-q",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr

"""P1.7.18 — Path Governance CLI/TUI Binding tests."""
from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys

import pytest

from agentic_runtime.path_governance import (
    PathGovernanceApiEnvelope,
    PathGovernanceCapabilityKind,
    PathGovernanceCliBindingMode,
    PathGovernanceCliCommandKind,
    PathGovernanceCliOutputFormat,
    PathGovernanceCliRenderedLine,
    PathGovernanceCliRenderLineLevel,
    PathGovernanceCliRequest,
    PathGovernanceCliResponse,
    PathGovernanceCliSideEffects,
    PathGovernanceProjectionRecord,
    PathGovernanceReadModel,
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    build_default_path_governance_capability_projection,
    build_path_governance_cli_request,
    build_path_governance_projection_record,
    build_path_governance_read_model,
    handle_path_governance_cli_request,
    render_path_governance_capability_table,
    render_path_governance_cli_response,
    render_path_governance_json_payload,
    render_path_governance_status_text,
)

_REQUIRED_COMMAND_KINDS = {
    "STATUS",
    "CAPABILITIES",
    "READ_MODEL",
    "API_ENVELOPE",
    "EVENTS",
    "HARNESS_SUMMARY",
    "POLICY_CONTEXT_SUMMARY",
    "TRACE_HOOK_SUMMARY",
    "VIOLATION_DRIFT_SUMMARY",
    "UNAVAILABLE_BINDINGS",
    "UNKNOWN",
}

_REQUIRED_OUTPUT_FORMATS = {"TEXT", "JSON", "TABLE", "TUI_TEXT", "UNKNOWN"}

_REQUIRED_BINDING_MODES = {
    "READ_ONLY",
    "PROJECTION_ONLY",
    "DEV_FIXTURE_ALLOWED",
    "ERROR",
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
    "tests/path_governance/test_p1_7_17_projection_api_event_contract.py",
)

_FIXTURE_LABEL = ProjectionSourceLabel.DEV_FIXTURE


def _module_source() -> str:
    return inspect.getsource(
        importlib.import_module("agentic_runtime.path_governance.cli_binding"),
    )


def _default_envelope() -> PathGovernanceApiEnvelope:
    return build_default_path_governance_capability_projection(
        cli_binding_available=True,
    )


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert pg.PathGovernanceCliCommandKind is PathGovernanceCliCommandKind
    assert pg.PathGovernanceCliOutputFormat is PathGovernanceCliOutputFormat
    assert pg.PathGovernanceCliBindingMode is PathGovernanceCliBindingMode
    assert pg.PathGovernanceCliSideEffects is PathGovernanceCliSideEffects
    assert pg.PathGovernanceCliRequest is PathGovernanceCliRequest
    assert pg.PathGovernanceCliRenderedLine is PathGovernanceCliRenderedLine
    assert pg.PathGovernanceCliResponse is PathGovernanceCliResponse
    assert pg.build_path_governance_cli_request is build_path_governance_cli_request
    assert pg.render_path_governance_status_text is render_path_governance_status_text
    assert pg.render_path_governance_capability_table is render_path_governance_capability_table
    assert pg.render_path_governance_json_payload is render_path_governance_json_payload
    assert pg.render_path_governance_cli_response is render_path_governance_cli_response
    assert pg.handle_path_governance_cli_request is handle_path_governance_cli_request


def test_command_kind_has_required_values() -> None:
    values = {item.value for item in PathGovernanceCliCommandKind}
    assert _REQUIRED_COMMAND_KINDS <= values


def test_output_format_has_required_values() -> None:
    values = {item.value for item in PathGovernanceCliOutputFormat}
    assert _REQUIRED_OUTPUT_FORMATS <= values


def test_binding_mode_has_required_values() -> None:
    values = {item.value for item in PathGovernanceCliBindingMode}
    assert _REQUIRED_BINDING_MODES <= values


def test_side_effects_default_false() -> None:
    side_effects = PathGovernanceCliSideEffects()
    assert side_effects.policy_called is False
    assert side_effects.approval_created is False
    assert side_effects.ledger_written is False
    assert side_effects.global_trace_written is False
    assert side_effects.runtime_mutated is False
    assert side_effects.enforcement_triggered is False
    assert side_effects.source_mutated is False
    assert side_effects.prompt_filtered is False
    assert side_effects.memory_written is False
    assert side_effects.tool_blocked is False


def test_cli_request_builds_deterministically() -> None:
    first = build_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.STATUS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    second = build_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.STATUS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert first.request_id == second.request_id
    assert first.request_hash == second.request_hash


def test_rendered_line_builds_deterministically() -> None:
    first = PathGovernanceCliRenderedLine.from_dict({
        "line_id": "",
        "level": "INFO",
        "text": "hello",
        "source_label": "LIVE",
    })
    second = PathGovernanceCliRenderedLine.from_dict({
        "line_id": "",
        "level": "INFO",
        "text": "hello",
        "source_label": "LIVE",
    })
    assert first.line_id == second.line_id
    assert first.line_hash == second.line_hash


def test_cli_response_builds_deterministically() -> None:
    request = build_path_governance_cli_request()
    first = render_path_governance_cli_response(request=request)
    second = render_path_governance_cli_response(request=request)
    assert first.response_id == second.response_id
    assert first.response_hash == second.response_hash


def test_status_command_renders_text_output() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.STATUS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert response.rendered_output
    assert "capability_count=" in response.rendered_output
    assert response.side_effects.policy_called is False


def test_capabilities_command_renders_capability_records() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.CAPABILITIES,
        output_format=PathGovernanceCliOutputFormat.TABLE,
    )
    assert "PATH_IDENTITY" in response.rendered_output
    assert "state_label" in response.rendered_output.lower() or "| LIVE |" in response.rendered_output


def test_read_model_command_renders_json_safe_payload() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.READ_MODEL,
        output_format=PathGovernanceCliOutputFormat.JSON,
    )
    payload = dict(response.json_payload)
    json.dumps(payload)
    assert "read_model" in payload


def test_api_envelope_command_renders_json_safe_payload() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.API_ENVELOPE,
        output_format=PathGovernanceCliOutputFormat.JSON,
    )
    payload = dict(response.json_payload)
    json.dumps(payload)
    assert "api_envelope" in payload
    assert payload["api_envelope"]["contract_name"]


def test_events_command_renders_event_contracts() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.EVENTS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert response.rendered_output
    assert "READ_MODEL_CREATED" in response.rendered_output
    assert response.side_effects.global_trace_written is False


def test_unavailable_command_renders_unavailable_reasons() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    text = response.rendered_output
    assert "shell" in text.lower() or "http_server" in text
    assert "policy_runtime" in text or "policy" in text.lower()
    assert "ledger" in text.lower()
    assert "enforcement" in text.lower()


def test_harness_summary_command_renders_read_only_summary() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.HARNESS_SUMMARY,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert "PATH_GOVERNANCE_TEST_HARNESS" in response.rendered_output


def test_policy_context_summary_command_renders_read_only_summary() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.POLICY_CONTEXT_SUMMARY,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert "POLICY_CONTEXT_BRIDGE" in response.rendered_output
    assert response.side_effects.policy_called is False


def test_trace_hook_summary_command_renders_read_only_summary() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.TRACE_HOOK_SUMMARY,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert "PATH_RESOLUTION_TRACE_HOOK" in response.rendered_output
    assert response.side_effects.ledger_written is False
    assert response.side_effects.global_trace_written is False


def test_violation_drift_summary_command_renders_read_only_summary() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.VIOLATION_DRIFT_SUMMARY,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert "PATH_VIOLATION_DRIFT_TRACE_HOOK" in response.rendered_output
    assert response.side_effects.runtime_mutated is False
    assert response.side_effects.enforcement_triggered is False


def test_cli_response_includes_source_labels() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.STATUS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    assert response.source_label is ProjectionSourceLabel.LIVE
    assert response.rendered_lines
    assert any(
        line.source_label is ProjectionSourceLabel.LIVE
        for line in response.rendered_lines
    )
    payload = dict(response.json_payload)
    assert payload["source_label"] == ProjectionSourceLabel.LIVE.value


def test_cli_response_preserves_unavailable_reasons() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS,
        output_format=PathGovernanceCliOutputFormat.JSON,
    )
    reasons = list(response.unavailable_reasons)
    assert reasons
    assert all("reason" in item and item["reason"] for item in reasons)


def test_no_fake_live_for_dev_fixture() -> None:
    record = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.PATH_IDENTITY,
        ProjectionSourceLabel.DEV_FIXTURE,
        "fixture capability",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )
    read_model = build_path_governance_read_model([record])
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.CAPABILITIES,
        output_format=PathGovernanceCliOutputFormat.TEXT,
        read_model=read_model,
    )
    assert "DEV_FIXTURE" in response.rendered_output
    assert response.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_no_fake_trace_verified() -> None:
    envelope = _default_envelope()
    assert envelope.read_model.trace_verified_count == 0
    response = handle_path_governance_cli_request(api_envelope=envelope)
    payload = dict(response.json_payload)
    assert payload.get("source_label") != ProjectionSourceLabel.TRACE_VERIFIED.value
    assert "TRACE_VERIFIED" not in response.rendered_output or "trace_verified=0" in response.rendered_output


def test_json_output_is_json_safe() -> None:
    response = handle_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.READ_MODEL,
        output_format=PathGovernanceCliOutputFormat.JSON,
    )
    encoded = json.dumps(dict(response.json_payload))
    decoded = json.loads(encoded)
    assert decoded["command_kind"] == PathGovernanceCliCommandKind.READ_MODEL.value


def test_text_output_is_deterministic() -> None:
    request = build_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.STATUS,
        output_format=PathGovernanceCliOutputFormat.TEXT,
    )
    first = render_path_governance_cli_response(request=request)
    second = render_path_governance_cli_response(request=request)
    assert first.rendered_output == second.rendered_output


def test_table_output_is_deterministic() -> None:
    request = build_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.CAPABILITIES,
        output_format=PathGovernanceCliOutputFormat.TABLE,
    )
    first = render_path_governance_cli_response(request=request)
    second = render_path_governance_cli_response(request=request)
    assert first.rendered_output == second.rendered_output


def test_changed_read_model_changes_response_hash() -> None:
    envelope = _default_envelope()
    request = build_path_governance_cli_request()
    baseline = render_path_governance_cli_response(
        request=request,
        api_envelope=envelope,
    )
    extra = build_path_governance_projection_record(
        PathGovernanceCapabilityKind.UNKNOWN,
        ProjectionSourceLabel.UNAVAILABLE,
        "extra",
        unavailable_reason="UNAVAILABLE: test",
        source_label=ProjectionSourceLabel.UNAVAILABLE,
    )
    changed_records = tuple(envelope.read_model.records) + (extra,)
    changed_read_model = build_path_governance_read_model(changed_records)
    changed = render_path_governance_cli_response(
        request=request,
        read_model=changed_read_model,
    )
    assert changed.response_hash != baseline.response_hash


def test_changed_api_envelope_changes_response_hash() -> None:
    request = build_path_governance_cli_request()
    first_envelope = _default_envelope()
    second_envelope = build_default_path_governance_capability_projection(
        cli_binding_available=True,
        metadata={"marker": "changed"},
    )
    first = render_path_governance_cli_response(
        request=request,
        api_envelope=first_envelope,
    )
    second = render_path_governance_cli_response(
        request=request,
        api_envelope=second_envelope,
    )
    assert first.response_hash != second.response_hash


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(PathGovernanceUnknownFieldError) as exc:
        PathGovernanceCliRequest.from_dict({
            "request_id": "x",
            "command_kind": "STATUS",
            "output_format": "TEXT",
            "shadow_authority_grant": True,
        })
    assert "UNKNOWN_FIELD" in str(exc.value.code)


def test_side_effects_all_false_in_response() -> None:
    response = handle_path_governance_cli_request()
    effects = response.side_effects
    assert effects.policy_called is False
    assert effects.approval_created is False
    assert effects.ledger_written is False
    assert effects.global_trace_written is False
    assert effects.runtime_mutated is False
    assert effects.enforcement_triggered is False
    assert effects.source_mutated is False
    assert effects.prompt_filtered is False
    assert effects.memory_written is False
    assert effects.tool_blocked is False


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
        "from agentic_runtime.memory",
        "from agentic_runtime.prompts",
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


def test_no_subprocess_or_environment_secret_access() -> None:
    source = _module_source()
    for snippet in (
        "subprocess",
        "os.environ",
    ):
        assert snippet not in source


def test_actual_cli_invocation_works_if_registered() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_runtime.cli",
            "path-governance",
            "status",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "LIVE" in proc.stdout or "capability_count=" in proc.stdout
    assert "policy_called" not in proc.stdout


def test_p1_7_0_to_p1_7_17_regression_still_pass() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *_P1_7_REGRESSION_FILES, "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_tui_text_output_is_deterministic() -> None:
    request = build_path_governance_cli_request(
        command_kind=PathGovernanceCliCommandKind.CAPABILITIES,
        output_format=PathGovernanceCliOutputFormat.TUI_TEXT,
    )
    first = render_path_governance_cli_response(request=request)
    second = render_path_governance_cli_response(request=request)
    assert first.rendered_output == second.rendered_output
    assert first.rendered_output.startswith("+")


def test_status_text_helper_returns_lines() -> None:
    envelope = _default_envelope()
    text, lines = render_path_governance_status_text(api_envelope=envelope)
    assert text
    assert lines
    assert lines[0].level is PathGovernanceCliRenderLineLevel.HEADER


def test_capability_table_helper_returns_rows() -> None:
    envelope = _default_envelope()
    text, lines = render_path_governance_capability_table(api_envelope=envelope)
    assert "PATH_IDENTITY" in text
    assert any(line.level is PathGovernanceCliRenderLineLevel.ROW for line in lines)


def test_json_payload_helper_returns_dict() -> None:
    envelope = _default_envelope()
    payload = render_path_governance_json_payload(
        api_envelope=envelope,
        command_kind=PathGovernanceCliCommandKind.API_ENVELOPE,
    )
    json.dumps(payload)
    assert "api_envelope" in payload

from __future__ import annotations

import json
from dataclasses import fields, replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FORBIDDEN_FLOW_CLI_COMMAND_KINDS,
    FlowCliCommandKind,
    FlowCliOutputFormat,
    FlowCliRequest,
    FlowCliSideEffects,
    handle_flow_cli_request,
    render_flow_cli_response,
)
from agentic_runtime.cli import main as cli_main


def test_all_flow_cli_commands_render_deterministically() -> None:
    for kind in FlowCliCommandKind:
        first = handle_flow_cli_request(FlowCliRequest(command_kind=kind))
        second = handle_flow_cli_request(FlowCliRequest(command_kind=kind))

        assert first.exit_code == 0
        assert first.response_hash == second.response_hash
        assert first.rendered_lines == second.rendered_lines
        assert first.json_payload == second.json_payload


def test_flow_cli_side_effects_all_false_and_fail_closed() -> None:
    response = handle_flow_cli_request(
        FlowCliRequest(command_kind=FlowCliCommandKind.INSPECT)
    )

    for effect_field in fields(response.side_effects):
        assert getattr(response.side_effects, effect_field.name) is False
    with pytest.raises(AurelFlowValidationError):
        FlowCliSideEffects(executes_nodes=True)
    with pytest.raises(AurelFlowValidationError):
        replace(response.side_effects, writes_trace=True)


def test_flow_cli_command_kinds_are_closed_world_read_only() -> None:
    kinds = {kind.value for kind in FlowCliCommandKind}

    assert kinds == {"DEMO", "INSPECT", "TIMELINE", "WIRING", "PROTOCOL", "SEAL"}
    for forbidden in FORBIDDEN_FLOW_CLI_COMMAND_KINDS:
        assert forbidden not in kinds, forbidden


def test_flow_cli_json_payloads_are_valid_canonical_json() -> None:
    for kind in FlowCliCommandKind:
        response = handle_flow_cli_request(
            FlowCliRequest(command_kind=kind, output_format=FlowCliOutputFormat.JSON)
        )
        payload = json.loads(response.json_payload)
        assert isinstance(payload, dict)
        assert render_flow_cli_response(response) == response.json_payload


def test_flow_cli_text_shows_truth_and_unavailable_reasons() -> None:
    inspect_text = render_flow_cli_response(
        handle_flow_cli_request(FlowCliRequest(command_kind=FlowCliCommandKind.INSPECT))
    )
    seal_text = render_flow_cli_response(
        handle_flow_cli_request(FlowCliRequest(command_kind=FlowCliCommandKind.SEAL))
    )

    assert "projection is not execution" in inspect_text
    assert "live=False trace_verified=False execution_available=False" in inspect_text
    assert "not TRACE_VERIFIED" in seal_text
    assert "rust_core_active=False" in seal_text


def test_flow_cli_never_claims_live_or_trace_verified() -> None:
    for kind in FlowCliCommandKind:
        response = handle_flow_cli_request(FlowCliRequest(command_kind=kind))
        text = render_flow_cli_response(response)
        assert "live=True" not in text
        assert "trace_verified=True" not in text
        assert response.truth_label.value not in ("LIVE", "TRACE_VERIFIED")


def test_cli_main_flow_inspect_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main(["flow", "inspect"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "flow inspect" in out
    assert "READ_MODEL_ONLY" in out


def test_cli_main_flow_seal_json_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main(["flow", "seal", "--base-p3", "--json"])
    out = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(out)
    assert payload["result"]["seal"]["trace_verified"] is False
    assert payload["result"]["seal"]["live"] is False
    assert payload["result"]["seal"]["boundary"]["execution_available"] is False


def test_flow_cli_has_no_control_subcommands() -> None:
    for forbidden_args in (
        ["flow", "execute"],
        ["flow", "approve"],
        ["flow", "resume"],
        ["flow", "stop"],
        ["flow", "retry"],
        ["flow", "rollback"],
    ):
        with pytest.raises(SystemExit) as excinfo:
            cli_main(forbidden_args)
        assert excinfo.value.code == 2  # argparse rejects unknown subcommand

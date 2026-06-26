"""CLI commands for P1.7.18 Path Governance CLI/TUI Binding. Read-only projection surface."""
from __future__ import annotations

import argparse
import json

from ..path_governance.cli_binding import (
    PathGovernanceCliCommandKind,
    PathGovernanceCliOutputFormat,
    handle_path_governance_cli_request,
)


def _output_format_from_args(args: argparse.Namespace) -> PathGovernanceCliOutputFormat:
    if getattr(args, "tui", False):
        return PathGovernanceCliOutputFormat.TUI_TEXT
    if getattr(args, "table", False):
        return PathGovernanceCliOutputFormat.TABLE
    if getattr(args, "json", False):
        return PathGovernanceCliOutputFormat.JSON
    return PathGovernanceCliOutputFormat.TEXT


def _print_response(response: object, *, as_json: bool) -> None:
    from ..path_governance.cli_binding import PathGovernanceCliResponse

    if not isinstance(response, PathGovernanceCliResponse):
        raise TypeError("response must be a PathGovernanceCliResponse")
    if as_json:
        print(json.dumps(dict(response.json_payload), sort_keys=True, separators=(",", ":")))
    else:
        print(response.rendered_output)


def _run_command(
    args: argparse.Namespace,
    command_kind: PathGovernanceCliCommandKind,
    *,
    default_json: bool = False,
) -> int:
    output_format = _output_format_from_args(args)
    if default_json and not getattr(args, "json", False) and not getattr(args, "table", False):
        output_format = PathGovernanceCliOutputFormat.JSON
    try:
        response = handle_path_governance_cli_request(
            command_kind=command_kind,
            output_format=output_format,
        )
    except Exception as exc:
        if getattr(args, "json", False) or default_json:
            print(json.dumps({
                "error": f"{type(exc).__name__}: {exc}",
                "source": "ERROR",
            }, sort_keys=True))
        else:
            print(f"ERROR: path governance CLI failed: {type(exc).__name__}: {exc}")
        return 2
    _print_response(response, as_json=output_format is PathGovernanceCliOutputFormat.JSON)
    return 0


def cmd_path_governance_status(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.STATUS)


def cmd_path_governance_capabilities(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.CAPABILITIES)


def cmd_path_governance_read_model(args: argparse.Namespace) -> int:
    return _run_command(
        args,
        PathGovernanceCliCommandKind.READ_MODEL,
        default_json=True,
    )


def cmd_path_governance_api_envelope(args: argparse.Namespace) -> int:
    return _run_command(
        args,
        PathGovernanceCliCommandKind.API_ENVELOPE,
        default_json=True,
    )


def cmd_path_governance_events(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.EVENTS)


def cmd_path_governance_unavailable(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.UNAVAILABLE_BINDINGS)


def cmd_path_governance_harness_summary(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.HARNESS_SUMMARY)


def cmd_path_governance_policy_context_summary(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.POLICY_CONTEXT_SUMMARY)


def cmd_path_governance_trace_hook_summary(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.TRACE_HOOK_SUMMARY)


def cmd_path_governance_violation_drift_summary(args: argparse.Namespace) -> int:
    return _run_command(args, PathGovernanceCliCommandKind.VIOLATION_DRIFT_SUMMARY)

"""CLI commands for P1.9.28 Output Passport read-only inspect binding."""
from __future__ import annotations

import argparse
import json

from ..output_passport.integration_tail import (
    build_output_passport_cli_binding_status,
    build_output_passport_projection_contract,
    build_output_passport_tui_binding_status,
    handle_output_passport_cli_inspect,
)


def cmd_output_passport_inspect(args: argparse.Namespace) -> int:
    result = handle_output_passport_cli_inspect(
        dev_fixture=args.dev_fixture,
    )
    if args.json or not args.text:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        for key in sorted(result):
            print(f"{key}: {result[key]}")
    return 0


def cmd_output_passport_projection(args: argparse.Namespace) -> int:
    contract = build_output_passport_projection_contract()
    payload = contract.to_canonical_dict()
    if args.json or not args.text:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"projection_status: {contract.projection_status.value}")
        print(f"contract_hash: {contract.contract_hash}")
        print(f"api_runtime: {contract.api_contract.runtime_status.value}")
        print(f"event_runtime: {contract.event_contract.runtime_status.value}")
    return 0


def cmd_output_passport_unavailable(args: argparse.Namespace) -> int:
    cli = build_output_passport_cli_binding_status()
    tui = build_output_passport_tui_binding_status()
    payload = {
        "cli_status": cli.status.value,
        "tui_status": tui.status.value,
        "tui_unavailable_reason": tui.unavailable_reason,
        "cli_command": cli.inspect_command.command_label,
        "read_only": cli.inspect_command.read_only,
    }
    if args.json or not args.text:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"cli: {cli.status.value}")
        print(f"tui: {tui.status.value} — {tui.unavailable_reason}")
    return 0

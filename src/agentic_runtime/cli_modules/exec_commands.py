"""Read-only AurelExec CLI commands (P4-EXEC-G status binding)."""

from __future__ import annotations

import argparse

from ..aurel_exec.exec_status import (
    build_exec_status_read_model,
    build_shell_binding_contract,
    handle_exec_cli_status,
)


def cmd_exec_status(_args: argparse.Namespace) -> int:
    contract = build_shell_binding_contract()
    if not contract.cli_wiring_available:
        raise RuntimeError("exec status CLI binding is unavailable")
    status = build_exec_status_read_model()
    response = handle_exec_cli_status(status)
    print(response.rendered_output)
    return 0

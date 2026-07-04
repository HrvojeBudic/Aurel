"""P4-EXEC-G CLI/Shell binding tests — read-only or unavailable with reason."""

from __future__ import annotations

import dataclasses
import json

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecCliCommandKind,
    build_exec_status_read_model,
    build_shell_binding_contract,
    handle_exec_cli_status,
)


def test_cli_status_binding_is_read_only_or_unavailable_with_reason():
    contract = build_shell_binding_contract()
    # the binding contract is read-only and its live CLI wiring is honestly
    # unavailable with a reason
    assert contract.read_only is True
    assert contract.cli_wiring_available is False
    assert contract.cli_wiring_unavailable_reason
    assert "P2 Shell" in contract.cli_wiring_unavailable_reason or (
        "flow-CLI" in contract.cli_wiring_unavailable_reason
    )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(contract, cli_wiring_available=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(contract, read_only=False)


def test_cli_command_vocabulary_is_closed_world_read_only():
    assert {kind.value for kind in ExecCliCommandKind} == {
        "STATUS",
        "COVERAGE",
        "HANDOFF",
        "SEAL",
    }
    for forbidden in (
        "SUBMIT", "RUN", "RETRY", "RECOVER", "ROLLBACK",
        "APPROVE", "MUTATE", "VERIFY", "ENFORCE", "EXECUTE",
    ):
        assert forbidden not in ExecCliCommandKind.__members__
    # a contract advertising a command outside the vocabulary is unconstructible
    contract = build_shell_binding_contract()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(contract, supported_commands=("STATUS", "SUBMIT"))


def test_status_rendering_is_deterministic_json_and_mutates_nothing():
    status = build_exec_status_read_model()
    response = handle_exec_cli_status(status)
    assert response.runtime_mutated is False
    assert response.executed is False
    payload = json.loads(response.rendered_output)
    assert payload["read_only"] is True
    assert payload["shell_ui_available"] is False
    assert set(payload["categories"]) == {name for name, _ in status.categories}
    # deterministic
    assert handle_exec_cli_status(status).rendered_output == response.rendered_output
    # mutation claims unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(response, runtime_mutated=True)


def test_shell_ui_is_unavailable():
    contract = build_shell_binding_contract()
    assert contract.shell_ui_available is False
    assert contract.shell_ui_unavailable_reason
    assert contract.api_server_available is False
    assert contract.react_frontend_available is False
    for boundary_field in (
        "shell_ui_available",
        "api_server_available",
        "react_frontend_available",
        "mutates_runtime",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(contract, **{boundary_field: True})
    status = build_exec_status_read_model()
    assert status.shell_ui_available is False


def test_cli_module_is_not_wired_into_agentic_runtime_cli():
    # honest wiring state: the agentic_runtime CLI has no exec command family
    from pathlib import Path

    import agentic_runtime.cli as runtime_cli

    source = Path(runtime_cli.__file__).read_text(encoding="utf-8")
    assert "aurel_exec" not in source
    assert "exec_status" not in source

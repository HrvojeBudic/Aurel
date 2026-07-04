"""Regression tests for terminal Shell operator canon sync with agent/STATE.md."""

from __future__ import annotations

from agentic_runtime.aurel_shell.terminal_shell_client import (
    OPERATOR_CANON_LAST_COMPLETED_PACK,
    OPERATOR_CANON_NEXT_NOT_STARTED,
    OPERATOR_CANON_NEXT_PACK,
    build_terminal_shell_read_model,
)
from agentic_runtime.cli_modules.shell_commands import format_shell_status_text


def test_operator_read_model_points_to_p211d_not_p210e() -> None:
    read_model = build_terminal_shell_read_model()

    assert read_model.next_pack_pointer == OPERATOR_CANON_NEXT_PACK == "P2.11-D"
    assert OPERATOR_CANON_LAST_COMPLETED_PACK == "P2.11-C"
    assert OPERATOR_CANON_NEXT_NOT_STARTED is True
    assert "P2.10-E is next and not implemented" not in read_model.limitations
    assert "P2.11-D is next and not implemented" in read_model.limitations


def test_shell_status_text_reflects_operator_canon() -> None:
    text = format_shell_status_text()

    assert "last_completed_pack: P2.11-C" in text
    assert "next_pack: P2.11-D" in text
    assert "next_pack_not_started: true" in text
    assert "P2.10-E is next and not implemented" not in text
    assert "p210e_not_started" not in text
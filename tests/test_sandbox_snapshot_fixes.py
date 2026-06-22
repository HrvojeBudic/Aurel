"""Regression tests for unique snapshot IDs and rollback reliability."""

from __future__ import annotations

import tempfile
from unittest.mock import patch

from agentic_runtime.core_types import VerifierResult
from agentic_runtime.file_patch import resolve_run_tests_command
from agentic_runtime.sandbox import UnsafeLocalSandbox
from agentic_runtime.verifier import StateVerifier
from tests.conftest import make_cmd


def test_snapshot_ids_are_unique_even_when_state_unchanged():
    sbx = UnsafeLocalSandbox(root=tempfile.mkdtemp())
    sbx.write_file("a.txt", "hello")

    s1 = sbx.snapshot()
    s2 = sbx.snapshot()

    assert s1 != s2
    assert len(sbx._snapshots) == 2


def test_rollback_restores_pre_write_state_with_unique_snapshots():
    sbx = UnsafeLocalSandbox(root=tempfile.mkdtemp())
    sbx.write_file("a.txt", "hello")
    snap_id = sbx.snapshot()

    sbx.write_file("a.txt", "world")
    sbx.rollback(snap_id)

    assert sbx.read_file("a.txt") == "hello"
    assert snap_id not in sbx._snapshots


def test_run_tests_verifier_uses_custom_command(write_kernel, card):
    kernel = write_kernel
    card.authority.write_paths = ["."]
    card.allowed_tools = ["run_tests", "read_file", "write_file"]
    kernel.sandbox.write_file("tests/custom_test.py", "assert True\n")
    kernel.verifier.test_integrity.snapshot()

    custom = ["python3", "-c", "import sys; sys.exit(0)"]
    cmd = make_cmd(card, "run_tests", {
        "test_file": "tests/custom_test.py",
        "command": custom,
    })
    res = kernel.runtime.submit(cmd, card)

    assert res.verifier.evidence.get("reexec_command") == custom


def test_patch_file_verifier_checks_real_post_state(write_kernel, card):
    kernel = write_kernel
    card.authority.write_paths = ["src/"]
    card.allowed_tools = ["patch_file", "read_file", "write_file"]
    kernel.sandbox.write_file("src/app.py", "alpha\nbeta\n")

    diff = (
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@ -1,2 +1,2 @@\n"
        " alpha\n"
        "-beta\n"
        "+gamma\n"
    )
    cmd = make_cmd(card, "patch_file", {"path": "src/app.py", "patch": diff})
    res = kernel.runtime.submit(cmd, card)

    assert res.ok
    assert kernel.sandbox.read_file("src/app.py") == "alpha\ngamma\n"


def test_failed_rollback_surfaces_rollback_failed(write_kernel, card):
    kernel = write_kernel
    card.authority.write_paths = ["src/"]
    cmd = make_cmd(card, "write_file", {"path": "src/x.py", "content": "ok\n"})
    fail = VerifierResult(False, "test_verifier", reason="forced verification failure")

    with patch.object(kernel.verifier, "verify", return_value=fail):
        with patch.object(kernel.sandbox, "rollback", side_effect=KeyError("broken")):
            res = kernel.runtime.submit(cmd, card)

    assert not res.ok
    assert res.verifier.code == "ROLLBACK_FAILED"
    assert "rollback failed" in res.verifier.reason.lower()


def test_resolve_run_tests_command_defaults_to_python3():
    assert resolve_run_tests_command({"test_file": "t.py"}) == ["python3", "t.py"]


def test_resolve_run_tests_command_preserves_custom_argv():
    custom = ["pytest", "-q", "tests/"]
    assert resolve_run_tests_command({"command": custom}) == custom

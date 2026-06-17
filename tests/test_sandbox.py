"""Sandbox confinement tests."""

import pytest

from agentic_runtime.sandbox import UnsafeLocalSandbox


def test_sandbox_rejects_traversal(tmp_path):
    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    sbx.write_file("src/inside.py", "ok")
    with pytest.raises(PermissionError):
        sbx.read_file("src/../outside.py")


def test_sandbox_rejects_absolute_path(tmp_path):
    sbx = UnsafeLocalSandbox(root=str(tmp_path))
    with pytest.raises(PermissionError):
        sbx.write_file("/etc/passwd", "nope")

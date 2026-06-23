"""P1.6.10H — Snapshot path traversal security tests."""
from __future__ import annotations

import os
import tempfile

import pytest

from agentic_runtime.sandbox import (
    SandboxMode,
    UnsafeLocalSandbox,
    create_sandbox,
)
try:
    from agentic_runtime.canonical_path import PathResolutionError  # noqa: F811
except ImportError:
    PathResolutionError = Exception  # fallback


@pytest.fixture
def sandbox_with_snapshots():
    """Create an UnsafeLocalSandbox with two snapshots containing test files."""
    root = tempfile.mkdtemp(prefix="snap_sec_test_")
    sb = create_sandbox(SandboxMode.UNSAFE_LOCAL, root=root, allow_unsafe=True)

    # Create some files
    test_dir = os.path.join(root, "logs")
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "result.txt"), "w") as f:
        f.write("ok")
    with open(os.path.join(root, "nested_file.txt"), "w") as f:
        f.write("nested")

    sb.snapshot()  # first snapshot
    sb.snapshot()  # second snapshot (contains the test files)

    # Build a fresh backend pointing to the same snapshots
    sb2 = create_sandbox(SandboxMode.UNSAFE_LOCAL, root=root, allow_unsafe=True)
    sb2._snapshots = dict(sb._snapshots)

    # Determine the snapshot ID that contains our test files (the second one)
    snap_ids = list(sb._snapshots.keys())
    assert len(snap_ids) == 2, f"expected 2 snapshots, got {len(snap_ids)}"

    yield sb2, snap_ids[1], root

    # Cleanup
    import shutil
    shutil.rmtree(root, ignore_errors=True)


class TestSnapshotPathTraversalFix:
    def test_normal_relative_snapshot_read_succeeds(self, sandbox_with_snapshots):
        """A normal relative path into a snapshot should succeed."""
        sb, snap_id, _ = sandbox_with_snapshots
        content = sb.read_snapshot_file(snap_id, "logs/result.txt")
        assert content == "ok"

    def test_parent_traversal_is_rejected(self, sandbox_with_snapshots):
        """A path with '../' parent traversal must be rejected."""
        sb, snap_id, _ = sandbox_with_snapshots
        with pytest.raises(PermissionError) as exc:
            sb.read_snapshot_file(snap_id, "../outside.txt")
        assert "path traversal" in str(exc.value).lower() or "escape" in str(exc.value).lower()

    def test_absolute_path_is_rejected(self, sandbox_with_snapshots):
        """An absolute path must be rejected."""
        sb, snap_id, _ = sandbox_with_snapshots
        with pytest.raises(PermissionError) as exc:
            sb.read_snapshot_file(snap_id, "/etc/passwd")
        assert "absolute" in str(exc.value).lower()

    def test_nested_traversal_is_rejected(self, sandbox_with_snapshots):
        """A path with nested parent traversal must be rejected."""
        sb, snap_id, _ = sandbox_with_snapshots
        with pytest.raises(PermissionError) as exc:
            sb.read_snapshot_file(snap_id, "logs/../../outside.txt")
        assert "path traversal" in str(exc.value).lower() or "escape" in str(exc.value).lower()

    def test_rejection_error_does_not_expose_host_paths(self, sandbox_with_snapshots):
        """Error messages must not expose internal host paths."""
        sb, snap_id, root = sandbox_with_snapshots
        try:
            sb.read_snapshot_file(snap_id, "../outside.txt")
        except PermissionError as e:
            msg = str(e)
            # The message should NOT contain the raw workspace path
            assert root not in msg, f"host path leaked in error: {msg}"
            assert "/etc/" not in msg

    def test_unknown_snapshot_id_raises_keyerror(self, sandbox_with_snapshots):
        """Reading from a nonexistent snapshot must raise KeyError."""
        sb, _, _ = sandbox_with_snapshots
        with pytest.raises(KeyError, match="unknown snapshot"):
            sb.read_snapshot_file("nonexistent-id", "foo.txt")

    def test_existing_verifier_behavior_still_works(self, sandbox_with_snapshots):
        """Valid nested reads that verifiers depend on still work."""
        sb, snap_id, _ = sandbox_with_snapshots
        content = sb.read_snapshot_file(snap_id, "nested_file.txt")
        assert content == "nested"

    def test_empty_path_is_rejected(self, sandbox_with_snapshots):
        """An empty relative path must be rejected."""
        sb, snap_id, _ = sandbox_with_snapshots
        with pytest.raises(PermissionError):
            sb.read_snapshot_file(snap_id, "")

    def test_dot_path_edge_case(self, sandbox_with_snapshots):
        """Dot-path resolves to directory — IsADirectoryError is safe, not traversal."""
        sb, snap_id, _ = sandbox_with_snapshots
        try:
            sb.read_snapshot_file(snap_id, "logs/.")
        except (IsADirectoryError, PermissionError, OSError):
            pass


class TestUnsafeLocalBackendHonesty:
    def test_restricted_local_is_not_hard_isolated(self):
        """The restricted_local profile uses UnsafeLocalSandbox — not hard isolated."""
        from agentic_runtime.sandbox_policy import (
            SandboxProfileName,
            get_sandbox_profile,
            materialize_sandbox_backend,
        )
        root = tempfile.mkdtemp(prefix="honesty_test_")
        try:
            profile = get_sandbox_profile(
                SandboxProfileName.RESTRICTED_LOCAL.value, root,
            )
            backend = materialize_sandbox_backend(profile)
            assert backend.is_hard_isolated is False
            assert backend.is_security_boundary is False
        finally:
            import shutil
            shutil.rmtree(root, ignore_errors=True)

    def test_unsafe_local_demo_is_unsafe(self):
        """unsafe_local_demo profile is explicitly unsafe."""
        from agentic_runtime.sandbox_policy import (
            SandboxProfileName,
            get_sandbox_profile,
            materialize_sandbox_backend,
        )
        root = tempfile.mkdtemp(prefix="honesty_test_")
        try:
            profile = get_sandbox_profile(
                SandboxProfileName.UNSAFE_LOCAL_DEMO.value, root,
            )
            assert profile.unsafe is True
            backend = materialize_sandbox_backend(profile)
            assert backend.is_hard_isolated is False
        finally:
            import shutil
            shutil.rmtree(root, ignore_errors=True)

    def test_diagnostics_reports_unsafe_for_restricted_local(self):
        """SandboxDiagnostics correctly reports unsafe/false isolation for restricted_local."""
        from agentic_runtime.sandbox_policy import (
            SandboxProfileName,
            create_profiled_sandbox,
        )
        root = tempfile.mkdtemp(prefix="honesty_test_")
        try:
            profiled, policy = create_profiled_sandbox(
                SandboxProfileName.RESTRICTED_LOCAL.value, root,
            )
            diag = policy.diagnostics(profiled)
            assert diag.unsafe is True, "restricted_local should report unsafe=True"
            assert diag.hard_isolated is False
            assert "not a hard sandbox boundary" in " ".join(diag.limitations).lower()
        finally:
            import shutil
            shutil.rmtree(root, ignore_errors=True)

    def test_diagnostics_reports_hard_isolated_for_docker(self):
        """Docker profile reports hard_isolated=True."""
        # Docker may not be available; check availability
        from agentic_runtime.sandbox_policy import (
            SandboxProfileName,
            SandboxUnavailableError,
            create_profiled_sandbox,
        )
        root = tempfile.mkdtemp(prefix="honesty_test_")
        try:
            try:
                profiled, policy = create_profiled_sandbox(
                    SandboxProfileName.DOCKER.value, root,
                )
            except SandboxUnavailableError:
                pytest.skip("Docker not available in this environment")
            diag = policy.diagnostics(profiled)
            assert diag.hard_isolated is True
            assert diag.security_boundary is True
            assert diag.unsafe is False
        finally:
            import shutil
            shutil.rmtree(root, ignore_errors=True)

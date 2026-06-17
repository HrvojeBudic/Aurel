"""Tests for CanonicalPathResolver."""

import os

import pytest

from agentic_runtime.canonical_path import CanonicalPathResolver, PathResolutionError


@pytest.fixture
def resolver(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("app")
    (tmp_path / "outside.py").write_text("outside")
    return CanonicalPathResolver(str(tmp_path))


def test_resolve_relative_within_root(resolver):
    r = resolver.resolve("src/app.py")
    assert r.relative == "src/app.py"


def test_path_traversal_denied(resolver):
    with pytest.raises(PathResolutionError, match="traversal"):
        resolver.resolve("src/../outside.py")


def test_absolute_path_denied(resolver):
    with pytest.raises(PathResolutionError, match="absolute"):
        resolver.resolve("/etc/passwd")


def test_traversal_not_covered_by_prefix(resolver):
    assert not resolver.is_covered_by_prefixes("src/../outside.py", ["src/"])


def test_symlink_escape_denied(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    outside = tmp_path / "outside_secret"
    outside.mkdir()
    (outside / "leak.txt").write_text("secret")
    (root / "link").symlink_to(outside)
    resolver = CanonicalPathResolver(str(root))
    with pytest.raises(PathResolutionError, match="symlink"):
        resolver.resolve("link/leak.txt")

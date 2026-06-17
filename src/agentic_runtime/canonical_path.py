"""
canonical_path.py — Single source of truth for path resolution.

Used by PolicyEngine (authority checks) and Sandbox (filesystem ops) so that
policy and enforcement agree on what a path *means*. Blocks:

  - absolute host paths (``/etc/passwd``)
  - ``..`` segments (even when normalization would stay inside root)
  - symlink escapes that resolve outside the root
"""
from __future__ import annotations

import os
from dataclasses import dataclass


class PathResolutionError(Exception):
    """Raised when a path cannot be safely resolved within the workspace."""

    def __init__(self, reason: str, original: str) -> None:
        self.reason = reason
        self.original = original
        super().__init__(f"{reason}: {original!r}")


@dataclass(frozen=True)
class ResolvedPath:
    """Canonical path within a workspace root."""

    relative: str
    absolute: str


def _norm_relative(rel: str) -> str:
    return rel.replace("\\", "/")


class CanonicalPathResolver:
    """Resolve user-supplied paths to canonical workspace-relative paths."""

    def __init__(self, root: str) -> None:
        self.root = os.path.realpath(os.path.abspath(root))

    def resolve(self, path: str) -> ResolvedPath:
        if not path or not str(path).strip():
            raise PathResolutionError("empty path", path)
        if "\0" in path:
            raise PathResolutionError("invalid path", path)
        if os.path.isabs(path):
            raise PathResolutionError("absolute host paths denied", path)

        normalized_input = path.replace("\\", "/")
        if ".." in normalized_input.split("/"):
            raise PathResolutionError("path traversal escapes workspace root", path)

        joined = os.path.join(self.root, path)
        norm = os.path.normpath(joined)
        if not _within_root(norm, self.root):
            raise PathResolutionError("path traversal escapes workspace root", path)

        # realpath resolves symlinks in existing prefix (even for not-yet-created leaf)
        real = os.path.realpath(norm)
        if not _within_root(real, self.root):
            raise PathResolutionError("symlink escapes workspace root", path)

        rel = os.path.relpath(real, self.root)
        if rel.startswith(".."):
            raise PathResolutionError("path traversal escapes workspace root", path)

        return ResolvedPath(relative=_norm_relative(rel), absolute=real)

    def is_covered_by_prefixes(self, path: str, prefixes: list[str]) -> bool:
        try:
            rel = self.resolve(path).relative
        except PathResolutionError:
            return False
        for prefix in prefixes:
            if prefix == "*":
                return True
            p = prefix.rstrip("/")
            if rel == p or rel.startswith(p + "/"):
                return True
        return False


def _within_root(candidate: str, root: str) -> bool:
    return candidate == root or candidate.startswith(root + os.sep)

"""Portable repository root discovery for subprocess test cwd."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    raise RuntimeError("Could not locate repository root")


REPO_ROOT = repo_root()

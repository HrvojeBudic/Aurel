"""Built-in tool manifest seed helpers (P1.3.8).

Production seed manifests are declarative capability declarations only.
Loading them does not register Tool Bus handlers or execute tools.
"""
from __future__ import annotations

from pathlib import Path

from .loader import ManifestLoadResult, load_manifest_directory

_BUILTIN_MANIFESTS_DIR = Path(__file__).resolve().parent / "manifests"


def get_builtin_manifest_directory() -> Path:
    """Return the directory containing shipped built-in tool manifest JSON files."""
    return _BUILTIN_MANIFESTS_DIR


def load_builtin_tool_manifests() -> list[ManifestLoadResult]:
    """Load all built-in seed manifests from the shipped manifests directory."""
    return load_manifest_directory(get_builtin_manifest_directory())

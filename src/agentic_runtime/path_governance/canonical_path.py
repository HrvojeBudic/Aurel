"""String-only canonical path helpers for P1.7.1.

This module does not inspect the filesystem, resolve symlinks, check trusted
roots, detect escapes, or make allow/deny decisions.
"""
from __future__ import annotations


TRAVERSAL_WARNING = (
    "Traversal-like segments preserved; escape detection scheduled for P1.7.5"
)


def normalize_path_string(raw_path: str) -> str:
    """Normalize a path string without filesystem authority."""
    path = raw_path.replace("\\", "/")
    is_absolute = path.startswith("/")
    parts: list[str] = []

    for segment in path.split("/"):
        if segment in ("", "."):
            continue
        parts.append(segment)

    normalized = "/".join(parts)
    if is_absolute:
        normalized = f"/{normalized}" if normalized else "/"
    return normalized


def path_normalization_warnings(normalized_path: str) -> tuple[str, ...]:
    """Return representation-only warnings; never enforcement decisions."""
    if ".." in normalized_path.split("/"):
        return (TRAVERSAL_WARNING,)
    return ()

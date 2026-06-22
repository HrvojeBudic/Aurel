"""Shared file patch helpers for tool execution and state verification."""
from __future__ import annotations


def apply_simple_unified_diff(original: str, diff: str) -> tuple[str, str]:
    """Apply a small single-file unified diff.

    Supports a conservative subset; invalid/mismatched hunks raise ValueError.
    """
    patch_lines = diff.splitlines(keepends=True)
    if not any(line.startswith("@@") for line in patch_lines):
        raise ValueError("invalid patch: missing hunk header")

    src = original.splitlines(keepends=True)
    out: list[str] = []
    idx = 0
    hunk_seen = False
    added = removed = 0

    for raw in patch_lines:
        line = raw if raw.endswith("\n") else raw + "\n"
        if line.startswith(("---", "+++")):
            continue
        if line.startswith("@@"):
            hunk_seen = True
            continue
        if not hunk_seen:
            continue
        tag = line[:1]
        body = line[1:]
        if tag == " ":
            if idx >= len(src) or src[idx] != body:
                raise ValueError("invalid patch: context mismatch")
            out.append(src[idx])
            idx += 1
        elif tag == "-":
            if idx >= len(src) or src[idx] != body:
                raise ValueError("invalid patch: removal mismatch")
            idx += 1
            removed += 1
        elif tag == "+":
            out.append(body)
            added += 1
        elif tag == "\\":
            continue
        else:
            raise ValueError("invalid patch: unsupported hunk line")

    out.extend(src[idx:])
    return "".join(out), f"applied patch (+{added}/-{removed})"


def resolve_run_tests_command(args: dict) -> list[str] | str:
    """Resolve the shell argv used by run_tests (shared by execution and verifier)."""
    command = args.get("command")
    if command is None:
        return ["python3", args.get("test_file", "test.py")]
    return command

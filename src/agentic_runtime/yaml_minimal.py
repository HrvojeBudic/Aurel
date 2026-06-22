"""Minimal YAML subset parser (stdlib only).

Supports mapping documents with nested dicts, lists, scalars (str, int, float,
bool, null). Sufficient for agent/config/*.yaml — not a full YAML 1.1 parser.
"""
from __future__ import annotations

from typing import Any


class YamlParseError(ValueError):
    pass


def load_yaml(text: str) -> dict[str, Any]:
    """Parse a constrained YAML mapping document into a dict."""
    lines = text.splitlines()
    if not any(line.strip() and not line.strip().startswith("#") for line in lines):
        return {}
    root, next_index = _parse_block(lines, 0, 0)
    if not isinstance(root, dict):
        raise YamlParseError("document root must be a mapping")
    for line_no in range(next_index, len(lines)):
        if lines[line_no].strip() and not lines[line_no].lstrip().startswith("#"):
            raise YamlParseError(f"unexpected content at line {line_no + 1}")
    return root


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_comment(line: str) -> str:
    out: list[str] = []
    in_single = False
    in_double = False
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            continue
        if ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]
        return parts
    if text in {"null", "Null", "NULL", "~"}:
        return None
    if text in {"true", "True", "TRUE"}:
        return True
    if text in {"false", "False", "FALSE"}:
        return False
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return int(text)
    try:
        if "." in text:
            return float(text)
    except ValueError:
        pass
    return text


def _next_content_index(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        if lines[i].strip() and not lines[i].lstrip().startswith("#"):
            return i
        i += 1
    return i


def _parse_block(lines: list[str], start: int, base_indent: int) -> tuple[Any, int]:
    i = start
    while i < len(lines):
        if not lines[i].strip() or lines[i].lstrip().startswith("#"):
            i += 1
            continue
        break
    if i >= len(lines):
        return {}, i

    first = _strip_comment(lines[i])
    ind = _indent(lines[i])
    if ind < base_indent:
        return {}, i

    if first.lstrip().startswith("- "):
        items: list[Any] = []
        while i < len(lines):
            line = lines[i]
            if not line.strip() or line.lstrip().startswith("#"):
                i += 1
                continue
            line_indent = _indent(line)
            if line_indent < base_indent:
                break
            if line_indent != base_indent:
                raise YamlParseError(f"unexpected indentation in list at line {i + 1}")
            stripped = _strip_comment(line).lstrip()
            if not stripped.startswith("- "):
                break
            content = stripped[2:].strip()
            if not content:
                raise YamlParseError(f"empty list item at line {i + 1}")
            if ":" in content and not content.startswith(("{", "[")):
                key, _, rest = content.partition(":")
                key = key.strip()
                rest = rest.strip()
                if not key:
                    raise YamlParseError(f"empty key at line {i + 1}")
                if rest:
                    item: dict[str, Any] = {key: _parse_scalar(rest)}
                    i += 1
                else:
                    child_index = _next_content_index(lines, i + 1)
                    if child_index < len(lines) and _indent(lines[child_index]) > line_indent:
                        nested, i = _parse_block(lines, child_index, _indent(lines[child_index]))
                    else:
                        nested = {}
                        i += 1
                    item = {key: nested}
                next_index = _next_content_index(lines, i)
                if next_index < len(lines) and _indent(lines[next_index]) > line_indent:
                    continuation, i = _parse_block(lines, next_index, _indent(lines[next_index]))
                    if not isinstance(continuation, dict):
                        raise YamlParseError(
                            f"unsupported nested list item continuation at line {next_index + 1}"
                        )
                    duplicate_keys = sorted(set(item) & set(continuation))
                    if duplicate_keys:
                        raise YamlParseError(
                            "duplicate key in list item at line "
                            f"{next_index + 1}: {duplicate_keys[0]}"
                        )
                    item.update(continuation)
                items.append(item)
            else:
                items.append(_parse_scalar(content))
                i += 1
                next_index = _next_content_index(lines, i)
                if next_index < len(lines) and _indent(lines[next_index]) > line_indent:
                    raise YamlParseError(
                        f"unsupported nested scalar list item at line {next_index + 1}"
                    )
        return items, i

    mapping: dict[str, Any] = {}
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if _indent(line) < base_indent:
            break
        if _indent(line) != base_indent:
            break
        stripped = _strip_comment(line).strip()
        if ":" not in stripped:
            raise YamlParseError(f"expected key:value at line {i + 1}")
        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        if not key:
            raise YamlParseError(f"empty key at line {i + 1}")
        if rest:
            mapping[key] = _parse_scalar(rest)
            i += 1
            continue
        if i + 1 < len(lines) and _indent(lines[i + 1]) > base_indent:
            child_indent = _indent(lines[i + 1])
            if lines[i + 1].lstrip().startswith("- "):
                nested, i = _parse_block(lines, i + 1, child_indent)
            else:
                nested, i = _parse_block(lines, i + 1, child_indent)
            mapping[key] = nested
        else:
            mapping[key] = None
            i += 1
    return mapping, i

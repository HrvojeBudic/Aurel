"""Serialization helpers for tool manifest domain models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

E = TypeVar("E", bound=Enum)


def enum_value(value: Enum | None) -> str | None:
    return value.value if value is not None else None


def enum_from(cls: type[E], value: Any) -> E | None:
    if value is None:
        return None
    if isinstance(value, cls):
        return value
    return cls(value)


def enum_list_values(items: list[Enum]) -> list[str]:
    return [item.value for item in items]


def enum_list_from(cls: type[E], items: list[Any]) -> list[E]:
    result: list[E] = []
    for item in items:
        parsed = enum_from(cls, item)
        if parsed is None:
            raise ValueError(f"invalid enum value for {cls.__name__}: {item!r}")
        result.append(parsed)
    return result


def datetime_to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def datetime_from_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)

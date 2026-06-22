"""P1.4.12 source hashing tests."""
from __future__ import annotations

from dataclasses import dataclass

from agentic_runtime.identity.source_attestation import (
    canonicalize_source_object,
    hash_canonical_source,
    hash_raw_source,
)


@dataclass(frozen=True)
class _TypedSource:
    name: str
    values: dict[str, int]
    created_at: str = "volatile"


def test_hash_raw_source_is_stable():
    assert hash_raw_source("a: 1\n") == hash_raw_source("a: 1\n")


def test_hash_raw_source_changes_when_raw_extra_field_added():
    base = "operator_contract:\n  name: Aurel\n"
    modified = "operator_contract:\n  name: Aurel\n  shadow_authority_grant: true\n"
    assert hash_raw_source(base) != hash_raw_source(modified)


def test_raw_hash_is_unnormalized():
    assert hash_raw_source("a: 1\n") != hash_raw_source("a: 1\r\n")


def test_hash_canonical_source_is_stable():
    obj = {"b": 2, "a": 1}
    assert hash_canonical_source(obj) == hash_canonical_source({"a": 1, "b": 2})


def test_canonical_hash_same_for_equivalent_typed_object():
    left = _TypedSource(name="x", values={"b": 2, "a": 1})
    right = _TypedSource(name="x", values={"a": 1, "b": 2})
    assert canonicalize_source_object(left) == canonicalize_source_object(right)
    assert hash_canonical_source(left) == hash_canonical_source(right)


def test_canonical_hash_excludes_runtime_timestamps():
    left = _TypedSource(name="x", values={"a": 1}, created_at="t1")
    right = _TypedSource(name="x", values={"a": 1}, created_at="t2")
    assert hash_canonical_source(left) == hash_canonical_source(right)

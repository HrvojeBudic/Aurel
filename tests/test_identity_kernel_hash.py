"""P1.4.1 — Identity Kernel hashing tests."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.identity.kernel import load_identity_kernel, parse_identity_kernel_document
from agentic_runtime.identity.kernel_hash import compute_identity_kernel_hash
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KERNEL = REPO_ROOT / "config" / "aurel" / "identity_kernel.yaml"


def test_same_semantic_kernel_produces_same_hash():
    kernel_a = load_identity_kernel(CANONICAL_KERNEL)
    kernel_b = load_identity_kernel(CANONICAL_KERNEL)
    assert compute_identity_kernel_hash(kernel_a).value == compute_identity_kernel_hash(kernel_b).value


def test_yaml_field_order_does_not_change_hash(tmp_path):
    text = CANONICAL_KERNEL.read_text(encoding="utf-8")
    reordered = text.replace(
        '  schema_version: "1.0"\n  name: "Aurel"',
        '  name: "Aurel"\n  schema_version: "1.0"',
    )
    path = tmp_path / "reordered.yaml"
    path.write_text(reordered, encoding="utf-8")
    canonical = load_identity_kernel(CANONICAL_KERNEL)
    reordered_kernel = load_identity_kernel(path)
    assert (
        compute_identity_kernel_hash(canonical).value
        == compute_identity_kernel_hash(reordered_kernel).value
    )


def test_changing_critical_invariant_changes_hash():
    doc = load_yaml(CANONICAL_KERNEL.read_text(encoding="utf-8"))
    doc["identity_kernel"]["invariants"] = list(doc["identity_kernel"]["invariants"])
    doc["identity_kernel"]["invariants"][0] = dict(doc["identity_kernel"]["invariants"][0])
    doc["identity_kernel"]["invariants"][0]["statement"] = "Modified statement."
    original = compute_identity_kernel_hash(load_identity_kernel(CANONICAL_KERNEL)).value
    modified = compute_identity_kernel_hash(parse_identity_kernel_document(doc)).value
    assert original != modified


def test_hash_algorithm_is_sha256():
    kernel_hash = compute_identity_kernel_hash(load_identity_kernel(CANONICAL_KERNEL))
    assert kernel_hash.algorithm == "sha256"
    assert len(kernel_hash.value) == 64

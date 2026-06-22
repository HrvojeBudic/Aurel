"""P1.4.2 — Persona Manifest hashing tests."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.identity.persona import (
    load_persona_manifest,
    parse_persona_manifest_document,
)
from agentic_runtime.identity.persona_hash import compute_persona_manifest_hash
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "persona_manifest.yaml"


# 23
def test_same_semantic_manifest_produces_same_hash():
    a = load_persona_manifest(CANONICAL)
    b = load_persona_manifest(CANONICAL)
    assert compute_persona_manifest_hash(a).value == compute_persona_manifest_hash(b).value


# 24
def test_yaml_field_order_does_not_change_hash(tmp_path):
    text = CANONICAL.read_text(encoding="utf-8")
    reordered = text.replace(
        '  schema_version: "1.0"\n  name: "Aurel Default Persona"',
        '  name: "Aurel Default Persona"\n  schema_version: "1.0"',
    )
    path = tmp_path / "reordered.yaml"
    path.write_text(reordered, encoding="utf-8")
    canonical = load_persona_manifest(CANONICAL)
    reordered_manifest = load_persona_manifest(path)
    assert (
        compute_persona_manifest_hash(canonical).value
        == compute_persona_manifest_hash(reordered_manifest).value
    )


# 25
def test_changing_critical_invariant_changes_hash():
    doc = load_yaml(CANONICAL.read_text(encoding="utf-8"))
    doc["persona_manifest"]["invariants"] = list(doc["persona_manifest"]["invariants"])
    doc["persona_manifest"]["invariants"][0] = dict(doc["persona_manifest"]["invariants"][0])
    doc["persona_manifest"]["invariants"][0]["statement"] = "Modified statement."
    original = compute_persona_manifest_hash(load_persona_manifest(CANONICAL)).value
    modified = compute_persona_manifest_hash(parse_persona_manifest_document(doc)).value
    assert original != modified


def test_hash_algorithm_is_sha256():
    persona_hash = compute_persona_manifest_hash(load_persona_manifest(CANONICAL))
    assert persona_hash.algorithm == "sha256"
    assert len(persona_hash.value) == 64

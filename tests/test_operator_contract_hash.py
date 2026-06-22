"""P1.4.3 — Operator Relationship Contract hash tests."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.operator_contract_hash import compute_operator_contract_hash

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "operator_contract.yaml"


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "operator_contract.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


# 42
def test_same_semantic_contract_produces_same_hash():
    contract_a = load_operator_contract(CANONICAL)
    contract_b = load_operator_contract(CANONICAL)
    assert compute_operator_contract_hash(contract_a).value == compute_operator_contract_hash(
        contract_b
    ).value


# 43
def test_yaml_field_order_does_not_change_hash(tmp_path):
    path = _copy_to(tmp_path)
    original = load_operator_contract(path)
    original_hash = compute_operator_contract_hash(original).value

    text = path.read_text(encoding="utf-8")
    reordered = text.replace(
        "  authority:\n    operator_final_authority: true\n    aurel_final_authority: false",
        "  authority:\n    aurel_final_authority: false\n    operator_final_authority: true",
        1,
    )
    path.write_text(reordered, encoding="utf-8")
    reloaded = load_operator_contract(path)
    assert compute_operator_contract_hash(reloaded).value == original_hash


# 44
def test_changing_critical_authority_invariant_changes_hash(tmp_path):
    path = _copy_to(tmp_path)
    original_hash = compute_operator_contract_hash(load_operator_contract(path)).value
    text = path.read_text(encoding="utf-8").replace(
        "operator_final_authority: true",
        "operator_final_authority: false",
        1,
    )
    path.write_text(text, encoding="utf-8")
    modified_hash = compute_operator_contract_hash(load_operator_contract(path)).value
    assert modified_hash != original_hash

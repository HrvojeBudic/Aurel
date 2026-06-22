"""P1.4.4 — Communication Modes hash tests."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.mode_hash import compute_communication_mode_registry_hash

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "communication_modes.yaml"


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "communication_modes.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


# 41
def test_same_semantic_registry_produces_same_hash():
    registry_a = load_communication_mode_registry(CANONICAL)
    registry_b = load_communication_mode_registry(CANONICAL)
    assert compute_communication_mode_registry_hash(registry_a).value == (
        compute_communication_mode_registry_hash(registry_b).value
    )


# 42
def test_yaml_field_order_does_not_change_hash(tmp_path):
    path = _copy_to(tmp_path)
    original = load_communication_mode_registry(path)
    original_hash = compute_communication_mode_registry_hash(original).value

    text = path.read_text(encoding="utf-8")
    reordered = text.replace(
        "    modes_can_grant_permissions: false\n    modes_can_change_autonomy: false",
        "    modes_can_change_autonomy: false\n    modes_can_grant_permissions: false",
        1,
    )
    path.write_text(reordered, encoding="utf-8")
    reloaded = load_communication_mode_registry(path)
    assert compute_communication_mode_registry_hash(reloaded).value == original_hash


# 43
def test_changing_critical_mode_boundary_changes_hash(tmp_path):
    path = _copy_to(tmp_path)
    original_hash = compute_communication_mode_registry_hash(
        load_communication_mode_registry(path)
    ).value
    text = path.read_text(encoding="utf-8").replace(
        "modes_can_grant_permissions: false",
        "modes_can_grant_permissions: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    modified_hash = compute_communication_mode_registry_hash(
        load_communication_mode_registry(path)
    ).value
    assert modified_hash != original_hash

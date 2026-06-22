"""P1.4.1 — Identity Kernel loader and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.kernel import (
    IdentityKernelError,
    default_identity_kernel_path,
    load_identity_kernel,
    parse_identity_kernel_document,
)
from agentic_runtime.identity.kernel_validation import validate_identity_kernel
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KERNEL = REPO_ROOT / "config" / "aurel" / "identity_kernel.yaml"


def _load_canonical_document() -> dict:
    return load_yaml(CANONICAL_KERNEL.read_text(encoding="utf-8"))


def _copy_canonical_to(tmp_path: Path) -> Path:
    target = tmp_path / "identity_kernel.yaml"
    target.write_text(CANONICAL_KERNEL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _mutate_yaml_text(text: str, replacements: dict[str, str]) -> str:
    out = text
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def test_valid_kernel_loads_and_validates():
    kernel = load_identity_kernel(CANONICAL_KERNEL)
    result = validate_identity_kernel(kernel)
    assert result.valid is True
    assert kernel.name == "Aurel"
    assert kernel.agent_class == "sovereign_personal_agent"
    assert len(kernel.invariants) == 8


def test_default_path_points_to_canonical_config():
    assert default_identity_kernel_path() == CANONICAL_KERNEL


def test_missing_required_section_fails():
    doc = _load_canonical_document()
    del doc["identity_kernel"]["immutables"]
    with pytest.raises(IdentityKernelError, match="immutables"):
        parse_identity_kernel_document(doc)


def test_missing_final_authority_fails(tmp_path):
    text = _mutate_yaml_text(
        CANONICAL_KERNEL.read_text(encoding="utf-8"),
        {'  final_authority: "operator"\n': ""},
    )
    path = tmp_path / "identity_kernel.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(IdentityKernelError, match="final_authority"):
        load_identity_kernel(path)


def test_name_other_than_aurel_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace('name: "Aurel"', 'name: "NotAurel"')
    path.write_text(text, encoding="utf-8")
    kernel = load_identity_kernel(path)
    result = validate_identity_kernel(kernel)
    assert result.valid is False
    assert any("name must be 'Aurel'" in err for err in result.errors)


def test_final_authority_other_than_operator_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'final_authority: "operator"',
        'final_authority: "aurel"',
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False
    assert any("final_authority" in err for err in result.errors)


def test_operator_final_authority_false_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "operator_final_authority: true",
        "operator_final_authority: false",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_self_escalation_allowed_true_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "self_escalation_allowed: false",
        "self_escalation_allowed: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_hidden_goals_allowed_true_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "hidden_goals_allowed: false",
        "hidden_goals_allowed: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_identity_replacement_allowed_true_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "identity_replacement_allowed: false",
        "identity_replacement_allowed: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_policy_bypass_self_grant_allowed_true_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "policy_bypass_self_grant_allowed: false",
        "policy_bypass_self_grant_allowed: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_untrusted_input_can_modify_identity_true_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "untrusted_input_can_modify_identity: false",
        "untrusted_input_can_modify_identity: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_operator_replacement_false_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "operator_replacement: true",
        "operator_replacement: false",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_self_authority_expansion_false_fails(tmp_path):
    path = _copy_canonical_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "self_authority_expansion: true",
        "self_authority_expansion: false",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_identity_kernel(load_identity_kernel(path))
    assert result.valid is False


def test_invariant_unknown_key_fails(tmp_path):
    doc = _load_canonical_document()
    doc["identity_kernel"]["invariants"] = list(doc["identity_kernel"]["invariants"])
    doc["identity_kernel"]["invariants"][0] = dict(doc["identity_kernel"]["invariants"][0])
    doc["identity_kernel"]["invariants"][0]["key"] = "unknown_kernel_key"
    kernel = parse_identity_kernel_document(doc)
    result = validate_identity_kernel(kernel)
    assert result.valid is False
    assert any("unknown key" in err for err in result.errors)


def test_critical_invariant_mutable_true_fails(tmp_path):
    doc = _load_canonical_document()
    doc["identity_kernel"]["invariants"] = list(doc["identity_kernel"]["invariants"])
    doc["identity_kernel"]["invariants"][0] = dict(doc["identity_kernel"]["invariants"][0])
    doc["identity_kernel"]["invariants"][0]["mutable"] = True
    result = validate_identity_kernel(parse_identity_kernel_document(doc))
    assert result.valid is False
    assert any("immutable" in err for err in result.errors)


def test_critical_invariant_without_fail_boot_fails(tmp_path):
    doc = _load_canonical_document()
    doc["identity_kernel"]["invariants"] = list(doc["identity_kernel"]["invariants"])
    doc["identity_kernel"]["invariants"][0] = dict(doc["identity_kernel"]["invariants"][0])
    doc["identity_kernel"]["invariants"][0]["violation_action"] = "warn"
    result = validate_identity_kernel(parse_identity_kernel_document(doc))
    assert result.valid is False
    assert any("fail_boot" in err for err in result.errors)


def test_invariant_expected_value_mismatch_fails(tmp_path):
    doc = _load_canonical_document()
    doc["identity_kernel"]["invariants"] = list(doc["identity_kernel"]["invariants"])
    doc["identity_kernel"]["invariants"][0] = dict(doc["identity_kernel"]["invariants"][0])
    doc["identity_kernel"]["invariants"][0]["expected_value"] = False
    result = validate_identity_kernel(parse_identity_kernel_document(doc))
    assert result.valid is False
    assert any("expected_value" in err for err in result.errors)

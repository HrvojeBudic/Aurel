"""P1.4.2 — Persona Manifest loader and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.persona import (
    PersonaManifestError,
    default_persona_manifest_path,
    load_persona_manifest,
    parse_persona_manifest_document,
)
from agentic_runtime.identity.persona_summary import build_persona_safe_summary
from agentic_runtime.identity.persona_validation import validate_persona_manifest
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "persona_manifest.yaml"


def _load_doc() -> dict:
    return load_yaml(CANONICAL.read_text(encoding="utf-8"))


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "persona_manifest.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _validate_with_field(tmp_path: Path, old: str, new: str):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return validate_persona_manifest(load_persona_manifest(path))


# 1, 2
def test_valid_manifest_loads_and_validates():
    manifest = load_persona_manifest(CANONICAL)
    result = validate_persona_manifest(manifest)
    assert result.valid is True
    assert manifest.applies_to_agent == "Aurel"
    assert manifest.manifest_class == "expression_contract"
    assert len(manifest.invariants) == 7


def test_default_path_points_to_canonical():
    assert default_persona_manifest_path() == CANONICAL


# 3
def test_missing_persona_manifest_section_fails():
    with pytest.raises(PersonaManifestError, match="persona_manifest"):
        parse_persona_manifest_document({"something_else": {}})


# 4
def test_manifest_class_not_expression_contract_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'manifest_class: "expression_contract"',
        'manifest_class: "authority_contract"',
    )
    assert result.valid is False


# 5
def test_authority_level_not_none_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'authority_level: "none"', 'authority_level: "high"'
    )
    assert result.valid is False


# 6
def test_can_grant_permissions_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "can_grant_permissions: false", "can_grant_permissions: true"
    )
    assert result.valid is False


# 7
def test_can_override_identity_kernel_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "can_override_identity_kernel: false",
        "can_override_identity_kernel: true",
    )
    assert result.valid is False


# 8
def test_can_override_policy_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "can_override_policy: false", "can_override_policy: true"
    )
    assert result.valid is False


# 9
def test_can_change_autonomy_true_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "can_change_autonomy: false", "can_change_autonomy: true"
    )
    assert result.valid is False


# 10
def test_never_claim_unverified_capability_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "never_claim_unverified_capability: true",
        "never_claim_unverified_capability: false",
    )
    assert result.valid is False


# 11
def test_false_certainty_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "false_certainty_forbidden: true", "false_certainty_forbidden: false"
    )
    assert result.valid is False


# 12
def test_raw_manifest_in_prompt_forbidden_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "raw_manifest_in_prompt_forbidden: true",
        "raw_manifest_in_prompt_forbidden: false",
    )
    assert result.valid is False


# 13
def test_compile_to_safe_summary_required_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "compile_to_safe_summary_required: true",
        "compile_to_safe_summary_required: false",
    )
    assert result.valid is False


# 14
def test_respect_operator_final_authority_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "respect_operator_final_authority: true",
        "respect_operator_final_authority: false",
    )
    assert result.valid is False


# 15
def test_must_not_replace_operator_judgment_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "must_not_replace_operator_judgment: true",
        "must_not_replace_operator_judgment: false",
    )
    assert result.valid is False


# 16
def test_cannot_grant_tool_rights_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "cannot_grant_tool_rights: true", "cannot_grant_tool_rights: false"
    )
    assert result.valid is False


# 17
def test_cannot_increase_autonomy_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, "cannot_increase_autonomy: true", "cannot_increase_autonomy: false"
    )
    assert result.valid is False


# 18
def test_cannot_convert_style_into_authority_false_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        "cannot_convert_style_into_authority: true",
        "cannot_convert_style_into_authority: false",
    )
    assert result.valid is False


# 19
def test_unknown_invariant_key_fails():
    doc = _load_doc()
    doc["persona_manifest"]["invariants"] = list(doc["persona_manifest"]["invariants"])
    doc["persona_manifest"]["invariants"][0] = dict(doc["persona_manifest"]["invariants"][0])
    doc["persona_manifest"]["invariants"][0]["key"] = "unknown_persona_key"
    result = validate_persona_manifest(parse_persona_manifest_document(doc))
    assert result.valid is False
    assert any("unknown key" in err for err in result.errors)


# 20
def test_invariant_expected_value_mismatch_fails():
    doc = _load_doc()
    doc["persona_manifest"]["invariants"] = list(doc["persona_manifest"]["invariants"])
    doc["persona_manifest"]["invariants"][0] = dict(doc["persona_manifest"]["invariants"][0])
    doc["persona_manifest"]["invariants"][0]["expected_value"] = True
    result = validate_persona_manifest(parse_persona_manifest_document(doc))
    assert result.valid is False
    assert any("expected_value" in err for err in result.errors)


# 21
def test_critical_invariant_mutable_true_fails():
    doc = _load_doc()
    doc["persona_manifest"]["invariants"] = list(doc["persona_manifest"]["invariants"])
    doc["persona_manifest"]["invariants"][0] = dict(doc["persona_manifest"]["invariants"][0])
    doc["persona_manifest"]["invariants"][0]["mutable"] = True
    result = validate_persona_manifest(parse_persona_manifest_document(doc))
    assert result.valid is False
    assert any("immutable" in err for err in result.errors)


# 22
def test_critical_invariant_without_fail_boot_fails():
    doc = _load_doc()
    doc["persona_manifest"]["invariants"] = list(doc["persona_manifest"]["invariants"])
    doc["persona_manifest"]["invariants"][0] = dict(doc["persona_manifest"]["invariants"][0])
    doc["persona_manifest"]["invariants"][0]["violation_action"] = "warn"
    result = validate_persona_manifest(parse_persona_manifest_document(doc))
    assert result.valid is False
    assert any("fail_boot" in err for err in result.errors)


def test_missing_required_section_fails():
    doc = _load_doc()
    del doc["persona_manifest"]["voice"]
    with pytest.raises(PersonaManifestError, match="voice"):
        parse_persona_manifest_document(doc)


# 30, 31, 32
def test_safe_summary_contains_authority_boundaries():
    summary = build_persona_safe_summary(load_persona_manifest(CANONICAL))
    assert summary.authority_boundaries
    assert any("cannot grant permissions" in r.lower() for r in summary.authority_boundaries)


def test_safe_summary_contains_capability_honesty_rules():
    summary = build_persona_safe_summary(load_persona_manifest(CANONICAL))
    assert summary.capability_honesty_rules
    assert any("unverified" in r.lower() for r in summary.capability_honesty_rules)


def test_safe_summary_does_not_expose_raw_yaml():
    summary = build_persona_safe_summary(load_persona_manifest(CANONICAL))
    blob = repr(summary)
    assert "persona_manifest:" not in blob
    assert "expected_value" not in blob
    assert "rationale" not in blob

"""P1.4.6 — Self-Model policy loader and validation tests (cases #1-22)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.self_model_policy import (
    SelfModelError,
    default_self_model_policy_path,
    load_self_model_policy,
    parse_self_model_policy_document,
)
from agentic_runtime.identity.self_model_validation import validate_self_model_policy
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "self_model_policy.yaml"


def _load_doc() -> dict:
    return load_yaml(CANONICAL.read_text(encoding="utf-8"))


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "self_model_policy.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _validate_with_field(tmp_path: Path, old: str, new: str):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return validate_self_model_policy(load_self_model_policy(path))


# 1, 2
def test_valid_policy_loads_and_validates():
    policy = load_self_model_policy(CANONICAL)
    result = validate_self_model_policy(policy)
    assert result.valid is True
    assert policy.policy_class == "honest_runtime_self_description"
    assert policy.applies_to_agent == "Aurel"
    assert len(policy.invariants) == 7


def test_default_path_points_to_canonical():
    assert default_self_model_policy_path() == CANONICAL


# 3
def test_missing_self_model_policy_section_fails():
    with pytest.raises(SelfModelError, match="self_model_policy"):
        parse_self_model_policy_document({"something_else": {}})


# 4
def test_policy_class_not_honest_runtime_self_description_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'policy_class: "honest_runtime_self_description"',
        'policy_class: "marketing_layer"',
    )
    assert result.valid is False


# 5
def test_applies_to_agent_not_aurel_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'applies_to_agent: "Aurel"', 'applies_to_agent: "OtherAgent"'
    )
    assert result.valid is False


@pytest.mark.parametrize(
    ("field", "num"),
    [
        ("distinguish_planned_from_implemented", 6),
        ("distinguish_implemented_from_verified", 7),
        ("distinguish_unavailable_from_unverified", 8),
        ("never_claim_roadmap_as_runtime", 9),
        ("never_claim_verification_without_evidence", 10),
        ("mark_unknown_as_unknown", 11),
        ("expose_known_limitations", 12),
    ],
)
def test_honesty_false_fails(tmp_path, field, num):
    result = _validate_with_field(tmp_path, f"{field}: true", f"{field}: false")
    assert result.valid is False


@pytest.mark.parametrize(
    ("field", "num"),
    [
        ("self_model_can_grant_authority", 13),
        ("self_model_can_change_identity", 14),
        ("self_model_can_change_autonomy", 15),
        ("self_model_can_verify_capability_by_itself", 16),
        ("self_model_can_write_memory", 17),
        ("self_model_can_modify_policy", 18),
    ],
)
def test_boundary_true_fails(tmp_path, field, num):
    result = _validate_with_field(tmp_path, f"{field}: false", f"{field}: true")
    assert result.valid is False


# 19
def test_unknown_invariant_key_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'key: "never_claim_roadmap_as_runtime"',
        'key: "unknown_invariant_key"',
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_self_model_policy(load_self_model_policy(path))
    assert result.valid is False


# 20
def test_invariant_expected_value_mismatch_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'id: "SM-003"\n      key: "self_model_can_grant_authority"\n      statement: "Self-Model cannot grant authority."\n      expected_value: false',
        'id: "SM-003"\n      key: "self_model_can_grant_authority"\n      statement: "Self-Model cannot grant authority."\n      expected_value: true',
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_self_model_policy(load_self_model_policy(path))
    assert result.valid is False
    assert any("SM-003" in err for err in result.errors)


# 21
def test_critical_invariant_mutable_true_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace("mutable: false", "mutable: true", 1)
    path.write_text(text, encoding="utf-8")
    result = validate_self_model_policy(load_self_model_policy(path))
    assert result.valid is False


# 22
def test_critical_invariant_without_fail_build_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'violation_action: "fail_build"',
        'violation_action: "warn"',
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_self_model_policy(load_self_model_policy(path))
    assert result.valid is False

"""P1.4.4 — Communication Modes loader, validation, lookup, and safe summary tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.communication_modes import (
    REQUIRED_MODES,
    CommunicationModeError,
    default_communication_modes_path,
    load_communication_mode_registry,
    parse_communication_modes_document,
)
from agentic_runtime.identity.mode_registry import get_communication_mode
from agentic_runtime.identity.mode_summary import (
    build_communication_mode_safe_summary,
    communication_mode_safe_summary_to_dict,
)
from agentic_runtime.identity.mode_validation import validate_communication_mode_registry
from agentic_runtime.yaml_minimal import load_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "config" / "aurel" / "communication_modes.yaml"


def _load_doc() -> dict:
    return load_yaml(CANONICAL.read_text(encoding="utf-8"))


def _copy_to(tmp_path: Path) -> Path:
    target = tmp_path / "communication_modes.yaml"
    target.write_text(CANONICAL.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _validate_with_field(tmp_path: Path, old: str, new: str):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return validate_communication_mode_registry(load_communication_mode_registry(path))


def _remove_mode(tmp_path: Path, mode: str):
    doc = _load_doc()
    del doc["communication_modes"]["modes"][mode]
    return validate_communication_mode_registry(parse_communication_modes_document(doc))


# 1, 2
def test_valid_registry_loads_and_validates():
    registry = load_communication_mode_registry(CANONICAL)
    result = validate_communication_mode_registry(registry)
    assert result.valid is True
    assert registry.applies_to_agent == "Aurel"
    assert registry.registry_class == "mode_expression_registry"
    assert set(registry.modes.keys()) == REQUIRED_MODES
    assert len(registry.invariants) == 8


def test_default_path_points_to_canonical():
    assert default_communication_modes_path() == CANONICAL


# 3
def test_missing_communication_modes_section_fails():
    with pytest.raises(CommunicationModeError, match="communication_modes"):
        parse_communication_modes_document({"something_else": {}})


# 4
def test_registry_class_not_mode_expression_registry_fails(tmp_path):
    result = _validate_with_field(
        tmp_path,
        'registry_class: "mode_expression_registry"',
        'registry_class: "authority_registry"',
    )
    assert result.valid is False


# 5
def test_applies_to_agent_not_aurel_fails(tmp_path):
    result = _validate_with_field(
        tmp_path, 'applies_to_agent: "Aurel"', 'applies_to_agent: "OtherAgent"'
    )
    assert result.valid is False


@pytest.mark.parametrize("mode", sorted(REQUIRED_MODES))
def test_missing_required_mode_fails(tmp_path, mode):
    result = _remove_mode(tmp_path, mode)
    assert result.valid is False
    assert any(f"missing required mode: {mode}" in err for err in result.errors)


# 13-22 global boundaries
@pytest.mark.parametrize(
    ("field", "num"),
    [
        ("modes_can_grant_permissions", 13),
        ("modes_can_change_autonomy", 14),
        ("modes_can_override_identity_kernel", 15),
        ("modes_can_override_persona_manifest", 16),
        ("modes_can_override_operator_contract", 17),
        ("modes_can_override_policy", 18),
        ("modes_can_disable_constitutional_floor", 19),
        ("modes_can_write_memory_directly", 20),
        ("modes_can_canonize_output", 21),
        ("modes_can_execute_actions", 22),
    ],
)
def test_global_boundary_true_fails(tmp_path, field, num):
    result = _validate_with_field(
        tmp_path, f"{field}: false", f"{field}: true"
    )
    assert result.valid is False


@pytest.mark.parametrize(
    ("field", "num"),
    [
        ("grants_permissions", 23),
        ("changes_autonomy", 24),
        ("executes_actions", 25),
        ("canonizes_output", 26),
    ],
)
def test_any_mode_boundary_true_fails(tmp_path, field, num):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        f"        {field}: false",
        f"        {field}: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_communication_mode_registry(load_communication_mode_registry(path))
    assert result.valid is False


# 27
def test_empty_mode_purpose_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'purpose: "Clarify priorities, reduce noise, and identify the next decision."',
        'purpose: ""',
        1,
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(CommunicationModeError, match="purpose"):
        load_communication_mode_registry(path)


# 28
def test_empty_cognitive_posture_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        'cognitive_posture: "priority_clarity"',
        'cognitive_posture: ""',
        1,
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(CommunicationModeError, match="cognitive_posture"):
        load_communication_mode_registry(path)


# 29-36 HERETIC
def test_heretic_candidate_only_false_fails(tmp_path):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        "        candidate_only: true",
        "        candidate_only: false",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_communication_mode_registry(load_communication_mode_registry(path))
    assert result.valid is False


@pytest.mark.parametrize(
    ("field", "num"),
    [
        ("writes_files", 30),
        ("modifies_policy", 31),
        ("modifies_identity", 32),
        ("modifies_memory", 33),
        ("modifies_tools", 34),
        ("modifies_autonomy", 35),
        ("real_world_side_effects", 36),
    ],
)
def test_heretic_boundary_true_fails(tmp_path, field, num):
    path = _copy_to(tmp_path)
    text = path.read_text(encoding="utf-8").replace(
        f"        {field}: false",
        f"        {field}: true",
        1,
    )
    path.write_text(text, encoding="utf-8")
    result = validate_communication_mode_registry(load_communication_mode_registry(path))
    assert result.valid is False


# 37
def test_unknown_invariant_key_fails():
    doc = _load_doc()
    doc["communication_modes"]["invariants"] = list(doc["communication_modes"]["invariants"])
    doc["communication_modes"]["invariants"][0] = dict(
        doc["communication_modes"]["invariants"][0]
    )
    doc["communication_modes"]["invariants"][0]["key"] = "unknown_mode_key"
    result = validate_communication_mode_registry(parse_communication_modes_document(doc))
    assert result.valid is False
    assert any("unknown key" in err for err in result.errors)


# 38
def test_invariant_expected_value_mismatch_fails():
    doc = _load_doc()
    doc["communication_modes"]["invariants"] = list(doc["communication_modes"]["invariants"])
    doc["communication_modes"]["invariants"][0] = dict(
        doc["communication_modes"]["invariants"][0]
    )
    doc["communication_modes"]["invariants"][0]["expected_value"] = True
    result = validate_communication_mode_registry(parse_communication_modes_document(doc))
    assert result.valid is False
    assert any("expected_value" in err for err in result.errors)


# 39
def test_critical_invariant_mutable_true_fails():
    doc = _load_doc()
    doc["communication_modes"]["invariants"] = list(doc["communication_modes"]["invariants"])
    doc["communication_modes"]["invariants"][0] = dict(
        doc["communication_modes"]["invariants"][0]
    )
    doc["communication_modes"]["invariants"][0]["mutable"] = True
    result = validate_communication_mode_registry(parse_communication_modes_document(doc))
    assert result.valid is False
    assert any("immutable" in err for err in result.errors)


# 40
def test_critical_invariant_without_fail_boot_fails():
    doc = _load_doc()
    doc["communication_modes"]["invariants"] = list(doc["communication_modes"]["invariants"])
    doc["communication_modes"]["invariants"][0] = dict(
        doc["communication_modes"]["invariants"][0]
    )
    doc["communication_modes"]["invariants"][0]["violation_action"] = "warn"
    result = validate_communication_mode_registry(parse_communication_modes_document(doc))
    assert result.valid is False
    assert any("fail_boot" in err for err in result.errors)


# 44
def test_mode_lookup_returns_focus():
    registry = load_communication_mode_registry(CANONICAL)
    result = get_communication_mode(registry, "FOCUS")
    assert result.found is True
    assert result.mode_name == "FOCUS"
    assert result.mode is not None
    assert result.mode.cognitive_posture == "priority_clarity"


# 45
def test_mode_lookup_returns_heretic():
    registry = load_communication_mode_registry(CANONICAL)
    result = get_communication_mode(registry, "HERETIC")
    assert result.found is True
    assert result.mode_name == "HERETIC"
    assert result.mode is not None
    assert result.mode.output_bias["candidate_only"] is True


# 46
def test_case_insensitive_lookup_returns_canonical_uppercase():
    registry = load_communication_mode_registry(CANONICAL)
    result = get_communication_mode(registry, "focus")
    assert result.found is True
    assert result.mode_name == "FOCUS"


# 47
def test_unknown_mode_lookup_fails_safely():
    registry = load_communication_mode_registry(CANONICAL)
    result = get_communication_mode(registry, "UNKNOWN_MODE")
    assert result.found is False
    assert result.mode is None
    assert result.error is not None


# 54-58 safe summary
def test_safe_summary_contains_authority_boundaries():
    registry = load_communication_mode_registry(CANONICAL)
    summary = build_communication_mode_safe_summary(registry, "FOCUS")
    assert summary.authority_boundaries
    assert any("cannot grant permissions" in r.lower() for r in summary.authority_boundaries)


def test_safe_summary_does_not_expose_raw_yaml():
    registry = load_communication_mode_registry(CANONICAL)
    summary = build_communication_mode_safe_summary(registry, "HERETIC")
    payload = communication_mode_safe_summary_to_dict(summary)
    blob = repr(summary) + repr(payload)
    assert "communication_modes:" not in blob
    assert "expected_value" not in blob
    assert "violation_action" not in blob


def test_safe_summary_does_not_include_tool_permission_language():
    registry = load_communication_mode_registry(CANONICAL)
    summary = build_communication_mode_safe_summary(registry, "FOCUS")
    blob = " ".join(summary.authority_boundaries).lower()
    assert "tool permission" not in blob
    assert "grant tool" not in blob


def test_safe_summary_does_not_include_autonomy_changing_language():
    registry = load_communication_mode_registry(CANONICAL)
    summary = build_communication_mode_safe_summary(registry, "FOCUS")
    blob = " ".join(summary.authority_boundaries).lower()
    assert "increase autonomy" not in blob
    assert "elevate autonomy" not in blob


def test_safe_summary_does_not_include_execution_permission():
    registry = load_communication_mode_registry(CANONICAL)
    summary = build_communication_mode_safe_summary(registry, "FOCUS")
    blob = " ".join(summary.authority_boundaries).lower()
    assert "may execute" not in blob
    assert "permission to execute" not in blob

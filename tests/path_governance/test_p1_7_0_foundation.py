"""P1.7.0 — Path Governance & Source Trust Foundation tests."""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any

import pytest

from agentic_runtime.path_governance import (
    CAPABILITY_STATUS_KNOWN_FIELDS,
    FoundationPosture,
    PATH_GOVERNANCE_UNAVAILABLE_REASONS,
    PathGovernanceCapabilityStatus,
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    SourceTrustLabel,
    get_path_governance_foundation_status,
    stable_hash,
    to_canonical_dict,
    to_canonical_json,
    validate_known_fields,
)


_FORBIDDEN_RUNTIME_MODULES = frozenset({
    "agentic_runtime.runtime",
    "agentic_runtime.trace",
    "agentic_runtime.sandbox",
    "agentic_runtime.sandbox_policy",
    "agentic_runtime.approval",
    "agentic_runtime.policy",
    "agentic_runtime.tools",
    "agentic_runtime.cli",
})

_ENFORCEMENT_METHOD_NAMES = frozenset({
    "enforce",
    "block",
    "apply",
    "approve",
    "submit",
    "execute",
    "resolve_path",
    "resolve_paths",
    "write_ledger",
})


def _minimal_capability_dict(**overrides: Any) -> dict[str, Any]:
    base = get_path_governance_foundation_status().to_canonical_dict()
    base.update(overrides)
    return base


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert pg.__all__
    status = get_path_governance_foundation_status()
    assert status.module_name == "path_governance"


def test_projection_source_labels_are_distinct_and_json_safe() -> None:
    values = [label.value for label in ProjectionSourceLabel]
    assert len(values) == len(set(values))
    payload = {"labels": values}
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["labels"] == values


def test_source_trust_labels_are_distinct_and_json_safe() -> None:
    values = [label.value for label in SourceTrustLabel]
    assert len(values) == len(set(values))
    payload = {"labels": values}
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["labels"] == values


def test_source_label_and_trust_label_are_not_confused() -> None:
    assert ProjectionSourceLabel is not SourceTrustLabel
    projection_values = {label.value for label in ProjectionSourceLabel}
    trust_values = {label.value for label in SourceTrustLabel}
    assert projection_values != trust_values
    assert "LIVE" in projection_values
    assert "LIVE" not in trust_values
    assert "TRUSTED" in trust_values
    assert "TRUSTED" not in projection_values


def test_capability_status_reports_p1_7_0_truth() -> None:
    status = get_path_governance_foundation_status()
    assert status.module_name == "path_governance"
    assert status.module_version == "p1.7.0"
    assert status.task_id == "P1.7.0"
    assert status.posture is FoundationPosture.FOUNDATION_ONLY
    assert status.enforcement_enabled is False
    assert status.resolver_available is False
    assert status.projection_available is False
    assert status.cli_available is False
    assert status.trace_hook_available is False
    assert status.policy_bridge_available is False
    assert status.source_label is ProjectionSourceLabel.UNAVAILABLE


def test_capability_status_has_unavailable_reasons() -> None:
    status = get_path_governance_foundation_status()
    assert status.unavailable_reasons == PATH_GOVERNANCE_UNAVAILABLE_REASONS
    assert status.unavailable_reasons["Resolver"] == (
        "Path/source resolvers scheduled for P1.7.10 and P1.7.11"
    )
    assert status.unavailable_reasons["Policy bridge"] == (
        "Policy context bridge scheduled for P1.7.16"
    )


def test_canonical_json_is_deterministic() -> None:
    status = get_path_governance_foundation_status()
    first = to_canonical_json(status)
    second = to_canonical_json(status)
    assert first == second
    assert json.loads(first) == to_canonical_dict(status)


def test_stable_hash_is_deterministic() -> None:
    status = get_path_governance_foundation_status()
    first = stable_hash(status)
    second = stable_hash(status)
    assert first == second
    assert len(first) == 64


def test_closed_world_validation_rejects_unknown_fields() -> None:
    payload = _minimal_capability_dict(shadow_authority_grant=True)
    with pytest.raises(PathGovernanceUnknownFieldError):
        PathGovernanceCapabilityStatus.from_dict(payload)

    raw = {"known": "value", "shadow_authority_grant": True}
    with pytest.raises(PathGovernanceUnknownFieldError):
        validate_known_fields(raw, frozenset({"known"}), label="test_payload")


def test_no_resolver_or_enforcement_claims_exist() -> None:
    status = get_path_governance_foundation_status()
    assert status.enforcement_enabled is False
    assert status.resolver_available is False
    assert status.projection_available is False

    import agentic_runtime.path_governance as pg

    for name in pg.__all__:
        obj = getattr(pg, name)
        if inspect.isclass(obj):
            methods = {
                member
                for member, _ in inspect.getmembers(obj, predicate=inspect.isfunction)
            }
            assert not _ENFORCEMENT_METHOD_NAMES & methods

    module_names = [
        info.name
        for info in pkgutil.iter_modules(pg.__path__, prefix=f"{pg.__name__}.")
    ]
    for module_name in module_names:
        module = importlib.import_module(module_name)
        source = inspect.getsource(module)
        assert "resolver_available = True" not in source
        assert "enforcement_enabled = True" not in source


def test_no_runtime_boundary_imports() -> None:
    loaded_modules = [
        name
        for name in sys.modules
        if name.startswith("agentic_runtime.path_governance")
    ]
    assert loaded_modules

    for module_name in loaded_modules:
        module = sys.modules[module_name]
        for attr_name in dir(module):
            obj = getattr(module, attr_name, None)
            if obj is None or not hasattr(obj, "__module__"):
                continue
            imported_module = getattr(obj, "__module__", "")
            for forbidden in _FORBIDDEN_RUNTIME_MODULES:
                assert not imported_module.startswith(forbidden)

    import agentic_runtime.path_governance as pg

    source_files = [
        inspect.getsource(importlib.import_module(name))
        for name in [
            pg.__name__,
            f"{pg.__name__}.labels",
            f"{pg.__name__}.types",
            f"{pg.__name__}.errors",
            f"{pg.__name__}.validation",
            f"{pg.__name__}.serialization",
            f"{pg.__name__}.foundation",
        ]
    ]
    forbidden_import_snippets = (
        "from agentic_runtime.runtime",
        "from agentic_runtime.trace",
        "from agentic_runtime.sandbox",
        "from agentic_runtime.approval",
        "from agentic_runtime.policy",
        "from agentic_runtime.tools",
        "from agentic_runtime.cli",
    )
    for source in source_files:
        for snippet in forbidden_import_snippets:
            assert snippet not in source

    assert CAPABILITY_STATUS_KNOWN_FIELDS == frozenset({
        "module_name",
        "module_version",
        "task_id",
        "posture",
        "enforcement_enabled",
        "resolver_available",
        "projection_available",
        "cli_available",
        "trace_hook_available",
        "policy_bridge_available",
        "source_label",
        "unavailable_reasons",
        "notes",
    })

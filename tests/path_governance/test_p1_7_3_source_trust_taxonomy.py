"""P1.7.3 — Source Trust Label Taxonomy tests."""
from __future__ import annotations

import importlib
import inspect

import pytest

from agentic_runtime.path_governance import (
    PathGovernanceUnknownFieldError,
    ProjectionSourceLabel,
    SourceTrustLabel,
    SourceTrustTaxonomy,
    TrustLabelDefinition,
    TrustPosture,
    build_source_trust_taxonomy,
    to_canonical_json,
)


_REQUIRED_TRUST_POSTURES = {
    "HIGH_CONFIDENCE",
    "OPERATOR_ANCHORED",
    "INTERNAL_CONTEXT",
    "LOCAL_CONTEXT",
    "GENERATED_CONTEXT",
    "EXTERNAL_CONTEXT",
    "LOW_TRUST",
    "UNKNOWN_TRUST",
    "QUARANTINED_CONTEXT",
}

_RESOLVER_OR_ENFORCEMENT_METHOD_NAMES = {
    "allow",
    "deny",
    "enforce",
    "permission",
    "can_inform",
    "can_write_memory",
    "can_command",
    "resolve_trust",
    "resolve_source_trust",
    "resolve_authority",
    "write_ledger",
    "approve",
    "submit",
}

_AUTHORITY_FIELD_NAMES = {
    "memory_authority",
    "prompt_authority",
    "tool_permission",
    "command_authority",
}

_FORBIDDEN_IMPORT_SNIPPETS = (
    "from agentic_runtime.runtime",
    "from agentic_runtime.trace",
    "from agentic_runtime.sandbox",
    "from agentic_runtime.sandbox_policy",
    "from agentic_runtime.approval",
    "from agentic_runtime.policy",
    "from agentic_runtime.tools",
    "from agentic_runtime.cli",
)


def _taxonomy() -> SourceTrustTaxonomy:
    return build_source_trust_taxonomy(source_label=ProjectionSourceLabel.DEV_FIXTURE)


def _definition(label: SourceTrustLabel) -> TrustLabelDefinition:
    definitions = {item.label: item for item in _taxonomy().definitions}
    return definitions[label]


def _joined(values: tuple[str, ...]) -> str:
    return " ".join(values).lower()


def test_package_imports_cleanly() -> None:
    import agentic_runtime.path_governance as pg

    assert TrustPosture is pg.TrustPosture
    assert TrustLabelDefinition is pg.TrustLabelDefinition
    assert SourceTrustTaxonomy is pg.SourceTrustTaxonomy
    assert build_source_trust_taxonomy is pg.build_source_trust_taxonomy


def test_trust_posture_has_required_values() -> None:
    assert {item.value for item in TrustPosture} == _REQUIRED_TRUST_POSTURES


def test_trust_label_definition_can_be_built() -> None:
    definition = TrustLabelDefinition(
        label=SourceTrustLabel.TRUSTED,
        definition="Source is explicitly trusted for semantic classification only.",
        default_posture=TrustPosture.HIGH_CONFIDENCE,
        allowed_interpretations=("may be cited with trust label",),
        forbidden_interpretations=("may not grant command authority",),
        authority_statement="TRUSTED does not mean unlimited authority.",
        requires_review_by_default=False,
        metadata={"fixture": "DEV_FIXTURE"},
    )

    assert definition.definition_hash
    assert len(definition.definition_hash) == 64
    assert "definition_hash" in to_canonical_json(definition)


def test_source_trust_taxonomy_can_be_built() -> None:
    taxonomy = _taxonomy()

    assert isinstance(taxonomy, SourceTrustTaxonomy)
    assert taxonomy.taxonomy_version == "source_trust_taxonomy.v1"
    assert taxonomy.taxonomy_hash
    assert len(taxonomy.taxonomy_hash) == 64
    assert taxonomy.source_label is ProjectionSourceLabel.DEV_FIXTURE


def test_taxonomy_includes_every_source_trust_label() -> None:
    taxonomy = _taxonomy()
    labels = [definition.label for definition in taxonomy.definitions]

    assert set(labels) == set(SourceTrustLabel)
    assert len(labels) == len(set(labels))


def test_every_definition_has_allowed_interpretations() -> None:
    assert all(item.allowed_interpretations for item in _taxonomy().definitions)


def test_every_definition_has_forbidden_interpretations() -> None:
    assert all(item.forbidden_interpretations for item in _taxonomy().definitions)


def test_every_definition_has_authority_statement() -> None:
    assert all(item.authority_statement for item in _taxonomy().definitions)


def test_trusted_does_not_imply_unlimited_authority() -> None:
    trusted = _definition(SourceTrustLabel.TRUSTED)
    forbidden = _joined(trusted.forbidden_interpretations)
    methods = {
        name
        for name, _ in inspect.getmembers(TrustLabelDefinition, predicate=inspect.isfunction)
    }

    assert "TRUSTED does not mean unlimited authority" in trusted.authority_statement
    for boundary in ("bypass policy", "grant tool permission", "override", "command"):
        assert boundary in forbidden
    assert not _RESOLVER_OR_ENFORCEMENT_METHOD_NAMES & methods


def test_operator_provided_does_not_override_policy() -> None:
    operator = _definition(SourceTrustLabel.OPERATOR_PROVIDED)
    boundary = f"{operator.authority_statement} {_joined(operator.forbidden_interpretations)}"

    assert "does not override policy" in boundary
    assert "may override system/developer/governance policy" in boundary


def test_internal_repo_does_not_imply_executable_safe() -> None:
    internal = _definition(SourceTrustLabel.INTERNAL_REPO)
    forbidden = _joined(internal.forbidden_interpretations)

    assert "does not mean executable-safe" in internal.authority_statement
    assert "executed because it is internal" in forbidden
    assert "bypass sandbox" in forbidden


def test_local_private_does_not_mean_safe_to_expose() -> None:
    local = _definition(SourceTrustLabel.LOCAL_PRIVATE)
    forbidden = _joined(local.forbidden_interpretations)

    assert "does not mean safe to expose" in local.authority_statement
    assert "exposed externally" in forbidden
    assert "network services automatically" in forbidden


def test_tool_generated_does_not_imply_truth() -> None:
    generated = _definition(SourceTrustLabel.TOOL_GENERATED)
    boundary = f"{generated.authority_statement} {_joined(generated.forbidden_interpretations)}"

    assert "does not mean true" in boundary
    assert "assumed true" in boundary


def test_external_can_inform_but_cannot_command() -> None:
    external = _definition(SourceTrustLabel.EXTERNAL)
    allowed = _joined(external.allowed_interpretations)
    forbidden = _joined(external.forbidden_interpretations)

    assert "may inform" in allowed
    assert "summarized" in allowed
    assert "cited" in allowed
    assert "cannot command" in external.authority_statement
    for boundary in ("command", "grant permissions", "redefine policy"):
        assert boundary in forbidden


def test_untrusted_can_be_identified_but_cannot_command() -> None:
    untrusted = _definition(SourceTrustLabel.UNTRUSTED)
    allowed = _joined(untrusted.allowed_interpretations)
    forbidden = _joined(untrusted.forbidden_interpretations)

    assert "identified" in allowed
    assert "quoted" in allowed
    assert "summarized defensively" in allowed
    assert "cannot command" in untrusted.authority_statement
    for boundary in ("command", "grant authority", "write memory"):
        assert boundary in forbidden


def test_unknown_is_explicit_not_silently_trusted() -> None:
    unknown = _definition(SourceTrustLabel.UNKNOWN)
    forbidden = _joined(unknown.forbidden_interpretations)

    assert "cannot be confidently classified" in unknown.definition
    assert "explicit uncertainty, not implicit trust" in unknown.authority_statement
    assert "silently treated as trusted" in forbidden
    assert "command" in forbidden
    assert "grant permissions" in forbidden


def test_quarantined_is_restricted_not_deleted() -> None:
    quarantined = _definition(SourceTrustLabel.QUARANTINED)
    boundary = f"{quarantined.definition} {quarantined.authority_statement}"
    forbidden = _joined(quarantined.forbidden_interpretations)

    assert "restricted" in boundary
    assert "not deleted" in boundary
    assert "ordinary prompt context" in forbidden
    assert "command" in forbidden
    assert "executed" in forbidden


def test_taxonomy_hash_is_deterministic() -> None:
    first = _taxonomy()
    second = _taxonomy()

    assert first.taxonomy_hash == second.taxonomy_hash
    assert to_canonical_json(first) == to_canonical_json(second)


def test_taxonomy_hash_is_order_insensitive_where_possible() -> None:
    taxonomy = _taxonomy()
    reordered = SourceTrustTaxonomy(
        definitions=tuple(reversed(taxonomy.definitions)),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert taxonomy.taxonomy_hash == reordered.taxonomy_hash
    assert [item.label.value for item in reordered.definitions] == sorted(
        item.label.value for item in taxonomy.definitions
    )


def test_changed_definition_changes_hash() -> None:
    taxonomy = _taxonomy()
    trusted = _definition(SourceTrustLabel.TRUSTED)
    changed = TrustLabelDefinition(
        label=trusted.label,
        definition=trusted.definition,
        default_posture=trusted.default_posture,
        allowed_interpretations=trusted.allowed_interpretations,
        forbidden_interpretations=trusted.forbidden_interpretations + (
            "may not secretly become resolver approval",
        ),
        authority_statement=trusted.authority_statement,
        requires_review_by_default=trusted.requires_review_by_default,
    )
    changed_taxonomy = SourceTrustTaxonomy(
        definitions=tuple(
            changed if item.label is SourceTrustLabel.TRUSTED else item
            for item in taxonomy.definitions
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
    )

    assert trusted.definition_hash != changed.definition_hash
    assert taxonomy.taxonomy_hash != changed_taxonomy.taxonomy_hash


def test_unknown_fields_are_rejected() -> None:
    taxonomy = _taxonomy()
    definition_payload = taxonomy.definitions[0].to_canonical_dict()
    definition_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as definition_error:
        TrustLabelDefinition.from_dict(definition_payload)
    assert definition_error.value.code.value == "UNKNOWN_FIELD"

    taxonomy_payload = taxonomy.to_canonical_dict()
    taxonomy_payload["shadow_authority_grant"] = True
    with pytest.raises(PathGovernanceUnknownFieldError) as taxonomy_error:
        SourceTrustTaxonomy.from_dict(taxonomy_payload)
    assert taxonomy_error.value.code.value == "UNKNOWN_FIELD"


def test_taxonomy_does_not_expose_resolver_or_enforcement() -> None:
    import agentic_runtime.path_governance as pg

    assert "source_trust_resolver" not in pg.__all__
    assert "source_authority_resolver" not in pg.__all__
    assert "resolve_source_trust" not in pg.__all__

    for cls in (TrustLabelDefinition, SourceTrustTaxonomy):
        methods = {
            name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        }
        assert not _RESOLVER_OR_ENFORCEMENT_METHOD_NAMES & methods

    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_trust_taxonomy",
    ))
    assert "AgenticRuntime.submit" not in source
    for snippet in _FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in source


def test_no_memory_prompt_tool_authority_is_granted() -> None:
    taxonomy = _taxonomy()
    taxonomy_payload = taxonomy.to_canonical_dict()
    definition_payload = taxonomy.definitions[0].to_canonical_dict()

    assert not _AUTHORITY_FIELD_NAMES & set(taxonomy_payload)
    assert not _AUTHORITY_FIELD_NAMES & set(definition_payload)
    for cls in (TrustLabelDefinition, SourceTrustTaxonomy):
        assert not _AUTHORITY_FIELD_NAMES & set(getattr(cls, "__annotations__", {}))


def test_no_network_or_filesystem_reads_occur() -> None:
    source = inspect.getsource(importlib.import_module(
        "agentic_runtime.path_governance.source_trust_taxonomy",
    ))
    forbidden_snippets = (
        "urlopen(",
        "requests.",
        "httpx.",
        "read_text(",
        ".read(",
        ".stat(",
        ".resolve(",
        "open(",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source

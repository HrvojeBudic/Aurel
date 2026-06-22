"""Policy Card deterministic canonical serialization (P1.6.0).

Produces a stable, sorted-key canonical representation suitable for
deterministic hashing and comparison. Same logical policy card always
produces the same canonical output.

Architectural law:
  - Same logical card → same canonical serialization → same canonical hash.
  - No unordered dict output, no runtime object addresses, no non-deterministic
    timestamps in canonical representation.
"""
from __future__ import annotations

import json
from typing import Any

from .models import (
    PolicyCard,
    PolicyCardAuthorityBinding,
    PolicyCardIdentity,
    PolicyCardRiskBinding,
    PolicyCardScope,
    PolicyCardSource,
)


def _identity_to_dict(identity: PolicyCardIdentity) -> dict[str, Any]:
    return {
        "card_id": identity.card_id,
        "name": identity.name,
        "namespace": identity.namespace,
        "slug": identity.slug,
        "version": identity.version,
    }


def _scope_to_dict(scope: PolicyCardScope) -> dict[str, Any]:
    result: dict[str, Any] = {
        "scope_type": scope.scope_type.value,
    }
    if scope.scope_id is not None:
        result["scope_id"] = scope.scope_id
    if scope.applies_to:
        result["applies_to"] = list(scope.applies_to)
    return result


def _risk_binding_to_dict(rb: PolicyCardRiskBinding) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if rb.risk_tier is not None:
        result["risk_tier"] = rb.risk_tier
    if rb.risk_floor is not None:
        result["risk_floor"] = rb.risk_floor
    if rb.risk_ceiling is not None:
        result["risk_ceiling"] = rb.risk_ceiling
    if rb.requires_oversight:
        result["requires_oversight"] = rb.requires_oversight
    return result


def _authority_binding_to_dict(ab: PolicyCardAuthorityBinding) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if ab.authority_scope is not None:
        result["authority_scope"] = ab.authority_scope
    if ab.required_authority is not None:
        result["required_authority"] = ab.required_authority
    if ab.operator_required:
        result["operator_required"] = ab.operator_required
    if ab.delegation_allowed:
        result["delegation_allowed"] = ab.delegation_allowed
    return result


def _source_to_dict(source: PolicyCardSource) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source_type": source.source_type,
    }
    if source.source_path is not None:
        result["source_path"] = source.source_path
    # raw_source_hash is deliberately excluded — it represents the raw
    # input bytes, not the canonical logical content. Including it would
    # make the canonical hash dependent on non-semantic formatting.
    if source.canonical_hash is not None:
        result["canonical_hash"] = source.canonical_hash
    if source.loaded_at is not None:
        result["loaded_at"] = source.loaded_at
    return result


def _metadata_to_dict(metadata: dict[str, Any]) -> dict[str, Any]:
    """Produce sorted metadata dict."""
    if not metadata:
        return {}
    return dict(sorted(metadata.items(), key=lambda item: item[0]))


def policy_card_to_canonical_dict(card: PolicyCard) -> dict[str, Any]:
    """Convert a PolicyCard to a sorted-key deterministic primitive dict.

    Fields are sorted alphabetically for stable JSON output. None/Optional
    values are omitted rather than included as null.
    """
    canonical: dict[str, Any] = {
        "description": card.description,
        "identity": _identity_to_dict(card.identity),
        "kind": card.kind.value,
        "metadata": _metadata_to_dict(dict(card.metadata)),
        "schema_version": card.schema_version,
        "scope": _scope_to_dict(card.scope),
        "status": card.status.value,
    }

    if card.risk_binding is not None:
        rb_dict = _risk_binding_to_dict(card.risk_binding)
        if rb_dict:
            canonical["risk_binding"] = rb_dict

    if card.authority_binding is not None:
        ab_dict = _authority_binding_to_dict(card.authority_binding)
        if ab_dict:
            canonical["authority_binding"] = ab_dict

    if card.source is not None:
        canonical["source"] = _source_to_dict(card.source)

    # Sort top-level keys for deterministic output
    return dict(sorted(canonical.items(), key=lambda item: item[0]))


def serialize_policy_card_canonical(card: PolicyCard) -> str:
    """Produce deterministic canonical JSON string for a PolicyCard.

    Uses sorted keys and compact separators. The output is stable
    across equivalent policy cards.
    """
    canonical = policy_card_to_canonical_dict(card)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))

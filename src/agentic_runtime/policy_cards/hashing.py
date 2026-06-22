"""Policy Card canonical hashing (P1.6.0).

Computes a deterministic SHA-256 hash of the canonical serialized
representation. Same logical policy card always produces the same hash.

Architectural law:
  - Raw source hash and canonical hash are conceptually separate.
  - Raw YAML text is not authority — only canonical typed representation is.
"""
from __future__ import annotations

import hashlib

from .models import PolicyCard
from .serialization import serialize_policy_card_canonical


def compute_policy_card_hash(card: PolicyCard) -> str:
    """Compute deterministic SHA-256 hex digest of canonical policy card.

    Uses canonical serialization (sorted keys, compact JSON) as the
    hash input. Returns the hex digest string.
    """
    canonical = serialize_policy_card_canonical(card)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

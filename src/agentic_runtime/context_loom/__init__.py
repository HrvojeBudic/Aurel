"""
context_loom — F4.0 governed context assembly (ContextLoom).

Upgrades plain context concatenation into a governed mechanism: every context
item carries provenance (F3.0 ``SourceKind`` + taint), assembly is deterministic
and budget-aware with no silent loss, and each bundle carries a ``context_ref``
(content hash) — the Front Signal reference and the trace/replay key. External-
origin items are data-only: rendered fenced as untrusted data, never as
instructions.

The umbrella flag ``AUREL_CONTEXTLOOM`` is defined here. In F4.0 it is defined-
not-gating (the Loom is a pure library, opt-in by call); it becomes load-bearing
when the entity loop routes context assembly through it (F4.3).
"""
from __future__ import annotations

import os

from .context_item import ContextItem, estimate_tokens, make_context_item
from .loom import ContextBundle, DroppedItem, assemble

_FLAG = "AUREL_CONTEXTLOOM"


def flag_enabled() -> bool:
    """True iff the ContextLoom flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


__all__ = [
    "ContextItem",
    "make_context_item",
    "estimate_tokens",
    "ContextBundle",
    "DroppedItem",
    "assemble",
    "flag_enabled",
]

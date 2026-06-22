"""Identity taxonomy types and notes for Agent Identity Card (P1.4.7)."""
from __future__ import annotations

from typing import Literal

IdentityType = Literal["model", "agent", "workload", "delegated", "human"]

TAXONOMY_NOT_IMPLEMENTED_NOTES: dict[str, str] = {
    "model_identity": "model_identity is not implemented in P1.4.7",
    "workload_identity": "workload_identity is not implemented in P1.4.7",
    "delegated_identity": "delegated_identity is not implemented in P1.4.7",
}


def taxonomy_notes_for_null_fields(
    model_identity: str | None,
    workload_identity: str | None,
    delegated_identity: str | None,
) -> tuple[str, ...]:
    """Return notes for null taxonomy placeholders (P1.4.7)."""
    notes: list[str] = []
    if model_identity is None:
        notes.append(TAXONOMY_NOT_IMPLEMENTED_NOTES["model_identity"])
    if workload_identity is None:
        notes.append(TAXONOMY_NOT_IMPLEMENTED_NOTES["workload_identity"])
    if delegated_identity is None:
        notes.append(TAXONOMY_NOT_IMPLEMENTED_NOTES["delegated_identity"])
    return tuple(notes)

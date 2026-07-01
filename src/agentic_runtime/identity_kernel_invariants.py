"""P1.ENF-D1 Identity Kernel invariant discovery read model."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .identity.kernel import (
    AurelIdentityKernel,
    IdentityInvariant,
    default_identity_kernel_path,
    load_identity_kernel,
)

SELECTED_INVARIANT_IDS: tuple[str, ...] = ("IK-002", "IK-005", "IK-006", "IK-007")

CANONICAL_IDENTITY_KERNEL_SOURCE = "config/aurel/identity_kernel.yaml"


@dataclass(frozen=True)
class IdentityKernelSource:
    path: str
    schema_version: str
    format: str = "yaml"

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "path": self.path,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class IdentityKernelInvariantRecord:
    invariant_id: str
    key: str
    title: str
    statement: str
    expected_value: bool
    severity: str
    violation_action: str
    rationale: str
    source_path: str
    enforcement_reason: str
    selected_for_enforcement: bool

    @classmethod
    def from_kernel_invariant(
        cls,
        invariant: IdentityInvariant,
        *,
        source_path: str,
        selected: bool,
    ) -> IdentityKernelInvariantRecord:
        return cls(
            invariant_id=invariant.id,
            key=invariant.key,
            title=invariant.key,
            statement=invariant.statement,
            expected_value=invariant.expected_value,
            severity=invariant.severity,
            violation_action=invariant.violation_action,
            rationale=invariant.rationale,
            source_path=source_path,
            enforcement_reason=_enforcement_reason(invariant.id),
            selected_for_enforcement=selected,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "enforcement_reason": self.enforcement_reason,
            "expected_value": self.expected_value,
            "invariant_id": self.invariant_id,
            "key": self.key,
            "rationale": self.rationale,
            "selected_for_enforcement": self.selected_for_enforcement,
            "severity": self.severity,
            "source_path": self.source_path,
            "statement": self.statement,
            "title": self.title,
            "violation_action": self.violation_action,
        }


@dataclass(frozen=True)
class IdentityKernelDiscoveryResult:
    source: IdentityKernelSource
    invariants: tuple[IdentityKernelInvariantRecord, ...]
    selected_invariant_ids: tuple[str, ...]
    ik_ids_found: tuple[str, ...]
    unavailable_invariants: tuple[str, ...]

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "ik_ids_found": list(self.ik_ids_found),
            "invariants": [item.to_canonical_dict() for item in self.invariants],
            "selected_invariant_ids": list(self.selected_invariant_ids),
            "source": self.source.to_canonical_dict(),
            "unavailable_invariants": list(self.unavailable_invariants),
        }


def _enforcement_reason(invariant_id: str) -> str:
    reasons = {
        "IK-002": "Submit must not allow self-authority escalation or impersonation.",
        "IK-005": "Submit must not allow self-granted policy bypass.",
        "IK-006": "Submit must not allow untrusted input to mutate identity or canon.",
        "IK-007": "Submit must not allow operator replacement or impersonation.",
    }
    return reasons.get(invariant_id, "Selected identity kernel invariant enforcement.")


def discover_identity_kernel_invariants(
    *,
    kernel_path: str | Path | None = None,
    selected_ids: tuple[str, ...] = SELECTED_INVARIANT_IDS,
) -> IdentityKernelDiscoveryResult:
    path = Path(kernel_path) if kernel_path is not None else default_identity_kernel_path()
    kernel = load_identity_kernel(path)
    source = IdentityKernelSource(
        path=_repo_relative_path(path),
        schema_version=kernel.schema_version,
    )
    by_id = {item.id: item for item in kernel.invariants}
    ik_ids_found = tuple(sorted(by_id))
    unavailable = tuple(item for item in selected_ids if item not in by_id)
    rel_path = _repo_relative_path(path)
    all_records = tuple(
        IdentityKernelInvariantRecord.from_kernel_invariant(
            invariant,
            source_path=rel_path,
            selected=invariant.id in selected_ids,
        )
        for invariant in kernel.invariants
    )
    return IdentityKernelDiscoveryResult(
        source=source,
        invariants=all_records,
        selected_invariant_ids=tuple(item for item in selected_ids if item in by_id),
        ik_ids_found=ik_ids_found,
        unavailable_invariants=unavailable,
    )


def load_canonical_identity_kernel(
    kernel_path: str | Path | None = None,
) -> AurelIdentityKernel:
    return load_identity_kernel(kernel_path)


def selected_invariants_by_id(
    discovery: IdentityKernelDiscoveryResult,
) -> Mapping[str, IdentityKernelInvariantRecord]:
    return {
        item.invariant_id: item
        for item in discovery.invariants
        if item.selected_for_enforcement
    }


def _repo_relative_path(path: Path) -> str:
    try:
        repo_root = default_identity_kernel_path().resolve().parents[2]
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)

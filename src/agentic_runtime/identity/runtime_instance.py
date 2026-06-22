"""Local runtime instance identity for Agent Identity Card (P1.4.7)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

RUNTIME_INSTANCE_PREFIX = "aurel-runtime-"


@dataclass(frozen=True)
class RuntimeInstanceId:
    """Local non-secret runtime instance identifier."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.startswith(RUNTIME_INSTANCE_PREFIX):
            raise ValueError(
                f"runtime_instance_id must start with {RUNTIME_INSTANCE_PREFIX!r}"
            )
        if len(self.value) <= len(RUNTIME_INSTANCE_PREFIX):
            raise ValueError("runtime_instance_id must include a unique suffix")


def generate_runtime_instance_id() -> RuntimeInstanceId:
    """Generate a local runtime instance id (not a secret or credential)."""
    return RuntimeInstanceId(value=f"{RUNTIME_INSTANCE_PREFIX}{uuid.uuid4()}")

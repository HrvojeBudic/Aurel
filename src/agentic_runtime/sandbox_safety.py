"""P1.ENF-E sandbox backend safety taxonomy and classification."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .sandbox import (
    BubblewrapSandbox,
    DockerSandbox,
    LocalSubprocessSandbox,
    SandboxBackend,
    SandboxMode,
    UnsafeLocalSandbox,
)


class SandboxSafetyClass(str, Enum):
    UNSAFE_LOCAL = "UNSAFE_LOCAL"
    DEV_FIXTURE = "DEV_FIXTURE"
    RESTRICTED_LOCAL = "RESTRICTED_LOCAL"
    SAFE_VERIFIED = "SAFE_VERIFIED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class SandboxBackendKind(str, Enum):
    UNSAFE_LOCAL_SANDBOX = "UnsafeLocalSandbox"
    BUBBLEWRAP_SANDBOX = "BubblewrapSandbox"
    DOCKER_SANDBOX = "DockerSandbox"
    DEV_FIXTURE_BACKEND = "DevFixtureSandbox"
    UNKNOWN = "UnknownSandboxBackend"


# No backend in this repo has completed SAFE_VERIFIED proof in P1.ENF-E scope.
SAFE_VERIFIED_PROOF_REFS: tuple[str, ...] = ()


@dataclass(frozen=True)
class SandboxBackendCapability:
    backend_kind: SandboxBackendKind
    safety_class: SandboxSafetyClass
    mode: str
    is_hard_isolated: bool
    is_security_boundary: bool
    safe_verified_proof_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "backend_kind": self.backend_kind.value,
            "is_hard_isolated": self.is_hard_isolated,
            "is_security_boundary": self.is_security_boundary,
            "limitations": list(self.limitations),
            "mode": self.mode,
            "safe_verified_proof_refs": list(self.safe_verified_proof_refs),
            "safety_class": self.safety_class.value,
        }


@dataclass(frozen=True)
class SandboxBackendRecord:
    backend_kind: SandboxBackendKind
    safety_class: SandboxSafetyClass
    module_path: str
    notes: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "backend_kind": self.backend_kind.value,
            "module_path": self.module_path,
            "notes": self.notes,
            "safety_class": self.safety_class.value,
        }


def backend_kind_for_instance(backend: SandboxBackend) -> SandboxBackendKind:
    if isinstance(backend, UnsafeLocalSandbox) or isinstance(
        backend, LocalSubprocessSandbox
    ):
        return SandboxBackendKind.UNSAFE_LOCAL_SANDBOX
    if isinstance(backend, BubblewrapSandbox):
        return SandboxBackendKind.BUBBLEWRAP_SANDBOX
    if isinstance(backend, DockerSandbox):
        return SandboxBackendKind.DOCKER_SANDBOX
    class_name = type(backend).__name__
    if class_name.endswith("Sandbox") or "Fixture" in class_name:
        return SandboxBackendKind.DEV_FIXTURE_BACKEND
    return SandboxBackendKind.UNKNOWN


def classify_sandbox_backend(
    backend: SandboxBackend,
    *,
    dev_fixture: bool = False,
) -> SandboxBackendCapability:
    if dev_fixture:
        return SandboxBackendCapability(
            backend_kind=SandboxBackendKind.DEV_FIXTURE_BACKEND,
            safety_class=SandboxSafetyClass.DEV_FIXTURE,
            mode=getattr(backend.mode, "value", str(backend.mode)),
            is_hard_isolated=bool(getattr(backend, "is_hard_isolated", False)),
            is_security_boundary=bool(getattr(backend, "is_security_boundary", False)),
            limitations=("DEV_FIXTURE is not LIVE",),
        )

    kind = backend_kind_for_instance(backend)
    mode = getattr(backend.mode, "value", str(backend.mode))
    hard = bool(getattr(backend, "is_hard_isolated", False))
    boundary = bool(getattr(backend, "is_security_boundary", False))

    if kind is SandboxBackendKind.UNSAFE_LOCAL_SANDBOX:
        return SandboxBackendCapability(
            backend_kind=kind,
            safety_class=SandboxSafetyClass.UNSAFE_LOCAL,
            mode=mode,
            is_hard_isolated=hard,
            is_security_boundary=boundary,
            limitations=(
                UnsafeLocalSandbox.UNSAFE_WARNING,
                "UNSAFE_LOCAL is not LIVE",
                "UNSAFE_LOCAL is not SAFE_VERIFIED",
            ),
        )

    if kind is SandboxBackendKind.DEV_FIXTURE_BACKEND:
        return SandboxBackendCapability(
            backend_kind=kind,
            safety_class=SandboxSafetyClass.DEV_FIXTURE,
            mode=mode,
            is_hard_isolated=hard,
            is_security_boundary=boundary,
            limitations=("DEV_FIXTURE is not LIVE",),
        )

    if kind in {
        SandboxBackendKind.BUBBLEWRAP_SANDBOX,
        SandboxBackendKind.DOCKER_SANDBOX,
    }:
        return SandboxBackendCapability(
            backend_kind=kind,
            safety_class=SandboxSafetyClass.RESTRICTED_LOCAL,
            mode=mode,
            is_hard_isolated=hard,
            is_security_boundary=boundary,
            limitations=(
                "Hard isolation backend — not SAFE_VERIFIED without explicit proof",
            ),
        )

    if kind is SandboxBackendKind.UNKNOWN:
        return SandboxBackendCapability(
            backend_kind=kind,
            safety_class=SandboxSafetyClass.ERROR,
            mode=mode,
            is_hard_isolated=hard,
            is_security_boundary=boundary,
            limitations=("Unknown sandbox backend classification",),
        )

    return SandboxBackendCapability(
        backend_kind=kind,
        safety_class=SandboxSafetyClass.ERROR,
        mode=mode,
        is_hard_isolated=hard,
        is_security_boundary=boundary,
    )


def discover_sandbox_backend_records() -> tuple[SandboxBackendRecord, ...]:
    return (
        SandboxBackendRecord(
            backend_kind=SandboxBackendKind.UNSAFE_LOCAL_SANDBOX,
            safety_class=SandboxSafetyClass.UNSAFE_LOCAL,
            module_path="src/agentic_runtime/sandbox.py",
            notes="Not a security boundary; demo/trusted workloads only",
        ),
        SandboxBackendRecord(
            backend_kind=SandboxBackendKind.BUBBLEWRAP_SANDBOX,
            safety_class=SandboxSafetyClass.RESTRICTED_LOCAL,
            module_path="src/agentic_runtime/sandbox.py",
            notes="Hard isolation when bwrap available; not SAFE_VERIFIED in this pack",
        ),
        SandboxBackendRecord(
            backend_kind=SandboxBackendKind.DOCKER_SANDBOX,
            safety_class=SandboxSafetyClass.RESTRICTED_LOCAL,
            module_path="src/agentic_runtime/sandbox.py",
            notes="Container isolation when docker available; not SAFE_VERIFIED in this pack",
        ),
    )


def resolve_wrapped_sandbox_backend(sandbox: SandboxBackend | Any) -> SandboxBackend:
    inner = getattr(sandbox, "_backend", None)
    if inner is not None:
        return inner
    return sandbox


def safety_class_allows_live_claim(safety_class: SandboxSafetyClass) -> bool:
    return safety_class is SandboxSafetyClass.SAFE_VERIFIED


def mode_from_profile_name(profile_name: str | None) -> str:
    if not profile_name:
        return SandboxMode.UNSAFE_LOCAL.value
    return profile_name.strip().lower()

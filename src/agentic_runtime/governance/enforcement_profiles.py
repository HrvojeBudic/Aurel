"""Enforcement profiles (F1) — named bundles over the G0–G5 governance scale.

A profile resolves a name (``dev`` / ``standard`` / ``hardened``) into the full
coherent set of ``build_runtime`` knobs that a governance level actually needs to
run. G2 (standard) is ENFORCE_FAIL_CLOSED, which requires an identity context, a
policy-card registry, and a restricted-or-safe sandbox backend; a profile
guarantees all three are wired so the level is runnable, not self-blocking.

This module reads ``config/aurel/enforcement_profiles.yaml`` (stdlib-only) and
maps each profile to concrete kwargs via :func:`profile_build_kwargs`. It does
*not* mutate global state — feature flags that are read from the environment
(durable memory, dual kernel) are surfaced on the :class:`ProfileSpec` and
applied separately at process entry by :func:`profile_process_env`, so the
library ``build_runtime(profile=…)`` path stays free of cross-call leakage.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import MutableMapping, Optional

from ..yaml_minimal import load_yaml
from .profile import GovernanceLevel, governed_approver, profile_for

PROFILE_ENV = "AUREL_PROFILE"
TRACE_DIR_ENV = "AUREL_TRACE_DIR"
DURABLE_MEMORY_ENV = "AUREL_DURABLE_MEMORY"
DUAL_KERNEL_ENV = "AUREL_DUAL_KERNEL"
ALLOW_MOCK_FALLBACK_ENV = "AUREL_ALLOW_MOCK_FALLBACK"

_SANDBOX_HARD = "hard"
_SANDBOX_UNSAFE_OK = "unsafe_ok"


class EnforcementProfileError(ValueError):
    """Raised for an unknown profile name or a malformed profiles document."""


def default_enforcement_profiles_path() -> Path:
    """Canonical repo-root path to enforcement_profiles.yaml."""
    return Path(__file__).resolve().parents[3] / "config" / "aurel" / "enforcement_profiles.yaml"


@dataclass(frozen=True)
class ProfileSpec:
    """A resolved enforcement profile — a coherent point on the G-scale."""

    name: str
    level: GovernanceLevel
    require_hard_sandbox: bool
    allow_unsafe: bool
    durable_memory: bool
    dual_kernel: bool
    banner: str
    # F2: whether an implicitly-defaulted mock provider may silently answer.
    # dev keeps today's behavior; standard/hardened fail honestly without a key.
    allow_mock_fallback: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level.value,
            "require_hard_sandbox": self.require_hard_sandbox,
            "allow_unsafe": self.allow_unsafe,
            "durable_memory": self.durable_memory,
            "dual_kernel": self.dual_kernel,
            "banner": self.banner,
            "allow_mock_fallback": self.allow_mock_fallback,
        }


def _spec_from_entry(name: str, entry: dict) -> ProfileSpec:
    try:
        level = GovernanceLevel(str(entry["level"]).strip())
    except (KeyError, ValueError) as exc:
        raise EnforcementProfileError(
            f"profile {name!r}: missing or invalid 'level'") from exc
    sandbox = str(entry.get("sandbox", _SANDBOX_HARD)).strip().lower()
    if sandbox not in (_SANDBOX_HARD, _SANDBOX_UNSAFE_OK):
        raise EnforcementProfileError(
            f"profile {name!r}: 'sandbox' must be 'hard' or 'unsafe_ok', got {sandbox!r}")
    return ProfileSpec(
        name=name,
        level=level,
        require_hard_sandbox=sandbox == _SANDBOX_HARD,
        allow_unsafe=sandbox == _SANDBOX_UNSAFE_OK,
        durable_memory=bool(entry.get("durable_memory", False)),
        dual_kernel=bool(entry.get("dual_kernel", False)),
        banner=str(entry.get("banner", "")),
        allow_mock_fallback=bool(entry.get("allow_mock_fallback", True)),
    )


def load_profiles(path: Optional[Path] = None) -> tuple[dict[str, ProfileSpec], str]:
    """Load all profiles and the declared default name from the yaml document."""
    path = path or default_enforcement_profiles_path()
    document = load_yaml(path.read_text(encoding="utf-8"))
    raw_profiles = document.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise EnforcementProfileError("enforcement_profiles.yaml has no 'profiles' mapping")
    profiles = {name: _spec_from_entry(name, entry) for name, entry in raw_profiles.items()}
    default = str(document.get("default", "standard")).strip()
    if default not in profiles:
        raise EnforcementProfileError(
            f"declared default profile {default!r} is not defined")
    return profiles, default


def resolve_profile_name(
    explicit: Optional[str] = None,
    *,
    profiles: Optional[dict[str, ProfileSpec]] = None,
    default: Optional[str] = None,
) -> str:
    """Resolve the active profile name: explicit arg > AUREL_PROFILE env > yaml default."""
    if profiles is None or default is None:
        profiles, default = load_profiles()
    chosen = (explicit or os.environ.get(PROFILE_ENV, "") or default).strip()
    if chosen not in profiles:
        known = ", ".join(sorted(profiles))
        raise EnforcementProfileError(
            f"unknown enforcement profile {chosen!r}; known profiles: {known}")
    return chosen


def profile_spec(name: Optional[str] = None) -> ProfileSpec:
    """Return the resolved :class:`ProfileSpec` for ``name`` (or the active default)."""
    profiles, default = load_profiles()
    resolved = resolve_profile_name(name, profiles=profiles, default=default)
    return profiles[resolved]


def profile_build_kwargs(
    spec: ProfileSpec,
    *,
    workspace_root: str = ".",
) -> tuple[dict, list[str]]:
    """Translate a profile into ``build_runtime`` kwargs + host limitations.

    Returns the submit-path enforcement bundle only (sandbox, identity, policy,
    enforcement config, approver). Feature flags that are env-read (durable
    memory, dual kernel) are intentionally *not* set here — see
    :func:`profile_process_env`. Every kwarg is a default the caller may override.
    """
    from ..identity_submit_context import load_default_identity_submit_context
    from ..policy_cards.registry import PolicyCardRegistry

    gprofile = profile_for(spec.level)
    limitations: list[str] = []
    kwargs: dict = {
        "approval_gate": governed_approver(gprofile),
        "governance_enforcement_config": gprofile.enforcement_config(),
        "identity_context_loader": load_default_identity_submit_context,
        "policy_card_registry": PolicyCardRegistry(),
        "workspace_root": workspace_root,
    }

    # Trace is the floor of the G-scale — `trace_required` is True at every level,
    # G5 included. A profiled build that kept the in-memory ledger would claim a
    # posture whose own first requirement it fails, so the bundle wires it. The
    # directory stays OUTSIDE the workspace: retained states are addressed by a
    # hash over the whole tree, so a store nested inside it would fold every
    # previous state into the next (see StateStore._reject_nested).
    if gprofile.trace_required:
        kwargs["trace_backend"] = "persistent"
        kwargs["trace_dir"] = os.environ.get(TRACE_DIR_ENV, "") or os.path.expanduser(
            os.path.join("~", ".aurel", "traces"))

    if spec.require_hard_sandbox:
        from ..sandbox_policy import resolve_apply_sandbox_profile

        sandbox_profile, sb_limits = resolve_apply_sandbox_profile()
        kwargs["sandbox_profile"] = sandbox_profile
        limitations.extend(sb_limits)
        if sb_limits:
            # Fell back to restricted_local: under G0–G3 fail-closed the sandbox
            # gate blocks execution. Say so plainly rather than let submits fail
            # one by one with an opaque reason.
            limitations.append(
                f"profile {spec.name!r} requires hard isolation but none is "
                "available; fail-closed submits will be blocked until bubblewrap "
                "or docker is installed (or use the 'dev' profile)")
    else:
        kwargs["allow_unsafe"] = True

    return kwargs, limitations


def profile_process_env(
    spec: ProfileSpec,
    env: Optional[MutableMapping[str, str]] = None,
) -> dict[str, str]:
    """Apply the profile's env-read feature flags as process defaults.

    Uses ``setdefault`` semantics so an explicit environment value always wins
    (the operator override). Intended for CLI/app entry, never for library
    ``build_runtime`` — mutating process env from a builder would leak across
    calls. Returns the flags that were set (for display/audit).

    ``env`` defaults to the real ``os.environ`` (the process); tests pass a
    throwaway mapping so they never mutate the global environment.
    """
    target: MutableMapping[str, str] = os.environ if env is None else env
    applied: dict[str, str] = {}
    if spec.durable_memory and DURABLE_MEMORY_ENV not in target:
        target[DURABLE_MEMORY_ENV] = "1"
        applied[DURABLE_MEMORY_ENV] = "1"
    if spec.dual_kernel and DUAL_KERNEL_ENV not in target:
        target[DUAL_KERNEL_ENV] = "1"
        applied[DUAL_KERNEL_ENV] = "1"
    if not spec.allow_mock_fallback and ALLOW_MOCK_FALLBACK_ENV not in target:
        target[ALLOW_MOCK_FALLBACK_ENV] = "0"
        applied[ALLOW_MOCK_FALLBACK_ENV] = "0"
    return applied

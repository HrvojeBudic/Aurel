"""``agentic-runtime governance`` — the G0–G5 scale surface (M6)."""

from __future__ import annotations

import argparse
import json


def cmd_governance_levels(args: argparse.Namespace) -> int:
    """Print the governance spectrum G0–G5 and each level's gate state."""
    from ..governance.profile import GovernanceLevel, profile_for

    rows = [profile_for(lvl).to_dict() for lvl in GovernanceLevel]
    if getattr(args, "json", False):
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    print("Governance scale  ABSOLUTE GOVERNED (G0) ⟷ HERETIC (G5)")
    print(f"{'lvl':4} {'auto≤':6} {'cap':5} {'enforce':22} {'sbx':4} {'anchor':7} trace")
    for r in rows:
        print(f"{r['level']:4} {r['auto_approve_max']:6} {r['reversibility_cap']:5} "
              f"{r['enforcement_mode']:22} {str(r['sandbox_required']):4} "
              f"{str(r['anchor_required']):7} {r['trace_required']}")
    print("\nFloor (all levels incl. HERETIC): anchored trace on; no self-escalation.")
    return 0


def cmd_governance_audit(args: argparse.Namespace) -> int:
    """Audit a persisted run for drift above its declared governance level."""
    from ..governance import GovernanceLevel, audit_governance
    from ..trace import PersistentTraceLedger

    led = PersistentTraceLedger(
        base_dir=args.trace_dir, run_id=args.run_id, checkpoint_every=args.checkpoint_every
    )
    events = list(led.replay())
    declared = GovernanceLevel(args.declared)
    report = audit_governance(declared, events)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["drift_detected"] else 0


def cmd_profile_show(args: argparse.Namespace) -> int:
    """List enforcement profiles and mark the active one (AUREL_PROFILE / default)."""
    from ..governance.enforcement_profiles import load_profiles, resolve_profile_name

    profiles, default = load_profiles()
    active = resolve_profile_name(getattr(args, "profile", None) or None,
                                  profiles=profiles, default=default)
    if getattr(args, "json", False):
        print(json.dumps({
            "active": active,
            "default": default,
            "profiles": {n: s.to_dict() for n, s in profiles.items()},
        }, indent=2, sort_keys=True))
        return 0
    print(f"Enforcement profiles  (active: {active}; default: {default})")
    print(f"{'':2}{'name':10} {'level':5} {'sandbox':10} {'durable_mem':11} {'dual_kernel':11}")
    for name, s in profiles.items():
        mark = "->" if name == active else "  "
        sandbox = "hard" if s.require_hard_sandbox else "unsafe_ok"
        print(f"{mark}{name:10} {s.level.value:5} {sandbox:10} "
              f"{str(s.durable_memory):11} {str(s.dual_kernel):11}")
        if s.banner:
            print(f"    {s.banner}")
    return 0


def cmd_profile_audit(args: argparse.Namespace) -> int:
    """Audit the active profile for shadow drift: are the enforcement points it
    declares actually wired and active, given this host? With --fail-on-drift the
    command exits non-zero when any declared enforcement is not truly in force —
    the CI gate that keeps 'what the config promises' equal to 'what runs'."""
    from .. import build_runtime
    from ..governance.enforcement_profiles import (profile_build_kwargs,
                                                   profile_spec)
    from ..governance.profile import profile_for
    from ..governance_enforcement import GovernanceEnforcementMode
    from ..sandbox_safety import (SandboxSafetyClass, classify_sandbox_backend,
                                  resolve_wrapped_sandbox_backend)

    spec = profile_spec(getattr(args, "profile", None) or None)
    gprofile = profile_for(spec.level)
    _kwargs, host_limits = profile_build_kwargs(spec, workspace_root=".")
    # drift = config/wiring regressions (a code bug — fails --fail-on-drift).
    # host_limitations = capability the host lacks (e.g. no bubblewrap) — real
    # and reported, but not a code defect, so it fails only under --strict.
    drift: list[str] = []
    host_limitations: list[str] = list(host_limits)

    kernel = build_runtime(profile=spec.name, workspace_root=".")
    rt = kernel.runtime
    expected_mode = gprofile.enforcement_mode
    fail_closed = expected_mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED

    if not rt._governance_enforcement_explicit:
        drift.append("governance enforcement is not wired (shadow-only)")
    if rt.governance_enforcement_config.mode is not expected_mode:
        drift.append(
            f"enforcement mode {rt.governance_enforcement_config.mode.value} "
            f"!= declared {expected_mode.value}")
    if fail_closed:
        if rt.identity_context_loader is None:
            drift.append("fail-closed profile has no identity context loader")
        if rt.policy_card_registry is None:
            drift.append("fail-closed profile has no policy card registry")
        backend = resolve_wrapped_sandbox_backend(rt.tools.sandbox)
        safety = classify_sandbox_backend(backend).safety_class
        if safety in {SandboxSafetyClass.UNSAFE_LOCAL, SandboxSafetyClass.DEV_FIXTURE}:
            # Wiring is correct; the host simply cannot provide hard isolation.
            host_limitations.append(
                f"fail-closed profile requires restricted-or-safe sandbox; "
                f"host provides {safety.value} — execution will be blocked until "
                "bubblewrap or docker is installed")

    strict = getattr(args, "strict", False)
    report = {
        "profile": spec.name,
        "level": spec.level.value,
        "expected_mode": expected_mode.value,
        "enforcement_wired": rt._governance_enforcement_explicit,
        "host_limitations": host_limitations,
        "drift": drift,
        "drift_detected": bool(drift),
        "host_capable": not host_limitations,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if drift and getattr(args, "fail_on_drift", False):
        return 1
    if host_limitations and strict:
        return 1
    return 0

"""Dual Kernel — Custos (govern) / Praxis (execute) with a canon-faithful merge gate.

Additive layer over the existing runtime. Nothing here mutates ``runtime.py`` or
weakens any existing gate. It supplies:

- ``sigma``      — the O(1) governance state-vector Σ (Kaptein path-policies).
- ``routing``    — measured autonomy → execution path (fast / governed / hard).
- ``constraints``— hard / soft split with the ABC bounded-recovery bound.
- ``merge_gate`` — ABC C1–C4 + DSD Book 12 readiness verdict; the only place a
                   speculative worldline becomes LIVE state.
- ``nc_bindings``— machine-readable NC-law ⇄ gate mapping, enforced in CI so the
                   merge gate can never drift from canon.

The one invariant: nothing reaches LIVE source state without a PASS verdict from
the merge gate over real (not claimed) evidence.
"""
from __future__ import annotations

from .constraints import (
    ConstraintSet,
    HardInvariant,
    NoSecretsEgress,
    ProtectedTestIntegrity,
    SoftConstraint,
    WithinAuthorityRisk,
    compliance_lower_bound,
    no_recovery_compliance,
)
from .merge_gate import (
    DeploymentReadinessDecision,
    MergeContext,
    MergeGate,
    MergeVerdict,
)
from .nc_bindings import (
    NCBinding,
    binding_for,
    load_bindings,
    validate_coverage,
)
from .kernel import DualKernelRuntime, RouteRecord
from .ledger import DualKernelEvent, DualKernelLedger
from .praxis import Praxis, SpeculativeOutcome
from .routing import AdmitDecision, Route, autonomy_index, route_for
from .sigma import GovernanceStateVector, SigmaGovernor

__all__ = [
    "GovernanceStateVector",
    "SigmaGovernor",
    "Route",
    "AdmitDecision",
    "autonomy_index",
    "route_for",
    "HardInvariant",
    "SoftConstraint",
    "ConstraintSet",
    "NoSecretsEgress",
    "ProtectedTestIntegrity",
    "WithinAuthorityRisk",
    "compliance_lower_bound",
    "no_recovery_compliance",
    "MergeVerdict",
    "MergeContext",
    "MergeGate",
    "DeploymentReadinessDecision",
    "Praxis",
    "SpeculativeOutcome",
    "DualKernelRuntime",
    "RouteRecord",
    "DualKernelLedger",
    "DualKernelEvent",
    "NCBinding",
    "load_bindings",
    "binding_for",
    "validate_coverage",
]

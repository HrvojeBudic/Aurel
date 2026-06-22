"""
policy.py — The Policy Engine.

Enforces the system law (Hrvoje §12):
    Capability  != Permission
    Tool Access != Authority
    Plan        != Action

Three independent gates, ALL must pass for ALLOW:

  1. CAPABILITY  — does a tool with this name exist & is it registered?
  2. PERMISSION  — does the issuer's AgentCard list this tool (and not deny it)?
  3. AUTHORITY   — does the issuer's AuthorityScope cover the *concrete target*
                   of this command (path, branch, network, secrets, risk)?

Paths are canonicalized via CanonicalPathResolver before authority checks so
``src/../outside.py`` cannot satisfy write authority for ``src/``.

Risk is re-scored by the engine (the entity's self-declared risk is advisory).
``run_tests`` is HIGH without a hard sandbox and never LOW (minimum MEDIUM).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .canonical_path import CanonicalPathResolver, PathResolutionError
from .core_types import AgentCard, CommandEnvelope, PolicyVerdict, RiskLevel
from .sandbox import SandboxBackend
from .test_integrity import (
    MUTATE_PROTECTED_TOOL,
    ProtectedPathPolicy,
)


_RISK_ORDER = {RiskLevel.TRIVIAL: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2,
               RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}

# Tool -> intrinsic risk floor. The engine raises from here based on targets.
_TOOL_RISK = {
    "read_file": RiskLevel.TRIVIAL,
    "list_dir": RiskLevel.TRIVIAL,
    "search_text": RiskLevel.TRIVIAL,
    "git_status": RiskLevel.TRIVIAL,
    "git_diff": RiskLevel.TRIVIAL,
    "search": RiskLevel.TRIVIAL,
    "run_tests": RiskLevel.MEDIUM,
    "run_python": RiskLevel.HIGH,
    "edit_file": RiskLevel.MEDIUM,
    "patch_file": RiskLevel.MEDIUM,
    "write_file": RiskLevel.MEDIUM,
    "run_shell": RiskLevel.HIGH,
    "git_commit": RiskLevel.MEDIUM,
    "delete_file": RiskLevel.HIGH,
    "network_fetch": RiskLevel.HIGH,
    "mutate_protected_verification": RiskLevel.HIGH,
}

_DESTRUCTIVE = {"delete_file", "run_shell"}
_ORDINARY_WRITE_TOOLS = frozenset({"edit_file", "write_file", "patch_file", "delete_file"})


@dataclass
class PolicyDecision:
    verdict: PolicyVerdict
    risk: RiskLevel
    reasons: list[str]

    @property
    def allowed(self) -> bool:
        return self.verdict is PolicyVerdict.ALLOW


def _max_risk(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    return a if _RISK_ORDER[a] >= _RISK_ORDER[b] else b


class PolicyEngine:
    def __init__(self, registered_tools: set[str],
                 sandbox: Optional[SandboxBackend] = None,
                 resolver: Optional[CanonicalPathResolver] = None,
                 protected_policy: Optional[ProtectedPathPolicy] = None,
                 contract_registry=None) -> None:
        self.registered_tools = registered_tools
        self.sandbox = sandbox
        self.resolver = resolver
        self.protected_policy = protected_policy or ProtectedPathPolicy()
        # P0.10: tool contracts declare a side_effect_profile that the engine
        # folds into risk so scoring reflects what a tool *does*, not its name.
        self.contract_registry = contract_registry

    def _resolver_for(self) -> Optional[CanonicalPathResolver]:
        if self.resolver is not None:
            return self.resolver
        if self.sandbox is not None:
            return CanonicalPathResolver(self.sandbox.root)
        return None

    def evaluate(self, cmd: CommandEnvelope, card: AgentCard) -> PolicyDecision:
        reasons: list[str] = []

        # Gate 1: CAPABILITY
        if cmd.tool not in self.registered_tools:
            return PolicyDecision(PolicyVerdict.DENY, RiskLevel.CRITICAL,
                                  [f"capability: tool '{cmd.tool}' not registered"])

        # Gate 2: PERMISSION
        if cmd.tool in card.denied_tools:
            return PolicyDecision(PolicyVerdict.DENY, RiskLevel.CRITICAL,
                                  [f"permission: tool '{cmd.tool}' explicitly denied"])
        if card.allowed_tools and cmd.tool not in card.allowed_tools:
            return PolicyDecision(PolicyVerdict.DENY, RiskLevel.CRITICAL,
                                  [f"permission: tool '{cmd.tool}' not in card scope"])

        # Gate 3: AUTHORITY (target-aware, canonical paths)
        risk = _TOOL_RISK.get(cmd.tool, RiskLevel.MEDIUM)
        # P0.10: fold the contract's declared side-effect profile into risk.
        if self.contract_registry is not None:
            contract = self.contract_registry.get(cmd.tool)
            if contract is not None:
                se_floor = contract.risk_floor()
                if _RISK_ORDER[se_floor] > _RISK_ORDER[risk]:
                    reasons.append(
                        f"side-effect profile raises risk to {se_floor.value}")
                risk = _max_risk(risk, se_floor)
        auth = card.authority
        resolver = self._resolver_for()

        target_path = (cmd.args.get("path") or cmd.args.get("file")
                       or cmd.args.get("root") or cmd.args.get("repo_path"))
        writes = cmd.tool in ("edit_file", "write_file", "patch_file", "delete_file",
                              MUTATE_PROTECTED_TOOL)
        reads = cmd.tool in ("read_file", "list_dir", "search_text",
                             "git_status", "git_diff")

        if target_path and resolver is not None:
            try:
                resolver.resolve(target_path)
            except PathResolutionError as e:
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    [f"authority: path resolution denied — {e.reason}"])

        if target_path and writes:
            if resolver is None:
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    [f"authority: no path resolver; cannot authorize write to '{target_path}'"])
            if not resolver.is_covered_by_prefixes(target_path, auth.write_paths):
                canonical = resolver.resolve(target_path).relative
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    [f"authority: no write authority over '{canonical}'"])

            # P0.4: block protected verification mutation on ordinary tools
            canonical = resolver.resolve(target_path).relative
            if (cmd.tool in _ORDINARY_WRITE_TOOLS
                    and self.protected_policy.is_protected(canonical)):
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    [f"authority: protected verification file '{canonical}' "
                     f"requires tool '{MUTATE_PROTECTED_TOOL}' with explicit approval"])

            if cmd.tool == MUTATE_PROTECTED_TOOL:
                if not self.protected_policy.is_protected(canonical):
                    return PolicyDecision(
                        PolicyVerdict.DENY, RiskLevel.CRITICAL,
                        [f"authority: '{MUTATE_PROTECTED_TOOL}' only for protected paths; "
                         f"'{canonical}' is not protected"])
                if not auth.allow_protected_mutation:
                    return PolicyDecision(
                        PolicyVerdict.DENY, RiskLevel.CRITICAL,
                        ["authority: card lacks allow_protected_mutation"])
                if cmd.args.get("approved") is not True:
                    return PolicyDecision(
                        PolicyVerdict.REQUIRE_APPROVAL, RiskLevel.HIGH,
                        ["protected verification mutation requires approved=true"])
                risk = RiskLevel.HIGH
                reasons.append("approved protected verification mutation")
        if target_path and reads:
            if resolver is None:
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    [f"authority: no path resolver; cannot authorize read of '{target_path}'"])
            if auth.read_paths:
                allowed_read = auth.read_paths
            elif auth.write_paths:
                allowed_read = auth.write_paths
            else:
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    ["authority: no read authority configured (read_paths and write_paths empty)"])
            if not resolver.is_covered_by_prefixes(target_path, allowed_read):
                canonical = resolver.resolve(target_path).relative
                return PolicyDecision(
                    PolicyVerdict.DENY, RiskLevel.CRITICAL,
                    [f"authority: no read authority over '{canonical}'"])

        if cmd.tool == "network_fetch" and not auth.allow_network:
            return PolicyDecision(PolicyVerdict.DENY, RiskLevel.CRITICAL,
                                  ["authority: network disabled for this card"])
        if cmd.args.get("touches_secrets") and not auth.allow_secrets:
            return PolicyDecision(PolicyVerdict.DENY, RiskLevel.CRITICAL,
                                  ["authority: secrets access disabled"])

        # run_tests: HIGH without hard sandbox; never LOW (minimum MEDIUM)
        if cmd.tool == "run_tests":
            hard = bool(self.sandbox and getattr(self.sandbox, "is_hard_isolated", False))
            if hard:
                risk = _max_risk(risk, RiskLevel.MEDIUM)
                reasons.append("run_tests in hard-isolated sandbox (minimum MEDIUM)")
            else:
                risk = RiskLevel.HIGH
                reasons.append("run_tests without hard sandbox — HIGH risk")

        # Risk escalation from concrete targets
        if cmd.tool in _DESTRUCTIVE:
            reasons.append("destructive operation")
        if cmd.args.get("irreversible"):
            risk = RiskLevel.HIGH
            reasons.append("declared irreversible")

        # Compare re-scored risk against the card ceiling
        if _RISK_ORDER[risk] > _RISK_ORDER[auth.max_risk]:
            reasons.append(
                f"risk {risk.value} exceeds card ceiling {auth.max_risk.value}")
            return PolicyDecision(PolicyVerdict.REQUIRE_APPROVAL, risk, reasons)

        if not reasons:
            reasons.append("within capability, permission, and authority")
        return PolicyDecision(PolicyVerdict.ALLOW, risk, reasons)

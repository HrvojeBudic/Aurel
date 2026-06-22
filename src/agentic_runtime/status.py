"""
status.py — Lightweight runtime diagnostics (P0.11).

Reports which sandbox backend is active and which governance subsystems are wired.
"""
from __future__ import annotations

from typing import Any

from . import __version__


def runtime_status(kernel=None, *, build_if_none: bool = True) -> dict[str, Any]:
    """Return a JSON-serializable snapshot of the wired kernel."""
    if kernel is None:
        if not build_if_none:
            raise ValueError("kernel is required when build_if_none=False")
        from . import build_runtime
        kernel = build_runtime()

    sandbox = kernel.sandbox
    mode = getattr(sandbox, "mode", None)
    mode_label = mode.value if mode is not None else type(sandbox).__name__
    sandbox_policy = getattr(kernel, "sandbox_policy", None)
    sandbox_diag = None
    if sandbox_policy is not None:
        sandbox_diag = sandbox_policy.diagnostics(sandbox)

    contracts = getattr(kernel.runtime, "contracts", None)
    contract_count = len(contracts.names) if contracts is not None else 0
    provider_health = {}
    if hasattr(kernel.router, "health"):
        provider_health = {
            profile: [h.__dict__ | {"status": h.status.value} for h in rows]
            for profile, rows in kernel.router.health().items()
        }

    return {
        "version": __version__,
        "sandbox": {
            "backend": sandbox_diag.backend_name if sandbox_diag else type(sandbox).__name__,
            "backend_wrapper": type(sandbox).__name__,
            "mode": mode_label,
            "hard_isolated": bool(getattr(sandbox, "is_hard_isolated", False)),
            "security_boundary": bool(getattr(sandbox, "is_security_boundary", False)),
            "root": getattr(sandbox, "root", ""),
            "profile": sandbox_diag.active_profile if sandbox_diag else "",
            "unsafe": sandbox_diag.unsafe if sandbox_diag else False,
            "policy_restricted": sandbox_diag.policy_restricted if sandbox_diag else False,
            "backend_available": sandbox_diag.backend_available if sandbox_diag else True,
            "read_allowed": sandbox_diag.read_allowed if sandbox_diag else True,
            "write_allowed": sandbox_diag.write_allowed if sandbox_diag else True,
            "exec_allowed": sandbox_diag.exec_allowed if sandbox_diag else True,
            "network_allowed": sandbox_diag.network_allowed if sandbox_diag else False,
            "secrets_allowed": sandbox_diag.secrets_allowed if sandbox_diag else False,
            "limitations": sandbox_diag.limitations if sandbox_diag else [],
        },
        "subsystems": {
            "policy_engine": kernel.policy is not None,
            "verifier": kernel.verifier is not None,
            "trace_ledger": kernel.trace is not None,
            "trace_backend": type(kernel.trace).__name__,
            "memory_governance": hasattr(kernel.memory, "policy"),
            "budget_ledger": kernel.budget is not None,
            "tool_contracts": contracts is not None,
        },
        "tools": {
            "registered_count": len(kernel.tools.registered),
            "contract_count": contract_count,
            "registered": sorted(kernel.tools.registered),
        },
        "model_router": {
            "default_provider": getattr(kernel.router, "default_provider", ""),
            "profiles": provider_health,
        },
        "trace_run_id": getattr(kernel.trace, "run_id", ""),
    }


def format_status(status: dict[str, Any]) -> str:
    """Human-readable status block for CLI / demo."""
    sb = status["sandbox"]
    sub = status["subsystems"]
    tools = status["tools"]
    model = status.get("model_router", {})
    lines = [
        f"agentic-runtime {status['version']}",
        f"sandbox: {sb['backend']} ({sb['mode']})"
        f"  profile={sb.get('profile', '') or 'n/a'}"
        f"  unsafe={sb.get('unsafe', False)}"
        f"  policy_restricted={sb.get('policy_restricted', False)}"
        f"  hard_isolated={sb['hard_isolated']}"
        f"  security_boundary={sb['security_boundary']}",
        f"policy_engine: {'yes' if sub['policy_engine'] else 'no'}",
        f"verifier: {'yes' if sub['verifier'] else 'no'}",
        f"trace: {sub['trace_backend']} (run_id={status.get('trace_run_id', '')})",
        f"memory_governance: {'yes' if sub['memory_governance'] else 'no'}",
        f"budget_ledger: {'yes' if sub['budget_ledger'] else 'no'}",
        f"tool_contracts: {'yes' if sub['tool_contracts'] else 'no'}"
        f"  ({tools['contract_count']} contracts, {tools['registered_count']} tools)",
        f"model_provider: {model.get('default_provider', '')}",
    ]
    return "\n".join(lines)

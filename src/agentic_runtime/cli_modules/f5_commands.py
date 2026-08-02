"""``aurel front serve`` — run the F5 Front server (the one door).

Requires ``AUREL_FRONT_SERVER=1`` (fail-closed otherwise). Binds a stdlib HTTP
server to localhost and serves read projections + the single `POST /proposals`
mutation. Read-only surfaces until later slices thicken them.
"""
from __future__ import annotations

import argparse
import json
import os


def cmd_front_seal(args: argparse.Namespace) -> int:
    """``aurel front seal [--json]`` — the derived F5 exit seal (read-only)."""
    from ..front_seal import build_f5_exit_seal

    seal = build_f5_exit_seal()
    if getattr(args, "json", False):
        print(json.dumps(seal.to_dict(), indent=2))
        return 0 if seal.sealed else 1
    print(f"F5 Front v1 exit seal: {seal.status.value}")
    for item in seal.items:
        mark = "OK " if item.status.value == "PASSED" else "XX "
        print(f"  {mark}{item.slice_id:6} {item.title}")
        if item.status.value != "PASSED":
            print(f"        module_present={item.module_present} "
                  f"report_present={item.report_present}")
    print("  UNAVAILABLE (declared, deferred):")
    for u in seal.unavailable:
        print(f"    - {u.surface_id}: {u.reason} [{u.future_owner}]")
    return 0 if seal.sealed else 1


def cmd_front_demo(args: argparse.Namespace) -> int:
    """``aurel front demo`` — project the north-star run from the trace (read-only)."""
    from .. import build_runtime
    from ..front_projection import FrontRunProjection

    runtime = build_runtime()
    projection = FrontRunProjection(runtime).to_dict()
    print(json.dumps(projection, indent=2))
    return 0


def cmd_aureleu_seal(args: argparse.Namespace) -> int:
    """``aurel aureleu seal [--json]`` — the derived F6 exit seal (read-only)."""
    from ..f6_seal import build_f6_exit_seal

    seal = build_f6_exit_seal()
    if getattr(args, "json", False):
        print(json.dumps(seal.to_dict(), indent=2))
        return 0 if seal.sealed else 1
    print(f"F6 AurelEU/Constitution/mandate exit seal: {seal.status.value}")
    for item in seal.items:
        mark = "OK " if item.status.value == "PASSED" else "XX "
        print(f"  {mark}{item.slice_id:6} {item.title}")
    print("  flipped from F5 (now live):")
    for seam, owner in seal.flipped_from_f5:
        print(f"    + {seam} [{owner}]")
    print("  UNAVAILABLE (declared, deferred):")
    for u in seal.unavailable:
        print(f"    - {u.surface_id}: {u.reason} [{u.future_owner}]")
    return 0 if seal.sealed else 1


def cmd_aureleu_status(args: argparse.Namespace) -> int:
    """``aurel aureleu status`` — project the F6 north-star run from the trace."""
    from .. import build_runtime
    from ..f6_projection import F6RunProjection

    print(json.dumps(F6RunProjection(build_runtime()).to_dict(), indent=2))
    return 0


def cmd_aureleu_panic(args: argparse.Namespace) -> int:
    """``aurel aureleu panic`` — record a governed panic (halt → G0). Never silent."""
    from .. import build_runtime
    from ..dn import panic

    reason = getattr(args, "reason", "") or "operator panic"
    result = panic(build_runtime(), reason, invoked_by="operator")
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def _operator_card(name: str, max_risk: str, scope_prefix: str) -> object:
    """The AgentCard every operator-issued `act` proposal is submitted under.

    Authority prefixes are matched against the **workspace-relative** canonical
    path (`CanonicalPathResolver.is_covered_by_prefixes`), so the default is the
    explicit wildcard `"*"` — "anywhere inside the workspace". That is not a hole:
    the resolver has already refused traversal, absolute host paths and symlink
    escapes before this check, and the sandbox root is the real jail. Narrow it
    with ``--write-scope src`` when a run should only touch one subtree.

    An empty ``allowed_tools`` means "whatever policy permits" rather than a
    hand-maintained allowlist that would drift from the tool registry. The risk
    ceiling is deliberately low: anything above it re-scores to REQUIRE_APPROVAL,
    which the inbox turns into a pending item instead of an execution.
    """
    from ..core_types import (AgentCard, AgentClass, AuthorityScope, RiskLevel,
                              canonical_json, sha)

    prefix = scope_prefix or "*"
    authority = AuthorityScope(
        write_paths=[prefix],
        read_paths=[prefix],
        max_risk=RiskLevel(max_risk),
    )
    mission = "Operator-issued actions from the Aurel Front surface"
    # A CONTENT-DERIVED id, not a per-process uuid. Approvals parked before a
    # restart are re-submitted afterwards, and the id is what proves they are
    # re-submitted under the same authority envelope: change the scope or the
    # ceiling and the id changes, so the stale pending item is refused instead of
    # silently executing under different permissions.
    card_id = "card_" + sha(canonical_json({
        "name": name,
        "class": AgentClass.CORE.value,
        "mission": mission,
        "authority": authority.to_dict(),
    }))[:12]
    return AgentCard(
        id=card_id,
        name=name,
        agent_class=AgentClass.CORE,
        mission=mission,
        authority=authority,
    )


def _profile_chain(router: object, profile_name: str) -> str:
    """`profile→provider/model` with the ranked failover links, for the banner.

    Reporting ``router.default_provider`` here would be a lie: that is only the
    fallback when no config resolves, while an actual turn routes through the
    profile's chain. Falls back to the provider name when no config is loaded.
    """
    try:
        profile = router.select_profile(profile_name)          # type: ignore[attr-defined]
    except Exception:
        return f"{profile_name}→{getattr(router, 'default_provider', '?')}"
    links = [f"{profile.provider}/{profile.model}"]
    links += [f"{link.provider}/{link.model}"
              for link in getattr(profile, "failover", []) or []]
    return f"{profile_name}→" + " → ".join(links)


def cmd_front_serve(args: argparse.Namespace) -> int:
    from .. import build_runtime, workspace_run_id
    from ..front_server import FrontServerDisabled, create_front_server
    from ..front_server.approval_inbox import ApprovalInbox
    from ..front_server.aureleu import AurelEUDispatcher
    from ..front_server.conversation import ConversationEngine
    from ..model_router import ModelRouter

    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 8765)
    # The operator server persists by default: a Front server whose history,
    # approvals and memory vanish on Ctrl-C is not something you can work with.
    # The trace dir lives OUTSIDE the workspace so retained states never nest
    # inside the tree they describe (see StateStore._reject_nested).
    trace_dir = os.path.expanduser(getattr(args, "trace_dir", "") or "~/.aurel/traces")
    trace_backend = getattr(args, "trace_backend", "") or "persistent"
    # The Front server is exactly the long-lived entrypoint that wants ONE
    # continuous run across restarts, so it opts into the workspace identity.
    run_id = getattr(args, "run_id", "") or None
    if trace_backend == "persistent" and not run_id:
        run_id = workspace_run_id()
    try:
        runtime = build_runtime(
            profile=getattr(args, "profile", "") or None,
            trace_backend=trace_backend,
            trace_dir=trace_dir,
            trace_run_id=run_id,
        )
        kernel = getattr(runtime, "runtime", runtime)
        # F5.C — the conversation engine needs a router; the config dir decides
        # which providers exist (the packaged default is offline/mock).
        router = ModelRouter(config_dir=getattr(args, "config_dir", None) or None)
        profile_name = getattr(args, "model_profile", "balanced")
        engine = ConversationEngine(kernel, router, default_profile=profile_name)
        # F5.2 — the two-phase approval queue, shared by the dispatcher (writes)
        # and the read models (pending list).
        card = _operator_card(getattr(args, "operator", "operator"),
                              getattr(args, "max_risk", "low"),
                              getattr(args, "write_scope", "*"))
        # The card is handed to the inbox so items parked by a previous process
        # can be re-bound to the live authority (and refused if it changed).
        inbox = ApprovalInbox(kernel, card=card)
        # F6.4 — persona resolution; the dispatcher only consults it when
        # AUREL_AURELEU is on, so binding it changes nothing while the flag is off.
        server = create_front_server(
            runtime, host=host, port=port,
            conversation_engine=engine, approval_inbox=inbox, card=card,
            aureleu=AurelEUDispatcher(kernel),
        )
    except FrontServerDisabled as e:
        print(f"front serve: {e}")
        print("  enable with: AUREL_FRONT_SERVER=1 aurel front serve")
        return 1
    # flush=True: stdout is block-buffered when redirected to a file/pipe and the
    # process then blocks in serve_forever(), so an unflushed banner never lands —
    # the operator sees an empty log and cannot tell what got bound.
    print(f"aurel front server on http://{server.host}:{server.port}  "
          f"(GET /health, GET /read/{{model}}, POST /proposals)", flush=True)
    print(f"  bound: conversation={_profile_chain(router, profile_name)} "
          f"config={getattr(args, 'config_dir', '') or 'packaged default'} "
          f"approvals=inbox card={card.name} "
          f"ceiling={card.authority.max_risk.value}", flush=True)
    print(f"  trace: {trace_backend} dir={trace_dir} "
          f"run={kernel.trace.run_id}", flush=True)
    print("  Ctrl-C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("\nstopped")
    return 0

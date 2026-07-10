"""``aurel front serve`` — run the F5 Front server (the one door).

Requires ``AUREL_FRONT_SERVER=1`` (fail-closed otherwise). Binds a stdlib HTTP
server to localhost and serves read projections + the single `POST /proposals`
mutation. Read-only surfaces until later slices thicken them.
"""
from __future__ import annotations

import argparse
import json


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


def cmd_front_serve(args: argparse.Namespace) -> int:
    from .. import build_runtime
    from ..front_server import FrontServerDisabled, create_front_server

    try:
        runtime = build_runtime()
        server = create_front_server(
            runtime, host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 8765),
        )
    except FrontServerDisabled as e:
        print(f"front serve: {e}")
        print("  enable with: AUREL_FRONT_SERVER=1 aurel front serve")
        return 1
    print(f"aurel front server on http://{server.host}:{server.port}  "
          f"(GET /health, GET /read/{{model}}, POST /proposals)")
    print("  Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("\nstopped")
    return 0

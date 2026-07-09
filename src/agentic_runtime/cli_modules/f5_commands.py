"""``aurel front serve`` — run the F5 Front server (the one door).

Requires ``AUREL_FRONT_SERVER=1`` (fail-closed otherwise). Binds a stdlib HTTP
server to localhost and serves read projections + the single `POST /proposals`
mutation. Read-only surfaces until later slices thicken them.
"""
from __future__ import annotations

import argparse


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

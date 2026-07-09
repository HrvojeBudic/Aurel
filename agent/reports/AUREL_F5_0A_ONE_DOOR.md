# AUREL F5.0a — "One Door" HTTP Server Foundation

_branch `feat/f5-front-v1`. The single UI↔kernel door, structurally enforced._

## What shipped
A stdlib `ThreadingHTTPServer` (`front_server/server.py`) driven by a declarative route
table (`front_server/routes.py`) where **exactly one** route is a mutation (`POST /proposals`),
reduced by `proposal_dispatcher.py` to the kernel. The server is **not constructed** when
`AUREL_FRONT_SERVER` is OFF (byte-identical runtime). `aurel front serve` runs it.

## Evidence
Seal `tests/test_p6f5_0a_one_door.py` — exactly one mutation route; flag-off ⇒ not constructed;
`/health`, `/read/*` (live projections since F5.1), `POST /proposals` → dispatcher; unknown → 404.

## Boundary
Stdlib-only, localhost, no TLS. Reads became live in F5.1.

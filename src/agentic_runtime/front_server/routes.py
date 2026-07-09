"""
routes.py — the Front server's declarative route table (F5.0a).

The whole "one door" doctrine is enforced *structurally* here: exactly ONE route
is a mutation (`POST /proposals`), and it is the only path that reduces to
`runtime.submit`. Everything else is a read-only projection. A seal asserts the
count so the invariant cannot silently erode.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Route:
    method: str
    path: str            # exact path, or a prefix ending in '/' for parametric reads
    mutation: bool
    handler: str         # FrontApp method name

    @property
    def is_prefix(self) -> bool:
        return self.path.endswith("/")


# The complete route table. INVARIANT: exactly one route has mutation=True.
ROUTES: tuple[Route, ...] = (
    Route("GET", "/health", False, "handle_health"),
    Route("GET", "/read/", False, "handle_read"),          # /read/{model}
    Route("GET", "/ws", False, "handle_websocket_upgrade"),  # push/stream, non-mutation
    Route("POST", "/proposals", True, "handle_proposals"),  # THE one door
)


def mutation_routes() -> tuple[Route, ...]:
    return tuple(r for r in ROUTES if r.mutation)


def match_route(method: str, path: str) -> Optional[Route]:
    """Match a request to a route. Exact first, then registered prefixes."""
    clean = path.split("?", 1)[0]
    for r in ROUTES:
        if r.method != method:
            continue
        if not r.is_prefix and clean == r.path:
            return r
        if r.is_prefix and clean.startswith(r.path):
            return r
    return None

"""Model cassette — deterministic replay of recorded model I/O (M5).

A run's non-determinism enters through the model call. To reconstruct a run
without the network, we record each ``(model_id, system, user) -> raw_response``
into a content-addressed cassette and, on replay, feed the recorded response
back instead of calling a provider. A cassette miss is a **fail-closed refusal**
— replay never fabricates a completion, so a replay that diverges from the
recording surfaces honestly instead of silently inventing an answer.

Determinism scope: the model leg becomes reproducible. Tool output that is
itself non-deterministic (``run_shell``/``run_tests`` stdout) is compared at the
world-state-hash level, not byte-for-byte; wall-clock and RNG-seed capture are
out of scope for this version (documented in docs/DEPLOYMENT.md).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .core_types import sha

CASSETTE_SCHEMA_VERSION = "model_cassette.v1"


def cassette_key(model_id: str, system: str, user: str) -> str:
    """Stable content address of one model request."""
    return sha(CASSETTE_SCHEMA_VERSION, model_id, system, user)


class CassetteMiss(RuntimeError):
    """Raised (or refused) when a replay request is not in the cassette."""


class ModelCassette:
    """Append-only, content-addressed store of recorded model responses."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._index: dict[str, dict] = {}
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            self._index[rec["key"]] = rec

    def has(self, model_id: str, system: str, user: str) -> bool:
        return cassette_key(model_id, system, user) in self._index

    def lookup(self, model_id: str, system: str, user: str) -> Optional[str]:
        rec = self._index.get(cassette_key(model_id, system, user))
        return rec["raw_response"] if rec is not None else None

    def record(self, model_id: str, system: str, user: str, raw_response: str) -> str:
        key = cassette_key(model_id, system, user)
        if key in self._index:
            return key
        # F2: a cassette persists the raw completion verbatim, so an API key that
        # ever leaked into model output (or an echoed prompt) would be written to
        # disk. Redact EXACT registered secret values only (not the heuristic
        # patterns, which would corrupt legitimate long token-like completions).
        from .secrets import SecretRedactor
        raw_response = SecretRedactor().redact_known(raw_response)
        rec = {
            "schema": CASSETTE_SCHEMA_VERSION,
            "key": key,
            "model_id": model_id,
            # store hashes of the prompts, not the prompts themselves, so a
            # cassette never leaks prompt content; the raw response is the payload.
            "system_hash": sha(system),
            "user_hash": sha(user),
            "raw_response": raw_response,
        }
        self._index[key] = rec
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        return key

    def __len__(self) -> int:
        return len(self._index)


class RecordingModelClient:
    """Wrap a real model client and record every completion into a cassette."""

    def __init__(self, inner, cassette: ModelCassette, *, model_id: Optional[str] = None):
        self._inner = inner
        self._cassette = cassette
        self.model_id: str = model_id or str(getattr(inner, "name", "model"))
        self.name = str(getattr(inner, "name", "recording"))

    def complete(self, system: str, user: str) -> str:
        raw = self._inner.complete(system, user)
        self._cassette.record(self.model_id, system, user, raw)
        return raw


class ReplayModelClient:
    """Serve recorded completions from a cassette; a miss fails closed."""

    name = "cassette-replay"

    def __init__(self, cassette: ModelCassette, *, model_id: str = "model"):
        self._cassette = cassette
        self.model_id = model_id

    def complete(self, system: str, user: str) -> str:
        raw = self._cassette.lookup(self.model_id, system, user)
        if raw is None:
            from .model_providers.schemas import refusal_json

            return refusal_json(
                "cassette miss: no recorded response for this request "
                "(replay is fail-closed and never fabricates a completion)"
            )
        return raw

"""A6 — Embedder seam: the real deterministic path + an honest unavailable seam.

The only *real* embedder in the system is
:class:`~agentic_runtime.memory.HashingEmbedder` — a deterministic char-3gram
hashing embedder (stdlib-only, no model, no network). A6 does NOT add a neural
embedder; it declares one as an explicitly **unavailable** seam so callers can
name the future capability without any code ever faking a neural vector.
"""

from __future__ import annotations

from typing import Any


class NeuralEmbedderUnavailable(RuntimeError):
    """Raised whenever the (declared, unimplemented) neural embedder is used."""


class NeuralEmbedderSeam:
    """A declared neural embedder that is honestly **never available**.

    Constructible so a config can reference it, but ``available`` is a read-only
    ``False`` that cannot be flipped, and ``embed`` always raises. This is the
    no-overclaim seam: A6 ships no real neural embeddings — the deterministic
    ``HashingEmbedder`` stays the only real embedder."""

    def __init__(self, model: str = "", **_config: Any) -> None:
        self.model = model

    @property
    def available(self) -> bool:
        return False

    def embed(self, text: str) -> list[float]:
        raise NeuralEmbedderUnavailable(
            "neural embeddings are not available (declared, not implemented); "
            "the deterministic HashingEmbedder is the only real embedder")


__all__ = ["NeuralEmbedderSeam", "NeuralEmbedderUnavailable"]

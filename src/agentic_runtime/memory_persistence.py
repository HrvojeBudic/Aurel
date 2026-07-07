"""A3 — Durable memory backends (JSONL, atomic) for the trace-projection store.

A backend is *dumb storage*: it appends opaque dict entries and reads them back,
in order, deterministically. It carries no authority — trust is decided at
rebuild time by :class:`~agentic_runtime.durable_memory.DurableMemoryFabric`,
which re-verifies every entry against the governed trace before admitting it.

Two backends:

* :class:`FileMemoryBackend` — append-only JSONL on local disk. Every append
  rewrites the whole file **atomically** (temp file → ``fsync`` → ``os.replace``
  → ``fsync`` dir), mirroring ``state_store``'s crash-safety idiom, so a partial
  or corrupt file is never visible after an interrupted write.
* :class:`ExternalMemoryBackend` — declared but honestly **UNAVAILABLE**:
  constructible, never available, every operation raises. No faked durability.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

_TMP_PREFIX = ".tmp-"


def _fsync_dir(path: str) -> None:
    """Best-effort fsync of a directory entry so a rename is durable."""
    try:
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def atomic_write_text(path: str, text: str) -> None:
    """Write ``text`` to ``path`` atomically: temp sibling → fsync → os.replace.

    A reader either sees the previous file or the new one — never a partial write.
    On any failure before the rename, the destination is left untouched and the
    temp file is cleaned up.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / f"{_TMP_PREFIX}{uuid4().hex}"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, dest)
        _fsync_dir(str(dest.parent))
    finally:
        if tmp.exists():
            try:
                os.remove(tmp)
            except OSError:
                pass


class MemoryBackendUnavailable(RuntimeError):
    """Raised by a backend that is declared but not actually available."""


@runtime_checkable
class MemoryBackend(Protocol):
    """Append-only, ordered, deterministic dict storage. No authority."""

    @property
    def available(self) -> bool: ...
    def append(self, entry: dict[str, Any]) -> None: ...
    def load(self) -> list[dict[str, Any]]: ...


class FileMemoryBackend:
    """Append-only JSONL backend with atomic full-file rewrites.

    Entries are buffered in memory and, on every append, the whole log is
    re-serialized (``json.dumps(..., sort_keys=True)`` — deterministic) and
    written atomically. Lazy: no file is created until the first append.
    """

    def __init__(self, path: str) -> None:
        self.path = str(path)
        self._entries: list[dict[str, Any]] = []
        self._loaded = False

    @property
    def available(self) -> bool:
        return True

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._entries = self._read_file()
        self._loaded = True

    def _read_file(self) -> list[dict[str, Any]]:
        p = Path(self.path)
        if not p.is_file():
            return []
        out: list[dict[str, Any]] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # Defensive: atomic writes never leave a partial line, but never
                # trust a corrupt line either — skip it rather than crash.
                continue
        return out

    def _flush(self) -> None:
        text = "".join(
            json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n"
            for e in self._entries
        )
        atomic_write_text(self.path, text)

    def append(self, entry: dict[str, Any]) -> None:
        self._ensure_loaded()
        self._entries.append(entry)
        self._flush()

    def load(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return list(self._entries)


class ExternalMemoryBackend:
    """A declared external durable store that is honestly **never available**.

    Constructible so callers can name it, but ``available`` is a read-only
    ``False`` that cannot be flipped, and every storage operation raises. This
    is the no-overclaim seam: A3 ships no real external durability.
    """

    def __init__(self, uri: str = "", **_config: Any) -> None:
        self.uri = uri

    @property
    def available(self) -> bool:
        return False

    def append(self, entry: dict[str, Any]) -> None:
        raise MemoryBackendUnavailable(
            "ExternalMemoryBackend is not available (declared, not implemented)")

    def load(self) -> list[dict[str, Any]]:
        raise MemoryBackendUnavailable(
            "ExternalMemoryBackend is not available (declared, not implemented)")


__all__ = [
    "atomic_write_text",
    "MemoryBackend",
    "MemoryBackendUnavailable",
    "FileMemoryBackend",
    "ExternalMemoryBackend",
]

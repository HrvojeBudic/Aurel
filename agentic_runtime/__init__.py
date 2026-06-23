"""Compatibility shim for the src-layout package in repo-local subprocesses."""
from __future__ import annotations

from pathlib import Path


_SHIM_DIR = Path(__file__).resolve().parent
_SRC_PACKAGE_DIR = _SHIM_DIR.parent / "src" / "agentic_runtime"
_SRC_INIT = _SRC_PACKAGE_DIR / "__init__.py"

if not _SRC_INIT.is_file():
    raise ModuleNotFoundError(
        f"Expected src package entrypoint at {_SRC_INIT}"
    )

if str(_SRC_PACKAGE_DIR) not in __path__:
    __path__.append(str(_SRC_PACKAGE_DIR))

globals()["__file__"] = str(_SRC_INIT)
exec(compile(_SRC_INIT.read_text(encoding="utf-8"), str(_SRC_INIT), "exec"), globals())

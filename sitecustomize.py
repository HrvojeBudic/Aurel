"""Repository-local Python bootstrap for src-layout subprocesses."""
from __future__ import annotations

import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent
_SRC = _REPO_ROOT / "src"

if _SRC.is_dir():
    src_str = str(_SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

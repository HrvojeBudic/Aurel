"""P1.4.0 — Identity, Autonomy & Agent Trust Constitution scope contract doc tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_runtime.identity.p14_scope import (
    P14_FORWARD_HOOKS,
    P14_PATCHES,
    P14_SCOPE_IN,
    P14_SCOPE_OUT,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

P14_DOC_FILES = (
    DOCS / "P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md",
    DOCS / "P1.4_AGENT_TRUST_CONSTITUTION.md",
    DOCS / "P1.4_RESEARCH_ALIGNMENT_NOTES.md",
)

REQUIRED_PHRASES = (
    "Identity is not policy",
    "Persona is not authority",
    "Mode is not permission",
    "Operator remains final authority",
    "Aurel cannot self-escalate",
    "Heretic mode is cognitive freedom",
    "Capability claims require evidence",
    "P1.5",
    "P1.6",
    "P1.7",
    "P1.8",
    "P1.9",
)


@pytest.mark.parametrize("doc_path", P14_DOC_FILES, ids=lambda p: p.name)
def test_p14_doc_exists_and_nonempty(doc_path: Path) -> None:
    assert doc_path.is_file(), f"missing doc: {doc_path}"
    assert doc_path.read_text(encoding="utf-8").strip()


def test_p14_docs_contain_required_phrases() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in P14_DOC_FILES)
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in combined]
    assert not missing, f"missing phrases in P1.4 docs: {missing}"


def test_p14_scope_constants() -> None:
    assert len(P14_PATCHES) == 21
    assert P14_PATCHES[0] == "P1.4.0"
    assert P14_PATCHES[-1] == "P1.4.20"
    assert P14_SCOPE_IN
    assert P14_SCOPE_OUT
    assert "P1.5" in P14_FORWARD_HOOKS
    assert "P1.9" in P14_FORWARD_HOOKS

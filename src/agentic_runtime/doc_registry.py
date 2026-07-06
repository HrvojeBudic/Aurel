"""Documentation path registry — the single seam between code and docs (M1).

The runtime and its tests reference a handful of documentation and canon files
by *name*, not by hard-coded path. Routing every such reference through this
module means the eventual physical relocation of documentation out of the
application tree (into a standalone ``docs/`` repo, say) is a change to the two
root constants here — ``DOCS_ROOT`` and ``CANON_ROOT`` — rather than a sweep of
literals across the codebase.

Two roots, because two kinds of file live under different lifecycles today:

* ``DOCS_ROOT`` — freestanding product/deployment documentation authored to
  stand on its own. Lives under ``<repo>/docs``. Override: ``AUREL_DOCS_ROOT``.
* ``CANON_ROOT`` — the agent canon the runtime itself still reads at runtime
  (ROADMAP/STATE/REPORTS index, per-patch reports). Currently ``<repo>/agent``;
  overridable via ``AUREL_CANON_ROOT`` so it can be relocated under ``docs/``
  once every reader routes through this registry.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_root() -> Path:
    override = os.environ.get("AUREL_DOCS_ROOT", "").strip()
    return Path(override) if override else repo_root() / "docs"


def canon_root() -> Path:
    override = os.environ.get("AUREL_CANON_ROOT", "").strip()
    return Path(override) if override else repo_root() / "agent"


class DocId(str, Enum):
    """Named documents referenced by code or seal checks."""

    # Root-level
    README = "README"
    # Canon (runtime-read; currently under CANON_ROOT)
    ARCHITECTURE = "ARCHITECTURE"
    STATE = "STATE"
    ROADMAP = "ROADMAP"
    TESTS = "TESTS"
    ALPHA_SEAL = "ALPHA_SEAL"
    REPORTS_INDEX = "REPORTS_INDEX"
    # Freestanding docs (under DOCS_ROOT)
    DEPLOYMENT = "DEPLOYMENT"
    P14_SCOPE_CONTRACT = "P14_SCOPE_CONTRACT"
    P14_TRUST_CONSTITUTION = "P14_TRUST_CONSTITUTION"
    P14_RESEARCH_ALIGNMENT = "P14_RESEARCH_ALIGNMENT"
    GOVERNANCE_SCALE = "GOVERNANCE_SCALE"


# id -> (root selector, relative path under that root)
_CANON = "canon"
_DOCS = "docs"
_ROOT = "root"

_DOC_MAP: dict[DocId, tuple[str, str]] = {
    DocId.README: (_ROOT, "README.md"),
    DocId.ARCHITECTURE: (_CANON, "ARCHITECTURE.md"),
    DocId.STATE: (_CANON, "STATE.md"),
    DocId.ROADMAP: (_CANON, "ROADMAP.md"),
    DocId.TESTS: (_CANON, "TESTS.md"),
    DocId.ALPHA_SEAL: (_CANON, "P1_0_ALPHA_SEAL.md"),
    DocId.REPORTS_INDEX: (_CANON, "REPORTS.md"),
    DocId.DEPLOYMENT: (_DOCS, "DEPLOYMENT.md"),
    DocId.P14_SCOPE_CONTRACT: (_DOCS, "P1.4_IDENTITY_AUTONOMY_SCOPE_CONTRACT.md"),
    DocId.P14_TRUST_CONSTITUTION: (_DOCS, "P1.4_AGENT_TRUST_CONSTITUTION.md"),
    DocId.P14_RESEARCH_ALIGNMENT: (_DOCS, "P1.4_RESEARCH_ALIGNMENT_NOTES.md"),
    DocId.GOVERNANCE_SCALE: (_DOCS, "canon/GOVERNANCE_SCALE.md"),
}


def _base(selector: str) -> Path:
    if selector == _CANON:
        return canon_root()
    if selector == _DOCS:
        return docs_root()
    return repo_root()


def doc_path(doc_id: DocId) -> Path:
    selector, rel = _DOC_MAP[doc_id]
    return _base(selector) / rel


def canon_report_path(report_rel: str) -> Path:
    """Resolve a per-patch report given a path relative to the canon root.

    Accepts both ``"reports/X.md"`` and the legacy ``"agent/reports/X.md"``
    form so existing call sites migrate incrementally.
    """
    rel = report_rel
    prefix = "agent/"
    if rel.startswith(prefix):
        rel = rel[len(prefix):]
    return canon_root() / rel


# Documents the alpha seal requires to be present.
ALPHA_SEAL_REQUIRED_DOCS: tuple[DocId, ...] = (
    DocId.README,
    DocId.ARCHITECTURE,
    DocId.STATE,
    DocId.ROADMAP,
    DocId.TESTS,
    DocId.ALPHA_SEAL,
    DocId.DEPLOYMENT,
)


def alpha_seal_required_paths() -> list[tuple[str, Path]]:
    """(label, path) pairs for the seal, label kept stable for evidence output."""
    labels = {
        DocId.README: "README.md",
        DocId.ARCHITECTURE: "agent/ARCHITECTURE.md",
        DocId.STATE: "agent/STATE.md",
        DocId.ROADMAP: "agent/ROADMAP.md",
        DocId.TESTS: "agent/TESTS.md",
        DocId.ALPHA_SEAL: "agent/P1_0_ALPHA_SEAL.md",
        DocId.DEPLOYMENT: "docs/DEPLOYMENT.md",
    }
    return [(labels[d], doc_path(d)) for d in ALPHA_SEAL_REQUIRED_DOCS]

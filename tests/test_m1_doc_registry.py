"""M1 — documentation path registry is the single code↔docs seam."""

from __future__ import annotations

import os

from agentic_runtime.doc_registry import (
    ALPHA_SEAL_REQUIRED_DOCS,
    DocId,
    alpha_seal_required_paths,
    canon_report_path,
    canon_root,
    doc_path,
    docs_root,
)


def test_new_docs_live_under_docs_root():
    for doc_id in (
        DocId.DEPLOYMENT,
        DocId.P14_SCOPE_CONTRACT,
        DocId.P14_TRUST_CONSTITUTION,
        DocId.P14_RESEARCH_ALIGNMENT,
    ):
        p = doc_path(doc_id)
        assert p.is_file(), f"missing {doc_id}: {p}"
        assert docs_root() in p.parents


def test_canon_docs_resolve_and_exist():
    for doc_id in (DocId.ARCHITECTURE, DocId.STATE, DocId.ROADMAP, DocId.TESTS):
        p = doc_path(doc_id)
        assert p.is_file(), f"missing canon {doc_id}: {p}"


def test_alpha_seal_required_labels_stable():
    labels = [label for label, _ in alpha_seal_required_paths()]
    assert labels == [
        "README.md",
        "agent/ARCHITECTURE.md",
        "agent/STATE.md",
        "agent/ROADMAP.md",
        "agent/TESTS.md",
        "agent/P1_0_ALPHA_SEAL.md",
        "docs/DEPLOYMENT.md",
    ]
    assert len(ALPHA_SEAL_REQUIRED_DOCS) == len(labels)


def test_canon_report_path_strips_legacy_prefix():
    a = canon_report_path("agent/reports/X.md")
    b = canon_report_path("reports/X.md")
    assert a == b
    assert a == canon_root() / "reports" / "X.md"


def test_roots_are_env_overridable(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_DOCS_ROOT", str(tmp_path / "d"))
    monkeypatch.setenv("AUREL_CANON_ROOT", str(tmp_path / "c"))
    assert docs_root() == tmp_path / "d"
    assert canon_root() == tmp_path / "c"
    # a docs-rooted id follows the override — this is the split-ready seam
    assert doc_path(DocId.DEPLOYMENT) == tmp_path / "d" / "DEPLOYMENT.md"

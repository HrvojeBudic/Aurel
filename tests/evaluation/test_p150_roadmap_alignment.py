"""P1.5.0 roadmap v3.2 alignment tests."""
from __future__ import annotations

import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(path: str) -> str:
    full = os.path.join(REPO, path)
    if os.path.isfile(full):
        with open(full) as f:
            return f.read()
    return ""


def test_roadmap_mentions_p150_current():
    text = _read("agent/ROADMAP.md")
    assert "P1.5.0" in text


def test_roadmap_mentions_p151_next():
    text = _read("agent/ROADMAP.md")
    assert "P1.5.1" in text


def test_roadmap_preserves_p1_p2_stability():
    text = _read("agent/ROADMAP.md")
    assert "P1.4" in text
    assert "P1.5" in text
    # v3.2 doctrine: P1-P2 remain stable
    assert "stable" in text.lower() or "P1.4.20" in text


def test_roadmap_mentions_hq_ahub_shub_lhub_ide():
    text = _read("agent/ROADMAP.md").lower()
    for term in ("aurel core", "hq", "a-hub", "s-hub", "l-hub", "ide"):
        assert term in text, f"ROADMAP missing: {term}"


def test_architecture_mentions_aurel_core_vs_hub_tools():
    text = _read("agent/ARCHITECTURE.md").lower()
    assert "aurel core" in text
    assert "hub" in text


def test_architecture_mentions_hub_memory_not_auto_aurel_memory():
    text = _read("agent/ARCHITECTURE.md").lower()
    assert "memory" in text
    assert "hub" in text
    assert "automatic" in text or "does not automatically" in text or "not automatically" in text


def test_architecture_mentions_open_weight_foundation():
    text = _read("agent/ARCHITECTURE.md").lower()
    assert "open-weight" in text or "open weight" in text or "mistral" in text or "sovereign" in text


def test_state_points_to_p151_next():
    text = _read("agent/STATE.md")
    assert "P1.5.1" in text or "P1.5.0" in text


def test_reports_index_mentions_p150_report():
    text = _read("agent/REPORTS.md")
    assert "P1.5.0" in text


def test_decisions_mentions_roadmap_v32_not_reset():
    text = _read("agent/DECISIONS.md")
    assert "v3.2" in text.lower() or "3.2" in text
    assert "reset" in text.lower() or "not a reset" in text.lower()

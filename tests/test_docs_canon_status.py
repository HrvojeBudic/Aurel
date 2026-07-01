"""P1.ENF-F-B docs / canon status checks."""
from __future__ import annotations

import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path: str) -> str:
    full = os.path.join(REPO, path)
    with open(full, encoding="utf-8") as f:
        return f.read()


def test_active_canon_points_to_v5_5() -> None:
    canon_index = _read("agent/CANON_INDEX.md")
    roadmap = _read("agent/ROADMAP.md")
    assert "Aurel Roadmap v5.5" in canon_index
    assert "ACTIVE_CANON" in canon_index
    assert "Aurel Roadmap v5.5" in roadmap


def test_historical_docs_labeled_in_canon_index() -> None:
    text = _read("agent/CANON_INDEX.md")
    for label in (
        "HISTORICAL_ARCHIVE",
        "HISTORICAL_REFERENCE",
        "SUPERSEDED_BY_V5_5",
        "DO_NOT_USE_AS_CURRENT_TASK_SOURCE",
    ):
        assert label in text


def test_p2_6_is_surface_projection_api_event_bridge() -> None:
    roadmap = _read("agent/ROADMAP.md")
    assert re.search(
        r"P2\.6.*Surface Projection.*API.*Event Bridge",
        roadmap,
        re.IGNORECASE | re.DOTALL,
    )


def test_p2_9_b_remains_not_done() -> None:
    state = _read("agent/STATE.md")
    canon = _read("agent/CANON_INDEX.md")
    assert "P2.9-B" in state
    assert "NOT DONE" in state
    assert "NOT DONE" in canon


def test_golden_thread_b_is_current_continuity_reference() -> None:
    state = _read("agent/STATE.md")
    canon = _read("agent/CANON_INDEX.md")
    assert "Golden Thread B" in state
    assert "Golden Thread B" in canon
    assert "golden_thread_b" in canon or "golden_thread_b.py" in state


def test_state_next_step_after_f_b_is_p1_enf_d1() -> None:
    state = _read("agent/STATE.md")
    active = _read("agent/ACTIVE_TASK.md")
    canon = _read("agent/CANON_INDEX.md")
    assert "P1.ENF-D1" in state
    assert "P1.ENF-D1" in active or "P1.ENF-F-B" in active
    assert "P1.ENF-D1" in canon


def test_canon_index_exists_and_indexed_in_state() -> None:
    assert os.path.isfile(os.path.join(REPO, "agent/CANON_INDEX.md"))
    state = _read("agent/STATE.md")
    assert "CANON_INDEX" in state or "canon" in state.lower()


def _line_denies_live_claim(line: str) -> bool:
    lower = line.lower()
    return any(
        marker in lower
        for marker in (
            "no ",
            "not ",
            "does not",
            "do not",
            "without ",
            " remains not",
            " claim.",
            " claim,",
            " boundary:",
            " or live",
            " or trace",
            "shell live behavior",
            "not shell live",
        )
    )


def test_no_active_doc_claims_shell_live() -> None:
    """Active state/canon docs must not positively claim Shell/P2 live completion."""
    claim = re.compile(r"\b(?:Shell\s+LIVE|Shell\s+complete|P2\s+complete)\b", re.IGNORECASE)
    for path in ("agent/STATE.md", "agent/CANON_INDEX.md", "agent/ACTIVE_TASK.md"):
        for line in _read(path).splitlines():
            if claim.search(line) and not _line_denies_live_claim(line):
                raise AssertionError(f"{path}: {line}")


def test_p1_enf_f_b_report_indexed() -> None:
    reports = _read("agent/REPORTS.md")
    assert "P1.ENF-F-B" in reports or "P1_ENF_F_B" in reports

"""F4.4 seal — projection + CLI + derived F4 exit seal.

  1. Derived status — SEALED only when every slice's module + report is present;
     a missing report or module BLOCKS the item and the seal (hermetic tmp-dir).
  2. Honest — overclaim guards hard-False; UNAVAILABLE surfaces explicit.
  3. Projections — loop-run + context-bundle read-models.
  4. Real repo — the live reports dir seals SEALED.
"""
from __future__ import annotations

from agentic_runtime.context_loom import assemble, make_context_item
from agentic_runtime.external_ingress import SourceKind
from agentic_runtime.f4_projection import project_context_bundle, project_loop_run
from agentic_runtime.f4_seal import F4_SLICES, SealStatus, build_f4_exit_seal


def _write_all_reports(d):
    for _sid, _title, _module, report in F4_SLICES:
        (d / report).write_text("stub", encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. Derived status.
# --------------------------------------------------------------------------- #
def test_all_present_is_sealed(tmp_path):
    _write_all_reports(tmp_path)
    seal = build_f4_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.SEALED
    assert seal.sealed is True
    assert all(i.status.value == "PASSED" for i in seal.items)


def test_missing_report_blocks(tmp_path):
    _write_all_reports(tmp_path)
    (tmp_path / F4_SLICES[0][3]).unlink()
    seal = build_f4_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED
    assert seal.sealed is False


def test_empty_reports_dir_blocks(tmp_path):
    seal = build_f4_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED


# --------------------------------------------------------------------------- #
# 2. Honesty.
# --------------------------------------------------------------------------- #
def test_overclaim_guards_false_and_unavailable_explicit(tmp_path):
    _write_all_reports(tmp_path)
    seal = build_f4_exit_seal(reports_dir=str(tmp_path))
    assert seal.claims_live_model_loop is False
    assert seal.claims_semantic_summarization is False
    assert seal.claims_client_bridge_live is False
    ids = {u.surface_id for u in seal.unavailable}
    assert {"live_model_loop", "mcp_client_bridge", "semantic_summarization"} <= ids
    for u in seal.unavailable:
        assert u.reason and u.future_owner


# --------------------------------------------------------------------------- #
# 3. Projections.
# --------------------------------------------------------------------------- #
def test_context_bundle_projection():
    bundle = assemble([
        make_context_item("goal", SourceKind.OPERATOR, "op"),
        make_context_item("x" * 400, SourceKind.SCRAPE, "scrape"),
    ], max_tokens=20, compress=True)
    proj = project_context_bundle(bundle)
    assert proj["context_ref"] == bundle.context_ref
    assert proj["external_items"] >= 1
    assert "scrape" in proj["by_source_kind"]
    assert proj["rendered_chars"] > 0


def test_loop_run_projection():
    fake = {
        "turns": [{"index": 0, "context_ref": "abc", "steps_planned": 1,
                   "steps_executed": 1, "observations": ["list_dir: ok"]}],
        "context_refs": ["abc"],
        "executed": 1,
        "terminated": "done",
    }
    proj = project_loop_run(fake)
    assert proj["terminated"] == "done"
    assert proj["executed"] == 1
    assert proj["turn_count"] == 1
    assert proj["context_refs"] == ["abc"]


# --------------------------------------------------------------------------- #
# 4. Real repo seals SEALED.
# --------------------------------------------------------------------------- #
def test_real_reports_dir_is_sealed():
    seal = build_f4_exit_seal()
    assert seal.status is SealStatus.SEALED, seal.to_dict()

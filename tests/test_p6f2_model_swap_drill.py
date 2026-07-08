"""F2 seal — Model Swap Drill behavioral diff.

Proves: the drill corpus round-trips (JSONL, deterministic key order, dedup);
``classify_response`` distinguishes plan/refusal/invalid; ``run_drill`` produces
a deterministic behavioral diff (same corpus + same candidate ⇒ byte-identical
report); a keyless candidate is honest ``candidate_refused`` (never a fabricated
comparison); the CLI wires end-to-end with honest fail-closed on a missing/empty
corpus.
"""

from __future__ import annotations

import argparse
import json

from agentic_runtime.model_providers.schemas import (refusal_json,
                                                     structured_plan_payload)
from agentic_runtime.model_swap_drill import (DrillCorpus, classify_response,
                                              run_drill)


def _plan(tools: list[str]) -> str:
    return json.dumps(structured_plan_payload(
        [{"step_id": f"s{i}", "tool": t, "args": {}, "reason": "r", "risk": "low"}
         for i, t in enumerate(tools)],
        intent_summary="x", confidence=0.9, requires_approval=False,
        assumptions=[]))


def _corpus(tmp_path):
    corpus = DrillCorpus(tmp_path / "corpus.jsonl")
    corpus.record("sys", "task one", _plan(["read_file", "write_file"]),
                  baseline_model="deepseek-v4-pro")
    corpus.record("sys", "task two", _plan(["run_tests"]),
                  baseline_model="deepseek-v4-pro")
    corpus.record("sys", "task three", refusal_json("cannot do this"),
                  baseline_model="deepseek-v4-pro")
    return corpus


def test_corpus_round_trip_and_dedup(tmp_path):
    corpus = _corpus(tmp_path)
    assert len(corpus) == 3
    corpus.record("sys", "task one", _plan(["read_file"]))   # dup key: ignored
    assert len(corpus) == 3
    reloaded = DrillCorpus(tmp_path / "corpus.jsonl")
    assert [e.key for e in reloaded.entries()] == [e.key for e in corpus.entries()]
    assert reloaded.entries()[0].baseline_model == "deepseek-v4-pro"


def test_classify_response_kinds():
    assert classify_response(_plan(["a", "b"])) == {
        "kind": "plan", "tools": ["a", "b"], "steps": 2}
    assert classify_response(refusal_json("no"))["kind"] == "refusal"
    assert classify_response("not json")["kind"] == "invalid_json"
    assert classify_response(json.dumps({"plan": "x"}))["kind"] == "invalid_schema"


def test_drill_diff_same_divergent_refused(tmp_path):
    corpus = _corpus(tmp_path)

    def candidate(profile, system, user):
        if "one" in user:
            return _plan(["read_file", "write_file"]), "qwen"   # same behavior
        if "two" in user:
            return _plan(["run_shell"]), "qwen"                 # divergent tools
        return refusal_json("cannot"), "qwen"                   # both refuse

    report = run_drill(corpus, candidate, "coding")
    assert report.total == 3
    assert report.counts == {"same_behavior": 2, "divergent": 1,
                             "candidate_refused": 0}
    # Baseline refusal + candidate refusal counts as same behavior.
    verdicts = {r.key: r.verdict for r in report.results}
    assert sorted(verdicts.values()) == ["divergent", "same_behavior", "same_behavior"]


def test_drill_deterministic(tmp_path):
    corpus = _corpus(tmp_path)

    def candidate(profile, system, user):
        return _plan(["read_file"]), "qwen"

    r1 = run_drill(corpus, candidate, "coding").to_dict()
    r2 = run_drill(corpus, candidate, "coding").to_dict()
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
    assert [r["key"] for r in r1["results"]] == sorted(r["key"] for r in r1["results"])


def test_keyless_candidate_is_honest_refused(tmp_path):
    corpus = _corpus(tmp_path)

    def keyless(profile, system, user):
        return refusal_json("DASHSCOPE_API_KEY not configured"), "qwen"

    report = run_drill(corpus, keyless, "coding")
    # Plan baselines become candidate_refused; the refusal baseline matches.
    assert report.counts["candidate_refused"] == 2
    assert report.counts["same_behavior"] == 1


def test_cli_end_to_end(tmp_path, capsys, monkeypatch):
    from agentic_runtime.cli_modules.drill_commands import cmd_drill_model_swap

    # Missing corpus fails closed.
    rc = cmd_drill_model_swap(argparse.Namespace(
        corpus=str(tmp_path / "nope.jsonl"), candidate="coding",
        config_dir="config/live", limit=None, json=False))
    assert rc == 1
    assert "no corpus" in capsys.readouterr().out

    corpus = _corpus(tmp_path)
    # Stub the router's complete so no network/keys are involved.
    from agentic_runtime import model_router

    def fake_complete(self, profile, system, user):
        return _plan(["read_file", "write_file"]), "stub"
    monkeypatch.setattr(model_router.ModelRouter, "complete", fake_complete)

    rc = cmd_drill_model_swap(argparse.Namespace(
        corpus=str(corpus.path), candidate="coding",
        config_dir="config/live", limit=None, json=True))
    out = capsys.readouterr().out
    assert rc == 0
    report = json.loads(out)
    assert report["total"] == 3
    assert report["candidate_profile"] == "coding"
    assert set(report["counts"]) == {"same_behavior", "divergent", "candidate_refused"}

"""``aurel drill model-swap`` — behavioral diff of a candidate provider (F2).

Replays a DrillCorpus (JSONL of system/user/baseline_response triples) against a
candidate model profile and prints per-entry verdicts + aggregate counts, so a
provider swap (e.g. DeepSeek → Qwen) is a measurement, not a leap of faith.
Honest output: a keyless candidate shows up as ``candidate_refused`` rows, never
a fabricated comparison; a missing/empty corpus fails closed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def cmd_drill_model_swap(args: argparse.Namespace) -> int:
    from ..model_config import ProviderConfigLoader
    from ..model_router import ModelRouter
    from ..model_swap_drill import DrillCorpus, run_drill

    corpus_path = Path(args.corpus)
    if not corpus_path.is_file():
        print(f"drill: no corpus at {corpus_path} (record one with DrillCorpus)")
        return 1
    corpus = DrillCorpus(corpus_path)
    if len(corpus) == 0:
        print(f"drill: corpus {corpus_path} is empty")
        return 1

    router = ModelRouter(config=ProviderConfigLoader(args.config_dir).load())
    report = run_drill(corpus, router.complete, args.candidate, limit=args.limit)

    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0
    counts = report.counts
    print(f"model-swap drill  candidate={args.candidate}  corpus={corpus_path}"
          f"  entries={report.total}")
    print(f"  same_behavior:     {counts['same_behavior']}")
    print(f"  divergent:         {counts['divergent']}")
    print(f"  candidate_refused: {counts['candidate_refused']}")
    for r in report.results:
        if r.verdict != "same_behavior":
            print(f"  [{r.verdict}] {r.key[:12]}  baseline={r.baseline['kind']}"
                  f"({','.join(r.baseline['tools'])}) candidate={r.candidate['kind']}"
                  f"({','.join(r.candidate['tools'])})")
    if counts["candidate_refused"] == report.total:
        print("note: candidate refused every entry — likely no API key; "
              "the drill measured nothing about behavior (honest PARTIAL)")
    return 0

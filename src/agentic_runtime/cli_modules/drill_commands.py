"""``aurel drill`` — operational drills (F2 model-swap, F8.5 succession)."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def _require_chronos(args: argparse.Namespace) -> bool:
    from ..chronos import flag_enabled

    if flag_enabled():
        return True
    reason = (
        "succession drill unavailable — set AUREL_CHRONOS=1 to enable "
        "read-only export/restore/verify/replay"
    )
    if getattr(args, "json", False):
        print(json.dumps({"available": False, "reason": reason}, indent=2))
    else:
        print(reason, file=sys.stderr)
    return False


def _default_trace_dir() -> str:
    from .. import build_runtime

    rt = build_runtime()
    trace = rt.runtime.trace
    base = getattr(trace, "base_dir", None)
    if base is not None:
        return str(base)
    return ".traces"


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


def cmd_drill_succession(args: argparse.Namespace) -> int:
    if not _require_chronos(args):
        return 1
    from ..succession_drill import run_succession_drill

    trace_dir = getattr(args, "trace_dir", "") or _default_trace_dir()
    out_dir = getattr(args, "out", "") or tempfile.mkdtemp(prefix="aurel-succession-")
    report = run_succession_drill(
        trace_dir,
        out_dir=out_dir,
        sample=int(getattr(args, "sample", 3) or 3),
    )

    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"succession drill  trace={trace_dir}  copy={report.export_path}  "
            f"sample={len(report.sample_run_ids)}"
        )
        print(
            f"  exported={report.exported}  restored={report.restored}  "
            f"verified={report.verified}  replayed={report.replayed}  "
            f"passed={report.passed}"
        )
        for d in report.discrepancies:
            print(f"  discrepancy [{d.get('stage')}]: {d}")
    return 0 if report.passed else 1

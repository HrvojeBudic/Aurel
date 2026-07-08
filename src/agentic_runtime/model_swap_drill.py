"""F2 Model Swap Drill — behavioral diff of a candidate provider over a corpus.

Answers "can I swap DeepSeek for Qwen?" with MEASUREMENT instead of faith:
replay a recorded prompt corpus against the candidate profile and diff the
behavior (refusal vs plan, schema validity, tool sequence, step count).

The drill uses its own ``DrillCorpus`` JSONL format — NOT the run cassette.
``ModelCassette`` deliberately stores prompt *hashes* (a run cassette must never
leak prompt content), so it cannot be replayed against a new provider. A drill
corpus is the opposite trade: a deliberate, operator-curated artifact that keeps
``(system, user, baseline_response)`` verbatim so candidates can be measured.
Baseline responses are compared as recorded — the old provider is never re-called.

Deterministic: entries are processed in ``key`` order and the report dict is
fully ordered, so the same corpus + same candidate responses ⇒ byte-identical
report. Honest: a candidate refusal (e.g. missing key) is counted and labeled
``candidate_refused`` — never faked into a comparison.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .core_types import sha

DRILL_CORPUS_SCHEMA = "drill_corpus.v1"


@dataclass
class DrillEntry:
    key: str
    system: str
    user: str
    baseline_response: str
    baseline_model: str = ""

    def to_dict(self) -> dict:
        return {
            "schema": DRILL_CORPUS_SCHEMA,
            "key": self.key,
            "system": self.system,
            "user": self.user,
            "baseline_response": self.baseline_response,
            "baseline_model": self.baseline_model,
        }


class DrillCorpus:
    """Append-only JSONL corpus of (system, user, baseline_response) triples."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._entries: dict[str, DrillEntry] = {}
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                entry = DrillEntry(
                    key=rec["key"], system=rec["system"], user=rec["user"],
                    baseline_response=rec["baseline_response"],
                    baseline_model=rec.get("baseline_model", ""))
                self._entries[entry.key] = entry

    def record(self, system: str, user: str, baseline_response: str,
               *, baseline_model: str = "") -> str:
        key = sha(DRILL_CORPUS_SCHEMA, system, user)
        if key in self._entries:
            return key
        entry = DrillEntry(key, system, user, baseline_response, baseline_model)
        self._entries[key] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), sort_keys=True))
            f.write("\n")
        return key

    def entries(self) -> list[DrillEntry]:
        """Deterministic ``key`` order."""
        return [self._entries[k] for k in sorted(self._entries)]

    def __len__(self) -> int:
        return len(self._entries)


def classify_response(raw: str) -> dict[str, Any]:
    """Deterministic behavioral signature of one model response."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"kind": "invalid_json", "tools": [], "steps": 0}
    if not isinstance(data, dict):
        return {"kind": "invalid_json", "tools": [], "steps": 0}
    if data.get("refusal_reason"):
        return {"kind": "refusal", "tools": [], "steps": 0,
                "reason": str(data.get("refusal_reason"))[:200]}
    plan = data.get("plan")
    if not isinstance(plan, list):
        return {"kind": "invalid_schema", "tools": [], "steps": 0}
    tools = [str(s.get("tool", "?")) for s in plan if isinstance(s, dict)]
    return {"kind": "plan", "tools": tools, "steps": len(tools)}


@dataclass
class DrillResult:
    key: str
    baseline: dict[str, Any]
    candidate: dict[str, Any]
    verdict: str          # same_behavior | divergent | candidate_refused

    def to_dict(self) -> dict:
        return {"key": self.key, "baseline": self.baseline,
                "candidate": self.candidate, "verdict": self.verdict}


@dataclass
class DrillReport:
    candidate_profile: str
    total: int
    results: list[DrillResult] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {"same_behavior": 0, "divergent": 0,
                               "candidate_refused": 0}
        for r in self.results:
            out[r.verdict] = out.get(r.verdict, 0) + 1
        return out

    def to_dict(self) -> dict:
        return {
            "candidate_profile": self.candidate_profile,
            "total": self.total,
            "counts": self.counts,
            "results": [r.to_dict() for r in self.results],
        }


def _verdict(baseline: dict, candidate: dict) -> str:
    if candidate["kind"] == "refusal" and baseline["kind"] != "refusal":
        return "candidate_refused"
    if (baseline["kind"], baseline["tools"]) == (candidate["kind"], candidate["tools"]):
        return "same_behavior"
    return "divergent"


def run_drill(corpus: DrillCorpus, complete, candidate_profile: str,
              *, limit: Optional[int] = None) -> DrillReport:
    """Replay the corpus against a candidate and diff behavior.

    ``complete`` is any ``(profile, system, user) -> (raw, name)`` callable —
    normally ``ModelRouter.complete``. Entries run in deterministic key order;
    ``limit`` (if given) bounds the run and is reported honestly via ``total``.
    """
    entries = corpus.entries()
    if limit is not None:
        entries = entries[:max(0, int(limit))]
    report = DrillReport(candidate_profile=candidate_profile, total=len(entries))
    for entry in entries:
        raw, _name = complete(candidate_profile, entry.system, entry.user)
        baseline = classify_response(entry.baseline_response)
        candidate = classify_response(raw)
        report.results.append(DrillResult(
            key=entry.key, baseline=baseline, candidate=candidate,
            verdict=_verdict(baseline, candidate)))
    return report


__all__ = [
    "DRILL_CORPUS_SCHEMA",
    "DrillCorpus",
    "DrillEntry",
    "DrillReport",
    "DrillResult",
    "classify_response",
    "run_drill",
]

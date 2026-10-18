#!/usr/bin/env python3
"""Safe RNN-assisted command candidate ranking; unresolved commands never auto-execute."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.cognition.chimera_rnn import RecurrentState, Evidence, KnowledgeBus

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "system/commands/native-command-candidates.json"
def tokenize(text):
    return set(re.findall(r"[a-z0-9_+.-]+", text.casefold()))
def rank(query, catalog, limit=10):
    q = tokenize(query)
    recurrent = RecurrentState(16)
    scored = []
    for row in catalog.get("commands", []):
        name = row.get("name", "")
        tokens = tokenize(name)
        overlap = len(q & tokens) / max(1, len(q | tokens))
        features = [float(overlap), float(row.get("status") == "native-implemented"), float(len(name) <= 8)]
        state = recurrent.step(features)
        score = overlap + (0.02 * sum(state[:3]) / 3)
        scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], item[1].get("normalized_name", "")))
    return [{"name": row["name"], "status": row["status"], "dispatch": row["dispatch"],
             "score": round(score, 6), "execution_allowed": row["execution_allowed"],
             "next_step": "execute only after native allowlist and argument policy checks" if row["execution_allowed"] else "queue for provider discovery and tests; do not execute"} for score, row in scored[:limit]]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    a=ap.parse_args()
    if not 1 <= a.limit <= 100: raise SystemExit("--limit must be 1..100")
    catalog=json.loads(a.catalog.read_text(encoding="utf-8"))
    results=rank(a.query, catalog, a.limit)
    bus=KnowledgeBus(max_items=1000)
    bus.add(Evidence.from_text("local-command-catalog", "command candidate query", a.query))
    print(json.dumps({"schema":"CHM-RNN-COMMAND-ROUTER-1",
      "engine":"deterministic recurrent-state ranking (not an LLM; no network inference)",
      "query":a.query,"results":results,
      "unresolved_count":catalog.get("counts",{}).get("candidate_only",0),
      "safety":"Ranking is advisory. This tool does not execute commands, install providers, or infer missing implementations."}, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()

#!/usr/bin/env python3
"""Safe RNN-assisted command candidate ranking; unresolved commands never auto-execute."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    from tools.cognition.chimera_rnn import RecurrentState
    from tools.cognition.local_llm import rerank as local_llm_rerank
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from chimera_rnn import RecurrentState
    from local_llm import rerank as local_llm_rerank

ROOT = Path(__file__).resolve().parents[2]
CATALOG = (Path(__file__).resolve().with_name("native-command-candidates.json") if Path(__file__).resolve().with_name("native-command-candidates.json").exists() else ROOT / "system/commands/native-command-candidates.json")
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
def queue_unresolved(query, catalog, queue_path):
    normalized = query.strip().casefold()
    exact = next((c for c in catalog.get("commands", []) if c.get("normalized_name") == normalized), None)
    if exact and exact.get("execution_allowed") is True:
        return None
    token = query.strip().split(maxsplit=1)[0] if query.strip() else ""
    token = token[:128]
    record = {"command_token": token, "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
              "status": "pending", "reason": "not an exact verified native command; provider/implementation evidence required",
              "created_at_utc": datetime.now(timezone.utc).isoformat()}
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(queue_path)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--queue", type=Path, default=Path.home()/".local/state/chimera/command-candidates.jsonl")
    ap.add_argument("--llm", action="store_true", help="use a separately configured loopback local LLM to rerank candidates")
    ap.add_argument("--rnn-model", type=Path, help="optional trained character-RNN JSON model for candidate ranking")
    a=ap.parse_args()
    if not 1 <= a.limit <= 100: raise SystemExit("--limit must be 1..100")
    catalog=json.loads(a.catalog.read_text(encoding="utf-8"))
    results=rank(a.query, catalog, max(a.limit, min(100, len(catalog.get("commands", [])))))
    llm_meta={"mode":"deterministic-rnn","validated":False}
    if a.rnn_model:
        try:
            from tools.cognition.trainable_rnn_lm import CharRNN
        except ModuleNotFoundError:
            from trainable_rnn_lm import CharRNN
        trained=CharRNN.load(a.rnn_model)
        results.sort(key=lambda row: (-trained.score(a.query+" "+row["name"]+" "+row["status"]), row["name"]))
        llm_meta={"mode":"trained-character-rnn","model":str(a.rnn_model),"validated":True,"llm_scale":False}
    if a.llm:
        candidates=[{"id":r["name"],"label":r["name"]+" | "+r["status"]} for r in results]
        ordered,llm_meta=local_llm_rerank(a.query,candidates,a.limit)
        by_name={r["name"]:r for r in results}
        results=[by_name[c["id"]] for c in ordered if c["id"] in by_name][:a.limit]
    else:
        results=results[:a.limit]
    queued=queue_unresolved(a.query, catalog, a.queue)
    print(json.dumps({"schema":"CHM-RNN-COMMAND-ROUTER-1",
      "engine":"deterministic recurrent-state retrieval"+(" with constrained local LLM reranking" if a.llm else "")+(" with trained character-RNN scoring" if a.rnn_model else ""), "llm":llm_meta,
      "query":a.query,"results":results,
      "unresolved_count":catalog.get("counts",{}).get("candidate_only",0),"queued_for_later":bool(queued),"queue_file":queued,
      "safety":"Ranking is advisory. This tool does not execute commands, install providers, or infer missing implementations."}, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()

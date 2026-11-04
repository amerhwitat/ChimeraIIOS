#!/usr/bin/env python3
"""Train and evaluate the small advisory character-RNN on the curated knowledge DB."""
from __future__ import annotations
import argparse, hashlib, json, math, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
try:
    from tools.cognition.trainable_rnn_lm import CharRNN
except ModuleNotFoundError:
    import importlib.util
    module_path=Path(__file__).with_name("trainable_rnn_lm.py")
    spec=importlib.util.spec_from_file_location("chimera_trainable_rnn_lm",module_path)
    if spec is None or spec.loader is None: raise
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    CharRNN=module.CharRNN

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--hidden",type=int,default=8)
    p.add_argument("--seed",type=int,default=2026)
    a=p.parse_args()
    db=json.loads(a.database.read_text(encoding="utf-8"))
    if db.get("schema")!="CHIMERA-HARDWARE-SYSTEMS-KNOWLEDGE-1": raise SystemExit("unsupported knowledge DB")
    rows=[]
    for item in db.get("entries",[]):
        text="topic "+item["domain"]+" "+item["title"]+" "+item["summary"]+" tags "+" ".join(item.get("tags",[]))
        rows.append(text[:160])
    if len(rows)<30: raise SystemExit("refusing to train on fewer than 30 knowledge records")
    corpus_hash=hashlib.sha256("\n".join(rows).encode()).hexdigest()
    rng=random.Random(a.seed); order=list(range(len(rows))); rng.shuffle(order)
    split=max(1,int(len(order)*0.8)); train=[rows[i] for i in order[:split]]; test=[rows[i] for i in order[split:]]
    vocab=sorted(set("".join(rows)+" \n"))
    model=CharRNN(vocab,hidden=a.hidden,seed=a.seed)
    losses=model.train(train,epochs=a.epochs,learning_rate=0.025)
    scores=[model.score(row) for row in test]
    if not scores or not all(math.isfinite(x) for x in losses+scores): raise SystemExit("non-finite training/evaluation metric")
    metadata={"training_source":"curated source-attributed hardware/systems knowledge database",
      "database_schema":db["schema"],"database_version":db.get("version"),"database_entries":len(rows),
      "train_sequences":len(train),"heldout_sequences":len(test),"corpus_sha256":corpus_hash,
      "epochs":len(losses),"loss_history":losses,"heldout_mean_log_probability":sum(scores)/len(scores),
      "seed":a.seed,"hidden_size":a.hidden,
      "model_scope":"small character-level vanilla RNN language model; advisory text-pattern component only; not an LLM and not authoritative"}
    a.output.parent.mkdir(parents=True,exist_ok=True);model.save(a.output,metadata)
    loaded=CharRNN.load(a.output)
    if abs(loaded.score(test[0])-model.score(test[0]))>1e-8: raise SystemExit("RNN checkpoint round-trip mismatch")
    print(json.dumps({"status":"trained-evaluated-roundtrip-validated","training_sequences":len(train),
      "heldout_sequences":len(test),"loss_first":losses[0],"loss_last":losses[-1],
      "heldout_mean_log_probability":metadata["heldout_mean_log_probability"],
      "corpus_sha256":corpus_hash,"output":str(a.output)}))
if __name__=="__main__": main()

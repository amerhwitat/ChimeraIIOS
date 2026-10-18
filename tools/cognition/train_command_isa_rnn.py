#!/usr/bin/env python3
"""Train a bounded, reproducible RNN LM from imported command and ISA catalogs."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.cognition.trainable_rnn_lm import CharRNN

def corpus_from(commands_path:Path,isa_path:Path,limit:int=200):
    commands=json.loads(commands_path.read_text(encoding="utf-8"))
    isa=json.loads(isa_path.read_text(encoding="utf-8"))
    def sample(rows):
        rows=[r[:160] for r in rows if len(r.strip())>=3]
        if len(rows)<=limit:return rows
        return [rows[(i*(len(rows)-1))//(limit-1)] for i in range(limit)]
    command_rows=[]
    for c in commands.get("commands",[]):
        command_rows.append("command "+str(c.get("name",""))+" status "+str(c.get("status",""))+
          " provider "+str(c.get("provider",""))+" target "+str(c.get("target","")))
    isa_rows=[]
    for row in isa.get("instructions",[]):
        isa_rows.append("instruction "+str(row.get("architecture",""))+" "+str(row.get("mnemonic",""))+
          " form "+str(row.get("form_id",""))+" encoding "+str(row.get("encoding_status",""))+
          " execution "+str(row.get("execution_status","")))
    return sample(command_rows)+sample(isa_rows),commands,isa

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--commands",type=Path,default=ROOT/"system/commands/native-command-candidates.json")
    p.add_argument("--isa",type=Path,default=ROOT/"isa/generated/universal-instruction-catalog.json")
    p.add_argument("--output",type=Path,default=ROOT/"build/runtime/trained-command-isa-rnn.json")
    p.add_argument("--epochs",type=int,default=2);p.add_argument("--hidden",type=int,default=12)
    a=p.parse_args()
    rows,commands,isa=corpus_from(a.commands,a.isa)
    if len(rows)<20:raise SystemExit(f"refusing to train on too-small command/ISA corpus: {len(rows)} rows")
    chars=sorted(set("".join(rows)+" \n"))
    model=CharRNN(chars,hidden=a.hidden,seed=7)
    losses=model.train(rows,epochs=a.epochs,learning_rate=0.025)
    digest=hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
    metadata={"training_source":"imported command candidate + universal ISA catalogs","training_sequences":len(rows),
      "command_rows":commands.get("counts",{}).get("total",len(commands.get("commands",[]))),
      "isa_rows":len(isa.get("instructions",[])),"corpus_sha256":digest,"epochs":len(losses),
      "loss_first":losses[0],"loss_last":losses[-1],"seed":7,"hidden_size":a.hidden,
      "model_scope":"small trained character-level RNN LM; not an LLM-scale foundation model; advisory ranking only"}
    a.output.parent.mkdir(parents=True,exist_ok=True);model.save(a.output,metadata)
    loaded=CharRNN.load(a.output)
    if abs(loaded.score(rows[0])-model.score(rows[0]))>1e-8:raise SystemExit("RNN weight round-trip validation failed")
    if not all(0<=x<1e6 for x in losses):raise SystemExit("RNN loss is non-finite or out of expected bounds")
    print(json.dumps({"status":"trained-and-roundtrip-validated","model_type":"trained-character-level-vanilla-RNN",
      "training_sequences":len(rows),"command_rows":metadata["command_rows"],"isa_rows":metadata["isa_rows"],
      "epochs":len(losses),"loss_first":losses[0],"loss_last":losses[-1],"corpus_sha256":digest,"model":str(a.output)}))
if __name__=="__main__":main()

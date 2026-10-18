#!/usr/bin/env python3
"""RNN-assisted retrieval over ISA catalog rows; never infers execution semantics."""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
try:
 from tools.cognition.chimera_rnn import RecurrentState
 from tools.cognition.local_llm import rerank as local_llm_rerank
except ModuleNotFoundError:
 sys.path.insert(0,str(Path(__file__).resolve().parent))
 from chimera_rnn import RecurrentState
 from local_llm import rerank as local_llm_rerank
DEFAULT=ROOT/"isa/generated/universal-instruction-catalog.json"
def tokens(value): return set(re.findall(r"[a-z0-9_+.-]+",str(value).casefold()))
def rank(query,catalog,limit=10):
 q=tokens(query); recurrent=RecurrentState(24); out=[]
 for row in catalog.get("instructions",[]):
  text=" ".join(str(row.get(k,"")) for k in ("architecture","mnemonic","form_id","source_ref","extensions"))
  t=tokens(text); overlap=len(q&t)/max(1,len(q|t))
  h=recurrent.step([overlap,float(row.get("encoding_status")=="sourced-mask-verified"),float(row.get("execution_status")=="conformance-tested")])
  score=overlap+0.02*sum(h[:4])/4
  out.append((score,row))
 out.sort(key=lambda x:(-x[0],x[1].get("architecture",""),x[1].get("mnemonic",""),x[1].get("form_id","")))
 return [{"architecture":r.get("architecture"),"mnemonic":r.get("mnemonic"),"form_id":r.get("form_id"),
  "encoding_status":r.get("encoding_status"),"execution_status":r.get("execution_status"),
  "source_ref":r.get("source_ref"),"score":round(s,6),"execution_allowed":False,
  "next_step":"verify architecture manual and conformance vectors before implementation"} for s,r in out[:limit]]
def queue_unresolved(query,catalog,queue_path):
 q=tokens(query)
 found=any(all(t in " ".join(str(row.get(k,"")) for k in ("architecture","mnemonic","form_id")).casefold() for t in q) for row in catalog.get("instructions",[]))
 if found:return None
 record={"candidate_hint":(query.strip().split(maxsplit=1)[0] if query.strip() else "")[:64],"query_token_count":len(q),"query_sha256":hashlib.sha256(query.encode("utf-8")).hexdigest(),"status":"pending",
  "reason":"no exact architecture/mnemonic candidate; source and conformance review required","created_at_utc":datetime.now(timezone.utc).isoformat()}
 queue_path.parent.mkdir(parents=True,exist_ok=True)
 with queue_path.open("a",encoding="utf-8") as stream:stream.write(json.dumps(record,ensure_ascii=False)+"\n")
 return str(queue_path)
def main():
 p=argparse.ArgumentParser();p.add_argument("query");p.add_argument("--limit",type=int,default=10);p.add_argument("--catalog",type=Path,default=DEFAULT);p.add_argument("--queue",type=Path,default=Path.home()/".local/state/chimera/isa-candidates.jsonl");p.add_argument("--llm",action="store_true",help="use a separately configured loopback local LLM to rerank candidates");p.add_argument("--rnn-model",type=Path,help="optional trained character-RNN JSON model for candidate ranking");a=p.parse_args()
 if not 1<=a.limit<=100:raise SystemExit("--limit must be 1..100")
 data=json.loads(a.catalog.read_text(encoding="utf-8"));results=rank(a.query,data,max(a.limit,min(100,len(data.get("instructions",[])))));llm_meta={"mode":"deterministic-rnn","validated":False}
 if a.rnn_model:
  try:
   from tools.cognition.trainable_rnn_lm import CharRNN
  except ModuleNotFoundError:
   from trainable_rnn_lm import CharRNN
  trained=CharRNN.load(a.rnn_model)
  results.sort(key=lambda r:(-trained.score(a.query+" "+str(r.get("architecture",""))+" "+str(r.get("mnemonic",""))+" "+str(r.get("form_id",""))),str(r.get("architecture","")),str(r.get("mnemonic",""))))
  llm_meta={"mode":"trained-character-rnn","model":str(a.rnn_model),"validated":True,"llm_scale":False}
 if a.llm:
  candidates=[{"id":str(r.get("architecture",""))+"|"+str(r.get("mnemonic",""))+"|"+str(r.get("form_id","")),"label":str(r.get("architecture",""))+" "+str(r.get("mnemonic",""))+" "+str(r.get("form_id",""))+" | "+str(r.get("encoding_status",""))+" | "+str(r.get("execution_status",""))} for r in results]
  ordered,llm_meta=local_llm_rerank(a.query,candidates,a.limit);by_id={str(r.get("architecture",""))+"|"+str(r.get("mnemonic",""))+"|"+str(r.get("form_id","")):r for r in results};results=[by_id[c["id"]] for c in ordered if c["id"] in by_id][:a.limit]
 else: results=results[:a.limit]
 queued=queue_unresolved(a.query,data,a.queue)
 print(json.dumps({"schema":"CHM-RNN-ISA-CANDIDATE-ROUTER-1","engine":"deterministic recurrent-state retrieval"+(" with constrained local LLM reranking" if a.llm else "")+(" with trained character-RNN scoring" if a.rnn_model else ""),"llm":llm_meta,"query":a.query,"result_count":len(results),"results":results,"queued_for_later":bool(queued),"queue_file":queued,"safety":"Ranking is advisory. No opcode, semantic, native mapping, or conformance fact is invented."},ensure_ascii=False,indent=2))
if __name__=="__main__":main()

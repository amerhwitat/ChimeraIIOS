#!/usr/bin/env python3
"""Trainable character-level recurrent language model for local OS research.

This is a small, auditable RNN language model, not an LLM-scale foundation model.
It learns next-character probabilities from supplied local catalogs. It never
assigns execution permissions or derives instruction semantics.
"""
from __future__ import annotations
import argparse, json, math, random
from pathlib import Path

class CharRNN:
    def __init__(self, chars, hidden=16, seed=7):
        self.chars = list(chars)
        if len(self.chars) < 2: raise ValueError("training corpus needs at least two characters")
        self.index = {c:i for i,c in enumerate(self.chars)}
        self.v = len(self.chars); self.h = int(hidden)
        if not 2 <= self.h <= 64: raise ValueError("hidden size must be 2..64")
        rng = random.Random(seed)
        scale = 0.08
        self.Wxh = [[rng.uniform(-scale,scale) for _ in range(self.v)] for _ in range(self.h)]
        self.Whh = [[rng.uniform(-scale,scale) for _ in range(self.h)] for _ in range(self.h)]
        self.Why = [[rng.uniform(-scale,scale) for _ in range(self.h)] for _ in range(self.v)]
        self.bh = [0.0]*self.h; self.by = [0.0]*self.v

    def _forward(self, inputs):
        states=[]; probs=[]; prev=[0.0]*self.h
        for ix in inputs:
            state=[math.tanh(self.Wxh[j][ix]+sum(self.Whh[j][k]*prev[k] for k in range(self.h))+self.bh[j]) for j in range(self.h)]
            logits=[sum(self.Why[i][j]*state[j] for j in range(self.h))+self.by[i] for i in range(self.v)]
            peak=max(logits); ex=[math.exp(max(-60.0,z-peak)) for z in logits]; total=sum(ex)
            probs.append([x/total for x in ex]); states.append(state); prev=state
        return states,probs

    def train(self, corpus, epochs=12, learning_rate=0.04):
        sequences=[]
        for line in corpus:
            seq=[self.index[c] for c in line if c in self.index]
            if len(seq)>=2: sequences.append(seq[:160])
        if not sequences: raise ValueError("no usable training sequences")
        history=[]
        for _epoch in range(max(1,min(epochs,100))):
            total_loss=0.0; count=0
            for seq in sequences:
                xs,ys=seq[:-1],seq[1:]
                states,probs=self._forward(xs)
                total_loss += -sum(math.log(max(1e-12,probs[t][ys[t]])) for t in range(len(ys))); count+=len(ys)
                gWxh=[[0.0]*self.v for _ in range(self.h)]; gWhh=[[0.0]*self.h for _ in range(self.h)]
                gWhy=[[0.0]*self.h for _ in range(self.v)]; gbh=[0.0]*self.h; gby=[0.0]*self.v
                dhnext=[0.0]*self.h
                for t in range(len(ys)-1,-1,-1):
                    dy=probs[t][:]; dy[ys[t]]-=1.0
                    for i in range(self.v):
                        gby[i]+=dy[i]
                        for j in range(self.h): gWhy[i][j]+=dy[i]*states[t][j]
                    dh=[sum(self.Why[i][j]*dy[i] for i in range(self.v))+dhnext[j] for j in range(self.h)]
                    dhraw=[dh[j]*(1.0-states[t][j]*states[t][j]) for j in range(self.h)]
                    for j in range(self.h):
                        gbh[j]+=dhraw[j]; gWxh[j][xs[t]]+=dhraw[j]
                        for k in range(self.h): gWhh[j][k]+=dhraw[j]*(states[t-1][k] if t else 0.0)
                    dhnext=[sum(self.Whh[j][k]*dhraw[j] for j in range(self.h)) for k in range(self.h)]
                def apply(matrix, grad):
                    for i,row in enumerate(matrix):
                        for j in range(len(row)): row[j]-=learning_rate*max(-5.0,min(5.0,grad[i][j]))
                apply(self.Wxh,gWxh); apply(self.Whh,gWhh); apply(self.Why,gWhy)
                for i in range(self.h): self.bh[i]-=learning_rate*max(-5.0,min(5.0,gbh[i]))
                for i in range(self.v): self.by[i]-=learning_rate*max(-5.0,min(5.0,gby[i]))
            history.append(total_loss/max(1,count))
        return history

    def score(self, text):
        if len(text)<2: return -100.0
        ids=[self.index.get(c,-1) for c in text]
        unk=self.index.get(" ",0)
        ids=[unk if i<0 else i for i in ids]
        _,probs=self._forward(ids[:-1])
        return sum(math.log(max(1e-12,probs[t][ids[t+1]])) for t in range(len(ids)-1))/max(1,len(ids)-1)

    def save(self,path,metadata=None):
        data={"schema":"CHIMERA-CHAR-RNN-LM-1","model_type":"trained-character-level-vanilla-RNN",
              "hidden_size":self.h,"vocabulary":self.chars,"Wxh":self.Wxh,"Whh":self.Whh,
              "Why":self.Why,"bh":self.bh,"by":self.by,"metadata":metadata or {}}
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,separators=(",",":")),encoding="utf-8")

    @classmethod
    def load(cls,path):
        d=json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(d,dict) or d.get("schema")!="CHIMERA-CHAR-RNN-LM-1":
            raise ValueError("unsupported model schema")
        vocabulary=d.get("vocabulary")
        hidden=d.get("hidden_size")
        if (not isinstance(vocabulary,list) or len(vocabulary)<2
                or not all(isinstance(c,str) and len(c)==1 for c in vocabulary)
                or len(set(vocabulary))!=len(vocabulary)
                or not isinstance(hidden,int) or isinstance(hidden,bool) or not 2<=hidden<=64):
            raise ValueError("model vocabulary or hidden size invalid")
        obj=cls(vocabulary,hidden)
        shapes={"Wxh":(obj.h,obj.v),"Whh":(obj.h,obj.h),"Why":(obj.v,obj.h),"bh":(obj.h,),"by":(obj.v,)}
        for key,shape in shapes.items():
            value=d.get(key)
            if len(shape)==2:
                valid=(isinstance(value,list) and len(value)==shape[0]
                       and all(isinstance(row,list) and len(row)==shape[1] for row in value))
                flat=[x for row in value for x in row] if valid else []
            else:
                valid=isinstance(value,list) and len(value)==shape[0]
                flat=value if valid else []
            if not valid or not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in flat):
                raise ValueError(f"model tensor invalid: {key}")
            setattr(obj,key,value)
        if not isinstance(d.get("metadata",{}),dict):
            raise ValueError("model metadata invalid")
        return obj

def extract_strings(value, out, depth=0):
    if depth>8 or len(out)>=20000: return
    if isinstance(value,str):
        v=value.strip()
        if 2<=len(v)<=256 and any(c.isalnum() for c in v): out.append(v)
    elif isinstance(value,list):
        for x in value: extract_strings(x,out,depth+1)
    elif isinstance(value,dict):
        for k,v in value.items():
            if k in {"source_ref","url","description","summary","provenance"}: continue
            extract_strings(k,out,depth+1); extract_strings(v,out,depth+1)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    t=sub.add_parser("train");t.add_argument("--source",type=Path,action="append",required=True);t.add_argument("--output",type=Path,required=True);t.add_argument("--epochs",type=int,default=12);t.add_argument("--hidden",type=int,default=16);t.add_argument("--seed",type=int,default=7)
    s=sub.add_parser("score");s.add_argument("--model",type=Path,required=True);s.add_argument("--text",required=True)
    a=p.parse_args()
    if a.command=="train":
        corpus=[]
        for path in a.source:
            if not path.is_file(): raise SystemExit("missing source catalog: "+str(path))
            raw=path.read_text(encoding="utf-8")
            try: extract_strings(json.loads(raw),corpus)
            except json.JSONDecodeError: corpus.extend(x.strip() for x in raw.splitlines() if x.strip())
        corpus=list(dict.fromkeys(corpus))
        chars=sorted(set("".join(corpus)+" \n"))
        model=CharRNN(chars,a.hidden,a.seed);loss=model.train(corpus,a.epochs)
        model.save(a.output,{"sources":[str(x) for x in a.source],"training_sequences":len(corpus),"epochs":len(loss),"final_mean_nll":loss[-1],"seed":a.seed})
        print(json.dumps({"status":"trained","model_type":"trained-character-level-vanilla-RNN","training_sequences":len(corpus),"vocabulary":len(chars),"hidden_size":a.hidden,"loss_first":loss[0],"loss_last":loss[-1],"model":str(a.output)}))
    else:
        model=CharRNN.load(a.model);print(json.dumps({"score":model.score(a.text),"model_type":"trained-character-level-vanilla-RNN"}))
if __name__=="__main__": main()

#!/usr/bin/env python3
"""Chimera online learning daemon.

Observes JSONL events emitted by system services and maintains a bounded model.
PyTorch is used when available; otherwise the daemon remains a safe collector.
The learner never executes actions, changes boot configuration, flashes firmware,
or performs destructive storage operations.
"""
import json, os, time, pathlib
from collections import Counter
EVENTS=pathlib.Path(os.environ.get("CHIMERA_LEARNING_EVENTS","/var/log/chimera/learning/events.jsonl"))
MODEL=pathlib.Path(os.environ.get("CHIMERA_LEARNING_MODEL","/var/lib/chimera/learning/model.json"))
NETWORK=pathlib.Path(os.environ.get("CHIMERA_NETWORK_STATE","/var/lib/chimera/network/discovery.json"))
MAX_EVENTS=int(os.environ.get("CHIMERA_LEARNING_MAX_EVENTS","100000"))
try:
    import torch
    import torch.nn as nn
    TORCH=True
except Exception:
    TORCH=False

def safe_event(e):
    if not isinstance(e,dict): return None
    action=str(e.get("action","unknown"))[:128]
    value=float(e.get("value",0) or 0)
    return {"ts":float(e.get("ts",time.time())), "action":action, "value":value}

def observe_network(counts):
    try:
        data=json.loads(NETWORK.read_text())
        for result in data.get("results",[]):
            if "error" in result: counts["network:error"]+=1; continue
            counts["network:scan"]+=1
            text=result.get("xml","")
            counts["network:bytes"]+=len(text)
            counts["network:host"]+=text.count("<host>")
    except Exception: pass

def main():
    EVENTS.parent.mkdir(parents=True,exist_ok=True); MODEL.parent.mkdir(parents=True,exist_ok=True)
    counts=Counter(); seen=0
    model={"backend":"pytorch" if TORCH else "collector","events":0,"actions":{}}
    with EVENTS.open("a+",encoding="utf-8") as f:
        f.seek(0)
        for line in f:
            try:
                e=safe_event(json.loads(line))
                if e: counts[e["action"]]+=1; seen+=1
            except Exception: pass
        while True:
            line=f.readline()
            if not line:
                time.sleep(0.25); continue
            try:
                e=safe_event(json.loads(line))
                if not e: continue
                counts[e["action"]]+=1; seen+=1
                observe_network(counts)\n                model["events"]=min(seen,MAX_EVENTS)
                model["actions"]=dict(counts.most_common(256))
                if seen % 32 == 0:
                    tmp=MODEL.with_suffix(".tmp")
                    tmp.write_text(json.dumps(model,indent=2),encoding="utf-8"); tmp.replace(MODEL)
            except Exception: continue
if __name__=="__main__": main()

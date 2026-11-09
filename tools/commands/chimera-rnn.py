#!/usr/bin/env python3
"""CLI for the deterministic Chimera recurrent-state and evidence reference engine."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/cognition"))
from chimera_rnn import Evidence, KnowledgeBus, RecurrentState

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action",required=True)
    sub.add_parser("info")
    step=sub.add_parser("step");step.add_argument("--size",type=int,default=32);step.add_argument("--features",type=float,nargs="+",required=True)
    evidence=sub.add_parser("evidence");evidence.add_argument("--source",required=True);evidence.add_argument("--title",required=True);evidence.add_argument("--summary",required=True)
    args=parser.parse_args()
    if args.action=="info":
        print(json.dumps({"engine":"RecurrentState","execution":"deterministic-reference","agi_claim":False,"state_size_limit":4096},indent=2));return 0
    if args.action=="step":
        state=RecurrentState(args.size);print(json.dumps({"state":state.step(args.features),"size":args.size},indent=2));return 0
    bus=KnowledgeBus();item=Evidence.from_text(args.source,args.title,args.summary);bus.add(item)
    print(bus.export());return 0
if __name__=="__main__": raise SystemExit(main())

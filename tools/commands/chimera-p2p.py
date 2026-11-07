#!/usr/bin/env python3
"""CLI for Chimera P2P envelope framing and integrity verification."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"p2p/python"))
from chimera_p2p import Envelope, decode

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action",required=True)
    enc=sub.add_parser("encode")
    enc.add_argument("--node-id",required=True)
    enc.add_argument("--kind",required=True)
    enc.add_argument("--sequence",type=int,required=True)
    enc.add_argument("--payload",required=True,help="JSON payload")
    enc.add_argument("--capability",action="append",default=[])
    dec=sub.add_parser("decode")
    dec.add_argument("input",nargs="?",default="-")
    args=parser.parse_args()
    if args.action=="encode":
        try: payload=json.loads(args.payload)
        except json.JSONDecodeError as exc: parser.error(f"invalid payload JSON: {exc}")
        envelope=Envelope(args.node_id,args.kind,args.sequence,payload,capabilities=args.capability)
        sys.stdout.buffer.write(envelope.encode())
        return 0
    raw=sys.stdin.buffer.read() if args.input=="-" else Path(args.input).read_bytes()
    try: message=decode(raw)
    except (ValueError,KeyError,json.JSONDecodeError) as exc:
        print(f"chimera-p2p: {exc}",file=sys.stderr);return 2
    print(json.dumps(message,ensure_ascii=False,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())

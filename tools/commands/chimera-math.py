#!/usr/bin/env python3
"""Dependency-free vector, tensor, 128D and hyperdimensional computing CLI."""
from __future__ import annotations
import argparse, hashlib, json, math, random, sys

def vector(value):
    try: v=json.loads(value)
    except json.JSONDecodeError as exc: raise ValueError(f"invalid vector JSON: {exc}") from exc
    if not isinstance(v,list) or not v or any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) for x in v):
        raise ValueError("vector must be a non-empty JSON array of finite numbers")
    return [float(x) for x in v]

def same(a,b):
    if len(a)!=len(b): raise ValueError("vector dimensions differ")
def dot(a,b):
    same(a,b);return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(sum(x*x for x in a))
def hdc_encode(text,dimension,seed):
    bits=[];counter=0
    while len(bits)<dimension:
        digest=hashlib.sha256(f"{seed}\0{counter}\0{text}".encode()).digest()
        for byte in digest:
            bits.extend(str((byte>>i)&1) for i in range(8))
        counter+=1
    return "".join(bits[:dimension])
def bits(value):
    if not value or any(c not in "01" for c in value): raise ValueError("HDC vector must contain only 0 and 1")
    return value
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="family",required=True)
    for family in ("vector","128d"):
        q=sub.add_parser(family);ops=q.add_subparsers(dest="op",required=True)
        for op in ("add","sub","dot","norm","normalize","cosine"):
            z=ops.add_parser(op);z.add_argument("--a",required=True)
            if op not in ("norm","normalize"): z.add_argument("--b",required=True)
    t=sub.add_parser("tensor");tops=t.add_subparsers(dest="op",required=True)
    for op in ("shape","transpose","matmul","outer"):
        z=tops.add_parser(op);z.add_argument("--a",required=True)
        if op not in ("shape","transpose"):z.add_argument("--b",required=True)
    h=sub.add_parser("hdc");hops=h.add_subparsers(dest="op",required=True)
    e=hops.add_parser("encode");e.add_argument("--text",required=True);e.add_argument("--dimension",type=int,default=10000);e.add_argument("--seed",type=int,default=7)
    for op in ("bind","similarity"):
        z=hops.add_parser(op);z.add_argument("--a",required=True);z.add_argument("--b",required=True)
    b=hops.add_parser("bundle");b.add_argument("--vectors",required=True,help="JSON array of equal-length bit strings")
    pm=hops.add_parser("permute");pm.add_argument("--a",required=True);pm.add_argument("--shift",type=int,default=1)
    a=p.parse_args()
    if a.family in ("vector","128d"):
        av=vector(a.a)
        if a.family=="128d" and len(av)!=128: raise ValueError("128D operations require exactly 128 components")
        if a.op=="norm": result=norm(av)
        elif a.op=="normalize":
            n=norm(av)
            if n==0: raise ValueError("zero vector cannot be normalized")
            result=[x/n for x in av]
        else:
            bv=vector(a.b)
            if a.family=="128d" and len(bv)!=128: raise ValueError("128D operations require exactly 128 components")
            same(av,bv)
            if a.op=="add": result=[x+y for x,y in zip(av,bv)]
            elif a.op=="sub": result=[x-y for x,y in zip(av,bv)]
            elif a.op=="dot": result=dot(av,bv)
            else:
                den=norm(av)*norm(bv)
                if den==0: raise ValueError("cosine similarity is undefined for a zero vector")
                result=dot(av,bv)/den
        print(json.dumps({"family":a.family,"operation":a.op,"dimension":len(av),"result":result},allow_nan=False));return 0
    if a.family=="tensor":
        x=json.loads(a.a)
        def shape(v):
            if not isinstance(v,list): return []
            child=shape(v[0]) if v else []
            if any(shape(item)!=child for item in v): raise ValueError("ragged tensors are not supported")
            return [len(v)]+child
        sx=shape(x)
        if a.op=="shape": result=sx
        elif a.op=="transpose":
            if len(sx)!=2: raise ValueError("transpose currently requires a rank-2 matrix")
            result=[list(row) for row in zip(*x)]
        elif a.op=="outer":
            y=json.loads(a.b)
            if len(sx)!=1 or len(shape(y))!=1: raise ValueError("outer requires two vectors")
            result=[[float(i)*float(j) for j in y] for i in x]
        else:
            y=json.loads(a.b);sy=shape(y)
            if len(sx)!=2 or len(sy)!=2 or sx[1]!=sy[0]: raise ValueError("matmul requires compatible rank-2 matrices")
            result=[[sum(float(x[i][k])*float(y[k][j]) for k in range(sx[1])) for j in range(sy[1])] for i in range(sx[0])]
        print(json.dumps({"family":"tensor","operation":a.op,"shape":shape(result),"result":result},allow_nan=False));return 0
    if a.family=="hdc":
        if a.op=="encode":
            if not 8<=a.dimension<=100000: raise ValueError("HDC dimension must be in 8..100000")
            result=hdc_encode(a.text,a.dimension,a.seed)
        elif a.op in ("bind","similarity"):
            x,y=bits(a.a),bits(a.b)
            if len(x)!=len(y): raise ValueError("HDC vector dimensions differ")
            if a.op=="bind": result="".join("1" if i!=j else "0" for i,j in zip(x,y))
            else:
                bipolar_x=[1 if c=="1" else -1 for c in x];bipolar_y=[1 if c=="1" else -1 for c in y]
                result=sum(i*j for i,j in zip(bipolar_x,bipolar_y))/len(x)
        elif a.op=="bundle":
            vectors=json.loads(a.vectors)
            if not isinstance(vectors,list) or not vectors: raise ValueError("bundle requires a non-empty JSON array")
            vectors=[bits(v) for v in vectors];n=len(vectors[0])
            if any(len(v)!=n for v in vectors): raise ValueError("HDC vector dimensions differ")
            result="".join("1" if sum(v[i]=="1" for v in vectors)>len(vectors)/2 else "0" for i in range(n))
        else:
            x=bits(a.a);shift=a.shift%len(x);result=x[-shift:]+x[:-shift] if shift else x
        print(json.dumps({"family":"hdc","operation":a.op,"dimension":len(result) if isinstance(result,str) else a.dimension if a.op=="encode" else len(x),"result":result,"bits":result if isinstance(result,str) else None},allow_nan=False));return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except (ValueError,TypeError,json.JSONDecodeError) as exc:
        print(f"chimera-math: {exc}",file=sys.stderr);raise SystemExit(2)

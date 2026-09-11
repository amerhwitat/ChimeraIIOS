"""Deterministic discovery for ISO-Tool assembler/disassembler backends."""
from __future__ import annotations
import json, os, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REGISTRY=ROOT/'registry.json'
def load_registry(): return json.loads(REGISTRY.read_text(encoding='utf-8'))
def _vs():
    roots=[Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Microsoft Visual Studio',Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft Visual Studio']
    return [p for r in roots if r.exists() for p in r.rglob('ml64.exe')]
def find_command(name):
    hit=shutil.which(name)
    if hit:return hit
    if name.lower() in {'ml','ml.exe','ml64','ml64.exe'}:
        h=_vs(); return str(h[0]) if h else None
    return None
def discover():
    out=[]
    for b in load_registry()['backends']:
        found=[p for c in b['commands'] if (p:=find_command(c))]
        out.append({**b,'found':found,'available':bool(found)})
    return out
def select(kind,target=None):
    c=[x for x in discover() if x['available'] and (kind in x['kind'].split('-') or x['kind']==kind)]
    if target:
        t=[x for x in c if target in x['targets'] or 'multi-target' in x['targets'] or 'llvm-targets' in x['targets']]
        c=t or c
    return c[0] if c else None
def version(executable):
    try:
        p=subprocess.run([executable,'--version'],capture_output=True,text=True,timeout=5)
        return (p.stdout or p.stderr).splitlines()[0].strip()
    except (OSError,subprocess.SubprocessError): return 'unknown'
if __name__=='__main__':
    for x in discover():
        e=x['found'][0] if x['found'] else ''
        print(f"{x['id']}: {'available' if x['available'] else 'missing'} {e} {version(e) if e else ''}".rstrip())

#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
import re,sys

ROOT=Path(__file__).resolve().parents[2]/"web"
errors=[]; warnings=[]

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set(); self.refs=[]; self.inline=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if "id" in d:self.ids.add(d["id"])
        for k in ("href","src"):
            v=d.get(k)
            if v:self.refs.append((k,v))
    def handle_data(self,data):
        self.inline.append(data)

def local_target(page,ref):
    ref=ref.split("#",1)[0].split("?",1)[0]
    if not ref or ref.startswith(("#","http:","https:","ws:","wss:","data:","mailto:","javascript:")): return None
    return (page.parent/ref).resolve()

for page in ROOT.glob("*.html"):
    p=Page()
    try:p.feed(page.read_text(encoding="utf-8"))
    except Exception as e:errors.append(f"{page.name}: HTML parse failed: {e}");continue
    for kind,ref in p.refs:
        target=local_target(page,ref)
        if target and not target.exists():
            errors.append(f"{page.name}: broken {kind} -> {ref}")
        if "#" in ref and not ref.startswith("#"):
            frag=ref.split("#",1)[1]
            if frag and frag not in p.ids:
                target=local_target(page,ref)
                if target is not None and target.exists():
                    tp=Page()
                    try:tp.feed(target.read_text(encoding="utf-8"))
                    except Exception:continue
                    if frag not in tp.ids and f"view-{frag}" not in tp.ids:
                        errors.append(f"{page.name}: broken fragment -> {ref}")
    for kind,ref in p.refs:
        if kind=="src" and ref.endswith(".js"):
            target=local_target(page,ref)
            if target and target.exists():
                js=target.read_text(encoding="utf-8")
                try:
                    import subprocess
                    r=subprocess.run(["node","--check",str(target)],capture_output=True,text=True)
                    if r.returncode:errors.append(f"{target.relative_to(ROOT)}: node --check failed: {r.stderr.strip()}")
                except FileNotFoundError:warnings.append("node not available for JavaScript syntax checks")

for js in ROOT.glob("*.js"):
    if js.name=="service-worker.js":continue
    try:
        import subprocess
        r=subprocess.run(["node","--check",str(js)],capture_output=True,text=True)
        if r.returncode:errors.append(f"{js.name}: node --check failed: {r.stderr.strip()}")
    except FileNotFoundError:break

if errors:
    print("WEB UI AUDIT: FAIL")
    print("\n".join(errors))
    sys.exit(1)
print("WEB UI AUDIT: PASS")
if warnings: print("\n".join(warnings))

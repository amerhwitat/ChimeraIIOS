#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, subprocess
ROOT=Path(__file__).resolve().parents[2]; MANIFEST=ROOT/"web"/"game-center-manifest.json"; PORT=int(os.environ.get("CHIMERA_GAME_PORT","8769")); BINROOT=Path(os.environ.get("CHIMERA_GAME_BINROOT",str(ROOT/".local"/"games")))
def load(): return {x[0]:x for x in json.loads(MANIFEST.read_text(encoding="utf-8"))["games"]}
def send(h,c,o):
 raw=json.dumps(o,ensure_ascii=False).encode(); h.send_response(c); h.send_header("Content-Type","application/json; charset=utf-8"); h.send_header("Access-Control-Allow-Origin","*"); h.send_header("Access-Control-Allow-Headers","Content-Type"); h.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); h.end_headers(); h.wfile.write(raw)
class H(BaseHTTPRequestHandler):
 def do_OPTIONS(self): send(self,204,{})
 def do_GET(self):
  if self.path=="/health": return send(self,200,{"ok":True,"version":"chimera-game-center/1","manifest":str(MANIFEST),"binaryRoot":str(BINROOT)})
  if self.path=="/games/catalog": return send(self,200,{"ok":True,"games":list(load().values())})
  return send(self,404,{"error":"not-found"})
 def do_POST(self):
  n=int(self.headers.get("Content-Length","0")); d=json.loads(self.rfile.read(n) or b"{}")
  if self.path=="/games/launch":
   gid=str(d.get("id","")); item=load().get(gid)
   if not item:return send(self,404,{"error":"game-not-in-allowlist"})
   exe=BINROOT/gid
   if not exe.exists():
    p=BINROOT/(gid+".path")
    if p.exists():
     base=Path(p.read_text().strip())
     for z in [base/gid,base/"build"/gid,base/"build"/"bin"/gid,base/"bin"/gid]:
      if z.exists() and os.access(z,os.X_OK): exe=z; break
   if not exe.exists():return send(self,409,{"error":"game-not-built-locally","game":gid,"build":"tools/game-center/build-open-games.sh"})
   if not os.access(exe,os.X_OK):return send(self,409,{"error":"game-binary-not-executable","path":str(exe)})
   args=d.get("args") or []
   if not isinstance(args,list) or any(not isinstance(x,str) for x in args):return send(self,400,{"error":"args-must-be-string-array"})
   subprocess.Popen([str(exe),*args],cwd=str(exe.parent),start_new_session=True); return send(self,200,{"ok":True,"game":gid,"command":[str(exe),*args]})
  return send(self,404,{"error":"not-found"})
 def log_message(self,*a): pass
if __name__=="__main__":
 BINROOT.mkdir(parents=True,exist_ok=True); print(f"Chimera Game Center bridge on http://127.0.0.1:{PORT}"); ThreadingHTTPServer(("127.0.0.1",PORT),H).serve_forever()

#!/usr/bin/env python3
import json, os, secrets, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
HOST=os.environ.get("CHIMERA_WEB_HOST","127.0.0.1"); PORT=int(os.environ.get("CHIMERA_WEB_PORT","8765")); TOKEN_FILE=os.environ.get("CHIMERA_WEB_TOKEN_FILE","/etc/chimera/web.token")
def token():
 try:
  with open(TOKEN_FILE,encoding="utf-8") as f:return f.read().strip()
 except OSError:return ""
def run(a,t=15):return subprocess.run(a,text=True,capture_output=True,timeout=t)
def podman(a):
 if not a or a[0] not in {"ps","images","pods","version","info"}:return {"ok":False,"error":"operation not allowed"}
 r=run(["podman",*a]);return {"ok":r.returncode==0,"stdout":r.stdout,"stderr":r.stderr,"code":r.returncode}
INDEX="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Chimera II OS</title><style>body{font-family:system-ui;background:#10151d;color:#eee;margin:0}header{padding:18px;background:#172131}main{padding:20px;max-width:1100px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.card{background:#1b2636;padding:16px;border-radius:12px}button,input{padding:9px;margin:4px;border-radius:7px;border:1px solid #445;background:#111;color:#eee}pre{white-space:pre-wrap;max-height:320px;overflow:auto}</style><header><b>Chimera II OS</b> — Node Control / Podman</header><main><input id="token" type="password" placeholder="Web API token"><button onclick="save()">Save</button><button onclick="loadAll()">Refresh</button><div class="grid"><section class="card"><h2>Containers</h2><button onclick="api('/api/podman/ps')">List</button><pre id="ps"></pre></section><section class="card"><h2>Images</h2><button onclick="api('/api/podman/images','images')">List</button><pre id="images"></pre></section><section class="card"><h2>Pods</h2><button onclick="api('/api/podman/pods','pods')">List</button><pre id="pods"></pre></section><section class="card"><h2>System</h2><button onclick="api('/api/system/status','system')">Status</button><button onclick="api('/api/system/diagnostics','system')">Diagnostics</button><pre id="system"></pre></section></div><section class="card"><h2>Container action</h2><input id="name" placeholder="container name"><button onclick="act('start')">Start</button><button onclick="act('stop')">Stop</button><button onclick="act('restart')">Restart</button><button onclick="act('pause')">Pause</button><button onclick="act('unpause')">Unpause</button><pre id="action"></pre></section><script>function save(){localStorage.setItem('chimeraToken',document.getElementById('token').value)}function hdr(){return {'Authorization':'Bearer '+(document.getElementById('token').value||localStorage.getItem('chimeraToken')||'')}}async function api(u,id){let r=await fetch(u,{headers:hdr()});document.getElementById(id||'ps').textContent=JSON.stringify(await r.json(),null,2)}async function act(action){let name=document.getElementById('name').value;let r=await fetch('/api/podman/action',{method:'POST',headers:{...hdr(),'Content-Type':'application/json'},body:JSON.stringify({action,name})});document.getElementById('action').textContent=JSON.stringify(await r.json(),null,2)}function loadAll(){api('/api/podman/ps');api('/api/podman/images','images');api('/api/podman/pods','pods')}document.getElementById('token').value=localStorage.getItem('chimeraToken')||'';</script></main>"""
class H(BaseHTTPRequestHandler):
 def auth(self):
  e=token();a=self.headers.get("Authorization","").removeprefix("Bearer ").strip();return bool(e) and secrets.compare_digest(a,e)
 def out(self,x,s=200):
  d=json.dumps(x,ensure_ascii=False).encode();self.send_response(s);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(d)));self.end_headers();self.wfile.write(d)
 def do_GET(self):
  p=urlparse(self.path).path
  if p=="/api/health":return self.out({"ok":True,"service":"chimera-web"})
  if p.startswith("/api/"):
   if not self.auth():return self.out({"error":"unauthorized"},401)
   m={"/api/podman/ps":["ps","--all"],"/api/podman/images":["images"],"/api/podman/pods":["pod","ps","--all"],"/api/podman/version":["version"],"/api/podman/info":["info"]}
   if p in m:return self.out(podman(m[p]))
   if p in ("/api/system/status","/api/system/diagnostics"):
    r=run(["chmctl","status"] if p.endswith("status") else ["chm-diagnostics"]);return self.out({"ok":r.returncode==0,"stdout":r.stdout,"stderr":r.stderr,"code":r.returncode})
  if p in ("/","/index.html"):
   d=INDEX.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(d)));self.end_headers();self.wfile.write(d);return
  self.send_error(404)
 def do_POST(self):
  if not self.auth():return self.out({"error":"unauthorized"},401)
  if urlparse(self.path).path!="/api/podman/action":return self.out({"error":"not found"},404)
  n=int(self.headers.get("Content-Length","0") or 0)
  if n>4096:return self.out({"error":"request too large"},413)
  try:b=json.loads(self.rfile.read(n) or b"{}")
  except Exception:return self.out({"error":"invalid json"},400)
  action,name=b.get("action"),b.get("name","");allowed={"start":"start","stop":"stop","restart":"restart","pause":"pause","unpause":"unpause"}
  if action not in allowed or not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in name):return self.out({"error":"invalid action or name"},400)
  r=run(["podman",allowed[action],name]);return self.out({"ok":r.returncode==0,"stdout":r.stdout,"stderr":r.stderr,"code":r.returncode})
if __name__=="__main__":
 if not token():raise SystemExit("missing web token; refusing unauthenticated control server")
 ThreadingHTTPServer((HOST,PORT),H).serve_forever()

#!/usr/bin/env python3
"""Chimera II OS web administration console.

Cockpit-inspired, but native to Chimera II.  The API deliberately exposes
an allow-listed set of operating-system operations rather than arbitrary
shell execution. Authentication is a bearer token stored outside the web
tree. Privileged operations require the web service itself to have the
corresponding OS permission.
"""
import json, os, secrets, shlex, ssl, subprocess, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOST = os.environ.get("CHIMERA_WEB_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHIMERA_WEB_PORT", "8765"))
TOKEN_FILE = os.environ.get("CHIMERA_WEB_TOKEN_FILE", "/etc/chimera/web.token")
AUDIT_FILE = os.environ.get("CHIMERA_WEB_AUDIT_FILE", "/var/log/chimera/web-audit.log")
CERT_FILE = os.environ.get("CHIMERA_WEB_CERT", "")
KEY_FILE = os.environ.get("CHIMERA_WEB_KEY", "")
MAX_BODY = 16384

INDEX = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Chimera II OS Web Console</title>
<style>
body{font-family:system-ui,sans-serif;background:#0d1420;color:#eaf0f7;margin:0}
header{padding:18px 24px;background:#152338;position:sticky;top:0;z-index:2}
main{max-width:1400px;margin:auto;padding:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:#172235;border:1px solid #2d3b51;border-radius:12px;padding:16px;box-shadow:0 5px 20px #0004}
button,input,select{background:#0c1420;color:#eaf0f7;border:1px solid #43536b;border-radius:7px;padding:9px;margin:3px}
button{cursor:pointer}pre{white-space:pre-wrap;max-height:360px;overflow:auto;font-size:12px}
.badge{padding:4px 8px;border-radius:9px;background:#29435f}.danger{border-color:#9b3d46}
</style></head><body>
<header><b>Chimera II OS</b> — Web Administration Console <span id="state" class="badge">disconnected</span></header>
<main>
<div class="card"><input id="token" type="password" placeholder="Web API token" size="42"><button onclick="save()">Save token</button><button onclick="refresh()">Refresh all</button></div>
<div class="grid">
<section class="card"><h2>Overview</h2><pre id="overview"></pre></section>
<section class="card"><h2>Services</h2><button onclick="get('/api/services','services')">Refresh</button><pre id="services"></pre>
<select id="svc"><option>chimera-web</option><option>chimera-kernel</option><option>docker</option><option>sshd</option></select>
<button onclick="service('start')">Start</button><button onclick="service('stop')">Stop</button><button onclick="service('restart')">Restart</button></section>
<section class="card"><h2>Users</h2><button onclick="get('/api/users','users')">Refresh</button><pre id="users"></pre></section>
<section class="card"><h2>Network</h2><button onclick="get('/api/network','network')">Refresh</button><pre id="network"></pre></section>
<section class="card"><h2>Storage</h2><button onclick="get('/api/storage','storage')">Refresh</button><pre id="storage"></pre></section>
<section class="card"><h2>Logs</h2><button onclick="get('/api/logs?lines=100','logs')">Refresh</button><pre id="logs"></pre></section>
<section class="card"><h2>Containers</h2><button onclick="get('/api/podman/ps','containers')">Refresh</button><pre id="containers"></pre></section>
<section class="card"><h2>Diagnostics</h2><button onclick="get('/api/diagnostics','diagnostics')">Run</button><pre id="diagnostics"></pre></section>
<section class="card"><h2>Power</h2><button class="danger" onclick="power('reboot')">Reboot</button><button class="danger" onclick="power('poweroff')">Power off</button><pre id="power"></pre></section>
</div></main>
<script>
const token=document.getElementById('token'); token.value=localStorage.getItem('chimeraToken')||'';
function save(){localStorage.setItem('chimeraToken',token.value)}
function hdr(){return {'Authorization':'Bearer '+(token.value||localStorage.getItem('chimeraToken')||'')}}
async function get(u,id){try{let r=await fetch(u,{headers:hdr()});let j=await r.json();document.getElementById(id).textContent=JSON.stringify(j,null,2);document.getElementById('state').textContent=r.ok?'connected':'error'}catch(e){document.getElementById(id).textContent=String(e)}}
async function post(u,b,id){let r=await fetch(u,{method:'POST',headers:{...hdr(),'Content-Type':'application/json'},body:JSON.stringify(b)});let j=await r.json();document.getElementById(id).textContent=JSON.stringify(j,null,2)}
function service(action){post('/api/service',{action,service:document.getElementById('svc').value},'services')}
function power(action){if(confirm('Confirm '+action+'?'))post('/api/power',{action},'power')}
function refresh(){get('/api/overview','overview');get('/api/services','services');get('/api/users','users');get('/api/network','network');get('/api/storage','storage');get('/api/logs?lines=100','logs');get('/api/podman/ps','containers');}
refresh();
</script></body></html>"""

def read_token():
    try:
        return Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
    except OSError:
        return ""

def audit(action, result):
    try:
        p = Path(AUDIT_FILE)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"time": time.time(), "action": action, "result": result}, separators=(",", ":")) + "\n")
    except OSError:
        pass

def run(argv, timeout=15, stdin=None):
    try:
        r = subprocess.run(argv, text=True, input=stdin, capture_output=True, timeout=timeout)
        return {"ok": r.returncode == 0, "stdout": r.stdout[-20000:], "stderr": r.stderr[-10000:], "code": r.returncode}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e), "code": 124}

def command_exists(name):
    return subprocess.run(["sh", "-c", "command -v " + shlex.quote(name)], capture_output=True).returncode == 0

def service_action(action, service):
    allowed = {"start", "stop", "restart", "reload", "enable", "disable"}
    if action not in allowed or not service or not service.replace("-", "").replace("_", "").replace(".", "").isalnum():
        return {"ok": False, "error": "invalid service action/name"}
    return run(["systemctl", action, service], 30)

def podman(argv):
    if not command_exists("podman"):
        return {"ok": False, "error": "podman is not installed"}
    if argv == ["ps"]: argv += ["--all"]
    return run(["podman", *argv])

class Handler(BaseHTTPRequestHandler):
    server_version = "ChimeraWeb/2.0"

    def auth(self):
        expected = read_token()
        supplied = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        return bool(expected) and secrets.compare_digest(supplied, expected)

    def authorized(self):
        if not self.auth():
            self.json({"ok": False, "error": "unauthorized"}, 401)
            return False
        return True

    def json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n > MAX_BODY:
            raise ValueError("request too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.json({"ok": True, "service": "chimera-web", "version": 2})
        if path in ("/", "/index.html"):
            data = INDEX.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if not self.authorized(): return

        if path == "/api/overview":
            return self.json({
                "ok": True, "uid": os.getuid(), "euid": os.geteuid(),
                "hostname": run(["hostname"]).get("stdout", "").strip(),
                "kernel": run(["uname", "-a"]).get("stdout", "").strip(),
                "uptime": Path("/proc/uptime").read_text().split()[0] if Path("/proc/uptime").exists() else None,
                "loadavg": os.getloadavg(),
            })
        if path == "/api/services":
            return self.json(run(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain"]))
        if path == "/api/users":
            return self.json(run(["getent", "passwd"]))
        if path == "/api/network":
            return self.json({
                "interfaces": run(["ip", "-brief", "address"]) if command_exists("ip") else {"error":"ip unavailable"},
                "routes": run(["ip", "route"]) if command_exists("ip") else {"error":"ip unavailable"},
                "network_manager": run(["nmcli", "-t", "general", "status"]) if command_exists("nmcli") else {"error":"nmcli unavailable"},
            })
        if path == "/api/storage":
            return self.json({
                "block_devices": run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL"]),
                "filesystems": run(["df", "-PT"]),
            })
        if path == "/api/logs":
            q = parse_qs(urlparse(self.path).query); lines = min(max(int(q.get("lines", ["100"])[0]), 1), 500)
            return self.json(run(["journalctl", "-n", str(lines), "--no-pager", "-o", "short-iso"]))
        if path == "/api/diagnostics":
            return self.json({
                "hostname": run(["hostname"]),
                "kernel": run(["uname", "-a"]),
                "memory": run(["free", "-h"]) if command_exists("free") else {},
                "disk": run(["df", "-h"]),
                "failed_services": run(["systemctl", "--failed", "--no-pager"]),
            })
        if path == "/api/podman/ps": return self.json(podman(["ps"]))
        if path == "/api/podman/images": return self.json(podman(["images"]))
        if path == "/api/podman/pods": return self.json(podman(["pod", "ps", "--all"]))
        return self.json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        if not self.authorized(): return
        path = urlparse(self.path).path
        try: b = self.body()
        except Exception as e: return self.json({"ok": False, "error": str(e)}, 400)

        if path == "/api/service":
            result = service_action(b.get("action", ""), b.get("service", ""))
            audit("service:" + str(b.get("action")) + ":" + str(b.get("service")), result["ok"])
            return self.json(result, 200 if result["ok"] else 403)
        if path == "/api/power":
            action = b.get("action")
            if action not in {"reboot", "poweroff"}: return self.json({"ok":False,"error":"invalid power action"},400)
            result = run(["systemctl", action], 10)
            audit("power:"+action, result["ok"])
            return self.json(result, 200 if result["ok"] else 403)
        if path == "/api/podman/action":
            action, name = b.get("action"), b.get("name", "")
            if action not in {"start","stop","restart","pause","unpause"} or not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in name):
                return self.json({"ok":False,"error":"invalid container action/name"},400)
            result = podman([action, name]); audit("podman:"+action+":"+name, result["ok"])
            return self.json(result, 200 if result["ok"] else 403)
        return self.json({"ok":False,"error":"not found"},404)

def main():
    if not read_token():
        raise SystemExit("missing web token; refusing unauthenticated control server")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    if CERT_FILE and KEY_FILE:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(CERT_FILE, KEY_FILE)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"Chimera II web console listening on {'https' if CERT_FILE and KEY_FILE else 'http'}://{HOST}:{PORT}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Chimera II localhost runtime bridge.

Binds only to 127.0.0.1. It exposes a small, explicit command contract for the
static Aurora UI; it never accepts arbitrary shell commands.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, shutil, subprocess, time

HOST="127.0.0.1"
PORT=int(os.environ.get("CHIMERA_BRIDGE_PORT","8765"))
ROOT=Path(__file__).resolve().parents[2]
PS_LAUNCHER=ROOT/"tools/emulation/playstation-launcher.sh"
PS_MANIFEST=ROOT/"web/playstation_emulators.json"
GAME_MANIFEST=ROOT/"web/game-center-manifest.json"

def send(h, code, obj):
    raw=json.dumps(obj).encode()
    h.send_response(code); h.send_header("Content-Type","application/json")
    h.send_header("Access-Control-Allow-Origin","*")
    h.send_header("Cache-Control","no-store"); h.end_headers(); h.wfile.write(raw)

def body(h):
    n=int(h.headers.get("Content-Length","0") or 0)
    if n>2_000_000: raise ValueError("request too large")
    return json.loads(h.rfile.read(n) or b"{}")

def exe(candidates):
    for c in candidates:
        p=shutil.which(c)
        if p: return p
    return None

def ps_items():
    return [e for g in json.loads(PS_MANIFEST.read_text())["generations"] for e in g["emulators"]]

def ps_item(eid):
    return next((x for x in ps_items() if x["id"]==eid),None)

def game_item(gid):
    if not GAME_MANIFEST.exists(): return None
    d=json.loads(GAME_MANIFEST.read_text())
    return next((x for x in d.get("games",[]) if x[0]==gid),None)

def safe_path(value):
    p=Path(os.path.expanduser(str(value or ""))).resolve()
    if not str(p): raise ValueError("path required")
    return p

class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()
    def do_GET(self):
        if self.path=="/health":
            return send(self,200,{"status":"online","version":"chimera-local-bridge-1","scope":"localhost"})
        send(self,404,{"error":"not-found"})
    def do_POST(self):
        try:
            d=body(self); path=self.path
            if path=="/emulators/status":
                e=ps_item(d.get("id",""))
                if not e:return send(self,404,{"error":"unknown-emulator"})
                installed=bool(exe(e.get("executable_candidates",[])))
                return send(self,200,{"id":e["id"],"installed":installed,"title":e["title"]})
            if path=="/launch/emulator":
                e=ps_item(d.get("id","")); media=d.get("media")
                if not e:return send(self,404,{"error":"unknown-emulator"})
                if not PS_LAUNCHER.exists():return send(self,503,{"error":"playstation-launcher-missing"})
                if not media:return send(self,400,{"error":"media-required"})
                p=safe_path(media)
                if not p.exists():return send(self,404,{"error":"media-not-found"})
                r=subprocess.run([str(PS_LAUNCHER),"run",e["id"],str(p)],capture_output=True,text=True,timeout=10)
                if r.returncode:return send(self,409,{"error":r.stderr.strip() or "emulator-not-installed"})
                return send(self,200,{"status":"launch-requested","id":e["id"]})
            if path=="/launch/mame":
                machine=str(d.get("machine","")).strip()
                if not machine:return send(self,400,{"error":"machine-required"})
                mame=exe(["mame","mame64","mame-x64"])
                if not mame:return send(self,503,{"error":"mame-not-installed"})
                allowed_video={"auto","bgfx","opengl","soft","sdl"}
                video=d.get("video","auto") if d.get("video","auto") in allowed_video else "auto"
                args=[mame,machine,"-video",video]
                rompath=str(d.get("rompath","roms")).strip()
                if rompath:args += ["-rompath",rompath]
                if d.get("window")=="fullscreen":args.append("-maximize")
                subprocess.Popen(args,start_new_session=True)
                return send(self,200,{"status":"launched","command":args})
            if path=="/launch/amiga":
                content=str(d.get("content","")).strip()
                if not content:return send(self,400,{"error":"content-required"})
                p=safe_path(content)
                if not p.exists():return send(self,404,{"error":"content-not-found"})
                a=exe(["fs-uae","fs-uae-launcher","uae","amiga"])
                if not a:return send(self,503,{"error":"amiga-core-not-installed"})
                subprocess.Popen([a,str(p)],start_new_session=True)
                return send(self,200,{"status":"launched","executable":a})
            if path=="/games/launch":
                g=game_item(d.get("id",""))
                if not g:return send(self,404,{"error":"unknown-game"})
                if len(g)>4 and g[4]=="browser":return send(self,400,{"error":"browser-game-use-browser-runtime"})
                return send(self,503,{"error":"native-game-runtime-not-registered","id":g[0],"hint":"Build/install the local game through tools/game-center."})
            if path.startswith("/mame/"):
                action=path[len("/mame/"):]
                if action not in {"state/save","state/load","record","snapshot","debug","media/mount","media/eject"}:
                    return send(self,404,{"error":"unsupported-mame-action"})
                # These actions are accepted only as structured requests; native MAME
                # integrations may implement them without exposing arbitrary commands.
                return send(self,200,{"status":"accepted","action":action,"machine":d.get("machine",""),"timestamp":time.time()})
            send(self,404,{"error":"not-found"})
        except (ValueError, OSError, subprocess.SubprocessError) as e:
            send(self,400,{"error":str(e)})
        except Exception as e:
            send(self,500,{"error":str(e)})

if __name__=="__main__":
    print(f"Chimera II local runtime bridge: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()

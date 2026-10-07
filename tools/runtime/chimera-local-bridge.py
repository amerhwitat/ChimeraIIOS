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
            if path=="/python/build-all":
                allowed={"BizXtreme","amerhwitat.github.io","keygen","PDFreaderPY","bruteforce","general","CPU4096","test","VanG","CPU4096Simulator","eth-key-check","BizX","ChimeraIIOS","nlp"}
                workspace=Path(os.environ.get("CHIMERA_PYTHON_WORKSPACE",str(ROOT.parent))).resolve()
                results=[]; total=0; failed=0
                for repo in sorted(allowed):
                    base=(workspace/repo).resolve()
                    if not base.exists(): results.append({"repo":repo,"status":"workspace-missing"}); continue
                    for script in base.rglob("*.py"):
                        total+=1
                        try:
                            p=subprocess.run(["python3","-m","py_compile",str(script)],cwd=str(base),capture_output=True,text=True,timeout=20)
                            if p.returncode: failed+=1; results.append({"repo":repo,"path":str(script.relative_to(base)),"status":"failed","stderr":p.stderr[-2000:]})
                        except Exception as e:
                            failed+=1; results.append({"repo":repo,"path":str(script.relative_to(base)),"status":"error","error":str(e)})
                return send(self,200 if failed==0 else 409,{"status":"pass" if failed==0 else "completed-with-errors","total":total,"failed":failed,"failures":results[:200]})
            if path=="/python/run":
                repo=str(d.get("repo","")).strip()
                rel=str(d.get("path","")).strip()
                allowed={"BizXtreme","amerhwitat.github.io","keygen","PDFreaderPY","bruteforce","general","CPU4096","test","VanG","CPU4096Simulator","eth-key-check","BizX","ChimeraIIOS","nlp"}
                if repo not in allowed:return send(self,403,{"error":"repository-not-allowlisted"})
                if not rel or rel.startswith("/") or ".." in Path(rel).parts or not rel.lower().endswith(".py"):
                    return send(self,400,{"error":"invalid-python-path"})
                workspace=Path(os.environ.get("CHIMERA_PYTHON_WORKSPACE",str(ROOT.parent))).resolve()
                script=(workspace/repo/rel).resolve()
                try:script.relative_to((workspace/repo).resolve())
                except ValueError:return send(self,403,{"error":"path-outside-repository"})
                if not script.exists():return send(self,404,{"error":"python-file-not-found"})
                # Only catalogued entry-point paths should be executed by the UI.
                base=script.name.lower()
                runnable=base in {"app.py","main.py","server.py","cli.py","run.py","launcher.py"} or base=="__main__.py"
                if not runnable:return send(self,400,{"error":"python-file-is-not-a-runnable-entrypoint"})
                p=subprocess.run(["python3",str(script)],cwd=str(script.parent),capture_output=True,text=True,timeout=20,env={**os.environ,"PYTHONUNBUFFERED":"1"})
                return send(self,200 if p.returncode==0 else 409,{"status":"completed" if p.returncode==0 else "failed","repo":repo,"path":rel,"returncode":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]})
            if path=="/iso/info" or path=="/iso/verify":
                iso=safe_path(d.get("iso"))
                if not iso.is_file(): return send(self,404,{"error":"iso-not-found"})
                tool=ROOT/"iso-tool.sh"
                if not tool.exists(): return send(self,503,{"error":"iso-tool-missing"})
                op="info" if path=="/iso/info" else "verify"
                p=subprocess.run([str(tool),op,str(iso)],capture_output=True,text=True,timeout=60,cwd=str(ROOT))
                return send(self,200 if p.returncode==0 else 409,{"status":"completed" if p.returncode==0 else "failed","operation":op,"iso":str(iso),"returncode":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]})
            if path=="/flash/detect":
                tool=ROOT/"desktop/aurora/aurora_flash_tool.py"
                if not tool.exists(): return send(self,503,{"error":"flash-tool-missing"})
                p=subprocess.run(["python3",str(tool),"--list"],capture_output=True,text=True,timeout=20,cwd=str(ROOT))
                return send(self,200 if p.returncode==0 else 409,{"status":"completed" if p.returncode==0 else "failed","returncode":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]})
            if path=="/flash/verify-image":
                image=safe_path(d.get("image")); expected=str(d.get("sha256","")).strip().lower()
                if not image.is_file(): return send(self,404,{"error":"image-not-found"})
                import hashlib
                h=hashlib.sha256()
                with image.open("rb") as f:
                    for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
                actual=h.hexdigest()
                return send(self,200,{"status":"match" if expected and actual==expected else "computed","image":str(image),"sha256":actual,"matches":bool(expected and actual==expected)})
            if path=="/flash/execute":
                image=safe_path(d.get("image")); device=str(d.get("device","")).strip()
                expected=str(d.get("sha256","")).strip()
                if not image.is_file(): return send(self,404,{"error":"image-not-found"})
                if not device.startswith("/dev/"): return send(self,400,{"error":"device-must-be-/dev-path"})
                tool=ROOT/"desktop/aurora/aurora_flash_tool.py"
                if not tool.exists(): return send(self,503,{"error":"flash-tool-missing"})
                if os.environ.get("CHIMERA_FLASH_CONFIRM")!="YES": return send(self,409,{"error":"flash-confirmation-required","hint":"Set CHIMERA_FLASH_CONFIRM=YES only after verifying the removable target."})
                args=["python3",str(tool),"--image",str(image),"--device",device]
                if expected: args += ["--sha256",expected]
                p=subprocess.run(args,capture_output=True,text=True,timeout=1800,cwd=str(ROOT))
                return send(self,200 if p.returncode==0 else 409,{"status":"completed" if p.returncode==0 else "failed","returncode":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]})
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

#!/usr/bin/env python3
"""Aurora/N-bit profile daemon. Persists policy; Koronos validates at process admission."""
import argparse, importlib.util, json, os, socket, socketserver, stat, sys
from pathlib import Path
def load_selector():
    here=Path(__file__).resolve()
    candidates=[here.parents[2]/"tools/nbit/select_mode.py",
                Path("/usr/share/chimera/nbit/select_mode.py"),
                Path("/usr/lib/chimera/tools/select_mode.py")]
    path=next((x for x in candidates if x.is_file()),None)
    if path is None: raise RuntimeError("N-bit selector implementation is not installed")
    spec=importlib.util.spec_from_file_location("chimera_nbit_selector",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
class Daemon:
    def __init__(self,config,selector): self.config=config; self.selector=selector
    def handle(self,request):
        if not isinstance(request,dict): return {"ok":False,"error":"request must be a JSON object"}
        op=request.get("op")
        if op=="get":
            if self.config.exists():
                try: return {"ok":True,"profile":json.loads(self.config.read_text(encoding="utf-8"))}
                except Exception: return {"ok":False,"error":"stored profile is invalid JSON"}
            return {"ok":True,"profile":self.selector.build_profile(64,"auto",None,"auto")}
        if op=="set":
            try:
                profile=self.selector.build_profile(int(request.get("bits",64)),
                    str(request.get("backend","auto")),request.get("compatibility"),
                    str(request.get("isa","auto")))
            except (TypeError,ValueError) as exc: return {"ok":False,"error":str(exc)}
            self.config.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.config.with_suffix(self.config.suffix+".tmp")
            tmp.write_text(json.dumps(profile,indent=2)+"\n",encoding="utf-8")
            os.chmod(tmp,0o600); tmp.replace(self.config)
            return {"ok":True,"profile":profile,"kernel_validation_required":True}
        return {"ok":False,"error":"supported operations are get and set"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--socket",type=Path,default=Path(os.environ.get("CHIMERA_NBIT_SOCKET","/run/chimera/nbitd.sock")))
    p.add_argument("--config",type=Path,default=Path(os.environ.get("CHIMERA_NBIT_PROFILE_FILE","/etc/chimera/nbit-mode.json")))
    a=p.parse_args()
    if not hasattr(socket,"AF_UNIX"): print("Unix sockets unavailable",file=sys.stderr); return 2
    try: selector=load_selector()
    except Exception as exc: print(str(exc),file=sys.stderr); return 2
    daemon=Daemon(a.config,selector)
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            raw=self.rfile.readline(1024*1024)
            try: request=json.loads(raw.decode("utf-8"))
            except Exception: response={"ok":False,"error":"invalid JSON request"}
            else: response=daemon.handle(request)
            self.wfile.write((json.dumps(response,separators=(",",":"))+"\n").encode("utf-8")); self.wfile.flush()
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads=True
        allow_reuse_address=True
    a.socket.parent.mkdir(parents=True,exist_ok=True)
    if a.socket.exists():
        if not stat.S_ISSOCK(a.socket.stat().st_mode):
            print("refusing to replace non-socket path",file=sys.stderr); return 2
        a.socket.unlink()
    with Server(str(a.socket),Handler) as server:
        os.chmod(a.socket,0o600)
        server.serve_forever()
    return 0
if __name__=="__main__": raise SystemExit(main())

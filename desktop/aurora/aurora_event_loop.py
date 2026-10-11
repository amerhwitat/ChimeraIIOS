#!/usr/bin/env python3
"""Aurora native/compatibility input event loop over newline-delimited JSON.

The compositor or compatibility adapter writes one event per line to stdin. The
dispatcher validates the event and invokes only allow-listed desktop actions.
"""
from __future__ import annotations
import argparse, json, os, socket, socketserver, stat, subprocess, sys, time
from pathlib import Path

ACTIONS={
 "select":"select","open":"open","rename":"rename","maximize":"maximize",
 "restore":"restore","minimize":"minimize","close":"close","context-menu":"context-menu",
 "select-all":"select-all","properties":"properties","copy":"copy","cut":"cut","paste":"paste",
 "delete":"delete","new-window":"new-window","refresh":"refresh"
}
SURFACES={"file","folder","desktop","window-titlebar","text","panel","empty-space"}
def resolve(event):
    surface=event.get("surface","file")
    kind=event.get("kind","pointer")
    button=event.get("button","left")
    clicks=int(event.get("click_count",1))
    key=event.get("key","")
    if surface not in SURFACES or kind not in ("pointer","keyboard","touch","compatibility"):
        raise ValueError("unsupported event kind or surface")
    if kind=="keyboard":
        mapping={"F2":"rename","Enter":"open","Delete":"delete","Escape":"close",
                 "ContextMenu":"context-menu","Shift+F10":"context-menu",
                 "Ctrl+A":"select-all","Ctrl+C":"copy","Ctrl+X":"cut","Ctrl+V":"paste",
                 "Alt+F4":"close","Meta+Up":"maximize","Meta+Down":"minimize"}
        return mapping.get(key,"")
    if button=="right" or kind=="touch" and event.get("gesture")=="long-press":
        return "context-menu"
    if clicks==1:
        return "select" if surface in ("file","folder","desktop","text") else "focus"
    if clicks==2:
        if surface=="window-titlebar": return "restore" if event.get("maximized") else "maximize"
        if surface in ("file","folder","desktop"): return "open"
        if surface=="panel": return "maximize"
        return "select-all" if surface=="text" else "open"
    if clicks==3:
        return "select-all" if surface=="text" else ("maximize" if surface=="window-titlebar" else "select")
    return ""
def dispatch_line(raw):
    try:
        event=json.loads(raw)
        action=resolve(event)
        if not action: return {"event":"ignored"}
        if action not in ACTIONS.values() and action!="focus":
            raise ValueError("action not allow-listed")
        request={"action":action,"surface":event.get("surface","file"),
                 "target":str(event.get("target",""))[:4096],
                 "mode":"compatibility" if event.get("kind")=="compatibility" else "native",
                 "timestamp_ns":time.monotonic_ns()}
        if os.environ.get("CHIMERA_DESKTOP_DISPATCH")=="1":
            dispatcher=os.environ.get("CHIMERA_DESKTOP_ACTION","/usr/bin/chimera-desktop-action")
            if Path(dispatcher).is_file():
                subprocess.run([dispatcher,action,request["target"]],check=False,timeout=5)
        return {"event":"dispatch","request":request}
    except Exception as exc:
        return {"event":"rejected","error":str(exc)[:240]}

class EventSocketHandler(socketserver.StreamRequestHandler):
    def handle(self):
        for raw in self.rfile:
            if len(raw)>1024*1024:
                response={"event":"rejected","error":"event exceeds 1 MiB"}
            else:
                response=dispatch_line(raw.decode("utf-8","replace"))
            self.wfile.write((json.dumps(response,separators=(",",":"))+"\\n").encode("utf-8"))
            self.wfile.flush()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--socket",type=Path,help="serve newline-delimited JSON events over a local Unix socket")
    args=parser.parse_args()
    if args.socket:
        if not hasattr(socket,"AF_UNIX"):
            print("Unix event sockets are unavailable; use stdin compatibility mode",file=sys.stderr); return 2
        args.socket.parent.mkdir(parents=True,exist_ok=True)
        if args.socket.exists():
            if not stat.S_ISSOCK(args.socket.stat().st_mode):
                print("refusing to replace a non-socket event path",file=sys.stderr); return 2
            args.socket.unlink()
        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads=True
            allow_reuse_address=True
        with Server(str(args.socket),EventSocketHandler) as server:
            os.chmod(args.socket,0o600)
            server.serve_forever()
        return 0
    for raw in sys.stdin:
        response=dispatch_line(raw)
        if response.get("event")=="rejected":
            print(json.dumps(response),file=sys.stderr,flush=True)
        else:
            print(json.dumps(response,separators=(",",":")),flush=True)
    return 0
if __name__=="__main__": main()

#!/usr/bin/env python3
"""Aurora native/compatibility input event loop over newline-delimited JSON.

The compositor or compatibility adapter writes one event per line to stdin. The
dispatcher validates the event and invokes only allow-listed desktop actions.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
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
def main():
    dispatcher=os.environ.get("CHIMERA_DESKTOP_ACTION","/usr/bin/chimera-desktop-action")
    for raw in sys.stdin:
        try:
            event=json.loads(raw)
            action=resolve(event)
            if not action: continue
            if action not in ACTIONS.values() and action!="focus":
                raise ValueError("action not allow-listed")
            request={"action":action,"surface":event.get("surface","file"),
                     "target":str(event.get("target",""))[:4096],
                     "mode":"compatibility" if event.get("kind")=="compatibility" else "native",
                     "timestamp_ns":time.monotonic_ns()}
            print(json.dumps({"event":"dispatch","request":request},separators=(",",":")),flush=True)
            # Dry-run is the safe default. Enable only when the compositor/session
            # explicitly opts in; no shell is involved.
            if os.environ.get("CHIMERA_DESKTOP_DISPATCH")=="1" and Path(dispatcher).is_file():
                subprocess.run([dispatcher,action,request["target"]],check=False,timeout=5)
        except Exception as exc:
            print(json.dumps({"event":"rejected","error":str(exc)[:240]}),file=sys.stderr,flush=True)
if __name__=="__main__": main()

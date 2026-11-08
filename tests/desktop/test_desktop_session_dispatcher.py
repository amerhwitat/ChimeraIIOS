#!/usr/bin/env python3
from __future__ import annotations
import os
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HELPER=ROOT/"tools/display/chimera-xsession.py"
DISPATCHER=ROOT/"tools/display/chimera-desktop-session"

def run(args,env):
    return subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)

def main():
    with tempfile.TemporaryDirectory(prefix="chimera-desktop-session-") as tmp:
        root=Path(tmp)
        wayland=root/"wayland"; x11=root/"x11"; bindir=root/"bin"; runtime=root/"runtime"
        for p in (wayland,x11,bindir,runtime): p.mkdir()
        runtime.chmod(0o700)
        probe=root/"probe"
        probe.write_text("#!/bin/sh\nprintf '%s|%s|%s\\n' \"$1\" \"$DESKTOP_SESSION\" \"$XDG_SESSION_TYPE\"\n",encoding="utf-8")
        probe.chmod(0o755)
        (wayland/"test-wayland.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Wayland Test\n"
            f"Exec={probe} --probe\nTryExec={probe}\n",encoding="utf-8")
        (x11/"test-x11.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=X11 Test\n"
            f"Exec={probe} --probe\nTryExec={probe}\n",encoding="utf-8")
        stub_xserver=bindir/"chimera-xserver-session"
        stub_xserver.write_text("#!/bin/sh\nprintf 'xserver|%s|%s\\n' \"$1\" \"$2\"\n",encoding="utf-8")
        stub_xserver.chmod(0o755)
        env=os.environ.copy()
        env.update({
            "CHIMERA_WAYLAND_SESSION_DIRS":str(wayland),
            "CHIMERA_XSESSION_DIRS":str(x11),
            "CHIMERA_XSESSION_HELPER":str(HELPER),
            "CHIMERA_XSERVER_SESSION":str(stub_xserver),
            "XDG_RUNTIME_DIR":str(runtime),
            "PATH":str(bindir)+os.pathsep+env.get("PATH",""),
        })
        wayland_run=run([str(DISPATCHER),"start","test-wayland"],env)
        assert wayland_run.returncode==0,(wayland_run.returncode,wayland_run.stdout,wayland_run.stderr)
        assert "--probe|test-wayland|wayland" in wayland_run.stdout,wayland_run.stdout
        x11_run=run([str(DISPATCHER),"start","--backend","x11","test-x11"],env)
        assert x11_run.returncode==0,(x11_run.returncode,x11_run.stdout,x11_run.stderr)
        assert "xserver|start|test-x11" in x11_run.stdout,x11_run.stdout
        listing=run([str(DISPATCHER),"list"],env)
        assert listing.returncode==0,(listing.returncode,listing.stdout,listing.stderr)
        assert "test-wayland" in listing.stdout and "test-x11" in listing.stdout,listing.stdout
        missing=run([str(DISPATCHER),"start","missing"],env)
        assert missing.returncode==127,missing.returncode
        unsafe=run([str(DISPATCHER),"start","../escape"],env)
        assert unsafe.returncode==2,unsafe.returncode
        hidden=wayland/"hidden.desktop"
        hidden.write_text("[Desktop Entry]\nType=Application\nName=Hidden\nHidden=true\nExec=/bin/true\n",encoding="utf-8")
        hidden_run=run([str(HELPER),"--type","wayland","hidden"],env)
        assert hidden_run.returncode==126,hidden_run.returncode
    print("Desktop dispatcher: Wayland/X11 routing, XDG discovery, missing/unsafe/hidden profiles passed")

if __name__=="__main__":
    main()

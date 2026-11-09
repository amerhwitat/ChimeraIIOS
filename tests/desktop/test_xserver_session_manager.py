#!/usr/bin/env python3
from __future__ import annotations
import os, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HELPER=ROOT/"tools/display/chimera-xsession.py"

def main():
    with tempfile.TemporaryDirectory(prefix="chimera-xsession-test-") as tmp:
        root=Path(tmp); sessions=root/"xsessions"; sessions.mkdir()
        probe=root/"session-probe"
        probe.write_text("#!/bin/sh\nprintf '%s|%s|%s\\n' \"$1\" \"$DESKTOP_SESSION\" \"$XDG_SESSION_TYPE\"\n",encoding="utf-8")
        probe.chmod(0o755)
        (sessions/"test.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Test Session\n"
            f"Exec={probe} --probe %f\nTryExec={probe}\n",
            encoding="utf-8")
        env=os.environ.copy(); env["CHIMERA_XSESSION_DIRS"]=str(sessions)
        ok=subprocess.run([sys.executable,str(HELPER),"test"],env=env,text=True,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        assert ok.returncode==0,(ok.returncode,ok.stdout,ok.stderr)
        assert "--probe|test|x11" in ok.stdout,ok.stdout
        missing=subprocess.run([sys.executable,str(HELPER),"missing"],env=env,text=True,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        assert missing.returncode==127,missing.returncode
        unsafe=subprocess.run([sys.executable,str(HELPER),"../escape"],env=env,text=True,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        assert unsafe.returncode==2,unsafe.returncode
        (sessions/"hidden.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Hidden\nHidden=true\nExec=/bin/true\n",
            encoding="utf-8")
        hidden=subprocess.run([sys.executable,str(HELPER),"hidden"],env=env,text=True,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        assert hidden.returncode==126,hidden.returncode
    print("X.Org session dispatcher: installed Exec, field codes, missing, unsafe and hidden-session checks passed")

if __name__=="__main__": main()

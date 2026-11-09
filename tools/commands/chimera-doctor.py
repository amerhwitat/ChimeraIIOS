#!/usr/bin/env python3
"""Run non-destructive diagnostics against the current Chimera userspace."""
import json, shutil, subprocess
from pathlib import Path

def check(name, ok, detail):
    print(f"{'PASS' if ok else 'WARN'} {name}: {detail}")
    return bool(ok)

def main():
    warnings=0
    for name in ("bash","python3","systemctl","ip"):
        ok=shutil.which(name) is not None
        warnings += not check("command/"+name,ok,"available" if ok else "not installed")
    for path in ("/usr/share/chimera/catalogs/command-isa-coverage.json",
                 "/usr/share/chimera/catalogs/terminal-shell-provider-status.json"):
        ok=Path(path).is_file()
        warnings += not check("catalog/"+Path(path).name,ok,"present" if ok else "missing")
    interfaces=[p.name for p in Path("/sys/class/net").glob("*") if p.name!="lo"]
    warnings += not check("network",bool(interfaces),", ".join(interfaces) if interfaces else "no non-loopback interface")
    dri=list(Path("/dev/dri").glob("*")) if Path("/dev/dri").exists() else []
    warnings += not check("graphics-device",bool(dri),", ".join(p.name for p in dri) if dri else "no DRM device node")
    libs=""
    if shutil.which("ldconfig"):
        p=subprocess.run(["ldconfig","-p"],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        libs=p.stdout
    gl=all(x in libs for x in ("libGL.so.1","libEGL.so.1"))
    warnings += not check("opengl-userspace",gl,"GL/EGL loader entries found" if gl else "GL/EGL loader not fully visible")
    audio=any(shutil.which(x) for x in ("pw-play","aplay","paplay","ffplay"))
    warnings += not check("audio-tools",audio,"audio playback utility found" if audio else "no playback utility found")
    print(json.dumps({"status":"warnings" if warnings else "ok","warning_count":warnings,
                      "koronos_runtime":"not-certified-by-hosted-linux-diagnostics"},sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Cross-platform, confirmation-gated host service lifecycle adapter."""
from __future__ import annotations
import argparse
import ctypes
import json
import os
import platform
import re
import shutil
import subprocess
import sys

CONFIRM = "CHIMERA-HOST-SERVICE-CHANGE"
NAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,128}$")

class ServiceError(ValueError):
    pass

def host_family():
    name = platform.system().lower()
    if name == "darwin": return "macos"
    if name == "windows": return "windows"
    if name == "freebsd": return "freebsd"
    if name == "linux": return "linux"
    return name or "unknown"

def valid_name(name):
    if not NAME_RE.fullmatch(name or ""):
        raise ServiceError("invalid service name; only letters, digits, dot, underscore, @ and hyphen are allowed")
    return name

def is_admin():
    if os.name == "nt":
        try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception: return False
    return hasattr(os, "geteuid") and os.geteuid() == 0

def _which(name):
    path = shutil.which(name)
    if not path: raise ServiceError(f"required host command is unavailable: {name}")
    return path

def plan(action, name=None, domain="system"):
    family = host_family()
    if action not in {"list","status","start","stop","enable","disable"}:
        raise ServiceError(f"unsupported action: {action}")
    if action != "list": valid_name(name)
    if domain not in {"system","user"}: raise ServiceError("domain must be system or user")
    if family == "linux":
        if shutil.which("systemctl"):
            if action == "list": return [_which("systemctl"),"list-units","--type=service","--all","--no-pager"], False
            unit = name if name.endswith(".service") else name + ".service"
            op = {"status":"status","start":"start","stop":"stop","enable":"enable","disable":"disable"}[action]
            return [_which("systemctl"),op,unit], action in {"start","stop","enable","disable"}
        if shutil.which("rc-status") and shutil.which("rc-service"):
            if action == "list": return [_which("rc-status"),"-a"], False
            op = {"status":"status","start":"start","stop":"stop","enable":"start","disable":"stop"}[action]
            if action in {"enable","disable"}:
                if not shutil.which("rc-update"): raise ServiceError("rc-update is required to enable or disable OpenRC services")
                return [_which("rc-update"),"add" if action=="enable" else "del",name,"default"], True
            return [_which("rc-service"),name,op], action in {"start","stop"}
        raise ServiceError("no supported Linux service manager detected (systemd or OpenRC)")
    if family == "freebsd":
        if action == "list": return [_which("service"),"-e"], False
        if action == "enable": return [_which("sysrc"),f"{name}_enable=YES"], True
        if action == "disable": return [_which("sysrc"),f"{name}_enable=NO"], True
        return [_which("service"),name,action], action in {"start","stop"}
    if family == "windows":
        if action == "list": return [_which("sc.exe"),"query","state=","all"], False
        if action == "status": return [_which("sc.exe"),"query",name], False
        if action == "start": return [_which("sc.exe"),"start",name], True
        if action == "stop": return [_which("sc.exe"),"stop",name], True
        if action == "enable": return [_which("sc.exe"),"config",name,"start=","auto"], True
        return [_which("sc.exe"),"config",name,"start=","disabled"], True
    if family == "macos":
        scope = "system" if domain == "system" else f"gui/{os.getuid()}"
        target = f"{scope}/{name}"
        if action == "list": return [_which("launchctl"),"list"], False
        if action == "status": return [_which("launchctl"),"print",target], False
        if action == "start": return [_which("launchctl"),"kickstart","-k",target], True
        if action == "stop": return [_which("launchctl"),"kill","SIGTERM",target], True
        if action == "enable": return [_which("launchctl"),"enable",target], True
        return [_which("launchctl"),"disable",target], True
    raise ServiceError(f"unsupported host operating system: {family}")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("list","status","start","stop","enable","disable"))
    parser.add_argument("service",nargs="?")
    parser.add_argument("--domain",choices=("system","user"),default="system",help="launchd domain on macOS")
    parser.add_argument("--apply",action="store_true",help="execute the planned action")
    parser.add_argument("--confirm",help=f"required phrase for mutations: {CONFIRM}")
    args=parser.parse_args(argv)
    try:
        command,mutating=plan(args.action,args.service,args.domain)
    except (ServiceError,KeyError) as exc:
        print(f"chimera-host-services: {exc}",file=sys.stderr); return 2
    print(json.dumps({"host":host_family(),"action":args.action,"service":args.service,"argv":command,"mutating":mutating},indent=2))
    if not args.apply: return 3 if mutating else 0
    if mutating and args.confirm != CONFIRM:
        print("REFUSED: explicit confirmation phrase required: "+CONFIRM,file=sys.stderr); return 3
    if mutating and (host_family()=="windows" or args.domain=="system") and not is_admin():
        print("REFUSED: system service changes require administrator/root privileges",file=sys.stderr); return 3
    return subprocess.run(command,check=False).returncode

if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Chimera II OS adaptive installer/orchestrator.

Inventory-first, dry-run by default. It detects firmware, CPU, memory, disks,
network, GPUs, virtualization and existing OS/boot entries, then emits a
reviewable installation plan. Destructive disk operations require --apply and
explicit confirmation; no remote code is executed.
"""
from __future__ import annotations
import argparse, json, os, platform, shutil, subprocess, sys, uuid
from pathlib import Path
from datetime import datetime, timezone

EDITIONS = {
    "desktop": {"purpose":"Aurora Wayland Glass workstation", "arch":["x86_64","arm64"], "uefi":True},
    "server": {"purpose":"routing, services, storage and compute", "arch":["x86_64","arm64","riscv64"], "uefi":True},
    "mobile": {"purpose":"mobile hardware profile", "arch":["arm64"], "uefi":True},
    "edge": {"purpose":"edge/network/AI node", "arch":["x86_64","arm64","riscv64"], "uefi":True},
    "iot": {"purpose":"constrained embedded/IoT node", "arch":["arm64","riscv64"], "uefi":False},
    "cvel": {"purpose":"virtualized CVEL/experimental edition", "arch":["x86_64","arm64","riscv64"], "uefi":True},
}

def run(cmd):
    try:
        p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=4)
        return p.stdout.strip()
    except Exception:
        return ""

def inventory():
    sysname=platform.system().lower(); machine=platform.machine().lower()
    fw="unknown"
    if Path("/sys/firmware/efi").exists(): fw="uefi"
    elif sysname=="windows": fw="uefi_or_bios"
    else: fw="bios_or_unknown"
    mem=None
    if Path("/proc/meminfo").exists():
        for line in Path("/proc/meminfo").read_text(errors="ignore").splitlines():
            if line.startswith("MemTotal:"): mem=int(line.split()[1])*1024; break
    disks=[]
    if sysname=="linux":
        ls=run(["lsblk","-J","-o","NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL"]) or "{}"
        try: disks=json.loads(ls).get("blockdevices",[])
        except Exception: disks=[]
    elif sysname=="windows":
        ps=shutil.which("powershell") or shutil.which("pwsh")
        if ps:
            raw=run([ps,"-NoProfile","-Command","Get-CimInstance Win32_DiskDrive | Select DeviceID,Model,Size,InterfaceType | ConvertTo-Json -Compress"])
            try: disks=json.loads(raw) if raw else []
            except Exception: disks=[]
    return {
        "schema":"CHIMERA-INSTALL-INVENTORY-1",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "host_id":str(uuid.uuid4()), "os":sysname, "kernel":platform.release(),
        "architecture":machine, "firmware":fw, "cpu":platform.processor(),
        "cpu_count":os.cpu_count(), "memory_bytes":mem, "disks":disks,
        "virtualization":run(["systemd-detect-virt"]) if shutil.which("systemd-detect-virt") else "unknown",
        "network_tools":{x:bool(shutil.which(x)) for x in ["ip","nmcli","iw","rfkill","networkctl"]},
        "secure_boot":run(["mokutil","--sb-state"]) if shutil.which("mokutil") else "unknown",
        "existing_os_evidence":{
            "windows":bool(Path("/Windows").exists() or Path("/mnt/c/Windows").exists()),
            "linux":bool(Path("/etc/os-release").exists()),
            "macos":sysname=="darwin"
        }
    }

def recommend(inv):
    a=inv["architecture"]
    if a in ("aarch64","arm64"):
        arch="arm64"
    elif "riscv" in a:
        arch="riscv64"
    else:
        arch="x86_64"
    ram=inv.get("memory_bytes") or 0
    if ram and ram < 2*1024**3: edition="iot"
    elif ram and ram < 4*1024**3: edition="edge"
    else: edition="desktop"
    if inv["virtualization"] not in ("unknown","none",""): edition="cvel"
    compatible=[k for k,v in EDITIONS.items() if arch in v["arch"]]
    if edition not in compatible: edition=compatible[0] if compatible else "server"
    return {"recommended_edition":edition,"target_arch":arch,"compatible_editions":compatible,
            "reason":"Hardware/firmware inventory heuristic; user selection remains authoritative."}

def plan(inv, choice):
    rec=recommend(inv)
    edition=choice or rec["recommended_edition"]
    if edition not in EDITIONS: raise SystemExit(f"Unknown edition: {edition}")
    if rec["target_arch"] not in EDITIONS[edition]["arch"]: raise SystemExit("Selected edition is not compatible with detected architecture")
    return {"schema":"CHIMERA-INSTALL-PLAN-1","inventory":inv,"selection":{
        "edition":edition,"architecture":rec["target_arch"],"mode":"preserve-existing-os",
        "boot":"UEFI-first; legacy fallback only when explicitly supported",
        "disk_policy":"never auto-partition or erase in unattended mode",
        "secure_boot_policy":"detect and report; signing/enrollment is an explicit step"},
        "recommendation":rec}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--edition",choices=EDITIONS); ap.add_argument("--output",default="chimera-install-plan.json"); ap.add_argument("--apply",action="store_true"); ap.add_argument("--confirm-destructive",action="store_true")
    args=ap.parse_args(); inv=inventory(); p=plan(inv,args.edition)
    if args.apply and not args.confirm_destructive:
        raise SystemExit("--apply requires --confirm-destructive; this installer never silently erases disks")
    if args.apply:
        p["selection"]["mode"]="apply-requested"; p["selection"]["note"]="Disk/boot mutation must be implemented by a platform-specific, signed installer backend."
    Path(args.output).write_text(json.dumps(p,indent=2),encoding="utf-8")
    print(json.dumps(p,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())

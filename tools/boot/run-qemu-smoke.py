#!/usr/bin/env python3
"""Capture and verify a bounded BIOS/QEMU smoke boot of the Chimera ISO.

The test is intentionally narrow: it does not claim six-case production
acceptance. Logs and evidence are retained even when boot markers are absent.
"""
from __future__ import annotations
import argparse, hashlib, json, socket, subprocess, sys, time
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def read(path: Path) -> str:
    try: return path.read_text(encoding="utf-8",errors="replace")
    except OSError: return ""

def monitor_command(path: Path, command: bytes, log: Path) -> bool:
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
            s.settimeout(2); s.connect(str(path))
            greeting=s.recv(8192)
            s.sendall(command+b"\n")
            time.sleep(.25)
            try: response=s.recv(8192)
            except (TimeoutError,OSError): response=b""
            with log.open("ab") as f: f.write(greeting+response+b"\n")
        return True
    except (FileNotFoundError,ConnectionRefusedError,TimeoutError,OSError):
        return False

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--iso",type=Path,required=True)
    ap.add_argument("--timeout",type=int,default=60)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    iso=a.iso.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    serial=out/"bios-serial.log"; debug=out/"bios-debugcon.log"
    qlog=out/"qemu-debug.log"; monlog=out/"qemu-monitor.log"
    mon=out/"qemu-monitor.sock"; evidence=out/"qemu-smoke-evidence.json"
    for p in (serial,debug,qlog,monlog):
        p.unlink(missing_ok=True)
    sums=Path(str(iso)+".sha256")
    if not iso.is_file() or not sums.is_file():
        print("QEMU smoke: ISO or checksum sidecar missing",file=sys.stderr); return 2
    fields=sums.read_text(encoding="ascii").strip().split()
    expected=fields[0] if fields else ""; actual=sha256(iso)
    if expected!=actual:
        print("QEMU smoke: checksum sidecar mismatch",file=sys.stderr); return 2
    cmd=["qemu-system-x86_64","-machine","q35,accel=tcg","-cpu","qemu64",
         "-m","2048","-smp","2","-cdrom",str(iso),"-boot","order=d,menu=on",
         "-display","none","-serial",f"file:{serial}","-debugcon",f"file:{debug}",
         "-global","isa-debugcon.iobase=0xe9","-monitor",f"unix:{mon},server,nowait",
         "-no-reboot","-no-shutdown","-d","guest_errors,int","-D",str(qlog)]
    proc=None; enter=False; menu_seen=False
    deadline=time.monotonic()+max(10,a.timeout)
    try:
        proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(80):
            if proc.poll() is not None: break
            if monitor_command(mon,b"info status",monlog): break
            time.sleep(.1)
        # GRUB timeout is intentionally long; send Enter to select default Live.
        enter=monitor_command(mon,b"sendkey ret",monlog)
        while time.monotonic()<deadline and proc.poll() is None:
            stext=read(serial); dtext=read(debug)
            merged=stext+"\n"+dtext
            if "KORONOS READY" in merged or "KORONOS" in merged: menu_seen=True
            if "[KRN ] KORONOS READY" in merged and ("[PMT ]" in merged or "SELFTEST" in merged): break
            time.sleep(.25)
    except FileNotFoundError:
        print("QEMU smoke: qemu-system-x86_64 unavailable",file=sys.stderr); return 2
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
    st=read(serial); dt=read(debug); qd=read(qlog); md=read(monlog)
    merged=st+"\n"+dt
    markers={
      "monitor_connected_and_enter_sent":enter,
      "kernel_ready":"[KRN ] KORONOS READY" in merged,
      "preemptive_kernel_task_selftest":("[PMT ] Native x86_64 context-save/timer-preemption gate passed" in merged or "[PMT ] SELFTEST PASS" in merged),
      "smp_selftest_pass":"[SMP ] Native x86_64 AP startup/two-CPU overlap gate passed" in merged,
      "native_stack_selftest_pass":"[NST ] Native block/VFS/PID1 gate passed" in merged,
      "installer_recovery_selftest_pass":"[INS ] Native installer/installed-root/recovery gate passed" in merged,
      "live_userspace_ready":"USERSPACE READY: target=live" in merged,
      "grub_or_kernel_output_seen":bool(st or dt or menu_seen),
    }
    ev={"schema":"CHIMERA-QEMU-SMOKE-2","scope":"BIOS QEMU default Live entry; markers read from both COM1 and debugcon",
        "production_acceptance":False,"iso_sha256":actual,"qemu_command":cmd,
        "timeout_seconds":a.timeout,"markers":markers,
        "logs":{p.name:sha256(p) if p.exists() else None for p in (serial,debug,qlog,monlog)},
        "log_sizes":{p.name:p.stat().st_size if p.exists() else 0 for p in (serial,debug,qlog,monlog)}}
    evidence.write_text(json.dumps(ev,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(ev,indent=2))
    return 0 if markers["kernel_ready"] and markers["preemptive_kernel_task_selftest"] else 1

if __name__=="__main__": raise SystemExit(main())

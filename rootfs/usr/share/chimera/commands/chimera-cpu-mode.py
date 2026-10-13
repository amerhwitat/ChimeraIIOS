#!/usr/bin/env python3
"""CPU profile selector for DOS guests and QEMU virtual machines.

The selector never changes the live host CPU mode. x86 real/protected mode is
architectural state controlled by firmware/kernel transitions. For DOS software,
the profile controls DOSBox-X DPMI availability; the program itself chooses whether
to enter protected mode. QEMU vCPU count controls guest CPUs, not bare-metal SMP.
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MODES = ("real", "protected")

def host_cpus() -> list[int]:
    try:
        return sorted(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return list(range(os.cpu_count() or 1))

def dosbox_config(mode: str, writable: bool) -> str:
    dpmi = "false" if mode == "real" else "true"
    return f"""[dos]\ndpmi={dpmi}\n\n[cpu]\ncore=auto\ncputype=auto\n\n[autoexec]\n"""
    
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=MODES, default="real", help="DOS execution profile: real mode (DPMI disabled) or protected-capable (DPMI enabled)")
    p.add_argument("--program", help="DOS .COM/.EXE/.BAT path to launch")
    p.add_argument("--args", nargs=argparse.REMAINDER, default=[], help="arguments passed to the DOS program after --args")
    p.add_argument("--vcpus", default="all", help="QEMU guest CPU count for --qemu-iso: all or a positive integer")
    p.add_argument("--qemu-iso", help="boot an ISO in QEMU with the requested guest vCPU count")
    p.add_argument("--host-affinity", action="store_true", help="restrict QEMU to all CPUs available to this process")
    p.add_argument("--list-cpus", action="store_true", help="list CPUs available to this process")
    p.add_argument("--writable", action="store_true", help="allow writes to the DOS program directory (otherwise mounted read-only)")
    args = p.parse_args(argv)
    cpus = host_cpus()
    if args.list_cpus:
        print("available_host_cpus=" + ",".join(map(str, cpus)))
        print("available_host_cpu_count=" + str(len(cpus)))
        return 0
    if args.qemu_iso:
        qemu = shutil.which("qemu-system-x86_64")
        if not qemu:
            print("chimera-cpu-mode: qemu-system-x86_64 is not installed", file=sys.stderr)
            return 127
        try:
            count = len(cpus) if args.vcpus == "all" else int(args.vcpus)
            if count < 1 or count > len(cpus):
                raise ValueError
        except ValueError:
            print(f"chimera-cpu-mode: --vcpus must be 'all' or 1..{len(cpus)}", file=sys.stderr)
            return 2
        cmd = [qemu, "-machine", "q35", "-cpu", "host", "-smp", str(count), "-m", "2048", "-cdrom", str(Path(args.qemu_iso).resolve()), "-boot", "d"]
        if args.host_affinity and shutil.which("taskset"):
            cmd = [shutil.which("taskset"), "-c", ",".join(map(str, cpus)), *cmd]
        return subprocess.run(cmd, check=False).returncode
    if not args.program:
        print("chimera-cpu-mode: specify --program DOSFILE or --qemu-iso ISO", file=sys.stderr)
        return 2
    program = Path(args.program).expanduser().resolve()
    if not program.is_file() or program.suffix.lower() not in (".com", ".exe", ".bat"):
        print("chimera-cpu-mode: program must be an existing DOS .COM, .EXE, or .BAT file", file=sys.stderr)
        return 2
    emulator = shutil.which("dosbox-x") or shutil.which("dosbox")
    if not emulator:
        print("chimera-cpu-mode: install DOSBox-X or DOSBox", file=sys.stderr)
        return 127
    if args.mode == "protected" and Path(emulator).name != "dosbox-x":
        print("chimera-cpu-mode: protected-capable profile requires DOSBox-X for the requested DPMI setting", file=sys.stderr)
        return 127
    writable = args.writable or os.environ.get("CHIMERA_DOS_WRITABLE") == "1"
    cfg = dosbox_config(args.mode, writable)
    with tempfile.TemporaryDirectory(prefix="chimera-dos-profile-") as td:
        conf = Path(td) / "profile.conf"
        conf.write_text(cfg, encoding="utf-8")
        mount_flag = "" if writable else " -ro"
        mount = f'mount c "{program.parent}"{mount_flag}'
        cmd = [emulator, "-conf", str(conf), "-c", mount, "-c", "c:", "-c", '"'+program.name+'"'+(" "+" ".join('"'+x+'"' if any(ch.isspace() for ch in x) else x for x in args.args) if args.args else ""), "-c", "exit"]
        return subprocess.run(cmd, check=False).returncode

if __name__ == "__main__":
    raise SystemExit(main())

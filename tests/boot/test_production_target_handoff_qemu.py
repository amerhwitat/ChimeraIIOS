#!/usr/bin/env python3
"""Boot each real production GRUB target from the same immutable ISO.

Unlike the candidate ELF probe, this test does not generate a replacement GRUB
configuration or repackage a test ISO. It selects the entries from the ISO's
own /boot/grub/grub.cfg and verifies the resulting debugcon trace.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

TARGETS = {
    "live": ("aurora-live", 0),
    "installer": ("install", 0),
    "recovery": ("recovery", 1),  # main recovery submenu, then its default first entry
}
VERIFY = Path(__file__).with_name("verify-userspace-handoff.py")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)


def extract(iso: Path, member: str, dest: Path) -> None:
    result = run("xorriso", "-osirrox", "on", "-indev", str(iso),
                 "-extract", member, str(dest), check=False)
    if result.returncode or not dest.is_file() or dest.stat().st_size == 0:
        raise RuntimeError(f"ISO is missing required production member {member}: {result.stdout}")


def menu_index(config: str, wanted_id: str) -> int:
    entries = re.findall(r"^\s*menuentry\b[^\n]*", config, flags=re.MULTILINE)
    for index, entry in enumerate(entries):
        match = re.search(r"--id\s+([^\s{]+)", entry)
        if match and match.group(1) == wanted_id:
            return index
    raise RuntimeError(f"production GRUB menu has no entry id {wanted_id!r}")


def monitor_send(path: Path, command: str) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(str(path))
                sock.sendall((command + "\n").encode("ascii"))
            return
        except (FileNotFoundError, ConnectionRefusedError):
            time.sleep(0.1)
    raise RuntimeError(f"QEMU monitor did not become available: {path}")


def boot_target(iso: Path, out: Path, target: str, index: int, nested_enter: int) -> int:
    trace = out / f"{target}-production-debugcon.log"
    monitor = out / f"{target}-monitor.sock"
    qemu_log = out / f"{target}-qemu.log"
    for stale in (trace, monitor, qemu_log):
        stale.unlink(missing_ok=True)
    command = [
        "qemu-system-x86_64", "-machine", "q35", "-m", "1024", "-smp", "1",
        "-accel", "tcg", "-display", "none", "-serial", "none",
        "-monitor", f"unix:{monitor},server,nowait", "-no-reboot", "-no-shutdown",
        "-boot", "d", "-cdrom", str(iso), "-debugcon", f"file:{trace}",
        "-global", "isa-debugcon.iobase=0xe9",
    ]
    with qemu_log.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            # Allow firmware and the production GRUB menu to initialize.
            time.sleep(5)
            for _ in range(index):
                monitor_send(monitor, "sendkey down")
                time.sleep(0.15)
            monitor_send(monitor, "sendkey ret")
            if nested_enter:
                time.sleep(2.5)
                monitor_send(monitor, "sendkey ret")
            deadline = time.monotonic() + 22
            while time.monotonic() < deadline:
                data = trace.read_text(encoding="latin1", errors="replace") if trace.exists() else ""
                if (f"USER INIT SYSCALL: target={target} init_pid=" in data and
                        f"USERSPACE READY: target={target} init_pid=" in data):
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
    if not trace.is_file() or trace.stat().st_size == 0:
        print(f"FAIL {target}: production QEMU boot emitted no debugcon trace")
        return 1
    data = trace.read_text(encoding="latin1", errors="replace")
    required_module = f"chimera-user-init-elf target={target}"
    if required_module not in data:
        print(f"FAIL {target}: production GRUB did not pass {required_module!r} to Koronos")
        print(data[-2500:])
        return 1
    result = subprocess.run([sys.executable, str(VERIFY), target, str(trace)], text=True)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    iso = args.iso.resolve()
    out = args.output.resolve()
    if not iso.is_file() or iso.stat().st_size == 0:
        raise SystemExit(f"ISO not found or empty: {iso}")
    out.mkdir(parents=True, exist_ok=True)
    grub = out / "production-grub.cfg"
    extract(iso, "/boot/grub/grub.cfg", grub)
    config = grub.read_text(encoding="utf-8", errors="replace")
    # Check the actual production media contains all three init ELF modules.
    for target in TARGETS:
        dest = out / f"target-init-{target}.elf"
        extract(iso, f"/boot/targets/target-init-{target}.elf", dest)
        run("readelf", "-h", str(dest))
        if menu_index(config, TARGETS[target][0]) < 0:
            raise RuntimeError(f"missing production GRUB entry for {target}")
    failed = []
    for target, (entry_id, nested) in TARGETS.items():
        rc = boot_target(iso, out, target, menu_index(config, entry_id), nested)
        if rc:
            failed.append(target)
    if failed:
        print("Production ISO userspace handoff NOT VERIFIED for: " + ", ".join(failed))
        return 1
    print("PASS: production Live, Installer and Recovery GRUB entries each launched their target init ELF from the same ISO.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

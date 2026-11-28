#!/usr/bin/env python3
"""Bounded BIOS/QEMU runtime test for native Live ring-3 VFS syscalls.

This is not the six-case production acceptance matrix. It records one BIOS
boot of the exact ISO checksum and requires kernel preemption, user-originated
initramfs/tmpfs syscalls, and the matching PID 1 readiness handshake.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path


REQUIRED = {
    "kernel_ready": "[KRN ] KORONOS READY",
    "kernel_task_preemption": "[PMT ] SELFTEST PASS",
    "initramfs_open_read_close": "LIVE: initramfs /etc/os-release open/read/close PASS",
    "tmpfs_write_seek_read": "LIVE: /tmp write/seek/read roundtrip PASS",
    "live_userspace_ready": "USERSPACE READY: target=live init_pid=",
    "kernel_pid1_active": "KORONOS PID1 ACTIVE: target=live init_pid=",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def wait_for_grub_menu(serial_log: Path, process: subprocess.Popen[bytes]) -> bool:
    """Wait until GRUB has actually rendered the Live menu before injecting a key."""
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline and process.poll() is None:
        serial = read_text(serial_log)
        if "Live Aurora / Koronos" in serial:
            time.sleep(0.5)
            return True
        time.sleep(0.2)
    return False


def send_enter(monitor_path: Path, process: subprocess.Popen[bytes]) -> bool:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as monitor:
                monitor.settimeout(1)
                monitor.connect(str(monitor_path))
                try:
                    monitor.recv(4096)
                except OSError:
                    pass
                monitor.sendall(b"sendkey ret\n")
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=75)
    args = parser.parse_args()

    iso = args.iso.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checksum = iso.with_suffix(iso.suffix + ".sha256")
    serial_log = output / "bios-serial.log"
    debug_log = output / "bios-debugcon.log"
    monitor = output / "qemu-monitor.sock"
    evidence_file = output / "bios-live-runtime-evidence.json"

    if not iso.is_file() or not checksum.is_file():
        print("QEMU runtime test: ISO/checksum missing", file=sys.stderr)
        return 2
    expected = checksum.read_text(encoding="ascii").strip().split()[0]
    actual = sha256(iso)
    if expected != actual:
        print("QEMU runtime test: ISO checksum mismatch", file=sys.stderr)
        return 2

    command = [
        "qemu-system-x86_64", "-machine", "q35,accel=tcg", "-m", "2048",
        "-smp", "1", "-cdrom", str(iso), "-boot", "d", "-display", "none",
        "-serial", f"file:{serial_log}", "-debugcon", f"file:{debug_log}",
        "-global", "isa-debugcon.iobase=0xe9",
        "-monitor", f"unix:{monitor},server,nowait", "-no-reboot", "-no-shutdown",
    ]
    process = None
    enter_sent = False
    timed_out = False
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        grub_menu_seen = wait_for_grub_menu(serial_log, process)
        enter_sent = send_enter(monitor, process) if grub_menu_seen else False
        deadline = time.monotonic() + max(15, args.timeout)
        while time.monotonic() < deadline and process.poll() is None:
            trace = read_text(debug_log)
            if all(marker in trace for marker in REQUIRED.values()):
                break
            if "KORONOS PANIC:" in trace or "[RUN ] ERROR:" in trace:
                break
            time.sleep(0.25)
        else:
            timed_out = True
    except FileNotFoundError:
        print("QEMU runtime test: qemu-system-x86_64 is not installed", file=sys.stderr)
        return 2
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        try:
            monitor.unlink(missing_ok=True)
        except OSError:
            pass

    trace = read_text(debug_log)
    serial = read_text(serial_log)
    markers = {name: token in trace for name, token in REQUIRED.items()}
    # Serial is retained for diagnosis; all acceptance markers must be from
    # debugcon, where the ring-3 syscall payload is copied by the kernel.
    errors = [line for line in trace.splitlines()
              if "KORONOS PANIC:" in line or "[RUN ] ERROR:" in line
              or "LIVE: FAIL" in line]
    evidence = {
        "schema": "CHIMERA-QEMU-LIVE-VFS-1",
        "scope": "one BIOS single-CPU QEMU boot; x86-64 kernel-task preemption and Live ring-3 initramfs/tmpfs syscalls",
        "production_acceptance": False,
        "iso_sha256": actual,
        "qemu_command": command,
        "timeout_seconds": args.timeout,
        "grub_menu_seen_on_serial": grub_menu_seen,
        "enter_sent_to_grub": enter_sent,
        "timed_out_waiting_for_full_marker_set": timed_out,
        "markers": markers,
        "runtime_errors": errors,
        "debugcon_sha256": sha256(debug_log) if debug_log.exists() else None,
        "serial_sha256": sha256(serial_log) if serial_log.exists() else None,
        "debugcon_log": debug_log.name,
        "serial_log": serial_log.name,
    }
    evidence_file.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if all(markers.values()) and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

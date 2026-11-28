#!/usr/bin/env python3
"""Run a bounded BIOS/QEMU smoke boot of the built Chimera ISO.

This is runtime smoke evidence for the default Live menu entry and the
single-CPU kernel-task preemption self-test. It is deliberately not the
six-case production acceptance verifier.
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


def press_enter(monitor_path: Path, process: subprocess.Popen[bytes]) -> bool:
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as monitor:
                monitor.settimeout(1.0)
                monitor.connect(str(monitor_path))
                try:
                    monitor.recv(4096)
                except OSError:
                    pass
                monitor.sendall(b"sendkey ret\n")
                return True
        except (FileNotFoundError, ConnectionRefusedError, TimeoutError, OSError):
            time.sleep(0.1)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    iso = args.iso.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    serial_log = output / "bios-serial.log"
    debug_log = output / "bios-debugcon.log"
    monitor_path = output / "qemu-monitor.sock"
    evidence_path = output / "qemu-smoke-evidence.json"
    checksum_path = iso.with_suffix(iso.suffix + ".sha256")

    if not iso.is_file() or not checksum_path.is_file():
        print("QEMU smoke: ISO or adjacent SHA-256 file is missing", file=sys.stderr)
        return 2

    checksum_fields = checksum_path.read_text(encoding="ascii").strip().split()
    expected_sha = checksum_fields[0] if checksum_fields else ""
    actual_sha = sha256(iso)
    if expected_sha != actual_sha:
        print("QEMU smoke: ISO SHA-256 does not match its build manifest", file=sys.stderr)
        return 2

    qemu = [
        "qemu-system-x86_64",
        "-machine", "q35,accel=tcg",
        "-m", "2048",
        "-smp", "2",
        "-cdrom", str(iso),
        "-boot", "d",
        "-display", "none",
        "-serial", f"file:{serial_log}",
        "-debugcon", f"file:{debug_log}",
        "-global", "isa-debugcon.iobase=0xe9",
        "-monitor", f"unix:{monitor_path},server,nowait",
        "-no-reboot",
        "-no-shutdown",
    ]

    process: subprocess.Popen[bytes] | None = None
    enter_sent = False
    deadline = time.monotonic() + max(10, args.timeout)
    try:
        process = subprocess.Popen(
            qemu,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        enter_sent = press_enter(monitor_path, process)
        while time.monotonic() < deadline and process.poll() is None:
            trace = read_text(debug_log)
            if "[KRN ] KORONOS READY" in trace and "[PMT ] SELFTEST PASS" in trace:
                break
            time.sleep(0.25)
    except FileNotFoundError:
        print("QEMU smoke: qemu-system-x86_64 is not installed", file=sys.stderr)
        return 2
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    debug_text = read_text(debug_log)
    serial_text = read_text(serial_log)
    markers = {
        "grub_menu_enter_sent": enter_sent,
        "kernel_ready": "[KRN ] KORONOS READY" in debug_text,
        "preemptive_kernel_task_selftest": "[PMT ] SELFTEST PASS" in debug_text,
        "smp_selftest_pass": "[SMP ] Native x86_64 AP startup/two-CPU overlap gate passed" in debug_text,
        "native_stack_selftest_pass": "[NST ] Native block/VFS/PID1 gate passed" in debug_text,
        "installer_recovery_selftest_pass": "[INS ] Native installer/installed-root/recovery gate passed" in debug_text,
        "live_userspace_ready": "USERSPACE READY: target=live" in debug_text or "USERSPACE READY: target=live" in serial_text,
    }
    evidence = {
        "schema": "CHIMERA-QEMU-SMOKE-1",
        "scope": "BIOS QEMU boot of default Live menu entry; kernel readiness and single-CPU preemption self-test only",
        "production_acceptance": False,
        "iso_sha256": actual_sha,
        "qemu_command": qemu,
        "timeout_seconds": args.timeout,
        "markers": markers,
        "debugcon_sha256": sha256(debug_log) if debug_log.exists() else None,
        "serial_sha256": sha256(serial_log) if serial_log.exists() else None,
        "debugcon_log": debug_log.name,
        "serial_log": serial_log.name,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if markers["kernel_ready"] and markers["preemptive_kernel_task_selftest"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

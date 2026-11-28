#!/usr/bin/env python3
"""Capture a bounded BIOS/QEMU smoke boot; never imply production acceptance."""
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
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def monitor_command(path: Path, command: bytes, log: Path) -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect(str(path))
            greeting = sock.recv(8192)
            sock.sendall(command + b"\n")
            try:
                response = sock.recv(8192)
            except (TimeoutError, OSError):
                response = b""
        with log.open("ab") as stream:
            stream.write(greeting + response + b"\n")
        return True
    except (FileNotFoundError, ConnectionRefusedError, TimeoutError, OSError) as exc:
        with log.open("a", encoding="utf-8") as stream:
            stream.write(f"monitor error: {type(exc).__name__}: {exc}\n")
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
    serial = output / "bios-serial.log"
    debugcon = output / "bios-debugcon.log"
    qemu_log = output / "qemu-debug.log"
    monitor_log = output / "qemu-monitor.log"
    monitor = output / "qemu-monitor.sock"
    evidence = output / "qemu-smoke-evidence.json"
    for path in (serial, debugcon, qemu_log, monitor_log):
        path.write_text("", encoding="utf-8")

    result = 1
    qemu_command: list[str] = []
    iso_digest = None
    menu_seen = False
    enter_sent = False
    error = None
    process = None

    try:
        checksum_file = Path(str(iso) + ".sha256")
        if not iso.is_file() or not checksum_file.is_file():
            raise RuntimeError("ISO or checksum sidecar missing")
        fields = checksum_file.read_text(encoding="ascii").strip().split()
        expected = fields[0] if fields else ""
        iso_digest = sha256(iso)
        if expected != iso_digest:
            raise RuntimeError("ISO checksum sidecar mismatch")

        qemu_command = [
            "qemu-system-x86_64",
            "-machine", "pc,accel=tcg",
            "-cpu", "max",
            "-m", "2048",
            "-smp", "1",
            "-cdrom", str(iso),
            "-boot", "order=d,menu=on",
            "-display", "none",
            "-serial", f"file:{serial}",
            "-debugcon", f"file:{debugcon}",
            "-global", "isa-debugcon.iobase=0xe9",
            "-monitor", f"unix:{monitor},server,nowait",
            "-no-reboot",
            "-no-shutdown",
            "-d", "guest_errors,int",
            "-D", str(qemu_log),
        ]
        process = subprocess.Popen(
            qemu_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + max(10, args.timeout)
        for _ in range(80):
            if process.poll() is not None:
                break
            if monitor_command(monitor, b"info status", monitor_log):
                break
            time.sleep(0.1)

        menu_deadline = min(deadline, time.monotonic() + 30)
        while time.monotonic() < menu_deadline and process.poll() is None:
            serial_text = read(serial)
            debug_text = read(debugcon)
            if "Chimera II OS" in serial_text or "Live Aurora / Koronos" in serial_text:
                menu_seen = True
                enter_sent = monitor_command(monitor, b"sendkey ret", monitor_log)
                break
            time.sleep(0.25)

        while time.monotonic() < deadline and process.poll() is None:
            combined = read(serial) + "\n" + read(debugcon)
            preemption_pass = (
                "[PMT ] Native x86_64 context-save/timer-preemption gate passed" in combined
                or "[PMT ] SELFTEST PASS" in combined
            )
            preemption_fail = (
                "[PMT ] Native x86_64 context-save/timer-preemption gate FAILED" in combined
                or "[PMT ] SELFTEST FAIL" in combined
            )
            if "[KRN ] KORONOS READY" in combined and (preemption_pass or preemption_fail):
                break
            time.sleep(0.25)

    except Exception as exc:  # preserve evidence for all test-harness failures
        error = f"{type(exc).__name__}: {exc}"
        print(f"QEMU smoke error: {error}", file=sys.stderr)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    serial_text = read(serial)
    debug_text = read(debugcon)
    combined = serial_text + "\n" + debug_text
    markers = {
        "grub_menu_seen": menu_seen,
        "monitor_connected_and_enter_sent": enter_sent,
        "kernel_ready": "[KRN ] KORONOS READY" in combined,
        "preemptive_kernel_task_selftest": (
            "[PMT ] Native x86_64 context-save/timer-preemption gate passed" in combined
            or "[PMT ] SELFTEST PASS" in combined
        ),
        "preemptive_kernel_task_selftest_failed": (
            "[PMT ] Native x86_64 context-save/timer-preemption gate FAILED" in combined
            or "[PMT ] SELFTEST FAIL" in combined
        ),
        "smp_selftest_pass": (
            "[SMP ] Native x86_64 AP startup/two-CPU overlap gate passed" in combined
        ),
        "native_stack_selftest_pass": (
            "[NST ] Native block/VFS/PID1 gate passed" in combined
        ),
        "installer_recovery_selftest_pass": (
            "[INS ] Native installer/installed-root/recovery gate passed" in combined
        ),
        "live_userspace_ready": "USERSPACE READY: target=live" in combined,
        "grub_or_kernel_output_seen": bool(serial_text or debug_text or menu_seen),
    }
    if error is None and markers["kernel_ready"] and markers["preemptive_kernel_task_selftest"]:
        result = 0

    logs = (serial, debugcon, qemu_log, monitor_log)
    evidence_doc = {
        "schema": "CHIMERA-QEMU-SMOKE-3",
        "scope": "BIOS QEMU default Live entry; COM1/debugcon; one vCPU; preemption self-test",
        "production_acceptance": False,
        "iso_sha256": iso_digest,
        "qemu_command": qemu_command,
        "timeout_seconds": args.timeout,
        "error": error,
        "qemu_exit_code": process.returncode if process is not None else None,
        "markers": markers,
        "logs": {
            path.name: sha256(path) if path.exists() else None for path in logs
        },
        "log_sizes": {
            path.name: path.stat().st_size if path.exists() else 0 for path in logs
        },
    }
    evidence.write_text(json.dumps(evidence_doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence_doc, indent=2))
    return result


if __name__ == "__main__":
    raise SystemExit(main())

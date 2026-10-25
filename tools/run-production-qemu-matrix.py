#!/usr/bin/env python3
"""Boot the exact built ISO in six headless BIOS/UEFI target cases.

This harness does not manufacture readiness markers. It writes an ISO digest
header, preserves the raw QEMU serial/debugcon output, and fails if required
production runtime evidence is missing. It is diagnostic acceptance, not a
replacement for the unchanged DAPS verifier or installer/recovery/SMP gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

TARGETS = {"live": 0, "installer": 2, "recovery": 5}
COMPONENTS = {
    "live": "aurora-session",
    "installer": "install-executor",
    "recovery": "recovery-runtime",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ovmf_pair() -> tuple[Path, Path] | None:
    roots = (Path("/usr/share/OVMF"), Path("/usr/share/edk2"))
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(root.rglob("OVMF_CODE*.fd"))
            candidates.extend(root.rglob("OVMF_CODE*.bin"))
    candidates.extend(Path("/usr/share").glob("OVMF_CODE*.fd"))
    candidates.extend(Path("/usr/share").glob("OVMF_CODE*.bin"))
    for code in sorted(set(candidates)):
        vars_path = Path(str(code).replace("OVMF_CODE", "OVMF_VARS"))
        if vars_path.is_file():
            return code, vars_path
    return None


def monitor_send(sock_path: Path, commands: list[str], wait_seconds: float = 0.15) -> None:
    deadline = time.monotonic() + 8
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while True:
        try:
            conn.connect(str(sock_path))
            break
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"QEMU monitor socket did not become ready: {sock_path}")
            time.sleep(0.1)
    conn.settimeout(0.3)
    try:
        try:
            conn.recv(4096)
        except (TimeoutError, OSError):
            pass
        for command in commands:
            conn.sendall((command + "\n").encode("ascii"))
            time.sleep(wait_seconds)
            try:
                conn.recv(4096)
            except (TimeoutError, OSError):
                pass
    finally:
        conn.close()


def target_marker_errors(target: str, text: str) -> list[str]:
    errors: list[str] = []
    if "[KRN ] KORONOS READY" not in text:
        errors.append("kernel-ready marker missing")
    syscall = re.search(
        r"USER INIT SYSCALL: target=" + re.escape(target) + r" init_pid=([1-9][0-9]*)",
        text,
    )
    native_pid = re.search(
        r"NATIVE INIT PID: target=" + re.escape(target) + r" pid=([1-9][0-9]*)",
        text,
    )
    target_ready = re.search(
        r"USERSPACE TARGET READY: " + re.escape(target) +
        r" component=" + re.escape(COMPONENTS[target]) +
        r" init pid=([1-9][0-9]*)",
        text,
    )
    if not syscall:
        errors.append("user-originated syscall acknowledgement with nonzero PID missing")
    if not native_pid:
        errors.append("native-init PID diagnostic with nonzero PID missing")
    if not target_ready:
        errors.append("target-specific production readiness marker missing")
    if syscall and native_pid and syscall.group(1) != native_pid.group(1):
        errors.append("syscall PID and native-init PID differ")
    if syscall and target_ready and syscall.group(1) != target_ready.group(1):
        errors.append("syscall PID and target-readiness PID differ")
    if syscall and target_ready and syscall.start() >= target_ready.start():
        errors.append("syscall acknowledgement does not precede target readiness")
    expected_mount = (
        f"USERSPACE ROOTFS MOUNTED: target={target}"
        if target in ("live", "recovery")
        else "USERSPACE INSTALLER STORAGE ROOT MOUNTED: target=installer"
    )
    if expected_mount not in text:
        errors.append("target-specific process-visible root namespace mount evidence missing")
    if "NATIVE INIT VFS SELFTEST PASS" not in text:
        errors.append("kernel-backed VFS self-test marker missing")
    if "USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE" not in text:
        errors.append("process-visible /etc/os-release OPEN/READ/CLOSE evidence missing")
    if "USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE" not in text:
        errors.append("writable /tmp CREATE/WRITE/READ/TRUNCATE evidence missing")
    if "NATIVE INIT BLOCKED" in text or "NATIVE INIT VFS SELFTEST FAIL" in text:
        errors.append("native init explicitly reported blocked/failed services")
    return errors


def run_case(iso: Path, output: Path, digest: str, target: str, firmware: str,
             pair: tuple[Path, Path] | None, timeout_seconds: int) -> dict:
    case_id = f"{target}-{firmware}"
    case_dir = output / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    debug_log = case_dir / "qemu-debugcon.raw.log"
    serial_log = case_dir / "qemu-serial.raw.log"
    trace = case_dir / "raw-trace.log"
    monitor = Path("/tmp") / f"chm-{os.getpid()}-{target}-{firmware}.sock"
    monitor.unlink(missing_ok=True)

    command = [
        "qemu-system-x86_64", "-machine", "q35", "-cpu", "max", "-smp", "2",
        "-m", "2048", "-cdrom", str(iso), "-boot", "d", "-display", "none",
        "-serial", f"file:{serial_log}", "-monitor", f"unix:{monitor},server,nowait",
        "-no-reboot", "-no-shutdown", "-debugcon", f"file:{debug_log}",
        "-global", "isa-debugcon.iobase=0xe9",
    ]
    if firmware == "uefi":
        if pair is None:
            trace.write_text(f"PRODUCTION ISO SHA-256: {digest}\nCASE: {case_id}\nOVMF code/vars pair unavailable\n")
            return {"case": case_id, "status": "BLOCKED", "errors": ["matching OVMF code/vars pair unavailable"], "trace": trace.relative_to(output).as_posix()}
        code, vars_template = pair
        vars_copy = case_dir / "OVMF_VARS.fd"
        shutil.copyfile(vars_template, vars_copy)
        command.extend([
            "-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={code}",
            "-drive", f"if=pflash,format=raw,unit=1,file={vars_copy}",
        ])
    if target in ("installer", "recovery"):
        disk = case_dir / "target-disk.qcow2"
        if not disk.exists():
            subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "4G"],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        command.extend(["-drive", f"file={disk},if=virtio,format=qcow2"])

    qemu_rc: int | None = None
    monitor_error = ""
    process = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        # GRUB's checked-in menu timeout is eight seconds. Navigate the actual
        # ISO menu, not a reconstructed target ISO or probe ELF.
        time.sleep(2.0)
        key_commands = ["sendkey down"] * TARGETS[target] + ["sendkey ret"]
        try:
            monitor_send(monitor, key_commands)
        except (TimeoutError, OSError) as exc:
            monitor_error = str(exc)
        try:
            qemu_rc = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                qemu_rc = process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                qemu_rc = process.wait(timeout=3)
    except FileNotFoundError as exc:
        monitor_error = f"QEMU executable missing: {exc}"
    finally:
        if process and process.poll() is None:
            process.kill()
            process.wait()
        monitor.unlink(missing_ok=True)

    debug = debug_log.read_text(encoding="utf-8", errors="replace") if debug_log.exists() else ""
    serial = serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.exists() else ""
    combined = (
        f"PRODUCTION ISO SHA-256: {digest}\n"
        f"CASE: target={target} firmware={firmware} qemu_exit={qemu_rc}\n"
        + (f"HARNESS NOTE: {monitor_error}\n" if monitor_error else "")
        + "\n===== RAW DEBUGCON =====\n" + debug
        + "\n===== RAW SERIAL =====\n" + serial
    )
    trace.write_text(combined, encoding="utf-8")
    errors = target_marker_errors(target, combined)
    if monitor_error:
        errors.append(f"menu selection/monitor issue: {monitor_error}")
    return {
        "case": case_id,
        "status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "qemu_exit": qemu_rc,
        "iso_sha256": digest,
        "trace": trace.relative_to(output).as_posix(),
        "serial_log": serial_log.relative_to(output).as_posix(),
        "debugcon_log": debug_log.relative_to(output).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    iso = args.iso.resolve()
    output = args.output.resolve()
    if not iso.is_file() or iso.stat().st_size == 0:
        parser.error(f"ISO missing or empty: {iso}")
    if args.timeout < 5 or args.timeout > 120:
        parser.error("--timeout must be between 5 and 120 seconds")
    if shutil.which("qemu-system-x86_64") is None or shutil.which("qemu-img") is None:
        parser.error("qemu-system-x86_64 and qemu-img are required")
    pair = ovmf_pair()
    if pair is None:
        print("WARNING: OVMF pair not found; BIOS cases will run, UEFI cases will be BLOCKED.")
    output.mkdir(parents=True, exist_ok=True)
    digest_before = sha256(iso)
    results = []
    for target in TARGETS:
        for firmware in ("bios", "uefi"):
            print(f"[MATRIX] target={target} firmware={firmware} iso_sha256={digest_before}", flush=True)
            results.append(run_case(iso, output, digest_before, target, firmware, pair, args.timeout))
            print(f"[MATRIX] {results[-1]['case']}={results[-1]['status']}", flush=True)
            for error in results[-1]["errors"]:
                print(f"  BLOCKER: {error}", flush=True)
    digest_after = sha256(iso)
    if digest_after != digest_before:
        results.append({"case": "artifact-integrity", "status": "BLOCKED",
                        "errors": ["ISO SHA-256 changed during the matrix"]})
    report = {
        "schema": "CHM-PRODUCTION-ISO-QEMU-MATRIX-1",
        "iso": str(iso),
        "iso_sha256": digest_before,
        "iso_sha256_after": digest_after,
        "cases": results,
        "target_boot_matrix": "PASS" if all(x["status"] == "PASS" for x in results) else "BLOCKED",
        "production_acceptance": "NOT ESTABLISHED BY THIS MATRIX",
        "note": "This report proves only the six exact-ISO target boot traces. The unchanged production DAPS verifier and independent persistence/recovery/display/SMP gates remain authoritative.",
    }
    (output / "matrix-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["target_boot_matrix"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

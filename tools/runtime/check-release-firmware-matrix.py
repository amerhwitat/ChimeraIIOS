#!/usr/bin/env python3
"""Fail-closed immutable-ISO six-case BIOS/UEFI release acceptance.

The same ISO bytes are booted for Live, Installer and Recovery under both
SeaBIOS and OVMF. For every case the runner records the exact QEMU argv,
firmware identity, serial trace, kernel debugcon trace, disk fixture hash,
ISO hash, exit code and the fail-closed userspace handoff verifier result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

TARGETS = {"live": 0, "installer": 2, "recovery": 5}
FIRMWARES = ("bios", "uefi")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def wait_for(path: Path, needles: list[str], timeout: float) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = read_text(path)
        if all(needle in text for needle in needles):
            return text
        time.sleep(0.25)
    raise TimeoutError(f"timed out waiting for {needles!r} in {path}")


class QMP:
    def __init__(self, sock_path: Path):
        deadline = time.monotonic() + 30
        sock = None
        while time.monotonic() < deadline:
            if sock_path.exists():
                try:
                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    sock.connect(str(sock_path))
                    break
                except OSError:
                    if sock is not None:
                        sock.close()
                    sock = None
            time.sleep(0.1)
        if sock is None:
            raise RuntimeError(f"QMP socket never appeared: {sock_path}")
        self.sock = sock
        self.stream = sock.makefile("rwb", buffering=0)
        greeting = json.loads(self.stream.readline().decode("utf-8"))
        if "QMP" not in greeting:
            raise RuntimeError(f"unexpected QMP greeting: {greeting}")
        self.next_id = 0
        self.call("qmp_capabilities")

    def call(self, command: str, arguments: dict | None = None):
        self.next_id += 1
        request_id = f"cmd{self.next_id}"
        message: dict = {"execute": command, "id": request_id}
        if arguments is not None:
            message["arguments"] = arguments
        self.stream.write((json.dumps(message) + "\n").encode("utf-8"))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            line = self.stream.readline()
            if not line:
                raise RuntimeError("QMP connection closed")
            response = json.loads(line.decode("utf-8"))
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise RuntimeError(f"QMP {command} failed: {response['error']}")
            return response.get("return", {})
        raise TimeoutError(f"QMP {command} timed out")

    def press(self, code: str) -> None:
        # QEMU 10 QAPI uses the qcode variant of KeyValue.
        self.call("send-key", {"keys": [{"type": "qcode", "data": code}]})
        time.sleep(0.2)

    def quit(self) -> None:
        try:
            self.call("quit")
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", type=Path, default=None)
    parser.add_argument("--ovmf", type=Path, default=None)
    parser.add_argument("--work", type=Path, default=None)
    parser.add_argument("--verifier", type=Path, default=None)
    parser.add_argument("--ovmf-version", default=None)
    parser.add_argument("--only", help="run only CASE such as live-bios")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    iso = (args.iso or Path(os.environ.get(
        "CHIMERA_RELEASE_ISO", str(root / "build/iso/chimera-ii-os.iso")))).resolve()
    ovmf = (args.ovmf or Path(os.environ.get(
        "CHIMERA_OVMF_FIRMWARE", "/usr/share/OVMF/OVMF.fd"))).resolve()
    work = (args.work or Path(os.environ.get(
        "CHIMERA_RELEASE_MATRIX_DIR", str(root / "build/release-matrix")))).resolve()
    verifier = (args.verifier or Path(os.environ.get(
        "CHIMERA_HANDOFF_VERIFIER", str(root / "tests/boot/verify-userspace-handoff.py")))).resolve()
    ovmf_version = args.ovmf_version or os.environ.get("CHIMERA_OVMF_VERSION", "unknown")

    work.mkdir(parents=True, exist_ok=True)
    if not iso.is_file():
        raise SystemExit(f"missing ISO: {iso}")
    if not ovmf.is_file():
        raise SystemExit(f"missing OVMF firmware: {ovmf}")
    if not verifier.is_file():
        raise SystemExit(f"missing handoff verifier: {verifier}")

    base_disk = work / "disk-base.img"
    if not base_disk.exists():
        subprocess.run(["truncate", "-s", "64M", str(base_disk)], check=True)
    iso_hash = sha256(iso)
    ovmf_hash = sha256(ovmf)
    qemu_version = subprocess.check_output(
        ["qemu-system-x86_64", "--version"], text=True
    ).splitlines()[0]

    cases = [(target, firmware) for firmware in FIRMWARES for target in TARGETS]
    if args.only:
        cases = [(t, f) for t, f in cases if f"{t}-{f}" == args.only]
        if not cases:
            raise SystemExit(f"unknown case: {args.only}")

    results = []
    all_pass = True
    for target, firmware in cases:
        case_name = f"{target}-{firmware}"
        case_dir = work / case_name
        case_dir.mkdir(parents=True, exist_ok=True)
        serial_trace = case_dir / "serial.log"
        kernel_trace = case_dir / "debugcon.log"
        qmp_log = case_dir / "qmp.log"
        qmp_sock = case_dir / "qmp.sock"
        disk = case_dir / "disk.img"
        shutil.copyfile(base_disk, disk)
        for stale in (serial_trace, kernel_trace, qmp_log, qmp_sock):
            if stale.exists():
                stale.unlink()

        qemu_args = [
            "qemu-system-x86_64",
            "-m", "512",
            "-smp", "1",
            "-cdrom", str(iso),
            "-hda", str(disk),
            "-serial", f"file:{serial_trace}",
            "-debugcon", f"file:{kernel_trace}",
            "-global", "isa-debugcon.iobase=0xe9",
            "-display", "none",
            "-monitor", "none",
            "-qmp", f"unix:{qmp_sock},server=on,wait=off",
            "-no-reboot",
            "-no-shutdown",
        ]
        if firmware == "uefi":
            qemu_args += ["-bios", str(ovmf)]

        command_line = " ".join(shlex.quote(arg) for arg in qemu_args)
        qmp_log.write_text(command_line + "\n", encoding="utf-8")
        with serial_trace.open("wb") as serial_handle:
            proc = subprocess.Popen(qemu_args, stdout=serial_handle, stderr=subprocess.STDOUT)
            qmp = None
            status = "FAIL"
            failure = ""
            try:
                qmp = QMP(qmp_sock)
                wait_for(serial_trace, ["Live Aurora / Koronos"], 90)
                for _ in range(TARGETS[target]):
                    qmp.press("down")
                qmp.press("ret")
                if target == "recovery":
                    wait_for(serial_trace, ["Loading dedicated recovery menu"], 60)
                    qmp.press("ret")
                wait_for(
                    kernel_trace,
                    [
                        "[KRN ] KORONOS READY",
                        f"USER INIT SYSCALL: target={target}",
                        f"USERSPACE READY: target={target}",
                    ],
                    150,
                )
                time.sleep(2)
                status = "PASS"
            except Exception as exc:
                failure = f"{type(exc).__name__}: {exc}"
            finally:
                if qmp is not None:
                    qmp.quit()
                try:
                    exit_code = proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    exit_code = proc.wait(timeout=10)

        verify = subprocess.run(
            [sys.executable, str(verifier), target, str(kernel_trace)],
            capture_output=True,
            text=True,
        )
        trace_text = read_text(kernel_trace)
        handoff = {
            "kernel_ready": "[KRN ] KORONOS READY" in trace_text,
            "init_syscall": f"USER INIT SYSCALL: target={target}" in trace_text,
            "userspace_ready": f"USERSPACE READY: target={target}" in trace_text,
        }
        if verify.returncode != 0:
            status = "FAIL"
            failure = failure or f"handoff verifier failed: {verify.stderr.strip() or verify.stdout.strip()}"
        if exit_code != 0:
            status = "FAIL"
            failure = failure or f"unexpected QEMU exit code {exit_code}"

        result = {
            "case": case_name,
            "target": target,
            "firmware": firmware,
            "grub_index": TARGETS[target],
            "status": status,
            "failure": failure,
            "iso_sha256": iso_hash,
            "disk_sha256": sha256(disk),
            "firmware_image_sha256": ovmf_hash if firmware == "uefi" else None,
            "firmware_label": (
                f"OVMF {ovmf_version} (OVMF.fd)" if firmware == "uefi"
                else "SeaBIOS (QEMU default)"
            ),
            "qemu_version": qemu_version,
            "qemu_command": command_line,
            "qemu_exit_code": exit_code,
            "handoff": handoff,
            "handoff_verifier": {
                "returncode": verify.returncode,
                "stdout": verify.stdout.strip(),
                "stderr": verify.stderr.strip(),
            },
            "serial_trace": str(serial_trace),
            "kernel_trace": str(kernel_trace),
        }
        (case_dir / "result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        results.append(result)
        all_pass = all_pass and status == "PASS"
        print(f"[{case_name}] {status} exit={exit_code} handoff={handoff}", flush=True)

    summary = {
        "iso": str(iso),
        "iso_sha256": iso_hash,
        "qemu_version": qemu_version,
        "ovmf": str(ovmf),
        "ovmf_sha256": ovmf_hash,
        "ovmf_version": ovmf_version,
        "all_pass": all_pass,
        "cases": results,
    }
    (work / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"ALL_PASS={all_pass}")
    print(f"SUMMARY={work / 'summary.json'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

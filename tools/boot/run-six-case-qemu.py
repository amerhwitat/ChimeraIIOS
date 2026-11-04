#!/usr/bin/env python3
"""Boot one immutable Koronos ISO for all target/firmware diagnostic cases.

This runner never remasters the ISO and never writes readiness/VFS/SMP/desktop/
installer/recovery markers. It captures raw QEMU debugcon and serial output;
the strict six-case verifier decides whether the real runtime evidence is
sufficient for production acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")
# Stable menu positions in boot/iso/grub.cfg. Recovery opens its own submenu.
MAIN_MENU_INDEX = {"live": 0, "installer": 2, "recovery": 5}
RECOVERY_MENU_INDEX = 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ovmf_images() -> tuple[Path, Path]:
    pairs = (
        (Path("/usr/share/OVMF/OVMF_CODE_4M.fd"), Path("/usr/share/OVMF/OVMF_VARS_4M.fd")),
        (Path("/usr/share/OVMF/OVMF_CODE.fd"), Path("/usr/share/OVMF/OVMF_VARS.fd")),
        (Path("/usr/share/edk2/ovmf/OVMF_CODE.fd"), Path("/usr/share/edk2/ovmf/OVMF_VARS.fd")),
    )
    for code, variables in pairs:
        if code.is_file() and variables.is_file():
            return code, variables
    raise FileNotFoundError("matching OVMF_CODE/OVMF_VARS pair not found; install the ovmf package")


def monitor_command(sock: socket.socket, command: str) -> None:
    sock.sendall((command + "\n").encode("ascii"))
    time.sleep(0.15)
    try:
        sock.recv(4096)
    except socket.timeout:
        pass


def select_grub_target(monitor_path: Path, target: str,
                       menu_indices: dict[str, int] | None = None) -> None:
    deadline = time.monotonic() + 20
    connection = None
    while time.monotonic() < deadline:
        try:
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.settimeout(1)
            connection.connect(str(monitor_path))
            break
        except OSError:
            if connection:
                connection.close()
            connection = None
            time.sleep(0.1)
    if connection is None:
        raise TimeoutError("QEMU monitor socket did not become available")
    with connection:
        try:
            connection.recv(4096)  # HMP greeting/prompt
        except socket.timeout:
            pass
        # The HMP socket opens before firmware has reached GRUB. Sending menu
        # keys immediately races firmware and silently leaves GRUB on its default.
        time.sleep(3.0)
        monitor_command(connection, "sendkey shift")
        time.sleep(0.3)
        monitor_command(connection, "sendkey home")
        indices = menu_indices or MAIN_MENU_INDEX
        for _ in range(indices[target]):
            monitor_command(connection, "sendkey down")
        monitor_command(connection, "sendkey ret")
        if target == "recovery":
            # Main menu recovery entry chains into boot/jasper/recovery.cfg.
            time.sleep(2)
            monitor_command(connection, "sendkey home")
            for _ in range(RECOVERY_MENU_INDEX):
                monitor_command(connection, "sendkey down")
            monitor_command(connection, "sendkey ret")


def run_case(iso: Path, evidence: Path, target: str, firmware: str,
             qemu: str, timeout_seconds: int, ovmf: tuple[Path, Path] | None,
             menu_indices: dict[str, int] | None = None) -> dict:
    case_dir = evidence / target / firmware
    case_dir.mkdir(parents=True, exist_ok=True)
    trace = case_dir / "debugcon.log"
    serial = case_dir / "serial.log"
    qemu_log = case_dir / "qemu.stderr.log"
    monitor = case_dir / "monitor.sock"
    before_hash = sha256(iso)

    command = [
        qemu, "-machine", "q35,accel=tcg", "-cpu", "max", "-m", "2048",
        "-smp", "2", "-display", "none", "-serial", f"file:{serial}",
        "-monitor", f"unix:{monitor},server,nowait", "-no-reboot",
        "-no-shutdown", "-cdrom", str(iso), "-boot", "order=d",
        "-debugcon", f"file:{trace}", "-global", "isa-debugcon.iobase=0xe9",
    ]
    if firmware == "uefi":
        if ovmf is None:
            raise ValueError("UEFI case requires OVMF_CODE and OVMF_VARS")
        code_image, vars_template = ovmf
        vars_copy = case_dir / "OVMF_VARS.fd"
        shutil.copy2(vars_template, vars_copy)
        command[1:1] = [
            "-drive", f"if=pflash,format=raw,readonly=on,file={code_image}",
            "-drive", f"if=pflash,format=raw,file={vars_copy}",
        ]

    qemu_rc = None
    selection_error = None
    with qemu_log.open("wb") as log:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=log)
        try:
            try:
                select_grub_target(monitor, target, menu_indices)
            except Exception as exc:  # preserve diagnostics; the verifier will block absent proof
                selection_error = f"{type(exc).__name__}: {exc}"
            try:
                qemu_rc = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                qemu_rc = 124  # expected idle timeout; verifier still requires real runtime markers
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    if not trace.exists():
        trace.write_bytes(b"")
    after_hash = sha256(iso)
    if before_hash != after_hash:
        raise RuntimeError(f"canonical ISO changed during {target}/{firmware} boot")
    trace_text = trace.read_text(encoding="utf-8", errors="replace")
    selected = re.search(r"chimera-user-init-elf\s+target=(live|installer|recovery)\b", trace_text)
    selected_target = selected.group(1) if selected else None
    if selected_target != target:
        selection_error = selection_error or (
            f"expected GRUB target {target}, observed {selected_target or 'no target-init module'}"
        )
    return {
        "target": target,
        "firmware": firmware,
        "selected_target": selected_target,
        "iso_sha256": before_hash,
        "qemu_exit_code": qemu_rc,
        "trace": str(trace.relative_to(evidence)),
        "serial_trace": str(serial.relative_to(evidence)) if serial.exists() else None,
        "qemu_log": str(qemu_log.relative_to(evidence)),
        "selection_error": selection_error,
        "qemu_command": command,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--timeout", type=int, default=35)
    parser.add_argument("--targets", nargs="+", choices=TARGETS, default=list(TARGETS))
    parser.add_argument("--firmwares", nargs="+", choices=FIRMWARES, default=list(FIRMWARES))
    parser.add_argument("--main-menu-index", action="append", default=[],
                        metavar="TARGET=INDEX",
                        help="Override a GRUB main-menu index for a different ISO menu layout")
    args = parser.parse_args()

    iso = args.iso.resolve()
    evidence = args.evidence_dir.resolve()
    if not iso.is_file() or iso.stat().st_size == 0:
        parser.error(f"canonical ISO missing or empty: {iso}")
    if shutil.which(args.qemu) is None:
        parser.error(f"QEMU executable not found: {args.qemu}")
    ovmf = ovmf_images() if "uefi" in args.firmwares else None
    menu_indices = dict(MAIN_MENU_INDEX)
    for item in args.main_menu_index:
        try:
            name, raw_index = item.split("=", 1)
            index = int(raw_index)
        except (ValueError, TypeError):
            parser.error(f"invalid --main-menu-index {item!r}; expected TARGET=INDEX")
        if name not in TARGETS or index < 0:
            parser.error(f"invalid --main-menu-index {item!r}")
        menu_indices[name] = index
    evidence.mkdir(parents=True, exist_ok=True)
    canonical_hash = sha256(iso)
    cases = []
    for target in args.targets:
        for firmware in args.firmwares:
            if sha256(iso) != canonical_hash:
                raise RuntimeError("canonical ISO hash changed between cases")
            cases.append(run_case(iso, evidence, target, firmware, args.qemu,
                                  args.timeout, ovmf, menu_indices))
    if sha256(iso) != canonical_hash:
        raise RuntimeError("canonical ISO hash changed after matrix execution")

    manifest = {
        "schema": "koronos-six-case-evidence-v1",
        "iso_sha256": canonical_hash,
        "cases": cases,
        "runner": "same-immutable-iso-qemu-diagnostic-runner-v1",
        "policy": "raw emulator traces only; no acceptance markers are synthesized",
    }
    (evidence / "matrix.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (evidence / "runner-summary.json").write_text(json.dumps({
        "schema": "koronos-six-case-runner-summary-v1",
        "iso_sha256": canonical_hash,
        "cases_attempted": len(cases),
        "cases_expected": 6,
        "selection_errors": sum(bool(case["selection_error"]) for case in cases),
        "trace_files": [case["trace"] for case in cases],
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"iso_sha256": canonical_hash, "cases_attempted": len(cases),
                      "evidence_dir": str(evidence)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

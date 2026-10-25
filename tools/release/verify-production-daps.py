#!/usr/bin/env python3
"""Fail-closed production DAPS verifier for a single immutable Koronos ISO.

Evidence is intentionally external to the verifier: this script never creates
readiness markers, treats build success as runtime success, or promotes probe
ISOs to production. See docs/PRODUCTION_DAPS.md for the evidence schema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")
KERNEL_MARKER = "[KRN ] KORONOS READY"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class GateError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read JSON evidence {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path}: top-level JSON must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise GateError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def read_trace(root: Path, item: dict, label: str, expected_sha: str) -> str:
    require(isinstance(item, dict), f"{label}: trace record must be an object")
    iso_sha = item.get("iso_sha256")
    require(iso_sha == expected_sha, f"{label}: trace ISO SHA-256 differs from candidate")
    payload_file = (root / str(item.get("payload_file", ""))).resolve()
    require(payload_file.is_relative_to(root.resolve()), f"{label}: payload path escapes evidence root")
    require(payload_file.is_file(), f"{label}: extracted production init ELF missing: {payload_file}")
    expected_payload_sha = item.get("payload_sha256")
    require(isinstance(expected_payload_sha, str) and SHA256_RE.fullmatch(expected_payload_sha),
            f"{label}: expected production init payload SHA-256 missing from trace evidence")
    actual_payload_sha = sha256_file(payload_file)
    require(actual_payload_sha == expected_payload_sha,
            f"{label}: extracted production init ELF hash mismatch")
    trace_path = (root / str(item.get("log", ""))).resolve()
    require(trace_path.is_relative_to(root.resolve()), f"{label}: trace path escapes evidence root")
    require(trace_path.is_file(), f"{label}: trace file missing: {trace_path}")
    text = trace_path.read_text(encoding="utf-8", errors="replace")
    kernel_at = text.find(KERNEL_MARKER)
    require(kernel_at >= 0, f"{label}: kernel-ready marker missing")

    target = label.split("/")[0]
    ack = list(re.finditer(
        rf"USER INIT SYSCALL: target={re.escape(target)} init_pid=([1-9][0-9]*)",
        text,
    ))
    ready = list(re.finditer(
        rf"USERSPACE READY: {re.escape(target)} init pid=([1-9][0-9]*)",
        text,
    ))
    require(ack, f"{label}: user-originated CPL3 syscall acknowledgement missing")
    require(ready, f"{label}: userspace readiness marker missing")
    require(kernel_at < ack[-1].start(), f"{label}: syscall acknowledgement precedes kernel readiness")
    require(ack[-1].start() < ready[-1].start(),
            f"{label}: userspace readiness precedes its syscall acknowledgement")
    require(ack[-1].group(1) == ready[-1].group(1),
            f"{label}: syscall acknowledgement PID and ready PID differ")
    ring3_return = text.find("USERSPACE SYSCALL RETURNED TO RING3", ack[-1].start())
    require(ring3_return >= 0, f"{label}: ring-3 return evidence missing")

    # Candidate user-init ELF probes are useful kernel smoke tests, but cannot
    # satisfy production release acceptance. Require explicit provenance from
    # the production initramfs extraction/launch path and bind it to this PID.
    target = label.split("/")[0]
    payload = list(re.finditer(
        rf"PRODUCTION INIT PAYLOAD: target={re.escape(target)} source=initramfs sha256=([0-9a-f]{{64}})",
        text,
    ))
    executed = list(re.finditer(
        rf"PRODUCTION INIT EXECUTED: target={re.escape(target)} pid=([1-9][0-9]*)",
        text,
    ))
    require(payload, f"{label}: production initramfs payload provenance missing (probe ELF is not production evidence)")
    require(executed, f"{label}: production init execution record missing")
    require(payload[-1].group(1) == expected_payload_sha,
            f"{label}: production init payload digest differs from independently recorded extracted payload")
    require(payload[-1].start() < ack[-1].start(),
            f"{label}: production payload provenance appears after user execution began")
    require(executed[-1].start() < ready[-1].start(),
            f"{label}: production init execution record appears after readiness")
    require(executed[-1].group(1) == ack[-1].group(1) == ready[-1].group(1),
            f"{label}: production init, syscall acknowledgement, and readiness PIDs differ")
    # Prove the same PID can use the mounted root VFS and writable /tmp from
    # ring 3. A generic syscall acknowledgement alone is not a file-I/O proof.
    pid = ack[-1].group(1)
    open_records = list(re.finditer(
        rf"USERSPACE FILE SYSCALL: target={re.escape(target)} pid={pid} op=open path=/etc/os-release result=fd:([1-9][0-9]*)",
        text,
    ))
    require(open_records, f"{label}: ring-3 rootfs OPEN evidence missing")
    fd = open_records[-1].group(1)
    read_records = list(re.finditer(
        rf"USERSPACE FILE SYSCALL: target={re.escape(target)} pid={pid} op=read path=/etc/os-release fd={fd} result=bytes:([1-9][0-9]*)",
        text,
    ))
    close_records = list(re.finditer(
        rf"USERSPACE FILE SYSCALL: target={re.escape(target)} pid={pid} op=close path=/etc/os-release fd={fd} result=0",
        text,
    ))
    tmp_records = list(re.finditer(
        rf"USERSPACE TMP SYSCALL: target={re.escape(target)} pid={pid} op=write path=/tmp/daps-probe result=bytes:([1-9][0-9]*)",
        text,
    ))
    require(read_records, f"{label}: ring-3 rootfs READ evidence missing")
    require(close_records, f"{label}: ring-3 rootfs CLOSE evidence missing")
    require(tmp_records, f"{label}: ring-3 writable /tmp write evidence missing")
    ready_at = ready[-1].start()
    for name, records in (("OPEN", open_records), ("READ", read_records),
                          ("CLOSE", close_records), ("/tmp WRITE", tmp_records)):
        require(ring3_return < records[-1].start() < ready_at,
                f"{label}: ring-3 {name} evidence is outside the acknowledged init execution window")
    require(open_records[-1].start() < read_records[-1].start() < close_records[-1].start(),
            f"{label}: rootfs OPEN/READ/CLOSE evidence is out of order")

    return text


def read_evidence_log(root: Path, relative: object, label: str, markers: tuple[str, ...]) -> str:
    require(isinstance(relative, str) and bool(relative), f"{label}: evidence log reference missing")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"{label}: evidence log path escapes evidence root")
    require(path.is_file(), f"{label}: evidence log missing: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    for marker in markers:
        require(marker in text, f"{label}: required evidence record missing: {marker}")
    return text


def verify(evidence_path: Path, report: bool = True) -> None:
    root = evidence_path.resolve().parent
    evidence = read_json(evidence_path)
    require(evidence.get("schema_version") == 1, "schema_version must be 1")
    iso_path = (root / str(evidence.get("iso", ""))).resolve()
    require(iso_path.is_relative_to(root), "ISO path escapes evidence root")
    require(iso_path.is_file(), "candidate ISO is missing")
    expected_sha = str(evidence.get("iso_sha256", ""))
    require(bool(SHA256_RE.fullmatch(expected_sha)), "iso_sha256 must be lowercase SHA-256")
    actual_sha = sha256_file(iso_path)
    require(actual_sha == expected_sha, f"candidate ISO hash mismatch: expected {expected_sha}, got {actual_sha}")
    with iso_path.open("rb") as stream:
        stream.seek(16 * 2048)
        primary_volume_descriptor = stream.read(7)
    require(primary_volume_descriptor == b"\x01CD001\x01",
            "candidate does not contain an ISO9660 primary volume descriptor at sector 16")

    traces = evidence.get("traces")
    require(isinstance(traces, dict), "traces must be an object")
    trace_text: dict[str, str] = {}
    for target in TARGETS:
        for firmware in FIRMWARES:
            label = f"{target}/{firmware}"
            require(label in traces, f"missing required production trace {label}")
            trace_text[label] = read_trace(root, traces[label], label, expected_sha)

    for firmware in FIRMWARES:
        live = trace_text[f"live/{firmware}"]
        require("USERSPACE TARGET READY: live component=aurora-session" in live,
                f"Live/{firmware}: actual Aurora session readiness missing")
        require("AURORA READY" in live, f"Live/{firmware}: Aurora runtime health marker missing")

    install = evidence.get("installer_persistence")
    require(isinstance(install, dict), "installer_persistence evidence missing")
    require(install.get("passed") is True, "installer persistence/cold reboot not accepted")
    require(install.get("iso_sha256") == expected_sha, "installer persistence evidence references a different ISO")
    require(install.get("write_verified") is True, "installer write postcondition missing")
    require(install.get("cold_reboot_verified") is True, "installed-disk cold reboot not verified")
    require(install.get("installed_system_ready") is True, "installed system readiness not verified")
    read_evidence_log(root, install.get("evidence_log"), "installer persistence", (
        "INSTALL WRITE VERIFIED",
        "INSTALLED DISK COLD REBOOT VERIFIED",
        "INSTALLED SYSTEM READY",
    ))

    recovery = evidence.get("recovery")
    require(isinstance(recovery, dict), "recovery evidence missing")
    require(recovery.get("passed") is True, "recovery repair not accepted")
    require(recovery.get("iso_sha256") == expected_sha, "recovery evidence references a different ISO")
    require(recovery.get("repair_action_executed") is True, "recovery repair action not executed")
    require(recovery.get("postcondition_verified") is True, "recovery repair postcondition not verified")
    read_evidence_log(root, recovery.get("evidence_log"), "recovery repair", (
        "RECOVERY REPAIR EXECUTED",
        "RECOVERY POSTCONDITION VERIFIED",
    ))

    smp = evidence.get("smp")
    require(isinstance(smp, dict), "SMP evidence missing")
    require(smp.get("passed") is True, "AP-backed concurrent SMP not accepted")
    require(smp.get("iso_sha256") == expected_sha, "SMP evidence references a different ISO")
    require(isinstance(smp.get("online_ap_cpus"), list) and len(set(smp["online_ap_cpus"])) >= 2,
            "SMP requires at least two distinct online CPU IDs including AP evidence")
    require(smp.get("overlap_observed") is True, "overlapping execution evidence missing")
    smp_log = read_evidence_log(root, smp.get("per_cpu_trace"), "SMP", ("SMP OVERLAP VERIFIED",))
    observed_cpus = set(re.findall(r"SMP AP ONLINE: cpu=([0-9]+)", smp_log))
    declared_cpus = {str(cpu) for cpu in smp["online_ap_cpus"]}
    require(len(observed_cpus) >= 2, "SMP trace must show at least two AP-online CPU records")
    require(declared_cpus.issubset(observed_cpus), "SMP declared CPU IDs are not all present in per-CPU trace")

    if report:
        print("PRODUCTION DAPS: PASS")
        print(f"ISO SHA-256: {expected_sha}")
        print("Runtime matrix: Live/Installer/Recovery × BIOS/UEFI: 6/6")
        print("Aurora, installer cold-reboot persistence, recovery postconditions, and AP-backed SMP: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path,
                        help="JSON evidence manifest; paths are relative to its directory")
    args = parser.parse_args()
    try:
        verify(args.evidence)
    except GateError as exc:
        print(f"PRODUCTION DAPS: BLOCKED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

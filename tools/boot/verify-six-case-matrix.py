#!/usr/bin/env python3
"""Fail-closed verifier for the canonical Koronos six-case release matrix.

Validates evidence produced by booting ONE immutable native Koronos ISO:
Live, Installer and Recovery under both BIOS and UEFI. It does not create
readiness markers, synthesize traces, or treat test ELFs as production payloads.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")
SCHEMA = "koronos-six-case-evidence-v1"
ACK = re.compile(r"USER INIT SYSCALL: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b")
READY = re.compile(r"USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b")
FIRMWARE = re.compile(r"BOOT FIRMWARE: (BIOS|UEFI)\b")
CPU = re.compile(r"SMP CPU ONLINE: logical_id=([0-9]+) apic_id=([0-9]+)\b")
OVERLAP = re.compile(r"SMP OVERLAP VERIFIED: cpu_a=([0-9]+) cpu_b=([0-9]+) overlap_ticks=([1-9][0-9]*)\b")
DESKTOP = re.compile(r"DESKTOP READY: profile=(aurora|marine) pid=([1-9][0-9]*)\b")
INSTALL_WRITE = re.compile(r"INSTALLER WRITE COMMITTED: token=([A-Za-z0-9._-]+)\b")
INSTALL_PERSIST = re.compile(r"INSTALLER COLD-BOOT PERSISTENCE VERIFIED: token=([A-Za-z0-9._-]+)\b")
RECOVERY_START = re.compile(r"RECOVERY REPAIR STARTED: transaction=([A-Za-z0-9._-]+)\b")
RECOVERY_DONE = re.compile(r"RECOVERY POSTCONDITION VERIFIED: transaction=([A-Za-z0-9._-]+)\b")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_trace(root: Path, relative: str, failures: list[str], label: str) -> str:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        failures.append(f"{label}: trace path escapes evidence directory")
        return ""
    if not candidate.is_file() or candidate.stat().st_size == 0:
        failures.append(f"{label}: missing or empty trace {relative!r}")
        return ""
    return candidate.read_text(encoding="utf-8", errors="replace")

def check_handoff(trace: str, target: str, failures: list[str], label: str) -> None:
    if "NATIVE INIT BLOCKED" in trace or re.search(r"\bexit(?:_code)?=78\b", trace):
        failures.append(f"{label}: native-init fail-closed exit 78/block marker observed")
        return
    kernel_at = trace.find("[KRN ] KORONOS READY")
    if kernel_at < 0:
        failures.append(f"{label}: missing Koronos kernel-ready marker")
        return
    acks, ready = list(ACK.finditer(trace)), list(READY.finditer(trace))
    if not acks: failures.append(f"{label}: missing CPL3-originated init syscall acknowledgement")
    if not ready: failures.append(f"{label}: missing userspace init readiness marker")
    if not any(a.group(1) == target and r.group(1) == target and a.group(2) == r.group(2)
               and kernel_at < a.start() < r.start() for a in acks for r in ready):
        failures.append(f"{label}: no ordered kernel -> CPL3 syscall -> matching nonzero PID readiness chain for {target}")

def check_runtime_contract(trace: str, target: str, firmware: str, failures: list[str], label: str) -> None:
    fw = FIRMWARE.search(trace)
    if not fw or fw.group(1).lower() != firmware:
        failures.append(f"{label}: trace does not prove {firmware.upper()} firmware execution")
    root_marker = f"VFS ACCEPTANCE: ROOT MOUNTED target={target} path=/"
    tmp_marker = f"VFS ACCEPTANCE: TMP WRITE-READ VERIFIED target={target} path=/tmp"
    if root_marker not in trace:
        failures.append(f"{label}: root filesystem mount/read contract not proven")
    if tmp_marker not in trace:
        failures.append(f"{label}: writable /tmp syscall round-trip not proven")
    matching = [(a, r) for a in ACK.finditer(trace) for r in READY.finditer(trace)
                if a.group(1) == target and r.group(1) == target and a.group(2) == r.group(2)
                and trace.find("[KRN ] KORONOS READY") < a.start() < r.start()]
    if matching:
        ack, ready = matching[0]
        root_at, tmp_at = trace.find(root_marker), trace.find(tmp_marker)
        if not (ack.start() < root_at < tmp_at < ready.start()):
            failures.append(f"{label}: VFS checks are not ordered inside the acknowledged init process before readiness")
    else:
        failures.append(f"{label}: VFS markers cannot be tied to the matching CPL3 init handoff")
    cpu_pairs = {(m.group(1), m.group(2)) for m in CPU.finditer(trace)}
    logical_ids = {logical for logical, _ in cpu_pairs}
    apic_ids = {apic for _, apic in cpu_pairs}
    if len(logical_ids) < 2 or len(apic_ids) < 2:
        failures.append(f"{label}: fewer than two distinct online logical/APIC CPU identities")
    if not any(m.group(1) != m.group(2) and m.group(1) in logical_ids and m.group(2) in logical_ids
               for m in OVERLAP.finditer(trace)):
        failures.append(f"{label}: no measured overlapping execution interval across two distinct online CPUs")

def check_desktop(root: Path, relative: str, profile: str, failures: list[str], label: str) -> None:
    trace = load_trace(root, relative, failures, label)
    if not trace: return
    match = DESKTOP.search(trace)
    if not match or match.group(1) != profile:
        failures.append(f"{label}: missing real DESKTOP READY marker for {profile}")
    if "NATIVE INIT BLOCKED" in trace:
        failures.append(f"{label}: native-init block marker observed")

def check_postcondition(root: Path, case: dict, target: str, failures: list[str], label: str) -> None:
    rel = case.get("postcondition_trace")
    if not isinstance(rel, str) or not rel:
        failures.append(f"{label}: missing target postcondition trace")
        return
    trace = load_trace(root, rel, failures, label + " postcondition")
    if target == "installer":
        writes, verified = INSTALL_WRITE.findall(trace), INSTALL_PERSIST.findall(trace)
        if not writes or not verified or not set(writes).intersection(verified):
            failures.append(f"{label}: installer write token was not verified after cold reboot")
    else:
        started, done = RECOVERY_START.findall(trace), RECOVERY_DONE.findall(trace)
        if not started or not done or not set(started).intersection(done):
            failures.append(f"{label}: recovery repair transaction lacks a matching verified postcondition")

def verify(iso: Path, evidence_dir: Path) -> dict:
    failures, cases_report = [], []
    if not iso.is_file() or iso.stat().st_size == 0:
        return {"schema": SCHEMA, "status": "BLOCKED", "failures": ["canonical ISO missing or empty"], "cases": []}
    iso_hash = sha256(iso)
    manifest_path = evidence_dir / "matrix.json"
    if not manifest_path.is_file():
        return {"schema": SCHEMA, "status": "BLOCKED", "iso_sha256": iso_hash,
                "failures": ["matrix.json missing: no six-case runtime evidence supplied"], "cases": []}
    try: manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": SCHEMA, "status": "BLOCKED", "iso_sha256": iso_hash, "failures": [f"invalid matrix.json: {exc}"], "cases": []}
    if not isinstance(manifest, dict):
        return {"schema": SCHEMA, "status": "BLOCKED", "iso_sha256": iso_hash, "failures": ["matrix.json root must be an object"], "cases": []}
    if manifest.get("schema") != SCHEMA: failures.append(f"matrix schema must be {SCHEMA}")
    if manifest.get("iso_sha256") != iso_hash: failures.append("matrix ISO SHA-256 does not match the canonical ISO under test")
    cases = manifest.get("cases")
    if not isinstance(cases, list): cases = []; failures.append("matrix cases must be an array")
    expected = {(t, f) for t in TARGETS for f in FIRMWARES}
    observed = []
    for index, case in enumerate(cases):
        label = f"case[{index}]"
        if not isinstance(case, dict): failures.append(f"{label}: case entry must be an object"); continue
        target, firmware = case.get("target"), case.get("firmware")
        if not isinstance(target, str) or not isinstance(firmware, str):
            failures.append(f"{label}: target and firmware must be strings")
            continue
        key = (target, firmware); observed.append(key)
        if key not in expected: failures.append(f"{label}: unsupported target/firmware pair {key!r}"); continue
        label = f"{target}/{firmware}"
        case_failure_start = len(failures)
        if case.get("iso_sha256") != iso_hash: failures.append(f"{label}: case did not attest the exact canonical ISO SHA-256")
        if case.get("qemu_exit_code") not in (0, 124):
            failures.append(f"{label}: QEMU exit code must be 0 or expected idle timeout 124, got {case.get('qemu_exit_code')!r}")
        rel = case.get("trace")
        trace = load_trace(evidence_dir, rel, failures, label) if isinstance(rel, str) and rel else ""
        if not isinstance(rel, str) or not rel: failures.append(f"{label}: missing main boot trace")
        if trace:
            check_handoff(trace, target, failures, label)
            check_runtime_contract(trace, target, firmware, failures, label)
        if target == "live":
            desktops = case.get("desktop_traces")
            if not isinstance(desktops, dict): failures.append(f"{label}: Aurora and Marine desktop traces are required")
            else:
                for profile in ("aurora", "marine"):
                    path = desktops.get(profile)
                    if not isinstance(path, str) or not path: failures.append(f"{label}: missing {profile} desktop trace reference")
                    else: check_desktop(evidence_dir, path, profile, failures, label + "/" + profile)
        else: check_postcondition(evidence_dir, case, target, failures, label)
        cases_report.append({"target": target, "firmware": firmware, "trace": rel,
                             "status": "PASS" if len(failures) == case_failure_start else "BLOCKED"})
    if len(observed) != len(expected) or set(observed) != expected or len(observed) != len(set(observed)):
        failures.append("matrix must contain exactly one case for each Live/Installer/Recovery x BIOS/UEFI pair")
    return {"schema": SCHEMA, "status": "PASS" if not failures else "BLOCKED",
            "iso_sha256": iso_hash, "cases_expected": 6, "cases_reported": len(cases_report),
            "failures": failures, "cases": cases_report,
            "policy": "No synthetic/test ELF, kernel-authored readiness, missing trace, partial VFS, or unverified SMP evidence can satisfy this gate."}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = verify(args.iso, args.evidence_dir)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())

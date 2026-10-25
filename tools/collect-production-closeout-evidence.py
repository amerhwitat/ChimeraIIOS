#!/usr/bin/env python3
"""Collect ISO identity and hash-bound production QEMU traces into fail-closed evidence.

Actual QEMU traces are kept distinct from candidate smoke logs. A blocked trace
remains BLOCKED, and independent display, installer persistence, recovery,
SMP, and VM/swap gates remain NOT RUN until separately evidenced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARE = ("bios", "uefi")
def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(iso: Path, output: Path, candidate_traces: Path, production_matrix: Path | None = None) -> dict:
    iso = iso.resolve()
    output = output.resolve()
    candidate_traces = candidate_traces.resolve()
    if not iso.is_file() or iso.stat().st_size == 0:
        raise ValueError(f"production ISO is missing or empty: {iso}")
    output.mkdir(parents=True, exist_ok=True)
    traces_dir = output / "closeout-traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    iso_rel = Path(iso.name)
    if iso.parent != output:
        # The DAPS validator resolves artifact paths relative to the evidence file.
        # Copying a potentially multi-gigabyte ISO is avoided; require same directory.
        raise ValueError("ISO must reside beside the evidence JSON so DAPS can verify its hash")

    iso_digest = sha256(iso)
    matrix_dir = production_matrix.resolve() if production_matrix is not None else None
    matrix_report = None
    matrix_cases: dict = {}
    matrix_note = "No production ISO QEMU matrix was supplied."
    if matrix_dir is not None:
        report_path = matrix_dir / "matrix-report.json"
        try:
            candidate_report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            candidate_report = None
        if isinstance(candidate_report, dict):
            report_hash = candidate_report.get("iso_sha256")
            after_hash = candidate_report.get("iso_sha256_after", report_hash)
            if isinstance(report_hash, str) and report_hash.lower() == iso_digest.lower() and isinstance(after_hash, str) and after_hash.lower() == iso_digest.lower():
                matrix_report = candidate_report
                raw_cases = candidate_report.get("cases")
                if isinstance(raw_cases, list):
                    matrix_cases = {
                        item.get("case"): item for item in raw_cases
                        if isinstance(item, dict) and isinstance(item.get("case"), str)
                    }
                matrix_note = "Exact-ISO QEMU matrix report hash matches the production ISO."
            else:
                matrix_note = "QEMU matrix ISO SHA-256 does not match this production ISO; matrix traces were not accepted."

    cases = {}
    production_trace_cases = set()
    component = {
        "live": "aurora-session",
        "installer": "install-executor",
        "recovery": "recovery-runtime",
    }
    for target in TARGETS:
        for firmware in FIRMWARE:
            case_id = f"{target}-{firmware}"
            candidate_name = f"{target}-debugcon.log" if firmware == "bios" else f"{target}-uefi-debugcon.log"
            candidate = candidate_traces / candidate_name
            raw_trace = ""
            trace_text = ""
            trace_source = "missing"
            production_bound = False
            matrix_case = matrix_cases.get(case_id) if matrix_report is not None else None
            if isinstance(matrix_case, dict) and matrix_case.get("qemu_started") is True and matrix_dir is not None:
                trace_rel = matrix_case.get("trace")
                if isinstance(trace_rel, str) and trace_rel:
                    rel_path = Path(trace_rel)
                    matrix_trace = (matrix_dir / rel_path).resolve()
                    if not rel_path.is_absolute() and ".." not in rel_path.parts and matrix_trace.is_relative_to(matrix_dir) and matrix_trace.is_file() and matrix_trace.stat().st_size:
                        copied = traces_dir / f"{case_id}-production-iso.log"
                        shutil.copyfile(matrix_trace, copied)
                        raw_trace = copied.relative_to(output).as_posix()
                        try:
                            trace_text = copied.read_text(encoding="utf-8")
                        except (OSError, UnicodeError):
                            trace_text = ""
                        trace_source = "production-iso-qemu-matrix"
                        production_bound = True
                        production_trace_cases.add(case_id)
            if not production_bound and candidate.is_file() and candidate.stat().st_size:
                copied = traces_dir / f"{case_id}-candidate-smoke.log"
                shutil.copyfile(candidate, copied)
                raw_trace = copied.relative_to(output).as_posix()
                try:
                    trace_text = copied.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    trace_text = ""
                trace_source = candidate_name

            syscall = re.search(
                r"USER INIT SYSCALL: target=" + re.escape(target) + r" init_pid=([1-9][0-9]*)",
                trace_text,
            )
            ready = re.search(
                r"USERSPACE TARGET READY: " + re.escape(target) +
                r" component=" + re.escape(component[target]) +
                r" init pid=([1-9][0-9]*)",
                trace_text,
            )
            rootfs_marker = f"USERSPACE ROOTFS MOUNTED: target={target}" if target in ("live", "recovery") else "USERSPACE INSTALLER STORAGE ROOT MOUNTED: target=installer"
            rootfs_open_close = "USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE" in trace_text
            tmpfs_mutation = "USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE" in trace_text
            display_match = re.search(r"DISPLAY MODE VERIFIED: ([0-9]+x[0-9]+)", trace_text)
            actual_status = "NOT RUN"
            if production_bound:
                actual_status = "PASS" if matrix_case.get("status") == "PASS" else "BLOCKED"
            case = {
                "status": actual_status,
                "production_iso": iso_rel.as_posix(),
                "iso_sha256": iso_digest,
                "raw_trace": raw_trace,
                "cpl3_syscall_ack": bool(syscall),
                "process_visible_rootfs": rootfs_marker in trace_text and rootfs_open_close,
                "display_mode_verified": bool(display_match),
                "display_mode": display_match.group(1) if display_match else "",
                "display_mode_evidence": raw_trace if display_match else "",
                "rootfs_file_syscalls_verified": rootfs_open_close,
                "rootfs_file_syscalls_evidence": raw_trace if rootfs_open_close else "",
                "syscall_pid": int(syscall.group(1)) if syscall else 0,
                "readiness_pid": int(ready.group(1)) if ready else 0,
                "candidate_trace_source": trace_source,
                "candidate_trace_is_production_evidence": production_bound,
            }
            if target in ("live", "recovery"):
                case["tmpfs_mutation_verified"] = tmpfs_mutation
                case["tmpfs_mutation_evidence"] = raw_trace if tmpfs_mutation else ""
            cases[case_id] = case

    data = {
        "schema_version": 1,
        "collector": "tools/collect-production-closeout-evidence.py",
        "production_iso_sha256": iso_digest,
        "candidate_smoke_substituted": len(production_trace_cases) != 6,
        "collection_note": f"{matrix_note} Actual production ISO traces bound: {len(production_trace_cases)}/6. Independent display, installer persistence, recovery repair, SMP and VM/swap gates remain NOT RUN.",
        "cases": cases,
        "display": {
            "status": "NOT RUN", "framebuffer_detected_verified": False,
            "highest_supported_mode_verified": False, "fallback_1024x768_verified": False,
            "fallback_640x480_verified": False, "aurora_compositor_handoff_verified": False,
            "selected_mode": "", "evidence": "",
        },
        "aurora_handoff": {"status": "NOT RUN", "evidence": ""},
        "installer_persistence": {
            "status": "NOT RUN", "write_verified": False, "cold_reboot_verified": False,
            "readback_verified": False, "evidence": "",
        },
        "recovery_repair": {
            "status": "NOT RUN", "repair_verified": False,
            "postcondition_verified": False, "evidence": "",
        },
        "smp": {
            "status": "NOT RUN", "ap_startup_verified": False,
            "overlapping_execution_verified": False, "cpu_ids": [],
            "evidence": "",
        },
    }
    report = output / "production-closeout-evidence.json"
    report.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--candidate-traces", required=True, type=Path)
    parser.add_argument("--production-matrix", type=Path, help="directory containing matrix-report.json and exact-ISO raw traces")
    args = parser.parse_args()
    try:
        data = collect(args.iso, args.output_dir, args.candidate_traces, args.production_matrix)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Collected ISO SHA-256 {data['production_iso_sha256']}")
    print(f"Evidence report: {(args.output_dir.resolve() / 'production-closeout-evidence.json')}")
    print("Production traces bound: " + str(sum(1 for case in data["cases"].values() if case["candidate_trace_is_production_evidence"])) + "/6; independent gates remain NOT RUN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

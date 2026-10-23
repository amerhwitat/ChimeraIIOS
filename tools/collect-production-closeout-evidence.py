#!/usr/bin/env python3
"""Collect real ISO identity and candidate traces into a fail-closed closeout report.

This collector deliberately does not promote candidate payload smoke tests to
production acceptance. Missing six-case production runs and independent gates
remain NOT RUN, so production-closeout-daps.py must reject the report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARE = ("bios", "uefi")
COMPONENT = {"live": "aurora-session", "installer": "install-executor", "recovery": "recovery-runtime"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(iso: Path, output: Path, candidate_traces: Path) -> dict:
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

    cases = {}
    for target in TARGETS:
        for firmware in FIRMWARE:
            case_id = f"{target}-{firmware}"
            candidate_name = f"{target}-debugcon.log" if firmware == "bios" else f"{target}-uefi-debugcon.log"
            candidate = candidate_traces / candidate_name
            raw_trace = ""
            if candidate.is_file() and candidate.stat().st_size:
                copied = traces_dir / f"{case_id}-candidate-smoke.log"
                shutil.copyfile(candidate, copied)
                raw_trace = copied.relative_to(output).as_posix()
            case = {
                "status": "NOT RUN",
                "production_iso": iso_rel.as_posix(),
                "iso_sha256": sha256(iso),
                "raw_trace": raw_trace,
                "cpl3_syscall_ack": False,
                "process_visible_rootfs": False,
                "display_mode_verified": False,
                "display_mode": "",
                "display_mode_evidence": "",
                "rootfs_file_syscalls_verified": False,
                "rootfs_file_syscalls_evidence": "",
                "syscall_pid": 0,
                "readiness_pid": 0,
                "candidate_trace_source": candidate_name if raw_trace else "missing",
                "candidate_trace_is_production_evidence": False,
            }
            if target in ("live", "recovery"):
                case["tmpfs_mutation_verified"] = False
                case["tmpfs_mutation_evidence"] = ""
            cases[case_id] = case

    data = {
        "schema_version": 1,
        "collector": "tools/collect-production-closeout-evidence.py",
        "production_iso_sha256": sha256(iso),
        "candidate_smoke_substituted": True,
        "collection_note": "Candidate target-specific smoke traces are archived for diagnosis only; all six actual production ISO/firmware cases and independent gates remain NOT RUN.",
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
    args = parser.parse_args()
    try:
        data = collect(args.iso, args.output_dir, args.candidate_traces)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Collected ISO SHA-256 {data['production_iso_sha256']}")
    print(f"Evidence report: {(args.output_dir.resolve() / 'production-closeout-evidence.json')}")
    print("Production closeout status: NOT RUN — candidate smoke is not production acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

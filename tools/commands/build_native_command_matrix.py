#!/usr/bin/env python3
"""Cross-build the real Chimera native multicall command for supported Linux ABIs.

The manifest records actual compiler outcomes, ELF machine verification and the
exact set of provider aliases that were linked for each target. A target with a
missing compiler or a failed compile is reported as a failure; no binary is
marked built without a verified ELF machine field. Cross-compilation is never
reported as runtime conformance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "x86_64": {"compiler": "cc", "machine": "Advanced Micro Devices X86-64", "elf_machine": 62},
    "aarch64": {"compiler": "aarch64-linux-gnu-gcc", "machine": "AArch64", "elf_machine": 183},
    "riscv64": {"compiler": "riscv64-linux-gnu-gcc", "machine": "RISC-V", "elf_machine": 243},
}
BUILT = "cross-compiled-and-elf-machine-validated"
OFFICIAL_STATUS = ROOT / "isa/generated/universal-instruction-catalog.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def official_snapshot() -> dict:
    data = json.loads(OFFICIAL_STATUS.read_text(encoding="utf-8"))
    coverage = data["coverage"]
    return {
        "source": "isa/generated/universal-instruction-catalog.json",
        "status": data.get("status", "not-run"),
        "conformance_tested": coverage["conformance_tested"],
        "not_implemented": coverage["not_implemented"],
        "scope": "Official ISA status. This build manifest never modifies it.",
    }


def provider_names(policy_path: Path, providers_path: Path | None) -> list[str]:
    if providers_path is None:
        return list(json.loads(policy_path.read_text(encoding="utf-8"))["native_build"]["multicall_aliases"])
    data = json.loads(providers_path.read_text(encoding="utf-8"))
    names = [row["name"] for row in data["providers"] if row.get("implementation") == "native"]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate provider names in engineering manifest")
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--providers", type=Path, default=None,
                        help="engineering provider manifest; defaults to policy multicall aliases")
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()

    providers = provider_names(args.policy, args.providers)
    if not args.source.is_file():
        raise SystemExit(f"missing source: {args.source}")

    readelf = shutil.which("readelf")
    if not readelf:
        raise SystemExit("readelf is required")

    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    failures: list[str] = []

    for target, spec in TARGETS.items():
        compiler = shutil.which(spec["compiler"])
        row = {
            "target": target,
            "compiler": spec["compiler"],
            "binary_status": "not-built",
            "runtime_status": "not-tested-cross-build-only",
            "providers_expected": len(providers),
            "providers_built": 0,
            "providers_linked": [],
            "providers_failed": list(providers),
        }

        if not compiler:
            row["reason"] = "target compiler unavailable"
            failures.append(target)
            rows.append(row)
            continue

        target_dir = args.output / target
        target_dir.mkdir(parents=True, exist_ok=True)
        binary = target_dir / "chimera-cmd"

        proc = subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(args.source), "-o", str(binary)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if proc.returncode:
            row["reason"] = "compiler failed"
            row["compiler_stderr"] = proc.stderr[-4000:]
            failures.append(target)
            rows.append(row)
            continue

        header = subprocess.run(
            [readelf, "-h", str(binary)], check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout
        machine = next(
            (line.split(":", 1)[1].strip() for line in header.splitlines()
             if line.strip().startswith("Machine:")),
            None,
        )
        if not machine or spec["machine"].casefold() not in machine.casefold():
            row["reason"] = f"ELF machine mismatch: expected {spec['machine']}, got {machine}"
            failures.append(target)
            rows.append(row)
            continue

        linked = []
        for name in providers:
            link = target_dir / name
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to("chimera-cmd")
            if not link.is_symlink() or link.resolve() != binary.resolve():
                row["reason"] = f"provider alias verification failed: {name}"
                failures.append(target)
                rows.append(row)
                break
            linked.append(name)

        if row.get("reason"):
            continue

        row.update({
            "binary_status": BUILT,
            "elf_machine": machine,
            "elf_machine_id": spec["elf_machine"],
            "binary": str(binary.relative_to(args.output)),
            "sha256": sha256(binary),
            "providers_built": len(linked),
            "providers_linked": linked,
            "providers_failed": [],
        })
        rows.append(row)

    manifest = {
        "schema": "CHM-NATIVE-COMMAND-ISA-BUILD-1",
        "policy": ("Only compiled outputs with a verified ELF machine field are marked "
                   "built. Cross-compilation is not native runtime acceptance."),
        "provider_manifest": str(args.providers) if args.providers else str(args.policy),
        "provider_count": len(providers),
        "providers": providers,
        "official_status_snapshot": official_snapshot(),
        "engineering_only": True,
        "target_count": len(TARGETS),
        "targets": rows,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "built": sum(row["binary_status"] == BUILT for row in rows),
        "targets": len(rows),
        "providers": len(providers),
        "failures": failures,
    }, sort_keys=True))
    return 1 if args.require_all and failures else 0


if __name__ == "__main__":
    sys.exit(main())

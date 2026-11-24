#!/usr/bin/env python3
"""Execute real Chimera command providers and record measured partial evidence.

This runner never changes official conformance status. It executes the real
multicall binary through per-provider symlinks, compares observable stdout and
exit codes against explicit cases, and records pass/fail counts per ISA. ISAs
without an executable binary and emulator are recorded as not-run, not passed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "src/chimera-command-compat/chimera-cmd.c"
DEFAULT_CASES = ROOT / "tools/commands/command-conformance-cases.json"
DEFAULT_PROVIDERS = ROOT / "system/commands/native-provider-engineering.json"
OFFICIAL_ISA = ROOT / "isa/generated/universal-instruction-catalog.json"
OFFICIAL_COMMANDS = ROOT / "system/commands/command-runtime-capabilities.json"

ISAS = ("x86_64", "aarch64", "riscv64")
EXPECTED_OFFICIAL = {"status": "not-run", "conformance_tested": 0, "not_implemented": 1613}
MAX_CAPTURE = 8000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def host_isa() -> str:
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    if machine in ("aarch64", "arm64"):
        return "aarch64"
    if machine in ("riscv64",):
        return "riscv64"
    return machine


def official_status() -> tuple[dict, bool]:
    isa_doc = json.loads(OFFICIAL_ISA.read_text(encoding="utf-8"))
    command_doc = json.loads(OFFICIAL_COMMANDS.read_text(encoding="utf-8"))
    coverage = isa_doc["coverage"]
    observed = {
        "status": isa_doc.get("status", "not-run"),
        "conformance_tested": coverage["conformance_tested"],
        "not_implemented": coverage["not_implemented"],
        "conformance_claim": False,
        "catalog_command_count": command_doc["command_count"],
        "commands_needing_compatibility_provider": command_doc["mode_counts"]["compatibility-provider-required"],
        "commands_needing_native_provider": command_doc["mode_counts"]["native-provider-required"],
        "native_backed_official": command_doc["mode_counts"]["native"],
    }
    unchanged = all(observed[key] == value for key, value in EXPECTED_OFFICIAL.items())
    return observed, unchanged


def substitute(value: str, mapping: dict[str, str]) -> str:
    for key, replacement in mapping.items():
        value = value.replace(key, replacement)
    return value


def run_cases(binary: Path, case_doc: dict, workdir: Path, mapping: dict[str, str],
              emulator: str | None) -> list[dict]:
    bindir = workdir / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    commands = {case["command"] for case in case_doc["cases"]}

    for name in commands:
        link = bindir / name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(binary)

    results = []
    for case in case_doc["cases"]:
        argv = [str(substitute(arg, mapping)) for arg in case.get("args", [])]
        invocation = ([emulator, str(bindir / case["command"])] if emulator
                      else [str(bindir / case["command"])]) + argv
        expected_exit = int(case.get("expected_exit", 0))
        expected_stdout = case.get("expected_stdout")
        if expected_stdout is not None:
            expected_stdout = substitute(expected_stdout, mapping)
        contains = case.get("expected_stdout_contains")
        if contains is not None:
            contains = substitute(contains, mapping)

        env = os.environ.copy()
        env.update(case.get("env", {}))
        env["CHIMERA_DISABLE_COMPAT"] = "1"
        stdin = case.get("stdin", "")

        record = {
            "id": case["id"],
            "command": case["command"],
            "args": argv,
            "expected_exit": expected_exit,
            "expected_stdout": expected_stdout,
            "expected_stdout_contains": contains,
            "pass": False,
        }

        try:
            proc = subprocess.run(
                invocation,
                input=stdin.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(workdir),
                env=env,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            record["failure_reason"] = f"execution error: {exc}"
            results.append(record)
            continue

        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        record["actual_exit"] = proc.returncode
        record["actual_stdout"] = stdout[:MAX_CAPTURE]
        record["actual_stderr"] = stderr[:MAX_CAPTURE]

        reasons = []
        if proc.returncode != expected_exit:
            reasons.append(f"exit {proc.returncode} != {expected_exit}")
        if expected_stdout is not None and stdout != expected_stdout:
            reasons.append("stdout mismatch")
        if contains is not None and contains not in stdout:
            reasons.append("expected substring missing from stdout")

        record["pass"] = not reasons
        if reasons:
            record["failure_reason"] = "; ".join(reasons)
        results.append(record)

    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--provider-manifest", type=Path, default=DEFAULT_PROVIDERS)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/command-conformance/evidence.json")
    parser.add_argument("--binary", type=Path, default=None,
                        help="use an existing host binary instead of compiling --source")
    parser.add_argument("--isa-binary", action="append", default=[], metavar="ISA=PATH",
                        help="executable multicall binary for a foreign ISA")
    parser.add_argument("--emulator", action="append", default=[], metavar="ISA=COMMAND",
                        help="user-mode emulator command for a foreign ISA")
    parser.add_argument("--require-all-isa", action="store_true")
    args = parser.parse_args()

    if not args.cases.is_file():
        raise SystemExit(f"missing cases: {args.cases}")
    if not args.provider_manifest.is_file():
        raise SystemExit(f"missing provider manifest: {args.provider_manifest}")
    if not args.source.is_file() and args.binary is None:
        raise SystemExit(f"missing source: {args.source}")

    case_doc = json.loads(args.cases.read_text(encoding="utf-8"))
    provider_doc = json.loads(args.provider_manifest.read_text(encoding="utf-8"))
    observed_official, official_unchanged = official_status()

    compiler = shutil.which("cc") or shutil.which("gcc")
    if args.binary is not None:
        host_binary = args.binary.resolve()
    else:
        if not compiler:
            raise SystemExit("no host C compiler available")
        build_dir = args.output.parent / "host-build"
        build_dir.mkdir(parents=True, exist_ok=True)
        host_binary = build_dir / "chimera-cmd"
        compile_proc = subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(args.source), "-o", str(host_binary)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if compile_proc.returncode:
            raise SystemExit(f"host compile failed: {compile_proc.stderr[-2000:]}")
        host_binary = host_binary.resolve()

    if not host_binary.is_file():
        raise SystemExit(f"host binary missing: {host_binary}")

    foreign_binaries = {}
    for item in args.isa_binary:
        if "=" not in item:
            raise SystemExit(f"invalid --isa-binary: {item}")
        name, path = item.split("=", 1)
        foreign_binaries[name] = Path(path).resolve()

    emulators = {}
    for item in args.emulator:
        if "=" not in item:
            raise SystemExit(f"invalid --emulator: {item}")
        name, command = item.split("=", 1)
        emulators[name] = command

    current_isa = host_isa()
    isa_results = {}
    all_case_results = []
    mapping_base = {
        "{cwd}": str(Path.cwd()),
        "{sysname}": platform.system(),
        "{nodename}": platform.node(),
    }

    with tempfile.TemporaryDirectory(prefix="chimera-command-conformance-") as tmp:
        root_tmp = Path(tmp)
        for isa in ISAS:
            workdir = root_tmp / isa
            workdir.mkdir(parents=True, exist_ok=True)
            (workdir / "sample.txt").write_text("alpha\nbeta\n", encoding="utf-8")
            (workdir / "emptydir").mkdir(exist_ok=True)
            (workdir / "link").symlink_to("sample.txt")

            mapping = dict(mapping_base)
            mapping["{workdir}"] = str(workdir)
            mapping["{bindir}"] = str(workdir / "bin")

            binary = host_binary if isa == current_isa else foreign_binaries.get(isa)
            emulator = emulators.get(isa)
            row = {
                "isa": isa,
                "host_isa": isa == current_isa,
                "binary": str(binary) if binary else None,
                "emulator": emulator,
                "executed": 0,
                "passed": 0,
                "failed": 0,
                "not_run": len(case_doc["cases"]),
                "status": "not-run",
            }

            if binary and binary.is_file():
                if emulator and not shutil.which(emulator.split()[0]):
                    row["reason"] = f"emulator not found: {emulator.split()[0]}"
                else:
                    results = run_cases(binary, case_doc, workdir, mapping, emulator)
                    row["executed"] = len(results)
                    row["passed"] = sum(1 for result in results if result["pass"])
                    row["failed"] = sum(1 for result in results if not result["pass"])
                    row["not_run"] = len(case_doc["cases"]) - len(results)
                    row["status"] = ("partial-engineering" if row["failed"] == 0
                                     else "partial-engineering-failed")
                    if isa == current_isa:
                        all_case_results = results
            else:
                row["reason"] = ("no executable provider binary for this ISA; "
                                 "cross-build alone is not runtime evidence")

            isa_results[isa] = row

    evidence = {
        "schema": "CHM-COMMAND-CONFORMANCE-EVIDENCE-1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": ("Partial engineering cases against real provider binaries. "
                  "Not an official architectural conformance suite."),
        "official_status": observed_official,
        "official_status_unchanged": official_unchanged,
        "full_catalog_run": False,
        "conformance_claim": False,
        "production_acceptance": False,
        "provider_manifest": str(args.provider_manifest.relative_to(ROOT)
                                 if args.provider_manifest.is_relative_to(ROOT)
                                 else args.provider_manifest),
        "provider_count": len(provider_doc["providers"]),
        "case_count": len(case_doc["cases"]),
        "host_isa": current_isa,
        "host_binary_sha256": digest(host_binary),
        "isa_results": isa_results,
        "cases": all_case_results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")

    print(json.dumps({
        "official_status_unchanged": official_unchanged,
        "host_isa": current_isa,
        "executed": sum(row["executed"] for row in isa_results.values()),
        "passed": sum(row["passed"] for row in isa_results.values()),
        "failed": sum(row["failed"] for row in isa_results.values()),
        "output": str(args.output),
    }, sort_keys=True))

    failures = sum(row["failed"] for row in isa_results.values())
    if not official_unchanged:
        return 2
    if failures:
        return 1
    if args.require_all_isa and any(row["executed"] == 0 for row in isa_results.values()):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

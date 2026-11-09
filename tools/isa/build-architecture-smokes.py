#!/usr/bin/env python3
"""Compile one freestanding toolchain smoke object for each declared ISA backend."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

C_SOURCE = r"""
typedef unsigned long long chm_u64;
volatile chm_u64 chm_isa_smoke(chm_u64 a, chm_u64 b) {
    volatile chm_u64 x = (a << 7) ^ (b >> 3);
    return x + (a ^ b);
}
"""

def run(command: list[str], timeout: int = 90) -> tuple[int, str]:
    try:
        p = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backends", type=Path, default=Path("tools/isa/architecture-backends.json"))
    ap.add_argument("--output", type=Path, default=Path("build/isa-smokes"))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    registry = json.loads(args.backends.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    clang = shutil.which("clang")
    nasm = shutil.which("nasm")
    file_tool = shutil.which("file")
    readobj = shutil.which("llvm-readobj")
    rows = []
    for arch, metadata in registry.get("architectures", {}).items():
        if arch == "unknown" or metadata.get("execution") == "unsupported":
            rows.append({"architecture": arch, "status": "unsupported-by-policy"})
            continue
        target_list = metadata.get("llvm_targets", [])
        if arch == "dos-x86":
            if not nasm:
                rows.append({"architecture": arch, "status": "toolchain-missing", "tool": "nasm"})
                continue
            out = args.output / (arch + ".com")
            with tempfile.TemporaryDirectory(prefix="chm-isa-") as td:
                src = Path(td) / "smoke.asm"
                src.write_text("BITS 16\nORG 0x100\nmov ax, 0x4c00\nint 0x21\n", encoding="ascii")
                rc, log = run([nasm, "-f", "bin", "-o", str(out), str(src)])
            row = {"architecture": arch, "target": "i8086-pc-none", "tool": "nasm", "status": "compiled" if rc == 0 and out.is_file() else "failed", "log": log}
            if out.is_file():
                row.update({"artifact": out.name, "sha256": digest(out), "bytes": out.stat().st_size})
                if file_tool:
                    _, row["file_type"] = run([file_tool, "-b", str(out)])
            rows.append(row)
            continue
        if not target_list:
            rows.append({"architecture": arch, "status": "no-compiler-target-declared"})
            continue
        if not clang:
            rows.append({"architecture": arch, "status": "toolchain-missing", "tool": "clang"})
            continue
        for index, target in enumerate(target_list):
            out = args.output / f"{arch}-{index}.o"
            with tempfile.TemporaryDirectory(prefix="chm-isa-") as td:
                src = Path(td) / "smoke.c"
                src.write_text(C_SOURCE, encoding="ascii")
                command = [clang, "-target", target, "-ffreestanding", "-fno-stack-protector", "-fno-pic", "-O0", "-c", str(src), "-o", str(out)]
                rc, log = run(command)
            row = {"architecture": arch, "target": target, "tool": "clang", "status": "compiled" if rc == 0 and out.is_file() else "failed", "log": log}
            if out.is_file():
                row.update({"artifact": out.name, "sha256": digest(out), "bytes": out.stat().st_size})
                if readobj:
                    _, row["object_headers"] = run([readobj, "--file-headers", str(out)])
                elif file_tool:
                    _, row["file_type"] = run([file_tool, "-b", str(out)])
            rows.append(row)
    failed = [r for r in rows if r["status"] in {"failed", "toolchain-missing"}]
    report = {
        "schema": "CHM-ISA-CROSS-COMPILE-SMOKE-1",
        "strict": args.strict,
        "backend_architecture_count": len(registry.get("architectures", {})),
        "attempt_count": sum(1 for r in rows if r["status"] not in {"unsupported-by-policy", "no-compiler-target-declared"}),
        "compiled_count": sum(1 for r in rows if r["status"] == "compiled"),
        "failed_count": len(failed),
        "results": rows,
        "note": "Freestanding object/COM smoke compilation proves only that the selected assembler/compiler emitted an artifact for this target. It does not prove ABI, sysroot, linker, loader, instruction conformance, or runtime support.",
    }
    report_path = args.output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[Chimera][ISA] compiled={report['compiled_count']} failed={report['failed_count']} attempts={report['attempt_count']} report={report_path}")
    return 1 if args.strict and failed else 0

if __name__ == "__main__":
    raise SystemExit(main())

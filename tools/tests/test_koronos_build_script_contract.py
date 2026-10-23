#!/usr/bin/env python3
"""Regression guard for the canonical Koronos build's ISO9660 test wiring."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
script = ROOT / "kernel" / "build-koronos.sh"
try:
    source = script.read_text(encoding="utf-8")
except OSError as exc:
    print(f"FAIL: cannot read {script}: {exc}", file=sys.stderr)
    raise SystemExit(2)

bad = r'\n"$BUILD/block-device-iso9660-test"'
if bad in source:
    print("FAIL: ISO9660 build commands contain a literal \\n instead of line breaks", file=sys.stderr)
    raise SystemExit(1)

lines = source.splitlines()
compile_line = next((i for i, line in enumerate(lines)
                     if ' -o "$BUILD/block-device-iso9660-test"' in line), None)
if compile_line is None or compile_line + 1 >= len(lines):
    print("FAIL: ISO9660 test compile/run commands are missing", file=sys.stderr)
    raise SystemExit(1)
if lines[compile_line + 1].strip() != '"$BUILD/block-device-iso9660-test"':
    print("FAIL: ISO9660 test executable must run as a separate shell command", file=sys.stderr)
    raise SystemExit(1)
if "sources=(block_device iso9660 " not in source:
    print("FAIL: block-device and ISO9660 objects are not part of the kernel build", file=sys.stderr)
    raise SystemExit(1)

print("koronos_build_script_contract: PASS")

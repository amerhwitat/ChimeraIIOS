#!/usr/bin/env python3
"""Regression guard for the canonical Koronos build's ISO9660 test wiring."""
from pathlib import Path
import subprocess
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

# The swap adapter must be linked into Koronos and its host regression test
# must be compiled with the canonical build and executed as a separate step.
if "swap_block_device" not in source.split("sources=(", 1)[1].split(")", 1)[0]:
    print("FAIL: swap block-device adapter is not part of the kernel object list", file=sys.stderr)
    raise SystemExit(1)
swap_test_compile = next((i for i, line in enumerate(lines)
                          if ' -o "$BUILD/swap-block-device-test"' in line), None)
if swap_test_compile is None:
    print("FAIL: swap block-device host test compile command is missing", file=sys.stderr)
    raise SystemExit(1)
# The compiler command uses shell continuations, so inspect the complete
# command block rather than only its final "-o" line.
swap_test_command = "\n".join(lines[max(0, swap_test_compile - 3):swap_test_compile + 1])
if not all(token in swap_test_command
           for token in ('"$ROOT/kernel/core/block_device.cpp"',
                         '"$ROOT/kernel/core/swap.cpp"',
                         '"$ROOT/kernel/core/swap_block_device.cpp"',
                         '"$ROOT/kernel/tests/swap_block_device_test.cpp"')):
    print("FAIL: swap block-device host test does not compile the adapter and its dependencies", file=sys.stderr)
    raise SystemExit(1)
if swap_test_compile + 1 >= len(lines) or lines[swap_test_compile + 1].strip() != '"$BUILD/swap-block-device-test"':
    print("FAIL: swap block-device host test must run immediately after compilation", file=sys.stderr)
    raise SystemExit(1)
if "koronos_swap_init_block_extent" not in source:
    print("FAIL: required-symbol gate does not include the swap block-device initializer", file=sys.stderr)
    raise SystemExit(1)

if 'SYSTEM_BLOCK_SIZE="${KORONOS_SYSTEM_BLOCK_SIZE:-4096}"' not in source:
    print("FAIL: system block size must default to 4096 and allow user configuration", file=sys.stderr)
    raise SystemExit(1)
if "-DKORONOS_SYSTEM_BLOCK_SIZE=$SYSTEM_BLOCK_SIZE" not in source:
    print("FAIL: configured system block size is not passed to the kernel compiler", file=sys.stderr)
    raise SystemExit(1)
if "power of two between 512 and 65536 bytes" not in source:
    print("FAIL: system block size bounds are not validated", file=sys.stderr)
    raise SystemExit(1)
if "--system-block-size" not in source or 'SYSTEM_BLOCK_SIZE="${1#*=}"' not in source:
    print("FAIL: system block size must be configurable by CLI", file=sys.stderr)
    raise SystemExit(1)

# The primary ISO builder must forward the same setting to the canonical kernel build.
iso_builder = ROOT / "build-chimera-iso.sh"
try:
    iso_source = iso_builder.read_text(encoding="utf-8")
except OSError as exc:
    print(f"FAIL: cannot read {iso_builder}: {exc}", file=sys.stderr)
    raise SystemExit(2)
if "--system-block-size" not in iso_source or "export KORONOS_SYSTEM_BLOCK_SIZE" not in iso_source:
    print("FAIL: primary ISO builder does not expose/forward system block size", file=sys.stderr)
    raise SystemExit(1)
if 'KORONOS_SYSTEM_BLOCK_SIZE="${KORONOS_SYSTEM_BLOCK_SIZE:-4096}"' not in iso_source:
    print("FAIL: primary ISO builder must default system block size to 4096", file=sys.stderr)
    raise SystemExit(1)

# Invalid CLI values must fail before compilation or filesystem side effects.
invalid = subprocess.run(
    ["bash", str(script), "--system-block-size", "1000"],
    cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
)
if invalid.returncode != 2 or "power of two" not in invalid.stderr:
    print("FAIL: invalid CLI system block size was not rejected early", file=sys.stderr)
    raise SystemExit(1)
missing = subprocess.run(
    ["bash", str(script), "--system-block-size"],
    cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
)
if missing.returncode != 2 or "requires a byte count" not in missing.stderr:
    print("FAIL: missing CLI system block size was not rejected", file=sys.stderr)
    raise SystemExit(1)

print("koronos_build_script_contract: PASS")

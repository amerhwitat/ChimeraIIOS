#!/usr/bin/env python3
"""Regression test for the build-chimera-iso.sh startup and storage-option order."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
script = ROOT / "build-chimera-iso.sh"
source = script.read_text(encoding="utf-8")

subprocess.run(["bash", "-n", str(script)], check=True)

block_start = source.index('if [[ -z "${CHIMERA_SYSTEM_BLOCK_SIZE:-}"')
default_branch_end = source.index("\nfi\n", block_start) + len("\nfi\n")
default_branch = source[block_start:default_branch_end]
if re.search(r"(?m)^\s*exit(?:\s|$)", default_branch):
    raise SystemExit("FAIL: missing block-size default must continue into build startup")

assignment = source.index('CHIMERA_SYSTEM_BLOCK_SIZE="${CHIMERA_SYSTEM_BLOCK_SIZE:-${SYSTEM_BLOCK_SIZE:-4096}}"', default_branch_end)
validation = source.index('if [[ ! "$CHIMERA_SYSTEM_BLOCK_SIZE" =~ ^[1-9][0-9]*$ ]]; then', assignment)
validation_end = source.index("\nfi\n", validation) + len("\nfi\n")
if "exit 2" not in source[validation:validation_end]:
    raise SystemExit("FAIL: invalid block sizes must fail closed with exit 2")
export_at = source.index("export CHIMERA_SYSTEM_BLOCK_SIZE SYSTEM_BLOCK_SIZE", validation_end)
if not assignment < validation < export_at:
    raise SystemExit("FAIL: block-size default, validation, and export order is incorrect")

parser_start = source.index("while [[ $# -gt 0 ]]")
prefix = source[:parser_start]
if re.search(r"(?m)^ensure_log_dir(?:\s|$)", prefix):
    raise SystemExit("FAIL: log directory must not be initialized before --storage-auto is parsed")

if 'LOG_FALLBACK_DIR="${CHIMERA_LOG_FALLBACK_DIR:-/tmp/chimera-build-logs-' not in source:
    raise SystemExit("FAIL: log fallback must use writable /tmp, not inherited TMPDIR")
if '--storage-auto) STORAGE_AUTO=1; shift;;' not in source:
    raise SystemExit("FAIL: --storage-auto option is missing")
if not source.rstrip().endswith('main "$@"'):
    raise SystemExit("FAIL: build entrypoint does not invoke main")

print("PASS: ISO builder defaults to 4 KiB, rejects invalid values, and continues into startup")

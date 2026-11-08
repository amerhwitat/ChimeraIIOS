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
block_end = source.index("export CHIMERA_SYSTEM_BLOCK_SIZE", block_start)
if "exit " in source[block_start:block_end]:
    raise SystemExit("FAIL: block-size default path must continue into build startup")

parser_start = source.index("while [[ $# -gt 0 ]]")
prefix = source[:parser_start]
if re.search(r"(?m)^ensure_log_dir(?:\s|$)", prefix):
    raise SystemExit("FAIL: log directory must not be initialized before --storage-auto is parsed")

if 'LOG_FALLBACK_DIR="${CHIMERA_LOG_FALLBACK_DIR:-/tmp/chimera-build-logs-' not in source:
    raise SystemExit("FAIL: log fallback must use writable /tmp, not inherited TMPDIR")
if '--storage-auto) STORAGE_AUTO=1; shift;;' not in source:
    raise SystemExit("FAIL: --storage-auto option is missing")
if "export CHIMERA_SYSTEM_BLOCK_SIZE SYSTEM_BLOCK_SIZE" not in source:
    raise SystemExit("FAIL: canonical system block size is not exported")
if not source.rstrip().endswith('main "$@"'):
    raise SystemExit("FAIL: build entrypoint does not invoke main")

print("PASS: ISO builder parses storage options before log setup and continues after the 4 KiB default")

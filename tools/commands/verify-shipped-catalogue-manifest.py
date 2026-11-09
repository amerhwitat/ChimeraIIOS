#!/usr/bin/env python3
"""Verify every command/ISA/provider catalogue staged in a hosted live rootfs."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

REQUIRED = {
    "chimera-command-list.json", "ss64-command-catalog.json",
    "ss64-command-catalog.ar.json", "native-command-candidates.json",
    "command-runtime-capabilities.json", "compatibility-binary-policy.json",
    "chimera-arabic.json", "native-provider-aliases.json",
    "online-command-catalog.json", "linux-command-registry.json",
    "os-command-runtime.json", "ISA.csv", "catalog.json",
    "universal-instruction-catalog.json", "isa-encoding-registry.json",
    "online-isa-index.json", "isa-encoding-samples.json",
    "riscv-opcodes.json", "isa-source-manifest.json",
    "architecture-backends.json", "instruction-semantics.schema.json",
    "isa_bitfields.schema.json", "isa_opcodes.csv",
    "isa_opcodes_expanded_with_encodings.csv",
    "chimera_r8192_opcode_index.csv", "isa_extension_0092_011c.csv",
    "linux-abi-command-matrix.json", "command-isa-coverage.json",
    "terminals-registry.json", "shells-registry.json",
    "terminals-binary-manifest.json", "shells-binary-manifest.json",
    "terminal-shell-provider-status.json",
}

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify-shipped-catalogue-manifest.py ROOTFS")
    rootfs = Path(sys.argv[1]).resolve()
    catalogues = rootfs / "usr/share/chimera/catalogs"
    manifest_path = catalogues / "catalogue-manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing catalogue manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "CHIMERA-COMMAND-ISA-CATALOGUE-MANIFEST-1":
        raise SystemExit("unsupported catalogue manifest schema")
    rows = manifest.get("files", [])
    if manifest.get("file_count") != len(rows) or len(rows) < 40:
        raise SystemExit(f"catalogue count mismatch or incomplete inventory: {len(rows)}")
    seen = set()
    for row in rows:
        rel = Path(row["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise SystemExit(f"unsafe catalogue path: {rel}")
        if rel.as_posix() in seen:
            raise SystemExit(f"duplicate catalogue path: {rel}")
        seen.add(rel.as_posix())
        path = catalogues / rel
        if not path.is_file():
            raise SystemExit(f"catalogue file missing: {rel}")
        data = path.read_bytes()
        if len(data) != row.get("size") or hashlib.sha256(data).hexdigest() != row.get("sha256"):
            raise SystemExit(f"catalogue checksum/size mismatch: {rel}")
    missing = sorted(REQUIRED - {Path(x).name for x in seen})
    if missing:
        raise SystemExit("required command/ISA/provider catalogues missing: " + ", ".join(missing))
    print(f"Verified {len(rows)} shipped command, ISA, provider and terminal catalogue files by SHA-256.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

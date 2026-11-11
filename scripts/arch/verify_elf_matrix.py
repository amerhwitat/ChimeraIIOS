#!/usr/bin/env python3
"""Fail-closed ELF target matrix verifier; standard-library only."""
from __future__ import annotations
import argparse, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "arch" / "native-elf-matrix.json"
ELF_MAGIC = b"\x7fELF"
ENDIAN = {"little": 1, "big": 2}
CLASS = {32: 1, 64: 2}

class MatrixError(ValueError):
    pass

def load_manifest(path: Path = MANIFEST) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "chimera-native-elf-matrix-v1":
        raise MatrixError("unknown native ELF matrix schema")
    ids = [t.get("id") for t in data.get("architecture_targets", [])]
    if not ids or len(ids) != len(set(ids)):
        raise MatrixError("architecture target IDs must be nonempty and unique")
    for t in data["architecture_targets"]:
        if t.get("status") == "current-repository-build-target" and t.get("execution_claim") != "buildable-target-only; production userspace acceptance separately required":
            raise MatrixError(f"{t['id']}: current-target claim must remain bounded")
        if t.get("id") != "wasm32" and t.get("elf_machine") is None:
            raise MatrixError(f"{t['id']}: ELF machine ID missing")
    return data

def read_elf_identity(path: Path) -> tuple[int, str, int]:
    with path.open("rb") as f:
        ident = f.read(20)
    if len(ident) < 20 or ident[:4] != ELF_MAGIC:
        raise MatrixError(f"{path}: not a complete ELF header")
    elf_class = {1: 32, 2: 64}.get(ident[4])
    endian = {1: "little", 2: "big"}.get(ident[5])
    if elf_class is None or endian is None or ident[6] != 1:
        raise MatrixError(f"{path}: invalid ELF class, byte order, or version")
    machine = int.from_bytes(ident[18:20], endian)
    return elf_class, endian, machine

def verify_artifact(target: dict, path: Path) -> None:
    if target["id"] == "wasm32":
        raise MatrixError("WASM is a virtual ISA and cannot be accepted as a native CPU ELF")
    cls, endian, machine = read_elf_identity(path)
    expected = (target["elf_class"], target["endianness"], target["elf_machine"])
    if (cls, endian, machine) != expected:
        raise MatrixError(f"{target['id']}: ELF identity mismatch: got class={cls}, endian={endian}, machine={machine}; expected {expected}")

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--artifacts", type=Path, help="directory containing <target-id>.elf for every target marked current-repository-build-target")
    args = ap.parse_args()
    try:
        data = load_manifest(args.manifest)
        if args.artifacts:
            required = [t for t in data["architecture_targets"] if t["status"] == "current-repository-build-target"]
            for target in required:
                path = args.artifacts / (target["id"] + ".elf")
                if not path.is_file():
                    raise MatrixError(f"required native ELF missing: {path}")
                verify_artifact(target, path)
        print(f"ELF matrix schema valid: {len(data['architecture_targets'])} target records; artifact verification {'requested' if args.artifacts else 'not requested'}")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, MatrixError) as exc:
        print(f"ELF MATRIX REJECTED: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
